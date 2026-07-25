# Desk Lesson-State Model

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

## 1. Scope

This document specifies the Desk's per-lesson state model: the seven canonical lesson states, the legal and
illegal transitions between them, the two-view visibility matrix, the optional-catalog rule, and the
reliability rules governing `completed` and `temporarily-unavailable`. It implements RC Area 1 (`PREF-01`),
with reliability (`PREF-06`), pacing (`PREF-13`), and content-boundary (`PREF-14`) constraints folded in where
they bear on lesson state.

Substance traces to `RC_TEACHER_PREFERENCE_RECORD.md` (the `PREF-NN.M` decision text quoted throughout this
document) and does not re-derive or reopen anything decided there, in `PROGRAM_DOSSIER.md`, or in the
closed content-readiness/DOK/alias decisions. Machine-readable companion: `desk_state_model.v2.json`.
Tests: `test_desk_state_model.py`.

**v2.0 supersedes v1.0.** RC issued nine rulings on 2026-07-24 resolving nine previously-OPEN items; this
package implements two of them, OPEN-17 (retakes) and OPEN-18 (skip transitions). Both are now DECIDED, not
open. See §8 and the `## Changelog — NT16 (v2.0)` section at the end of this document for the full history —
nothing in v1.0's OPEN-17/OPEN-18 treatment has been silently dropped; it is preserved there as superseded.

## 2. The seven lesson states

Exactly these seven, spelled exactly this way — no eighth state, no renaming:

`today` · `released` · `unreleased` · `skipped` · `optional-catalog` · `completed` · `temporarily-unavailable`

| State | Layer | Meaning |
|---|---|---|
| `today` | navigation | The teacher-designated lesson for the current class day — the Desk's primary front door (PREF-01.2). A lesson must be released to be `today`; designating a not-yet-released lesson as today implicitly releases it in the same action. |
| `released` | navigation | Teacher has made the lesson available. Openable and workable, including work-ahead, whether or not it also carries the `today` designation (PREF-01.4, PREF-01.5). |
| `unreleased` | navigation | The default state of every lesson at creation, before any teacher release action. Hidden/unavailable to students (PREF-01.8). |
| `skipped` | navigation | Teacher has designated this lesson as not being pursued in the normal sequence. Grey and inert (PREF-01.9). |
| `optional-catalog` | navigation | A content-ingestion-time classification (e.g. Lesson 4-1, record `nt14-ingest-4-1-2026-07-23`) that keeps a lesson off the normal student path — both views — until a teacher explicitly assigns it (PREF-01.10, PREF-14.1/.2). |
| `completed` | evidence | The student has server-ledger-verified evidence satisfying this lesson's teacher-designated completion criteria (feeds PREF-03's completion-percentage mechanic). **DECIDED terminal** (RC's 2026-07-24 ruling, OPEN-17): zero legal exit transitions — never demoted by an evidence-source outage, a teacher action, or a within-quarter retake. |
| `temporarily-unavailable` | evidence | The authoritative evidence source needed to determine this lesson's completion status is unreachable. Renders as UNKNOWN, never zero. Never applies to a lesson already known-`completed`. |

**`completed` is DECIDED terminal — the retake affordance is orthogonal.** RC's 2026-07-24 ruling settles
OPEN-17: `completed` remains terminal for the lesson tile, full stop — this is now decided policy, not the
conservative placeholder v1.0 carried pending RC's answer. A within-quarter retake (PREF-06.4: "retakes are
allowed within the quarter") is an **orthogonal** activity/affordance attached to the already-completed
lesson. It never demotes completion, never relocks the tile, never erases history, and never alters the
grading engine via navigation state — retaking an assessment is an assessment-layer event, not a Desk
state-machine transition. `completed` keeps its zero legal exit transitions unchanged. The retake affordance's
own implementation (where the retake action lives in the UI, how retake attempts are scored) is **deferred to
later work packages** (D8) — this document fixes only that it must never touch `completed`'s Desk-tile state.
See the machine-readable `retake_affordance` object in `desk_state_model.v2.json`.

**Two-layer structure.** As `RC_TEACHER_PREFERENCE_RECORD.md` notes under PREF-01.1: five of the seven states
(`today`, `released`, `unreleased`, `skipped`, `optional-catalog`) are directly-named navigation/release-layer
facts from RC's Area 1 text — set once per lesson, shared by every student in the section. The other two
(`completed`, `temporarily-unavailable`) are per-student evidence-layer states required for the model to stay
internally consistent with PREF-03 (completion %) and PREF-06 / dossier §15 — they are not independently new
navigation rules RC stated in Area 1.

**State derivation (rendering precedence).** For Desk rendering, a (lesson, student) pair resolves to exactly
one of the seven states via this precedence order, evaluated top to bottom, first match wins:

1. `completed`
2. `temporarily-unavailable`
3. `today`
4. `skipped`
5. `optional-catalog`
6. `released`
7. `unreleased`

`completed` is checked first so a later evidence-source outage can never downgrade it (dossier §15 item 2).
`temporarily-unavailable` is checked next, before any curriculum-layer fact, so an outage overlays whichever
curriculum state currently holds without altering that underlying curriculum classification — recovery
(§3, T16/T17) restores rendering to that same underlying curriculum state, not a default.

## 3. Transition table

Two states — `unreleased` and `optional-catalog` — are **initial/resting classifications**, not normally
entered via a Desk transition: `unreleased` is the default for every newly created lesson; `optional-catalog`
is the default for content ingested with the NT14-style marker. Every other state is reached only by an
explicit teacher action or a server-verified evidence event.

### 3.1 Legal transitions (decided)

This table is **decided** — every row traces to RC's text (directly, via the general "teacher
release/designation drives most transitions" principle for the ordinary release/today/completion/recovery
cases, or via RC's 2026-07-24 ruling on OPEN-18). As of v2.0, **all five skip-related transitions (T3, T7,
T11, T12, T13) are decided policy** — nothing skip-related remains provisional; see §3.1b for the (now empty)
retirement note.

| ID | From | To | Trigger | Actor | Basis |
|---|---|---|---|---|---|
| T1 | `unreleased` | `released` | Teacher releases the lesson | teacher | PREF-01.4, PREF-01.8, PREF-13.2 |
| T2 | `unreleased` | `today` | Teacher designates as today's lesson (implicitly releases) | teacher | PREF-13.2 |
| T3 | `unreleased` | `skipped` | Teacher designates as skipped, without ever releasing | **teacher_only** | PREF-01.9, PREF-13.2 — **RC-confirmed** 2026-07-24 (OPEN-18): already legal in v1.0, this ruling settles it as decided, not a new grant |
| T4 | `released` | `today` | Teacher promotes an already-released lesson to today | teacher | PREF-13.2 |
| T5 | `released` | `completed` | Server-ledger evidence satisfies completion criteria | system_evidence | PREF-03.4 |
| T6 | `released` | `temporarily-unavailable` | Evidence source becomes unreachable | system_evidence | PREF-06.6, PREF-06.9 |
| T7 | `released` | `skipped` | Teacher retroactively designates as skipped | **teacher_only** | PREF-01.9, PREF-13.2 — **promoted from provisional** by RC's 2026-07-24 ruling (OPEN-18) |
| T8 | `today` | `released` | Teacher moves the today designation elsewhere | teacher | PREF-01.6, PREF-13.2 |
| T9 | `today` | `completed` | Same as T5, while still marked today | system_evidence | PREF-03.4 |
| T10 | `today` | `temporarily-unavailable` | Same as T6, while still marked today | system_evidence | PREF-06.6, PREF-06.9 |
| T11 | `today` | `skipped` | Teacher designates as skipped **before completion** — see precondition below | **teacher_only** | PREF-01.9, PREF-13.2 — **promoted from provisional** by RC's 2026-07-24 ruling (OPEN-18) |
| T12 | `skipped` | `released` | Teacher reverses a prior skip decision | **teacher_only** | PREF-13.2 — **promoted from provisional** by RC's 2026-07-24 ruling (OPEN-18) |
| T13 | `skipped` | `today` | Same question as T12, direct to today | **teacher_only** | PREF-13.2 — **promoted from provisional** by RC's 2026-07-24 ruling (OPEN-18) |
| T14 | `optional-catalog` | `released` | **Explicit** teacher assignment | teacher | PREF-01.10, PREF-14.1/.2 |
| T15 | `optional-catalog` | `today` | Same as T14, direct to today | teacher | PREF-01.10, PREF-14.1/.2 |
| T16 | `temporarily-unavailable` | `released` | Evidence source recovers; reconciled evidence shows not-yet-complete | system_evidence | PREF-06.6, PREF-06.9 |
| T17 | `temporarily-unavailable` | `today` | Same as T16, if the lesson still held the today designation underneath | system_evidence | PREF-06.6, PREF-06.9 |
| T18 | `temporarily-unavailable` | `completed` | Evidence source recovers; reconciled evidence shows it was already complete | system_evidence | PREF-06.6, PREF-06.9 |

**T11's precondition — pre-completion only.** T11 (`today` → `skipped`) is legal **only while the lesson has
not yet reached `completed` for the student in question** (machine-readable `precondition` field on T11 in
`desk_state_model.v2.json`: `student_completion_state != 'completed'`). A completed lesson can **never** reach
`skipped` under any circumstance — see illegal transition X3 in §3.2, which is the guard that enforces this
precondition. If the precondition is ever violated (i.e., the lesson is already `completed`), T11 simply does
not apply; X3 governs instead.

**Every skip transition is teacher-only.** T3, T7, T11, T12, T13 all carry `"actor": "teacher_only"` and
`"student_may_initiate": false` in the JSON. **Students cannot initiate skip or unskip under any
circumstance** — see the dedicated skip-authority note in §9.

**`completed`'s transition entry — DECIDED terminal (OPEN-17 resolved).** `completed` has no row above as a
"From" state: this model defines **zero legal exit transitions** out of `completed`. This is now **DECIDED
policy** per RC's 2026-07-24 ruling — not the conservative placeholder v1.0 carried pending RC's answer. A
within-quarter retake (PREF-06.4: "retakes are allowed within the quarter") never reopens this tile: it is an
**orthogonal** activity/affordance attached to the completed lesson (§2, and the `retake_affordance` object in
the JSON) that never demotes, relocks, erases history, or alters the grading engine via navigation state. The
retake affordance's own implementation is deferred to later work packages (D8) — but the Desk-tile
terminality of `completed` itself is settled, not deferred.

### 3.1b Provisional transitions — retired (OPEN-18 resolved, v2.0)

**This bucket is now permanently empty.** In v1.0, four transitions (T7, T11, T12, T13) lived here as
non-normative, provisional entries (`"normative": false`, `"open_item": "OPEN-18"` in the JSON) because RC had
not yet decided whether `skipped` was reachable after release or reversible. RC's 2026-07-24 ruling resolved
OPEN-18: all four are promoted into the decided §3.1 table above (`transitions.legal` in the JSON), each now
carrying `"provenance": "RESOLVED by RC 2026-07-24"` in place of the old `"normative": false` /
`"open_item": "OPEN-18"` tags. The machine-readable `transitions.provisional_retirement` object in
`desk_state_model.v2.json` records this promotion explicitly, preserving the history rather than silently
dropping it. Nothing remains in this section going forward; it is kept only as the retirement marker for what
used to live here — see the `## Changelog — NT16 (v2.0)` section at the end of this document for the full
before/after.

Superseded v1.0 table, for historical reference only (do **not** treat as current — all four rows below are
now in §3.1, decided):

| ID | From | To | Trigger | Open item / register entry |
|---|---|---|---|---|
| T7 | `released` | `skipped` | Teacher retroactively designates as skipped | ~~OPEN-18~~ / U2 — now RESOLVED, see §3.1 |
| T11 | `today` | `skipped` | Same question as T7, applied while marked today | ~~OPEN-18~~ / U2 — now RESOLVED, see §3.1 |
| T12 | `skipped` | `released` | Teacher reverses a prior skip decision | ~~OPEN-18~~ / U3 — now RESOLVED, see §3.1 |
| T13 | `skipped` | `today` | Same question as T12, direct to today | ~~OPEN-18~~ / U3 — now RESOLVED, see §3.1 |

### 3.2 Illegal transitions (explicit — these matter as much as the legal ones)

| ID | From | To | Why illegal |
|---|---|---|---|
| X1 | `completed` | `temporarily-unavailable` | **Core reliability invariant.** An evidence-source outage may never demote or erase known-completed work — dossier §15 item 2; PREF-06.9. |
| X2 | `completed` | `unreleased` | No demotion path out of `completed` exists in RC's text. |
| X3 | `completed` | `skipped` | No demotion path out of `completed`; skipping is a curriculum-pursuit designation, not evidence erasure. **CONFIRMED FORBIDDEN** by RC's 2026-07-24 ruling (OPEN-18) — `completed → skipped` remains illegal, and this entry is the guard that enforces T11's pre-completion precondition (§3.1): once a lesson reaches `completed` for a student, T11 can never legally apply to it, and no other skip transition can either. |
| X4 | `completed` | `optional-catalog` | No demotion path out of `completed`; `optional-catalog` is a content classification, not reachable from a per-student completion fact. |
| X5 | `unreleased` | `completed` | No evidence path exists before release. |
| X6 | `unreleased` | `temporarily-unavailable` | No evidence determination is meaningful before release — nothing is being made unreachable. |
| X7 | `unreleased` | `optional-catalog` | `optional-catalog` is a content-ingestion-time classification (NT14), not a runtime demotion target for an ordinary unreleased lesson. |
| X8 | `skipped` | `completed` | Skipped lessons are inert and not openable; no evidence can attach without first becoming `released`/`today`. |
| X9 | `skipped` | `temporarily-unavailable` | Same as X8 — no evidence determination applies to an inert, unopenable lesson. |
| X10 | `skipped` | `unreleased` | No defined "un-skip to hidden" path; a reversal (T12/T13, now decided — see §3.1) goes through `released`/`today` — never back to `unreleased`. |
| X11 | `skipped` | `optional-catalog` | Not meaningful: `skipped` is a normal-path curriculum lesson the class walked past; `optional-catalog` content was never on the normal path. |
| X12 | `optional-catalog` | `unreleased` | Does not fall back to ordinary `unreleased`; its only forward path is explicit assignment (T14/T15). |
| X13 | `optional-catalog` | `skipped` | Not meaningful: never on the normal curriculum path for the class to skip over. |
| X14 | `optional-catalog` | `completed` | Must be explicitly assigned into `released`/`today` first. |
| X15 | `optional-catalog` | `temporarily-unavailable` | Same as X14 — no evidence determination applies to unassigned catalog content. |
| X16 | `optional-catalog` | `released`/`today` **via the ordinary `teacher_release`/`teacher_designate_today` trigger** | Illegal specifically via those triggers — optional-catalog content must never auto-schedule. The sole legal path out is T14/T15 via `explicit_teacher_assignment`. |
| X17 | `temporarily-unavailable` | `unreleased` | An availability failure must never reclassify a lesson's curriculum status. |
| X18 | `temporarily-unavailable` | `skipped` | Same as X17. |
| X19 | `temporarily-unavailable` | `optional-catalog` | Same as X17; also a content-ingestion classification never reachable via an availability failure. |

## 4. Visibility rules (state × view)

Two views, per RC Area 1: the **primary view** (today's assignment as the primary front door, "what's next"
secondary, plus a nearby/recent-released window) and the **expandable roadmap** (the broader released roadmap
behind a secondary/expandable view).

| State | Primary view | Roadmap view |
|---|---|---|
| `today` | Visible, openable — the front door (PREF-01.2) | Visible, openable — marks current position |
| `released` | Visible, openable, **only within the nearby/recent window** (PREF-01.6) | Visible, openable — every released lesson (PREF-01.7) |
| `unreleased` | **Not visible, not openable** — must not appear (PREF-01.8) | **Not visible, not openable** — must not appear (PREF-01.8) |
| `skipped` | Not visible | Visible, **grey, inert (not openable)** — roadmap-only (PREF-01.9) |
| `optional-catalog` | Not visible — absent until explicit assignment (PREF-01.10) | Not visible — absent until explicit assignment; the roadmap is still part of the normal student path |
| `completed` | Visible, openable (badge over prior release visibility) | Visible, openable — reviewable |
| `temporarily-unavailable` | Visible, openable (fail-open) — completion shown as UNKNOWN, no credit | Visible, openable (fail-open) — same rule |

Notes:
- "What's next" is not a state — it is a secondary label the primary view applies to the next `released`
  lesson in sequence after `today` (PREF-01.3, PREF-13.2 — there is no fixed calendar; the teacher designates
  today's and next lesson directly).
- `optional-catalog` is invisible in *both* views by construction: the instant it is explicitly assigned it
  transitions to `released`/`today` (T14/T15) and is no longer in the `optional-catalog` state, so it never
  needs to be "shown while still optional-catalog."

## 5. Optional-catalog rule

Lesson 4-1's 19 practice items were ingested under record `nt14-ingest-4-1-2026-07-23` carrying a top-level
`"availability": "optional-catalog"` marker on each registry row. `qb.select()` (`qb.py`) drops
optional-catalog rows **by default**; a caller opts in with the keyword-only `include_optional=True`.
`qb.get()` and `qb.get_for_packet()` are unchanged by this marker — explicit by-id lookup is deliberate
teacher access and always returns optional-catalog rows regardless of any flag. `qb.stats()` reports the
triple denominators (raw = required-active + optional-catalog + merged-alias; 919 = 878 + 19 + 22).

The Desk-level consequence, mirroring that content-layer default exactly:

- Optional-catalog content **never auto-schedules** and never appears as a `today`/`released` lesson through
  ordinary release triggers.
- It **never enters pacing** — no fixed calendar assumes its presence (PREF-13.2).
- It **never counts toward completion** — the completion-percentage mechanic (PREF-03.4) never includes it.
- It **never surfaces in the normal student path** (either the primary view or the expandable roadmap) absent
  **explicit teacher assignment** — the Desk-layer analogue of `qb.select(include_optional=True)`, modeled
  here as the dedicated `explicit_teacher_assignment` trigger (transitions T14/T15; see also the illegal
  transition X16, which forbids reaching `released`/`today` from `optional-catalog` via the *ordinary*
  release/designate-today triggers).

This section reaffirms, and does not reopen, Lesson 4-1's status: CLAUDE.md's "Lesson 4-1 (OPTIONAL
CATALOG — not scheduled, not required)" section and PREF-14.1/.2 both state 4-1 stays optional-catalog and is
never auto-scheduled.

## 6. Reliability rules

Citing `PROGRAM_DOSSIER.md` §15 items 1–3 directly:

1. **Unknown ≠ zero** (§15 item 1). When authoritative evidence for a lesson is unavailable, the Desk reports
   `temporarily-unavailable` / UNKNOWN — never `0`, never affirmatively "incomplete," never a silently-picked
   branch.
2. **Unavailability may not relock** (§15 item 2). Evidence-source unavailability alone can never relock or
   revoke known-`completed` work. `temporarily-unavailable` is **not** zero, **not** erased work, **not** a
   relock, and **not** a demotion of `completed` — see illegal transition X1, the single most important entry
   in §3.2.
3. **Fail-open navigation never awards credit** (§15 item 3). During uncertainty the UI may permissively
   navigate — a `temporarily-unavailable` lesson stays openable in both views (§4) — but official credit is
   only ever awarded from verified authoritative evidence; no credit accrues while a lesson renders
   `temporarily-unavailable`.

These three items are restated for the grading/attempts surface specifically at PREF-06.6–.9 in
`RC_TEACHER_PREFERENCE_RECORD.md`; this document cites both without re-deriving or reopening either.

## 7. Work-ahead rule

Students may open any teacher-`released` lesson and work ahead of `today`'s assignment, but **only** within
released material (PREF-01.4, PREF-01.5):

- Work-ahead eligible states: `released`, `today`.
- Work-ahead refused: `unreleased` (hidden/unavailable, PREF-01.8) and `optional-catalog` unless and until it
  has been explicitly assigned (at which point it is no longer in the `optional-catalog` state — it is
  `released`/`today`, and work-ahead applies normally). `skipped` is also refused — it is inert and not
  openable (§4).
- `completed` and `temporarily-unavailable` lessons remain independently openable (review, or fail-open per
  §6 item 3) but are not "work-ahead" targets in the RC sense — a student revisiting or fail-open-navigating
  into one of these is not "getting ahead" into new material.
- Work-ahead is never a path into unreleased or unassigned optional-catalog content, under any state or
  trigger in §3.

## 8. Points where RC's text did not fully settle a transition — both now RESOLVED

This section originally reported two unregistered ambiguities and, in v1.0, tracked them as canonical register
entries **OPEN-17** and **OPEN-18** in `OPEN_DECISIONS_REGISTER.md` (owned elsewhere in this tranche), because
encoding either question's answer as if it were settled RC policy would have misrepresented the record at the
time. **RC issued rulings on both on 2026-07-24 (NT16).** Neither question is open any longer — both are
DECIDED policy, recorded below with the ruling text and provenance.

- **OPEN-17 — is `completed` terminal at the Desk-tile layer, or does a within-quarter retake reopen it?**
  **RESOLVED by RC 2026-07-24.** Ruling: `completed` remains TERMINAL for the lesson tile. A retake is an
  ORTHOGONAL activity/affordance attached to the completed lesson — it never demotes completion, never
  relocks, never erases history, and never alters the grading engine via navigation state. `completed` keeps
  ZERO legal exit transitions — this is now DECIDED, not open. The retake-affordance concept is documented as
  orthogonal (§2, and the `retake_affordance` object in `desk_state_model.v2.json`); its implementation details
  are deferred to the work packages (D8). This supersedes v1.0's provisional choice, which kept zero legal
  exits as a conservative reading pending RC's decision — the outcome is unchanged, but the status is now
  DECIDED rather than provisional.
- **OPEN-18 — is `skipped` reachable after release, and is a skip designation reversible?**
  **RESOLVED by RC 2026-07-24.** Ruling, in full:
  - `unreleased → skipped` remains ALLOWED — T3, **CONFIRMED** (already legal in v1.0; the ruling settles it
    as decided policy, no duplicate transition minted).
  - `released → skipped` is ALLOWED — T7, promoted from `transitions.provisional` to `transitions.legal`.
  - `today → skipped` is ALLOWED **BEFORE COMPLETION** — T11, promoted to `transitions.legal` with a
    machine-readable `precondition` field (§3.1): a completed lesson can never reach `skipped`.
  - `skipped → released` is ALLOWED — T12, promoted to `transitions.legal`.
  - `skipped → today` is ALLOWED — T13, promoted to `transitions.legal`.
  - `completed → skipped` remains FORBIDDEN — X3, **CONFIRMED**, and updated to cite this ruling as the guard
    against T11's pre-completion condition being violated (§3.2).
  - **Students cannot initiate skip or unskip.** Every skip transition (T3, T7, T11, T12, T13) carries a
    machine-readable teacher-authority annotation (`"actor": "teacher_only"`, `"student_may_initiate": false`)
    — see §9.

  This supersedes v1.0's provisional choice, which recorded T7/T11/T12/T13 in `transitions.provisional`
  (`"normative": false`) as a non-normative implementation placeholder pending RC's answer — see §3.1b for the
  retirement note preserving that history.

## 9. Skip authority — teacher-only, no student initiation

RC's 2026-07-24 ruling on OPEN-18 is explicit that skip/unskip authority belongs to the teacher alone:

- **Students cannot initiate a skip** (`unreleased`/`released`/`today` → `skipped`, i.e. T3/T7/T11) **or an
  unskip** (`skipped` → `released`/`today`, i.e. T12/T13) — under any circumstance, through any Desk
  affordance.
- Every one of the five skip-related transitions carries `"actor": "teacher_only"` and
  `"student_may_initiate": false` in `desk_state_model.v2.json`.
- The top-level `skip_authority` object in the JSON is the single machine-readable source of truth for this
  rule: it names all five transitions (`T3`, `T7`, `T11`, `T12`, `T13`), fixes `student_may_initiate: false`,
  and records `forbidden_target_from_completed: true` — reaffirming that skip authority never overrides X3
  (`completed → skipped` stays illegal regardless of who is asking).
- This is distinct from, and does not loosen, the ordinary `teacher` actor used for release/today/assignment
  transitions (T1, T2, T4, T8, T14, T15) — skip/unskip specifically get the stricter `teacher_only` actor value
  precisely because RC's ruling calls out student-initiation as forbidden for this class of transition.

## Changelog — NT16 (v2.0)

**2026-07-24 — v2.0 supersedes v1.0.** Implements RC's 2026-07-24 rulings resolving OPEN-17 (retakes) and
OPEN-18 (skip transitions), the two open items this package (D4) owned out of RC's nine 2026-07-24 rulings.
Provenance token for every change below: `RESOLVED by RC 2026-07-24`.

- **OPEN-17 RESOLVED:** `completed` is DECIDED terminal (zero legal exits, confirmed policy — not a
  placeholder). Added the top-level `retake_affordance` object: a within-quarter retake is an orthogonal
  affordance that never demotes completion, never relocks, never erases history, and never alters the grading
  engine via navigation state. Implementation deferred to D8.
- **OPEN-18 RESOLVED:** T7 (`released → skipped`), T12 (`skipped → released`), and T13 (`skipped → today`)
  promoted from `transitions.provisional` to `transitions.legal`. T11 (`today → skipped`) promoted to
  `transitions.legal` with a new machine-readable pre-completion `precondition` field.
- T3 (`unreleased → skipped`) **CONFIRMED** by RC's ruling — already legal in v1.0; no duplicate transition
  minted.
- X3 (`completed → skipped`) **CONFIRMED FORBIDDEN**; its reason/cites updated to name this ruling and its
  role as the guard against T11's precondition being violated.
- `transitions.provisional` is now permanently empty (§3.1b rewritten as a retirement note); the JSON's new
  `transitions.provisional_retirement` object records the promotion history so it is not silently lost.
- `transitions.unresolved` is now permanently empty; the JSON's new `transitions.resolved` array carries U1,
  U2, U3 with their original topic text preserved, plus resolution text and provenance — no identifier was
  dropped.
- Added an `actor` field to every entry in `transitions.legal` (`teacher` | `system_evidence` |
  `teacher_only`); every skip transition (T3, T7, T11, T12, T13) additionally carries
  `student_may_initiate: false`. New §9 documents teacher-only skip authority.
- Added top-level `skip_authority` and `retake_affordance` objects to the JSON (see §9 and §2 respectively).
- `open_item_ids` is now empty; added `resolved_open_item_ids: ["OPEN-17", "OPEN-18"]`.
- Replaced `provisional_implementation_choices` with `resolved_open_items` (OPEN-17/OPEN-18 mapped to
  `RESOLVED` status, ruling text, and what each supersedes).
- Retitled `open_items_affecting_this_policy` to `resolved_items_affecting_this_policy`, reframed as resolved.
- `states.completed`'s description rewritten as DECIDED terminal; its `open_item` key removed, replaced by
  `status`/`resolved_open_item`/`provenance` metadata.
- Machine-readable companion renamed `desk_state_model.v1.json` → `desk_state_model.v2.json`; v1.0 is deleted
  (superseded, not archived elsewhere — this changelog and the JSON's own `changelog` array are the historical
  record of what v1.0 contained).
