"""
test_rc_rulings_acceptance.py -- NT16 work package F: the consolidated RC-rulings
acceptance-proof suite (NT15 product-policy).

Package: NT15 product-policy · Version: 2.0 · Date: 2026-07-24
Source of authority: RC final decisions, 2026-07-24 (Grok preference interview + RC
clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
Status: Authoritative -- gates all future Desk / grading / Schoology implementation.

WHAT THIS MODULE IS
--------------------
RC issued nine rulings on 2026-07-24 resolving OPEN-08, 09, 10, 11, 15, 16, 17, 18, and
19. Each ruling already has deep regression coverage spread across
test_grading_policy_ref.py (D2), test_parity_check.py (D3), test_desk_state_model.py
(D4), and test_policy_package.py's own cross-document guards -- this module does not
replace or weaken any of that coverage.

What none of those suites provides is a SINGLE, small, explicitly-numbered file a
reviewer can read start to finish to confirm every one of the nine rulings is
discriminatingly proven -- not merely exercised incidentally as one assertion among
many hundreds spread across four files. That is this module's whole job: exactly
THIRTEEN named acceptance proofs (`test_proof_01_...` through `test_proof_13_...`),
each docstring-quoting the specific ruling it proves and that ruling's OPEN-NN id, each
grouped under a section comment naming the ruling(s) it belongs to.

Every proof CALLS the real reference implementation (grading_policy_ref.py /
parity_check.py) or READS the real machine-readable artifact (desk_state_model.v2.json)
and the real synthetic fixtures under fixtures/schoology/ -- never a re-implementation
of the formula under test compared against itself. Every numeric assertion carries an
explicit expected value with a tolerance (pytest.approx with a stated rel/abs), computed
independently of the code path under test, never merely recomputed from it.

Codex review remediation (2026-07-24) -- C1, C2, C3, C4, C5. A second Codex review pass
found defects in the IMPLEMENTATION of already-RESOLVED rulings (see grading_policy_ref.py
and parity_check.py's own module docstrings for the full defect/fix history). This module
is updated to match: proof 13 is REWRITTEN (the old "tolerates display rounding" reading
was itself the C2 defect -- reconciliation is UNDERLYING-ONLY, and rounding never forgives
a real difference); proofs 01/02 are strengthened for C1 (the exact-integer-cross-product
completion gate, exercised through the ORDINARY compute_quarter_grade(w, a,
compute_completion(c, n)) calling sequence); proof 04 is strengthened for C3 (authorization
by membership, not by which parameter the caller used); proof 12 is extended for C4 (the
ASSESSMENT ceiling enforced at the reducer); proof 03 is extended for C5 (the display
rounding mode is a labeled implementation reading, not a silent invention).

Hermetic: standard library + pytest only. No network. Every file this suite reads lives
inside product-policy/, located via pathlib.Path(__file__).parent.

Run: python -m pytest test_rc_rulings_acceptance.py -q   (from product-policy/)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import grading_policy_ref as gpr
import parity_check

HERE = Path(__file__).resolve().parent
FIXTURES_DIR = HERE / "fixtures" / "schoology"
DESK_MODEL_PATH = HERE / "desk_state_model.v2.json"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def desk_model() -> dict:
    return json.loads(DESK_MODEL_PATH.read_text(encoding="utf-8"))


# =========================================================================================
# OPEN-08 -- exact-ratio branch selection, no pre-rounding before the 0.40 gate.
# =========================================================================================


def test_proof_01_branch_selection_uses_the_exact_ratio_with_no_pre_rounding():
    """OPEN-08 (RESOLVED by RC 2026-07-24): "Compare the EXACT completion ratio against
    the inclusive 0.40 threshold. No pre-rounding before branch selection."

    39/100 (0.39, strictly below 0.40) must take the BELOW-threshold AVERAGE branch;
    40/100 (0.40, exactly at the inclusive threshold) must take the AT/ABOVE-threshold
    MAX branch. The completion ratio fed into compute_quarter_grade below is the exact
    value compute_completion returned -- not a re-typed literal -- so this proof also
    confirms no rounding sneaks in between the two calls.

    C1 (HIGH, Codex review 2026-07-24) strengthening: `compute_completion` now returns a
    `CompletionRatio` -- a `float` SUBCLASS carrying the exact completed_count/
    assigned_count it was computed from -- rather than a bare float. This proof also
    confirms (a) that subclass is still a genuine `float` (isinstance) and round-trips
    through `float()` to the same value, so no existing caller of a bare float is broken;
    and (b) the gate stays exact even at extreme counts where the FLOAT ratio itself is
    exactly 0.40 by construction (40000000000000000/100000000000000000, precisely 2/5) --
    the inclusive MAX branch must still fire through the ORDINARY two-call sequence every
    real caller writes: compute_quarter_grade(w, a, compute_completion(c, n)).

    V1 (HIGH, Codex re-check 2026-07-24) accuracy correction: the exactness guarantee
    demonstrated here holds for the PRISTINE `CompletionRatio` object itself (or for
    explicit `completed_count=`/`assigned_count=` kwargs) -- it does NOT hold once that
    object has been coerced, rounded, copied, or serialized into a bare float, which
    discards its carried counts entirely (see `CompletionRatio`'s docstring). This pair
    happens to have no representation error at this scale to begin with, so degrading it
    below does not flip the branch -- proof 02 below is the discriminating case where
    degrading the ADVERSARIAL pair does flip the branch. The assertion below exists only
    to confirm the degradation itself is real (a plain `float`, not a `CompletionRatio`),
    not to claim it produces a wrong answer here.
    """
    completion_39 = gpr.compute_completion(39, 100)
    completion_40 = gpr.compute_completion(40, 100)

    # The exact ratios that must reach compute_quarter_grade's comparison.
    assert completion_39 == 0.39
    assert completion_40 == 0.40

    # C1: the CompletionRatio subclass must behave as a genuine float everywhere -- no
    # consumer that only expects a bare float can be broken by the subclass.
    assert isinstance(completion_39, float)
    assert isinstance(completion_40, float)
    assert float(completion_39) == 0.39, "CompletionRatio must round-trip through float()"
    assert float(completion_40) == 0.40, "CompletionRatio must round-trip through float()"

    work_aggregate = 80.0
    assessment_aggregate = 60.0
    expected_average = 70.0  # (80.0 + 60.0) / 2.0
    expected_max = 80.0  # max(80.0, 60.0)

    below_threshold_result = gpr.compute_quarter_grade(work_aggregate, assessment_aggregate, completion_39)
    at_threshold_result = gpr.compute_quarter_grade(work_aggregate, assessment_aggregate, completion_40)

    assert below_threshold_result == pytest.approx(expected_average, rel=1e-9), (
        "39/100 (0.39) must take the AVERAGE branch (below the 0.40 gate)"
    )
    assert at_threshold_result == pytest.approx(expected_max, rel=1e-9), (
        "40/100 (0.40) must take the MAX branch (inclusive at exactly the 0.40 gate)"
    )

    # C1 (HIGH): a large-count pair that is EXACTLY 2/5 (40000000000000000 * 5 ==
    # 100000000000000000 * 2 -- no representation error at all, unlike the adversarial
    # pair in proof 02) must still take the inclusive MAX branch through the ORDINARY
    # two-call sequence -- the exactness fix must not have swapped one collapse for
    # another right at the boundary itself.
    exact_large_completion = gpr.compute_completion(40_000_000_000_000_000, 100_000_000_000_000_000)
    assert float(exact_large_completion) == 0.4
    exact_large_result = gpr.compute_quarter_grade(work_aggregate, assessment_aggregate, exact_large_completion)
    assert exact_large_result == pytest.approx(expected_max, rel=1e-9), (
        "40000000000000000/100000000000000000 is EXACTLY 2/5 -- the inclusive gate must "
        "still select MAX at this scale, via the ordinary compute_quarter_grade(w, a, "
        "compute_completion(c, n)) calling sequence every real caller writes"
    )

    # V1 (HIGH, Codex re-check 2026-07-24): degrading this same ratio to a bare float
    # (e.g. via float()) discards its carried provenance -- confirmed here even though
    # the outcome happens to agree with the exact path for this particular pair (there is
    # no representation error at this scale to begin with). This demonstrates the
    # degradation itself is real; proof 02 below demonstrates it actually flipping the
    # branch for the adversarial pair.
    degraded_exact_large = float(exact_large_completion)
    assert not isinstance(degraded_exact_large, gpr.CompletionRatio)
    degraded_exact_large_result = gpr.compute_quarter_grade(
        work_aggregate, assessment_aggregate, degraded_exact_large
    )
    assert degraded_exact_large_result == pytest.approx(expected_max, rel=1e-9)


def test_proof_02_ratio_just_below_0_40_cannot_round_upward_into_max():
    """OPEN-08 (RESOLVED by RC 2026-07-24): "No pre-rounding before branch selection."

    0.3999999 is strictly below the 0.40 gate, but round(0.3999999, 1) == 0.4 -- so a
    PRE-ROUNDING implementation (round the ratio to one decimal, THEN compare to the
    gate) would incorrectly take the MAX branch here. This proof asserts BOTH that the
    would-be-wrong pre-rounded value is 0.4, AND that the real implementation still
    takes the AVERAGE branch -- proving the exact ratio, not a rounded stand-in, is what
    actually reaches compute_quarter_grade's comparison. That second assertion is what
    makes this proof discriminating rather than incidental.

    C1 (HIGH, Codex review 2026-07-24) strengthening: a RELATED but distinct defect can
    put the wrong ratio in front of the gate with no rounding FUNCTION involved at all --
    for sufficiently large completed_count/assigned_count pairs, the binary FLOAT ratio
    itself can collapse to exactly 0.40 even though the true rational value is strictly
    below it. completed_count=40000000000000000, assigned_count=100000000000000001 is
    mathematically just BELOW 2/5 (5*completed_count = 200000000000000000 <
    2*assigned_count = 200000000000000002), yet completed_count/assigned_count AS A FLOAT
    equals exactly 0.4. This proof asserts the float genuinely collapses to 0.4, then
    asserts the ORDINARY two-call sequence -- compute_quarter_grade(w, a,
    compute_completion(completed_count, assigned_count)) -- still takes the AVERAGE
    branch, proving compute_quarter_grade decides the gate from the CompletionRatio's
    carried exact integer counts, never from the lossy float value itself.

    V1 (HIGH, Codex re-check 2026-07-24) strengthening: the exactness guarantee just
    proved holds for the PRISTINE `CompletionRatio` object (or for explicit
    `completed_count=`/`assigned_count=` kwargs) -- it does NOT hold for a value that has
    been coerced into a bare float, which discards the carried counts. This proof's final
    section degrades the SAME adversarial ratio via `float()` and confirms the branch
    actually flips to MAX -- the documented, boundary-imprecise tier-3 fallback this
    package now discloses everywhere (CompletionRatio's docstring,
    GRADING_POLICY_SPEC.md, grading_policy.v2.json), not a silent wrong answer nobody
    warned about.

    Pre-branch rounding proof (NT16-B): a value can be legitimately rounded UP to 0.4 by
    `round_final_grade_for_display` -- e.g. `round_final_grade_for_display(0.3999999) ==
    0.4` is true under BOTH half-up and half-even, since 0.3999999 is far from any tie --
    while `compute_quarter_grade` must still treat the same 0.3999999 as strictly BELOW
    the 0.40 gate and take the AVERAGE branch. This proves display rounding is never
    consulted before the branch decision, not merely that no rounding FUNCTION happens to
    be named in the branch-selection code path.
    """
    ratio = gpr.compute_completion(3999999, 10000000)
    assert ratio == 0.3999999
    assert ratio < gpr.COMPLETION_THRESHOLD

    # The discriminating assertion: a pre-rounding implementation would have seen 0.4
    # (at/above the inclusive gate) and wrongly taken the MAX branch here.
    assert round(ratio, 1) == 0.4

    work_aggregate = 80.0
    assessment_aggregate = 60.0
    expected_average = 70.0  # (80.0 + 60.0) / 2.0

    result = gpr.compute_quarter_grade(work_aggregate, assessment_aggregate, ratio)
    assert result == pytest.approx(expected_average, rel=1e-9), (
        "0.3999999 must still take the AVERAGE branch -- the exact ratio, not "
        "round(ratio, 1), is what compute_quarter_grade compares against the 0.40 gate"
    )

    # C1 (HIGH): the adversarial large-count pair whose FLOAT ratio collapses to exactly
    # 0.40 even though the true rational value is strictly below 2/5.
    adversarial_completed_count = 40_000_000_000_000_000
    adversarial_assigned_count = 100_000_000_000_000_001
    assert 5 * adversarial_completed_count < 2 * adversarial_assigned_count, (
        "the adversarial pair must be mathematically strictly BELOW 2/5 -- this is the "
        "premise the rest of this proof depends on"
    )
    adversarial_completion = gpr.compute_completion(adversarial_completed_count, adversarial_assigned_count)
    assert float(adversarial_completion) == 0.4, (
        "the float ratio must genuinely collapse to exactly 0.4 here -- this is the real, "
        "demonstrated representation-error defect C1 fixes, not a hypothetical"
    )

    adversarial_result = gpr.compute_quarter_grade(work_aggregate, assessment_aggregate, adversarial_completion)
    assert adversarial_result == pytest.approx(expected_average, rel=1e-9), (
        "the adversarial pair is truly below the 0.40 gate and must take the AVERAGE "
        "branch (70.0) -- reverting the exact-integer-cross-product gate back to a float "
        "comparison of `completion` against COMPLETION_THRESHOLD would wrongly select MAX "
        "(80.0) here instead, because the float ratio itself equals exactly 0.4"
    )

    # V1 (HIGH, Codex re-check 2026-07-24): the exactness guarantee just proved is
    # SPECIFIC to the pristine CompletionRatio -- it does not extend to a value that has
    # been coerced into a bare float. Degrading the SAME adversarial ratio via float()
    # (an operation earlier docs called perfectly safe) discards its carried counts, and
    # the gate falls back to comparing the collapsed 0.4 float directly against the
    # threshold -- wrongly selecting MAX here. This is the documented tier-3 fallback,
    # not a silent wrong answer: it is real, and every artifact this package ships now
    # discloses it (see CompletionRatio's docstring, GRADING_POLICY_SPEC.md's "V1
    # hardening" section, and grading_policy.v2.json's quarter_rule.
    # gate_decision_from_counts).
    degraded_adversarial_completion = float(adversarial_completion)
    assert not isinstance(degraded_adversarial_completion, gpr.CompletionRatio), (
        "float() must actually strip the CompletionRatio provenance for this to be a "
        "meaningful demonstration of the fallback tier"
    )
    degraded_adversarial_result = gpr.compute_quarter_grade(
        work_aggregate, assessment_aggregate, degraded_adversarial_completion
    )
    assert degraded_adversarial_result == pytest.approx(max(work_aggregate, assessment_aggregate), rel=1e-9), (
        "a degraded (bare-float) adversarial ratio falls back to tier 3 and wrongly "
        "selects MAX (80.0) here -- this is the documented, disclosed fallback behavior, "
        "not an undiscovered bug, and this assertion is what keeps that documented "
        "behavior honest rather than aspirational"
    )

    # Pre-branch rounding proof (NT16-B): round_final_grade_for_display(0.3999999) == 0.4
    # is true under BOTH half-up and half-even (0.3999999 is nowhere near a tie), yet
    # compute_quarter_grade must still take the AVERAGE branch for the SAME 0.3999999 --
    # proving display rounding is never applied before the 0.40 branch decision, not just
    # that no rounding call happens to appear in the gate's own source line.
    assert gpr.round_final_grade_for_display(0.3999999) == pytest.approx(0.4, rel=1e-9), (
        "0.3999999 legitimately displays as 0.4 -- this alone is not evidence of a "
        "pre-rounding defect; what matters is the branch decision below"
    )
    pre_branch_result = gpr.compute_quarter_grade(work_aggregate, assessment_aggregate, 0.3999999)
    assert pre_branch_result == pytest.approx(expected_average, rel=1e-9), (
        "compute_quarter_grade(..., completion=0.3999999) must still take the AVERAGE "
        "branch (70.0) even though round_final_grade_for_display(0.3999999) == 0.4 -- "
        "display rounding is never consulted before the 40% branch decision"
    )


# =========================================================================================
# OPEN-09 -- internal full precision is distinct from student-facing display rounding.
# =========================================================================================


def test_proof_03_internal_precision_is_distinct_from_display_rounding():
    """OPEN-09 (RESOLVED by RC 2026-07-24): "Full precision internally. Round ONLY the
    student-facing final-grade DISPLAY to one decimal."

    Constructs a quarter grade whose full-precision internal value and one-decimal
    display value genuinely differ (95.54455445544555 vs 95.5), and asserts: the
    internal value retains full precision, the display value is the rounded one-decimal
    form, and the two are NOT equal to each other.

    C5 (MEDIUM, Codex review 2026-07-24) / AMENDMENT (RC 2026-07-24, NT16-B, a later
    same-day ruling): RC's OPEN-09 ruling fixed "one decimal" but originally never
    specified the tie-breaking MODE. This package FIRST labeled
    `round_final_grade_for_display`'s Python-`round` half-even ("banker's rounding")
    behavior as an implementation reading pending RC confirmation, not itself a ruling
    (the same "do not invent silently" discipline used for OPEN-11's excused/unknown
    reading). RC has SINCE directly ruled on the mode; her verbatim amendment is "Use
    conventional decimal ROUND_HALF_UP for the student-facing one-decimal display.
    Example: 89.25 -> 89.3. Do not use Python binary-float round() or half-even behavior
    for the display contract." This proof asserts the HALF-UP behavior the amendment
    requires -- including RC's own 89.25 -> 89.3 example, with an explicit divergence
    check against Python's builtin `round` so a silent regression back to half-even
    cannot pass unnoticed -- AND that grading_policy.v2.json's label now names half-up
    with the amendment's provenance.
    """
    work_aggregate = gpr.compute_work_aggregate(190, 200, 2, 2, 1.0)
    assessment_aggregate = 50.0
    completion = 0.90  # above the 0.40 gate -> MAX branch, and work_aggregate wins it

    quarter_grade = gpr.compute_quarter_grade(work_aggregate, assessment_aggregate, completion)
    display_value = gpr.round_final_grade_for_display(quarter_grade)
    display_string = gpr.final_grade_display_string(quarter_grade)

    assert quarter_grade == pytest.approx(95.54455445544555, rel=1e-9), (
        "the internal quarter grade must retain full precision"
    )
    assert display_value == pytest.approx(95.5, rel=1e-9), (
        "the display value must be rounded to one decimal"
    )
    assert display_string == "95.5"
    assert quarter_grade != display_value, (
        "the full-precision internal value and the rounded display value must genuinely differ"
    )

    # AMENDMENT (RC 2026-07-24, NT16-B): RC's own worked example is the strongest
    # discriminating witness -- Python's builtin round(89.25, 1) == 89.2 (half-even),
    # while decimal ROUND_HALF_UP gives 89.3. Asserting both the new value AND its
    # divergence from builtin round() guards against a silent regression to the old mode.
    assert gpr.round_final_grade_for_display(89.25) == pytest.approx(89.3, rel=1e-9), (
        "RC's amendment: half-up rounds 89.25 UP to 89.3, not down to the even 89.2"
    )
    assert round(89.25, 1) == pytest.approx(89.2, rel=1e-9), (
        "sanity check on the discriminating premise: Python's builtin round is half-even "
        "and gives 89.2 here, which is why 89.25 -> 89.3 actually proves half-up is active"
    )
    assert gpr.round_final_grade_for_display(89.25) != round(89.25, 1), (
        "round_final_grade_for_display(89.25) must diverge from Python's builtin "
        "round(89.25, 1) -- if it ever matches, this function silently regressed to "
        "half-even (or plain builtin round)"
    )

    # A second discriminating witness at a different magnitude.
    assert gpr.round_final_grade_for_display(0.25) == pytest.approx(0.3, rel=1e-9), (
        "half-up: 0.25 rounds UP to 0.3, not down to the even 0.2"
    )
    assert gpr.round_final_grade_for_display(0.25) != round(0.25, 1), (
        "round_final_grade_for_display(0.25) must diverge from builtin round(0.25, 1) "
        "(0.2, half-even) -- otherwise this is not actually exercising half-up"
    )

    # 0.35 is NOT an exact binary midpoint (as a float it is
    # 0.34999999999999997779...), so it does NOT discriminate half-up from half-even --
    # both modes round it DOWN to 0.3. This remains a valid regression pin (it would
    # still catch an unrelated defect, e.g. a wrong decimals exponent) but it is NOT
    # evidence of which rounding mode is active, and must never be cited as such.
    assert gpr.round_final_grade_for_display(0.35) == pytest.approx(0.3, rel=1e-9), (
        "0.35 is not an exact binary midpoint (its float value is strictly below 0.35), "
        "so both half-up and half-even round it down to 0.3 here -- this value does not "
        "distinguish the two modes"
    )

    # grading_policy.v2.json's label must now name half-up, with the amendment's
    # provenance -- never silently presented as if the mode were still an unconfirmed
    # implementation guess.
    policy_json = json.loads((HERE / "grading_policy.v2.json").read_text(encoding="utf-8"))
    display_rounding_mode = policy_json["rounding_rules"]["display_rounding_mode"]
    assert "half-up" in display_rounding_mode.lower(), (
        "grading_policy.v2.json's rounding_rules.display_rounding_mode must name "
        "half-up explicitly"
    )
    assert "amended by rc 2026-07-24" in display_rounding_mode.lower(), (
        "grading_policy.v2.json's rounding_rules.display_rounding_mode must disclose "
        "RC's 2026-07-24 amendment provenance for the rounding mode"
    )


# =========================================================================================
# OPEN-10 -- unconditional +1.0/student/class-day extra-credit cap.
# =========================================================================================


def test_proof_04_ti84_and_equation_lab_cap_at_plus_1_0_per_day(monkeypatch):
    """OPEN-10 (RESOLVED by RC 2026-07-24): "+1.0 point per student per class day cap
    for currently-authorized extra credit (TI-84 +0.5, Equation Lab +0.5, stacking
    allowed). Any FUTURE extra-credit source requires a new policy decision -- it never
    silently exceeds the cap."

    C3 (HIGH, Codex review 2026-07-24) strengthening: authorization is decided by
    MEMBERSHIP in AUTHORIZED_EXTRA_CREDIT_SOURCES, never by which parameter the caller
    used. This proof also asserts: (a) an AUTHORIZED id ("ti84") supplied through the
    generic `additional_sources` channel contributes the normal +0.5 and STACKS up to the
    same 1.0 cap exactly like the dedicated flags would; and (b) an UNAUTHORIZED id
    ALWAYS raises PolicyDecisionRequiredError, even when an unrelated flag
    (`ti84_completed`) is UNKNOWN -- the pre-C3 defect let the UNKNOWN short-circuit run
    BEFORE the authorization check, so this call would have silently returned UNKNOWN
    instead of raising.
    """
    stacked = gpr.compute_extra_credit(ti84_completed=True, equation_lab_completed=True)
    assert stacked == 1.0
    assert stacked == gpr.EXTRA_CREDIT_DAILY_CAP_POINTS == 1.0

    # C3 (HIGH): an authorized id reaching this function through the GENERIC channel
    # (rather than its dedicated boolean flag) must contribute exactly like the flag
    # would -- authorization is by membership, never by which parameter was used. Checked
    # BEFORE the TI84_EXTRA_CREDIT_POINTS/EQUATION_LAB_EXTRA_CREDIT_POINTS monkeypatch
    # below, so these assertions compare against the real +0.5 constants, not the
    # deliberately-bumped 0.8 test values used for the cap-binding check further down.
    generic_ti84_only = gpr.compute_extra_credit(additional_sources=["ti84"])
    assert generic_ti84_only == pytest.approx(0.5, rel=1e-9), (
        "additional_sources=['ti84'] is an AUTHORIZED source and must contribute +0.5, "
        "exactly as ti84_completed=True would -- it must NOT raise "
        "PolicyDecisionRequiredError merely for arriving through the generic channel"
    )
    generic_stacked = gpr.compute_extra_credit(additional_sources=["ti84", "equation_lab"])
    assert generic_stacked == pytest.approx(1.0, rel=1e-9)
    assert generic_stacked == pytest.approx(gpr.EXTRA_CREDIT_DAILY_CAP_POINTS, rel=1e-9), (
        "two authorized sources arriving via the generic channel must stack up to the "
        "same 1.0 cap as the dedicated flags"
    )

    # C3 (HIGH), the discriminating assertion: an UNAUTHORIZED id must ALWAYS raise
    # PolicyDecisionRequiredError, even when an UNRELATED flag is UNKNOWN. The pre-C3
    # defect let the UNKNOWN short-circuit run FIRST, so this call would have silently
    # returned UNKNOWN instead of raising -- reintroducing that ordering would make this
    # `pytest.raises` block fail to see the expected exception.
    with pytest.raises(gpr.PolicyDecisionRequiredError):
        gpr.compute_extra_credit(ti84_completed=gpr.UNKNOWN, additional_sources=["bonus_worksheet"])

    # Prove the 1.0 is the CAP actually binding -- not an accident of the two 0.5-point
    # sources happening to sum to exactly 1.0: bump each source's per-completion value
    # past the cap and confirm the stacked total is still clipped to the cap, not to the
    # (now-larger) raw sum.
    monkeypatch.setattr(gpr, "TI84_EXTRA_CREDIT_POINTS", 0.8)
    monkeypatch.setattr(gpr, "EQUATION_LAB_EXTRA_CREDIT_POINTS", 0.8)
    stacked_bumped = gpr.compute_extra_credit(ti84_completed=True, equation_lab_completed=True)
    assert stacked_bumped == gpr.EXTRA_CREDIT_DAILY_CAP_POINTS == 1.0
    assert stacked_bumped < 0.8 + 0.8, "the raw stacked sum (1.6) must NOT be what is returned"

    with pytest.raises(gpr.PolicyDecisionRequiredError):
        gpr.compute_extra_credit(ti84_completed=True, additional_sources=["bonus_worksheet"])


# =========================================================================================
# OPEN-11 -- non-class / partial / absent / uncertain-attendance days never auto-zero.
# =========================================================================================


def test_proof_05_non_class_partial_absent_and_uncertain_days_never_auto_zero():
    """OPEN-11 (RESOLVED by RC 2026-07-24): "Non-class days are EXCLUDED from the
    participation requirement. Partial/absent/uncertain attendance NEVER auto-zeroes --
    such days are excused/unknown unless RC explicitly designates the day
    participation-eligible. UNKNOWN is distinct from zero."

    Four cases, the last one the contrast that makes this discriminating rather than
    incidental: a genuinely PRESENT day with no valid response IS legitimately 0 out of
    1 -- it is only the non-class/excused/uncertain days that must never collapse to a
    plain zero.
    """
    non_class_day = gpr.compute_participation_day(False, is_class_day=False)
    assert non_class_day.earned == 0.0
    assert non_class_day.possible == 0.0
    assert non_class_day.status == "excluded_non_class_day"

    excused_absent_day = gpr.compute_participation_day(False, attendance="absent")
    assert excused_absent_day.earned == 0.0
    assert excused_absent_day.possible == 0.0  # NOT 0-out-of-1
    assert excused_absent_day.status == "excused_not_participation_eligible"

    uncertain_attendance_day = gpr.compute_participation_day(True, attendance="unknown")
    assert uncertain_attendance_day.earned is gpr.UNKNOWN
    assert uncertain_attendance_day.possible is gpr.UNKNOWN
    assert uncertain_attendance_day.status == "unknown"

    # Contrast: a PRESENT day with no valid response IS legitimately 0 out of 1 -- this
    # is what makes the excused/excluded/unknown cases above discriminating, not merely
    # "everything with a falsy response is zero."
    present_no_response_day = gpr.compute_participation_day(False, attendance="present")
    assert present_no_response_day.earned == 0.0
    assert present_no_response_day.possible == 1.0
    assert present_no_response_day.status == "counted"


# =========================================================================================
# OPEN-15 -- WORK is point-based (combined earned/possible), never percentage-plus-points.
# =========================================================================================


def test_proof_06_work_uses_combined_earned_possible_not_percentage_plus_points():
    """OPEN-15 (RESOLVED by RC 2026-07-24): "WORK = 100 * (packet_points_earned +
    participation_points_earned + extra_credit_points_earned) /
    (packet_points_possible + participation_points_possible) ... NEVER add a percentage
    directly to raw flat points."

    packet 190/200, participation 2/2, extra credit 1.0. The superseded v1.0
    plain-addition placeholder (packet PERCENTAGE 95.0 + participation raw points 2.0 +
    extra credit points 1.0) landed on 98.0; the point-based ratio RC decided lands on a
    different value. This proof asserts the point-based result AND explicitly asserts it
    does NOT equal the superseded addition.
    """
    point_based = gpr.compute_work_aggregate(
        packet_points_earned=190,
        packet_points_possible=200,
        participation_points_earned=2,
        participation_points_possible=2,
        extra_credit_points_earned=1.0,
    )
    superseded_plain_addition = 98.0  # 95.0 (packet %) + 2.0 (participation points) + 1.0 (extra credit)

    assert point_based == pytest.approx(95.54455445544555, rel=1e-9)
    assert point_based != superseded_plain_addition


def test_proof_07_extra_credit_can_push_work_above_100():
    """OPEN-15 (RESOLVED by RC 2026-07-24): "Extra credit raises the numerator but NOT
    the denominator. WORK MAY EXCEED 100."

    A fully-earned 100/100 packet plus 1.0 extra credit (with zero participation
    possible) yields WORK == 101.0 -- above 100 -- and this value is NOT clamped back
    down to 100.
    """
    work_aggregate = gpr.compute_work_aggregate(
        packet_points_earned=100,
        packet_points_possible=100,
        participation_points_earned=0,
        participation_points_possible=0,
        extra_credit_points_earned=1.0,
    )
    assert work_aggregate == pytest.approx(101.0, rel=1e-9)
    assert work_aggregate > 100.0, "WORK must not be clamped at 100"


# =========================================================================================
# OPEN-16 -- zero eligible denominator is UNKNOWN everywhere, never a fabricated zero.
# =========================================================================================


def test_proof_08_zero_denominator_is_unknown_everywhere_never_a_fabricated_zero():
    """OPEN-16 (RESOLVED by RC 2026-07-24): "No eligible designated work/participation
    => completion UNKNOWN, WORK UNKNOWN, quarter grade UNKNOWN. Student-facing display =
    dash / 'not enough evidence', never zero."

    Checks all three grading-engine UNKNOWNs, the student-facing display string, AND
    (via parity_check, reusing the real student_0005 zero-denominator fixture) that the
    Schoology-projection side does not fabricate a zero either.
    """
    completion = gpr.compute_completion(0, 0)
    work_aggregate = gpr.compute_work_aggregate(0, 0, 0, 0, 0)
    quarter_grade = gpr.compute_quarter_grade(gpr.UNKNOWN, gpr.UNKNOWN, gpr.UNKNOWN)

    assert completion is gpr.UNKNOWN
    assert work_aggregate is gpr.UNKNOWN
    assert quarter_grade is gpr.UNKNOWN

    display_string = gpr.final_grade_display_string(gpr.UNKNOWN)
    assert display_string == gpr.UNKNOWN_DISPLAY_TOKEN
    assert display_string != "0"
    assert display_string != "0.0"
    assert gpr.UNKNOWN_DISPLAY_TEXT == "not enough evidence"

    fixture = _load_fixture("student_0005_zero_denominator_no_eligible_evidence.json")
    report = parity_check.check_student_parity(fixture)

    assert report["work_aggregate"] == parity_check.UNKNOWN
    assert report["assessment_aggregate"] == parity_check.UNKNOWN
    assert report["a2_expected_quarter_grade"] == parity_check.UNKNOWN
    assert report["a2_expected_quarter_grade"] != 0
    assert report["a2_expected_quarter_grade"] != 0.0
    assert report["schoology_native_quarter_grade"] == parity_check.UNKNOWN
    assert report["divergent"] is True, (
        "an all-UNKNOWN student must still be surfaced for RC review, never silently "
        "treated as 'nothing to reconcile'"
    )


# =========================================================================================
# OPEN-17 -- `completed` is DECIDED terminal; a retake is an orthogonal affordance.
# =========================================================================================


def test_proof_09_completed_tile_stays_completed_when_a_retake_becomes_available(desk_model):
    """OPEN-17 (RESOLVED by RC 2026-07-24): "completed remains TERMINAL for the lesson
    tile. A retake is an ORTHOGONAL activity/affordance attached to the completed
    lesson -- it never demotes completion, never relocks, never erases history, and
    never alters the grading engine via navigation state. completed keeps ZERO legal
    exit transitions -- this is now DECIDED, not open."
    """
    legal = desk_model["transitions"]["legal"]
    outbound_from_completed = [t for t in legal if t["from"] == "completed"]
    assert outbound_from_completed == [], (
        f"'completed' must have zero outbound entries in transitions.legal, found: "
        f"{[t['id'] for t in outbound_from_completed]}"
    )

    retake = desk_model["retake_affordance"]
    assert retake["demotes_completion"] is False
    assert retake["relocks"] is False
    assert retake["erases_history"] is False
    assert retake["alters_grading_engine_via_navigation_state"] is False
    assert retake["completed_is_terminal"] is True


# =========================================================================================
# OPEN-18 -- teacher-only skip/unskip transitions are legal and pre-completion-guarded;
# students can never initiate a skip, and completed -> skipped stays forbidden.
# =========================================================================================


def test_proof_10_all_authorized_teacher_skip_unskip_transitions_are_legal(desk_model):
    """OPEN-18 (RESOLVED by RC 2026-07-24): "unreleased -> skipped remains legal (T3,
    CONFIRMED). released -> skipped is ALLOWED (T7, promoted to legal). today -> skipped
    is ALLOWED BEFORE COMPLETION (T11, promoted to legal with a machine-readable
    precondition; a completed lesson can never reach skipped). skipped -> released is
    ALLOWED (T12, promoted to legal). skipped -> today is ALLOWED (T13, promoted to
    legal)."
    """
    legal_by_id = {t["id"]: t for t in desk_model["transitions"]["legal"]}
    expected_ids = {"T3", "T7", "T11", "T12", "T13"}
    assert expected_ids <= set(legal_by_id.keys()), (
        f"expected {sorted(expected_ids)} all present in transitions.legal, missing "
        f"{sorted(expected_ids - set(legal_by_id.keys()))}"
    )

    for tid in sorted(expected_ids):
        entry = legal_by_id[tid]
        assert entry.get("normative", True) is not False, f"{tid} must not carry normative: false"
        assert "open_item" not in entry, (
            f"{tid} must not carry a stale open_item marker (found {entry.get('open_item')!r})"
        )

    t11 = legal_by_id["T11"]
    assert "precondition" in t11, "T11 must carry a machine-readable pre-completion precondition"
    precondition = t11["precondition"]
    assert precondition.get("condition") == "lesson_not_yet_completed_for_this_student"
    assert precondition.get("field") == "student_completion_state != 'completed'"


def test_proof_11_student_skip_attempts_and_completed_to_skipped_are_rejected(desk_model):
    """OPEN-18 (RESOLVED by RC 2026-07-24): "completed -> skipped remains FORBIDDEN (X3,
    CONFIRMED). Students cannot initiate skip or unskip -- every skip transition carries
    a teacher-only actor and student_may_initiate: false."
    """
    legal_by_id = {t["id"]: t for t in desk_model["transitions"]["legal"]}
    skip_transition_ids = {"T3", "T7", "T11", "T12", "T13"}

    for tid in sorted(skip_transition_ids):
        entry = legal_by_id[tid]
        assert entry.get("actor") == "teacher_only", f"{tid} must carry actor == 'teacher_only'"
        assert entry.get("student_may_initiate") is False, (
            f"{tid} must carry student_may_initiate == False"
        )

    assert desk_model["skip_authority"].get("student_may_initiate") is False

    illegal = desk_model["transitions"]["illegal"]
    completed_to_skipped_illegal = [
        t for t in illegal if t["from"] == "completed" and t["to"] == "skipped"
    ]
    assert len(completed_to_skipped_illegal) == 1, (
        "transitions.illegal must contain exactly one completed -> skipped entry (X3)"
    )

    legal = desk_model["transitions"]["legal"]
    completed_to_skipped_legal = [
        t for t in legal if t["from"] == "completed" and t["to"] == "skipped"
    ]
    assert completed_to_skipped_legal == [], (
        "completed -> skipped must NEVER appear in transitions.legal"
    )


# =========================================================================================
# OPEN-19 -- point-weighted multi-item reduction, never an unweighted percentage average.
# =========================================================================================


def test_proof_12_point_weighted_reduction_differs_from_unweighted_percentage_average():
    """OPEN-19 (RESOLVED by RC 2026-07-24): "component_percentage =
    100 * sum(current_official_points_earned) / sum(points_possible) ... NEVER
    equal-average assignment percentages when possible-points differ."

    Two items with differing possible-points, [(90, 100), (1, 10)]: the point-weighted
    reduction RC decided (100 * (90+1) / (100+10) = 82.727...) diverges sharply from the
    FORBIDDEN unweighted average of the two per-item percentages ((90% + 10%) / 2 =
    50.0%). This proof asserts the point-weighted result AND explicitly asserts it does
    NOT equal the forbidden unweighted average.

    C4 (HIGH, Codex review 2026-07-24) extension: this proof is extended, rather than
    minting a fourteenth numbered proof, to also cover the ASSESSMENT ceiling defect C4
    fixed -- both are OPEN-19 implementation questions. Before C4,
    `compute_assessment_aggregate([(120, 100)])` returned `120.0`, an out-of-[0, 100]
    value nothing upstream ever caught. This proof asserts that call now raises
    `PolicyDomainError`; that `compute_component_percentage`'s STRICT default
    (`allow_above_100=False`) raises identically for the same over-ceiling item (the
    ceiling is the shared strict default, not a special case bolted onto
    `compute_assessment_aggregate` alone); and that the explicit `allow_above_100=True`
    opt-in (reserved for a WORK-side group where extra credit legitimately lifts earned
    above possible -- never legitimate for ASSESSMENT) still returns the raw 120.0
    unclamped, proving the ceiling is a deliberate default, not an unconditional clamp.
    """
    items = [(90, 100), (1, 10)]
    point_weighted = gpr.compute_component_percentage(items)
    forbidden_unweighted_average = 50.0  # (90.0% + 10.0%) / 2

    assert point_weighted == pytest.approx(82.72727272727273, rel=1e-9)
    assert point_weighted != forbidden_unweighted_average

    # C4 (HIGH): the ASSESSMENT ceiling is enforced at the reducer -- an item whose
    # points_earned exceeds points_possible is a DATA DEFECT for ASSESSMENT, never a
    # silently-passed-through above-100 value.
    over_ceiling_items = [(120, 100)]
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_assessment_aggregate(over_ceiling_items)

    # compute_component_percentage's STRICT default (allow_above_100=False) raises
    # identically for the same over-ceiling item.
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_component_percentage(over_ceiling_items)

    # The explicit, narrow WORK-side opt-in still returns the raw (unclamped) ratio --
    # this is deliberately never exposed by compute_assessment_aggregate itself.
    opted_in_result = gpr.compute_component_percentage(over_ceiling_items, allow_above_100=True)
    assert opted_in_result == pytest.approx(120.0, rel=1e-9)


# =========================================================================================
# OPEN-09 -- reconciliation is UNDERLYING-ONLY; rounding never forgives a real difference
# (C2 fix, Codex review, HIGH, RESOLVED 2026-07-24).
# =========================================================================================


def test_proof_13_reconciliation_never_forgives_a_real_difference_or_claims_convergence_from_rounding():
    """OPEN-09 (RESOLVED by RC 2026-07-24): "Schoology keeps native (unrounded)
    earned/possible totals. Reconciliation compares underlying values consistently and
    must not mistake display rounding for substantive divergence."

    C2 fix (Codex review, HIGH, RESOLVED 2026-07-24) -- this proof is REWRITTEN to match
    the corrected reading. This module's own v2.0-as-first-shipped implementation of the
    ruling above misread "must not mistake display rounding for substantive divergence"
    as PERMISSION TO FORGIVE a real difference whenever
    `schoology_value_is_display_rounded=True` was declared -- `_rounding_only_difference()`
    rounded BOTH figures and silently converted a raw divergence into `divergent: False`.
    That reading was wrong: the ruling bans FALSE ALARMS over cosmetic rounding; it never
    authorizes suppressing a genuine underlying difference. That helper and its
    forgiveness branch are DELETED. The corrected behavior: `divergent` is purely
    `abs(delta) > tolerance`, on EITHER comparison basis, with no exception --
    reconciliation is UNDERLYING-ONLY. `comparison_basis` / `underlying_convergence_established`
    replace the deleted `rounding_only_difference` field: `underlying_convergence_established`
    is `True` ONLY on the full-precision basis with no difference beyond tolerance -- a
    display-rounded OBSERVATION never proves the underlying figures agree, even when the
    observed numbers happen to match.

    Four legs, using check_student_parity over the real fixtures:
      (a) student_0006 (a genuine 0.03 underlying difference) WITH
          schoology_value_is_display_rounded=True declared -> STILL divergent=True;
          comparison_basis names the degraded (display-rounded-observation) basis, and
          underlying_convergence_established is False. THE DISCRIMINATING ASSERTION: if
          the deleted forgiveness path were reintroduced, `divergent` would read False here.
      (b) the SAME fixture WITHOUT the declaration -> the SAME 0.03 gap is STILL
          divergent=True on the ordinary full-precision basis -- rounding buys no
          forgiveness on either basis.
      (c) student_0002 (a genuinely large, real divergence) WITH the declaration -> STILL
          divergent=True -- the flag never blanket-forgives a real difference, of any size.
      (d) student_0001 (a genuinely convergent student, undeclared/full-precision basis)
          -> divergent=False AND underlying_convergence_established=True -- this is the
          ONLY basis on which this harness ever asserts genuine underlying convergence.
      (e) The old forgiveness path is verifiably dead: parity_check carries no
          `_rounding_only_difference` attribute, and no report produced above carries the
          deleted `rounding_only_difference` key.
    """
    rounding_only_fixture = _load_fixture("student_0006_display_rounding_only_difference.json")

    declared_report = parity_check.check_student_parity(
        rounding_only_fixture, schoology_value_is_display_rounded=True
    )
    assert declared_report["a2_expected_quarter_grade"] == pytest.approx(88.03, rel=1e-9)
    assert declared_report["schoology_native_quarter_grade"] == pytest.approx(88.0, rel=1e-9)
    assert declared_report["comparison_basis"] == (
        "display-rounded-observation -- underlying convergence NOT established"
    )
    assert declared_report["underlying_convergence_established"] is False
    assert declared_report["divergent"] is True, (
        "a genuine 0.03 underlying difference must NOT be forgiven just because the "
        "caller declared the Schoology-side figure display-rounded -- the deleted "
        "_rounding_only_difference path would have set this False instead"
    )

    undeclared_report = parity_check.check_student_parity(rounding_only_fixture)
    assert undeclared_report["schoology_value_is_display_rounded"] is False
    assert undeclared_report["comparison_basis"] == "underlying-full-precision"
    assert undeclared_report["underlying_convergence_established"] is False
    assert undeclared_report["divergent"] is True

    large_divergence_fixture = _load_fixture("student_0002_above_gate_divergent.json")
    large_divergence_report = parity_check.check_student_parity(
        large_divergence_fixture, schoology_value_is_display_rounded=True
    )
    assert large_divergence_report["a2_expected_quarter_grade"] == pytest.approx(
        95.54455445544555, rel=1e-9
    )
    assert large_divergence_report["schoology_native_quarter_grade"] == pytest.approx(
        76.89243027888446, rel=1e-9
    )
    assert large_divergence_report["comparison_basis"] == (
        "display-rounded-observation -- underlying convergence NOT established"
    )
    assert large_divergence_report["underlying_convergence_established"] is False
    assert large_divergence_report["divergent"] is True

    convergent_fixture = _load_fixture("student_0001_above_gate_convergent.json")
    convergent_report = parity_check.check_student_parity(convergent_fixture)
    assert convergent_report["a2_expected_quarter_grade"] == pytest.approx(88.0, rel=1e-9)
    assert convergent_report["schoology_native_quarter_grade"] == pytest.approx(88.0, rel=1e-9)
    assert convergent_report["comparison_basis"] == "underlying-full-precision"
    assert convergent_report["divergent"] is False
    assert convergent_report["underlying_convergence_established"] is True, (
        "a genuinely convergent student on the undeclared full-precision basis must reach "
        "True here -- this is the ONLY basis on which this harness ever asserts genuine "
        "underlying convergence"
    )

    # The old forgiveness path is dead, not merely unused: no such attribute on the
    # module, and no report produced above carries the deleted key at all.
    assert not hasattr(parity_check, "_rounding_only_difference"), (
        "parity_check._rounding_only_difference must not exist -- the C2 remediation "
        "deleted the rounding-forgiveness helper entirely"
    )
    for report in (declared_report, undeclared_report, large_divergence_report, convergent_report):
        assert "rounding_only_difference" not in report, (
            "no check_student_parity report may carry the deleted 'rounding_only_difference' "
            "key -- comparison_basis / underlying_convergence_established replace it"
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
