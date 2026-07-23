#!/usr/bin/env python3
"""
build_course_map.py

Builds course_map.json for WS5 (Algebra 2 course-map deliverable).

READ-ONLY on all sources:
  - questionbank/registry.jsonl
  - questionbank/calibration/{lesson}.json
  - questionbank/assessment_shells.jsonl
  - inventory/dedup/item_uid_alias_map.json  (WS-dedup canonical-identity map)
  - graph/skill_bridge_gaps.md, graph/chains.md (not parsed here; used for the
    human-readable COURSE_MAP.md / prereq_gaps.md deliverables written alongside
    this script's output)

WRITES ONLY: inventory/course-map/course_map.json

Deterministic: no randomness, no wall-clock-dependent ordering (only the
`generated_at` timestamp varies between runs). Ends with `assert` self-checks
against the manager-supplied / dedup-workstream-supplied ground-truth numbers;
if any assert fails this script raises and produces no (or a clearly wrong)
file rather than silently adjusting the numbers.

--------------------------------------------------------------------------
NODE IDENTITY (revised per Codex integration-gate Finding 1, HIGH):
--------------------------------------------------------------------------
`registry.jsonl` has 900 rows but only 815 UNIQUE `id` strings — 85 legacy
ids are each shared by 2 rows with DIFFERING content (all within a single
lesson: 5-1, 5-4, or 5-5; verified no cross-lesson collisions). Keying tree
nodes by `item.id` would silently collapse those 85 pairs. Every node is now
keyed by the opaque `item_uid` from `inventory/dedup/item_uid_alias_map.json`
(one per registry row/line, always unique); `legacy_id` is kept as a
possibly-ambiguous human-readable alias.

Edge target resolution: a resolved edge's SOURCE is always an exact known
row (so `source_uid` is always unambiguous). Its TARGET is a legacy-id
string parsed out of `prereq_ids`/`rehearses`/`echoes` — if that legacy id
is one of the 85 ambiguous ones, the edge cannot be pinned to either
candidate item_uid (no target prompt to disambiguate against), so it is
flagged `target_ambiguous=true` with both candidate uids listed, rather than
silently attached to one. `target_lesson`/`cross_unit` remain computable
even for ambiguous targets because every ambiguous id's two occurrences sit
in the SAME lesson (verified below) — the ambiguity is which of the two
lesson-mates is meant, never which lesson.

--------------------------------------------------------------------------
DROPPED-EDGE RECLASSIFICATION (Finding 2, MEDIUM):
--------------------------------------------------------------------------
4-1 is RETIRED-pending-teacher-revival (WS1: calibrated, then pulled from the
registry), not a never-built front-of-year lesson like 3-1. Dropped edges
targeting 4-1 are now reason "retirement-gap"; only the genuinely
never-yet-built target (3-1) keeps "frontload-gap".
"""

import json
import re
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "questionbank" / "registry.jsonl"
CALIBRATION_DIR = REPO_ROOT / "questionbank" / "calibration"
ASSESSMENT_SHELLS_PATH = REPO_ROOT / "questionbank" / "assessment_shells.jsonl"
ALIAS_MAP_PATH = REPO_ROOT / "inventory" / "dedup" / "item_uid_alias_map.json"
DUP_REMEDIATION_REF = "inventory/dedup/DUPLICATE_ID_REMEDIATION.md"
OUT_PATH = Path(__file__).resolve().parent / "course_map.json"

LESSON_PREFIX_RE = re.compile(r"^\d-\d")

# ---------------------------------------------------------------------------
# Canonical structure (given by spec — 6 topics, 37 lessons)
# ---------------------------------------------------------------------------

TOPIC_TITLES = {
    1: "Linear Functions and Systems (inferred — front-of-year)",
    2: "Quadratic Functions and Complex Numbers (inferred — front-of-year)",
    3: "Polynomial Functions",
    4: "Rational Functions and Inverse Variation",
    5: "Rational Exponents and Radical Functions",
    6: "Exponential and Logarithmic Functions",
}

TOPIC_LESSONS = {
    1: ["1-1", "1-2", "1-3", "1-4", "1-5", "1-6", "1-7"],
    2: ["2-1", "2-2", "2-3", "2-4", "2-5", "2-6", "2-7"],
    3: ["3-1", "3-2", "3-3", "3-4", "3-5", "3-6"],
    4: ["4-1", "4-2", "4-3", "4-4", "4-5", "4-6"],
    5: ["5-1", "5-2", "5-3", "5-4", "5-5", "5-6"],
    6: ["6-1", "6-2", "6-3", "6-4", "6-5"],
}

LESSONS_WITH_ITEMS = {
    "3-5", "4-3", "4-4", "4-5", "5-1", "5-4", "5-5", "6-3", "6-4", "6-5",
}

EXPECTED_ITEMS_PER_LESSON = {
    "3-5": 42, "4-3": 74, "4-4": 91, "4-5": 81, "5-1": 132,
    "5-4": 132, "5-5": 96, "6-3": 100, "6-4": 69, "6-5": 83,
}

CALIBRATION_LESSONS = {
    "3-5", "4-1", "4-3", "4-4", "4-5", "5-1", "5-4", "5-5", "6-3", "6-4", "6-5",
}

# Lessons whose readiness == "absent" (calibration-but-0-rows retired, or
# dept-skipped / assessment-shell placeholders).
ABSENT_LESSONS = {"4-1", "3-6", "4-2", "4-6", "5-2", "5-3", "5-6", "6-1", "6-2"}

# Grounded feeder-skill labels (NOT fabricated content — cross-unit dependency
# facts named by the manager spec). Each gets an explicit " (inferred)" suffix.
FEEDER_SKILL_TITLES = {
    "1-2": "Transformations of Functions (inferred)",
    "2-3": "Factoring / Solving Quadratic Equations (inferred)",
    "2-4": "Complex Numbers (inferred)",
    "3-1": "Polynomial operations (feeds 5-1) (inferred)",
}


def unit_of(lesson_code: str) -> str:
    """'4-3' -> '4' (the part before the first '-')."""
    return lesson_code.split("-")[0]


def load_registry():
    rows = []
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_calibration(lesson_code: str):
    path = CALIBRATION_DIR / f"{lesson_code}.json"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_assessment_shell_ids():
    ids = set()
    with ASSESSMENT_SHELLS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ids.add(json.loads(line)["id"])
    return ids


def load_alias_map():
    with ALIAS_MAP_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def readiness_for(lesson_code: str) -> str:
    if lesson_code == "3-5":
        return "calibrated"
    if lesson_code in LESSONS_WITH_ITEMS:
        return "partial"
    if lesson_code in ABSENT_LESSONS:
        return "absent"
    return "frontload-blocked"


def title_objective_eq_for(lesson_code: str, calibration):
    """Returns (title, objective, essential_question) honoring the rule that
    content only comes from calibration files or the four grounded
    feeder-skill exceptions — never fabricated."""
    if lesson_code in CALIBRATION_LESSONS and calibration is not None:
        return (
            calibration.get("title"),
            calibration.get("objective"),
            calibration.get("essential_question"),
        )
    if lesson_code in FEEDER_SKILL_TITLES:
        return (FEEDER_SKILL_TITLES[lesson_code], None, None)
    return (None, None, None)


def classify_dropped_reason(target_id, shell_ids, lessons_with_items):
    if target_id in shell_ids or target_id.startswith("topic"):
        return "assessment-forward-ref"
    m = LESSON_PREFIX_RE.match(target_id)
    if m and m.group(0) == "4-1":
        return "retirement-gap"
    if m and m.group(0) not in lessons_with_items:
        return "frontload-gap"
    return "retired-missing"


def main():
    rows = load_registry()
    shell_ids = load_assessment_shell_ids()
    alias = load_alias_map()
    alias_map = alias["alias_map"]

    # ---- identity: registry_line (1-based, contiguous) -> item_uid --------
    line2uid = {}
    legacy_ambiguous = {}          # legacy_id -> bool
    legacy_lesson = {}             # legacy_id -> lesson (single value; verified below)
    legacy_unique_uid = {}         # legacy_id -> item_uid, only for unambiguous ids
    legacy_uid_candidates = {}     # legacy_id -> [item_uid, ...] ordered by registry_line

    for legacy_id, entry in alias_map.items():
        legacy_ambiguous[legacy_id] = entry["ambiguous"]
        uids_sorted = sorted(entry["item_uids"], key=lambda u: u["registry_line"])
        lessons_seen = {u["lesson"] for u in uids_sorted}
        # Invariant this build depends on: every ambiguous legacy id's two rows
        # share one lesson (collisions are within-lesson only). Verified against
        # the dedup workstream's data; assert rather than silently assume.
        assert len(lessons_seen) == 1, (
            f"legacy id {legacy_id!r} spans multiple lessons {lessons_seen} — "
            "cross-lesson collision breaks the cross_unit-for-ambiguous-targets shortcut"
        )
        legacy_lesson[legacy_id] = uids_sorted[0]["lesson"]
        legacy_uid_candidates[legacy_id] = [u["item_uid"] for u in uids_sorted]
        if not entry["ambiguous"]:
            legacy_unique_uid[legacy_id] = uids_sorted[0]["item_uid"]
        for u in uids_sorted:
            line2uid[u["registry_line"]] = u["item_uid"]

    registry_legacy_ids = set(alias_map.keys())  # 815 distinct legacy id strings

    # ---- rows grouped by lesson, tagged with 1-based registry_line ---------
    rows_by_lesson = OrderedDict()
    for i, r in enumerate(rows, start=1):
        rows_by_lesson.setdefault(r["lesson"], []).append((i, r))
    for lesson in rows_by_lesson:
        rows_by_lesson[lesson].sort(key=lambda pair: pair[0])  # by registry_line

    items_per_lesson = {lesson: len(rs) for lesson, rs in rows_by_lesson.items()}

    def build_item_object(registry_line, row):
        legacy_id = row["id"]
        return {
            "item_uid": line2uid[registry_line],
            "legacy_id": legacy_id,
            "legacy_id_ambiguous": legacy_ambiguous.get(legacy_id, False),
            "registry_line": registry_line,
            "dok": row.get("dok"),
            "role": row.get("role"),
            "skill_tokens": row.get("skill_tokens") or [],
            "standards": row.get("standards") or [],
            "topics": row.get("topics") or [],
            "source": row.get("source"),
        }

    # ---- edges --------------------------------------------------------------
    FIELD_TYPE = [("prereq_ids", "prereq"), ("rehearses", "rehearses"), ("echoes", "echoes")]
    resolved_edges = []
    dropped_edges = []

    for i, r in enumerate(rows, start=1):
        src_legacy = r["id"]
        src_lesson = r["lesson"]
        src_uid = line2uid[i]
        for field, etype in FIELD_TYPE:
            targets = r.get(field) or []
            for tgt in targets:
                if tgt in registry_legacy_ids:
                    tgt_lesson = legacy_lesson[tgt]
                    cross_unit = unit_of(src_lesson) != unit_of(tgt_lesson)
                    tgt_ambiguous = legacy_ambiguous[tgt]
                    edge = {
                        "source_uid": src_uid,
                        "source_legacy": src_legacy,
                        "target_uid": None if tgt_ambiguous else legacy_unique_uid[tgt],
                        "target_legacy": tgt,
                        "type": etype,
                        "source_lesson": src_lesson,
                        "target_lesson": tgt_lesson,
                        "cross_unit": cross_unit,
                        "target_ambiguous": tgt_ambiguous,
                    }
                    if tgt_ambiguous:
                        edge["target_uid_candidates"] = legacy_uid_candidates[tgt]
                        edge["review_ref"] = DUP_REMEDIATION_REF
                    resolved_edges.append(edge)
                else:
                    reason = classify_dropped_reason(tgt, shell_ids, LESSONS_WITH_ITEMS)
                    dropped_edges.append({
                        "source_uid": src_uid,
                        "source": src_legacy,
                        "target": tgt,
                        "type": etype,
                        "reason": reason,
                    })

    # ---- topics / lessons ----------------------------------------------------
    topics_out = []
    for topic_num in sorted(TOPIC_LESSONS.keys()):
        lessons_out = []
        for lesson_code in TOPIC_LESSONS[topic_num]:
            calibration = load_calibration(lesson_code)
            title, objective, eq = title_objective_eq_for(lesson_code, calibration)
            registry_rows_count = items_per_lesson.get(lesson_code, 0)
            has_items = registry_rows_count > 0
            readiness = readiness_for(lesson_code)

            lesson_obj = {
                "lesson": lesson_code,
                "title": title,
                "objective": objective,
                "essential_question": eq,
                "registry_rows": registry_rows_count,
                "has_items": has_items,
                "placeholder": not has_items,
                "readiness": readiness,
                "items": [
                    build_item_object(line_no, row)
                    for line_no, row in rows_by_lesson.get(lesson_code, [])
                ],
            }
            if readiness == "frontload-blocked":
                lesson_obj["frontload_blocked"] = True
            lessons_out.append(lesson_obj)
        topics_out.append({
            "topic": topic_num,
            "title": TOPIC_TITLES[topic_num],
            "lessons": lessons_out,
        })

    # ---- stats ----------------------------------------------------------------
    lessons_total = sum(len(v) for v in TOPIC_LESSONS.values())
    lessons_with_items_count = len(LESSONS_WITH_ITEMS)
    lessons_placeholder = lessons_total - lessons_with_items_count
    items_total = sum(items_per_lesson.values())

    edges_resolved_by_type = Counter(e["type"] for e in resolved_edges)
    edges_cross_unit = sum(1 for e in resolved_edges if e["cross_unit"])
    edges_fully_resolved = sum(1 for e in resolved_edges if not e["target_ambiguous"])
    edges_target_ambiguous = sum(1 for e in resolved_edges if e["target_ambiguous"])
    edges_touching_duplicated_id = sum(
        1 for e in resolved_edges
        if legacy_ambiguous.get(e["source_legacy"], False) or e["target_ambiguous"]
    )
    edges_dropped_by_reason = Counter(e["reason"] for e in dropped_edges)

    # NOTE on naming (matches inventory/dedup/item_uid_alias_map.json's own `meta`
    # block terminology): "unique_legacy_ids" = count of DISTINCT legacy id
    # STRINGS in the registry (815) — not "count of strings that are singleton".
    # "ambiguous_legacy_ids" = how many of those 815 distinct strings are shared
    # by >1 row (85). 815 - 85 = 730 true one-row-per-string ids (not asserted
    # separately; not a number the spec calls out).
    distinct_item_uids = len(set(line2uid.values()))
    unique_legacy_ids = len(registry_legacy_ids)
    ambiguous_legacy_ids = sum(1 for v in legacy_ambiguous.values() if v)

    stats = {
        "topics": len(TOPIC_LESSONS),
        "lessons_total": lessons_total,
        "lessons_with_items": lessons_with_items_count,
        "lessons_placeholder": lessons_placeholder,
        "items_total": items_total,
        "items_per_lesson": {k: items_per_lesson.get(k, 0) for k in sorted(EXPECTED_ITEMS_PER_LESSON)},
        "distinct_item_uids": distinct_item_uids,
        "unique_legacy_ids": unique_legacy_ids,
        "ambiguous_legacy_ids": ambiguous_legacy_ids,
        "edges_resolved_total": len(resolved_edges),
        "edges_resolved_by_type": dict(edges_resolved_by_type),
        "edges_fully_resolved": edges_fully_resolved,
        "edges_target_ambiguous": edges_target_ambiguous,
        "edges_cross_unit": edges_cross_unit,
        "edges_touching_duplicated_id": edges_touching_duplicated_id,
        "edges_dropped_total": len(dropped_edges),
        "edges_dropped_by_reason": dict(edges_dropped_by_reason),
    }

    course_map = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_of_truth": (
            "questionbank/registry.jsonl + questionbank/calibration + graph/ "
            "+ inventory/dedup/item_uid_alias_map.json (all read-only)"
        ),
        "node_identity": (
            "Tree nodes are keyed by opaque item_uid (900 total, one per registry "
            "row/line, always unique). legacy_id (the human-readable registry `id`, "
            "e.g. '5-1-savvas-q18') is kept as a possibly-shared alias: 815 of 900 "
            "legacy ids are unique, but 85 are ambiguous — two different registry "
            "rows share the same legacy_id string, always within a single lesson "
            "(5-1, 5-4, or 5-5; never spanning lessons). 17 of the 193 resolved "
            "edges have a target whose legacy_id is ambiguous — these carry "
            "target_uid=null, target_ambiguous=true, and both candidate item_uids, "
            "rather than being silently pinned to one. See "
            "inventory/dedup/item_uid_alias_map.json and "
            f"{DUP_REMEDIATION_REF}."
        ),
        "note": "Item tree = 900 registry rows (900 unique item_uids) across 10 lessons; other lessons are structural placeholders. Pacing is advisory. See COURSE_MAP.md.",
        "topics": topics_out,
        "prereq_edges": resolved_edges,
        "dropped_edges": dropped_edges,
        "stats": stats,
    }

    # -----------------------------------------------------------------------
    # SELF-CHECKS — manager-supplied / dedup-workstream-supplied ground truth.
    # STOP (raise) on mismatch; never silently adjust.
    # -----------------------------------------------------------------------
    assert stats["topics"] == 6, stats["topics"]
    assert stats["lessons_total"] == 37, stats["lessons_total"]
    assert stats["lessons_with_items"] == 10, stats["lessons_with_items"]
    assert stats["lessons_placeholder"] == 27, stats["lessons_placeholder"]
    assert stats["items_total"] == 900, stats["items_total"]

    for lesson, expected_count in EXPECTED_ITEMS_PER_LESSON.items():
        actual = items_per_lesson.get(lesson, 0)
        assert actual == expected_count, f"{lesson}: expected {expected_count}, got {actual}"

    # -- node identity (Finding 1) --
    assert stats["distinct_item_uids"] == 900, stats["distinct_item_uids"]
    assert stats["unique_legacy_ids"] == 815, stats["unique_legacy_ids"]
    assert stats["ambiguous_legacy_ids"] == 85, stats["ambiguous_legacy_ids"]
    assert stats["unique_legacy_ids"] == len(registry_legacy_ids) == 815
    total_nodes = sum(len(l["items"]) for t in topics_out for l in t["lessons"])
    assert total_nodes == 900, total_nodes

    # -- edges (Finding 1) --
    assert stats["edges_resolved_total"] == 193, stats["edges_resolved_total"]
    assert stats["edges_resolved_by_type"] == {"prereq": 129, "rehearses": 42, "echoes": 22}, stats["edges_resolved_by_type"]
    assert stats["edges_fully_resolved"] == 176, stats["edges_fully_resolved"]
    assert stats["edges_target_ambiguous"] == 17, stats["edges_target_ambiguous"]
    assert stats["edges_fully_resolved"] + stats["edges_target_ambiguous"] == stats["edges_resolved_total"]
    assert stats["edges_cross_unit"] == 16, stats["edges_cross_unit"]
    assert stats["edges_touching_duplicated_id"] == 43, stats["edges_touching_duplicated_id"]

    # -- dropped edges (Finding 2) --
    assert stats["edges_dropped_total"] == 18, stats["edges_dropped_total"]
    assert stats["edges_dropped_by_reason"] == {
        "assessment-forward-ref": 12,
        "retirement-gap": 4,
        "frontload-gap": 1,
        "retired-missing": 1,
    }, stats["edges_dropped_by_reason"]

    # readiness distribution sanity (1 calibrated + 9 partial + 9 absent + 18 frontload-blocked == 37)
    readiness_counts = Counter(
        lesson["readiness"] for topic in topics_out for lesson in topic["lessons"]
    )
    assert readiness_counts["calibrated"] == 1, readiness_counts
    assert readiness_counts["partial"] == 9, readiness_counts
    assert readiness_counts["absent"] == 9, readiness_counts
    assert readiness_counts["frontload-blocked"] == 18, readiness_counts

    OUT_PATH.write_text(json.dumps(course_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
