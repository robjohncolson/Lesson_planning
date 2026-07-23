"""
build_classification.py

Read-only build script for WS2 deliverables. Reads questionbank/registry.jsonl
(never writes to it) plus the hand-authored judgments in classifications_data.py,
and emits three files under inventory/visuals/:

  1. visual_asset_classification.json
  2. VISUAL_ASSETS_REPORT.md
  3. broken_path_repair.json

This script performs NO writes to questionbank/. It only writes the three
files above (plus reusing extract_absent_visuals.py's read-only helpers).
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from classifications_data import CLASSIFICATIONS
from extract_absent_visuals import (
    REPO_ROOT,
    REGISTRY_PATH,
    load_rows,
    is_absent,
    is_broken_path,
    sha256_of_file,
    EXPECTED_ABSENT_BY_LESSON,
    EXPECTED_ABSENT_TOTAL,
    EXPECTED_BROKEN_IDS,
    QUIRK_IDS,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
LESSON_ORDER = ["4-3", "4-4", "4-5", "5-1", "5-4", "5-5", "6-3", "6-4", "6-5"]
VISUAL_TYPES = ["graph", "photo", "table", "diagram", "map", "none"]
IMPORTANCE_LEVELS = ["essential", "supporting", "decorative"]
RECOVERABILITY_LEVELS = ["tikz_regenerable", "source_pdf_required", "irreplaceable_photo"]


def make_excerpt(prompt, n=180):
    if not prompt:
        return ""
    single_line = re.sub(r"\s+", " ", prompt).strip()
    if len(single_line) > n:
        return single_line[:n].rstrip() + "..."
    return single_line


def main():
    pre_hash = sha256_of_file(REGISTRY_PATH)

    rows = load_rows(REGISTRY_PATH)
    absent = [(ln, row) for ln, row in rows if is_absent(row)]
    broken = [(ln, row) for ln, row in rows if is_broken_path(row, REPO_ROOT)]

    # ---- Sanity: reconfirm the 137 / 7 invariants before building anything ----
    assert len(absent) == EXPECTED_ABSENT_TOTAL, f"ABSENT total mismatch: {len(absent)}"
    by_lesson_check = {}
    for ln, row in absent:
        by_lesson_check[row["lesson"]] = by_lesson_check.get(row["lesson"], 0) + 1
    assert by_lesson_check == EXPECTED_ABSENT_BY_LESSON, f"per-lesson mismatch: {by_lesson_check}"
    assert len(broken) == 7, f"BROKEN total mismatch: {len(broken)}"
    assert {row["id"] for _, row in broken} == set(EXPECTED_BROKEN_IDS)

    missing_keys = [ln for ln, _ in absent if ln not in CLASSIFICATIONS]
    assert not missing_keys, f"Missing classification judgments for registry_line(s): {missing_keys}"
    extra_keys = [k for k in CLASSIFICATIONS if k not in {ln for ln, _ in absent}]
    assert not extra_keys, f"classifications_data.py has stale/extra keys not in ABSENT set: {extra_keys}"

    # ================= Build visual_asset_classification.json =================
    class_rows = []
    for ln, row in absent:
        importance, imp_rat, recoverability, rec_rat, flags = CLASSIFICATIONS[ln]
        assert importance in IMPORTANCE_LEVELS, f"bad importance for line {ln}: {importance}"
        assert recoverability in RECOVERABILITY_LEVELS, f"bad recoverability for line {ln}: {recoverability}"
        visual_type = row.get("visual_type")
        assert visual_type in VISUAL_TYPES, f"unexpected visual_type '{visual_type}' at line {ln}"

        row_flags = list(flags)
        if row["id"] in QUIRK_IDS:
            assert "has_visual_true_but_visual_type_none" in row_flags, (
                f"quirk id {row['id']} (line {ln}) missing required flag"
            )
            assert visual_type == "none", f"quirk id {row['id']} visual_type should be 'none', got {visual_type}"
        if row["id"] == "4-5-savvas-concept-summary-lesson-4-5-2":
            assert "visual_type_map_is_concept_summary" in row_flags
            assert visual_type == "map"

        class_rows.append({
            "id": row["id"],
            "registry_line": ln,
            "lesson": row["lesson"],
            "visual_type": visual_type,
            "importance": importance,
            "importance_rationale": imp_rat,
            "recoverability": recoverability,
            "recoverability_rationale": rec_rat,
            "dok": row.get("dok"),
            "source": row.get("source"),
            "prompt_excerpt": make_excerpt(row.get("prompt")),
            "flags": row_flags,
        })

    assert len(class_rows) == 137

    # ---- Summaries ----
    by_lesson = {}
    by_visual_type = {}
    by_importance = {}
    by_recoverability = {}
    cross = {lvl: {r: 0 for r in RECOVERABILITY_LEVELS} for lvl in IMPORTANCE_LEVELS}
    by_lesson_x_visual_type = {}
    needs_confirm = 0

    for r in class_rows:
        by_lesson[r["lesson"]] = by_lesson.get(r["lesson"], 0) + 1
        by_visual_type[r["visual_type"]] = by_visual_type.get(r["visual_type"], 0) + 1
        by_importance[r["importance"]] = by_importance.get(r["importance"], 0) + 1
        by_recoverability[r["recoverability"]] = by_recoverability.get(r["recoverability"], 0) + 1
        cross[r["importance"]][r["recoverability"]] += 1
        by_lesson_x_visual_type.setdefault(r["lesson"], {})
        by_lesson_x_visual_type[r["lesson"]][r["visual_type"]] = (
            by_lesson_x_visual_type[r["lesson"]].get(r["visual_type"], 0) + 1
        )
        if "needs_teacher_confirmation" in r["flags"]:
            needs_confirm += 1

    # ---- Reconciliation assertions ----
    assert sum(by_lesson.values()) == 137
    assert by_lesson == EXPECTED_ABSENT_BY_LESSON
    assert sum(by_visual_type.values()) == 137
    assert sum(by_importance.values()) == 137
    assert sum(by_recoverability.values()) == 137
    assert sum(sum(d.values()) for d in cross.values()) == 137
    assert sum(sum(d.values()) for d in by_lesson_x_visual_type.values()) == 137
    for lvl in IMPORTANCE_LEVELS:
        assert sum(cross[lvl].values()) == by_importance.get(lvl, 0), (
            f"cross-tab row {lvl} does not reconcile to by_importance"
        )

    registry_sha256 = pre_hash  # pre == post since this script never writes registry.jsonl

    classification_doc = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "definition": (
                "ABSENT = has_visual==True AND image field empty/None (inventory visuals_absent "
                "definition). Total 137 across nine lessons."
            ),
            "reconciliation_note": (
                "137 uses has_visual (matches inventory). The alternative 'visual_type!=none' reading "
                "yields 132; the 5-row gap is the has_visual_true_but_visual_type_none quirk rows "
                "(6-3-ex-3, 6-3-tryit-3, 6-3-tryit-4, 6-3-tryit-5, 6-4-tryit-1), which are retained here."
            ),
            "registry_sha256": registry_sha256,
            "total": 137,
        },
        "rows": class_rows,
        "summary": {
            "by_lesson": {k: by_lesson.get(k, 0) for k in LESSON_ORDER},
            "by_visual_type": by_visual_type,
            "by_importance": by_importance,
            "by_recoverability": by_recoverability,
            "cross_importance_x_recoverability": cross,
            "by_lesson_x_visual_type": by_lesson_x_visual_type,
            "needs_teacher_confirmation_count": needs_confirm,
        },
    }

    out_json_path = os.path.join(OUT_DIR, "visual_asset_classification.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(classification_doc, f, indent=2, ensure_ascii=False)

    # ================= Build broken_path_repair.json =================
    fixes = []
    for ln, row in broken:
        image = row["image"]
        basename = os.path.basename(image)
        current_full = os.path.join(REPO_ROOT, image.replace("/", os.sep))
        proposed_rel = "questionbank/calibration/sources/" + basename
        proposed_full = os.path.join(REPO_ROOT, proposed_rel.replace("/", os.sep))
        fixes.append({
            "id": row["id"],
            "lesson": row["lesson"],
            "current_image": image,
            "current_file_exists": os.path.exists(current_full),
            "proposed_image": proposed_rel,
            "proposed_file_exists": os.path.exists(proposed_full),
        })

    assert len(fixes) == 7
    assert all(fx["proposed_file_exists"] for fx in fixes), "Not all proposed paths exist on disk!"
    assert all(not fx["current_file_exists"] for fx in fixes), "A 'broken' path unexpectedly exists!"

    broken_doc = {
        "status": "PROPOSED -- NOT APPLIED. registry.jsonl was NOT modified. Path repairs listed for human review only.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "registry_sha256": registry_sha256,
        "count": 7,
        "fixes": sorted(fixes, key=lambda x: x["id"]),
    }

    out_broken_path = os.path.join(OUT_DIR, "broken_path_repair.json")
    with open(out_broken_path, "w", encoding="utf-8") as f:
        json.dump(broken_doc, f, indent=2, ensure_ascii=False)

    # ================= Build VISUAL_ASSETS_REPORT.md =================
    md = build_markdown_report(classification_doc, broken_doc)
    out_md_path = os.path.join(OUT_DIR, "VISUAL_ASSETS_REPORT.md")
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(md)

    # ================= Final byte-unchanged check =================
    post_hash = sha256_of_file(REGISTRY_PATH)
    assert pre_hash == post_hash, "registry.jsonl changed during build (should be impossible)!"

    print("Wrote:")
    print(" ", out_json_path)
    print(" ", out_md_path)
    print(" ", out_broken_path)
    print()
    print(f"registry.jsonl sha256 before: {pre_hash}")
    print(f"registry.jsonl sha256 after:  {post_hash}")
    print("MATCH" if pre_hash == post_hash else "MISMATCH -- INVESTIGATE")
    print()
    print("by_lesson:", classification_doc["summary"]["by_lesson"])
    print("by_visual_type:", classification_doc["summary"]["by_visual_type"])
    print("by_importance:", classification_doc["summary"]["by_importance"])
    print("by_recoverability:", classification_doc["summary"]["by_recoverability"])
    print("cross:", classification_doc["summary"]["cross_importance_x_recoverability"])
    print("needs_teacher_confirmation_count:", needs_confirm)


def build_markdown_report(classification_doc, broken_doc):
    meta = classification_doc["meta"]
    summary = classification_doc["summary"]
    rows = classification_doc["rows"]

    lines = []
    lines.append("# Visual Asset Inventory -- 137 Absent + 7 Broken-Path (WS2)")
    lines.append("")
    lines.append(
        "Scope: **137 ABSENT rows** (`has_visual==True` AND `image` field empty/None -- the "
        "inventory's authoritative `visuals_absent` definition) across nine lessons (4-3, 4-4, "
        "4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5), plus **7 BROKEN-PATH rows** in lesson 3-5 whose "
        "`image` field points at a file that no longer exists on disk."
    )
    lines.append("")
    lines.append(
        "> **This is analysis only.** `questionbank/registry.jsonl` was read-only throughout and "
        "was NOT modified. Path repairs below are PROPOSED for human review, not applied. "
        f"registry.jsonl sha256: `{meta['registry_sha256']}` (unchanged before/after this run)."
    )
    lines.append("")
    lines.append("## Definition and reconciliation")
    lines.append("")
    lines.append(f"- **has_visual definition:** {meta['definition']}")
    lines.append(f"- **137 vs 132 reconciliation:** {meta['reconciliation_note']}")
    lines.append("")

    # ---- Per-lesson summary table ----
    lines.append("## Per-lesson summary")
    lines.append("")
    lines.append("| lesson | rows | essential | supporting | decorative | tikz | source_pdf | irreplaceable_photo |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for lesson in LESSON_ORDER:
        lesson_rows = [r for r in rows if r["lesson"] == lesson]
        n = len(lesson_rows)
        ess = sum(1 for r in lesson_rows if r["importance"] == "essential")
        sup = sum(1 for r in lesson_rows if r["importance"] == "supporting")
        dec = sum(1 for r in lesson_rows if r["importance"] == "decorative")
        tikz = sum(1 for r in lesson_rows if r["recoverability"] == "tikz_regenerable")
        pdf = sum(1 for r in lesson_rows if r["recoverability"] == "source_pdf_required")
        photo = sum(1 for r in lesson_rows if r["recoverability"] == "irreplaceable_photo")
        lines.append(f"| {lesson} | {n} | {ess} | {sup} | {dec} | {tikz} | {pdf} | {photo} |")
    total_ess = summary["by_importance"].get("essential", 0)
    total_sup = summary["by_importance"].get("supporting", 0)
    total_dec = summary["by_importance"].get("decorative", 0)
    total_tikz = summary["by_recoverability"].get("tikz_regenerable", 0)
    total_pdf = summary["by_recoverability"].get("source_pdf_required", 0)
    total_photo = summary["by_recoverability"].get("irreplaceable_photo", 0)
    lines.append(f"| **TOTAL** | **137** | **{total_ess}** | **{total_sup}** | **{total_dec}** | **{total_tikz}** | **{total_pdf}** | **{total_photo}** |")
    lines.append("")

    # ---- Per visual-type table ----
    lines.append("## Per-visual-type summary")
    lines.append("")
    lines.append("| visual_type | count |")
    lines.append("|---|---|")
    for vt in VISUAL_TYPES:
        if vt in summary["by_visual_type"]:
            lines.append(f"| {vt} | {summary['by_visual_type'][vt]} |")
    lines.append(f"| **TOTAL** | **137** |")
    lines.append("")

    # ---- Recoverability prose ----
    lines.append("## Recoverability breakdown")
    lines.append("")
    lines.append(
        f"Of the 137 absent-visual rows: **{total_tikz} are TikZ-regenerable** (the figure's "
        "content -- a stated equation, a fully-specified table, or a labeled geometric solid with "
        f"all dimensions given in text -- can be redrawn without the original asset), **{total_pdf} "
        "require the Savvas SE/TE source PDF** (the defining data -- unlabeled figure dimensions, an "
        "unequationed curve, or a specific student error -- exists only in the original figure), and "
        f"**{total_photo} are irreplaceable photos** (a real-world scene, object, or person that would "
        "need the original photographic asset, even though most of these are decorative/supporting "
        "because their numeric givens are also transcribed into the prompt text)."
    )
    lines.append("")
    lines.append("Cross-tab of importance x recoverability:")
    lines.append("")
    lines.append("| importance | tikz_regenerable | source_pdf_required | irreplaceable_photo | row total |")
    lines.append("|---|---|---|---|---|")
    cross = summary["cross_importance_x_recoverability"]
    for lvl in IMPORTANCE_LEVELS:
        row = cross[lvl]
        rowtotal = sum(row.values())
        lines.append(f"| {lvl} | {row.get('tikz_regenerable',0)} | {row.get('source_pdf_required',0)} | {row.get('irreplaceable_photo',0)} | {rowtotal} |")
    lines.append(f"| **column total** | **{total_tikz}** | **{total_pdf}** | **{total_photo}** | **137** |")
    lines.append("")

    # ---- Teacher-judgment items ----
    lines.append("## Teacher-judgment items (`needs_teacher_confirmation`)")
    lines.append("")
    lines.append(
        f"{summary['needs_teacher_confirmation_count']} of the 137 rows are flagged for a human "
        "second look. This always includes the 5 `has_visual`/`visual_type==none` quirk rows and "
        "the 1 mislabeled-map concept-summary row, plus other borderline importance/recoverability calls."
    )
    lines.append("")
    lines.append("| id | lesson | registry_line | why it needs confirming |")
    lines.append("|---|---|---|---|")
    for r in rows:
        if "needs_teacher_confirmation" in r["flags"]:
            why = r["importance_rationale"]
            lines.append(f"| {r['id']} | {r['lesson']} | {r['registry_line']} | {why} |")
    lines.append("")

    # ---- Quirk rows called out explicitly ----
    lines.append("### The 5 has_visual/visual_type=none quirk rows")
    lines.append("")
    lines.append(
        "These rows have `has_visual==True` but `visual_type==\"none\"` in the registry -- they are "
        "part of the 137 by definition (dropping them via a `visual_type!=none` filter would wrongly "
        "shrink the count to 132) but need a teacher's confirmation that no visual asset is actually needed."
    )
    lines.append("")
    lines.append("| id | lesson | importance | recoverability |")
    lines.append("|---|---|---|---|")
    for r in rows:
        if "has_visual_true_but_visual_type_none" in r["flags"]:
            lines.append(f"| {r['id']} | {r['lesson']} | {r['importance']} | {r['recoverability']} |")
    lines.append("")

    lines.append("### The mislabeled map row")
    lines.append("")
    for r in rows:
        if "visual_type_map_is_concept_summary" in r["flags"]:
            lines.append(
                f"- `{r['id']}` (lesson {r['lesson']}, registry_line {r['registry_line']}): "
                f"visual_type recorded as `map` but content is a concept-summary table/word-problem. "
                f"{r['importance_rationale']}"
            )
    lines.append("")

    # ---- Broken-path section ----
    lines.append("## Broken-path set (lesson 3-5, 7 rows)")
    lines.append("")
    lines.append(
        "These 7 rows have `has_visual==True` and a non-empty `image` field, but the referenced file "
        "does not exist on disk. All 7 point at `questionbank/images/3-5_savvas_example-N.png`, and "
        "the corresponding file exists at `questionbank/calibration/sources/3-5_savvas_example-N.png` "
        "instead. This is a PROPOSED path repair only -- see `broken_path_repair.json` for the "
        "machine-readable version; `registry.jsonl` was NOT edited."
    )
    lines.append("")
    lines.append("| id | current_image | current_exists | proposed_image | proposed_exists |")
    lines.append("|---|---|---|---|---|")
    for fx in broken_doc["fixes"]:
        lines.append(
            f"| {fx['id']} | `{fx['current_image']}` | {fx['current_file_exists']} | "
            f"`{fx['proposed_image']}` | {fx['proposed_file_exists']} |"
        )
    lines.append("")

    # ---- Full per-row appendix ----
    lines.append("## Appendix: full per-row table (all 137)")
    lines.append("")
    lines.append("| id | lesson | visual_type | importance | recoverability | flags |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        flags_str = ", ".join(r["flags"]) if r["flags"] else ""
        lines.append(
            f"| {r['id']} | {r['lesson']} | {r['visual_type']} | {r['importance']} | "
            f"{r['recoverability']} | {flags_str} |"
        )
    lines.append("")

    lines.append("## Registry integrity")
    lines.append("")
    lines.append(
        f"`questionbank/registry.jsonl` sha256 was `{meta['registry_sha256']}` both before and "
        "after this analysis run. The file was opened read-only; no writes were made to it or to "
        "any other file under `questionbank/`."
    )
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("\nASSERTION FAILED -- STOPPING:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(1)
