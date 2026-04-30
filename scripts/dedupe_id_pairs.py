"""Dedupe `-N` re-ingest pairs in questionbank/registry.jsonl.

For each registry id `X-N` (N>=2 integer) where `X` also exists in the
registry, treat the pair as duplicates from re-ingestion. Score each row
by populated-field count, pick the highest-scoring row as the winner,
merge any unique non-empty fields the loser has, drop the loser, and
rewrite all references across registry / assessment_shells / tex / yaml /
tagging from the suffixed id -> the canonical id.

Default: dry-run. Use --apply to actually rewrite files.

See PLAN_dedupe_id_pairs.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

REGISTRY = ROOT / "questionbank" / "registry.jsonl"
ASSESSMENT_SHELLS = ROOT / "questionbank" / "assessment_shells.jsonl"

# Suffix shape: trailing "-<digits>" with N>=2.
SUFFIX_RE = re.compile(r"^(.+)-(\d+)$")

# Default scope: only Try-It and Example canonical IDs are considered re-ingest dupes.
# Other numbered IDs (concept-box-N, teacher-edition-purposefulquestio-N, etc.) are
# legitimately distinct items, NOT re-ingest dupes; require --all to touch them.
TRY_IT_RE = re.compile(
    r"^[0-9]+-[0-9]+-savvas-try-it-[0-9]+[a-z]?(-lesson-[\d-]+(-[a-z][a-z\-]*)?)?$"
)
EXAMPLE_RE = re.compile(
    r"^[0-9]+-[0-9]+-savvas-example-[0-9]+[a-z]?(-lesson-[\d-]+(-[a-z][a-z\-]*)?)?$"
)


def in_default_scope(canonical: str) -> bool:
    return bool(TRY_IT_RE.match(canonical) or EXAMPLE_RE.match(canonical))

# Fields that count as "populated" for scoring. String fields = non-empty/non-null.
SCALAR_FIELDS = (
    "prompt", "dok", "dok_rationale", "correct",
    "teacher_answer", "notes", "image",
)
# Bool field that contributes when True.
BOOL_FIELDS = ("has_visual",)
# List fields scored for non-emptiness.
LIST_FIELDS = (
    "answers", "topics", "tags", "skill_tokens",
    "standards", "prereq_ids", "rehearses", "echoes",
)
ALL_MERGE_FIELDS = SCALAR_FIELDS + BOOL_FIELDS + LIST_FIELDS


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def is_populated(row: dict, field: str) -> bool:
    if field not in row:
        return False
    v = row[field]
    if v is None:
        return False
    if field in BOOL_FIELDS:
        return bool(v)
    if field in LIST_FIELDS:
        return isinstance(v, list) and len(v) > 0
    if isinstance(v, str):
        return v.strip() != ""
    # numeric (dok / correct) — count any non-null value
    return True


def score_row(row: dict) -> int:
    return sum(1 for f in ALL_MERGE_FIELDS if is_populated(row, f))


def build_equivalence_classes(ids: set[str]) -> dict[str, list[str]]:
    """Group ids by canonical base (the id obtained by stripping ALL trailing
    `-<digits>` segments that, when stripped one at a time, still resolve to
    an id present in the set).

    Returns a map canonical_id -> [canonical_id, *suffixed_siblings] only for
    classes with size >= 2.
    """
    classes: dict[str, list[str]] = defaultdict(list)
    for i in ids:
        # Walk back to a canonical: peel `-N` while the parent exists in `ids`.
        cur = i
        while True:
            m = SUFFIX_RE.match(cur)
            if not m:
                break
            parent = m.group(1)
            if parent in ids:
                cur = parent
            else:
                break
        if cur != i or any(
            SUFFIX_RE.match(j) and SUFFIX_RE.match(j).group(1) == i and j in ids
            for j in ids
        ):
            classes[cur].append(i)
    # Ensure the canonical itself is in its class list.
    out: dict[str, list[str]] = {}
    for canonical, members in classes.items():
        full = set(members)
        full.add(canonical)
        if len(full) >= 2:
            out[canonical] = sorted(full)
    return out


def pick_winner(rows_by_id: dict[str, dict], canonical: str, members: list[str]) -> tuple[str, dict[str, int]]:
    scores = {m: score_row(rows_by_id[m]) for m in members if m in rows_by_id}
    if not scores:
        return canonical, scores
    max_score = max(scores.values())
    top = [m for m, s in scores.items() if s == max_score]
    # Tie -> canonical wins if among top; else shortest id wins.
    if canonical in top:
        return canonical, scores
    top.sort(key=lambda s: (len(s), s))
    return top[0], scores


def merge_fields(winner_row: dict, loser_rows: list[dict]) -> list[str]:
    """Copy non-empty fields from losers into winner where winner is empty.
    Returns a list of field names that were merged in.
    """
    merged: list[str] = []
    for field in ALL_MERGE_FIELDS:
        if is_populated(winner_row, field):
            continue
        for loser in loser_rows:
            if is_populated(loser, field):
                winner_row[field] = loser[field]
                merged.append(field)
                break
    return merged


def boundary_pattern(old_id: str) -> re.Pattern:
    return re.compile(r"(?<![\w\-])" + re.escape(old_id) + r"(?![\w\-])")


def rewrite_jsonl_rows(rows: list[dict], rename_map: dict[str, str], drop_ids: set[str]) -> tuple[list[dict], int, int]:
    """Drop rows whose id is in drop_ids; rename ids and edge-list refs.
    Returns (new_rows, n_id_renamed, n_edge_refs_rewritten).
    """
    edge_fields = ("prereq_ids", "rehearses", "echoes", "used_in")
    n_id = 0
    n_edge = 0
    new_rows: list[dict] = []
    for row in rows:
        rid = row.get("id")
        if isinstance(rid, str) and rid in drop_ids:
            continue
        if isinstance(rid, str) and rid in rename_map:
            row["id"] = rename_map[rid]
            n_id += 1
        for f in edge_fields:
            if f in row and isinstance(row[f], list):
                new_list = []
                for v in row[f]:
                    if isinstance(v, str) and v in rename_map:
                        new_list.append(rename_map[v])
                        n_edge += 1
                    else:
                        new_list.append(v)
                row[f] = new_list
        new_rows.append(row)
    return new_rows, n_id, n_edge


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


def classify_target(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("tex/"):
        return "tex"
    if rel.startswith("lessons/"):
        return "yaml"
    if rel.startswith("tagging/"):
        return "tagging"
    return "other"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Dedupe `-N` re-ingest pairs. Default scope: only Try-It and Example "
            "canonical IDs (the real re-ingest collisions). Use --all to consider "
            "EVERY equivalence class — DANGEROUS: this will likely drop legitimately "
            "distinct numbered items (concept-box-1..12, teacher-edition-purposefulquestio-1..8, "
            "etc.) which are NOT re-ingest dupes."
        )
    )
    p.add_argument("--apply", action="store_true",
                   help="Actually rewrite files (default: dry-run)")
    p.add_argument("--all", action="store_true",
                   help="Consider ALL equivalence classes, not just Try-It/Example "
                        "(dangerous — see description)")
    args = p.parse_args(argv)

    if not REGISTRY.exists():
        print(f"ERROR: registry not found at {REGISTRY}", file=sys.stderr)
        return 2

    registry_rows = load_jsonl(REGISTRY)
    shells_rows = load_jsonl(ASSESSMENT_SHELLS) if ASSESSMENT_SHELLS.exists() else []

    rows_by_id: dict[str, dict] = {}
    for r in registry_rows:
        rid = r.get("id")
        if isinstance(rid, str):
            # If duplicate-literal id, keep first occurrence (seed.py's
            # last-write-wins is a separate problem — don't touch here).
            rows_by_id.setdefault(rid, r)

    all_ids = set(rows_by_id.keys())
    for r in shells_rows:
        rid = r.get("id")
        if isinstance(rid, str):
            all_ids.add(rid)

    classes = build_equivalence_classes(all_ids)

    print("=" * 72)
    print(f"dedupe_id_pairs.py - {'APPLY' if args.apply else 'DRY-RUN'}")
    print("=" * 72)
    print(f"Registry rows (unique ids):    {len(rows_by_id)}")
    print(f"Assessment-shell rows:         {len(shells_rows)}")
    print(f"Distinct IDs scanned:          {len(all_ids)}")
    print(f"Equivalence classes (size>=2): {len(classes)}")
    print()

    rename_map: dict[str, str] = {}   # losing-or-suffixed id -> winner canonical id
    drop_ids: set[str] = set()         # registry rows to remove
    pair_details: list[dict] = []      # for reporting
    classes_skipped_no_row: list[str] = []
    classes_skipped_out_of_scope: list[str] = []

    for canonical in sorted(classes.keys()):
        members = classes[canonical]
        # Default-scope filter: skip classes whose canonical isn't a Try-It/Example.
        if not args.all and not in_default_scope(canonical):
            classes_skipped_out_of_scope.append(canonical)
            continue
        # Only consider members that have actual rows in the registry; if all
        # references are in shells/tex only, skip (we have nothing to merge).
        registry_members = [m for m in members if m in rows_by_id]
        if len(registry_members) < 2:
            classes_skipped_no_row.append(canonical)
            continue

        winner_id, scores = pick_winner(rows_by_id, canonical, registry_members)
        loser_ids = [m for m in registry_members if m != winner_id]
        loser_rows = [rows_by_id[lid] for lid in loser_ids]
        winner_row = rows_by_id[winner_id]

        merged_fields = merge_fields(winner_row, loser_rows)

        # The winner's row will live under `canonical` after dedupe.
        # Build rename map for ALL non-canonical members (and the winner, if it
        # was a suffixed id) -> canonical.
        for m in members:
            if m == canonical:
                continue
            rename_map[m] = canonical
        # If winner was suffixed, also drop the canonical id row only if it's
        # present and is one of the losers (it is, by construction).
        for lid in loser_ids:
            drop_ids.add(lid)

        pair_details.append({
            "canonical": canonical,
            "members": members,
            "scores": scores,
            "winner": winner_id,
            "losers": loser_ids,
            "merged_fields": merged_fields,
        })

    # Sample of 5 pairs in detail.
    print("Sample pair details (first 5):")
    print("-" * 72)
    for d in pair_details[:5]:
        print(f"  canonical : {d['canonical']}")
        print(f"  members   : {d['members']}")
        print(f"  scores    : {d['scores']}")
        print(f"  winner    : {d['winner']}  (writes under id={d['canonical']})")
        print(f"  losers    : {d['losers']}")
        print(f"  merged in : {d['merged_fields'] or '(none — winner already complete)'}")
        print()

    # Summary stats.
    n_classes = len(pair_details)
    n_drop = len(drop_ids)
    triples = [d for d in pair_details if len(d["members"]) > 2]
    winner_was_canonical = sum(1 for d in pair_details if d["winner"] == d["canonical"])
    winner_was_suffixed = n_classes - winner_was_canonical
    needs_rename_winner = sum(
        1 for d in pair_details if d["winner"] != d["canonical"]
    )

    print(f"Classes (>= 2 members with rows): {n_classes}")
    print(f"Classes with >2 members (triple+): {len(triples)}")
    if triples:
        print("  triples sample:")
        for d in triples[:8]:
            print(f"    {d['canonical']} -> {d['members']}")
        print()
    print(f"Rows that would be DROPPED:       {n_drop}")
    print(f"Winner was canonical:             {winner_was_canonical}")
    print(f"Winner was suffixed (gets renamed to canonical): {winner_was_suffixed}")
    print(f"Classes skipped (no registry row): {len(classes_skipped_no_row)}")
    if not args.all:
        print(f"Skipped {len(classes_skipped_out_of_scope)} classes "
              f"(concept-box / teacher-edition / etc.) - outside Try-It/Example scope")
    print()

    # Now compute reference rewrite counts for each file class.
    sorted_olds = sorted(rename_map.keys(), key=lambda s: -len(s))

    # Registry edges (we'll count via a dry pass).
    _, n_reg_id, n_reg_edge = rewrite_jsonl_rows(
        [json.loads(json.dumps(r)) for r in registry_rows],  # deep copy
        rename_map, drop_ids,
    )
    # Assessment shells.
    _, n_shells_id, n_shells_edge = rewrite_jsonl_rows(
        [json.loads(json.dumps(r)) for r in shells_rows],
        rename_map, set(),  # never drop shell rows
    )

    # Text files by class.
    text_targets = collect_text_targets()
    text_counts: dict[str, int] = defaultdict(int)
    text_files_changed: dict[str, int] = defaultdict(int)
    for path in text_targets:
        _, n = rewrite_text_file(path, rename_map, sorted_olds)
        cls = classify_target(path)
        if n > 0:
            text_counts[cls] += n
            text_files_changed[cls] += 1

    print("Reference rewrites that would occur:")
    print(f"  registry.jsonl id renames:        {n_reg_id}")
    print(f"  registry.jsonl edge refs:         {n_reg_edge}")
    print(f"  assessment_shells.jsonl id:       {n_shells_id}")
    print(f"  assessment_shells.jsonl edges:    {n_shells_edge}")
    for cls in ("tex", "yaml", "tagging"):
        print(f"  {cls:30s} refs: {text_counts.get(cls, 0):5d}  ({text_files_changed.get(cls, 0)} files)")
    print()

    if not args.apply:
        print("Dry-run only. Re-run with --apply to write changes.")
        return 0

    # ---- APPLY ----
    print("=" * 72)
    print("APPLYING")
    print("=" * 72)

    new_registry, n_reg_id_a, n_reg_edge_a = rewrite_jsonl_rows(
        registry_rows, rename_map, drop_ids,
    )
    write_jsonl(REGISTRY, new_registry)
    print(f"registry.jsonl: dropped {n_drop} rows, renamed {n_reg_id_a} ids, rewrote {n_reg_edge_a} edge refs")

    if shells_rows:
        new_shells, n_sh_id_a, n_sh_edge_a = rewrite_jsonl_rows(
            shells_rows, rename_map, set(),
        )
        write_jsonl(ASSESSMENT_SHELLS, new_shells)
        print(f"assessment_shells.jsonl: renamed {n_sh_id_a} ids, rewrote {n_sh_edge_a} edge refs")

    files_modified = 0
    for path in text_targets:
        new_text, n = rewrite_text_file(path, rename_map, sorted_olds)
        if n > 0:
            atomic_write(path, new_text)
            print(f"{path.relative_to(ROOT)}: {n} replacements")
            files_modified += 1
    print(f"Text files modified: {files_modified}")

    # Verify pass — grep for any leftover hits of dropped/suffixed ids.
    print()
    print("Verify pass: scanning for leftover suffixed IDs...")
    leftovers = 0
    for path in [REGISTRY, ASSESSMENT_SHELLS] + text_targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old in rename_map:
            if old == rename_map[old]:
                continue
            # Use boundary search to avoid false positives where `old` is a
            # prefix of an unrelated id.
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
