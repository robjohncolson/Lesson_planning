"""Append one or more validated question entries to the registry.

Takes JSON on stdin (either a single object or a JSON array of objects),
validates required fields and lesson calibration existence, assigns a
stable id if one is not provided, and appends to registry.jsonl.

Used by the Claude-Code ingestion workflow: after Claude reads a
screenshot and drafts a JSON stub, pipe the stub through this script
to commit it to the registry.

Usage:
    echo '{"lesson":"3-5","prompt":"...","answers":[...],"correct":1,"dok":2,...}' | python qb_append.py
    python qb_append.py stub.json
    python qb_append.py < stub.json   # same thing

Flags:
    --dry-run   validate + print id assignments; do not write
    --force     skip duplicate-prompt detection
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import qb

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

REQUIRED = {"lesson", "prompt", "dok"}


def slugify(s: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:limit] or "q"


def ensure_calibration(lesson: str) -> None:
    if not qb.load_calibration(lesson):
        raise SystemExit(
            f"ERROR: no calibration at questionbank/calibration/{lesson}.json. "
            "Populate Savvas DOK anchors for this lesson first."
        )


def assign_id(entry: dict, taken: set[str]) -> str:
    if entry.get("id"):
        return entry["id"]
    lesson = entry["lesson"]
    hint = entry.get("source") or entry.get("prompt", "q")[:40]
    base = f"{lesson}-{slugify(hint)}"
    candidate = base
    i = 2
    while candidate in taken:
        candidate = f"{base}-{i}"
        i += 1
    return candidate


def validate(entry: dict) -> None:
    missing = REQUIRED - entry.keys()
    if missing:
        raise SystemExit(f"ERROR: missing required fields: {sorted(missing)}")
    if entry["dok"] not in (1, 2, 3, 4):
        raise SystemExit(f"ERROR: dok must be 1/2/3/4, got {entry['dok']!r}")
    if entry.get("answers") and not isinstance(entry["answers"], list):
        raise SystemExit("ERROR: answers must be a list")
    if entry.get("correct") is not None and isinstance(entry["correct"], int):
        n = len(entry.get("answers", []))
        if n and not (1 <= entry["correct"] <= n):
            raise SystemExit(f"ERROR: correct={entry['correct']} out of range for {n} answers")


def normalize(entry: dict, taken: set[str], existing_prompts: set[str], force: bool) -> dict | None:
    validate(entry)
    ensure_calibration(entry["lesson"])
    if not force and entry["prompt"] in existing_prompts:
        print(f"skip (duplicate prompt): {entry['prompt'][:60]}", file=sys.stderr)
        return None

    out = {
        "id": assign_id(entry, taken),
        "lesson": entry["lesson"],
        "source": entry.get("source", ""),
        "page": entry.get("page"),
        "image": entry.get("image"),
        "has_visual": bool(entry.get("has_visual", False)),
        "prompt": entry["prompt"],
        "answers": entry.get("answers", []),
        "correct": entry.get("correct"),
        "dok": int(entry["dok"]),
        "dok_rationale": entry.get("dok_rationale", ""),
        "topics": entry.get("topics", []),
        "tags": entry.get("tags", []),
        "used_in": entry.get("used_in", []),
        "notes": entry.get("notes", ""),
        "created_at": entry.get("created_at") or dt.date.today().isoformat(),
    }
    taken.add(out["id"])
    existing_prompts.add(out["prompt"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="JSON file path; if omitted, read stdin")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="ignore duplicate-prompt check")
    args = ap.parse_args()

    raw = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    data = json.loads(raw)
    entries = data if isinstance(data, list) else [data]

    existing = qb.load()
    taken = {q["id"] for q in existing}
    prompts = {q["prompt"] for q in existing}

    appended = []
    for e in entries:
        norm = normalize(e, taken, prompts, args.force)
        if norm is None:
            continue
        appended.append(norm)

    for entry in appended:
        print(f"{'(dry)' if args.dry_run else 'append'} {entry['id']}  dok={entry['dok']}  {entry['prompt'][:50]}")
        if not args.dry_run:
            qb.append(entry)

    print(f"{'Would append' if args.dry_run else 'Appended'} {len(appended)}.", file=sys.stderr)


if __name__ == "__main__":
    main()
