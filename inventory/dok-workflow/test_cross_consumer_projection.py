"""NT7 Stage 3 -- cross-consumer identity proof.

This suite proves that every consumer of the DOK verification workflow
agrees, PER item_uid, on the same review state -- there is exactly ONE
canonical predicate (tools/dok-review/dok_review.py's `entry_is_verified`,
reached via `tool_state_for`), and every downstream projection of it
(the generator's emitted artifact, the dashboard's reader, and the
review-tool's own console-facing rows) must reproduce it byte-for-byte,
never re-derive or approximate it.

The four projections compared, per item_uid, everywhere below:

  (a) TOOL API           -- dok_review.tool_state_for(uid, latest_by_uid,
                             _approved_versions_override=...) called directly.
  (b) GENERATOR ARTIFACT -- the emitted wave-plan JSON's own
                             item['review_state'] field (written by
                             inventory/dok-workflow/gen_dok_wave_plan.py,
                             which imports and calls the SAME tool_state_for).
  (c) DASHBOARD          -- inventory/dashboard/build_content_readiness.py's
                             wave_plan_item_review_state(item) helper, a
                             fail-closed READ of the generator artifact's
                             'review_state' field (never a re-derivation).
  (d) REPORT/CONSOLE     -- dok_review.get_queue_rows(plan, log,
                             _approved_versions_override=...)'s per-row
                             'tool_state' (what `dok_review.py queue` and the
                             HTML report both print).

Two scenarios:

  SCENARIO 1 ("baseline", zero-review-log baseline; NT10 re-scoped per
  DOK_VERIFICATION_WORKFLOW.md step 3(e)) -- a BASELINE-REGENERATED wave
  plan (the REAL generator run against a review-log path that has never
  been created, since the COMMITTED plan now carries RC's 39 verified
  rows), gated by a PINNED EMPTY approvals-manifest fixture built here
  under pytest's tmp_path (NOT the real
  tools/dok-review/rubric_approvals.json -- that file now carries the
  APPROVED-STATE manifest, exactly one approval, v0.2 @
  2026-07-20T19:06:13-04:00, and is therefore no longer empty; its pin,
  REAL_APPROVALS_SHA256, is asserted only by
  test_integration_ambient_repo_state_pins). All 900 item_uids must
  read 'unreviewed' on all four projections, and the baseline plan's own
  dok_status totals must be exactly {known_auto: 421, unreviewed: 437,
  calibrated: 42} with zero 'verified' items -- this holds regardless of
  manifest content, because zero review-log entries means every item_uid's
  review_state is 'unreviewed' independent of rubric-approval state.

  SCENARIO 2 ("populated") -- a synthetic review log + a synthetic
  two-version approvals manifest, both built entirely under pytest's
  `tmp_path`, fed through the REAL generator (gen_dok_wave_plan.py, run as a
  subprocess with --review-log/--approvals-manifest/--out pointed at the
  temp fixtures) to produce a regenerated wave plan. All four projections
  must agree, per item_uid, across all 900 uids, and match this fixture
  matrix (real item_uids drawn from the committed plan; see inline comments
  at each fixture's construction for exactly why each one was chosen):

    1. unreviewed        -- (implicit) any uid with no log entry --
                             892 of the 900 uids in scenario 2.
    2. reviewed_once      -- iu_e9b11d852f4f (4-4-savvas-q1): a plain
                             rule-2-adjacent-unsourced confirm (no
                             --provenance). Never verified.
    3. reviewed_once      -- iu_9f4d494aacdd (4-4-savvas-q2): a
                             needs-source-check entry, THEN a later plain
                             confirm (no --resolves-source-check) for the
                             SAME uid. Demonstrates the chain veto: the
                             later confirm's prior_unresolved_nsc stamp
                             reads True, and it never verifies.
    4. invalid-entry      -- iu_f3b53df5eb47 (4-4-savvas-q3): ONE
                             hand-crafted raw JSONL line (never through the
                             tool) -- a 'change' missing rationale/
                             provenance/item_basis, structurally malformed
                             per entry_is_malformed.
    5. reviewed_once      -- iu_7f589eaba8ad (3-5-savvas-q30): a rule-1-
                             GRADE confirm (provenance resolves on disk
                             against the real dok3_anchors for lesson 3-5)
                             but stamped with rubric_version
                             "v-approved-future" (approved_at 2099) --
                             recorded_at (now) predates that approval, so it
                             never verifies (no retroactive verification).
    6. verified           -- iu_3b42ab3340d5 (3-5-savvas-q27): a rule-1-
                             grade confirm (provenance resolves against the
                             real dok3_anchors for lesson 3-5, Practice #27)
                             stamped "v-approved-past" (approved_at 2020,
                             already in effect). The ONLY item that verifies
                             from SYNTHETIC fixtures in this suite (NT10:
                             the REAL-DASHBOARD leg's fixture additionally
                             seeds the real 39-entry RC log, whose 39 uids
                             verify there -- see
                             dashboard_fixture_log_and_manifest).
    7. reviewed_once      -- iu_e30935a56ed6 (4-4-savvas-q4): a well-formed
                             'change' (rationale + free-text provenance +
                             item_basis "textbook-exact") whose provenance
                             does NOT resolve on disk (lesson 4-4 has zero
                             calibration anchors) -- textbook-exact requires
                             resolved provenance to verify, so this never
                             does.
    8. reviewed_once /    -- iu_3c70a19c8d36 (5-4-savvas-q41, wave 3, dok 3,
       unreviewed             role dok3-driver) gets a plain confirm;
                             iu_77d25e1e6131 (5-4-savvas-q41, wave 4, dok 2,
                             the OTHER row sharing that same legacy id) is
                             NEVER touched and must stay 'unreviewed' on all
                             four projections -- identity isolation across
                             the 85 ambiguous ids the whole item_uid scheme
                             exists to disambiguate.

HARD CONSTRAINTS, split into two mechanisms with two distinct roles (NT8
final round, per Fable's design decision):
  - TEST-CAUSED-MUTATION detection -- the autouse `_guard_repo_state`
    fixture snapshots the guarded repo files (registry, committed wave
    plan, real approvals manifest, real review log existence) BEFORE each
    test and compares the AFTER snapshot to it. before == after proves the
    test mutated nothing. It pins NO constants and asserts NOTHING about
    what the ambient content currently is, so every non-integration test
    stays hermetic w.r.t. ambient repo state (a deleted, poisoned, or
    legitimately-extended manifest cannot fail them).
  - EXTERNAL-DRIFT detection -- `test_integration_ambient_repo_state_pins`
    is the ONE test in this suite (mirroring the tool suite's
    TestRealManifestIntegrationOnly pattern) that asserts what the ambient,
    committed repo state currently IS: registry / committed-wave-plan (H1)
    / approved-state-manifest / real-review-log sha pins, the exact single
    v0.2 @ 2026-07-20T19:06:13-04:00 approval entry, and the real review
    log's pinned 39-entry NT10 state (RC batch confirmation -- the old
    review-log-ABSENCE pin is retired). Genuine drift (a future v0.3
    approval, a regenerated plan, a new real review) is EXPECTED to fail
    that one test only, prompting a deliberate re-pin.
All synthetic fixtures (review logs, approvals manifests, generator
--out output) live ONLY under pytest's `tmp_path`; no non-integration test
reads the ambient approvals manifest or review log.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths + sys.path setup. This file lives at <repo>/inventory/dok-workflow/,
# so REPO_ROOT is two levels up from its own parent directory.
# ---------------------------------------------------------------------------
WORKFLOW_DIR = Path(__file__).resolve().parent            # .../inventory/dok-workflow
REPO_ROOT = WORKFLOW_DIR.parents[1]                        # repo root
TOOL_DIR = REPO_ROOT / "tools" / "dok-review"
DASHBOARD_DIR = REPO_ROOT / "inventory" / "dashboard"

for _p in (TOOL_DIR, DASHBOARD_DIR, WORKFLOW_DIR):
    _p_str = str(_p)
    if _p_str not in sys.path:
        sys.path.insert(0, _p_str)

import dok_review  # noqa: E402  (path insert above must precede this import)
import build_content_readiness  # noqa: E402  (module-level code is import-safe: main() is __main__-guarded)

GEN_SCRIPT = WORKFLOW_DIR / "gen_dok_wave_plan.py"
COMMITTED_PLAN_PATH = WORKFLOW_DIR / "dok_wave_plan.json"
REGISTRY_PATH = REPO_ROOT / "questionbank" / "registry.jsonl"
REAL_REVIEW_LOG_PATH = TOOL_DIR / "review_log.jsonl"
REAL_APPROVALS_PATH = TOOL_DIR / "rubric_approvals.json"

# Manager-supplied, pre-verified hashes (also independently re-derived while
# building this test). INTEGRATION-BY-NATURE (NT8 final round): these pins
# assert what the CURRENT committed repo state is, so they are asserted
# ONLY by `test_integration_ambient_repo_state_pins` -- never by the
# autouse guard (which is snapshot-based and pins nothing) and never by any
# hermetic test.
# NT9 calibration-evidence re-pin (2026-07-22): COMMITTED_PLAN_SHA256 is the
# regenerated wave plan's hash after lesson 5-4's TE p.258 item_analysis was
# transcribed into questionbank/calibration/5-4.json (evidence only -- no
# registry mutation, no decisions recorded). The ONLY change from the NT8
# plan is that 61 lesson-5-4 rows flipped match_quality none -> exact with
# te_bucket populated ([1] x42, [2] x16, [3] x3); proven by reverse-
# reconstruction (reverting exactly those fields reproduces the NT8 plan
# byte-for-byte). dok_status totals (421/437/42, verified_count == 0), wave
# counts, identities, and ordering are unchanged.
# Prior pin (NT8 post-approval): 4fc6baa43251f5fd25257c840d2cea27d66eb56a450103b5b746cc2e7967671e
# Prior pin (NT9 calibration-evidence): f1dbdd19dcbf35c7f40fc2ab9e4a4336990ae7185edf1a7de82b87fda8df7266
# NT10 first-real-recording re-pin (2026-07-22): the FIRST real review-log
# entries landed -- RC's 39 lesson-5-4 rule-1 batch confirmations, recorded
# through tools/dok-review/dok_review.py under approved rubric v0.2 (per
# inventory/te-comparison-5-4/rc_batch_confirmation_proposal.json). The
# committed plan was regenerated per DOK_VERIFICATION_WORKFLOW.md step 3(a):
# verified_count 0 -> 39; the 39 rows (base bucket 'unreviewed', all lesson
# 5-4: 1 in wave 3, 38 in wave 4) now carry review_state/dok_status
# 'verified' (displayed totals 421/398/42/39); registry, identities, wave
# counts, match_quality unchanged. The real review log is now PINNED here
# too (39 entries; the zero-reviews premise is retired).
# Prior pin (NT10): 14c49acf907bb884fe0c58c33fc928230066e4b595bfdaae7126e7ff18835a3c
# NT11 named re-pin (rc-merge-auth-5-4-2026-07-23, 2026-07-23): SUB-A wrote
# the merged-alias tombstone marker fields (status/alias_of/merged_at/
# merge_authorization) onto 22 of the 900 registry rows (lesson 5-4);
# gen_dok_wave_plan.py was regenerated to carry those markers as an additive
# 'status'/'alias_of' overlay (plus a new 'identity_reconciliation' block)
# on every item. dok/role/wave/dok_status/review_state content is untouched
# (every EXPECTED_* pin in gen_dok_wave_plan.py still passed unmodified) --
# only the wave-plan and registry file hashes moved.
# NAMED re-pin (nt14-ingest-4-1-2026-07-23): the NT14 Lesson 4-1
# optional-catalog ingestion appended 19 rows (registry lines 901-919; the
# first 900 lines are byte-identical to the prior pin's content) and the
# wave plan was regenerated with a new, DISTINCT 'optional-catalog' bucket
# (19 items) -- waves '0'..'4' membership is unchanged (42/4/220/7/627),
# so the WAVE_KEYS-scoped queue universe stays exactly 900.
# NAMED re-pin #2 (nt14-ingest-4-1-2026-07-23, RC acceptance correction):
# machine-readable source_gap markers added to registry lines 909/911
# (4-1-savvas-q16 "given-illegible", q18 "answer-truncated") ONLY -- the
# first 900 lines remain byte-identical to the frozen a2fe2782... baseline
# -- and the wave plan's optional-catalog bucket carries the marker on
# those two items. uids unchanged (lesson/source/prompt untouched); the
# alias map regenerated byte-identical.
# Prior pins: 26f578b7cba22397f4015509a17dd097cfd829a2f48250ebf779237d3b9ad82c
#             262730cec82df88d5b814d7ea679b048d46eabaa84b74bd0cf21fc2456b7e23d
COMMITTED_PLAN_SHA256 = "1aca1e2d955d0da7f907097be1c2d09862a391c4e60145c8227d2b528c91cebf"
# Prior pins: b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8
#             a2fe278292e97a432a6275b807fdfe730ab67a38efd09a70e5241355959dba17
#             279d3464d7cb71f58968b02213cafa849815bd6a4ebaf13bdb7d124c471f2dc6
REGISTRY_SHA256 = "5a9dff0bacd0c7ccd168d582405f95fa5da42c50b4975bb85555eb644f90d6ad"
REAL_REVIEW_LOG_SHA256 = "4b61fd3bbaf47031c0b901e425ed2cbe1c206dba30bc745f2667d8ef48c17bf0"
REAL_REVIEW_LOG_ENTRY_COUNT = 39
# REAL_APPROVALS_SHA256 is the APPROVED-STATE manifest's hash: exactly one
# approval entry, {"version": "v0.2", "approved_at":
# "2026-07-20T19:06:13-04:00"} -- NOT an empty manifest. This file is
# immutable and never written by the tool or this suite.
REAL_APPROVALS_SHA256 = "a889b88e2ed6da2e02a360d4114bbffdd814d37636adc41943f095ba7fd66ae7"

# ---------------------------------------------------------------------------
# NT7-R Stage R4 additions: REAL downstream builders, exercised end-to-end
# via subprocess, plus an inventory MIRROR helper for the dashboard (which
# takes no CLI args at all and resolves every input relative to its own
# script's parent directory -- so retargeting it means placing files, never
# editing it).
# ---------------------------------------------------------------------------
BASE_BUILDER_SCRIPT = REPO_ROOT / "inventory" / "build_content_readiness_inventory.py"
CONSOLE_DIR = REPO_ROOT / "inventory" / "decision-console"
CONSOLE_SCRIPT = CONSOLE_DIR / "build_console.py"
REAL_INVENTORY_DIR = REPO_ROOT / "inventory"

# The REAL input files inventory/dashboard/build_content_readiness.py loads,
# relative to its own INVENTORY_DIR (= HERE.parent) -- see that script's
# INPUT_FILES dict. Mirrored verbatim (read-only copies) under a tmp_path so
# a byte-identical copy of the dashboard script, placed at
# <mirror>/inventory/dashboard/build_content_readiness.py, resolves every
# one of these paths inside the mirror instead of the real repo.
MIRROR_INPUT_RELPATHS = (
    "content_readiness_inventory.json",
    "dok-workflow/dok_wave_plan.json",
    "review-queue/collision_review_queue.json",
    "visuals/visual_asset_classification.json",
    "visuals/broken_path_repair.json",
    "topic-4-1/inventory-4-1-assets.json",
    "course-map/course_map.json",
)


def _build_inventory_mirror(root):
    """Build a temp INVENTORY MIRROR under `root` (a tmp_path, or a
    subdirectory of one): <root>/inventory/dashboard/build_content_readiness.py
    -- a literal file copy of the real (already NT7-R Stage R4-edited)
    script, never a rewritten/parameterized variant -- plus
    <root>/inventory/{content_readiness_inventory.json,
    dok-workflow/dok_wave_plan.json, review-queue/collision_review_queue.json,
    visuals/visual_asset_classification.json, visuals/broken_path_repair.json,
    topic-4-1/inventory-4-1-assets.json, course-map/course_map.json} -- read-only
    copies of the REAL inputs the dashboard script loads. The script resolves
    every input relative to its own parent directory
    (INVENTORY_DIR = HERE.parent), so this file placement alone makes it
    fully retargetable at the mirror without touching a single line of it.
    Returns the mirror's own `inventory/` Path (the directory the mirrored
    script will treat as INVENTORY_DIR)."""
    mirror_inventory = root / "inventory"
    mirror_dashboard = mirror_inventory / "dashboard"
    mirror_dashboard.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        DASHBOARD_DIR / "build_content_readiness.py",
        mirror_dashboard / "build_content_readiness.py",
    )

    for relpath in MIRROR_INPUT_RELPATHS:
        src = REAL_INVENTORY_DIR / relpath
        dst = mirror_inventory / relpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

    return mirror_inventory


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# Files the autouse guard snapshots for TEST-CAUSED-MUTATION detection.
# REAL_REVIEW_LOG_PATH is included so a test that CREATES the real review
# log is caught (None -> sha), without asserting that the ambient log must
# be absent (that current-state claim is integration-by-nature and lives in
# test_integration_ambient_repo_state_pins).
_GUARDED_REPO_FILES = (
    REGISTRY_PATH,
    COMMITTED_PLAN_PATH,
    REAL_APPROVALS_PATH,
    REAL_REVIEW_LOG_PATH,
)


def _repo_state_snapshot():
    """Hermetic-compatible snapshot of the guarded repo files:
    {path: sha256-or-None-if-missing}. Captures what is there WITHOUT
    asserting anything about what it should be -- content/existence pins
    are integration-by-nature and live ONLY in
    test_integration_ambient_repo_state_pins()."""
    return {
        str(p): (_sha256(p) if p.exists() else None)
        for p in _GUARDED_REPO_FILES
    }


@pytest.fixture(autouse=True)
def _guard_repo_state():
    """Runs around every test function in this file (autouse).
    TEST-CAUSED-MUTATION detection ONLY (NT8 final round, Fable design):
    snapshots the guarded files BEFORE the test and compares the AFTER
    snapshot TO THAT SNAPSHOT -- before == after proves the test itself
    mutated nothing (including creating the real review log). It pins no
    constants and depends in no way on what the ambient content happens to
    be, so it never breaks a hermetic test under a deleted, poisoned, or
    legitimately-extended manifest. External drift of the committed state
    is detected separately, by test_integration_ambient_repo_state_pins."""
    before = _repo_state_snapshot()
    yield
    after = _repo_state_snapshot()
    assert after == before, (
        "a test in this suite MUTATED guarded repo state (before/after "
        "snapshot mismatch) -- this suite must never write the registry, "
        "the committed wave plan, the real approvals manifest, or the real "
        f"review log.\n  before: {before}\n  after:  {after}"
    )


# ---------------------------------------------------------------------------
# INTEGRATION -- the ONE test in this suite permitted to assert what the
# AMBIENT, committed repo state currently IS (external-drift detection).
# Mirrors tools/dok-review/test_dok_review.py's TestRealManifestIntegrationOnly
# pattern. Every other test is hermetic w.r.t. the approvals manifest and
# review log (tmp_path fixtures only), guarded by the snapshot-based
# autouse fixture above (which compares before/after to each other and
# pins nothing).
# ---------------------------------------------------------------------------

def test_integration_ambient_repo_state_pins():
    """INTEGRATION test -- external-drift detection, this suite's only
    ambient-state reader. Asserts the committed repo inputs this suite was
    last reconciled against (NT10, first real recording):
      - the real review log EXISTS and is pinned byte-for-byte
        (REAL_REVIEW_LOG_SHA256, exactly REAL_REVIEW_LOG_ENTRY_COUNT == 39
        entries -- RC's 5-4 batch confirmations; the pre-NT10 zero-reviews
        premise is retired),
      - registry pinned (REGISTRY_SHA256),
      - committed wave plan pinned to H1 (COMMITTED_PLAN_SHA256),
        verified_count == 39,
      - the real approvals manifest pinned (REAL_APPROVALS_SHA256) AND
        semantically exactly one approval: v0.2 @ 2026-07-20T19:06:13-04:00,
        offset-aware.
    Genuine external drift -- a legitimate future v0.3 approval, a
    regenerated wave plan, a new real review -- is EXPECTED to fail THIS
    test and only this test: update the pins deliberately, per
    DOK_VERIFICATION_WORKFLOW.md's named-update procedure."""
    assert REAL_REVIEW_LOG_PATH.exists(), (
        f"{REAL_REVIEW_LOG_PATH} is missing -- the committed wave plan "
        "claims verified_count 39 from exactly this log (NT10); a deleted/"
        "moved real log is external drift, re-pin deliberately"
    )
    assert _sha256(REAL_REVIEW_LOG_PATH) == REAL_REVIEW_LOG_SHA256, (
        "tools/dok-review/review_log.jsonl drifted from the pinned NT10 "
        "39-entry state (RC batch confirmation, 2026-07-22) -- a new real "
        "review landed (or the log was tampered with); re-run the "
        "named-update procedure and re-pin deliberately"
    )
    real_log_entries = dok_review.read_log_entries(REAL_REVIEW_LOG_PATH)
    assert len(real_log_entries) == REAL_REVIEW_LOG_ENTRY_COUNT
    assert _sha256(REGISTRY_PATH) == REGISTRY_SHA256, (
        "questionbank/registry.jsonl drifted from the pinned baseline"
    )
    committed_plan_doc = json.loads(COMMITTED_PLAN_PATH.read_text(encoding="utf-8"))
    assert committed_plan_doc["verification_note"]["verified_count"] == 39
    assert _sha256(COMMITTED_PLAN_PATH) == COMMITTED_PLAN_SHA256, (
        "the committed inventory/dok-workflow/dok_wave_plan.json drifted "
        "from the pinned H1 baseline"
    )
    assert _sha256(REAL_APPROVALS_PATH) == REAL_APPROVALS_SHA256, (
        "the real tools/dok-review/rubric_approvals.json drifted from the "
        "pinned approved-state manifest (exactly one approval: v0.2 @ "
        "2026-07-20T19:06:13-04:00)"
    )
    raw = json.loads(REAL_APPROVALS_PATH.read_text(encoding="utf-8"))
    assert raw.get("approvals") == [
        {"version": "v0.2", "approved_at": "2026-07-20T19:06:13-04:00"}
    ]
    approved = dok_review.load_rubric_approvals(REAL_APPROVALS_PATH)
    assert set(approved.keys()) == {"v0.2"}
    assert approved["v0.2"].tzinfo is not None
    assert approved["v0.2"].utcoffset() is not None


# ---------------------------------------------------------------------------
# Scenario 1 -- "baseline" (zero review-log entries; pinned empty-manifest
# fixture -- the real manifest is no longer empty, see module docstring).
# ---------------------------------------------------------------------------

def test_scenario1_baseline_all_unreviewed_four_way_identity(tmp_path):
    """All-unreviewed baseline, re-scoped (NT10, per
    DOK_VERIFICATION_WORKFLOW.md step 3(e)): the COMMITTED plan now carries
    39 verified rows (RC's first real recording), so the all-unreviewed
    premise is proven against a BASELINE-REGENERATED plan instead -- the
    REAL generator, run as a subprocess against a review-log path that was
    NEVER created and a PINNED EMPTY approvals-manifest fixture built here
    under tmp_path (NOT the real tools/dok-review/rubric_approvals.json --
    that file carries the APPROVED-STATE v0.2 entry; and NOT the real
    review_log.jsonl -- that file now carries the 39 RC entries). Every one
    of the 900 item_uids must read 'unreviewed' on all four projections,
    and the regenerated baseline plan's own dok_status totals must match
    the manager-verified BASE figures exactly, with zero verified items --
    this holds regardless of manifest content, because with zero review-log
    entries every item_uid's review_state is 'unreviewed' independent of
    rubric approval state. The baseline plan's uid universe is anchored to
    the committed plan's (same 900 uids)."""
    absent_log = tmp_path / "absent.jsonl"
    assert not absent_log.exists()

    committed_plan = dok_review.load_plan(COMMITTED_PLAN_PATH)
    committed_uid_to_item, _uid_to_line, duplicates = dok_review.build_uid_index(committed_plan)
    assert duplicates == []
    assert len(committed_uid_to_item) == 900

    # PINNED EMPTY-MANIFEST FIXTURE: written here, under tmp_path, so it is
    # empty BY CONSTRUCTION -- this scenario no longer reads the real
    # manifest (which now carries the APPROVED v0.2 entry).
    empty_manifest_path = tmp_path / "empty_approvals.json"
    empty_manifest_path.write_text(json.dumps({"approvals": []}), encoding="utf-8")
    fixture_approved = dok_review.load_rubric_approvals(empty_manifest_path)
    assert fixture_approved == {}

    # BASELINE-REGENERATED plan (NT10 re-scope): the REAL generator against
    # the never-created log + empty manifest reproduces the all-unreviewed,
    # zero-verified baseline hermetically.
    baseline_plan_out = tmp_path / "dok_wave_plan.baseline.json"
    result = subprocess.run(
        [
            sys.executable, str(GEN_SCRIPT),
            "--review-log", str(absent_log),
            "--approvals-manifest", str(empty_manifest_path),
            "--out", str(baseline_plan_out),
        ],
        cwd=str(WORKFLOW_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"generator exited nonzero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert not absent_log.exists(), "the generator must never create the review log"

    baseline_plan = dok_review.load_plan(baseline_plan_out)
    baseline_uid_to_item, _b_uid_to_line, b_duplicates = dok_review.build_uid_index(baseline_plan)
    assert b_duplicates == []
    assert len(baseline_uid_to_item) == 900
    # Identity anchoring: same uid universe as the committed plan.
    assert set(baseline_uid_to_item) == set(committed_uid_to_item)

    latest_by_uid = dok_review.latest_entries_by_uid(dok_review.read_log_entries(absent_log))
    assert latest_by_uid == {}

    # (d) REPORT/CONSOLE-FACING projection, computed once for all 900 rows.
    queue_state_by_uid = {
        row["item_uid"]: row["tool_state"]
        for row in dok_review.get_queue_rows(baseline_plan, absent_log, _approved_versions_override=fixture_approved)
    }
    assert len(queue_state_by_uid) == 900

    dok_status_totals = Counter()
    verified_count = 0
    for uid, item in baseline_uid_to_item.items():
        # (a) TOOL API
        a_state = dok_review.tool_state_for(uid, latest_by_uid, _approved_versions_override=fixture_approved)
        # (b) GENERATOR ARTIFACT (the baseline-regenerated plan)
        b_state = item["review_state"]
        # (c) DASHBOARD
        c_state = build_content_readiness.wave_plan_item_review_state(item)
        # (d) REPORT/CONSOLE-FACING
        d_state = queue_state_by_uid[uid]

        assert a_state == b_state == c_state == d_state == "unreviewed", (
            f"uid={uid}: expected all-unreviewed baseline but got "
            f"tool_api={a_state!r} generator_artifact={b_state!r} "
            f"dashboard={c_state!r} queue_rows={d_state!r}"
        )

        dok_status_totals[item["dok_status"]] += 1
        if item["dok_status"] == "verified":
            verified_count += 1

    assert verified_count == 0
    assert dict(dok_status_totals) == {"known_auto": 421, "unreviewed": 437, "calibrated": 42}
    assert "verified" not in dok_status_totals
    assert baseline_plan["verification_note"]["verified_count"] == 0


# ---------------------------------------------------------------------------
# Scenario 2 -- "populated" fixture matrix.
# ---------------------------------------------------------------------------

# Real item_uids drawn from the committed plan (see the module docstring's
# fixture-matrix table for why each one was picked).
FIX6_UID = "iu_3b42ab3340d5"          # 3-5-savvas-q27 -- VERIFIES (only item that does)
FIX5_UID = "iu_7f589eaba8ad"          # 3-5-savvas-q30 -- pre-approval rule-1 confirm
FIX2_UID = "iu_e9b11d852f4f"          # 4-4-savvas-q1  -- plain rule-2 confirm
FIX3_UID = "iu_9f4d494aacdd"          # 4-4-savvas-q2  -- nsc-pending chain
FIX4_UID = "iu_f3b53df5eb47"          # 4-4-savvas-q3  -- hand-crafted invalid entry
FIX7_UID = "iu_e30935a56ed6"          # 4-4-savvas-q4  -- incomplete textbook-exact change
FIX8_UID = "iu_3c70a19c8d36"          # 5-4-savvas-q41, wave 3, dok 3 -- reviewed half of the pair
FIX8_SIBLING_UID = "iu_77d25e1e6131"  # 5-4-savvas-q41, wave 4, dok 2 -- MUST stay unreviewed

EXPECTED_STATES = {
    FIX6_UID: "verified",
    FIX5_UID: "reviewed_once",
    FIX2_UID: "reviewed_once",
    FIX3_UID: "reviewed_once",
    FIX4_UID: "invalid-entry",
    FIX7_UID: "reviewed_once",
    FIX8_UID: "reviewed_once",
    FIX8_SIBLING_UID: "unreviewed",
}

STRUCTURAL_FIELDS = ("registry_line", "id", "dok", "role", "te_bucket", "match_quality", "assessment_linked")


def _bucket_order(plan):
    """{(wave, lesson): [item_uid, ...]} in stored list order."""
    order = {}
    for wave, lesson, item in dok_review.iter_queue_items(plan):
        order.setdefault((wave, lesson), []).append(item["item_uid"])
    return order


def test_scenario2_populated_fixture_matrix_four_way_identity(tmp_path):
    """Build the synthetic review log + approvals manifest fixture matrix,
    run the REAL generator against them (subprocess, --out into tmp_path),
    and prove all four projections agree per item_uid across all 900 uids --
    THE cross-consumer identity proof -- plus the structural invariants that
    must hold on the regenerated plan (900 items, wave totals unchanged,
    exactly one verified item, and every field except dok_status/review_state
    identical to the committed plan per uid)."""
    tmp_log = tmp_path / "review_log.jsonl"
    tmp_manifest = tmp_path / "rubric_approvals.json"
    tmp_plan_out = tmp_path / "dok_wave_plan.generated.json"

    committed_plan = dok_review.load_plan(COMMITTED_PLAN_PATH)
    committed_uid_to_item, _uid_to_line, dup = dok_review.build_uid_index(committed_plan)
    assert dup == []

    # Sanity-check the fixture uids really are what the docstring claims --
    # if the committed plan ever changes shape, this fails loudly here
    # instead of the assertions below silently testing the wrong thing.
    assert committed_uid_to_item[FIX6_UID]["id"] == "3-5-savvas-q27"
    assert committed_uid_to_item[FIX5_UID]["id"] == "3-5-savvas-q30"
    assert committed_uid_to_item[FIX2_UID]["id"] == "4-4-savvas-q1"
    assert committed_uid_to_item[FIX3_UID]["id"] == "4-4-savvas-q2"
    assert committed_uid_to_item[FIX4_UID]["id"] == "4-4-savvas-q3"
    assert committed_uid_to_item[FIX7_UID]["id"] == "4-4-savvas-q4"
    assert committed_uid_to_item[FIX7_UID]["dok"] == 2
    assert committed_uid_to_item[FIX8_UID]["id"] == "5-4-savvas-q41"
    assert committed_uid_to_item[FIX8_UID]["wave"] == "3" and committed_uid_to_item[FIX8_UID]["dok"] == 3
    assert committed_uid_to_item[FIX8_SIBLING_UID]["id"] == "5-4-savvas-q41"
    assert committed_uid_to_item[FIX8_SIBLING_UID]["wave"] == "4" and committed_uid_to_item[FIX8_SIBLING_UID]["dok"] == 2

    # NT10 (2026-07-22): the committed plan is no longer all-unreviewed --
    # it carries RC's 39 verified lesson-5-4 rows (the first real recording,
    # pinned by test_integration_ambient_repo_state_pins). This scenario's
    # tmp plan is regenerated from a FIXTURE log that does NOT contain those
    # 39 RC entries, so committed-vs-tmp comparisons below must expect
    # exactly those uids to differ in dok_status/review_state (committed
    # 'verified', tmp base 'unreviewed') -- and nothing else.
    committed_verified_uids = {
        uid for uid, item in committed_uid_to_item.items()
        if item["dok_status"] == "verified"
    }
    assert len(committed_verified_uids) == 39
    assert all(committed_uid_to_item[u]["lesson"] == "5-4" for u in committed_verified_uids)
    assert FIX8_UID in committed_verified_uids            # RC confirmed the wave-3 q41 copy
    assert FIX8_SIBLING_UID not in committed_verified_uids  # the wave-4 copy-A stays untouched

    # ---- synthetic approvals manifest: two versions, one already in effect
    # (2020, well before any real test run) and one not yet in effect (2099).
    tmp_manifest.write_text(
        json.dumps({
            "approvals": [
                {"version": "v-approved-past", "approved_at": "2020-01-01T00:00:00+00:00"},
                {"version": "v-approved-future", "approved_at": "2099-01-01T00:00:00+00:00"},
            ]
        }),
        encoding="utf-8",
    )

    plan_arg = str(COMMITTED_PLAN_PATH)
    log_arg = str(tmp_log)

    # Fixture 6: post-approval, resolved (rule-1) confirm -- the ONLY item
    # anywhere in this suite that VERIFIES. Practice #27 is a real dok3_anchors
    # entry in questionbank/calibration/3-5.json ("Savvas Practice #27 ...").
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX6_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #27",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:00:00+00:00",
    ])

    # Fixture 2: plain rule-2-adjacent-unsourced confirm (no --provenance) --
    # well-formed, REVIEWED, never verification-grade.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX2_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:05:00+00:00",
    ])

    # Fixture 3a: needs-source-check (terminal-unresolved, rationale required).
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX3_UID, "--reviewed-by", "fixture",
        "--disposition", "needs-source-check",
        "--rationale", "Cannot confirm this item's DOK against the TE bucket without the source page.",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:10:00+00:00",
    ])
    # Fixture 3b: a LATER plain confirm for the SAME uid, with NO
    # --resolves-source-check attestation. Per the chain model this must NOT
    # clear the pending nsc -- asserted below both via tool_state (never
    # verified) and directly via the raw log entry's 'prior_unresolved_nsc'
    # stamp (the chain-veto mechanism itself). Lesson 4-4 has no calibration
    # anchors, so this confirm is rule-2-adjacent regardless -- the veto
    # assertion below is checked independently of that fact.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX3_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:15:00+00:00",
    ])

    # Fixture 5: a rule-1-GRADE confirm (provenance resolves on disk against
    # the real dok3_anchors Practice #30 entry for lesson 3-5) stamped with
    # the NOT-YET-EFFECTIVE "v-approved-future" version (approved_at 2099) --
    # recorded_at (tool-stamped "now") predates that approval, so this never
    # verifies: no retroactive verification, even though the disposition
    # itself is otherwise exactly as strong as fixture 6's.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX5_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #30",
        "--rubric-version", "v-approved-future",
        "--reviewed-at", "2026-02-01T09:20:00+00:00",
    ])

    # Fixture 7: a well-formed 'change' (rationale + free-text provenance +
    # item_basis) -- but item_basis == "textbook-exact" requires provenance
    # that RESOLVES on disk, and lesson 4-4 has zero calibration anchors, so
    # this provenance can never resolve. Never verified.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX7_UID, "--reviewed-by", "fixture",
        "--disposition", "change", "--chosen-dok", "3",
        "--rationale", "Reviewer judgment: item requires chaining multiple justified steps, not recall.",
        "--provenance", "Savvas TE p. 214 (free text -- not a calibration-anchor scheme reference)",
        "--item-basis", "textbook-exact",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:25:00+00:00",
    ])

    # Fixture 8: review ONLY iu_3c70a19c8d36 (the wave-3 dok3-driver half of
    # the 5-4-savvas-q41 ambiguous-id pair). iu_77d25e1e6131 (the wave-4 half)
    # must be completely unaffected -- identity isolation, the whole point of
    # item_uid keying over the shared legacy `id`.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX8_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:30:00+00:00",
    ])

    # Fixture 4: ONE hand-crafted raw JSONL line, appended directly to the
    # log file (NOT via the tool). A 'change' entry missing rationale/
    # provenance/item_basis is structurally malformed per entry_is_malformed
    # -- this must classify as 'invalid-entry', never 'reviewed_once'.
    with open(tmp_log, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "item_uid": FIX4_UID,
            "reviewed_by": "fixture",
            "reviewed_at": "2026-02-01T09:35:00+00:00",
            "decision": "change",
            "new_dok": 3,
            # rationale / provenance / item_basis deliberately absent.
        }) + "\n")

    # Sanity: confirm fixture 3's raw chain really did stamp
    # prior_unresolved_nsc=True on the later confirm.
    all_entries = dok_review.read_log_entries(tmp_log)
    fix3_chain = dok_review.entries_for_uid(all_entries, FIX3_UID)
    assert len(fix3_chain) == 2
    assert fix3_chain[0]["decision"] == "needs-source-check"
    assert fix3_chain[1]["decision"] == "confirm"
    assert fix3_chain[1]["prior_unresolved_nsc"] is True

    # ---- run the REAL generator against the fixtures ----
    result = subprocess.run(
        [
            sys.executable, str(GEN_SCRIPT),
            "--review-log", str(tmp_log),
            "--approvals-manifest", str(tmp_manifest),
            "--out", str(tmp_plan_out),
        ],
        cwd=str(WORKFLOW_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"generator exited nonzero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert tmp_plan_out.exists()

    tmp_plan = dok_review.load_plan(tmp_plan_out)
    tmp_uid_to_item, _tmp_uid_to_line, tmp_dup = dok_review.build_uid_index(tmp_plan)
    assert tmp_dup == []
    assert len(tmp_uid_to_item) == 900

    tmp_approved = dok_review.load_rubric_approvals(tmp_manifest)
    tmp_latest_by_uid = dok_review.latest_entries_by_uid(dok_review.read_log_entries(tmp_log))
    tmp_queue_state_by_uid = {
        row["item_uid"]: row["tool_state"]
        for row in dok_review.get_queue_rows(tmp_plan, tmp_log, _approved_versions_override=tmp_approved)
    }
    assert len(tmp_queue_state_by_uid) == 900

    # ---- THE cross-consumer identity proof: all four projections agree,
    # per item_uid, across all 900 uids, and match the fixture matrix. ----
    verified_uids = set()
    for uid in committed_uid_to_item:
        expected = EXPECTED_STATES.get(uid, "unreviewed")

        a_state = dok_review.tool_state_for(uid, tmp_latest_by_uid, _approved_versions_override=tmp_approved)
        b_state = tmp_uid_to_item[uid]["review_state"]
        c_state = build_content_readiness.wave_plan_item_review_state(tmp_uid_to_item[uid])
        d_state = tmp_queue_state_by_uid[uid]

        assert a_state == b_state == c_state == d_state == expected, (
            f"uid={uid}: tool_api={a_state!r} generator_artifact={b_state!r} "
            f"dashboard={c_state!r} queue_rows={d_state!r} expected={expected!r}"
        )
        if b_state == "verified":
            verified_uids.add(uid)

    assert verified_uids == {FIX6_UID}

    # ---- structural invariants on the regenerated plan ----
    assert tmp_plan["verification_note"]["verified_count"] == 1
    # NAMED update (nt14-ingest-4-1-2026-07-23): the regenerated plan now
    # carries the distinct optional-catalog audit bucket (19 Lesson 4-1
    # rows). Waves '0'..'4' — the required review program — are unchanged.
    assert tmp_plan["wave_counts"] == {
        "0": 42, "1": 4, "2": 220, "3": 7, "4": 627, "optional-catalog": 19,
    }

    # NAMED update (nt14-ingest-4-1-2026-07-23): summing over ALL wave keys
    # now includes the optional-catalog audit bucket -- 919 raw = 900
    # required-program items (waves '0'..'4', unchanged) + 19 optional.
    total_items = sum(len(items) for lessons in tmp_plan["waves"].values() for items in lessons.values())
    assert total_items == 919
    required_program_items = sum(
        len(items)
        for wave_key, lessons in tmp_plan["waves"].items()
        if wave_key != "optional-catalog"
        for items in lessons.values()
    )
    assert required_program_items == 900

    for uid, committed_item in committed_uid_to_item.items():
        tmp_item = tmp_uid_to_item[uid]

        for field in STRUCTURAL_FIELDS:
            assert committed_item.get(field) == tmp_item.get(field), (
                f"uid={uid} field={field!r}: committed={committed_item.get(field)!r} "
                f"tmp={tmp_item.get(field)!r}"
            )
        assert committed_item["wave"] == tmp_item["wave"], f"uid={uid}: wave differs"
        assert committed_item["lesson"] == tmp_item["lesson"], f"uid={uid}: lesson differs"

        # dok_status: identical everywhere EXCEPT (i) fixture 6's uid, which
        # flips to 'verified' in the TMP plan -- its committed BASE status
        # ('calibrated') is recoverable right here, from the committed
        # plan's own value -- and (ii) the 39 RC-verified uids (NT10), which
        # are 'verified' in the COMMITTED plan but fall back to their base
        # bucket ('unreviewed' for all 39) in the tmp plan, because this
        # scenario's fixture log does not contain the RC entries.
        if uid == FIX6_UID:
            assert committed_item["dok_status"] == "calibrated"
            assert tmp_item["dok_status"] == "verified"
        elif uid in committed_verified_uids:
            assert committed_item["dok_status"] == "verified"
            assert tmp_item["dok_status"] == "unreviewed", (
                f"uid={uid}: RC-verified uid's tmp base bucket should be "
                f"'unreviewed', got {tmp_item['dok_status']!r}"
            )
        else:
            assert committed_item["dok_status"] == tmp_item["dok_status"], (
                f"uid={uid}: dok_status changed unexpectedly "
                f"(committed={committed_item['dok_status']!r}, tmp={tmp_item['dok_status']!r})"
            )

        # review_state: identical everywhere EXCEPT the uids that actually
        # received a log entry in this scenario (the EXPECTED_STATES table)
        # and (NT10) the RC-verified uids, which read 'verified' in the
        # committed plan but 'unreviewed' in this scenario's tmp plan.
        if uid not in EXPECTED_STATES:
            if uid in committed_verified_uids:
                assert committed_item["review_state"] == "verified"
                assert tmp_item["review_state"] == "unreviewed"
            else:
                assert committed_item["review_state"] == tmp_item["review_state"] == "unreviewed"

    # ---- per-(wave,lesson) bucket membership/order: buckets containing a
    # fixture uid are checked by SET equality only (a dok_status change can
    # in principle shift sort position within its own lesson bucket); every
    # other bucket is checked by EXACT order equality. ----
    committed_buckets = _bucket_order(committed_plan)
    tmp_buckets = _bucket_order(tmp_plan)
    assert set(committed_buckets) == set(tmp_buckets)

    fixture_bucket_keys = {
        (committed_uid_to_item[uid]["wave"], committed_uid_to_item[uid]["lesson"])
        for uid in EXPECTED_STATES
    }
    for key in committed_buckets:
        if key in fixture_bucket_keys:
            assert set(committed_buckets[key]) == set(tmp_buckets[key]), f"bucket {key}: membership changed"
        else:
            assert committed_buckets[key] == tmp_buckets[key], f"bucket {key}: order changed unexpectedly"

    # ---- scenario-2 teardown (NT8 final round): this test no longer reads
    # the ambient manifest/registry/plan state inline. Test-caused mutation
    # is detected by the autouse snapshot guard (_guard_repo_state, which
    # compares before/after to each other); ambient-state pins are
    # integration-by-nature and live ONLY in
    # test_integration_ambient_repo_state_pins. ----


# ---------------------------------------------------------------------------
# Fail-closed manifest variants (tool-API level, no generator run needed).
# ---------------------------------------------------------------------------

def test_fail_closed_manifest_variants_block_retroactive_verification(tmp_path):
    """A malformed (non-JSON) approvals manifest, and an absent one, must
    both make load_rubric_approvals() fail closed to {} -- which means even
    an otherwise-verification-grade entry (the same rule-1-grade, past-
    approved-version confirm used as fixture 6 in scenario 2) can no longer
    verify. Checked against a GENUINELY approved manifest first, as a sanity
    check that the fixture entry really is verification-grade absent the
    manifest problem."""
    tmp_log = tmp_path / "review_log.jsonl"
    uid = FIX6_UID  # 3-5-savvas-q27 -- same rule-1-grade confirm as scenario 2's fixture 6

    dok_review.main([
        "--plan", str(COMMITTED_PLAN_PATH), "--log", str(tmp_log), "review",
        "--item-uid", uid, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #27",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:00:00+00:00",
    ])
    latest_by_uid = dok_review.latest_entries_by_uid(dok_review.read_log_entries(tmp_log))

    # Sanity check: a genuinely-approved manifest DOES verify this entry.
    good_manifest = tmp_path / "good_manifest.json"
    good_manifest.write_text(
        json.dumps({"approvals": [{"version": "v-approved-past", "approved_at": "2020-01-01T00:00:00+00:00"}]}),
        encoding="utf-8",
    )
    good_approved = dok_review.load_rubric_approvals(good_manifest)
    assert dok_review.tool_state_for(uid, latest_by_uid, _approved_versions_override=good_approved) == "verified"

    # MALFORMED manifest (not JSON at all) -> load_rubric_approvals fails
    # closed to {} -> the SAME entry can no longer verify.
    malformed_manifest = tmp_path / "malformed_manifest.json"
    malformed_manifest.write_text("not json", encoding="utf-8")
    malformed_approved = dok_review.load_rubric_approvals(malformed_manifest)
    assert malformed_approved == {}
    assert (
        dok_review.tool_state_for(uid, latest_by_uid, _approved_versions_override=malformed_approved)
        == "reviewed_once"
    )

    # ABSENT manifest -> same fail-closed {} result.
    absent_manifest = tmp_path / "does_not_exist_manifest.json"
    assert not absent_manifest.exists()
    absent_approved = dok_review.load_rubric_approvals(absent_manifest)
    assert absent_approved == {}
    assert (
        dok_review.tool_state_for(uid, latest_by_uid, _approved_versions_override=absent_approved)
        == "reviewed_once"
    )


# ---------------------------------------------------------------------------
# NT7-R Stage R4 -- de-tautologizing the cross-consumer proof: exercise the
# REAL downstream builders (inventory/build_content_readiness_inventory.py,
# the mirrored inventory/dashboard/build_content_readiness.py,
# inventory/decision-console/build_console.py) end-to-end via subprocess,
# rather than only calling helper functions imported in-process. Everything
# above this point (scenarios 1/2, the fail-closed manifest variants) is
# UNCHANGED.
# ---------------------------------------------------------------------------


def _write_standard_manifest(manifest_path):
    """The SAME two-version approvals manifest shape used by
    test_scenario2_populated_fixture_matrix_four_way_identity: one version
    already in effect (2020) and one not yet in effect (2099)."""
    manifest_path.write_text(
        json.dumps({
            "approvals": [
                {"version": "v-approved-past", "approved_at": "2020-01-01T00:00:00+00:00"},
                {"version": "v-approved-future", "approved_at": "2099-01-01T00:00:00+00:00"},
            ]
        }),
        encoding="utf-8",
    )


def _populate_shared_fixture_chain(log_path):
    """Append the SAME fixture matrix as
    test_scenario2_populated_fixture_matrix_four_way_identity's fixtures 2,
    3a/3b, 4, 5, 6, 7, 8 (see that test's inline comments for exactly why
    each one is shaped the way it is) to `log_path`, via the REAL tool (plus
    one hand-crafted invalid line for fixture 4). This is a standalone
    function, not shared code with that test -- that test's body must stay
    completely untouched -- so the module-scoped fixture below can build an
    equivalent log without touching it."""
    plan_arg = str(COMMITTED_PLAN_PATH)
    log_arg = str(log_path)

    # Fixture 6: post-approval, resolved (rule-1) confirm -- the ONLY item
    # that verifies.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX6_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #27",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:00:00+00:00",
    ])
    # Fixture 2: plain rule-2-adjacent-unsourced confirm.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX2_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:05:00+00:00",
    ])
    # Fixture 3a: needs-source-check.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX3_UID, "--reviewed-by", "fixture",
        "--disposition", "needs-source-check",
        "--rationale", "Cannot confirm this item's DOK against the TE bucket without the source page.",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:10:00+00:00",
    ])
    # Fixture 3b: later plain confirm, no --resolves-source-check -- chain veto.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX3_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:15:00+00:00",
    ])
    # Fixture 5: rule-1-grade confirm stamped with the NOT-YET-EFFECTIVE version.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX5_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #30",
        "--rubric-version", "v-approved-future",
        "--reviewed-at", "2026-02-01T09:20:00+00:00",
    ])
    # Fixture 7: well-formed 'change' whose provenance can never resolve (lesson 4-4).
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX7_UID, "--reviewed-by", "fixture",
        "--disposition", "change", "--chosen-dok", "3",
        "--rationale", "Reviewer judgment: item requires chaining multiple justified steps, not recall.",
        "--provenance", "Savvas TE p. 214 (free text -- not a calibration-anchor scheme reference)",
        "--item-basis", "textbook-exact",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:25:00+00:00",
    ])
    # Fixture 8: review ONLY the wave-3 half of the ambiguous 5-4-savvas-q41 pair.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX8_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:30:00+00:00",
    ])
    # Fixture 4: hand-crafted invalid entry (missing rationale/provenance/item_basis).
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "item_uid": FIX4_UID,
            "reviewed_by": "fixture",
            "reviewed_at": "2026-02-01T09:35:00+00:00",
            "decision": "change",
            "new_dok": 3,
        }) + "\n")


def _populate_dashboard_fixture_chain(log_path):
    """NT10 re-scope: the fixture matrix for the REAL-DASHBOARD leg, now
    layered ON TOP of a byte-copy of the REAL 39-entry review log (seeded by
    dashboard_fixture_log_and_manifest before this function runs). Same
    rich mix as _populate_shared_fixture_chain MINUS fixture 6 (no verified
    3-5 row -- that would demote 3-5's ws6 CALIBRATED state and trip the
    dashboard's pinned distribution) and MINUS fixture 8 (FIX8_UID,
    iu_3c70a19c8d36, is one of the 39 RC-verified uids in the seeded real
    log; appending the old rule-2 confirm on top would demote it from
    'verified' to 'reviewed_once' and break the frozen claimed=39
    reconciliation). The ambiguous-pair identity discipline FIX8 used to
    exercise is now exercised more strongly by the seed itself: FIX8_UID is
    VERIFIED while FIX8_SIBLING_UID stays 'unreviewed'. See
    dashboard_fixture_log_and_manifest's docstring for why this leg's
    overall verified count must now be exactly 39 (the frozen NT10
    baseline), no longer 0."""
    plan_arg = str(COMMITTED_PLAN_PATH)
    log_arg = str(log_path)

    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX2_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:05:00+00:00",
    ])
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX3_UID, "--reviewed-by", "fixture",
        "--disposition", "needs-source-check",
        "--rationale", "Cannot confirm this item's DOK against the TE bucket without the source page.",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:10:00+00:00",
    ])
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX3_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:15:00+00:00",
    ])
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX5_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #30",
        "--rubric-version", "v-approved-future",
        "--reviewed-at", "2026-02-01T09:20:00+00:00",
    ])
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", FIX7_UID, "--reviewed-by", "fixture",
        "--disposition", "change", "--chosen-dok", "3",
        "--rationale", "Reviewer judgment: item requires chaining multiple justified steps, not recall.",
        "--provenance", "Savvas TE p. 214 (free text -- not a calibration-anchor scheme reference)",
        "--item-basis", "textbook-exact",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:25:00+00:00",
    ])
    # (fixture 8 deliberately ABSENT here -- see this function's docstring:
    # FIX8_UID arrives already-verified via the seeded real log.)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "item_uid": FIX4_UID,
            "reviewed_by": "fixture",
            "reviewed_at": "2026-02-01T09:35:00+00:00",
            "decision": "change",
            "new_dok": 3,
        }) + "\n")


@pytest.fixture(scope="module")
def console_fixture_log_and_manifest(tmp_path_factory):
    """Module-scoped: build, ONCE per test-module run, the SAME fixture
    review-log + approvals-manifest matrix as
    test_scenario2_populated_fixture_matrix_four_way_identity (fixtures 2,
    3a/3b, 4, 5, 6, 7, 8 -- so EXPECTED_STATES describes this log's outcome
    too), under a dedicated tmp_path_factory directory. Used by the
    REAL-CONSOLE tests below, which read this SAME (log_path,
    manifest_path) READ-ONLY -- neither appends further entries to it."""
    shared_dir = tmp_path_factory.mktemp("nt7_console_fixture")
    log_path = shared_dir / "review_log.jsonl"
    manifest_path = shared_dir / "rubric_approvals.json"
    _write_standard_manifest(manifest_path)
    _populate_shared_fixture_chain(log_path)
    return log_path, manifest_path


@pytest.fixture(scope="module")
def console_fixture_wave_plan(console_fixture_log_and_manifest, tmp_path_factory):
    """Module-scoped: run the REAL generator ONCE against
    console_fixture_log_and_manifest's (log, manifest), producing the
    fixture-regenerated wave plan (carrying FIX6_UID as 'verified') reused
    (read-only) by both REAL-CONSOLE tests below."""
    log_path, manifest_path = console_fixture_log_and_manifest
    out_dir = tmp_path_factory.mktemp("nt7_console_wave_plan")
    out_path = out_dir / "dok_wave_plan.generated.json"
    result = subprocess.run(
        [
            sys.executable, str(GEN_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out", str(out_path),
        ],
        cwd=str(WORKFLOW_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"generator exited nonzero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert out_path.exists()
    return out_path


@pytest.fixture(scope="module")
def dashboard_fixture_log_and_manifest(tmp_path_factory):
    """Module-scoped: build, ONCE per test-module run, the REAL-DASHBOARD
    leg's fixture: a byte-copy of the REAL 39-entry review log (RC's NT10
    batch confirmation -- pinned ambiently by
    test_integration_ambient_repo_state_pins) with the rich fixture mix
    (FIX2/3/4/5/7 -- reviewed_once / nsc-chain / invalid-entry; NO fixture
    6, NO fixture 8, see _populate_dashboard_fixture_chain) layered on top,
    plus a manifest approving v-approved-past (2020), v0.2 (the REAL
    approval instant, 2026-07-20T19:06:13-04:00 -- required so the seeded
    RC entries verify exactly as they do ambiently), and v-approved-future
    (2099).

    WHY the fixture's overall verified count must be exactly 39 (NT10
    re-scope of the old ZERO-verified premise):
    inventory/build_content_readiness_inventory.py's
    baseline_reconciliation hard-pins `{'metric': 'verified rows',
    'claimed': 39, ...}` (the NT10 frozen baseline -- a LITERAL 39, not
    parameterized by --review-log/--approvals-manifest), and
    inventory/dashboard/build_content_readiness.py hard-pins
    `check("dok.verified", ..., 39)` / `check("dok.unreviewed", ..., 398)`.
    So the REAL base builder and REAL dashboard can only ever complete a
    real subprocess run (exit 0) against a fixture whose verified set is
    EXACTLY the ambient one (the 39 RC uids, all lesson 5-4 -- which also
    leaves the ws6 pinned distribution untouched, since no 3-5 row
    verifies). Seeding the real log gives exactly that, while the layered
    mix still exercises every OTHER review_state value end to end
    (reviewed_once, invalid-entry) through both real scripts. The
    REAL-CONSOLE leg below has no such hard-pin (its coherence guard only
    requires verified==0 when the approvals manifest itself is empty), so
    it keeps its own fixture-6-carrying log+manifest instead."""
    shared_dir = tmp_path_factory.mktemp("nt7_dashboard_fixture")
    log_path = shared_dir / "review_log.jsonl"
    manifest_path = shared_dir / "rubric_approvals.json"
    manifest_path.write_text(
        json.dumps({
            "approvals": [
                {"version": "v-approved-past", "approved_at": "2020-01-01T00:00:00+00:00"},
                {"version": "v0.2", "approved_at": "2026-07-20T19:06:13-04:00"},
                {"version": "v-approved-future", "approved_at": "2099-01-01T00:00:00+00:00"},
            ]
        }),
        encoding="utf-8",
    )
    # Seed: byte-copy of the REAL 39-entry log (verified via the ambient
    # pin; the autouse guard proves this fixture never touches the real
    # file itself).
    shutil.copy(REAL_REVIEW_LOG_PATH, log_path)
    _populate_dashboard_fixture_chain(log_path)
    return log_path, manifest_path


@pytest.fixture(scope="module")
def dashboard_fixture_wave_plan(dashboard_fixture_log_and_manifest, tmp_path_factory):
    """Module-scoped: run the REAL generator ONCE against
    dashboard_fixture_log_and_manifest's (log, manifest) -- zero verified
    items overall -- reused (read-only) by both REAL-DASHBOARD tests below."""
    log_path, manifest_path = dashboard_fixture_log_and_manifest
    out_dir = tmp_path_factory.mktemp("nt7_dashboard_wave_plan")
    out_path = out_dir / "dok_wave_plan.generated.json"
    result = subprocess.run(
        [
            sys.executable, str(GEN_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out", str(out_path),
        ],
        cwd=str(WORKFLOW_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"generator exited nonzero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert out_path.exists()
    return out_path


# ---------------------------------------------------------------------------
# REAL-DASHBOARD (c') leg.
# ---------------------------------------------------------------------------

def test_real_dashboard_end_to_end_matches_tool_api_projection(
    tmp_path, dashboard_fixture_log_and_manifest, dashboard_fixture_wave_plan
):
    """De-tautologized (c): run the REAL base builder
    (inventory/build_content_readiness_inventory.py) and a byte-identical
    COPY of the REAL dashboard (inventory/dashboard/build_content_readiness.py,
    retargeted at a mirror inventory/ directory purely by file placement --
    see _build_inventory_mirror) end-to-end against the (zero-verified)
    dashboard fixture log+manifest, and prove the dashboard's own PUBLISHED
    per-item aggregates.dok.review_state_uid_sets (the NT7-R Stage R4
    additive field) agrees, uid-for-uid across all 900 uids, with
    dok_review.tool_state_for() called directly.

    Two SEPARATE scripts -- build_content_readiness_inventory.py and
    gen_dok_wave_plan.py -- each independently recompute the SAME canonical
    projection from the SAME raw (log, manifest); the mirrored dashboard's
    own three-way per-item coherence guard must pass on their real outputs
    (exit 0), and this test additionally checks the dashboard's PUBLISHED
    artifact against the tool API directly -- the non-tautological version
    of leg (c): the real dashboard, run end-to-end, publishes states
    identical to the tool's. See dashboard_fixture_log_and_manifest's
    docstring for why this fixture (unlike the REAL-CONSOLE leg's) is built
    to have EXACTLY the ambient 39-uid verified set (NT10) overall."""
    log_path, manifest_path = dashboard_fixture_log_and_manifest
    gen_out_path = dashboard_fixture_wave_plan

    mirror_inventory = _build_inventory_mirror(tmp_path)

    # (i) REAL base builder, independently recomputed canonical projection.
    result_base = subprocess.run(
        [
            sys.executable, str(BASE_BUILDER_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out-dir", str(mirror_inventory),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_base.returncode == 0, (
        f"REAL base builder exited nonzero.\nSTDOUT:\n{result_base.stdout}\nSTDERR:\n{result_base.stderr}"
    )
    assert (mirror_inventory / "content_readiness_inventory.json").exists()

    # (ii) place the fixture-regenerated wave plan into the mirror.
    shutil.copy(gen_out_path, mirror_inventory / "dok-workflow" / "dok_wave_plan.json")

    # (iii) subprocess the mirrored dashboard script -- MUST exit 0.
    mirror_dashboard_script = mirror_inventory / "dashboard" / "build_content_readiness.py"
    result_dash = subprocess.run(
        [sys.executable, str(mirror_dashboard_script)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_dash.returncode == 0, (
        "mirrored dashboard exited nonzero -- its three-way per-item gate should have "
        f"passed on real code.\nSTDOUT:\n{result_dash.stdout}\nSTDERR:\n{result_dash.stderr}"
    )

    # (iv) read its published content_readiness.json.
    published = json.loads(
        (mirror_inventory / "dashboard" / "content_readiness.json").read_text(encoding="utf-8")
    )
    uid_sets = published["aggregates"]["dok"]["review_state_uid_sets"]
    uid_sets_lookup = {state: set(uids) for state, uids in uid_sets.items()}
    assert set(uid_sets_lookup) == {"invalid-entry", "reviewed_once", "verified"}

    def _published_state(uid):
        for state in ("invalid-entry", "reviewed_once", "verified"):
            if uid in uid_sets_lookup[state]:
                return state
        return "unreviewed"

    committed_plan = dok_review.load_plan(COMMITTED_PLAN_PATH)
    committed_uid_to_item, _u2l, dup = dok_review.build_uid_index(committed_plan)
    assert dup == []
    assert len(committed_uid_to_item) == 900

    shared_latest_by_uid = dok_review.latest_entries_by_uid(dok_review.read_log_entries(log_path))
    shared_approved = dok_review.load_rubric_approvals(manifest_path)

    mismatches = []
    for uid in committed_uid_to_item:
        expected = dok_review.tool_state_for(uid, shared_latest_by_uid, _approved_versions_override=shared_approved)
        actual = _published_state(uid)
        if actual != expected:
            mismatches.append((uid, actual, expected))
    assert not mismatches, f"dashboard-published vs tool-API mismatches (uid, actual, expected): {mismatches[:10]}"

    # Sanity: prove the published sets actually assert something non-trivial,
    # not "everything empty, trivially equal." This fixture is seeded with
    # the REAL 39-entry log (NT10 -- see dashboard_fixture_log_and_manifest's
    # docstring), so the published verified set must be EXACTLY the 39 RC
    # uids; the layered mix still exercises reviewed_once (FIX2, FIX3
    # post-chain, FIX5, FIX7) and invalid-entry (FIX4) non-trivially, and
    # the ambiguous-pair identity discipline shows up as FIX8_UID verified
    # while FIX8_SIBLING_UID (same legacy id, different uid) stays
    # unreviewed.
    rc_verified_uids = {
        e["item_uid"] for e in dok_review.read_log_entries(REAL_REVIEW_LOG_PATH)
    }
    assert len(rc_verified_uids) == 39
    assert uid_sets_lookup["verified"] == rc_verified_uids
    assert FIX8_UID in uid_sets_lookup["verified"]
    assert _published_state(FIX8_SIBLING_UID) == "unreviewed"
    assert uid_sets_lookup["invalid-entry"] == {FIX4_UID}
    assert {FIX2_UID, FIX3_UID, FIX5_UID, FIX7_UID} <= uid_sets_lookup["reviewed_once"]


def test_real_dashboard_end_to_end_rejects_corrupted_base_inventory(
    tmp_path, dashboard_fixture_log_and_manifest, dashboard_fixture_wave_plan
):
    """REAL-DASHBOARD negative: corrupt ONLY the mirror's freshly-built
    content_readiness_inventory.json (add a fake item_uid to its
    aggregate.dok_verified_item_uids) after the REAL base builder writes it,
    then run the mirrored dashboard -- it must fail loudly (nonzero exit)
    and name the offending uid, rather than silently accepting a base
    inventory that disagrees with the wave plan's own projection."""
    log_path, manifest_path = dashboard_fixture_log_and_manifest
    gen_out_path = dashboard_fixture_wave_plan
    fake_uid = "iu_deadbeefdead"

    mirror_inventory = _build_inventory_mirror(tmp_path)

    result_base = subprocess.run(
        [
            sys.executable, str(BASE_BUILDER_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out-dir", str(mirror_inventory),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_base.returncode == 0, (
        f"REAL base builder exited nonzero.\nSTDOUT:\n{result_base.stdout}\nSTDERR:\n{result_base.stderr}"
    )

    shutil.copy(gen_out_path, mirror_inventory / "dok-workflow" / "dok_wave_plan.json")

    base_inv_path = mirror_inventory / "content_readiness_inventory.json"
    base_inv = json.loads(base_inv_path.read_text(encoding="utf-8"))
    assert fake_uid not in base_inv["aggregate"]["dok_verified_item_uids"]
    base_inv["aggregate"]["dok_verified_item_uids"] = sorted(
        base_inv["aggregate"]["dok_verified_item_uids"] + [fake_uid]
    )
    base_inv_path.write_text(json.dumps(base_inv, ensure_ascii=False, indent=2), encoding="utf-8")

    mirror_dashboard_script = mirror_inventory / "dashboard" / "build_content_readiness.py"
    result_dash = subprocess.run(
        [sys.executable, str(mirror_dashboard_script)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_dash.returncode != 0, "mirrored dashboard should have rejected a corrupted base inventory"
    combined = result_dash.stdout + result_dash.stderr
    assert fake_uid in combined, (
        f"expected the divergent uid {fake_uid!r} to be named in the dashboard's failure output.\n"
        f"STDOUT:\n{result_dash.stdout}\nSTDERR:\n{result_dash.stderr}"
    )


def test_real_dashboard_rejects_same_cardinality_uid_swap(
    tmp_path, dashboard_fixture_log_and_manifest, dashboard_fixture_wave_plan
):
    """SAME-CARDINALITY WRONG-UID negative: prove the dashboard's per-item
    verified-uid gate is genuinely a per-ITEM identity check, not something
    that could be weakened to a count comparison without this suite
    noticing.

    NT10 re-scope (stronger than the old FIX5-for-FIX6 construction): both
    the wave plan and the base inventory now come from the SAME
    39-verified dashboard fixture (the seeded real log -- see
    dashboard_fixture_log_and_manifest), and the hand-corruption swaps
    EXACTLY ONE uid inside aggregate.dok_verified_item_uids: FIX8_UID
    (iu_3c70a19c8d36, 5-4-savvas-q41, wave 3 -- genuinely RC-verified) is
    replaced by FIX8_SIBLING_UID (iu_77d25e1e6131 -- the OTHER registry row
    behind the SAME ambiguous legacy id '5-4-savvas-q41', wave 4, never
    reviewed). Same cardinality (39), same lesson (5-4), same base bucket
    ('unreviewed'), so EVERY count-level figure -- dok_review_state_totals,
    per-lesson dok_status buckets, the ws6 distribution, the frozen 39/398
    pins -- still agrees perfectly; ONLY the per-item identity diverges.
    This is exactly the failure mode the identity rule exists for: the two
    copies of a duplicated legacy id must never be interchangeable. A
    count-only gate would see nothing wrong here; only a genuine per-item
    identity comparison can tell the pair apart, and the dashboard's
    symmetric-difference assert must name BOTH uids.

    (Hand-corrupting the base inventory after a real builder run remains
    the point: it simulates a base-inventory rebuild skipped or run against
    the wrong log -- the post-approval divergence the workflow doc's
    fail-loud list warns about.)"""
    log_path, manifest_path = dashboard_fixture_log_and_manifest
    gen_out_path = dashboard_fixture_wave_plan  # carries the 39 RC-verified uids

    mirror_inventory = _build_inventory_mirror(tmp_path)

    # (i) REAL base builder, against the 39-verified fixture chain -- the
    # only chain its own hard-pinned (claimed=39) baseline_reconciliation
    # can accept without itself exiting nonzero.
    result_base = subprocess.run(
        [
            sys.executable, str(BASE_BUILDER_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out-dir", str(mirror_inventory),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_base.returncode == 0, (
        f"REAL base builder exited nonzero.\nSTDOUT:\n{result_base.stdout}\nSTDERR:\n{result_base.stderr}"
    )

    # (ii) place the SAME fixture chain's wave plan into the mirror -- the
    # REAL generator's own output, untouched.
    shutil.copy(gen_out_path, mirror_inventory / "dok-workflow" / "dok_wave_plan.json")

    # (iii) HAND-CORRUPT the freshly-built (self-consistent, 39-verified)
    # base inventory: swap FIX8_UID -> FIX8_SIBLING_UID inside
    # dok_verified_item_uids. No other field needs touching -- cardinality,
    # totals, and per-lesson buckets are all unchanged by construction.
    base_inv_path = mirror_inventory / "content_readiness_inventory.json"
    base_inv = json.loads(base_inv_path.read_text(encoding="utf-8"))

    verified_uids = base_inv["aggregate"]["dok_verified_item_uids"]
    assert len(verified_uids) == 39
    assert FIX8_UID in verified_uids
    assert FIX8_SIBLING_UID not in verified_uids
    base_inv["aggregate"]["dok_verified_item_uids"] = sorted(
        [u for u in verified_uids if u != FIX8_UID] + [FIX8_SIBLING_UID]
    )
    assert len(base_inv["aggregate"]["dok_verified_item_uids"]) == 39  # same cardinality

    base_inv_path.write_text(json.dumps(base_inv, ensure_ascii=False, indent=2), encoding="utf-8")

    # (iv) run the REAL mirrored dashboard subprocess.
    mirror_dashboard_script = mirror_inventory / "dashboard" / "build_content_readiness.py"
    result_dash = subprocess.run(
        [sys.executable, str(mirror_dashboard_script)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result_dash.returncode != 0, (
        "mirrored dashboard should have rejected the same-cardinality uid swap -- "
        "per-item identity must never be satisfied by a count-level match alone.\n"
        f"STDOUT:\n{result_dash.stdout}\nSTDERR:\n{result_dash.stderr}"
    )
    combined = result_dash.stdout + result_dash.stderr

    # GATE ORDERING (researched directly against the live source of
    # inventory/dashboard/build_content_readiness.py's main()): the per-item
    # three-way `check("dok.verified_item_uid_sets_three_way", ...)` call
    # only APPENDS to the deferred `checks` list -- it does not raise by
    # itself. The VERY NEXT statement is a raw `assert not
    # _verified_uid_sym_diff`, which DOES raise immediately, naming the
    # symmetric difference in its own message -- and this executes BEFORE
    # the later PASS/FAIL-printing loop that would otherwise report the
    # deferred `checks` list and call fail()/sys.exit(1). So that raw
    # assert's message is what actually reaches stderr (as an uncaught
    # AssertionError traceback); the deferred check-table printout never
    # runs at all. Assert on that specific message.
    assert "symmetric-difference" in combined, (
        "expected the dashboard's per-item uid symmetric-difference assert to fire "
        f"(before any deferred check-table print).\nSTDOUT:\n{result_dash.stdout}\nSTDERR:\n{result_dash.stderr}"
    )
    # THIS is the assertion that must FAIL if the dashboard's per-item gate
    # were ever weakened from set equality to count equality: this fixture
    # was deliberately built so EVERY count-level figure already agrees
    # (verified count 39==39, dok_review_state_totals matching, per-lesson
    # buckets identical) -- a count-only check would see nothing wrong here
    # and never mention either uid. Only a genuine per-item identity
    # comparison can tell the two '5-4-savvas-q41' registry rows apart,
    # which is exactly what the symmetric-difference message must name.
    assert FIX8_UID in combined, f"expected {FIX8_UID!r} named in the failure text.\n{combined}"
    assert FIX8_SIBLING_UID in combined, f"expected {FIX8_SIBLING_UID!r} named in the failure text.\n{combined}"


# ---------------------------------------------------------------------------
# REAL-CONSOLE (d') leg.
# ---------------------------------------------------------------------------

def test_real_console_fixture_mode_end_to_end(
    tmp_path, console_fixture_log_and_manifest, console_fixture_wave_plan
):
    """De-tautologized (d): subprocess the REAL
    inventory/decision-console/build_console.py in FIXTURE MODE against the
    shared fixture wave plan + manifest -- must exit 0 -- then check its
    published console_data.json against the tool API and against the wave
    plan's own baked-in structural fields."""
    log_path, manifest_path = console_fixture_log_and_manifest
    gen_out_path = console_fixture_wave_plan
    console_out_dir = tmp_path / "console_out"

    result_console = subprocess.run(
        [
            sys.executable, str(CONSOLE_SCRIPT),
            "--fixture-wave-plan", str(gen_out_path),
            "--fixture-approvals-manifest", str(manifest_path),
            "--fixture-out", str(console_out_dir),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_console.returncode == 0, (
        f"REAL console fixture-mode build exited nonzero.\n"
        f"STDOUT:\n{result_console.stdout}\nSTDERR:\n{result_console.stderr}"
    )

    console_data = json.loads((console_out_dir / "console_data.json").read_text(encoding="utf-8"))

    committed_plan = dok_review.load_plan(COMMITTED_PLAN_PATH)
    committed_uid_to_item, _u2l, dup = dok_review.build_uid_index(committed_plan)
    assert dup == []
    shared_latest_by_uid = dok_review.latest_entries_by_uid(dok_review.read_log_entries(log_path))
    shared_approved = dok_review.load_rubric_approvals(manifest_path)
    tool_verified_uids = {
        uid for uid in committed_uid_to_item
        if dok_review.tool_state_for(uid, shared_latest_by_uid, _approved_versions_override=shared_approved)
        == "verified"
    }
    assert tool_verified_uids == {FIX6_UID}

    assert console_data["meta"]["locked_counts"]["canonical_verified_count"] == len(tool_verified_uids) == 1

    # The wave-0 dok3-driver sample item IS fixture-6 (iu_3b42ab3340d5,
    # 3-5-savvas-q27, the 3-5 dok3-driver) -- shows dok_status 'verified'.
    wave0_items = console_data["section5"]["wave0_sample"]["items"]
    dok3_driver_item = next(it for it in wave0_items if it["role"] == "dok3-driver")
    assert dok3_driver_item["item_uid"] == FIX6_UID
    assert dok3_driver_item["dok_status"] == "verified"

    # The q41 section2 pair copies keep dok 2/3 with their two uids intact
    # (fixture 8 only touches review_state/dok_status overlay for one of the
    # two copies -- registry_line/dok/id are structural and untouched).
    pairs = console_data["section2"]["pairs"]
    q41_pair = next(p for p in pairs if p["legacy_id"] == "5-4-savvas-q41")
    copies_by_uid = {c["item_uid"]: c for c in q41_pair["copies"]}
    assert set(copies_by_uid) == {FIX8_UID, FIX8_SIBLING_UID}
    assert copies_by_uid[FIX8_UID]["dok"] == 3
    assert copies_by_uid[FIX8_SIBLING_UID]["dok"] == 2


def test_real_console_fixture_mode_rejects_empty_manifest_with_verified_plan(
    console_fixture_wave_plan, tmp_path
):
    """REAL-CONSOLE negative: the SAME fixture wave plan (carrying 1
    verified item baked in via the shared log+manifest) paired with an
    EXPLICIT EMPTY approvals-manifest fixture built here under tmp_path (NOT
    the real tools/dok-review/rubric_approvals.json -- that file now carries
    the APPROVED-STATE entry for DOK rubric v0.2 and is therefore no longer
    empty) -- build_console.py's coherence guard (b) must refuse to build:
    an empty approvals manifest can never coexist with a wave plan claiming
    a verified item. Exit nonzero, message names the empty fixture
    manifest's path."""
    gen_out_path = console_fixture_wave_plan
    console_out_dir = tmp_path / "console_out_neg"
    empty_manifest_path = tmp_path / "empty_approvals.json"
    empty_manifest_path.write_text(json.dumps({"approvals": []}), encoding="utf-8")

    result_console = subprocess.run(
        [
            sys.executable, str(CONSOLE_SCRIPT),
            "--fixture-wave-plan", str(gen_out_path),
            "--fixture-approvals-manifest", str(empty_manifest_path),
            "--fixture-out", str(console_out_dir),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_console.returncode != 0, "console should have refused an empty manifest against a verified plan"
    combined = result_console.stdout + result_console.stderr
    assert "EMPTY" in combined
    expected_manifest_display = str(empty_manifest_path.resolve()).replace("\\", "/")
    assert expected_manifest_display in combined.replace("\\", "/")


# ---------------------------------------------------------------------------
# NSC-VETO DECISIVE.
# ---------------------------------------------------------------------------

def test_nsc_veto_decisive_blocks_otherwise_verification_grade_confirm(tmp_path):
    """De-tautologize the needs-source-check veto. Scenario 2's fixture 3
    (4-4-savvas-q2) never had a real calibration anchor to resolve against
    in the first place -- lesson 4-4 has zero calibration anchors -- so its
    later plain confirm was rule-2-adjacent regardless of the NSC veto; the
    veto was never actually the DECISIVE reason it failed to verify there.
    This test re-points the same needs-source-check -> confirm chain shape
    at a lesson 3-5 item that DOES have a real, resolving calibration
    anchor, so the final confirm is otherwise FULLY verification-grade, and
    the ONLY thing standing between it and 'verified' is the
    unresolved-NSC veto.

    Corpus note on "distinct from #27 and #30": questionbank/calibration/
    3-5.json anchors exactly four Savvas practice numbers -- #7 and #18 in
    dok2_anchors, #27 and #30 in dok3_anchors. Of those four, only #27 and
    #30 were ever ingested into questionbank/registry.jsonl (no
    '3-5-savvas-q07' or '3-5-savvas-q18' row exists anywhere in the
    registry), and both are already used elsewhere in this suite as
    FIX6_UID / FIX5_UID. There is therefore no THIRD lesson-3-5 practice
    item, in the actual corpus, that both exists as a reviewable wave-plan
    item AND has a real, resolving calibration anchor. This test reuses
    FIX5_UID (3-5-savvas-q30, Practice #30) in its OWN fully isolated
    tmp_path log+manifest -- never combined with the module-scoped
    dashboard_fixture_log_and_manifest / console_fixture_log_and_manifest
    above, or with any other test's log -- so this reuse creates no
    cross-test chain contamination: every "use" of iu_7f589eaba8ad lives in
    an entirely separate append-only log file, and each test function gets
    its own fresh tmp_path.
    """
    uid = FIX5_UID  # 3-5-savvas-q30 -- see corpus note above.
    log_path = tmp_path / "review_log.jsonl"
    manifest_path = tmp_path / "rubric_approvals.json"
    manifest_path.write_text(
        json.dumps({"approvals": [{"version": "v-approved-past", "approved_at": "2020-01-01T00:00:00+00:00"}]}),
        encoding="utf-8",
    )
    plan_arg = str(COMMITTED_PLAN_PATH)
    log_arg = str(log_path)

    # Entry 1: needs-source-check (terminal-unresolved, rationale required).
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", uid, "--reviewed-by", "fixture",
        "--disposition", "needs-source-check",
        "--rationale", "Need to check the Performance Task source before confirming DOK 3.",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-03-01T09:00:00+00:00",
    ])
    # Entry 2: a PLAIN confirm (no --resolves-source-check) -- proves the
    # veto persists across an intervening entry, not just immediately after
    # the needs-source-check.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", uid, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-03-01T09:05:00+00:00",
    ])
    # Entry 3: the DECISIVE one -- a confirm that IS otherwise fully
    # verification-grade (resolved rule-1 provenance against the item's own
    # dok3_anchors entry for Practice #30, an already-approved rubric
    # version, tool-stamped recorded_at necessarily >= approved_at) but
    # WITHOUT --resolves-source-check.
    dok_review.main([
        "--plan", plan_arg, "--log", log_arg, "review",
        "--item-uid", uid, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #30",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-03-01T09:10:00+00:00",
    ])

    all_entries = dok_review.read_log_entries(log_path)
    chain = dok_review.entries_for_uid(all_entries, uid)
    assert len(chain) == 3
    latest_entry = chain[-1]

    # The raw latest entry carries the veto stamp...
    assert latest_entry["prior_unresolved_nsc"] is True
    # ...and DOES record a resolved, verification-grade disposition (proven
    # directly off the stamped fields, not re-derived here):
    assert latest_entry["confirmation_basis"] == "rule-1-textbook-provenance"
    assert latest_entry["provenance_resolved"] is True

    approved = dok_review.load_rubric_approvals(manifest_path)

    # It would otherwise satisfy entry_is_verified()'s disposition+rubric
    # clauses -- proven against the REAL predicate, not reimplemented here:
    # flip ONLY the veto field and the SAME function then says True.
    would_verify_entry = dict(latest_entry)
    would_verify_entry["prior_unresolved_nsc"] = False
    assert dok_review.entry_is_verified(would_verify_entry, _approved_versions_override=approved) is True
    # ...but the REAL (unpatched) entry, with the veto intact, does not verify.
    assert dok_review.entry_is_verified(latest_entry, _approved_versions_override=approved) is False

    latest_by_uid = dok_review.latest_entries_by_uid(all_entries)

    # (a) TOOL API
    a_state = dok_review.tool_state_for(uid, latest_by_uid, _approved_versions_override=approved)

    # (b) GENERATOR ARTIFACT
    gen_out = tmp_path / "dok_wave_plan.generated.json"
    result_gen = subprocess.run(
        [
            sys.executable, str(GEN_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out", str(gen_out),
        ],
        cwd=str(WORKFLOW_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_gen.returncode == 0, (
        f"generator exited nonzero.\nSTDOUT:\n{result_gen.stdout}\nSTDERR:\n{result_gen.stderr}"
    )
    gen_plan = dok_review.load_plan(gen_out)
    uid_to_item, _u2l, dup = dok_review.build_uid_index(gen_plan)
    assert dup == []
    b_state = uid_to_item[uid]["review_state"]

    # (c) DASHBOARD (direct fail-closed read, same style test_scenario2 uses)
    c_state = build_content_readiness.wave_plan_item_review_state(uid_to_item[uid])

    # (d) REPORT/CONSOLE-FACING
    d_state = next(
        row["tool_state"]
        for row in dok_review.get_queue_rows(gen_plan, log_path, _approved_versions_override=approved)
        if row["item_uid"] == uid
    )

    assert a_state == b_state == c_state == d_state == "reviewed_once", (
        f"uid={uid}: tool_api={a_state!r} generator_artifact={b_state!r} "
        f"dashboard={c_state!r} queue_rows={d_state!r} -- expected the NSC veto to "
        "be the DECISIVE, sole reason this otherwise fully verification-grade "
        "confirm does not verify"
    )


# ---------------------------------------------------------------------------
# MALFORMED-LOG-SHAPE end-to-end.
# ---------------------------------------------------------------------------

def test_malformed_log_shape_end_to_end_fails_closed(tmp_path):
    """DISCRIMINATING version: a non-dict JSON line poisons the WHOLE review
    log (dok_review.read_log_entries's whole-log fail-closed policy) even
    when the log ALSO contains an otherwise fully verification-grade entry
    recorded BEFORE the poison -- this proves whole-log poisoning actually
    collapses a real verification, not merely that an already-unverifiable
    log stays unverified (the weaker thing the old version of this test
    proved).

    Sequence: (i) record ONE verification-grade entry -- the SAME rule-1
    post-approval confirm on FIX6_UID (iu_3b42ab3340d5, 3-5-savvas-q27,
    provenance resolving against lesson 3-5's real dok3_anchors Practice #27
    entry, rubric_version "v-approved-past" which IS in effect) -- via the
    tool's own CLI path; (ii) FIRST prove, at the tool-API level on the log
    as it stands right after (i), that this entry really does verify absent
    any poison; (iii) THEN append one hand-crafted, non-dict JSON line;
    (iv) prove the collapse end-to-end through BOTH the REAL generator and
    the REAL base builder, run as real subprocesses against the poisoned
    log -- not just at the tool-API level."""
    log_path = tmp_path / "review_log.jsonl"
    manifest_path = tmp_path / "rubric_approvals.json"
    _write_standard_manifest(manifest_path)  # v-approved-past (in effect) + v-approved-future

    uid = FIX6_UID  # 3-5-savvas-q27 -- the ONE item that verifies anywhere in this suite.

    # (i) ONE verification-grade entry, via the tool's own CLI path -- the
    # SAME rule-1-grade, post-approval confirm used as fixture 6 elsewhere
    # in this file.
    dok_review.main([
        "--plan", str(COMMITTED_PLAN_PATH), "--log", str(log_path), "review",
        "--item-uid", uid, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #27",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:00:00+00:00",
    ])

    # (ii) PROVE it verifies ABSENT the poison, at the tool-API level, on the
    # log exactly as it stands right now (before any malformed line is
    # appended). Without this proof, the negative assertions below would be
    # meaningless -- they'd just show an already-non-verifying entry stayed
    # non-verified, not that poisoning COLLAPSED a real verification.
    approved = dok_review.load_rubric_approvals(manifest_path)
    pre_poison_latest = dok_review.latest_entries_by_uid(dok_review.read_log_entries(log_path))
    assert (
        dok_review.tool_state_for(uid, pre_poison_latest, _approved_versions_override=approved)
        == "verified"
    ), (
        "fixture entry must be verification-grade BEFORE the malformed line "
        "is appended, or the whole-log-poisoning proof below is vacuous"
    )

    # (iii) THEN append ONE hand-crafted, non-dict JSON line -- never via the
    # tool. This is what must poison the WHOLE log, including the valid
    # entry recorded above, not just get skipped as one bad line among
    # otherwise-good ones.
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps([1, 2, 3]) + "\n")

    # (iv-a) generator run against the poisoned log: exits 0, verified 0,
    # FIX6_UID's review_state specifically collapses to 'unreviewed' (not
    # merely "some item somewhere is unreviewed"), warning on stderr.
    gen_out = tmp_path / "dok_wave_plan.generated.json"
    result_gen = subprocess.run(
        [
            sys.executable, str(GEN_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out", str(gen_out),
        ],
        cwd=str(WORKFLOW_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_gen.returncode == 0, (
        f"generator should fail-closed to an empty log, not fail the run.\n"
        f"STDOUT:\n{result_gen.stdout}\nSTDERR:\n{result_gen.stderr}"
    )
    assert "WARNING" in result_gen.stderr

    plan = dok_review.load_plan(gen_out)
    assert plan["verification_note"]["verified_count"] == 0
    uid_to_item, _u2l, dup = dok_review.build_uid_index(plan)
    assert dup == []
    assert uid_to_item[uid]["review_state"] == "unreviewed", (
        f"uid={uid}: expected the otherwise-verifying entry to collapse to "
        f"'unreviewed' once the malformed line poisons the whole log, got "
        f"{uid_to_item[uid]['review_state']!r}"
    )
    all_review_states = {
        item["review_state"]
        for wave in plan["waves"].values()
        for items in wave.values()
        for item in items
    }
    assert all_review_states == {"unreviewed"}

    # (iv-b) REAL base builder run against the SAME poisoned log + the SAME
    # approved manifest. NT10 premise change: the builder's
    # baseline_reconciliation now carries the frozen claimed=39 baseline
    # (RC's first real recording -- step 3(b1)), so a whole-log-poisoned
    # (therefore zero-verified) projection can no longer complete a run:
    # the fail-CLOSED collapse (tool layer: WARNING, zero verified) now
    # meets the fail-LOUD frozen-baseline gate (builder layer:
    # computed=0 != claimed=39 -> VALIDATION FAILED, NOTHING WRITTEN,
    # nonzero exit, the DELIBERATE FROZEN-BASELINE guidance naming step
    # 3(b1)). This is the intended post-recording behavior: a poisoned log
    # must never let the builder silently overwrite published artifacts
    # that claim 39 verified rows with a collapsed-to-zero inventory.
    out_dir = tmp_path / "base_builder_out"
    out_dir.mkdir()
    result_base = subprocess.run(
        [
            sys.executable, str(BASE_BUILDER_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(manifest_path),
            "--out-dir", str(out_dir),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_base.returncode != 0, (
        "base builder should REFUSE to publish a collapsed-to-zero "
        "inventory while its frozen baseline claims 39 verified rows "
        "(NT10) -- a poisoned log must fail loudly here, not exit 0.\n"
        f"STDOUT:\n{result_base.stdout}\nSTDERR:\n{result_base.stderr}"
    )
    # The fail-CLOSED collapse still happened at the tool layer...
    assert "WARNING" in result_base.stderr
    combined_base = result_base.stdout + result_base.stderr
    # ...and the refusal is the named frozen-baseline reconciliation gate,
    # not a crash: it must name the mismatch and the deliberate pin.
    assert "computed=0 claimed=39" in combined_base
    assert "DELIBERATE FROZEN-BASELINE RECONCILIATION CLAIM" in combined_base
    assert "NOTHING WRITTEN" in combined_base
    assert not (out_dir / "content_readiness_inventory.json").exists(), (
        "the base builder must not write any inventory output when its "
        "frozen-baseline reconciliation gate fails"
    )


# ---------------------------------------------------------------------------
# DUPLICATE-VERSION MANIFEST end-to-end.
# ---------------------------------------------------------------------------

def test_duplicate_version_manifest_blocks_verification_end_to_end(tmp_path):
    """A rubric-approvals manifest listing the SAME version twice fails
    closed to {} (load_rubric_approvals's duplicate-version guard) -- prove
    fixture-6's otherwise-verifying confirm (the SAME rule-1-grade,
    v-approved-past confirm used as scenario 2's fixture 6) does NOT verify
    under such a manifest, at both the tool-API level and end-to-end through
    the REAL generator (verified 0, in agreement)."""
    log_path = tmp_path / "review_log.jsonl"
    dup_manifest = tmp_path / "rubric_approvals.json"
    dup_manifest.write_text(
        json.dumps({
            "approvals": [
                {"version": "v-approved-past", "approved_at": "2020-01-01T00:00:00+00:00"},
                {"version": "v-approved-past", "approved_at": "2020-06-01T00:00:00+00:00"},
            ]
        }),
        encoding="utf-8",
    )

    dok_review.main([
        "--plan", str(COMMITTED_PLAN_PATH), "--log", str(log_path), "review",
        "--item-uid", FIX6_UID, "--reviewed-by", "fixture",
        "--disposition", "confirm",
        "--provenance", "calibration-anchor:3-5:practice #27",
        "--rubric-version", "v-approved-past",
        "--reviewed-at", "2026-02-01T09:00:00+00:00",
    ])

    dup_approved = dok_review.load_rubric_approvals(dup_manifest)
    assert dup_approved == {}
    latest_by_uid = dok_review.latest_entries_by_uid(dok_review.read_log_entries(log_path))
    assert (
        dok_review.tool_state_for(FIX6_UID, latest_by_uid, _approved_versions_override=dup_approved)
        == "reviewed_once"
    )

    gen_out = tmp_path / "dok_wave_plan.generated.json"
    result_gen = subprocess.run(
        [
            sys.executable, str(GEN_SCRIPT),
            "--review-log", str(log_path),
            "--approvals-manifest", str(dup_manifest),
            "--out", str(gen_out),
        ],
        cwd=str(WORKFLOW_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result_gen.returncode == 0, (
        f"generator exited nonzero.\nSTDOUT:\n{result_gen.stdout}\nSTDERR:\n{result_gen.stderr}"
    )
    assert "WARNING" in result_gen.stderr  # duplicate-version warning from load_rubric_approvals

    plan = dok_review.load_plan(gen_out)
    assert plan["verification_note"]["verified_count"] == 0
    uid_to_item, _u2l, dup = dok_review.build_uid_index(plan)
    assert dup == []
    assert uid_to_item[FIX6_UID]["review_state"] == "reviewed_once"
