# Schoology Projection & Reconciliation Contract

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

Deliverable D3 (Schoology projection + reconciliation contract), RC decision area 5 (`PREF-05`), with
`PREF-11` for organization/surfaces and `PREF-03` for the grade formula being projected. This document is a
**contract**, not an integration. It specifies structure, rules, and verdicts; it does not, and must not,
perform any live action against Schoology (§9).

**Resolved open-item dependencies (NT16, 2026-07-24):** v1.0 of this document touched two RC-owned open items
it explicitly did not resolve: `OPEN-15` (how the WORK aggregate's components combine and normalize to a
common scale — owned by D2/`GRADING_POLICY_SPEC.md`, cited here only as a secondary, provisional illustration
in §4.3) and `OPEN-19` (how multiple same-kind items reduce to a single scalar — this document's own
parity-fixture simulation convention, §4.3). RC issued final rulings on both on 2026-07-24 (see
`grading_policy.v2.json` → `resolved_open_items`). This version's §4.3 has been genuinely reworked, not merely
relabeled, to reflect the now-decided point-based arithmetic — see §4.3 for the refreshed reasoning and
recomputed numbers. Two further items land on this document specifically in this tranche: `OPEN-09`
(rounding — reconciliation must be display-rounding-aware, §8) and `OPEN-16` (zero denominator — the
projector must never fabricate a zero-valued assignment, §3). All four (`OPEN-09`, `OPEN-15`, `OPEN-16`,
`OPEN-19`) are `RESOLVED by RC 2026-07-24`; `OPEN-04` (human-facing naming strings) remains genuinely open and
is unaffected by any of this tranche's rulings.

Machine-readable companion: `schoology_projection.v2.json`. Reference simulator/parity checker:
`parity_check.py` + `test_parity_check.py`, run against synthetic fixtures in `fixtures/schoology/`.

---

## 0. CRITICAL FRAMING — read before anything else

**Schoology course/section IDs do not exist yet.** There is no live Schoology access, no API call, no
CDP/browser write, and no network call of any kind involved in producing or verifying this contract. Every
identifier used below and in the fixtures (`SYNTHETIC-COURSE-0001`, `SYNTHETIC-SECTION-0001A`, etc.) is
invented and does not correspond to any real Schoology tenant. This document specifies what a future,
explicitly-authorized implementation phase must do; it does not itself do it. See §9 for the binding
normative statement of this constraint.

---

## 1. Role of Schoology (`PREF-05`)

Per RC Area 5, Schoology is **not a passive mirror**. It is, and is intended to eventually become:

- The **primary school-facing assignment surface** — where students and families see what is due.
- The **familiar grade-alert home** — the notification channel families already check and trust.
- The **school-facing gradebook display** — the number a parent, counselor, or administrator looks at
  first.
- The **deep-link surface** into exact Desk activities — a lesson, a lesson quiz, an assigned TI-84
  exercise, an assigned Equation Lab exercise (§5; also required by `PREF-08` for TI-84 specifically).
- An **independent calculator** of the published grade, wherever Schoology's own category/weight gradebook
  model can faithfully express RC's grading policy (`PREF-03`). Where it cannot (§4), Schoology's native
  computation is demoted to informative status and A2's computation becomes the sole authoritative source
  for that figure — but Schoology still computes *something* natively from the assignments A2 publishes,
  and that something is exactly what this contract's reconciliation step exists to check.

**What A2 retains regardless of any of the above:**

- **Durable evidence.** The append-only evidence ledger (`PROGRAM_DOSSIER.md` §15 item 7) lives in A2, not
  Schoology. Schoology assignments and grades are a *projection* of that evidence, never the evidence itself.
- **Item identity.** Which Savvas bank item, which registry `item_uid`, which Desk activity produced a given
  score is an A2 fact. Schoology's assignment objects carry enough structure to deep-link back to it (§5),
  but Schoology is never asked to reconstruct or re-derive item identity.
- **Teacher designation.** Whether a given piece of evidence *counts* toward WORK, ASSESSMENT, completion,
  or extra credit is decided by A2's server-side teacher-designation function (`PREF-03.9`, `PREF-04.6`).
  Schoology never makes this call (§2, hard constraint).
- **Policy versioning.** `grading_policy.v2.json` (the sibling D2 deliverable, superseding v1.0 as of the
  2026-07-24 NT16 rulings) is the versioned source of truth for the formula. Schoology has no concept of
  "policy version" and is not asked to have one.
- **Receipts / audit.** Every projection run and every reconciliation check produces a structured record
  (§7, §8) that A2 retains; Schoology's own audit trail (if any) is not relied upon as the system of record.
- **Independently computing the expected grade.** A2 computes its own authoritative quarter grade
  (`grading_policy_ref.py`) without depending on Schoology's math being correct, available, or even
  reachable. This is the entire premise of §2's "two calculations" requirement.

---

## 2. The required principle: one policy, two calculations, explicit reconciliation

RC's text is explicit and this contract treats it as load-bearing, not decorative. Three obligations follow
directly from it:

1. **Publish granularity.** A2 must publish assignments, categories, points, and grades at a granularity fine
   enough that Schoology's own gradebook math can compute a meaningful, reproducible **informative native
   calculation** over that published per-category evidence — not from some external explanation of A2's
   formula that Schoology's UI can't represent. This does **not** mean Schoology's native calculation
   reproduces A2's official quarter grade: §4 establishes that, for the completion-gated conditional formula,
   it structurally cannot. The official quarter grade remains A2-computed and is published as the sole
   authoritative value (§4.6). §3 specifies this granularity; §4 is the honest accounting of exactly where —
   and why — Schoology's native computation and A2's authoritative computation diverge.
2. **Compare, don't assume.** Every reconciliation cycle computes Schoology's result from what was actually
   published and compares it, mechanically, against A2's independently-computed expected result. Agreement
   is never assumed from the act of publishing; it is checked (§8, `parity_check.py`).
3. **Surface, never silently accept two conflicting official totals.** If the two numbers disagree, that
   disagreement is a first-class output surfaced to RC — never averaged away, never silently overwritten in
   either direction, never left for a parent or student to discover as an unexplained discrepancy between
   "what Schoology says" and "what the report card says" (§8).

**RC's hard constraint, stated plainly:** Schoology must **never retroactively decide which raw evidence
qualifies for credit.** Qualification — whether a submission counts as a valid participation response,
whether a packet answer is teacher-designated for credit, whether an extra-credit exercise was "completed
successfully" — is A2's teacher-designation function (`PREF-03.9`, `PREF-04.6`), and it happens **upstream**
of projection. By the time a score reaches Schoology, the qualification question has already been answered;
Schoology receives an already-decided point value, never a raw submission it could re-judge. This is not
merely a data-flow convenience — it is the boundary that keeps Schoology's role advisory-and-display rather
than authoritative-and-judging, consistent with §1's "A2 retains" list.

---

## 3. Assignment / category mapping

Organized by topic and lesson per `PREF-11` (organization & surfaces: "projections organized by topic and
lesson"). Two Schoology grading categories carry the two A2 aggregates 1:1 (`PREF-03.1`):

| A2 category | Schoology category | Composition (`PREF-03.2`/`.3`) |
|---|---|---|
| WORK | `WORK` | teacher-designated digital packet work + daily participation evidence + designated extra credit |
| ASSESSMENT | `ASSESSMENT` | lesson quizzes + topic assessments |

Per-entity mapping, one row per A2 entity type. **Human-facing naming strings (assignment titles, category
display names) are unresolved — `OPEN-04`.** This contract specifies *structure only*: which category, what
granularity, what point value, whether the Schoology "Extra Credit" flag applies. Final display strings are
RC's to set later.

| A2 entity | Schoology category | Granularity | Points | Extra-credit flag | Notes |
|---|---|---|---|---|---|
| Lesson packet work | WORK | one assignment per lesson | teacher-set (fixtures use 100.0) | no | Digital, teacher-designated portion only (`PREF-02`) — pure paper practice is never projected, never graded, never tracked. |
| Daily participation | WORK | one assignment per eligible class day per lesson | `1.0` present / `0.0` absent (`PREF-04.1`/`.2`) | no | Participation is inherently at most `1.0` per class day (`PREF-04.1`/`.2`); the daily cap RC settled under `OPEN-10` (`RESOLVED by RC 2026-07-24`) governs **extra credit**, not this row — see the two extra-credit rows below. Day eligibility follows `OPEN-11` (`RESOLVED by RC 2026-07-24`): a non-class day, and an excused partial-attendance/absent day RC has not designated participation-eligible, contribute **no assignment at all** (excluded from the requirement — never a projected `0`). A day whose attendance is genuinely unknown projects as UNKNOWN, never `0` (§8). |
| TI-84 extra credit | WORK | one assignment per assigned TI-84 exercise | `0.5` (`PREF-04.3`) | **yes** | Belongs to WORK, never ASSESSMENT (`PREF-04.5`). Deep-link required (`PREF-08`, §5). A2 applies the `+1.0` per-student-per-class-day extra-credit cap (`OPEN-10`, `RESOLVED by RC 2026-07-24`) **before** projection; this contract projects the already-capped earned points and never re-caps or un-caps them. |
| Equation Lab extra credit | WORK | one assignment per assigned Equation Lab exercise | `0.5` (`PREF-04.4`) | **yes** | Belongs to WORK, never ASSESSMENT (`PREF-04.5`). Deep-link required (§5). Same `+1.0`/student/class-day cap as the TI-84 row (`OPEN-10`, `RESOLVED by RC 2026-07-24`) — the two stack to the cap, and A2 applies it before projection. |
| Lesson quiz | ASSESSMENT | one assignment per lesson | teacher-set (fixtures use 100.0) | no | |
| Topic assessment | ASSESSMENT | one assignment per topic | teacher-set (fixtures use 100.0) | no | |
| **Official quarter grade** | *(none — not a category total)* | one manual/override column per grading period | N/A | N/A | Authoritative; see §4. |

**Release gating.** Only lessons in a state that is actually live to students are projected as live Schoology
assignments, mirroring the seven canonical Desk lesson states (`DESK_STATE_MODEL.md`, `PREF-01`):

- `today`, `released`, `completed` → always projected.
- `temporarily-unavailable` → **still projected, never retracted.** Unavailability of an evidence source must
  never hide or remove already-published work (`PROGRAM_DOSSIER.md` §15 item 2). This state means "A2 cannot
  currently determine completion," not "Schoology should un-publish the assignment."
- `unreleased`, `skipped` → **never projected.** Publishing an assignment for a lesson students cannot yet
  see (or will never see in sequence) would contradict `PREF-01`'s release model at the school-facing surface.
- `optional-catalog` (e.g., Lesson 4-1, `nt14-ingest-4-1-2026-07-23`) → **never projected unless a teacher has
  explicitly assigned it.** This mirrors `qb.select()`'s `include_optional` opt-in exactly (`CLAUDE.md` §
  "Lesson 4-1 (OPTIONAL CATALOG)") — optional-catalog content is never auto-scheduled, and that guarantee
  extends to the Schoology projection layer, not just the Desk navigation layer.

**Fail-closed convention (Codex SOL review R-B, findings B1 and R2).** The rules above describe the *intent*;
the following describes exactly how `_should_project()` decides it, because "unknown state is not permission"
has to be spelled out precisely or it silently rots into "unknown state defaults to permission":

1. **Missing, `None`, empty, or unrecognized `lesson_state` is NEVER treated as permission to project.** Only
   an explicitly recognized always-project state authorizes projection; there is no permissive default.
2. **The REAL NT14 content-registry marker is honored directly.** A raw registry row (qb.py; record
   `nt14-ingest-4-1-2026-07-23`) carries a top-level `availability` field, not this catalog schema's own
   invented `lesson_state` field — a raw row has no `lesson_state` at all. `_should_project()` checks
   `availability == "optional-catalog"` independently of `lesson_state`; either signal being optional-catalog
   is enough to require explicit assignment, and the restrictive reading always wins over a permissive or
   disagreeing `lesson_state`.
3. **A present-but-unrecognized `availability` value fails closed immediately, unconditionally, before
   `lesson_state` is even consulted** (R2 fix). A case variant (`"Optional-Catalog"`) or any other garbage
   value is never ignored and never allowed to fall through to a permissive `lesson_state` — only a genuinely
   *absent* `availability` (the normal case for the vast majority of records) continues to the `lesson_state`
   check.
4. **`explicitly_assigned` must be strictly boolean, checked by identity, never by truthiness** (R2 fix). Only
   the literal Python singleton `True` counts as assigned; only literal `False` (or the key being absent, which
   defaults to `False`) counts as legitimately not-yet-assigned. Any other value — a stringified `"true"` or
   `"false"`, an int `1` or `0`, an explicit `None` — is a type/serialization anomaly, not a legitimate signal:
   it fails closed and is never coerced. (The specific hole this closes: `bool(x)` treats *any* non-empty
   string as truthy, so a record carrying `"explicitly_assigned": "false"` would otherwise publish
   optional-catalog content.)
5. **A malformed record is fail-closed AND surfaced, never silently dropped** (R2 fix, §8). Rules 3 and 4
   above are the ONLY two conditions this contract currently classifies as "malformed" (as opposed to routine
   non-projection); `parity_check.detect_projection_anomalies()` returns the structured list — see §8.

`parity_check.py`'s `project_course()` / `_should_project()` / `_classify_entry()` / `detect_projection_anomalies()`
implement this gating exactly; see `test_parity_check.py::test_project_course_gates_on_canonical_lesson_states`,
`::test_optional_catalog_lesson_is_projected_only_when_explicitly_assigned`,
`::test_temporarily_unavailable_lesson_is_still_projected_never_retracted`, the `test_b1_*` group, and the
`test_r2_*` group.

**Zero-denominator / no-fabricated-zero rule (`OPEN-16`, `RESOLVED by RC 2026-07-24`).** RC's ruling on the D2
side (`grading_policy.v2.json` → `zero_denominator_rule`) is: no eligible designated work/participation/
assessment evidence (denominator `== 0`) means completion, WORK, ASSESSMENT, and the quarter grade are ALL
`UNKNOWN` — never a fabricated `0` or `100`, and student-facing display is a dash / "not enough evidence,"
never zero. This tranche makes the corollary explicit for the projection layer specifically:

- **The projector must never fabricate a synthetic zero-scored/zero-points assignment to force a grade into
  being computable.** `project_course()` only ever emits assignment records that trace back to a REAL catalog
  entry in `course_catalog["lessons"]` — it has no code path that synthesizes an assignment out of nothing,
  and in particular it never invents a placeholder zero-points assignment purely so some downstream ratio
  becomes computable. A student with no eligible designated evidence is a per-student reconciliation fact
  (see §8), not something this projector "fixes" by fabricating evidence.
- **An all-`UNKNOWN` student still reconciles as `UNKNOWN`, on both sides, never forced to a number.** When a
  student has no eligible designated work, participation, or assessment evidence posted at all (e.g. a
  brand-new student added before any digital work has been designated this early in the quarter), A2's
  authoritative quarter grade is `UNKNOWN` (per the D2 ruling above) AND Schoology's native flat-ratio figure
  is *also* `UNKNOWN` (its own possible-points denominator is `0`, so `compute_schoology_native_grade` returns
  `UNKNOWN` rather than dividing by zero or silently reporting `0%`). Per §8, `UNKNOWN` is still surfaced for
  RC review — it is never treated as "nothing to reconcile," and it is never coerced into a number by either
  side of the comparison.
- `fixtures/schoology/student_0005_zero_denominator_no_eligible_evidence.json` is the dedicated fixture for
  this case (every assignment list empty, `completion_pct: null`); `test_parity_check.py`'s zero-denominator
  test group asserts `work_aggregate`, `assessment_aggregate`, `a2_expected_quarter_grade`, and
  `schoology_native_quarter_grade` are all `parity_check.UNKNOWN` (never `0` or `0.0`), and that every record
  `project_course()` emits traces to a real catalog entry with `points_possible > 0` (never a fabricated
  zero-points placeholder). See `schoology_projection.v2.json` → `zero_denominator_rule` for the
  machine-readable form of this rule.

---

## 4. NATIVE-FEASIBILITY VERDICT — the 40%-conditional formula

### 4.1 The question

Is `PREF-03`'s quarter-grade rule —

```
if completion >= 0.40:                       # inclusive (PREF-03.5)
    quarter_grade = max(work_aggregate, assessment_aggregate)      # PREF-03.5
else:
    quarter_grade = average(work_aggregate, assessment_aggregate)  # PREF-03.6
```

— natively representable inside Schoology's own gradebook computation, using only the category/weight
machinery Schoology's gradebook is documented to provide?

### 4.2 Reasoning from Schoology's documented gradebook capability model

Schoology's gradebook is built around a small, well-known set of primitives. Reasoning from that model
(**ASSUMPTION-1** — see §4.5; this is the state of Schoology's gradebook as generally documented and
understood, not something re-verified against a live tenant for this contract):

- **Grading categories** group assignments (e.g., "Homework," "Tests") and can each carry a **weight**
  (percentage of the final grade) or be left unweighted.
- **Two whole-course computation modes**: a course computes its overall grade either as a **weighted average
  of category percentages** (each category contributes its fixed weight regardless of how many points it
  contains) or as a flat **total-points ratio** across every assignment in the course, unweighted by
  category.
- **Per-assignment settings** include points possible, an **"Extra Credit"** flag (a flagged assignment's
  earned points add to the numerator of whatever total it belongs to without adding to the denominator), and
  drop-lowest-style rules that some category configurations support.
- Critically: **none of the above primitives include a user-defined conditional expression that reads one
  category's own computed value (or an auxiliary "completion percentage") and, based on a threshold, *selects
  a different arithmetic operation* to combine categories.** Category weights are fixed configuration, set
  once by a teacher/admin; they are not runtime-computed branches. There is no documented mechanism by which
  "if category A's completion crosses 40%, switch the whole-course formula from an average to a max" can be
  expressed as gradebook configuration.

### 4.3 Verdict

**NOT NATIVELY REPRESENTABLE.**

The completion-gated `max()`/`average()` switch across the WORK and ASSESSMENT aggregates is not something
Schoology's category/weight gradebook model can express as native configuration. Any category-weight
scheme, drop-rule combination, or extra-credit flagging that tried to *reproduce* the same outputs as the
conditional formula for one student's specific numbers would only coincidentally match — and would silently
diverge for every other student whose completion percentage or aggregate values fell in a different region
of the threshold. **This contract deliberately does not attempt such a scheme.** Constructing category
weights or point-possible ratios crafted to *mimic* the conditional switch for a plausible-looking subset of
cases would misrepresent Schoology's actual capability and would violate the honesty task this section
exists to satisfy — it would be presenting invented parity as if it were native support.

**This reasoning alone is sufficient to establish the verdict.** The completion-gated `max()`/`average()`
switch has no native gradebook expression regardless of how any individual aggregate happens to be computed
upstream of it — the verdict does not depend on, and survives unchanged under, any future RC decision about
WORK-aggregate arithmetic (`OPEN-15`, discussed next). Nothing below this point is required to reach
`NOT_NATIVELY_REPRESENTABLE`.

**A secondary illustration, refreshed for the now-decided point-based arithmetic — still NOT a normative
reason for the verdict.** `OPEN-15` and `OPEN-19` were unresolved when v1.0 of this document was written; RC
issued final rulings on both on 2026-07-24 (`grading_policy.v2.json` → `resolved_open_items`). This is not a
relabeling exercise — the numbers below are genuinely recomputed from the fixtures using the now-DECIDED
formulas, replacing v1.0's placeholder-derived pair.

RC's ruling fixes WORK as a points-earned/points-possible ratio (`OPEN-15`):

```
WORK = 100 * (packet_points_earned + participation_points_earned + extra_credit_points_earned)
       / (packet_points_possible + participation_points_possible)
```

and fixes how multiple same-kind items reduce to one scalar (`OPEN-19`) — point-weighted, never an
unweighted average of per-item percentages:

```
component_percentage = 100 * sum(points_earned) / sum(points_possible)
```

Recomputed against `fixtures/schoology/student_0002_above_gate_divergent.json` (two lesson packets, two
participation days, two extra-credit exercises, two quizzes, one topic assessment):

- `work_aggregate = 100 * (190 + 2 + 1.0) / (200 + 2) = 95.544554…` — up from the superseded placeholder's
  `98.0` (that earlier number came from plain scalar addition, not a real points ratio).
- `assessment_aggregate = 100 * (62 + 65 + 66) / (100 + 100 + 100) = 64.333…`.
- Completion (`0.90`) is above the 40% gate, so `a2_expected_quarter_grade = max(95.544554…, 64.333…) =
  95.544554…`.
- Schoology's native flat-ratio figure over the SAME published evidence is **unaffected** by either ruling —
  it was always, and remains, a flat points ratio, never the WORK/ASSESSMENT aggregate arithmetic:
  `100 * 386 / 502 = 76.892430…`.
- The gap (`≈18.65` points) remains large and remains a clear DIVERGENT case — RC's ruling did not make the
  conditional-switch problem disappear; it means the numbers demonstrating it are now real, decided
  arithmetic rather than placeholder arithmetic.

**This illustration exists only to show the reconciliation harness produces sane, real numbers under the
now-decided formulas** — exactly as before, it is not, on its own, load-bearing for the verdict, which rests
solely on the conditional cross-category switch having no native gradebook expression (the "reasoning alone is
sufficient" paragraph above is genuinely independent of this illustration, was true before either ruling, and
remains true after).

### 4.3.1 What genuinely changed for the PER-CATEGORY surfaces (honest re-evaluation)

The whole-course verdict above is unchanged. But the reasoning behind §4.5's per-category rows (WORK category
native percentage, ASSESSMENT category native percentage) **has** genuinely changed, and this document says so
plainly rather than silently carrying forward v1.0's now-inaccurate justification:

- Under v1.0's superseded placeholder, WORK combined a **percentage-scale packet score** with **flat point
  bonuses** by direct addition — an operation with no native Schoology equivalent at all, regardless of
  configuration. The old §4.5 justification ("not the same computation as `compute_work_aggregate`") was
  accurate for that reason.
- Under RC's now-decided formula, WORK is a **points-earned/points-possible ratio**, with extra credit raising
  the numerator only — that is *structurally the same arithmetic* as Schoology's native category math **plus**
  its per-assignment "Extra Credit" flag (both already documented in §4.2). ASSESSMENT, likewise, is now a
  plain point-weighted ratio (`OPEN-19`) — again structurally identical to native category math. The old §4.5
  justification is **no longer accurate** for either row, and this document does not carry it forward
  unexamined — see the revised table in §4.5.
- **Honest preconditions, not overclaiming.** Structural sameness of the arithmetic does not, by itself,
  guarantee the *numbers* match — that additionally requires:
  1. Daily participation days published as **real point-bearing Schoology assignments** inside the WORK
     category (not merely tracked in A2 and summarized) — one assignment per class day per lesson, matching
     `aggregate_participation`'s own per-day accounting exactly.
  2. Extra credit (TI-84, Equation Lab) published **with Schoology's native Extra Credit flag set** — so
     Schoology's own category math excludes it from the denominator exactly the way `compute_work_aggregate`
     does.
  3. The WORK category containing **exactly** the designated evidence A2 counted for that student in that
     period — no more (no pure-paper-practice assignment accidentally placed in WORK, `PREF-02`), no less
     (every packet/participation/extra-credit item A2 designated must actually be published, not a partial
     subset).
  4. The ASSESSMENT category, symmetrically, containing exactly the lesson-quiz and topic-assessment items
     `compute_assessment_aggregate` summed — no more, no less.
- **Does §3's mapping already satisfy these preconditions?** Yes, with no change required. §3's
  `assignment_mapping` table — written before `OPEN-15`/`OPEN-19` were resolved — already publishes
  participation as a real point-bearing per-class-day-per-lesson assignment inside WORK (precondition 1),
  already flags both TI-84 and Equation Lab extra credit with `extra_credit: true` (precondition 2), and
  already keeps WORK/ASSESSMENT category membership in `assignment_mapping` 1:1 with `grading_policy.v2.json`'s
  own WORK/ASSESSMENT component lists (preconditions 3–4, mirrored in `categories.WORK.components` /
  `categories.ASSESSMENT.components` in `schoology_projection.v2.json`). This section's honesty obligation
  does not require inventing a new mapping — it requires *saying plainly* that the existing one happens to
  already satisfy what the new ruling asks for.
- **What this does NOT mean.** Per-category reproducibility is not the same claim as whole-course
  reproducibility. §4.3's verdict concerns the **cross-category** completion-gated `max()`/`average()` switch,
  which still has no native gradebook expression no matter how faithfully either category's own internal
  arithmetic can now be reproduced. Reproducing WORK-alone or ASSESSMENT-alone natively (given the
  preconditions above) says nothing about reproducing the *combination* of the two under a runtime-computed
  conditional — that remains impossible for the same reason it always was (§4.2's last bullet). This contract
  still deliberately does NOT construct a category-weight scheme crafted to mimic the conditional switch.

### 4.4 Smallest safe projection

Given §4.3, the smallest safe projection is:

1. **Publish the granular per-category evidence** exactly as specified in §3 — real assignments, real
   points, real categories — so that Schoology's own display, grade-alert notifications (§6), and per-
   category percentages stay meaningful, reproducible, and useful *as a lens onto the underlying evidence*,
   even though they are not the final word.
2. **Carry A2's authoritatively-computed quarter grade as the published value of record**, via a manual /
   override mechanism rather than Schoology's computed category-weight total (see §4.6 on the mechanism
   itself). This value comes from `grading_policy_ref.compute_quarter_grade` (this tranche's D2 deliverable)
   unchanged — this contract does not re-derive or approximate that formula, it re-publishes its output.
3. **Reconcile every cycle**: compute Schoology's native result from exactly what was published, compare it
   against A2's expected result, and surface any divergence to RC (§8). Divergence is the *expected steady
   state* for many students under this design, not a bug to be engineered away — see §4.5.

### 4.5 Informative vs. authoritative — what nobody should mistake for the official grade

| Schoology surface | Status |
|---|---|
| WORK category native percentage (points-earned/points-possible within that category) | **Informative only, by default — but structurally the SAME points-earned/points-possible ratio `compute_work_aggregate` now uses (`OPEN-15`, RESOLVED — see §4.3.1).** §3's mapping already satisfies the preconditions for exact per-category reproduction; this row's status stays "informative only" because Schoology is never configured to *supply* the official grade from it (§4.6) — only to display it as a lens onto the underlying evidence. |
| ASSESSMENT category native percentage | **Informative only, by default — but structurally the SAME point-weighted ratio `compute_assessment_aggregate` now uses (`OPEN-19`, RESOLVED — see §4.3.1).** Same caveat and same preconditions as WORK. |
| Whole-course native computed grade (whatever Schoology's configured mode produces) | **Informative only, and expected to diverge from the official grade in the general case (§4.3). UNCHANGED by `OPEN-15`/`OPEN-19`** — the cross-category conditional switch has no native expression regardless of either aggregate's own internal arithmetic. Must never be read, displayed to a parent, or exported as "the grade." |
| Manual override / "Official Quarter Grade" column (A2-sourced) | **Authoritative.** This is the number that matches the report card, matches `grading_policy_ref.py`'s output, and is what reconciliation checks against. |

**Assumption to confirm (ASSUMPTION-1):** the capability claims in §4.2 (categories, weights, points-vs-total
modes, the extra-credit flag, the absence of conditional cross-category formulas) reflect Schoology's
gradebook as generally documented and understood. They have **not** been re-verified against a live
Schoology tenant for this contract — no such tenant exists yet (§0). Whoever implements this projection
against a real Schoology course must re-confirm these capability claims against Schoology's then-current,
actual product documentation before relying on them, and must re-run this verdict if Schoology's gradebook
has since added conditional/rule-based grading features this contract is unaware of.

**Assumption to confirm (ASSUMPTION-2):** whether Schoology's actual mechanism for carrying a non-computed
authoritative value is a genuine "override the calculated final grade" feature, or must instead be
implemented as a dedicated manual assignment/column deliberately excluded from both categories' weighting —
is not verifiable offline. §4.6 specifies the *requirement* (a value Schoology does not recompute); which of
these two concrete Schoology mechanisms satisfies it is an implementation detail to confirm once tenant
access exists.

**Assumption to confirm (ASSUMPTION-3):** the SOLE Schoology-native computation mode this contract's
reference simulator (`parity_check.compute_schoology_native_grade`) implements is `flat_total_points` — a
flat points-earned/points-possible ratio across every assignment that was ACTUALLY published (§7), with
extra-credit-flagged assignments contributing to the numerator only, and any assignment carrying Schoology's
"no score entered yet" state excluded entirely from the ratio (never counted as a `0`). That last exclusion
— that an ungraded assignment does not silently drag the ratio down as if it had scored zero — is the
specific, unverified-offline claim: it is generally how LMS gradebooks behave by default, but has **not**
been re-confirmed against a live Schoology tenant. `flat_total_points` is chosen deliberately: it requires no
invented category-weight numbers (§4.3's explicit refusal), unlike a weighted-category mode would. **Any
future Schoology-native computation mode MUST be implemented as a separate, explicitly-named function — never
silently blended into or swapped for this one, and never selected implicitly.** Every reconciliation report
`check_student_parity()` produces names the mode it actually used via its `schoology_computation_mode` field
(`schoology_projection.v2.json` → `schoology_native_computation.mode`), so no run ever compares under an
unstated assumption.

### 4.6 The official-quarter-grade mechanism (requirement, not implementation detail)

Whatever the concrete Schoology feature turns out to be (§4.5, ASSUMPTION-2), it MUST have this property:
**Schoology must not itself compute this value from category weights.** It is written once, by A2, as a
finished number, and Schoology's job is only to display it, alert on its change, and never silently
recompute over it. `schoology_projection.v2.json`'s `official_quarter_grade_projection` block records this
as `"native_category_totals_authoritative": false`.

---

## 5. Deep-link URL contract

`PREF-08` requires stable, lesson-specific deep links for TI-84 exercises; the same requirement is extended
here to every activity type Schoology surfaces (`PREF-05`, `PREF-11`): lesson packet, lesson quiz, TI-84
exercise, Equation Lab exercise.

Two distinct pieces make up a deep link, with two very different stability guarantees:

### 5.1 `a2_activity_key` — durable, A2-owned, stable

```
a2://{course_slug}/{topic}/{lesson_id}/{artifact_type}/{artifact_id}
```

Example (from the synthetic fixtures): `a2://a2-synthetic-algebra2/4-3/4-3/ti84_extra_credit/zeros-ex1`.

- **Never changes** as long as the underlying lesson identity (topic, lesson, artifact type, artifact id)
  doesn't change. It is a pure function of that identity — no database-assigned surrogate id, no timestamp,
  no run-specific value.
- This is the key A2 uses to resolve "which exact Desk activity does this Schoology assignment point at,"
  independent of whatever Schoology-side identifiers get minted or reminted.
- `parity_check.deep_link_for()` computes this deterministically; `test_parity_check.py`'s
  `test_deep_link_is_stable_across_repeated_projection_for_the_same_lesson` and
  `test_deep_link_differs_for_different_lesson_identities` verify stability and uniqueness.

### 5.2 `schoology_url_template` — Schoology-owned, placeholder, may change

```
https://{schoology_domain}/course/{schoology_course_id}/assignment/{schoology_assignment_id}
```

- Every `{...}` token is a **placeholder**. `schoology_domain`, `schoology_course_id`, `schoology_section_id`,
  and `schoology_assignment_id` are Schoology-minted identifiers that **do not exist yet** (§0). This contract
  never fabricates a concrete value for any of them —
  `test_deep_link_schoology_template_never_fabricates_a_real_course_or_assignment_id` asserts the literal
  template tokens are what's returned, not invented IDs.
- **What may change:** the Schoology-side identifiers themselves, if a course/section is recreated, or if an
  assignment is deleted and recreated by a non-idempotent process (which §7 exists to prevent).
- **What must never change:** the *mapping* from an `a2_activity_key` to whichever `schoology_assignment_id`
  currently represents it. That mapping is exactly what the idempotency external key (§7) exists to make
  re-derivable — if a Schoology assignment is ever recreated, the external key lets the projector find and
  reuse the same logical slot rather than losing the link.

---

## 6. Notification usage

Per RC Area 5, Schoology is meant to become the "familiar grade-alert home" and the assignment/notification
surface. This contract's obligation here is narrow and deliberate: **rely on Schoology's own native
notification system; do not build a parallel one.**

- When a projected assignment is created or its points/score change, Schoology's own student/parent
  notification preferences govern whether and how an alert fires. A2 does not attempt to replicate, predict,
  or override that behavior.
- This is precisely why **idempotency (§7) matters for notification hygiene, not just data cleanliness**: a
  non-idempotent projector that deletes-and-recreates an assignment on every run would generate spurious
  "new assignment posted" and "grade removed" notification storms for families, even when nothing
  substantively changed. A projector that only updates-in-place when nothing changed (§7) avoids this.
- The manual "Official Quarter Grade" column (§4.6) is expected to be published/updated on the normal
  grading-period cadence. Re-publishing an unchanged value must be a no-op (§7) so families are not alerted
  to a "grade change" that isn't one.
- Notification content/copy is out of scope here — naming strings are `OPEN-04`.

---

## 7. Idempotency rules

Re-projection must **converge**: running the same projection twice against unchanged source data produces
the identical set of Schoology assignments, never duplicates.

- **Stable external key.** Every projected assignment is identified, across runs, by a deterministic key
  that is a pure function of A2-known values only:

  ```
  external_key = f"a2:{course_id}:{lesson_id}:{artifact_type}:{artifact_id}"
  ```

  No timestamp, no random id, no Schoology-assigned value feeds into this key — that is precisely what makes
  it safe to compute *before* an assignment exists in Schoology, to check "does this already exist," and to
  recompute identically on every future run. `parity_check.external_key()` implements this;
  `test_project_course_is_idempotent_and_produces_no_duplicates` verifies both single-run uniqueness and
  cross-run convergence.

- **Update-vs-create semantics.** For every projected record: look up `external_key` in whatever mapping
  Schoology's real API exposes (or, absent that, an A2-side mapping table — see ASSUMPTION-2 in §4.5 on
  which mechanism Schoology actually offers). If found, **update** the existing assignment/score in place.
  If not found, **create** it once and record the mapping. Never create a second assignment for a key that
  already resolved to one. `parity_check.merge_projection()` simulates exactly this create-or-update
  reduction over repeated projection runs.

- **Convergence, not just non-duplication.** Two consecutive runs over identical input must produce
  byte-identical output records (verified by `run_1 == run_2` in the test suite) — not merely "the same
  count." A projector whose output varies run-to-run for unchanged input (e.g., because it embeds a
  generation timestamp) would still technically avoid duplicates while breaking every downstream assumption
  that depends on stable content.

---

## 8. Divergence handling

Cites `PROGRAM_DOSSIER.md` §15 items 1–3 directly; this section is where those items become operational for
Schoology reconciliation specifically.

- **Every report names the computation mode it used.** `check_student_parity()`'s report carries a
  `schoology_computation_mode` field (currently always `"flat_total_points"` — §4.5, ASSUMPTION-3) so a
  reader never has to assume, guess, or dig through code to know what Schoology-native calculation the
  `schoology_native_quarter_grade` figure in that same report represents. No run compares under an unstated
  mode.
- **Display rounding must never be mistaken for a substantive divergence, and a real divergence must NEVER be
  forgiven — reconciliation is UNDERLYING-ONLY (`OPEN-09`, RESOLVED by RC 2026-07-24; C2 fix, Codex review,
  HIGH, RESOLVED by RC 2026-07-24).** RC's ruling: full precision internally; only the student-facing
  final-grade DISPLAY rounds to one decimal; Schoology keeps native (unrounded) earned/possible totals; A2
  never publishes a rounded display value into Schoology.
  **C2 correction.** v2.0's first implementation of this section misread "must not mistake display rounding
  for substantive divergence" as *permission to forgive* a difference whenever the Schoology-side figure was
  declared display-rounded: `_rounding_only_difference()` rounded BOTH figures and a raw divergence was
  silently converted to `divergent: False`. That reading was wrong — the ruling bans FALSE ALARMS over
  cosmetic rounding; it does not authorize suppressing a genuine underlying difference.
  `_rounding_only_difference()` and its forgiveness branch (`divergent = raw_divergent and not
  rounding_only_difference`) are **DELETED**. Concretely, in `check_student_parity()`:
  - The substantive comparison **always** runs on underlying full-precision values, using the existing
    numeric `tolerance` — this never changes, and rounding never narrows or waives it, on **either**
    comparison basis.
  - The `schoology_value_is_display_rounded` parameter (default `False`) still exists as the explicit,
    machine-readable declaration that the Schoology-side figure being compared is itself already
    display-rounded rather than full precision — the one legitimate case: reconciling against a real,
    already-rounded external figure once a live Schoology tenant exists. It no longer changes whether a
    difference is flagged `divergent`.
  - When that declaration is made, the comparison basis is **degraded**, and the report says so rather than
    pretend: `comparison_basis` is set to a value naming the limitation (vs. `"underlying-full-precision"`
    for the ordinary, undeclared case), and `underlying_convergence_established` is forced to `False` — even
    if the observed numbers happen to match exactly — because a display-rounded observation never proves the
    underlying figures agree.
  - **A genuine divergence is flagged divergent on either basis, always.** Declaring
    `schoology_value_is_display_rounded=True` narrows nothing about the divergence verdict; it only narrows
    what the report may honestly *claim* about convergence.
  - The report carries `comparison_basis` (`str`) and `underlying_convergence_established` (`bool`) fields
    alongside `divergent`, so a reader can never mistake "consistent with the rounded display" for "the
    underlying numbers agree." Neither field is a forgiveness signal, and neither can suppress `divergent`.
  - This is tested in **both directions**:
    `fixtures/schoology/student_0006_display_rounding_only_difference.json` (a genuine `0.03` underlying gap)
    is reported `divergent: True` whether or not `schoology_value_is_display_rounded` is declared — the
    declaration changes `comparison_basis` and `underlying_convergence_established`, **never** `divergent`;
    `fixtures/schoology/student_0001_above_gate_convergent.json` (figures that genuinely agree) reconciles
    `divergent: False`, `underlying_convergence_established: True` on the default full-precision basis, but
    the SAME exact numeric match declared display-rounded still reports
    `underlying_convergence_established: False` — convergence is never asserted from a degraded basis;
    `fixtures/schoology/student_0002_above_gate_divergent.json`'s genuinely large gap remains `divergent: True`
    regardless of the declaration, proving the flag never forgives anything.
- **No fabricated zero (`OPEN-16`, RESOLVED by RC 2026-07-24) — see §3 for the full statement.** The projector
  never fabricates a synthetic zero-scored/zero-points assignment to force a grade into being computable, and
  an all-`UNKNOWN` student (no eligible designated evidence at all) reconciles as `UNKNOWN` on both sides,
  never forced to a number. `fixtures/schoology/student_0005_zero_denominator_no_eligible_evidence.json` is the
  dedicated fixture; per the next bullet, its `UNKNOWN` result is still surfaced to RC, not treated as
  "nothing to reconcile."
- **Surface to RC, never silent, never auto-resolve.** Every reconciliation run produces a structured report
  per student (`parity_check.check_student_parity()`), and every divergent result includes both figures, the
  delta, and an explicit note describing which figure is authoritative. Nothing in this pipeline is permitted
  to pick a winner silently, average the two figures together, or suppress a divergence because it happened
  before. RC is the owner of what happens next with a divergence report; this contract's job stops at
  producing an unambiguous, actionable one.
- **An unavailable/unknown state must never render as zero or erased work** (dossier §15 item 1, item 3).
  Concretely: if A2's authoritative computation is `UNKNOWN` (required evidence not yet available — e.g. an
  ungraded topic assessment), the reconciliation report is **always** flagged divergent, *regardless of
  whether Schoology's native figure happens to look complete*. `fixtures/schoology/
  student_0004_unknown_assessment_evidence.json` demonstrates the specific hazard this guards against:
  Schoology's native total-points ratio, computed by excluding the one ungraded assignment from the ratio
  (ASSUMPTION-3, §4.5 — a common LMS default, but itself unverified against a live tenant), produces a
  perfectly plausible-looking 85.07%. That number must never be read, displayed, or stored as the official
  grade, and the missing evidence itself must never be rendered as a `0`. Both are equally wrong; `UNKNOWN`
  is the only correct state, and it is what A2 publishes and what the reconciliation report states in plain
  language.
- **A malformed catalog record must be visible to RC, not quietly unpublished** (R2 fix). A record that fails
  closed for a routine, expected reason (unreleased, skipped, or optional-catalog not yet explicitly assigned)
  is not an anomaly. A record that fails closed because its `availability` or `explicitly_assigned` field is
  PRESENT but malformed (an unrecognized `availability` value, or a non-boolean `explicitly_assigned` value —
  see §3's fail-closed convention) **is** an anomaly, and `parity_check.detect_projection_anomalies()`
  surfaces it as a structured `{external_key, field, raw_value, reason, projected: false}` record. Any
  RC-facing caller of the projector MUST call and display this list alongside `project_course()`'s output —
  never drop it silently.
- **Fail-open navigation never awards credit** (dossier §15 item 3) has a direct Schoology-side corollary:
  a temporarily-unreachable evidence source may leave a Schoology assignment showing an incomplete or stale
  score, but it must never cause the projector to fabricate a completed/passing score to "fill the gap," and
  (§3) it must never cause an already-projected assignment to be retracted.
- **Unavailability may not relock** (dossier §15 item 2): once a `completed` lesson's assignment has been
  projected with a score, a later evidence-source outage must never cause that assignment or score to be
  removed, zeroed, or hidden in Schoology. `test_temporarily_unavailable_lesson_is_still_projected_never_
  retracted` codifies this at the projection layer.

---

## 9. NO-LIVE-WRITE constraint (normative)

This clause is binding on every artifact in this deliverable and on any future work that builds on it:

1. This contract, `schoology_projection.v2.json`, `parity_check.py`, `test_parity_check.py`, and every file
   under `fixtures/schoology/` **MUST NOT** perform, and as of this version **DO NOT** perform, any network
   call, HTTP request, Schoology REST/GraphQL API call, OAuth handshake, CDP/browser automation step, or any
   other write of any kind against a live Schoology tenant.
2. All "projection" and "parity check" operations described and implemented here operate **exclusively**
   over local, synthetic, invented fixture data. Every course id, section id, student id, and assignment id
   appearing anywhere in this package is fictitious and does not correspond to any real Schoology account,
   course, or student.
3. Real Schoology course/section identifiers **do not exist yet.** Building a live integration against them
   is explicitly **out of scope** for this deliverable and requires separate, later authorization once a
   real Schoology tenant, course, and section exist to integrate against.
4. Any future implementer connecting this contract to a live Schoology API **MUST** first re-verify every
   capability claim marked ASSUMPTION in §4.5 against Schoology's then-current, actual, documented gradebook
   API and behavior — this contract's feasibility verdict (§4.3) is reasoned from a documented capability
   model, not from live testing, and must not be treated as a substitute for that verification.
5. Nothing in this document authorizes, and nothing in `parity_check.py` implements, an actual write path
   into Schoology. The presence of a `schoology_url_template` or an `external_key` scheme is a **design for a
   future write path**, not evidence that one exists.

---

## Changelog — NT16 (v2.0)

Supersedes v1.0 (`schoology_projection.v1.json`, deleted). RC issued final rulings on 2026-07-24 resolving
`OPEN-08/09/10/11/15/16/17/18/19`; this version consumes the four that bear on D3 (`OPEN-09`, `OPEN-15`,
`OPEN-16`, `OPEN-19`) and refreshes reasoning genuinely rather than relabeling it.

- **`OPEN-15` (RESOLVED)** — `parity_check.compute_work_aggregate`'s signature replaced (three-scalar
  addition → `packet_points_earned`/`packet_points_possible`/`participation_points_earned`/
  `participation_points_possible`/`extra_credit_points_earned=0.0`), mirroring `grading_policy_ref.py`'s new
  point-based ratio formula exactly. `_sum_points` now returns an `(earned, possible)` pair instead of a
  single earned scalar.
- **`OPEN-19` (RESOLVED)** — `_average_percentage`'s unweighted-average fixture convention replaced by
  `_points_weighted_percentage`, delegating to the new `compute_assessment_aggregate` (point-weighted:
  `100 * sum(earned) / sum(possible)`). Equal-averaging per-item percentages when possible-points differ is
  now explicitly FORBIDDEN, matching RC's ruling.
- **§4.3 refreshed, not relabeled** — the verdict remains `NOT_NATIVELY_REPRESENTABLE`, sustained
  independently by the cross-category conditional-switch reasoning alone. The secondary illustration is
  recomputed with real point-based numbers (`95.54` vs `76.89`, superseding the placeholder `98.0`-vs-`76.9`
  pair); the stale "Note (OPEN-19)" unweighted-average caveat is deleted. New §4.3.1 honestly documents what
  changed for the per-category surfaces: WORK and ASSESSMENT are now structurally the same arithmetic as
  Schoology's native category math, subject to four preconditions §3's existing mapping already satisfies.
  §4.5's WORK/ASSESSMENT rows updated accordingly; the whole-course row's status is explicitly unchanged.
- **`OPEN-09` (RESOLVED)** — new §3 zero-denominator subsection is unrelated to this item (see next bullet);
  the rounding-awareness ruling instead lands in §8: `check_student_parity()` gains a
  `schoology_value_is_display_rounded` parameter (default `False`) and a `rounding_only_difference` report
  field. A difference is treated as non-substantive ONLY when explicitly declared display-rounded AND
  attributable purely to 1-decimal rounding — never inferred silently, and never blanket-forgiving a genuine
  divergence. New fixture: `fixtures/schoology/student_0006_display_rounding_only_difference.json`, tested in
  both directions.
- **`OPEN-16` (RESOLVED)** — new §3 subsection: the projector must never fabricate a synthetic zero-scored/
  zero-points assignment to force a grade into being computable; an all-`UNKNOWN` student reconciles as
  `UNKNOWN` on both sides, never forced to a number. New fixture:
  `fixtures/schoology/student_0005_zero_denominator_no_eligible_evidence.json`. New machine-readable
  `zero_denominator_rule` block in `schoology_projection.v2.json`.
- Every `grading_policy.v1.json` / `schoology_projection.v1.json` reference updated to the `.v2.json`
  filenames; `grading_policy.v1.json` and `schoology_projection.v1.json` are both deleted, superseded by their
  v2.0 successors.
- `open_item_ids` reduced to `["OPEN-04"]` (still genuinely open — naming strings, unaffected by this
  tranche); `resolved_open_item_ids` added listing all seven NT16-resolved items relevant to this package,
  each retaining its id with resolution provenance (`RESOLVED by RC 2026-07-24`) rather than being deleted.
- **C2 fix (Codex review, HIGH, RESOLVED by RC 2026-07-24)** — corrected a mid-tranche defect within this same
  v2.0 package: `parity_check._rounding_only_difference()` and its forgiveness branch
  (`divergent = raw_divergent and not rounding_only_difference`) in `check_student_parity()` are **DELETED**.
  `schoology_value_is_display_rounded=True` no longer converts a raw divergence into `divergent: False`;
  reconciliation is now UNDERLYING-ONLY on either comparison basis. The `rounding_only_difference` report
  field (a forgiveness signal) is removed and replaced by `comparison_basis` (`str`) and
  `underlying_convergence_established` (`bool`) — see §8 above and `schoology_projection.v2.json`'s
  `rounding_awareness` / `divergence_handling.report_fields` blocks. `underlying_convergence_established` is
  never `True` on a declared display-rounded basis, even when the observed figures happen to match exactly.
  Full before/after test coverage: `test_parity_check.py`'s rounding-only-difference test group.
