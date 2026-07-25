"""
test_grading_policy_ref.py -- pytest coverage for grading_policy_ref.py (NT15 D2).

Package: NT15 product-policy · Version: 2.0 · Date: 2026-07-24
Source of authority: RC final decisions, 2026-07-24 (Grok preference interview + RC
clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)

Hermetic: no network, no dependency on any repo file outside product-policy/. The JSON
fixture is loaded relative to this file's own directory, same as grading_policy_ref.py does.

Run: python -m pytest test_grading_policy_ref.py -q   (from product-policy/)

NT16 note: this suite covers the v2.0 API in full. It keeps every still-valid v1.0 test
(domain validation, UNKNOWN propagation, override precedence + the R1 ordering fix,
threshold inclusivity) and adds coverage for the seven items RC resolved on 2026-07-24
(OPEN-08, 09, 10, 11, 15, 16, 19). Some v1.0 tests are adapted rather than kept verbatim
where the domain itself changed (e.g. `work_aggregate` and `teacher_override` lose their
`[0, 100]` ceiling under OPEN-15) -- each such adaptation is called out in a comment.
"""

import fractions
import json
import math
from pathlib import Path

import pytest

import grading_policy_ref as gpr


# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

_POLICY_JSON_PATH = Path(__file__).parent / "grading_policy.v2.json"


@pytest.fixture(scope="module")
def policy_json():
    with open(_POLICY_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Quarter rule: both branches
# ---------------------------------------------------------------------------


def test_branch_above_threshold_takes_max():
    result = gpr.compute_quarter_grade(work_aggregate=80.0, assessment_aggregate=95.0, completion=0.75)
    assert result == max(80.0, 95.0) == 95.0


def test_branch_below_threshold_takes_average():
    result = gpr.compute_quarter_grade(work_aggregate=80.0, assessment_aggregate=90.0, completion=0.10)
    assert result == (80.0 + 90.0) / 2.0 == 85.0


def test_branch_above_threshold_max_can_pick_either_aggregate():
    result_work_larger = gpr.compute_quarter_grade(work_aggregate=99.0, assessment_aggregate=60.0, completion=1.0)
    assert result_work_larger == 99.0

    result_assessment_larger = gpr.compute_quarter_grade(work_aggregate=60.0, assessment_aggregate=99.0, completion=1.0)
    assert result_assessment_larger == 99.0


# ---------------------------------------------------------------------------
# OPEN-08 (RESOLVED): exact-ratio comparison, no pre-rounding, ever.
# ---------------------------------------------------------------------------


def test_completion_exactly_at_threshold_is_inclusive_and_takes_max_branch():
    """RC's ruling: compare the EXACT ratio against the inclusive 0.40 gate. Exactly
    0.40 must take the MAX branch, not the average branch."""
    work, assessment = 70.0, 88.0
    result = gpr.compute_quarter_grade(work_aggregate=work, assessment_aggregate=assessment, completion=0.40)
    assert result == max(work, assessment) == 88.0
    assert result != (work + assessment) / 2.0


def test_completion_exactly_at_threshold_via_computed_ratio():
    completion = gpr.compute_completion(2, 5)
    assert completion == 0.40
    work, assessment = 70.0, 88.0
    result = gpr.compute_quarter_grade(work_aggregate=work, assessment_aggregate=assessment, completion=completion)
    assert result == max(work, assessment)


def test_completion_just_below_threshold_takes_average_branch():
    work, assessment = 70.0, 88.0
    result = gpr.compute_quarter_grade(work_aggregate=work, assessment_aggregate=assessment, completion=0.3999)
    assert result == (work + assessment) / 2.0 == 79.0
    assert result != max(work, assessment)


def test_completion_39_of_100_takes_average_39_percent_branch():
    """39/100 = 0.39, just under the 0.40 gate -> average branch."""
    completion = gpr.compute_completion(39, 100)
    assert completion == 0.39
    result = gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=completion)
    assert result == (70.0 + 90.0) / 2.0


def test_completion_40_of_100_takes_max_branch():
    """40/100 = 0.40, exactly the inclusive gate -> max branch."""
    completion = gpr.compute_completion(40, 100)
    assert completion == 0.40
    result = gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=completion)
    assert result == max(70.0, 90.0)


def test_ratio_just_below_threshold_must_not_round_up_to_the_gate():
    """0.399999999 would round to 0.40 at 2+ decimals, which would incorrectly flip the
    branch if any pre-rounding were applied. OPEN-08 forbids that -- the exact ratio must
    still take the average branch."""
    completion = gpr.compute_completion(399999999, 1000000000)
    assert completion < 0.40
    assert round(completion, 2) == 0.40  # sanity: rounding WOULD have crossed the gate
    result = gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=completion)
    assert result == (70.0 + 90.0) / 2.0
    assert result != max(70.0, 90.0)


def test_compute_completion_no_longer_accepts_round_ndigits():
    """v1.0's round_ndigits parameter is REMOVED entirely (OPEN-08)."""
    with pytest.raises(TypeError):
        gpr.compute_completion(2, 5, round_ndigits=2)


def test_compute_quarter_grade_no_longer_accepts_round_ndigits():
    """v1.0's round_ndigits parameter is REMOVED entirely (OPEN-09)."""
    with pytest.raises(TypeError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=0.9, round_ndigits=1)


# ---------------------------------------------------------------------------
# OPEN-09 (RESOLVED): internal full precision vs. display-only rounding.
# ---------------------------------------------------------------------------


def test_internal_result_stays_full_precision_not_rounded():
    completion = gpr.compute_completion(1, 3)  # 0.3333333333333333
    work, assessment = 66.66666666666667, 100.0
    result = gpr.compute_quarter_grade(work_aggregate=work, assessment_aggregate=assessment, completion=completion)
    # below-threshold branch -> average, full precision, NOT rounded to any digit count.
    expected = (work + assessment) / 2.0
    assert result == expected
    assert result != round(expected, 1)


def test_round_final_grade_for_display_rounds_to_one_decimal():
    assert gpr.round_final_grade_for_display(87.449) == 87.4
    assert gpr.round_final_grade_for_display(87.451) == 87.5
    assert gpr.FINAL_GRADE_DISPLAY_DECIMALS == 1


def test_round_final_grade_for_display_passes_unknown_through_unchanged():
    assert gpr.round_final_grade_for_display(gpr.UNKNOWN) is gpr.UNKNOWN
    assert gpr.round_final_grade_for_display(None) is gpr.UNKNOWN


def test_display_rounding_diverges_from_internal_value_but_does_not_mutate_it():
    raw = gpr.compute_quarter_grade(work_aggregate=87.449, assessment_aggregate=10.0, completion=1.0)
    assert raw == 87.449  # internal value: full precision, untouched
    displayed = gpr.round_final_grade_for_display(raw)
    assert displayed == 87.4  # display value: rounded
    assert raw != displayed  # the two must never be conflated


def test_final_grade_display_string_formats_one_decimal():
    assert gpr.final_grade_display_string(87.449) == "87.4"
    assert gpr.final_grade_display_string(100.0) == "100.0"


def test_final_grade_display_string_unknown_is_dash_never_zero():
    assert gpr.final_grade_display_string(gpr.UNKNOWN) == gpr.UNKNOWN_DISPLAY_TOKEN
    assert gpr.final_grade_display_string(None) == gpr.UNKNOWN_DISPLAY_TOKEN
    assert gpr.final_grade_display_string(gpr.UNKNOWN) != "0"
    assert gpr.final_grade_display_string(gpr.UNKNOWN) != "0.0"


# ---------------------------------------------------------------------------
# UNKNOWN propagation
# ---------------------------------------------------------------------------


def test_unknown_completion_yields_unknown_result_not_zero_or_a_branch():
    work, assessment = 70.0, 88.0
    result = gpr.compute_quarter_grade(work_aggregate=work, assessment_aggregate=assessment, completion=gpr.UNKNOWN)
    assert result is gpr.UNKNOWN
    assert result != 0
    assert result != max(work, assessment)
    assert result != (work + assessment) / 2.0


def test_unknown_completion_via_none_also_yields_unknown():
    result = gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=88.0, completion=None)
    assert result is gpr.UNKNOWN


def test_unknown_work_aggregate_yields_unknown_never_zero():
    result = gpr.compute_quarter_grade(work_aggregate=gpr.UNKNOWN, assessment_aggregate=88.0, completion=0.90)
    assert result is gpr.UNKNOWN
    assert result != 0


def test_unknown_assessment_aggregate_yields_unknown_never_zero():
    result = gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=gpr.UNKNOWN, completion=0.10)
    assert result is gpr.UNKNOWN
    assert result != 0


def test_unknown_work_aggregate_below_threshold_also_unknown():
    result = gpr.compute_quarter_grade(work_aggregate=None, assessment_aggregate=88.0, completion=0.05)
    assert result is gpr.UNKNOWN


def test_compute_completion_unknown_inputs():
    assert gpr.compute_completion(gpr.UNKNOWN, 5) is gpr.UNKNOWN
    assert gpr.compute_completion(2, gpr.UNKNOWN) is gpr.UNKNOWN
    assert gpr.compute_completion(None, 5) is gpr.UNKNOWN
    assert gpr.compute_completion(0, 0) is gpr.UNKNOWN


def test_unknown_sentinel_has_no_truth_value():
    with pytest.raises(TypeError):
        bool(gpr.UNKNOWN)


# ---------------------------------------------------------------------------
# Teacher override precedence
# ---------------------------------------------------------------------------


def test_teacher_override_wins_over_computed_max_branch():
    result = gpr.compute_quarter_grade(
        work_aggregate=70.0, assessment_aggregate=95.0, completion=0.90, teacher_override=100.0
    )
    assert result == 100.0
    assert result != max(70.0, 95.0)


def test_teacher_override_wins_over_computed_average_branch():
    result = gpr.compute_quarter_grade(
        work_aggregate=70.0, assessment_aggregate=90.0, completion=0.05, teacher_override=60.0
    )
    assert result == 60.0
    assert result != (70.0 + 90.0) / 2.0


def test_teacher_override_wins_over_unknown_completion():
    result = gpr.compute_quarter_grade(
        work_aggregate=70.0, assessment_aggregate=90.0, completion=gpr.UNKNOWN, teacher_override=82.0
    )
    assert result == 82.0
    assert result is not gpr.UNKNOWN


def test_teacher_override_wins_over_unknown_aggregates():
    result = gpr.compute_quarter_grade(
        work_aggregate=gpr.UNKNOWN, assessment_aggregate=gpr.UNKNOWN, completion=gpr.UNKNOWN, teacher_override=75.0
    )
    assert result == 75.0


def test_no_teacher_override_falls_through_to_computed_value():
    result = gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=0.90)
    assert result == max(70.0, 90.0)


# ---------------------------------------------------------------------------
# R1 (Codex GPT-5.6 SOL review R-A re-check, MEDIUM): a valid teacher override must
# NEVER mask a malformed KNOWN completion/aggregate. Domain validation of every
# supplied value runs before override precedence. Unchanged in v2.0; adapted below only
# where the domain itself changed (work_aggregate/teacher_override lose their [0, 100]
# ceiling under OPEN-15, so their "malformed" example must now be a negative value
# rather than an over-100 one).
# ---------------------------------------------------------------------------


def test_r1_valid_override_does_not_mask_malformed_completion():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=70.0, assessment_aggregate=90.0, completion=1.2, teacher_override=85.0
        )


def test_r1_valid_override_does_not_mask_malformed_assessment_aggregate():
    """assessment_aggregate keeps its [0, 100] domain (PREF-04.5 unaffected by OPEN-15)."""
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=70.0, assessment_aggregate=999.0, completion=0.90, teacher_override=85.0
        )


def test_r1_valid_override_does_not_mask_malformed_negative_work_aggregate():
    """work_aggregate's domain is now non-negative-with-no-upper-bound (OPEN-15); a
    NEGATIVE work_aggregate is what is malformed now, not an over-100 one."""
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=-10.0, assessment_aggregate=90.0, completion=0.90, teacher_override=85.0
        )


def test_r1_valid_override_still_wins_over_unknown_completion():
    result = gpr.compute_quarter_grade(
        work_aggregate=70.0, assessment_aggregate=90.0, completion=gpr.UNKNOWN, teacher_override=85.0
    )
    assert result == 85.0
    assert result is not gpr.UNKNOWN


def test_r1_malformed_override_itself_still_raises():
    """teacher_override's domain is also now unbounded above (OPEN-15); a NEGATIVE
    override is malformed, an above-100 one is not (see
    test_teacher_override_above_100_now_allowed)."""
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=70.0, assessment_aggregate=90.0, completion=0.90, teacher_override=-5.0
        )


# ---------------------------------------------------------------------------
# OPEN-15 (RESOLVED): work_aggregate / teacher_override lose their [0, 100] ceiling.
# ---------------------------------------------------------------------------


def test_work_aggregate_above_100_now_allowed():
    result = gpr.compute_quarter_grade(work_aggregate=150.0, assessment_aggregate=50.0, completion=1.0)
    assert result == 150.0


def test_teacher_override_above_100_now_allowed():
    result = gpr.compute_quarter_grade(
        work_aggregate=70.0, assessment_aggregate=90.0, completion=0.90, teacher_override=150.0
    )
    assert result == 150.0


def test_assessment_aggregate_still_bounded_at_100():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=100.5, completion=0.90)


# ---------------------------------------------------------------------------
# Participation (OPEN-11, RESOLVED): compute_participation_day / ParticipationDay /
# aggregate_participation. Every case in the RC ruling's table.
# ---------------------------------------------------------------------------


def test_compute_participation_point_removed():
    """v1.0's compute_participation_point is REMOVED -- compute_participation_day is
    its OPEN-11-resolved replacement."""
    assert not hasattr(gpr, "compute_participation_point")


def test_participation_non_class_day_is_excluded_zero_zero_regardless_of_attendance():
    for attendance in ("present", "partial", "absent", "unknown"):
        day = gpr.compute_participation_day(True, is_class_day=False, attendance=attendance)
        assert day == gpr.ParticipationDay(0.0, 0.0, "excluded_non_class_day")


def test_participation_present_with_valid_response_counted():
    day = gpr.compute_participation_day(True, attendance="present")
    assert day.earned == gpr.PARTICIPATION_POINT_PRESENT == 1.0
    assert day.possible == 1.0
    assert day.status == "counted"


def test_participation_present_without_valid_response_counted_as_absent_point():
    day = gpr.compute_participation_day(False, attendance="present")
    assert day.earned == gpr.PARTICIPATION_POINT_ABSENT == 0.0
    assert day.possible == 1.0
    assert day.status == "counted"


def test_participation_present_unknown_response_is_unknown_earned_but_known_possible():
    day = gpr.compute_participation_day(gpr.UNKNOWN, attendance="present")
    assert day.earned is gpr.UNKNOWN
    assert day.possible == 1.0
    assert day.status == "unknown"

    day_none = gpr.compute_participation_day(None, attendance="present")
    assert day_none.earned is gpr.UNKNOWN


def test_participation_partial_or_absent_not_eligible_is_excused_zero_zero():
    """NOT an auto-zero: possible is 0.0 too, so it never enters the requirement."""
    for attendance in ("partial", "absent"):
        day = gpr.compute_participation_day(True, attendance=attendance, participation_eligible_designation=False)
        assert day == gpr.ParticipationDay(0.0, 0.0, "excused_not_participation_eligible")


def test_participation_partial_or_absent_eligible_designation_counts_like_present():
    for attendance in ("partial", "absent"):
        day = gpr.compute_participation_day(True, attendance=attendance, participation_eligible_designation=True)
        assert day.earned == gpr.PARTICIPATION_POINT_PRESENT
        assert day.possible == 1.0
        assert day.status == "counted"

        day_absent_response = gpr.compute_participation_day(
            False, attendance=attendance, participation_eligible_designation=True
        )
        assert day_absent_response.earned == gpr.PARTICIPATION_POINT_ABSENT
        assert day_absent_response.possible == 1.0


def test_participation_attendance_unknown_is_unknown_both_fields_regardless_of_designation():
    for designation in (True, False):
        day = gpr.compute_participation_day(True, attendance="unknown", participation_eligible_designation=designation)
        assert day.earned is gpr.UNKNOWN
        assert day.possible is gpr.UNKNOWN
        assert day.status == "unknown"


def test_participation_invalid_attendance_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_participation_day(True, attendance="assembly_day")


def test_participation_excused_and_unknown_never_produce_automatic_zero_rc_bullet_3():
    """Direct coverage for RC's CONFIRMED bullet 3 (2026-07-24): 'Neither case produces
    an automatic participation zero.' An automatic zero would look like `possible ==
    1.0` with `earned == 0.0` -- a counted day the student is being penalized on. This
    test asserts BOTH excused cases (non-class, and partial/absent-not-eligible) land on
    `possible == 0.0` (never 1.0) and BOTH unknown-attendance cases land on UNKNOWN
    (never a numeric 0.0) -- contrasted against the one case that IS legitimately 0/1
    (present with no valid response), which proves these are not merely "everything
    with a falsy response is zero.\""""
    non_class = gpr.compute_participation_day(False, is_class_day=False)
    assert non_class.possible == 0.0 and non_class.possible != 1.0
    assert non_class.earned == 0.0

    excused_partial = gpr.compute_participation_day(True, attendance="partial", participation_eligible_designation=False)
    assert excused_partial.possible == 0.0 and excused_partial.possible != 1.0
    assert excused_partial.earned == 0.0

    excused_absent = gpr.compute_participation_day(False, attendance="absent", participation_eligible_designation=False)
    assert excused_absent.possible == 0.0 and excused_absent.possible != 1.0
    assert excused_absent.earned == 0.0

    unknown_attendance = gpr.compute_participation_day(True, attendance="unknown")
    assert unknown_attendance.earned is gpr.UNKNOWN
    assert unknown_attendance.possible is gpr.UNKNOWN
    assert not (unknown_attendance.earned == 0.0)  # never silently collapses to numeric 0.0

    # Contrast: present-with-no-response IS legitimately 0-earned/1-possible -- proving
    # the excused/unknown cases above are a deliberate exception, not a coincidence of
    # "falsy response always means zero."
    present_no_response = gpr.compute_participation_day(False, attendance="present")
    assert present_no_response.earned == 0.0
    assert present_no_response.possible == 1.0


def test_aggregate_participation_sums_known_days():
    days = [
        gpr.compute_participation_day(True, attendance="present"),   # 1.0 / 1.0
        gpr.compute_participation_day(False, attendance="present"),  # 0.0 / 1.0
        gpr.compute_participation_day(True, is_class_day=False),     # 0.0 / 0.0 (excluded)
        gpr.compute_participation_day(
            True, attendance="partial", participation_eligible_designation=False
        ),                                                            # 0.0 / 0.0 (excused)
    ]
    earned, possible = gpr.aggregate_participation(days)
    assert earned == 1.0
    assert possible == 2.0


def test_aggregate_participation_unknown_response_propagates_to_earned_only():
    days = [
        gpr.compute_participation_day(gpr.UNKNOWN, attendance="present"),  # UNKNOWN / 1.0
        gpr.compute_participation_day(True, attendance="present"),         # 1.0 / 1.0
    ]
    earned, possible = gpr.aggregate_participation(days)
    assert earned is gpr.UNKNOWN
    assert possible == 2.0  # possible side is still fully known


def test_aggregate_participation_unknown_attendance_propagates_to_both_fields():
    days = [
        gpr.compute_participation_day(True, attendance="unknown"),  # UNKNOWN / UNKNOWN
        gpr.compute_participation_day(True, attendance="present"),  # 1.0 / 1.0
    ]
    earned, possible = gpr.aggregate_participation(days)
    assert earned is gpr.UNKNOWN
    assert possible is gpr.UNKNOWN


# ---------------------------------------------------------------------------
# Extra credit (OPEN-10, RESOLVED): unconditional +1.0/day cap, stacking, and
# PolicyDecisionRequiredError for unauthorized sources.
# ---------------------------------------------------------------------------


def test_extra_credit_ti84_only():
    result = gpr.compute_extra_credit(ti84_completed=True, equation_lab_completed=False)
    assert result == 0.5 == gpr.TI84_EXTRA_CREDIT_POINTS


def test_extra_credit_equation_lab_only():
    result = gpr.compute_extra_credit(ti84_completed=False, equation_lab_completed=True)
    assert result == 0.5 == gpr.EQUATION_LAB_EXTRA_CREDIT_POINTS


def test_extra_credit_both_stacked_lands_exactly_at_the_cap():
    result = gpr.compute_extra_credit(ti84_completed=True, equation_lab_completed=True)
    assert result == 1.0 == gpr.EXTRA_CREDIT_DAILY_CAP_POINTS
    assert result == gpr.TI84_EXTRA_CREDIT_POINTS + gpr.EQUATION_LAB_EXTRA_CREDIT_POINTS


def test_extra_credit_none_completed_is_zero():
    result = gpr.compute_extra_credit(ti84_completed=False, equation_lab_completed=False)
    assert result == 0.0


def test_extra_credit_unknown_component_yields_unknown():
    assert gpr.compute_extra_credit(ti84_completed=gpr.UNKNOWN, equation_lab_completed=False) is gpr.UNKNOWN


def test_extra_credit_cap_actually_clips_when_stacked_sum_would_exceed_it(monkeypatch):
    """The 1.0 cap cannot bind under the CURRENT two authorized 0.5 sources (they sum to
    exactly 1.0). To prove the cap is a real, enforced ceiling -- not a no-op -- bump the
    per-source point values past the cap and confirm compute_extra_credit still clips."""
    monkeypatch.setattr(gpr, "TI84_EXTRA_CREDIT_POINTS", 0.8)
    monkeypatch.setattr(gpr, "EQUATION_LAB_EXTRA_CREDIT_POINTS", 0.8)
    result = gpr.compute_extra_credit(ti84_completed=True, equation_lab_completed=True)
    assert result == gpr.EXTRA_CREDIT_DAILY_CAP_POINTS == 1.0
    assert result < 0.8 + 0.8  # the raw stacked sum (1.6) is NOT what is returned


def test_extra_credit_no_longer_accepts_daily_cap_parameter():
    """v1.0's opt-in daily_cap parameter is REMOVED -- the cap is unconditional policy."""
    with pytest.raises(TypeError):
        gpr.compute_extra_credit(ti84_completed=True, daily_cap=5.0)


def test_extra_credit_unauthorized_additional_source_raises_policy_decision_required():
    with pytest.raises(gpr.PolicyDecisionRequiredError):
        gpr.compute_extra_credit(ti84_completed=True, additional_sources=["bonus_worksheet"])


def test_extra_credit_unauthorized_source_error_names_the_source():
    with pytest.raises(gpr.PolicyDecisionRequiredError, match="bonus_worksheet"):
        gpr.compute_extra_credit(additional_sources=["bonus_worksheet"])


def test_extra_credit_empty_additional_sources_does_not_raise():
    """An empty/None additional_sources is not a request for anything unauthorized."""
    result = gpr.compute_extra_credit(ti84_completed=True, additional_sources=[])
    assert result == 0.5
    result_none = gpr.compute_extra_credit(ti84_completed=True, additional_sources=None)
    assert result_none == 0.5


def test_policy_decision_required_error_is_distinct_from_policy_domain_error():
    assert not issubclass(gpr.PolicyDecisionRequiredError, gpr.PolicyDomainError)
    assert not issubclass(gpr.PolicyDomainError, gpr.PolicyDecisionRequiredError)


# ---------------------------------------------------------------------------
# WORK aggregate (OPEN-15, RESOLVED): point-based ratio, replacing v1.0's plain
# three-scalar addition.
# ---------------------------------------------------------------------------


def test_work_aggregate_matches_point_based_formula():
    result = gpr.compute_work_aggregate(
        packet_points_earned=80.0,
        packet_points_possible=100.0,
        participation_points_earned=4.0,
        participation_points_possible=5.0,
        extra_credit_points_earned=1.0,
    )
    expected = 100.0 * (80.0 + 4.0 + 1.0) / (100.0 + 5.0)
    assert result == pytest.approx(expected)


def test_work_aggregate_disagrees_with_the_old_v1_percentage_plus_points_model():
    """v1.0 would have summed a percentage-scale packet SCORE with flat points:
    80.0 (already a percentage) + 4.0 + 1.0 = 85.0. v2.0's point-based ratio over the
    SAME underlying evidence (80/100 packet points, 4/5 participation points, 1.0 extra
    credit) must produce a materially different number, proving this is not just the
    old formula in disguise."""
    v1_style_flat_sum = 80.0 + 4.0 + 1.0  # what v1.0's compute_work_aggregate would have returned
    result = gpr.compute_work_aggregate(
        packet_points_earned=80.0,
        packet_points_possible=100.0,
        participation_points_earned=4.0,
        participation_points_possible=5.0,
        extra_credit_points_earned=1.0,
    )
    assert result != v1_style_flat_sum
    assert result == pytest.approx(100.0 * 85.0 / 105.0)


def test_work_aggregate_extra_credit_can_push_work_above_100():
    result = gpr.compute_work_aggregate(
        packet_points_earned=100.0,
        packet_points_possible=100.0,
        participation_points_earned=5.0,
        participation_points_possible=5.0,
        extra_credit_points_earned=1.0,
    )
    assert result > 100.0
    assert result == pytest.approx(100.0 * 106.0 / 105.0)


def test_work_aggregate_extra_credit_never_enters_the_denominator():
    with_extra_credit = gpr.compute_work_aggregate(50.0, 100.0, 0.0, 0.0, extra_credit_points_earned=1.0)
    without_extra_credit = gpr.compute_work_aggregate(50.0, 100.0, 0.0, 0.0, extra_credit_points_earned=0.0)
    # extra credit raises the numerator only -- denominator (100.0) is unchanged either way.
    assert with_extra_credit - without_extra_credit == pytest.approx(1.0)


def test_work_aggregate_extra_credit_defaults_to_zero():
    result = gpr.compute_work_aggregate(50.0, 100.0, 0.0, 0.0)
    assert result == 50.0


def test_work_aggregate_zero_denominator_is_unknown():
    """OPEN-16: no eligible designated work/participation -> WORK UNKNOWN."""
    result = gpr.compute_work_aggregate(0.0, 0.0, 0.0, 0.0)
    assert result is gpr.UNKNOWN


def test_work_aggregate_propagates_unknown_in_any_of_the_five_inputs():
    base = dict(
        packet_points_earned=80.0,
        packet_points_possible=100.0,
        participation_points_earned=4.0,
        participation_points_possible=5.0,
        extra_credit_points_earned=1.0,
    )
    for key in base:
        kwargs = dict(base)
        kwargs[key] = gpr.UNKNOWN
        assert gpr.compute_work_aggregate(**kwargs) is gpr.UNKNOWN


def test_work_aggregate_no_longer_accepts_v1_signature():
    """v1.0's 3-positional-scalar signature (digital_packet_work_score,
    participation_points, extra_credit_points) is REPLACED; calling with only one
    positional value now fails because packet_points_possible etc. are required."""
    with pytest.raises(TypeError):
        gpr.compute_work_aggregate(75.0)


# ---------------------------------------------------------------------------
# Domain validation: compute_work_aggregate's five inputs.
# ---------------------------------------------------------------------------


def test_work_aggregate_negative_packet_points_earned_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_work_aggregate(-10.0, 100.0, 4.0, 5.0)


def test_work_aggregate_negative_packet_points_possible_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_work_aggregate(80.0, -100.0, 4.0, 5.0)


def test_work_aggregate_negative_participation_points_earned_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_work_aggregate(80.0, 100.0, -4.0, 5.0)


def test_work_aggregate_negative_participation_points_possible_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_work_aggregate(80.0, 100.0, 4.0, -5.0)


def test_work_aggregate_negative_extra_credit_points_earned_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_work_aggregate(80.0, 100.0, 4.0, 5.0, extra_credit_points_earned=-1.0)


def test_work_aggregate_nan_component_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_work_aggregate(float("nan"), 100.0, 4.0, 5.0)


def test_work_aggregate_bool_component_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_work_aggregate(True, 100.0, 4.0, 5.0)


# ---------------------------------------------------------------------------
# Point-weighted component reduction (OPEN-19, RESOLVED).
# ---------------------------------------------------------------------------


def test_component_percentage_matches_point_weighted_formula():
    result = gpr.compute_component_percentage([(9.0, 10.0), (45.0, 50.0)])
    assert result == pytest.approx(100.0 * (9.0 + 45.0) / (10.0 + 50.0))


def test_component_percentage_diverges_from_unweighted_equal_average_when_possible_points_differ():
    """RC's ruling explicitly FORBIDS equal-averaging per-item percentages when
    possible-points differ. A 9/10 item (90%) and a 2/50 item (4%) must reduce to the
    point-weighted 18.3%, NOT the equal average of 47%."""
    items = [(9.0, 10.0), (2.0, 50.0)]
    result = gpr.compute_component_percentage(items)
    point_weighted_expected = 100.0 * (9.0 + 2.0) / (10.0 + 50.0)
    unweighted_equal_average = (100.0 * 9.0 / 10.0 + 100.0 * 2.0 / 50.0) / 2.0
    assert result == pytest.approx(point_weighted_expected)
    assert result != pytest.approx(unweighted_equal_average)
    assert result == pytest.approx(18.333333333333332)
    assert unweighted_equal_average == pytest.approx(47.0)


def test_component_percentage_equal_possible_points_matches_simple_average_incidentally():
    """When every item shares the same possible-points scale, point-weighted and
    equal-averaged percentages coincide -- this is a coincidence of equal weights, not
    evidence that equal-averaging is the rule."""
    items = [(9.0, 10.0), (8.0, 10.0)]
    result = gpr.compute_component_percentage(items)
    assert result == pytest.approx((90.0 + 80.0) / 2.0)


def test_component_percentage_unknown_item_yields_unknown():
    assert gpr.compute_component_percentage([(9.0, 10.0), (gpr.UNKNOWN, 50.0)]) is gpr.UNKNOWN
    assert gpr.compute_component_percentage([(9.0, 10.0), (2.0, gpr.UNKNOWN)]) is gpr.UNKNOWN
    assert gpr.compute_component_percentage([(9.0, 10.0), (None, 50.0)]) is gpr.UNKNOWN


def test_component_percentage_zero_possible_total_is_unknown():
    assert gpr.compute_component_percentage([]) is gpr.UNKNOWN
    assert gpr.compute_component_percentage([(0.0, 0.0), (0.0, 0.0)]) is gpr.UNKNOWN


def test_component_percentage_negative_values_raise_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_component_percentage([(-1.0, 10.0)])
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_component_percentage([(1.0, -10.0)])


def test_assessment_aggregate_uses_the_same_point_weighted_reduction():
    items = [(9.0, 10.0), (2.0, 50.0)]
    assert gpr.compute_assessment_aggregate(items) == pytest.approx(gpr.compute_component_percentage(items))


def test_assessment_aggregate_zero_denominator_is_unknown():
    assert gpr.compute_assessment_aggregate([]) is gpr.UNKNOWN


# ---------------------------------------------------------------------------
# PREF-04.5: participation + extra credit stay WORK-side only.
# ---------------------------------------------------------------------------


def test_extra_credit_and_participation_land_in_work_not_assessment(policy_json):
    participation_day = gpr.compute_participation_day(True, attendance="present")
    earned, possible = gpr.aggregate_participation([participation_day])
    extra_credit = gpr.compute_extra_credit(ti84_completed=True, equation_lab_completed=True)

    work = gpr.compute_work_aggregate(
        packet_points_earned=88.0,
        packet_points_possible=100.0,
        participation_points_earned=earned,
        participation_points_possible=possible,
        extra_credit_points_earned=extra_credit,
    )
    assert work == pytest.approx(100.0 * (88.0 + 1.0 + 1.0) / (100.0 + 1.0))

    work_components = policy_json["aggregates"]["WORK"]["components"]
    assessment_components = policy_json["aggregates"]["ASSESSMENT"]["components"]
    assert "daily_participation_evidence" in work_components
    assert "designated_extra_credit" in work_components
    assert "daily_participation_evidence" not in assessment_components
    assert "designated_extra_credit" not in assessment_components


# ---------------------------------------------------------------------------
# Zero denominator (OPEN-16, RESOLVED): completion / WORK / component / quarter grade /
# display, end to end.
# ---------------------------------------------------------------------------


def test_zero_denominator_completion_is_unknown():
    assert gpr.compute_completion(0, 0) is gpr.UNKNOWN


def test_zero_denominator_work_aggregate_is_unknown():
    assert gpr.compute_work_aggregate(0.0, 0.0, 0.0, 0.0) is gpr.UNKNOWN


def test_zero_denominator_component_percentage_is_unknown():
    assert gpr.compute_component_percentage([]) is gpr.UNKNOWN


def test_zero_denominator_propagates_all_the_way_to_the_quarter_grade_and_display():
    completion = gpr.compute_completion(0, 0)
    work = gpr.compute_work_aggregate(0.0, 0.0, 0.0, 0.0)
    assessment = gpr.compute_assessment_aggregate([])

    assert completion is gpr.UNKNOWN
    assert work is gpr.UNKNOWN
    assert assessment is gpr.UNKNOWN

    quarter_grade = gpr.compute_quarter_grade(work, assessment, completion)
    assert quarter_grade is gpr.UNKNOWN

    assert gpr.final_grade_display_string(quarter_grade) == gpr.UNKNOWN_DISPLAY_TOKEN
    assert gpr.final_grade_display_string(quarter_grade) != "0"
    assert gpr.final_grade_display_string(quarter_grade) != "0.0"


# ---------------------------------------------------------------------------
# Input domain validation: malformed / out-of-domain input FAILS CLOSED (unchanged
# machinery from v1.0, re-verified against the v2.0 surface).
# ---------------------------------------------------------------------------


def test_completed_count_exceeding_assigned_count_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(6, 5)


def test_negative_completed_count_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(-1, 5)


def test_negative_assigned_count_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(1, -5)


def test_quarter_grade_completion_above_one_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=1.5)


def test_quarter_grade_completion_below_zero_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=-0.1)


def test_quarter_grade_negative_work_aggregate_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=-5.0, assessment_aggregate=90.0, completion=0.90)


def test_quarter_grade_over_scale_assessment_aggregate_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=999.0, completion=0.90)


def test_quarter_grade_negative_teacher_override_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=70.0, assessment_aggregate=90.0, completion=0.90, teacher_override=-5.0
        )


def test_completion_nan_completed_count_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(float("nan"), 5)


def test_completion_infinite_assigned_count_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(1, math.inf)


def test_quarter_grade_infinite_completion_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion=math.inf)


def test_quarter_grade_negative_infinite_work_aggregate_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=-math.inf, assessment_aggregate=90.0, completion=0.90)


def test_completion_string_type_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion("6", 5)
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(6, "5")


def test_completion_bool_type_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(True, 5)
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion(2, False)


def test_quarter_grade_string_completion_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completion="0.9")


def test_quarter_grade_bool_teacher_override_raises_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=70.0, assessment_aggregate=90.0, completion=0.90, teacher_override=True
        )


def test_domain_violation_is_never_unknown():
    try:
        gpr.compute_completion(6, 5)
        raised = False
        result = None
    except gpr.PolicyDomainError:
        raised = True
        result = None
    assert raised is True
    assert result is not gpr.UNKNOWN


def test_valid_boundary_values_still_succeed_after_domain_validation():
    assert gpr.compute_quarter_grade(work_aggregate=0.0, assessment_aggregate=100.0, completion=1.0) == 100.0
    assert gpr.compute_quarter_grade(work_aggregate=0.0, assessment_aggregate=0.0, completion=0.0) == 0.0
    assert gpr.compute_completion(0, 5) == 0.0
    assert gpr.compute_completion(5, 5) == 1.0


def test_round_final_grade_for_display_rejects_non_numeric():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.round_final_grade_for_display("87.4")
    with pytest.raises(gpr.PolicyDomainError):
        gpr.round_final_grade_for_display(float("nan"))


# ---------------------------------------------------------------------------
# JSON constants match what the reference implementation actually uses
# ---------------------------------------------------------------------------


def test_json_domains_match_module_validation(policy_json):
    domains = policy_json["domains"]

    assert domains["counts"]["min"] == 0
    assert domains["counts"]["type"] == "non_negative_integer"

    assert domains["completion_ratio"]["min"] == 0
    assert domains["completion_ratio"]["max"] == 1

    assert domains["assessment_percentage_scale_value"]["min"] == 0
    assert domains["assessment_percentage_scale_value"]["max"] == 100

    assert domains["unbounded_non_negative_percentage_value"]["min"] == 0
    assert domains["unbounded_non_negative_percentage_value"]["max"] is None

    assert domains["work_component_points"]["min"] == 0
    assert domains["work_component_points"]["max"] is None

    assert domains["attendance_enum"]["allowed_values"] == ["present", "partial", "absent", "unknown"]


def test_json_declares_policy_domain_error_as_the_exception_type(policy_json):
    assert policy_json["domain_violation_policy"]["exception_type"] == "PolicyDomainError"
    assert gpr.PolicyDomainError.__name__ == "PolicyDomainError"
    assert issubclass(gpr.PolicyDomainError, Exception)


def test_json_declares_policy_decision_required_error_as_the_exception_type(policy_json):
    assert policy_json["policy_decision_required_policy"]["exception_type"] == "PolicyDecisionRequiredError"
    assert gpr.PolicyDecisionRequiredError.__name__ == "PolicyDecisionRequiredError"
    assert issubclass(gpr.PolicyDecisionRequiredError, Exception)


def test_json_constants_match_module_constants(policy_json):
    constants = policy_json["constants"]
    assert gpr.COMPLETION_THRESHOLD == constants["completion_threshold"] == 0.40
    assert gpr.COMPLETION_THRESHOLD_INCLUSIVE == constants["completion_threshold_inclusive"] is True
    assert gpr.PARTICIPATION_POINT_PRESENT == constants["participation_point_per_class_day_present"] == 1.0
    assert gpr.PARTICIPATION_POINT_ABSENT == constants["participation_point_per_class_day_absent"] == 0.0
    assert gpr.TI84_EXTRA_CREDIT_POINTS == constants["ti84_extra_credit_points"] == 0.5
    assert gpr.EQUATION_LAB_EXTRA_CREDIT_POINTS == constants["equation_lab_extra_credit_points"] == 0.5
    assert gpr.EXTRA_CREDIT_DAILY_CAP_POINTS == constants["extra_credit_daily_cap_points"] == 1.0
    assert list(gpr.AUTHORIZED_EXTRA_CREDIT_SOURCES) == constants["authorized_extra_credit_sources"] == ["ti84", "equation_lab"]
    assert gpr.FINAL_GRADE_DISPLAY_DECIMALS == constants["final_grade_display_decimals"] == 1
    assert gpr.UNKNOWN_DISPLAY_TOKEN == constants["unknown_display_token"]
    assert gpr.UNKNOWN_DISPLAY_TEXT == constants["unknown_display_text"] == "not enough evidence"


def test_json_top_level_provenance_keys(policy_json):
    assert policy_json["version"] == "2.0"
    assert policy_json["date"] == "2026-07-24"
    assert policy_json["source_of_authority"] == (
        "RC final decisions 2026-07-24 (Grok preference interview + RC clarifications; "
        "NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)"
    )


def test_json_open_item_ids_is_now_empty(policy_json):
    """All items this policy previously tracked as open are now resolved."""
    assert policy_json["open_item_ids"] == []


def test_json_resolved_open_item_ids_lists_all_seven(policy_json):
    expected = {"OPEN-08", "OPEN-09", "OPEN-10", "OPEN-11", "OPEN-15", "OPEN-16", "OPEN-19"}
    assert set(policy_json["resolved_open_item_ids"]) == expected


def test_json_resolved_open_items_carry_status_and_provenance(policy_json):
    resolved = policy_json["resolved_open_items"]
    expected_ids = {"OPEN-08", "OPEN-09", "OPEN-10", "OPEN-11", "OPEN-15", "OPEN-16", "OPEN-19"}
    assert set(resolved.keys()) == expected_ids
    for item_id, entry in resolved.items():
        assert entry["status"] == "RESOLVED", item_id
        assert entry["provenance"] == "RESOLVED by RC 2026-07-24", item_id
        assert isinstance(entry["ruling"], str) and len(entry["ruling"]) > 0, item_id
        assert isinstance(entry["supersedes"], str) and len(entry["supersedes"]) > 0, item_id


def test_json_no_open_item_identifier_was_deleted(policy_json):
    """OPEN-NN identifiers must never silently disappear -- a resolved item keeps its id
    (in resolved_open_item_ids / resolved_open_items) and gains status + resolution text
    + provenance, rather than vanishing from the document."""
    for item_id in ("OPEN-08", "OPEN-09", "OPEN-10", "OPEN-11", "OPEN-15", "OPEN-16", "OPEN-19"):
        assert item_id in policy_json["resolved_open_item_ids"]
        assert item_id in policy_json["resolved_open_items"]


def test_json_provisional_implementation_choices_block_is_gone(policy_json):
    """Nothing in this policy is provisional anymore -- the v1.0 placeholder block is
    removed, not merely edited to say something new."""
    assert "provisional_implementation_choices" not in policy_json


def test_json_has_a_changelog(policy_json):
    assert "changelog" in policy_json
    assert isinstance(policy_json["changelog"], list)
    assert len(policy_json["changelog"]) >= 1
    assert policy_json["changelog"][0]["version"] == "2.0"


def test_module_loads_policy_from_the_json_file_not_a_hardcoded_copy():
    assert gpr.POLICY["constants"]["completion_threshold"] == gpr.COMPLETION_THRESHOLD
    assert gpr._POLICY_PATH.name == "grading_policy.v2.json"


# ---------------------------------------------------------------------------
# C1 (HIGH, Codex review 2026-07-24): float collapse at the 0.40 gate.
#
# `compute_completion` returns a binary float; comparing that float to
# COMPLETION_THRESHOLD can collapse to exactly 0.40 even when the true rational value is
# strictly below it, for sufficiently large counts. Fixed by an exact integer
# cross-product (`_completion_meets_threshold_exact` / `compute_completion_threshold_met`)
# and, after a peer-review follow-up, by `CompletionRatio` -- a float subclass
# `compute_completion` returns that carries its own exact counts, so the ORDINARY
# `compute_quarter_grade(w, a, compute_completion(c, n))` calling sequence is exact by
# construction and not just the explicit-kwargs style.
# ---------------------------------------------------------------------------

_ADVERSARIAL_COMPLETED_COUNT = 40_000_000_000_000_000
_ADVERSARIAL_ASSIGNED_COUNT = 100_000_000_000_000_001


def test_c1_adversarial_pair_float_ratio_collapses_to_exactly_the_threshold():
    """Sanity check on the defect itself: the exact ratio is strictly below 2/5, yet the
    float `compute_completion` returns collapses to exactly 0.4."""
    assert 5 * _ADVERSARIAL_COMPLETED_COUNT < 2 * _ADVERSARIAL_ASSIGNED_COUNT
    ratio = gpr.compute_completion(_ADVERSARIAL_COMPLETED_COUNT, _ADVERSARIAL_ASSIGNED_COUNT)
    assert ratio == 0.4


def test_c1_adversarial_pair_ordinary_two_call_sequence_takes_average_branch():
    """THE primary C1 discriminating test: the ORDINARY calling sequence every real
    caller writes -- compute the ratio via compute_completion, then pass it straight to
    compute_quarter_grade -- must take the AVERAGE branch for the adversarial pair, not
    the MAX branch a naive float comparison would wrongly select. No explicit
    completed_count=/assigned_count= kwargs are supplied here; the exactness must come
    from the ratio itself (CompletionRatio) carrying its own counts."""
    ratio = gpr.compute_completion(_ADVERSARIAL_COMPLETED_COUNT, _ADVERSARIAL_ASSIGNED_COUNT)
    result = gpr.compute_quarter_grade(80.0, 60.0, ratio)
    assert result == (80.0 + 60.0) / 2.0 == 70.0
    assert result != max(80.0, 60.0)


def test_c1_adversarial_pair_via_explicit_kwargs_takes_average_branch():
    """The same adversarial pair, via the explicit completed_count=/assigned_count=
    kwargs (no completion supplied at all)."""
    result = gpr.compute_quarter_grade(
        work_aggregate=80.0,
        assessment_aggregate=60.0,
        completed_count=_ADVERSARIAL_COMPLETED_COUNT,
        assigned_count=_ADVERSARIAL_ASSIGNED_COUNT,
    )
    assert result == (80.0 + 60.0) / 2.0 == 70.0
    assert result != max(80.0, 60.0)


def test_c1_completion_threshold_met_adversarial_pair_is_false():
    assert gpr.compute_completion_threshold_met(_ADVERSARIAL_COMPLETED_COUNT, _ADVERSARIAL_ASSIGNED_COUNT) is False


def test_c1_exact_pair_at_threshold_boundary_takes_max_inclusive():
    """A pair exactly equal to 2/5 -- including a large exact one -- must still take the
    MAX branch (inclusivity preserved), through both calling styles."""
    assert gpr.compute_completion_threshold_met(2, 5) is True
    assert gpr.compute_completion_threshold_met(40_000_000_000_000_000, 100_000_000_000_000_000) is True

    ratio = gpr.compute_completion(40_000_000_000_000_000, 100_000_000_000_000_000)
    assert ratio == 0.4
    result_ordinary_sequence = gpr.compute_quarter_grade(80.0, 60.0, ratio)
    assert result_ordinary_sequence == max(80.0, 60.0) == 80.0

    result_explicit_kwargs = gpr.compute_quarter_grade(
        work_aggregate=80.0,
        assessment_aggregate=60.0,
        completed_count=40_000_000_000_000_000,
        assigned_count=100_000_000_000_000_000,
    )
    assert result_explicit_kwargs == max(80.0, 60.0) == 80.0


def test_c1_completion_threshold_met_39_of_100_and_40_of_100():
    """39/100 -> AVERAGE, 40/100 -> MAX still hold under the exact-integer gate."""
    assert gpr.compute_completion_threshold_met(39, 100) is False
    assert gpr.compute_completion_threshold_met(40, 100) is True


def test_c1_ordinary_sequence_39_of_100_takes_average_40_of_100_takes_max():
    ratio_39 = gpr.compute_completion(39, 100)
    ratio_40 = gpr.compute_completion(40, 100)
    result_39 = gpr.compute_quarter_grade(70.0, 90.0, ratio_39)
    result_40 = gpr.compute_quarter_grade(70.0, 90.0, ratio_40)
    assert result_39 == (70.0 + 90.0) / 2.0
    assert result_40 == max(70.0, 90.0)


def test_c1_completion_threshold_met_unknown_and_zero_denominator():
    assert gpr.compute_completion_threshold_met(gpr.UNKNOWN, 5) is gpr.UNKNOWN
    assert gpr.compute_completion_threshold_met(2, gpr.UNKNOWN) is gpr.UNKNOWN
    assert gpr.compute_completion_threshold_met(None, 5) is gpr.UNKNOWN
    assert gpr.compute_completion_threshold_met(0, 0) is gpr.UNKNOWN  # OPEN-16


def test_c1_completion_threshold_met_domain_errors_mirror_compute_completion():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion_threshold_met(6, 5)  # completed > assigned
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion_threshold_met(-1, 5)
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_completion_threshold_met(True, 5)  # bool masquerading as a number


def test_c1_quarter_grade_completed_count_without_assigned_count_raises():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, completed_count=5)
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(work_aggregate=70.0, assessment_aggregate=90.0, assigned_count=100)


def test_c1_quarter_grade_malformed_counts_not_masked_by_teacher_override():
    """R1 discipline extended to the new exact-count kwargs: a malformed count pair
    still raises even when a perfectly valid teacher_override is also supplied."""
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=70.0,
            assessment_aggregate=90.0,
            completed_count=6,
            assigned_count=5,
            teacher_override=85.0,
        )


def test_c1_explicit_kwargs_take_precedence_over_conflicting_bare_float_completion():
    """completion=0.90 alone would take MAX; the explicit exact counts say strictly
    below the threshold and must win."""
    result = gpr.compute_quarter_grade(
        work_aggregate=80.0,
        assessment_aggregate=60.0,
        completion=0.90,
        completed_count=1,
        assigned_count=1000,
    )
    assert result == (80.0 + 60.0) / 2.0


@pytest.mark.parametrize(
    "bare_ratio, expected",
    [
        # 0.39 rounds to 0.4 at one decimal. If ANY pre-rounding were reintroduced into
        # the bare-float fallback branch, this case would flip to the MAX branch (80.0).
        (0.39, (80.0 + 60.0) / 2.0),
        (0.35, (80.0 + 60.0) / 2.0),
        (0.40, 80.0),  # inclusive at exactly the threshold, even on the fallback path
    ],
)
def test_c1_bare_float_fallback_branch_applies_no_pre_rounding(bare_ratio, expected):
    """OPEN-08 (RESOLVED by RC 2026-07-24) binds the BARE-FLOAT fallback branch too.

    Manager gap-check, NT16 Codex-review remediation round: the exact-cross-product path
    (carried counts / explicit kwargs) is well covered, but the documented bare-float
    fallback -- reached when a caller supplies a plain float that carries no counts and
    passes no `completed_count=`/`assigned_count=` kwargs -- had NO test asserting that it
    applies no pre-rounding. A mutation that reintroduced `round(completion, 1)` into that
    branch survived the entire suite. It no longer does: 0.39 and 0.35 both round UP to 0.4
    at one decimal, so any pre-rounding there flips them into the MAX branch and fails here.

    This does not weaken the C1 ruling that the float is never the branch input when exact
    counts exist -- it guards the residual, explicitly-documented fallback so that path
    cannot silently regress either.
    """
    assert gpr.compute_quarter_grade(
        work_aggregate=80.0, assessment_aggregate=60.0, completion=bare_ratio
    ) == expected


def test_c1_completion_ratio_is_float_compatible_but_arithmetic_degrades_provenance():
    """V1 (HIGH, Codex re-check 2026-07-24): an earlier version of this test's name and
    docstring said CompletionRatio 'behaves as an ordinary float everywhere' and stopped
    there. That overstates the guarantee: the NUMERIC-compatibility half is real and is
    still verified below (isinstance/equality/arithmetic/round()/float() all produce the
    mathematically correct value, so no existing consumer that expects a bare float is
    broken) -- but none of arithmetic, round(), or float() coercion preserves the
    CompletionRatio's carried provenance. Every one of them returns a plain `float`, not
    a `CompletionRatio`; the exact completed_count/assigned_count this ratio was computed
    from does NOT survive any of them. See CompletionRatio's docstring for the full list
    of degrading operations and why that is the honest design, not a defect."""
    ratio = gpr.compute_completion(1, 4)
    assert isinstance(ratio, float)
    assert isinstance(ratio, gpr.CompletionRatio)

    # Numeric compatibility: real, and still verified here.
    assert ratio == 0.25
    assert ratio + 1.0 == 1.25
    assert round(ratio, 2) == 0.25
    assert float(ratio) == 0.25
    assert type(float(ratio)) is float

    # V1: none of the above survives as a CompletionRatio -- provenance is lost, not
    # merely "also available as a float". This is the point the old name/docstring did
    # not make explicit.
    assert not isinstance(ratio + 1.0, gpr.CompletionRatio)
    assert not isinstance(round(ratio, 2), gpr.CompletionRatio)
    assert not isinstance(float(ratio), gpr.CompletionRatio)


def test_c1_completion_ratio_carries_the_exact_counts_it_was_computed_from():
    ratio = gpr.compute_completion(3, 7)
    assert ratio.completed_count == 3
    assert ratio.assigned_count == 7


def test_c1_zero_denominator_completion_is_unknown_not_a_completion_ratio():
    """assigned_count == 0 (OPEN-16) must still return the bare UNKNOWN sentinel, not a
    CompletionRatio wrapping some fabricated ratio."""
    result = gpr.compute_completion(0, 0)
    assert result is gpr.UNKNOWN
    assert not isinstance(result, gpr.CompletionRatio)


def test_c1_explicit_kwargs_matching_carried_completion_ratio_counts_is_consistent():
    """Supplying both a carrying `completion` AND explicit kwargs that describe the SAME
    evidence is redundant but not an error."""
    ratio = gpr.compute_completion(39, 100)
    result = gpr.compute_quarter_grade(
        work_aggregate=70.0,
        assessment_aggregate=90.0,
        completion=ratio,
        completed_count=39,
        assigned_count=100,
    )
    assert result == (70.0 + 90.0) / 2.0


def test_c1_explicit_kwargs_conflicting_with_carried_completion_ratio_counts_raises():
    """Supplying a carrying `completion` (from compute_completion) AND explicit kwargs
    that describe DIFFERENT evidence is a caller-side defect: two different counts
    cannot both govern the same gate decision."""
    ratio = gpr.compute_completion(39, 100)  # below threshold
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(
            work_aggregate=70.0,
            assessment_aggregate=90.0,
            completion=ratio,
            completed_count=40,  # disagrees with the ratio's carried completed_count
            assigned_count=100,
        )


def test_c1_threshold_fraction_invariant_is_exactly_two_fifths():
    assert gpr._COMPLETION_THRESHOLD_FRACTION == fractions.Fraction(2, 5)
    assert float(gpr._COMPLETION_THRESHOLD_FRACTION) == gpr.COMPLETION_THRESHOLD


# ---------------------------------------------------------------------------
# V1 (HIGH, Codex re-check 2026-07-24): CompletionRatio provenance is silently
# destroyed by the very operations the docs previously advertised as safe.
#
# Reproduced live with the witness pair completed=40000000000000000,
# assigned=100000000000000001 (exact ratio strictly BELOW 2/5, so AVERAGE is the correct
# branch): `ratio + 0.0`, `float(ratio)`, `round(ratio, 12)`, `abs(ratio)`, and a JSON
# round-trip all silently degrade the pristine CompletionRatio to a bare float and flip
# branch selection to the MAX branch (80.0) via the documented, boundary-imprecise
# fallback tier -- not a silent wrong answer once the docs are corrected (see
# CompletionRatio's docstring, compute_completion's, compute_quarter_grade's,
# GRADING_POLICY_SPEC.md §3, and grading_policy.v2.json's quarter_rule.
# gate_decision_from_counts), but it must actually happen, and the docs must actually say
# so, or the correction would be describing fiction. This section proves: (a) the
# degradation is real; (b) the documentation actually discloses it, in every artifact
# named above; (c) completed_count/assigned_count are read-only, so a tampering attempt
# raises rather than silently succeeding; (d) a hand-crafted ratio whose counts disagree
# with its own float value raises PolicyDomainError, never UNKNOWN; (e) legitimate
# pristine ratios across a representative range are unaffected by any of the above.
# ---------------------------------------------------------------------------

_V1_WITNESS_COMPLETED_COUNT = 40_000_000_000_000_000
_V1_WITNESS_ASSIGNED_COUNT = 100_000_000_000_000_001


@pytest.mark.parametrize(
    "degrade",
    [
        pytest.param(lambda r: r + 0.0, id="plus_zero"),
        pytest.param(lambda r: float(r), id="float_coercion"),
        pytest.param(lambda r: round(r, 12), id="round_12"),
        pytest.param(lambda r: abs(r), id="abs"),
        pytest.param(lambda r: json.loads(json.dumps(r)), id="json_round_trip"),
    ],
)
def test_v1_doc_advertised_operations_degrade_to_the_fallback_tier(degrade):
    """V1 (HIGH): each of these operations is exactly what earlier docs called safe
    ('behaves as an ordinary float everywhere'). Each one silently produces a bare float
    with no carried counts, so compute_quarter_grade can no longer use the exact-integer
    gate and falls back to comparing the lossy float directly against
    COMPLETION_THRESHOLD -- for the witness pair (exact ratio strictly below 2/5, whose
    float representation nonetheless collapses to exactly 0.4), that fallback wrongly
    selects the MAX branch (80.0) instead of the correct AVERAGE branch (70.0) the
    pristine ratio gives."""
    ratio = gpr.compute_completion(_V1_WITNESS_COMPLETED_COUNT, _V1_WITNESS_ASSIGNED_COUNT)

    pristine_result = gpr.compute_quarter_grade(80.0, 60.0, ratio)
    assert pristine_result == pytest.approx(70.0), "the pristine ratio must take AVERAGE"

    degraded = degrade(ratio)
    assert not isinstance(degraded, gpr.CompletionRatio), (
        "the operation under test must actually produce a bare float, not a "
        "CompletionRatio -- otherwise this test would not be exercising degradation at all"
    )
    degraded_result = gpr.compute_quarter_grade(80.0, 60.0, degraded)
    assert degraded_result == pytest.approx(80.0), (
        "a degraded bare float must fall back to the float-vs-threshold comparison and "
        "wrongly select MAX here -- this is the documented fallback tier, not a silent "
        "wrong answer, but it must be real"
    )


def test_v1_documentation_discloses_provenance_loss_everywhere(policy_json):
    """Guard test: the correction to V1's over-promising docs must actually be present in
    every artifact a caller might read -- CompletionRatio's docstring,
    compute_completion's docstring, compute_quarter_grade's docstring,
    GRADING_POLICY_SPEC.md, and grading_policy.v2.json's C1 gate-decision text. If any of
    these silently drifts back to a bare 'behaves as an ordinary float everywhere' claim
    with no provenance-loss warning, this test fails -- it checks each specific artifact
    the ruling named, not merely that a warning exists somewhere in the package."""

    def _has_provenance_warning(text: str) -> bool:
        lowered = text.lower()
        return "provenance" in lowered and ("lost" in lowered or "destroyed" in lowered)

    assert _has_provenance_warning(gpr.CompletionRatio.__doc__), (
        "CompletionRatio's docstring must disclose that provenance is lost by "
        "arithmetic/coercion/rounding/copying/serialization"
    )
    assert _has_provenance_warning(gpr.compute_completion.__doc__), (
        "compute_completion's docstring must disclose the same provenance-loss warning"
    )
    assert _has_provenance_warning(gpr.compute_quarter_grade.__doc__), (
        "compute_quarter_grade's docstring must disclose the same provenance-loss "
        "warning for its tier-3 fallback"
    )

    spec_path = Path(__file__).parent / "GRADING_POLICY_SPEC.md"
    spec_text = spec_path.read_text(encoding="utf-8")
    assert _has_provenance_warning(spec_text), (
        "GRADING_POLICY_SPEC.md must disclose the provenance-loss warning, not merely "
        "the original (now-corrected) 'behaves as an ordinary float everywhere' claim"
    )

    gate_text = policy_json["quarter_rule"]["gate_decision_from_counts"]
    assert _has_provenance_warning(gate_text), (
        "grading_policy.v2.json's quarter_rule.gate_decision_from_counts must disclose "
        "the provenance-loss warning"
    )


def test_v1_completed_count_and_assigned_count_are_read_only():
    """V1 (HIGH): a CompletionRatio's carried counts must not be mutable after
    construction -- a mutated ratio could otherwise lie about its own provenance (e.g.
    flipping a below-threshold ratio's counts to make it read as above-threshold, with no
    error at all). Assignment must raise, never silently succeed."""
    ratio = gpr.compute_completion(1, 1000)  # 0.001, strictly below the 0.40 gate
    with pytest.raises(AttributeError):
        ratio.completed_count = 999
    with pytest.raises(AttributeError):
        ratio.assigned_count = 1

    # The ratio itself, and its real counts, must be unaffected by the failed attempts.
    assert ratio.completed_count == 1
    assert ratio.assigned_count == 1000
    assert gpr.compute_quarter_grade(80.0, 60.0, ratio) == pytest.approx((80.0 + 60.0) / 2.0)


def test_v1_crafted_ratio_whose_counts_disagree_with_its_float_raises_domain_error():
    """V1 (HIGH): read-only counts stop MUTATION of a genuine ratio, but they cannot stop
    a caller from hand-constructing a CompletionRatio directly with a float value that
    never matched its own counts -- a crafted/corrupted ratio. compute_quarter_grade must
    catch this with the count-vs-float consistency check and raise PolicyDomainError
    (never UNKNOWN -- this is a data defect, not unavailable evidence)."""
    # 999/1000 == 0.999, but the float value claims 0.001 -- these disagree.
    crafted = gpr.CompletionRatio(0.001, completed_count=999, assigned_count=1000)
    assert isinstance(crafted, gpr.CompletionRatio)
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(80.0, 60.0, crafted)

    # Also via the ordinary positional constructor call shape.
    crafted_positional = gpr.CompletionRatio(0.90, 1, 1000)  # 1/1000 == 0.001, not 0.90
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_quarter_grade(80.0, 60.0, crafted_positional)


@pytest.mark.parametrize(
    "completed_count, assigned_count, expected_branch",
    [
        (_V1_WITNESS_COMPLETED_COUNT, _V1_WITNESS_ASSIGNED_COUNT, "average"),  # witness pair
        (2, 5, "max"),  # exact 2/5, inclusive boundary
        (39, 100, "average"),
        (0, 1, "average"),
        (5, 5, "max"),  # n/n
    ],
)
def test_v1_consistency_check_does_not_fire_for_pristine_ratios(completed_count, assigned_count, expected_branch):
    """The count-vs-float consistency check (V1) must never reject a genuine
    compute_completion result -- across the witness pair, the exact 2/5 boundary, a
    representative below-threshold pair, the zero/one edge, and the n/n edge. A false
    positive here would break every ordinary caller of this module."""
    ratio = gpr.compute_completion(completed_count, assigned_count)
    result = gpr.compute_quarter_grade(80.0, 60.0, ratio)  # must not raise
    expected = 80.0 if expected_branch == "max" else 70.0
    assert result == pytest.approx(expected)


def test_v1_consistency_check_does_not_fire_for_bare_float_with_unrelated_explicit_kwargs():
    """The consistency check is scoped to a completion that CARRIES counts (a
    CompletionRatio) -- it must not compare a bare float `completion` against explicit
    completed_count=/assigned_count= kwargs that were never claimed to describe it. The
    existing precedence rule (explicit kwargs win over a bare float) is unaffected."""
    result = gpr.compute_quarter_grade(
        work_aggregate=80.0,
        assessment_aggregate=60.0,
        completion=0.90,  # would-be MAX on its own, and does not match 1/1000 at all
        completed_count=1,
        assigned_count=1000,
    )
    assert result == pytest.approx((80.0 + 60.0) / 2.0)


def test_json_declares_gate_decision_from_counts_rule(policy_json):
    quarter_rule = policy_json["quarter_rule"]
    assert "gate_decision_from_counts" in quarter_rule
    text = quarter_rule["gate_decision_from_counts"].lower()
    assert "exact integer cross-product" in text
    assert "never" in text


# ---------------------------------------------------------------------------
# C3 (HIGH, Codex review 2026-07-24): extra-credit authorization by membership, not by
# which parameter the caller used.
# ---------------------------------------------------------------------------


def test_c3_authorized_source_via_generic_channel_contributes():
    result = gpr.compute_extra_credit(additional_sources=["ti84"])
    assert result == 0.5


def test_c3_both_authorized_sources_via_generic_channel_capped():
    result = gpr.compute_extra_credit(additional_sources=["ti84", "equation_lab"])
    assert result == 1.0 == gpr.EXTRA_CREDIT_DAILY_CAP_POINTS


def test_c3_flag_and_generic_channel_same_source_does_not_double_count():
    result = gpr.compute_extra_credit(ti84_completed=True, additional_sources=["ti84"])
    assert result == 0.5


def test_c3_unauthorized_source_raises_even_when_a_flag_is_unknown():
    with pytest.raises(gpr.PolicyDecisionRequiredError):
        gpr.compute_extra_credit(ti84_completed=gpr.UNKNOWN, additional_sources=["unauthorized_thing"])


def test_c3_malformed_source_id_raises_policy_domain_error():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_extra_credit(additional_sources=[123])
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_extra_credit(additional_sources=[""])
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_extra_credit(additional_sources=[None])


def test_c3_malformed_source_id_is_not_policy_decision_required_error():
    """Malformed input is a §7.2 domain violation, distinct from a well-formed-but-
    unauthorized name (§7.3) -- the two failure modes must never be conflated."""
    try:
        gpr.compute_extra_credit(additional_sources=[123])
        raised = None
    except Exception as exc:  # noqa: BLE001 -- intentionally broad to inspect the type
        raised = exc
    assert isinstance(raised, gpr.PolicyDomainError)
    assert not isinstance(raised, gpr.PolicyDecisionRequiredError)


def test_json_declares_extra_credit_membership_authorization_rule(policy_json):
    rule = policy_json["extra_credit_cap_rule"]
    assert "authorization_is_by_membership_not_channel" in rule
    assert "deduplication_rule" in rule
    assert "malformed_source_id_policy" in rule


# ---------------------------------------------------------------------------
# C4 (HIGH, Codex review 2026-07-24): ASSESSMENT ceiling enforced at the reducer.
# ---------------------------------------------------------------------------


def test_c4_assessment_aggregate_raises_when_earned_exceeds_possible():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_assessment_aggregate([(120.0, 100.0)])


def test_c4_assessment_aggregate_legitimate_set_returns_value_in_0_100():
    result = gpr.compute_assessment_aggregate([(85.0, 100.0), (18.0, 20.0)])
    assert 0.0 <= result <= 100.0
    assert result == pytest.approx(100.0 * (85.0 + 18.0) / (100.0 + 20.0))


def test_c4_component_percentage_allow_above_100_true_returns_value_above_100():
    result = gpr.compute_component_percentage([(120.0, 100.0)], allow_above_100=True)
    assert result == 120.0


def test_c4_component_percentage_allow_above_100_false_raises_for_the_same_input():
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_component_percentage([(120.0, 100.0)])
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_component_percentage([(120.0, 100.0)], allow_above_100=False)


def test_c4_component_percentage_allow_above_100_still_propagates_unknown():
    assert gpr.compute_component_percentage([(gpr.UNKNOWN, 100.0)], allow_above_100=True) is gpr.UNKNOWN
    assert gpr.compute_component_percentage([(120.0, gpr.UNKNOWN)], allow_above_100=True) is gpr.UNKNOWN


def test_c4_component_percentage_allow_above_100_still_zero_denominator_is_unknown():
    assert gpr.compute_component_percentage([], allow_above_100=True) is gpr.UNKNOWN
    assert gpr.compute_component_percentage([(0.0, 0.0)], allow_above_100=True) is gpr.UNKNOWN


def test_c4_component_percentage_one_item_over_one_item_under_still_raises_strict():
    """Even if the GROUP total would land under 100%, a single item individually
    exceeding its own possible points is still a per-item data defect under the strict
    default."""
    with pytest.raises(gpr.PolicyDomainError):
        gpr.compute_component_percentage([(120.0, 100.0), (0.0, 1000.0)])


def test_json_declares_per_item_ceiling_rule(policy_json):
    rule = policy_json["component_reduction_rule"]
    assert "per_item_ceiling" in rule
    text = rule["per_item_ceiling"].lower()
    assert "allow_above_100" in text
    assert "assessment" in text


# ---------------------------------------------------------------------------
# C5 (MEDIUM, Codex review 2026-07-24) / AMENDED by RC 2026-07-24 (NT16-B): rounding
# mode is now DECIDED (half-up, decimal ROUND_HALF_UP) -- see
# grading_policy_ref.py's round_final_grade_for_display docstring for RC's verbatim
# amendment and the full half-up-vs-half-even discrimination discussion.
# ---------------------------------------------------------------------------


def test_c5_round_final_grade_for_display_half_up_tie_examples_amended_by_rc():
    """RC's 2026-07-24 amendment: 'Use conventional decimal ROUND_HALF_UP for the
    student-facing one-decimal display. Example: 89.25 -> 89.3.' 0.25 is an exact binary
    midpoint whose preceding digit is even, so it is a genuine discriminating witness:
    half-up rounds it UP to 0.3, while Python's builtin (half-even) round would round it
    DOWN to 0.2 -- this test asserts both the new value and its divergence from the old
    builtin-round behavior.

    0.35 is NOT an exact binary midpoint (as a float it is
    0.34999999999999997779...), so it does NOT discriminate half-up from half-even --
    both modes round it DOWN to 0.3. The value pinned here is UNCHANGED from before the
    amendment; only the reasoning changed (it was never proof of half-even, and is not
    proof of half-up either -- it is a non-discriminating regression pin, retained for
    an unrelated purpose such as catching a wrong decimals exponent)."""
    assert gpr.round_final_grade_for_display(0.25) == 0.3
    assert gpr.round_final_grade_for_display(0.25) != round(0.25, 1)  # builtin round: 0.2

    assert gpr.round_final_grade_for_display(0.35) == 0.3  # value unchanged; non-discriminating


def test_round_final_grade_for_display_rc_worked_example_89_25_discriminates():
    """RC's own worked example from the 2026-07-24 amendment: 'Example: 89.25 -> 89.3.'
    89.25 is an exact binary midpoint at one decimal whose preceding digit (2) is EVEN,
    so this is the strongest available discriminating witness: half-up rounds UP to
    89.3, while Python's builtin round (half-even) rounds DOWN to the even 89.2. Both
    the new value and its divergence from builtin round() are asserted, so a silent
    regression back to half-even/builtin round cannot pass unnoticed."""
    assert gpr.round_final_grade_for_display(89.25) == 89.3
    assert round(89.25, 1) == 89.2  # sanity: this is what makes 89.25 discriminate
    assert gpr.round_final_grade_for_display(89.25) != round(89.25, 1)


def test_round_final_grade_for_display_89_75_is_an_agreement_tie_not_discriminating():
    """89.75 is ALSO an exact binary midpoint at one decimal, but its preceding digit
    (7) is ODD -- half-even rounds UP to the even 89.8, which is the SAME result
    half-up gives. This is an AGREEMENT tie: both modes produce 89.8, so this value
    must never be cited as proof of which rounding mode is active."""
    assert gpr.round_final_grade_for_display(89.75) == 89.8
    assert round(89.75, 1) == 89.8  # builtin (half-even) agrees -- non-discriminating


def test_round_final_grade_for_display_89_35_is_not_an_exact_midpoint_non_discriminating():
    """89.35 looks like a '.x5' tie but is NOT an exact binary midpoint: as a Python
    float it is 89.34999999999999431565..., strictly BELOW its nominal midpoint, so
    BOTH half-up and half-even round it DOWN to 89.3. This is a valid regression pin
    (e.g. it would catch a wrong decimals exponent) but it does not distinguish the two
    rounding modes and must never be cited as such."""
    assert gpr.round_final_grade_for_display(89.35) == 89.3
    assert round(89.35, 1) == 89.3  # builtin agrees here too -- non-discriminating


def test_round_final_grade_for_display_accepts_completion_ratio_float_subclass():
    """`compute_completion` returns a `CompletionRatio` -- a `float` SUBCLASS, not merely
    float-like. `Decimal()` must accept it exactly as it would a plain float (Decimal's
    constructor works from the exact binary value of any float instance, subclass or
    not), so `round_final_grade_for_display` must work unchanged when handed a
    CompletionRatio directly, e.g. as a display value for a raw completion percentage."""
    ratio = gpr.compute_completion(3, 8)  # exact binary value: 0.375
    assert isinstance(ratio, gpr.CompletionRatio)
    assert isinstance(ratio, float)
    displayed = gpr.round_final_grade_for_display(ratio)
    assert displayed == 0.4
    assert not isinstance(displayed, gpr.CompletionRatio)  # display value is a plain float


def test_json_declares_display_rounding_mode(policy_json):
    rounding_rules = policy_json["rounding_rules"]
    assert "display_rounding_mode" in rounding_rules
    text = rounding_rules["display_rounding_mode"].lower()
    assert "half-up" in text
    assert "amended by rc 2026-07-24" in text


def test_json_open_item_register_still_exactly_open_01_through_19(policy_json):
    """C5's remediation must NOT mint a new OPEN-NN id -- the resolved-item register
    stays exactly the seven items resolved in this package (OPEN-08/09/10/11/15/16/19);
    no OPEN-20 (or any other new id) may appear anywhere in the register."""
    resolved = policy_json["resolved_open_items"]
    assert "OPEN-20" not in resolved
    for item_id in resolved:
        assert item_id.startswith("OPEN-")
        number = int(item_id.split("-")[1])
        assert 1 <= number <= 19
