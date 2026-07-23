#!/usr/bin/env python3
"""
build_collision_review_queue.py

Generates a human-review queue for the 85 ambiguous legacy-ID collisions
identified by the (closed, frozen) dedup workstream.

READS (read-only, never written to):
  - questionbank/registry.jsonl
  - inventory/dedup/item_uid_alias_map.json

WRITES (under inventory/review-queue/ only):
  - collision_review_queue.json
  - COLLISION_REVIEW_QUEUE.md
  - README.md

This script performs NO merges. Both item_uids in every ambiguous group
remain live and resolvable; every recommendation produced here is advisory
only. Run from the repo root:

    python inventory/review-queue/build_collision_review_queue.py

Deterministic / byte-stable: same two source files in -> same three output
files out (aside from the generated_at_utc timestamp field in the JSON meta).
"""

import difflib
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "questionbank" / "registry.jsonl"
ALIAS_MAP_PATH = REPO_ROOT / "inventory" / "dedup" / "item_uid_alias_map.json"
OUT_DIR = REPO_ROOT / "inventory" / "review-queue"

JSON_OUT_PATH = OUT_DIR / "collision_review_queue.json"
MD_OUT_PATH = OUT_DIR / "COLLISION_REVIEW_QUEUE.md"
README_OUT_PATH = OUT_DIR / "README.md"

LESSON_ORDER = ["5-1", "5-4", "5-5"]
CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2}


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# Drift-tag helpers
# ---------------------------------------------------------------------------

def tag_trailing_standards(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    if na == nb:
        return False
    stripped_a = re.sub(r"\s*MP\.\d+\s*", " ", na).strip()
    stripped_b = re.sub(r"\s*MP\.\d+\s*", " ", nb).strip()
    return stripped_a == stripped_b


def tag_whitespace_or_spacing(a: str, b: str) -> bool:
    return norm(a) == norm(b) and a != b


def tag_circ_spacing(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    if na == nb:
        return False
    ca = re.sub(r"\s*\\circ\s*", r"\\circ", na)
    cb = re.sub(r"\s*\\circ\s*", r"\\circ", nb)
    return ca == cb


def tag_subset_relation(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    if na == nb:
        return False
    return (na in nb) or (nb in na)


def visual_signature(s: str):
    return (
        "\\placeholder" in s,
        "[IMAGE" in s,
        ("[GRAPH" in s or "TIKZ" in s),
    )


def tag_visual_encoding(a: str, b: str) -> bool:
    return visual_signature(a) != visual_signature(b)


def tag_latex_formatting(a: str, b: str) -> bool:
    return (("\\frac" in a) != ("\\frac" in b)) or ((")/(" in a) != (")/(" in b))


def compute_drift_tags(a: str, b: str):
    tags = []
    is_trailing_standards = tag_trailing_standards(a, b)
    # subset_relation is redundant when the entire subset gap is explained by
    # a dropped trailing MP.x tag -- suppress it there so drift display and
    # rationale agree; genuine stem-omission cases (no tag involved) keep it.
    if tag_subset_relation(a, b) and not is_trailing_standards:
        tags.append("subset_relation")
    if is_trailing_standards:
        tags.append("trailing_standards_tag")
    if tag_whitespace_or_spacing(a, b):
        tags.append("whitespace_or_spacing")
    if tag_circ_spacing(a, b):
        tags.append("circ_spacing")
    if tag_visual_encoding(a, b):
        tags.append("visual_encoding")
    if tag_latex_formatting(a, b):
        tags.append("latex_formatting")
    if not tags:
        tags.append("other_textual")
    return tags


# ---------------------------------------------------------------------------
# Recommendation ladder (deterministic, advisory only)
# ---------------------------------------------------------------------------

def recommend(legacy_id: str, a: str, b: str, uid_a: str, uid_b: str, drift_tags):
    la, lb = len(a), len(b)

    if "trailing_standards_tag" in drift_tags:
        # Keep whichever capture actually contains an MP.x tag.
        a_has_tag = bool(re.search(r"MP\.\d+", a))
        if a_has_tag and not bool(re.search(r"MP\.\d+", b)):
            keep, other, keep_label = uid_a, uid_b, "A"
        else:
            keep, other, keep_label = uid_b, uid_a, "B"
        rationale = (
            "Identical item; drifted capture dropped the trailing standards tag "
            f"(MP.x) -- keep the tagged/complete capture ({keep_label})."
        )
        return keep, other, rationale, "high"

    if "subset_relation" in drift_tags:
        if lb > la:
            keep, other, keep_label, other_label = uid_b, uid_a, "B", "A"
        else:
            keep, other, keep_label, other_label = uid_a, uid_b, "A", "B"
        rationale = (
            f"Capture {keep_label} is the full item; the other is missing the "
            "instruction stem it prepends -- keep the complete capture."
        )
        return keep, other, rationale, "high"

    if "whitespace_or_spacing" in drift_tags or "circ_spacing" in drift_tags:
        if lb > la:
            keep, other, keep_label = uid_b, uid_a, "B"
        else:
            keep, other, keep_label = uid_a, uid_b, "A"
        rationale = (
            "Cosmetic drift only (whitespace/\\circ spacing); text is identical "
            f"after normalization -- either is acceptable, suggested keep is the "
            f"{keep_label} capture; reviewer's call."
        )
        return keep, other, rationale, "low"

    # Substantive drift: visual_encoding / latex_formatting / other_textual
    if lb > la:
        keep, other, keep_label = uid_b, uid_a, "B"
    else:
        keep, other, keep_label = uid_a, uid_b, "A"

    if "visual_encoding" in drift_tags:
        rationale = (
            "Captures differ in how the visual is encoded (\\placeholder vs "
            "[IMAGE:]/[GRAPH/TIKZ]) -- suggested keep is the longer capture; "
            "reviewer confirm which visual form the pipeline wants."
        )
    elif "latex_formatting" in drift_tags:
        rationale = (
            "Captures differ in LaTeX formatting (e.g. \\frac vs (a)/(b)); "
            "suggested keep is the longer/cleaner capture."
        )
    else:
        rationale = (
            "Same slot re-captured with textual drift; suggested keep is the "
            "more complete (longer) capture."
        )
    return keep, other, rationale, "medium"


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def md_table_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", "<br>")


def visible_whitespace(s: str) -> str:
    """Make whitespace legible in a markdown bullet: spaces -> middot."""
    return s.replace(" ", "·").replace("\n", "↵")


def render_inline_ops_md(inline_ops):
    lines = []
    for op in inline_ops:
        kind = op["op"]
        a_txt = visible_whitespace(op["a"])
        b_txt = visible_whitespace(op["b"])
        if kind == "replace":
            lines.append(f'- replace: A has "{a_txt}" where B has "{b_txt}"')
        elif kind == "delete":
            lines.append(f'- delete: A has extra "{a_txt}"')
        elif kind == "insert":
            lines.append(f'- insert: B adds "{b_txt}"')
    return lines


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not REGISTRY_PATH.exists():
        sys.exit(f"ABORT: registry not found at {REGISTRY_PATH}")
    if not ALIAS_MAP_PATH.exists():
        sys.exit(f"ABORT: alias map not found at {ALIAS_MAP_PATH}")

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        raw = f.read()
    raw_lines = raw.split("\n")
    nonempty_rows = [l for l in raw_lines if l.strip()]

    if len(nonempty_rows) != 900:
        sys.exit(
            f"ABORT: expected 900 non-empty registry rows, found {len(nonempty_rows)}"
        )

    with open(ALIAS_MAP_PATH, encoding="utf-8") as f:
        alias_data = json.load(f)

    meta_in = alias_data["meta"]
    alias_map = alias_data["alias_map"]
    dispositions = alias_data["dispositions"]

    if meta_in.get("total_rows") != 900:
        sys.exit("ABORT: alias map meta.total_rows != 900")
    if meta_in.get("unique_legacy_ids") != 815:
        sys.exit("ABORT: alias map meta.unique_legacy_ids != 815")
    if meta_in.get("ambiguous_legacy_ids") != 85:
        sys.exit("ABORT: alias map meta.ambiguous_legacy_ids != 85")

    ambiguous_ids = sorted(
        [lid for lid, entry in alias_map.items() if entry.get("ambiguous")]
    )
    if len(ambiguous_ids) != 85:
        sys.exit(f"ABORT: expected 85 ambiguous legacy ids, found {len(ambiguous_ids)}")

    disp_keys = set(dispositions.keys())
    ambiguous_set = set(ambiguous_ids)
    if disp_keys != ambiguous_set:
        sys.exit("ABORT: dispositions key set does not match ambiguous alias_map entries")
    if not all(v == "merge-candidate" for v in dispositions.values()):
        sys.exit("ABORT: not all dispositions == 'merge-candidate'")

    sha_checks = 0
    groups = []

    for legacy_id in ambiguous_ids:
        entry = alias_map[legacy_id]
        uids = entry["item_uids"]
        if len(uids) != 2:
            sys.exit(f"ABORT: {legacy_id} does not have exactly 2 item_uids")

        # ascending registry_line order -> A = smaller, B = larger
        ordered = sorted(uids, key=lambda u: u["registry_line"])
        cap_a_meta, cap_b_meta = ordered[0], ordered[1]

        if cap_a_meta["lesson"] != cap_b_meta["lesson"]:
            sys.exit(f"ABORT: {legacy_id} captures have different lessons")
        if cap_a_meta["source"] != cap_b_meta["source"]:
            sys.exit(f"ABORT: {legacy_id} captures have different sources")

        lesson = cap_a_meta["lesson"]
        source = cap_a_meta["source"]

        captures = {}
        for label, cap_meta in (("A", cap_a_meta), ("B", cap_b_meta)):
            line_no = cap_meta["registry_line"]
            row = json.loads(nonempty_rows[line_no - 1])

            if row.get("id") != legacy_id:
                sys.exit(
                    f"ABORT: {legacy_id} capture {label}: registry line {line_no} "
                    f"id mismatch (got {row.get('id')!r})"
                )
            prompt = row.get("prompt")
            if prompt is None:
                sys.exit(f"ABORT: {legacy_id} capture {label}: prompt is null")

            computed_sha1 = sha1_text(prompt)
            if computed_sha1 != cap_meta["prompt_sha1"]:
                sys.exit(
                    f"ABORT: {legacy_id} capture {label}: prompt_sha1 mismatch "
                    f"(line {line_no})"
                )
            sha_checks += 1

            captures[label] = {
                "item_uid": cap_meta["item_uid"],
                "registry_line": line_no,
                "prompt_sha1": cap_meta["prompt_sha1"],
                "prompt": prompt,
                "length": len(prompt),
            }

        prompt_a = captures["A"]["prompt"]
        prompt_b = captures["B"]["prompt"]

        similarity_ratio = round(
            difflib.SequenceMatcher(None, prompt_a, prompt_b).ratio(), 4
        )
        opcodes = difflib.SequenceMatcher(None, prompt_a, prompt_b).get_opcodes()
        inline_ops = [
            {"op": tag, "a": prompt_a[i1:i2], "b": prompt_b[j1:j2]}
            for tag, i1, i2, j1, j2 in opcodes
            if tag != "equal"
        ]

        drift_tags = compute_drift_tags(prompt_a, prompt_b)

        canonical_keep, drifted_duplicate, rationale, confidence = recommend(
            legacy_id,
            prompt_a,
            prompt_b,
            captures["A"]["item_uid"],
            captures["B"]["item_uid"],
            drift_tags,
        )

        groups.append(
            {
                "legacy_id": legacy_id,
                "lesson": lesson,
                "source": source,
                "disposition": "merge-candidate",
                "capture_a": captures["A"],
                "capture_b": captures["B"],
                "diff": {
                    "similarity_ratio": similarity_ratio,
                    "drift_tags": drift_tags,
                    "inline_ops": inline_ops,
                },
                "recommendation": {
                    "canonical_keep": canonical_keep,
                    "drifted_duplicate": drifted_duplicate,
                    "rationale": rationale,
                    "confidence": confidence,
                },
                "both_item_uids_retained": True,
            }
        )

    expected_sha_checks = 85 * 2
    if sha_checks != expected_sha_checks:
        sys.exit(
            f"ABORT: expected {expected_sha_checks} sha1 verifications, did {sha_checks}"
        )

    # Sort groups: lesson asc (in LESSON_ORDER), confidence high>medium>low, legacy_id asc
    def sort_key(g):
        lesson_idx = LESSON_ORDER.index(g["lesson"]) if g["lesson"] in LESSON_ORDER else 999
        conf_rank = CONFIDENCE_RANK.get(g["recommendation"]["confidence"], 99)
        return (lesson_idx, conf_rank, g["legacy_id"])

    groups.sort(key=sort_key)

    per_lesson_counts = {}
    for lesson in LESSON_ORDER:
        per_lesson_counts[lesson] = sum(1 for g in groups if g["lesson"] == lesson)

    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    for g in groups:
        confidence_dist[g["recommendation"]["confidence"]] += 1

    if per_lesson_counts != {"5-1": 32, "5-4": 29, "5-5": 24}:
        sys.exit(f"ABORT: per-lesson counts mismatch: {per_lesson_counts}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    registry_sha256 = sha256_of_file(REGISTRY_PATH)
    alias_map_sha256 = sha256_of_file(ALIAS_MAP_PATH)

    json_meta = {
        "generated_from": [
            "questionbank/registry.jsonl",
            "inventory/dedup/item_uid_alias_map.json",
        ],
        "total_registry_rows": 900,
        "unique_legacy_ids": 815,
        "distinct_item_uids": 900,
        "ambiguous_legacy_ids": 85,
        "exact_duplicate_rows": 0,
        "group_count": len(groups),
        "per_lesson_counts": per_lesson_counts,
        "recommendation_confidence_distribution": confidence_dist,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "guarantee": (
            "advisory only -- never auto-merge; both item_uids retained for "
            "every group"
        ),
        "source_sha256": {
            "registry.jsonl": registry_sha256,
            "item_uid_alias_map.json": alias_map_sha256,
        },
    }

    json_out = {"meta": json_meta, "groups": groups}

    with open(JSON_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(json_out, ensure_ascii=False, indent=2))

    # -------------------------------------------------------------------
    # COLLISION_REVIEW_QUEUE.md
    # -------------------------------------------------------------------
    md_lines = []
    md_lines.append("# Collision Review Queue")
    md_lines.append("")
    md_lines.append(
        "This queue lists the 85 legacy question-bank IDs from lessons 5-1, "
        "5-4, and 5-5 that the (closed, frozen) dedup workstream flagged as "
        "**ambiguous**: one legacy id resolved to two distinct `item_uid`s "
        "because the item was captured twice with slight textual drift "
        "(\"double-ingest-with-drift\")."
    )
    md_lines.append(
        "**Nothing here merges anything.** Both `item_uid`s for every group "
        "below remain live in the registry. The \"suggested canonical keep\" "
        "is an advisory recommendation only -- a human (the teacher) makes "
        "the final call using the checkboxes at the end of each group."
    )
    md_lines.append(
        "Confidence is assigned by a deterministic ladder: **high** = the "
        "drift is a clear completeness gap (one capture is missing an "
        "instruction stem or a standards tag like `MP.3`); **medium** = "
        "substantive drift (visual encoding, LaTeX formatting, or other "
        "textual differences) where the longer capture is suggested but "
        "review matters more; **low** = cosmetic-only drift (whitespace or "
        "`\\circ` spacing) where the two captures are identical after "
        "normalization."
    )
    md_lines.append(
        "Groups are organized by lesson (5-1, then 5-4, then 5-5), and "
        "within each lesson ordered by confidence (high to low)."
    )
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append("| Lesson | Groups |")
    md_lines.append("|---|---|")
    for lesson in LESSON_ORDER:
        md_lines.append(f"| {lesson} | {per_lesson_counts[lesson]} |")
    md_lines.append(f"| **Total** | **{len(groups)}** |")
    md_lines.append("")
    md_lines.append("| Confidence | Groups |")
    md_lines.append("|---|---|")
    md_lines.append(f"| high | {confidence_dist['high']} |")
    md_lines.append(f"| medium | {confidence_dist['medium']} |")
    md_lines.append(f"| low | {confidence_dist['low']} |")
    md_lines.append("")

    for lesson in LESSON_ORDER:
        lesson_groups = [g for g in groups if g["lesson"] == lesson]
        md_lines.append(f"## Lesson {lesson}")
        md_lines.append("")
        md_lines.append(f"{len(lesson_groups)} ambiguous groups in this lesson.")
        md_lines.append("")

        for g in lesson_groups:
            legacy_id = g["legacy_id"]
            cap_a = g["capture_a"]
            cap_b = g["capture_b"]
            diff = g["diff"]
            rec = g["recommendation"]

            md_lines.append(f"### {legacy_id}")
            md_lines.append("")
            md_lines.append(f"Source: {g['source']}")
            md_lines.append(
                f"Capture A = `{cap_a['item_uid']}` (line {cap_a['registry_line']}) "
                f"&middot; Capture B = `{cap_b['item_uid']}` (line {cap_b['registry_line']})"
            )
            md_lines.append(
                "Both item_uids are retained -- nothing is merged."
            )
            md_lines.append("")

            md_lines.append("**Side-by-side prompts**")
            md_lines.append("")
            md_lines.append(
                f"| Capture A (line {cap_a['registry_line']}) | "
                f"Capture B (line {cap_b['registry_line']}) |"
            )
            md_lines.append("|---|---|")
            md_lines.append(
                f"| {md_table_escape(cap_a['prompt'])} | {md_table_escape(cap_b['prompt'])} |"
            )
            md_lines.append("")

            md_lines.append("**Diff (exact)**")
            md_lines.append("")
            op_lines = render_inline_ops_md(diff["inline_ops"])
            if op_lines:
                md_lines.extend(op_lines)
            else:
                md_lines.append("- (no character-level differences)")
            md_lines.append(f"- similarity: {diff['similarity_ratio']}")
            md_lines.append(f"- drift: {', '.join(diff['drift_tags'])}")
            md_lines.append("")

            keep_label = "A" if rec["canonical_keep"] == cap_a["item_uid"] else "B"
            other_label = "B" if keep_label == "A" else "A"
            md_lines.append("**Recommendation**")
            md_lines.append("")
            md_lines.append(
                f"Suggested canonical keep: **Capture {keep_label}** "
                f"(`{rec['canonical_keep']}`). Flagged drifted duplicate: "
                f"Capture {other_label} (`{rec['drifted_duplicate']}`). "
                f"Confidence: {rec['confidence']}. Rationale: {rec['rationale']}"
            )
            md_lines.append(
                "Advisory -- final decision is the teacher's; both uids stay "
                "live until the teacher acts."
            )
            md_lines.append("")

            md_lines.append("**Decision**")
            md_lines.append("")
            md_lines.append("- [ ] Keep Capture A as canonical, retire B")
            md_lines.append("- [ ] Keep Capture B as canonical, retire A")
            md_lines.append("- [ ] Keep BOTH (distinct items)")
            md_lines.append("- [ ] Other / needs SME")
            md_lines.append("- Notes: ____")
            md_lines.append("")

    with open(MD_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    # -------------------------------------------------------------------
    # README.md
    # -------------------------------------------------------------------
    readme_lines = []
    readme_lines.append("# Collision Review Queue -- README")
    readme_lines.append("")
    readme_lines.append("## What this is")
    readme_lines.append("")
    readme_lines.append(
        "The (closed, frozen) dedup workstream identified 85 legacy question-"
        "bank IDs, all in lessons 5-1, 5-4, and 5-5, that each resolve to two "
        "distinct `item_uid`s in `questionbank/registry.jsonl` -- a "
        "\"double-ingest-with-drift\" pattern where the same source item was "
        "captured twice, with small textual differences between the two "
        "captures. This directory builds a practical, human-workable review "
        "queue over those 85 groups so a teacher (or reviewer) can look at "
        "both captures side by side and decide what, if anything, to do."
    )
    readme_lines.append("")
    readme_lines.append("## Files")
    readme_lines.append("")
    readme_lines.append(
        "- `build_collision_review_queue.py` -- the generator. Reads the two "
        "read-only sources below and writes the three deliverables. "
        "Deterministic and reproducible."
    )
    readme_lines.append(
        "- `collision_review_queue.json` -- 85 machine-readable records, "
        "sorted by lesson then confidence then legacy id. Use this for "
        "tooling, spreadsheets, or further sorting/filtering."
    )
    readme_lines.append(
        "- `COLLISION_REVIEW_QUEUE.md` -- the human-workable queue. Open "
        "this file to work through the 85 groups by hand: each group shows "
        "both full prompts side by side, an exact character-level diff, a "
        "suggested (advisory) recommendation, and a checkbox block to record "
        "the actual decision."
    )
    readme_lines.append(
        "- `README.md` -- this file."
    )
    readme_lines.append("")
    readme_lines.append("## NEVER-AUTO-MERGE GUARANTEE")
    readme_lines.append("")
    readme_lines.append(
        "**Nothing in this workstream merges, collapses, renumbers, or "
        "deletes any registry row or item_uid.** Both distinct item_uids for "
        "every one of the 85 groups remain live and resolvable in "
        "`questionbank/registry.jsonl` exactly as they were before this "
        "queue was built. The \"canonical keep\" recommendation attached to "
        "each group is **advisory only** -- it is a suggestion for which "
        "capture is likely the cleaner/more complete one, not an action "
        "taken. The teacher makes the final merge/keep-both decision, "
        "recorded via the checkboxes in `COLLISION_REVIEW_QUEUE.md`. "
        "`questionbank/registry.jsonl` and everything under "
        "`inventory/dedup/` are read-only inputs to this workstream and are "
        "byte-unchanged by it."
    )
    readme_lines.append("")
    readme_lines.append("## How the recommendation and confidence are computed")
    readme_lines.append("")
    readme_lines.append(
        "For each group, the two captures (A = lower registry line, B = "
        "higher registry line) are compared with Python's stdlib "
        "`difflib.SequenceMatcher` on the raw prompt text, producing a "
        "similarity ratio and the exact non-equal character-level opcodes. "
        "A set of drift tags is then computed (subset relation, trailing "
        "`MP.x` standards tag, whitespace/`\\circ` spacing, differing visual "
        "encoding, differing LaTeX formatting, or generic textual drift). A "
        "fixed, deterministic ladder picks the recommendation from these "
        "tags, in this priority order:"
    )
    readme_lines.append("")
    readme_lines.append(
        "1. **trailing_standards_tag** (captures are identical except one "
        "carries a trailing `MP.x` tag) -> keep the tagged capture. "
        "Confidence: high."
    )
    readme_lines.append(
        "2. **subset_relation** (one capture's normalized text is fully "
        "contained in the other's, and the gap is NOT just a dropped `MP.x` "
        "tag) -> keep the longer/complete capture. Confidence: high."
    )
    readme_lines.append(
        "3. **whitespace_or_spacing / circ_spacing** (captures are identical "
        "once whitespace is normalized) -> cosmetic only; suggested keep is "
        "the longer capture. Confidence: low."
    )
    readme_lines.append(
        "4. Otherwise, substantive drift (visual_encoding / "
        "latex_formatting / other_textual) -> suggested keep is the longer "
        "capture as the richer/more-complete one. Confidence: medium."
    )
    readme_lines.append("")
    readme_lines.append(
        "**A \"high\" confidence recommendation still requires human "
        "confirmation.** Confidence describes how mechanically clear-cut the "
        "drift pattern is, not a green light to act automatically -- no step "
        "in this workstream ever merges anything on its own."
    )
    readme_lines.append("")
    readme_lines.append("## How to regenerate")
    readme_lines.append("")
    readme_lines.append("From the repo root:")
    readme_lines.append("")
    readme_lines.append("```")
    readme_lines.append("python inventory/review-queue/build_collision_review_queue.py")
    readme_lines.append("```")
    readme_lines.append("")
    readme_lines.append(
        "The generator reads `questionbank/registry.jsonl` and "
        "`inventory/dedup/item_uid_alias_map.json` read-only (never opened "
        "for writing) and re-writes the three files listed above. Output is "
        "reproducible/byte-stable aside from the `generated_at_utc` "
        "timestamp in the JSON meta block."
    )
    readme_lines.append("")
    readme_lines.append("## Reconciliation")
    readme_lines.append("")
    readme_lines.append(
        "900 registry rows / 815 unique legacy ids / 85 ambiguous groups. "
        "`group_count` in `collision_review_queue.json` must equal 85 -- the "
        "generator aborts before writing any output if this (or any other "
        "consistency check) fails."
    )

    with open(README_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(readme_lines) + "\n")

    # -------------------------------------------------------------------
    # Self-check stdout
    # -------------------------------------------------------------------
    print(f"GROUPS: {len(groups)}")
    print(
        "PER-LESSON COUNTS: "
        + ", ".join(f"{lesson}={per_lesson_counts[lesson]}" for lesson in LESSON_ORDER)
    )
    print(
        "CONFIDENCE DISTRIBUTION: "
        + ", ".join(f"{k}={v}" for k, v in confidence_dist.items())
    )
    print(f"SHA MATCH: all {sha_checks} prompt hashes verified OK")
    print(
        "RECONCILES TO DEDUP MAP: "
        f"{meta_in['total_rows']}/{meta_in['unique_legacy_ids']}/"
        f"{meta_in['ambiguous_legacy_ids']} = PASS"
    )
    print("WROTE:")
    print(f"  {JSON_OUT_PATH}")
    print(f"  {MD_OUT_PATH}")
    print(f"  {README_OUT_PATH}")


if __name__ == "__main__":
    main()
