"""Pull all item screenshots from Supabase Storage to local disk.

Downloads every object in the item-screenshots bucket to
questionbank/images/<name>, skipping files whose local byte count already
matches the remote Content-Length. Safe to re-run.

Usage:
    set SUPABASE_URL=https://bzqbhtrurzzavhqbgqrs.supabase.co
    set SUPABASE_SERVICE_ROLE_KEY=<service role key>
    python supabase/pull_screenshots.py [--dry-run]
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import requests

BUCKET   = "item-screenshots"
DEST_DIR = Path(__file__).resolve().parent.parent / "questionbank" / "images"
# Storage list API returns at most 1 000 objects per call; page if needed.
PAGE_SIZE = 1000


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"error: {name} not set")
    return v.replace("\r", "").replace("\n", "")


def list_objects(url: str, key: str) -> list[dict]:
    """Return all objects in the bucket, paging through 1 000-item pages."""
    headers = {"Authorization": f"Bearer {key}", "apikey": key,
               "Content-Type": "application/json"}
    objects: list[dict] = []
    offset = 0
    while True:
        body = {"prefix": "", "limit": PAGE_SIZE, "offset": offset,
                "sortBy": {"column": "name", "order": "asc"}}
        r = requests.post(
            f"{url}/storage/v1/object/list/{BUCKET}",
            headers=headers, json=body, timeout=30,
        )
        if not r.ok:
            sys.exit(f"error: listing bucket failed: {r.status_code} {r.text[:200]}")
        page = r.json()
        objects.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return objects


def pull(url: str, key: str, name: str, dest: Path, dry: bool) -> str:
    """Download one object. Returns 'ok', 'skip', or 'fail'."""
    # Public bucket: use the public URL (no auth header needed).
    remote_url = f"{url}/storage/v1/object/public/{BUCKET}/{name}"

    if dest.exists():
        # Cheap skip: HEAD for Content-Length, compare to local size.
        h = requests.head(remote_url, timeout=10)
        remote_size = int(h.headers.get("content-length", -1))
        if remote_size >= 0 and dest.stat().st_size == remote_size:
            print(f"  skip {name}  (already up-to-date)")
            return "skip"

    if dry:
        print(f"  [dry-run] {name} -> {dest}")
        return "ok"

    r = requests.get(remote_url, timeout=30)
    if not r.ok:
        print(f"  FAIL {name}: {r.status_code} {r.text[:200]}")
        return "fail"

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    print(f"  ok   {name}  ({len(r.content):>9} bytes)")
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    url = env("SUPABASE_URL").rstrip("/")
    key = env("SUPABASE_SERVICE_ROLE_KEY")

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"listing {BUCKET} bucket...")
    objects = list_objects(url, key)
    # Filter out folder-sentinel entries (name ends with / or metadata is None).
    objects = [o for o in objects if o.get("name") and not o["name"].endswith("/")]
    print(f"found {len(objects)} object(s)\n")

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for obj in objects:
        name = obj["name"]
        dest = DEST_DIR / name
        counts[pull(url, key, name, dest, args.dry_run)] += 1

    total = len(objects)
    print(f"\ndone: {counts['ok']}/{total} downloaded  |  {counts['skip']} skipped  |  {counts['fail']} failed")
    return 0 if counts["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
