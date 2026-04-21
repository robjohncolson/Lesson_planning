"""Merge tagging/*_pilot.jsonl v2 fields into questionbank/registry.jsonl.

Each pilot row is a patch: looks up the id in the registry and updates the v2
fields (role, standards, prereq_ids, rehearses, echoes, skill_tokens, notes).
Non-v2 fields are left untouched. Rewrites registry.jsonl in place.

Usage:
    python merge_tags.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REGISTRY = Path("questionbank/registry.jsonl")
PILOT_DIR = Path("tagging")
V2_FIELDS = ("role", "standards", "prereq_ids", "rehearses", "echoes", "skill_tokens")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_registry() -> list[dict]:
    return [json.loads(line) for line in REGISTRY.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_pilot_patches() -> dict[str, dict]:
    patches: dict[str, dict] = {}
    # Order matters: T1 coverage (pool items, weaker tagging) loads FIRST,
    # then pilots overwrite with richer operational-spine tagging.
    patterns = ("*_t1_coverage.jsonl", "*_pilot.jsonl")
    for pattern in patterns:
        for p in sorted(PILOT_DIR.glob(pattern)):
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                # Normalize rehearses to list[str] (schema v2 requires list; early pilots used string)
                r = row.get("rehearses")
                if isinstance(r, str):
                    row["rehearses"] = [r] if r else []
                elif r is None:
                    row["rehearses"] = []
                patches[row["id"]] = {**row, "_source_file": p.name}
    return patches


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    registry = load_registry()
    patches = load_pilot_patches()

    by_id = {r["id"]: r for r in registry}
    applied = 0
    missing: list[tuple[str, str]] = []
    for pid, patch in patches.items():
        target = by_id.get(pid)
        if target is None:
            missing.append((pid, patch.get("_source_file", "?")))
            continue
        for f in V2_FIELDS:
            if f in patch:
                target[f] = patch[f]
        if patch.get("notes") and not target.get("notes"):
            target["notes"] = patch["notes"]
        applied += 1

    print(f"Patched {applied}/{len(patches)} tagged items into registry.")
    if missing:
        print(f"\n{len(missing)} pilot rows missing from registry:")
        for pid, src in missing:
            print(f"  - {pid}  (from {src})")

    if args.dry_run:
        print("(dry run — no file written)")
        return 0

    out = "\n".join(json.dumps(r, ensure_ascii=False) for r in registry) + "\n"
    REGISTRY.write_text(out, encoding="utf-8")
    print(f"Wrote {REGISTRY}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
