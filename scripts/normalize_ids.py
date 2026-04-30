"""Normalize Try-It and Example registry IDs to short forms.

Default: dry-run. Use --apply to actually rewrite files.

See PLAN_normalize_ids.md for full rationale.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent

REGISTRY = ROOT / "questionbank" / "registry.jsonl"
ASSESSMENT_SHELLS = ROOT / "questionbank" / "assessment_shells.jsonl"

# Anchored regexes. Suffix is optional but, if present, must match the whitelist
# shape: -lesson-<digits-and-hyphens>(-<short alpha tag>)?
TRYIT_RE = re.compile(
    r"^([0-9]+-[0-9]+)-savvas-try-it-([0-9]+[a-z]?)(?:-lesson-[\d\-]+(?:-[a-z][a-z\-]*)?)?$"
)
EX_RE = re.compile(
    r"^([0-9]+-[0-9]+)-savvas-example-([0-9]+[a-z]?)(?:-lesson-[\d\-]+(?:-[a-z][a-z\-]*)?)?$"
)

# Broader recognizer: anything starting with `<L>-savvas-(try-it|example)-N` —
# used to flag IDs that LOOK like they should normalize but didn't fit the
# strict regex above (so a human can review them).
RECOG_RE = re.compile(
    r"^([0-9]+-[0-9]+)-savvas-(try-it|example)-([0-9]+[a-z]?)(.*)$"
)


def load_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def build_rename_map(all_ids: set[str]):
    """Return (rename_map, skipped, pattern_counts).

    rename_map: old_id -> new_id (only when regex matches AND no collision).
    skipped: list of (old_id, reason) for IDs that look like try-it/example
             but don't fit the strict regex.
    pattern_counts: Counter of which regex variant matched.
    """
    rename_map: dict[str, str] = {}
    skipped: list[tuple[str, str]] = []
    pattern_counts: Counter[str] = Counter()

    for old in all_ids:
        m = TRYIT_RE.match(old)
        if m:
            new = f"{m.group(1)}-tryit-{m.group(2)}"
            rename_map[old] = new
            # categorize variant for reporting
            if old == f"{m.group(1)}-savvas-try-it-{m.group(2)}":
                pattern_counts["tryit_bare"] += 1
            elif old == f"{m.group(1)}-savvas-try-it-{m.group(2)}-lesson-{m.group(1)}":
                pattern_counts["tryit_lesson_match"] += 1
            elif old.endswith("-matches-examp") or "matches-examp" in old:
                pattern_counts["tryit_matches_examp"] += 1
            else:
                pattern_counts["tryit_other_suffix"] += 1
            continue
        m = EX_RE.match(old)
        if m:
            new = f"{m.group(1)}-ex-{m.group(2)}"
            rename_map[old] = new
            if old == f"{m.group(1)}-savvas-example-{m.group(2)}":
                pattern_counts["ex_bare"] += 1
            elif old == f"{m.group(1)}-savvas-example-{m.group(2)}-lesson-{m.group(1)}":
                pattern_counts["ex_lesson_match"] += 1
            else:
                pattern_counts["ex_other_suffix"] += 1
            continue

        # Didn't match strict regex. If it LOOKS like a try-it/example (and is
        # not a teacher-edition addendum), record it for review.
        rec = RECOG_RE.match(old)
        if rec:
            skipped.append((old, "did not match strict regex"))

    return rename_map, skipped, pattern_counts


def detect_collisions(rename_map: dict[str, str], existing: set[str]):
    """Return list of collision messages; empty if clean."""
    collisions: list[str] = []
    new_to_old: dict[str, list[str]] = defaultdict(list)
    for old, new in rename_map.items():
        new_to_old[new].append(old)
    for new, olds in new_to_old.items():
        if len(olds) > 1:
            collisions.append(
                f"COLLISION: {len(olds)} old IDs map to '{new}': {olds}"
            )
        if new in existing and new not in rename_map:
            # The new ID exists already as a separate non-rewritten item
            collisions.append(
                f"COLLISION: '{new}' already exists in registry; "
                f"would clobber when renaming {olds}"
            )
    return collisions


def boundary_pattern(old_id: str) -> re.Pattern:
    return re.compile(r"(?<![\w\-])" + re.escape(old_id) + r"(?![\w\-])")


# ---- File rewriters ---------------------------------------------------------

def rewrite_jsonl_rows(rows: list[dict], rename_map: dict[str, str]) -> tuple[list[dict], int]:
    """Walk each row; rewrite id and any list-of-ids edge fields."""
    edge_fields = ("prereq_ids", "rehearses", "echoes", "used_in")
    changes = 0
    new_rows = []
    for row in rows:
        rid = row.get("id")
        if rid in rename_map:
            row["id"] = rename_map[rid]
            changes += 1
        for f in edge_fields:
            if f in row and isinstance(row[f], list):
                new_list = []
                for v in row[f]:
                    if isinstance(v, str) and v in rename_map:
                        new_list.append(rename_map[v])
                        changes += 1
                    else:
                        new_list.append(v)
                row[f] = new_list
        new_rows.append(row)
    return new_rows, changes


def rewrite_text_file(path: Path, rename_map: dict[str, str], sorted_olds: list[str]) -> tuple[str, int]:
    text = path.read_text(encoding="utf-8")
    total = 0
    for old in sorted_olds:
        pat = boundary_pattern(old)
        text, n = pat.subn(rename_map[old], text)
        total += n
    return text, total


def atomic_write(path: Path, content: str | bytes):
    tmp = path.with_suffix(path.suffix + ".tmp")
    if isinstance(content, bytes):
        tmp.write_bytes(content)
    else:
        tmp.write_text(content, encoding="utf-8", newline="\n")
    tmp.replace(path)


def write_jsonl(path: Path, rows: list[dict]):
    out = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    atomic_write(path, out)


# ---- File discovery ---------------------------------------------------------

def collect_text_targets() -> list[Path]:
    targets: list[Path] = []
    tex_dir = ROOT / "tex"
    if tex_dir.is_dir():
        for p in sorted(tex_dir.glob("*.tex")):
            if p.name.endswith("_regen.tex"):
                continue
            targets.append(p)
    lessons_dir = ROOT / "lessons"
    if lessons_dir.is_dir():
        for p in sorted(lessons_dir.glob("*.yaml")):
            targets.append(p)
    tagging_dir = ROOT / "tagging"
    op = tagging_dir / "operational_ids.json"
    if op.exists():
        targets.append(op)
    pilot = tagging_dir / "5-1_pilot.jsonl"
    if pilot.exists():
        targets.append(pilot)
    return targets


# ---- Main -------------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="Actually rewrite files (default: dry-run)")
    args = p.parse_args(argv)

    if not REGISTRY.exists():
        print(f"ERROR: registry not found at {REGISTRY}", file=sys.stderr)
        return 2

    registry_rows = load_jsonl(REGISTRY)
    shells_rows = load_jsonl(ASSESSMENT_SHELLS) if ASSESSMENT_SHELLS.exists() else []
    all_ids: set[str] = set()
    for r in registry_rows:
        if isinstance(r.get("id"), str):
            all_ids.add(r["id"])
    for r in shells_rows:
        if isinstance(r.get("id"), str):
            all_ids.add(r["id"])

    rename_map, skipped, pattern_counts = build_rename_map(all_ids)
    collisions = detect_collisions(rename_map, all_ids)

    print("=" * 72)
    print(f"normalize_ids.py — {'APPLY' if args.apply else 'DRY-RUN'}")
    print("=" * 72)
    print(f"Registry rows: {len(registry_rows)}")
    print(f"Assessment-shell rows: {len(shells_rows)}")
    print(f"Distinct IDs scanned: {len(all_ids)}")
    print(f"Total renames planned: {len(rename_map)}")
    print()
    print("Pattern breakdown:")
    for k, v in sorted(pattern_counts.items()):
        print(f"  {k:30s} {v}")
    print()

    # First 10 examples of each pattern
    by_pattern: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for old, new in rename_map.items():
        if "-tryit-" in new:
            by_pattern["tryit"].append((old, new))
        else:
            by_pattern["ex"].append((old, new))
    for k, lst in by_pattern.items():
        lst.sort()
        print(f"First 10 {k} renames:")
        for old, new in lst[:10]:
            print(f"  {old}  ->  {new}")
        print()

    if skipped:
        print(f"SKIPPED (looks like try-it/example but didn't fit strict regex): {len(skipped)}")
        for old, reason in skipped[:30]:
            print(f"  {old}  ({reason})")
        print()
    else:
        print("SKIPPED: 0 — every recognized try-it/example ID fit the strict regex.")
        print()

    # Spot-check: ensure no teacher-edition IDs are in the rename map
    te_in_map = [i for i in rename_map if "teacher-edition" in i or "teacher-s-edition" in i]
    print(f"Teacher-edition IDs in rename map (should be 0): {len(te_in_map)}")
    if te_in_map:
        for i in te_in_map[:10]:
            print(f"  LEAK: {i}")
    print()

    if collisions:
        print("=" * 72)
        print(f"STOP: {len(collisions)} collision(s) detected. Resolve manually.")
        print("=" * 72)
        for c in collisions:
            print(c)
        return 1

    print("Collisions: 0")
    print()

    if not args.apply:
        print("Dry-run only. Re-run with --apply to write changes.")
        return 0

    # ---- APPLY ----
    sorted_olds = sorted(rename_map.keys(), key=lambda s: -len(s))

    # 1. Registry
    new_registry, n_reg = rewrite_jsonl_rows(registry_rows, rename_map)
    write_jsonl(REGISTRY, new_registry)
    print(f"registry.jsonl: rewrote {n_reg} id/edge references")

    # 2. Assessment shells
    if shells_rows:
        new_shells, n_shells = rewrite_jsonl_rows(shells_rows, rename_map)
        write_jsonl(ASSESSMENT_SHELLS, new_shells)
        print(f"assessment_shells.jsonl: rewrote {n_shells} id/edge references")

    # 3. Text targets (tex, yaml, tagging)
    text_targets = collect_text_targets()
    file_change_count = 0
    for path in text_targets:
        new_text, n = rewrite_text_file(path, rename_map, sorted_olds)
        if n > 0:
            atomic_write(path, new_text)
            print(f"{path.relative_to(ROOT)}: {n} replacements")
            file_change_count += 1
    print(f"Total text files modified: {file_change_count}")

    # 4. Verify pass — grep for any leftover hits
    print()
    print("Verify pass: scanning for leftover old IDs...")
    leftovers = 0
    for path in [REGISTRY, ASSESSMENT_SHELLS] + text_targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old in rename_map:
            if boundary_pattern(old).search(text):
                print(f"  LEFTOVER: {old} in {path.relative_to(ROOT)}")
                leftovers += 1
    if leftovers == 0:
        print("Verify: clean (0 leftovers).")
    else:
        print(f"Verify: {leftovers} leftover hits — investigate.")
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
