# RC Teacher Preference Record

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

## Provenance

This record is derived from two sources, both dated 2026-07-24:

1. The Grok preference interview conducted with RC, and
2. RC's direct clarifications on that interview's output.

The substance recorded below is RC's — every decision, every negative constraint, every open question
originates from her interview answers and clarifications, not from this document's author. This document's
only contributions are: organizing that substance into the fourteen canonical `PREF-NN` areas, decomposing
each area into atomic, individually checkable `PREF-NN.M` sub-decisions, assigning the canonical `OPEN-NN`
tokens to items RC's text left unsettled, and cross-referencing already-closed decisions (content-readiness,
DOK, alias resolution, the dossier §15 reliability addendum) so they are cited rather than re-derived. This
record does not design, recommend, or extrapolate beyond what RC's text states. Where RC's phrasing is
compressed into a table cell, the operative constraint — especially a negative one ("never," "not," "only,"
"absent until," "must not") — is preserved in force, not softened into a positive-sounding preference.

## How to read this record

- **Status `DECIDED`** — RC settled this. It is binding on every downstream deliverable (D2–D8) unless a
  later, dated RC decision explicitly supersedes it.
- **Status `OPEN`** — RC's interview text and clarifications do not settle this point. The sub-decision cell
  carries the bare token `OPEN-NN` from §4 of the NT15 shared brief. Each `OPEN-NN` has exactly one heading in
  `OPEN_DECISIONS_REGISTER.md`; RC is the owner of every open item. Downstream deliverables must not guess a
  value for an OPEN item — they must implement around its absence (see PREF-06 / dossier §15: absence of a
  value is `UNKNOWN`, never a silently-picked default).
- **Status `DEFERRED`** — RC explicitly decided **not** to build this now. This is not the same as OPEN: no
  decision is pending, it is postponed by RC's own choice. Deferred items are recorded here for completeness
  but are **not** entered in the open-items register.
- **Sub-id convention `PREF-NN.M`** — `NN` is the fixed two-digit canonical area number from the tranche
  brief (`PREF-01` … `PREF-14`; never renumbered, never reordered). `M` is a 1-based index assigned in the
  order the corresponding commitment appears in RC's text for that area. `M` is stable within this document
  version — a future clarification that adds a sub-decision to an area appends the next `M` rather than
  renumbering existing rows.

---

## PREF-01 — Desk navigation & release model

| ID | Decision | Status |
|---|---|---|
| PREF-01.1 | Lesson-state vocabulary for the Desk navigation model — seven states, spelled exactly this way. Five are RC's own Area 1 navigation-state names: `today`, `released`, `unreleased`, `skipped`, `optional-catalog`. The remaining two are NT15 operational additions, not RC decisions: `completed`, `temporarily-unavailable`. | DECIDED |
| PREF-01.2 | Today's assignment is the Desk's primary front door (the default landing view). | DECIDED |
| PREF-01.3 | "What's next" is a secondary view — not the front door. | DECIDED |
| PREF-01.4 | Students may open any teacher-released (`released`) lesson. | DECIDED |
| PREF-01.5 | Students may work ahead of today's assignment, but **only** within released material — never `unreleased` material. | DECIDED |
| PREF-01.6 | The primary view shows today plus nearby/recently released lessons first. | DECIDED |
| PREF-01.7 | The broader released roadmap lives behind a secondary/expandable view, not on the primary view. | DECIDED |
| PREF-01.8 | Unreleased (`unreleased`) lessons are hidden/unavailable to students. | DECIDED |
| PREF-01.9 | Skipped (`skipped`) lessons render grey/inert, and appear **only** in the broader view — never on the primary view. | DECIDED |
| PREF-01.10 | Optional-catalog (`optional-catalog`) content is absent from the normal navigation path until a teacher explicitly assigns it. | DECIDED |
| PREF-01.11 | Skip-transition legality, promoted to normative with teacher authority (NT16, resolves OPEN-18): `unreleased`→`skipped` ALLOWED (confirms the already-legal T3 — it was never one of the provisional four); `released`→`skipped` ALLOWED (T7 promoted); `today`→`skipped` ALLOWED BEFORE COMPLETION (T11 promoted, pre-completion condition encoded); `skipped`→`released` ALLOWED (T12 promoted); `skipped`→`today` ALLOWED (T13 promoted); `completed`→`skipped` FORBIDDEN (confirms the already-illegal X3). Students CANNOT initiate skip/unskip — every skip transition is teacher-only, consistent with PREF-13.2's teacher-designation authority. The `transitions.provisional` bucket is retired/emptied with provenance. — RESOLVED by RC 2026-07-24 | DECIDED |

PREF-01.1's five RC-named states (`today`, `released`, `unreleased`, `skipped`, `optional-catalog`) are the
ones used throughout PREF-01.2–PREF-01.10 above — that is the RC-sourced substance of this area. The row's
other two states are **NT15 operational elaboration, not an RC Area-1 decision**: `completed` (a lesson whose
teacher-designated work is finished; see PREF-03's completion-percentage mechanic) and
`temporarily-unavailable` (evidence-source unreachable; see PREF-06 / dossier §15 items 1–2, "unknown ≠ zero"
and "unavailability may not relock") were added only so D4 DESK_STATE_MODEL has one fixed, complete
seven-member target vocabulary to check against. `DECIDED` on PREF-01.1 certifies that this vocabulary is
now fixed for the package — it does not certify that RC personally named all seven states; the row's own
text already draws that line, and no reader should attribute the two-state addition to RC.

## PREF-02 — Classroom modality (paper-first + digital capture)

| ID | Decision | Status |
|---|---|---|
| PREF-02.1 | Classroom modality is paper-first: packet/practice materials are projected as PDFs. | DECIDED |
| PREF-02.2 | Mathematical thinking and work happen on paper. | DECIDED |
| PREF-02.3 | Only teacher-designated answers are entered digitally — not the full worked solution. | DECIDED |
| PREF-02.4 | Digital capture of those designated answers tolerates mathematically equivalent forms (not exact-string match). | DECIDED |
| PREF-02.5 | Pure paper practice (not teacher-designated for digital capture) is **not** graded and **not** individually tracked. | DECIDED |

## PREF-03 — Grade composition & quarter rule

| ID | Decision | Status |
|---|---|---|
| PREF-03.1 | There are exactly two principal grade aggregates: WORK and ASSESSMENT. | DECIDED |
| PREF-03.2 | WORK aggregate = teacher-designated digital packet work + daily participation evidence + designated extra credit. | DECIDED |
| PREF-03.3 | ASSESSMENT aggregate = lesson quizzes + topic assessments. | DECIDED |
| PREF-03.4 | Completion percentage is computed from teacher-designated digital work (not all packet content). | DECIDED |
| PREF-03.5 | Quarter rule, upper branch: if `completion >= 0.40` (inclusive — "≥ 40%") then `quarter_grade = max(work_aggregate, assessment_aggregate)`. | DECIDED |
| PREF-03.6 | Quarter rule, lower branch: if `completion < 0.40` then `quarter_grade = average(work_aggregate, assessment_aggregate)` (arithmetic mean of the two aggregates). | DECIDED |
| PREF-03.7 | Teacher override of the computed quarter grade is preserved — the formula's output is not final/unoverridable. | DECIDED |
| PREF-03.8 | The grading policy (this formula and its constants) is versioned — future changes are tracked as a new version, not a silent mutation of this one. | DECIDED |
| PREF-03.9 | Clients (Desk, Schoology, or any other consumer) **never** determine designation (what counts as teacher-designated) or official credit — that authority is server-side/A2 only. | DECIDED |
| PREF-03.10 | Rounding rule for the completion percentage itself: compare the EXACT completion ratio against the inclusive 0.40 threshold; no pre-rounding before branch selection (resolves OPEN-08) — RESOLVED by RC 2026-07-24. | DECIDED |
| PREF-03.11 | Rounding rule for the WORK/ASSESSMENT aggregate scores and the published quarter grade: full precision is kept internally; only the student-facing final-grade display is rounded, to one decimal; Schoology keeps native earned/possible totals; reconciliation compares underlying values consistently and must not mistake display rounding for substantive divergence (resolves OPEN-09) — RESOLVED by RC 2026-07-24. | DECIDED |
| PREF-03.12 | WORK-aggregate combination, point-based (NT16, resolves OPEN-15): `WORK = 100 × (packet_points_earned + participation_points_earned + extra_credit_points_earned) / (packet_points_possible + participation_points_possible)`. Only teacher-designated official evidence enters; extra credit raises earned but NOT possible; WORK may exceed 100; a zero denominator falls to PREF-03.13's UNKNOWN rule; a percentage must NEVER be added directly to raw flat points. This SUPERSEDES the provisional three-scalar plain addition. — RESOLVED by RC 2026-07-24 | DECIDED |
| PREF-03.13 | Zero-denominator semantics (NT16, resolves OPEN-16): when there is no eligible designated work/participation, completion, WORK, and quarter grade are all UNKNOWN — never zero. Student-facing display is a dash / "not enough evidence"; the Schoology projection must NOT fabricate a zero-valued assignment to force a grade. — RESOLVED by RC 2026-07-24 | DECIDED |
| PREF-03.14 | Reduction of multiple same-kind items to a single aggregate scalar, point-weighted within each component, not an equal average (NT16, resolves OPEN-19): `component_percentage = 100 × Σ(current_official_points_earned) / Σ(points_possible)` for packet assignments, lesson quizzes, topic assessments, or any same-kind designated group, using each item's CURRENT OFFICIAL server-designated score (attempt-selection/overrides are governed by their own rules); equal-average of assignment percentages is NEVER used when possible-points differ. `ASSESSMENT = 100 × total_assessment_points_earned / total_assessment_points_possible` (quizzes + topic assessments on actual point scales). — RESOLVED by RC 2026-07-24 | DECIDED |

The completion threshold is inclusive at exactly `0.40`: a student at precisely 40% completion takes the
max-branch, not the average-branch. "Completion" here is scoped to teacher-designated digital work only
(PREF-03.4) — it is not a raw count of all packet items, digital or paper. The two rounding questions
(PREF-03.10, PREF-03.11) are now **RESOLVED by RC 2026-07-24** (NT16): the completion ratio is compared
against the 0.40 threshold at full precision with no pre-rounding (PREF-03.10), while only the student-facing
final-grade display is rounded, to one decimal, with Schoology retaining native point totals and
reconciliation operating on underlying values (PREF-03.11). Both resolutions are independent of the
threshold's inclusivity, which RC's text settled explicitly from the outset. PREF-03.12 through .14 record
three further NT16 rulings that had no prior PREF row: the point-based WORK formula (resolves OPEN-15), the
zero-denominator UNKNOWN rule (resolves OPEN-16), and the point-weighted same-kind reduction plus ASSESSMENT
formula (resolves OPEN-19). See "NT16 rulings — 2026-07-24" below for all nine rulings recorded together.

## PREF-04 — Participation & extra credit

| ID | Decision | Status |
|---|---|---|
| PREF-04.1 | ≥1 valid digital packet response on a class day earns `1.0` participation point for that day. | DECIDED |
| PREF-04.2 | Zero valid digital packet responses on a class day earns `0.0` participation points for that day. | DECIDED |
| PREF-04.3 | An assigned TI-84 exercise completed successfully earns `+0.5` participation points as extra credit. | DECIDED |
| PREF-04.4 | An assigned Equation Lab exercise completed successfully likewise earns `+0.5` participation points as extra credit. | DECIDED |
| PREF-04.5 | Participation points and both extra-credit mechanisms belong to the WORK aggregate — never ASSESSMENT. | DECIDED |
| PREF-04.6 | "Tracked" activity is **not** automatically equal to main-grade credit — server policy plus teacher designation are authoritative over whether tracked evidence becomes credited. | DECIDED |
| PREF-04.7 | Daily cap on total extra-credit participation points: +1.0 point per student per class day, applying to currently-authorized extra credit (TI-84 +0.5, Equation Lab +0.5, stacking allowed); any FUTURE extra-credit source requires a new policy decision and must never silently exceed the cap (resolves OPEN-10) — RESOLVED by RC 2026-07-24. | DECIDED |
| PREF-04.8 | Participation credit on partial-attendance or non-class days: non-class days are excluded from the participation requirement; partial/absent/uncertain attendance is NEVER auto-zeroed — such days are excused/unknown unless RC explicitly designates the day participation-eligible; UNKNOWN is distinct from zero (resolves OPEN-11) — RESOLVED by RC 2026-07-24. | DECIDED |

PREF-04.5 is the constant referenced elsewhere in this package as "aggregate carrying participation + extra
credit = WORK": nothing in this area ever flows into the ASSESSMENT aggregate. The extra-credit cap and
attendance questions (PREF-04.7, PREF-04.8) are now **RESOLVED by RC 2026-07-24** (NT16): a +1.0
point-per-student-per-class-day cap applies to currently-authorized extra credit (TI-84 +0.5, Equation Lab
+0.5, stacking allowed), with any future extra-credit source requiring a new policy decision rather than
silently exceeding the cap (PREF-04.7); and non-class days are excluded from the participation requirement
while partial/absent/uncertain attendance is never auto-zeroed — such days are excused/unknown unless RC
explicitly designates the day participation-eligible, with UNKNOWN kept distinct from zero (PREF-04.8).

## PREF-05 — Schoology role & reconciliation

| ID | Decision | Status |
|---|---|---|
| PREF-05.1 | Schoology is explicitly **not** a passive mirror of Desk. | DECIDED |
| PREF-05.2 | Schoology is (eventually) the primary school-facing assignment/notification surface. | DECIDED |
| PREF-05.3 | Schoology is the familiar grade-alert home. | DECIDED |
| PREF-05.4 | Schoology provides the school-facing gradebook display. | DECIDED |
| PREF-05.5 | Schoology provides a deep-link surface into exact Desk lesson/quiz/TI-84/Equation-Lab activities. | DECIDED |
| PREF-05.6 | Schoology also functions as an independent calculator of the published grade, to the extent its category/weight gradebook model can faithfully express RC's policy (qualified, not unconditional, independence). | DECIDED |
| PREF-05.7 | A2 — not Schoology — remains responsible for durable evidence, item identity, teacher designation, policy versioning, and receipts/audit. | DECIDED |
| PREF-05.8 | A2 computes the expected grade independently of whatever Schoology computes. | DECIDED |
| PREF-05.9 | Required principle "one policy, two calculations, explicit reconciliation": A2 must publish sufficiently granular assignments/categories/points/grades for Schoology to be able to reproduce the intended result. | DECIDED |
| PREF-05.10 | A2 compares Schoology's computed result against A2's own expected result. | DECIDED |
| PREF-05.11 | Divergence between the two calculations is surfaced to RC — never silently absorbed. | DECIDED |
| PREF-05.12 | The system must **never** silently accept two conflicting official grade totals. | DECIDED |
| PREF-05.13 | Schoology must **not** retroactively decide which raw evidence qualifies for credit — that authority stays with A2/teacher designation, not with whatever Schoology's gradebook happens to compute. | DECIDED |
| PREF-05.14 | RC requires an honesty analysis, as a condition of the projection design: determine whether the 40%-conditional max/average formula (PREF-03.5/.6) is natively representable in Schoology's documented category/weight gradebook model (categories, weights, points — no conditional cross-category formulas); if it is not natively representable, specify the smallest safe projection approach without pretending native parity exists. The finding itself is carried by D3 SCHOOLOGY_PROJECTION_CONTRACT, not by this record. | DECIDED |

**Reconciling annotation (NT15, not RC's words):** PREF-05.9's phrase "reproduce the intended result" is RC's
own verbatim Area 5 wording, recorded above exactly as she said it and not reworded here. It is not in tension
with D3's native-feasibility finding (`SCHOOLOGY_PROJECTION_CONTRACT.md` §4, NATIVE-FEASIBILITY VERDICT:
NOT_NATIVELY_REPRESENTABLE) — RC's same Area 5 text also mandated the honesty task recorded at PREF-05.14,
precisely so a native-representability gap would be resolved openly rather than concealed by softening
PREF-05.9's wording. D3's verdict answers *how* RC's intent in PREF-05.9 is satisfied, not *whether* it is:
Schoology reproduces the informative per-category calculation over the granular evidence A2 publishes (the
publish obligation PREF-05.9 states), while the official completion-gated conditional grade (PREF-03.5/.6)
arrives via the A2-computed override column and is reconciled against Schoology's figure per
PREF-05.10–.13. This annotation explains the resolution; it does not alter PREF-05.9's decision text, which
remains RC's words.

The exact strings Schoology will display for assignments/categories are unresolved (OPEN-04; recorded fully
under PREF-11, since it is a naming question, but it applies to this area's projection surface too). PREF-05.9
through .13 are the operational content of "one policy, two calculations, explicit reconciliation" — they
obligate A2 to publish, compare, and surface divergence, and they forbid Schoology from becoming a second,
independent source of credit-granting truth.

## PREF-06 — Attempts, recovery & reliability

| ID | Decision | Status |
|---|---|---|
| PREF-06.1 | Unlimited attempts on student work — no attempt cap. | DECIDED |
| PREF-06.2 | Workflow order: feedback is given after submission, followed by correction/resubmission. | DECIDED |
| PREF-06.3 | Late work is accepted. | DECIDED |
| PREF-06.4 | Retakes are allowed within the quarter. | DECIDED |
| PREF-06.5 | Teacher overrides are preserved/available. | DECIDED |
| PREF-06.6 | An unknown/unavailable grade state must **never** render as zero. | DECIDED |
| PREF-06.7 | An unknown/unavailable grade state must **never** render as erased work. | DECIDED |
| PREF-06.8 | An unknown/unavailable grade state must **never** render as fabricated credit. | DECIDED |
| PREF-06.9 | An unknown/unavailable grade state must **never** cause erroneous relocking. | DECIDED |
| PREF-06.10 | `completed` is TERMINAL at the Desk-tile layer — zero legal exits, now DECIDED rather than open (NT16, resolves OPEN-17). A retake is an ORTHOGONAL activity/affordance attached to the completed lesson: it never demotes completion, relocks the tile, erases history, or alters the grading engine via navigation state. Implementation details of the retake affordance are deferred to the relevant work packages. — RESOLVED by RC 2026-07-24 | DECIDED |

PREF-06.6 through .9 restate, for the grading/attempts surface specifically, the reliability addendum RC
directed at `PROGRAM_DOSSIER.md` §15 (items 1 "Unknown ≠ zero" and 2 "Unavailability may not relock" in
particular). This record cites that addendum; it does not re-derive or reopen it.

## PREF-07 — Answer evaluation authority

| ID | Decision | Status |
|---|---|---|
| PREF-07.1 | Official-answer equivalence checking must be deterministic symbolic/numeric equivalence where supported (example given: `x + y ≡ y + x`). | DECIDED |
| PREF-07.2 | Where equivalence support does not exist, or the form is disputed, there is a teacher review/override path. | DECIDED |
| PREF-07.3 | AI may explain (e.g., why an answer is or is not correct) — a permitted, supporting role. | DECIDED |
| PREF-07.4 | AI **never**, alone, decides official correctness. | DECIDED |
| PREF-07.5 | AI **never**, alone, decides grade credit. | DECIDED |
| PREF-07.6 | Default numeric-equivalence tolerance values are unresolved (OPEN-12). | OPEN |
| PREF-07.7 | The specific CAS/symbolic-equivalence engine to use is unresolved (OPEN-13). | OPEN |

PREF-07.4 and PREF-07.5 are independent negative constraints — "never decides correctness" and "never decides
credit" are not the same claim (a system could in principle judge mathematical correctness without that
judgment automatically becoming grade credit); both are recorded so neither is lost.

## PREF-08 — TI-84 trainer scope

| ID | Decision | Status |
|---|---|---|
| PREF-08.1 | Required skill: graphing/window selection. | DECIDED |
| PREF-08.2 | Required skill: tables. | DECIDED |
| PREF-08.3 | Required skill: zeros/intersections/extrema. | DECIDED |
| PREF-08.4 | Required skill: sequences. | DECIDED |
| PREF-08.5 | Required skill: solver. | DECIDED |
| PREF-08.6 | Whether matrices are a required skill is undecided (OPEN-01). | OPEN |
| PREF-08.7 | Regression is explicitly omitted from required skills. | DECIDED |
| PREF-08.8 | Curriculum may require these skills as content while individual TI-84 trainer exercises remain designated as extra credit (curricular requirement is distinct from grading designation). | DECIDED |
| PREF-08.9 | TI-84 trainer exercise URLs must support stable, lesson-specific deep links. | DECIDED |

## PREF-09 — Equation Lab scope

| ID | Decision | Status |
|---|---|---|
| PREF-09.1 | Initial scope, narrow: polynomial identities. | DECIDED |
| PREF-09.2 | Initial scope, narrow: quadratic equations. | DECIDED |
| PREF-09.3 | Primary interaction mode is answer/simplified-form entry — not full derivation entry. | DECIDED |
| PREF-09.4 | Unlimited retries. | DECIDED |
| PREF-09.5 | Immediate feedback. | DECIDED |
| PREF-09.6 | Step-by-step enforcement is deferred — RC decided not to build it now. | DEFERRED |
| PREF-09.7 | Equation Lab's role is reinforcement/extra-credit, **not** main assessment. | DECIDED |
| PREF-09.8 | Choice of AI provider for Equation Lab is unresolved (OPEN-02). | OPEN |

## PREF-10 — Desk personality & reward economy

| ID | Decision | Status |
|---|---|---|
| PREF-10.1 | Keep the retro System-7 personality/UI theme. | DECIDED |
| PREF-10.2 | Keep the completion calendar. | DECIDED |
| PREF-10.3 | Keep streaks. | DECIDED |
| PREF-10.4 | Keep the candy/per-question economy. | DECIDED |
| PREF-10.5 | Do not build gifting. | DEFERRED |
| PREF-10.6 | Do not build Tetris (mini-game). | DEFERRED |
| PREF-10.7 | Do not build leaderboards. | DEFERRED |
| PREF-10.8 | Do not build celebration noise. | DEFERRED |
| PREF-10.9 | The candy/reward economy need not block the first academic release. | DECIDED |
| PREF-10.10 | Candy is to be phased in shortly after the first academic release. | DECIDED |
| PREF-10.11 | Reward seams must be preserved in the academic-release architecture so the later candy implementation needs no rework. | DECIDED |
| PREF-10.12 | The exact timing detail for candy/reward activation is unresolved (OPEN-14). | OPEN |

PREF-10.5 through .8 are RC's explicit "do not build" list — each is independently checkable (a build that
adds any one of these regresses this record even if the other three are respected). PREF-10.9 through .11
obligate the academic-first implementation to leave hooks/seams for candy, even though candy itself ships
later — this is a sequencing decision, not a design instruction for what those seams look like.

## PREF-11 — Organization & surfaces

| ID | Decision | Status |
|---|---|---|
| PREF-11.1 | Desk is the primary learning interface. | DECIDED |
| PREF-11.2 | Schoology is the primary distribution/notification/deep-link/school-facing-gradebook surface. | DECIDED |
| PREF-11.3 | Projections are organized by topic and lesson. | DECIDED |
| PREF-11.4 | DOK is teacher-primary. | DECIDED |
| PREF-11.5 | DOK is **not** emphasized to students. | DECIDED |
| PREF-11.6 | Automate Schoology maintenance where possible. | DECIDED |
| PREF-11.7 | Desk/product naming strings are unresolved (OPEN-03). | OPEN |
| PREF-11.8 | Schoology assignment and category naming strings are unresolved (OPEN-04). | OPEN |

## PREF-12 — ELL & accessibility

| ID | Decision | Status |
|---|---|---|
| PREF-12.1 | Vocabulary support is required. | DECIDED |
| PREF-12.2 | Worked examples are required. | DECIDED |
| PREF-12.3 | Simpler-language explanations are required, while preserving mathematical demand — simplification must not reduce rigor. | DECIDED |
| PREF-12.4 | Platform is Chromebook-first. | DECIDED |
| PREF-12.5 | Platform is mobile-adaptive (secondary to Chromebook-first). | DECIDED |
| PREF-12.6 | Tolerance for flaky connectivity is required. | DECIDED |
| PREF-12.7 | Paper-first continuation is required as a fallback under connectivity issues. | DECIDED |
| PREF-12.8 | Audio support for ELL is unresolved (OPEN-05). | OPEN |
| PREF-12.9 | Bilingual support scope is unresolved (OPEN-06). | OPEN |
| PREF-12.10 | The exact AI integration for ELL explanations is unresolved (OPEN-07). | OPEN |

PREF-12.3's "preserving mathematical demand" is a negative constraint in substance even though phrased
positively in RC's text: language simplification is authorized, but a reduction in mathematical rigor/demand
is not — the two must not be conflated when this is implemented.

## PREF-13 — Pacing

| ID | Decision | Status |
|---|---|---|
| PREF-13.1 | Lessons commonly span 2–3 periods. | DECIDED |
| PREF-13.2 | RC (the teacher) designates today's/next lesson — there is no fixed calendar driving sequencing. | DECIDED |
| PREF-13.3 | "~1 topic/quarter" is explicitly a temporary planning assumption, not a permanent rule. | DECIDED |
| PREF-13.4 | Do not hard-code four topics. | DECIDED |
| PREF-13.5 | Do not hard-code a fixed annual pace. | DECIDED |
| PREF-13.6 | Intervention/makeup/enrichment subsystems are deferred — RC decided not to build them now. | DEFERRED |

## PREF-14 — Content boundaries

| ID | Decision | Status |
|---|---|---|
| PREF-14.1 | Lesson 4-1 stays optional-catalog. | DECIDED |
| PREF-14.2 | Lesson 4-1 is never auto-scheduled. | DECIDED |
| PREF-14.3 | Application/product development may proceed before complete quiz/content ingestion — development is not blocked on full content. | DECIDED |
| PREF-14.4 | Existing content-readiness decisions remain authoritative. | DECIDED |
| PREF-14.5 | Existing DOK decisions remain authoritative. | DECIDED |
| PREF-14.6 | Existing verified-item decisions remain authoritative. | DECIDED |
| PREF-14.7 | Existing alias-resolution decisions remain authoritative. | DECIDED |

PREF-14.1 and .2 reaffirm — they do not reopen — Lesson 4-1's `optional-catalog` status from NT14 (see
Cross-references below). PREF-14.4 through .7 are named here individually because each is a separately closed
decision domain (content-readiness pipeline, DOK verification, verified-item registry, alias/merge
resolution); this record cites all four as authoritative and closed without restating their content.

---

## NT16 rulings — 2026-07-24

RC issued nine rulings on 2026-07-24 that resolve nine previously-`OPEN` register items in
`OPEN_DECISIONS_REGISTER.md`. This subsection collects all nine together, in RC's substance, so a reader can
see the full NT16 event in one place; each ruling is also recorded at its governing `PREF-NN.M` row above (four
existing rows flipped from `OPEN` to `DECIDED` — PREF-03.10, PREF-03.11, PREF-04.7, PREF-04.8 — and five new
`DECIDED` rows added at the next available `M` index in their area — PREF-03.12, PREF-03.13, PREF-03.14,
PREF-06.10, PREF-01.11). These rulings are the "later, dated RC decision" contemplated by "How to read this
record" above: each supersedes the `OPEN` status the corresponding row carried in v1.0. As with the rest of
this record, the substance below is RC's; nothing here is invented beyond what she stated.

**OPEN-08 (completion rounding) → PREF-03.10.** Compare the EXACT completion ratio against the inclusive 0.40
threshold; no pre-rounding before branch selection. RESOLVED by RC 2026-07-24.

**OPEN-09 (grade rounding) → PREF-03.11.** Full precision internally; round ONLY the student-facing
final-grade display to one decimal; Schoology keeps native earned/possible totals; reconciliation compares
underlying values consistently and must not mistake display rounding for substantive divergence. RESOLVED by
RC 2026-07-24.

**OPEN-10 (extra-credit cap) → PREF-04.7.** +1.0 point per student per class day cap for
currently-authorized extra credit (TI-84 +0.5, Equation Lab +0.5, stacking allowed); any FUTURE extra-credit
source requires a new policy decision — never silently exceeds the cap. RESOLVED by RC 2026-07-24.

**OPEN-11 (partial attendance / non-class days) → PREF-04.8.** Non-class days excluded from the
participation requirement; partial/absent/uncertain attendance NEVER auto-zero — such days are excused/unknown
unless RC explicitly designates the day participation-eligible; UNKNOWN distinct from zero. RESOLVED by RC
2026-07-24.

**OPEN-15 (WORK aggregation, point-based) → PREF-03.12.** `WORK = 100 × (packet_points_earned +
participation_points_earned + extra_credit_points_earned) / (packet_points_possible +
participation_points_possible)`. Only teacher-designated official evidence enters. Extra credit raises earned
but NOT possible. WORK may exceed 100. Zero denominator falls to OPEN-16's rule. NEVER add a percentage
directly to raw flat points. This SUPERSEDES the provisional three-scalar plain addition. RESOLVED by RC
2026-07-24.

**OPEN-16 (zero denominator) → PREF-03.13.** No eligible designated work/participation ⇒ completion UNKNOWN,
WORK UNKNOWN, quarter grade UNKNOWN; student-facing display = dash / "not enough evidence", never zero; the
Schoology projection must NOT fabricate a zero-valued assignment to force a grade. RESOLVED by RC 2026-07-24.

**OPEN-17 (retakes) → PREF-06.10.** `completed` remains TERMINAL for the lesson tile; a retake is an
ORTHOGONAL activity/affordance attached to the completed lesson — never demotes completion, relocks, erases
history, or alters the grading engine via navigation state. `completed` keeps zero legal exits — now DECIDED,
not open. The retake-affordance concept is documented as orthogonal; implementation details deferred to the
work packages. RESOLVED by RC 2026-07-24.

**OPEN-18 (skip transitions, promoted to normative) → PREF-01.11.** `unreleased`→`skipped` ALLOWED (confirms
the already-legal T3 — it was never one of the provisional four); `released`→`skipped` ALLOWED (T7 promoted);
`today`→`skipped` ALLOWED BEFORE COMPLETION (T11 promoted, pre-completion condition encoded);
`skipped`→`released` ALLOWED (T12 promoted); `skipped`→`today` ALLOWED (T13 promoted); `completed`→`skipped`
FORBIDDEN (confirms the already-illegal X3); students CANNOT initiate skip/unskip (teacher-only actor on every
skip transition). The `transitions.provisional` bucket is retired/emptied with provenance. RESOLVED by RC
2026-07-24.

**OPEN-19 (multi-item reduction, point-weighted) → PREF-03.14.** `component_percentage = 100 ×
Σ(current_official_points_earned) / Σ(points_possible)` for packet assignments, lesson quizzes, topic
assessments, any same-kind designated group; each item's CURRENT OFFICIAL server-designated score;
attempt-selection/overrides governed by their own rules; NEVER equal-average assignment percentages when
possible-points differ. `ASSESSMENT = 100 × total_assessment_points_earned / total_assessment_points_possible`
(quizzes + topic assessments on actual point scales). RESOLVED by RC 2026-07-24.

**Interim rule for OPEN-12 / OPEN-13 (NT16 annotation, not RC's words, and NOT a resolution of either item):**
RC also stated an interim operating rule that governs answer-evaluation behavior while OPEN-12 (numeric-
equivalence tolerance defaults) and OPEN-13 (CAS/symbolic-equivalence engine choice) remain `OPEN` and owned by
RC: clearly-deterministic cases may be accepted; unsupported symbolic/tolerance cases route to teacher review,
never auto-fail. This is recorded here as an operating rule for implementers. It does **not** close either
PREF-07.6 or PREF-07.7 — both remain `OPEN` in the PREF-07 table above, and both remain open items in
`OPEN_DECISIONS_REGISTER.md`.

The ten items RC did not rule on remain `OPEN` and unchanged by this section: OPEN-01 through OPEN-07,
OPEN-12, OPEN-13, and OPEN-14.

---

## Cross-references

- **NT14 optional-catalog semantics** (record `nt14-ingest-4-1-2026-07-23`): registry rows carry a top-level
  `"availability": "optional-catalog"` marker. `qb.select()` drops these rows by default; the explicit
  keyword-only `include_optional=True` opts in. `qb.get()` / `qb.get_for_packet()` are unchanged — explicit
  by-id access is deliberate teacher access and always returns optional-catalog rows regardless of that flag.
  `qb.stats()` reports the triple denominators: raw registry rows == required-active rows + optional-catalog
  rows + merged-alias rows (919 = 878 + 19 + 22). PREF-14.1/.2 reaffirm Lesson 4-1's status under this record;
  they do not reopen it. Source: `qb.py` module docstring ("Optional-catalog exclusion") and `CLAUDE.md` §
  "Lesson 4-1 (OPTIONAL CATALOG — not scheduled, not required)".
- **`PROGRAM_DOSSIER.md` §15** (Incident-Derived A2 Reliability Addendum, RC-directed 2026-07-22): item 1
  "Unknown ≠ zero," item 2 "Unavailability may not relock," item 3 "Fail-open navigation never awards
  credit," item 4 "Server ledger + stable student identity are authoritative — browser state is
  identity-scoped cache only, never a source of record," and item 7 "Official evidence is append-only" are
  the direct basis for PREF-06's reliability constraints. This record cites those items; it does not restate
  them as new policy or reopen any of the eleven items in that addendum.
- **Closed content-readiness / DOK / verified-item / alias decisions**: the canonical verification pipeline,
  the 39-entry DOK review log (`tools/dok-review/review_log.jsonl`), and the 22-pair RC-authorized
  merged-alias resolution (`rc-merge-auth-5-4-2026-07-23`, realized in `qb.py`'s `get`/`select`/
  `get_for_packet`) are authoritative and closed. PREF-14.4 through .7 cite them; this record does not reopen,
  relitigate, or extend any of them.

## Downstream bindings

| PREF area | Implementing deliverable(s) |
|---|---|
| PREF-01 — Desk navigation & release model | D4 DESK_STATE_MODEL; D6 PHASED_PRODUCT_SEQUENCE |
| PREF-02 — Classroom modality (paper-first + digital capture) | D4 DESK_STATE_MODEL; D5 ANSWER_EQUIVALENCE_CONTRACT |
| PREF-03 — Grade composition & quarter rule | D2 GRADING_POLICY_SPEC; D3 SCHOOLOGY_PROJECTION_CONTRACT |
| PREF-04 — Participation & extra credit | D2 GRADING_POLICY_SPEC |
| PREF-05 — Schoology role & reconciliation | D3 SCHOOLOGY_PROJECTION_CONTRACT; D2 GRADING_POLICY_SPEC |
| PREF-06 — Attempts, recovery & reliability | D4 DESK_STATE_MODEL; D2 GRADING_POLICY_SPEC |
| PREF-07 — Answer evaluation authority | D5 ANSWER_EQUIVALENCE_CONTRACT |
| PREF-08 — TI-84 trainer scope | D6 PHASED_PRODUCT_SEQUENCE; D2 GRADING_POLICY_SPEC; D8 NEXT_TRANCHE_PROPOSAL |
| PREF-09 — Equation Lab scope | D6 PHASED_PRODUCT_SEQUENCE; D2 GRADING_POLICY_SPEC; D8 NEXT_TRANCHE_PROPOSAL |
| PREF-10 — Desk personality & reward economy | D6 PHASED_PRODUCT_SEQUENCE; D8 NEXT_TRANCHE_PROPOSAL |
| PREF-11 — Organization & surfaces | D3 SCHOOLOGY_PROJECTION_CONTRACT; D6 PHASED_PRODUCT_SEQUENCE |
| PREF-12 — ELL & accessibility | D6 PHASED_PRODUCT_SEQUENCE; D8 NEXT_TRANCHE_PROPOSAL |
| PREF-13 — Pacing | D6 PHASED_PRODUCT_SEQUENCE |
| PREF-14 — Content boundaries | D6 PHASED_PRODUCT_SEQUENCE; D8 NEXT_TRANCHE_PROPOSAL |

---

## Changelog — NT16 (v2.0)

- **2026-07-24 (v2.0).** RC issued nine additional rulings, resolving OPEN-08, OPEN-09, OPEN-10, OPEN-11,
  OPEN-15, OPEN-16, OPEN-17, OPEN-18, and OPEN-19 (see "NT16 rulings — 2026-07-24" above). Four previously-
  `OPEN` sub-decision rows flipped to `DECIDED`, in place, with the `OPEN-NN` cross-reference token kept
  visible in the decision text: PREF-03.10 (OPEN-08), PREF-03.11 (OPEN-09), PREF-04.7 (OPEN-10), PREF-04.8
  (OPEN-11). Five new `DECIDED` sub-decision rows were added, each appending the next available `M` index in
  its area — no existing row was renumbered, reordered, or deleted: PREF-03.12 (WORK point-based aggregation,
  OPEN-15), PREF-03.13 (zero-denominator UNKNOWN semantics, OPEN-16), PREF-03.14 (point-weighted same-kind
  reduction + ASSESSMENT formula, OPEN-19), PREF-06.10 (retake orthogonality / `completed` terminal at the
  tile, OPEN-17), and PREF-01.11 (skip-transition legality + teacher-only authority, OPEN-18). The prose
  paragraphs under PREF-03 and PREF-04 were updated to reflect these resolutions. Ten items remain `OPEN` and
  unchanged: OPEN-01 through OPEN-07, OPEN-12, OPEN-13, OPEN-14 — including an NT16-recorded interim operating
  rule for OPEN-12/OPEN-13 (deterministic cases may be accepted; unsupported symbolic/tolerance cases route to
  teacher review, never auto-fail) that is explicitly labeled as an interim rule, not a resolution of either
  item. This document itself carried no direct in-text references to the sibling v1 JSON artifacts, so none
  needed rewriting here; noted for completeness, the NT16 package-wide rename applies to
  `grading_policy.v1.json` → `grading_policy.v2.json`, `desk_state_model.v1.json` → `desk_state_model.v2.json`,
  and `schoology_projection.v1.json` → `schoology_projection.v2.json`. PREF-05.9's verbatim wording and its
  reconciling annotation were left untouched, as required.
