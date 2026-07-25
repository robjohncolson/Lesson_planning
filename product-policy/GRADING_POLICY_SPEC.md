# Grading Policy Specification — Grade Composition, Quarter Rule, Participation & Extra Credit (D2)

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

This document is the normative prose companion to `grading_policy.v2.json` (machine-readable
constants) and `grading_policy_ref.py` (reference implementation). It covers RC's decision
areas **3 (Grade Composition)** and **4 (Participation / Extra Credit)** — canonical IDs
**PREF-03** and **PREF-04** — and the seven items RC's 2026-07-24 NT16 rulings resolved:
**OPEN-08, OPEN-09, OPEN-10, OPEN-11, OPEN-15, OPEN-16, OPEN-19**. It does not reopen or
restate any other RC decision area; those are cited only where directly relevant.

**v2.0 supersedes v1.0.** v1.0 shipped six OPEN items as narrow, explicitly-labeled
PROVISIONAL / UNRESOLVED-PENDING-RC placeholders (OPEN-08, 09, 10, 11, 15, 16), and had no
rule at all for multi-item reduction (OPEN-19). RC's final rulings on 2026-07-24 resolve all
seven. Every sentence in this document describes v2.0's DECIDED behavior; a v1.0 placeholder
is mentioned only inside an explicitly-labeled "superseded" note or the Changelog at the end.

---

## 1. Definitions — the two principal aggregates

RC's decision text (Area 3) establishes exactly two principal aggregates. Every piece of
graded evidence belongs to exactly one of them; nothing straddles both.

### 1.1 WORK aggregate (PREF-03.2, OPEN-15 RESOLVED)

**WORK** is now a POINT-BASED ratio, per RC's OPEN-15 ruling (`RESOLVED by RC 2026-07-24`):

```
WORK = 100 * (packet_points_earned + participation_points_earned + extra_credit_points_earned)
       / (packet_points_possible + participation_points_possible)
```

- Only teacher-designated OFFICIAL evidence enters the formula.
- **Extra credit raises the numerator but NOT the denominator.** There is no
  `extra_credit_points_possible` term — extra credit's entire purpose is to add credit beyond
  what was assigned, so it must never be netted against a possible-points figure.
- **WORK MAY EXCEED 100.** There is no upper clamp anywhere in `compute_work_aggregate`. A
  student who earns the full designated packet + participation points AND stacks both
  authorized extra-credit sources will show WORK > 100. This is intended, not a defect.
- **Zero denominator falls to OPEN-16's rule** (§2, §6): if
  `packet_points_possible + participation_points_possible == 0`, WORK is UNKNOWN, never a
  fabricated 0 or 100.
- **Never add a percentage directly to raw flat points.** A packet score that arrives as a
  percentage must first be converted to an (earned, possible) point pair on a consistent
  scale before it enters this formula — this formula only ever operates on point pairs, never
  on a mix of percentage-scale and point-scale numbers.

This SUPERSEDES v1.0's plain-addition placeholder (`digital_packet_work_score +
participation_points + extra_credit_points`), which combined a percentage-scale packet score
with flat point bonuses (1.0/day, 0.5/exercise) with no common scale — an unresolved-pending-RC
risk, not a decided formula. See §9 for the full ruling text and what it supersedes.

Explicitly IN the WORK aggregate:
- Teacher-designated digital packet work (the digital-capture portion of packet work that the
  teacher has designated as tracked; see PREF-02, classroom modality — cited, not reopened),
  expressed as `packet_points_earned` / `packet_points_possible`.
- Daily participation evidence (PREF-04.1/.2, OPEN-11 RESOLVED — see §4 below), aggregated via
  `aggregate_participation` into `participation_points_earned` / `participation_points_possible`.
- Designated extra credit: the TI-84 exercise credit and the Equation Lab exercise credit
  (PREF-04.3/.4, OPEN-10 RESOLVED — see §4 below), and no other extra-credit source unless a
  new RC policy decision authorizes it (`extra_credit_points_earned` only — no possible-points
  counterpart).

Explicitly NOT in the WORK aggregate:
- Pure paper practice. Per PREF-02, pure paper practice is **not graded or individually
  tracked** at all. It has no digital record, so it cannot be "teacher-designated digital
  packet work" and cannot contribute to WORK, to completion (§2), or to anything else in this
  policy.
- Lesson quizzes and topic assessments (these belong to ASSESSMENT, §1.2).

### 1.2 ASSESSMENT aggregate (PREF-03.3, OPEN-19 RESOLVED)

**ASSESSMENT** = lesson quizzes **+** topic assessments, reduced with the same point-weighted
rule as any other multi-item group (§8):

```
ASSESSMENT = 100 * total_assessment_points_earned / total_assessment_points_possible
```

computed over every lesson quiz and topic assessment on its actual point scale — never an
equal average of per-item percentages (§8). `compute_assessment_aggregate` is a thin, named
wrapper over the general point-weighted reducer (`compute_component_percentage`) for exactly
this group.

Explicitly IN the ASSESSMENT aggregate:
- Lesson quizzes.
- Topic assessments.

Explicitly NOT in the ASSESSMENT aggregate:
- Participation evidence and extra credit (these belong to WORK only — PREF-04.5; never
  ASSESSMENT under any circumstance). This is unchanged by OPEN-15/OPEN-19 — extra credit still
  never touches ASSESSMENT's scale, which is why `assessment_aggregate` keeps its `[0, 100]`
  domain in `compute_quarter_grade` even though `work_aggregate` no longer does (§3, §7).
- Teacher-designated digital packet work.

---

## 2. Completion percentage (PREF-03.4, OPEN-08 and OPEN-16 RESOLVED)

Completion percentage is defined **only** over teacher-designated digital work:

```
completion = (teacher-designated digital work items COMPLETED)
             ------------------------------------------------------
             (teacher-designated digital work items ASSIGNED)
```

- **Numerator:** the count (or points, if the teacher's designation is point-weighted) of
  teacher-designated digital work the student has completed.
- **Denominator:** the count (or points) of teacher-designated digital work assigned to the
  student.
- **Scope:** teacher-designated digital work ONLY. Pure paper practice is not graded or
  individually tracked (PREF-02) and therefore has no digital record to count in either the
  numerator or the denominator — it cannot enter completion at all, by construction, not by a
  filtering step applied afterward.

This is the completion percentage referenced by the quarter rule's 40% gate (§3).

**No pre-rounding (`OPEN-08`, `RESOLVED by RC 2026-07-24`).** RC's ruling: "Compare the EXACT
completion ratio against the inclusive 0.40 threshold. No pre-rounding before branch
selection." `compute_completion` therefore returns the exact float ratio and no longer accepts
a rounding parameter at all — the v1.0 `round_ndigits` opt-in hook is REMOVED. The comparison
against the 0.40 gate, performed in `compute_quarter_grade` (§3), always operates on this exact
ratio.

**Zero-denominator case (`OPEN-16`, `RESOLVED by RC 2026-07-24`).** RC's ruling: "No eligible
designated work/participation => completion UNKNOWN, WORK UNKNOWN, quarter grade UNKNOWN.
Student-facing display = dash / 'not enough evidence', never zero." When no digital work has
been designated yet — the denominator is 0 — `compute_completion` returns `UNKNOWN` (never `0`,
never a fabricated ratio). This is now DECIDED policy, not a provisional placeholder: the
real-world consequence (every student's completion, and therefore the quarter-rule branch, is
UNKNOWN for the entire early-quarter window before any digital work is designated) is confirmed
as the intended behavior, and the student-facing rendering of that UNKNOWN state is itself
specified — see §6 and `round_final_grade_for_display` / `final_grade_display_string`.

---

## 3. The quarter rule (PREF-03.4–.6, OPEN-08, OPEN-09, OPEN-15 RESOLVED)

```
if completion >= 0.40:            # INCLUSIVE — RC's text says "≥ 40%"
    quarter_grade = max(work_aggregate, assessment_aggregate)      # PREF-03.5
else:                              # completion < 0.40
    quarter_grade = average(work_aggregate, assessment_aggregate)  # PREF-03.6
                   = (work_aggregate + assessment_aggregate) / 2
```

- The gate is **inclusive at exactly 40%**: a completion value of exactly `0.40` takes the
  **max** branch, not the average branch. This is the single most load-bearing boundary
  condition in this policy and is tested explicitly (see `test_grading_policy_ref.py`).
- **The comparison uses the EXACT completion ratio (`OPEN-08`, `RESOLVED`).** No rounding of
  any kind is introduced before this comparison, under any circumstance — `compute_completion`
  no longer even exposes a rounding parameter (§2), and `compute_quarter_grade` performs the
  `>=` (or `>`) comparison directly against the value it is given.
- The "average" branch is the arithmetic mean of the two aggregates — no weighting.
- Both branches require both aggregates and the completion value to be known. If any of the
  three is unavailable, the branch itself is undeterminable (§6).
- **`work_aggregate` has no upper bound (`OPEN-15`, `RESOLVED`).** Because WORK may exceed 100
  (§1.1), `compute_quarter_grade` validates `work_aggregate` (and, symmetrically,
  `teacher_override`) only as a finite, non-negative number — the `[0, 100]` ceiling that
  applied in v1.0 is removed for these two. `assessment_aggregate` keeps its `[0, 100]` domain
  unchanged, because extra credit never touches ASSESSMENT (PREF-04.5). See §7 for the full
  domain table.
- **No rounding of the result (`OPEN-09`, `RESOLVED`).** `compute_quarter_grade` returns the
  full-precision `max`/average result with no rounding option — the v1.0 `round_ndigits`
  opt-in hook is REMOVED. See "Rounding and display" below.

#### C1 remediation — the gate must be decided by an exact integer cross-product (Codex review 2026-07-24, HIGH)

A Codex review pass found that OPEN-08's ruling ("compare the EXACT completion ratio") was not
fully honored by the implementation: `compute_completion` returns a binary **float**
(`completed_count / assigned_count`), and `compute_quarter_grade` compared that float directly
to `completion_threshold`. For sufficiently large counts, the float can round to **exactly**
`0.40` even when the true rational value is **strictly below** it — e.g.
`completed_count = 40_000_000_000_000_000`, `assigned_count = 100_000_000_000_000_001` gives an
exact ratio strictly below `2/5` (`5 * completed_count < 2 * assigned_count`), yet
`completed_count / assigned_count` as a float is exactly `0.4`. Comparing that float to
`completion_threshold` would wrongly select the **MAX** branch instead of **AVERAGE**. This is a
real, demonstrated defect at the boundary, not a theoretical one.

**Fix.** The gate is now decided by an **exact integer cross-product** whenever raw counts are
available, never by the binary float ratio:

```
completed_count / assigned_count  ??  completion_threshold
   <=>
completed_count * THRESHOLD_DENOMINATOR  ??  assigned_count * THRESHOLD_NUMERATOR
```

`THRESHOLD_NUMERATOR` / `THRESHOLD_DENOMINATOR` is `completion_threshold`'s exact `Fraction`
form (`2/5` for `0.40`), derived from the JSON file's own **decimal literal** — a second parse of
the same file using `json.load(..., parse_float=fractions.Fraction)`, so `Fraction("0.40")` is
computed exactly (`2/5`) with **no floating-point intermediate at all** — rather than from the
already-lossy binary `float` the main constant holds. (An earlier draft of this fix used
`fractions.Fraction(COMPLETION_THRESHOLD).limit_denominator()`, a HEURISTIC that guesses the
"intended" simple fraction back from an already-rounded float; it happens to recover `2/5` for
`0.40`, but a heuristic is exactly what an exactness fix should not depend on for a future
threshold value. The decimal-string parse is exact by construction, not by guessing, and an
import-time assertion — `float(_COMPLETION_THRESHOLD_FRACTION) == COMPLETION_THRESHOLD` — fails
loudly if the two ever diverge, rather than silently deciding the gate against the wrong
fraction.) Both sides of the cross-product comparison are plain Python integers (arbitrary
precision); there is no floating-point arithmetic anywhere on this path, so it cannot collapse at
any count, however large.

- `compute_completion_threshold_met(completed_count, assigned_count)` is the public, standalone
  form of this exact gate decision. It mirrors `compute_completion`'s UNKNOWN/domain handling
  exactly: UNKNOWN if either input is UNKNOWN/None; UNKNOWN if `assigned_count == 0` (OPEN-16,
  zero eligible denominator); `PolicyDomainError` for any malformed/out-of-domain input, via the
  same shared validation (`_validate_completion_counts`) `compute_completion` uses.
- `compute_quarter_grade` gains a **keyword-only** `completed_count=`/`assigned_count=` pair
  (both default `None`). `completion` itself now defaults to `None` (UNKNOWN) rather than being a
  required positional argument, so a caller using only the exact-count style never needs to pass
  a redundant `completion` value — every existing caller that supplies `completion` explicitly is
  completely unaffected.

**Hardening (same day, peer-review follow-up).** A first version of this fix closed the defect
only for callers who explicitly re-passed `completed_count=`/`assigned_count=` to
`compute_quarter_grade`. But the **ordinary** calling sequence every real caller actually writes —

```python
completion = compute_completion(completed_count, assigned_count)
quarter_grade = compute_quarter_grade(work, assessment, completion)
```

— still collapsed, because the counts available at the first call were discarded the moment
`compute_completion` returned a bare float. The fix now reaches this ordinary sequence too, via
`CompletionRatio`: `compute_completion` returns a `float` **subclass** — it *is* a float, not
merely float-like, so ordinary float operations (arithmetic, comparison, `round()`, `float()`,
JSON serialization) run without raising — that additionally carries the exact `completed_count`/
`assigned_count` it was computed from. `compute_quarter_grade` recognizes a carrying `completion`
argument automatically. **The carried counts survive only while the object itself, untouched,
reaches `compute_quarter_grade` — see the "V1" hardening below for why "runs without raising" is
not the same guarantee as "provenance survives."** The full precedence order is now:

1. **Explicit `completed_count=`/`assigned_count=` kwargs**, when both supplied — always win.
2. **A `completion` that carries its own counts** (a `CompletionRatio` from `compute_completion`)
   — used automatically when no explicit kwargs are supplied. This is what makes the ordinary
   two-call sequence above exact by construction, with no change required at the call site.
3. **A bare float** with no carried counts and no explicit kwargs — the ONLY remaining path that
   falls back to comparing the float directly against `completion_threshold`, still documented as
   subject to representation error at the boundary. **This tier is reached for TWO distinct
   reasons, not one** (V1, HIGH, Codex re-check 2026-07-24 — an earlier version of this sentence
   said "only when the exact counts... do not exist anywhere in the call chain to recover," which
   was false): either the exact counts genuinely never existed anywhere in the call chain, **or**
   they existed on a `CompletionRatio` but its provenance was destroyed before reaching this
   function by arithmetic, coercion, rounding, copying, or serialization performed on it (see the
   "V1" hardening below). A bare float carries no information distinguishing the two cases — both
   land on this same honestly-imprecise fallback, not silently pretended to be exact either way.

If explicit kwargs are supplied **and** `completion` carries its own counts, the two must agree:
a mismatch is a caller-side defect (contradictory inputs for the same decision, not a policy
question) and raises `PolicyDomainError`; matching values are accepted as redundant-but-
consistent.

- **The float `completion` path (tier 3) is kept, and still works, for callers who only have a
  bare ratio with no provenance** — it is not removed. It remains explicitly documented (in this
  spec, in `compute_quarter_grade`'s and `CompletionRatio`'s docstrings, and in
  `grading_policy.v2.json` → `quarter_rule.gate_decision_from_counts` /
  `rounding_rules.completion_threshold_gate_exactness`) as **subject to representation error at
  the boundary**. Tiers 1 and 2 are the correct, exact inputs whenever raw counts are available
  anywhere in the call chain (explicitly, or carried on the ratio); tier 3 remains a documented,
  imperfect convenience for when they are not.
- **Order of operations is unaffected.** `completed_count`/`assigned_count`, when supplied
  explicitly, and any conflict check against a carrying `completion`'s counts, are validated (and
  can raise `PolicyDomainError`) in the same "validate every supplied value first" pass as
  `completion`, `work_aggregate`, `assessment_aggregate`, and `teacher_override` (§7.4) — before
  override precedence is applied. A malformed count pair, or a count pair that contradicts a
  carrying `completion`, is never masked by a simultaneously-supplied, well-formed
  `teacher_override`.

#### V1 hardening (Codex re-check 2026-07-24, HIGH) — provenance is honestly narrow, not silently destroyed

A Codex re-check pass found that the C1-hardening prose above, while correct about the mechanism,
over-promised in exactly the way flagged at the top of §3.2's C1 subsection: it said
`CompletionRatio` "behaves as an ordinary float everywhere" and left it there, which reads as a
guarantee that the exactness carries through ordinary use. Live reproduction with the witness
pair `completed = 40_000_000_000_000_000`, `assigned = 100_000_000_000_000_001` (exact ratio
strictly below `2/5`, so AVERAGE is the correct branch) showed the guarantee does **not** survive:

```
pristine ratio      -> 70.0  (correct, AVERAGE)
ratio + 0.0         -> 80.0  *** flips to MAX
float(ratio)        -> 80.0  *** flips to MAX
round(ratio, 12)    -> 80.0  *** flips to MAX
abs(ratio)          -> 80.0  *** flips to MAX
json round-trip     -> 80.0  *** flips to MAX
```

Every one of those operations is exactly what the earlier prose called safe. Each one silently
returns a plain `float` — not a degraded `CompletionRatio`, a genuinely different, uninstrumented
object — so the carried counts are gone and `compute_quarter_grade` has no choice but to fall back
to tier 3 (§3, above), which is imprecise at the boundary by design. Three compounding problems,
and their fixes:

1. **The documentation was misleading.** Fixed by this section, and by the corresponding
   docstrings in `grading_policy_ref.py` (`CompletionRatio`, `compute_completion`,
   `compute_quarter_grade`) and `grading_policy.v2.json`
   (`quarter_rule.gate_decision_from_counts`): every one of these artifacts now states plainly
   that arithmetic, coercion, rounding, copying, or serialization of a `CompletionRatio` produces
   a bare `float`, the provenance is lost, and branch selection falls back to tier 3 — reached
   whenever counts are **absent OR provenance was lost**, not only when counts never existed.
   Callers who need the exactness guarantee to hold must pass `compute_completion(...)`'s result
   directly to `compute_quarter_grade` with nothing performed on it in between, or supply
   `completed_count=`/`assigned_count=` explicitly. **This is not fixed by making provenance
   survive arithmetic** — that would require overriding every dunder method `float` has, and would
   still fail the moment the value is serialized (e.g. to JSON, or to Schoology); the fallback
   tier is the honest design, and the fix is to describe it accurately, not to fight it.
2. **The counts were public and mutable.** `r.completed_count = 999` used to be accepted and could
   flip a below-threshold ratio into the MAX branch with no error at all — a crafted or
   accidentally mutated ratio could lie about its own provenance. Fixed: `completed_count` and
   `assigned_count` are now **read-only properties over private slots** — assigning either one now
   raises `AttributeError` unconditionally, instead of silently succeeding.
3. **Nothing verified the carried counts actually matched the float.** Read-only attributes stop
   *mutation* of a genuine ratio, but they cannot stop a caller from *hand-constructing* a
   `CompletionRatio` directly with a float value that never matched its own counts in the first
   place (a "crafted" ratio, bypassing `compute_completion` entirely). Fixed:
   `compute_quarter_grade` now verifies, whenever `completion` carries counts, that
   `float(fractions.Fraction(completed_count, assigned_count))` equals the ratio's own float
   value, **before** trusting those counts for the gate decision and before override precedence is
   applied (same "validate every supplied value first" discipline as §7.4). A mismatch is a
   caller/data defect, never UNKNOWN — it raises `PolicyDomainError`. This check provably cannot
   fire for any ratio `compute_completion` itself can produce (for any valid non-negative integer
   pair `a`, `b` with `b > 0`, `float(fractions.Fraction(a, b))` and `a / b` are the same
   correctly-rounded double for the same exact rational value), so it is verified across the
   witness pair, the exact `2/5` boundary, `39/100`, `0/1`, and `n/n` without a false positive.

`CompletionRatio` also now defines `__reduce__` so that copying (`copy.copy`/`copy.deepcopy`) and
pickling degrade it HONESTLY to a bare `float` — matching the "copying... produces a bare float"
disclosure above — instead of raising `TypeError` (the default float-subclass reduction cannot
supply the two extra constructor arguments `CompletionRatio.__new__` requires). This keeps the
class picklable/copyable enough not to break a consumer that does this, without pretending
provenance survived the round trip.

See `grading_policy_ref.py`'s module docstring ("Codex review remediation") and
`grading_policy.v2.json` → `changelog` for the machine-readable record of this pass, and the
Changelog section at the end of this document.

### 3.1 Teacher override (PREF-03.7)

Teacher override is preserved and **takes precedence** over the computed quarter-rule result,
including a result that would otherwise be UNKNOWN (§6). A supplied teacher override is always
the returned value; the computed formula never runs when an override is present.
`teacher_override`'s domain is unbounded-non-negative, matching `work_aggregate` (see above) —
an override matching an above-100 WORK value must not be rejected.

### 3.2 Rounding and display (PREF-03, OPEN-09 RESOLVED)

RC's ruling: "Full precision internally. Round ONLY the student-facing final-grade DISPLAY to
one decimal. Schoology keeps native earned/possible totals. Reconciliation compares underlying
values consistently and must not mistake display rounding for substantive divergence."

- **Internal precision.** Every computation in this policy — `compute_completion`,
  `compute_component_percentage`, `compute_assessment_aggregate`, `compute_work_aggregate`,
  `compute_quarter_grade` — operates at full float precision and returns full-precision
  results. None of them round.
- **Display-only rounding.** `round_final_grade_for_display(value)` rounds to
  `FINAL_GRADE_DISPLAY_DECIMALS` (1, loaded from JSON) for showing a quarter grade to a student
  or teacher. `final_grade_display_string(value)` additionally renders `UNKNOWN` as
  `UNKNOWN_DISPLAY_TOKEN` (an em dash, "—") rather than `"0.0"` (§6). Neither function's output
  may be fed back into any further computation.
- **Schoology reconciliation is UNDERLYING-ONLY; rounding never forgives a genuine difference**
  (C2 remediation; V2 doc correction, Codex re-check 2026-07-24 — this bullet previously carried
  the rule C2 deleted from the code as if it were still live text; see the Changelog at the end
  of this document). Schoology keeps its own native, full-precision earned/possible totals — this
  policy never publishes a rounded display value into Schoology in the first place — so the
  substantive comparison always runs on full-precision values on both sides, at a plain numeric
  tolerance, with no exception: no amount of rounding on either side can turn a genuine underlying
  difference into a non-divergence. When only a DISPLAY-ROUNDED OBSERVATION of the Schoology-side
  figure is available (a caller may explicitly declare this — the one legitimate case is
  reconciling against an already-rounded figure from a real Schoology tenant), the comparison
  basis is DEGRADED and reported as a limitation rather than silently treated as equivalent to the
  underlying value: `comparison_basis` is set to `"display-rounded-observation -- underlying
  convergence NOT established"`, and `underlying_convergence_established` is forced to `False` —
  even when the observed numbers happen to match. `underlying_convergence_established` is `True`
  ONLY when the comparison ran on the default, full-precision basis and found no difference beyond
  tolerance; a degraded basis never earns that claim, no matter what it observes.

### 3.3 Versioning (PREF-03.8)

This policy is versioned. This document and its companion JSON are **v2.0**, superseding
**v1.0** (`grading_policy.v1.json`, now deleted) as of the 2026-07-24 NT16 rulings. Any future
change to the constants, the gate, the branch formulas, or the aggregate definitions is a new
version, not a silent edit to v2.0.

---

## 4. Participation and extra credit (PREF-04, OPEN-10 and OPEN-11 RESOLVED)

Both participation and extra credit are WORK-side units (§1.1) and **never** enter the
ASSESSMENT aggregate under any circumstance (PREF-04.5).

### 4.1 Participation-day rule (OPEN-11, `RESOLVED by RC 2026-07-24`)

RC's ruling: "Non-class days are EXCLUDED from the participation requirement. Partial/
absent/uncertain attendance NEVER auto-zeroes — such days are excused/unknown unless RC
explicitly designates the day participation-eligible. UNKNOWN is distinct from zero."

`compute_participation_day(has_valid_response, *, is_class_day, attendance,
participation_eligible_designation)` returns a `ParticipationDay(earned, possible, status)`
per the following table. This REPLACES v1.0's `compute_participation_point`, which returned
`UNKNOWN` for any non-class or partial-attendance day as an unresolved-pending-RC placeholder.

| Case | `is_class_day` | `attendance` | designation | `earned` | `possible` | `status` |
|---|---|---|---|---|---|---|
| Non-class day | `False` | — | — | `0.0` | `0.0` | `excluded_non_class_day` |
| Present, response known | `True` | `present` | — | `1.0` or `0.0` (PREF-04.1/.2) | `1.0` | `counted` |
| Present, response unknown | `True` | `present` | — | `UNKNOWN` | `1.0` | `unknown` |
| Partial/absent, not eligible | `True` | `partial`/`absent` | `False` | `0.0` | `0.0` | `excused_not_participation_eligible` |
| Partial/absent, eligible | `True` | `partial`/`absent` | `True` | same as "present" rows | same as "present" rows | same as "present" rows |
| Attendance unknown | `True` | `unknown` | (any) | `UNKNOWN` | `UNKNOWN` | `unknown` |

Two rows deserve emphasis, because they look similar but are NOT the same evidentiary state:

- **`excused_not_participation_eligible` is `0.0`/`0.0`, not a zero score.** The day is excluded
  from the participation requirement entirely — it contributes to neither the earned nor the
  possible side of the ratio. This is deliberately distinct from an "auto-zero" (which would be
  `0.0`/`1.0`, penalizing the student for a day that didn't count).
- **Genuinely-unknown attendance is `UNKNOWN`/`UNKNOWN`, never the excused reading.** "The
  attendance itself is not known" is a different evidentiary state from "the attendance is
  known to be partial/absent." The two must never be conflated.

**A documented reading, not an invention beyond RC's ruling.** RC's text permits either
"excused" or "unknown" for a KNOWN partial/absent day without an eligibility designation. This
implementation chooses **excused** (0.0/0.0, excluded from the requirement) as the reading that
simultaneously honors "excluded from the participation requirement" and "never auto-zero" —
0/0 contributes to neither side of the ratio, so it cannot be mistaken for a zero score, and it
does not silently shrink the requirement's denominator the way a counted-but-zero-earning day
would. Genuinely-UNKNOWN attendance is kept as its own, distinct case.

**CONFIRMED by RC 2026-07-24 (later same date; NT16-B).** The "documented reading" above was, until this
confirmation, an implementation choice RC's original ruling permitted but did not itself pin down — labeled
pending RC confirmation, not presented as settled policy. RC has since directly confirmed it, in the same
four-point form recorded in `OPEN_DECISIONS_REGISTER.md`'s OPEN-11 section: a known absent/partial/non-class
day is excused (`0.0`/`0.0`); a genuinely uncertain attendance state remains `UNKNOWN`; neither case produces
an automatic zero; RC may explicitly designate an otherwise-excused day participation-eligible. No behavior
changes — `compute_participation_day` already implemented all four points — only the "pending RC confirmation"
labeling above is superseded.

`aggregate_participation(days)` sums a sequence of `ParticipationDay` into a single
`(earned, possible)` pair for `compute_work_aggregate`'s `participation_points_earned` /
`participation_points_possible` arguments, propagating `UNKNOWN` independently on each side.

### 4.2 Extra credit and its daily cap (PREF-04.3/.4, OPEN-10 `RESOLVED by RC 2026-07-24`)

| Unit | Condition | Value | Sub-ID |
|---|---|---|---|
| Daily participation point | ≥1 valid digital packet response on a class day | `1.0` | PREF-04.1 |
| Daily participation point | no valid digital packet response on a class day | `0.0` | PREF-04.2 |
| TI-84 extra credit | assigned TI-84 exercise completed successfully | `+0.5` | PREF-04.3 |
| Equation Lab extra credit | assigned Equation Lab exercise completed successfully | `+0.5` | PREF-04.4 |

RC's ruling: "+1.0 point per student per class day cap for currently-authorized extra credit
(TI-84 +0.5, Equation Lab +0.5, stacking allowed). Any FUTURE extra-credit source requires a
new policy decision — it never silently exceeds the cap."

- **The cap (`EXTRA_CREDIT_DAILY_CAP_POINTS`, 1.0) is now UNCONDITIONAL policy**, applied
  inside `compute_extra_credit` on every call. The v1.0 opt-in `daily_cap` parameter is
  REMOVED — there is no longer a way to call this function without the cap applying.
  Stacking both currently-authorized sources (TI-84 `+0.5` and Equation Lab `+0.5`) is
  explicitly allowed and lands exactly at the cap (`1.0`), not over it.
- **An unauthorized additional source raises `PolicyDecisionRequiredError`, never silently
  extends or gets clipped into the ledger.** `compute_extra_credit`'s `additional_sources`
  parameter exists solely to make this refusal explicit: if the caller supplies a source name
  there that is **not** in `AUTHORIZED_EXTRA_CREDIT_SOURCES`, the function raises
  `PolicyDecisionRequiredError` naming the unauthorized source(s) rather than adding, ignoring,
  or clamping it. A new RC policy decision is required before any additional extra-credit source
  may contribute to WORK.

#### C3 remediation — authorization is by membership, not by which parameter was used (Codex review 2026-07-24, HIGH)

A Codex review pass found two defects in how `compute_extra_credit` decided authorization:

1. **`additional_sources=["ti84"]` wrongly raised `PolicyDecisionRequiredError`, even though
   `"ti84"` *is* authorized.** The prior implementation treated *any* non-empty
   `additional_sources` argument as an unauthorized request, regardless of its contents —
   authorization was being decided by *which parameter the caller used* (the dedicated boolean
   flags vs. the generic `additional_sources` channel), not by *membership* in
   `AUTHORIZED_EXTRA_CREDIT_SOURCES`.
2. **An unauthorized source in `additional_sources` was never checked when a flag was
   UNKNOWN**, because the UNKNOWN short-circuit ran *before* the authorization check —
   `compute_extra_credit(ti84_completed=UNKNOWN, additional_sources=["unauthorized_thing"])`
   returned `UNKNOWN` instead of raising, silently skipping the authorization gate whenever
   unrelated evidence happened to be unavailable.

**Fix.** Authorization is now decided purely by **membership in
`AUTHORIZED_EXTRA_CREDIT_SOURCES`**, checked identically no matter which channel a source
arrives through, and checked **before** the UNKNOWN short-circuit, unconditionally:

- Every entry supplied via `additional_sources` is validated (type-checked, then
  authorization-checked) **first**, regardless of whether `ti84_completed` or
  `equation_lab_completed` is UNKNOWN. An unauthorized source **always** raises
  `PolicyDecisionRequiredError` — RC's ruling that a future source needs a new policy decision
  is an obligation that cannot be skipped just because unrelated evidence is unavailable.
- An authorized source supplied via `additional_sources` (e.g. `additional_sources=["ti84"]`)
  now contributes its point value normally — exactly as if the corresponding dedicated boolean
  flag (`ti84_completed=True`) had been used — and still stacks under the same `+1.0`/day cap.
- **De-duplication rule:** a source counts **at most once** per student per class day, no
  matter which channel(s) signal it. If the same authorized source is signaled via *both* its
  dedicated flag (e.g. `ti84_completed=True`) *and* `additional_sources=["ti84"]`, the two are
  treated as the **same** evidence, not independent evidence — it contributes its point value
  once, not twice.
- **Malformed source ids** (non-string, or an empty string) raise `PolicyDomainError`, not
  `PolicyDecisionRequiredError` — a malformed id is a caller-side data defect (§7.2), kept
  strictly distinct from a well-formed-but-not-yet-authorized source name (§7.3).

This is recorded machine-readably in `grading_policy.v2.json` →
`extra_credit_cap_rule.authorization_is_by_membership_not_channel` /
`.deduplication_rule` / `.malformed_source_id_policy`.

**"Tracked" ≠ automatic main-grade credit (PREF-04.6).** That a response or exercise
completion is *recorded* does not by itself grant main-grade credit. Server policy and teacher
designation are authoritative over whether recorded evidence becomes graded credit — the same
authority principle as §5 below. A client observing "the student did something today" is not
the same event as "this counts toward the grade."

---

## 5. Authority

- **Clients never determine designation or official credit (PREF-03.9).** No Desk client,
  Schoology projection, or any other consumer of this policy may decide, on its own, what
  counts as teacher-designated digital work, what qualifies as a valid participation response,
  what an item's current official score is, or what the official quarter grade is. Those
  decisions are server-policy and teacher-designation authoritative.
- **A new extra-credit source is a policy decision, not a client decision (OPEN-10).** A client
  may never decide on its own that some additional activity counts as extra credit; only an
  explicit new RC ruling can add to `AUTHORIZED_EXTRA_CREDIT_SOURCES`.
- **Teacher override always takes precedence** over any computed result (§3.1), including over
  an UNKNOWN state (§6).
- **This policy is versioned** (§3.3); v2.0 is this document and its companion JSON.

---

## 6. UNKNOWN semantics

Per `PROGRAM_DOSSIER.md` §15 item 1 ("Unknown ≠ zero"): when an input required for a
computation in this policy is unavailable, the result is **UNKNOWN** — never `0`, never a
silently-chosen branch, never fabricated credit.

Concretely, in this policy:

- If **completion** is unavailable, the quarter-rule branch (§3) is undeterminable. The
  quarter grade is **UNKNOWN**, not a guess at which branch would have applied and not `0`.
- If **work_aggregate** or **assessment_aggregate** is unavailable, the quarter grade is
  **UNKNOWN** for the same reason, even if completion itself is known.
- If a participation day's response or attendance is unavailable, the corresponding field(s) of
  its `ParticipationDay` are **UNKNOWN** (§4.1), never `0.0`.
- If any item in a point-weighted reduction (§8) has an unavailable earned or possible value,
  the whole reduction is **UNKNOWN** (§8), never computed over a partial/assumed set.
- **Zero eligible denominator is its own UNKNOWN case, now fully decided (`OPEN-16`,
  `RESOLVED by RC 2026-07-24`).** "No eligible designated work/participation" propagates
  UNKNOWN through the whole chain: `compute_completion` (assigned_count == 0),
  `compute_work_aggregate` (packet + participation possible == 0), `compute_component_percentage`
  / `compute_assessment_aggregate` (possible == 0), and therefore `compute_quarter_grade`
  itself. This is confirmed, decided behavior, not merely tolerated as in v1.0.
- **Student-facing display of an UNKNOWN quarter grade is a dash, never a zero
  (`OPEN-16`, `RESOLVED`).** `final_grade_display_string(UNKNOWN)` returns
  `UNKNOWN_DISPLAY_TOKEN` (an em dash, "—"); `UNKNOWN_DISPLAY_TEXT` ("not enough evidence") is
  the accessible long form for contexts where a bare dash is insufficient. This policy never
  syncs a fabricated zero-valued Schoology assignment to represent an UNKNOWN state.
- The **only** thing that overrides an UNKNOWN result is an explicit teacher override (§3.1) —
  because teacher designation is server-authoritative and is allowed to resolve a state the
  automated computation cannot.
- UNKNOWN is a first-class value distinct from `0`, `False`, and absence-of-record. It must
  never be coerced to a number, treated as a normal falsy value, or used to silently pick a
  default branch.

This mirrors the broader reliability principle in `PROGRAM_DOSSIER.md` §15 (cited, not
reopened): unavailability of an evidence source is never treated as evidence of zero, and never
causes previously-known state to be erased or relocked.

---

## 7. Input domains and fail-closed validation (UNKNOWN vs. a defect vs. a policy gap)

Per Codex GPT-5.6 SOL review R-A, finding A1 (HIGH): the reference implementation must not let
malformed or out-of-domain numeric input silently flow through official arithmetic (e.g.
`compute_completion(6, 5)` producing a fabricated `1.2` completion). This section states the
input domains this policy defines, the rule for what happens when they are violated, and — new
in v2.0 — the third failure mode `PolicyDecisionRequiredError` introduces (OPEN-10).

### 7.1 The domains

| Input | Domain | Enforced in |
|---|---|---|
| `completed_count`, `assigned_count` | non-negative integer; `assigned_count >= completed_count` | `compute_completion` |
| `completion` | finite number in `[0, 1]` | `compute_quarter_grade` |
| `assessment_aggregate` | finite number in `[0, 100]` (percentage scale — unchanged by OPEN-15) | `compute_quarter_grade` |
| `work_aggregate`, `teacher_override` | finite number, `>= 0`, **no upper bound** (OPEN-15: WORK may exceed 100) | `compute_quarter_grade` |
| `packet_points_earned`, `packet_points_possible`, `participation_points_earned`, `participation_points_possible`, `extra_credit_points_earned` | non-negative finite number | `compute_work_aggregate` |
| `points_earned`, `points_possible` (each item pair) | non-negative finite number | `compute_component_percentage`, `compute_assessment_aggregate` |
| `ParticipationDay.earned`, `ParticipationDay.possible` (per day, once known) | non-negative finite number | `aggregate_participation` |
| `attendance` | exactly one of `"present"`, `"partial"`, `"absent"`, `"unknown"` | `compute_participation_day` |
| `value` (a computed grade) | finite number | `round_final_grade_for_display` |

All numeric domains additionally reject non-finite numbers (`NaN`, `+inf`, `-inf`) and reject
values of the wrong type outright — a numeric input must genuinely be `int`/`float` (a Python
`bool` does **not** count, even though `bool` is technically a subclass of `int`), never a
string, never silently coerced. These domains are also recorded machine-readably in
`grading_policy.v2.json` → `"domains"`, so a downstream consumer (e.g. a Schoology projection, or
a future Desk client) can read them without parsing this prose.

Note: `work_aggregate`'s components as they feed `compute_work_aggregate` are validated only as
"non-negative finite" (no upper bound) — the same is now true of the *aggregate itself* once it
reaches `compute_quarter_grade` (unlike v1.0, where the aggregate had a `[0, 100]` ceiling not
present on its components). This is intentional: OPEN-15's ruling means WORK's scale is
genuinely unbounded above, so applying an upper bound anywhere in the WORK pipeline would
contradict the ruling, not merely leave it unresolved.

### 7.2 The rule: domain violations FAIL CLOSED — they are a defect, not UNKNOWN

**A malformed or out-of-domain input raises `PolicyDomainError`. It never returns `UNKNOWN`.**

This distinction is deliberate and load-bearing:

- **UNKNOWN** (§6) means *"this input is well-formed, but the authoritative evidence for it is
  not available right now"* (PROGRAM_DOSSIER.md §15 item 1) — a genuine, legitimate reliability
  state that this policy must never treat as zero or as a silently-picked branch.
- **A domain violation** — a negative count, `completed_count` greater than `assigned_count`, a
  completion ratio of `1.2`, a `NaN`, a string where a number is required, an `attendance` value
  outside the four-item enum — is not an evidence state at all. It is a **defect** in the caller
  (or in whatever produced the value upstream).

Returning `UNKNOWN` for a defect would let a bug silently masquerade as a legitimate
"evidence unavailable" condition — exactly the failure mode §15 exists to prevent — and it would
quietly widen "never fabricate credit" into "never even notice something is wrong." This policy
keeps the two failure modes strictly separate: **UNKNOWN propagates; a domain violation raises.**
Neither is ever converted into the other, and neither is ever clamped, coerced, or silently
"corrected" to something close enough.

`PolicyDomainError` is defined once, in `grading_policy_ref.py`, and is the only exception type
this module raises for domain violations. It is intentionally a distinct type — not reused from
elsewhere in the codebase — so that a caller can catch domain violations specifically without
also swallowing unrelated errors.

### 7.3 A third failure mode: `PolicyDecisionRequiredError` (OPEN-10, `RESOLVED`)

`compute_extra_credit` introduces a failure mode that is neither UNKNOWN nor a domain
violation: a caller supplying evidence for an extra-credit source outside
`AUTHORIZED_EXTRA_CREDIT_SOURCES`. The source name may be perfectly well-formed — the problem
is not malformation, and it is not unavailable evidence — it is that this policy has no
authority to grant credit for it yet. RC's ruling is explicit that "any FUTURE extra-credit
source requires a new policy decision — it never silently exceeds the cap," so this case raises
`PolicyDecisionRequiredError` rather than being silently ignored, added anyway, or clamped into
the existing cap. Like `PolicyDomainError`, this is its own exception type, not reused or
conflated with the other two failure modes.

**C3 remediation note (Codex review 2026-07-24, HIGH; see §4.2):** this authorization check is
by **membership** in `AUTHORIZED_EXTRA_CREDIT_SOURCES`, checked identically for a source
supplied via `additional_sources` regardless of whether a dedicated boolean flag is also present
or UNKNOWN — it is never skipped because unrelated evidence is unavailable. A *malformed*
(non-string/empty) source id is a §7.2 domain violation (`PolicyDomainError`), not a §7.3 policy
gap — the two remain strictly distinct: a well-formed-but-not-yet-authorized name raises
`PolicyDecisionRequiredError`; a malformed name raises `PolicyDomainError`.

### 7.4 Order of operations in `compute_quarter_grade`: a teacher override never masks a malformed known value

Per Codex GPT-5.6 SOL review R-A re-check, finding **R1 (MEDIUM)**: an earlier version of
`compute_quarter_grade` validated the teacher override and returned it **before** `completion`,
`work_aggregate`, or `assessment_aggregate` were domain-checked at all. That meant a perfectly
valid override could silently mask a malformed KNOWN value — e.g. `completion=1.2` or an
out-of-range `assessment_aggregate` would "sail through" unexamined whenever an override
happened to be supplied, contradicting §7.2's unconditional "malformed ⇒ raise" rule.

**The fix, and the rule it encodes:** `compute_quarter_grade` validates the domain of every
**supplied** value — `completion`, `work_aggregate`, `assessment_aggregate`, and
`teacher_override` itself — **before** override precedence is applied. Only a value that is
genuinely `UNKNOWN`/`None` skips domain validation (there is nothing to validate — it represents
unavailability, not a malformed value) and remains fully overridable exactly as before. This
ordering is unchanged by the v2.0 domain widening (§7.1) — it now simply validates
`work_aggregate`/`teacher_override` against their new unbounded-non-negative domain, and
`assessment_aggregate` against its unchanged `[0, 100]` domain, at the same point in the
sequence as before:

- **Availability vs. malformation stays the load-bearing distinction (§7.2), and this ordering is
  simply that distinction applied consistently:** an `UNKNOWN` completion or aggregate is a
  legitimate reliability state a teacher override may resolve (§3.1, §6) — this is unchanged. A
  malformed KNOWN completion or aggregate (out of range, wrong type, non-finite) is a defect and
  raises `PolicyDomainError` **even when a well-formed override is also supplied** — an override
  is never allowed to "cover for" a bad known input.
- A malformed override itself still raises `PolicyDomainError`, exactly as before.
- Teacher-override precedence over genuine `UNKNOWN` (§3.1) is preserved exactly: if
  `completion`/`work_aggregate`/`assessment_aggregate` is `UNKNOWN` and a well-formed override is
  supplied, the override still wins.

---

## 8. Point-weighted multi-item reduction (OPEN-19, `RESOLVED by RC 2026-07-24`)

RC's ruling: "`component_percentage = 100 * sum(current_official_points_earned) /
sum(points_possible)` for packet assignments, lesson quizzes, topic assessments, any same-kind
designated group. Each item contributes its CURRENT OFFICIAL server-designated score;
attempt-selection/overrides are governed by their own rules (out of scope here). NEVER
equal-average assignment percentages when possible-points differ." And, for the ASSESSMENT
side specifically: "`ASSESSMENT = 100 * total_assessment_points_earned /
total_assessment_points_possible` (quizzes + topic assessments on their actual point scales)."

This is a genuinely new rule — v1.0 had no multi-item reduction at all; it implicitly assumed a
single scalar packet-work/assessment score with no defined way to combine several items of
differing point value.

```
component_percentage = 100 * sum(points_earned) / sum(points_possible)
```

- **Point-weighted, never equal-averaged.** Two items worth `9/10` and `2/50` reduce to
  `100 * (9 + 2) / (10 + 50) = 18.3%`, NOT the equal average of their individual percentages
  (`(90% + 4%) / 2 = 47%`). Equal-averaging per-item percentages when possible-points differ
  across items is explicitly FORBIDDEN by RC's ruling — it silently over-weights low-point
  items and under-weights high-point ones relative to their actual share of the total possible
  points.
- **Each item contributes its CURRENT OFFICIAL server-designated score.** Which score is
  "current official" for an item with multiple attempts (e.g. best-of, most-recent, teacher-
  selected) is governed by its own separate rule, out of scope for this policy — this reduction
  only ever consumes whatever `(points_earned, points_possible)` pair it is handed for that
  item.
- **Never add a percentage directly to raw flat points.** As in §1.1, a percentage-scale value
  must be converted to a point pair on a consistent scale before it enters this formula.
- **Zero denominator falls to OPEN-16's rule (§2, §6):** `sum(points_possible) == 0` (including
  the empty-items case) returns `UNKNOWN`, never a fabricated 0% or a `ZeroDivisionError`.
- **Applies to any same-kind designated group,** not only ASSESSMENT: packet assignments,
  lesson quizzes, topic assessments, or any other group of items a teacher has designated as
  belonging together. `compute_component_percentage(items)` is the general-purpose function;
  `compute_assessment_aggregate(items)` is a named wrapper over it specifically for the
  lesson-quiz + topic-assessment group (PREF-03.3, §1.2), so that ASSESSMENT's own role in this
  policy (never touched by extra credit — PREF-04.5) has a dedicated entry point.

---

## 9. Decided rulings — OPEN items resolved 2026-07-24

RC's decision text settles the two-aggregate model, the WORK/ASSESSMENT composition, the
completion-percentage definition and scope, the 40% gate and its inclusivity, both branch
formulas, teacher-override precedence, and the four participation/extra-credit unit values.
RC's 2026-07-24 NT16 rulings settle the seven items that were previously open. Each is listed
below with its canonical ID, ruling text, provenance, and what v1.0 provisional choice it
supersedes. None of these is an invented default — each is RC's own ruling text, implemented
exactly.

- **`OPEN-08` — Completion-percentage rounding.** `RESOLVED by RC 2026-07-24`. Ruling: "Compare
  the EXACT completion ratio against the inclusive 0.40 threshold. No pre-rounding before branch
  selection." Supersedes: v1.0's `compute_completion` exposed an opt-in `round_ndigits`
  parameter (default `None`, no rounding) as an unresolved-pending-RC placeholder; v2.0 removes
  `round_ndigits` entirely. See §2, §3.
- **`OPEN-09` — Point/score rounding for aggregates and the published grade.**
  `RESOLVED by RC 2026-07-24`. Ruling: "Full precision internally. Round ONLY the student-facing
  final-grade DISPLAY to one decimal. Schoology keeps native earned/possible totals.
  Reconciliation compares underlying values consistently and must not mistake display rounding
  for substantive divergence." Supersedes: v1.0's `compute_quarter_grade` exposed an opt-in
  `round_ndigits` parameter with no internal/display distinction; v2.0 removes it and adds
  `round_final_grade_for_display` / `final_grade_display_string`. See §3.2.

  **C5 addendum (MEDIUM, Codex review 2026-07-24) — the rounding MODE, labeled, not invented.**
  RC's ruling above fixes "round the display to one decimal" but says NOTHING about which
  tie-breaking mode to use for a value that lands exactly on a `.x5` boundary at that precision.
  `round_final_grade_for_display` uses Python's built-in `round`, whose mode is **half-even**
  ("banker's rounding"): `round(0.25, 1) == 0.2` (rounds DOWN to the even `0.2`), `round(0.35, 1)
  == 0.3` (rounds DOWN to the even `0.3`). This is now stated EXPLICITLY — in the function's
  docstring and in `grading_policy.v2.json` → `rounding_rules.display_rounding_mode` — as an
  **IMPLEMENTATION READING pending RC confirmation, not a ruling**, per the same "do not invent
  silently" discipline already applied to OPEN-11's excused/unknown reading (§4.1). Half-even is
  Python's default, not a value RC's text specifies. **No new `OPEN-NN` id is minted** for this
  residual question — the resolved-item register is closed at exactly `OPEN-01`..`OPEN-19`
  (enforced by a package guard); a future package may record the residual question under its own
  id if RC's confirmation ever narrows or changes it. (This half-even reading was later AMENDED
  by RC's own direct ruling on the mode — see immediately below.)

  **AMENDED by RC 2026-07-24 (later same date; NT16-B).** RC has since directly ruled on the
  residual rounding-MODE question the C5 addendum above flagged. Verbatim: "Use conventional
  decimal ROUND_HALF_UP for the student-facing one-decimal display. Example: 89.25 -> 89.3. Do
  not use Python binary-float round() or half-even behavior for the display contract. Keep full
  precision internally. Do not round before the 40% branch decision. Schoology reconciliation
  compares underlying values; display rounding cannot conceal real divergence." This SUPERSEDES
  the half-even reading the C5 addendum recorded (preserved above as history, not current
  behavior); `round_final_grade_for_display` now rounds via
  `decimal.Decimal(value).quantize(exponent, rounding=ROUND_HALF_UP)`, with `exponent` derived
  from `final_grade_display_decimals` rather than hard-coded. See §4.1's own amendment note for
  the analogous OPEN-11 confirmation. No new `OPEN-NN` id is minted; `OPEN-09` stays `RESOLVED`.
- **`OPEN-10` — Daily cap on extra-credit participation points.** `RESOLVED by RC 2026-07-24`.
  Ruling: "+1.0 point per student per class day cap for currently-authorized extra credit
  (TI-84 +0.5, Equation Lab +0.5, stacking allowed). Any FUTURE extra-credit source requires a
  new policy decision — it never silently exceeds the cap." Supersedes: v1.0's
  `compute_extra_credit` applied no cap by default and exposed an opt-in `daily_cap` parameter;
  v2.0 makes the 1.0-point cap unconditional and raises `PolicyDecisionRequiredError` for any
  unauthorized additional source. See §4.2, §7.3.
- **`OPEN-11` — Participation credit on partial-attendance / non-class days.**
  `RESOLVED by RC 2026-07-24`. Ruling: "Non-class days are EXCLUDED from the participation
  requirement. Partial/absent/uncertain attendance NEVER auto-zeroes — such days are
  excused/unknown unless RC explicitly designates the day participation-eligible. UNKNOWN is
  distinct from zero." Supersedes: v1.0's `compute_participation_point` returned `UNKNOWN` for
  any non-class or partial-attendance day; v2.0 replaces it with `compute_participation_day`,
  distinguishing excluded, excused, counted, and genuinely-unknown cases. See §4.1.

  **CONFIRMED by RC 2026-07-24 (later same date; NT16-B).** RC's excused-vs-unknown reading
  (§4.1) is now directly confirmed, not merely a documented reading — see §4.1's own amendment
  note and `OPEN_DECISIONS_REGISTER.md`'s OPEN-11 section for RC's verbatim four-point
  confirmation. No code change; `compute_participation_day` already conformed.
- **`OPEN-15` — WORK-aggregate component combination + scale normalization.**
  `RESOLVED by RC 2026-07-24`. Ruling: "WORK = 100 * (packet_points_earned +
  participation_points_earned + extra_credit_points_earned) / (packet_points_possible +
  participation_points_possible). Only teacher-designated official evidence enters. Extra
  credit raises the numerator but NOT the denominator. WORK MAY EXCEED 100. Zero denominator
  falls to OPEN-16's rule. NEVER add a percentage directly to raw flat points." Supersedes:
  v1.0's `compute_work_aggregate` combined the three components by plain scalar addition with
  no common scale. See §1.1.
- **`OPEN-16` — Completion percentage when no digital work has been designated yet (zero
  denominator).** `RESOLVED by RC 2026-07-24`. Ruling: "No eligible designated work/
  participation => completion UNKNOWN, WORK UNKNOWN, quarter grade UNKNOWN. Student-facing
  display = dash / 'not enough evidence', never zero." Supersedes: v1.0 already returned
  `UNKNOWN` for `compute_completion`'s zero-denominator case, but left the real-world
  consequence (an early-quarter UNKNOWN window) unresolved-pending-RC; v2.0 confirms UNKNOWN
  propagation through WORK and the quarter grade as decided policy, with a defined display
  convention. See §2, §6.
- **`OPEN-19` — Multi-item reduction (point-weighted).** `RESOLVED by RC 2026-07-24`. Ruling: see
  §8 in full. Supersedes: v1.0 had no multi-item reduction rule at all. See §8.

None of these rulings changes any value RC's original text already settled (the 40% gate, its
inclusivity, the branch formulas, or the four participation/extra-credit unit values).

---

## Changelog — NT16 (v2.0)

- **Supersedes `grading_policy.v1.json` (deleted) and this document's v1.0.** All machine-
  readable constants now live solely in `grading_policy.v2.json`.
- **OPEN-08 (RESOLVED):** exact-ratio completion comparison; `compute_completion`'s
  `round_ndigits` parameter removed.
- **OPEN-09 (RESOLVED):** full-precision internal computation; new display-only
  `round_final_grade_for_display` / `final_grade_display_string`; `compute_quarter_grade`'s
  `round_ndigits` parameter removed.
- **OPEN-10 (RESOLVED):** unconditional `+1.0`/student/class-day extra-credit cap
  (`EXTRA_CREDIT_DAILY_CAP_POINTS`); `compute_extra_credit`'s opt-in `daily_cap` parameter
  removed; new `additional_sources` parameter raises `PolicyDecisionRequiredError` for any
  source outside `AUTHORIZED_EXTRA_CREDIT_SOURCES`.
- **OPEN-11 (RESOLVED):** `compute_participation_point` replaced by `compute_participation_day`
  (returning the new `ParticipationDay` NamedTuple) and `aggregate_participation`, distinguishing
  excluded-non-class, excused-not-eligible, counted, and genuinely-unknown-attendance cases.
  `compute_participation_point` is REMOVED (no back-compat wrapper is kept; no file outside
  `product-policy/`'s NT15/NT16 artifacts referenced it).
- **OPEN-15 (RESOLVED):** `compute_work_aggregate`'s signature and formula replaced entirely —
  point-based ratio over packet + participation + extra-credit points, WORK may exceed 100.
- **OPEN-16 (RESOLVED):** zero-eligible-denominator consequence (completion/WORK/quarter grade
  all UNKNOWN) confirmed as decided policy, with `unknown_display_token` / `unknown_display_text`
  as the defined student-facing rendering.
- **OPEN-19 (RESOLVED, new):** point-weighted multi-item reduction added —
  `compute_component_percentage`, `compute_assessment_aggregate`. Equal-averaging per-item
  percentages when possible-points differ is forbidden.
- **New exception type:** `PolicyDecisionRequiredError`, distinct from `PolicyDomainError`, for
  extra-credit requests this policy is not yet authorized to grant (§7.3).
- **`compute_quarter_grade` domain widened:** `work_aggregate` and `teacher_override` lose their
  `[0, 100]` ceiling and become non-negative with no upper bound (OPEN-15); `assessment_aggregate`
  keeps `[0, 100]` (PREF-04.5, unaffected).
- **`grading_policy.v2.json`:** `provisional_implementation_choices` removed and replaced by
  `resolved_open_items` (all seven items carry `status: "RESOLVED"`, a
  `"RESOLVED by RC 2026-07-24"` provenance token, RC's ruling text, and what v1.0 choice each
  supersedes); `open_item_ids` is now empty; `resolved_open_item_ids` lists the seven resolved
  items; new constants `extra_credit_daily_cap_points`, `authorized_extra_credit_sources`,
  `final_grade_display_decimals`, `unknown_display_token`, `unknown_display_text`; new
  `work_aggregate_formula`, `assessment_aggregate_formula`, `component_reduction_rule`,
  `rounding_rules`, `extra_credit_cap_rule`, `participation_day_rule`, `zero_denominator_rule`,
  and top-level `changelog` blocks.

## Changelog — NT16 Codex-review remediation (v2.0, same date)

A Codex review pass over this v2.0 package found four defects in the IMPLEMENTATION of
already-RESOLVED rulings (not in the rulings themselves — no OPEN-NN ruling text is changed by
this remediation). See `grading_policy.v2.json` → `changelog` (the `NT16-codex-remediation` and
`NT16-codex-remediation-c1-hardening` entries) for the machine-readable form.

- **C1 (HIGH):** `compute_quarter_grade`'s 0.40 gate compared a binary float `completion` ratio
  to `completion_threshold`, which can collapse to exactly the threshold for large
  `completed_count`/`assigned_count` pairs even when the true rational value is strictly below
  it. Fixed via an exact integer cross-product (§3, "C1 remediation" above): `compute_completion`
  now returns a `CompletionRatio` (a `float` subclass carrying its own exact counts) so the
  ordinary `compute_quarter_grade(w, a, compute_completion(c, n))` sequence is exact by
  construction; `compute_quarter_grade` also gains explicit `completed_count=`/`assigned_count=`
  keyword-only arguments, which take highest precedence; a bare float with no carried counts and
  no explicit kwargs remains the sole, documented-imprecise fallback. New public
  `compute_completion_threshold_met`. `completion_threshold`'s exact `Fraction` form is now
  derived from the JSON file's decimal literal (not the lossy binary float), with an import-time
  invariant assertion.
- **C3 (HIGH):** `compute_extra_credit` decided authorization by which parameter the caller used
  instead of by membership in `authorized_extra_credit_sources`. Fixed (§4.2, "C3 remediation"
  above): authorization is now membership-based, checked for every supplied source
  unconditionally before the UNKNOWN short-circuit; a source counts at most once per student per
  class day regardless of which channel signals it; a malformed source id raises
  `PolicyDomainError`, distinct from an unauthorized-but-well-formed one.
- **C4 (HIGH):** `compute_assessment_aggregate` (via `compute_component_percentage`) had no
  per-item ceiling, so an earned-exceeds-possible item could push the reduction above `100`.
  Fixed (§8): `compute_component_percentage` gains `allow_above_100` (default `False`, strict);
  `compute_assessment_aggregate` always uses the strict default, so its result is guaranteed in
  `[0, 100]` by construction.
- **C5 (MEDIUM):** `round_final_grade_for_display`'s rounding MODE (Python's half-even /
  "banker's rounding") was never stated. Fixed (§9, OPEN-09 addendum below): explicitly labeled,
  in the docstring and in `grading_policy.v2.json` → `rounding_rules.display_rounding_mode`, as an
  implementation reading pending RC confirmation — not a ruling. No new `OPEN-NN` id is minted;
  the resolved-item register stays exactly `OPEN-01`..`OPEN-19`. **AMENDED by RC 2026-07-24
  (later same date; NT16-B):** the mode is now decided — half-up (decimal `ROUND_HALF_UP`), per
  RC's verbatim ruling recorded in §9's `OPEN-09` addendum above; this entry is left otherwise
  unchanged as the historical record of the original C5 finding.

## Changelog — NT16 Codex re-check remediation (v2.0, same date)

A Codex re-check pass over the prior remediation found two further HIGH-severity residuals: one
in the IMPLEMENTATION of the already-fixed C1 ruling (not the ruling itself), and one a stale
document passage left behind by the C2 code fix. See `grading_policy_ref.py`'s module docstring
("Codex review remediation") and `grading_policy.v2.json` → `changelog` for the machine-readable
form of the V1 entry.

- **V1 (HIGH):** the C1-hardening prose (§3, above) said `CompletionRatio` "behaves as an
  ordinary float everywhere" without disclosing that every one of those "ordinary float"
  operations — arithmetic, coercion, rounding, copying, serialization — silently discards the
  carried counts and degrades the ratio to a bare `float`, which routes branch selection to the
  documented-imprecise tier-3 fallback. Fixed (§3, "V1 hardening" above): the documentation now
  states this plainly everywhere it previously overstated the guarantee (this document,
  `grading_policy_ref.py`'s `CompletionRatio`/`compute_completion`/`compute_quarter_grade`
  docstrings, and `grading_policy.v2.json`'s `quarter_rule.gate_decision_from_counts`).
  `CompletionRatio.completed_count`/`.assigned_count` are now READ-ONLY (properties over private
  slots; assignment raises `AttributeError`), closing the tampering hole where a mutated ratio
  could lie about its own provenance. `compute_quarter_grade` gains a count-vs-float consistency
  check: whenever `completion` carries counts, it verifies
  `float(fractions.Fraction(completed_count, assigned_count))` equals the ratio's own float value
  before trusting those counts for the gate, raising `PolicyDomainError` (never UNKNOWN) for a
  crafted/corrupted ratio whose counts disagree with its float — verified not to false-positive
  across the witness pair, the exact `2/5` boundary, `39/100`, `0/1`, and `n/n`.
  `CompletionRatio.__reduce__` makes copying/pickling degrade honestly to a bare `float` instead
  of raising `TypeError`.
- **V2 (HIGH, document half):** §3.2's Schoology-reconciliation bullet still stated, as live
  normative text, the forgiveness rule the C2 remediation had already DELETED from
  `parity_check.py` — "a difference that disappears once both sides are rounded to one decimal is
  display rounding... and must not be reported as one." That is a reimplementation hazard: it
  reads as an instruction to round both sides and treat a match as non-divergent, exactly the
  defect C2 fixed in code. Fixed (§3.2, above): the bullet now states the corrected semantics —
  reconciliation compares underlying full-precision values only, rounding never forgives a
  difference, and a display-rounded-observation basis is explicitly degraded
  (`comparison_basis`/`underlying_convergence_established`) rather than treated as equivalent to
  the underlying value. (The corresponding code fix, `parity_check.py`'s C2 remediation, and the
  package-wide stale-phrase guard against this formulation recurring, are tracked by a separate,
  concurrently-running work package — this entry covers only this document's normative text.)

## Changelog — NT16-B RC amendment and confirmation (2026-07-24, later same date)

RC issued two further rulings later on 2026-07-24, resolving the two implementation readings the
Codex-review remediation above had explicitly flagged as "pending RC confirmation" (C5's OPEN-09
rounding-mode reading, AMENDED below, and OPEN-11's excused-vs-unknown reading, CONFIRMED below).
Neither ruling reopens its OPEN-NN id or mints a new one; both OPEN-09 and OPEN-11 remain
`RESOLVED`.

- **OPEN-09, rounding MODE — AMENDED.** RC's verbatim ruling: "Use conventional decimal
  ROUND_HALF_UP for the student-facing one-decimal display. Example: 89.25 -> 89.3. Do not use
  Python binary-float round() or half-even behavior for the display contract. Keep full precision
  internally. Do not round before the 40% branch decision. Schoology reconciliation compares
  underlying values; display rounding cannot conceal real divergence." `round_final_grade_for_
  display` (`grading_policy_ref.py`) is rewritten to round via
  `decimal.Decimal(value).quantize(Decimal(1).scaleb(-FINAL_GRADE_DISPLAY_DECIMALS),
  rounding=ROUND_HALF_UP)`, constructing the `Decimal` directly from the exact binary `float`
  value (never from `str(value)`, which would introduce a hidden double-rounding step) — never
  Python's builtin `round`. This SUPERSEDES the C5 half-even implementation reading (§9, above),
  which is preserved in place as the historical record of what this package guessed before RC's
  amendment, not as current behavior. `grading_policy.v2.json`'s `rounding_rules.display_
  rounding_mode` and this document's §4.1/§9 passages are updated with the same provenance.
- **OPEN-11, excused-vs-unknown reading — CONFIRMED.** RC's verbatim four-point confirmation: "A
  known absent, partial-attendance, or non-class day is excused and contributes 0 earned / 0
  possible. A genuinely uncertain attendance state remains UNKNOWN. Neither case produces an
  automatic participation zero. RC may explicitly designate an otherwise excused day as
  participation-eligible." `compute_participation_day` already conformed to all four points
  before this confirmation — no code change accompanies it, only the removal of the "pending RC
  confirmation" / "documented reading, not itself a ruling" labeling §4.1 previously carried.
