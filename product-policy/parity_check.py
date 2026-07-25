"""
parity_check.py -- NT15 product-policy Deliverable D3 (Schoology projection & reconciliation).

Package: NT15 product-policy · Version: 2.0 · Date: 2026-07-24
Source of authority: RC final decisions, 2026-07-24 (Grok preference interview + RC
clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
Status: Authoritative -- gates all future Desk / grading / Schoology implementation.

Traces to PREF-05 (Schoology role & reconciliation), with PREF-11 (organization) and
PREF-03 (the grade formula being projected). See SCHOOLOGY_PROJECTION_CONTRACT.md for
the normative prose and schoology_projection.v2.json for the machine-readable contract.

NO-LIVE-WRITE (normative, see contract §9): this module performs NO network access, NO
Schoology REST/GraphQL/API call, NO OAuth handshake, NO CDP/browser automation, and NO
write of any kind against a live Schoology tenant. It operates exclusively over local,
synthetic fixture JSON files under fixtures/schoology/. Schoology course/section IDs do
not exist yet (NT15 brief §0) -- every identifier used here is an invented placeholder.

--------------------------------------------------------------------------------------
NT16 (v2.0) supersession -- OPEN-15/OPEN-19's arithmetic is now DECIDED, OPEN-09's
rounding discipline and OPEN-16's zero-denominator rule are now encoded in this harness.
--------------------------------------------------------------------------------------
v1.0 combined WORK's three components by plain scalar addition and reduced multiple
same-kind items (several packets; several quizzes + topic assessments) by a simple
unweighted average -- both were explicitly labeled provisional, fixture-only
conventions, never asserted as decided upstream policy (OPEN-15, OPEN-19). RC issued
final rulings on both on 2026-07-24 (see grading_policy.v2.json / GRADING_POLICY_SPEC.md
§1.1, §8). This version:

  OPEN-15 (RESOLVED) -- `compute_work_aggregate`'s three-scalar-addition signature is
    REPLACED by the point-based earned/possible signature RC decided:
        WORK = 100 * (packet_points_earned + participation_points_earned + extra_credit_points_earned)
               / (packet_points_possible + participation_points_possible)
    WORK may exceed 100 (extra credit raises the numerator only). Zero denominator falls
    to OPEN-16 below.
  OPEN-19 (RESOLVED) -- `_average_percentage`'s unweighted-average fixture convention is
    REPLACED by `_points_weighted_percentage`, which delegates to the sibling module's
    DECIDED point-weighted reduction (`compute_assessment_aggregate` /
    `compute_component_percentage`): `100 * sum(points_earned) / sum(points_possible)`.
    Equal-averaging per-item percentages when possible-points differ is FORBIDDEN.

    V3 FIX (Codex re-check, HIGH, RESOLVED by RC 2026-07-24): this OPEN-19 hermetic
    fallback -- `_local_compute_assessment_aggregate`, used ONLY when
    `grading_policy_ref.py` is absent at runtime -- silently reimplemented the ORIGINAL
    C4 defect its own docstring claimed to have already fixed: it never enforced the
    packaged path's strict per-item `points_earned <= points_possible` domain check, so a
    malformed item (e.g. `(120, 100)`) silently produced an out-of-domain 120.0 for
    ASSESSMENT instead of raising -- the same C4 defect (extra credit never touches
    ASSESSMENT, PREF-04.5), just reintroduced on the fallback path the packaged path had
    already fixed. `_local_compute_assessment_aggregate` now enforces the identical
    strict check -- raising the SAME `PolicyDomainError` type the packaged path raises
    (never UNKNOWN, never a clamp) -- see that function's own docstring and
    `test_parity_check.py`'s forced-fallback test group. The sibling
    `_local_compute_work_aggregate` and `_local_compute_quarter_grade` fallbacks were
    also checked for the same class of divergence (a domain violation the packaged path
    raises on, but the local fallback silently let through): `_local_compute_work_aggregate`
    was missing the packaged path's non-negative-input validation (now added), and
    `_local_compute_quarter_grade` was missing the packaged path's completion-in-[0,1] /
    assessment-in-[0,100] / work-non-negative validation (now added). None of this
    module's local fallbacks may ever again silently diverge from the packaged formula
    each one claims to reimplement identically.
  OPEN-16 (RESOLVED) -- no eligible designated work/participation (zero denominator) =>
    completion/WORK/quarter grade all UNKNOWN, never a fabricated zero. This harness
    enforces the Schoology-side corollary too: the projector never fabricates a synthetic
    zero-scored/zero-points assignment to force a grade into being computable, and an
    all-UNKNOWN student still reconciles as UNKNOWN, never a forced number (see
    `project_course`, `test_parity_check.py`'s zero-denominator / no-fabricated-zero
    tests).
  OPEN-09 (RESOLVED) -- full precision internally; only the student-facing DISPLAY
    rounds to one decimal. Schoology keeps native (unrounded) earned/possible totals, and
    A2 never publishes a rounded display value into Schoology in the first place. This
    harness's substantive comparison ALWAYS runs on full-precision underlying values, at
    plain numeric `tolerance`, with NO exception -- rounding NEVER forgives a difference.

    C2 FIX (Codex review, HIGH, RESOLVED 2026-07-24): v2.0's FIRST implementation of this
    ruling misread "must not mistake display rounding for substantive divergence" as
    PERMISSION TO FORGIVE a difference whenever the caller declared the Schoology-side
    figure display-rounded -- `_rounding_only_difference()` rounded BOTH figures and a raw
    divergence was silently converted to `divergent: False`. That reading was wrong: the
    ruling bans FALSE ALARMS over cosmetic rounding; it never authorizes suppressing a
    genuine underlying difference. `_rounding_only_difference()` and its forgiveness
    branch (`divergent = raw_divergent and not rounding_only_difference`) are DELETED --
    there is no code path left in this module that can turn a raw divergence into
    `divergent: False` on account of rounding.

    `check_student_parity`'s `schoology_value_is_display_rounded` parameter still exists
    -- a caller may DECLARE that the Schoology-side figure it is comparing against is
    itself already display-rounded rather than full precision (the one legitimate case:
    reconciling against a real, already-rounded external figure once a live Schoology
    tenant exists) -- but that declaration no longer changes whether a difference is
    flagged `divergent`. It changes only what the report may HONESTLY claim about the
    comparison: a degraded (display-rounded) basis sets `comparison_basis` to name the
    limitation and forces `underlying_convergence_established` to `False` -- even when the
    observed numbers happen to match -- so no reader or downstream consumer can mistake
    "consistent with the rounded display" for "the underlying numbers agree." Only a
    comparison run on the default, undeclared, full-precision basis that finds no
    difference beyond `tolerance` sets `underlying_convergence_established` to `True` --
    that is the ONLY basis on which this harness ever asserts genuine convergence.

WHAT THIS MODULE DOES
----------------------
1. Computes A2's authoritative expected quarter grade for a student, by genuinely
   importing and reusing grading_policy_ref.py (the sibling NT15 D2 deliverable, owned
   by a parallel workstream) when it is present at runtime -- see `_load_grading_policy_ref`.
   If that module is absent, a local reimplementation is used instead (see
   `_local_compute_work_aggregate` / `_local_compute_quarter_grade` /
   `_local_compute_assessment_aggregate`) so this module remains independently runnable
   and hermetic. This local fallback is not a second policy authority -- every branch of
   it mirrors a DECIDED RC ruling (PREF-03.5/.6, OPEN-15, OPEN-19), never a different or
   independently-invented formula than the sibling module's own.
2. Simulates what Schoology's NATIVE gradebook would compute from the SAME granular,
   per-assignment evidence once it has been projected into Schoology as individual
   points-based assignments (see `compute_schoology_native_grade`). This is a flat
   points-earned / points-possible ratio across everything posted, with extra-credit-
   flagged assignments contributing to the numerator only (never the denominator) and
   ungraded/unavailable assignments excluded from the ratio entirely. This is ASSUMPTION-3
   in SCHOOLOGY_PROJECTION_CONTRACT.md §4.5 / schoology_projection.v2.json's
   feasibility_verdict.assumptions_to_confirm -- flagged there as unverified against a
   real Schoology tenant, not asserted as fact. This computation is UNAFFECTED by the
   OPEN-15/OPEN-19 WORK-arithmetic rulings above -- it was always a flat points ratio.
3. Compares the two and reports divergence STRUCTURALLY -- never silently equal, never
   auto-resolved (contract §8). UNKNOWN never becomes 0 (dossier §15 item 1): if A2's
   authoritative grade is UNKNOWN, the report is ALWAYS flagged divergent regardless of
   what Schoology's native figure happens to compute, because a plausible-looking native
   number must never be mistaken for -- or silently reconciled against -- an unresolved
   authoritative state. Reconciliation is UNDERLYING-ONLY (OPEN-09; C2 fix, RESOLVED
   2026-07-24): a numeric difference between the two full-precision values is NEVER
   forgiven, on either comparison basis, with no exception -- see `check_student_parity`
   for the `comparison_basis` / `underlying_convergence_established` fields that report,
   rather than suppress, a degraded (declared display-rounded) comparison.
4. Projects a course/lesson catalog into a deterministic, idempotent set of assignment
   records with stable external keys and deep-link templates (see `project_course`),
   gating projection by the seven canonical Desk lesson states (only `today`, `released`,
   `completed`, and `temporarily-unavailable` are ever projected; `unreleased` and
   `skipped` never are; `optional-catalog` only when explicitly assigned by a teacher --
   mirrors qb.select()'s include_optional opt-in and CLAUDE.md's 4-1 policy). This
   projection ONLY ever emits records that trace back to a real catalog entry -- it never
   fabricates a synthetic zero-scored/zero-points assignment purely to make some
   downstream ratio computable (OPEN-16, RESOLVED).

Standard library only. No network. No dependency on any file outside product-policy/.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, Tuple

HERE = Path(__file__).resolve().parent
FIXTURES_DIR = HERE / "fixtures" / "schoology"
GRADING_POLICY_REF_PATH = HERE / "grading_policy_ref.py"

# parity_check's own JSON-friendly UNKNOWN sentinel (a plain string, unlike
# grading_policy_ref's dedicated _Unknown object) -- see dossier §15 item 1.
UNKNOWN = "UNKNOWN"

COMPLETION_THRESHOLD = 0.40  # PREF-03.4, inclusive at exactly 0.40 -- mirrors the shared
# constant in grading_policy.v2.json's "constants" block. Used ONLY by the local
# fallback formula; when grading_policy_ref.py is importable its own constant is used.

# OPEN-09 (RESOLVED by RC 2026-07-24): the student-facing display precision -- mirrors
# grading_policy.v2.json's "final_grade_display_decimals" constant (1). Documentary only
# as of the C2 fix (Codex review, HIGH, RESOLVED 2026-07-24): it is no longer consulted
# to forgive a numeric difference (that forgiveness path -- `_rounding_only_difference`
# -- has been deleted; see the comment block above `_COMPARISON_BASIS_FULL_PRECISION`).
# It is retained here purely to describe, for a reader, what precision a real Schoology
# tenant's DISPLAY would show a student -- it plays no role in `check_student_parity`'s
# divergence verdict. This harness never rounds any of its own computed figures --
# rounding is display-only, never internal (OPEN-09).
FINAL_GRADE_DISPLAY_DECIMALS = 1


# --------------------------------------------------------------------------------------
# Defensive import of the sibling D2 deliverable (grading_policy_ref.py).
# --------------------------------------------------------------------------------------

def _load_grading_policy_ref(path: Path = GRADING_POLICY_REF_PATH) -> Optional[ModuleType]:
    """
    Attempt to import grading_policy_ref.py from the given path (defaults to the real
    sibling file in this directory). Returns the imported module on success, or None on
    ANY failure (file missing, syntax error, import error, etc.) -- callers must treat
    None as "fall back to the local formula", never raise. `path` is a parameter (not
    hard-coded) so tests can exercise the "absent" branch deterministically by pointing
    at a nonexistent path, without ever touching the real sibling file.
    """
    if not path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("grading_policy_ref", path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


GRADING_POLICY_REF = _load_grading_policy_ref()

if GRADING_POLICY_REF is not None:
    # Prefer the sibling module's own display-precision constant when it is loadable --
    # it is loaded FROM grading_policy.v2.json, the single source of truth. The local
    # literal above is only a hermetic fallback for when the sibling is absent.
    FINAL_GRADE_DISPLAY_DECIMALS = GRADING_POLICY_REF.FINAL_GRADE_DISPLAY_DECIMALS


# --------------------------------------------------------------------------------------
# V3 FIX (Codex re-check, HIGH, RESOLVED by RC 2026-07-24): a shared PolicyDomainError type
# and validation helpers for this module's LOCAL hermetic fallback formulas
# (`_local_compute_assessment_aggregate` / `_local_compute_work_aggregate` /
# `_local_compute_quarter_grade`), so a malformed KNOWN input on the fallback path raises
# the SAME error type the packaged grading_policy_ref path raises for the identical
# condition -- never UNKNOWN, never a silently clamped/coerced value -- mirroring
# grading_policy_ref.PolicyDomainError / _require_non_negative / _require_in_range exactly.
#
# When grading_policy_ref.py IS importable at import time, `PolicyDomainError` here IS
# that module's own exception class (not merely a look-alike) -- so a caller that catches
# `parity_check.PolicyDomainError` gets identical behavior on EITHER path, including the
# forced-fallback path exercised by test_parity_check.py's forced-fallback tests (which
# monkeypatch `GRADING_POLICY_REF` to None AFTER this binding already happened at import
# time, so the alias to the real sibling class survives). Only when grading_policy_ref.py
# is genuinely absent FROM THE START (`GRADING_POLICY_REF` is `None` at import time) does
# this module define its own local class -- the one case with no sibling class to alias.
# --------------------------------------------------------------------------------------

if GRADING_POLICY_REF is not None:
    PolicyDomainError = GRADING_POLICY_REF.PolicyDomainError
else:

    class PolicyDomainError(Exception):
        """parity_check's own domain-error type, used ONLY when grading_policy_ref.py is
        genuinely absent at runtime (no sibling PolicyDomainError class exists to alias).
        Semantically identical to grading_policy_ref.PolicyDomainError: raised when an
        input to one of this module's local fallback formulas is malformed or outside its
        declared domain -- never converted to UNKNOWN, 0, or a clamped/coerced value. See
        that class's own docstring (grading_policy_ref.py) for the full
        UNKNOWN-vs-PolicyDomainError rationale this module's local fallbacks mirror."""


def _local_require_number(value: Any, name: str) -> Any:
    """Mirrors grading_policy_ref._require_number's domain check, for use ONLY by this
    module's LOCAL (hermetic) fallback formulas -- see _local_compute_assessment_aggregate
    / _local_compute_work_aggregate / _local_compute_quarter_grade. Raises
    PolicyDomainError (never returns UNKNOWN, never clamps) unless `value` is a genuine,
    finite int/float (never a bool, never a string or other type masquerading as a
    number)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyDomainError(
            f"{name} must be a number (int or float), got {type(value).__name__}: {value!r}"
        )
    if not math.isfinite(value):
        raise PolicyDomainError(f"{name} must be finite (no NaN/+-inf), got {value!r}")
    return value


def _local_require_non_negative(value: Any, name: str) -> Any:
    """Mirrors grading_policy_ref._require_non_negative, for this module's LOCAL fallback
    formulas ONLY. Raises PolicyDomainError unless `value` is a finite number >= 0."""
    number = _local_require_number(value, name)
    if number < 0:
        raise PolicyDomainError(f"{name} must be non-negative, got {number!r}")
    return number


def _local_require_in_range(value: Any, name: str, lo: float, hi: float) -> Any:
    """Mirrors grading_policy_ref._require_in_range, for this module's LOCAL fallback
    formulas ONLY. Raises PolicyDomainError unless `value` is a finite number in
    [lo, hi]."""
    number = _local_require_number(value, name)
    if not (lo <= number <= hi):
        raise PolicyDomainError(f"{name} must be in [{lo}, {hi}], got {number!r}")
    return number


def _is_unknown_value(v: Any) -> bool:
    """True if `v` is parity_check's own UNKNOWN string, None, or (when the sibling
    module is loaded) that module's own UNKNOWN sentinel object."""
    if v is None or v == UNKNOWN:
        return True
    if GRADING_POLICY_REF is not None and v is GRADING_POLICY_REF.UNKNOWN:
        return True
    return False


def _to_ref_value(v: Any) -> Any:
    """Translate a parity_check-side UNKNOWN/None into grading_policy_ref's own UNKNOWN
    sentinel object before calling into that module; pass numeric values through unchanged."""
    if GRADING_POLICY_REF is not None and _is_unknown_value(v):
        return GRADING_POLICY_REF.UNKNOWN
    return v


def _from_ref_value(v: Any) -> Any:
    """Translate a value returned BY grading_policy_ref back into parity_check's own
    plain-string UNKNOWN sentinel so downstream code/reports never have to special-case
    that module's internal sentinel type."""
    if GRADING_POLICY_REF is not None and v is GRADING_POLICY_REF.UNKNOWN:
        return UNKNOWN
    return v


# --------------------------------------------------------------------------------------
# A2's authoritative expected-grade computation. `compute_a2_quarter_grade`'s branch logic
# delegates to grading_policy_ref.py (or mirrors RC's DECIDED PREF-03.5/.6 formula locally)
# when present/absent respectively. `compute_work_aggregate`'s three-component COMBINATION
# is now likewise a DECIDED formula (OPEN-15, RESOLVED by RC 2026-07-24) -- see the module
# docstring and SCHOOLOGY_PROJECTION_CONTRACT.md section 4.3.
# --------------------------------------------------------------------------------------

def compute_work_aggregate(
    packet_points_earned: Any,
    packet_points_possible: Any,
    participation_points_earned: Any,
    participation_points_possible: Any,
    extra_credit_points_earned: Any = 0.0,
) -> Any:
    """
    WORK aggregate (PREF-03.2; OPEN-15, RESOLVED by RC 2026-07-24) -- POINT-BASED:

        WORK = 100 * (packet_points_earned + participation_points_earned + extra_credit_points_earned)
               / (packet_points_possible + participation_points_possible)

    This REPLACES v1.0's plain three-scalar addition (`digital_packet_work_score +
    participation_points + extra_credit_points`), which was an explicitly-labeled
    unresolved-pending-RC placeholder. Only teacher-designated official evidence enters.
    Extra credit raises the numerator only, never the denominator -- there is no
    `extra_credit_points_possible` parameter, by design. WORK MAY EXCEED 100 -- there is
    no upper clamp. Zero denominator (`packet_points_possible + participation_points_possible
    == 0`) is UNKNOWN, never a fabricated 0 or 100 (OPEN-16, RESOLVED).

    Delegates to grading_policy_ref.compute_work_aggregate (the sibling D2 deliverable,
    this tranche's real, decided implementation) when present; falls back to
    `_local_compute_work_aggregate` -- an identical reimplementation of the SAME decided
    formula, never a different one -- when absent, so this module stays independently
    runnable and hermetic.
    """
    if GRADING_POLICY_REF is not None:
        result = GRADING_POLICY_REF.compute_work_aggregate(
            _to_ref_value(packet_points_earned),
            _to_ref_value(packet_points_possible),
            _to_ref_value(participation_points_earned),
            _to_ref_value(participation_points_possible),
            _to_ref_value(extra_credit_points_earned),
        )
        return _from_ref_value(result)
    return _local_compute_work_aggregate(
        packet_points_earned,
        packet_points_possible,
        participation_points_earned,
        participation_points_possible,
        extra_credit_points_earned,
    )


def _local_compute_work_aggregate(
    packet_points_earned: Any,
    packet_points_possible: Any,
    participation_points_earned: Any,
    participation_points_possible: Any,
    extra_credit_points_earned: Any = 0.0,
) -> Any:
    """RC's DECIDED point-based WORK formula (OPEN-15, RESOLVED by RC 2026-07-24),
    reimplemented locally ONLY for use when grading_policy_ref.py is absent at runtime --
    this is never a different formula than the sibling module's own, merely a hermetic
    stand-in for it.

    V3 FIX (Codex re-check, HIGH): this fallback previously skipped the packaged path's
    non-negative-input validation entirely (grading_policy_ref.compute_work_aggregate
    validates all five inputs via `_require_non_negative` before combining them) -- a
    negative or malformed known value would have silently flowed through this arithmetic
    instead of raising. It now enforces the identical check via `_local_require_non_negative`,
    raising PolicyDomainError (never UNKNOWN, never a clamp) for the same class of
    violation the packaged path rejects. There is still no `earned <= possible` check
    here (unlike ASSESSMENT) -- WORK legitimately may exceed 100 via extra credit, exactly
    as the packaged path allows."""
    if (
        _is_unknown_value(packet_points_earned)
        or _is_unknown_value(packet_points_possible)
        or _is_unknown_value(participation_points_earned)
        or _is_unknown_value(participation_points_possible)
        or _is_unknown_value(extra_credit_points_earned)
    ):
        return UNKNOWN
    packet_points_earned = _local_require_non_negative(packet_points_earned, "packet_points_earned")
    packet_points_possible = _local_require_non_negative(packet_points_possible, "packet_points_possible")
    participation_points_earned = _local_require_non_negative(
        participation_points_earned, "participation_points_earned"
    )
    participation_points_possible = _local_require_non_negative(
        participation_points_possible, "participation_points_possible"
    )
    extra_credit_points_earned = _local_require_non_negative(
        extra_credit_points_earned, "extra_credit_points_earned"
    )
    denominator = packet_points_possible + participation_points_possible
    if denominator == 0:
        return UNKNOWN  # OPEN-16, RESOLVED: no eligible designated work/participation -> UNKNOWN
    numerator = packet_points_earned + participation_points_earned + extra_credit_points_earned
    return 100.0 * numerator / denominator


def compute_assessment_aggregate(items: list) -> Any:
    """
    ASSESSMENT aggregate (PREF-03.3; OPEN-19, RESOLVED by RC 2026-07-24) -- POINT-WEIGHTED
    multi-item reduction over the combined lesson-quizzes + topic-assessments group:

        ASSESSMENT = 100 * sum(points_earned) / sum(points_possible)

    `items` is an iterable of `(points_earned, points_possible)` pairs. This REPLACES
    v1.0's `_average_percentage`'s simple unweighted-average fixture convention, which
    was never asserted as decided upstream policy. Equal-averaging per-item percentages
    when possible-points differ is FORBIDDEN by RC's ruling -- this function always
    computes the point-weighted ratio. Returns UNKNOWN if any pair contains an UNKNOWN
    value, or if `sum(points_possible) == 0` (OPEN-16, RESOLVED zero-denominator rule).

    Delegates to grading_policy_ref.compute_assessment_aggregate when present; falls back
    to `_local_compute_assessment_aggregate` (the identical decided formula) when absent.
    """
    if GRADING_POLICY_REF is not None:
        translated = [(_to_ref_value(e), _to_ref_value(p)) for (e, p) in items]
        result = GRADING_POLICY_REF.compute_assessment_aggregate(translated)
        return _from_ref_value(result)
    return _local_compute_assessment_aggregate(items)


def _local_compute_assessment_aggregate(items: list) -> Any:
    """RC's DECIDED point-weighted reduction (OPEN-19, RESOLVED by RC 2026-07-24),
    reimplemented locally ONLY for use when grading_policy_ref.py is absent at runtime --
    this now genuinely IS the identical decided arithmetic the packaged
    grading_policy_ref.compute_assessment_aggregate / compute_component_percentage
    enforce, not merely a same-shaped approximation of it.

    V3 FIX (Codex re-check, HIGH, RESOLVED by RC 2026-07-24): before this fix, this
    fallback silently OMITTED the packaged path's strict per-item
    `points_earned <= points_possible` domain check -- reimplementing the ORIGINAL C4
    defect its own (then-false) docstring claimed was already fixed. A malformed item
    such as `(120, 100)` used to flow straight through the arithmetic and return a bare
    120.0 -- an out-of-domain ASSESSMENT percentage -- instead of raising. Extra credit
    never touches ASSESSMENT (PREF-04.5), so `points_earned` exceeding `points_possible`
    on an ASSESSMENT item is ALWAYS a DATA DEFECT (a corrupted/mis-recorded score), never
    a legitimate policy outcome. This function now enforces that check identically to
    `compute_component_percentage`'s strict (`allow_above_100=False`) default that
    `compute_assessment_aggregate` always uses: every KNOWN item must satisfy
    `points_earned <= points_possible`, or this raises `PolicyDomainError` -- never
    UNKNOWN, never a clamp. Because every item individually satisfies that bound, the
    result is guaranteed to land in `[0, 100]` BY CONSTRUCTION, exactly as the packaged
    path guarantees.

    Validation and UNKNOWN-propagation ordering mirrors the packaged path exactly: an
    UNKNOWN/None item is skipped (contributes nothing to either sum) but does NOT
    short-circuit the loop -- every OTHER known item is still validated, so a malformed
    known item is never masked by an unrelated UNKNOWN item elsewhere in the same list.
    UNKNOWN is returned only after every item has been examined, and only if no
    known-item validation failure was found first (a PolicyDomainError always wins over
    UNKNOWN, since a domain violation is a defect, not merely unavailable evidence)."""
    earned_total = 0.0
    possible_total = 0.0
    saw_unknown = False
    for points_earned, points_possible in items:
        if _is_unknown_value(points_earned) or _is_unknown_value(points_possible):
            saw_unknown = True
            continue
        points_earned = _local_require_non_negative(points_earned, "points_earned")
        points_possible = _local_require_non_negative(points_possible, "points_possible")
        if points_earned > points_possible:
            raise PolicyDomainError(
                f"points_earned ({points_earned}) exceeds points_possible "
                f"({points_possible}) for a same-kind designated ASSESSMENT item -- this "
                "is a DATA DEFECT (OPEN-19; C4/V3, Codex review), not a policy question, "
                "and is never silently allowed to push the reduction above 100% -- extra "
                "credit never touches ASSESSMENT (PREF-04.5)."
            )
        earned_total += points_earned
        possible_total += points_possible
    if saw_unknown:
        return UNKNOWN
    if possible_total == 0:
        return UNKNOWN
    return 100.0 * earned_total / possible_total


def compute_a2_quarter_grade(work_aggregate: Any, assessment_aggregate: Any, completion_pct: Any) -> Any:
    """A2's authoritative PREF-03 quarter-grade formula: max/average gated on the 40%
    completion threshold (exact-ratio comparison, OPEN-08 RESOLVED), UNKNOWN-propagating
    (dossier §15 item 1). Delegates to grading_policy_ref.compute_quarter_grade when that
    module is importable. Returns full precision, never rounded (OPEN-09, RESOLVED) --
    display rounding is a separate, explicit step this module never performs internally."""
    if GRADING_POLICY_REF is not None:
        result = GRADING_POLICY_REF.compute_quarter_grade(
            _to_ref_value(work_aggregate), _to_ref_value(assessment_aggregate), _to_ref_value(completion_pct)
        )
        return _from_ref_value(result)
    return _local_compute_quarter_grade(work_aggregate, assessment_aggregate, completion_pct)


def _local_compute_quarter_grade(
    work_aggregate: Any, assessment_aggregate: Any, completion_pct: Any, threshold: float = COMPLETION_THRESHOLD
) -> Any:
    """RC's DECIDED PREF-03 quarter-grade formula (max/average gated on the 40% completion
    threshold), reimplemented locally ONLY for use when grading_policy_ref.py is absent at
    runtime -- never a different formula than the sibling module's own compute_quarter_grade,
    merely a hermetic stand-in for the narrow 3-positional-argument subset of it that
    parity_check.py actually calls (no teacher_override / exact-count kwargs -- this module
    never supplies those).

    V3 FIX (Codex re-check, HIGH): this fallback previously skipped ALL of the packaged
    path's domain validation entirely. grading_policy_ref.compute_quarter_grade validates
    every SUPPLIED (non-UNKNOWN) value BEFORE deciding whether the result is UNKNOWN -- a
    KNOWN value is validated even when a SIBLING value is UNKNOWN (see that function's own
    "Order of operations" docstring section) -- so a malformed known value (completion
    outside [0, 1], an out-of-[0, 100] assessment_aggregate, or a negative work_aggregate)
    used to flow straight through the max/average arithmetic unexamined. This now enforces
    the identical checks, in the identical order (validate every known value first; only
    THEN decide UNKNOWN), raising PolicyDomainError -- never UNKNOWN, never a clamp -- for
    the same class of violation the packaged path rejects. `work_aggregate` remains
    unbounded-non-negative (OPEN-15: WORK may exceed 100), matching the packaged path
    exactly -- there is no upper-bound check on it, by design.

    UNKNOWN-propagation is UNCHANGED by this fix: if any of the three (now-validated)
    values is UNKNOWN/None, the branch is undeterminable and this still returns UNKNOWN --
    never 0, never a silently-picked branch."""
    if not _is_unknown_value(completion_pct):
        completion_pct = _local_require_in_range(completion_pct, "completion_pct", 0, 1)
    if not _is_unknown_value(work_aggregate):
        work_aggregate = _local_require_non_negative(work_aggregate, "work_aggregate")
    if not _is_unknown_value(assessment_aggregate):
        assessment_aggregate = _local_require_in_range(assessment_aggregate, "assessment_aggregate", 0, 100)

    if _is_unknown_value(work_aggregate) or _is_unknown_value(assessment_aggregate) or _is_unknown_value(completion_pct):
        return UNKNOWN
    if completion_pct >= threshold:
        return max(work_aggregate, assessment_aggregate)
    return (work_aggregate + assessment_aggregate) / 2.0


# --------------------------------------------------------------------------------------
# Fixture-evidence reduction helpers.
#
# OPEN-19 (RESOLVED by RC 2026-07-24): multiple same-kind items (several lesson packets;
# several quizzes + topic assessments) reduce to ONE scalar via the POINT-WEIGHTED rule
# RC decided:
#     component_percentage = 100 * sum(points_earned) / sum(points_possible)
# This SUPERSEDES v1.0's fixture-only "simple unweighted average" convention, which was
# never asserted as decided upstream policy in the first place -- see
# grading_policy_ref.py's compute_component_percentage / compute_assessment_aggregate
# (the real, decided implementation `_points_weighted_percentage` below delegates to via
# `compute_assessment_aggregate` above) and GRADING_POLICY_SPEC.md section 8. Equal-
# averaging per-item percentages when possible-points differ is FORBIDDEN by this ruling;
# this harness never does it. OPEN-19 compounds with OPEN-15 (which governs how the WORK
# components combine once each same-kind group has already been reduced to an
# (earned, possible) pair) but is a distinct question: OPEN-15 governs the top-level WORK
# ratio; OPEN-19 governs how each same-kind item GROUP reduces to the pair OPEN-15's
# formula consumes. See SCHOOLOGY_PROJECTION_CONTRACT.md §4.3 for the full, refreshed
# discussion.
# --------------------------------------------------------------------------------------

def _points_weighted_percentage(assignments: list) -> Any:
    """Point-weighted multi-item reduction (OPEN-19, RESOLVED by RC 2026-07-24) for a
    same-kind evidence group expressed in this module's fixture shape (a list of dicts
    each carrying `points_earned`/`points_possible`/`status`) -- used here for the
    combined quiz + topic-assessment ASSESSMENT group. Delegates to
    `compute_assessment_aggregate` for the actual point-weighted arithmetic. Any
    ungraded/unavailable item in the group makes the WHOLE reduction UNKNOWN -- never
    silently dropped, never treated as zero (dossier §15 item 1). An empty group (nothing
    assigned in this category yet) is UNKNOWN too, via the same zero-denominator rule
    (OPEN-16, RESOLVED) `compute_assessment_aggregate` already applies to an empty
    `items` iterable -- no special-casing needed here for that case."""
    items = []
    for a in assignments:
        if a.get("status") != "graded" or a.get("points_earned") is None:
            return UNKNOWN
        items.append((a["points_earned"], a["points_possible"]))
    return compute_assessment_aggregate(items)


def _sum_points(assignments: list) -> Tuple[Any, Any]:
    """Sums already-graded per-item (points_earned, points_possible) pairs into a single
    (earned, possible) pair -- used for lesson-packet work, daily participation, and
    extra credit. OPEN-15's point-based `compute_work_aggregate` (RESOLVED by RC
    2026-07-24) needs points_POSSIBLE for packet work and participation, not merely a
    pre-reduced percentage/scalar the way v1.0's placeholder additive formula did -- this
    is the one structural change v2.0 requires here: `_sum_points` now yields earned AND
    possible, not earned alone.

    An empty list means nothing was assigned in this category yet -- contributes
    (0.0, 0.0): nothing to add to either side of `compute_work_aggregate`'s ratio,
    matching that function's own `extra_credit_points_earned=0.0` default-like behavior
    for "nothing here." A non-empty list containing an ungraded/unavailable item makes
    BOTH earned AND possible UNKNOWN for the whole group -- never silently partial, never
    a fabricated zero for evidence that exists but hasn't been graded yet (dossier §15
    item 1)."""
    if not assignments:
        return 0.0, 0.0
    earned_total = 0.0
    possible_total = 0.0
    for a in assignments:
        if a.get("status") != "graded" or a.get("points_earned") is None:
            return UNKNOWN, UNKNOWN
        earned_total += a["points_earned"]
        possible_total += a["points_possible"]
    return earned_total, possible_total


# The ONLY Schoology-native computation mode this simulator implements (B4 fix, Codex SOL
# review R-B): a flat points-earned/points-possible ratio across everything ACTUALLY
# published, unweighted by category. This is a deliberate choice, not an oversight -- the
# contract (§4.4) explicitly rejects inventing a weighted-category scheme that would only
# coincidentally mimic the conditional formula (that would misrepresent Schoology's actual
# capability as native parity). If a weighted-category mode is ever needed, it MUST be a
# separate, explicitly-named function -- never silently blended into this one -- and every
# report this module produces names the mode it used (`schoology_computation_mode` below)
# so no run ever compares under an unstated assumption. This computation is UNAFFECTED by
# the OPEN-15/OPEN-19 WORK-arithmetic rulings -- it was always, and remains, a flat
# points-earned/points-possible ratio over published evidence.
SCHOOLOGY_COMPUTATION_MODE = "flat_total_points"


def compute_schoology_native_grade(course_id: str, published_records: dict, fixture: dict) -> Any:
    """
    Simulates Schoology's native gradebook computation under `SCHOOLOGY_COMPUTATION_MODE`
    (SCHOOLOGY_PROJECTION_CONTRACT.md §4.5, ASSUMPTION-1) -- a flat points-earned /
    points-possible ratio, with extra-credit-flagged assignments contributing to the
    numerator only (not the denominator, matching a typical LMS "Extra Credit" assignment
    flag) and any ungraded/unavailable assignment excluded entirely from the ratio (a
    common LMS default for "no score entered yet" -- ASSUMPTION-3).

    Reconciles from what was ACTUALLY published (B4 fix): `published_records` must be the
    `external_key -> record` mapping `project_course()` actually produced for this course
    catalog, not an independent copy of the fixture's own per-item fields. For each score
    entry in `fixture`, this function looks up its `external_key`; if that key was never
    projected (e.g. the lesson was `unreleased`, or `optional-catalog` without explicit
    assignment), the entry contributes NOTHING to this ratio -- Schoology never received
    it, so it cannot be part of what Schoology natively computes. For entries that WERE
    published, the published record's `points_possible`/`extra_credit` (not the fixture
    entry's own duplicated copies) are authoritative for this computation, since that is
    what was actually sent to Schoology.

    Returned on the SAME 0-100 percentage scale as A2's aggregates so the two figures are
    directly comparable. This number is INFORMATIVE ONLY -- it is NEVER the authoritative
    published grade (contract §4.5).
    """
    all_assignments = (
        list(fixture.get("packet_assignments", []))
        + list(fixture.get("participation_assignments", []))
        + list(fixture.get("extra_credit_assignments", []))
        + list(fixture.get("quiz_assignments", []))
        + list(fixture.get("topic_assessment_assignments", []))
    )
    earned = 0.0
    possible = 0.0
    for a in all_assignments:
        key = external_key(course_id, a["lesson_id"], a["artifact_type"], a["artifact_id"])
        record = published_records.get(key)
        if record is None:
            continue  # never projected -- Schoology never received this evidence
        if a.get("status") != "graded" or a.get("points_earned") is None:
            continue  # ungraded/unavailable -- excluded from the native ratio (ASSUMPTION-3)
        earned += a["points_earned"]
        if not record.get("extra_credit", False):
            possible += record["points_possible"]
    if possible == 0:
        return UNKNOWN
    return 100.0 * earned / possible


# --------------------------------------------------------------------------------------
# Display-rounding-AWARE reporting (OPEN-09, RESOLVED by RC 2026-07-24) -- NOT
# rounding-forgiveness.
#
# C2 FIX (Codex review, HIGH, RESOLVED 2026-07-24): this section previously contained
# `_rounding_only_difference()`, a helper that rounded BOTH figures and let
# `check_student_parity` convert a raw divergence into `divergent: False` whenever the
# caller declared `schoology_value_is_display_rounded=True`. That was a misreading of
# RC's ruling -- "must not mistake display rounding for substantive divergence" bans
# FALSE ALARMS over cosmetic rounding; it is NOT permission to suppress a genuine
# underlying difference. The helper and its forgiveness branch are DELETED. There is no
# longer any function or code path in this module that can turn a raw divergence into
# `divergent: False` on account of rounding.
#
# The corrected reading: reconciliation is UNDERLYING-ONLY. The substantive comparison in
# `check_student_parity` ALWAYS runs on full-precision values at plain numeric
# `tolerance`, with no exception. `schoology_value_is_display_rounded` still exists as
# the one legitimate, explicit declaration this ruling calls for (a caller reconciling
# against a real, already-rounded external figure, once a live Schoology tenant exists,
# must be able to say so) -- but it no longer changes the divergence verdict. It changes
# only what the report may HONESTLY claim about the comparison basis -- see
# `_COMPARISON_BASIS_FULL_PRECISION` / `_COMPARISON_BASIS_DISPLAY_ROUNDED` and
# `check_student_parity`'s `comparison_basis` / `underlying_convergence_established`
# report fields below. A display-rounded-observation basis NEVER asserts genuine
# underlying convergence, even when the observed numbers happen to match -- convergence
# is asserted ONLY when the comparison actually ran on the full-precision basis and found
# no difference beyond `tolerance`.
# --------------------------------------------------------------------------------------

_COMPARISON_BASIS_FULL_PRECISION = "underlying-full-precision"
_COMPARISON_BASIS_DISPLAY_ROUNDED = (
    "display-rounded-observation -- underlying convergence NOT established"
)


# --------------------------------------------------------------------------------------
# Parity check for one student fixture.
# --------------------------------------------------------------------------------------

def check_student_parity(
    fixture: dict,
    course_catalog: Optional[dict] = None,
    tolerance: float = 1e-6,
    schoology_value_is_display_rounded: bool = False,
) -> dict:
    """
    Run one student fixture through BOTH computations (A2-authoritative and
    Schoology-native-simulated) over the SAME underlying evidence, and report divergence
    structurally. Never silently equal, never auto-resolved (contract §8).

    `course_catalog` defaults to `load_course_catalog()` (the synthetic
    course_section_synthetic.json fixture) when not supplied. The Schoology-native side
    reconciles from the records `project_course(course_catalog)` ACTUALLY produced (B4 fix)
    -- never from an independent re-derivation of the fixture's own per-item fields -- so
    the comparison reflects what was really published, not an assumed parallel copy of it.

    RECONCILIATION IS UNDERLYING-ONLY (OPEN-09, RESOLVED by RC 2026-07-24; C2 fix, Codex
    review, HIGH, RESOLVED 2026-07-24): the substantive comparison ALWAYS runs on
    full-precision underlying values at plain numeric `tolerance` -- rounding NEVER
    forgives a difference, on either comparison basis, with no exception. This corrects
    this module's own earlier (defective) reading, which converted a raw divergence into
    `divergent: False` whenever `schoology_value_is_display_rounded=True` was declared;
    that forgiveness path (`_rounding_only_difference`) has been deleted entirely -- see
    the module docstring's OPEN-09 section and the comment block above
    `_COMPARISON_BASIS_FULL_PRECISION` for the full history of the defect and its fix.

    `schoology_value_is_display_rounded` (default `False`) declares, for THIS comparison
    call only, that the `schoology_native_quarter_grade` figure being compared is itself
    already rounded to student-facing display precision (one decimal --
    `FINAL_GRADE_DISPLAY_DECIMALS`) rather than a full-precision underlying value -- the
    one legitimate case this parameter exists for: reconciling against a real,
    already-rounded external figure (e.g. a live Schoology display value, once a live
    tenant exists). It NO LONGER changes whether a numeric difference is flagged
    `divergent` -- that verdict is always the plain-tolerance comparison of whatever two
    figures this call actually has, full stop. What the declaration DOES change is what
    the report may honestly CLAIM about the comparison:
      - `comparison_basis` is set to `_COMPARISON_BASIS_FULL_PRECISION` for the ordinary,
        undeclared case, or to `_COMPARISON_BASIS_DISPLAY_ROUNDED` when this flag is
        `True` -- naming, rather than hiding, a degraded comparison basis.
      - `underlying_convergence_established` is `True` ONLY when the comparison ran on
        the full-precision basis AND no difference beyond `tolerance` was found. It is
        `False` whenever the basis is degraded (this flag is `True`) -- REGARDLESS of how
        small the observed difference is -- and `False` whenever `divergent` is `True`. A
        display-rounded observation NEVER proves the underlying figures agree; this
        boolean makes that impossible to mistake for "the underlying numbers agree."
    An `UNKNOWN` `a2_expected_quarter_grade` or `schoology_native_quarter_grade` is always
    surfaced as divergent regardless of this parameter (dossier §15 item 1) -- there is no
    numeric comparison to run in that case, so `underlying_convergence_established` is
    `False` and `delta` is `None`.
    """
    if course_catalog is None:
        course_catalog = load_course_catalog()
    course_id = course_catalog["course_id"]
    published_records = {r["external_key"]: r for r in project_course(course_catalog)}

    packet_earned, packet_possible = _sum_points(fixture.get("packet_assignments", []))
    participation_earned, participation_possible = _sum_points(fixture.get("participation_assignments", []))
    extra_credit_earned, _extra_credit_possible = _sum_points(fixture.get("extra_credit_assignments", []))
    assessment_aggregate = _points_weighted_percentage(
        list(fixture.get("quiz_assignments", [])) + list(fixture.get("topic_assessment_assignments", []))
    )
    completion_pct = fixture.get("completion_pct")

    work_aggregate = compute_work_aggregate(
        packet_earned, packet_possible, participation_earned, participation_possible, extra_credit_earned
    )
    a2_expected = compute_a2_quarter_grade(work_aggregate, assessment_aggregate, completion_pct)
    schoology_native = compute_schoology_native_grade(course_id, published_records, fixture)

    comparison_basis = (
        _COMPARISON_BASIS_DISPLAY_ROUNDED if schoology_value_is_display_rounded else _COMPARISON_BASIS_FULL_PRECISION
    )

    if _is_unknown_value(a2_expected):
        # UNKNOWN vs ANYTHING is ALWAYS surfaced -- a plausible-looking native number
        # must never be mistaken for, or silently reconciled against, an unresolved
        # authoritative state (dossier §15 item 1: unknown != zero). This includes the
        # OPEN-16 zero-denominator case: an all-UNKNOWN student (no eligible designated
        # work/participation/assessment evidence at all) still reconciles as UNKNOWN --
        # never a fabricated number -- and is still surfaced for RC review.
        divergent = True
        delta = None
        underlying_convergence_established = False
        note = (
            "A2's authoritative quarter grade is UNKNOWN (required evidence unavailable). "
            f"Schoology's native figure ({schoology_native!r}) is INFORMATIVE ONLY and MUST NOT "
            "be displayed, stored, or treated as the official grade; the missing evidence MUST "
            "NOT be rendered as zero or as erased work. Surface to RC for resolution -- never "
            "auto-resolve (PROGRAM_DOSSIER.md §15 items 1-3)."
        )
    elif _is_unknown_value(schoology_native):
        divergent = True
        delta = None
        underlying_convergence_established = False
        note = (
            "Schoology-native figure is UNKNOWN/unavailable (no gradeable evidence posted); "
            "cannot reconcile -- surfaced to RC, not silently skipped."
        )
    else:
        delta = a2_expected - schoology_native
        # UNDERLYING-ONLY, NO FORGIVENESS (C2 fix): `divergent` is the plain-tolerance
        # comparison of the two underlying figures, full stop, on EITHER comparison
        # basis. Nothing about `schoology_value_is_display_rounded` narrows this check.
        divergent = abs(delta) > tolerance
        # Convergence is asserted ONLY on the full-precision basis, and ONLY when no
        # difference beyond tolerance was found. A display-rounded-observation basis is
        # NEVER sufficient to assert underlying convergence, even if divergent is False --
        # a rounded observation matching by chance never proves the underlying figures
        # actually agree.
        underlying_convergence_established = (not divergent) and not schoology_value_is_display_rounded

        if divergent:
            note = (
                "DIVERGENT: Schoology's native total-points figure does not match A2's "
                "authoritative quarter grade. Schoology's figure is INFORMATIVE ONLY; A2's "
                "figure is authoritative and is the one published via the manual override "
                "column (contract §4.6). Surface to RC -- never auto-resolve."
            )
            if schoology_value_is_display_rounded:
                note += (
                    " (schoology_value_is_display_rounded=True was declared, but this harness "
                    "NEVER forgives a difference on that basis -- the underlying comparison is "
                    "always the substantive one, and a real difference was found here.)"
                )
        elif schoology_value_is_display_rounded:
            # NOT a forgiveness branch: divergent is already False (no difference beyond
            # tolerance), but the comparison basis was declared degraded, so the report
            # must not claim CONVERGENT -- see underlying_convergence_established above.
            note = (
                f"NOT CONVERGED (degraded basis): the two figures do not differ beyond "
                f"tolerance (delta={delta:.6f}), but schoology_value_is_display_rounded=True "
                "was declared for this comparison -- comparison_basis is "
                "display-rounded-observation, not underlying-full-precision, so underlying "
                "convergence has NOT been established from this comparison alone. This is "
                "descriptive only, never a substantive reconciliation result -- see "
                "comparison_basis / underlying_convergence_established."
            )
        else:
            note = "CONVERGENT: Schoology's native total-points figure matches A2's authoritative grade."

    return {
        "student_id": fixture.get("student_id"),
        "label": fixture.get("label"),
        "completion_pct": completion_pct,
        "work_aggregate": work_aggregate,
        "assessment_aggregate": assessment_aggregate,
        "a2_expected_quarter_grade": a2_expected,
        "schoology_native_quarter_grade": schoology_native,
        "schoology_computation_mode": SCHOOLOGY_COMPUTATION_MODE,
        "schoology_value_is_display_rounded": schoology_value_is_display_rounded,
        "comparison_basis": comparison_basis,
        "underlying_convergence_established": underlying_convergence_established,
        "divergent": divergent,
        "delta": delta,
        "note": note,
    }


def load_student_fixtures(fixtures_dir: Path = FIXTURES_DIR) -> list:
    files = sorted(fixtures_dir.glob("student_*.json"))
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def load_course_catalog(fixtures_dir: Path = FIXTURES_DIR) -> dict:
    path = fixtures_dir / "course_section_synthetic.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_all_parity_checks(fixtures_dir: Path = FIXTURES_DIR) -> list:
    # Load the catalog ONCE so every student in this run reconciles against the SAME
    # published snapshot (B4 fix) -- not a fresh independent projection per student.
    course_catalog = load_course_catalog(fixtures_dir)
    return [
        check_student_parity(f, course_catalog=course_catalog) for f in load_student_fixtures(fixtures_dir)
    ]


# --------------------------------------------------------------------------------------
# Course/lesson catalog -> deterministic, idempotent Schoology assignment projection.
# --------------------------------------------------------------------------------------

# Only these Desk lesson states are ever projected as live Schoology assignments
# (canonical seven states -- DESK_STATE_MODEL.md). `unreleased` and `skipped` are
# NEVER projected (PREF-01). `optional-catalog` is projected ONLY when a teacher has
# explicitly assigned it (mirrors qb.select()'s include_optional opt-in and CLAUDE.md's
# 4-1 policy). `temporarily-unavailable` IS still projected/kept -- unavailability alone
# must never retract or hide already-projected work (dossier §15 item 2).
_ALWAYS_PROJECT_STATES = {"today", "released", "completed", "temporarily-unavailable"}
_NEVER_PROJECT_STATES = {"unreleased", "skipped"}
_OPTIONAL_CATALOG_STATE = "optional-catalog"
_CANONICAL_LESSON_STATES = _ALWAYS_PROJECT_STATES | _NEVER_PROJECT_STATES | {_OPTIONAL_CATALOG_STATE}

# The REAL content-registry marker (qb.py, record nt14-ingest-4-1-2026-07-23) for
# optional-catalog content is a top-level "availability": "optional-catalog" field on the
# raw registry row -- NOT the `lesson_state` field this projector's own catalog schema
# invented for Desk navigation state. A raw registry row (e.g. an actual Lesson 4-1 item)
# carries `availability` but has NO `lesson_state` field at all; `_should_project` must
# honor that real marker directly, not merely a normalized `lesson_state` synonym.
_OPTIONAL_CATALOG_AVAILABILITY = "optional-catalog"


def _classify_entry(entry: dict) -> Tuple[bool, Optional[dict]]:
    """
    Core fail-closed release-gating classifier (B1 fix + R2 fix, Codex SOL review R-B).
    Returns `(should_project, anomaly)`. `anomaly` is `None` for every NORMAL outcome
    (including every normal non-projection: unreleased, skipped, or optional-catalog not
    yet explicitly assigned -- none of those are data problems, they are the intended
    resting states). `anomaly` is a structured `{"field", "raw_value", "reason"}` dict
    ONLY when a record is MALFORMED in a way that must be surfaced to a human, never
    silently dropped (contract §8's "surface, never silent" principle) -- see
    `detect_projection_anomalies`, which scans a whole catalog for these.

    Two independent signals can flag a record as optional-catalog content that must
    never be auto-projected: this catalog schema's own `lesson_state` field, OR the REAL
    NT14 content-registry marker `availability == "optional-catalog"` (qb.py; record
    nt14-ingest-4-1-2026-07-23). EITHER signal being optional-catalog is sufficient to
    require an explicit teacher assignment -- the restrictive reading always wins, so a
    permissive/absent/disagreeing `lesson_state` can never bypass the real `availability`
    marker (a raw registry row has no `lesson_state` field at all and must still be
    correctly gated by `availability` alone).

    R2 FIX -- `availability` MUST be checked BEFORE anything else, and a PRESENT value
    that is not the exact string `"optional-catalog"` (a case variant, or any other
    garbage) is a MALFORMED marker: it fails closed immediately and is surfaced as an
    anomaly. It is never silently ignored, and never falls through to a permissive
    `lesson_state` (the residual hole the R2 review found: a present-but-unrecognized
    `availability` value used to fall through to the `lesson_state` branch below and
    project when `lesson_state` was `released`). Only a genuinely ABSENT `availability`
    (`None`, i.e. the key is missing -- the normal case for the vast majority of records,
    which carry no registry-availability concept at all) continues past this check.

    R2 FIX -- `explicitly_assigned` MUST be strictly boolean. Only the literal Python
    singleton `True` counts as "assigned"; only literal `False` (or the key being absent,
    which defaults to `False`) counts as "not yet assigned" (normal, no anomaly). ANY
    other value -- a stringified `"true"`/`"false"`, an int `1`/`0`, an explicit `None`,
    or anything else -- is a type/serialization anomaly: it fails closed (treated as NOT
    assigned) and is surfaced, never coerced via Python truthiness. The residual hole the
    R2 review found was exactly this: `bool(entry.get("explicitly_assigned", False))`
    treats ANY non-empty string (including the string `"false"`) as truthy, silently
    publishing optional-catalog content whose assignment flag was merely mis-serialized.

    For every other record, an unrecognized, missing, `None`, or empty `lesson_state` is
    NEVER treated as permission to project -- "unknown state is not permission." Only an
    explicitly recognized always-project state (`today`/`released`/`completed`/
    `temporarily-unavailable`) authorizes projection; anything else fails closed (not
    itself flagged as an anomaly here -- that gap was B1's scope, not R2's).
    """
    lesson_state = entry.get("lesson_state")
    availability = entry.get("availability")

    if availability is not None and availability != _OPTIONAL_CATALOG_AVAILABILITY:
        # Present but not the exact recognized marker -- malformed. Fails closed
        # UNCONDITIONALLY, before lesson_state is even consulted. Never ignored.
        return False, {
            "field": "availability",
            "raw_value": availability,
            "reason": (
                "unrecognized availability value -- expected exactly 'optional-catalog' or "
                "absent; fails closed and is never ignored or allowed to fall through to a "
                "permissive lesson_state"
            ),
        }

    optional_via_state = lesson_state == _OPTIONAL_CATALOG_STATE
    optional_via_availability = availability == _OPTIONAL_CATALOG_AVAILABILITY
    if optional_via_state or optional_via_availability:
        # Restrictive wins: once EITHER signal flags optional-catalog, explicit teacher
        # assignment is the sole gate, regardless of what `lesson_state` otherwise claims
        # (including a permissive value like "released", or a missing/garbage value).
        raw_assigned = entry.get("explicitly_assigned", False)
        if raw_assigned is True:
            return True, None
        if raw_assigned is False:
            return False, None  # normal: legitimately not yet assigned, not an anomaly
        return False, {
            "field": "explicitly_assigned",
            "raw_value": raw_assigned,
            "reason": (
                "explicitly_assigned must be strictly boolean True/False (identity-checked, "
                "not truthiness-checked); a non-bool value (e.g. a stringified 'true'/'false', "
                "an int 1/0, or None) fails closed and is never coerced"
            ),
        }

    if lesson_state not in _CANONICAL_LESSON_STATES:
        # Missing, None, empty, or unrecognized -- fail closed, never fail open.
        return False, None
    if lesson_state in _NEVER_PROJECT_STATES:
        return False, None
    return lesson_state in _ALWAYS_PROJECT_STATES, None


def _should_project(entry: dict) -> bool:
    """Thin boolean wrapper over `_classify_entry` -- see that function for the full
    fail-closed gating convention (B1 fix + R2 fix). Use `detect_projection_anomalies`
    to also surface WHY a malformed record was rejected."""
    return _classify_entry(entry)[0]


def detect_projection_anomalies(course_catalog: dict) -> list:
    """
    Scans a course catalog and surfaces every MALFORMED record's rejection reason --
    never silently dropped (contract §8's "surface, never silent" principle; R2 fix,
    Codex SOL review). Routine, NORMAL non-projection (unreleased, skipped, or
    optional-catalog not yet explicitly assigned) is deliberately NOT included here --
    only a record whose `availability` or `explicitly_assigned` field is PRESENT but
    malformed is an anomaly worth a human's attention. A malformed record must be
    visible to RC, not quietly unpublished -- this is the structured place to look.
    """
    course_id = course_catalog["course_id"]
    anomalies = []
    for entry in course_catalog["lessons"]:
        _, anomaly = _classify_entry(entry)
        if anomaly is None:
            continue
        anomalies.append(
            {
                "external_key": external_key(
                    course_id,
                    entry.get("lesson_id", "UNKNOWN"),
                    entry.get("artifact_type", "UNKNOWN"),
                    entry.get("artifact_id", "UNKNOWN"),
                ),
                "field": anomaly["field"],
                "raw_value": anomaly["raw_value"],
                "reason": anomaly["reason"],
                "projected": False,  # malformed records always fail closed
            }
        )
    return anomalies


def external_key(course_id: str, lesson_id: str, artifact_type: str, artifact_id: str) -> str:
    """
    Stable external key identifying a projected assignment across runs (contract §7).
    A pure, deterministic function of (course_id, lesson_id, artifact_type, artifact_id)
    only -- no timestamps, no random ids -- so re-projection always converges to the same
    key for the same lesson identity, and "does this assignment already exist?" is always
    answerable by exact-match lookup rather than fuzzy title matching.
    """
    return f"a2:{course_id}:{lesson_id}:{artifact_type}:{artifact_id}"


def deep_link_for(course_catalog: dict, entry: dict) -> dict:
    """
    Deep-link contract (SCHOOLOGY_PROJECTION_CONTRACT.md §5): `a2_activity_key` is OUR
    durable, stable identity string for this exact activity -- it never changes as long
    as the lesson identity (topic/lesson_id/artifact_type/artifact_id) doesn't change.
    `schoology_url_template` is an UNRESOLVED placeholder template -- Schoology domain,
    course id, and assignment id are Schoology-minted identifiers that do not exist yet
    (NT15 brief §0) and are deliberately NEVER fabricated here.
    """
    course_slug = course_catalog["course_slug"]
    a2_activity_key = (
        f"a2://{course_slug}/{entry['topic']}/{entry['lesson_id']}/{entry['artifact_type']}/{entry['artifact_id']}"
    )
    schoology_url_template = (
        "https://{schoology_domain}/course/{schoology_course_id}/assignment/{schoology_assignment_id}"
    )
    return {"a2_activity_key": a2_activity_key, "schoology_url_template": schoology_url_template}


def project_course(course_catalog: dict) -> list:
    """
    Pure, deterministic projection of a course/lesson catalog into assignment records.
    Calling this twice on the same input yields identical records in identical order --
    no create-without-checking-the-external-key-first, no duplicate assignments (contract
    §7). This function performs NO network/API call of any kind (NO-LIVE-WRITE, contract
    §9) -- it only ever returns Python data describing what WOULD be created/updated.

    NO-FABRICATED-ZERO (OPEN-16, RESOLVED by RC 2026-07-24): every record this function
    returns traces back to a REAL catalog entry in `course_catalog["lessons"]` -- it never
    synthesizes an assignment out of nothing, and in particular it never invents a
    synthetic zero-scored/zero-points assignment purely to make some downstream ratio
    computable. A student with no eligible designated work/participation is a
    per-student reconciliation fact (see `check_student_parity`'s UNKNOWN handling), not
    something this projector "fixes" by fabricating evidence.

    This function itself returns ONLY successfully-classified records (projected or
    routinely withheld) -- it does not surface malformed-record detail. Call
    `detect_projection_anomalies(course_catalog)` alongside this function to get the
    structured list of records that were rejected for a MALFORMED reason (an unrecognized
    `availability` value, or a non-boolean `explicitly_assigned` value) rather than a
    routine one (unreleased/skipped/not-yet-assigned optional-catalog); a real RC-facing
    caller of this projector MUST call both and display anomalies, never silently drop
    them (contract §8).
    """
    course_id = course_catalog["course_id"]
    records = []
    for entry in course_catalog["lessons"]:
        if not _should_project(entry):
            continue
        records.append(
            {
                "external_key": external_key(course_id, entry["lesson_id"], entry["artifact_type"], entry["artifact_id"]),
                "schoology_category": entry["schoology_category"],
                "points_possible": entry["points_possible"],
                "extra_credit": entry.get("extra_credit", False),
                "naming_status": "OPEN-04",  # human-facing assignment/category names are unresolved
                "deep_link": deep_link_for(course_catalog, entry),
            }
        )
    return records


def merge_projection(existing: dict, new_records: list) -> dict:
    """
    Update-vs-create semantics (contract §7): if `external_key` already exists in
    `existing`, UPDATE it in place; otherwise CREATE it. Never appends a duplicate.
    Returns a NEW dict (does not mutate `existing`) keyed by external_key.
    """
    merged = dict(existing)
    for record in new_records:
        merged[record["external_key"]] = record
    return merged


# --------------------------------------------------------------------------------------
# CLI entry point -- prints an actionable, human-readable divergence report for RC.
# --------------------------------------------------------------------------------------

def main() -> None:
    reports = run_all_parity_checks()
    for r in reports:
        flag = "DIVERGENT" if r["divergent"] else "convergent"
        print(
            f"[{flag}] {r['student_id']} ({r['label']}): "
            f"a2_expected={r['a2_expected_quarter_grade']!r} "
            f"schoology_native={r['schoology_native_quarter_grade']!r} -- {r['note']}"
        )
    divergent_count = sum(1 for r in reports if r["divergent"])
    print(f"\n{divergent_count}/{len(reports)} student(s) flagged for RC reconciliation review.")

    catalog = load_course_catalog()
    projected = project_course(catalog)
    print(f"\nProjected {len(projected)} Schoology assignment(s) from {len(catalog['lessons'])} catalog entries "
          f"({len(catalog['lessons']) - len(projected)} withheld: unreleased/skipped/not-yet-assigned optional-catalog).")

    anomalies = detect_projection_anomalies(catalog)
    if anomalies:
        print(f"\n{len(anomalies)} MALFORMED record(s) detected -- surfaced for RC review, never silently unpublished:")
        for a in anomalies:
            print(f"  [ANOMALY] {a['external_key']}: {a['field']}={a['raw_value']!r} -- {a['reason']}")
    else:
        print("\nNo malformed records detected in this catalog.")


if __name__ == "__main__":
    main()
