"""Bulk-upload DOCX/PPTX lesson packets to Supabase Storage.

Globs a directory for L*_P*_{student,teacher}.docx and L*_P*_slides.pptx
(plus APStats_* variants) and uploads each to the lesson-docx bucket.
Creates the bucket (public) if it does not already exist.

Usage:
    set SUPABASE_URL=https://bzqbhtrurzzavhqbgqrs.supabase.co
    set SUPABASE_SERVICE_ROLE_KEY=<service role key>
    python supabase/upload_docx.py /path/to/dir [--dry-run]
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import requests

BUCKET = "lesson-docx"

MIME = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

# Patterns: L41_P2_student.docx / APStats_U4-L2_P1_slides.pptx
DOCX_GLOBS  = ["L*_P*_student.docx", "L*_P*_teacher.docx",
               "APStats_*_P*_student.docx", "APStats_*_P*_teacher.docx"]
PPTX_GLOBS  = ["L*_P*_slides.pptx", "APStats_*_P*_slides.pptx"]


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"error: {name} not set")
    return v.replace("\r", "").replace("\n", "")


def ensure_bucket(url: str, key: str, dry: bool) -> None:
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


def upload(url: str, key: str, f: Path, dry: bool) -> str:
    """Upload one file. Returns 'ok', 'skip', or 'fail'."""
    suffix = f.suffix.lower()
    mime = MIME.get(suffix)
    if mime is None:
        print(f"  skip {f.name}: unrecognised extension {suffix}")
        return "skip"
    if dry:
        print(f"  [dry-run] {f.name}")
        return "ok"
    r = requests.post(
        f"{url}/storage/v1/object/{BUCKET}/{f.name}",
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": mime,
            "x-upsert": "true",
        },
        data=f.read_bytes(),
        timeout=60,
    )
    if r.ok:
        print(f"  ok   {f.name}  ({f.stat().st_size:>9} bytes)")
        return "ok"
    print(f"  FAIL {f.name}: {r.status_code} {r.text[:200]}")
    return "fail"


def collect(src: Path) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for pattern in DOCX_GLOBS + PPTX_GLOBS:
        for f in sorted(src.glob(pattern)):
            if f not in seen:
                seen.add(f)
                files.append(f)
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", help="directory containing lesson DOCX/PPTX files")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.directory)
    if not src.is_dir():
        sys.exit(f"error: not a directory: {src}")

    url = env("SUPABASE_URL").rstrip("/")
    key = env("SUPABASE_SERVICE_ROLE_KEY")

    files = collect(src)
    print(f"found {len(files)} matching file(s) in {src}\n")
    ensure_bucket(url, key, args.dry_run)

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for f in files:
        counts[upload(url, key, f, args.dry_run)] += 1

    total = len(files)
    print(f"\ndone: {counts['ok']}/{total} uploaded  |  {counts['skip']} skipped  |  {counts['fail']} failed")
    return 0 if counts["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
