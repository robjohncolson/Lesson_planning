"""Seed the question-bank registry from an existing Blooket CSV.

Each Blooket row -> one registry entry. All seeded questions get the
supplied --default-dok unless already classified elsewhere. Review and
bump DOK manually in registry.jsonl afterward.

Usage:
    python import_blooket_csv.py Blooket_Day3_Multiplicity.csv --lesson 3-5 --default-dok 1 --tag day3
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import sys
from pathlib import Path

import qb

# Windows: reconfigure stdout/stderr to UTF-8 so unicode math symbols print.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def slugify(s: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:limit] or "q"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--lesson", required=True)
    ap.add_argument("--default-dok", type=int, default=1)
    ap.add_argument("--source-prefix", default="", help="e.g. 'Blooket Day 3 #'")
    ap.add_argument("--tag", action="append", default=[], help="repeatable")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    existing_ids = {q["id"] for q in qb.load()}
    existing_prompts = {q["prompt"] for q in qb.load()}
    appended = 0
    skipped = 0

    with open(args.csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    # Skip the two Blooket header rows and find the first data row.
    data_rows = []
    for row in rows:
        if not row or not row[0].strip():
            continue
        if row[0].strip() == "Question #" or row[0].startswith("Blooket"):
            continue
        if not row[0].strip().isdigit():
            continue
        data_rows.append(row)

    for row in data_rows:
        qnum = row[0].strip()
        prompt = row[1].strip() if len(row) > 1 else ""
        answers = [row[i].strip() for i in (2, 3, 4, 5) if i < len(row) and row[i].strip()]
        try:
            correct = int(row[7].strip()) if len(row) > 7 and row[7].strip() else None
        except ValueError:
            correct = None

        if not prompt or prompt in existing_prompts:
            skipped += 1
            continue

        csv_stem = Path(args.csv_path).stem.lower().replace("_", "-")
        base_slug = slugify(f"{csv_stem}-q{qnum}")
        qid = f"{args.lesson}-{base_slug}"
        i = 2
        while qid in existing_ids:
            qid = f"{args.lesson}-{base_slug}-{i}"
            i += 1
        existing_ids.add(qid)

        entry = {
            "id": qid,
            "lesson": args.lesson,
            "source": f"{args.source_prefix}{qnum}" if args.source_prefix else "Blooket import",
            "page": None,
            "image": None,
            "has_visual": False,
            "prompt": prompt,
            "answers": answers,
            "correct": correct,
            "dok": args.default_dok,
            "dok_rationale": "Seeded from Blooket CSV; review and calibrate.",
            "topics": [],
            "tags": list(args.tag) + ["seeded-from-blooket"],
            "used_in": [],
            "notes": "",
            "created_at": dt.date.today().isoformat(),
        }

        if args.dry_run:
            print(entry["id"], "--", prompt[:60])
        else:
            qb.append(entry)
        appended += 1

    msg = f"{'Would append' if args.dry_run else 'Appended'} {appended}, skipped {skipped} (duplicates)."
    print(msg, file=sys.stderr)


if __name__ == "__main__":
    main()
