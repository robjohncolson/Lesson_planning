"""
test_parity_check.py -- pytest suite for NT15 product-policy Deliverable D3
(Schoology projection & reconciliation, parity_check.py).

Package: NT15 product-policy · Version: 2.0 · Date: 2026-07-24
Source of authority: RC final decisions, 2026-07-24 (Grok preference interview + RC
clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
Status: Authoritative -- gates all future Desk / grading / Schoology implementation.

Hermetic: no network, no dependency on any repo file outside product-policy/. Fixture
JSON files are loaded relative to this file's own directory via pathlib.Path(__file__).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import parity_check

HERE = Path(__file__).resolve().parent
FIXTURES_DIR = HERE / "fixtures" / "schoology"


def _load(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------------
# Convergent case.
# ----------------------------------------------------------------------------------

def test_convergent_case_reports_not_divergent():
    fixture = _load("student_0001_above_gate_convergent.json")
    report = parity_check.check_student_parity(fixture)

    assert report["student_id"] == "SYNTHETIC-STUDENT-0001"
    assert report["a2_expected_quarter_grade"] == pytest.approx(88.0)
    assert report["schoology_native_quarter_grade"] == pytest.approx(88.0)
    assert report["divergent"] is False
    assert report["delta"] == pytest.approx(0.0, abs=1e-6)
    assert report["comparison_basis"] == parity_check._COMPARISON_BASIS_FULL_PRECISION
    assert report["underlying_convergence_established"] is True
    assert report["schoology_value_is_display_rounded"] is False
    assert "CONVERGENT" in report["note"]


# ----------------------------------------------------------------------------------
# Divergent case is detected AND surfaced (both directions: native understating and
# native overstating relative to A2's authoritative figure). Numbers below are the
# NT16-recomputed point-based figures (OPEN-15/OPEN-19, RESOLVED by RC 2026-07-24) --
# they supersede v1.0's placeholder-derived numbers (98.0/69.5/91.0), but the
# fixture data itself, and Schoology's native flat-ratio figure (unaffected by
# OPEN-15/OPEN-19), are unchanged.
# ----------------------------------------------------------------------------------

def test_divergent_case_above_gate_is_detected_and_surfaced():
    fixture = _load("student_0002_above_gate_divergent.json")
    report = parity_check.check_student_parity(fixture)

    assert report["completion_pct"] >= parity_check.COMPLETION_THRESHOLD
    # A2 takes the max(work, assessment) branch; work is by far the stronger aggregate.
    # work_aggregate = 100*(190+2+1.0)/(200+2) = 95.544554...
    assert report["work_aggregate"] == pytest.approx(95.544554, abs=1e-4)
    assert report["assessment_aggregate"] == pytest.approx(64.333333, abs=1e-4)
    assert report["a2_expected_quarter_grade"] == pytest.approx(95.544554, abs=1e-4)
    # Schoology's native flat ratio blends WORK+ASSESSMENT together and lands far lower.
    # UNAFFECTED by OPEN-15/OPEN-19 -- this was always a flat points ratio.
    assert report["schoology_native_quarter_grade"] == pytest.approx(76.892430, abs=1e-4)
    assert report["divergent"] is True
    assert report["comparison_basis"] == parity_check._COMPARISON_BASIS_FULL_PRECISION
    assert report["underlying_convergence_established"] is False
    assert report["delta"] is not None
    assert report["delta"] > 15.0  # a large, clearly-actionable gap, not rounding noise
    assert "DIVERGENT" in report["note"]
    assert "RC" in report["note"]
    assert "never auto-resolve" in report["note"].lower()


def test_divergent_case_below_gate_is_detected_and_surfaced_other_direction():
    fixture = _load("student_0003_below_gate_divergent.json")
    report = parity_check.check_student_parity(fixture)

    assert report["completion_pct"] < parity_check.COMPLETION_THRESHOLD
    # A2 takes the average(work, assessment) branch.
    # work_aggregate = 100*(50+0+0)/(100+1) = 49.504950...; assessment = 89.0
    assert report["work_aggregate"] == pytest.approx(49.504950, abs=1e-4)
    assert report["assessment_aggregate"] == pytest.approx(89.0)
    assert report["a2_expected_quarter_grade"] == pytest.approx(69.252475, abs=1e-4)
    assert report["schoology_native_quarter_grade"] == pytest.approx(75.747508, abs=1e-4)
    assert report["divergent"] is True
    # This time the native figure OVERSTATES relative to A2's authoritative figure --
    # confirms the mismatch is not an artifact of one particular direction.
    assert report["delta"] < 0
    assert "DIVERGENT" in report["note"]


def test_divergence_is_never_silently_auto_resolved():
    """The report never picks a winner between the two figures -- it always returns
    BOTH values plus an explicit divergent flag for a human/RC to act on."""
    for name in ("student_0002_above_gate_divergent.json", "student_0003_below_gate_divergent.json"):
        report = parity_check.check_student_parity(_load(name))
        assert report["divergent"] is True
        assert report["a2_expected_quarter_grade"] != report["schoology_native_quarter_grade"]
        # Both figures are preserved in the report -- nothing gets overwritten/dropped.
        assert isinstance(report["a2_expected_quarter_grade"], float)
        assert isinstance(report["schoology_native_quarter_grade"], float)


# ----------------------------------------------------------------------------------
# UNKNOWN never becomes 0.
# ----------------------------------------------------------------------------------

def test_unknown_assessment_evidence_never_becomes_zero_or_a_number():
    fixture = _load("student_0004_unknown_assessment_evidence.json")
    report = parity_check.check_student_parity(fixture)

    # The topic assessment is ungraded -- A2's authoritative grade MUST be UNKNOWN,
    # never 0, never a silently-picked branch, never a fabricated number.
    assert report["a2_expected_quarter_grade"] == parity_check.UNKNOWN
    assert report["a2_expected_quarter_grade"] != 0
    assert report["a2_expected_quarter_grade"] != 0.0

    # work_aggregate WAS fully computable (all its inputs were graded) -- UNKNOWN must
    # not "leak backwards" into evidence that was actually available.
    # work_aggregate = 100*(90+1+0)/(100+1) = 90.099009...
    assert report["work_aggregate"] == pytest.approx(90.099009, abs=1e-4)

    # assessment_aggregate is UNKNOWN because one of its two required inputs is ungraded.
    assert report["assessment_aggregate"] == parity_check.UNKNOWN

    # Schoology's native figure DOES compute a plausible-looking number here (by
    # excluding the ungraded item) -- this fixture exists specifically to prove that
    # number is never conflated with the authoritative UNKNOWN state.
    assert report["schoology_native_quarter_grade"] == pytest.approx(85.074627, abs=1e-4)

    # UNKNOWN vs anything is ALWAYS flagged -- never silently treated as fine/equal.
    assert report["divergent"] is True
    assert "UNKNOWN" in report["note"]
    assert "MUST NOT" in report["note"]


def test_unknown_propagates_from_raw_evidence_helpers_never_as_zero():
    # An empty assignment list means "nothing to reduce" -> UNKNOWN, never 0 (OPEN-19's
    # point-weighted reduction hits its own zero-denominator rule, OPEN-16).
    assert parity_check._points_weighted_percentage([]) == parity_check.UNKNOWN
    # An ungraded entry anywhere in the list makes the WHOLE reduction UNKNOWN.
    ungraded = [{"status": "unavailable", "points_earned": None, "points_possible": 100.0}]
    assert parity_check._points_weighted_percentage(ungraded) == parity_check.UNKNOWN
    # An empty participation/extra-credit/packet list means "nothing assigned" ->
    # (0.0, 0.0) is correct here (matches grading_policy_ref.compute_work_aggregate's own
    # "nothing here" behavior), NOT UNKNOWN -- this is deliberately different from
    # "graded evidence exists but wasn't scored yet". OPEN-15 (RESOLVED): _sum_points now
    # yields an (earned, possible) PAIR, not a single scalar.
    assert parity_check._sum_points([]) == (0.0, 0.0)
    # But an ungraded entry that DOES exist still propagates UNKNOWN on BOTH sides of the
    # pair, never 0.
    assert parity_check._sum_points(ungraded) == (parity_check.UNKNOWN, parity_check.UNKNOWN)


def test_run_all_parity_checks_produces_exactly_the_expected_divergence_mix():
    reports = parity_check.run_all_parity_checks()
    # 6 student fixtures as of NT16: the original 4 (1 convergent, 3 divergent) plus the
    # zero-denominator (OPEN-16) and display-rounding (OPEN-09) fixtures added this
    # tranche. Neither new fixture is run with schoology_value_is_display_rounded=True
    # here (run_all_parity_checks never passes that flag), so both surface as ordinary
    # divergent reports under default parameters -- see the dedicated test groups below
    # for what each fixture demonstrates when exercised directly with the flag.
    assert len(reports) == 6
    divergent = [r for r in reports if r["divergent"]]
    convergent = [r for r in reports if not r["divergent"]]
    assert len(convergent) == 1
    assert len(divergent) == 5


# ----------------------------------------------------------------------------------
# OPEN-15 (RESOLVED by RC 2026-07-24): point-based WORK aggregate. compute_work_aggregate
# now takes packet/participation earned+possible and an extra-credit earned scalar, and
# delegates to grading_policy_ref.compute_work_aggregate exactly.
# ----------------------------------------------------------------------------------

def test_compute_work_aggregate_point_based_formula():
    # WORK = 100 * (packet_earned + participation_earned + extra_credit_earned)
    #        / (packet_possible + participation_possible)
    result = parity_check.compute_work_aggregate(90.0, 100.0, 1.0, 1.0, 0.5)
    assert result == pytest.approx(100.0 * (90.0 + 1.0 + 0.5) / (100.0 + 1.0))


def test_compute_work_aggregate_zero_denominator_is_unknown_never_fabricated():
    # OPEN-16 (RESOLVED): no eligible designated work/participation -> UNKNOWN, never a
    # ZeroDivisionError, never a fabricated 0 or 100.
    result = parity_check.compute_work_aggregate(0.0, 0.0, 0.0, 0.0, 0.0)
    assert result == parity_check.UNKNOWN
    assert result != 0
    assert result != 0.0


def test_compute_work_aggregate_propagates_unknown_never_as_zero():
    result = parity_check.compute_work_aggregate(parity_check.UNKNOWN, 100.0, 0.0, 0.0, 0.0)
    assert result == parity_check.UNKNOWN


def test_local_fallback_work_aggregate_agrees_with_grading_policy_ref_when_both_available():
    """Sanity-check that parity_check's local point-based fallback (used only when the
    sibling module is absent) computes the SAME number as grading_policy_ref's own
    compute_work_aggregate on a representative case -- both implement the identical
    OPEN-15 DECIDED formula, never a different one."""
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip("grading_policy_ref.py not present at runtime (parallel NT15 workstream).")
    args = (96.0, 100.0, 1.0, 1.0, 0.5)
    ref_result = parity_check._from_ref_value(
        parity_check.GRADING_POLICY_REF.compute_work_aggregate(*args)
    )
    local_result = parity_check._local_compute_work_aggregate(*args)
    assert ref_result == pytest.approx(local_result)


# ----------------------------------------------------------------------------------
# OPEN-19 (RESOLVED by RC 2026-07-24): point-weighted multi-item reduction.
# Equal-averaging per-item percentages when possible-points differ is FORBIDDEN.
# ----------------------------------------------------------------------------------

def test_compute_assessment_aggregate_is_point_weighted_not_an_average():
    # A 90/100 item and a 2/50 item: point-weighted = (90+2)/(100+50) * 100 = 61.333...
    # An equal average of per-item percentages (90% + 4%) / 2 = 47% would be WRONG and
    # is explicitly forbidden by RC's ruling -- this test proves the harness never does it.
    result = parity_check.compute_assessment_aggregate([(90.0, 100.0), (2.0, 50.0)])
    assert result == pytest.approx(100.0 * (90.0 + 2.0) / (100.0 + 50.0))
    assert result != pytest.approx(47.0)


def test_compute_assessment_aggregate_zero_denominator_is_unknown():
    assert parity_check.compute_assessment_aggregate([]) == parity_check.UNKNOWN


def test_compute_assessment_aggregate_propagates_unknown():
    assert parity_check.compute_assessment_aggregate([(50.0, 100.0), (parity_check.UNKNOWN, 100.0)]) == parity_check.UNKNOWN


def test_local_fallback_assessment_aggregate_agrees_with_grading_policy_ref_when_both_available():
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip("grading_policy_ref.py not present at runtime (parallel NT15 workstream).")
    items = [(90.0, 100.0), (2.0, 50.0)]
    ref_result = parity_check._from_ref_value(
        parity_check.GRADING_POLICY_REF.compute_assessment_aggregate(items)
    )
    local_result = parity_check._local_compute_assessment_aggregate(items)
    assert ref_result == pytest.approx(local_result)


# ----------------------------------------------------------------------------------
# V3 FIX (Codex re-check, HIGH, RESOLVED by RC 2026-07-24): the hermetic local fallback
# (`_local_compute_assessment_aggregate`, exercised whenever `grading_policy_ref.py` is
# absent at runtime) previously reimplemented the ORIGINAL C4 defect its own docstring
# claimed was already fixed -- it silently omitted the strict per-item
# `points_earned <= points_possible` domain check, so `[(120.0, 100.0)]` returned a bare
# 120.0 (an out-of-domain ASSESSMENT percentage -- extra credit never touches ASSESSMENT,
# PREF-04.5) instead of raising. Both the packaged path AND the forced-fallback path must
# now reject this identically, and the two paths must still agree on a legitimate input.
# ----------------------------------------------------------------------------------

def test_packaged_assessment_aggregate_rejects_points_earned_exceeding_possible():
    """V3, path 1 of 2: the packaged grading_policy_ref path already correctly rejects an
    ASSESSMENT item whose points_earned exceeds points_possible -- this is the DATA DEFECT
    C4 fixed there. This test pins that behavior down explicitly for this module's own
    public `compute_assessment_aggregate` entry point (not just grading_policy_ref's own
    suite), so a future change to parity_check's delegation cannot silently swallow it."""
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip("grading_policy_ref.py not present at runtime (parallel NT15 workstream).")
    with pytest.raises(parity_check.PolicyDomainError):
        parity_check.compute_assessment_aggregate([(120.0, 100.0)])


def test_forced_fallback_assessment_aggregate_also_rejects_points_earned_exceeding_possible(monkeypatch):
    """V3, path 2 of 2 -- THE discriminating test for this finding. Monkeypatches
    `parity_check.GRADING_POLICY_REF` to `None` so `compute_assessment_aggregate` is
    genuinely forced onto `_local_compute_assessment_aggregate` (never merely calling that
    private function directly, which would not prove the public dispatch path is also
    exercised correctly) and confirms the SAME (120.0, 100.0) violation is still rejected.
    Running this against the pre-V3-fix fallback FAILS: it returned a bare 120.0 instead
    of raising -- the exact hazard V3 flagged (the fallback path is only ever exercised
    when nobody is looking, i.e. when grading_policy_ref.py is genuinely absent)."""
    monkeypatch.setattr(parity_check, "GRADING_POLICY_REF", None)
    with pytest.raises(parity_check.PolicyDomainError):
        parity_check.compute_assessment_aggregate([(120.0, 100.0)])


def test_packaged_and_forced_fallback_assessment_aggregate_agree_on_a_legitimate_input_set(monkeypatch):
    """V3 parity guard: on a normal, LEGITIMATE input set (no domain violation), the
    packaged path and the forced-fallback path -- exercised through the SAME public
    `compute_assessment_aggregate` entry point -- must produce the identical number, so
    future drift between them is caught by this suite rather than discovered only once
    grading_policy_ref.py is genuinely absent in some real deployment."""
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip("grading_policy_ref.py not present at runtime (parallel NT15 workstream).")
    items = [(90.0, 100.0), (2.0, 50.0)]
    packaged_result = parity_check.compute_assessment_aggregate(items)

    monkeypatch.setattr(parity_check, "GRADING_POLICY_REF", None)
    forced_fallback_result = parity_check.compute_assessment_aggregate(items)

    assert forced_fallback_result == pytest.approx(packaged_result)


# ----------------------------------------------------------------------------------
# V3 re-check: sibling local-fallback divergences found and fixed alongside the main
# assessment-aggregate defect above -- `_local_compute_work_aggregate` was missing the
# packaged path's non-negative-input validation, and `_local_compute_quarter_grade` was
# missing its completion-in-[0,1] / assessment-in-[0,100] / work-non-negative validation.
# ----------------------------------------------------------------------------------

def test_packaged_and_forced_fallback_work_aggregate_both_reject_a_negative_input(monkeypatch):
    """Sibling-divergence fix: grading_policy_ref.compute_work_aggregate validates every
    known input as non-negative; the local hermetic fallback previously skipped that
    validation entirely, silently letting a negative input flow through the arithmetic."""
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip("grading_policy_ref.py not present at runtime (parallel NT15 workstream).")
    with pytest.raises(parity_check.PolicyDomainError):
        parity_check.compute_work_aggregate(-5.0, 100.0, 0.0, 0.0, 0.0)

    monkeypatch.setattr(parity_check, "GRADING_POLICY_REF", None)
    with pytest.raises(parity_check.PolicyDomainError):
        parity_check.compute_work_aggregate(-5.0, 100.0, 0.0, 0.0, 0.0)


def test_packaged_and_forced_fallback_quarter_grade_both_reject_an_out_of_range_assessment(monkeypatch):
    """Sibling-divergence fix: grading_policy_ref.compute_quarter_grade validates
    assessment_aggregate is in [0, 100] (extra credit never touches ASSESSMENT,
    PREF-04.5); the local hermetic fallback previously skipped that validation entirely."""
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip("grading_policy_ref.py not present at runtime (parallel NT15 workstream).")
    with pytest.raises(parity_check.PolicyDomainError):
        parity_check.compute_a2_quarter_grade(80.0, 150.0, 0.75)

    monkeypatch.setattr(parity_check, "GRADING_POLICY_REF", None)
    with pytest.raises(parity_check.PolicyDomainError):
        parity_check.compute_a2_quarter_grade(80.0, 150.0, 0.75)


# ----------------------------------------------------------------------------------
# Reconciliation coherence (Codex SOL review R-B, finding B4): the Schoology-native
# figure must reconcile from the records project_course() ACTUALLY produced, keyed by
# external_key -- not from an independent re-derivation of a student fixture's own
# per-item fields -- and every report names the computation mode it used.
# ----------------------------------------------------------------------------------

def test_schoology_native_grade_excludes_evidence_for_never_projected_lessons():
    """A score for a lesson that was never actually projected (e.g. `unreleased`) must
    contribute NOTHING to the Schoology-native figure -- Schoology never received it, so
    it cannot be part of what Schoology natively computes from what was published."""
    catalog = parity_check.load_course_catalog()
    published_records = {r["external_key"]: r for r in parity_check.project_course(catalog)}
    course_id = catalog["course_id"]

    # "4-5" is `unreleased` in the catalog fixture -- confirm it was never published.
    never_published_key = parity_check.external_key(course_id, "4-5", "lesson_packet_work", "packet")
    assert never_published_key not in published_records

    fixture_with_unpublished_evidence = {
        "student_id": "SYNTHETIC-STUDENT-TEST-B4",
        "packet_assignments": [
            {"lesson_id": "4-5", "artifact_type": "lesson_packet_work", "artifact_id": "packet",
             "points_earned": 100.0, "points_possible": 100.0, "extra_credit": False, "status": "graded"},
        ],
        "participation_assignments": [],
        "extra_credit_assignments": [],
        "quiz_assignments": [],
        "topic_assessment_assignments": [],
    }
    native = parity_check.compute_schoology_native_grade(
        course_id, published_records, fixture_with_unpublished_evidence
    )
    # No published assignment corresponds to this evidence -- the possible-points total
    # stays 0 -- UNKNOWN, never a fabricated 100.0 from evidence Schoology never received.
    assert native == parity_check.UNKNOWN


def test_schoology_native_grade_uses_published_points_possible_not_fixture_copy():
    """The catalog-declared (published) points_possible/extra_credit are authoritative for
    the Schoology-native computation -- not whatever a fixture entry's own duplicated copy
    of those fields happens to say -- since that catalog data is what was really published."""
    catalog = parity_check.load_course_catalog()
    published_records = {r["external_key"]: r for r in parity_check.project_course(catalog)}
    course_id = catalog["course_id"]

    # "4-3"/lesson_packet_work/packet is published with points_possible=100.0 in the catalog.
    fixture = {
        "student_id": "SYNTHETIC-STUDENT-TEST-B4B",
        "packet_assignments": [
            # Deliberately WRONG points_possible on the fixture side (25.0, not 100.0) --
            # the published catalog value must win, proving the join is real, not cosmetic.
            {"lesson_id": "4-3", "artifact_type": "lesson_packet_work", "artifact_id": "packet",
             "points_earned": 25.0, "points_possible": 25.0, "extra_credit": False, "status": "graded"},
        ],
        "participation_assignments": [], "extra_credit_assignments": [],
        "quiz_assignments": [], "topic_assessment_assignments": [],
    }
    native = parity_check.compute_schoology_native_grade(course_id, published_records, fixture)
    # earned=25.0 over the PUBLISHED points_possible=100.0 (catalog), not the fixture's own 25.0.
    assert native == pytest.approx(25.0)


def test_check_student_parity_report_names_the_computation_mode_used():
    """Every reconciliation report explicitly names the Schoology computation mode it
    assumed, so no run silently compares under an unstated mode."""
    report = parity_check.check_student_parity(_load("student_0001_above_gate_convergent.json"))
    assert report["schoology_computation_mode"] == parity_check.SCHOOLOGY_COMPUTATION_MODE
    assert report["schoology_computation_mode"] == "flat_total_points"


# ----------------------------------------------------------------------------------
# OPEN-09 (RESOLVED by RC 2026-07-24): display-rounding-AWARE reconciliation -- NOT
# rounding-forgiveness (C2 fix, Codex review, HIGH, RESOLVED 2026-07-24).
#
# C2's finding: RC's ruling ("reconciliation compares underlying values consistently and
# must not mistake display rounding for substantive divergence") bans FALSE ALARMS over
# cosmetic rounding -- it is NOT permission to FORGIVE a genuine underlying difference.
# v2.0's first implementation misread it as forgiveness: `_rounding_only_difference()`
# rounded BOTH figures and converted a raw divergence into `divergent: False` whenever
# `schoology_value_is_display_rounded=True` was declared. That helper and its forgiveness
# branch are DELETED. Reconciliation is now UNDERLYING-ONLY: the substantive comparison
# ALWAYS runs on full-precision values at plain numeric `tolerance`, on EITHER comparison
# basis, with no exception. `schoology_value_is_display_rounded` no longer changes the
# divergence verdict at all -- it only changes what the report may honestly CLAIM about
# the comparison, via the `comparison_basis` (str) and `underlying_convergence_established`
# (bool) fields: a display-rounded-observation basis NEVER asserts genuine underlying
# convergence, even when the observed numbers happen to match.
# ----------------------------------------------------------------------------------

def test_rounding_only_difference_on_display_rounded_basis_is_not_reported_as_converged():
    """C2 (HIGH), required test 1: the two full-precision figures differ by 0.03 -- a
    REAL underlying difference, far beyond the numeric `tolerance` this harness always
    applies. Declaring schoology_value_is_display_rounded=True must NOT convert this into
    a convergent report: underlying_convergence_established is False, comparison_basis
    names the degraded basis, and the difference is still surfaced divergent."""
    fixture = _load("student_0006_display_rounding_only_difference.json")
    report = parity_check.check_student_parity(fixture, schoology_value_is_display_rounded=True)

    assert report["a2_expected_quarter_grade"] == pytest.approx(88.03)
    assert report["schoology_native_quarter_grade"] == pytest.approx(88.0)
    assert report["delta"] == pytest.approx(0.03, abs=1e-4)
    assert report["schoology_value_is_display_rounded"] is True
    assert report["comparison_basis"] == parity_check._COMPARISON_BASIS_DISPLAY_ROUNDED
    assert "NOT established" in report["comparison_basis"]
    assert report["underlying_convergence_established"] is False
    # The real (0.03) difference is STILL flagged divergent -- never forgiven.
    assert report["divergent"] is True
    assert "DIVERGENT" in report["note"]
    assert "CONVERGENT" not in report["note"]


def test_identical_full_precision_figures_reconcile_convergent_and_establish_underlying_convergence():
    """C2, required test 2: on the default, undeclared, full-precision basis, figures
    that genuinely agree within tolerance reconcile convergent AND establish underlying
    convergence -- this is the ONLY basis on which this harness ever asserts it."""
    fixture = _load("student_0001_above_gate_convergent.json")
    report = parity_check.check_student_parity(fixture)

    assert report["schoology_value_is_display_rounded"] is False
    assert report["comparison_basis"] == parity_check._COMPARISON_BASIS_FULL_PRECISION
    assert report["delta"] == pytest.approx(0.0, abs=1e-6)
    assert report["divergent"] is False
    assert report["underlying_convergence_established"] is True
    assert "CONVERGENT" in report["note"]


def test_same_underlying_values_without_the_flag_are_still_divergent():
    """The SAME fixture, same numbers -- but schoology_value_is_display_rounded left at
    its default False. The comparison basis is the ordinary full-precision one, and the
    (tiny but real) difference is reported divergent -- exactly as when the flag is
    declared True (see test_display_rounded_declaration_never_changes_the_divergence_
    verdict below): the flag has NO effect on the divergence verdict, ever."""
    fixture = _load("student_0006_display_rounding_only_difference.json")
    report = parity_check.check_student_parity(fixture)  # flag defaults to False

    assert report["schoology_value_is_display_rounded"] is False
    assert report["comparison_basis"] == parity_check._COMPARISON_BASIS_FULL_PRECISION
    assert report["delta"] == pytest.approx(0.03, abs=1e-4)
    assert report["underlying_convergence_established"] is False
    assert report["divergent"] is True
    assert "DIVERGENT" in report["note"]


def test_display_rounded_declaration_never_changes_the_divergence_verdict():
    """C2 (HIGH), required test 4 (discrimination proof): the SAME fixture's divergence
    verdict must be IDENTICAL whether or not schoology_value_is_display_rounded is
    declared -- proving no code path can turn a raw divergence into divergent=False by
    virtue of that flag. Under the pre-fix implementation this test FAILS: the
    declared-True call reported divergent=False (forgiven) while the declared-False call
    reported divergent=True on the exact same numbers."""
    fixture = _load("student_0006_display_rounding_only_difference.json")
    declared = parity_check.check_student_parity(fixture, schoology_value_is_display_rounded=True)
    undeclared = parity_check.check_student_parity(fixture, schoology_value_is_display_rounded=False)

    assert declared["delta"] == pytest.approx(undeclared["delta"])
    assert declared["divergent"] is True
    assert undeclared["divergent"] is True
    assert declared["divergent"] == undeclared["divergent"]
    # Only the basis-describing fields differ -- never the divergence verdict itself.
    assert declared["comparison_basis"] != undeclared["comparison_basis"]
    assert declared["underlying_convergence_established"] is False
    assert undeclared["underlying_convergence_established"] is False


def test_display_rounded_flag_does_not_forgive_a_genuinely_large_divergence():
    """C2 (HIGH), required test 3: declaring schoology_value_is_display_rounded=True on a
    fixture with a genuinely large gap (student 0002, delta > 15 points) must NOT forgive
    it -- a real divergence is flagged divergent regardless of the declared basis."""
    fixture = _load("student_0002_above_gate_divergent.json")
    report = parity_check.check_student_parity(fixture, schoology_value_is_display_rounded=True)

    assert report["schoology_value_is_display_rounded"] is True
    assert report["comparison_basis"] == parity_check._COMPARISON_BASIS_DISPLAY_ROUNDED
    assert report["underlying_convergence_established"] is False
    assert report["divergent"] is True
    assert "DIVERGENT" in report["note"]


def test_display_rounded_basis_never_asserts_convergence_even_on_an_exact_numeric_match():
    """The strongest form of "never declare underlying convergence from a display-rounded
    observation": even when the observed figures match EXACTLY (delta ~ 0), a comparison
    explicitly declared display-rounded must still NOT claim underlying convergence -- a
    rounded observation matching by chance never proves the underlying figures agree."""
    fixture = _load("student_0001_above_gate_convergent.json")
    report = parity_check.check_student_parity(fixture, schoology_value_is_display_rounded=True)

    assert report["delta"] == pytest.approx(0.0, abs=1e-6)
    assert report["divergent"] is False  # no evidence of a numeric problem was found...
    assert report["underlying_convergence_established"] is False  # ...but convergence is still NOT asserted.
    assert report["comparison_basis"] == parity_check._COMPARISON_BASIS_DISPLAY_ROUNDED
    assert "CONVERGENT" not in report["note"]
    assert "NOT CONVERGED" in report["note"]


def test_rounding_only_difference_helper_is_deleted():
    """C2 (HIGH), required test 4: the forgiveness helper itself must no longer exist on
    the module -- proves the old forgiveness path is structurally gone, not merely
    unreachable/dead code left behind."""
    assert not hasattr(parity_check, "_rounding_only_difference")


def test_no_forgiveness_report_field_survives():
    """The old rounding_only_difference report field (a forgiveness signal) is gone
    entirely, replaced by comparison_basis / underlying_convergence_established, which
    are purely descriptive and never suppress divergent."""
    fixture = _load("student_0006_display_rounding_only_difference.json")
    report = parity_check.check_student_parity(fixture, schoology_value_is_display_rounded=True)
    assert "rounding_only_difference" not in report
    assert "comparison_basis" in report
    assert "underlying_convergence_established" in report


# ----------------------------------------------------------------------------------
# OPEN-16 (RESOLVED by RC 2026-07-24): zero denominator / no fabricated zero. No
# eligible designated work/participation/assessment evidence => completion/WORK/
# ASSESSMENT/quarter grade all UNKNOWN, and the Schoology projector never fabricates a
# synthetic zero-valued assignment to force a grade into being computable.
# ----------------------------------------------------------------------------------

def test_zero_denominator_all_unknown_student_reconciles_as_unknown_never_forced_to_a_number():
    fixture = _load("student_0005_zero_denominator_no_eligible_evidence.json")
    report = parity_check.check_student_parity(fixture)

    assert report["completion_pct"] is None
    assert report["work_aggregate"] == parity_check.UNKNOWN
    assert report["assessment_aggregate"] == parity_check.UNKNOWN
    assert report["a2_expected_quarter_grade"] == parity_check.UNKNOWN
    assert report["a2_expected_quarter_grade"] != 0
    assert report["a2_expected_quarter_grade"] != 0.0
    # Schoology's native figure ALSO lands on UNKNOWN -- its own possible-points
    # denominator is 0 (no evidence was posted at all) -- never a fabricated 0%/100%.
    assert report["schoology_native_quarter_grade"] == parity_check.UNKNOWN
    # UNKNOWN is ALWAYS surfaced for RC review, even when BOTH sides agree it's UNKNOWN --
    # it is never treated as "nothing to reconcile."
    assert report["divergent"] is True


def test_project_course_never_fabricates_a_synthetic_zero_valued_assignment():
    """The projector only ever emits assignment records that trace back to a real
    catalog entry (lesson_id/artifact_type/artifact_id) -- it must never invent a
    synthetic zero-scored/zero-points assignment purely to make some downstream ratio
    computable (OPEN-16, RESOLVED; contract's zero_denominator_rule/no_fabricated_zero)."""
    catalog = parity_check.load_course_catalog()
    projected = parity_check.project_course(catalog)
    catalog_keys = {
        parity_check.external_key(catalog["course_id"], e["lesson_id"], e["artifact_type"], e["artifact_id"])
        for e in catalog["lessons"]
    }
    assert len(projected) > 0
    for record in projected:
        # Every projected record traces to a REAL catalog entry -- nothing invented.
        assert record["external_key"] in catalog_keys
        # No fabricated zero-points placeholder assignment.
        assert record["points_possible"] > 0.0


def test_compute_schoology_native_grade_on_entirely_empty_evidence_is_unknown_not_zero():
    """An entirely-empty fixture (no evidence of any kind) must make the Schoology-native
    figure UNKNOWN (zero possible-points denominator) -- never a fabricated 0%."""
    catalog = parity_check.load_course_catalog()
    published_records = {r["external_key"]: r for r in parity_check.project_course(catalog)}
    empty_fixture = {
        "student_id": "SYNTHETIC-STUDENT-TEST-EMPTY",
        "packet_assignments": [], "participation_assignments": [], "extra_credit_assignments": [],
        "quiz_assignments": [], "topic_assessment_assignments": [],
    }
    native = parity_check.compute_schoology_native_grade(catalog["course_id"], published_records, empty_fixture)
    assert native == parity_check.UNKNOWN
    assert native != 0
    assert native != 0.0


# ----------------------------------------------------------------------------------
# Defensive import of grading_policy_ref.py -- reused when present, skips/xfails
# cleanly when absent (it is owned by a parallel NT15 workstream).
# ----------------------------------------------------------------------------------

def test_grading_policy_ref_import_is_defensive_for_a_missing_path():
    """Simulate the "absent" branch WITHOUT touching the real sibling file: point the
    loader at a path that doesn't exist and confirm it degrades to None, not an exception."""
    missing_path = HERE / "does_not_exist_grading_policy_ref.py"
    assert not missing_path.exists()
    assert parity_check._load_grading_policy_ref(missing_path) is None


def test_local_fallback_formula_agrees_with_grading_policy_ref_when_both_available():
    """When grading_policy_ref.py IS present at runtime, sanity-check that
    parity_check's local fallback formula (used only when the sibling is absent)
    computes the SAME numbers on a representative case -- they must never silently
    diverge from each other, since both claim to implement the identical PREF-03 formula."""
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip(
            "grading_policy_ref.py not present at runtime (parallel NT15 workstream); "
            "parity_check falls back to its local PREF-03 formula reimplementation, "
            "which is exercised directly by the other tests in this module."
        )
    cases = [
        (80.0, 95.0, 0.75),
        (80.0, 90.0, 0.10),
        (60.0, 99.0, 0.40),  # inclusive boundary
    ]
    for work, assessment, completion in cases:
        ref_result = parity_check._from_ref_value(
            parity_check.GRADING_POLICY_REF.compute_quarter_grade(work, assessment, completion)
        )
        local_result = parity_check._local_compute_quarter_grade(work, assessment, completion)
        assert ref_result == pytest.approx(local_result)


def test_parity_check_actually_reuses_grading_policy_ref_module_when_present():
    """Confirms this is a genuine integration, not just a same-shaped coincidence:
    monkeypatch-free -- if the sibling module is present, GRADING_POLICY_REF must be
    the real imported module object exposing its documented public functions."""
    if parity_check.GRADING_POLICY_REF is None:
        pytest.skip("grading_policy_ref.py not present at runtime (parallel NT15 workstream).")
    assert hasattr(parity_check.GRADING_POLICY_REF, "compute_quarter_grade")
    assert hasattr(parity_check.GRADING_POLICY_REF, "compute_work_aggregate")
    assert hasattr(parity_check.GRADING_POLICY_REF, "compute_assessment_aggregate")
    assert hasattr(parity_check.GRADING_POLICY_REF, "compute_component_percentage")
    assert hasattr(parity_check.GRADING_POLICY_REF, "UNKNOWN")


# ----------------------------------------------------------------------------------
# Idempotency: re-projection converges; no duplicate assignments.
# ----------------------------------------------------------------------------------

def test_project_course_is_idempotent_and_produces_no_duplicates():
    catalog = parity_check.load_course_catalog()

    run_1 = parity_check.project_course(catalog)
    run_2 = parity_check.project_course(catalog)

    assert run_1 == run_2, "re-projecting identical input must converge to identical output"

    keys_1 = [r["external_key"] for r in run_1]
    assert len(keys_1) == len(set(keys_1)), "no duplicate external keys within a single projection run"

    # Simulate "create-or-update" across two runs via merge_projection: the merged size
    # must equal a single run's size -- running the projector twice never grows the set.
    merged_once = parity_check.merge_projection({}, run_1)
    merged_twice = parity_check.merge_projection(merged_once, run_2)
    assert len(merged_twice) == len(merged_once) == len(run_1)
    assert merged_twice == merged_once


def test_project_course_gates_on_canonical_lesson_states():
    catalog = parity_check.load_course_catalog()
    projected = parity_check.project_course(catalog)
    projected_lesson_ids = {r["external_key"].split(":")[2] for r in projected}

    # Released / today / topic-assessment entries ARE projected.
    assert "4-3" in projected_lesson_ids
    assert "4-4" in projected_lesson_ids
    assert "TOPIC-4-ASSESSMENT" in projected_lesson_ids

    # Unreleased (4-5) and optional-catalog-not-explicitly-assigned (4-1) are NOT
    # projected -- mirrors PREF-01 and CLAUDE.md's 4-1 optional-catalog policy.
    assert "4-5" not in projected_lesson_ids
    assert "4-1" not in projected_lesson_ids

    total_catalog_entries = len(catalog["lessons"])
    assert len(projected) < total_catalog_entries


def test_optional_catalog_lesson_is_projected_only_when_explicitly_assigned():
    catalog = parity_check.load_course_catalog()
    # Find the 4-1 optional-catalog entry and flip explicitly_assigned on a COPY --
    # this test must not mutate the on-disk fixture (loaded fresh each call anyway).
    entry_4_1 = next(e for e in catalog["lessons"] if e["lesson_id"] == "4-1")
    assert entry_4_1["lesson_state"] == "optional-catalog"
    assert parity_check._should_project(entry_4_1) is False

    assigned_copy = dict(entry_4_1)
    assigned_copy["explicitly_assigned"] = True
    assert parity_check._should_project(assigned_copy) is True


def test_temporarily_unavailable_lesson_is_still_projected_never_retracted():
    """Unavailability alone must never retract or hide already-projected work
    (PROGRAM_DOSSIER.md §15 item 2)."""
    entry = {
        "lesson_id": "4-9", "topic": "4-9", "lesson_state": "temporarily-unavailable",
        "artifact_type": "lesson_packet_work", "artifact_id": "packet",
        "schoology_category": "WORK", "points_possible": 100.0, "extra_credit": False,
    }
    assert parity_check._should_project(entry) is True


# ----------------------------------------------------------------------------------
# B1 fix (Codex SOL review R-B, HIGH): fail-closed release gating + the REAL NT14
# `availability` marker (qb.py; record nt14-ingest-4-1-2026-07-23). The pre-fix
# `_should_project` did `entry.get("lesson_state", "released")` -- a missing/unrecognized
# state silently defaulted to the permissive "released" and got projected -- and never
# consulted `availability` at all, so a permissive lesson_state could bypass the real
# optional-catalog marker entirely. Each test below asserts the CORRECT (post-fix) answer.
# Running these against the pre-fix code makes every assertion fail EXCEPT
# test_b1_garbage_lesson_state_without_marker_is_not_projected, which is explicitly
# non-discriminating (see its docstring and the fixture file's top-level _comment for why).
# ----------------------------------------------------------------------------------

def _load_b1_catalog() -> dict:
    return _load("course_catalog_nt14_b1_edge_cases.json")


def _b1_entry(catalog: dict, artifact_id: str) -> dict:
    return next(e for e in catalog["lessons"] if e["artifact_id"] == artifact_id)


def test_b1_raw_nt14_row_without_explicit_assignment_is_not_projected():
    """Raw NT14 registry-row shape (real availability marker, NO lesson_state field at
    all, not explicitly assigned) must NOT be projected. DISCRIMINATES: pre-fix code
    defaults the missing lesson_state to 'released' and projects it anyway."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "b1-raw-not-assigned")
    assert "lesson_state" not in entry
    assert entry["availability"] == "optional-catalog"
    assert parity_check._should_project(entry) is False


def test_b1_explicit_assignment_overrides_conflicting_restrictive_lesson_state():
    """Explicit teacher assignment on an availability-marked record projects it even
    when an explicit, restrictive lesson_state ('unreleased') is ALSO present --
    explicit assignment is the sole gate once availability flags optional-catalog.
    DISCRIMINATES: pre-fix code hits the NEVER_PROJECT_STATES branch for 'unreleased'
    and returns False without ever consulting explicitly_assigned or availability."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "b1-explicit-assignment-overrides-restrictive-state")
    assert entry["lesson_state"] == "unreleased"
    assert entry["availability"] == "optional-catalog"
    assert entry["explicitly_assigned"] is True
    assert parity_check._should_project(entry) is True


def test_b1_missing_lesson_state_fails_closed():
    """An ordinary record (no availability marker) simply missing its lesson_state field
    must NOT be projected -- unknown state is not permission. DISCRIMINATES: pre-fix code
    defaults to 'released' and projects it anyway."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "b1-missing-state-plain")
    assert "lesson_state" not in entry
    assert "availability" not in entry
    assert parity_check._should_project(entry) is False


def test_b1_garbage_lesson_state_without_marker_is_not_projected():
    """Present-but-unrecognized lesson_state, no availability marker, must NOT be
    projected. NOTE -- does NOT discriminate pre/post fix on its own: the pre-fix code's
    final whitelist-membership check already correctly rejects any present, non-matching
    string; the actual pre-fix bug was narrowly the MISSING-key default plus never
    consulting `availability`. Included as correctness coverage for the fixed fail-closed
    behavior, not claimed as proof of the fix -- see
    test_b1_garbage_lesson_state_with_marker_and_explicit_assignment_is_still_projected
    below for the discriminating garbage-state case."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "b1-garbage-state-plain")
    assert entry["lesson_state"] == "banana"
    assert "availability" not in entry
    assert parity_check._should_project(entry) is False


def test_b1_conflicting_marker_vs_permissive_lesson_state_resolves_restrictively():
    """A permissive lesson_state ('released') can never override the real availability
    marker when no explicit assignment has been given -- the restrictive reading wins.
    DISCRIMINATES: pre-fix code never looks at availability, sees 'released', and
    projects it anyway."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "b1-conflict-not-assigned")
    assert entry["lesson_state"] == "released"
    assert entry["availability"] == "optional-catalog"
    assert entry["explicitly_assigned"] is False
    assert parity_check._should_project(entry) is False


def test_b1_garbage_lesson_state_with_marker_and_explicit_assignment_is_still_projected():
    """Even a garbage/unrecognized lesson_state does not block projection once the real
    availability marker is present AND the teacher has explicitly assigned it.
    DISCRIMINATES: pre-fix code sees 'banana', falls through every branch to the final
    whitelist check, and returns False without ever consulting availability or
    explicitly_assigned."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "b1-garbage-state-with-marker-assigned")
    assert entry["lesson_state"] == "banana"
    assert entry["availability"] == "optional-catalog"
    assert entry["explicitly_assigned"] is True
    assert parity_check._should_project(entry) is True


def test_b1_project_course_end_to_end_over_the_edge_case_catalog():
    """Integration check: running the real project_course() over the whole B1+R2
    edge-case catalog produces exactly the two entries that should be projected (the
    explicit teacher assignments) and excludes every other entry -- including all six
    R2 malformed-value entries added below."""
    catalog = _load_b1_catalog()
    projected = parity_check.project_course(catalog)
    projected_artifact_ids = {r["external_key"].split(":")[-1] for r in projected}
    assert projected_artifact_ids == {
        "b1-explicit-assignment-overrides-restrictive-state",
        "b1-garbage-state-with-marker-assigned",
    }


# ----------------------------------------------------------------------------------
# R2 fix (Codex SOL review R-B, HIGH, residual): two holes survived the B1 fix --
# (1) `bool(entry.get("explicitly_assigned", False))` treats any non-empty string
# (including the string "false") as truthy, and (2) a present-but-malformed
# `availability` value fell through to a permissive `lesson_state`. Each test below
# asserts the CORRECT (post-fix) answer -- NOT projected in every case. Running these
# against the exact pre-fix `_should_project` (the `bool(...)` line intact, no
# availability-mismatch handling) makes every assertion fail EXCEPT
# test_r2_explicitly_assigned_int_0_is_not_projected, which is explicitly
# non-discriminating (see its docstring for why).
# ----------------------------------------------------------------------------------

def test_r2_explicitly_assigned_string_false_is_not_projected():
    """explicitly_assigned serialized as the STRING 'false' must NOT be projected --
    only the Python bool True counts; a truthy-but-non-bool string is a
    type/serialization anomaly, never coerced. DISCRIMINATES: pre-fix `bool("false")`
    is True (any non-empty string is truthy) -> old code incorrectly projects it."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "r2-explicitly-assigned-string-false")
    assert entry["explicitly_assigned"] == "false"
    assert isinstance(entry["explicitly_assigned"], str)
    assert parity_check._should_project(entry) is False


def test_r2_explicitly_assigned_string_true_is_not_projected():
    """explicitly_assigned serialized as the STRING 'true' must NOT be projected --
    only the literal Python bool True counts, never a stringified look-alike.
    DISCRIMINATES: pre-fix `bool("true")` is True, so old code projects it purely by
    coincidence of the string's content, not by any real type check."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "r2-explicitly-assigned-string-true")
    assert entry["explicitly_assigned"] == "true"
    assert isinstance(entry["explicitly_assigned"], str)
    assert parity_check._should_project(entry) is False


def test_r2_explicitly_assigned_int_1_is_not_projected():
    """explicitly_assigned serialized as the int 1 must NOT be projected -- `1 is True`
    is False in Python (bool and int are distinct types). DISCRIMINATES: pre-fix
    `bool(1)` is True -> old code incorrectly projects it."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "r2-explicitly-assigned-int-1")
    assert entry["explicitly_assigned"] == 1
    assert entry["explicitly_assigned"] is not True
    assert parity_check._should_project(entry) is False


def test_r2_explicitly_assigned_int_0_is_not_projected():
    """explicitly_assigned serialized as the int 0 must NOT be projected -- only a
    literal bool False (or an absent key) counts as 'not assigned'; int 0 is still a
    non-bool type anomaly under the strict identity check. NOTE -- does NOT
    discriminate pre/post fix on its own: `bool(0)` is already False under the
    pre-fix code (0 is falsy), so old code happens to reject it too, for the wrong
    reason (blind truthiness, not a real type/identity check). Included as legitimate
    regression coverage for the new strict-identity convention, not claimed as proof
    of the fix -- see test_r2_explicitly_assigned_int_1_is_not_projected and the
    string-value tests above for the discriminating cases in this same family."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "r2-explicitly-assigned-int-0")
    assert entry["explicitly_assigned"] == 0
    assert entry["explicitly_assigned"] is not False
    assert parity_check._should_project(entry) is False


def test_r2_availability_case_variant_is_not_projected():
    """A case-variant availability value ('Optional-Catalog') paired with a permissive
    lesson_state ('released') must NOT be projected -- a present-but-unrecognized
    availability value fails closed unconditionally, before lesson_state is ever
    consulted, and must never fall through to the permissive state. DISCRIMINATES:
    pre-fix code's case-sensitive exact-match on availability fails silently, falls
    through to lesson_state='released', and old code incorrectly projects it."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "r2-availability-case-variant")
    assert entry["availability"] == "Optional-Catalog"
    assert entry["lesson_state"] == "released"
    assert parity_check._should_project(entry) is False


def test_r2_availability_garbage_value_is_not_projected():
    """A garbage availability value paired with a permissive lesson_state ('released')
    must NOT be projected -- same reasoning as the case-variant test. DISCRIMINATES:
    pre-fix code falls through to lesson_state='released' and incorrectly projects it."""
    catalog = _load_b1_catalog()
    entry = _b1_entry(catalog, "r2-availability-garbage")
    assert entry["availability"] == "maybe-optional-catalog-ish"
    assert entry["lesson_state"] == "released"
    assert parity_check._should_project(entry) is False


def test_r2_malformed_records_are_surfaced_as_anomalies_never_silently_dropped():
    """Every R2 malformed record must appear in detect_projection_anomalies() --
    fail closed AND surfaced, never silently unpublished (contract §8)."""
    catalog = _load_b1_catalog()
    anomalies = parity_check.detect_projection_anomalies(catalog)
    anomaly_artifact_ids = {a["external_key"].split(":")[-1] for a in anomalies}
    assert anomaly_artifact_ids == {
        "r2-explicitly-assigned-string-false",
        "r2-explicitly-assigned-string-true",
        "r2-explicitly-assigned-int-1",
        "r2-explicitly-assigned-int-0",
        "r2-availability-case-variant",
        "r2-availability-garbage",
    }
    for a in anomalies:
        assert a["projected"] is False
        assert a["field"] in ("explicitly_assigned", "availability")
        assert a["reason"]  # non-empty, human-readable


def test_r2_normal_non_projection_is_never_flagged_as_an_anomaly():
    """Routine, NORMAL non-projection (unreleased, skipped, or optional-catalog not yet
    explicitly assigned) must NOT appear in detect_projection_anomalies() -- only
    genuinely malformed records are anomalies; a legitimately-not-yet-assigned record
    is not a data problem."""
    catalog = _load_b1_catalog()
    anomalies = parity_check.detect_projection_anomalies(catalog)
    anomaly_artifact_ids = {a["external_key"].split(":")[-1] for a in anomalies}
    assert "b1-raw-not-assigned" not in anomaly_artifact_ids
    assert "b1-conflict-not-assigned" not in anomaly_artifact_ids
    assert "b1-missing-state-plain" not in anomaly_artifact_ids
    assert "b1-garbage-state-plain" not in anomaly_artifact_ids


# ----------------------------------------------------------------------------------
# Deep-link templates produce stable links for the same lesson identity.
# ----------------------------------------------------------------------------------

def test_deep_link_is_stable_across_repeated_projection_for_the_same_lesson():
    catalog = parity_check.load_course_catalog()
    run_1 = {r["external_key"]: r for r in parity_check.project_course(catalog)}
    run_2 = {r["external_key"]: r for r in parity_check.project_course(catalog)}

    key = parity_check.external_key("SYNTHETIC-COURSE-0001", "4-3", "lesson_packet_work", "packet")
    assert key in run_1 and key in run_2
    assert run_1[key]["deep_link"] == run_2[key]["deep_link"]
    assert run_1[key]["deep_link"]["a2_activity_key"] == "a2://a2-synthetic-algebra2/4-3/4-3/lesson_packet_work/packet"


def test_deep_link_differs_for_different_lesson_identities():
    catalog = parity_check.load_course_catalog()
    projected = {r["external_key"]: r for r in parity_check.project_course(catalog)}

    key_43 = parity_check.external_key("SYNTHETIC-COURSE-0001", "4-3", "lesson_packet_work", "packet")
    key_44 = parity_check.external_key("SYNTHETIC-COURSE-0001", "4-4", "lesson_packet_work", "packet")
    assert projected[key_43]["deep_link"]["a2_activity_key"] != projected[key_44]["deep_link"]["a2_activity_key"]


def test_deep_link_schoology_template_never_fabricates_a_real_course_or_assignment_id():
    catalog = parity_check.load_course_catalog()
    projected = parity_check.project_course(catalog)
    for record in projected:
        template = record["deep_link"]["schoology_url_template"]
        # The Schoology-side identifiers are unresolved placeholders -- they must
        # remain literal template tokens, never a concrete invented Schoology id.
        assert "{schoology_domain}" in template
        assert "{schoology_course_id}" in template
        assert "{schoology_assignment_id}" in template


# ----------------------------------------------------------------------------------
# Open-item declaration regression guard (Codex SOL review R-B, finding A2, extended for
# NT16): OPEN-15 and OPEN-19 (this contract's own dependencies, now RESOLVED by RC
# 2026-07-24) and OPEN-16 (newly encoded by this tranche) must all still be findable in
# the machine-readable contract -- resolved items keep their id with resolution
# provenance, they are never silently deleted.
# ----------------------------------------------------------------------------------

def test_json_contract_declares_resolved_open_15_16_19():
    contract_json = json.loads((HERE / "schoology_projection.v2.json").read_text(encoding="utf-8"))
    assert "OPEN-15" in contract_json["resolved_open_item_ids"]
    assert "OPEN-16" in contract_json["resolved_open_item_ids"]
    assert "OPEN-19" in contract_json["resolved_open_item_ids"]
    for open_id in ("OPEN-15", "OPEN-16", "OPEN-19"):
        assert contract_json["resolved_open_items"][open_id]["status"] == "RESOLVED"
        assert contract_json["resolved_open_items"][open_id]["provenance"] == "RESOLVED by RC 2026-07-24"
    # OPEN-04 remains genuinely open, unaffected by this tranche's rulings.
    assert contract_json["open_item_ids"] == ["OPEN-04"]


def test_contract_markdown_cites_open_15_16_19():
    contract_md = (HERE / "SCHOOLOGY_PROJECTION_CONTRACT.md").read_text(encoding="utf-8")
    assert "OPEN-15" in contract_md
    assert "OPEN-16" in contract_md
    assert "OPEN-19" in contract_md


# ----------------------------------------------------------------------------------
# R5/R6 documentation completeness (Codex SOL review R-B, LOW): the computation mode
# must be named in the JSON's report_fields and prose, and ASSUMPTION-3 (referenced by
# parity_check.py) must have an actual numbered definition in the contract, not just a
# code comment pointing at a definition that was never written.
# ----------------------------------------------------------------------------------

def test_json_declares_schoology_computation_mode_in_report_fields_and_names_the_value():
    contract_json = json.loads((HERE / "schoology_projection.v2.json").read_text(encoding="utf-8"))
    assert "schoology_computation_mode" in contract_json["divergence_handling"]["report_fields"]
    # C2 fix (HIGH, RESOLVED 2026-07-24): rounding_only_difference (a forgiveness signal)
    # is gone, replaced by comparison_basis / underlying_convergence_established.
    assert "rounding_only_difference" not in contract_json["divergence_handling"]["report_fields"]
    assert "comparison_basis" in contract_json["divergence_handling"]["report_fields"]
    assert "underlying_convergence_established" in contract_json["divergence_handling"]["report_fields"]
    assert "schoology_value_is_display_rounded" in contract_json["divergence_handling"]["report_fields"]
    assert contract_json["schoology_native_computation"]["mode"] == "flat_total_points"
    assert "future_mode_rule" in contract_json["schoology_native_computation"]


def test_contract_markdown_defines_assumption_3_by_name():
    contract_md = (HERE / "SCHOOLOGY_PROJECTION_CONTRACT.md").read_text(encoding="utf-8")
    assert "Assumption to confirm (ASSUMPTION-3)" in contract_md
    assert "flat_total_points" in contract_md


def test_json_declares_zero_denominator_rule_and_rounding_awareness():
    """Machine-readable coverage for the two rulings this D3 tranche encodes directly:
    OPEN-16's no-fabricated-zero rule and OPEN-09's rounding-awareness rule."""
    contract_json = json.loads((HERE / "schoology_projection.v2.json").read_text(encoding="utf-8"))
    assert "zero_denominator_rule" in contract_json
    assert "no_fabricated_zero" in contract_json["zero_denominator_rule"]
    assert "rounding_awareness" in contract_json
    assert contract_json["rounding_awareness"]["source"] == "OPEN-09, RESOLVED by RC 2026-07-24"
    # C2 fix (HIGH, RESOLVED 2026-07-24): the rounding_awareness block's own
    # report_fields_added list must match reality -- no forgiveness field survives.
    added_fields = contract_json["rounding_awareness"]["report_fields_added"]
    assert "rounding_only_difference" not in added_fields
    assert "comparison_basis" in added_fields
    assert "underlying_convergence_established" in added_fields


def test_contract_markdown_never_says_reproduce_the_intended_result():
    """That phrase belongs only in D1 -- never in D3."""
    contract_md = (HERE / "SCHOOLOGY_PROJECTION_CONTRACT.md").read_text(encoding="utf-8")
    assert "reproduce the intended result" not in contract_md
