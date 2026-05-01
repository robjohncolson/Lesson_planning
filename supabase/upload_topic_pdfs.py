"""Bulk-upload Savvas textbook chapter PDFs to Supabase Storage.

Globs a directory for a2_*_SE.pdf and a2_*_TE.pdf and uploads each to the
topic-pdfs bucket. Creates the bucket (public) if it does not already exist.

Usage:
    set SUPABASE_URL=https://bzqbhtrurzzavhqbgqrs.supabase.co
    set SUPABASE_SERVICE_ROLE_KEY=<service role key>
    python supabase/upload_topic_pdfs.py /path/to/dir [--dry-run]
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path

import requests

BUCKET = "topic-pdfs"
MAX_BYTES = 50 * 1024 * 1024          # 50 MB guard
FNAME_RE  = re.compile(r"^a2_\d-\d_(SE|TE)\.pdf$")


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"error: {name} not set")
    return v.replace("\r", "").replace("\n", "")


def ensure_bucket(url: str, key: str, dry: bool) -> None:
    """Create the bucket if it does not exist (404 -> create with public=true)."""
    if dry:
        return
    headers = {"Authorization": f"Bearer {key}", "apikey": key,
               "Content-Type": "application/json"}
    r = requests.get(f"{url}/storage/v1/bucket/{BUCKET}", headers=headers, timeout=10)
    if r.status_code == 200:
        return
    if r.status_code == 404:
        body = {"id": BUCKET, "name": BUCKET, "public": True}
        cr = requests.post(f"{url}/storage/v1/bucket", headers=headers,
                           json=body, timeout=10)
        if not cr.ok:
            sys.exit(f"error: could not create bucket {BUCKET}: {cr.status_code} {cr.text[:200]}")
        print(f"created bucket {BUCKET}")
    else:
        sys.exit(f"error: bucket check failed: {r.status_code} {r.text[:200]}")


def upload(url: str, key: str, pdf: Path, dry: bool) -> str:
    """Upload one PDF. Returns 'ok', 'skip', or 'fail'."""
    size = pdf.stat().st_size
    if size > MAX_BYTES:
        print(f"  skip {pdf.name}: {size // (1024*1024)} MB exceeds 50 MB limit")
        return "skip"
    if dry:
        print(f"  [dry-run] {pdf.name}")
        return "ok"
    r = requests.post(
        f"{url}/storage/v1/object/{BUCKET}/{pdf.name}",
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/pdf",
            "x-upsert": "true",
        },
        data=pdf.read_bytes(),
        timeout=60,
    )
    if r.ok:
        print(f"  ok   {pdf.name}  ({size:>9} bytes)")
        return "ok"
    print(f"  FAIL {pdf.name}: {r.status_code} {r.text[:200]}")
    return "fail"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", help="directory containing a2_*_(SE|TE).pdf files")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.directory)
    if not src.is_dir():
        sys.exit(f"error: not a directory: {src}")

    url = env("SUPABASE_URL").rstrip("/")
    key = env("SUPABASE_SERVICE_ROLE_KEY")

    candidates = sorted(src.glob("*.pdf"))
    pdfs, skipped = [], 0
    for f in candidates:
        if FNAME_RE.match(f.name):
            pdfs.append(f)
        else:
            print(f"  warn: skipping non-matching filename: {f.name}")
            skipped += 1

    print(f"found {len(pdfs)} matching PDF(s) in {src}  ({skipped} filename-skipped)\n")
    ensure_bucket(url, key, args.dry_run)

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for pdf in pdfs:
        counts[upload(url, key, pdf, args.dry_run)] += 1

    total = len(pdfs)
    print(f"\ndone: {counts['ok']}/{total} uploaded  |  {counts['skip']} skipped  |  {counts['fail']} failed")
    return 0 if counts["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
