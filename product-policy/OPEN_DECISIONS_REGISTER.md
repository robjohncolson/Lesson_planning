# Open Decisions Register

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.
**Register status:** 10 open / 9 resolved (was 19 open in v1.0).

## Purpose and how to use this register

**The owner of every item in this register is RC.** No other person, document, or downstream deliverable in
this package resolves, closes, or narrows any of these on her behalf — each item is recorded here because, at
some point, only RC's interview text and clarifications, or a later dated RC ruling, could settle it.

This register is **the single place** a downstream implementer (Desk, Schoology projection, grading engine,
TI-84 trainer, Equation Lab, ELL/accessibility work, or any future tranche) checks before assuming a value for
one of these questions. For any item still marked `OPEN` below: **no deliverable in this package — and no
deliverable built on top of it — may guess a value for it.** Where a sibling deliverable had to be runnable
anyway, it may implement a narrow, explicitly labeled placeholder so its code and tests can execute; that
placeholder is never policy, never a recommendation to RC, and never something a later document may cite as if
it had been decided. Each still-open entry below says, where applicable, which sibling deliverable carries such
a placeholder and points at it.

**This register's defining discipline, corrected as of NT16 (v2.0): it is the canonical list of every question
that was ever open, and each entry carries its CURRENT status.** Version 1.0 of this register asserted "every
item below is unresolved" and that its defining discipline was to contain "ONLY genuinely unresolved matters."
That was true at the time, but RC has since ruled on nine of the original nineteen items, so it is no longer
the operative rule. The corrected discipline: an item RC has ruled on is marked `RESOLVED by RC 2026-07-24`,
with her ruling and its provenance recorded in place, and it is **never deleted** — so a downstream reader can
always find both the original question and RC's answer to it here, together. Only the items still marked
`OPEN` below may not be guessed at; a `RESOLVED` entry is binding policy kept here for the audit trail, not an
open question. See "Not in this register, and why" at the end of this document for the full, corrected
boundary — DEFERRED items are still excluded, but RESOLVED items are now an explicit carve-out that remains
listed.

**A resolved entry may also carry a flagged residual sub-question, without reopening.** RC ruling on the
question an entry below asked does not automatically foreclose every narrower reading question her ruling's own
text leaves unaddressed. This package already establishes the pattern for exactly that situation:
`GRADING_POLICY_SPEC.md` §4.1 records OPEN-11's excused-vs-unknown case as "a documented reading, not an
invention beyond RC's ruling" — a reading RC's text permits but does not itself pin down, clearly distinguished
in its own labeling from the ruling itself. Where a `RESOLVED` entry below carries such a note, it is recorded as
a labeled implementation reading flagged for RC to confirm or override — never presented as a second ruling,
never a reason to flip the entry's `Status` back to `OPEN`, and never grounds for minting a new `OPEN-NN` id.
The entry's `Status` line, the register's summary table, and the 10-open/9-resolved inventory all stay exactly
as RC's ruling left them.

## Summary table

| ID | Title | Traces to (PREF) | Raised by | Status |
|---|---|---|---|---|
| OPEN-01 | TI-84 matrices skill: include or exclude | PREF-08 | RC (Area 8, undecided at interview time) | OPEN |
| OPEN-02 | Equation Lab AI provider choice | PREF-09 | RC (Area 9, undecided at interview time) | OPEN |
| OPEN-03 | Desk / product naming strings | PREF-11 | RC (Area 11, undecided at interview time) | OPEN |
| OPEN-04 | Schoology assignment + category naming strings | PREF-05, PREF-11 | RC (Areas 5 and 11, undecided at interview time) | OPEN |
| OPEN-05 | Audio support for ELL | PREF-12 | RC (Area 12, undecided at interview time) | OPEN |
| OPEN-06 | Bilingual support scope | PREF-12 | RC (Area 12, undecided at interview time) | OPEN |
| OPEN-07 | Exact AI integration for ELL explanations | PREF-12 | RC (Area 12, undecided at interview time) | OPEN |
| OPEN-08 | Completion-percentage rounding rule | PREF-03 | RC (Area 3, undecided at interview time) | RESOLVED by RC 2026-07-24 |
| OPEN-09 | Point/score rounding rule for aggregates and the published grade | PREF-03 | RC (Area 3, undecided at interview time) | RESOLVED by RC 2026-07-24 |
| OPEN-10 | Daily cap on extra-credit participation points | PREF-04 | RC (Area 4, undecided at interview time) | RESOLVED by RC 2026-07-24 |
| OPEN-11 | Participation credit on partial-attendance / non-class days | PREF-04 | RC (Area 4, undecided at interview time) | RESOLVED by RC 2026-07-24 |
| OPEN-12 | Numeric-equivalence tolerance defaults | PREF-07 | RC (Area 7, undecided at interview time) | OPEN |
| OPEN-13 | CAS / symbolic-equivalence engine choice | PREF-07 | RC (Area 7, undecided at interview time) | OPEN |
| OPEN-14 | Candy / reward activation timing detail | PREF-10 | RC (Area 10, undecided at interview time) | OPEN |
| OPEN-15 | WORK-aggregate component combination + scale normalization | PREF-03, PREF-04 | Manager (Opus 5), minted during NT15 implementation (D2) | RESOLVED by RC 2026-07-24 |
| OPEN-16 | Completion percentage when no digital work is designated yet (zero denominator) | PREF-03 | Manager (Opus 5), minted during NT15 implementation (D2) | RESOLVED by RC 2026-07-24 |
| OPEN-17 | Whether `completed` is terminal at the Desk-tile layer, or a retake reopens it | PREF-01, PREF-06 | Manager (Opus 5), minted during NT15 implementation (D4) | RESOLVED by RC 2026-07-24 |
| OPEN-18 | Whether `skipped` is reachable after release, and whether it is reversible | PREF-01, PREF-13 | Manager (Opus 5), minted during NT15 implementation (D4) | RESOLVED by RC 2026-07-24 |
| OPEN-19 | Reduction of multiple same-kind items to a single aggregate scalar | PREF-03 | Manager (Opus 5), minted during NT15 implementation (D3) | RESOLVED by RC 2026-07-24 |

---

### OPEN-01 — TI-84 matrices skill: include or exclude

**Question.** Should the TI-84 matrices skill be a required TI-84 trainer skill, alongside
graphing/window selection, tables, zeros/intersections/extrema, sequences, and solver?

**Owner.** RC.

**Why it is open.** RC's Area 8 text names five required skills explicitly (`PREF-08.1`–`.5`) and explicitly
omits regression (`PREF-08.7`, DECIDED). Matrices sits in neither list — RC's text states directly that
matrices is undecided (`PREF-08.6`). It is not a case of RC being silent by omission the way an unstated skill
would be; RC's clarifications flagged matrices by name as unresolved.

**What unblocks it.** RC's explicit inclusion or exclusion decision for the matrices skill.

**Consequence if left open.** The TI-84 trainer's required-skill scope cannot be finalized; any trainer build
or curriculum-alignment document that lists "required skills" must render matrices as pending, not as included
or excluded by default. No sibling deliverable in this tranche implements a placeholder for this — it is a
content-scope question, not a runtime computation, so there is nothing to leave a labeled stand-in for.

---

### OPEN-02 — Equation Lab AI provider choice

**Question.** Which AI provider should power Equation Lab's explanation features?

**Owner.** RC.

**Why it is open.** RC's Area 9 text settles Equation Lab's scope (polynomial identities + quadratic
equations), its primary interaction mode (answer/simplified-form entry), unlimited retries, immediate
feedback, and its reinforcement/extra-credit (not main-assessment) role. It does not name or select an AI
provider (`PREF-09.8`).

**What unblocks it.** RC's selection of a specific AI provider (or explicit criteria for the implementer to
choose one on RC's behalf).

**Consequence if left open.** No Equation Lab AI-explanation integration can be built or vendor-committed.
This is independent of the Answer Equivalence Contract's Tier 4 (AI explanation only, D5) — Tier 4 defines the
*authority boundary* an AI may operate within (explain, never alone decide correctness or credit) regardless
of which provider is eventually chosen; OPEN-02 is the provider selection itself, not the authority question.

---

### OPEN-03 — Desk / product naming strings

**Question.** What are the actual display strings (product name, section labels, UI copy) for the Desk?

**Owner.** RC.

**Why it is open.** RC's Area 11 text settles Desk's role as the primary learning interface, that Schoology is
the primary distribution/notification surface, that projections are organized by topic and lesson, that DOK is
teacher-primary and not emphasized to students, and that Schoology maintenance should be automated where
possible. It does not fix any naming strings (`PREF-11.7`).

**What unblocks it.** RC supplying the naming strings she wants used, or explicit sign-off on proposed
candidates.

**Consequence if left open.** No Desk-facing UI copy can be treated as final. Any interim strings used in
mockups, fixtures, or prototypes must be understood as placeholders, not committed product naming.

---

### OPEN-04 — Schoology assignment + category naming strings

**Question.** What are the actual display strings Schoology will show for assignment titles and category
names (e.g., the WORK/ASSESSMENT category labels, individual assignment titles)?

**Owner.** RC.

**Why it is open.** `SCHOOLOGY_PROJECTION_CONTRACT.md` §3 states explicitly that "final display strings are
RC's to set later" and specifies structure only (which category, what granularity, what point value, whether
the extra-credit flag applies) — never the human-facing strings themselves. `RC_TEACHER_PREFERENCE_RECORD.md`
records this under both PREF-05 (Schoology role) and PREF-11 (organization/surfaces), since it is a naming
question that surfaces on the projection layer specifically.

**What unblocks it.** RC supplying the naming strings for Schoology categories and assignment titles.

**Consequence if left open.** The projection contract's structural mapping (§3 of
`SCHOOLOGY_PROJECTION_CONTRACT.md`) is implementable today using placeholder category keys (`WORK`,
`ASSESSMENT`) and entity-type labels, but no display string reaching a student, parent, or counselor through
Schoology can be treated as final until RC sets them.

---

### OPEN-05 — Audio support for ELL

**Question.** What audio support (e.g., text-to-speech, recorded narration, pronunciation aids) should the
platform provide for ELL students, if any?

**Owner.** RC.

**Why it is open.** RC's Area 12 text settles vocabulary support, worked examples, simpler-language
explanations that preserve mathematical demand, Chromebook-first + mobile-adaptive platform choice, and
tolerance for flaky connectivity with paper-first fallback, all as required (`PREF-12.1`–`.7`, DECIDED). Audio
support specifically is named as unresolved (`PREF-12.8`).

**What unblocks it.** RC's decision on whether audio support is required, and if so, what form it takes.

**Consequence if left open.** No audio-support feature can be scoped, designed, or built for the ELL
accessibility work. It is not safe to assume audio is either included or excluded from the required
accessibility set.

---

### OPEN-06 — Bilingual support scope

**Question.** What is the scope of bilingual support (e.g., which languages, which surfaces — Desk UI,
worked examples, vocabulary support — get bilingual treatment)?

**Owner.** RC.

**Why it is open.** Same boundary as OPEN-05: RC's Area 12 text settles the required accessibility items listed
above but leaves bilingual support scope explicitly unresolved (`PREF-12.9`).

**What unblocks it.** RC's decision on which languages and which surfaces require bilingual support.

**Consequence if left open.** No bilingual-support feature can be scoped, designed, or built. The ELL
accessibility requirements that are decided (vocabulary support, worked examples, simpler-language
explanations) must not be assumed to already include or exclude a bilingual dimension.

---

### OPEN-07 — Exact AI integration for ELL explanations

**Question.** What is the exact AI integration (provider, mechanism, scope of use) for generating or assisting
ELL simpler-language explanations?

**Owner.** RC.

**Why it is open.** RC's Area 12 text requires simpler-language explanations that preserve mathematical demand
(`PREF-12.3`, DECIDED) but does not specify the AI integration that would produce them (`PREF-12.10`).

**What unblocks it.** RC's decision on the specific AI integration to use for ELL explanation generation.

**Consequence if left open.** No ELL-explanation AI feature can be vendor-committed or built. This is distinct
from OPEN-02 (Equation Lab's AI provider) — the two features serve different product surfaces and RC's text
leaves each open independently; neither answer may be assumed to apply to the other.

---

### OPEN-08 — Completion-percentage rounding rule

**Question.** Is the completion ratio (`GRADING_POLICY_SPEC.md` §2) rounded before being compared to the 40%
gate, and if so, to how many digits and under what rounding mode (e.g., round-half-up, round-half-even,
truncation)?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** Compare the EXACT completion ratio against the inclusive 0.40 threshold; no pre-rounding before
branch selection.

**Supersedes.** v1.0's `grading_policy_ref.py` `compute_completion` exposed an opt-in `round_ndigits` parameter
(default `None`, no rounding) as an unresolved-pending-RC placeholder that left rounding an open question.
`grading_policy.v2.json` removes `round_ndigits` entirely from `compute_completion` — pre-rounding is now
forbidden policy, not merely undecided.

**Why it was open (historical).** RC's text settled the completion-percentage definition and scope
(teacher-designated digital work only, `PREF-03.4`) and settled the 40% gate's inclusivity exactly
(`completion >= 0.40` takes the max branch — `PREF-03.5`). It did not say anything about rounding the ratio
itself before that comparison (`PREF-03.10`), which is what this item asked and what the ruling above now
answers.

**Consequence while it was open (historical).** `grading_policy_ref.py`'s `compute_completion` applied no
rounding by default; an optional `round_ndigits` parameter existed only as an opt-in hook
(`GRADING_POLICY_SPEC.md` §8). That hook was a runnable placeholder for testing the parts of the policy RC had
settled — it was not a proposal for what the rounding rule should be, and no other document was permitted to
cite its existence as if RC had decided to round (or not round) the completion ratio. This has now been
superseded by the ruling above.

---

### OPEN-09 — Point/score rounding rule for aggregates and the published grade

**Question.** Are the WORK aggregate, the ASSESSMENT aggregate, or the final published quarter grade rounded,
and if so, to how many digits and under what rounding mode?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** Full precision internally; round ONLY the student-facing final-grade display, to one decimal;
Schoology keeps native earned/possible totals; reconciliation compares underlying values consistently and must
not mistake display rounding for substantive divergence.

**Supersedes.** v1.0's `compute_quarter_grade` exposed an opt-in `round_ndigits` parameter (default `None`, no
rounding), with no internal/display distinction, as an unresolved-pending-RC placeholder. `grading_policy.v2.json`
removes `round_ndigits` from `compute_quarter_grade` and adds dedicated display-only functions
(`round_final_grade_for_display`, `final_grade_display_string`).

**Residual — rounding MODE, flagged for RC confirmation (not itself a ruling).** RC's ruling above settles
display *precision* (one decimal, display-only, full precision retained internally) but her text does not
specify the rounding MODE that produces that one-decimal value — round-half-up, round-half-even ("banker's
rounding"), and truncation disagree on cases like `round(0.25, 1)` (`0.2` under half-even, `0.3` under half-up)
and `round(0.35, 1)` (`0.3` under half-even). This narrower question was never put to RC, and the ruling above
does not answer it. The implementation reads the silence as **half-even** (Python's built-in `round`), and labels
that reading explicitly rather than presenting it as decided: `grading_policy.v2.json`'s `display_rounding_mode`
field, `grading_policy_ref.py`'s docstring, and `GRADING_POLICY_SPEC.md` all carry the same caveat — an
implementation choice pending RC confirmation, not a second ruling. This follows the same labeled-reading pattern
already established for OPEN-11's excused-vs-unknown case (`GRADING_POLICY_SPEC.md` §4.1: "a documented reading,
not an invention beyond RC's ruling"). OPEN-09 itself stays `RESOLVED` — RC did rule, and the ruling above is
implemented in full; this residual note flags a narrower, still-open reading question for RC to confirm or
override. It does not reopen OPEN-09, does not change the register's 10-open/9-resolved inventory, and does not
mint a new `OPEN-NN` id.

**Why it was open (historical).** RC's text settled both quarter-rule branch formulas exactly (`max()` and the
arithmetic mean, `PREF-03.5`/`.6`) but said nothing about whether the aggregate values or the resulting quarter
grade were rounded for display or for the record (`PREF-03.11`) — independently for the WORK aggregate, the
ASSESSMENT aggregate, and the published quarter grade, which the ruling above now settles.

**Consequence while it was open (historical).** `grading_policy_ref.py`'s `compute_quarter_grade` applied no
rounding by default; an optional `round_ndigits` parameter existed only as an opt-in hook
(`GRADING_POLICY_SPEC.md` §8). As with OPEN-08, this hook was a runnable placeholder for testing, not a decided
rounding rule — no downstream document was permitted to treat "no rounding" as RC's chosen answer. This has now
been superseded by the ruling above.

**AMENDED by RC 2026-07-24 (later same date; NT16-B) — rounding MODE confirmed.** The residual question above
has now been directly answered. RC's verbatim ruling: "Use conventional decimal ROUND_HALF_UP for the
student-facing one-decimal display. Example: 89.25 → 89.3. Do not use Python binary-float round() or half-even
behavior for the display contract. Keep full precision internally. Do not round before the 40% branch decision.
Schoology reconciliation compares underlying values; display rounding cannot conceal real divergence." This
SUPERSEDES the half-even implementation reading recorded above, which was never a ruling and is preserved here
as the historical record of what this package read into RC's silence before she confirmed the mode.
`round_final_grade_for_display` (`grading_policy_ref.py`) now rounds via
`decimal.Decimal(value).quantize(exponent, rounding=ROUND_HALF_UP)`, with `exponent` derived from
`final_grade_display_decimals` rather than hard-coded; `grading_policy.v2.json`'s
`rounding_rules.display_rounding_mode` and `GRADING_POLICY_SPEC.md` §4.1/§9 have been updated to match. OPEN-09
stays `RESOLVED` — this is an amendment to an already-decided ruling's previously-unconfirmed residual, not a
reopening, and no new `OPEN-NN` id is minted for it.

---

### OPEN-10 — Daily cap on extra-credit participation points

**Question.** Is there a cap on the total extra-credit participation points a student can earn in a single day
(e.g., if a student completes both a TI-84 exercise and an Equation Lab exercise on the same day, earning
`+0.5` each)?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** +1.0 point per student per class day cap for currently-authorized extra credit (TI-84 +0.5,
Equation Lab +0.5, stacking allowed); any FUTURE extra-credit source requires a new policy decision — it never
silently exceeds the cap.

**Supersedes.** v1.0's `compute_extra_credit` applied no cap by default and exposed an opt-in `daily_cap`
parameter as an unresolved-pending-RC placeholder. `grading_policy.v2.json` makes the 1.0-point cap
unconditional policy and removes the `daily_cap` parameter; a request naming an extra-credit source outside the
two currently-authorized sources now requires a new RC policy decision rather than silently extending the
ledger or being clipped into the existing cap.

**Why it was open (historical).** RC's Area 4 text fixed the two named extra-credit unit values exactly
(`+0.5` for TI-84, `+0.5` for Equation Lab, `PREF-04.3`/`.4`) but never stated whether these could stack
without limit on a single day, or whether some daily ceiling applied (`PREF-04.7`) — settled now by the ruling
above.

**Consequence while it was open (historical).** `grading_policy_ref.py`'s `compute_extra_credit` applied no cap
by default; an optional `daily_cap` parameter existed only as an opt-in hook (`GRADING_POLICY_SPEC.md` §8).
This was a runnable placeholder for testing the decided per-unit values, not evidence that RC had decided
against a cap — the question became more consequential as more extra-credit-eligible exercise types were added
in future tranches. This has now been superseded by the ruling above.

---

### OPEN-11 — Participation credit on partial-attendance / non-class days

**Question.** How should daily participation credit be handled on a day of partial attendance, or on a day
that is not a normal class day at all (e.g., an assembly day, or a day the student is enrolled in the section
but the section does not meet)?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** Non-class days are EXCLUDED from the participation requirement. Partial/absent/uncertain attendance
NEVER auto-zeroes — such days are excused/unknown unless RC explicitly designates the day
participation-eligible. UNKNOWN is distinct from zero.

**Supersedes.** v1.0's `compute_participation_point` returned `UNKNOWN` for any non-class or
partial-attendance day as an unresolved-pending-RC placeholder. `grading_policy.v2.json` replaces it with a
rule that distinguishes excluded/excused non-class and non-eligible partial/absent days (contributing nothing,
never an auto-zero) from genuinely-unknown attendance (UNKNOWN), and adds an explicit
participation-eligible-designation override for partial/absent days RC designates as participation-eligible.

**Why it was open (historical).** RC's Area 4 text defined participation credit in terms of "a class day"
(`PREF-04.1`/`.2`, DECIDED) but did not address what happened when that day was not a full ordinary class day
(`PREF-04.8`) — settled now by the ruling above.

**Consequence while it was open (historical).** `grading_policy_ref.py`'s `compute_participation_point` returned
`UNKNOWN` (never a guessed `0.0` or `1.0`) whenever the caller explicitly marked a day as non-class or
partial-attendance (`GRADING_POLICY_SPEC.md` §8). This was the correct and safe UNKNOWN-not-zero direction for
a runnable reference, not a decided policy for what should actually happen on such days. This has now been
superseded by the ruling above.

**CONFIRMED by RC 2026-07-24 (later same date; NT16-B).** RC issued a further, explicit four-point confirmation
of the excused-vs-unknown implementation reading `GRADING_POLICY_SPEC.md` §4.1 and `grading_policy_ref.py`'s
`compute_participation_day` had already read into her original ruling above (previously labeled "a documented
reading, not an invention beyond RC's ruling," not itself a second ruling). Her verbatim confirmation:

- "A known absent, partial-attendance, or non-class day is excused and contributes 0 earned / 0 possible."
- "A genuinely uncertain attendance state remains UNKNOWN."
- "Neither case produces an automatic participation zero."
- "RC may explicitly designate an otherwise excused day as participation-eligible."

`compute_participation_day` already conformed to all four points before this confirmation — no code change
accompanies it, only the removal of the "pending RC confirmation" / "documented reading, not itself a ruling"
labeling these four cases previously carried. OPEN-11 stays `RESOLVED`; no new `OPEN-NN` id is minted.

---

### OPEN-12 — Numeric-equivalence tolerance defaults

**Question.** What are the actual tolerance value(s) — absolute vs. relative, and the specific threshold — for
treating a decimal submission as equivalent to a fraction/exact-value expected answer?

**Owner.** RC.

**Why it is open.** RC's Area 7 text requires deterministic symbolic/numeric equivalence where supported
(`PREF-07.1`, DECIDED) and `ANSWER_EQUIVALENCE_CONTRACT.md` records that the *concept* of numeric tolerance is
part of the policy (a numeric submission within tolerance of the expected value is accepted), but the actual
tolerance value is not fixed by RC's text (`PREF-07.6`).

**What unblocks it.** RC's decision on the tolerance value(s) to use, and whether tolerance should be
absolute, relative, or vary by item type.

**Interim operating rule (NT16, 2026-07-24 — NOT a resolution of this item).** RC stated an interim rule that
governs answer-evaluation behavior while this item remains open: clearly-deterministic cases may be accepted;
unsupported symbolic/tolerance cases route to teacher review, never auto-fail. This is an operating rule for
implementers to follow in the meantime — it does **not** settle the tolerance value(s) asked by the Question
above, and OPEN-12 remains `OPEN` and owned by RC.

**Consequence if left open.** The exact Tier-1 `auto-correct`/`auto-incorrect` boundary for every
numeric-tolerance-bearing item is undetermined. Per `ANSWER_EQUIVALENCE_CONTRACT.md`, any test vector that
depends on a specific tolerance boundary carries the `OPEN-12` token and its `expected_outcome` is illustrative,
not settled policy — only clearly-inside or clearly-outside cases can be handled by convention until this is
set.

---

### OPEN-13 — CAS / symbolic-equivalence engine choice

**Question.** Which CAS/symbolic-equivalence engine or library does Tier 1 (deterministic equivalence
checking) run on?

**Owner.** RC.

**Why it is open.** RC's Area 7 text requires deterministic symbolic/numeric equivalence checking and gives one
worked example (`x + y ≡ y + x`, `PREF-07.1`, DECIDED), but does not name or select an engine (`PREF-07.7`).
`ANSWER_EQUIVALENCE_CONTRACT.md` states explicitly that the contract deliberately does not choose one.

**What unblocks it.** RC's selection of a specific CAS/symbolic-equivalence engine (or explicit delegation of
that technical choice to an implementer, with RC's sign-off on the resulting capability boundary).

**Interim operating rule (NT16, 2026-07-24 — NOT a resolution of this item).** RC stated an interim rule that
governs answer-evaluation behavior while this item remains open: clearly-deterministic cases may be accepted;
unsupported symbolic/tolerance cases route to teacher review, never auto-fail. This is an operating rule for
implementers to follow in the meantime — it does **not** select an engine or settle the capability boundary
asked by the Question above, and OPEN-13 remains `OPEN` and owned by RC.

**Consequence if left open.** The actual boundary of what Tier 1 can prove at all is undetermined — whether
factored-vs-expanded equivalence, trig-identity equivalence, or other symbolic rewrites are provable
deterministically depends entirely on engine capability. Per `ANSWER_EQUIVALENCE_CONTRACT.md`, until an engine
is chosen, any item requiring symbolic proof beyond simple arithmetic/commutativity should be treated as
provisionally Tier 2 (routes to teacher review) in production, even though the contract's illustrative test
vectors assume a baseline-capable engine for clarity of exposition.

---

### OPEN-14 — Candy / reward activation timing detail

**Question.** What is the exact timing detail for when the candy/reward economy activates relative to the
first academic release (e.g., a specific date, a specific milestone, a specific number of weeks after
launch)?

**Owner.** RC.

**Why it is open.** RC's Area 10 text settles that the candy/per-question economy is kept (`PREF-10.4`,
DECIDED), that it need not block the first academic release (`PREF-10.9`, DECIDED), that it is phased in
"shortly after" that release (`PREF-10.10`, DECIDED), and that reward seams must be preserved in the
academic-first architecture so the later candy implementation needs no rework (`PREF-10.11`, DECIDED). "Shortly
after" is not a specific timing commitment — the exact activation detail is unresolved (`PREF-10.12`).

**What unblocks it.** RC's decision on the specific timing trigger for candy/reward activation.

**Consequence if left open.** The academic-release architecture must preserve reward seams (already decided and
binding) but cannot commit to an actual activation date or milestone for candy/rewards until RC sets one.

---

### OPEN-15 — WORK-aggregate component combination + scale normalization

**Question.** How do the WORK aggregate's three components — teacher-designated digital packet work,
daily participation evidence, and designated extra credit — combine into a single WORK aggregate value? In
particular, what weighting (if any) and what common scale should be applied, given that packet work is
naturally percentage- or point-scale while participation (`1.0`/day) and extra credit (`0.5`/exercise) are
flat point bonuses?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** WORK aggregation is point-based: `WORK = 100 × (packet_points_earned + participation_points_earned
+ extra_credit_points_earned) / (packet_points_possible + participation_points_possible)`. Only
teacher-designated official evidence enters. Extra credit raises earned but NOT possible. WORK may exceed 100.
Zero denominator falls to OPEN-16's rule. NEVER add a percentage directly to raw flat points. This SUPERSEDES
the provisional three-scalar plain addition.

**Supersedes.** v1.0's `compute_work_aggregate` combined the three WORK components (digital packet work score +
participation points + extra-credit points) by plain scalar addition — an unresolved-pending-RC placeholder
that risked mixing a percentage-scale score with flat point bonuses without normalization. The point-based
ratio formula above replaces that three-scalar addition entirely; the old three-scalar-addition signature is
removed in `grading_policy.v2.json`.

**Why it was open (historical).** RC's Area 3 text listed the three WORK components joined by "+"
(`PREF-03.2`, DECIDED as to *which* components belong in WORK) but never fixed a weighting or a common scale
across them. This item was minted by the manager (Opus 5) during NT15 implementation, not stated as unresolved
by RC directly — an implementer would otherwise have had to silently infer a combination formula RC never
specified. RC's ruling above now supplies that formula directly.

**Consequence while it was open (historical).** `grading_policy_ref.py`'s `compute_work_aggregate`
(`GRADING_POLICY_SPEC.md` §1.1, §8) combined the three components by plain addition, with no weighting or
scale normalization, as a labeled runnable placeholder only — explicitly **not** a decided formula. The risk
this left open: combining a percentage-scale packet score with flat point bonuses by plain addition meant the
WORK aggregate's effective scale drifted depending on how many participation/extra-credit points a student
happened to accumulate, which could make it non-comparable to the ASSESSMENT aggregate it was later `max`'d or
averaged against under the quarter rule (§3 of `GRADING_POLICY_SPEC.md`). `SCHOOLOGY_PROJECTION_CONTRACT.md`
(D3) independently declared this same dependency at the top of the document and again in its §4.3. This has
now been superseded by the ruling above; WORK may exceed 100 as a decided consequence of the point-based
formula.

---

### OPEN-16 — Completion percentage when no digital work is designated yet (zero denominator)

**Question.** What should "completion percentage" mean when the teacher has not yet designated any digital
work at all — i.e., when the completion ratio's denominator is 0?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** No eligible designated work/participation ⇒ completion UNKNOWN, WORK UNKNOWN, quarter grade
UNKNOWN; student-facing display = dash / "not enough evidence", never zero; the Schoology projection must NOT
fabricate a zero-valued assignment to force a grade.

**Supersedes.** v1.0's `compute_completion` already returned `UNKNOWN` for a zero denominator, but the
real-world consequence — an early-quarter `UNKNOWN` window for every student — was left unresolved-pending-RC,
not confirmed policy. RC's ruling confirms `UNKNOWN` propagation through WORK (`compute_work_aggregate`) and
the quarter grade (`compute_quarter_grade`) as decided policy, and adds a defined display convention (dash /
"not enough evidence").

**Why it was open (historical).** RC's Area 3 text defined completion percentage over teacher-designated
digital work (`PREF-03.4`, DECIDED as to scope) but did not address the case where no such work had been
designated yet. This item was minted by the manager (Opus 5) during NT15 implementation: an implementer would
otherwise have had to silently infer a value (e.g., treating undesignated work as 0% or 100% complete) for a
case RC had never addressed. RC's ruling above confirms the outcome directly.

**Consequence while it was open (historical).** This had a real, non-cosmetic teacher-facing consequence: early
in a quarter, before the teacher had designated any digital work, every student's completion — and therefore
the quarter-rule branch (§3 of `GRADING_POLICY_SPEC.md`) — was `UNKNOWN` for every student, for as long as the
denominator stayed at 0. `grading_policy_ref.py`'s `compute_completion` returned `UNKNOWN` (never `0`, never a
fabricated ratio) in this case, which was the correct and safe UNKNOWN-not-zero direction per dossier §15 item
1 — but whether that early-quarter `UNKNOWN` window was an acceptable outcome, or whether RC wanted a
different treatment, was itself the open question. The ruling above confirms it as the decided, acceptable
outcome.

---

### OPEN-17 — Whether `completed` is terminal at the Desk-tile layer, or a retake reopens it

**Question.** Does a within-quarter retake ever move a lesson's Desk-tile state back out of `completed` (e.g.
to `released`, for a fresh attempt to be visible), or is retake activity purely an assessment/evidence-layer
event that leaves the Desk tile showing `completed` throughout?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** `completed` remains TERMINAL for the lesson tile; a retake is an ORTHOGONAL activity/affordance
attached to the completed lesson — never demotes completion, relocks, erases history, or alters the grading
engine via navigation state. `completed` keeps zero legal exits — now DECIDED, not open. The retake-affordance
concept is documented as orthogonal; implementation details are deferred to the work packages (D8).

**Supersedes.** v1.0's `DESK_STATE_MODEL.md` §3.1/§8 and `desk_state_model.v1.json` kept zero legal exit
transitions from `completed` as a conservative reading pending RC's decision — flagged unresolved-pending-RC
and subject to change if RC decided otherwise. RC's ruling confirms that same zero-exit modeling as DECIDED
policy (not merely a conservative placeholder), and adds the retake-affordance concept (`desk_state_model.v2.json`
top-level `retake_affordance` object) as an orthogonal activity that is never itself a Desk-state transition.
Cross-reference: `desk_state_model.v2.json`'s `transitions.resolved` array carries this same resolution under
its preserved identifier **U1** (`completed → null`, "any legal exit from completed... reopening the Desk
tile") alongside U2/U3 (see OPEN-18 below).

**Why it was open (historical).** RC's Area 6 text stated plainly that retakes are allowed within the quarter
(`PREF-06.4`, DECIDED). RC's text did not say whether a retake was visible as a Desk-tile state change at all.
This was a real product question, not a formal modeling gap: `DESK_STATE_MODEL.md`'s transition table (§3.1)
defined **zero legal exit transitions** out of `completed` — deliberately, as the conservative reading
consistent with dossier §15 item 2 ("no event demotes known-completed work"). That zero-exit modeling was a
considered choice, not loosened just to manufacture an answer to this item; the two questions (is the
conservative modeling correct, and does RC want retakes visible on the tile) were independent, and only RC
could resolve the second — which the ruling above now does.

**Consequence while it was open (historical).** Had RC decided retakes should reopen the tile, the Desk would
have needed a new "completed lesson reopened for retake" affordance that the v1.0 state model did not provide
— new UI/state surface to design, not a detail the existing model could absorb by re-reading RC's text more
carefully. `DESK_STATE_MODEL.md` §3.1 and §8 documented the v1.0 provisional choice (no exit transition) and
flagged it as unresolved-pending-RC; that choice was not policy and could not be cited as if RC had settled it.
The ruling above now settles it: zero exits is DECIDED policy, and the retake affordance (U1, above) is
orthogonal rather than a state-model change.

---

### OPEN-18 — Whether `skipped` is reachable after release, and whether it is reversible

**Question.** Two related sub-questions: (a) can an already-`released` (but not-yet-completed) lesson be
retroactively marked `skipped`, or is `skipped` reachable only from `unreleased` (a pre-release planning
decision)? (b) is a `skipped` designation reversible at all, or is it a one-way/terminal designation for the
school year?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** Skip-transition legality is promoted to normative, with teacher authority: `unreleased`→`skipped`
ALLOWED (confirms the already-legal T3 — it was never one of the provisional four); `released`→`skipped`
ALLOWED (T7 promoted); `today`→`skipped` ALLOWED BEFORE COMPLETION (T11 promoted, pre-completion condition
encoded); `skipped`→`released` ALLOWED (T12 promoted); `skipped`→`today` ALLOWED (T13 promoted);
`completed`→`skipped` FORBIDDEN (confirms the already-illegal X3); students CANNOT initiate skip/unskip
(teacher-only actor on every skip transition). The `transitions.provisional` bucket is retired/emptied with
provenance.

**Supersedes.** v1.0's `DESK_STATE_MODEL.md` recorded T7 (`released`→`skipped`), T11 (`today`→`skipped`), T12
(`skipped`→`released`), and T13 (`skipped`→`today`) in a dedicated, non-normative **`transitions.provisional`**
bucket (§3.1b of the document; the `transitions.provisional` array in `desk_state_model.v1.json`), each tagged
`"normative": false` and cross-referenced to register entries **U2** (T7/T11) and **U3** (T12/T13) in the
JSON's `transitions.unresolved` array. RC's ruling promotes all four — T7, T11 (now carrying a machine-readable
pre-completion precondition), T12, and T13 — into the decided `transitions.legal` table in
`desk_state_model.v2.json`. `transitions.provisional` is now permanently empty (recorded in that file's
`transitions.provisional_retirement` object), and U2/U3 move to a `transitions.resolved` array, their
identifiers preserved, carrying resolution text and provenance. T3 (`unreleased`→`skipped`) and X3
(`completed`→`skipped` illegal) were **not** new grants or new prohibitions — they were already legal/illegal
respectively in v1.0's `transitions.legal`/`transitions.illegal` tables; RC's ruling **confirms** both rather
than creating a duplicate transition id. Every skip/unskip transition (T3, T7, T11, T12, T13) now carries
`"actor": "teacher_only"` and `"student_may_initiate": false` in `desk_state_model.v2.json`, and a new top-level
`skip_authority` object codifies that teacher-only rule package-wide.

**Why it was open (historical).** RC's Area 1 text established that skipped lessons render grey/inert and
appear only in the broader roadmap view (`PREF-01.9`, DECIDED), and Area 13 established that RC designates
lessons directly with no fixed calendar (`PREF-13.2`, DECIDED). Neither area's verbatim text addressed the
specific transition cases above, which is why T7/T11/T12/T13 lived in the non-normative provisional bucket
pending RC's answer — inferred only from the general principle that teacher-designation authority extends to
it (`PREF-13.2`), not a decided statement of RC's. The ruling above now supplies that decision directly.

**Consequence while it was open (historical).** The four transitions lived in `transitions.provisional`
(non-normative), not in the decided `transitions.legal` table: an implementation could provisionally allow T7,
T11, T12, and T13 pending RC's answer, but could not present any of them as decided or required behavior, and a
build that omitted all four was equally acceptable to one that implemented all four under the provisional
label. This has now been superseded by the ruling above: all four are promoted into `transitions.legal`, the
provisional bucket is retired, and no sibling deliverable should be read as leaving either sub-question open
any longer.

---

### OPEN-19 — Reduction of multiple same-kind items to a single aggregate scalar

**Question.** How do several same-kind graded items reduce to one scalar — e.g., how do several lesson packets
reduce to one packet-work score feeding WORK, and how do several lesson quizzes plus topic assessments reduce
to one ASSESSMENT aggregate scalar?

**Owner.** RC.

**Status.** RESOLVED by RC 2026-07-24.

**Ruling.** `component_percentage = 100 × Σ(current_official_points_earned) / Σ(points_possible)` for packet
assignments, lesson quizzes, topic assessments, any same-kind designated group; each item's CURRENT OFFICIAL
server-designated score; attempt-selection/overrides governed by their own rules; NEVER equal-average
assignment percentages when possible-points differ. `ASSESSMENT = 100 × total_assessment_points_earned /
total_assessment_points_possible` (quizzes + topic assessments on actual point scales).

**Supersedes.** v1.0's `parity_check.py` `_average_percentage` helper combined multiple same-kind graded items
by simple unweighted average, explicitly labeled a "FIXTURE SIMULATION CONVENTION for this parity checker
only," not asserted as decided upstream policy; `SCHOOLOGY_PROJECTION_CONTRACT.md` (D3) named the same
dependency at OPEN-19 in its declared open-item list and its §4.3 "Note (OPEN-19)" paragraph. RC's ruling
replaces any equal-average convention with the point-weighted reduction above (`compute_component_percentage` /
`compute_assessment_aggregate` in `grading_policy.v2.json`), and forbids equal-averaging per-item percentages
when possible-points differ.

**Why it was open (historical).** RC's Area 3 text, and `GRADING_POLICY_SPEC.md`'s formalization of it, both
took the WORK and ASSESSMENT scalars as already-given inputs to the quarter rule (§3 of
`GRADING_POLICY_SPEC.md`) — neither said how several packets reduce to one packet-work score, or how several
quizzes plus topic assessments reduce to one ASSESSMENT scalar. This item was minted by the manager (Opus 5)
during NT15 implementation, when `parity_check.py` needed a reduction function to be runnable at all and would
otherwise have had to silently pick one. The ruling above now supplies that reduction method directly. This
item remains adjacent to, but distinct from, OPEN-15: OPEN-19 is about how same-kind items (several packets;
several quizzes/assessments) reduce to a single scalar; OPEN-15 is about how the resulting WORK-side scalars
(packet-work score, participation, extra credit) combine with each other into the WORK aggregate. Both are now
resolved, but resolving one did not automatically resolve the other — RC ruled on each.

**Consequence while it was open (historical).** `parity_check.py`'s `_average_percentage` helper combined
multiple same-kind graded items by simple unweighted average, explicitly labeled in its surrounding comment as
a "FIXTURE SIMULATION CONVENTION for this parity checker only" — not asserted as decided upstream policy, and a
real Desk/questionbank scoring layer could have aggregated differently. This has now been superseded by the
ruling above: point-weighted reduction is decided policy, and equal-averaging per-item percentages when
possible-points differ is forbidden.

---

## Not in this register, and why

**Deferred items are excluded by design — DEFERRED ≠ OPEN.** Three matters are RC's explicit decisions **not**
to build now; no decision is pending on any of them, so none appears above:

- **Step-by-step enforcement** for Equation Lab (`PREF-09.6`) — RC decided not to build enforced
  step-by-step solution checking now.
- **Gifting, Tetris, leaderboards, and celebration noise** on the Desk (`PREF-10.5`–`.8`) — RC decided not to
  build any of these four now.
- **Intervention / makeup / enrichment subsystems** (`PREF-13.6`) — RC decided not to build these now.

Each of these is recorded with status `DEFERRED` in `RC_TEACHER_PREFERENCE_RECORD.md`. A deferred item is not
a pending question awaiting an RC answer — RC has already answered it ("not now"). Treating a deferred item as
if it were open would misrepresent a settled decision as an unresolved one, so none of the three is entered
here. This is unchanged by NT16.

**Carve-out, corrected as of NT16 (v2.0): RESOLVED entries are the one exception to "decided matters are
absent."** Version 1.0 of this section additionally said that decided or otherwise-settled matters were
"likewise absent by design, not by oversight." That statement described two kinds of matter: PREF rows that
were `DECIDED` from the outset and never carried an `OPEN-NN` token (they were never assigned a register entry
to begin with), and the three `DEFERRED` matters above. It did **not**, and could not, describe a third kind
that exists only as of this NT16 update: the nine items that were minted here as `OPEN-NN`, given their own
register heading, and have now been ruled on by RC (OPEN-08, 09, 10, 11, 15, 16, 17, 18, 19). Those nine keep
their heading, their original Question, and now their Status/Ruling/Supersedes, permanently, in this register
— they are not absent, and must not be treated as if they had been removed once resolved. Deleting a resolved
entry would destroy the audit trail of what was asked and how RC answered; the entire value of a register like
this one is that a downstream reader can find both the question and the answer in the same place, not just the
answer in isolation, or worse, no visible trace that the question was ever asked at all.

**Decided or otherwise-settled matters that never carried an `OPEN-NN` token are still absent by design**, not
by oversight. Two examples worth naming explicitly, since both could plausibly be mistaken for open questions:

- **TI-84 regression** (`PREF-08.7`) — RC excluded this outright from the required-skills list. This is a
  `DECIDED` negative ("regression is explicitly omitted"), not an undecided matter like matrices (OPEN-01
  above) — the two are easy to conflate but RC's text treats them differently. It never carried an `OPEN-NN`
  token and is not entered here.
- **The 40% completion gate's inclusivity** (`PREF-03.5`) — RC settled this exactly, from the outset: a
  completion value of precisely `0.40` takes the `max` branch, not the average branch. Only the *rounding* of
  the completion ratio before that comparison was ever open (OPEN-08 — now `RESOLVED by RC 2026-07-24`, see the
  entry above); the gate's own inclusivity was never in question and still does not appear in this register as
  an open item — it is, and always was, `DECIDED` in `RC_TEACHER_PREFERENCE_RECORD.md`, and never had its own
  `OPEN-NN` heading to retain.

Every status-`DECIDED` sub-decision in `RC_TEACHER_PREFERENCE_RECORD.md` (PREF-01 through PREF-14) that never
carried an `OPEN-NN` token is, likewise, absent from this register on the same basis: it is binding, not
pending, and was never assigned a register entry in the first place. This is distinct from the four rows this
NT16 update flipped from `OPEN` to `DECIDED` in place (PREF-03.10, PREF-03.11, PREF-04.7, PREF-04.8) and the
five new `DECIDED` rows it added (PREF-03.12 through .14, PREF-06.10, PREF-01.11) — those nine carry an
`OPEN-NN` token and DO remain here, marked `RESOLVED by RC 2026-07-24`, per the carve-out above.

## Changelog — NT16 (v2.0)

- **2026-07-24 (v2.0).** RC issued nine rulings resolving OPEN-08, OPEN-09, OPEN-10, OPEN-11, OPEN-15,
  OPEN-16, OPEN-17, OPEN-18, and OPEN-19. This register moves from 19 open / 0 resolved (v1.0) to 10 open / 9
  resolved (v2.0) — see the headline count near the top and the `Status` column added to the summary table.
  All 19 `OPEN-NN` headings and their original `Question` text are unchanged and unremoved. Each of the nine
  resolved entries gained, in place: a `Status` line (`RESOLVED by RC 2026-07-24`), a `Ruling` block carrying
  RC's substance, and a `Supersedes` note naming the prior provisional/placeholder behavior it replaces; each
  entry's original "Why it is open" and "Consequence if left open" sections were retitled with a
  "(historical)" label and left otherwise intact rather than deleted, so the reasoning that made the item open
  in the first place remains legible. OPEN-17's entry additionally preserves its cross-reference to
  `desk_state_model.v2.json`'s resolved-item identifier **U1**; OPEN-18's entry preserves **U2**/**U3** and
  states that T7/T11/T12/T13 were promoted from `transitions.provisional` (now retired/empty) into
  `transitions.legal`, while T3 and X3 were confirmed rather than newly created. OPEN-12 and OPEN-13 remain
  `OPEN` and unchanged in status; each gained an "Interim operating rule (NT16 ... — NOT a resolution)"
  paragraph recording RC's interim rule (deterministic cases may be accepted; unsupported symbolic/tolerance
  cases route to teacher review, never auto-fail) without closing either item. The "Purpose and how to use
  this register" section and the "Not in this register, and why" section were both rewritten to state the
  corrected discipline: RESOLVED entries are retained (with status), not deleted, alongside the unchanged rule
  that DEFERRED items and never-`OPEN-NN` `DECIDED` matters remain excluded. The ten items RC did not rule on
  are unchanged: OPEN-01 through OPEN-07, OPEN-12, OPEN-13, OPEN-14.
