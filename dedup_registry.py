"""Dedup questionbank/registry.jsonl by removing X-2 duplicates of X.

For each pair (X, X-2) where both IDs exist:
  1. Verify duplicate condition: same lesson AND normalized prompts match.
  2. Pick the one to KEEP by priority:
       a. Whichever is referenced in any build_L*.py builder.
       b. Whichever has v2 fields (role / skill_tokens).
       c. If tied, keep the non-'-2' variant.
  3. Rewrite references (prereq_ids, rehearses, echoes, used_in) in registry.jsonl
     and tagging/*_pilot.jsonl to point at the kept ID.
  4. Drop the losers.
  5. Write tagging/dedup_report.md.

Usage:
    python dedup_registry.py [--dry-run]   (default: dry-run)
    python dedup_registry.py               (still dry-run unless --no-dry-run)
    python dedup_registry.py --no-dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

REGISTRY = Path("questionbank/registry.jsonl")
PILOT_DIR = Path("tagging")
REPORT = Path("tagging/dedup_report.md")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def norm(s: str) -> str:
    """Normalize whitespace + unicode for prompt comparison."""
    s = unicodedata.normalize("NFKC", s or "")
    return " ".join(s.split()).lower()


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def save_jsonl(p: Path, rows: list[dict]) -> None:
    out = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    p.write_text(out, encoding="utf-8")


def load_builder_ids() -> set[str]:
    """Return all savvas-style IDs mentioned in any build_L*.py."""
    ids: set[str] = set()
    for fn in sorted(Path(".").glob("build_L*.py")):
        content = fn.read_text(encoding="utf-8")
        # Match quoted strings containing 'savvas' or common id patterns
        matches = re.findall(r'[\"\']([0-9a-zA-Z][\w\-]+)[\"\']', content)
        for m in matches:
            if m.strip():
                ids.add(m.strip())
    return ids


def has_v2_fields(row: dict) -> bool:
    return bool(row.get("role") or row.get("skill_tokens") or row.get("standards"))


def rewrite_refs(rows: list[dict], dropped_id: str, kept_id: str) -> int:
    """Replace all references to dropped_id with kept_id. Returns count of rewrites."""
    count = 0
    REF_FIELDS = ("prereq_ids", "rehearses", "echoes", "used_in")
    for row in rows:
        for field in REF_FIELDS:
            val = row.get(field)
            if val is None:
                continue
            if isinstance(val, str):
                if val == dropped_id:
                    row[field] = kept_id
                    count += 1
            elif isinstance(val, list):
                new_list = []
                changed = False
                for item in val:
                    if item == dropped_id:
                        new_list.append(kept_id)
                        changed = True
                    else:
                        new_list.append(item)
                if changed:
                    row[field] = new_list
                    count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="Default: dry-run. Use --no-dry-run to apply.")
    ap.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    args = ap.parse_args()
    dry_run = args.dry_run

    mode_label = "DRY RUN" if dry_run else "LIVE RUN"
    print(f"=== dedup_registry.py [{mode_label}] ===")

    registry = load_jsonl(REGISTRY)
    by_id: dict[str, dict] = {r["id"]: r for r in registry}
    builder_ids = load_builder_ids()
    print(f"Registry rows: {len(registry)}")
    print(f"Builder-referenced IDs: {len(builder_ids)}")

    # Load all pilot files
    pilot_files: dict[Path, list[dict]] = {}
    for p in sorted(PILOT_DIR.glob("*_pilot.jsonl")):
        pilot_files[p] = load_jsonl(p)

    # Phase A: find candidate pairs
    candidate_pairs: list[tuple[str, str]] = []
    for row in registry:
        rid = row["id"]
        if rid.endswith("-2"):
            base = rid[:-2]
            if base in by_id:
                candidate_pairs.append((base, rid))

    print(f"Candidate -2 pairs found: {len(candidate_pairs)}")

    # Phase B: classify each pair
    dropped_rows: list[dict] = []  # rows to remove
    kept_ids: set[str] = set()
    suspicious: list[tuple[str, str, str]] = []  # (base, dup, reason)

    # Table rows for report
    report_rows: list[dict] = []

    for base_id, dup_id in candidate_pairs:
        base_row = by_id[base_id]
        dup_row = by_id[dup_id]

        # Verify condition 1: same lesson
        if base_row.get("lesson") != dup_row.get("lesson"):
            suspicious.append((base_id, dup_id, f"different lesson: {base_row.get('lesson')} vs {dup_row.get('lesson')}"))
            continue

        # Verify condition 2: normalized prompts match
        base_prompt = norm(base_row.get("prompt", ""))
        dup_prompt = norm(dup_row.get("prompt", ""))
        if base_prompt != dup_prompt:
            suspicious.append((base_id, dup_id,
                                f"prompt mismatch (base={repr(base_prompt[:60])!r}, dup={repr(dup_prompt[:60])!r})"))
            continue

        # Determine which to keep
        base_in_builders = base_id in builder_ids
        dup_in_builders = dup_id in builder_ids

        if base_in_builders and dup_in_builders:
            # Both referenced — this is ambiguous; keep base, note it
            keep, drop = base_id, dup_id
            reason = "both in builders — kept non-'-2' (base)"
        elif base_in_builders:
            keep, drop = base_id, dup_id
            reason = "base referenced in builder"
        elif dup_in_builders:
            keep, drop = dup_id, base_id
            reason = "-2 variant referenced in builder"
        else:
            # Check v2 fields
            base_v2 = has_v2_fields(base_row)
            dup_v2 = has_v2_fields(dup_row)
            if base_v2 and not dup_v2:
                keep, drop = base_id, dup_id
                reason = "base has v2 fields; -2 untagged"
            elif dup_v2 and not base_v2:
                keep, drop = dup_id, base_id
                reason = "-2 has v2 fields; base untagged"
            else:
                # Tie: keep non-'-2'
                keep, drop = base_id, dup_id
                reason = "tie — kept non-'-2' by default"

        kept_ids.add(keep)
        drop_row = by_id[drop]
        keep_row = by_id[keep]
        # Promote v2 fields from dropped row to kept row if kept is missing them
        V2_FIELDS = ("role", "standards", "prereq_ids", "rehearses", "echoes", "skill_tokens")
        promoted = []
        for f in V2_FIELDS:
            if drop_row.get(f) and not keep_row.get(f):
                keep_row[f] = drop_row[f]
                promoted.append(f)
        if drop_row.get("notes") and not keep_row.get("notes"):
            keep_row["notes"] = drop_row["notes"]
            promoted.append("notes")
        if promoted:
            reason += f" [promoted v2 fields from dropped: {', '.join(promoted)}]"

        dropped_rows.append(drop_row)
        report_rows.append({"dropped": drop, "kept": keep, "reason": reason, "rewrites": 0})

    print(f"Pairs to drop: {len(dropped_rows)}")
    print(f"Suspicious (not dropped): {len(suspicious)}")

    # Phase C: rewrite references (all in registry + pilots)
    # Do rewrites BEFORE dropping
    total_rewrites = 0
    for entry in report_rows:
        drop_id = entry["dropped"]
        keep_id = entry["kept"]
        n = rewrite_refs(registry, drop_id, keep_id)
        # Also rewrite in pilots
        for pilot_rows in pilot_files.values():
            n += rewrite_refs(pilot_rows, drop_id, keep_id)
        entry["rewrites"] = n
        total_rewrites += n

    print(f"Total reference rewrites: {total_rewrites}")

    # Phase D: build final registry (drop the losers)
    dropped_ids = {e["dropped"] for e in report_rows}
    final_registry = [r for r in registry if r["id"] not in dropped_ids]
    print(f"Registry after dedup: {len(final_registry)} rows (dropped {len(registry) - len(final_registry)})")

    # Phase E: write report
    report_lines = ["# Dedup Report\n",
                    f"Mode: **{mode_label}**\n",
                    f"Original rows: {len(registry)}  |  After dedup: {len(final_registry)}  |  Dropped: {len(dropped_ids)}\n",
                    "",
                    "## Dropped pairs\n",
                    "| dropped_id | kept_id | reason | rewrites_performed |",
                    "|---|---|---|---|"]
    for e in report_rows:
        report_lines.append(f"| `{e['dropped']}` | `{e['kept']}` | {e['reason']} | {e['rewrites']} |")

    report_lines.append("")
    if suspicious:
        report_lines.append("## Suspicious pairs (NOT dropped)\n")
        report_lines.append("| base_id | dup_id | reason |")
        report_lines.append("|---|---|---|")
        for base_id, dup_id, reason in suspicious:
            report_lines.append(f"| `{base_id}` | `{dup_id}` | {reason} |")
        report_lines.append("")

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")

    if dry_run:
        print("\n(dry run — no files modified)")
        return 0

    # Live: write registry and pilots
    save_jsonl(REGISTRY, final_registry)
    print(f"Wrote {REGISTRY}")

    for pilot_path, pilot_rows in pilot_files.items():
        save_jsonl(pilot_path, pilot_rows)
    if pilot_files:
        print(f"Rewrote {len(pilot_files)} pilot files.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
