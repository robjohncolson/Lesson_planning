"""Generate the DOK verification wave plan (WS4).

READ-ONLY analysis. Reads questionbank/registry.jsonl,
questionbank/calibration/*.json, and inventory/dedup/item_uid_alias_map.json,
all opened in 'r' mode only. This script NEVER writes to, mutates, or
truncates any of them. It writes exactly one file: dok_wave_plan.json, in
this same directory (inventory/dok-workflow/).

--------------------------------------------------------------------------
IDENTITY KEY (mirrors inventory/course-map/build_course_map.py's NODE
IDENTITY convention verbatim):
--------------------------------------------------------------------------
`registry.jsonl` has 900 rows but only 815 UNIQUE `id` strings -- 85 legacy
ids are each shared by 2 rows with DIFFERING dok/role/wave content (170
rows total). Example: `5-4-savvas-q41` is both registry line 299 (dok=2,
role=None) and registry line 328 (dok=3, role=dok3-driver) -- two distinct
rows, one legacy id. Keying wave-plan items (or the downstream review log,
progress accounting, and qb_promote.py promotion step) by `id` would
silently conflate those 85 pairs: a single review/promotion for
`5-4-savvas-q41` would incorrectly credit BOTH rows at their different
dok/wave.

Every emitted item is therefore keyed PRIMARILY by the opaque `item_uid`
from `inventory/dedup/item_uid_alias_map.json` (one per registry row/line,
always unique: 900 distinct uids for 900 rows), joined by 1-based registry
line number exactly as build_course_map.py does it
(`line2uid[registry_line]`). The legacy `id` field is kept on each item for
DISPLAY ONLY -- it is never unique enough to use alone as a join/match key.
See DOK_VERIFICATION_WORKFLOW.md's "Identity key" note and
REVIEW_INTERFACE_SPEC.md's Data model section for how this propagates to
review_log.jsonl and qb_promote.py.

What it computes, per registry row:
  - dok_status:   verified / known_auto / calibrated / unreviewed.
                  BASE dok_status (known_auto / calibrated / unreviewed) is a
                  pure function of the registry row (plus its lesson's
                  calibration file) -- see compute_dok_status()'s precedence
                  below. 'verified' is NOT part of that base precedence any
                  more: it is an OVERLAY applied afterward from the canonical
                  review-log projection (see "Canonical verification
                  projection" below). registry 'reviewed_by' / 'reviewed_at'
                  fields are application-time metadata that a future,
                  deliberate promotion step (qb_promote.py, sketched in
                  REVIEW_INTERFACE_SPEC.md) may someday write onto a row --
                  they are NEVER read by this generator and are NEVER
                  verification authority for any consumer. The base
                  precedence:
                    1. known_auto if 'Auto-assigned DOK' appears in
                       row['dok_rationale'].
                    2. calibrated if the row's lesson has REAL calibration
                       anchors (non-empty dok2_anchors or dok3_anchors in
                       its calibration file -- only 3-5 qualifies today) AND
                       the row was not auto-assigned.
                       NOTE: 'calibrated' is a LESSON-LEVEL provenance
                       status (the lesson's calibration file has real
                       anchors) -- it is never earned by a single row being
                       reviewed. The per-row review intermediate is tracked
                       via the canonical projection's 'review_state' field
                       (unreviewed / invalid-entry / reviewed_once /
                       verified -- tools/dok-review/dok_review.py's
                       TOOL_STATES), not by this base precedence. See
                       DOK_VERIFICATION_WORKFLOW.md's state machine.
                    3. unreviewed otherwise.

  Canonical verification projection: this generator no longer computes
  'verified' itself. It imports tools/dok-review/dok_review.py (the ONE
  canonical implementation of the review-log projection -- see that
  module's docstring for the full two-tier REVIEWED/VERIFIED model) and, for
  each item_uid, calls dok_review.tool_state_for(uid, latest, approved) to
  get a 'review_state' in dok_review.TOOL_STATES. The emitted dok_status is
  'verified' iff review_state == 'verified'; otherwise it falls back to the
  base precedence above. 'review_state' itself is ALSO emitted verbatim as
  an additive per-item field (immediately after 'dok_status') so a consumer
  can see 'invalid-entry' / 'reviewed_once' distinctions that the
  four-value dok_status vocabulary deliberately does not surface.
  DESIGN CALL: the dok_status vocabulary stays exactly
  {known_auto, unreviewed, calibrated, verified} -- it is NOT widened to
  carry 'invalid-entry' or 'reviewed_once'; those only ever appear in
  review_state. In particular, an item whose latest review-log entry is a
  well-formed 'needs-source-check' shows review_state == 'reviewed_once'
  (NOT a separate 'nsc-pending' value) -- dok_review.entry_is_verified's
  prior_unresolved_nsc veto permanently blocks it from ever becoming
  'verified' until a LATER entry explicitly attests
  resolves_source_check=true with provenance that re-resolves on disk (see
  dok_review.py's _chain_pending_nsc_states docstring).

  Fail-closed inputs: the review log (tools/dok-review/review_log.jsonl by
  default) is read via dok_review.read_log_entries(), wrapped here in a
  try/except -- a malformed log (JSONDecodeError / OSError /
  UnicodeDecodeError) prints one WARNING to stderr and is treated as EMPTY
  ([]), never falling back to any registry field. The rubric-approvals
  manifest (tools/dok-review/rubric_approvals.json by default) is read via
  dok_review.load_rubric_approvals(), which already fail-closes internally
  (missing -> {}, malformed -> {} with its own warning). Empty entries or
  empty approvals both mean zero verified items -- there is no scenario in
  which a missing/malformed input yields a nonzero verified count.
  - te_bucket / match_quality: cross-check against the lesson's TE
    item_analysis (Savvas item-number -> DOK bucket), three-way:
      exact   -- id is exactly '{lesson}-savvas-q{N}' and N is in a TE
                 bucket for that lesson. Direct, high-confidence signal.
      derived -- id is '{lesson}-savvas-q{N}<suffix>' (a sub-part, e.g.
                 '-partc-design') and N is in a TE bucket. The base item's
                 bucket is only a weak hint for the sub-part.
      none    -- id has no '{lesson}-savvas-q{N}' prefix, or N is not in
                 any analyzed TE bucket. No direct TE signal.
  - wave:            0-4, via the wave-order algorithm below.
  - assessment_linked: True iff lesson in {4-3, 4-5, 6-4} (the three
    lessons that feed downstream LEHS / topic assessments).

Merged-alias overlay (rc-merge-auth-5-4-2026-07-23, additive, dual-
denominator identity): 22 of the 900 registry rows (lesson 5-4, registry
lines 279-297/299/302/303) now carry four v2 tombstone marker fields --
status=="merged-alias", alias_of, merged_at, merge_authorization -- written
by a Fable-authorized merge that resolved 22 of the 85 ambiguous-legacy-id
pairs (the other 63 stay unresolved). This generator carries those markers
onto the corresponding plan item VERBATIM, as an ADDITIVE 'status' /
'alias_of' pair on every item (DESIGN CALL, documented here so it stays
consistent: every non-alias row gets the explicit default status=='active',
alias_of==None -- never simply an absent field, so a consumer can always
switch on item['status'] without a KeyError). This NEVER changes dok/role/
wave/lesson/dok_status/review_state for any row (the merge only added the
four marker fields to the registry; it touched no dok/role content), so
every existing EXPECTED_* assertion below is unaffected by it -- proven by
the assertions themselves still passing unmodified.
This is an AUDIT surface (per RC's dual-denominator semantics): it keeps
ALL 900 identities, alias rows included and explicitly marked, never
dropped or silently conflated with their survivor. The output's top-level
'identity_reconciliation' block additionally publishes the three counts --
raw_registry_identities (900), merged_alias_identities (22),
active_canonical_items (878) -- and asserts raw == active + merged_alias
before anything is written. STUDENT-FACING / canonical-readiness consumers
(e.g. qb.py) instead resolve each merged-alias row to its survivor (via
alias_of, deliberately -- never by legacy-id ambiguity) and report only the
878 active items; this plan is not itself a selection surface, so it never
performs that resolution -- it only carries the markers other consumers key
off of.

Wave-order algorithm (first match wins):
  Wave 0 -- lesson == '3-5'.
  Wave 1 -- lesson in ASSESSMENT_FEEDING_LESSONS and role == 'dok3-driver'.
  Wave 2 -- lesson in ASSESSMENT_FEEDING_LESSONS (all remaining rows).
  Wave 3 -- role == 'dok3-driver' (remaining, non-assessment-feeding
            lessons).
  Wave 4 -- everything else.

Intra-wave ordering (governs both which lesson bucket a row lands under
and the row order inside dok_wave_plan.json["waves"][wave][lesson]) is a
single composite sort key applied across the whole wave before grouping:
  (a) assessment_linked lessons first (0/1)
  (b) role rank: dok3-driver < launch-model-1 < launch-model-2 <
      do-now-bridge < do-now-explore < explore-practice < explore-tps <
      optional-stretch < (none/other)
  (c) dok_status risk rank: known_auto < unreviewed < calibrated < verified
      (weakest/highest-risk signal first)
  (d) lesson curriculum order (3-5, 4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3,
      6-4, 6-5)
  (e) item number ascending, parsed from id where present, else a large
      sentinel.
Grouping into the JSON's nested {wave: {lesson: [...]}} shape is a stable
bucket-by-lesson pass over this globally sorted sequence, so within any
one lesson's list the relative order is exactly (b),(c),(e) (the only
keys that still vary once wave/lesson are fixed).

This script is deterministic (stable sort throughout) and asserts its
wave counts, per-(wave,lesson) counts, dok_status totals, and TE
cross-check counts against manager-verified figures before writing
anything. If any assertion fails, it prints the mismatch and exits
nonzero WITHOUT writing dok_wave_plan.json.

Stdout is kept ASCII-safe: registry prompts/rationale contain non-ASCII
text and are never printed here, only ids, counts, and enum-like fields.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import OrderedDict, Counter

# ---------------------------------------------------------------------------
# Paths (never opened in write mode for anything under questionbank/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

REGISTRY_PATH = os.path.join(REPO_ROOT, 'questionbank', 'registry.jsonl')
CALIBRATION_DIR = os.path.join(REPO_ROOT, 'questionbank', 'calibration')
ALIAS_MAP_PATH = os.path.join(REPO_ROOT, 'inventory', 'dedup', 'item_uid_alias_map.json')
OUT_JSON = os.path.join(SCRIPT_DIR, 'dok_wave_plan.json')

# tools/dok-review is not importable as a normal package (hyphen in the
# directory name), so it is reached via an explicit sys.path insert. This is
# the ONE canonical implementation of the review-log verification predicate
# (dok_review.entry_is_verified, via tool_state_for) -- this generator never
# reimplements any part of that predicate locally. dok_review.py has no
# module-level import side effects (confirmed by reading it in full before
# this import was added), so this insert + import is safe to run at module
# import time, including when audit_match_quality.py does
# `import gen_dok_wave_plan as G`.
DOK_REVIEW_TOOL_DIR = os.path.join(REPO_ROOT, 'tools', 'dok-review')
if DOK_REVIEW_TOOL_DIR not in sys.path:
    sys.path.insert(0, DOK_REVIEW_TOOL_DIR)
import dok_review  # noqa: E402  (path insert must precede this import)

DEFAULT_REVIEW_LOG_PATH = os.path.join(DOK_REVIEW_TOOL_DIR, 'review_log.jsonl')
DEFAULT_APPROVALS_PATH = os.path.join(DOK_REVIEW_TOOL_DIR, 'rubric_approvals.json')


def repo_relative_display_path(path):
    """Return a REPO-RELATIVE, POSIX-form path for `path` (e.g.
    'tools/dok-review/review_log.jsonl') when it resolves inside
    REPO_ROOT -- no absolute user path is ever hardcoded or emitted for the
    canonical, in-repo inputs (mirrors dok_review.py's own Paths-section
    convention), and it keeps dok_wave_plan.json's hash machine-independent
    for a default run. Falls back to the plain absolute path only when
    `path` resolves OUTSIDE REPO_ROOT (e.g. a scratchpad/test fixture in a
    temp dir passed via --review-log / --approvals-manifest for
    fail-closed smoke-testing) -- a repo-relative form would be meaningless
    (or itself just as machine-specific, via '..' segments) for those.
    """
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

ASSESSMENT_FEEDING_LESSONS = ['4-3', '4-5', '6-4']
ASSESSMENT_FEEDING_SET = set(ASSESSMENT_FEEDING_LESSONS)

# Curriculum order of the 10 lessons that currently have registry rows.
LESSON_CURRICULUM_ORDER = ['3-5', '4-3', '4-4', '4-5', '5-1', '5-4', '5-5', '6-3', '6-4', '6-5']
LESSON_ORDER_INDEX = {les: i for i, les in enumerate(LESSON_CURRICULUM_ORDER)}

ROLE_RANK = {
    'dok3-driver': 0,
    'launch-model-1': 1,
    'launch-model-2': 2,
    'do-now-bridge': 3,
    'do-now-explore': 4,
    'explore-practice': 5,
    'explore-tps': 6,
    'optional-stretch': 7,
}
ROLE_RANK_OTHER = 8  # None / any role not in the table above

DOK_STATUS_RANK = {
    'known_auto': 0,
    'unreviewed': 1,
    'calibrated': 2,
    'verified': 3,
}

ITEM_NUMBER_SENTINEL = 10 ** 9

# Manager-verified expectations (this script must reproduce these exactly).
EXPECTED_WAVE_COUNTS = {0: 42, 1: 4, 2: 220, 3: 7, 4: 627}
EXPECTED_WAVE_LESSON_COUNTS = {
    (0, '3-5'): 42,
    (1, '4-3'): 2, (1, '4-5'): 1, (1, '6-4'): 1,
    (2, '4-3'): 72, (2, '4-5'): 80, (2, '6-4'): 68,
    (3, '4-4'): 1, (3, '5-1'): 1, (3, '5-4'): 1, (3, '5-5'): 1, (3, '6-3'): 1, (3, '6-5'): 2,
    (4, '4-4'): 90, (4, '5-1'): 131, (4, '5-4'): 131, (4, '5-5'): 95, (4, '6-3'): 99, (4, '6-5'): 81,
}
EXPECTED_BASE_DOK_STATUS_TOTALS = {'known_auto': 421, 'unreviewed': 437, 'calibrated': 42}
EXPECTED_LESSON_ROW_COUNTS = {
    '3-5': 42, '4-3': 74, '4-4': 91, '4-5': 81, '5-1': 132,
    '5-4': 132, '5-5': 96, '6-3': 100, '6-4': 69, '6-5': 83,
}
# NT9 calibration-evidence re-pin (2026-07-22): lesson 5-4's TE p.258
# item_analysis transcription landed in questionbank/calibration/5-4.json
# (evidence only -- no registry mutation, no decisions). 61 5-4 rows with
# ids '5-4-savvas-q15'..'q46' flipped match_quality none -> exact
# (224 -> 285). The 22 exact disagreements are exactly the copy-A rows of
# 5-4's 22 DOK-conflict pairs (registry lines 279-297: q21-q39 dok=2 vs
# TE dok1; line 299: q41 dok=2 vs TE dok3; lines 302/303: q44/q45 dok=2
# vs TE dok1). Independently recomputed from the source captures by the
# NT9 manager before this re-pin; dok_status totals unchanged (dok comes
# from the registry, not TE).
EXPECTED_EXACT_COUNT = 285
EXPECTED_EXACT_DISAGREEMENTS = 22
EXPECTED_DERIVED_DISAGREEMENT_IDS = {
    '4-3-savvas-q35-partc-design',
    '4-3-savvas-q36-partA-build',
    '4-3-savvas-q36-partC-evaluate-fairness',
}

# NT11 merge re-pin (rc-merge-auth-5-4-2026-07-23): SUB-A's registry mutation
# marked 22 of the 900 rows (lesson 5-4) status=='merged-alias'. These are a
# NEW, additive dual-denominator pin -- dok/role/wave/lesson content is
# untouched by the merge, so every OTHER EXPECTED_* pin above is unaffected
# and deliberately NOT re-pinned here.
EXPECTED_MERGED_ALIAS_ROWS = 22
EXPECTED_ACTIVE_CANONICAL_ITEMS = 878


# ---------------------------------------------------------------------------
# Loading (read-only)
# ---------------------------------------------------------------------------
def load_registry():
    rows = []
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_alias_map():
    """Read-only. Returns the parsed inventory/dedup/item_uid_alias_map.json.

    Structure: {"alias_map": {legacy_id: {"ambiguous": bool, "item_uids": [
    {"item_uid", "lesson", "source", "prompt_sha1", "registry_line",
    "exact_duplicate"}, ...]}}}. See build_course_map.py's identical read of
    this same file for the canonical join this generator mirrors.
    """
    with open(ALIAS_MAP_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_calibration():
    cal = {}
    for fname in os.listdir(CALIBRATION_DIR):
        full = os.path.join(CALIBRATION_DIR, fname)
        if not fname.endswith('.json') or not os.path.isfile(full):
            continue
        les = fname[:-5]
        with open(full, 'r', encoding='utf-8') as f:
            cal[les] = json.load(f)
    return cal


def calibration_has_real_anchors(cal_entry):
    """Mirrors build_content_readiness_inventory.py exactly: a lesson counts
    as calibrated if dok2_anchors or dok3_anchors is a non-empty list."""
    if cal_entry is None:
        return False
    d2 = cal_entry.get('dok2_anchors') or []
    d3 = cal_entry.get('dok3_anchors') or []
    return len(d2) > 0 or len(d3) > 0


def build_item_to_dok(calibration):
    """lesson -> {savvas_item_number(int): dok_bucket(int)} from item_analysis.

    A few item numbers appear under more than one example in a calibration
    file's item_analysis (e.g. 4-3 item 38 is listed under both example_1's
    dok1 bucket and example_2's dok2 bucket). Registry rows record which
    example they are anchored to (dok_rationale says "anchored to Example
    N"), and empirically that always matches the FIRST example (in
    item_analysis's own key order, i.e. example_1 before example_2, etc.)
    that claims the item. So first-assignment wins here; later repeats of
    the same item number under a different bucket are logged as a conflict
    but do not overwrite the first bucket.
    """
    out = {}
    conflicts = []
    for les, cal_entry in calibration.items():
        ia = (cal_entry or {}).get('item_analysis') or {}
        mapping = {}
        for _example_key, buckets in ia.items():
            if not isinstance(buckets, dict):
                continue
            for dok_key, numbers in buckets.items():
                m = re.match(r'^dok(\d+)$', dok_key)
                if not m:
                    continue
                dok_bucket = int(m.group(1))
                for num in numbers or []:
                    if num in mapping:
                        if mapping[num] != dok_bucket:
                            conflicts.append((les, num, mapping[num], dok_bucket))
                        continue  # keep first-assigned bucket
                    mapping[num] = dok_bucket
        out[les] = mapping
    if conflicts:
        print('NOTE: item_analysis has the same item number in >1 DOK bucket (first occurrence kept):')
        for les, num, old, new in conflicts:
            print(f'  lesson={les} item={num} kept_bucket=dok{old} ignored_later_bucket=dok{new}')
    return out


# ---------------------------------------------------------------------------
# Per-row computation
# ---------------------------------------------------------------------------
def compute_dok_status(row, calibrated_lessons):
    """BASE dok_status, purely registry-derived: known_auto / calibrated /
    unreviewed. 'verified' is NOT computed here -- it is applied afterward
    by main() as an overlay, sourced ONLY from the canonical review-log
    projection (dok_review.tool_state_for() == 'verified'; see module
    docstring's "Canonical verification projection" section). The registry's
    own 'reviewed_by' / 'reviewed_at' fields are application-time metadata --
    written only by a future, deliberate promotion step (qb_promote.py,
    sketched in REVIEW_INTERFACE_SPEC.md, not built) -- and are NEVER read
    here and NEVER verification authority for any consumer of this
    function's output, including inventory/provenance-audit/audit_match_quality.py
    which calls this function directly.

    RESOLVED (NT7-R Stage R2): inventory/build_content_readiness_inventory.py
    no longer keys its own 'verified' off registry 'reviewed_by' at all --
    it now derives 'verified' via this SAME canonical review-log projection
    (dok_review.entry_is_verified via tool_state_for), computed
    INDEPENDENTLY from (registry, alias map, review log, approvals
    manifest) rather than by reading this generator's own output, so the
    two builders' agreement is a real cross-check, not a copy. Registry
    reviewed_by/reviewed_at are demoted to application-time metadata
    repo-wide, not just here.

    NAMED FUTURE STEP (out of this workstream's scope):
    inventory/provenance-audit/audit_match_quality.py still calls THIS
    function directly for its own row-by-row cross-check against the
    frozen wave plan's dok_status field -- since this function never
    returns 'verified', that cross-check will start flagging a mismatch
    once a real review promotes items to 'verified' in the wave plan;
    updating that script is a future pass, not addressed here.
    """
    rationale = row.get('dok_rationale') or ''
    if 'Auto-assigned DOK' in rationale:
        return 'known_auto'
    if row.get('lesson') in calibrated_lessons:
        return 'calibrated'
    return 'unreviewed'


GENERIC_Q_RE = re.compile(r'q(\d+)')


def compute_te_match(row, item_to_dok):
    """Returns (item_number_for_sort, te_bucket_list_or_None, match_quality)."""
    lesson = row.get('lesson')
    rid = row.get('id') or ''
    exact_prefix = f'{lesson}-savvas-q'

    if rid.startswith(exact_prefix):
        rest = rid[len(exact_prefix):]
        m = re.match(r'^(\d+)(.*)$', rest)
        if m:
            item_number = int(m.group(1))
            suffix = m.group(2)
            te = item_to_dok.get(lesson, {}).get(item_number)
            if te is None:
                return item_number, None, 'none'
            if suffix == '':
                return item_number, [te], 'exact'
            return item_number, [te], 'derived'

    # Doesn't match the lesson-savvas-q{N} convention at all -> no TE signal.
    # Still try a generic q-number parse for sort-key purposes only (e).
    gm = GENERIC_Q_RE.search(rid)
    item_number = int(gm.group(1)) if gm else ITEM_NUMBER_SENTINEL
    return item_number, None, 'none'


def sort_key(item):
    assessment_rank = 0 if item['assessment_linked'] else 1
    role_rank = ROLE_RANK.get(item['role'], ROLE_RANK_OTHER)
    dok_status_rank = DOK_STATUS_RANK[item['dok_status']]
    lesson_rank = LESSON_ORDER_INDEX[item['lesson']]
    item_number = item['_item_number']
    return (assessment_rank, role_rank, dok_status_rank, lesson_rank, item_number)


def compute_wave(row):
    lesson = row.get('lesson')
    role = row.get('role')
    if lesson == '3-5':
        return 0
    if lesson in ASSESSMENT_FEEDING_SET and role == 'dok3-driver':
        return 1
    if lesson in ASSESSMENT_FEEDING_SET:
        return 2
    if role == 'dok3-driver':
        return 3
    return 4


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description=(
            'Generate the DOK verification wave plan. Registry/calibration/'
            'alias-map inputs are always read from their canonical repo '
            'locations; only the review-log and approvals-manifest inputs '
            '(and the output path) are overridable, for smoke-testing the '
            'fail-closed canonical verification projection without touching '
            'the real tools/dok-review/ files.'
        )
    )
    parser.add_argument(
        '--review-log', default=DEFAULT_REVIEW_LOG_PATH,
        help=(
            'Path to the review log consumed by the canonical verification '
            'projection (default: tools/dok-review/review_log.jsonl). A '
            'missing file means "no reviews yet" (dok_review.read_log_entries '
            'returns [] without creating it). A malformed file is caught here '
            'and treated as empty -- fail-closed, never a fallback to any '
            'registry field.'
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
        '--out', default=OUT_JSON,
        help='Output path for the generated wave plan JSON (default: the '
             'canonical inventory/dok-workflow/dok_wave_plan.json).',
    )
    cli_args = parser.parse_args()
    review_log_path = cli_args.review_log
    approvals_manifest_path = cli_args.approvals_manifest
    out_path = cli_args.out

    rows = load_registry()
    calibration = load_calibration()
    alias = load_alias_map()
    calibrated_lessons = {les for les, cal in calibration.items() if calibration_has_real_anchors(cal)}
    item_to_dok = build_item_to_dok(calibration)

    # ---- identity: registry_line (1-based, contiguous) -> item_uid --------
    # Mirrors inventory/course-map/build_course_map.py's join exactly: every
    # legacy id's item_uids entries are keyed by their own 1-based
    # registry_line, so two rows sharing a legacy id (the 85 ambiguous ids)
    # land at two different lines and therefore get two different item_uids.
    line2uid = {}
    for _legacy_id, entry in alias['alias_map'].items():
        for u in entry['item_uids']:
            line2uid[u['registry_line']] = u['item_uid']

    items = []
    base_dok_status_totals = Counter()
    lesson_row_counts = Counter()
    match_quality_totals = Counter()
    merge_status_totals = Counter()
    exact_disagreements = []
    derived_disagreements = []

    for line_no, row in enumerate(rows, start=1):
        lesson = row.get('lesson')
        role = row.get('role')
        dok = row.get('dok')
        rid = row.get('id')
        item_uid = line2uid.get(line_no)

        base_dok_status = compute_dok_status(row, calibrated_lessons)
        item_number, te_bucket, match_quality = compute_te_match(row, item_to_dok)
        assessment_linked = lesson in ASSESSMENT_FEEDING_SET
        wave = compute_wave(row)

        # Merged-alias overlay (rc-merge-auth-5-4-2026-07-23): carried
        # VERBATIM from the registry row, never re-derived. Every row gets an
        # explicit status -- 'merged-alias' for the 22 tombstone rows,
        # 'active' (the DESIGN CALL default, documented in the module
        # docstring) for all 878 others -- so no item ever has a
        # missing/None status a consumer must special-case.
        merge_status = row.get('status') if row.get('status') == 'merged-alias' else 'active'
        alias_of = row.get('alias_of') if merge_status == 'merged-alias' else None

        base_dok_status_totals[base_dok_status] += 1
        lesson_row_counts[lesson] += 1
        match_quality_totals[match_quality] += 1
        merge_status_totals[merge_status] += 1

        if te_bucket is not None and dok is not None and dok != te_bucket[0]:
            if match_quality == 'exact':
                exact_disagreements.append(rid)
            elif match_quality == 'derived':
                derived_disagreements.append(rid)

        items.append({
            'item_uid': item_uid,
            'registry_line': line_no,
            'id': rid,
            'lesson': lesson,
            'dok': dok,
            'role': role,
            'dok_status': base_dok_status,
            'assessment_linked': assessment_linked,
            'te_bucket': te_bucket,
            'match_quality': match_quality,
            'wave': wave,
            'status': merge_status,
            'alias_of': alias_of,
            '_item_number': item_number,
        })

    # ------------------------------------------------------------------
    # Canonical verification projection (overlay on top of base dok_status).
    # Uses ONLY tools/dok-review/dok_review.py's own functions -- no local
    # reimplementation of any predicate. Fail-closed: a malformed review log
    # is caught here and treated as empty (zero verified, never a fallback
    # to a registry field); a missing/malformed approvals manifest is
    # already fail-closed inside dok_review.load_rubric_approvals().
    # ------------------------------------------------------------------
    try:
        review_log_entries = dok_review.read_log_entries(review_log_path)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        print(
            f'WARNING: could not read review log at {review_log_path} ({exc}) '
            '-- treating as NO entries (fail-closed: zero verified)',
            file=sys.stderr,
        )
        review_log_entries = []

    approved_rubric_versions = dok_review.load_rubric_approvals(approvals_manifest_path)
    latest_by_uid = dok_review.latest_entries_by_uid(review_log_entries)

    for it in items:
        review_state = dok_review.tool_state_for(
            it['item_uid'],
            latest_by_uid,
            _approved_versions_override=approved_rubric_versions,
        )
        it['review_state'] = review_state
        if review_state == 'verified':
            it['dok_status'] = 'verified'
        # else: it['dok_status'] stays at its base value (known_auto /
        # calibrated / unreviewed) computed above -- 'verified' is never
        # widened onto review_state values other than 'verified' itself.

    dok_status_totals = Counter(it['dok_status'] for it in items)
    review_state_totals = Counter(it['review_state'] for it in items)

    # ------------------------------------------------------------------
    # Validate before writing anything.
    # ------------------------------------------------------------------
    errors = []

    if len(items) != 900:
        errors.append(f'expected 900 registry rows, got {len(items)}')

    for les, expected_n in EXPECTED_LESSON_ROW_COUNTS.items():
        got = lesson_row_counts.get(les, 0)
        if got != expected_n:
            errors.append(f'lesson {les} row count: expected {expected_n}, got {got}')
    other_lessons = set(lesson_row_counts) - set(EXPECTED_LESSON_ROW_COUNTS)
    if other_lessons:
        errors.append(f'unexpected lessons with registry rows: {sorted(other_lessons)}')

    # BASE dok_status totals (before the verified overlay) -- invariant
    # under ANY review log / approvals manifest content, since compute_dok_status()
    # never returns 'verified' any more.
    base_dok_status_dict = dict(base_dok_status_totals)
    for k, v in EXPECTED_BASE_DOK_STATUS_TOTALS.items():
        if base_dok_status_dict.get(k, 0) != v:
            errors.append(f'base dok_status[{k}]: expected {v}, got {base_dok_status_dict.get(k, 0)}')
    unexpected_base_statuses = set(base_dok_status_dict) - set(EXPECTED_BASE_DOK_STATUS_TOTALS)
    if unexpected_base_statuses:
        errors.append(f'unexpected base dok_status values: {sorted(unexpected_base_statuses)}')

    # Fail-closed guards on the canonical projection -- always true regardless
    # of which review log / manifest was actually passed in.
    if not approved_rubric_versions and dok_status_totals.get('verified', 0) != 0:
        errors.append(
            'approvals manifest is empty (no approved rubric versions) but '
            f"verified count is {dok_status_totals.get('verified', 0)} (expected 0)"
        )
    if not review_log_entries:
        if dok_status_totals.get('verified', 0) != 0:
            errors.append(
                'review log has no entries but verified count is '
                f"{dok_status_totals.get('verified', 0)} (expected 0)"
            )
        non_unreviewed = [it['item_uid'] for it in items if it['review_state'] != 'unreviewed']
        if non_unreviewed:
            errors.append(
                f'review log has no entries but {len(non_unreviewed)} item(s) have a '
                f'review_state other than "unreviewed": {non_unreviewed[:10]} (showing up to 10)'
            )

    # Structural coherence between dok_status and review_state, and the
    # displayed dok_status totals must still account for all 900 rows.
    bad_review_states = [it['item_uid'] for it in items if it['review_state'] not in dok_review.TOOL_STATES]
    if bad_review_states:
        errors.append(
            f'{len(bad_review_states)} item(s) have a review_state outside '
            f'dok_review.TOOL_STATES: {bad_review_states[:10]} (showing up to 10)'
        )
    verified_by_status = {it['item_uid'] for it in items if it['dok_status'] == 'verified'}
    verified_by_review_state = {it['item_uid'] for it in items if it['review_state'] == 'verified'}
    if verified_by_status != verified_by_review_state:
        errors.append(
            "the set of items with dok_status=='verified' does not equal the set "
            "with review_state=='verified' "
            f'(dok_status-only: {sorted(verified_by_status - verified_by_review_state)[:5]}, '
            f'review_state-only: {sorted(verified_by_review_state - verified_by_status)[:5]})'
        )
    if sum(dok_status_totals.values()) != 900:
        errors.append(f'displayed dok_status totals do not sum to 900: got {sum(dok_status_totals.values())}')

    wave_counts = Counter(it['wave'] for it in items)
    for w, expected_n in EXPECTED_WAVE_COUNTS.items():
        if wave_counts.get(w, 0) != expected_n:
            errors.append(f'wave {w} count: expected {expected_n}, got {wave_counts.get(w, 0)}')
    if sum(wave_counts.values()) != 900:
        errors.append(f'wave counts do not sum to 900: got {sum(wave_counts.values())}')

    wave_lesson_counts = Counter((it['wave'], it['lesson']) for it in items)
    for key, expected_n in EXPECTED_WAVE_LESSON_COUNTS.items():
        got = wave_lesson_counts.get(key, 0)
        if got != expected_n:
            errors.append(f'wave/lesson {key}: expected {expected_n}, got {got}')
    # Any (wave, lesson) combination present that ISN'T in the expected table is also a bug.
    unexpected_combos = set(wave_lesson_counts) - set(EXPECTED_WAVE_LESSON_COUNTS)
    if unexpected_combos:
        errors.append(f'unexpected (wave, lesson) combinations found: {sorted(unexpected_combos)}')

    if match_quality_totals.get('exact', 0) != EXPECTED_EXACT_COUNT:
        errors.append(f"match_quality 'exact' count: expected {EXPECTED_EXACT_COUNT}, got {match_quality_totals.get('exact', 0)}")
    if len(exact_disagreements) != EXPECTED_EXACT_DISAGREEMENTS:
        errors.append(f'exact disagreements: expected {EXPECTED_EXACT_DISAGREEMENTS}, got {len(exact_disagreements)} -> {exact_disagreements}')
    if set(derived_disagreements) != EXPECTED_DERIVED_DISAGREEMENT_IDS:
        errors.append(f'derived disagreements mismatch: got {sorted(derived_disagreements)}, expected {sorted(EXPECTED_DERIVED_DISAGREEMENT_IDS)}')

    # ------------------------------------------------------------------
    # item_uid identity validation (WS4 identity-keying fix). Hard-fails
    # (no write) if the item_uid join is not exactly 1:1 with the 900
    # registry lines -- this is what disambiguates the 85 ids shared by
    # 170 rows (e.g. 5-4-savvas-q41 at lines 299 and 328).
    # ------------------------------------------------------------------
    item_uids_present = [it['item_uid'] for it in items if it['item_uid'] is not None]
    if len(item_uids_present) != 900:
        errors.append(f'expected 900 items carrying a non-null item_uid, got {len(item_uids_present)}')
    distinct_item_uids = set(item_uids_present)
    if len(distinct_item_uids) != 900:
        errors.append(f'expected 900 distinct item_uids, got {len(distinct_item_uids)}')

    uid_mismatches = [
        (it['registry_line'], it['item_uid'], line2uid.get(it['registry_line']))
        for it in items
        if it['item_uid'] != line2uid.get(it['registry_line'])
    ]
    if uid_mismatches:
        errors.append(
            f'item_uid does not match line2uid[registry_line] for {len(uid_mismatches)} item(s): '
            f'{uid_mismatches[:10]} (showing up to 10)'
        )

    line_occurrences = Counter(it['registry_line'] for it in items)
    bad_lines = [n for n in range(1, 901) if line_occurrences.get(n, 0) != 1]
    if bad_lines:
        errors.append(
            f'{len(bad_lines)} registry line(s) not present exactly once across emitted items: '
            f'{bad_lines[:10]} (showing up to 10)'
        )

    # ------------------------------------------------------------------
    # Merged-alias / dual-denominator validation (rc-merge-auth-5-4-2026-07-23).
    # Registry-derived, so this is invariant while the registry stays frozen --
    # same status as the other EXPECTED_* pins above.
    # ------------------------------------------------------------------
    merged_alias_count = merge_status_totals.get('merged-alias', 0)
    active_count = merge_status_totals.get('active', 0)
    unexpected_merge_statuses = set(merge_status_totals) - {'active', 'merged-alias'}
    if unexpected_merge_statuses:
        errors.append(f'unexpected item status values: {sorted(unexpected_merge_statuses)}')
    if merged_alias_count != EXPECTED_MERGED_ALIAS_ROWS:
        errors.append(
            f'merged-alias row count: expected {EXPECTED_MERGED_ALIAS_ROWS}, got {merged_alias_count}'
        )
    if active_count != EXPECTED_ACTIVE_CANONICAL_ITEMS:
        errors.append(
            f'active row count: expected {EXPECTED_ACTIVE_CANONICAL_ITEMS}, got {active_count}'
        )
    if merged_alias_count + active_count != len(items):
        errors.append(
            f'dual-denominator reconciliation failed: active ({active_count}) + '
            f'merged_alias ({merged_alias_count}) != total items ({len(items)})'
        )
    # Cross-check against inventory/dedup/item_uid_alias_map.json's OWN,
    # independently-computed merged_alias_rows count (SUB-B's file) -- this
    # generator's registry-derived count must agree with that separately
    # validated figure, not just with itself.
    alias_map_merged_alias_rows = alias.get('meta', {}).get('merged_alias_rows')
    if alias_map_merged_alias_rows != merged_alias_count:
        errors.append(
            'merged-alias row count disagrees with item_uid_alias_map.json meta.merged_alias_rows: '
            f'generator computed {merged_alias_count}, alias map meta says {alias_map_merged_alias_rows}'
        )
    bad_alias_rows = [
        it['item_uid'] for it in items
        if it['status'] == 'merged-alias' and not it['alias_of']
    ]
    if bad_alias_rows:
        errors.append(
            f'{len(bad_alias_rows)} merged-alias item(s) have a missing/empty alias_of: '
            f'{bad_alias_rows[:10]} (showing up to 10)'
        )

    if errors:
        print('=== VALIDATION FAILED -- dok_wave_plan.json NOT WRITTEN ===')
        for e in errors:
            print(' -', e)
        sys.exit(1)

    # ------------------------------------------------------------------
    # All invariants passed. Build the output structure.
    # ------------------------------------------------------------------
    items_sorted = sorted(items, key=sort_key)

    waves = OrderedDict()
    for w in (0, 1, 2, 3, 4):
        waves[str(w)] = OrderedDict()

    for it in items_sorted:
        w_key = str(it['wave'])
        les = it['lesson']
        waves[w_key].setdefault(les, [])
        waves[w_key][les].append({
            'item_uid': it['item_uid'],
            'id': it['id'],
            'registry_line': it['registry_line'],
            'dok': it['dok'],
            'role': it['role'],
            'dok_status': it['dok_status'],
            'review_state': it['review_state'],
            'assessment_linked': it['assessment_linked'],
            'te_bucket': it['te_bucket'],
            'match_quality': it['match_quality'],
            'status': it['status'],
            'alias_of': it['alias_of'],
        })

    wave_definitions = {
        '0': "Calibration / tool-validation (3-5)",
        '1': "Assessment-feeding DOK-3 spines (4-3, 4-5, 6-4 dok3-driver rows)",
        '2': "Assessment-feeding lesson bodies (remaining 4-3, 4-5, 6-4 rows)",
        '3': "Remaining DOK-3 spines (dok3-driver rows outside the assessment-feeding lessons)",
        '4': "Remaining lesson bodies (everything else)",
    }

    verification_note = {
        'review_log_path': repo_relative_display_path(review_log_path),
        'approvals_manifest_path': repo_relative_display_path(approvals_manifest_path),
        'review_log_entry_count': len(review_log_entries),
        'approved_rubric_versions': sorted(approved_rubric_versions.keys()),
        'review_state_totals': {state: review_state_totals.get(state, 0) for state in dok_review.TOOL_STATES},
        'verified_count': dok_status_totals.get('verified', 0),
        'statement': (
            "The ONLY verification predicate used anywhere in this plan is "
            "tools/dok-review/dok_review.py's entry_is_verified(), applied "
            "per item_uid via tool_state_for() over the review log's "
            "latest-entry-per-item_uid projection, gated by the rubric-"
            "approvals manifest; it is fail-closed end to end -- a missing "
            "or malformed review log or approvals manifest always yields "
            "zero verified items, never a fallback to any registry field "
            "such as reviewed_by/reviewed_at."
        ),
    }

    output = {
        'generated_by': 'gen_dok_wave_plan.py',
        'source_note': (
            'Base dok_status (known_auto/calibrated/unreviewed) is derived '
            'read-only from questionbank/registry.jsonl + '
            'questionbank/calibration/*.json + '
            'inventory/dedup/item_uid_alias_map.json; none of those are ever '
            "modified. The 'verified' overlay and the additive 'review_state' "
            'field come from the canonical, read-only verification projection '
            'in tools/dok-review/dok_review.py (imported, not reimplemented), '
            'applied to tools/dok-review/review_log.jsonl and '
            'tools/dok-review/rubric_approvals.json -- see verification_note '
            'below for exactly which paths and counts were used this run. '
            'Source unmodified.'
        ),
        'identity_note': (
            "Identity key is the opaque item_uid (900 distinct values, one per "
            "registry row/line, joined via inventory/dedup/item_uid_alias_map.json "
            "by 1-based registry line -- mirrors inventory/course-map/build_course_map.py's "
            "node_identity convention). The legacy `id` field is DISPLAY-ONLY: 85 "
            "legacy ids are each shared by 2 distinct registry rows (170 rows total), "
            "e.g. '5-4-savvas-q41' is both registry line 299 (dok=2, role=None) and "
            "registry line 328 (dok=3, role=dok3-driver) -- two different item_uids. "
            "Any review/promotion tooling built against this plan MUST key by "
            "item_uid, never by id alone. See DOK_VERIFICATION_WORKFLOW.md's "
            "Identity key note and REVIEW_INTERFACE_SPEC.md's Data model section."
        ),
        'assessment_feeding_lessons': ASSESSMENT_FEEDING_LESSONS,
        'wave_definitions': wave_definitions,
        'wave_counts': {str(w): wave_counts.get(w, 0) for w in (0, 1, 2, 3, 4)},
        'verification_note': verification_note,
        'identity_reconciliation': {
            'raw_registry_identities': len(items),
            'merged_alias_identities': merged_alias_count,
            'active_canonical_items': active_count,
            'authorization_record_id': 'rc-merge-auth-5-4-2026-07-23',
            'statement': (
                "This plan is an AUDIT surface: it carries ALL "
                "raw_registry_identities (900), with the "
                "merged_alias_identities (22, rc-merge-auth-5-4-2026-07-23) "
                "explicitly marked on their item via status=='merged-alias' "
                "+ alias_of (verbatim from the registry row) -- never "
                "dropped, never silently conflated with their survivor. "
                "STUDENT-FACING / canonical-readiness surfaces (e.g. qb.py, "
                "the base content-readiness inventory, the dashboard, the "
                "decision console) instead report active_canonical_items "
                "(878): every merged-alias row resolved DELIBERATELY to its "
                "survivor (via alias_of or the dedup map's resolved_alias), "
                "never selected or counted itself. Reconciliation is exact "
                "and asserted before this file is written: "
                "raw_registry_identities == active_canonical_items + "
                "merged_alias_identities (900 == 878 + 22)."
            ),
        },
        'waves': waves,
    }

    tmp_path = out_path + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, out_path)

    # ------------------------------------------------------------------
    # Summary (ASCII-safe; never prints prompt/rationale text).
    # ------------------------------------------------------------------
    print('=== DOK WAVE PLAN SUMMARY ===')
    print('total registry rows:', len(items))
    print('base dok_status totals:', dict(base_dok_status_totals))
    print('dok_status totals (after verified overlay):', dict(dok_status_totals))
    print('review_state totals:', dict(review_state_totals))
    print('review_log_path:', review_log_path, '| entries:', len(review_log_entries))
    print('approvals_manifest_path:', approvals_manifest_path, '| approved versions:', sorted(approved_rubric_versions.keys()))
    print('verified count:', dok_status_totals.get('verified', 0))
    print('wave counts:', {w: wave_counts.get(w, 0) for w in (0, 1, 2, 3, 4)})
    print()
    print('per (wave, lesson) counts:')
    for w in (0, 1, 2, 3, 4):
        lessons_in_wave = sorted(
            [les for (ww, les) in wave_lesson_counts if ww == w],
            key=lambda les: LESSON_ORDER_INDEX[les],
        )
        parts = [f'{les}={wave_lesson_counts[(w, les)]}' for les in lessons_in_wave]
        print(f'  wave {w}: ' + ', '.join(parts))
    print()
    print('match_quality totals:', dict(match_quality_totals))
    print('exact disagreements:', len(exact_disagreements))
    print('derived disagreements:', sorted(derived_disagreements))
    print()
    print(f'item_uid identity: {len(distinct_item_uids)} distinct uids, all 900 registry lines covered exactly once')
    print()
    print(
        f'dual-denominator identity (rc-merge-auth-5-4-2026-07-23): '
        f'raw_registry_identities={len(items)} merged_alias_identities={merged_alias_count} '
        f'active_canonical_items={active_count} '
        f'(reconciles: {active_count} + {merged_alias_count} == {len(items)})'
    )
    print()
    print('ALL ASSERTIONS PASSED')
    print('Wrote:', out_path)


if __name__ == '__main__':
    main()
