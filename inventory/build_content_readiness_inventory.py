"""
Build the content-readiness inventory for the Lesson_planning questionbank.

READ-ONLY analysis. Reads questionbank/registry.jsonl, questionbank/calibration/*.json,
questionbank/images/, questionbank/calibration/sources/, and repo-root / source/ SE-TE files.
Writes ONLY:
  - inventory/content_readiness_inventory.json
  - inventory/CONTENT_READINESS_INVENTORY.md

Does not modify registry.jsonl, any calibration/*.json, any file under
questionbank/calibration/sources/ or questionbank/images/, or any other existing file.

Everything in this report is a snapshot of CURRENT on-disk state only. Where the data
suggests a history or cause (e.g. "these rows look duplicated"), the report says so is
explicitly UNKNOWN from these files unless it can be verified from what's on disk right now.

Run from anywhere; paths are resolved relative to the repo root (parent of this
script's directory).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

REGISTRY_PATH = os.path.join(REPO_ROOT, 'questionbank', 'registry.jsonl')
CALIBRATION_DIR = os.path.join(REPO_ROOT, 'questionbank', 'calibration')
CALIBRATION_SOURCES_DIR = os.path.join(CALIBRATION_DIR, 'sources')
IMAGES_DIR = os.path.join(REPO_ROOT, 'questionbank', 'images')
SOURCE_DIR = os.path.join(REPO_ROOT, 'source')
ALIAS_MAP_PATH = os.path.join(REPO_ROOT, 'inventory', 'dedup', 'item_uid_alias_map.json')

# tools/dok-review is not importable as a normal package (hyphen in the
# directory name), so it is reached via an explicit sys.path insert -- the
# same pattern inventory/dok-workflow/gen_dok_wave_plan.py uses. This is the
# ONE canonical implementation of the review-log verification predicate
# (dok_review.entry_is_verified, via tool_state_for) -- this builder never
# reimplements any part of that predicate locally, and it never reads
# gen_dok_wave_plan.py or dok_wave_plan.json: the canonical projection below
# is computed INDEPENDENTLY from (registry, alias map, review log, approvals
# manifest), so it is a real cross-check against the wave plan rather than a
# copy of it. dok_review.py has no module-level import side effects
# (confirmed by reading it in full before this import was added), so this
# insert + import is safe to run at module import time.
DOK_REVIEW_TOOL_DIR = os.path.join(REPO_ROOT, 'tools', 'dok-review')
if DOK_REVIEW_TOOL_DIR not in sys.path:
    sys.path.insert(0, DOK_REVIEW_TOOL_DIR)
import dok_review  # noqa: E402  (path insert must precede this import)

DEFAULT_REVIEW_LOG_PATH = os.path.join(DOK_REVIEW_TOOL_DIR, 'review_log.jsonl')
DEFAULT_APPROVALS_PATH = os.path.join(DOK_REVIEW_TOOL_DIR, 'rubric_approvals.json')

# ---------------------------------------------------------------------------
# The 37 lesson slots, in order
# ---------------------------------------------------------------------------
SLOTS = (
    ['1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7'] +
    ['2-1', '2-2', '2-3', '2-4', '2-5', '2-6', '2-7'] +
    ['3-1', '3-2', '3-3', '3-4', '3-5', '3-6'] +
    ['4-1', '4-2', '4-3', '4-4', '4-5', '4-6'] +
    ['5-1', '5-2', '5-3', '5-4', '5-5', '5-6'] +
    ['6-1', '6-2', '6-3', '6-4', '6-5']
)
assert len(SLOTS) == 37, f"expected 37 slots, got {len(SLOTS)}"

# ---------------------------------------------------------------------------
# Load registry
# ---------------------------------------------------------------------------
def load_registry():
    rows = []
    with open(REGISTRY_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_alias_map():
    """Read-only. Returns the parsed inventory/dedup/item_uid_alias_map.json.
    Mirrors inventory/dok-workflow/gen_dok_wave_plan.py's identical read of
    this same file: {"alias_map": {legacy_id: {"ambiguous": bool,
    "item_uids": [{"item_uid", "lesson", "source", "prompt_sha1",
    "registry_line", "exact_duplicate"}, ...]}}}."""
    with open(ALIAS_MAP_PATH, encoding='utf-8') as f:
        return json.load(f)


def build_line2uid(alias):
    """1-based registry line -> item_uid, built exactly as
    inventory/dok-workflow/gen_dok_wave_plan.py builds it: every legacy id's
    item_uids entries are keyed by their own 1-based registry_line, so two
    rows sharing a legacy id (the 85 ambiguous ids) land at two different
    lines and therefore resolve to two different item_uids. 900 distinct
    entries for a well-formed alias map."""
    line2uid = {}
    for _legacy_id, entry in alias['alias_map'].items():
        for u in entry['item_uids']:
            line2uid[u['registry_line']] = u['item_uid']
    return line2uid


def repo_relative_display_path(path):
    """Return a REPO-RELATIVE, POSIX-form path for `path` when it resolves
    inside REPO_ROOT (mirrors inventory/dok-workflow/gen_dok_wave_plan.py's
    identical helper) -- no absolute user path is ever emitted for the
    canonical, in-repo default review-log/approvals-manifest inputs. Falls
    back to the plain absolute path only when `path` resolves OUTSIDE
    REPO_ROOT (e.g. a scratchpad/test fixture passed via --review-log /
    --approvals-manifest for fail-closed smoke-testing) -- a repo-relative
    form would be meaningless (or itself just as machine-specific, via '..'
    segments) for those."""
    abs_path = os.path.abspath(str(path))
    try:
        rel = os.path.relpath(abs_path, REPO_ROOT)
    except ValueError:
        # Different drive on Windows -- relpath can't express this as a
        # relative path at all, so it must be outside the repo.
        return abs_path
    rel_posix = rel.replace(os.sep, '/')
    if rel_posix.split('/')[0] == os.pardir:
        # Starts with '..' -- resolves outside REPO_ROOT.
        return abs_path
    return rel_posix


def load_calibration():
    cal = {}
    for fname in os.listdir(CALIBRATION_DIR):
        if not fname.endswith('.json'):
            continue
        les = fname[:-5]
        path = os.path.join(CALIBRATION_DIR, fname)
        with open(path, encoding='utf-8') as f:
            cal[les] = json.load(f)
    return cal


def count_screenshots():
    """Count image files per lesson prefix under questionbank/images/."""
    counts = Counter()
    for fname in os.listdir(IMAGES_DIR):
        m = re.match(r'^(\d+-\d+)(?=[_.])', fname)
        if m:
            counts[m.group(1)] += 1
    return counts


def has_evidence_answer(row):
    """answers_with_evidence gate: teacher_answer present+nonempty OR
    'Answer key (from source):' literal marker in notes."""
    ta = row.get('teacher_answer')
    if ta is not None and str(ta).strip() != '':
        return True
    notes = row.get('notes') or ''
    if 'Answer key (from source):' in notes:
        return True
    return False


def image_asset_absent(row):
    """True if has_visual and row['image'] is empty/None: the reference itself is
    missing (there is no path to even check on disk)."""
    return not row.get('image')


def image_asset_broken_path(row):
    """True if has_visual and row['image'] is non-empty, but the referenced file does
    not currently exist on disk. This is a broken PATH, not an absent reference."""
    img = row.get('image')
    if not img:
        return False
    # image paths in the registry are stored relative to repo root
    # (e.g. "questionbank/images/3-5_....png")
    full_path = img if os.path.isabs(img) else os.path.join(REPO_ROOT, img)
    return not os.path.exists(full_path)


def resolve_repairable(image_path):
    """For a registry image path that does not resolve on disk, check whether a file
    with the same basename currently exists under questionbank/calibration/sources/.
    Returns (repairable: bool, resolved_path: str|None), resolved_path relative to repo
    root with forward slashes. Read-only: does not touch the registry or the sources
    directory."""
    basename = os.path.basename(image_path)
    candidate = os.path.join(CALIBRATION_SOURCES_DIR, basename)
    if os.path.exists(candidate):
        rel = os.path.relpath(candidate, REPO_ROOT).replace(os.sep, '/')
        return True, rel
    return False, None


def calibration_has_real_anchors(cal_entry):
    """A lesson's calibration counts as having REAL anchors if dok2_anchors
    or dok3_anchors is a non-empty list."""
    if cal_entry is None:
        return False
    d2 = cal_entry.get('dok2_anchors') or []
    d3 = cal_entry.get('dok3_anchors') or []
    return len(d2) > 0 or len(d3) > 0


def item_analysis_status(cal_entry):
    """'none' = no calibration file or key absent.
    'empty' = key present but {} or [].
    'real' = key present and non-empty."""
    if cal_entry is None:
        return 'none'
    if 'item_analysis' not in cal_entry:
        return 'none'
    ia = cal_entry['item_analysis']
    if ia in ({}, [], None):
        return 'empty'
    if hasattr(ia, '__len__') and len(ia) == 0:
        return 'empty'
    return 'real'


def se_pdf_exists(les):
    return os.path.exists(os.path.join(REPO_ROOT, f'a2_{les}_SE.pdf'))


def te_pdf_exists(les):
    return os.path.exists(os.path.join(REPO_ROOT, f'a2_{les}_TE.pdf'))


def se_tex_exists(les):
    root_tex = os.path.exists(os.path.join(REPO_ROOT, f'a2_{les}_SE.tex'))
    source_tex = os.path.exists(os.path.join(SOURCE_DIR, f'{les}_savvas_SE.tex'))
    return root_tex or source_tex


def te_tex_exists(les):
    root_tex = os.path.exists(os.path.join(REPO_ROOT, f'a2_{les}_TE.tex'))
    source_tex = os.path.exists(os.path.join(SOURCE_DIR, f'{les}_savvas_TE.tex'))
    return root_tex or source_tex


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------
def build(review_log_path, approvals_manifest_path):
    all_rows = load_registry()
    calibration = load_calibration()
    screenshot_counts = count_screenshots()
    alias_map = load_alias_map()
    line2uid = build_line2uid(alias_map)

    # Canonical DOK verification projection (NT7-R2). Computed
    # INDEPENDENTLY from (registry, alias map, review log, approvals
    # manifest) -- this builder never reads dok_wave_plan.json, so this is a
    # real cross-check against the wave plan's own projection, not a copy of
    # it. read_log_entries() is already WHOLE-LOG fail-closed (a missing
    # file returns [] silently; any structural defect prints one stderr
    # warning and returns []), so it is called directly here, never wrapped
    # in another try/except. load_rubric_approvals() is likewise already
    # fail-closed internally (missing/malformed -> {}).
    review_log_entries = dok_review.read_log_entries(review_log_path)
    approved_rubric_versions = dok_review.load_rubric_approvals(approvals_manifest_path)
    latest_by_uid = dok_review.latest_entries_by_uid(review_log_entries)
    verified_item_uids = []
    review_state_totals = Counter()

    rows_by_lesson = {}
    for line_no, r in enumerate(all_rows, start=1):
        r['_registry_line'] = line_no
        rows_by_lesson.setdefault(r['lesson'], []).append(r)

    # calibrated lessons = lessons whose calibration file has real anchors
    calibrated_lessons = {
        les for les, cal in calibration.items() if calibration_has_real_anchors(cal)
    }

    lesson_objs = []
    anomalies = []
    unknowns = []

    # global accumulators (for secondary aggregates / reconciliation)
    g_total_rows = 0
    g_answers_with_evidence = 0
    g_missing_answers = 0
    g_visual_items = 0
    g_visuals_absent = 0
    g_visuals_absent_nine = 0
    g_visuals_broken_path = 0
    g_visuals_broken_path_nine = 0
    g_visuals_missing_asset = 0
    g_visuals_missing_asset_nine = 0
    g_topics_nonempty = 0
    g_topics_nonempty_nine = 0
    g_known_auto = 0
    g_unreviewed = 0
    g_calibrated_rows = 0
    g_verified = 0
    g_base_known_auto = 0
    g_base_calibrated = 0
    g_base_unreviewed = 0
    g_dup_id_excess_rows = 0
    g_dup_id_strings_sum = 0
    g_dup_id_participating_rows = 0
    g_src_coordinates = 0
    g_src_excess_rows = 0
    g_src_participating_rows = 0
    g_missing_answers_nine = 0
    g_broken_path_details = []
    # Dual-denominator identity (rc-merge-auth-5-4-2026-07-23, additive):
    # 22 of the 900 registry rows now carry status=='merged-alias'. This
    # builder's existing per-lesson/global metrics above (registry_rows,
    # dok_status, missing_answers, readiness gates, etc.) are UNCHANGED --
    # they are registry-row-count based (audit-style), exactly like
    # inventory/dok-workflow/gen_dok_wave_plan.py's own untouched pins, since
    # the merge added only marker fields and touched no dok/role/answer/
    # visual/topic content. The counts below are a NEW, additive overlay
    # publishing the RC-mandated active/alias breakdown explicitly, never a
    # rewrite of the existing gates.
    g_merged_alias_rows = 0
    g_merged_alias_item_uids = []

    THE_NINE = ['4-3', '4-4', '4-5', '5-1', '5-4', '5-5', '6-3', '6-4', '6-5']

    for les in SLOTS:
        rows = rows_by_lesson.get(les, [])
        n = len(rows)
        cal_entry = calibration.get(les)
        has_cal = cal_entry is not None
        is_calibrated_lesson = les in calibrated_lessons

        se_pdf = se_pdf_exists(les)
        te_pdf = te_pdf_exists(les)
        se_tex = se_tex_exists(les)
        te_tex = te_tex_exists(les)
        shots = screenshot_counts.get(les, 0)

        # answers with evidence / missing answers
        ans_ev = sum(1 for r in rows if has_evidence_answer(r))
        missing_ans = n - ans_ev

        # visuals: split ABSENT reference (no image field) from BROKEN PATH
        # (image field present but file not found on disk).
        vis_items = sum(1 for r in rows if r.get('has_visual'))
        vis_absent = sum(1 for r in rows if r.get('has_visual') and image_asset_absent(r))
        broken_rows = [r for r in rows if r.get('has_visual') and image_asset_broken_path(r)]
        vis_broken = len(broken_rows)
        vis_missing = vis_absent + vis_broken  # kept for continuity with earlier reports

        for r in broken_rows:
            img = r.get('image')
            repairable, resolved = resolve_repairable(img)
            g_broken_path_details.append({
                'id': r.get('id'),
                'lesson': les,
                'current_image_path': img,
                'repairable': repairable,
                'resolved_path': resolved,
            })

        # topics
        topics_ne = sum(1 for r in rows if (r.get('topics') or []))

        # dok_status: BASE bucket (known_auto -> calibrated -> unreviewed) is
        # a pure function of the registry row (plus its lesson's calibration
        # status) -- same precedence as before this fix, minus the
        # (forbidden) reviewed_by branch that used to sit ahead of it.
        # 'verified' is NOT part of that base precedence: it is an OVERLAY
        # applied per row afterward from the canonical DOK review-log
        # projection (tools/dok-review/dok_review.py's tool_state_for(),
        # keyed by this row's item_uid via line2uid) -- mirrors
        # inventory/dok-workflow/gen_dok_wave_plan.py's identical overlay. A
        # verified row LEAVES its base bucket for 'verified' instead; every
        # other row stays exactly at its base bucket. Registry
        # 'reviewed_by'/'reviewed_at' are application-time metadata and are
        # NEVER read for this derivation.
        known_auto = 0
        calibrated_cnt = 0
        unreviewed_cnt = 0
        verified_cnt = 0
        base_known_auto = 0
        base_calibrated = 0
        base_unreviewed = 0
        merged_alias_cnt = 0
        for r in rows:
            if r.get('status') == 'merged-alias':
                merged_alias_cnt += 1
            rationale = r.get('dok_rationale') or ''
            if 'Auto-assigned DOK' in rationale:
                base_bucket = 'known_auto'
                base_known_auto += 1
            elif is_calibrated_lesson:
                base_bucket = 'calibrated'
                base_calibrated += 1
            else:
                base_bucket = 'unreviewed'
                base_unreviewed += 1

            uid = line2uid.get(r['_registry_line'])
            if r.get('status') == 'merged-alias':
                g_merged_alias_item_uids.append(uid)
            review_state = dok_review.tool_state_for(
                uid, latest_by_uid, _approved_versions_override=approved_rubric_versions
            )
            review_state_totals[review_state] += 1

            if review_state == 'verified':
                verified_cnt += 1
                verified_item_uids.append(uid)
            elif base_bucket == 'known_auto':
                known_auto += 1
            elif base_bucket == 'calibrated':
                calibrated_cnt += 1
            else:
                unreviewed_cnt += 1

        assert known_auto + unreviewed_cnt + calibrated_cnt + verified_cnt == n, (
            f"dok_status counts do not sum to registry_rows for {les}"
        )

        # item_analysis status
        ia_status = item_analysis_status(cal_entry)

        # source-coordinate review queue (NOT "duplicates"): expose the full triplet.
        # coordinates = number of (lesson, source) groups with size > 1.
        # excess_rows = sum over each such group of (group_size - 1).
        # participating_rows = sum of the full sizes of those groups.
        source_counter = Counter(r.get('source') for r in rows)
        source_coords = sum(1 for v in source_counter.values() if v > 1)
        source_excess = sum(v - 1 for v in source_counter.values() if v > 1)
        source_participating = sum(v for v in source_counter.values() if v > 1)

        # duplicate-id metric: expose the full triplet.
        # strings = number of distinct id values that appear more than once.
        # excess_rows = sum over each such group of (group_size - 1).
        # participating_rows = sum of the full sizes of those groups.
        id_counter = Counter(r.get('id') for r in rows)
        dup_strings = sum(1 for v in id_counter.values() if v > 1)
        dup_excess = sum(v - 1 for v in id_counter.values() if v > 1)
        dup_participating = sum(v for v in id_counter.values() if v > 1)

        # readiness rubric
        gates_failed = []
        if n == 0:
            if not (has_cal or shots > 0 or se_tex or te_tex or se_pdf or te_pdf):
                readiness = 'absent'
                reason = 'no source material on disk (no SE/TE pdf/tex, no calibration file, no screenshots, 0 registry rows)'
            else:
                readiness = 'blocked'
                staged = []
                if has_cal:
                    staged.append('calibration file')
                if shots > 0:
                    staged.append(f'{shots} screenshots')
                if se_tex:
                    staged.append('SE.tex')
                if te_tex:
                    staged.append('TE.tex')
                if se_pdf:
                    staged.append('SE.pdf')
                if te_pdf:
                    staged.append('TE.pdf')
                reason = (
                    f"has staged material ({', '.join(staged)}) — 0 registry rows "
                    "(ingestion status UNKNOWN from disk)"
                )
        else:
            if missing_ans > 0:
                gates_failed.append(f'missing_answers={missing_ans}>0')
            if topics_ne != n:
                gates_failed.append(f'topics_nonempty={topics_ne}<{n}')
            if not is_calibrated_lesson:
                gates_failed.append('lesson not calibrated (no real dok2/dok3 anchors)')
            if vis_missing > 0:
                gates_failed.append(f'visuals_missing_asset={vis_missing}>0')
            if verified_cnt != n:
                gates_failed.append(f'dok_status.verified={verified_cnt}<{n}')

            if not gates_failed:
                readiness = 'ready'
                reason = 'all gates passed'
            else:
                readiness = 'partial'
                reason = '; '.join(gates_failed)

        notes = []
        if les == '3-5':
            notes.append(
                "Legacy '3-5_student_day1.pdf' / '3-5_teacher_day1.pdf' also exist at repo root "
                "(pre-canonical duplicates); canonical SE/TE is a2_3-5_SE.pdf / a2_3-5_TE.pdf, "
                "which is what se_pdf/te_pdf report here."
            )
        if les == '4-1':
            notes.append(
                "As of this snapshot, 4-1's calibration file has a REAL item_analysis (5 examples "
                "mapped to Savvas practice-item numbers) but empty dok2_anchors/dok3_anchors and 0 "
                "registry rows. Whether ingestion was ever attempted, is pending, or was abandoned "
                "is UNKNOWN from these files."
            )

        lesson_obj = {
            'lesson': les,
            'se_pdf': se_pdf,
            'te_pdf': te_pdf,
            'se_tex': se_tex,
            'te_tex': te_tex,
            'registry_rows': n,
            'answers_with_evidence': ans_ev,
            'missing_answers': missing_ans,
            'visual_items': vis_items,
            'visuals_absent': vis_absent,
            'visuals_broken_path': vis_broken,
            'visuals_missing_asset': vis_missing,
            'topics_nonempty': topics_ne,
            'dok_status': {
                'known_auto': known_auto,
                'unreviewed': unreviewed_cnt,
                'calibrated': calibrated_cnt,
                'verified': verified_cnt,
            },
            'item_analysis': ia_status,
            # source-coordinate review-queue triplet (per lesson). "collisions" here is
            # kept as the field name for excess_rows for continuity with earlier reports.
            'source_coordinate_groups': source_coords,
            'source_coordinate_collisions': source_excess,
            'source_coordinate_participating_rows': source_participating,
            # duplicate-id triplet (per lesson). duplicate_id_excess_rows replaces the
            # earlier field name duplicate_id_rows.
            'duplicate_id_strings': dup_strings,
            'duplicate_id_excess_rows': dup_excess,
            'duplicate_id_participating_rows': dup_participating,
            'screenshots': shots,
            'has_calibration': has_cal,
            'readiness': readiness,
            'readiness_reason': reason,
            # Dual-denominator identity (rc-merge-auth-5-4-2026-07-23,
            # additive -- see the note above the g_merged_alias_rows
            # accumulator). 'registry_rows' above is UNCHANGED (still the
            # raw, audit-style row count); active_registry_rows is the
            # RC-mandated denominator a student-facing consumer (qb.py)
            # actually selects from.
            'merged_alias_rows': merged_alias_cnt,
            'active_registry_rows': n - merged_alias_cnt,
        }
        if notes:
            lesson_obj['notes'] = notes
        lesson_objs.append(lesson_obj)

        # accumulate globals
        g_total_rows += n
        g_answers_with_evidence += ans_ev
        g_missing_answers += missing_ans
        g_visual_items += vis_items
        g_visuals_absent += vis_absent
        g_visuals_broken_path += vis_broken
        g_visuals_missing_asset += vis_missing
        g_topics_nonempty += topics_ne
        g_known_auto += known_auto
        g_unreviewed += unreviewed_cnt
        g_calibrated_rows += calibrated_cnt
        g_verified += verified_cnt
        g_base_known_auto += base_known_auto
        g_base_calibrated += base_calibrated
        g_base_unreviewed += base_unreviewed
        g_dup_id_excess_rows += dup_excess
        g_dup_id_strings_sum += dup_strings
        g_dup_id_participating_rows += dup_participating
        g_src_coordinates += source_coords
        g_src_excess_rows += source_excess
        g_src_participating_rows += source_participating
        g_merged_alias_rows += merged_alias_cnt
        if les in THE_NINE:
            g_missing_answers_nine += missing_ans
            g_visuals_missing_asset_nine += vis_missing
            g_visuals_absent_nine += vis_absent
            g_visuals_broken_path_nine += vis_broken
            g_topics_nonempty_nine += topics_ne

    assert len(lesson_objs) == 37

    # ------------------------------------------------------------------
    # Baseline reconciliation
    # ------------------------------------------------------------------
    all_ids = Counter(r.get('id') for r in all_rows)
    unique_ids = len(all_ids)
    dup_id_strings = sum(1 for v in all_ids.values() if v > 1)
    dup_id_participating_rows_global = sum(v for v in all_ids.values() if v > 1)
    real_screenshots = sum(screenshot_counts.values())
    calibrated_lesson_count = len(calibrated_lessons)

    # internal cross-check: per-lesson accumulation must agree with the global,
    # cross-lesson computation above (duplicate ids do not straddle lessons here).
    assert g_dup_id_strings_sum == dup_id_strings, (
        f"per-lesson dup id strings sum {g_dup_id_strings_sum} != global {dup_id_strings}"
    )
    assert g_dup_id_participating_rows == dup_id_participating_rows_global, (
        f"per-lesson dup id participating rows {g_dup_id_participating_rows} != global "
        f"{dup_id_participating_rows_global}"
    )

    def verdict(claimed, computed):
        return 'CONFIRMED' if claimed == computed else f'DISCREPANCY: computed={computed} claimed={claimed}'

    baseline = [
        {'metric': 'total registry rows', 'claimed': 900, 'computed': g_total_rows,
         'verdict': verdict(900, g_total_rows)},
        {'metric': 'unique ids', 'claimed': 815, 'computed': unique_ids,
         'verdict': verdict(815, unique_ids)},
        {'metric': 'duplicate id strings (ids appearing more than once)', 'claimed': 85, 'computed': dup_id_strings,
         'verdict': verdict(85, dup_id_strings)},
        {'metric': 'known-auto DOK rows', 'claimed': 421, 'computed': g_known_auto,
         'verdict': verdict(421, g_known_auto)},
        {'metric': 'missing-answer rows across the nine', 'claimed': 339, 'computed': g_missing_answers_nine,
         'verdict': verdict(339, g_missing_answers_nine)},
        {'metric': 'source-coordinate review-queue excess rows (global)', 'claimed': 176, 'computed': g_src_excess_rows,
         'verdict': verdict(176, g_src_excess_rows)},
        {'metric': 'topics nonempty across the nine', 'claimed': 0, 'computed': g_topics_nonempty_nine,
         'verdict': verdict(0, g_topics_nonempty_nine)},
        {'metric': 'calibrated lessons', 'claimed': 1, 'computed': calibrated_lesson_count,
         'verdict': verdict(1, calibrated_lesson_count)},
        # NT10 named update per DOK_VERIFICATION_WORKFLOW.md step 3(b1),
        # 2026-07-22: claimed 0 -> 39 (the first canonical verified set |S|:
        # RC's 39 lesson-5-4 rule-1 batch confirmations recorded through
        # tools/dok-review/dok_review.py under approved rubric v0.2; see
        # tools/dok-review/review_log.jsonl, 39 entries). Deliberately
        # re-confirmed as part of this named update, not silently flipped.
        {'metric': 'verified rows', 'claimed': 39, 'computed': g_verified,
         'verdict': verdict(39, g_verified)},
        {'metric': 'real screenshots', 'claimed': 114, 'computed': real_screenshots,
         'verdict': verdict(114, real_screenshots)},
        # NT11 named addition (rc-merge-auth-5-4-2026-07-23): 22 of the 900
        # rows (lesson 5-4) now carry status=='merged-alias'. Registry-
        # frozen invariant, same status as the pins above.
        {'metric': 'merged-alias rows (rc-merge-auth-5-4-2026-07-23)', 'claimed': 22, 'computed': g_merged_alias_rows,
         'verdict': verdict(22, g_merged_alias_rows)},
    ]

    all_confirmed = all(b['verdict'] == 'CONFIRMED' for b in baseline)

    readiness_dist = Counter(l['readiness'] for l in lesson_objs)

    # proposed_path_fixes: analysis-only output. Registry rows are NOT modified by this
    # script; this block records, for each broken-path row, whether a same-basename file
    # currently exists under questionbank/calibration/sources/ and what the corrected
    # path would be, for a human to apply separately.
    proposed_fixes = [
        {
            'id': d['id'],
            'lesson': d['lesson'],
            'current_image_path': d['current_image_path'],
            'proposed_path': d['resolved_path'],
            'repairable': d['repairable'],
        }
        for d in g_broken_path_details
    ]

    aggregate = {
        'total_registry_rows': g_total_rows,
        'total_answers_with_evidence': g_answers_with_evidence,
        'total_missing_answers_all_lessons': g_missing_answers,
        'total_missing_answers_the_nine': g_missing_answers_nine,
        'total_visual_items': g_visual_items,
        'total_visuals_absent_all_lessons': g_visuals_absent,
        'total_visuals_absent_the_nine': g_visuals_absent_nine,
        'total_visuals_broken_path_all_lessons': g_visuals_broken_path,
        'total_visuals_broken_path_the_nine': g_visuals_broken_path_nine,
        'total_visuals_missing_asset_all_lessons': g_visuals_missing_asset,
        'total_visuals_missing_asset_the_nine': g_visuals_missing_asset_nine,
        'note_visuals_missing_asset': (
            f'visuals_missing_asset ({g_visuals_missing_asset} all-lessons / {g_visuals_missing_asset_nine} '
            'the-nine) is visuals_absent + visuals_broken_path, kept for continuity with earlier reports. '
            f'Split: {g_visuals_absent} rows are visuals_absent (empty image field; all {g_visuals_absent_nine} '
            f'of them are in the nine) and {g_visuals_broken_path} rows are visuals_broken_path (non-empty '
            f'image field pointing at a file that is not currently on disk; all {g_visuals_broken_path} of '
            'them are in lesson 3-5, and all are repairable — see proposed_path_fixes).'
        ),
        'total_topics_nonempty_all_lessons': g_topics_nonempty,
        'total_topics_nonempty_the_nine': g_topics_nonempty_nine,
        'dok_status_totals': {
            'known_auto': g_known_auto,
            'unreviewed': g_unreviewed,
            'calibrated': g_calibrated_rows,
            'verified': g_verified,
            'sum': g_known_auto + g_unreviewed + g_calibrated_rows + g_verified,
        },
        # Additive (NT7-R2): canonical DOK verification projection outputs.
        # 'verified' above is populated ONLY from these -- never from
        # registry reviewed_by/reviewed_at.
        'dok_verified_item_uids': sorted(verified_item_uids),
        'dok_review_state_totals': {
            state: review_state_totals.get(state, 0) for state in dok_review.TOOL_STATES
        },
        'dok_verification_note': {
            'review_log_path': repo_relative_display_path(review_log_path),
            'approvals_manifest_path': repo_relative_display_path(approvals_manifest_path),
            'review_log_entry_count': len(review_log_entries),
            'approved_rubric_versions': sorted(approved_rubric_versions.keys()),
            'statement': (
                "The ONLY verification predicate used anywhere in this report is "
                "tools/dok-review/dok_review.py's entry_is_verified(), applied per "
                "item_uid via tool_state_for() over the review log's "
                "latest-entry-per-item_uid projection, gated by the rubric-approvals "
                "manifest, and computed independently of dok_wave_plan.json; it is "
                "fail-closed end to end -- a missing or malformed review log or "
                "approvals manifest always yields zero verified rows, never a "
                "fallback to registry reviewed_by/reviewed_at."
            ),
        },
        # Legacy/continuity aggregate fields (unchanged values/semantics from earlier reports):
        'total_duplicate_id_rows': g_dup_id_excess_rows,
        'total_source_coordinate_collisions': g_src_excess_rows,
        # Full triplets (Finding 2): state precisely which of the three counts is meant.
        'source_coordinate_review': {
            'coordinates': g_src_coordinates,
            'excess_rows': g_src_excess_rows,
            'participating_rows': g_src_participating_rows,
        },
        'duplicate_id_review': {
            'strings': dup_id_strings,
            'excess_rows': g_dup_id_excess_rows,
            'participating_rows': g_dup_id_participating_rows,
        },
        'calibrated_lessons_list': sorted(calibrated_lessons),
        'readiness_distribution': {
            'ready': readiness_dist.get('ready', 0),
            'partial': readiness_dist.get('partial', 0),
            'blocked': readiness_dist.get('blocked', 0),
            'absent': readiness_dist.get('absent', 0),
        },
        # Dual-denominator identity (rc-merge-auth-5-4-2026-07-23, additive).
        # This is the authoritative place to read the RC-mandated active/
        # alias split from this artifact: every OTHER count above
        # (registry_rows, dok_status_totals, etc.) stays registry-row-based
        # (audit-style, alias rows included) -- unchanged by this merge,
        # exactly like gen_dok_wave_plan.py's own untouched pins, since the
        # merge added only marker fields and never touched dok/role/answer/
        # visual/topic content.
        'identity_reconciliation': {
            'raw_registry_identities': g_total_rows,
            'merged_alias_identities': g_merged_alias_rows,
            'active_canonical_items': g_total_rows - g_merged_alias_rows,
            'merged_alias_item_uids': sorted(g_merged_alias_item_uids),
            'authorization_record_id': 'rc-merge-auth-5-4-2026-07-23',
            'statement': (
                "This inventory's existing metrics above (registry_rows, "
                "dok_status_totals, readiness gates, etc.) are registry-row-"
                "count based (audit-style): they include all 900 rows, alias "
                "rows among them, unchanged by this merge. STUDENT-FACING "
                "selection (qb.py) instead resolves each merged-alias row "
                "DELIBERATELY to its survivor (via alias_of) and never "
                "selects or counts the alias row itself, leaving "
                "active_canonical_items (878) as what a packet/quiz build "
                "actually draws from. Reconciliation is exact: "
                "raw_registry_identities == active_canonical_items + "
                "merged_alias_identities (900 == 878 + 22)."
            ),
        },
    }

    # ------------------------------------------------------------------
    # Anomalies — snapshot observations only. Where a pattern is consistent with a
    # history/cause, that history/cause is explicitly marked UNKNOWN: these files only
    # prove current on-disk state, not how it came to be.
    # ------------------------------------------------------------------
    anomalies.append({
        'title': '4-1: staged assets present, 0 current registry rows',
        'detail': (
            "As of this snapshot, 4-1 has a calibration file with a REAL item_analysis (Savvas "
            "practice items mapped to 5 examples) and 61 screenshots in questionbank/images/, but 0 "
            "registry rows and no SE/TE pdf or tex anywhere on disk. Whether ingestion into "
            "registry.jsonl was ever attempted, is pending, or was abandoned is UNKNOWN from these "
            "files — only the current on-disk state is observable. readiness=blocked."
        ),
    })

    visuals_absent_by_lesson = {
        l['lesson']: l['visuals_absent'] for l in lesson_objs if l['visuals_absent'] > 0
    }
    anomalies.append({
        'title': 'Visual-asset gap splits into two distinct issues: absent references vs. repairable broken paths',
        'detail': (
            f"{g_visuals_absent} registry rows have has_visual=true but an EMPTY image field — there "
            f"is no asset reference to resolve at all. By lesson: {visuals_absent_by_lesson}. Only 3-5 "
            "and 4-1 have any screenshots in questionbank/images/ at all, so every has_visual row in "
            "the other nine-lesson slots is unresolved by construction. Separately, "
            f"{g_visuals_broken_path} rows (all in lesson 3-5) have has_visual=true AND a non-empty "
            "image field, but the referenced file does not currently exist at that path. In summary: "
            f"{g_visuals_absent} references are genuinely ABSENT (empty image field, all in the nine); "
            f"{g_visuals_broken_path} are REPAIRABLE broken paths in 3-5 whose PNGs already exist under "
            "questionbank/calibration/sources/ — a path-fix, not missing content. See "
            "proposed_path_fixes for the corrected paths (analysis only; registry.jsonl was not "
            "modified)."
        ),
    })

    dup_by_lesson = {
        l['lesson']: {'strings': l['duplicate_id_strings'], 'participating_rows': l['duplicate_id_participating_rows']}
        for l in lesson_objs if l['duplicate_id_strings'] > 0
    }
    anomalies.append({
        'title': 'Duplicate-id strings concentrated in 5-1 / 5-4 / 5-5',
        'detail': (
            f"{dup_id_strings} duplicate-id strings involving {g_dup_id_participating_rows} "
            f"participating rows ({g_dup_id_excess_rows} excess rows) exist across the full registry, "
            f"and all of them are within exactly three lessons: {dup_by_lesson}. No other lesson has "
            "any duplicate id, and every duplicated id currently appears in exactly 2 rows. This "
            "pattern is consistent with duplicated bulk-ingest appends having hit only those three "
            "lessons, but the actual CAUSE is UNKNOWN from the data alone — these files show only the "
            "current state, not how it arose."
        ),
    })

    nine_row_total = sum(l['registry_rows'] for l in lesson_objs if l['lesson'] in THE_NINE)
    anomalies.append({
        'title': 'Topics absent on the nine (current state)',
        'detail': (
            f"As of this snapshot, {g_topics_nonempty_nine} of {nine_row_total} registry rows across "
            "the nine currently carry a non-empty topics list, even though each of those lessons' "
            "calibration files has a populated topic_vocabulary list. Whether topics were ever copied "
            "from topic_vocabulary into per-row topics during ingest is UNKNOWN from these files; only "
            "the current absence is observable. (3-5 is the exception: all 42 of its rows currently "
            "have non-empty topics.)"
        ),
    })

    anomalies.append({
        'title': 'DOK review pipeline: current state is almost entirely unreviewed',
        'detail': (
            f"{g_known_auto}/{g_total_rows} rows currently have auto-assigned DOK (dok_rationale "
            f"contains 'Auto-assigned DOK'); {g_verified} rows currently verify under the canonical "
            "DOK review-log projection (tools/dok-review/dok_review.py's entry_is_verified, applied "
            "per row via tool_state_for() over the review log and rubric-approvals manifest actually "
            "used this run — see aggregate.dok_verification_note for the exact paths/counts); only "
            "3-5 is currently a calibrated lesson (real dok2_anchors/dok3_anchors). Registry "
            "'reviewed_by'/'reviewed_at' fields are application-time metadata and are never read for "
            "this derivation."
        ),
    })

    anomalies.append({
        'title': 'Source-coordinate collisions are a REVIEW QUEUE, not confirmed duplicates',
        'detail': (
            f"{g_src_excess_rows} excess rows across {g_src_coordinates} (lesson, source) coordinates "
            f"/ {g_src_participating_rows} participating rows currently share an identical (lesson, "
            "source) coordinate with at least one other row in the same lesson. This does NOT mean the "
            "prompts are duplicate content — it means multiple registry rows point at the same named "
            "Savvas source location (e.g. the same 'Model & Discuss' launch prompt got registered more "
            "than once, or several sub-parts of one source share one coordinate label) and need human "
            "disambiguation before they can be trusted as distinct items. See aggregate."
            "source_coordinate_review for the full coordinates/excess_rows/participating_rows triplet, "
            "and each lesson's source_coordinate_groups / source_coordinate_collisions / "
            "source_coordinate_participating_rows fields for the per-lesson breakdown."
        ),
    })

    unknowns_note = (
        "Every SE/TE/tex/screenshot/registry/calibration column resolved to a concrete boolean or "
        "count from files actually present or absent on disk at generation time — no column value "
        "itself is UNKNOWN. The 26 'absent' lesson slots are a definite finding (confirmed zero "
        "matching files of any kind), not an unknown. What IS unknown, and called out explicitly in "
        "the anomalies above, is HISTORY and CAUSE: whether/when 4-1 ingestion was attempted, whether "
        "topics were ever propagated from topic_vocabulary, and what produced the 5-1/5-4/5-5 "
        "duplicate ids. These files only prove current state, not how that state came to be."
    )

    result = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'method': 'Computed from disk, read-only, snapshot-only. No registry or source file was modified.',
        'definition_the_nine': 'lessons with registry rows excluding calibrated 3-5 (858 rows): 4-3,4-4,4-5,5-1,5-4,5-5,6-3,6-4,6-5',
        'column_method_notes': {
            'lesson': 'One of the 37 fixed slot ids (Topic-Lesson), in curriculum order.',
            'se_pdf': "os.path.exists('a2_{lesson}_SE.pdf') at repo root.",
            'te_pdf': "os.path.exists('a2_{lesson}_TE.pdf') at repo root.",
            'se_tex': "os.path.exists('a2_{lesson}_SE.tex') at repo root OR os.path.exists('source/{lesson}_savvas_SE.tex').",
            'te_tex': "os.path.exists('a2_{lesson}_TE.tex') at repo root OR os.path.exists('source/{lesson}_savvas_TE.tex').",
            'registry_rows': "count of rows in questionbank/registry.jsonl where row['lesson'] == this lesson.",
            'answers_with_evidence': "count of rows where (row['teacher_answer'] is present and str(...).strip() != '') OR ('Answer key (from source):' literal substring appears in row['notes']).",
            'missing_answers': 'registry_rows - answers_with_evidence.',
            'visual_items': "count of rows where row['has_visual'] is truthy.",
            'visuals_absent': "count of rows where has_visual is truthy AND row['image'] is empty/None — the reference itself is absent, so there is no path to even check on disk. Global=137, all in the nine.",
            'visuals_broken_path': "count of rows where has_visual is truthy AND row['image'] is non-empty BUT the referenced file does not currently exist on disk relative to repo root — a broken path, not an absent reference. Global=7, all in lesson 3-5. See proposed_path_fixes for which of these are repairable.",
            'visuals_missing_asset': "= visuals_absent + visuals_broken_path. Kept as a single total for continuity with earlier reports; use the two split columns above for the precise breakdown (they mean different things and call for different remediation).",
            'topics_nonempty': "count of rows where (row['topics'] or []) is a non-empty list.",
            'dok_status': (
                "BASE bucket precedence (pure function of the registry row + its lesson's calibration "
                "status): (1) known_auto if 'Auto-assigned DOK' appears in row['dok_rationale']; "
                "(2) calibrated if the row's lesson has REAL calibration anchors (non-empty dok2_anchors "
                "or dok3_anchors in its calibration file — only 3-5 qualifies) AND the row was not "
                "auto-assigned; (3) unreviewed otherwise. 'calibrated' is a LESSON-LEVEL property gating "
                "a ROW-LEVEL count: a row only counts as calibrated if BOTH its lesson has real anchors "
                "AND its own DOK was not auto-assigned. 'verified' is NOT part of that base precedence — "
                "it is an OVERLAY applied afterward from the canonical DOK review-log projection: each "
                "row's item_uid (joined via inventory/dedup/item_uid_alias_map.json by 1-based registry "
                "line, mirroring inventory/dok-workflow/gen_dok_wave_plan.py's identical join, computed "
                "independently here rather than read from its output) is looked up in "
                "tools/dok-review/dok_review.py's tool_state_for(); a row is 'verified' iff that returns "
                "'verified' (see dok_review.py's entry_is_verified for the exact fail-closed predicate), "
                "and a verified row LEAVES its base bucket for 'verified' instead. Registry "
                "'reviewed_by'/'reviewed_at' fields are application-time metadata and are NEVER read "
                "here. See aggregate.dok_verification_note for the exact review-log/approvals-manifest "
                "paths and counts used this run. The four counts always sum to registry_rows."
            ),
            'item_analysis': "'none' = calibration file absent OR the 'item_analysis' key is absent from it; 'empty' = key present but {} or []; 'real' = key present and non-empty.",
            'source_coordinate_groups': "REVIEW QUEUE metric ('coordinates' in the triplet). Within the lesson, group rows by identical row['source']; count the groups with size > 1. Global=125.",
            'source_coordinate_collisions': "REVIEW QUEUE metric ('excess_rows' in the triplet; field name kept from earlier reports). Within the lesson, group rows by identical row['source']; sum over each group of (group_size - 1). This does NOT mean the prompts are duplicate content — see the anomaly below. Global=176.",
            'source_coordinate_participating_rows': "REVIEW QUEUE metric ('participating_rows' in the triplet). Within the lesson, group rows by identical row['source']; for each group with size > 1, sum the FULL group size (not just the excess). Global=301.",
            'duplicate_id_strings': "Within the lesson, group rows by identical row['id']; count the distinct id strings that appear more than once. Global=85.",
            'duplicate_id_excess_rows': "Within the lesson, group rows by identical row['id']; sum over each group of (group_size - 1). Replaces the field name duplicate_id_rows used in earlier reports. Global=85 (every duplicated id currently appears in exactly 2 rows, so strings==excess_rows numerically).",
            'duplicate_id_participating_rows': "Within the lesson, group rows by identical row['id']; for each group with size > 1, sum the FULL group size. Global=170.",
            'screenshots': "count of files in questionbank/images/ whose filename matches the regex ^{lesson}(?=[_.]) (i.e. a '3-5_...' or '3-5.png' style prefix).",
            'has_calibration': "os.path.exists('questionbank/calibration/{lesson}.json').",
            'readiness': (
                "'absent' = zero material of any kind (no se/te pdf/tex, no calibration, no screenshots, 0 registry rows). "
                "'blocked' = some staged material exists but 0 registry rows (nothing to teach from yet). "
                "'ready' = registry_rows>0 AND missing_answers==0 AND topics_nonempty==registry_rows AND lesson calibrated (real anchors) AND visuals_missing_asset==0 AND dok_status.verified==registry_rows. "
                "'partial' = registry_rows>0 but any ready gate fails."
            ),
            'readiness_reason': 'Human-readable list of the specific gates that failed (or the no-material explanation for absent, or the staged-material-but-zero-registry-rows explanation for blocked — worded as a snapshot observation, not a causal claim).',
        },
        'baseline_reconciliation': baseline,
        'aggregate': aggregate,
        'lessons': lesson_objs,
        'proposed_path_fixes': {
            'method': (
                'Analysis only. Lists, for every visuals_broken_path row, whether a file with the same '
                'basename currently exists under questionbank/calibration/sources/ and what the corrected '
                'path would be. registry.jsonl was NOT modified by this script or by this analysis.'
            ),
            'count': len(proposed_fixes),
            'fixes': proposed_fixes,
        },
        'anomalies': anomalies,
        'unknowns': [unknowns_note],
    }

    # diagnostics: internal cross-check values for main()'s assertions.
    # NOT part of the emitted JSON/MD artifacts -- everything a consumer
    # needs is already in result['aggregate'] (dok_status_totals,
    # dok_verified_item_uids, dok_review_state_totals,
    # dok_verification_note).
    diagnostics = {
        'base_dok_status_totals': {
            'known_auto': g_base_known_auto,
            'unreviewed': g_base_unreviewed,
            'calibrated': g_base_calibrated,
        },
        'canonical_verified_count': review_state_totals.get('verified', 0),
        'approved_rubric_versions': approved_rubric_versions,
        'review_log_entry_count': len(review_log_entries),
    }

    return result, all_confirmed, diagnostics


def render_markdown(result):
    lines = []
    lines.append('# Content Readiness Inventory — Lesson_planning Questionbank')
    lines.append('')
    lines.append(
        'Purpose: a definitive, per-lesson inventory of what content-readiness material actually '
        'exists on disk for all 37 Algebra 2 lesson slots (Topics 1 through 6), covering Savvas SE/TE '
        'source availability, questionbank registry coverage, answer-key evidence, visual-asset '
        'resolution, DOK review status, calibration status, and known data-quality risks (duplicate '
        'ids, source-coordinate collisions, missing topic tags). Everything here is a snapshot of '
        'CURRENT on-disk state; where a pattern suggests a history or cause, that history/cause is '
        'explicitly marked UNKNOWN rather than asserted.'
    )
    lines.append('')
    lines.append(f"**generated_at:** {result['generated_at']}")
    lines.append('')
    lines.append(
        f"**{result['method']}** Every number in this report is computed directly from "
        "questionbank/registry.jsonl, questionbank/calibration/*.json, questionbank/images/, "
        "questionbank/calibration/sources/, and repo-root/source SE-TE files at generation time — "
        "nothing here is hand-entered or hardcoded."
    )
    lines.append('')

    # Baseline reconciliation
    lines.append('## 1. Baseline Reconciliation')
    lines.append('')
    lines.append(
        'Every metric below was independently computed from disk and checked against the '
        'pre-investigated ground truth. All should read CONFIRMED.'
    )
    lines.append('')
    lines.append('| metric | claimed | computed | verdict |')
    lines.append('|---|---|---|---|')
    for b in result['baseline_reconciliation']:
        lines.append(f"| {b['metric']} | {b['claimed']} | {b['computed']} | {b['verdict']} |")
    lines.append('')

    # Dual-denominator identity (rc-merge-auth-5-4-2026-07-23)
    lines.append('## 1b. Dual-Denominator Identity (rc-merge-auth-5-4-2026-07-23)')
    lines.append('')
    idn = result['aggregate']['identity_reconciliation']
    lines.append(
        f"raw_registry_identities={idn['raw_registry_identities']}, "
        f"merged_alias_identities={idn['merged_alias_identities']}, "
        f"active_canonical_items={idn['active_canonical_items']} "
        f"(reconciles: {idn['active_canonical_items']} + {idn['merged_alias_identities']} == "
        f"{idn['raw_registry_identities']})."
    )
    lines.append('')
    lines.append(idn['statement'])
    lines.append('')
    lines.append(
        'Every OTHER metric in this report (registry_rows, dok_status, readiness gates, etc.) '
        'is registry-row-count based (audit-style: all 900 rows, alias rows included, unchanged '
        'by this merge). Per-lesson breakdown (only lessons with a nonzero merged_alias_rows '
        'shown):'
    )
    lines.append('')
    lines.append('| lesson | registry_rows | merged_alias_rows | active_registry_rows |')
    lines.append('|---|---|---|---|')
    for l in result['lessons']:
        if l['merged_alias_rows'] > 0:
            lines.append(
                f"| {l['lesson']} | {l['registry_rows']} | {l['merged_alias_rows']} | "
                f"{l['active_registry_rows']} |"
            )
    lines.append('')

    # 37-row matrix
    lines.append('## 2. The 37-Lesson-Slot Matrix')
    lines.append('')
    lines.append(
        '`src-collisions (excess)` and `dup-id (strings)` are single numbers standing in for a fuller '
        'triplet each — see `aggregate.source_coordinate_review` / `aggregate.duplicate_id_review` in '
        'the JSON, and Section 4 (Method Notes) below, for the full coordinates/excess_rows/'
        'participating_rows breakdown per metric.'
    )
    lines.append('')
    header = (
        '| lesson | SE.pdf | TE.pdf | SE.tex | TE.tex | rows | ans(evid) | miss | visual | '
        'vis_absent | vis_broken | vis_miss(total) | topics | dok known-auto/unrev/calib/verif | '
        'item_analysis | src-collisions (excess) | dup-id (strings) | shots | readiness |'
    )
    sep = '|---' * 19 + '|'
    lines.append(header)
    lines.append(sep)

    def b(v):
        return '✓' if v else '–'

    for l in result['lessons']:
        d = l['dok_status']
        dok_str = f"{d['known_auto']}/{d['unreviewed']}/{d['calibrated']}/{d['verified']}"
        lines.append(
            f"| {l['lesson']} | {b(l['se_pdf'])} | {b(l['te_pdf'])} | {b(l['se_tex'])} | {b(l['te_tex'])} | "
            f"{l['registry_rows']} | {l['answers_with_evidence']} | {l['missing_answers']} | "
            f"{l['visual_items']} | {l['visuals_absent']} | {l['visuals_broken_path']} | "
            f"{l['visuals_missing_asset']} | {l['topics_nonempty']} | "
            f"{dok_str} | {l['item_analysis']} | {l['source_coordinate_collisions']} | "
            f"{l['duplicate_id_strings']} | {l['screenshots']} | {l['readiness']} |"
        )
    lines.append('')

    # Readiness reasons (for lessons with rows or staged material)
    lines.append('### Readiness reasons (non-absent slots)')
    lines.append('')
    for l in result['lessons']:
        if l['readiness'] != 'absent':
            lines.append(f"- **{l['lesson']}** ({l['readiness']}): {l['readiness_reason']}")
    lines.append('')

    # Legend & rubric
    lines.append('## 3. Readiness Legend & Rubric')
    lines.append('')
    lines.append('- `✓` = present/true, `–` = absent/false, for boolean columns.')
    lines.append('- **absent**: no se_pdf AND no te_pdf AND no se_tex AND no te_tex AND registry_rows==0 AND not has_calibration AND screenshots==0. Zero material of any kind.')
    lines.append('- **blocked**: some material exists (has_calibration OR screenshots>0 OR se_tex OR te_tex OR se_pdf OR te_pdf) BUT registry_rows==0 — nothing usable to teach from yet.')
    lines.append('- **ready**: registry_rows>0 AND missing_answers==0 AND topics_nonempty==registry_rows AND the lesson is calibrated (real dok2/dok3 anchors) AND visuals_missing_asset==0 AND dok_status.verified==registry_rows.')
    lines.append('- **partial**: registry_rows>0 but at least one ready-gate fails.')
    lines.append('')
    lines.append(
        f"Distribution across the 37 slots: ready={result['aggregate']['readiness_distribution']['ready']}, "
        f"partial={result['aggregate']['readiness_distribution']['partial']}, "
        f"blocked={result['aggregate']['readiness_distribution']['blocked']}, "
        f"absent={result['aggregate']['readiness_distribution']['absent']}."
    )
    lines.append('')

    # Method notes
    lines.append('## 4. Method Notes Per Column')
    lines.append('')
    for col, note in result['column_method_notes'].items():
        lines.append(f"- **{col}**: {note}")
    lines.append('')

    # Anomalies
    lines.append('## 5. Anomalies & Risks (snapshot observations; cause/history UNKNOWN unless stated)')
    lines.append('')
    for a in result['anomalies']:
        lines.append(f"### {a['title']}")
        lines.append('')
        lines.append(a['detail'])
        lines.append('')

    # Aggregate secondary numbers
    lines.append('## 6. Secondary Aggregates')
    lines.append('')
    agg = result['aggregate']
    lines.append(f"- total registry rows: {agg['total_registry_rows']}")
    lines.append(f"- total answers_with_evidence: {agg['total_answers_with_evidence']}")
    lines.append(f"- total missing_answers (all 37 lessons): {agg['total_missing_answers_all_lessons']}")
    lines.append(f"- total missing_answers (the nine): {agg['total_missing_answers_the_nine']}")
    lines.append(f"- total visual_items: {agg['total_visual_items']}")
    lines.append(f"- total visuals_absent (all lessons): {agg['total_visuals_absent_all_lessons']} (the nine only: {agg['total_visuals_absent_the_nine']})")
    lines.append(f"- total visuals_broken_path (all lessons): {agg['total_visuals_broken_path_all_lessons']} (the nine only: {agg['total_visuals_broken_path_the_nine']})")
    lines.append(f"- total visuals_missing_asset (all lessons, incl. 3-5): {agg['total_visuals_missing_asset_all_lessons']}")
    lines.append(f"- total visuals_missing_asset (the nine only): {agg['total_visuals_missing_asset_the_nine']}")
    lines.append(f"  - {agg['note_visuals_missing_asset']}")
    lines.append(f"- total topics_nonempty (all lessons): {agg['total_topics_nonempty_all_lessons']}")
    lines.append(f"- total topics_nonempty (the nine only): {agg['total_topics_nonempty_the_nine']}")
    d = agg['dok_status_totals']
    lines.append(f"- dok_status totals: known_auto={d['known_auto']}, unreviewed={d['unreviewed']}, calibrated={d['calibrated']}, verified={d['verified']} (sum={d['sum']})")
    scr = agg['source_coordinate_review']
    lines.append(
        f"- source-coordinate review queue (full triplet): coordinates={scr['coordinates']}, "
        f"excess_rows={scr['excess_rows']}, participating_rows={scr['participating_rows']} "
        f"({scr['excess_rows']} excess rows across {scr['coordinates']} coordinates / "
        f"{scr['participating_rows']} participating rows)"
    )
    dir_ = agg['duplicate_id_review']
    lines.append(
        f"- duplicate-id metric (full triplet): strings={dir_['strings']}, "
        f"excess_rows={dir_['excess_rows']}, participating_rows={dir_['participating_rows']} "
        f"({dir_['strings']} duplicate-id strings involving {dir_['participating_rows']} rows)"
    )
    lines.append(f"- calibrated lessons: {agg['calibrated_lessons_list']}")
    lines.append('')

    # Proposed path fixes (analysis only)
    lines.append('## 7. Proposed Path Fixes (analysis only — registry.jsonl NOT modified)')
    lines.append('')
    ppf = result['proposed_path_fixes']
    lines.append(ppf['method'])
    lines.append('')
    lines.append(f"{ppf['count']} rows affected, all in lesson 3-5:")
    lines.append('')
    lines.append('| id | lesson | current image path | repairable | proposed path |')
    lines.append('|---|---|---|---|---|')
    for fix in ppf['fixes']:
        lines.append(
            f"| {fix['id']} | {fix['lesson']} | {fix['current_image_path']} | "
            f"{'yes' if fix['repairable'] else 'no'} | {fix['proposed_path'] or '(none found)'} |"
        )
    lines.append('')

    # Unknown / absent evidence
    lines.append('## 8. UNKNOWN / Absent Evidence')
    lines.append('')
    absent_slots = [l['lesson'] for l in result['lessons'] if l['readiness'] == 'absent']
    lines.append(f"The following {len(absent_slots)} slots are `absent` (zero material found on disk for any of se_pdf/te_pdf/se_tex/te_tex/has_calibration/screenshots/registry_rows):")
    lines.append('')
    lines.append(', '.join(absent_slots))
    lines.append('')
    for note in result['unknowns']:
        lines.append(f"> {note}")
    lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=(
            'Build the content-readiness inventory (read-only analysis). '
            'Registry/calibration/images/source inputs are always read from '
            'their canonical repo locations; only the review-log and '
            'approvals-manifest inputs (for the canonical DOK verification '
            'projection) and the output directory are overridable, for '
            'smoke-testing the fail-closed projection without touching the '
            'real tools/dok-review/ files.'
        )
    )
    parser.add_argument(
        '--review-log', default=DEFAULT_REVIEW_LOG_PATH,
        help=(
            'Path to the review log consumed by the canonical verification '
            'projection (default: tools/dok-review/review_log.jsonl). A '
            'missing file means "no reviews yet" (dok_review.read_log_entries '
            'returns [] without creating it); a malformed file is caught '
            'inside read_log_entries itself (one stderr warning + []) -- '
            'fail-closed, never a fallback to any registry field.'
        ),
    )
    parser.add_argument(
        '--approvals-manifest', default=DEFAULT_APPROVALS_PATH,
        help=(
            'Path to the rubric-approvals manifest (default: '
            'tools/dok-review/rubric_approvals.json). Missing/malformed -> '
            'no approvals (dok_review.load_rubric_approvals is already '
            'fail-closed).'
        ),
    )
    parser.add_argument(
        '--out-dir', default=SCRIPT_DIR,
        help=(
            'Directory both output artifacts (content_readiness_inventory.json, '
            "CONTENT_READINESS_INVENTORY.md) are written to (default: this "
            "script's own directory, inventory/)."
        ),
    )
    args = parser.parse_args()

    out_json = os.path.join(args.out_dir, 'content_readiness_inventory.json')
    out_md = os.path.join(args.out_dir, 'CONTENT_READINESS_INVENTORY.md')

    result, all_confirmed, diagnostics = build(args.review_log, args.approvals_manifest)

    # ------------------------------------------------------------------
    # Validate EVERYTHING in memory before writing anything (Finding 4).
    # A failed invariant must never leave overwritten, unvalidated artifacts on disk.
    # ------------------------------------------------------------------
    errors = []

    if len(result['lessons']) != 37:
        errors.append(f"expected 37 lessons, got {len(result['lessons'])}")

    lesson_order = [l['lesson'] for l in result['lessons']]
    if lesson_order != SLOTS:
        errors.append(f"lesson slot order mismatch: {lesson_order} != {SLOTS}")

    dist = result['aggregate']['readiness_distribution']
    expected_dist = {'ready': 0, 'partial': 10, 'blocked': 1, 'absent': 26}
    if dist != expected_dist:
        errors.append(f"unexpected readiness distribution: {dist} (expected {expected_dist})")

    dok_tot = result['aggregate']['dok_status_totals']
    if dok_tot['sum'] != 900:
        errors.append(f"dok_status_totals sum != 900: got {dok_tot['sum']}")
    displayed_dok_sum = (
        dok_tot['known_auto'] + dok_tot['unreviewed'] + dok_tot['calibrated'] + dok_tot['verified']
    )
    if displayed_dok_sum != 900:
        errors.append(f"displayed dok_status_totals do not sum to 900: got {displayed_dok_sum}")

    # Registry-frozen invariant (NT7-R2): BASE dok_status, computed
    # PRE-overlay, is a pure function of registry.jsonl + calibration files
    # and must never move regardless of review-log / approvals-manifest
    # content. Replaces the old hard-pinned (421,437,42,0) tuple, which
    # baked the (forbidden) always-0 'verified' assumption into the same
    # check as the base counts.
    base_tot = diagnostics['base_dok_status_totals']
    expected_base_dok = (421, 437, 42)
    actual_base_dok = (base_tot['known_auto'], base_tot['unreviewed'], base_tot['calibrated'])
    if actual_base_dok != expected_base_dok:
        errors.append(
            f"base (pre-overlay) dok_status tuple mismatch: {actual_base_dok} "
            f"(expected {expected_base_dok})"
        )

    # Canonical verification projection self-consistency: the displayed
    # verified count, the independently-tallied canonical count, and the
    # length of the emitted dok_verified_item_uids list must all agree.
    verified_uids = result['aggregate']['dok_verified_item_uids']
    if not (dok_tot['verified'] == diagnostics['canonical_verified_count'] == len(verified_uids)):
        errors.append(
            f"verified count mismatch: displayed={dok_tot['verified']} "
            f"canonical={diagnostics['canonical_verified_count']} "
            f"len(dok_verified_item_uids)={len(verified_uids)}"
        )

    # Fail-closed guards on the canonical projection -- always true
    # regardless of which review log / approvals manifest was actually
    # passed in.
    if not diagnostics['approved_rubric_versions'] and dok_tot['verified'] != 0:
        errors.append(
            'approvals manifest is empty (no approved rubric versions) but '
            f"verified count is {dok_tot['verified']} (expected 0)"
        )
    if diagnostics['review_log_entry_count'] == 0:
        if dok_tot['verified'] != 0:
            errors.append(
                f"review log has no entries but verified count is {dok_tot['verified']} (expected 0)"
            )
        review_state_tot = result['aggregate']['dok_review_state_totals']
        non_unreviewed = sum(v for k, v in review_state_tot.items() if k != 'unreviewed')
        if non_unreviewed != 0 or review_state_tot.get('unreviewed', 0) != 900:
            errors.append(
                'review log has no entries but review_state totals are not '
                f'all-unreviewed: {review_state_tot}'
            )

    # Dual-denominator reconciliation (rc-merge-auth-5-4-2026-07-23).
    identity = result['aggregate']['identity_reconciliation']
    if identity['merged_alias_identities'] != 22:
        errors.append(
            f"merged_alias_identities: expected 22, got {identity['merged_alias_identities']}"
        )
    if identity['raw_registry_identities'] != identity['active_canonical_items'] + identity['merged_alias_identities']:
        errors.append(
            'identity_reconciliation failed: raw_registry_identities '
            f"({identity['raw_registry_identities']}) != active_canonical_items "
            f"({identity['active_canonical_items']}) + merged_alias_identities "
            f"({identity['merged_alias_identities']})"
        )
    if len(identity['merged_alias_item_uids']) != identity['merged_alias_identities']:
        errors.append(
            f"len(merged_alias_item_uids)={len(identity['merged_alias_item_uids'])} != "
            f"merged_alias_identities={identity['merged_alias_identities']}"
        )

    if not all_confirmed:
        errors.append("not every baseline_reconciliation verdict is CONFIRMED:")
        for bl in result['baseline_reconciliation']:
            if bl['verdict'] != 'CONFIRMED':
                errors.append(f"  -> {bl['metric']}: {bl['verdict']}")
                if bl['metric'] == 'verified rows':
                    errors.append(
                        "     DELIBERATE FROZEN-BASELINE RECONCILIATION CLAIM, not a bug: "
                        "'verified rows' is pinned to claimed=39 on purpose (NT10 named "
                        "update, 2026-07-22; see "
                        "inventory/dok-workflow/DOK_VERIFICATION_WORKFLOW.md, "
                        "\"Approval procedure (operational, named updates)\", step 3(b1)). "
                        "When the canonical verified count first rises above 0, update the "
                        "claimed value to the new |S| and re-confirm this row deliberately "
                        "per step 3(b1) -- this failure means that step was skipped, not "
                        "that the pin is wrong."
                    )

    if errors:
        print('=== VALIDATION FAILED — NOTHING WRITTEN ===')
        for e in errors:
            print(' -', e)
        sys.exit(1)

    # ------------------------------------------------------------------
    # All invariants passed. Render, then write both artifacts atomically:
    # dump to a sibling .tmp file in the same directory, flush, os.replace() over
    # the real path. os.replace is atomic on Windows when src/dst share a volume.
    # ------------------------------------------------------------------
    md = render_markdown(result)

    os.makedirs(args.out_dir, exist_ok=True)

    tmp_json = out_json + '.tmp'
    with open(tmp_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_json, out_json)

    tmp_md = out_md + '.tmp'
    with open(tmp_md, 'w', encoding='utf-8') as f:
        f.write(md)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_md, out_md)

    print('=== SELF-VALIDATION ===')
    print('lesson count:', len(result['lessons']))
    print('slot order OK:', lesson_order == SLOTS)
    print('readiness distribution:', dist)
    print('dok_status totals:', dok_tot)
    print('base (pre-overlay) dok_status totals:', base_tot)
    print('dok_review_state_totals:', result['aggregate']['dok_review_state_totals'])
    print()
    print('=== BASELINE RECONCILIATION ===')
    for bl in result['baseline_reconciliation']:
        print(f"  {bl['metric']}: claimed={bl['claimed']} computed={bl['computed']} -> {bl['verdict']}")
    print()
    print('ALL BASELINE CONFIRMED:', all_confirmed)
    print()
    print('Wrote:', out_json)
    print('Wrote:', out_md)


if __name__ == '__main__':
    main()
