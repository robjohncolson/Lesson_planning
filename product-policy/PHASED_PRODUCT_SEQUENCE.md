# Phased Product Sequence

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

## Scope and a hard constraint on this document's own form

Deliverable D6. This document sequences the product build across the areas RC has decided (`PREF-01`
through `PREF-14`) into ordered phases, and states the dependency that justifies each phase's position.

**This document contains no calendar dates, no durations, no sprint counts, no "Q1/Q2"-style labels, and no
week/period estimates for the phases below — and deliberately so.** `PREF-13.2` records that RC herself
designates today's/next lesson; there is no fixed calendar driving sequencing. A phased plan that attached
dates or durations to Phase A/B/C/D would silently reassert a fixed calendar RC's own pacing decision (§7
below) rejects. What follows is **sequence and dependency order only**: which phase must exist before which
other phase can be built, and why — never when.

Substance traces to `RC_TEACHER_PREFERENCE_RECORD.md`. Where this document makes a sequencing or
architectural choice RC's text does not itself state, that choice is flagged inline, so a later reader can
separate RC's decisions from this document's own elaboration. The single largest such elaboration is §3
(reward seams) — flagged there in detail, and flagged again here so it is not missed: **RC decided that
reward seams must be preserved (`PREF-10.11`); RC did not specify what those seams are.** Naming them
concretely is this document's job, not a restatement of RC's words.

---

## 1. Ordering principle

**Academic core first.** `PREF-10.9` states plainly that the candy/reward economy need not block the first
academic release. That is the single ordering principle this whole document applies: build and ship the
academic core — the parts of the product a student needs in order to do graded mathematical work and have it
count correctly — before building the reward/personality layer that makes the Desk fun to return to. Candy
is not on the critical path to a working gradebook; a working gradebook is a prerequisite for everything else
in this sequence.

This principle does **not** extend to ELL/accessibility. RC marked `PREF-12` **required**, with no language
suggesting it is deferrable or a later add-on — vocabulary support, worked examples, simpler-language
explanations preserving mathematical demand, Chromebook-first/mobile-adaptive delivery, and tolerance for
flaky connectivity with paper-first fallback are all `DECIDED`, not `OPEN` or `DEFERRED`. Because the student
population this platform serves is explicitly ELL-heavy (see `CLAUDE.md`'s class-context notes), a first
academic release that did not carry `PREF-12` would not be a working academic core for these students — it
would be a working academic core for a different, non-representative population. §2.6 below states this
explicitly rather than leaving it implied.

---

## 2. Phase A — academic core

Phase A is the first release. It is the smallest set of components that lets a student do graded work on the
Desk, have that work captured and evaluated, have grades computed correctly, and have the result reach
Schoology as RC's Area 5 decisions require. Nothing in Phase A is reward/personality content (§3, §4) —
that is deliberately excluded here, not merely unmentioned.

| # | Component | Governing deliverable | RC decision area(s) | Dependency prerequisites |
|---|---|---|---|---|
| 2.1 | Desk navigation & lesson-state model | `DESK_STATE_MODEL.md` (D4) | `PREF-01`, `PREF-06`, `PREF-13`, `PREF-14` | None within Phase A — this is the foundational layer. It depends only on lesson identity already established by the closed content-readiness/DOK/alias pipeline (`PREF-14.4`–`.7`, cited, not reopened here). |
| 2.2 | Student packets | Pre-existing content infrastructure (`tex/*.tex`/`.pdf`, `questionbank/registry.jsonl`, `qb.py`) — **no new NT15 deliverable governs this component; it is cited, not created, by this tranche** | `PREF-02`, `PREF-14` | Desk navigation (2.1), for the lesson identity/state a packet attaches to. |
| 2.3 | Answer capture | `ANSWER_EQUIVALENCE_CONTRACT.md` (D5) | `PREF-02`, `PREF-07` | Desk navigation (2.1) — a lesson must be `released`/`today` before capture is meaningful — **and** student packets (2.2), whose teacher-designated-answer fields are what capture operates against. |
| 2.4 | Grading pipeline | `GRADING_POLICY_SPEC.md` (D2) | `PREF-03`, `PREF-04` | Answer capture (2.3) only — the pipeline reads item-level, server-authoritative evidence and teacher designation directly (`PREF-03.9`, `PREF-04.6`) and computes completion percentage from that evidence itself. It does **not** read the Desk's `completed` tile state as an input — see the dependency-direction note immediately below the table. |
| 2.5 | Schoology projection | `SCHOOLOGY_PROJECTION_CONTRACT.md` (D3) | `PREF-05`, `PREF-11` | Grading pipeline (2.4), whose aggregates and quarter grade are the values projected, **and** Desk navigation (2.1), whose lesson states gate which assignments are live-projected (D3 §3). This is a release-gating dependency only (which lessons are `unreleased`/`skipped`/`optional-catalog` vs. live) — it is not a grade-computation dependency, and is unrelated to the note below. |
| 2.6 | ELL / accessibility | No single governing deliverable — this is a **cross-cutting requirement**, not a separate build step, and is threaded through 2.1–2.5 simultaneously | `PREF-12` | None separately. It is not sequenced after 2.1–2.5; it is a required property *of* 2.1–2.5 (Desk navigation's UI, packets' language and worked examples, answer capture's interaction surface, and Schoology-facing text must all carry it). A Phase A release missing it is not "Phase A minus an optional feature" — it is an incomplete Phase A. |

**Dependency direction for the grading pipeline, stated explicitly.** The grading pipeline's input is
item-level, server-authoritative teacher designation and evidence — `PREF-03.9` and `PREF-04.6` are explicit
that server policy and teacher designation are authoritative and that clients never determine designation or
official credit. Completion percentage and the quarter-rule branch (`GRADING_POLICY_SPEC.md` §2–§3) are
computed from that evidence **directly**, never by reading the Desk's `completed` tile state. The Desk's
`completed` state (D4 transitions T5/T9) is instead a **downstream projection** of that same evidence — it
renders what the grading pipeline already computed; it is not a source the grading pipeline reads. This
inversion matters concretely because of `OPEN-17` (whether a within-quarter retake reopens the `completed`
tile — now RESOLVED: `completed` is DECIDED terminal at the Desk-tile layer, and a within-quarter retake is
an orthogonal activity/affordance attached to the completed lesson, with its implementation deferred to the
work packages, never a Desk-state transition). Consistent with the dependency direction stated here, RC's
answer to `OPEN-17` changes only that navigation-layer affordance — it never changes completion-percentage
or quarter-branch computation, because neither one reads tile state in the first place; this is exactly the
invariant that makes RC's answer safe to build against without touching the grading pipeline's arithmetic.
This mirrors
`PROGRAM_DOSSIER.md` §15 item 4 (server ledger and stable identity are authoritative; browser/projection state
is cache only, never a source of record): the Desk tile is exactly that kind of projection, and a navigation-
layer decision must never be able to leak into official grade computation by way of a reversed dependency.

**Why this is a phase, not a flat feature list.** Each row genuinely depends on the ones above it being in
place — this is not an arbitrary presentation order. A grading pipeline cannot compute a WORK aggregate
before there is answer capture producing evaluated outcomes to feed it; Schoology cannot project a quarter
grade that does not yet exist. ELL/accessibility is the one exception to strict sequencing precisely because
it is not a downstream consumer of the others — it is a quality bar every one of them must independently meet.

**What Phase A explicitly does not include:** the candy/per-question economy, completion calendar populated
with live reward state, streak counting, TI-84 trainer, and Equation Lab are all out of scope for this phase
(§3, §5, §6 below). Phase A's obligation toward the reward economy is narrower and is the subject of the next
section: leave the seams that let Phase B be built later without reopening Phase A's code.

---

## 3. REWARD SEAMS — what Phase A must preserve for Phase B

**This is the most important section of this document.** `PREF-10.11` requires that "reward seams must be
preserved in the academic-release architecture so the later candy implementation needs no rework." RC's text
states the requirement; it does not specify the seams themselves. **Everything below this paragraph in §3 is
this document's engineering elaboration of that requirement, not a restatement of anything RC said.** A later
reader who wants to know exactly what RC decided about reward seams should read `PREF-10.11` alone — one
sentence. Everything more specific than that sentence originates here, in NT15, and is offered so that Phase
A has something concrete to build against, not because RC dictated this particular design.

### 3.1 Per-question evaluation-outcome event

- **Emitted by:** the answer-evaluation pipeline (`ANSWER_EQUIVALENCE_CONTRACT.md`'s Tier 1–4 model), once
  per submitted attempt, **regardless of which tier resolved it and regardless of the verdict**.
- **Carries:** student identity (the server-ledger stable identity per `PROGRAM_DOSSIER.md` §15 item 4 — never
  a browser-cache identity), item identity (the bank `item_uid`), lesson identity, a monotonic per-student
  per-item attempt number, the Tier verdict (`auto-correct` / `auto-incorrect` / `route-to-review` / `unknown`
  — the vocabulary D5 already defines), and whether the item is currently teacher-designated for official
  credit (a factual flag, carried as data — not a judgment the event itself makes).
- **Invariant it must respect:** the event is a **record of fact** — "an evaluation happened, and here is its
  outcome" — never a reward decision. Whether a given outcome *should* earn candy is entirely Phase B's
  business, undesigned as of this document. The reason this event must exist in Phase A even though nothing
  reads it yet is exactly what `PREF-10.11` is protecting against: if this event does not exist until Phase B
  is built, building Phase B would require reopening Phase A's evaluation pipeline to add it — the rework RC
  explicitly ruled out.

### 3.2 Per-day participation-evaluated event

- **Emitted by:** the grading pipeline's participation computation (`GRADING_POLICY_SPEC.md` §4,
  `PREF-04.1`/`.2`), once per student per class day.
- **Carries:** student identity, a lesson-scoped class-day identifier (a cadence unit, not a calendar date —
  consistent with `PREF-13.2`'s "no fixed calendar"), and the computed participation value (`1.0` / `0.0` /
  `UNKNOWN` per D2 §6).
- **Invariant it must respect:** this event mirrors the same PREF-04.1/.2 computation the grading pipeline
  already performs for official WORK-aggregate purposes — it is not a second, reward-side re-derivation of
  "did the student participate today." A streak feature (Phase B) consuming this event must accept what it
  says; it may never override or re-decide participation, because that determination is server/grading-policy
  authoritative (`PREF-03.9`, `PREF-04.6`), not something a reward subsystem gets a vote on.

### 3.3 Lesson-completed event

- **Emitted by:** the Desk state model's completion transition (`DESK_STATE_MODEL.md` transitions T5/T9:
  `released`/`today` → `completed`).
- **Carries:** student identity, lesson identity, topic identity (supporting `PREF-11.3`'s "organized by topic
  and lesson").
- **Invariant it must respect:** fires only from a genuine `completed` transition backed by server-ledger-
  verified evidence (D4 §2) — never from a client-side guess, and never retroactively fabricated to "fill in"
  a calendar for a student who has not actually completed the lesson.

### 3.4 A stable, append-only, replayable event stream

- The three event types above are not three unrelated channels; they compose **one** event stream with stable
  ordering and append-only writes. This is the reward-facing architectural analogue of
  `PROGRAM_DOSSIER.md` §15 item 7 ("official evidence is append-only") — that item governs the underlying
  academic evidence itself; this stream is a derivative feed built from that evidence, and it inherits the
  same append-only discipline for the same reason: a feed that could be edited or replayed inconsistently
  would let reward state silently drift from the academic facts it is supposed to reflect.
- **Replayability is the point.** Phase B's reward economy (candy balances, streak counters) must be
  reconstructible from scratch by replaying this stream from its start — no special one-time seeding step,
  and no write access to the academic tables that produced it. If the reward economy's state is ever
  suspected of drifting, replaying the stream is the recovery path, not a manual patch to reward data.
- **Invariant it must respect — one-directional flow.** Phase A's academic core writes to this stream. Phase
  B's reward economy only ever reads or subscribes. There is no path in this design by which reward-economy
  code writes back into the stream or into the underlying academic evidence it is derived from.

### 3.5 Read-only projection interface for streaks and the completion calendar

- **Exposed by:** Phase A's academic core, over the lesson-completed and participation-evaluated facts (§3.2,
  §3.3), so that Phase B's completion calendar and streak logic can be built as *consumers* of this interface
  rather than needing their own redundant copy of "was lesson X completed on day Y" logic.
- **Invariant it must respect — the one `PREF-10.11` most directly protects:** **reward state is never a
  source of academic truth.** If a reward-side streak counter or calendar display ever disagrees with the
  academic evidence about whether a day counts as complete/participated, the academic evidence wins,
  unconditionally, and the reward-side value is corrected to match it — never the reverse. This is the direct
  extension of `PREF-03.9` ("clients never determine designation or official credit") to the reward layer: a
  reward subsystem is architecturally a *consumer* of academic fact, never a co-author of it. **Reward
  computation must never write to official evidence, under any circumstance** — this is not a performance
  optimization or a "nice to have" separation, it is the property that keeps a future candy-economy bug or a
  student manipulating client-side reward state from ever being able to touch a grade.

### 3.6 What Phase A does NOT build

To say it plainly, so it cannot be mistaken for partial reward-economy delivery: **the candy/per-question
economy itself (`PREF-10.4`) is not built in Phase A.** No candy balance exists. No candy-earning rule exists.
No completion-calendar UI populated with real reward state exists. No streak-counting logic exists. What
Phase A ships, per §3.1–3.5, is solely the *capability* for Phase B to be built later without modifying Phase
A's evaluation pipeline, grading pipeline, or Desk state model. The seams are plumbing; the economy that will
eventually flow through them is entirely Phase B's content.

---

## 4. Phase B — reward economy activation

Builds the candy/per-question economy, the completion calendar (populated with real reward state, on top of
the read-only projection from §3.5), and streaks (`PREF-10.2`/`.3`/`.4`) — the parts of `PREF-10` RC decided
to keep, on top of the retro System-7 personality (`PREF-10.1`, already-existing Desk UI theme, not newly
built here).

- **Depends on:** Phase A's reward seams (§3) existing, stable, and already integrated into the evaluation
  and grading pipelines. Phase B is a pure consumer of §3's stream and projection interface — it should not
  require touching Phase A's evaluation/grading/Desk-state code at all, which is exactly the test of whether
  §3 was designed correctly.
- **Sequencing relative to Phase A:** `PREF-10.9` (candy need not block the first academic release) and
  `PREF-10.10` (candy is phased in shortly after) together fix that Phase B follows Phase A. **Exact timing
  detail is explicitly unresolved — `OPEN-14`.** This document does not narrow that open item; it states only
  that Phase B comes after Phase A in sequence, never a "how soon" value.
- **What Phase B explicitly excludes:** gifting, Tetris (mini-game), leaderboards, and celebration noise
  (`PREF-10.5`–`.8`) are RC's explicit "do not build" list for the reward/personality layer. They are not
  part of Phase B, and — per §7 below — they are not scheduled into any phase at all.

---

## 5. Phase C — TI-84 trainer

Scope per `PREF-08`: the five decided required skills — graphing/window selection (`PREF-08.1`), tables
(`PREF-08.2`), zeros/intersections/extrema (`PREF-08.3`), sequences (`PREF-08.4`), and solver (`PREF-08.5`).
Trainer exercise URLs must support stable, lesson-specific deep links (`PREF-08.9`), and exercises are
designated extra credit rather than main assessment (`PREF-08.8`, realized as the `+0.5` participation credit
already specified in `GRADING_POLICY_SPEC.md` §4, `PREF-04.3`).

- **Depends on:** the grading pipeline's extra-credit mechanism (`GRADING_POLICY_SPEC.md`, `PREF-04.3`) —
  Phase C exercises need somewhere to deposit their `+0.5` credit, and that mechanism is Phase A content, not
  new work — and the Schoology deep-link contract (`SCHOOLOGY_PROJECTION_CONTRACT.md` §5, `PREF-08.9`), which
  already specifies the `a2_activity_key` / `schoology_url_template` pattern this phase's exercises must use.
- **Does not depend on Phase B.** Nothing about the TI-84 trainer's required skills, deep links, or
  extra-credit designation reads from or writes to the reward-seam stream (§3). Its position as "Phase C,"
  after "Phase B," in this document's presentation order is **this document's own sequencing choice**, not an
  RC-mandated dependency — RC's text does not say TI-84 must follow the reward economy, only that it must
  follow the academic core's extra-credit and deep-link mechanisms (both Phase A content). A future planner
  could build Phase C in parallel with, or even before, Phase B without violating anything RC decided.
- **Matrices are unresolved** (`OPEN-01`) — whether matrices belong among the required skills is not decided;
  this phase's scope is the five skills above until RC resolves it.
- **Regression is omitted — not deferred, not open.** `PREF-08.7` is a `DECIDED` exclusion: RC excluded
  regression from the required-skill set outright. This is different from the `DEFERRED` items in §7 below,
  which RC chose not to build *for now*; regression is simply not part of this scope at all.

---

## 6. Phase D — Equation Lab

Scope per `PREF-09`: narrow initial coverage of polynomial identities (`PREF-09.1`) and quadratic equations
(`PREF-09.2`). Primary interaction is answer/simplified-form entry (`PREF-09.3`) rather than full-derivation
entry, with unlimited retries (`PREF-09.4`) and immediate feedback (`PREF-09.5`). Its role is
reinforcement/extra-credit, explicitly **not** main assessment (`PREF-09.7`) — the same `+0.5` extra-credit
mechanism as Phase C (`PREF-04.4`).

- **Depends on:** the grading pipeline's extra-credit mechanism (`PREF-04.4`) and the same Schoology deep-link
  contract pattern used for TI-84 (`SCHOOLOGY_PROJECTION_CONTRACT.md` §5, whose per-entity table already
  includes an Equation Lab extra-credit row).
- **Does not depend on Phase B or Phase C.** As with Phase C, its position after Phase C in this document's
  presentation order is this document's sequencing choice, not an RC-stated dependency; Equation Lab's actual
  prerequisites are Phase A's extra-credit mechanism and deep-link contract only.
- **Step-by-step enforcement is deferred**, not part of this phase's scope at all (`PREF-09.6` — see §7).
- **AI provider choice is unresolved** (`OPEN-02`) — this phase's answer/simplified-form checking cannot be
  fully specified until that choice is made; the equivalence-authority model it must obey either way is
  `PREF-07` / `ANSWER_EQUIVALENCE_CONTRACT.md`, already binding regardless of provider.

---

## 7. Deferred — explicitly not scheduled into any phase

The following are RC's own decisions **not** to build right now. They are recorded here for completeness,
exactly as they appear in `RC_TEACHER_PREFERENCE_RECORD.md`, and are deliberately **absent** from Phase A
through Phase D above — this section does not assign them a future phase, a "Phase E," or any other place in
the sequence. Scheduling them, even provisionally, would misrepresent RC's decision as merely postponed
rather than declined for now.

| Item | Canonical ID | Status |
|---|---|---|
| Step-by-step enforcement in Equation Lab | `PREF-09.6` | `DEFERRED` |
| Gifting | `PREF-10.5` | `DEFERRED` |
| Tetris (mini-game) | `PREF-10.6` | `DEFERRED` |
| Leaderboards | `PREF-10.7` | `DEFERRED` |
| Celebration noise | `PREF-10.8` | `DEFERRED` |
| Intervention / makeup / enrichment subsystems | `PREF-13.6` | `DEFERRED` |

These are distinct from the `OPEN-NN` items referenced throughout this document (e.g. `OPEN-01`, `OPEN-02`,
`OPEN-14`): `OPEN` means RC has not yet settled a question; `DEFERRED` means RC settled the question, and the
answer is "not now." Nothing in this document treats the two the same way, and nothing above schedules a
`DEFERRED` item into a phase on the theory that it is merely waiting its turn.

---

## 8. Dependency graph

Textual only — no dates, no durations, no phase-length estimates.

```
Phase A — academic core
 |
 +-- Desk navigation & lesson-state model            (D4 / PREF-01, PREF-06, PREF-13, PREF-14)
 |     no Phase-A dependency; foundational
 |
 +-- Student packets                                 (pre-existing pipeline / PREF-02, PREF-14)
 |     depends on: Desk navigation (lesson identity)
 |
 +-- Answer capture                                  (D5 / PREF-02, PREF-07)
 |     depends on: Desk navigation + student packets
 |
 +-- Grading pipeline                                (D2 / PREF-03, PREF-04)
 |     depends on: Answer capture (item-level evidence + teacher designation)
 |     NOT the Desk's `completed` tile state (that tile is a downstream projection of
 |     this pipeline's evidence, not an input to it — OPEN-17 invariant, now RESOLVED, see S2.4)
 |
 +-- Schoology projection                            (D3 / PREF-05, PREF-11)
 |     depends on: Grading pipeline + Desk navigation (release-state gating only,
 |     not a grade-computation dependency)
 |
 +-- ELL / accessibility (PREF-12)
       cross-cutting; required inside every component above, not a downstream step

 => Phase A also emits the reward-seam event stream (S3.1-S3.5), consumed by nothing yet.

Phase B — reward economy activation                  (PREF-10.2/.3/.4; phased per PREF-10.9/.10; timing OPEN-14)
 depends on: Phase A's reward seams (S3) only
 does not depend on: Phase C, Phase D

Phase C — TI-84 trainer                               (PREF-08; matrices OPEN-01; regression excluded PREF-08.7)
 depends on: Phase A's grading-pipeline extra-credit mechanism (PREF-04.3)
           + Phase A's Schoology deep-link contract (PREF-08.9)
 does not depend on: Phase B

Phase D — Equation Lab                                (PREF-09; AI provider OPEN-02)
 depends on: Phase A's grading-pipeline extra-credit mechanism (PREF-04.4)
           + Phase A's Schoology deep-link contract
 does not depend on: Phase B, Phase C

Deferred (not scheduled): PREF-09.6, PREF-10.5-.8, PREF-13.6
```

The only strictly RC-mandated cross-phase ordering constraints in this graph are: (1) Phase A precedes
Phase B (`PREF-10.9`/`.10`), and (2) Phase C and Phase D each depend on specific Phase A components (the
extra-credit mechanism and the deep-link contract) rather than on Phase B or on each other. The letter
ordering B-then-C-then-D used for presentation in §4–§6 is this document's own organizational choice, flagged
here so it is not mistaken for a dependency RC herself stated.

---

## 9. Pacing constraint

`PREF-13.3`–`.5` are explicit: "~1 topic/quarter" is a **temporary planning assumption only**, not a rule this
or any downstream document may hard-code; four topics must not be hard-coded; a fixed annual pace must not be
hard-coded. This document's phase list (A/B/C/D) is a **dependency ordering**, not a pacing plan, and carries
no assumption about how many topics, lessons, or periods elapse within or between phases. `PREF-13.2` remains
in force throughout every phase above: RC designates today's/next lesson directly, lesson by lesson, with no
fixed calendar driving sequencing — regardless of which product phase (A, B, C, or D) happens to be active at
the time. A future document that attaches topic counts or a fixed pace to any phase in this sequence would
contradict `PREF-13.3`–`.5`, not extend them.

---

## Provenance summary

- Sections 1, 2 (component list only, not the dependency reasoning), 4, 5, 6, 7, and 9 restate RC's own
  decision text (`PREF-01`, `PREF-03`, `PREF-04`, `PREF-05`, `PREF-08`, `PREF-09`, `PREF-10.1`–`.4` and
  `.9`–`.10`, `PREF-11`, `PREF-12`, `PREF-13`) organized into a sequence; they do not add substance RC did not
  state.
- The **dependency reasoning** connecting components (why 2.3 needs 2.1+2.2, why 2.5 needs 2.4, etc.), the
  **letter ordering of Phase C relative to Phase D and both relative to Phase B**, and — most significantly —
  **all of §3's specific reward-seam design** (the five named seams, their fields, their emitters, and their
  invariants) are this document's own engineering elaboration of `PREF-10.11`, offered because RC's text
  states the requirement to preserve seams without specifying what they are. None of this elaboration is
  attributed to RC; it is NT15's contribution, open to correction or replacement without touching any
  `PREF-NN` or `OPEN-NN` id as recorded in `RC_TEACHER_PREFERENCE_RECORD.md`.
- This document contains no calendar dates, no durations, no sprint counts, no "Q1/Q2" labels, and no
  week/period estimates anywhere in its phase or dependency content, consistent with the hard rule stated in
  the Scope section above.

---

## Changelog — NT16 (v2.0)

RC has since ruled on `OPEN-17`, one of the items recorded in `OPEN_DECISIONS_REGISTER.md`. This document's
phase and dependency substance is otherwise unchanged — the ordering principle (§1), Phase A's component
table (§2), the reward-seam design (§3), Phases B through D (§4–§6), the deferred-item list (§7), the
dependency graph (§8), and the pacing constraint (§9) are unaffected. The single substantive update is to
§2's dependency-direction note and the corresponding line in §8's dependency graph: `OPEN-17` is no longer
an open navigation-affordance question. RC's ruling settles it as DECIDED policy — `completed` remains
terminal at the Desk-tile layer, and a within-quarter retake is an orthogonal activity/affordance attached
to the completed lesson, with implementation deferred to the work packages — never a Desk-state transition,
and never a path by which a navigation-layer decision could reach completion-percentage or quarter-branch
computation.
