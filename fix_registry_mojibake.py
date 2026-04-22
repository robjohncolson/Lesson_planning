"""One-shot pass: run ftfy.fix_text over every prompt/answer in
questionbank/registry.jsonl. Reports a per-row diff list, writes the cleaned
file, and leaves a backup at registry.jsonl.bak so the change can be reverted.

Usage:  python fix_registry_mojibake.py [--apply]

Without --apply, runs in dry-run mode and prints the changes only.
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from pathlib import Path

import ftfy

REGISTRY = Path(__file__).parent / "questionbank" / "registry.jsonl"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def fix_row(row: dict) -> tuple[dict, list[tuple[str, str, str]]]:
    """Return (fixed_row, diffs) where diffs is [(field, before_snippet, after_snippet)]."""
    diffs: list[tuple[str, str, str]] = []
    fixed = dict(row)
    for field in ("prompt",):
        v = row.get(field)
        if isinstance(v, str):
            fv = ftfy.fix_text(v)
            if fv != v:
                diffs.append((field, _snip(v), _snip(fv)))
                fixed[field] = fv
    answers = row.get("answers")
    if isinstance(answers, list):
        new_ans = []
        any_changed = False
        for a in answers:
            if isinstance(a, str):
                fa = ftfy.fix_text(a)
                if fa != a:
                    any_changed = True
                    diffs.append(("answers", _snip(a), _snip(fa)))
                new_ans.append(fa)
            else:
                new_ans.append(a)
        if any_changed:
            fixed["answers"] = new_ans
    return fixed, diffs


def _snip(s: str, n: int = 80) -> str:
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = p.parse_args()

    rows: list[dict] = []
    with REGISTRY.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    changed_rows: list[tuple[str, list]] = []
    fixed_rows: list[dict] = []
    for row in rows:
        fixed, diffs = fix_row(row)
        fixed_rows.append(fixed)
        if diffs:
            changed_rows.append((row.get("id", "?"), diffs))

    print(f"Registry: {len(rows)} rows total, {len(changed_rows)} need fixing.")
    for rid, diffs in changed_rows:
        print(f"\n  {rid}:")
        for field, before, after in diffs:
            print(f"    [{field}]")
            print(f"      - {before}")
            print(f"      + {after}")

    if not args.apply:
        print("\n(dry-run; pass --apply to write)")
        return 0

    backup = REGISTRY.with_suffix(REGISTRY.suffix + ".bak")
    shutil.copyfile(REGISTRY, backup)
    print(f"\nBackup → {backup.name}")
    with REGISTRY.open("w", encoding="utf-8", newline="\n") as f:
        for row in fixed_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote cleaned {REGISTRY.name} ({len(fixed_rows)} rows).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
