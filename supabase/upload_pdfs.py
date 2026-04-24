"""Upload all existing tex/*_{student,teacher,slides}.pdf to Supabase Storage.

One-shot migration — run after supabase/seed.py so every lesson has a live
PDF in the lesson-pdfs bucket on first load of the web app. After teachers
start editing + rebuilding via Railway, this script isn't needed again.

Usage:
    set SUPABASE_URL=https://bzqbhtrurzzavhqbgqrs.supabase.co
    set SUPABASE_SERVICE_ROLE_KEY=<service role key, ONE LINE no line breaks>
    python supabase/upload_pdfs.py [--dry-run]
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
TEX_DIR = REPO / "tex"
BUCKET = "lesson-pdfs"


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"error: {name} not set")
    return v.replace("\r", "").replace("\n", "")  # strip any stray line breaks


def upload(url: str, key: str, pdf: Path, object_name: str, dry: bool) -> bool:
    if dry:
        print(f"  [dry-run] {pdf.name:40s} -> {object_name}")
        return True
    r = requests.post(
        f"{url}/storage/v1/object/{BUCKET}/{object_name}",
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/pdf",
            "x-upsert": "true",
        },
        data=pdf.read_bytes(),
        timeout=30,
    )
    if not r.ok:
        print(f"  FAIL {object_name}: {r.status_code} {r.text[:200]}")
        return False
    print(f"  ok   {pdf.name:40s} -> {object_name}  ({pdf.stat().st_size:>8} bytes)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    url = env("SUPABASE_URL").rstrip("/")
    key = env("SUPABASE_SERVICE_ROLE_KEY")

    # student + teacher + slides + do_now, all L*_P*_*.pdf (+ APStats_*)
    pdfs = sorted(TEX_DIR.glob("L*_P*_student.pdf")) \
         + sorted(TEX_DIR.glob("L*_P*_teacher.pdf")) \
         + sorted(TEX_DIR.glob("L*_P*_slides.pdf")) \
         + sorted(TEX_DIR.glob("L*_P*_do_now.pdf")) \
         + sorted(TEX_DIR.glob("APStats_*_do_now.pdf"))

    print(f"uploading {len(pdfs)} PDFs to {BUCKET} bucket...\n")
    ok = 0
    for pdf in pdfs:
        # Object name mirrors the filename; unique per lesson+edition
        if upload(url, key, pdf, pdf.name, args.dry_run):
            ok += 1
    print(f"\n{ok}/{len(pdfs)} uploaded")
    return 0 if ok == len(pdfs) else 1


if __name__ == "__main__":
    sys.exit(main())
