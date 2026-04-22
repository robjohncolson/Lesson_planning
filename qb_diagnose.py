"""qb_diagnose.py — Curriculum DAG diagnostics.

Reads:
  - questionbank/registry.jsonl (post-dedup)
  - questionbank/assessment_shells.jsonl
  - tagging/*_pilot.jsonl (operational-spine tags)
  - tagging/*_t1_coverage.jsonl (pool tags from Phase 2)

Emits three reports under graph/:
  1. graph/skill_bridge_gaps.md
  2. graph/nominal_rehearsals.md
  3. graph/redundant_practice.md

Pure-read. Never modifies registry or tag files.

Usage:
    python qb_diagnose.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REGISTRY = Path("questionbank/registry.jsonl")
SHELLS = Path("questionbank/assessment_shells.jsonl")
TAGGING = Path("tagging")
GRAPH = Path("graph")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_all_tags() -> dict[str, dict]:
    """Load all v2 patches: pilot files + t1_coverage files, keyed by ID.

    Later files override earlier ones (coverage adds, doesn't overwrite pilots).
    """
    patches: dict[str, dict] = {}
    # Pilot files first (operational spine)
    for p in sorted(TAGGING.glob("*_pilot.jsonl")):
        for row in load_jsonl(p):
            patches[row["id"]] = row
    # Coverage files (pool items — won't overlap with pilots if Phase 2 filtered correctly)
    for p in sorted(TAGGING.glob("*_t1_coverage.jsonl")):
        for row in load_jsonl(p):
            if row["id"] not in patches:  # don't overwrite operational spine
                patches[row["id"]] = row
    return patches


def build_unified_registry(registry: list[dict], patches: dict[str, dict]) -> list[dict]:
    """Return registry with v2 fields applied from patches (in memory only)."""
    V2_FIELDS = ("role", "standards", "prereq_ids", "rehearses", "echoes", "skill_tokens")
    result = []
    for row in registry:
        merged = dict(row)
        patch = patches.get(row["id"])
        if patch:
            for f in V2_FIELDS:
                if f in patch:
                    merged[f] = patch[f]
            if patch.get("notes") and not merged.get("notes"):
                merged["notes"] = patch["notes"]
        result.append(merged)
    return result


def token_set(row: dict) -> frozenset[str]:
    return frozenset(row.get("skill_tokens") or [])


def main() -> int:
    GRAPH.mkdir(exist_ok=True)

    registry_raw = load_jsonl(REGISTRY)
    shells = load_jsonl(SHELLS)
    patches = load_all_tags()

    # Build a merged in-memory view (does NOT write registry)
    registry = build_unified_registry(registry_raw, patches)

    # Index
    all_items = registry + shells
    by_id: dict[str, dict] = {r["id"]: r for r in all_items}

    tagged = [r for r in registry if r.get("role") or r.get("skill_tokens") or r.get("standards")]
    shell_by_id = {s["id"]: s for s in shells}

    print(f"Registry: {len(registry)} rows, {len(tagged)} tagged (merged view), {len(shells)} assessment shells.")

    # -------------------------------------------------------------------------
    # Report 1: skill_bridge_gaps.md
    # Per lesson: any skill_token in a dok3-driver that does NOT appear in any
    # earlier-role item (do-now-*, launch-model-*, explore-tps, explore-practice)
    # in the SAME lesson.
    # -------------------------------------------------------------------------

    EARLIER_ROLES = {"do-now-bridge", "do-now-explore", "launch-model-1", "launch-model-2",
                     "explore-tps", "explore-practice"}

    lessons = sorted({r.get("lesson", "") for r in tagged if r.get("lesson")})

    bridge_lines: list[str] = ["# Skill Bridge Gaps\n",
                               "Per lesson: skill_tokens on dok3-driver items that have NO earlier-role item "
                               "(do-now, launch, explore-tps, or explore-practice) providing that token in the same lesson.\n"]

    total_gaps = 0
    for lesson in lessons:
        lesson_items = [r for r in tagged if r.get("lesson") == lesson]
        drivers = [r for r in lesson_items if r.get("role") == "dok3-driver"]
        if not drivers:
            continue

        # Tokens covered by earlier-role items
        earlier_tokens: set[str] = set()
        for r in lesson_items:
            if r.get("role") in EARLIER_ROLES:
                earlier_tokens.update(token_set(r))

        # Pool items for this lesson (any role — for candidate recommendations)
        pool_by_token: dict[str, list[str]] = defaultdict(list)
        for r in lesson_items:
            for tok in token_set(r):
                pool_by_token[tok].append(r["id"])

        # Also include items from coverage (they're already merged in)
        # Items from OTHER lessons that have tokens (for cross-lesson recommendations if needed)
        # (Not needed for this report)

        lesson_gap_lines: list[str] = []
        for driver in drivers:
            driver_tokens = token_set(driver)
            gaps = driver_tokens - earlier_tokens
            if gaps:
                lesson_gap_lines.append(f"\n### DOK-3: `{driver['id']}`\n")
                for gap_tok in sorted(gaps):
                    total_gaps += 1
                    # Candidates: same lesson items with this token, NOT the driver itself
                    cands = [iid for iid in pool_by_token.get(gap_tok, [])
                             if iid != driver["id"]]
                    cand_str = ", ".join(f"`{c}`" for c in cands[:5]) if cands else "_none in this lesson_"
                    lesson_gap_lines.append(
                        f"- DOK-3 uses `{gap_tok}` but no earlier-role item in {lesson} exercises it.")
                    lesson_gap_lines.append(
                        f"  Candidates from pool: [{cand_str}]")

        if lesson_gap_lines:
            bridge_lines.append(f"\n## Lesson {lesson}\n")
            bridge_lines.extend(lesson_gap_lines)

    if total_gaps == 0:
        bridge_lines.append("\n_No bridge gaps found. All dok3-driver tokens are covered by earlier-role items._\n")
    else:
        bridge_lines.insert(2, f"**Total gaps: {total_gaps}** across {len(lessons)} lessons.\n")

    gap_path = GRAPH / "skill_bridge_gaps.md"
    gap_path.write_text("\n".join(bridge_lines), encoding="utf-8")
    print(f"Wrote {gap_path}  ({total_gaps} gaps)")

    # -------------------------------------------------------------------------
    # Report 2: nominal_rehearsals.md
    # Per item with rehearses field: check skill_token overlap with the
    # assessment shell's skill_tokens. Emit mismatches.
    # -------------------------------------------------------------------------

    rehearsal_lines: list[str] = ["# Nominal Rehearsals\n",
                                  "Items tagged with `rehearses: [...]` whose skill_tokens do NOT overlap "
                                  "with the target assessment shell's tokens. A non-overlapping rehearsal "
                                  "is 'nominal' — it claims to prepare students for an assessment skill "
                                  "it doesn't actually exercise.\n"]

    mismatch_count = 0
    match_count = 0
    for r in tagged:
        rehearses = r.get("rehearses")
        if not rehearses:
            continue
        if isinstance(rehearses, str):
            rehearses = [rehearses]
        for target_id in (rehearses if isinstance(rehearses, list) else [rehearses]):
            if not target_id:
                continue
            target = shell_by_id.get(target_id)
            if not target:
                # Target is not an assessment shell — skip (it's a prereq chain, not rehearsal)
                continue
            item_tokens = token_set(r)
            target_tokens = token_set(target)
            overlap = item_tokens & target_tokens
            if overlap:
                match_count += 1
            else:
                mismatch_count += 1
                rehearsal_lines.append(
                    f"\n- `{r['id']}` rehearses `{target_id}` but token overlap is empty.")
                rehearsal_lines.append(
                    f"  Item tokens: {sorted(item_tokens)}")
                rehearsal_lines.append(
                    f"  Assessment tokens: {sorted(target_tokens)}")

    if mismatch_count == 0 and match_count == 0:
        rehearsal_lines.append(
            "\n_No rehearsal edges found pointing to assessment shells. Check that rehearses fields point at shell IDs._\n")
    elif mismatch_count == 0:
        rehearsal_lines.append(
            f"\n_All {match_count} rehearsal edges have token overlap — no mismatches._\n")
    else:
        rehearsal_lines.insert(2,
            f"**{mismatch_count} mismatched rehearsals** (no token overlap). "
            f"{match_count} well-aligned rehearsals.\n")

    rehearsal_path = GRAPH / "nominal_rehearsals.md"
    rehearsal_path.write_text("\n".join(rehearsal_lines), encoding="utf-8")
    print(f"Wrote {rehearsal_path}  ({mismatch_count} mismatches, {match_count} good)")

    # -------------------------------------------------------------------------
    # Report 3: redundant_practice.md
    # Per lesson: explore-practice / explore-tps items with IDENTICAL skill_token
    # sets (not just overlapping). Emit as candidate-drop lists.
    # For each redundant group, suggest a pool replacement that adds tokens
    # needed by the lesson's dok3-driver but missing from the redundant group.
    # -------------------------------------------------------------------------

    PRACTICE_ROLES = {"explore-practice", "explore-tps"}

    redundant_lines: list[str] = ["# Redundant Practice\n",
                                  "Per lesson: explore-practice and explore-tps items with IDENTICAL "
                                  "skill_token sets **AND** matching `prereq_ids` chain **AND** matching "
                                  "`rehearses` targets. Items sharing tokens but scaffolded from different "
                                  "Try-Its or rehearsing different assessment items are NOT grouped — they "
                                  "serve distinct pedagogical roles.\n"]

    total_redundant_groups = 0

    for lesson in lessons:
        lesson_items = [r for r in tagged if r.get("lesson") == lesson]
        practice_items = [r for r in lesson_items if r.get("role") in PRACTICE_ROLES]

        # Find DOK-3 driver tokens for this lesson
        driver_tokens: set[str] = set()
        for r in lesson_items:
            if r.get("role") == "dok3-driver":
                driver_tokens.update(token_set(r))

        # Group by (token_set, prereq chain, rehearses targets). Items with same
        # tokens but different scaffolding parents or different assessment targets
        # serve distinct purposes and must not be grouped.
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for r in practice_items:
            tset = token_set(r)
            if not tset:  # skip items with no tokens (teacher-edition etc.)
                continue
            prereq = tuple(sorted(r.get("prereq_ids") or []))
            rehearses_list = r.get("rehearses") or []
            if isinstance(rehearses_list, str):
                rehearses_list = [rehearses_list]
            rehearses_key = tuple(sorted(rehearses_list))
            groups[(tset, prereq, rehearses_key)].append(r)

        lesson_redundant: list[str] = []
        for (tset, prereq_key, rehearses_key), group in groups.items():
            if len(group) < 2:
                continue
            total_redundant_groups += 1
            lesson_redundant.append(f"\nRedundant group (same tokens: {sorted(tset)}):")
            if prereq_key:
                lesson_redundant.append(
                    f"  Shared prereq chain: {list(prereq_key)}")
            if rehearses_key:
                lesson_redundant.append(
                    f"  Shared rehearses target: {list(rehearses_key)}")
            for item in group:
                lesson_redundant.append(f"- `{item['id']}` [{', '.join(sorted(token_set(item)))}]")
            lesson_redundant.append(f"Suggestion: keep 1, drop {len(group) - 1}.")

            # Candidate replacements: pool items in same lesson NOT in this group
            # that add dok3-needed tokens
            needed_tokens = driver_tokens - tset
            if needed_tokens:
                candidates: list[tuple[str, set[str]]] = []
                for r in lesson_items:
                    if r["id"] in {item["id"] for item in group}:
                        continue
                    if r.get("role") in PRACTICE_ROLES:
                        added = token_set(r) & needed_tokens
                        if added:
                            candidates.append((r["id"], added))
                if candidates:
                    lesson_redundant.append(
                        f"Candidate replacement from pool (adds DOK-3-needed tokens):")
                    for cand_id, added in sorted(candidates, key=lambda x: -len(x[1]))[:3]:
                        lesson_redundant.append(
                            f"  - `{cand_id}` adds {sorted(added)}")
                else:
                    lesson_redundant.append(
                        f"No pool replacement found with needed tokens {sorted(needed_tokens)}.")

        if lesson_redundant:
            redundant_lines.append(f"\n## Lesson {lesson}\n")
            redundant_lines.extend(lesson_redundant)

    if total_redundant_groups == 0:
        redundant_lines.append(
            "\n_No redundant practice groups found. All token sets are unique._\n")
    else:
        redundant_lines.insert(2,
            f"**{total_redundant_groups} redundant group(s)** found across {len(lessons)} lessons.\n")

    redundant_path = GRAPH / "redundant_practice.md"
    redundant_path.write_text("\n".join(redundant_lines), encoding="utf-8")
    print(f"Wrote {redundant_path}  ({total_redundant_groups} redundant groups)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
