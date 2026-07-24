"""audit_match_quality.py -- NT5 provenance audit (read-only).

NT10 canonicalization pass (2026-07-22, Fable-authorized; the workflow
doc's step 3(f) NAMED FUTURE PASS, now PERFORMED): this audit was written
against the NT5 snapshot (match_quality totals 224/4/672; base-only
dok_status; zero review-log entries). Since then (a) lesson 5-4's TE
p.258 item_analysis was transcribed into questionbank/calibration/5-4.json
(NT9: exact 224 -> 285), and (b) the FIRST real review-log entries landed
(NT10: RC's 39 lesson-5-4 rule-1 batch confirmations; the frozen plan's
dok_status now carries the canonical 'verified' overlay). This pass
re-pins the match_quality totals to the recomputed present and makes the
row-level cross-check compare like-with-like: the audit now recomputes the
BASE dok_status AND applies the SAME canonical review-state overlay every
other consumer uses (tools/dok-review/dok_review.py's tool_state_for over
the real review log + approvals manifest -- imported, never
reimplemented) before comparing to the frozen plan's dok_status.

Historical note -- the question this audit originally answered for RC
(why did the 22 lesson-5-4 DOK-conflict pairs carry match_quality "none"
despite questionbank/calibration/5-4.json existing?) is now RESOLVED: the
5-4 calibration file's item_analysis was empty then; it is populated now
(TE p.258 transcription), so all 44 conflict-pair rows read 'exact'. The
branch-mechanism analysis (prefix+digit vs non-prefix populations) is
retained -- it is the durable part of that answer.

READ-ONLY with respect to every source it touches:
  - questionbank/registry.jsonl
  - questionbank/calibration/*.json
  - inventory/dedup/item_uid_alias_map.json
  - inventory/dashboard/content_readiness.json (cross-check only)
  - inventory/dok-workflow/gen_dok_wave_plan.py (imported as a module for
    its functions; NEVER calls main(), so it never writes
    dok_wave_plan.json)
  - tools/dok-review/dok_review.py (imported for the canonical projection
    only: read_log_entries / load_rubric_approvals / latest_entries_by_uid
    / tool_state_for; nothing invoked here ever writes the review log)
  - tools/dok-review/review_log.jsonl + rubric_approvals.json (read-only
    inputs to that projection)

Writes exactly one file: provenance_audit_data.json, in this same
directory (inventory/provenance-audit/). No network imports
(no requests/urllib/socket), no subprocess calls.

Matching-logic provenance: this script does not reimplement the
match_quality algorithm from scratch. It imports
inventory/dok-workflow/gen_dok_wave_plan.py and calls its functions
directly:
  - G.load_registry()          (gen_dok_wave_plan.py:191-199)
  - G.load_alias_map()          (gen_dok_wave_plan.py:202-211)
  - G.load_calibration()        (gen_dok_wave_plan.py:214-223)
  - G.calibration_has_real_anchors()  (gen_dok_wave_plan.py:226-233)
  - G.build_item_to_dok()       (gen_dok_wave_plan.py:236-273)
  - G.compute_dok_status()      (gen_dok_wave_plan.py:279-287)
  - G.compute_te_match()        (gen_dok_wave_plan.py:293-316)
This alone would only mean the audit uses the *same code path* as the
generator -- it would not by itself prove the audit's numbers match the
frozen dok_wave_plan.json (e.g. the frozen file could be stale relative
to current registry.jsonl/calibration/*.json). The actual guarantee is
established by an explicit cross-check (see step 3 in main(), below):
this script also reads inventory/dok-workflow/dok_wave_plan.json
read-only, flattens its waves[wave][lesson][] lists keyed by item_uid,
and asserts -- for all rows currently in the registry (919 as of
nt14-ingest-4-1-2026-07-23; 900 at NT5 writing) -- that the frozen plan's
registry_line/id/lesson/dok/dok_status/te_bucket/match_quality/status/
alias_of/availability fields equal what this script independently
recomputes from the current on-disk sources. A mismatch fails loudly (assertion error, nothing
written) instead of silently reporting stale or drifted numbers. The
only code this script adds is (a) the validation harness that
recomputes wave-plan totals and per-lesson breakdowns and cross-checks
them against the frozen dok_wave_plan.json row-by-row, (b) the
reason_code classifier for why a given row's match_quality is "none"
(built directly on top of compute_te_match's own branch order -- see
reason_code_for()), and (c) the 22-conflict-pair finder.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # .../Lesson_planning
DOK_WORKFLOW_DIR = os.path.join(REPO_ROOT, 'inventory', 'dok-workflow')

REGISTRY_PATH = os.path.join(REPO_ROOT, 'questionbank', 'registry.jsonl')
ALIAS_MAP_PATH = os.path.join(REPO_ROOT, 'inventory', 'dedup', 'item_uid_alias_map.json')
CONTENT_READINESS_PATH = os.path.join(REPO_ROOT, 'inventory', 'dashboard', 'content_readiness.json')
DOK_WAVE_PLAN_PATH = os.path.join(DOK_WORKFLOW_DIR, 'dok_wave_plan.json')
OUT_JSON = os.path.join(SCRIPT_DIR, 'provenance_audit_data.json')

sys.dont_write_bytecode = True  # never leave a __pycache__/*.pyc behind in dok-workflow/
sys.path.insert(0, DOK_WORKFLOW_DIR)
import gen_dok_wave_plan as G  # noqa: E402  (read-only import; main() is never called)

DOK_REVIEW_TOOL_DIR = os.path.join(REPO_ROOT, 'tools', 'dok-review')
sys.path.insert(0, DOK_REVIEW_TOOL_DIR)
import dok_review as DR  # noqa: E402  (read-only import; canonical projection only)

# NT10 canonicalization re-pins (step 3(f) pass, 2026-07-22): exact
# 224 -> 285 / none 672 -> 611 after NT9's 5-4 TE p.258 item_analysis
# transcription (61 lesson-5-4 rows flipped none -> exact). derived and
# the 900 total are unchanged. The BASE dok_status totals below are the
# registry-derived invariant (identical to gen_dok_wave_plan.py's
# EXPECTED_BASE_DOK_STATUS_TOTALS); the CANONICAL (overlaid) totals are
# deliberately NOT pinned here -- they move with every recording batch,
# and drift is caught state-neutrally by the row-level cross-check
# against the frozen plan instead.
# NT14 named re-pin (nt14-ingest-4-1-2026-07-23, 2026-07-23): 19 new rows
# appended for lesson 4-1 (all availability=='optional-catalog'). This is a
# full AUDIT surface (see module docstring / identity_reconciliation below)
# -- it recomputes over EVERY row currently in registry.jsonl, so its totals
# are the RAW figures (919), unlike content_readiness_inventory.json's
# completion/readiness aggregates, which exclude these 19 rows by binding
# course policy. All 19 rows are Savvas-declared (not 'Auto-assigned DOK')
# and lesson 4-1 is not calibrated, so they land in base dok_status
# 'unreviewed' (437 -> 456); their ids/item numbers (q8..q26) all match
# 4-1's real, populated item_analysis, so match_quality 'exact' rises by
# exactly 19 (285 -> 304); 'derived' and 'none' are untouched.
EXPECTED_EXACT = 304
EXPECTED_DERIVED = 4
EXPECTED_NONE = 611
EXPECTED_TOTAL = 919
EXPECTED_CONFLICT_PAIRS = 22
EXPECTED_BASE_DOK_STATUS = {'known_auto': 421, 'unreviewed': 456, 'calibrated': 42}
TARGET_LESSON = '5-4'

# NT11 addition (rc-merge-auth-5-4-2026-07-23): registry-derived, invariant
# while the registry stays frozen -- same status as EXPECTED_BASE_DOK_STATUS
# above. This is an AUDIT surface (per RC's dual-denominator semantics): it
# carries and explicitly marks all 22 merged-alias rows, never drops them.
EXPECTED_MERGED_ALIAS_ROWS = 22
# NT14 addition (nt14-ingest-4-1-2026-07-23): same AUDIT-surface treatment
# for the 19 optional-catalog rows (lesson 4-1) -- carried and explicitly
# marked, never dropped, here alongside the merged-alias rows.
EXPECTED_OPTIONAL_CATALOG_ROWS = 19
EXPECTED_ACTIVE_CANONICAL_ITEMS = 878


def sha1_hex(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def main():
    rows = G.load_registry()
    calibration = G.load_calibration()
    alias = G.load_alias_map()
    calibrated_lessons = {les for les, cal in calibration.items() if G.calibration_has_real_anchors(cal)}
    item_to_dok = G.build_item_to_dok(calibration)

    # item_uid identity join (built up front so both the per-row totals
    # loop below and the dok_wave_plan.json cross-check in step 1b can
    # use it): mirrors gen_dok_wave_plan.py:357-360 exactly.
    alias_map = alias['alias_map']
    line2uid = {}
    for _legacy_id, entry in alias_map.items():
        for u in entry['item_uids']:
            line2uid[u['registry_line']] = u['item_uid']

    # ------------------------------------------------------------------
    # 1. Recompute match_quality / dok_status for all rows currently in the
    #    registry (919, nt14-ingest-4-1-2026-07-23) using gen_dok_wave_plan.py's
    #    own functions, and verify the frozen totals (304 exact / 4 derived /
    #    611 none) reproduce exactly.
    #
    #    NT10 (step 3(f) pass): dok_status is now computed LIKE-WITH-LIKE
    #    against the frozen plan -- the registry-derived BASE status
    #    (G.compute_dok_status, which never returns 'verified') plus the
    #    SAME canonical review-state overlay every other consumer applies
    #    (dok_review.tool_state_for over the real review log + approvals
    #    manifest; 'verified' overlays the base status iff the canonical
    #    state is 'verified' -- mirroring gen_dok_wave_plan.py's main()
    #    overlay exactly). Both the base and the canonical value are kept
    #    per row.
    # ------------------------------------------------------------------
    review_log_entries = DR.read_log_entries(DR.DEFAULT_LOG)  # fail-closed: [] on any defect
    approved_versions = DR.load_rubric_approvals()            # fail-closed: {} on any defect
    latest_by_uid = DR.latest_entries_by_uid(review_log_entries)

    per_row = []  # parallel to rows, 0-indexed; line_no = index+1
    mq_totals = Counter()
    mq_by_lesson = Counter()
    base_dok_status_totals = Counter()
    dok_status_totals = Counter()   # canonical (overlay applied)
    review_state_totals = Counter()
    merge_status_totals = Counter()  # rc-merge-auth-5-4-2026-07-23
    # NT14 addition (nt14-ingest-4-1-2026-07-23): parallel AUDIT-surface
    # tally for the new 'availability' marker, alongside merge_status_totals
    # above -- same "carry and explicitly mark every row, never drop it"
    # philosophy this audit already applies to merged-alias rows.
    availability_totals = Counter()

    for line_no, row in enumerate(rows, start=1):
        lesson = row.get('lesson')
        dok_status_base = G.compute_dok_status(row, calibrated_lessons)
        item_uid = line2uid.get(line_no)
        review_state = DR.tool_state_for(
            item_uid, latest_by_uid, _approved_versions_override=approved_versions,
        )
        dok_status = 'verified' if review_state == 'verified' else dok_status_base
        item_number, te_bucket, match_quality = G.compute_te_match(row, item_to_dok)
        # rc-merge-auth-5-4-2026-07-23 (additive): recomputed independently
        # from the registry row itself, mirroring gen_dok_wave_plan.py's
        # identical merge-status overlay -- never read from the frozen plan
        # (that would make the cross-check below tautological). Left
        # exactly as-is for NT14: 'status' tracks the merge/alias mechanism
        # only -- optional-catalog rows carry status=='active' here (they
        # are not merged-alias rows), matching the frozen plan's own
        # per-item 'status' field for them, cross-checked below via
        # CROSS_CHECK_FIELDS. 'availability' (new, orthogonal marker) is
        # tracked separately just below.
        merge_status = row.get('status') if row.get('status') == 'merged-alias' else 'active'
        row_alias_of = row.get('alias_of') if merge_status == 'merged-alias' else None
        # NT14 (nt14-ingest-4-1-2026-07-23, additive): recomputed
        # independently from the registry row itself, same non-tautological
        # discipline as merge_status above.
        availability = row.get('availability')
        mq_totals[match_quality] += 1
        mq_by_lesson[(lesson, match_quality)] += 1
        base_dok_status_totals[dok_status_base] += 1
        dok_status_totals[dok_status] += 1
        review_state_totals[review_state] += 1
        merge_status_totals[merge_status] += 1
        availability_totals[availability or 'none'] += 1
        per_row.append({
            'item_uid': item_uid,
            'registry_line': line_no,
            'lesson': lesson,
            'id': row.get('id'),
            'dok': row.get('dok'),
            'dok_status': dok_status,
            'dok_status_base': dok_status_base,
            'review_state': review_state,
            'item_number': item_number,
            'te_bucket': te_bucket,
            'match_quality': match_quality,
            'status': merge_status,
            'alias_of': row_alias_of,
            'availability': availability,
        })

    assert len(rows) == EXPECTED_TOTAL, f'expected {EXPECTED_TOTAL} registry rows, got {len(rows)}'
    # BASE dok_status totals are the registry-derived invariant -- they
    # hold regardless of review-log content (the overlay never mutates
    # the base computation).
    assert dict(base_dok_status_totals) == EXPECTED_BASE_DOK_STATUS, (
        f'base dok_status totals: expected {EXPECTED_BASE_DOK_STATUS}, '
        f'got {dict(base_dok_status_totals)}'
    )
    assert mq_totals.get('exact', 0) == EXPECTED_EXACT, (
        f"match_quality 'exact': expected {EXPECTED_EXACT}, got {mq_totals.get('exact', 0)}"
    )
    assert mq_totals.get('derived', 0) == EXPECTED_DERIVED, (
        f"match_quality 'derived': expected {EXPECTED_DERIVED}, got {mq_totals.get('derived', 0)}"
    )
    assert mq_totals.get('none', 0) == EXPECTED_NONE, (
        f"match_quality 'none': expected {EXPECTED_NONE}, got {mq_totals.get('none', 0)}"
    )
    assert sum(mq_totals.values()) == EXPECTED_TOTAL

    # ------------------------------------------------------------------
    # 1b. Row-level cross-check against the frozen
    #     inventory/dok-workflow/dok_wave_plan.json (read-only). This is
    #     the actual proof that this script's independently recomputed
    #     numbers agree with the shipped plan, not just that it calls the
    #     same functions. Flatten waves[wave][lesson][] keyed by
    #     item_uid (including the "optional-catalog" bucket, nt14-ingest-
    #     4-1-2026-07-23), then diff every one of the 919 rows on
    #     registry_line/id/lesson/dok/dok_status/te_bucket/match_quality/
    #     status/alias_of/availability.
    # ------------------------------------------------------------------
    with open(DOK_WAVE_PLAN_PATH, 'r', encoding='utf-8') as f:
        frozen_plan = json.load(f)

    # NOTE: the per-item dicts inside dok_wave_plan.json's waves[wave][lesson]
    # lists do NOT carry their own 'lesson' field (gen_dok_wave_plan.py:502-511
    # -- lesson is implicit in the dict's position under waves[w_key][les]).
    # Inject it here from the enclosing key so the cross-check below can
    # compare 'lesson' like any other field.
    frozen_by_uid = {}
    for _wave_key, lessons_dict in frozen_plan['waves'].items():
        for _lesson, plan_rows in lessons_dict.items():
            for pr in plan_rows:
                frozen_by_uid[pr['item_uid']] = {**pr, 'lesson': _lesson}

    assert len(frozen_by_uid) == EXPECTED_TOTAL, (
        f'expected {EXPECTED_TOTAL} item_uids in frozen dok_wave_plan.json, got {len(frozen_by_uid)}'
    )

    # NT10: 'dok_status' here is the canonical (overlay-applied) value, so
    # this stays like-with-like against the plan's own overlaid field;
    # 'review_state' (the additive canonical-projection field the plan
    # carries verbatim) is cross-checked too.
    # NT11 (rc-merge-auth-5-4-2026-07-23): 'status'/'alias_of' added so the
    # 22 merged-alias rows are explicitly carried and cross-checked in this
    # audit surface too, not silently dropped -- recomputed independently
    # from the registry row itself (see the per_row loop above), never read
    # from the frozen plan, so this is a real cross-check.
    # NT14 (nt14-ingest-4-1-2026-07-23): 'availability' added on the same
    # principle, for the 19 optional-catalog rows.
    CROSS_CHECK_FIELDS = (
        'registry_line', 'id', 'lesson', 'dok', 'dok_status', 'review_state',
        'te_bucket', 'match_quality', 'status', 'alias_of', 'availability',
    )
    cross_check_mismatches = []
    for rec in per_row:
        uid = rec['item_uid']
        frozen_rec = frozen_by_uid.get(uid)
        if frozen_rec is None:
            cross_check_mismatches.append((uid, 'MISSING_FROM_FROZEN_PLAN', None, None))
            continue
        for field in CROSS_CHECK_FIELDS:
            ours = rec.get(field)
            theirs = frozen_rec.get(field)
            if ours != theirs:
                cross_check_mismatches.append((uid, field, ours, theirs))

    assert not cross_check_mismatches, (
        f'{len(cross_check_mismatches)} field mismatch(es) vs frozen dok_wave_plan.json '
        f'(uid, field, recomputed, frozen): {cross_check_mismatches[:10]} (showing up to 10)'
    )
    cross_check_rows_note = (
        f'{len(per_row)}/{len(per_row)} rows agree with frozen dok_wave_plan.json on '
        f'{", ".join(CROSS_CHECK_FIELDS)} (row-level cross-check via item_uid join)'
    )

    # ------------------------------------------------------------------
    # 1c. Triple-split identity (rc-merge-auth-5-4-2026-07-23 + NT14
    # nt14-ingest-4-1-2026-07-23). This is an AUDIT surface: it carries and
    # explicitly marks all 919 identities (22 merged-alias rows + 19
    # optional-catalog rows included), never drops them.
    # ------------------------------------------------------------------
    merged_alias_count = merge_status_totals.get('merged-alias', 0)
    # NT14: merge_status_totals['active'] still includes the 19 optional-
    # catalog rows (they carry status=='active', NOT 'merged-alias' -- an
    # orthogonal marker; see the per_row loop above), so it must be reduced
    # by optional_catalog_count to get the true active/required count.
    optional_catalog_count = availability_totals.get('optional-catalog', 0)
    active_count = merge_status_totals.get('active', 0) - optional_catalog_count
    assert merged_alias_count == EXPECTED_MERGED_ALIAS_ROWS, (
        f'merged-alias row count: expected {EXPECTED_MERGED_ALIAS_ROWS}, got {merged_alias_count}'
    )
    assert optional_catalog_count == EXPECTED_OPTIONAL_CATALOG_ROWS, (
        f'optional-catalog row count: expected {EXPECTED_OPTIONAL_CATALOG_ROWS}, got {optional_catalog_count}'
    )
    assert active_count == EXPECTED_ACTIVE_CANONICAL_ITEMS, (
        f'active row count: expected {EXPECTED_ACTIVE_CANONICAL_ITEMS}, got {active_count}'
    )
    assert active_count + optional_catalog_count + merged_alias_count == EXPECTED_TOTAL, (
        f'identity reconciliation failed: active ({active_count}) + optional_catalog '
        f'({optional_catalog_count}) + merged_alias ({merged_alias_count}) != total ({EXPECTED_TOTAL})'
    )
    merged_alias_item_uids = sorted(r['item_uid'] for r in per_row if r['status'] == 'merged-alias')
    optional_catalog_item_uids = sorted(r['item_uid'] for r in per_row if r['availability'] == 'optional-catalog')

    # ------------------------------------------------------------------
    # 2. Per-lesson match_quality breakdown + whether the lesson's
    #    calibration file carries any usable item_analysis data (i.e.
    #    whether item_to_dok[lesson] is non-empty). This is the
    #    "source-coverage" signal: a lesson can only ever produce
    #    exact/derived rows if this is non-empty.
    # ------------------------------------------------------------------
    per_lesson = {}
    for les in G.LESSON_CURRICULUM_ORDER:
        exact = mq_by_lesson.get((les, 'exact'), 0)
        derived = mq_by_lesson.get((les, 'derived'), 0)
        none_ = mq_by_lesson.get((les, 'none'), 0)
        cal_entry = calibration.get(les)
        ia_raw = (cal_entry or {}).get('item_analysis')
        if ia_raw is None:
            ia_state = 'missing_key'  # calibration file has no 'item_analysis' key at all
        elif ia_raw == {}:
            ia_state = 'empty_dict'   # key present, but zero examples/buckets recorded
        else:
            ia_state = 'populated'
        per_lesson[les] = {
            'exact': exact,
            'derived': derived,
            'none': none_,
            'total': exact + derived + none_,
            'item_analysis_state': ia_state,
            'item_to_dok_numbers': len(item_to_dok.get(les, {})),
            'lesson_level_calibrated_dok_status': les in calibrated_lessons,
        }

    # ------------------------------------------------------------------
    # 3. Find the 22 DOK-conflict pairs: ambiguous legacy ids (shared by
    #    exactly 2 registry rows per inventory/dedup/item_uid_alias_map.json)
    #    where both rows are lesson 5-4 AND their registry 'dok' values
    #    differ. This mirrors the join
    #    inventory/dashboard/build_content_readiness.py performs between
    #    inventory/review-queue/collision_review_queue.json's ambiguous
    #    groups and dok_wave_plan.json's per-row dok
    #    (build_content_readiness.py:126-172), recomputed here directly
    #    from registry.jsonl + the alias map so it does not depend on
    #    the dashboard's own (also-read-only) output.
    # ------------------------------------------------------------------
    conflict_pairs = []
    for legacy_id, entry in alias_map.items():
        if not entry.get('ambiguous'):
            continue
        uids = entry['item_uids']
        if len(uids) != 2:
            continue
        lessons = {u['lesson'] for u in uids}
        if lessons != {TARGET_LESSON}:
            continue
        a, b = uids
        line_a, line_b = a['registry_line'], b['registry_line']
        dok_a_raw, dok_b_raw = rows[line_a - 1].get('dok'), rows[line_b - 1].get('dok')
        if dok_a_raw == dok_b_raw:
            continue  # same-DOK prompt-drift collision, not a DOK conflict
        # lower dok = "_a", higher dok = "_b" (matches
        # inventory/dashboard/content_readiness.json's dok_conflict_subset convention)
        if dok_a_raw <= dok_b_raw:
            lo, hi = a, b
            dok_lo, dok_hi = dok_a_raw, dok_b_raw
        else:
            lo, hi = b, a
            dok_lo, dok_hi = dok_b_raw, dok_a_raw
        # rc-merge-auth-5-4-2026-07-23 (additive): sourced from the dedup
        # map's OWN "resolved_alias" key (join-level, DELIBERATE resolution
        # -- never re-derived by guessing which of lo/hi is the alias),
        # mirroring inventory/dashboard/build_content_readiness.py's
        # identical annotation of its own dok_conflict_rows.
        resolved_alias = entry.get('resolved_alias')
        conflict_pairs.append({
            'legacy_id': legacy_id,
            'uid_a': lo['item_uid'], 'line_a': lo['registry_line'], 'dok_a': dok_lo,
            'uid_b': hi['item_uid'], 'line_b': hi['registry_line'], 'dok_b': dok_hi,
            'merged_alias_item_uid': resolved_alias['alias_uid'] if resolved_alias else None,
            'survivor_item_uid': resolved_alias['survivor_uid'] if resolved_alias else None,
        })
    conflict_pairs.sort(key=lambda p: p['legacy_id'])

    # Every one of these 22 conflict pairs IS one of the 22 merge-authorized
    # groups -- each must resolve to a merged-alias annotation.
    unresolved_pairs = [p['legacy_id'] for p in conflict_pairs if p['merged_alias_item_uid'] is None]
    assert not unresolved_pairs, (
        f'expected all {EXPECTED_CONFLICT_PAIRS} conflict pairs to have a resolved_alias '
        f'annotation, but these do not: {unresolved_pairs}'
    )

    assert len(conflict_pairs) == EXPECTED_CONFLICT_PAIRS, (
        f'expected {EXPECTED_CONFLICT_PAIRS} DOK-conflict pairs, got {len(conflict_pairs)}'
    )
    assert all(p['legacy_id'].startswith('5-4-') for p in conflict_pairs)

    # Cross-check against the dashboard's already-computed subset (read-only;
    # this script does not depend on it existing, but verifies agreement
    # when it does).
    cross_check_note = 'content_readiness.json not present; cross-check skipped'
    if os.path.isfile(CONTENT_READINESS_PATH):
        with open(CONTENT_READINESS_PATH, 'r', encoding='utf-8') as f:
            cr = json.load(f)
        dashboard_pairs = {
            (r['id'], r['dok_a'], r['dok_b'], r['uid_a'], r['uid_b'])
            for r in cr['dok_conflict_subset']['rows']
        }
        our_pairs = {
            (p['legacy_id'], p['dok_a'], p['dok_b'], p['uid_a'], p['uid_b'])
            for p in conflict_pairs
        }
        assert dashboard_pairs == our_pairs, 'conflict-pair set disagrees with content_readiness.json'
        cross_check_note = 'matches inventory/dashboard/content_readiness.json dok_conflict_subset exactly (22/22)'

    # ------------------------------------------------------------------
    # 3b. Branch-population split for lesson 5-4 (and, for completeness,
    #     every other lesson): compute_te_match (gen_dok_wave_plan.py:
    #     293-316) checks the '{lesson}-savvas-q' PREFIX FIRST (line 299),
    #     then the leading-digit parse (line 301) -- ONLY rows that pass
    #     both ever reach the item_to_dok lookup at line 305. Rows whose
    #     id lacks the prefix (or whose remainder doesn't start with
    #     digits) fall straight to the no-prefix branch at lines 312-316
    #     and never touch item_to_dok at all. So "none" for a given
    #     lesson is produced by up to two distinct branches, not one --
    #     this table makes that split explicit instead of asserting a
    #     single uniform mechanism.
    # ------------------------------------------------------------------
    branch_population_by_lesson = {}
    for les in G.LESSON_CURRICULUM_ORDER:
        prefix = f'{les}-savvas-q'
        prefix_rows_n = 0
        nonprefix_rows_n = 0
        for row in rows:
            if row.get('lesson') != les:
                continue
            rid = row.get('id') or ''
            if rid.startswith(prefix):
                rest = rid[len(prefix):]
                if G.re.match(r'^(\d+)(.*)$', rest):
                    prefix_rows_n += 1
                    continue
            nonprefix_rows_n += 1
        branch_population_by_lesson[les] = {
            'prefix_digit_rows': prefix_rows_n,   # reach the item_to_dok lookup (line 305)
            'nonprefix_rows': nonprefix_rows_n,   # short-circuit at lines 312-316, never look up
            'total': prefix_rows_n + nonprefix_rows_n,
        }

    target_lines = []
    for p in conflict_pairs:
        target_lines.append(p['line_a'])
        target_lines.append(p['line_b'])
    target_lines.sort()

    def reason_code_for(row, item_to_dok):
        """Derived directly from compute_te_match's own branch ORDER
        (gen_dok_wave_plan.py:293-316), not just its outcome: the prefix
        check (line 299) and leading-digit parse (line 301) are
        evaluated FIRST, exactly as in compute_te_match, before ever
        consulting item_to_dok. Only a row that passes both checks reaches
        the lookup at line 305, at which point the reason splits on
        whether the lesson has any item_to_dok data at all (empty/missing
        item_analysis) vs. has data but simply lacks this item number."""
        lesson = row.get('lesson')
        rid = row.get('id') or ''
        exact_prefix = f'{lesson}-savvas-q'
        if rid.startswith(exact_prefix):
            rest = rid[len(exact_prefix):]
            m = G.re.match(r'^(\d+)(.*)$', rest)
            if m:
                item_number = int(m.group(1))
                mapping = item_to_dok.get(lesson, {})
                if item_number in mapping:
                    return 'MATCHED'  # should not occur for a 'none' row
                if not mapping:
                    return 'NO_ITEM_ANALYSIS_DATA_FOR_LESSON'
                return 'ITEM_NUMBER_NOT_IN_TE_BUCKET'
        # id doesn't start with '{lesson}-savvas-q', or the remainder
        # doesn't start with digits: same short-circuit as
        # compute_te_match's lines 312-316 -- item_to_dok is never
        # consulted for this row at all.
        return 'NO_SAVVAS_ID_PREFIX_MATCH'

    evidence_rows = []
    pair_by_line = {}
    for p in conflict_pairs:
        pair_by_line[p['line_a']] = (p['legacy_id'], 'lower_dok_copy')
        pair_by_line[p['line_b']] = (p['legacy_id'], 'higher_dok_copy')

    for line_no in target_lines:
        row = rows[line_no - 1]
        prompt = row.get('prompt') or ''
        prompt_sha1_recomputed = sha1_hex(prompt)
        # prompt_sha1 as recorded in the alias map (independently computed
        # by inventory/dedup/build_item_uid_map.py at a prior point in time).
        item_uid = line2uid.get(line_no)
        alias_entry = alias_map.get(row.get('id'), {})
        stored_prompt_sha1 = None
        for u in alias_entry.get('item_uids', []):
            if u['registry_line'] == line_no:
                stored_prompt_sha1 = u['prompt_sha1']
                break

        item_number, te_bucket, match_quality = G.compute_te_match(row, item_to_dok)
        dok_status_base = G.compute_dok_status(row, calibrated_lessons)
        review_state = DR.tool_state_for(
            item_uid, latest_by_uid, _approved_versions_override=approved_versions,
        )
        dok_status = 'verified' if review_state == 'verified' else dok_status_base
        reason_code = reason_code_for(row, item_to_dok)
        legacy_id, pair_role = pair_by_line[line_no]

        evidence_rows.append({
            'item_uid': item_uid,
            'registry_line': line_no,
            'legacy_id': row.get('id'),
            'pair_id': legacy_id,
            'pair_role': pair_role,
            'lesson': row.get('lesson'),
            'dok': row.get('dok'),
            'dok_rationale': row.get('dok_rationale'),
            'role': row.get('role'),
            'dok_status': dok_status,
            'dok_status_base': dok_status_base,
            'review_state': review_state,
            'te_bucket': te_bucket,
            'match_quality': match_quality,
            'reason_code': reason_code,
            'source': row.get('source'),
            'page': row.get('page'),
            'created_at': row.get('created_at'),
            'prompt': prompt,
            'prompt_sha1_stored_in_alias_map': stored_prompt_sha1,
            'prompt_sha1_recomputed_from_registry_prompt': prompt_sha1_recomputed,
            'prompt_sha1_recompute_matches_stored': stored_prompt_sha1 == prompt_sha1_recomputed,
        })

    assert len(evidence_rows) == 44, f'expected 44 evidence rows, got {len(evidence_rows)}'
    # NT10 canonical present (was: all 44 'none' with reason
    # NO_ITEM_ANALYSIS_DATA_FOR_LESSON, when 5-4's item_analysis was still
    # empty): the TE p.258 transcription populated item_to_dok['5-4'], so
    # every conflict-pair row now matches its own item number 'exact'.
    assert all(r['match_quality'] == 'exact' for r in evidence_rows)
    assert all(r['reason_code'] == 'MATCHED' for r in evidence_rows)
    assert all(r['te_bucket'] is not None for r in evidence_rows)
    # NT10 recording effect on the pairs: RC's batch confirmation verified
    # the TE-agreeing copy of every conflict pair (and ONLY that copy) --
    # exactly one member of each pair is canonically 'verified', the other
    # stays at its base status. Checked per pair, not just in aggregate.
    verified_by_pair = Counter(
        r['pair_id'] for r in evidence_rows if r['review_state'] == 'verified'
    )
    assert sum(verified_by_pair.values()) == 22, (
        f'expected exactly 22 verified rows among the 44 conflict-pair rows, '
        f'got {sum(verified_by_pair.values())}'
    )
    assert all(verified_by_pair.get(p["legacy_id"], 0) == 1 for p in conflict_pairs), (
        'expected exactly ONE verified member per conflict pair'
    )
    assert all(
        (r['dok_status'] == 'verified') == (r['review_state'] == 'verified')
        for r in evidence_rows
    )
    # Independent confirmation (not just via reason_code) that all 44 rows
    # belong to the prefix+digit branch population, i.e. their id is a
    # bare '{lesson}-savvas-q{N}' string that DOES reach the item_to_dok
    # lookup -- none of the 44 are no-prefix rows that short-circuit
    # before ever consulting item_to_dok.
    assert all(
        G.re.match(r'^(\d+)$', r['legacy_id'][len(f"{r['lesson']}-savvas-q"):]) is not None
        for r in evidence_rows
        if r['legacy_id'].startswith(f"{r['lesson']}-savvas-q")
    ) and all(r['legacy_id'].startswith(f"{r['lesson']}-savvas-q") for r in evidence_rows), (
        'expected all 44 conflict-pair rows to be bare prefix+digit ids (the branch that '
        'reaches item_to_dok), found at least one outside that population'
    )

    # ------------------------------------------------------------------
    # 5. Write output (this directory only).
    # ------------------------------------------------------------------
    output = {
        'generated_by': (
            'audit_match_quality.py (NT5 provenance audit; NT10 canonicalization pass, step 3(f); '
            'NT14 re-pin, nt14-ingest-4-1-2026-07-23)'
        ),
        'source_note': (
            'Derived read-only from questionbank/registry.jsonl, '
            'questionbank/calibration/*.json, inventory/dedup/item_uid_alias_map.json, '
            'inventory/dok-workflow/gen_dok_wave_plan.py (imported for its functions '
            'only -- main() never called, dok_wave_plan.json never written by this script), '
            'and tools/dok-review/dok_review.py (imported for the canonical review-state '
            'projection only, over tools/dok-review/review_log.jsonl + rubric_approvals.json '
            '-- nothing here ever writes the review log). '
            'dok_status is the canonical value: registry-derived BASE status plus the '
            "'verified' overlay wherever the canonical projection reads 'verified' -- "
            'the SAME like-with-like value the frozen plan carries. '
            'Cross-checked, where present, against inventory/dashboard/content_readiness.json, '
            'and row-by-row (all 919 rows, via item_uid) against the frozen '
            'inventory/dok-workflow/dok_wave_plan.json. No source file modified.'
        ),
        'verified_totals': {
            'exact': mq_totals.get('exact', 0),
            'derived': mq_totals.get('derived', 0),
            'none': mq_totals.get('none', 0),
            'total': sum(mq_totals.values()),
        },
        'dok_status_totals': dict(dok_status_totals),
        'base_dok_status_totals': dict(base_dok_status_totals),
        'review_state_totals': dict(review_state_totals),
        'per_lesson_match_quality': per_lesson,
        'frozen_plan_row_cross_check': cross_check_rows_note,
        'branch_population_by_lesson': branch_population_by_lesson,
        'lesson_5_4_branch_note': (
            f"lesson 5-4 has {branch_population_by_lesson['5-4']['prefix_digit_rows']} "
            f"prefix+digit rows (id matches '5-4-savvas-q{{N}}', reaches the item_to_dok "
            f"lookup -- item_to_dok['5-4'] now carries "
            f"{len(item_to_dok.get('5-4', {}))} item numbers from the TE p.258 "
            f"item_analysis transcription, so rows whose number is present match 'exact'; "
            f"before NT9 that mapping was empty and every one of these rows read 'none') and "
            f"{branch_population_by_lesson['5-4']['nonprefix_rows']} non-prefix rows (id does "
            f"not match that pattern, short-circuits to 'none' without ever consulting "
            f"item_to_dok). All 44 of the 22 conflict-pair rows are "
            f"confirmed (by assertion, above) to be in the prefix+digit population -- their ids "
            f"are all bare '5-4-savvas-q{{N}}' strings -- and each pair now has exactly one "
            f"canonically 'verified' member (RC's NT10 batch confirmation of the TE-agreeing copy)."
        ),
        'conflict_pairs_count': len(conflict_pairs),
        'conflict_pairs_cross_check': cross_check_note,
        'conflict_pairs': conflict_pairs,
        'rows': evidence_rows,
        # Triple-split identity (rc-merge-auth-5-4-2026-07-23 + NT14
        # nt14-ingest-4-1-2026-07-23, additive). This audit is an AUDIT
        # surface: it carries ALL 919 identities, alias rows AND
        # optional-catalog rows included and explicitly marked (per_row's
        # 'status'/'alias_of' and 'availability', cross-checked above
        # against the frozen plan). It never itself resolves/excludes/
        # schedules them -- STUDENT-FACING selection (qb.py) is what
        # resolves merged-alias rows to their survivor, and no consumer
        # anywhere auto-schedules optional-catalog rows.
        'identity_reconciliation': {
            'raw_registry_identities': EXPECTED_TOTAL,
            'merged_alias_identities': merged_alias_count,
            'optional_catalog_identities': optional_catalog_count,
            'active_canonical_items': active_count,
            'merged_alias_item_uids': merged_alias_item_uids,
            'optional_catalog_item_uids': optional_catalog_item_uids,
            'authorization_record_id': 'rc-merge-auth-5-4-2026-07-23',
            'optional_catalog_authorization_record_id': 'nt14-ingest-4-1-2026-07-23',
            'statement': (
                'raw_registry_identities == active_canonical_items + optional_catalog_identities + '
                'merged_alias_identities (919 == 878 + 19 + 22). Every other total in this audit '
                '(verified_totals, dok_status_totals, etc.) is registry-row-count based (all 919 '
                'rows, alias rows and optional-catalog rows included, unchanged by either the merge '
                'or this ingestion). optional_catalog_identities (lesson 4-1, '
                'nt14-ingest-4-1-2026-07-23) are, by binding course policy, never auto-scheduled, '
                'never placed in pacing, and never described as required or ready-to-teach -- '
                'distinct from merged_alias_identities (lesson 5-4), which resolve DELIBERATELY to a '
                'survivor row.'
            ),
        },
    }

    tmp_path = OUT_JSON + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, OUT_JSON)

    print('=== PROVENANCE AUDIT SUMMARY ===')
    print('match_quality totals:', output['verified_totals'])
    print('base dok_status totals (registry-derived invariant):', dict(base_dok_status_totals))
    print('canonical dok_status totals (overlay applied):', dict(dok_status_totals))
    print('review_state totals (canonical projection):', dict(review_state_totals))
    print('frozen dok_wave_plan.json row cross-check:', cross_check_rows_note)
    print('per-lesson match_quality:')
    for les in G.LESSON_CURRICULUM_ORDER:
        pl = per_lesson[les]
        bp = branch_population_by_lesson[les]
        print(f"  {les:5s} exact={pl['exact']:3d} derived={pl['derived']:2d} none={pl['none']:3d} "
              f"total={pl['total']:3d}  item_analysis={pl['item_analysis_state']:11s} "
              f"branches[prefix_digit={bp['prefix_digit_rows']:3d} nonprefix={bp['nonprefix_rows']:3d}]")
    print('conflict pairs found:', len(conflict_pairs), '--', cross_check_note)
    print(
        f'triple-split identity (rc-merge-auth-5-4-2026-07-23 + nt14-ingest-4-1-2026-07-23): '
        f'raw={EXPECTED_TOTAL} active={active_count} optional_catalog={optional_catalog_count} '
        f'merged_alias={merged_alias_count} '
        f'(reconciles: {active_count} + {optional_catalog_count} + {merged_alias_count} == {EXPECTED_TOTAL})'
    )
    print('ALL ASSERTIONS PASSED')
    print('Wrote:', OUT_JSON)


if __name__ == '__main__':
    main()
