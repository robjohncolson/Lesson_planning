"""Emit per-builder polish worksheets under graph/polish/.

Consolidates the three diagnostic reports (skill_bridge_gaps, nominal_rehearsals,
redundant_practice) into one markdown per builder, filtered to the items that
builder actually uses. Ends each worksheet with a concrete "proposed builder
edit" block — Python-list shaped, hand-apply only.

Usage:  python qb_polish_worksheet.py
Writes: graph/polish/L{NN}_P{N}.md for every builder in tagging/operational_ids.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
OPERATIONAL = ROOT / "tagging" / "operational_ids.json"
GRAPH = ROOT / "graph"
POLISH = GRAPH / "polish"
GAPS = GRAPH / "skill_bridge_gaps.md"
NOMINAL = GRAPH / "nominal_rehearsals.md"
REDUNDANT = GRAPH / "redundant_practice.md"


def builder_to_lesson(name: str) -> tuple[str, str]:
    """`build_L41_P1_packets.py` -> ('4-1', 'P1')."""
    m = re.match(r"build_L(\d)(\d)_P(\d)_packets\.py", name)
    if not m:
        raise ValueError(f"Unexpected builder name: {name}")
    return f"{m.group(1)}-{m.group(2)}", f"P{m.group(3)}"


# ---- Report parsers -----------------------------------------------------
# Each returns a dict keyed by lesson ('4-1') of structured blocks.


def parse_gaps(text: str) -> dict[str, list[dict]]:
    """Returns {lesson: [{'dok3_id': str, 'gaps': [(token, [candidates])]}]}."""
    out: dict[str, list[dict]] = {}
    lesson = None
    entry = None
    for line in text.splitlines():
        m_lesson = re.match(r"## Lesson (\S+)", line)
        if m_lesson:
            lesson = m_lesson.group(1)
            out.setdefault(lesson, [])
            entry = None
            continue
        m_dok3 = re.match(r"### DOK-3: `([^`]+)`", line)
        if m_dok3 and lesson is not None:
            entry = {"dok3_id": m_dok3.group(1), "gaps": []}
            out[lesson].append(entry)
            continue
        m_gap = re.match(
            r"- DOK-3 uses `([^`]+)` but no earlier-role item in \S+ exercises it\.",
            line,
        )
        if m_gap and entry is not None:
            entry["gaps"].append({"token": m_gap.group(1), "candidates": []})
            continue
        m_cand = re.match(r"\s*Candidates from pool: \[(.*)\]", line)
        if m_cand and entry is not None and entry["gaps"]:
            raw = m_cand.group(1).strip()
            if raw and "none" not in raw:
                entry["gaps"][-1]["candidates"] = re.findall(r"`([^`]+)`", raw)
    return out


def parse_nominal(text: str) -> list[dict]:
    """Returns list of {'item_id', 'target', 'item_tokens', 'target_tokens'}."""
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(
            r"- `([^`]+)` rehearses `([^`]+)` but token overlap is empty\.", lines[i]
        )
        if m:
            entry = {"item_id": m.group(1), "target": m.group(2)}
            # look ahead for item/assessment tokens
            for j in range(i + 1, min(i + 5, len(lines))):
                mi = re.match(r"\s*Item tokens: (\[.*\])", lines[j])
                ma = re.match(r"\s*Assessment tokens: (\[.*\])", lines[j])
                if mi:
                    entry["item_tokens"] = mi.group(1)
                if ma:
                    entry["target_tokens"] = ma.group(1)
            out.append(entry)
        i += 1
    return out


def parse_redundant(text: str) -> dict[str, list[dict]]:
    """Returns {lesson: [{'tokens', 'items': [id], 'drop_count', 'replacements': [(id, tokens_added)]}]}."""
    out: dict[str, list[dict]] = {}
    lesson = None
    group = None
    in_candidates = False
    for line in text.splitlines():
        m_lesson = re.match(r"## Lesson (\S+)", line)
        if m_lesson:
            lesson = m_lesson.group(1)
            out.setdefault(lesson, [])
            group = None
            continue
        m_grp = re.match(r"Redundant group \(same tokens: \[([^\]]*)\]\):", line)
        if m_grp and lesson is not None:
            group = {
                "tokens": [t.strip().strip("'") for t in m_grp.group(1).split(",") if t.strip()],
                "items": [],
                "drop_count": 0,
                "replacements": [],
                "no_replacement": False,
            }
            out[lesson].append(group)
            in_candidates = False
            continue
        if group is None:
            continue
        m_item = re.match(r"- `([^`]+)` \[", line)
        if m_item and not in_candidates:
            group["items"].append(m_item.group(1))
            continue
        m_sugg = re.match(r"Suggestion: keep 1, drop (\d+)\.", line)
        if m_sugg:
            group["drop_count"] = int(m_sugg.group(1))
            continue
        if re.match(r"Candidate replacement", line):
            in_candidates = True
            continue
        if re.match(r"No pool replacement", line):
            group["no_replacement"] = True
            continue
        m_rep = re.match(r"\s*- `([^`]+)` adds \[([^\]]*)\]", line)
        if m_rep and in_candidates:
            tokens = [t.strip().strip("'") for t in m_rep.group(2).split(",") if t.strip()]
            group["replacements"].append((m_rep.group(1), tokens))
    return out


# ---- Worksheet emission --------------------------------------------------


def collect_builder_ids(builder_ids: dict) -> set[str]:
    """Flatten all ID lists for a builder into one set."""
    ids = set()
    for key, vals in builder_ids.items():
        if isinstance(vals, list):
            ids.update(vals)
    return ids


def format_id_lists(builder_ids: dict) -> str:
    lines = []
    for key in ("DO_NOW_IDS", "LAUNCH_IDS", "EXPLORE_IDS", "PRACTICE_IDS",
               "REINFORCE_IDS", "DOK3_ID", "DOK3_PAIR_ID"):
        if key in builder_ids:
            lines.append(f"- `{key}` ({len(builder_ids[key])}): {', '.join(f'`{x}`' for x in builder_ids[key])}")
    return "\n".join(lines)


def emit_worksheet(builder: str, info: dict,
                   gaps_by_lesson: dict,
                   nominals: list[dict],
                   redundant_by_lesson: dict) -> str:
    lesson, period = builder_to_lesson(builder)
    ids = info["ids"]
    builder_ids_flat = collect_builder_ids(ids)
    dok3 = set(ids.get("DOK3_ID", []) + ids.get("DOK3_PAIR_ID", []))

    out = [f"# Polish Worksheet — L{lesson.replace('-','')}_{period} ({builder})",
           "",
           f"Lesson: **{lesson}**  ·  Period: **{period}**  ·  Generated by `qb_polish_worksheet.py`",
           ""]

    # Current operational items
    out.append("## Current operational items")
    out.append("")
    out.append(format_id_lists(ids) or "_(none)_")
    out.append("")

    # --- Skill-bridge gaps scoped to this period's DOK-3 ---
    out.append("## Skill-bridge gaps")
    out.append("")
    period_gap_entries = [
        e for e in gaps_by_lesson.get(lesson, [])
        if e["dok3_id"] in dok3
    ]
    if not dok3:
        out.append("_No DOK-3 driver in this period — gap check skipped._")
        out.append("")
    elif not period_gap_entries:
        out.append("_No gaps for this period's DOK-3 driver._")
        out.append("")
    else:
        # dedup entries (report sometimes emits duplicates)
        seen = set()
        for e in period_gap_entries:
            key = e["dok3_id"]
            if key in seen:
                continue
            seen.add(key)
            out.append(f"**DOK-3 driver:** `{e['dok3_id']}`")
            out.append("")
            for g in e["gaps"]:
                cands = g["candidates"]
                cand_str = ", ".join(f"`{c}`" for c in cands) if cands else "_none in pool_"
                out.append(f"- Missing token: `{g['token']}`  ·  pool candidates: {cand_str}")
            out.append("")

    # --- Nominal rehearsals touching this period ---
    out.append("## Nominal rehearsals")
    out.append("")
    period_nominals = [n for n in nominals if n["item_id"] in builder_ids_flat]
    if not period_nominals:
        out.append("_No nominal rehearsals on this period's items._")
    else:
        for n in period_nominals:
            out.append(f"- `{n['item_id']}` rehearses `{n['target']}` but tokens don't overlap.")
            out.append(f"  - Item: {n.get('item_tokens', '?')}")
            out.append(f"  - Assessment: {n.get('target_tokens', '?')}")
    out.append("")

    # --- Redundancy groups touching this period ---
    out.append("## Redundant practice groups")
    out.append("")
    period_groups = []
    for g in redundant_by_lesson.get(lesson, []):
        touching = [x for x in g["items"] if x in builder_ids_flat]
        if touching:
            period_groups.append((g, touching))
    if not period_groups:
        out.append("_No redundancy affecting this period._")
        out.append("")
    else:
        for g, touching in period_groups:
            tokens = ", ".join(f"`{t}`" for t in g["tokens"])
            out.append(f"**Tokens:** {tokens}")
            out.append("")
            out.append(f"Group members (🟢 = in this period):")
            for item in g["items"]:
                marker = "🟢" if item in builder_ids_flat else "  "
                out.append(f"- {marker} `{item}`")
            out.append(f"- _Keep 1, drop {g['drop_count']}._")
            if g["replacements"]:
                out.append("")
                out.append("  Pool replacements (add DOK-3-needed tokens):")
                for rid, rtok in g["replacements"]:
                    tokstr = ", ".join(f"`{t}`" for t in rtok)
                    out.append(f"    - `{rid}` adds [{tokstr}]")
            elif g["no_replacement"]:
                out.append("")
                out.append("  _No pool replacement covers the DOK-3 needs._")
            out.append("")

    # --- Proposed builder edits ---
    out.append("## Proposed builder edit")
    out.append("")
    edits = propose_edits(ids, period_gap_entries, period_groups, period_nominals)
    if not edits:
        out.append("_No edits proposed — this period looks clean._")
    else:
        out.append("```python")
        out.extend(edits)
        out.append("```")
    out.append("")
    out.append("---")
    out.append("")
    out.append("**Workflow:** read · accept/reject each swap · hand-edit the builder · rebuild packet · re-run `merge_tags.py && qb_graph.py && qb_diagnose.py` · regenerate this worksheet.")
    out.append("")
    return "\n".join(out)


def propose_edits(ids: dict, gap_entries: list[dict],
                  redundant_groups: list[tuple],
                  nominals: list[dict]) -> list[str]:
    """Emit Python-shaped comments describing swaps, no auto-apply."""
    lines: list[str] = []

    # Gap-fill suggestions: for each gap with a pool candidate, propose adding
    # to EXPLORE_IDS (or PRACTICE_IDS if that's where the builder puts things).
    explore_key = next((k for k in ("EXPLORE_IDS", "PRACTICE_IDS") if k in ids), None)
    for e in gap_entries:
        for g in e["gaps"]:
            if g["candidates"]:
                for cand in g["candidates"]:
                    if cand in collect_builder_ids(ids):
                        continue
                    if explore_key:
                        lines.append(
                            f"# ADD to {explore_key}: '{cand}'  "
                            f"# fills gap `{g['token']}` for DOK-3 {e['dok3_id']}"
                        )

    # Redundancy resolution: find items in the period that are in redundant
    # groups, suggest dropping the extras and replacing with pool items.
    for g, touching in redundant_groups:
        # de-dup within `touching` (registry has duplicate-ID rows in Topic 5)
        seen_t = []
        for t in touching:
            if t not in seen_t:
                seen_t.append(t)
        if len(seen_t) <= 1:
            continue  # only one *distinct* period item, not locally redundant
        keep = seen_t[0]
        drops = seen_t[1:]
        for d in drops:
            # Figure out which key it's in
            drop_key = None
            for k, v in ids.items():
                if isinstance(v, list) and d in v:
                    drop_key = k
                    break
            lines.append(
                f"# DROP from {drop_key or '?'}: '{d}'  "
                f"# redundant with '{keep}' (same tokens)"
            )
        if g["replacements"]:
            rid, rtok = g["replacements"][0]
            if rid not in collect_builder_ids(ids) and explore_key:
                tokstr = ", ".join(rtok)
                lines.append(
                    f"# ADD to {explore_key}: '{rid}'  "
                    f"# covers needed tokens [{tokstr}]"
                )

    # Nominal rehearsals — flag, don't auto-resolve
    for n in nominals:
        lines.append(
            f"# REVIEW: '{n['item_id']}' claims to rehearse {n['target']} but no token overlap — "
            f"retag or replace."
        )
    return lines


def main() -> None:
    POLISH.mkdir(parents=True, exist_ok=True)

    with OPERATIONAL.open("r", encoding="utf-8") as f:
        operational = json.load(f)

    gaps_by_lesson = parse_gaps(GAPS.read_text(encoding="utf-8"))
    nominals = parse_nominal(NOMINAL.read_text(encoding="utf-8"))
    redundant_by_lesson = parse_redundant(REDUNDANT.read_text(encoding="utf-8"))

    written = []
    for builder, info in sorted(operational.items()):
        lesson, period = builder_to_lesson(builder)
        fname = f"L{lesson.replace('-','')}_{period}.md"
        out_path = POLISH / fname
        content = emit_worksheet(builder, info, gaps_by_lesson, nominals, redundant_by_lesson)
        out_path.write_text(content, encoding="utf-8")
        written.append(fname)

    print(f"Wrote {len(written)} polish worksheets to {POLISH.relative_to(ROOT)}/:")
    for f in written:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
