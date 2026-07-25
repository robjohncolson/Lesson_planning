"""
grading_policy_ref.py -- Reference implementation of NT15 product-policy Deliverable D2
(Grade composition & quarter rule; Participation & extra credit).

Package: NT15 product-policy · Version: 2.0 · Date: 2026-07-24
Source of authority: RC final decisions, 2026-07-24 (Grok preference interview + RC
clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
Status: Authoritative -- gates all future Desk / grading / Schoology implementation.

Traces to PREF-03 (grade composition & quarter rule) and PREF-04 (participation & extra
credit). See GRADING_POLICY_SPEC.md for the normative prose and grading_policy.v2.json
for the machine-readable constants. This module LOADS its constants from that JSON file
at import time rather than hard-coding them, so the JSON remains the single source of
truth -- if the JSON changes, this module's behavior changes with it.

Standard-library only. No network. No dependency on any other file in this repository.

UNKNOWN handling (PROGRAM_DOSSIER.md §15 item 1, "Unknown != zero"): every function in
this module treats an unavailable required input as UNKNOWN and propagates UNKNOWN as
the result -- never 0, never a silently-chosen branch, never fabricated credit. The one
exception, by design, is `teacher_override` in `compute_quarter_grade`: a supplied
teacher override always takes precedence, including over an otherwise-UNKNOWN result,
because teacher designation is server-authoritative and clients never determine official
credit (PREF-03.9).

--------------------------------------------------------------------------------------
NT16 (v2.0) supersession -- OPEN-08/09/10/11/15/16/19 are now DECIDED, not provisional.
--------------------------------------------------------------------------------------
v1.0 shipped six OPEN items (OPEN-08, 09, 10, 11, 15, 16) as narrow, explicitly-labeled
PROVISIONAL / UNRESOLVED-PENDING-RC placeholders, plus left multi-item reduction
(OPEN-19) unaddressed entirely. RC issued final rulings on all seven on 2026-07-24. This
version implements those rulings exactly -- see grading_policy.v2.json ->
"resolved_open_items" for each ruling's text and what it supersedes, and
GRADING_POLICY_SPEC.md §8 for the normative prose. In summary:

  OPEN-08 (RESOLVED) -- compare the EXACT completion ratio against the inclusive 0.40
    threshold; no pre-rounding before branch selection. `compute_completion`'s
    `round_ndigits` parameter is REMOVED (it enabled the now-forbidden pre-rounding).
  OPEN-09 (RESOLVED) -- full precision internally; round ONLY the student-facing
    final-grade DISPLAY to one decimal (`round_final_grade_for_display`,
    `final_grade_display_string`). `compute_quarter_grade`'s `round_ndigits` parameter is
    REMOVED. AMENDED by RC 2026-07-24 (NT16-B, a later same-day ruling): the display
    tie-breaking MODE is decimal ROUND_HALF_UP, not Python's builtin half-even `round`.
    The half-even reading was this package's own prior implementation guess, labeled
    pending RC confirmation; it is now superseded -- see `round_final_grade_for_display`'s
    docstring below for the full history and RC's verbatim amendment.
  OPEN-10 (RESOLVED) -- +1.0 point/student/class-day cap on currently-authorized extra
    credit (TI-84 +0.5, Equation Lab +0.5, stacking allowed), applied unconditionally.
    `compute_extra_credit`'s opt-in `daily_cap` parameter is REMOVED; an unauthorized
    `additional_sources` argument raises `PolicyDecisionRequiredError` (a new RC policy
    decision is required) rather than ever silently exceeding the cap.
  OPEN-11 (RESOLVED) -- non-class days are EXCLUDED from the participation requirement;
    partial/absent/uncertain attendance NEVER auto-zeroes (excused/unknown, never 0)
    unless RC explicitly designates the day participation-eligible. `compute_participation_point`
    is REPLACED by `compute_participation_day` / `ParticipationDay` / `aggregate_participation`.
    CONFIRMED by RC 2026-07-24 (NT16-B, a later same-day ruling): RC directly confirmed
    the excused (not unknown) reading for a known partial/absent/non-class day, in a
    verbatim four-point ruling -- see `compute_participation_day`'s docstring below.
  OPEN-15 (RESOLVED) -- WORK is now POINT-BASED:
    WORK = 100 * (packet_points_earned + participation_points_earned + extra_credit_points_earned)
           / (packet_points_possible + participation_points_possible)
    This SUPERSEDES the v1.0 plain-addition placeholder. `compute_work_aggregate`'s
    signature is REPLACED accordingly.
  OPEN-16 (RESOLVED) -- no eligible designated work/participation (zero denominator) =>
    completion UNKNOWN, WORK UNKNOWN, quarter grade UNKNOWN; student-facing display is a
    dash / "not enough evidence", never zero.
  OPEN-19 (RESOLVED, new in v2.0) -- point-weighted multi-item reduction:
    component_percentage = 100 * sum(points_earned) / sum(points_possible)
    New: `compute_component_percentage`, `compute_assessment_aggregate`. Equal-averaging
    per-item percentages when possible-points differ is FORBIDDEN.

INPUT DOMAINS AND FAIL-CLOSED VALIDATION (Codex GPT-5.6 SOL review R-A, finding A1, HIGH;
manager ruling 2026-07-24; see GRADING_POLICY_SPEC.md §7 for the full normative treatment).
Every numeric input to this module has a declared domain (also recorded machine-readably in
grading_policy.v2.json -> "domains"). An input outside its domain -- wrong type (including a
bool passed where a number is required), non-finite (NaN/±inf), negative where non-negative
is required, completed_count exceeding assigned_count, completion outside [0, 1], an
assessment_aggregate outside [0, 100], or an invalid attendance value -- raises
PolicyDomainError. It is NEVER converted to UNKNOWN, 0, or a clamped/coerced value.

This is a deliberate, load-bearing distinction: UNKNOWN (see above) means "well-formed input,
but the authoritative evidence for it is unavailable" (dossier §15 item 1). A domain violation
means the input itself is malformed -- a defect in the caller, not a reliability/evidence
condition. Silently treating a defect as UNKNOWN would let a bug masquerade as a legitimate
"evidence unavailable" state, which is exactly the failure mode §15 exists to prevent. So the
two failure modes are kept strictly separate: UNKNOWN propagates; a domain violation raises.

A THIRD, distinct failure mode is introduced in v2.0: `PolicyDecisionRequiredError`, raised
only by `compute_extra_credit` when the caller supplies evidence for an extra-credit source
outside the currently-authorized set. This is neither a defect (the input can be perfectly
well-formed) nor an UNKNOWN evidence state -- it means the request asks this policy to do
something RC has not yet authorized (OPEN-10). See that class's docstring.

--------------------------------------------------------------------------------------
Codex review remediation (2026-07-24) -- C1, C3, C4, C5.
--------------------------------------------------------------------------------------
A second Codex review pass over this v2.0 package found four defects in the
IMPLEMENTATION of already-RESOLVED rulings (not in the rulings themselves -- no OPEN-NN
ruling text changes here; these are bug fixes to code that did not yet fully comply with
its own documented ruling). Each is fixed in this same v2.0 file; see
grading_policy.v2.json's "changelog" for the corresponding entry.

  C1 (HIGH) -- `compute_quarter_grade`'s 0.40 gate compared a binary FLOAT `completion`
    ratio to COMPLETION_THRESHOLD; for sufficiently large completed_count/assigned_count
    pairs the float can round to exactly 0.40 even when the true rational value is
    strictly below it, wrongly selecting the MAX branch (OPEN-08's ruling is "compare the
    EXACT ratio" -- a float comparison can violate that at extreme counts). Fixed by
    `_completion_meets_threshold_exact` / `compute_completion_threshold_met`, an exact
    integer cross-product, and a new keyword-only `completed_count`/`assigned_count` pair
    on `compute_quarter_grade` that takes precedence over the float `completion` when
    supplied. The float `completion` parameter still works exactly as before for callers
    who only have a ratio -- it is now documented as subject to representation error at
    the boundary, with the exact-count path as the correct input whenever raw counts are
    available.
  C3 (HIGH) -- `compute_extra_credit` decided authorization by WHICH PARAMETER the caller
    used (the dedicated boolean flags vs. `additional_sources`) instead of by membership
    in AUTHORIZED_EXTRA_CREDIT_SOURCES, so `additional_sources=["ti84"]` (an authorized
    source) wrongly raised `PolicyDecisionRequiredError`, and an unauthorized source in
    `additional_sources` was never even checked when a flag was UNKNOWN (the UNKNOWN
    short-circuit ran first). Fixed: authorization is now checked by membership, for
    EVERY supplied source, unconditionally, before the UNKNOWN short-circuit; an
    authorized source reaching this function via `additional_sources` now contributes
    normally (deduplicated against the same source's dedicated flag -- a source counts at
    most once per student per class day, however it arrives).
  C4 (HIGH) -- `compute_assessment_aggregate` (and `compute_component_percentage`)
    computed the point-weighted ratio with no per-item ceiling, so
    `compute_assessment_aggregate([(120, 100)])` returned `120.0`, an out-of-[0, 100]
    value that nothing upstream of `compute_quarter_grade` ever caught. Fixed:
    `compute_component_percentage` gains `allow_above_100` (default `False`, STRICT --
    every item must satisfy `points_earned <= points_possible`, `PolicyDomainError`
    otherwise); `compute_assessment_aggregate` always uses the strict (default) path, so
    its result is guaranteed in `[0, 100]` by construction. `allow_above_100=True` is an
    explicit opt-in reserved for WORK-side groups where extra credit legitimately lifts
    earned above possible -- never legitimate for ASSESSMENT (PREF-04.5).
  C5 (MEDIUM) -- `round_final_grade_for_display` used Python's `round`, which is
    half-even ("banker's rounding": `round(0.25, 1) == 0.2`, `round(0.35, 1) == 0.3`),
    without ever stating that choice. RC's original OPEN-09 ruling fixed "one decimal"
    but said nothing about the tie-breaking mode. This was FIRST explicitly labeled, in
    this docstring and in grading_policy.v2.json's `rounding_rules.display_rounding_mode`,
    as an IMPLEMENTATION READING pending RC confirmation -- not a ruling -- per the same
    "do not invent silently" discipline already applied to OPEN-11's excused/unknown
    reading. No new OPEN-NN id was introduced for this (the resolved-item register is
    closed at OPEN-01..OPEN-19).

--------------------------------------------------------------------------------------
NT16-B -- RC amendment (OPEN-09 rounding MODE) and confirmation (OPEN-11), 2026-07-24
(later same date than the rulings and Codex remediation above).
--------------------------------------------------------------------------------------
RC has since directly ruled on both of the residual "pending RC confirmation" readings
above -- the C5 rounding-mode reading and OPEN-11's excused/unknown reading. Neither
reopens its OPEN-NN id, and no new OPEN-NN id is minted for either; both OPEN-09 and
OPEN-11 remain RESOLVED.

  OPEN-09 rounding MODE -- AMENDED. RC's verbatim ruling: "Use conventional decimal
    ROUND_HALF_UP for the student-facing one-decimal display. Example: 89.25 -> 89.3.
    Do not use Python binary-float round() or half-even behavior for the display
    contract. Keep full precision internally. Do not round before the 40% branch
    decision. Schoology reconciliation compares underlying values; display rounding
    cannot conceal real divergence." This SUPERSEDES the half-even implementation
    reading the C5 finding above recorded -- half-even was never a ruling, and that
    passage is retained only as the historical record of what this package guessed
    before RC's amendment, not as a description of current behavior.
    `round_final_grade_for_display` now rounds via
    `Decimal(value).quantize(exponent, rounding=ROUND_HALF_UP)`; see that function's own
    docstring for the full implementation, the half-up-vs-half-even discrimination
    detail, and which boundary values do and do not distinguish the two modes.
  OPEN-11 excused/unknown reading -- CONFIRMED. RC's verbatim four-point confirmation:
    "A known absent, partial-attendance, or non-class day is excused and contributes 0
    earned / 0 possible. A genuinely uncertain attendance state remains UNKNOWN. Neither
    case produces an automatic participation zero. RC may explicitly designate an
    otherwise excused day as participation-eligible." `compute_participation_day` already
    conformed to all four points before this confirmation -- no code change accompanies
    it, only the removal of the "documented reading, not itself a ruling" / "pending RC
    confirmation" labeling `compute_participation_day`'s docstring previously carried.
"""

from __future__ import annotations

import fractions
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Optional, Sequence, Tuple, Union

_POLICY_PATH = Path(__file__).parent / "grading_policy.v2.json"

with open(_POLICY_PATH, "r", encoding="utf-8") as _f:
    POLICY: dict[str, Any] = json.load(_f)

# --- Constants loaded FROM grading_policy.v2.json (single source of truth). ---
# Nothing below is hard-coded independently of the JSON; if the JSON's "constants"
# block changes, these names change with it.
_CONSTANTS = POLICY["constants"]
COMPLETION_THRESHOLD: float = _CONSTANTS["completion_threshold"]
COMPLETION_THRESHOLD_INCLUSIVE: bool = _CONSTANTS["completion_threshold_inclusive"]
PARTICIPATION_POINT_PRESENT: float = _CONSTANTS["participation_point_per_class_day_present"]
PARTICIPATION_POINT_ABSENT: float = _CONSTANTS["participation_point_per_class_day_absent"]
TI84_EXTRA_CREDIT_POINTS: float = _CONSTANTS["ti84_extra_credit_points"]
EQUATION_LAB_EXTRA_CREDIT_POINTS: float = _CONSTANTS["equation_lab_extra_credit_points"]
EXTRA_CREDIT_DAILY_CAP_POINTS: float = _CONSTANTS["extra_credit_daily_cap_points"]
AUTHORIZED_EXTRA_CREDIT_SOURCES: Tuple[str, ...] = tuple(_CONSTANTS["authorized_extra_credit_sources"])
FINAL_GRADE_DISPLAY_DECIMALS: int = _CONSTANTS["final_grade_display_decimals"]
UNKNOWN_DISPLAY_TOKEN: str = _CONSTANTS["unknown_display_token"]
UNKNOWN_DISPLAY_TEXT: str = _CONSTANTS["unknown_display_text"]

def _load_completion_threshold_fraction() -> fractions.Fraction:
    """
    C1 (HIGH, Codex review 2026-07-24; hardened same day after a peer-review follow-up):
    derive `completion_threshold`'s EXACT Fraction form directly from the JSON file's own
    decimal literal -- via a SEPARATE parse of the same file using
    `parse_float=fractions.Fraction` -- rather than from the already-lossy binary `float`
    the main `POLICY` dict holds.

    `fractions.Fraction(COMPLETION_THRESHOLD)` (a plain float) would capture the float's
    OWN binary-representation error (0.40 is not exactly representable in base 2) and
    require a `.limit_denominator()` HEURISTIC to guess back the simple decimal fraction
    it was probably authored as. A heuristic is exactly what this exactness fix must not
    rely on: `.limit_denominator()` with no bound could, for some future threshold value,
    silently guess a fraction other than the one actually intended. Parsing the JSON
    SOURCE TEXT's decimal digits directly (via `json.load(..., parse_float=Fraction)`)
    has no floating-point intermediate at all -- `Fraction("0.40")` is exactly `2/5` by
    construction, not by approximation, no matter what threshold value is written in the
    JSON. This second parse is scoped ONLY to recovering this one exact value; it does
    not replace or alter the main `POLICY` dict (whose other constants are still meant to
    be ordinary floats) -- see `_completion_meets_threshold_exact` for how the resulting
    Fraction is used to decide the 0.40 gate by exact integer cross-product, never by
    comparing a binary float to COMPLETION_THRESHOLD.
    """
    with open(_POLICY_PATH, "r", encoding="utf-8") as f:
        exact_policy = json.load(f, parse_float=fractions.Fraction)
    return exact_policy["constants"]["completion_threshold"]


_COMPLETION_THRESHOLD_FRACTION: fractions.Fraction = _load_completion_threshold_fraction()

# Invariant check, not a heuristic: converting the exact Fraction back to a float must
# reproduce COMPLETION_THRESHOLD bit-for-bit. If it doesn't, the JSON's decimal literal
# and this module's float constant have diverged -- a defect in this module (or in the
# JSON file itself), not a legitimate policy state, and this must fail loudly at import
# time rather than silently deciding the 0.40 gate against the wrong fraction.
assert float(_COMPLETION_THRESHOLD_FRACTION) == COMPLETION_THRESHOLD, (
    "completion_threshold Fraction derivation diverged from the float constant: "
    f"float({_COMPLETION_THRESHOLD_FRACTION}) = {float(_COMPLETION_THRESHOLD_FRACTION)!r} "
    f"!= COMPLETION_THRESHOLD = {COMPLETION_THRESHOLD!r}"
)

_VALID_ATTENDANCE = ("present", "partial", "absent", "unknown")


class _Unknown:
    """
    Sentinel type for UNKNOWN (per PROGRAM_DOSSIER.md §15 item 1: "Unknown != zero").

    UNKNOWN is a first-class value, distinct from 0, False, and None. It must never be
    coerced to a number or treated as a normal falsy value by accident -- `bool(UNKNOWN)`
    raises TypeError on purpose. Callers must test identity explicitly: `value is UNKNOWN`.
    """

    _instance: "Optional[_Unknown]" = None

    def __new__(cls) -> "_Unknown":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNKNOWN"

    def __bool__(self) -> bool:
        raise TypeError(
            "UNKNOWN has no truth value -- it is neither a success nor a falsy zero. "
            "Check `value is UNKNOWN` explicitly instead of using it in a boolean context."
        )

    def __eq__(self, other: object) -> bool:
        return other is self

    def __hash__(self) -> int:
        return hash("UNKNOWN")


UNKNOWN = _Unknown()

Value = Union[float, int, _Unknown, None]


def _is_unknown(value: Value) -> bool:
    """True if `value` is the UNKNOWN sentinel or None (both mean 'input unavailable')."""
    return value is UNKNOWN or value is None


class PolicyDomainError(Exception):
    """
    Raised when an input to this module is malformed or outside the domain declared for
    it (see grading_policy.v2.json -> "domains"; GRADING_POLICY_SPEC.md §7).

    This is DELIBERATELY DISTINCT from UNKNOWN. UNKNOWN means "well-formed input, but the
    authoritative evidence for it is unavailable" (PROGRAM_DOSSIER.md §15 item 1) -- a
    legitimate reliability state this module must propagate, never suppress. A
    PolicyDomainError means the input itself is malformed -- a negative count, a
    completion ratio outside [0, 1], a NaN, a string where a number is required,
    completed_count exceeding assigned_count, an invalid attendance value -- which is a
    DEFECT in the caller (or in whatever produced the value upstream), not a
    reliability/evidence condition.

    Treating a defect as UNKNOWN would let a bug silently masquerade as a legitimate
    "evidence unavailable" state -- exactly the failure mode §15 exists to prevent. So
    this module keeps the two failure modes strictly separate: UNKNOWN propagates; a
    domain violation FAILS CLOSED and raises PolicyDomainError loudly instead of
    returning UNKNOWN, 0, or a clamped/coerced value.
    """


class PolicyDecisionRequiredError(Exception):
    """
    Raised by `compute_extra_credit` when the caller supplies evidence for an extra-
    credit source outside `AUTHORIZED_EXTRA_CREDIT_SOURCES` (currently: TI-84 and
    Equation Lab only). This is OPEN-10's ruling (RESOLVED by RC 2026-07-24): "Any FUTURE
    extra-credit source requires a new policy decision -- it never silently exceeds the
    cap."

    This is DELIBERATELY DISTINCT from both UNKNOWN and PolicyDomainError:
      - It is not UNKNOWN -- the caller's input is not "unavailable evidence"; it is a
        concrete, well-formed request.
      - It is not a PolicyDomainError -- the input need not be malformed (a source name
        can be a perfectly well-formed string); the problem is that this policy has no
        authority to grant credit for it yet.

    A new RC policy decision is required before any additional extra-credit source may
    contribute to the WORK aggregate. This module never silently absorbs an unauthorized
    source into the existing cap, clips it to fit, or ignores it -- it raises loudly
    instead, so the gap in authority is visible rather than quietly papered over.
    """


def _require_number(value: Any, name: str) -> Union[int, float]:
    """
    Raise PolicyDomainError unless `value` is a genuine int/float (never bool, never a
    string or other type) and finite (never NaN/±inf). Returns `value` unchanged so
    callers can chain: `x = _require_number(x, "x")`.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyDomainError(
            f"{name} must be a number (int or float), got {type(value).__name__}: {value!r}"
        )
    if not math.isfinite(value):
        raise PolicyDomainError(f"{name} must be finite (no NaN/±inf), got {value!r}")
    return value


def _require_non_negative_integer(value: Any, name: str) -> int:
    """Raise PolicyDomainError unless `value` is a finite, non-negative, whole number."""
    number = _require_number(value, name)
    if isinstance(number, float) and not number.is_integer():
        raise PolicyDomainError(f"{name} must be a whole-number count, got {number!r}")
    whole = int(number)
    if whole < 0:
        raise PolicyDomainError(f"{name} must be non-negative, got {whole!r}")
    return whole


def _require_non_negative(value: Any, name: str) -> Union[int, float]:
    """Raise PolicyDomainError unless `value` is a finite number >= 0."""
    number = _require_number(value, name)
    if number < 0:
        raise PolicyDomainError(f"{name} must be non-negative, got {number!r}")
    return number


def _require_in_range(
    value: Any, name: str, lo: Union[int, float], hi: Union[int, float]
) -> Union[int, float]:
    """Raise PolicyDomainError unless `value` is a finite number in [lo, hi]."""
    number = _require_number(value, name)
    if not (lo <= number <= hi):
        raise PolicyDomainError(f"{name} must be in [{lo}, {hi}], got {number!r}")
    return number


class CompletionRatio(float):
    """
    C1 (HIGH, Codex review 2026-07-24; hardened same day after a peer-review follow-up):
    the `float` subclass `compute_completion` returns. `isinstance(x, float)` is `True`
    because it genuinely IS a float, not merely float-like -- so every ordinary float
    operation (arithmetic, comparison, `round()`, `float()`, JSON serialization, copying,
    pickling) runs without raising. It additionally carries the exact `completed_count`/
    `assigned_count` it was computed from, as read-only `.completed_count`/
    `.assigned_count` properties.

    WHY THIS EXISTS: the peer-review follow-up to the original C1 fix found that the
    exact-count gate (`completed_count=`/`assigned_count=` keyword-only arguments on
    `compute_quarter_grade`) only closed the float-collapse defect when a caller
    remembered to pass the raw counts to `compute_quarter_grade` a SECOND time. The
    ORDINARY calling sequence every real caller actually writes --

        completion = compute_completion(completed_count, assigned_count)
        quarter_grade = compute_quarter_grade(work, assessment, completion)

    -- still collapsed, because the counts that existed at the first call were thrown
    away the moment `compute_completion` returned a bare float. `CompletionRatio` closes
    that gap: `compute_quarter_grade` recognizes a `completion` argument that carries its
    own counts and uses them for the exact-integer gate decision AUTOMATICALLY, with no
    extra effort from the caller and no change to the ordinary two-call sequence above --
    PROVIDED the object it recognizes is the pristine one `compute_completion` returned
    (see the exactness-guarantee warning below).

    V1 (HIGH, Codex re-check 2026-07-24) -- THE EXACTNESS GUARANTEE IS NARROW; READ THIS
    BEFORE RELYING ON IT. An earlier version of this docstring said this class "behaves as
    an ordinary float everywhere" and left it at that -- true as far as it went, but
    dangerously incomplete: "behaves as an ordinary float" is exactly the problem. The
    carried counts survive ONLY for as long as you hold the exact object
    `compute_completion` returned, completely untouched. The moment this ratio is used in
    ANY of the following, the result is an ORDINARY `float` with NO carried counts
    whatsoever -- not a degraded `CompletionRatio`, just a plain `float`, because that is
    what every one of these operations is defined to return for a float subclass:

      - arithmetic, including additive identities and no-ops (`ratio + 0.0`, `ratio * 1`,
        unary `+ratio`, ...)
      - coercion (`float(ratio)`)
      - rounding (`round(ratio, N)`)
      - `abs(ratio)`, and any other builtin that internally returns `float(self)`
      - JSON (or any other) serialization and deserialization / round-tripping
      - copying (`copy.copy`/`copy.deepcopy`) or pickling -- deliberately implemented (see
        `__reduce__` below) to degrade HONESTLY to a bare float rather than either
        crashing or silently reconstructing a `CompletionRatio` whose provenance was not
        actually carried across the copy/pickle boundary

    Once any of the above has happened, the provenance is lost: `compute_quarter_grade`
    has no way to tell that the resulting bare float ever came from exact counts, and
    falls back to comparing it directly against `COMPLETION_THRESHOLD` -- the documented,
    boundary-imprecise fallback tier (see that function's docstring, tier 3). This is NOT
    a defect to be patched by making provenance survive arithmetic -- doing so would mean
    overriding every dunder method `float` has, and it would still fail the instant the
    value is serialized (e.g. to JSON, or to Schoology). It is the honest design: the
    fallback tier exists precisely because a bare float's provenance genuinely cannot be
    recovered once lost, and pretending otherwise would be worse than documenting the
    limitation plainly.

    Callers who need the exactness guarantee to actually hold must do one of:
      1. Pass `compute_completion(...)`'s result DIRECTLY as `compute_quarter_grade`'s
         `completion=` argument, with no operation performed on it in between; or
      2. Supply `completed_count=`/`assigned_count=` to `compute_quarter_grade` explicitly.

    READ-ONLY COUNTS (V1, HIGH): `completed_count`/`assigned_count` are exposed as
    properties over private slots, with no setter -- assigning either one now raises
    `AttributeError` instead of silently succeeding. Read-only attributes stop a caller
    from MUTATING a genuine ratio after construction (a mutated ratio could otherwise lie
    about its own provenance -- e.g. setting `.completed_count` on a below-threshold ratio
    to a value that flips the gate), but they cannot stop a caller from hand-constructing a
    `CompletionRatio` directly with a float value that never matched its own counts in the
    first place (a "crafted" ratio, bypassing `compute_completion` entirely).
    `compute_quarter_grade` defends against that separately, with an explicit
    float-vs-exact-fraction consistency check before it ever trusts a carried pair for the
    gate decision -- see that function's docstring.

    A `CompletionRatio` produced by `compute_completion` itself is always internally
    consistent (its float value and its carried counts describe the same ratio by
    construction, since values are already validated as a non-negative-integer pair
    satisfying `completed_count <= assigned_count`); the consistency check above exists for
    the crafted-construction case this class cannot prevent on its own.
    """

    __slots__ = ("_completed_count", "_assigned_count")

    def __new__(cls, value: float, completed_count: int, assigned_count: int) -> "CompletionRatio":
        self = super().__new__(cls, value)
        self._completed_count = completed_count
        self._assigned_count = assigned_count
        return self

    @property
    def completed_count(self) -> int:
        """Read-only (V1, HIGH, Codex re-check 2026-07-24) -- see class docstring's
        "READ-ONLY COUNTS" section. Assigning to this attribute raises `AttributeError`."""
        return self._completed_count

    @property
    def assigned_count(self) -> int:
        """Read-only (V1, HIGH, Codex re-check 2026-07-24) -- see class docstring's
        "READ-ONLY COUNTS" section. Assigning to this attribute raises `AttributeError`."""
        return self._assigned_count

    def __reduce__(self) -> Tuple[Any, Tuple[float]]:
        """
        V1 (HIGH, Codex re-check 2026-07-24): copying (`copy.copy`/`copy.deepcopy`) and
        pickling this ratio degrade it HONESTLY to a bare `float` -- exactly like every
        other operation listed in the class docstring's exactness-guarantee warning. This
        neither raises (without this override, the default float-subclass reduction calls
        `cls.__new__(cls, value)` with no way to supply the two extra required constructor
        arguments, which raises `TypeError` -- an unnecessary crash for a "consumer" as
        ordinary as `copy.copy` or `pickle`) NOR silently reconstructs a `CompletionRatio`
        that would misrepresent untouched provenance across a copy/pickle boundary it
        never actually carried its counts across.
        """
        return (float, (float(self),))


def compute_completion(
    completed_count: Value,
    assigned_count: Value,
) -> Union["CompletionRatio", _Unknown]:
    """
    Completion percentage, defined ONLY over teacher-designated digital work (PREF-03.4).
    Pure paper practice is not graded or individually tracked (PREF-02) and never enters
    this ratio -- it must not appear in either completed_count or assigned_count.

        completion = completed_count / assigned_count

    Returns UNKNOWN if either input is UNKNOWN/None, or if assigned_count == 0.

    OPEN-08 (RESOLVED by RC 2026-07-24): "Compare the EXACT completion ratio against the
    inclusive 0.40 threshold. No pre-rounding before branch selection." This function
    therefore returns the exact ratio with NO rounding option at all -- the v1.0
    `round_ndigits` parameter, which enabled the now-forbidden pre-rounding, is REMOVED.
    The threshold comparison itself happens downstream in `compute_quarter_grade`.

    C1 (HIGH, Codex review 2026-07-24; hardened same day) -- the returned value is a
    `CompletionRatio` (see that class), a `float` SUBCLASS that also carries the exact
    `completed_count`/`assigned_count` it was computed from. THE FLOAT VALUE ITSELF
    REMAINS A DERIVED DISPLAY/REPORTING VALUE ONLY, subject to binary-representation
    error at the 0.40 boundary for extreme counts, exactly as documented before.

    V1 (HIGH, Codex re-check 2026-07-24): the carried provenance is NARROW, not a
    blanket guarantee -- it survives only while the exact object returned here reaches
    `compute_quarter_grade` untouched. Any arithmetic, coercion, rounding, copying, or
    serialization performed on it in between -- even `ratio + 0.0`, `float(ratio)`,
    `round(ratio, N)`, a JSON round-trip, or `copy.copy(ratio)` -- degrades it to a bare
    `float` and the provenance is lost; the exactness guarantee then no longer applies,
    and the gate falls back to comparing the lossy float directly against
    `COMPLETION_THRESHOLD` (see `CompletionRatio`'s docstring for the full list of
    degrading operations and `compute_quarter_grade`'s docstring, tier 3, for the
    fallback path this reaches). This is the honest design, not a defect: callers who
    need the guarantee to hold must pass this function's result directly, unmodified, or
    supply `completed_count=`/`assigned_count=` explicitly.

    What changes when the pristine object DOES reach `compute_quarter_grade` untouched:
    it no longer has to compare the float directly against the threshold; it uses the
    CARRIED counts to decide the gate by exact integer cross-product automatically (see
    `compute_quarter_grade`'s docstring) -- the ordinary
    `compute_quarter_grade(w, a, compute_completion(c, n))` calling sequence is therefore
    exact by construction, with no extra effort from the caller, PROVIDED nothing between
    the two calls touches the ratio.

    Domain (GRADING_POLICY_SPEC.md §7; Codex SOL review R-A finding A1): both
    completed_count and assigned_count, once known (not UNKNOWN/None), must be
    non-negative, finite, whole-number counts -- never negative, never fractional,
    never NaN/inf, never a bool or string masquerading as a number. Additionally,
    completed_count may never exceed assigned_count (you cannot complete more
    teacher-designated digital work than was assigned). Any violation raises
    PolicyDomainError -- this is a malformed/defective input, not a legitimate
    UNKNOWN evidence state (§7.2), so it is never silently coerced, clamped, or
    reported as UNKNOWN.

    OPEN-16 (RESOLVED by RC 2026-07-24): "No eligible designated work/participation =>
    completion UNKNOWN". assigned_count == 0 means no digital work has been designated
    yet; this now returns UNKNOWN as DECIDED policy (not a provisional placeholder) --
    the early-quarter consequence (every student's completion, and therefore the
    quarter-rule branch, is UNKNOWN before any digital work is designated) is confirmed,
    not merely tolerated. (Note: assigned_count == 0 with completed_count == 0 is
    well-formed and returns UNKNOWN; assigned_count == 0 with completed_count > 0 is
    malformed -- completed_count cannot exceed assigned_count -- and raises
    PolicyDomainError.)
    """
    if _is_unknown(completed_count) or _is_unknown(assigned_count):
        return UNKNOWN

    completed_count, assigned_count = _validate_completion_counts(completed_count, assigned_count)

    if assigned_count == 0:
        return UNKNOWN
    return CompletionRatio(completed_count / assigned_count, completed_count, assigned_count)


def _validate_completion_counts(completed_count: Any, assigned_count: Any) -> Tuple[int, int]:
    """
    Shared domain validation for a (completed_count, assigned_count) pair. Both values
    must already be known (not UNKNOWN/None) -- callers check that first, since UNKNOWN
    is availability, not malformation, and has nothing to validate.

    Used by `compute_completion` and, as of the C1 remediation (Codex review
    2026-07-24), by the exact-count gate (`compute_completion_threshold_met` and
    `compute_quarter_grade`'s `completed_count`/`assigned_count` kwargs) as well, so both
    entry points enforce the identical domain: non-negative, finite, whole-number counts,
    never a bool or string masquerading as a number, and completed_count may never exceed
    assigned_count. Raises PolicyDomainError on any violation.
    """
    completed_count = _require_non_negative_integer(completed_count, "completed_count")
    assigned_count = _require_non_negative_integer(assigned_count, "assigned_count")

    if completed_count > assigned_count:
        raise PolicyDomainError(
            f"completed_count ({completed_count}) cannot exceed assigned_count "
            f"({assigned_count}) -- teacher-designated digital work cannot show more "
            "completed than assigned."
        )
    return completed_count, assigned_count


def _completion_meets_threshold_exact(completed_count: int, assigned_count: int) -> bool:
    """
    C1 (HIGH, Codex review 2026-07-24): decide the OPEN-08 completion gate via an EXACT
    integer cross-product -- never via the float `completion` ratio.

    `compute_completion` returns a binary float (`completed_count / assigned_count`).
    For sufficiently large counts, that float can round to exactly COMPLETION_THRESHOLD
    (0.40) even when the true rational value is strictly BELOW it -- e.g.
    `completed_count=40_000_000_000_000_000`, `assigned_count=100_000_000_000_000_001`
    gives an exact ratio strictly below 2/5 (`5*completed_count < 2*assigned_count`), yet
    `completed_count / assigned_count` as a float rounds to exactly `0.4`. Comparing that
    float to COMPLETION_THRESHOLD would wrongly select the MAX branch. This function
    instead decides:

        completed_count / assigned_count  ??  COMPLETION_THRESHOLD
        <=>
        completed_count * THRESHOLD_DENOMINATOR  ??  assigned_count * THRESHOLD_NUMERATOR

    where THRESHOLD_NUMERATOR/THRESHOLD_DENOMINATOR is COMPLETION_THRESHOLD's exact
    Fraction form (2/5), recovered from the JSON constant (`_COMPLETION_THRESHOLD_FRACTION`)
    rather than hard-coded. Both sides are plain Python integers (arbitrary precision) --
    there is no floating-point arithmetic anywhere on this path, so it cannot collapse at
    any count, however large.

    PRECONDITION (enforced by callers, not here): `completed_count`/`assigned_count` are
    already validated non-negative whole numbers with `completed_count <= assigned_count`
    and `assigned_count > 0` -- the zero-denominator/UNKNOWN case (OPEN-16) is handled by
    the caller before this function is ever invoked.
    """
    cross_left = completed_count * _COMPLETION_THRESHOLD_FRACTION.denominator
    cross_right = assigned_count * _COMPLETION_THRESHOLD_FRACTION.numerator
    if COMPLETION_THRESHOLD_INCLUSIVE:
        return cross_left >= cross_right
    return cross_left > cross_right


def compute_completion_threshold_met(
    completed_count: Value,
    assigned_count: Value,
) -> Union[bool, _Unknown]:
    """
    C1 (HIGH, Codex review 2026-07-24): the public, standalone form of the OPEN-08
    completion gate, decided by EXACT integer cross-product
    (`_completion_meets_threshold_exact`) rather than by comparing the float
    `compute_completion` ratio to COMPLETION_THRESHOLD. Returns `True` if completion is
    at-or-above (or strictly above, per COMPLETION_THRESHOLD_INCLUSIVE) the threshold,
    `False` otherwise.

    Domain/UNKNOWN handling mirrors `compute_completion` exactly: UNKNOWN if either input
    is UNKNOWN/None; UNKNOWN if `assigned_count == 0` (OPEN-16 zero-eligible-denominator
    -- no eligible designated work means the gate itself is undeterminable, not trivially
    met); PolicyDomainError for any malformed/out-of-domain input (wrong type,
    non-finite, negative, non-whole, `completed_count > assigned_count`).

    `compute_quarter_grade`'s keyword-only `completed_count`/`assigned_count` arguments
    call this function internally to decide the branch when supplied, taking precedence
    over the float `completion` argument -- see that function's docstring for how the two
    calling styles interact.
    """
    if _is_unknown(completed_count) or _is_unknown(assigned_count):
        return UNKNOWN

    completed_count, assigned_count = _validate_completion_counts(completed_count, assigned_count)

    if assigned_count == 0:
        return UNKNOWN
    return _completion_meets_threshold_exact(completed_count, assigned_count)


class ParticipationDay(NamedTuple):
    """
    One day's participation evidence, expressed as earned/possible points plus a status
    label explaining which OPEN-11 case produced them (see `compute_participation_day`,
    whose excused-vs-unknown distinction was CONFIRMED by RC 2026-07-24, NT16-B).

    `earned` and `possible` are each either a non-negative float or UNKNOWN -- never a
    guessed number standing in for unavailable evidence.
    """

    earned: Value
    possible: Value
    status: str


def _present_like_participation_day(has_valid_response: Union[bool, _Unknown, None]) -> ParticipationDay:
    """Shared logic for a day that is treated exactly like a normal present class day:
    "present" attendance, or "partial"/"absent" attendance that RC has explicitly
    designated participation-eligible (OPEN-11)."""
    if _is_unknown(has_valid_response):
        return ParticipationDay(UNKNOWN, 1.0, "unknown")
    return ParticipationDay(
        PARTICIPATION_POINT_PRESENT if has_valid_response else PARTICIPATION_POINT_ABSENT,
        1.0,
        "counted",
    )


def compute_participation_day(
    has_valid_response: Union[bool, _Unknown, None],
    *,
    is_class_day: bool = True,
    attendance: str = "present",
    participation_eligible_designation: bool = False,
) -> ParticipationDay:
    """
    OPEN-11 (RESOLVED by RC 2026-07-24): "Non-class days are EXCLUDED from the
    participation requirement. Partial/absent/uncertain attendance NEVER auto-zeroes --
    such days are excused/unknown unless RC explicitly designates the day
    participation-eligible. UNKNOWN is distinct from zero."

    This REPLACES v1.0's `compute_participation_point`, which returned UNKNOWN (not a
    guessed 0.0/1.0) for ANY non-class or partial-attendance day -- an unresolved-
    pending-RC placeholder. RC's ruling distinguishes four cases, each returning a
    `ParticipationDay(earned, possible, status)`:

    1. `is_class_day is False` -> `ParticipationDay(0.0, 0.0, "excluded_non_class_day")`.
       Contributes nothing to earned OR possible -- the day is excluded from the
       participation requirement entirely, not counted as a zero.

    2. `is_class_day is True`, `attendance == "present"`:
       - `has_valid_response` known (True/False) -> possible 1.0; earned
         PARTICIPATION_POINT_PRESENT if truthy else PARTICIPATION_POINT_ABSENT; status
         "counted".
       - `has_valid_response` UNKNOWN/None -> earned UNKNOWN, possible 1.0, status
         "unknown". (Attendance is known -- the day counts toward the requirement -- but
         whether the student responded is not yet known.)

    3. `is_class_day is True`, `attendance in ("partial", "absent")`,
       `participation_eligible_designation is False` (the default) ->
       `ParticipationDay(0.0, 0.0, "excused_not_participation_eligible")`. Excluded from
       the requirement -- this is deliberately NOT an auto-zero, because `possible` is
       0.0 too: the day simply does not enter either side of the participation ratio.

    4. `is_class_day is True`, `attendance in ("partial", "absent")`,
       `participation_eligible_designation is True` (RC has explicitly designated this
       day participation-eligible despite the partial/absent attendance) -> treated
       exactly like case 2 (`attendance == "present"`) above.

    5. `is_class_day is True`, `attendance == "unknown"` ->
       `ParticipationDay(UNKNOWN, UNKNOWN, "unknown")`, regardless of
       `participation_eligible_designation`. Genuinely-unknown attendance is never zero.

    A documented reading, not an invention beyond RC's ruling (historical framing -- see
    the CONFIRMED paragraph below for RC's direct ruling on this exact question): RC's
    text permits either "excused" or "unknown" for a KNOWN partial/absent day without an
    eligibility designation. This implementation chooses EXCUSED (case 3: `possible =
    0.0`, excluded from the requirement) as the reading that simultaneously honors
    "excluded from the participation requirement" (the day does not silently shrink the
    requirement's denominator by leaving it counted-but-earning-zero) and "never
    auto-zero" (0/0 is not a zero score -- it contributes nothing to either side of the
    ratio). Genuinely-UNKNOWN attendance (case 5) is kept distinct and maps to UNKNOWN,
    never to the excused reading -- "the attendance itself is not known" is a different
    evidentiary state from "the attendance is known to be partial/absent."

    CONFIRMED by RC 2026-07-24 (NT16-B, a later same-day ruling than the ruling quoted at
    the top of this docstring): the excused-vs-unknown reading immediately above was,
    until this confirmation, a documented implementation choice RC's original ruling
    permitted but did not itself pin down -- labeled "pending RC confirmation," not
    presented as settled policy. RC has since directly confirmed it, in her own verbatim
    four-point form:

      - "A known absent, partial-attendance, or non-class day is excused and contributes
        0 earned / 0 possible."
      - "A genuinely uncertain attendance state remains UNKNOWN."
      - "Neither case produces an automatic participation zero."
      - "RC may explicitly designate an otherwise excused day as participation-eligible."

    This confirms cases 1, 3, 4, and 5 above exactly as already implemented here -- no
    code in this function changes as a result; only the "pending RC confirmation" /
    "documented reading, not itself a ruling" labeling these cases previously carried is
    superseded. See `OPEN_DECISIONS_REGISTER.md`'s `OPEN-11` section for the same
    four-point confirmation with full provenance.

    Domain (§7): `attendance` must be exactly one of "present", "partial", "absent",
    "unknown" -- any other value raises PolicyDomainError. This check runs before any
    other branch, including the `is_class_day is False` case, so a malformed attendance
    value is never silently ignored just because the day turns out to be excluded for an
    unrelated reason.
    """
    if attendance not in _VALID_ATTENDANCE:
        raise PolicyDomainError(
            f"attendance must be one of {_VALID_ATTENDANCE}, got {attendance!r}"
        )

    if not is_class_day:
        return ParticipationDay(0.0, 0.0, "excluded_non_class_day")

    if attendance == "unknown":
        return ParticipationDay(UNKNOWN, UNKNOWN, "unknown")

    if attendance == "present":
        return _present_like_participation_day(has_valid_response)

    # attendance in ("partial", "absent")
    if not participation_eligible_designation:
        return ParticipationDay(0.0, 0.0, "excused_not_participation_eligible")
    return _present_like_participation_day(has_valid_response)


def aggregate_participation(days: Iterable[ParticipationDay]) -> Tuple[Value, Value]:
    """
    Sums a sequence of `ParticipationDay` into a single (earned, possible) pair suitable
    for `compute_work_aggregate`'s `participation_points_earned` /
    `participation_points_possible` arguments.

    UNKNOWN in any day's `earned` propagates UNKNOWN to the total `earned`; UNKNOWN in
    any day's `possible` propagates UNKNOWN to the total `possible` -- independently, so
    (for example) a day with unknown response but known attendance (possible=1.0,
    earned=UNKNOWN) makes the earned-total UNKNOWN while the possible-total still
    accumulates normally.

    Domain: every known (non-UNKNOWN) `earned`/`possible` value is validated as a finite
    non-negative number -- this runs for every day regardless of whether some other day
    is UNKNOWN, so a malformed KNOWN value is never masked by an unrelated UNKNOWN day
    (the same "validate everything supplied" discipline as `compute_quarter_grade`, §7.3).
    """
    earned_total = 0.0
    possible_total = 0.0
    earned_unknown = False
    possible_unknown = False

    for day in days:
        if _is_unknown(day.earned):
            earned_unknown = True
        else:
            earned_total += _require_non_negative(day.earned, "ParticipationDay.earned")

        if _is_unknown(day.possible):
            possible_unknown = True
        else:
            possible_total += _require_non_negative(day.possible, "ParticipationDay.possible")

    earned: Value = UNKNOWN if earned_unknown else earned_total
    possible: Value = UNKNOWN if possible_unknown else possible_total
    return (earned, possible)


def compute_extra_credit(
    *,
    ti84_completed: Union[bool, _Unknown, None] = False,
    equation_lab_completed: Union[bool, _Unknown, None] = False,
    additional_sources: Optional[Sequence[str]] = None,
) -> Union[float, _Unknown]:
    """
    PREF-04.3/.4: an assigned TI-84 exercise completed successfully earns
    TI84_EXTRA_CREDIT_POINTS (+0.5); an assigned Equation Lab exercise completed
    successfully earns EQUATION_LAB_EXTRA_CREDIT_POINTS (+0.5). Both belong to the WORK
    side of the ledger, never ASSESSMENT (PREF-04.5) -- see compute_work_aggregate.

    OPEN-10 (RESOLVED by RC 2026-07-24): "+1.0 point per student per class day cap for
    currently-authorized extra credit (TI-84 +0.5, Equation Lab +0.5, stacking allowed).
    Any FUTURE extra-credit source requires a new policy decision -- it never silently
    exceeds the cap." This function therefore:

      - Sums whichever of the currently-authorized sources were completed, then applies
        EXTRA_CREDIT_DAILY_CAP_POINTS (1.0, loaded from JSON) UNCONDITIONALLY -- there is
        no longer an opt-in `daily_cap` parameter (v1.0's placeholder is REMOVED); the
        cap is now policy, not a caller convenience.
      - If `additional_sources` contains a source outside `AUTHORIZED_EXTRA_CREDIT_SOURCES`,
        raises `PolicyDecisionRequiredError` naming the unauthorized source(s) -- a new RC
        policy decision is required before any additional extra-credit source may
        contribute. The cap is never silently clipped or extended to accommodate an
        unauthorized source; the request is refused outright.

    C3 (HIGH, Codex review 2026-07-24) -- authorization is decided by MEMBERSHIP in
    `AUTHORIZED_EXTRA_CREDIT_SOURCES`, not by which parameter the caller happened to use.
    Two defects this fixes:

      1. `additional_sources=["ti84"]` used to raise `PolicyDecisionRequiredError` even
         though "ti84" IS authorized -- the old check treated ANY non-empty
         `additional_sources` as unauthorized, regardless of its contents. A source
         reaching this function through the generic `additional_sources` channel is
         checked against the SAME authorized set as the dedicated boolean flags, and
         contributes the SAME points if authorized.
      2. An unauthorized source used to go unchecked whenever `ti84_completed` or
         `equation_lab_completed` was UNKNOWN, because the UNKNOWN short-circuit ran
         BEFORE the authorization check. Every supplied `additional_sources` entry is now
         validated and authorization-checked FIRST, unconditionally -- an unauthorized id
         ALWAYS raises `PolicyDecisionRequiredError`, including when an unrelated flag is
         UNKNOWN. RC's ruling that a future source needs a new policy decision is an
         obligation that cannot be skipped just because unrelated evidence happens to be
         unavailable.

    De-duplication rule: a source counts AT MOST ONCE per student per class day, no
    matter which channel it arrives through. If the same authorized source is signaled
    via BOTH its dedicated boolean flag (e.g. `ti84_completed=True`) AND via
    `additional_sources` (e.g. `additional_sources=["ti84"]`), the two channels are
    aliases for the same piece of evidence, not independent evidence -- it still
    contributes only TI84_EXTRA_CREDIT_POINTS once, not twice.

    Malformed source ids (non-string, or an empty string) raise `PolicyDomainError`, not
    `PolicyDecisionRequiredError` -- a malformed id is a caller-side data defect, not a
    request for a policy this module isn't authorized to grant, and the two failure modes
    must stay distinct (see module docstring, "domains" section).

    Returns UNKNOWN if either `ti84_completed` or `equation_lab_completed` is
    UNKNOWN/None (unresolved evidence, not "not completed") -- but only AFTER every
    supplied `additional_sources` entry has been validated and authorization-checked;
    see point 2 above.
    """
    # C3 fix: validate + authorize every supplied additional source FIRST, unconditionally
    # -- BEFORE the UNKNOWN short-circuit below. A malformed id is a PolicyDomainError; an
    # unauthorized-but-well-formed id is a PolicyDecisionRequiredError. Both are checked
    # regardless of whether ti84_completed/equation_lab_completed is UNKNOWN.
    generic_sources: Sequence[str] = tuple(additional_sources) if additional_sources else ()
    if generic_sources:
        malformed = [source for source in generic_sources if not isinstance(source, str) or not source]
        if malformed:
            raise PolicyDomainError(
                f"additional_sources entries must be non-empty strings, got: {malformed!r}"
            )
        unauthorized = [source for source in generic_sources if source not in AUTHORIZED_EXTRA_CREDIT_SOURCES]
        if unauthorized:
            raise PolicyDecisionRequiredError(
                f"Extra-credit source(s) not currently authorized: {', '.join(unauthorized)}. "
                f"Only {', '.join(AUTHORIZED_EXTRA_CREDIT_SOURCES)} are authorized (OPEN-10, "
                "RESOLVED by RC 2026-07-24). A new RC policy decision is required before "
                "this source may contribute -- it is never silently added to the ledger or "
                "clipped into the existing cap."
            )

    if _is_unknown(ti84_completed) or _is_unknown(equation_lab_completed):
        return UNKNOWN

    # Every entry in generic_sources is now known-authorized (membership was validated
    # above). De-duplication: "ti84"/"equation_lab" contribute once whether signaled via
    # the dedicated flag, the generic channel, or both.
    total = 0.0
    if ti84_completed or "ti84" in generic_sources:
        total += TI84_EXTRA_CREDIT_POINTS
    if equation_lab_completed or "equation_lab" in generic_sources:
        total += EQUATION_LAB_EXTRA_CREDIT_POINTS

    return min(total, EXTRA_CREDIT_DAILY_CAP_POINTS)


def compute_component_percentage(
    items: Iterable[Tuple[Value, Value]],
    *,
    allow_above_100: bool = False,
) -> Union[float, _Unknown]:
    """
    OPEN-19 (RESOLVED by RC 2026-07-24), point-weighted multi-item reduction:

        component_percentage = 100 * sum(points_earned) / sum(points_possible)

    `items` is an iterable of `(points_earned, points_possible)` pairs, each pair being
    one item's CURRENT OFFICIAL server-designated score (attempt-selection/overrides are
    governed by their own rules, out of scope for this policy). Applies to packet
    assignments, lesson quizzes, topic assessments, or any other same-kind designated
    group with more than one item.

    FORBIDDEN, per RC's ruling: equal-averaging per-item percentages when possible-points
    differ across items (e.g. averaging a 9/10 item and a 45/50 item as (90% + 90%) / 2
    is fine when they agree, but averaging a 9/10 item and a 2/50 item as
    (90% + 4%) / 2 = 47% is NOT the same as the point-weighted
    (9 + 2) / (10 + 50) = 18.3% this policy requires). This function always computes the
    point-weighted ratio -- it never averages per-item percentages, and a percentage must
    never be added directly to raw flat points.

    C4 (HIGH, Codex review 2026-07-24) -- `allow_above_100` (keyword-only, default
    `False`):

      - `allow_above_100=False` (the STRICT default): every item must satisfy
        `points_earned <= points_possible`. A violation raises `PolicyDomainError` --
        per OPEN-19, `points_earned` exceeding `points_possible` on a same-kind
        designated item is a DATA DEFECT (a corrupted or mis-recorded score), not a
        policy question, and is kept distinct from UNKNOWN exactly as every other
        malformed-input case in this module is (§7). Because every item individually
        satisfies `earned <= possible`, the resulting `component_percentage` is
        guaranteed to land in `[0, 100]` BY CONSTRUCTION -- there is no separate
        aggregate-level ceiling check because none is needed once every item-level one
        holds.
      - `allow_above_100=True` is an explicit, deliberate opt-in for the narrow case
        where a component GROUP legitimately contains extra credit: a WORK-side
        component (e.g. a packet-assignment group) whose earned points may legitimately
        exceed its possible points once extra credit is folded in at the item level.
        Callers must opt in on purpose, per group, knowing that group's composition --
        this is never the default, and it is NEVER legitimate for ASSESSMENT (PREF-04.5:
        extra credit never touches ASSESSMENT under any circumstance) --
        `compute_assessment_aggregate` below always uses the strict default and does not
        expose this opt-in at all.

    Returns UNKNOWN if any item's `points_earned` or `points_possible` is UNKNOWN/None,
    or if `sum(points_possible) == 0` (OPEN-16 -- zero eligible denominator). This holds
    identically regardless of `allow_above_100`.

    Domain (§7): every known (non-UNKNOWN) `points_earned` / `points_possible` value is
    validated as a finite non-negative number -- this runs for every item regardless of
    whether some other item is UNKNOWN, so a malformed KNOWN value is never masked by an
    unrelated UNKNOWN item. This also holds identically regardless of `allow_above_100`;
    only the additional `earned <= possible` per-item check is gated by that flag.
    """
    earned_total = 0.0
    possible_total = 0.0
    saw_unknown = False

    for points_earned, points_possible in items:
        if _is_unknown(points_earned) or _is_unknown(points_possible):
            saw_unknown = True
            continue
        points_earned = _require_non_negative(points_earned, "points_earned")
        points_possible = _require_non_negative(points_possible, "points_possible")
        if not allow_above_100 and points_earned > points_possible:
            raise PolicyDomainError(
                f"points_earned ({points_earned}) exceeds points_possible "
                f"({points_possible}) for a same-kind designated item -- this is a DATA "
                "DEFECT (OPEN-19; C4, Codex review 2026-07-24), not a policy question, "
                "and is never silently allowed to push the reduction above 100%. Pass "
                "allow_above_100=True only for a WORK-side group where extra credit "
                "legitimately lifts earned above possible at the item level -- this is "
                "never legitimate for ASSESSMENT (PREF-04.5)."
            )
        earned_total += points_earned
        possible_total += points_possible

    if saw_unknown:
        return UNKNOWN

    if possible_total == 0:
        return UNKNOWN

    return 100.0 * earned_total / possible_total


def compute_assessment_aggregate(items: Iterable[Tuple[Value, Value]]) -> Union[float, _Unknown]:
    """
    OPEN-19 (RESOLVED by RC 2026-07-24):

        ASSESSMENT = 100 * total_assessment_points_earned / total_assessment_points_possible

    over the combined lesson-quizzes + topic-assessments group, each item on its actual
    point scale. This is the same point-weighted reduction as `compute_component_percentage`
    (see that function's docstring for the full domain/UNKNOWN/forbidden-averaging
    treatment); this wrapper exists so ASSESSMENT's specific role (PREF-03.3, PREF-04.5:
    extra credit never touches ASSESSMENT) has its own named entry point.

    C4 (HIGH, Codex review 2026-07-24): this wrapper ALWAYS calls
    `compute_component_percentage` with its STRICT default (`allow_above_100=False`) and
    exposes no way to opt out -- every item must satisfy `points_earned <= points_possible`
    (`PolicyDomainError` otherwise), so this function's result is guaranteed to be in
    `[0, 100]` BY CONSTRUCTION, rather than relying on a downstream caller (e.g.
    `compute_quarter_grade`) to catch an out-of-domain value after the fact. Extra credit
    never touches ASSESSMENT (PREF-04.5), so there is no legitimate reason for an
    ASSESSMENT item to ever show earned exceeding possible.
    """
    return compute_component_percentage(items)


def compute_work_aggregate(
    packet_points_earned: Value,
    packet_points_possible: Value,
    participation_points_earned: Value,
    participation_points_possible: Value,
    extra_credit_points_earned: Value = 0.0,
) -> Union[float, _Unknown]:
    """
    OPEN-15 (RESOLVED by RC 2026-07-24), point-based WORK aggregate -- this REPLACES
    v1.0's plain three-scalar addition (`digital_packet_work_score + participation_points
    + extra_credit_points`), which combined a percentage-scale packet score with flat
    point bonuses without any common scale. RC's ruling fixes the formula exactly:

        WORK = 100 * (packet_points_earned + participation_points_earned + extra_credit_points_earned)
               / (packet_points_possible + participation_points_possible)

    Only teacher-designated official evidence enters. Extra credit
    (`extra_credit_points_earned`) raises the numerator but NEVER the denominator --
    there is no `extra_credit_points_possible` parameter, by design, because extra
    credit's whole point is to add credit beyond what was assigned. Consequently WORK MAY
    EXCEED 100 -- there is no upper clamp anywhere in this function. Downstream,
    `compute_quarter_grade`'s `work_aggregate` domain has been widened to a non-negative
    number with no upper bound to accommodate this (see that function's docstring).

    Returns UNKNOWN if any of the five inputs is UNKNOWN/None -- a required-but-
    unavailable input never silently contributes 0 to the aggregate (dossier §15 item 1).

    OPEN-16 (RESOLVED by RC 2026-07-24): if
    `packet_points_possible + participation_points_possible == 0` (no eligible
    designated work or participation at all), the result is UNKNOWN -- never a
    ZeroDivisionError, never a fabricated 0 or 100.

    Domain (§7): each of the five inputs, once known (not UNKNOWN/None), must be a
    finite, non-negative number -- never negative, never NaN/inf, never a bool or string
    masquerading as a number. A violation raises PolicyDomainError -- a malformed input,
    not an UNKNOWN evidence state.
    """
    if (
        _is_unknown(packet_points_earned)
        or _is_unknown(packet_points_possible)
        or _is_unknown(participation_points_earned)
        or _is_unknown(participation_points_possible)
        or _is_unknown(extra_credit_points_earned)
    ):
        return UNKNOWN

    packet_points_earned = _require_non_negative(packet_points_earned, "packet_points_earned")
    packet_points_possible = _require_non_negative(packet_points_possible, "packet_points_possible")
    participation_points_earned = _require_non_negative(participation_points_earned, "participation_points_earned")
    participation_points_possible = _require_non_negative(participation_points_possible, "participation_points_possible")
    extra_credit_points_earned = _require_non_negative(extra_credit_points_earned, "extra_credit_points_earned")

    denominator = packet_points_possible + participation_points_possible
    if denominator == 0:
        return UNKNOWN

    numerator = packet_points_earned + participation_points_earned + extra_credit_points_earned
    return 100.0 * numerator / denominator


def compute_quarter_grade(
    work_aggregate: Value,
    assessment_aggregate: Value,
    completion: Value = None,
    teacher_override: Optional[float] = None,
    *,
    completed_count: Value = None,
    assigned_count: Value = None,
) -> Union[float, _Unknown]:
    """
    PREF-03 quarter rule:
        if completion >= COMPLETION_THRESHOLD (0.40, INCLUSIVE at exactly 0.40):
            quarter_grade = max(work_aggregate, assessment_aggregate)      # PREF-03.5
        else:
            quarter_grade = average(work_aggregate, assessment_aggregate) # PREF-03.6

    Authority (PREF-03.7/.9): `teacher_override`, when supplied (not None) AND itself
    well-formed, ALWAYS wins over the computed formula -- including over an otherwise-
    UNKNOWN result. Clients never determine designation or official credit; this
    function only ever returns the value the server-authoritative teacher override or
    the deterministic formula produces.

    C1 (HIGH, Codex review 2026-07-24; hardened same day after a peer-review follow-up)
    -- the completion gate is decided by EXACT counts whenever they are available, in
    ANY of three ways, in this precedence order:

      1. `completed_count=`/`assigned_count=` (keyword-only), EXPLICITLY supplied --
         highest precedence. When BOTH are supplied (i.e. left at neither's `None`
         default), they win over everything else: the gate is decided by
         `compute_completion_threshold_met`'s exact integer cross-product, which cannot
         suffer float collapse at any count, however large. If only ONE of the pair is
         supplied, that is a caller-side defect (a single count cannot determine a
         ratio) and raises `PolicyDomainError`.
      2. `completion=<CompletionRatio>` -- a ratio produced by `compute_completion`
         CARRIES the exact `completed_count`/`assigned_count` it was computed from (see
         `CompletionRatio`). If explicit `completed_count=`/`assigned_count=` kwargs were
         NOT supplied, but `completion` is such a carrying value, THOSE CARRIED counts
         are used for the exact-integer gate decision automatically. This is what makes
         the ORDINARY calling sequence exact by construction, with no extra effort from
         the caller:

             completion = compute_completion(completed_count, assigned_count)
             quarter_grade = compute_quarter_grade(work, assessment, completion)

         If BOTH explicit kwargs AND a carrying `completion` are supplied, they must
         describe the SAME evidence: a mismatch between the kwargs and the carried
         counts is a caller-side defect (contradictory inputs for the same decision, not
         a policy question) and raises `PolicyDomainError`. Matching values are fine
         (redundant but consistent) and simply confirm the same counts either way.

         V1 (HIGH, Codex re-check 2026-07-24) -- crafted/corrupted-ratio defense:
         whenever `completion` carries counts (this tier), this function verifies, BEFORE
         trusting those counts for the gate, that the ratio's OWN float value actually
         equals the exact fraction its own carried counts imply:
         `float(fractions.Fraction(completed_count, assigned_count))` must equal
         `float(completion)`. `CompletionRatio.completed_count`/`.assigned_count` are
         read-only (see that class), which stops a caller from MUTATING a genuine ratio
         after construction, but nothing stops a caller from hand-CONSTRUCTING a
         `CompletionRatio` directly with a float value that never matched its own counts
         in the first place -- e.g. `CompletionRatio(0.001, completed_count=999,
         assigned_count=1000)`, bypassing `compute_completion` entirely. A ratio built
         that way could otherwise flip the gate to whatever branch its fabricated float
         value implies while still being trusted for its (unrelated) carried counts. A
         mismatch here is a caller/data defect -- never a policy question, and never
         UNKNOWN (§7) -- so it raises `PolicyDomainError`. This check provably cannot
         fire for any ratio `compute_completion` itself can produce: for any valid
         non-negative integer pair `a`, `b` with `b > 0`, `float(fractions.Fraction(a,
         b))` and `a / b` are the same correctly-rounded IEEE-754 double for the same
         exact rational value, so a pristine `CompletionRatio` always passes. It also
         does not fire on tier 3 (a bare float carries no counts to check against in the
         first place) and is a DIFFERENT question from the kwargs-vs-carried-counts
         contradiction check just above (that check asks whether two independently
         supplied sources of truth AGREE with each other; this check asks whether the
         carried pair is internally self-consistent with its own float value).
      3. `completion=<bare float>` -- a plain float with no carried counts, and no
         explicit `completed_count=`/`assigned_count=` kwargs either. This is the ONLY
         case where the gate falls back to comparing the float directly against
         COMPLETION_THRESHOLD -- and that comparison IS subject to floating-point
         representation error at the boundary: for sufficiently large
         completed_count/assigned_count pairs the exact rational value can be strictly
         below 2/5 while the nearest double still equals exactly 0.4, which would select
         the wrong branch. This is a real, demonstrated defect at this specific boundary
         (not a theoretical concern) -- see `_completion_meets_threshold_exact`'s
         docstring for a concrete adversarial pair.

         V1 (HIGH, Codex re-check 2026-07-24): this tier is reached whenever `completion`
         arrives here as a bare float with no carried counts -- and that happens for TWO
         distinct reasons, not one. An earlier version of this docstring described tier 3
         as reached "only" when a caller genuinely has no raw counts anywhere in the call
         chain; that was false. It is equally reached whenever a `CompletionRatio` DID
         carry exact counts but its provenance was destroyed before reaching this
         function by arithmetic, coercion, rounding, copying, or serialization performed
         on it (`ratio + 0.0`, `float(ratio)`, `round(ratio, N)`, a JSON round-trip, etc.
         -- see `CompletionRatio`'s docstring for the full list). Once that has happened,
         this function has no way to tell the two cases apart: a bare float carries no
         information about whether counts once existed and were lost, or never existed at
         all. Both land on this same honestly-imprecise fallback, documented as exactly
         this limited -- not silently pretended to be exact either way.

        Note on `None` vs. `UNKNOWN` for `completed_count`/`assigned_count`: as with
        `teacher_override` elsewhere in this function, left at their `None` DEFAULT means
        "not explicitly supplied here." Explicitly passing the `UNKNOWN` sentinel for one
        of them (while still supplying both keyword arguments) means "I am opting into
        the exact-count style, but this count is itself unavailable" -- which still
        counts as "both supplied" for the "must be supplied together" check, and
        correctly yields an UNKNOWN gate (bypassing any carried counts on `completion`,
        per precedence order 1 above).

    `completion` therefore now defaults to `None` (UNKNOWN) rather than being a required
    positional argument -- a caller using only the explicit-kwargs exact-count style
    never needs to pass a redundant `completion` value at all. Every existing caller that
    supplies `completion` explicitly is completely unaffected, and every value
    `compute_completion` itself ever returns is automatically exact once it reaches this
    function, with no change to the call site.

    Order of operations (R1 fix, Codex GPT-5.6 SOL review R-A re-check; see
    GRADING_POLICY_SPEC.md §7.3): domain validation of every SUPPLIED (non-UNKNOWN/None)
    value -- completion, work_aggregate, assessment_aggregate, teacher_override, AND (as
    of the C1 remediation) completed_count/assigned_count -- happens FIRST,
    unconditionally, before override precedence is applied. Only THEN is the override
    checked and, if present, returned. This is deliberate: a teacher override may resolve
    genuine UNAVAILABILITY (UNKNOWN completion/aggregate -- see below), but it must NEVER
    mask a MALFORMED known value. If completion=1.2, an out-of-range assessment_aggregate,
    a malformed completed_count/assigned_count pair (e.g. completed_count exceeding
    assigned_count), or a completed_count/assigned_count pair that CONTRADICTS a carrying
    `completion`'s own counts, is supplied alongside a perfectly valid override, that is
    still a defect and still raises PolicyDomainError -- the override does not get a
    chance to "cover for" a bad known input by short-circuiting before validation runs.
    (An earlier version of this function validated the override and returned it before
    checking completion/work_aggregate/assessment_aggregate at all, which let those
    malformed KNOWN values sail through unexamined whenever an override happened to be
    present. That was itself the R1 defect; this ordering fixes it, and remains
    unchanged in v2.0 and by the C1 remediation.)

    UNKNOWN propagation (dossier §15 item 1, "Unknown != zero"): if the completion gate
    (via any of the three calling styles) is undeterminable, or work_aggregate, or
    assessment_aggregate is UNKNOWN/None (and there is no teacher override), the branch
    is undeterminable and the quarter grade is UNKNOWN -- never 0, never a silently-picked
    branch, never fabricated credit. UNKNOWN/None values are NOT domain-validated (there
    is nothing to validate -- they represent unavailability, not a malformed value) and
    REMAIN fully overridable: a teacher override still wins over an UNKNOWN completion/
    aggregate exactly as before. Availability (UNKNOWN, overridable) and malformation
    (PolicyDomainError, never overridable) are kept strictly distinct.

    OPEN-09 (RESOLVED by RC 2026-07-24): "Full precision internally. Round ONLY the
    student-facing final-grade DISPLAY to one decimal." This function therefore performs
    NO rounding at all, at any point -- the v1.0 `round_ndigits` parameter is REMOVED.
    Callers who need a display-formatted value must call
    `round_final_grade_for_display` / `final_grade_display_string` on this function's
    result; the result of THIS function must never itself be rounded before being used
    in any further computation or synced to Schoology.

    Domain (§7): once known (not None/UNKNOWN), `completion` must be a finite number in
    [0, 1]; `assessment_aggregate` must be a finite number in [0, 100] (extra credit
    never touches ASSESSMENT -- PREF-04.5 -- so its scale is unchanged from v1.0).
    `work_aggregate` and `teacher_override` (when supplied), by contrast, are now
    validated only as finite non-negative numbers with NO upper bound: OPEN-15's ruling
    means WORK may exceed 100 (extra credit raises the numerator but not the
    denominator), so a quarter grade -- and any override matching an above-100 WORK
    value -- may also exceed 100. RC's ruling does not state an explicit upper bound on
    the quarter grade or the override; removing their [0, 100] ceiling follows directly
    from "WORK may exceed 100," not from an independent invented policy. A violation
    raises PolicyDomainError instead of silently flowing through the max/average
    arithmetic -- e.g. completion > 1.0, a negative work_aggregate, or an
    out-of-[0,100]-range assessment_aggregate is a malformed input, not an UNKNOWN
    evidence state, and is never clamped or coerced. This validation runs for ALL
    supplied values regardless of whether an override is also present (see "Order of
    operations" above). `completed_count`/`assigned_count`, when both supplied, share
    `compute_completion`'s domain exactly (see `_validate_completion_counts`).
    """
    # Validate the domain of every SUPPLIED (known) value first -- including the
    # override itself -- BEFORE any override precedence is applied. UNKNOWN/None values
    # are skipped here (that is availability, not malformation) and remain overridable.
    if not _is_unknown(completion):
        completion = _require_in_range(completion, "completion", 0, 1)
    if not _is_unknown(work_aggregate):
        # OPEN-15 (RESOLVED): WORK may exceed 100, so no upper bound here.
        work_aggregate = _require_non_negative(work_aggregate, "work_aggregate")
    if not _is_unknown(assessment_aggregate):
        # PREF-04.5: extra credit never touches ASSESSMENT, so its [0, 100] scale stands.
        assessment_aggregate = _require_in_range(assessment_aggregate, "assessment_aggregate", 0, 100)
    if teacher_override is not None:
        # OPEN-15 (RESOLVED): an override matching an above-100 WORK value must not be
        # rejected, so teacher_override shares work_aggregate's unbounded domain.
        teacher_override = _require_non_negative(teacher_override, "teacher_override")

    # C1 (HIGH, Codex review 2026-07-24): the exact-count gate. `completed_count`/
    # `assigned_count` are keyword-only and opt-in (default None = "not explicitly
    # supplied here"). When BOTH are supplied, they are validated here -- BEFORE
    # override precedence, exactly like every other supplied value above.
    counts_supplied = completed_count is not None or assigned_count is not None
    if counts_supplied and (completed_count is None or assigned_count is None):
        raise PolicyDomainError(
            "completed_count and assigned_count must be supplied together for the "
            "exact-count gate decision (C1) -- one without the other cannot determine "
            "a ratio."
        )

    # C1 hardening (peer-review follow-up, same day): a `completion` produced by
    # `compute_completion` carries its own exact counts (see `CompletionRatio`). Recover
    # them here so the ORDINARY `compute_quarter_grade(w, a, compute_completion(c, n))`
    # calling sequence is exact by construction, with no extra effort from the caller.
    carried_counts: Optional[Tuple[int, int]] = None
    if isinstance(completion, CompletionRatio):
        carried_counts = (completion.completed_count, completion.assigned_count)

        # V1 (HIGH, Codex re-check 2026-07-24) -- crafted/corrupted-ratio defense: a
        # CompletionRatio's carried counts are only guaranteed consistent with its own
        # float value when the object was produced by compute_completion.
        # completed_count/assigned_count are read-only (see that class), which blocks
        # MUTATING a genuine ratio after construction, but nothing stops a caller from
        # hand-constructing a CompletionRatio directly with a float value that never
        # matched its own counts in the first place. Verify the ratio's own float value
        # equals the exact fraction its own carried counts imply BEFORE trusting those
        # counts for the gate decision below -- and before override precedence, like
        # every other supplied value validated above. This provably cannot fire for any
        # ratio compute_completion itself can produce (float(Fraction(a, b)) == a / b
        # for every valid non-negative integer pair with b > 0 -- both are the same
        # correctly-rounded double for the same exact rational value). A mismatch means
        # this is a crafted/corrupted ratio, not a genuine compute_completion result -- a
        # caller/data defect, never UNKNOWN (§7).
        carried_completed, carried_assigned = carried_counts
        try:
            expected_ratio = float(fractions.Fraction(carried_completed, carried_assigned))
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            raise PolicyDomainError(
                f"completion carries completed_count={carried_completed!r}/"
                f"assigned_count={carried_assigned!r}, which cannot form a valid ratio "
                f"({exc}) -- this is not a genuine compute_completion result."
            ) from exc
        if float(completion) != expected_ratio:
            raise PolicyDomainError(
                f"completion's float value ({float(completion)!r}) does not match the "
                f"exact ratio its own carried counts imply ({carried_completed}/"
                f"{carried_assigned} = {expected_ratio!r}) -- this is a crafted or "
                "corrupted CompletionRatio, not a genuine compute_completion result, and "
                "is never trusted for the exact-count gate decision."
            )

    if (
        counts_supplied
        and carried_counts is not None
        and not (_is_unknown(completed_count) or _is_unknown(assigned_count))
    ):
        # Both an explicit kwarg pair AND a completion carrying its own counts were
        # supplied -- they must describe the SAME evidence. Disagreement is a caller
        # defect (contradictory inputs for the same decision), not a policy question,
        # and is caught here, before override precedence, like every other malformed
        # supplied value.
        validated_kwarg_counts = _validate_completion_counts(completed_count, assigned_count)
        if validated_kwarg_counts != carried_counts:
            raise PolicyDomainError(
                "completed_count/assigned_count kwargs "
                f"({validated_kwarg_counts[0]}/{validated_kwarg_counts[1]}) disagree "
                f"with the counts carried by the `completion` argument "
                f"({carried_counts[0]}/{carried_counts[1]}) -- these must describe the "
                "same evidence; supply only one source of truth for the gate."
            )

    exact_gate: Union[bool, _Unknown, None] = None
    if counts_supplied:
        # Explicit kwargs take precedence over anything carried on `completion`.
        # compute_completion_threshold_met performs its own UNKNOWN/domain handling,
        # identical to compute_completion's -- including raising PolicyDomainError here,
        # before the override check below, for a malformed known count pair.
        exact_gate = compute_completion_threshold_met(completed_count, assigned_count)
    elif carried_counts is not None:
        exact_gate = compute_completion_threshold_met(*carried_counts)

    # Override precedence: only now, after every supplied value (including the exact
    # counts, if any) has been validated, does a present override win.
    if teacher_override is not None:
        return teacher_override

    if _is_unknown(work_aggregate) or _is_unknown(assessment_aggregate):
        return UNKNOWN

    if counts_supplied or carried_counts is not None:
        # C1: exact counts (explicit kwargs, or carried on a CompletionRatio) take
        # precedence over a bare float `completion` entirely -- the float value is not
        # consulted as a fallback here.
        if _is_unknown(exact_gate):
            return UNKNOWN
        at_or_above = exact_gate
    else:
        if _is_unknown(completion):
            return UNKNOWN
        # OPEN-08 (RESOLVED by RC 2026-07-24): compare the EXACT completion ratio -- no
        # rounding may be introduced before this comparison, under any circumstance.
        # (This bare-float path is reached ONLY when `completion` carries no counts of
        # its own and no explicit completed_count=/assigned_count= kwargs were supplied
        # -- see the docstring's calling-style precedence order. It remains documented
        # as subject to representation error at the boundary.)
        if COMPLETION_THRESHOLD_INCLUSIVE:
            at_or_above = completion >= COMPLETION_THRESHOLD
        else:
            at_or_above = completion > COMPLETION_THRESHOLD

    if at_or_above:
        result = max(work_aggregate, assessment_aggregate)
    else:
        result = (work_aggregate + assessment_aggregate) / 2.0

    # OPEN-09 (RESOLVED): no rounding here -- full precision is returned; display
    # rounding happens only in round_final_grade_for_display / final_grade_display_string.
    return result


def round_final_grade_for_display(value: Value) -> Union[float, _Unknown]:
    """
    OPEN-09 (RESOLVED by RC 2026-07-24; rounding MODE AMENDED by RC 2026-07-24, NT16-B):
    rounds `value` to FINAL_GRADE_DISPLAY_DECIMALS (1, loaded from JSON) for
    STUDENT-FACING DISPLAY ONLY.

    This is a display formatting step, not a computation. Internal computation
    (`compute_quarter_grade`, `compute_work_aggregate`, `compute_component_percentage`,
    `compute_assessment_aggregate`, `compute_completion`) stays full precision; the
    rounded value this function returns must NEVER be fed back into any of those
    functions, and must never be synced to Schoology as if it were the underlying score
    -- Schoology keeps native (unrounded) earned/possible totals, and reconciliation
    logic must compare the underlying full-precision values, never this display-rounded
    one, or it risks mistaking ordinary display rounding for a substantive divergence.

    AMENDMENT (NT16-B, RC 2026-07-24, a later same-day ruling than the original OPEN-09
    ruling above) -- the rounding MODE is now DECIDED, not an implementation guess. RC's
    verbatim ruling: "Use conventional decimal ROUND_HALF_UP for the student-facing
    one-decimal display. Example: 89.25 -> 89.3. Do not use Python binary-float round()
    or half-even behavior for the display contract. Keep full precision internally. Do
    not round before the 40% branch decision. Schoology reconciliation compares
    underlying values; display rounding cannot conceal real divergence." This function
    therefore rounds via `Decimal(value).quantize(exponent, rounding=ROUND_HALF_UP)`, NOT
    Python's builtin `round`.

    HISTORY (C5, MEDIUM, Codex review 2026-07-24; superseded by the amendment above) --
    this function previously used Python's builtin `round`, whose tie-breaking rule is
    HALF-EVEN ("banker's rounding"): a value exactly halfway between two representable
    one-decimal results rounds to whichever of the two has an EVEN final digit, not
    always up (`round(0.25, 1) == 0.2`, `round(0.35, 1) == 0.3`). RC's original OPEN-09
    ruling fixed "round the display to one decimal" but said NOTHING about which
    tie-breaking mode to use, so half-even -- Python's default, not a value RC's text
    specified -- was FIRST stated here as an IMPLEMENTATION READING pending RC
    confirmation, not itself a ruling (the same "do not invent silently" discipline
    already applied to OPEN-11's excused/unknown reading, GRADING_POLICY_SPEC.md §4.1).
    RC has now directly confirmed HALF-UP instead, per the amendment above -- the
    half-even reading was never a ruling, and this HISTORY paragraph is retained only as
    an audit trail of what this package guessed before RC's amendment, not as a live
    description of current behavior. No new OPEN-NN id is minted for the amendment;
    OPEN-09 remains RESOLVED (the resolved-item register stays closed at
    OPEN-01..OPEN-19).

    HALF-UP tie-breaking, concretely, at one decimal (RC's own worked example):

        round_final_grade_for_display(89.25) == 89.3
        round_final_grade_for_display(0.25)  == 0.3

    A tie can only arise from a value that is an EXACT binary midpoint at this display
    precision. Among ordinary `.x5`-at-the-second-decimal values, this is a narrower set
    than it looks, and not every one of them actually DISCRIMINATES half-up from
    half-even:

      - `89.75` is ALSO an exact binary midpoint, but its preceding digit (`7`) is ODD, so
        half-even rounds UP to the even `89.8` -- the SAME result half-up gives.
        `round_final_grade_for_display(89.75) == 89.8` under EITHER mode; this is an
        agreement tie, not evidence of which mode is active, and this module's test
        suite labels it as such rather than mis-citing it as proof of the mode.
      - `0.35` and `89.35` look like `.x5` ties but are NOT exact binary midpoints at all:
        as a Python `float`, `0.35` is actually `0.34999999999999997779...`, strictly
        BELOW its nominal midpoint, so BOTH half-up and half-even round it DOWN to `0.3`
        (and `89.35` down to `89.3`). These remain valid regression pins -- they guard
        against an unrelated class of defect, such as a wrong display-decimals exponent
        -- but they are non-discriminating between half-up and half-even and must never
        be cited as proof of the rounding mode.

    Construction detail: this function builds `Decimal` directly from the binary `float`
    `value` (never from `str(value)`/`repr(value)`) so the exact binary value -- the same
    value every internal computation in this module already operates on -- is what gets
    rounded, with no separate repr-based rounding step (which would itself be a hidden
    double-rounding hazard) introduced at display time. The quantization `exponent` is
    DERIVED from `FINAL_GRADE_DISPLAY_DECIMALS` (`Decimal(1).scaleb(-FINAL_GRADE_DISPLAY_
    DECIMALS)`) rather than hard-coded, so this function stays correct if that
    JSON-loaded constant ever changes.

    UNKNOWN passes through UNCHANGED (never becomes 0 or a fabricated rounded number) --
    see `final_grade_display_string` for the student-facing string form of an UNKNOWN
    grade.
    """
    if _is_unknown(value):
        return UNKNOWN
    value = _require_number(value, "value")
    exponent = Decimal(1).scaleb(-FINAL_GRADE_DISPLAY_DECIMALS)
    return float(Decimal(value).quantize(exponent, rounding=ROUND_HALF_UP))


def final_grade_display_string(value: Value) -> str:
    """
    Formats `value` as a one-decimal (FINAL_GRADE_DISPLAY_DECIMALS) student-facing
    string, e.g. "87.5". If `value` is UNKNOWN/None, returns UNKNOWN_DISPLAY_TOKEN (an
    em dash, "—") rather than "0" or "0.0" -- OPEN-16 (RESOLVED by RC 2026-07-24):
    "Student-facing display = dash / 'not enough evidence', never zero." A grade that
    cannot yet be computed must never be shown to a student or a teacher as a zero, which
    would misrepresent "not enough evidence" as "you have earned nothing."

    UNKNOWN_DISPLAY_TEXT ("not enough evidence") is the accessible/long-form equivalent
    of UNKNOWN_DISPLAY_TOKEN, for contexts (screen readers, tooltips, print packets)
    where a bare dash is not descriptive enough on its own.
    """
    if _is_unknown(value):
        return UNKNOWN_DISPLAY_TOKEN
    rounded = round_final_grade_for_display(value)
    return f"{rounded:.{FINAL_GRADE_DISPLAY_DECIMALS}f}"
