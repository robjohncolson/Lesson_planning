"""
build_console.py -- NT3 Teacher Decision Console data pipeline.

Reads a fixed set of READ-ONLY inputs from across the Lesson_planning repo and
derives:
  - inventory/decision-console/console_data.json
  - inventory/decision-console/thumbnails/<bank_id>.png (64 PNGs)
  - (if a template exists) inventory/decision-console/TEACHER_DECISION_CONSOLE.html

This script performs NO pedagogical judgment. It presents evidence and options;
it never marks anything "verified" and never writes to any input file. All
locked/frozen counts are asserted in the GUARD ASSERTS section below and
nowhere else -- every other count in the output is computed from the inputs
at run time.

Run: python build_console.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent               # .../inventory/decision-console
REPO_ROOT = HERE.parent.parent                        # .../Lesson_planning

REGISTRY_PATH = REPO_ROOT / "questionbank" / "registry.jsonl"
WAVE_PLAN_PATH = REPO_ROOT / "inventory" / "dok-workflow" / "dok_wave_plan.json"
COURSE_MAP_PATH = REPO_ROOT / "inventory" / "course-map" / "course_map.json"
ALIAS_MAP_PATH = REPO_ROOT / "inventory" / "dedup" / "item_uid_alias_map.json"
CONTENT_READINESS_PATH = REPO_ROOT / "inventory" / "dashboard" / "content_readiness.json"
VISUAL_CLASS_PATH = REPO_ROOT / "inventory" / "visuals" / "visual_asset_classification.json"
MANIFEST_PATH = REPO_ROOT / "inventory" / "tikz-staging" / "MANIFEST.json"
TIKZ_STAGING_DIR = REPO_ROOT / "inventory" / "tikz-staging"
CALIBRATION_DIR = REPO_ROOT / "questionbank" / "calibration"

# Optional (may not exist) -- a teacher's/RC's confirmation export, read-only
# input, same directory as this script. Never written to.
RC_DECISIONS_PATH = HERE / "teacher_decisions_rc_v1.json"

OUT_DATA_PATH = HERE / "console_data.json"
THUMB_DIR = HERE / "thumbnails"
TEMPLATE_PATH = HERE / "console_template.html"
ASSEMBLED_HTML_PATH = HERE / "TEACHER_DECISION_CONSOLE.html"

# tools/dok-review is not importable as a normal package (hyphen in the
# directory name), so it is reached via an explicit sys.path insert -- the
# same pattern inventory/dok-workflow/gen_dok_wave_plan.py already uses.
# dok_review.py has no module-level import side effects (confirmed by
# reading it in full before this import was added), so this insert + import
# is safe to run at module import time. Read-only: this console only ever
# calls dok_review.load_rubric_approvals() (never writes review_log.jsonl or
# rubric_approvals.json -- see the "Canonical coherence guards" section in
# main() below).
DOK_REVIEW_TOOL_DIR = REPO_ROOT / "tools" / "dok-review"
if str(DOK_REVIEW_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(DOK_REVIEW_TOOL_DIR))
import dok_review  # noqa: E402  (path insert must precede this import)

RUBRIC_APPROVALS_PATH = DOK_REVIEW_TOOL_DIR / "rubric_approvals.json"

# ---------------------------------------------------------------------------
# Frozen hashes (the ONLY place these numbers/hashes are hardcoded, per spec)
# ---------------------------------------------------------------------------

FROZEN_HASHES = {
    # NT11 named re-pin (rc-merge-auth-5-4-2026-07-23, 2026-07-23): SUB-A's
    # merge mutation wrote the four v2 tombstone marker fields
    # (status=="merged-alias", alias_of, merged_at, merge_authorization) onto
    # the 22 merge-authorized rows (lesson 5-4). No dok/role/answer/visual/
    # topic content changed on any row.
    # Prior pin: b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8
    # NT14 named re-pin (nt14-ingest-4-1-2026-07-23, 2026-07-23): 19 new
    # rows appended (lines 901-919, ids 4-1-savvas-q8..q26), all carrying
    # top-level "availability": "optional-catalog". No existing row (lines
    # 1-900) was modified by this ingestion.
    # Prior pin (rc-merge-auth-5-4-2026-07-23): a2fe278292e97a432a6275b807fdfe730ab67a38efd09a70e5241355959dba17
    # NAMED update (nt14-ingest-4-1-2026-07-23, RC acceptance correction):
    # source_gap markers added to registry lines 909/911 (4-1-savvas-q16/q18)
    # only; first 900 lines still byte-identical to the frozen baseline.
    # Prior pin: 279d3464d7cb71f58968b02213cafa849815bd6a4ebaf13bdb7d124c471f2dc6
    REGISTRY_PATH: "5a9dff0bacd0c7ccd168d582405f95fa5da42c50b4975bb85555eb644f90d6ad",
    # NT9 calibration-evidence re-pin (2026-07-22): wave plan regenerated after
    # lesson 5-4's TE p.258 item_analysis was transcribed into
    # questionbank/calibration/5-4.json (evidence only -- no registry mutation,
    # no decisions recorded). The ONLY change in the regenerated plan is that
    # 61 lesson-5-4 rows flipped match_quality none -> exact with te_bucket
    # populated ([1] x42, [2] x16, [3] x3); proven by reverse-reconstruction:
    # reverting exactly those fields reproduces the prior plan byte-for-byte
    # (sha256 4fc6baa4...). dok_status totals (421/437/42, verified 0), wave
    # counts, identities, and ordering are all unchanged.
    # Prior pin (NT8 post-approval): 4fc6baa43251f5fd25257c840d2cea27d66eb56a450103b5b746cc2e7967671e
    # NT10 named re-pin per DOK_VERIFICATION_WORKFLOW.md step 3(d),
    # 2026-07-22: wave plan regenerated (H1) after the FIRST real review-log
    # recordings -- RC's 39 lesson-5-4 rule-1 batch confirmations under
    # approved rubric v0.2 (tools/dok-review/review_log.jsonl, 39 entries,
    # sha256 4b61fd3bbaf47031c0b901e425ed2cbe1c206dba30bc745f2667d8ef48c17bf0).
    # The plan's verified_count is now 39 (all lesson 5-4; base buckets:
    # unreviewed 437 -> 398); registry/identities/wave counts unchanged.
    # Prior pin (NT9 calibration-evidence): f1dbdd19dcbf35c7f40fc2ab9e4a4336990ae7185edf1a7de82b87fda8df7266
    # NT11 named re-pin (rc-merge-auth-5-4-2026-07-23, 2026-07-23): wave plan
    # regenerated by gen_dok_wave_plan.py after the registry merge mutation
    # above -- the ONLY change is the additive 'status'/'alias_of' overlay
    # (plus the new 'identity_reconciliation' block) on all 900 items; every
    # EXPECTED_* wave/dok_status/lesson-count pin in gen_dok_wave_plan.py
    # still passed unmodified (dok/role/wave content untouched by the merge).
    # Prior pin (NT10): 14c49acf907bb884fe0c58c33fc928230066e4b595bfdaae7126e7ff18835a3c
    # NT14 named re-pin (nt14-ingest-4-1-2026-07-23, 2026-07-23): wave plan
    # regenerated by gen_dok_wave_plan.py after the registry ingestion above
    # -- adds the new "optional-catalog" wave bucket (19 items, lesson 4-1)
    # and the triple-split identity_reconciliation block; every wave 0-4 /
    # dok_status/lesson-count pin for the pre-existing 900 rows is
    # unmodified (this ingestion touched no existing row).
    # Prior pin (rc-merge-auth-5-4-2026-07-23): 26f578b7cba22397f4015509a17dd097cfd829a2f48250ebf779237d3b9ad82c
    # NAMED update (nt14-ingest-4-1-2026-07-23, RC acceptance correction):
    # the optional-catalog bucket's q16/q18 items now carry source_gap.
    # Prior pin: 262730cec82df88d5b814d7ea679b048d46eabaa84b74bd0cf21fc2456b7e23d
    WAVE_PLAN_PATH: "1aca1e2d955d0da7f907097be1c2d09862a391c4e60145c8227d2b528c91cebf",
    # NT14 named re-pin (nt14-ingest-4-1-2026-07-23, 2026-07-23): course_map.json
    # regenerated by a sibling NT14 workstream (out of this batch's authorized
    # write scope) now that 4-1 has real (optional-catalog) items -- the 4
    # dropped_edges that used to read reason=='retirement-gap' targeting 4-1-*
    # are now resolved (edges_dropped_total 18 -> 14), and 4-1's own lesson
    # block reads registry_rows: 19 / readiness: 'optional-catalog'.
    # Prior pin: c8274dfbaab29424d0cb5f15093359bab948112dee70d432ede7597d0fd095c0
    COURSE_MAP_PATH: "f2bd625a7aaf2d31e27afd1e5d7700df8a08b20f58f98fbfb557b1fcc706af30",
    # NT11 named re-pin (rc-merge-auth-5-4-2026-07-23, 2026-07-23): SUB-B
    # regenerated the alias map with the additive "resolved_alias" enrichment
    # for the 22 merge-authorized groups (meta.merged_alias_rows/
    # alias_resolved_groups now 22, unresolved_ambiguous_groups now 63) --
    # alias_map/item_uids entries and the "ambiguous" flag are unchanged.
    # Prior pin: be4b507b7fb7aee904fead8515686d2583c2732e948aaf3ced134e63d97c7ff1
    # NT14 named re-pin (nt14-ingest-4-1-2026-07-23, 2026-07-23): alias map
    # regenerated to add the 19 new lesson-4-1 rows (total_rows 900 -> 919,
    # unique_legacy_ids 815 -> 834); the 22 rc-merge-auth-5-4 groups'
    # resolved_alias enrichment is unchanged.
    # Prior pin (rc-merge-auth-5-4-2026-07-23): 27b8c13b6c2a03d1c33e86ce4007dcfa27a7e56717044b821ac7db934d2ede5e
    ALIAS_MAP_PATH: "1f45860496344b5caeca774be4d75b5455e93b42bbb025a3f9a1221b7076e860",
}


class GuardFailure(SystemExit):
    pass


def guard(cond: bool, msg: str) -> None:
    if not cond:
        raise GuardFailure(f"GUARD FAILED: {msg}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def display_path(path: Path) -> str:
    """Repo-relative POSIX path when `path` resolves inside REPO_ROOT;
    otherwise the plain absolute path. Used for paths that MAY point outside
    the repo (a --fixture-* argument living under a scratchpad/tmp_path dir),
    unlike rel() which assumes the path is always inside REPO_ROOT. Mirrors
    inventory/dok-workflow/gen_dok_wave_plan.py's repo_relative_display_path()."""
    path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def dok_rationale_derived(dok_status: str, te_bucket, match_quality) -> str:
    """Human-readable rationale for how a row's displayed DOK came to be,
    keyed off the wave-plan's own dok_status vocabulary. 'verified' is the
    NT7 canonical-projection overlay (see gen_dok_wave_plan.py's "Canonical
    verification projection" section): dok_status only ever reads 'verified'
    when tools/dok-review/dok_review.py's entry_is_verified() (reached via
    tool_state_for()) says so for that item_uid, gated by the teacher-
    approved rubric-approvals manifest. The final raise is intentional --
    any dok_status value outside this module's four-value vocabulary
    (known_auto / calibrated / unreviewed / verified) is a build bug, not a
    display gap, and must fail loudly rather than render a guess."""
    if dok_status == "calibrated":
        return "DOK carried from the authored lesson calibration (dok_status: calibrated)"
    if dok_status == "known_auto":
        return "DOK auto-derived from source labeling (dok_status: known_auto)"
    if dok_status == "verified":
        return (
            "DOK verified via the canonical review-log projection (review_state: verified — "
            "tools/dok-review/dok_review.py entry_is_verified under the teacher-approved rubric "
            "manifest)"
        )
    if dok_status == "unreviewed" and te_bucket:
        return f"Unreviewed; TE bucket suggests DOK {te_bucket} (match_quality: {match_quality})"
    if dok_status == "unreviewed" and not te_bucket:
        return (
            "Unreviewed; carried as-ingested from the registry; no TE-bucket cross-check available "
            f"(match_quality: {match_quality})"
        )
    raise GuardFailure(f"unhandled dok_status combination: dok_status={dok_status!r} te_bucket={te_bucket!r}")


def load_calibration_item_anchors(lesson: str) -> dict[str, dict]:
    """Read questionbank/calibration/{lesson}.json (read-only, optional --
    the file may not exist for a given lesson) and return the ITEM-LEVEL
    anchors it names, keyed by the legacy id the anchor's own 'source'
    string resolves to.

    Each anchor entry in dok2_anchors / dok3_anchors carries a 'source'
    string of the form "Savvas Practice #<N> (...)"; that is parsed into
    the legacy id '{lesson}-savvas-q{N}' -- the ONLY on-disk, per-row
    textbook DOK trace this calibration file provides. There is no
    'item_analysis' key in these files (that lesson-level Savvas-DOK map
    exists only for lesson 4-1 today) -- dok2_anchors/dok3_anchors are it.

    Returns {} if the calibration file is missing, unreadable as the
    expected shape, or has no anchors -- that is the correct "no
    item-level trace on disk" result, not an error condition.
    """
    calib_path = CALIBRATION_DIR / f"{lesson}.json"
    if not calib_path.exists():
        return {}
    doc = load_json(calib_path)
    anchors: dict[str, dict] = {}
    for level, why_key in (("dok2_anchors", "why_dok2"), ("dok3_anchors", "why_dok3")):
        for a in doc.get(level, None) or []:
            m = re.search(r"Savvas Practice #(\d+)", a.get("source", "") or "")
            if not m:
                continue
            legacy_id = f"{lesson}-savvas-q{m.group(1)}"
            anchors[legacy_id] = {
                "level": level[:-len("_anchors")],  # "dok2" or "dok3"
                "source": a.get("source", ""),
                "why": a.get(why_key, ""),
                "calib_file": rel(calib_path),
            }
    return anchors


# ---------------------------------------------------------------------------
# Load all inputs (read-only)
# ---------------------------------------------------------------------------

def load_registry_rows() -> dict[int, dict]:
    rows = {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rows[i] = json.loads(line)
    return rows


def parse_args(argv=None) -> argparse.Namespace:
    """FIXTURE MODE is a test affordance for the cross-consumer proof suite
    (inventory/dok-workflow/test_cross_consumer_projection.py-style fixtures),
    NOT a normal operating mode -- it never runs unattended and never touches
    the repo. All three --fixture-* flags are required together (an
    all-or-nothing group); the default (no args at all) is the real build:
    real wave plan, real approvals manifest, full outputs (console_data.json,
    thumbnails/, TEACHER_DECISION_CONSOLE.html), all guards enforced."""
    parser = argparse.ArgumentParser(
        description=(
            "Build the Teacher Decision Console. With no arguments: real, "
            "frozen repo inputs in, real outputs out (console_data.json, "
            "thumbnails/, TEACHER_DECISION_CONSOLE.html), every guard "
            "enforced. FIXTURE MODE (--fixture-wave-plan / "
            "--fixture-approvals-manifest / --fixture-out, all three "
            "required together) substitutes a fixture wave plan and rubric-"
            "approvals manifest for smoke-testing the canonical-projection "
            "coherence guards, skips thumbnail rendering and HTML assembly, "
            "and writes console_data.json ONLY into --fixture-out -- never "
            "into the repo."
        )
    )
    parser.add_argument(
        "--fixture-wave-plan", default=None,
        help="Path to a fixture wave-plan JSON (test-only; substitutes for "
             "the real, frozen inventory/dok-workflow/dok_wave_plan.json).",
    )
    parser.add_argument(
        "--fixture-approvals-manifest", default=None,
        help="Path to a fixture rubric-approvals manifest JSON (test-only; "
             "substitutes for the real tools/dok-review/rubric_approvals.json).",
    )
    parser.add_argument(
        "--fixture-out", default=None,
        help="Directory to write the fixture console_data.json into "
             "(test-only; never the repo).",
    )
    args = parser.parse_args(argv)

    fixture_flags = [args.fixture_wave_plan, args.fixture_approvals_manifest, args.fixture_out]
    provided = [f for f in fixture_flags if f is not None]
    if provided and len(provided) != 3:
        parser.error(
            "--fixture-wave-plan, --fixture-approvals-manifest, and --fixture-out "
            f"must all be provided together (got {len(provided)} of 3) -- "
            "FIXTURE MODE is all-or-nothing"
        )
    return args


def main() -> None:
    args = parse_args()
    fixture_mode = args.fixture_wave_plan is not None

    if fixture_mode:
        print("#" * 78)
        print("### FIXTURE MODE ###")
        print("### Substituting fixture wave plan + fixture approvals manifest.")
        print("### Thumbnail rendering and HTML assembly are SKIPPED.")
        print(f"### console_data.json will be written ONLY to: {args.fixture_out}")
        print("### (never into the repo)")
        print("#" * 78)

    wave_plan_path_effective = Path(args.fixture_wave_plan) if fixture_mode else WAVE_PLAN_PATH
    approvals_path_effective = Path(args.fixture_approvals_manifest) if fixture_mode else RUBRIC_APPROVALS_PATH
    fixture_out_dir = Path(args.fixture_out) if fixture_mode else None
    out_data_path_effective = (fixture_out_dir / "console_data.json") if fixture_mode else OUT_DATA_PATH

    print("=== build_console.py starting ===")

    # -----------------------------------------------------------------
    # GUARD ASSERTS -- part 1: frozen input hashes (start-of-build)
    # -----------------------------------------------------------------
    # FIXTURE MODE skips ONLY the wave-plan entry of FROZEN_HASHES (the
    # fixture file is not the real, frozen wave plan by construction) --
    # every other frozen hash is still enforced exactly as before.
    for path, expected in FROZEN_HASHES.items():
        if fixture_mode and path == WAVE_PLAN_PATH:
            continue
        actual = sha256_file(path)
        guard(
            actual == expected,
            f"{rel(path)} sha256 mismatch at START of build.\n"
            f"  expected: {expected}\n  actual:   {actual}",
        )
    if fixture_mode:
        print("[guard] 3 of 4 frozen input hashes verified (start) -- wave-plan hash check "
              "skipped in FIXTURE MODE (fixture file hashed into meta instead)")
    else:
        print("[guard] all 4 frozen input hashes verified (start)")

    registry_rows = load_registry_rows()
    # NT14 named update (nt14-ingest-4-1-2026-07-23): 900 -> 919 (19 new
    # lesson-4-1 rows, all availability=='optional-catalog').
    guard(len(registry_rows) == 919, f"registry.jsonl must have exactly 919 lines, got {len(registry_rows)}")
    print(f"[guard] registry.jsonl has {len(registry_rows)} lines")

    wave_plan = load_json(wave_plan_path_effective)
    course_map = load_json(COURSE_MAP_PATH)
    alias_map_doc = load_json(ALIAS_MAP_PATH)
    alias_map = alias_map_doc["alias_map"]
    content_readiness = load_json(CONTENT_READINESS_PATH)
    visual_class = load_json(VISUAL_CLASS_PATH)
    manifest = load_json(MANIFEST_PATH)
    approved = dok_review.load_rubric_approvals(approvals_path_effective)

    # Build a flattened uid -> (wave_key, item) index across ALL waves.
    uid_index: dict[str, tuple[str, dict]] = {}
    for wave_key, wave in wave_plan["waves"].items():
        for _lesson, items in wave.items():
            for it in items:
                uid_index[it["item_uid"]] = (wave_key, it)

    # -----------------------------------------------------------------
    # GUARD ASSERTS -- part 2: derived structural checks
    # -----------------------------------------------------------------

    dok_conflict_subset = content_readiness["dok_conflict_subset"]
    conflict_rows = dok_conflict_subset["rows"]
    guard(len(conflict_rows) == 22, f"dok_conflict_subset.rows must have exactly 22 rows, got {len(conflict_rows)}")

    def derive_lesson(legacy_id: str) -> str:
        parts = legacy_id.split("-")
        return "-".join(parts[:2])

    guard(
        all(derive_lesson(r["id"]) == "5-4" for r in conflict_rows),
        "all 22 dok_conflict_subset rows must derive to lesson 5-4",
    )

    dok2v3 = [r for r in conflict_rows if r["dok_a"] == 2 and r["dok_b"] == 3]
    guard(len(dok2v3) == 1, f"expected exactly one dok_a=2/dok_b=3 conflict row, found {len(dok2v3)}")
    guard(
        dok2v3[0]["id"] == "5-4-savvas-q41",
        f"the sole dok2-vs-dok3 conflict row must be id 5-4-savvas-q41, got {dok2v3[0]['id']}",
    )

    wave0 = wave_plan["waves"]["0"]
    wave0_flat = [it for items in wave0.values() for it in items]
    guard(len(wave0_flat) == 42, f"wave 0 flattened must have 42 items, got {len(wave0_flat)}")

    essential_rows = [r for r in visual_class["rows"] if r["recoverability"] == "source_pdf_required"]
    guard(len(essential_rows) == 14, f"essential (source_pdf_required) visual rows must be 14, got {len(essential_rows)}")
    guard(
        all(r["importance"] == "essential" for r in essential_rows),
        "all source_pdf_required rows must carry importance == essential",
    )

    manifest_header = manifest[0]
    manifest_data_rows = manifest[1:]
    guard(
        manifest_header.get("total_unique_ids") == 71,
        f"manifest header total_unique_ids must be 71, got {manifest_header.get('total_unique_ids')}",
    )
    guard(len(manifest_data_rows) == 71, f"manifest data rows must be 71, got {len(manifest_data_rows)}")

    pass_rows = [r for r in manifest_data_rows if r.get("compile_status") == "pass"]
    guard(len(pass_rows) == 64, f"manifest compile_status==pass rows must be 64, got {len(pass_rows)}")

    disk_pdfs = {p.name for p in TIKZ_STAGING_DIR.glob("*.pdf")}
    manifest_pdfs = {r["staging_file"].replace(".tex", ".pdf") for r in pass_rows}
    guard(
        disk_pdfs == manifest_pdfs,
        "the 64 pass rows' staging_file->pdf names must exactly match the .pdf files on disk in "
        f"inventory/tikz-staging/. disk-only={disk_pdfs - manifest_pdfs} manifest-only={manifest_pdfs - disk_pdfs}",
    )
    print(f"[guard] 64 compile-pass rows match 64 pdf files on disk exactly")

    dropped_edges = course_map["dropped_edges"]
    retirement_gap_into_41 = [
        e for e in dropped_edges if e.get("reason") == "retirement-gap" and e.get("target", "").startswith("4-1-")
    ]
    # NT14 named update (nt14-ingest-4-1-2026-07-23): 4 -> 0. course_map.json
    # has been independently regenerated now that 4-1 has real (optional-
    # catalog) items to resolve prereq/echo edges against -- the 4 edges
    # that used to read reason=='retirement-gap' targeting 4-1-* are
    # resolved, not dropped, so 0 remain.
    guard(
        len(retirement_gap_into_41) == 0,
        f"expected exactly 0 retirement-gap dropped_edges targeting 4-1-* "
        f"(resolved against 4-1's real items per course_map.json), got {len(retirement_gap_into_41)}",
    )

    four_one_stranded = content_readiness["four_one_stranded"]
    readiness_edges = four_one_stranded["dangling_edges_into_4_1"]
    guard(len(readiness_edges) == 0, f"four_one_stranded.dangling_edges_into_4_1 must have 0 entries, got {len(readiness_edges)}")

    def edge_key(e):
        return (e["source"], e["target"], e["type"])

    guard(
        {edge_key(e) for e in retirement_gap_into_41} == {edge_key(e) for e in readiness_edges},
        "course_map retirement-gap edges into 4-1 must be identical (as sets of source/target/type) to "
        "content_readiness.four_one_stranded.dangling_edges_into_4_1",
    )
    print("[guard] 0 dangling retirement-gap edges into 4-1 verified consistent across both sources (nt14-ingest-4-1-2026-07-23)")

    # -----------------------------------------------------------------
    # GUARD ASSERTS -- part 2b: canonical verification-projection coherence
    #
    # NT7 re-pin: the wave plan is no longer just a static planning
    # artifact -- it carries the canonical review-log projection
    # (review_state, additive) and an overlaid dok_status that can now read
    # 'verified'. This console's build must be able to SEE that projection
    # and refuse to build if it is internally incoherent, rather than
    # silently trusting whatever dok_status a wave-plan row happens to
    # carry. `approved` was already loaded above via
    # dok_review.load_rubric_approvals(approvals_path_effective) -- read-only,
    # same fail-closed semantics the tool and generator both rely on.
    # -----------------------------------------------------------------
    all_wave_items = [it for wave in wave_plan["waves"].values() for items in wave.values() for it in items]

    verified_rows = [it for it in all_wave_items if it.get("review_state") == "verified"]
    status_verified_rows = [it for it in all_wave_items if it.get("dok_status") == "verified"]
    verified_uids = {it["item_uid"] for it in verified_rows}
    status_verified_uids = {it["item_uid"] for it in status_verified_rows}

    # (a) plan-internal coherence: dok_status's 'verified' value is NEVER
    # anything other than an overlay of review_state=='verified' (see
    # gen_dok_wave_plan.py's "Canonical verification projection" section) --
    # the two sets of item_uids must be identical.
    guard(
        verified_uids == status_verified_uids,
        "plan-internal coherence: the set of wave-plan items with "
        "review_state=='verified' must equal the set with dok_status=='verified'. "
        f"review_state-only={sorted(verified_uids - status_verified_uids)} "
        f"dok_status-only={sorted(status_verified_uids - verified_uids)}",
    )

    # (b) if the rubric-approvals manifest is EMPTY (no teacher approval
    # recorded anywhere), NOTHING may be marked verified -- fail loudly and
    # name both the empty manifest and the offending uids.
    if not approved:
        guard(
            len(verified_uids) == 0 and len(status_verified_uids) == 0,
            f"the rubric-approvals manifest at {display_path(approvals_path_effective)} is EMPTY "
            "(no approved rubric versions) but the wave plan carries verified item(s) -- nothing "
            "may be marked verified until a teacher approves a rubric version. "
            f"review_state-verified uids={sorted(verified_uids)} "
            f"dok_status-verified uids={sorted(status_verified_uids)}",
        )

    # (c) count them for meta.
    canonical_verified_count = len(verified_uids)
    print(
        "[guard] canonical verification projection coherence OK "
        f"(approved manifest versions={sorted(approved.keys())}, verified_count={canonical_verified_count})"
    )

    print("=== all guard asserts passed ===\n")

    # -----------------------------------------------------------------
    # Thumbnails: render each of the 64 compile-pass PDFs to PNG
    #
    # FIXTURE MODE skips this entirely -- no PDF rendering, no thumbnails/
    # writes, nothing touched under HERE. It exists purely to smoke-test the
    # canonical-projection coherence guards above against a fixture wave
    # plan + approvals manifest.
    # -----------------------------------------------------------------
    if fixture_mode:
        print("[fixture] thumbnail rendering SKIPPED (FIXTURE MODE)")
    else:
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
        pdftoppm = shutil.which("pdftoppm")
        gswin = shutil.which("gswin64c")

        # The 2 teacher-flagged rows (manifest_header["needs_teacher_confirmation_ids"])
        # get a high-DPI render so the click-to-zoom lightbox in console_template.html
        # shows a crisp figure instead of an upscaled 60-DPI thumbnail. Every other
        # row stays at the original 60 DPI contact-sheet resolution.
        FLAGGED_THUMB_IDS = set(manifest_header["needs_teacher_confirmation_ids"])
        FLAGGED_DPI = 180
        DEFAULT_DPI = 60

        rendered = 0
        skipped = 0
        for row in pass_rows:
            bank_id = row["bank_id"]
            pdf_path = TIKZ_STAGING_DIR / row["staging_file"].replace(".tex", ".pdf")
            out_png = THUMB_DIR / f"{bank_id}.png"
            out_stub = THUMB_DIR / bank_id  # pdftoppm -singlefile appends .png itself

            is_flagged = bank_id in FLAGGED_THUMB_IDS
            dpi = FLAGGED_DPI if is_flagged else DEFAULT_DPI

            # Flagged rows always force a fresh render at FLAGGED_DPI (bypassing the
            # up-to-date skip below) so a previously-rendered 60-DPI PNG is never
            # left stale for the two teacher-facing zoom targets.
            if not is_flagged and out_png.exists() and out_png.stat().st_mtime >= pdf_path.stat().st_mtime:
                skipped += 1
                continue

            ok = False
            if pdftoppm:
                proc = subprocess.run(
                    ["pdftoppm", "-png", "-r", str(dpi), "-singlefile", str(pdf_path), str(out_stub)],
                    capture_output=True,
                    text=True,
                )
                ok = proc.returncode == 0 and out_png.exists()
                if not ok:
                    print(f"  [warn] pdftoppm failed for {bank_id}: {proc.stderr.strip()}")

            if not ok and gswin:
                proc = subprocess.run(
                    [
                        "gswin64c",
                        "-dSAFER",
                        "-dBATCH",
                        "-dNOPAUSE",
                        "-sDEVICE=png16m",
                        f"-r{dpi}",
                        f"-sOutputFile={out_png}",
                        str(pdf_path),
                    ],
                    capture_output=True,
                    text=True,
                )
                ok = proc.returncode == 0 and out_png.exists()
                if not ok:
                    print(f"  [warn] gswin64c fallback failed for {bank_id}: {proc.stderr.strip()}")

            guard(ok, f"failed to render thumbnail for {bank_id} via both pdftoppm and gswin64c fallback")
            rendered += 1

        png_count = len(list(THUMB_DIR.glob("*.png")))
        guard(png_count == 64, f"expected exactly 64 PNG thumbnails, found {png_count}")
        print(
            f"[thumbnails] rendered={rendered} skipped(up-to-date)={skipped} total_pngs={png_count} "
            f"(flagged high-DPI ids {sorted(FLAGGED_THUMB_IDS)} forced to {FLAGGED_DPI} DPI)\n"
        )

    # -----------------------------------------------------------------
    # SECTION 1 -- Lesson 4-1 revive vs retire
    # -----------------------------------------------------------------

    def fmt_edge(e):
        return f"{e['source']} {e['type']}→{e['target']}"

    edges_str = "; ".join(fmt_edge(e) for e in retirement_gap_into_41)
    # NT14 named update (nt14-ingest-4-1-2026-07-23): retirement_gap_into_41
    # is now empty (course_map.json independently regenerated -- the 4 edges
    # that used to dangle into 4-1 are resolved against 4-1's real
    # optional-catalog items). The "downstream_effects" bullets below no
    # longer describe something a revive/retire DECISION would unblock or
    # need to re-point; they are phrased as historical/status context
    # instead, naming the 4 specific edges this superseded.
    formerly_dangling_edges_str = (
        "4-3-tryit-1 prereq→4-1-savvas-q10; 6-3-savvas-q54 echoes→4-1-savvas-q17; "
        "6-4-savvas-q13 echoes→4-1-savvas-q19; 4-5-savvas-q25 echoes→4-1-savvas-q26"
    )

    evidence = [
        {
            "fact": "As of 2026-05-13 the department skipped L41 (Klimsara confirmed); cadence jumped directly to L43.",
            "source": "CONTINUATION_PROMPT.md:32 (as cited by inventory/topic-4-1/DIAGNOSIS.md)",
        },
        {
            "fact": "An earlier planning note lists 4-1 as part of the planned lesson set: \"4-1,4-3,4-4,4-5 (LEHS 8 question assessment)\".",
            "source": "A2LessonSelection.txt:4",
        },
        {
            "fact": "CLAUDE.md still reads \"### Lesson 4-1 (ready, Fri F / Mon A start)\" with a full P1/P2/P3 table -- this is stale and contradicts the documented 2026-05-13 retirement.",
            "source": "CLAUDE.md:45",
        },
        {
            "fact": "questionbank/calibration/4-1.json is fully authored (47 lines), not a placeholder: item_analysis maps all 5 Savvas Examples to practice-item numbers by DOK; notes name practice items #20/#22/#25/#26 (all anchored to Example 3) as the Savvas-declared DOK-3 anchors; dok2_anchors/dok3_anchors arrays are empty by design, meant to be backfilled only after ingestion.",
            "source": "inventory/topic-4-1/DIAGNOSIS.md lines 22-43 (describing questionbank/calibration/4-1.json)",
        },
        {
            "fact": "61 screenshots exist on disk for lesson 4-1: 2 concept + 1 launch + 6 example/try-it (question only) + 37 practice-item images (q8-q26) + 15 Teacher Edition addenda.",
            "source": "inventory/topic-4-1/DIAGNOSIS.md lines 45-57 (questionbank/images/4-1_*, cross-checked against inventory-4-1-assets.json)",
        },
        {
            "fact": "15 skeleton stubs exist in skeletons/4-1_practice_skeletons.json (q8-q19, q21, q23, q24); every one is a pristine, un-transcribed \"TODO: transcribe...\" placeholder -- not a single one has been filled in.",
            "source": "inventory/topic-4-1/DIAGNOSIS.md lines 69-79",
        },
        {
            "fact": "NT14 NAMED UPDATE (nt14-ingest-4-1-2026-07-23, 2026-07-23): OUTDATED -- '0 registry rows exist for lesson 4-1' was the pre-ingestion count. 19 registry rows now exist (4-1-savvas-q8..q26, registry.jsonl lines 901-919), every one carrying availability=='optional-catalog'. This does NOT make 4-1 required, ready-to-teach, revived, or auto-scheduled -- see meta.identity_reconciliation.optional_catalog_identities and this section's effort-path notes below.",
            "source": "questionbank/registry.jsonl lines 901-919 (nt14-ingest-4-1-2026-07-23); supersedes inventory/topic-4-1/DIAGNOSIS.md line 92",
        },
        {
            "fact": "No a2_4-1_SE.* or a2_4-1_TE.* (pdf or tex) exists anywhere in the repo, while nine sibling lessons (4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5) each have both SE and TE source.",
            "source": "inventory/topic-4-1/DIAGNOSIS.md lines 94-99",
        },
        {
            "fact": "The four DOK-3 anchor items (Savvas practice #20/#22/#25/#26) have BOTH _question.png and _answer.png screenshots on disk, but were never even generated as skeleton stubs -- the gap is one step earlier than \"un-transcribed,\" it is \"not yet generated.\"",
            "source": "inventory/topic-4-1/DIAGNOSIS.md lines 59-64, 81-84",
        },
        {
            "fact": "tagging/4-1_*.jsonl is documented as deleted during the 2026-05-13 retirement cull, alongside the L41 tex retirement and Supabase row deletion.",
            "source": "CONTINUATION_PROMPT.md:192 (as cited by inventory/topic-4-1/DIAGNOSIS.md lines 100-101, 128-130)",
        },
        {
            "fact": "L41 lesson tex now lives only in legacy/tex/ (46 files: P1=14, P2=18, P3=14); tex/ has zero L41_* files.",
            "source": "inventory/topic-4-1/DIAGNOSIS.md lines 102-108",
        },
        {
            "fact": "NT14 NAMED UPDATE (2026-07-23): whether ingestion was EVER attempted is no longer unknown going forward -- 19 items were deliberately ingested 2026-07-23 as OPTIONAL CATALOG content (nt14-ingest-4-1-2026-07-23). Whether an EARLIER, pre-NT14 attempt was made and culled during the 2026-05-13 department skip remains UNKNOWN from disk alone, exactly as before; the department-skip history itself is unchanged and is not reversed or reinterpreted by this ingestion.",
            "source": "inventory/topic-4-1/DIAGNOSIS.md lines 132-158 (original epistemic note); nt14-ingest-4-1-2026-07-23 (2026-07-23 named update)",
        },
    ]

    section1 = {
        "heading": "Lesson 4-1: Revive vs Retire",
        "evidence": evidence,
        "staged_state": four_one_stranded["staged"],
        "dangling_edges": retirement_gap_into_41,
        "options": {
            "revive": {
                "downstream_effects": [
                    "NT14 NAMED UPDATE (nt14-ingest-4-1-2026-07-23): the 4 retirement-gap edges into "
                    f"4-1 ({formerly_dangling_edges_str}) are ALREADY resolved -- course_map.json was "
                    "independently regenerated once 4-1 had real (optional-catalog) items to resolve "
                    "them against, so there is nothing left for a revive decision to unblock on this "
                    "front. A genuine revive (to required/ready-to-teach) instead means promoting "
                    "these 19 rows out of availability=='optional-catalog'.",
                ],
                "effort_paths": {
                    "revive-ingestion-only": (
                        "NT14 NAMED UPDATE (nt14-ingest-4-1-2026-07-23): the transcribe+append step this "
                        "path used to describe as future work is DONE -- all 19 practice items (q8-q26) "
                        "were transcribed and appended to registry.jsonl 2026-07-23, but as "
                        "availability=='optional-catalog' rows, not as required/ready-to-teach content. "
                        "What remains for an actual revive decision: backfill calibration "
                        "dok2_anchors/dok3_anchors (still empty in questionbank/calibration/4-1.json), and "
                        "a separate course-policy call to flip these 19 rows from optional-catalog to "
                        "required/active. NOT blocked on SE/TE."
                    ),
                    "revive-full-rebuild": (
                        "All of ingestion-only PLUS SE/TE export from Savvas + PDF→LaTeX conversion + full "
                        "tex/L41_P{1,2,3} packet + pacer rebuild (RECOVERY_PLAN Steps 3b+6). BLOCKED on acquiring "
                        "a2_4-1_SE/TE."
                    ),
                },
                "risks": [
                    "Overrides a documented department-level decision -- if the 2026-05-13 skip was POLICY rather "
                    "than time pressure, revival conflicts with the department",
                    "NT14 NAMED UPDATE: the 19 serial transcriptions are DONE (2026-07-23, as optional-catalog "
                    "rows) -- this risk is now about promoting already-spent ingestion effort to required "
                    "status on a lesson that may never be taught, not about spending it in the first place",
                    "Full-rebuild path indefinitely blocked on SE/TE acquisition",
                ],
            },
            "retire": {
                "downstream_effects": [
                    "NT14 NAMED UPDATE (nt14-ingest-4-1-2026-07-23): the 4 lessons that used to carry "
                    f"dangling edges into 4-1 ({formerly_dangling_edges_str}) no longer need bridge "
                    "re-pointing -- course_map.json already resolves those edges against 4-1's real "
                    "(optional-catalog) items. A retire decision now would instead mean formally excluding "
                    "these 19 rows from the catalog (a distinct action from the pre-ingestion 'never built' "
                    "state this section originally described).",
                    "CLAUDE.md:45 stale 'ready' table needs correcting to retired",
                ],
                "effort": (
                    "NT14 NAMED UPDATE: bridge re-pointing is no longer part of this effort (course_map.json "
                    "already resolves the 4 formerly-dangling edges against 4-1's real items) -- retiring "
                    "today means formally excluding the 19 already-ingested optional-catalog rows from the "
                    "catalog + CLAUDE.md correction; no further ingestion work."
                ),
                "risks": [
                    "Staged work (61 screenshots + authored calibration, now 19 ingested optional-catalog "
                    "rows) permanently excluded from required content",
                    "Inverse variation on-ramp into Topic 4 rational functions lost from the graph",
                ],
            },
        },
        "recommendation": {
            "label": "FABLE RECOMMENDATION",
            "confidence": 0.7,
            "visually_distinct": True,
            "text": "Revive via ingestion-only from the existing 61 screenshots.",
            # NT14 named update (nt14-ingest-4-1-2026-07-23): this recommendation predates the
            # 2026-07-23 ingestion. The ingestion-only ACTION it recommends is now DONE (as
            # availability=='optional-catalog' rows, not required/ready-to-teach) -- what remains
            # open is the separate course-policy call to promote them. Recorded here as
            # status/context, not re-decided by this build.
            "note": (
                "NT14 NAMED UPDATE (2026-07-23): the ingestion-only action this recommendation "
                "proposed is DONE (19 rows, availability=='optional-catalog'; see this section's "
                "evidence and effort_paths above). This recommendation and its rationale/"
                "residual_risk below are preserved as the historical record of what was recommended "
                "BEFORE that ingestion -- they are not re-decided or re-scored by this NT14 build. "
                "The still-open decision is whether/when to promote these 19 rows to required/"
                "ready-to-teach status, per course policy."
            ),
            "rationale": [
                "(a) NT14 NAMED UPDATE: 4 lessons carried dangling retirement-gap edges into 4-1 at the time "
                "this recommendation was made; course_map.json has since been independently regenerated and "
                "those edges are now resolved against 4-1's real (optional-catalog) items, so this specific "
                "cost no longer applies to a retirement decision made today",
                "(b) the ingest pipeline is already staged (calibration + screenshots + 15 stubs), making "
                "ingestion-only the lowest-effort path to graph integrity",
                "(c) inverse variation is the conceptual on-ramp for Topic 4's rational functions",
                "(d) the 4 missing DOK-3 anchor stubs are mechanical to create from their screenshots",
            ],
            "residual_risk": (
                "If the 5/13 dept skip was department POLICY rather than time pressure, retire instead -- "
                "that is precisely the judgment only the teacher can make, hence 0.7 not higher. (NT14 named "
                "update: retiring today would no longer require re-pointing the 4 edges named above -- "
                "course_map.json already resolves them against 4-1's real items -- it would instead mean "
                "formally excluding the 19 already-ingested optional-catalog rows from the catalog.)"
            ),
        },
        "decision": {
            "decision_id": "s1-revive-or-retire-4-1",
            "actions": ["revive-ingestion-only", "revive-full-rebuild", "retire-and-repoint", "defer"],
        },
    }

    # -----------------------------------------------------------------
    # SECTION 2 -- 22 DOK-conflict pairs
    # -----------------------------------------------------------------

    def build_copy(legacy_id: str, uid: str, line: int, dok_given: int) -> dict:
        reg = registry_rows.get(line)
        guard(reg is not None, f"registry line {line} not found for {legacy_id}/{uid}")

        entry = uid_index.get(uid)
        guard(entry is not None, f"item_uid {uid} ({legacy_id}, line {line}) not found in flattened wave plan")
        wave_key, witem = entry
        guard(
            witem["registry_line"] == line and witem["id"] == legacy_id,
            f"wave plan entry for {uid} does not match ({legacy_id}, line {line}): "
            f"got id={witem['id']} line={witem['registry_line']}",
        )
        guard(
            witem["dok"] == dok_given,
            f"wave plan dok ({witem['dok']}) does not match dok_conflict_subset dok ({dok_given}) for {uid}",
        )

        alias_entries = alias_map.get(legacy_id, {}).get("item_uids", [])
        alias_entry = next((e for e in alias_entries if e["registry_line"] == line), None)
        guard(
            alias_entry is not None and alias_entry["item_uid"] == uid,
            f"alias_map[{legacy_id}] has no item_uids entry matching (uid={uid}, registry_line={line})",
        )

        return {
            "item_uid": uid,
            "registry_line": line,
            "lesson": reg["lesson"],
            "dok": dok_given,
            "role": witem["role"],
            "wave": wave_key,
            "te_bucket": witem["te_bucket"],
            "match_quality": witem["match_quality"],
            "dok_status": witem["dok_status"],
            "prompt": reg["prompt"],
            "answers": reg["answers"],
            "correct": reg["correct"],
            "notes": reg["notes"],
            "registry_dok_rationale": reg["dok_rationale"],
            "source": reg["source"],
            "prompt_sha1": alias_entry["prompt_sha1"],
            "dok_rationale_derived": dok_rationale_derived(
                witem["dok_status"], witem["te_bucket"], witem["match_quality"]
            ),
            # rc-merge-auth-5-4-2026-07-23 (additive): carried verbatim from
            # the wave-plan item (which itself carries it verbatim from the
            # registry row). 'active' for the 21 non-alias copies across
            # these 22 pairs' 44 total copies; 'merged-alias' for the one
            # alias copy per pair.
            "status": witem.get("status", "active"),
        }

    pairs = []
    highlight_id = None
    for row in conflict_rows:
        legacy_id = row["id"]
        copy_a = build_copy(legacy_id, row["uid_a"], row["line_a"], row["dok_a"])
        copy_b = build_copy(legacy_id, row["uid_b"], row["line_b"], row["dok_b"])
        if row["dok_a"] == 2 and row["dok_b"] == 3:
            highlight_id = legacy_id

        # rc-merge-auth-5-4-2026-07-23 (additive, DELIBERATE join-level
        # resolution): sourced from the dedup map's OWN "resolved_alias" key
        # (inventory/dedup/item_uid_alias_map.json, SUB-B's additive
        # enrichment) -- never re-derived from the wave-plan items' row-level
        # alias_of above, though the two are cross-checked for agreement
        # here. Every one of these 22 section2 pairs IS one of the 22
        # merge-authorized groups (dok_conflict_subset's rows == the merge's
        # 22 pairs, guarded elsewhere in this script), so a resolved_alias
        # entry must be present for every single one.
        resolved_alias = alias_map.get(legacy_id, {}).get("resolved_alias")
        guard(
            resolved_alias is not None,
            f"legacy_id {legacy_id!r} is one of the 22 section2 DOK-conflict pairs but "
            "item_uid_alias_map.json carries no resolved_alias entry for it",
        )
        copies_by_uid = {c["item_uid"]: c for c in (copy_a, copy_b)}
        guard(
            set(copies_by_uid) == {resolved_alias["alias_uid"], resolved_alias["survivor_uid"]},
            f"legacy_id {legacy_id!r}: resolved_alias's (alias_uid, survivor_uid) does not match "
            f"this pair's two copies (copies={sorted(copies_by_uid)}, "
            f"resolved_alias={resolved_alias['alias_uid']!r}/{resolved_alias['survivor_uid']!r})",
        )
        guard(
            copies_by_uid[resolved_alias["alias_uid"]]["status"] == "merged-alias"
            and copies_by_uid[resolved_alias["survivor_uid"]]["status"] != "merged-alias",
            f"legacy_id {legacy_id!r}: resolved_alias's alias_uid/survivor_uid does not agree "
            "with the copies' own row-level status field",
        )

        pairs.append(
            {
                "legacy_id": legacy_id,
                "decision_id": f"s2-{legacy_id}",
                "copies": [copy_a, copy_b],
                "resolved_alias": resolved_alias,
            }
        )

    guard(highlight_id is not None, "no highlight_id (dok2-vs-dok3 pair) found while building section2 pairs")

    section2_intro = (
        "Each of the 22 pairs below is one legacy bank id carried by two distinct registry rows (two "
        "item_uids) whose DOK labels differ. Both copies are shown in full, side by side. Four actions are "
        "available for each pair — keep-both, reconcile-labels (pick the authoritative DOK label; both rows "
        "stay), merge-candidate (route to the collision review queue), and needs-source-check — and none is "
        "a default or an expected outcome. These pairs are sequenced ahead of the same-DOK prompt-drift "
        "collisions only because DOK labels affect wave placement. 21 pairs differ dok1-vs-dok2; "
        "5-4-savvas-q41 is the sole dok2-vs-dok3 pair."
    )

    section2 = {
        "count": len(conflict_rows),
        "intro": section2_intro,
        "highlight_id": highlight_id,
        "actions": ["keep-both", "reconcile-labels", "merge-candidate", "needs-source-check"],
        "pairs": pairs,
    }

    # -----------------------------------------------------------------
    # SECTION 3 -- TikZ figure contact sheet (64 compile-pass figures)
    # -----------------------------------------------------------------
    #
    # IMPORTANT: MANIFEST.json's own "item_uid" field is NOT the real opaque
    # item_uid -- it is just a copy of bank_id (the legacy id). The real
    # item_uid must be resolved through the frozen alias map, keyed by
    # bank_id. Some legacy ids are ambiguous (2 registry rows share the same
    # bank_id); those must never be silently pinned to one -- both
    # candidates are carried and the console leaves item_uid/registry_line
    # null with ambiguous:true.

    def resolve_manifest_identity(bank_id: str) -> dict:
        entry = alias_map.get(bank_id)
        guard(entry is not None, f"manifest bank_id {bank_id!r} not found in alias_map")
        uids = entry["item_uids"]
        if len(uids) == 1:
            u = uids[0]
            return {
                "legacy_id": bank_id,
                "item_uid": u["item_uid"],
                "registry_line": u["registry_line"],
                "ambiguous": False,
            }
        if len(uids) == 2:
            return {
                "legacy_id": bank_id,
                "item_uid": None,
                "registry_line": None,
                "ambiguous": True,
                "uid_candidates": [
                    {"item_uid": u["item_uid"], "registry_line": u["registry_line"]} for u in uids
                ],
            }
        raise GuardFailure(
            f"unexpected alias_map cardinality ({len(uids)}) for manifest bank_id {bank_id!r} "
            "(expected 1 or 2 item_uids entries)"
        )

    manifest_identities = {r["bank_id"]: resolve_manifest_identity(r["bank_id"]) for r in manifest_data_rows}

    # Guard asserts for FIX 1 (identity resolution).
    guard(
        len(manifest_identities) == len(manifest_data_rows),
        f"expected all {len(manifest_data_rows)} manifest bank_ids to resolve through the alias map, "
        f"got {len(manifest_identities)}",
    )
    ambiguous_bank_ids = sorted(bid for bid, ident in manifest_identities.items() if ident["ambiguous"])
    guard(
        len(ambiguous_bank_ids) == 4,
        f"expected exactly 4 ambiguous manifest bank_ids, got {len(ambiguous_bank_ids)}: {ambiguous_bank_ids}",
    )
    EXPECTED_AMBIGUOUS_BANK_IDS = {
        "5-1-savvas-q45",
        "5-1-savvas-q48",
        "5-4-savvas-q44",
        "5-5-savvas-q36",
    }
    guard(
        set(ambiguous_bank_ids) == EXPECTED_AMBIGUOUS_BANK_IDS,
        f"expected the 4 ambiguous manifest bank_ids to be exactly {sorted(EXPECTED_AMBIGUOUS_BANK_IDS)}, "
        f"got {ambiguous_bank_ids}",
    )
    guard(
        manifest_identities["4-3-ex-6"]["item_uid"] == "iu_5610833d718c"
        and manifest_identities["4-3-ex-6"]["registry_line"] == 49,
        "4-3-ex-6 must resolve unambiguously to item_uid iu_5610833d718c / registry_line 49",
    )
    guard(
        manifest_identities["6-4-savvas-q30"]["item_uid"] == "iu_939654beefb4"
        and manifest_identities["6-4-savvas-q30"]["registry_line"] == 614,
        "6-4-savvas-q30 must resolve unambiguously to item_uid iu_939654beefb4 / registry_line 614",
    )

    def carry_manifest_row(row: dict) -> dict:
        """Full manifest row with the bogus raw item_uid dropped and replaced
        by the alias-map-resolved identity fields."""
        carried = {k: v for k, v in row.items() if k != "item_uid"}
        carried.update(manifest_identities[row["bank_id"]])
        return carried

    # -----------------------------------------------------------------
    # Optional RC/teacher decisions export -- recorded context only, not an
    # approval or sign-off state established by this builder. If the file is
    # absent the builder proceeds exactly as before (no recorded_context on
    # any flagged row, no crash).
    # -----------------------------------------------------------------

    RC_ACTION_VERBS = {
        "confirm": "confirmed",
        "reject": "rejected",
        "needs-rework": "flagged needs-rework",
    }

    def compose_recorded_context_parenthetical(note: str) -> str:
        """Derive a short parenthetical from an RC decision's own note text.
        Every word in the result is drawn from the note -- this only trims
        trailing punctuation and, where the note ends in a bare copular
        clause ("<subject> is <adjective phrase>", optionally with the
        subject wrapped in the note's own parentheses), drops the linking
        "is" so the clause reads as a compact adjectival tag."""
        n = note.strip()
        if n.endswith("."):
            n = n[:-1]

        m = re.search(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s+is\s+(\w+)$", n)
        if m:
            detail, verdict = m.group(1), m.group(2)
            verdict = {"acceptable": "accepted"}.get(verdict.lower(), verdict)
            tag = detail.split(",")[0].strip()
            return f"{tag}, {verdict}"

        m2 = re.search(r"\bis\b", n)
        if m2:
            combined = n[: m2.start()] + n[m2.end() :]
            return re.sub(r"\s+", " ", combined).strip()

        return n

    def load_rc_decisions_by_decision_id() -> dict[str, dict]:
        """Read the optional RC decisions export (read-only) and return its
        section-3 decisions keyed by decision_id. Returns {} if the file
        does not exist -- the build must never crash on its absence."""
        if not RC_DECISIONS_PATH.exists():
            return {}
        doc = load_json(RC_DECISIONS_PATH)
        return {d["decision_id"]: d for d in doc.get("decisions", []) if d.get("section") == 3}

    def build_recorded_context(rc_decision: dict) -> dict:
        """recorded_context is display-only context carried from the RC
        export -- not an approval or sign-off state established here."""
        reviewer = rc_decision["reviewer"]
        action = rc_decision["action"]
        date_part = rc_decision["timestamp"][:10]
        verb = RC_ACTION_VERBS.get(action, action)
        parenthetical = compose_recorded_context_parenthetical(rc_decision["note"])
        return {
            "status_line": f"{verb} by {reviewer} {date_part} ({parenthetical})",
            "action": action,
            "reviewer": reviewer,
            "timestamp": rc_decision["timestamp"],
            "note": rc_decision["note"],
        }

    rc_decisions_by_id = load_rc_decisions_by_decision_id()

    # Console-authored, neutral replacements for the raw MANIFEST.json notes
    # on the 2 teacher-flagged rows (the raw notes contain first-person build
    # narration -- "Verified visually via rendered PNG", "Confirm ... before
    # wiring" -- which must not be presented as console copy).
    FLAGGED_INTERPRETIVE_SUMMARIES = {
        "4-3-ex-6": (
            "Interpretive choice flagged by the NT2 build: the source text says 'rectangular prism with a "
            "square base'; the figure renders Option 1 as a cube (all edges 2x) because the stated volume "
            "(2x)^3 implies height = base side = 2x. The figure shows both package options (Option 1 prism, "
            "Option 2 cylinder with r = x, h = 2x). The teacher decision is whether this reading is acceptable."
        ),
        "6-4-savvas-q30": (
            "Schematic layout flagged by the NT2 build: focus F below a curved surface; epicenter E on the "
            "surface directly above F; station S elsewhere on the surface; arc ES highlighted; dashed arcs "
            "from F represent seismic waves. Relative positions follow the item text; exact distances, "
            "curvature, and wave count are illustrative choices. The teacher decision is whether this layout "
            "is acceptable."
        ),
    }

    manifest_by_id = {r["bank_id"]: r for r in manifest_data_rows}
    needs_confirmation_ids = manifest_header["needs_teacher_confirmation_ids"]

    flagged = []
    for bank_id in needs_confirmation_ids:
        row = manifest_by_id[bank_id]
        flag_kind = row["flags"][0] if row.get("flags") else None
        carried = carry_manifest_row(row)
        carried.pop("notes", None)
        carried["display_provenance"] = (
            "NT2 build QA (tikz-staging MANIFEST): compile PASS; PNG rendered during batch QA."
        )
        carried["interpretive_summary"] = FLAGGED_INTERPRETIVE_SUMMARIES[bank_id]
        carried["flag_kind"] = flag_kind
        decision_id = f"s3-fig-{bank_id}"
        carried["decision_id"] = decision_id

        rc_decision = rc_decisions_by_id.get(decision_id)
        if rc_decision is not None:
            carried["recorded_context"] = build_recorded_context(rc_decision)

        flagged.append(carried)

    # Count of flagged rows carrying recorded_context (RC/teacher decisions already
    # recorded in teacher_decisions_rc_v1.json). Used below to build section6's
    # recorded-exclusion note. Computed here, not hardcoded, so it degrades to 0
    # automatically when teacher_decisions_rc_v1.json is absent (rc_decisions_by_id
    # is {} in that case -- see load_rc_decisions_by_decision_id above).
    recorded_flagged_count = sum(1 for f in flagged if "recorded_context" in f)

    # Held / no_asset / reclassified rows keep their notes verbatim (they are
    # neutral build-QA notes, not first-person narration) -- only the
    # identity fields are fixed up.
    held = [carry_manifest_row(r) for r in manifest_data_rows if r["status"] == "held-teacher"]
    no_asset = [carry_manifest_row(r) for r in manifest_data_rows if r["status"] == "no-asset"]
    reclassified = [
        carry_manifest_row(r) for r in manifest_data_rows if r["status"] == "reclassified-map->table"
    ]

    figures = []
    for r in pass_rows:
        identity = manifest_identities[r["bank_id"]]
        figures.append(
            {
                "bank_id": r["bank_id"],
                **identity,
                "lesson": r["lesson"],
                "figure_type": r["figure_type"],
                "status": r["status"],
                "compile_status": r["compile_status"],
                "pdf_file": r["staging_file"].replace(".tex", ".pdf"),
                "thumb_key": r["bank_id"],
            }
        )
    figures.sort(key=lambda f: (f["lesson"], f["bank_id"]))

    partition = dict(manifest_header["status_split"])
    partition["total_unique_ids"] = manifest_header["total_unique_ids"]
    partition["regenerated_and_compiling_total"] = manifest_header["regenerated_and_compiling_total"]

    section3 = {
        "partition": partition,
        "flagged": flagged,
        "flag_actions": ["confirm", "reject", "needs-rework"],
        "held": held,
        "no_asset": no_asset,
        "reclassified": reclassified,
        "figures": figures,
    }

    # -----------------------------------------------------------------
    # SECTION 4 -- 14 essential missing visuals (source_pdf_required)
    # -----------------------------------------------------------------

    section4_items = []
    for row in essential_rows:
        legacy_id = row["id"]
        registry_line = row["registry_line"]
        alias_entries = alias_map.get(legacy_id, {}).get("item_uids", [])
        matching = [e for e in alias_entries if e["registry_line"] == registry_line]
        guard(
            len(matching) == 1,
            f"expected exactly one alias_map entry for ({legacy_id}, line {registry_line}), found {len(matching)}",
        )
        item_uid = matching[0]["item_uid"]

        reg = registry_rows.get(registry_line)
        guard(reg is not None, f"registry line {registry_line} not found for essential visual {legacy_id}")

        page = reg.get("page")
        if page not in (None, ""):
            source_requirement = f"Savvas SE/TE page {page} (from registry source: {reg['source']})"
        else:
            source_requirement = "source PDF page unknown — needs SE/TE lookup"

        section4_items.append(
            {
                "legacy_id": legacy_id,
                "item_uid": item_uid,
                "registry_line": registry_line,
                "lesson": row["lesson"],
                "visual_type": row["visual_type"],
                "prompt_excerpt": row["prompt_excerpt"],
                "depicts": row["recoverability_rationale"],
                "why_essential": row["importance_rationale"],
                "registry_source": reg["source"],
                "registry_page": page,
                "source_requirement": source_requirement,
                "decision_id": f"s4-{legacy_id}-L{registry_line}",
            }
        )

    section4_items.sort(key=lambda x: x["registry_line"])

    section4 = {
        "items": section4_items,
        "count": len(section4_items),
        "actions": ["provide-source", "accept-gap", "reclassify"],
    }

    # -----------------------------------------------------------------
    # SECTION 5 -- DOK acceptance rubric v0.2 + wave-0 sample
    #
    # v0.1-PROPOSED received request-changes from RC on 2026-07-20 (that decision
    # lives in the RC export, teacher_decisions_rc_v1.json, decision s5-rubric-v0.1
    # -- it is NOT re-recorded here, only carried forward as status context).
    # v0.2 is the requested revision: RC's authority hierarchy replaces
    # the flat v0.1 criteria list. Full prose lives in DOK_RUBRIC_v0.2.md; this
    # dict is a structured summary for the console. Approval state below is read
    # solely from the rubric_approvals.json manifest at build time (see `approved`
    # and the rubric_watermark/manifest_state_sentence branches above) -- v0.2 is
    # APPROVED as of 2026-07-20T19:06:13-04:00, but verification of any review-log
    # entry still requires that entry's own rubric_version to be a manifest key
    # AND its recorded_at to be at or after that key's approved_at (no retroactive
    # verification).
    # -----------------------------------------------------------------

    RUBRIC_HIERARCHY = [
        "Confirmed textbook DOK governs exact, unchanged textbook items.",
        "Conflicting or provenance-missing textbook labels remain UNRESOLVED pending source verification.",
        "Adapted, split, extended, and teacher-authored items are rated by their actual cognitive demand.",
        "DOK measures cognitive demand, not difficulty.",
        "Any teacher override requires rationale and provenance.",
    ]

    def v02_rule_annotation(dok_status: str, role, dok: int, source: str, legacy_id: str) -> dict:
        """Hypothetical-only: how DOK_RUBRIC_v0.2.md's authority hierarchy WOULD classify this
        wave-0 sample item, under v0.2. This is an illustration, not a recorded classification --
        approval state comes solely from the rubric_approvals.json manifest, and this function
        itself never records or reflects any approval, regardless of what it returns.

        The primary rule (1 vs 2) is decided ONLY by whether this exact item is named as an
        item-level anchor in its lesson's calibration file -- NOT by dok_status alone.
        dok_status == 'calibrated' is a LESSON-LEVEL provenance status (the lesson's calibration
        file has real anchors *somewhere*) -- per inventory/dok-workflow/gen_dok_wave_plan.py's own
        comment, 'it is never earned by a single row being reviewed'. Only the four items actually
        named in dok2_anchors/dok3_anchors carry a per-row, on-disk textbook DOK trace with an
        articulated rationale; everything else in the lesson -- including other calibrated rows --
        has no such trace and must fall to rule 2, UNRESOLVED pending source verification.
        """
        lesson = derive_lesson(legacy_id)
        anchors = load_calibration_item_anchors(lesson)
        anchor = anchors.get(legacy_id)

        if anchor is not None:
            rule = 1
            text = (
                f"Would be classified under rule 1 (confirmed textbook DOK governs exact, unchanged "
                f"textbook items) -- as a named anchor, not from dok_status alone: this item is named "
                f"as a {anchor['level'].upper()} calibration anchor in {anchor['calib_file']} "
                f"(source: {anchor['source']!r}), which is a per-row, on-disk textbook DOK trace with "
                f"an articulated rationale ({anchor['level']} rationale: {anchor['why']!r}). Because "
                f"this specific item is one of the on-disk item-level anchors, DOK {dok} would stand "
                f"as the confirmed textbook label. (dok_status {dok_status!r} alone is lesson-level "
                f"provenance only and would NOT, by itself, have been sufficient without this anchor "
                f"match.)"
            )
        else:
            anchor_ids = ", ".join(sorted(anchors)) if anchors else "none on disk for this lesson"
            rule = 2
            text = (
                f"Would be classified under rule 2 (conflicting or provenance-missing textbook "
                f"labels remain UNRESOLVED pending source verification), for two facts together: "
                f"(1) dok_status {dok_status!r} is a LESSON-LEVEL provenance status only -- per "
                f"inventory/dok-workflow/gen_dok_wave_plan.py's own comment, 'calibrated' is never "
                f"earned by a single row being reviewed; and (2) this item ({legacy_id}) is NOT named "
                f"among the item-level anchors on disk for lesson {lesson} (anchors found there: "
                f"{anchor_ids}), so no per-row textbook DOK trace exists for it. The registry DOK "
                f"({dok}) would therefore be held UNRESOLVED pending source verification, not "
                f"accepted as a confirmed textbook label."
            )

        if role == "dok3-driver" or (isinstance(dok, int) and dok >= 2):
            text += (
                " Rule 4 note: this item's apparent difficulty (its length, its word-problem framing, "
                "or its multi-part structure) is not itself what would set the DOK -- rule 4 holds "
                "that DOK measures cognitive demand, not difficulty."
            )

        return {"rule_number": rule, "hierarchy_rule": RUBRIC_HIERARCHY[rule - 1], "note": text}

    # Watermark keys on ACTUAL manifest state (`approved`, loaded read-only
    # above from approvals_path_effective via dok_review.load_rubric_approvals)
    # -- not a hardcoded string. Empty manifest keeps the exact original
    # "awaiting approval" watermark; a non-empty manifest names the approved
    # version(s) + their approved_at dates and states the no-retroactive-
    # verification rule plainly.
    if approved:
        approved_versions_sorted = sorted(approved.keys())
        approved_desc = "; ".join(
            f"{v} (approved_at {approved[v].isoformat()})" for v in approved_versions_sorted
        )
        rubric_watermark = (
            f"APPROVED — {approved_desc} — verification is active only for review-log entries "
            "recorded at or after each version's own approved_at (no retroactive verification)"
        )
        # Dynamic counterpart of the surviving_mechanics manifest-state sentence
        # below, keyed on the same `approved` mapping: names the approved
        # version(s) + approved_at date(s) + the canonical verified count
        # (already computed by the coherence guards above), while retaining the
        # no-retroactivity rule verbatim in substance.
        manifest_state_sentence = (
            f"The approvals manifest is APPROVED — {approved_desc} — with "
            f"{canonical_verified_count} item(s) currently verified under it; review-log "
            "entries recorded before a version's own approved_at never verify under that "
            "version and must be re-reviewed (a new entry, with a new recorded_at, after "
            "approval) to become eligible."
        )
    else:
        rubric_watermark = "AWAITING TEACHER APPROVAL — nothing may be marked verified until approved"
        manifest_state_sentence = (
            "The approvals "
            "manifest ships EMPTY, so nothing can "
            "verify until a teacher approves this rubric; recording review-log entries before "
            "approval is permitted but they can never become verified and must be re-reviewed after "
            "approval."
        )

    rubric = {
        "version": "v0.2",
        "watermark": rubric_watermark,
        "prior_version_status": {
            "version": "v0.1-PROPOSED",
            "status": "request-changes by RC 2026-07-20",
            "note": (
                "That decision is recorded in the RC export (teacher_decisions_rc_v1.json, decision "
                "s5-rubric-v0.1); it is shown here as status context only, not re-recorded as a new "
                "decision."
            ),
        },
        "hierarchy": RUBRIC_HIERARCHY,
        "surviving_mechanics": [
            "Reviewer id + ISO timestamp + disposition (confirm / change+new-DOK / needs-source-check) "
            "+ chosen DOK (when disposition is change+new-DOK) + rationale note required on every "
            "disagreement + rubric_version recorded on every future log entry.",
            "The two-tier VERIFIED predicate as implemented in tools/dok-review/dok_review.py's "
            "entry_is_verified: an entry is REVIEWED when well-formed (non-empty reviewed_by, "
            "parseable offset-aware reviewed_at, recognized decision, decision-specific required "
            "fields), and VERIFIED only when it additionally records a resolved verification-grade "
            "disposition (a rule-1 confirm whose provenance resolves on disk and binds to the item "
            "itself, or a complete change with item_basis-appropriate provenance), has no unresolved "
            "needs-source-check earlier in its item_uid's chain, and carries a rubric_version listed "
            "in the approvals manifest with a tool-stamped recorded_at not earlier than that version's "
            "approved_at -- no retroactive verification. The tool was aligned to this rubric (NT6), "
            "and the wave plan and dashboard now consume this same canonical projection (NT7) -- one "
            "projection — the generator and dashboard consume it directly; this console's build "
            "guards verify plan-manifest coherence at build time, and the cross-consumer identity "
            "suite (inventory/dok-workflow/test_cross_consumer_projection.py) proves per-item "
            "agreement across tool, generator, dashboard, and console surfaces. "
            + manifest_state_sentence,
            "Consistency with tools/dok-review's append-only review_log.jsonl record shape: "
            "{item_uid, registry_line, item_id, lesson, reviewed_by, reviewed_at, prior_dok, "
            "reviewer_dok, current_dok, new_dok, decision, te_bucket, match_quality, "
            "disagreement_resolved, note, rubric_version, rationale, provenance, "
            "provenance_resolved, confirmation_basis, item_basis, resolves_source_check, "
            "prior_unresolved_nsc, recorded_at (tool-stamped)}.",
        ],
        "record_shape": {
            "item_uid": "iu_…",
            "registry_line": 0,
            "reviewer": "<reviewer-id>",
            "timestamp": "<ISO8601>",
            "disposition": "confirm | change+new-DOK | needs-source-check",
            "chosen_dok": "1|2|3 (only when disposition=change+new-DOK)",
            "rubric_version": "v0.2",
            "note": "required on every disagreement",
        },
        "tool_alignment_note": (
            "Shape is consistent with tools/dok-review/dok_review.py's append-only review_log.jsonl records "
            "({item_uid, registry_line, item_id, lesson, reviewed_by, reviewed_at, prior_dok, reviewer_dok, "
            "current_dok, new_dok, decision, te_bucket, match_quality, disagreement_resolved, note, "
            "rubric_version, rationale, provenance, provenance_resolved, confirmation_basis, item_basis, "
            "resolves_source_check, prior_unresolved_nsc, recorded_at (tool-stamped)}); the console reads "
            "the tool's semantics for display only and writes NO review-log entries."
        ),
        "rubric_doc": {
            "file": "DOK_RUBRIC_v0.2.md",
            "note": (
                "Full prose for the authority hierarchy, the surviving v0.1 mechanics, and the v0.1 -> "
                "v0.2 mapping table lives in DOK_RUBRIC_v0.2.md (same directory). This panel is a "
                "structured summary, not a substitute."
            ),
        },
        "decision_id": "s5-rubric-v0.2",
        "actions": ["approve-rubric", "request-changes", "defer"],
    }

    # Deterministic, stratified wave-0 sample selection.
    w0_sorted = sorted(wave0_flat, key=lambda it: it["registry_line"])

    dok3_driver = next(it for it in w0_sorted if it["role"] == "dok3-driver")
    first_explore = next(it for it in w0_sorted if it["role"] == "explore-practice")
    lowest_optional_stretch = next(it for it in w0_sorted if it["role"] == "optional-stretch")
    lowest_null_role = next(it for it in w0_sorted if it["role"] is None)
    second_explore = next(
        it
        for it in w0_sorted
        if it["role"] == "explore-practice" and it["dok"] != first_explore["dok"]
    )

    sample_items = [dok3_driver, first_explore, lowest_optional_stretch, lowest_null_role, second_explore]

    wave0_sample_items = []
    for it in sample_items:
        reg = registry_rows.get(it["registry_line"])
        guard(reg is not None, f"registry line {it['registry_line']} not found for wave0 sample item {it['id']}")
        wave0_sample_items.append(
            {
                "item_uid": it["item_uid"],
                "registry_line": it["registry_line"],
                "legacy_id": it["id"],
                "role": it["role"],
                "dok": it["dok"],
                "dok_status": it["dok_status"],
                "prompt": reg["prompt"],
                "v02_rule_applied": v02_rule_annotation(
                    it["dok_status"], it["role"], it["dok"], reg["source"], it["id"]
                ),
                "would_record": {
                    "item_uid": it["item_uid"],
                    "registry_line": it["registry_line"],
                    "reviewer": "<teacher-id — placeholder>",
                    "timestamp": "<at review time — placeholder>",
                    "disposition": "(illustration) confirm",
                    "chosen_dok": None,
                    "rubric_version": "v0.2",
                    "note": "(illustration only — not recorded)",
                },
            }
        )

    section5 = {
        "rubric": rubric,
        "wave0_sample": {
            "banner": "SAMPLE — NOT RECORDED",
            "note": (
                "Worked illustration of what a rubric-applied review WOULD record. No review-log entry is "
                "written anywhere by this console."
            ),
            "items": wave0_sample_items,
        },
    }

    # -----------------------------------------------------------------
    # SECTION 6 -- export mechanism note (static)
    # -----------------------------------------------------------------

    section6 = {
        "schema_file": "decisions_export.schema.json",
        "template_file": "teacher_decisions.template.json",
        "export_note": (
            "The Export button downloads teacher_decisions.json (Blob) and offers a copy-to-clipboard textarea "
            "fallback. Proposals only; no registry writes."
        ),
        # None when there is nothing recorded to exclude (e.g. teacher_decisions_rc_v1.json
        # is absent) -- the template hides the note entirely in that case rather than
        # showing a false "0 excluded" line.
        "recorded_exclusion_note": (
            f"{recorded_flagged_count} Section 3 decision(s) already recorded in "
            "teacher_decisions_rc_v1.json are excluded from this export (shown above as "
            "recorded, not re-exported; re-deciding one requires a new export revision)."
        ) if recorded_flagged_count else None,
    }

    # -----------------------------------------------------------------
    # META
    # -----------------------------------------------------------------

    # CALIBRATION_DIR / "3-5.json" is included here (not in FROZEN_HASHES) because
    # v02_rule_annotation() reads it read-only via load_calibration_item_anchors() to
    # resolve the wave-0 sample's item-level anchor trace (Fix A1); every wave-0 item
    # is lesson 3-5 (guarded above), so this is the one calibration file actually read.
    extra_hash_paths = [CONTENT_READINESS_PATH, VISUAL_CLASS_PATH, MANIFEST_PATH, CALIBRATION_DIR / "3-5.json"]
    frozen_inputs_meta = []
    for path in FROZEN_HASHES:
        if fixture_mode and path == WAVE_PLAN_PATH:
            # FIXTURE MODE: the real wave-plan hash check was skipped above (part
            # 1 guards) -- record the fixture file's own path + sha256 instead of
            # the real, frozen wave plan's.
            frozen_inputs_meta.append({
                "path": display_path(wave_plan_path_effective),
                "sha256": sha256_file(wave_plan_path_effective),
                "fixture_substituted_for": rel(WAVE_PLAN_PATH),
            })
        else:
            frozen_inputs_meta.append({"path": rel(path), "sha256": sha256_file(path)})
    frozen_inputs_meta += [{"path": rel(p), "sha256": sha256_file(p)} for p in extra_hash_paths]

    # approvals_manifest_state: derived from ACTUAL manifest state (`approved`),
    # not hardcoded -- mirrors the rubric watermark logic above. read_only is
    # always true: this console (like dok_review.py itself) never writes to a
    # rubric-approvals manifest, real or fixture.
    approvals_manifest_state = {
        "path": display_path(approvals_path_effective),
        "approved_versions": sorted(approved.keys()),
        "read_only": True,
    }

    # Triple-split identity (rc-merge-auth-5-4-2026-07-23 + NT14
    # nt14-ingest-4-1-2026-07-23), computed from the wave plan actually
    # loaded this run (real or fixture) -- 'registry_rows' above stays the
    # raw, audit-style total; this is the authoritative place a console
    # reader gets the active/optional-catalog/merged-alias split.
    # STUDENT-FACING selection (qb.py) is what actually resolves/excludes
    # merged-alias rows and never selects/schedules optional-catalog rows;
    # this console only reports the counts.
    merged_alias_item_uids_console = sorted(
        it["item_uid"] for it in all_wave_items if it.get("status") == "merged-alias"
    )
    # NT14 (nt14-ingest-4-1-2026-07-23, additive): 19 lesson-4-1 wave-plan
    # items carry "availability": "optional-catalog" (never "status":
    # "merged-alias" -- a distinct, orthogonal marker). These must ALSO be
    # excluded from active_registry_rows, per the binding course-policy rule
    # that optional-catalog rows are never counted toward required-content
    # denominators.
    optional_catalog_item_uids_console = sorted(
        it["item_uid"] for it in all_wave_items if it.get("availability") == "optional-catalog"
    )
    active_registry_rows = (
        len(registry_rows) - len(merged_alias_item_uids_console) - len(optional_catalog_item_uids_console)
    )
    guard(
        len(merged_alias_item_uids_console) == 22,
        f"expected exactly 22 merged-alias wave-plan items, got {len(merged_alias_item_uids_console)}",
    )
    guard(
        len(optional_catalog_item_uids_console) == 19,
        f"expected exactly 19 optional-catalog wave-plan items, got {len(optional_catalog_item_uids_console)}",
    )
    guard(
        active_registry_rows + len(merged_alias_item_uids_console) + len(optional_catalog_item_uids_console)
        == len(registry_rows),
        "identity_reconciliation failed: active_registry_rows "
        f"({active_registry_rows}) + optional_catalog_rows "
        f"({len(optional_catalog_item_uids_console)}) + merged_alias_rows "
        f"({len(merged_alias_item_uids_console)}) != registry_rows ({len(registry_rows)})",
    )

    meta = {
        "generated_by": "build_console.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "frozen_inputs": frozen_inputs_meta,
        "locked_counts": {
            "registry_rows": len(registry_rows),
            "active_registry_rows": active_registry_rows,
            "merged_alias_rows": len(merged_alias_item_uids_console),
            # NT14 (nt14-ingest-4-1-2026-07-23, additive): 19 lesson-4-1
            # rows, excluded from active_registry_rows above (see the
            # identity_reconciliation block below for the full split).
            "optional_catalog_rows": len(optional_catalog_item_uids_console),
            "dok_conflict_pairs": len(conflict_rows),
            "wave0_items": len(wave0_flat),
            "essential_missing_visuals": len(essential_rows),
            "tikz_total_ids": len(manifest_data_rows),
            "tikz_compile_pass": len(pass_rows),
            "dangling_edges_into_4_1": len(retirement_gap_into_41),
            # NT7: count of wave-plan items whose canonical review-log
            # projection reads verified (see GUARD ASSERTS part 2b above).
            # Always 0 against the real wave plan + real (empty) approvals
            # manifest; nonzero only ever appears in a FIXTURE MODE run.
            "canonical_verified_count": canonical_verified_count,
        },
        "identity_reconciliation": {
            "raw_registry_identities": len(registry_rows),
            "merged_alias_identities": len(merged_alias_item_uids_console),
            "optional_catalog_identities": len(optional_catalog_item_uids_console),
            "active_canonical_items": active_registry_rows,
            "merged_alias_item_uids": merged_alias_item_uids_console,
            "optional_catalog_item_uids": optional_catalog_item_uids_console,
            "authorization_record_id": "rc-merge-auth-5-4-2026-07-23",
            "optional_catalog_authorization_record_id": "nt14-ingest-4-1-2026-07-23",
            "statement": (
                "raw_registry_identities == active_canonical_items + optional_catalog_identities + "
                "merged_alias_identities (919 == 878 + 19 + 22). "
                "meta.locked_counts.registry_rows above stays the raw, audit-style total; "
                "active_registry_rows is what a student-facing consumer (qb.py) actually selects "
                "from. optional_catalog_identities (lesson 4-1, nt14-ingest-4-1-2026-07-23) are "
                "rows that exist in the registry but are, by binding course policy, never auto-"
                "scheduled, never placed in pacing, and never described as required or ready-to-"
                "teach pending a separate, later course-policy decision -- distinct from "
                "merged_alias_identities (lesson 5-4), which resolve DELIBERATELY to a survivor row."
            ),
        },
        "approvals_manifest_state": approvals_manifest_state,
        "proposals_only_disclaimer": (
            "All controls in this console produce PROPOSALS ONLY. Nothing here writes the registry or any "
            "source file. A later, separate, teacher-gated step turns exported proposals into changes."
        ),
    }

    console_data = {
        "meta": meta,
        "section1": section1,
        "section2": section2,
        "section3": section3,
        "section4": section4,
        "section5": section5,
        "section6": section6,
    }

    out_data_path_effective.parent.mkdir(parents=True, exist_ok=True)
    with open(out_data_path_effective, "w", encoding="utf-8") as f:
        json.dump(console_data, f, ensure_ascii=False, indent=2)
    print(f"[write] {out_data_path_effective}")

    # Round-trip sanity check.
    with open(out_data_path_effective, "r", encoding="utf-8") as f:
        json.load(f)
    print("[check] console_data.json is valid JSON (round-tripped)")

    # -----------------------------------------------------------------
    # STEP 4 -- HTML assembly hook
    #
    # FIXTURE MODE skips this entirely (no thumbnails were rendered above,
    # and console_data.json was written only into --fixture-out, never HERE).
    # -----------------------------------------------------------------

    if fixture_mode:
        print("[fixture] HTML assembly SKIPPED (FIXTURE MODE)")
    elif TEMPLATE_PATH.exists():
        template_html = TEMPLATE_PATH.read_text(encoding="utf-8")

        thumbs_b64 = {}
        for row in pass_rows:
            bank_id = row["bank_id"]
            png_path = THUMB_DIR / f"{bank_id}.png"
            guard(png_path.exists(), f"thumbnail PNG missing for {bank_id} during HTML assembly")
            import base64

            b64 = base64.b64encode(png_path.read_bytes()).decode("ascii")
            thumbs_b64[bank_id] = f"data:image/png;base64,{b64}"

        data_json_text = json.dumps(console_data, ensure_ascii=False, indent=2)
        thumbs_json_text = json.dumps(thumbs_b64, ensure_ascii=False)

        assembled = template_html.replace('"__CONSOLE_DATA_JSON__"', data_json_text)
        assembled = assembled.replace('"__THUMBNAILS_JSON__"', thumbs_json_text)

        guard(
            "__CONSOLE_DATA_JSON__" not in assembled,
            "console_template.html token __CONSOLE_DATA_JSON__ was not replaced (check exact quoting)",
        )
        guard(
            "__THUMBNAILS_JSON__" not in assembled,
            "console_template.html token __THUMBNAILS_JSON__ was not replaced (check exact quoting)",
        )

        ASSEMBLED_HTML_PATH.write_text(assembled, encoding="utf-8")
        print(f"[write] {ASSEMBLED_HTML_PATH}")
    else:
        print(
            f"[warn] {TEMPLATE_PATH} does not exist yet -- skipping HTML assembly. "
            "console_data.json and thumbnails/ were still written; another agent delivers the template "
            "and the manager re-runs this build."
        )

    # -----------------------------------------------------------------
    # GUARD ASSERTS -- part 3: re-hash registry.jsonl (end-of-build)
    # -----------------------------------------------------------------
    final_hash = sha256_file(REGISTRY_PATH)
    guard(
        final_hash == FROZEN_HASHES[REGISTRY_PATH],
        f"registry.jsonl sha256 mismatch at END of build (it must never be modified).\n"
        f"  expected: {FROZEN_HASHES[REGISTRY_PATH]}\n  actual:   {final_hash}",
    )
    print("[guard] registry.jsonl re-hash verified unchanged (end)")

    print("\n=== build_console.py finished successfully ===")


if __name__ == "__main__":
    main()
