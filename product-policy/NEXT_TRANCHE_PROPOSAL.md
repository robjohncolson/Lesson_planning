# Next Tranche Proposal — Recommended First Implementation Tranche

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

## 0. What this document is — read before anything else

**This is deliverable D8: a proposal, not an authorization.** Nothing in this document is executed by
NT15. No work package below is dispatched, approved, or begun by the act of writing this file. The
header block above states the *product-policy package's* authority (RC's decisions bind downstream
work); it does not mean this specific document's *sequencing recommendation* has been approved. Every
recommendation below is this document's own contribution — labeled as such throughout — and requires
separate sign-off (by the NT15 manager, Fable, and/or RC as appropriate) before any of it is dispatched.

**Provenance-discipline convention used throughout this document:**
- **RC decided** — traces to a `PREF-NN.M` row in `RC_TEACHER_PREFERENCE_RECORD.md` with status `DECIDED`.
- **NT15 contract specifies** — traces to D2/D3/D4/D5's own operational elaboration (already-written,
  already-authoritative machine-checkable behavior), cited by document name and section.
- **This proposal recommends** — this document's own sequencing/scoping judgment, not RC's words and not
  a contract's specified behavior. Marked with **RECOMMENDATION** inline wherever it appears.

**A citation correction, reported for the record.** The dispatch instructions for this deliverable stated
"per PREF-14.2, application development may precede complete quiz/content ingestion." Checking
`RC_TEACHER_PREFERENCE_RECORD.md` directly: `PREF-14.2` reads "Lesson 4-1 is never auto-scheduled" —
a different decision. The sub-decision that actually states "application/product development may proceed
before complete quiz/content ingestion — development is not blocked on full content" is `PREF-14.3`. This
document cites `PREF-14.3` throughout (§1) as the substantively correct source, and reports the discrepancy
here rather than silently citing either the wrong id or a corrected one without comment. **This correction is
flagged to the NT15 manager (Opus 5) in this implementer's final report; it is not a new open item and does
not require an `OPEN-NN` id — it is a citation-accuracy correction, not an unresolved RC question.**

---

## 1. Scope statement

**This proposal recommends that the first implementation tranche build exactly `PHASED_PRODUCT_SEQUENCE.md`
(D6) Phase A — the academic core — and nothing from Phase B, C, or D.** Concretely, the recommended tranche
delivers local, non-deployed, package-level implementations of:

- Desk lesson-state model (D4) — `DESK_STATE_MODEL.md`.
- Answer-evaluation authority model (D5) — `ANSWER_EQUIVALENCE_CONTRACT.md`.
- Grading policy (D2) — `GRADING_POLICY_SPEC.md`.
- Schoology projection contract (D3) — `SCHOOLOGY_PROJECTION_CONTRACT.md`, synthetic-fixture-only.
- The reward-seam event stream that Phase A must emit so Phase B needs no rework (`PHASED_PRODUCT_SEQUENCE.md`
  §3, `PREF-10.11`).
- The ELL/accessibility conformance requirement (`PREF-12`) threaded through all of the above, per D6 §2.6's
  explicit statement that this is not a downstream step but a quality bar every component must independently
  meet.

**This is not gated on content ingestion.** `PREF-14.3` (RC decided): "Application/product development may
proceed before complete quiz/content ingestion — development is not blocked on full content." The packages
recommended below operate on RC's grading/Desk-state/answer-equivalence/Schoology-projection *policy logic*
using synthetic fixtures and abstract lesson/item identifiers (exactly the pattern D2–D5's own reference
implementations already use) — none of them require the FRONTLOAD content (Topics 1–2, 3-1…3-4) or the
remaining Topic-4/5/6 DOK-verification work to be complete. Content-readiness, DOK, verified-item, and
alias-resolution decisions remain authoritative and are cited, not reopened (`PREF-14.4`–`.7`).

**Relationship to `PROGRAM_DOSSIER.md` §12's existing "first implementation tranche."** `PROGRAM_DOSSIER.md`
§12 already proposes a first tranche — "prove the canonical course model before touching the database"
(read-only DB snapshot, field-ownership spec, clone-only migration 007, one pure-function course-tree →
Schoology-plan projection proof). That tranche is about the *canonical course/lesson identity model*. This
proposal is about a different, complementary concern: RC's *grading/Desk-state/answer-evaluation/Schoology-
projection policy*, captured in NT15's D2–D5. **RECOMMENDATION:** the two are independent and parallel-safe —
neither blocks the other. The work packages below use placeholder lesson/item identifiers and do not require
§12's course-model migration to land first. A later integration step (out of scope here) will wire the two
together once both exist.

**Relationship to the A2 Railway/Supabase bootstrap (P0).** Reading `algebra2-platform/BOOTSTRAP_HANDOFF.md`
(read-only, for grounding only — not modified by this document or this implementer): the P0 bootstrap's
*staging* work (monorepo skeleton, `identity-ledger` service code, bootstrap SQL, smoke-test script,
secrets-manifest and isolation docs) is **already complete on disk**. What remains is entirely RC's own
action — creating the isolated A2 Supabase project, creating the isolated A2 Railway project, pushing the
private repo, setting the fresh-minted secrets, and running the one-time smoke test — none of which any agent
may perform (§2 below). This proposal does not re-propose that staging work; it is done. It only proposes
work that sits *on top of* the existing scaffold and does not require P0 to have cleared.

---

## 2. Gating reality check

Per `PROGRAM_DOSSIER.md` §14.0 (A2 Railway Bootstrap, the P0 gate): **nothing can be configured or deployed
to A2 until the isolated Supabase project and isolated Railway project exist, both created by RC, both using
RC's own credentials and console access.** No agent — including this one — can or should perform those
creations. `algebra2-platform/BOOTSTRAP_HANDOFF.md`'s own "DO NOT" section states this in the plainest terms
available: *"DO NOT touch, read, probe, connect to, or reference the AP Statistics systems in any live way"*
and every cloud-resource creation is marked as the human's action, not staged code.

This proposal therefore separates every recommended work package into exactly one of two buckets. **No work
package below straddles both** — each is either entirely local/scaffold-only, or entirely blocked pending RC.

### Bucket (a) — can proceed locally / clone-only / scaffold-only, no deployment, no live credentials

All six work packages in §3 below (D8-WP1 through D8-WP6) are in this bucket. Each:
- Is pure library/package code plus its own local test suite, executable with `pytest`/`node --test` (or
  the project's existing local test runners) on a developer machine.
- Requires no A2 Supabase connection, no A2 Railway deploy, no live Schoology session, and no AP Stats
  contact of any kind.
- Operates exclusively over synthetic fixtures and abstract identifiers, exactly as D2–D5's own reference
  implementations (`grading_policy_ref.py`, `desk_state_model.v2.json`, `parity_check.py`,
  `answer_equivalence_vectors.json`) already do.
- Where a package's *eventual* production use requires a live service (e.g., D8-WP5's evidence-submission
  client eventually posting to the deployed `identity-ledger`), this proposal scopes the *recommended* work
  to the local library and its tests against the identity-ledger's own already-existing local test suite
  (`algebra2-platform/services/identity-ledger/test/*`) — never against a deployed instance. Wiring it to a
  live service is explicitly bucket (b), not recommended here.

### Bucket (b) — blocked on P0 and on RC's own actions; not proposed for execution here

None of these are proposed as work packages in §3 — they are listed here only so the boundary is explicit
and nothing is silently assumed:

- Completing `algebra2-platform/BOOTSTRAP_HANDOFF.md` Steps 0–5 (creating the A2 Supabase project, creating
  the A2 Railway project, pushing the private repo, setting env vars, first deploy, smoke test). **RC's own
  action, already fully staged and scripted; this proposal does not re-propose it and assumes no timeline for
  it.**
- Deploying any of §3's packages to a live environment, or running any of them against a live A2 database.
- Any live Schoology connection: confirming the API-permission question (`PROGRAM_DOSSIER.md` R3),
  obtaining real course/section IDs (R4), re-probing selectors (R5), or any `tools/schoology-publisher`
  apply run (Gate ⛔3). `SCHOOLOGY_PROJECTION_CONTRACT.md` §9's NO-LIVE-WRITE constraint remains binding on
  every package this proposal recommends — none of them perform, or are recommended to ever perform, a
  network call, HTTP request, OAuth handshake, or CDP/browser step against a live Schoology tenant.
- Any AP Stats contact of any kind (Gate ⛔0, deferred/user-accepted risk — not reopened here).
- Any DDL against shared Supabase project A (Gate ⛔1) or student-facing reads of the `lesson_planning`
  schema (Gate ⛔2) — both belong to `PROGRAM_DOSSIER.md` §12's tranche, not this one.

**Nothing in §3 quietly assumes any of the above has happened or will happen on any particular timeline.**

---

## 3. Proposed work packages

Ordered by dependency (earliest = fewest prerequisites). All six are bucket (a). **RECOMMENDATION** for the
owned-path assignments — per `OWNED_PATHS.md`'s convention, these must be entered into that matrix by the
manager/Fable *before* any package is dispatched; this document does not itself edit `OWNED_PATHS.md` (out of
this implementer's owned-file scope) and does not assume that registration has happened.

Existing `algebra2-platform` paths already claimed by other, unrelated workstreams per `OWNED_PATHS.md`
(`packages/course-model/`; `services/identity-ledger/src/server.js`, `.../src/validate-item-uid.js`,
`.../test/server.test.mjs`) are avoided entirely below — none of the six proposed owned paths overlaps them.

| ID | Title | Delivers | Governing NT15 deliverable(s) | Depends on | Proposed owned path |
|---|---|---|---|---|---|
| D8-WP1 | Desk lesson-state engine | A framework-agnostic library implementing the 7 canonical states; **all eighteen decided transitions** T1–T18 (T7/T11/T12/T13 promoted into `transitions.legal` by RC's 2026-07-24 ruling resolving `OPEN-18`, `transitions.provisional` now permanently empty); illegal-transition guards X1–X19; precedence-ordered state derivation; and the two-view visibility matrix | D4 `DESK_STATE_MODEL.md` | None — foundational, per D6 §2.1 | `algebra2-platform/packages/desk-state/` (**new** package; no existing scaffold covers this) |
| D8-WP2 | Answer-evaluation authority engine | A library implementing the Tier 1–4 separation: Tier-1 deterministic checks scoped to baseline capability, Tier-2 unsupported-form routing, a Tier-3 override interface stub, a Tier-4 explanation-only stub that never resolves to a graded outcome | D5 `ANSWER_EQUIVALENCE_CONTRACT.md` | D8-WP1 (a lesson must be `released`/`today` for capture to be meaningful, per D6 §2.3) and the pre-existing packet infrastructure (`qb.py`, `tex/*` — cited, not rebuilt) | `algebra2-platform/packages/answer-equivalence/` (**new** package) |
| D8-WP3 | Grading policy engine | A library reproducing `grading_policy_ref.py`'s computations (WORK/ASSESSMENT aggregates, completion %, the 40%-inclusive quarter rule, UNKNOWN semantics, teacher-override precedence) as a shared, importable package, versioned per `PREF-03.8` | D2 `GRADING_POLICY_SPEC.md` | D8-WP2 only — specifically the per-answer Tier verdicts plus the item-level, server-authoritative teacher-designation flag they carry (`PREF-03.9`, `PREF-04.6`: server policy and teacher designation, never a client or a navigation-layer state, decide what counts toward completion/WORK). **Not D8-WP1.** Completion % and the quarter-rule branch are computed directly from that item-level evidence; the Desk `completed` tile (D8-WP1) is a downstream *projection* of the same evidence, never a source this package reads (dossier §15 item 4: server ledger is authoritative, client/projection state is never a source of record) | `algebra2-platform/packages/grading-contracts/` (**existing scaffold** — currently README-only, "Not yet implemented"; this proposal fills it, does not create a competing package) |
| D8-WP4 | Schoology projection engine | A library reproducing `parity_check.py`'s structure operating exclusively over synthetic fixtures: assignment/category mapping, the official-quarter-grade override mechanism, the deep-link contract (`a2_activity_key` + literal `schoology_url_template` placeholders), idempotency (`external_key`, create-vs-update, convergence), and divergence-report shape | D3 `SCHOOLOGY_PROJECTION_CONTRACT.md` | D8-WP3 (projects the aggregates/quarter grade) and D8-WP1 (lesson states gate what projects) | `algebra2-platform/packages/schoology-projection/` (**new** package — deliberately distinct from the future `tools/schoology-publisher/` live-write tool named in `PROGRAM_DOSSIER.md` WP7, which is a separate, later, explicitly-gated workstream not proposed here) |
| D8-WP5 | Reward-seam event stream | The append-only, replayable event stream `PHASED_PRODUCT_SEQUENCE.md` §3 requires Phase A to emit: the per-question evaluation-outcome event (§3.1), per-day participation-evaluated event (§3.2), and lesson-completed event (§3.3), plus the read-only projection interface (§3.5) Phase B will later consume. Builds **only** the seam — no candy balance, no streak logic (§3.6) | D6 `PHASED_PRODUCT_SEQUENCE.md` §3 (`PREF-10.11`), consuming facts from D8-WP1–WP3 | D8-WP1, D8-WP2, D8-WP3 (wraps their emitted facts) | `algebra2-platform/packages/evidence-client/` (**existing scaffold** — currently README-only, "Client library for submitting and verifying A2 evidence receipts"; this proposal's scope is the local library + its tests against the identity-ledger's own local test suite only — see §2 bucket-(a) note) |
| D8-WP6 | ELL/accessibility conformance pass | A conformance checklist plus a lightweight harness that verifies D8-WP1–WP5's public interfaces each expose the required hooks: vocabulary support, worked-example surfacing, simpler-language explanation hooks that preserve mathematical demand, Chromebook-first/offline-tolerant assumptions | `PREF-12`, threaded per D6 §2.6 (no single governing D-deliverable; cross-cutting) | Threaded through D8-WP1–WP5 simultaneously, not sequenced strictly after them | `algebra2-platform/docs/ell-accessibility/` (**new**, docs + checklist + a small conformance-test harness; acceptance criteria are additionally embedded as required test cases inside each of D8-WP1–WP5's own owned paths, not only here) |

**Explicitly excluded from this tranche's work-package list, per D6's own phase ordering:** Phase C (TI-84
trainer, `PREF-08`) and Phase D (Equation Lab, `PREF-09`) are **RECOMMENDATION**-excluded from this first
tranche. `RC_TEACHER_PREFERENCE_RECORD.md`'s downstream-bindings table lists this deliverable (D8) among the
implementers of `PREF-08`/`PREF-09`/`PREF-10`/`PREF-12`/`PREF-14` — this document satisfies that binding by
recording the recommendation explicitly rather than by including Phase C/D work packages in the *first*
tranche: D6 §5/§6 state that Phase C and Phase D each depend only on Phase A's extra-credit mechanism
(delivered here by D8-WP3) and Schoology deep-link contract (delivered here by D8-WP4), not on completing
Phase B. Once this tranche ships, a **future** tranche proposal may recommend Phase C/D work packages against
those now-existing dependencies — that is not this document's recommendation for the *first* tranche.

---

## 4. Acceptance criteria per work package

Each criterion below is concrete and checkable — a test, a static/import-graph check, or a diff against an
existing conformance fixture — not an aspirational statement. Where an NT15 contract already defines
machine-checkable behavior, the criterion requires conformance to that artifact by name.

**D8-WP1 — Desk lesson-state engine**
1. The state-derivation function reproduces `DESK_STATE_MODEL.md` §2's precedence order exactly
   (`completed` > `temporarily-unavailable` > `today` > `skipped` > `optional-catalog` > `released` >
   `unreleased`, first match wins) — verified byte-for-byte against `test_desk_state_model.py`'s existing
   conformance fixture as a regression baseline.
2. Every legal transition — **all eighteen, T1–T18** — and every illegal transition X1–X19
   (`DESK_STATE_MODEL.md` §3) is encoded and unit-tested **as conformance to decided policy**; an attempted
   illegal transition is rejected, never silently applied. Per RC's 2026-07-24 ruling resolving `OPEN-18`,
   T7/T11/T12/T13 are decided legal transitions exactly like the other fourteen — there is no longer a
   smaller "decided set" that excludes them (see 2a).
2a. **T7, T11, T12, and T13 are now decided legal transitions, implemented and tested as conformance to
   decided policy — the same standard as every other transition in `transitions.legal`.** RC's 2026-07-24
   ruling on `OPEN-18` promoted all four out of the retired `transitions.provisional` bucket
   (`desk_state_model.v2.json`'s `transitions.provisional` is now permanently empty; the promotion history is
   recorded in its `transitions.provisional_retirement` object). A build that omits any of the four, or that
   still carries a `provisional: true` / `open_item: "OPEN-18"` / `normative: false` marker on any of them, is
   **no longer acceptable** under this criterion. Specifically:
   - T11 (`today` → `skipped`) is legal **only before completion** — its machine-readable `precondition`
     (`student_completion_state != 'completed'`) must be present and enforced; an attempt against an
     already-`completed` lesson is rejected under X3, never silently applied under T11.
   - Every one of T3, T7, T11, T12, T13 carries `actor: "teacher_only"` and `student_may_initiate: false`; a
     test asserts a simulated student-initiated skip or unskip request is rejected on every one of the five.
   - A test asserts `completed → skipped` (X3) is rejected unconditionally, confirming it is never reachable
     through T11 or any other transition.
3. A test asserts that only the `explicit_teacher_assignment` trigger (T14/T15) moves a lesson out of
   `optional-catalog`, and that the ordinary release/designate-today triggers fail against an
   `optional-catalog` lesson (illegal transition X16).
4. The visibility-matrix function reproduces `DESK_STATE_MODEL.md` §4's (primary-view, roadmap-view)
   visibility/openability pair for all seven states.
5. A test enumerates every transition attempt *from* `completed` and asserts each is rejected — zero legal
   exits, per RC's 2026-07-24 ruling resolving `OPEN-17`, which settles this as **DECIDED** policy, not the
   model's prior provisional choice (`DESK_STATE_MODEL.md` §8 no longer records this as open; see also §5
   below). A further test asserts that a retake becoming available for a completed lesson — the orthogonal
   `retake_affordance`
   concept in `desk_state_model.v2.json` — does not change the Desk tile's state at all: the tile remains
   `completed` before, during, and after a retake becomes available or is attempted; retake availability is
   never itself a Desk-state transition.

**D8-WP2 — Answer-evaluation authority engine**
1. For every vector in `answer_equivalence_vectors.json`, the engine's tier and verdict output matches the
   vector's `expected_outcome`/`decision_authority` fields exactly (regression conformance against the
   existing corpus).
2. A property test asserts every Tier-2-routed submission yields `route-to-review`, never `auto-incorrect`
   (the Tier-2 asymmetry `ANSWER_EQUIVALENCE_CONTRACT.md` requires).
3. Every vector whose `decision_authority` is `"ai"` resolves to `route-to-review` — Tier 4 never itself
   produces a graded outcome (re-verified in the new package, not merely inherited from the vectors file).
4. A simulated evaluator-unavailable condition (distinct from Tier 2's "engine reachable but form
   unsupported") yields `UNKNOWN` and routes to Tier 3 — never `incorrect`, per the contract's "Attempts
   Interaction" section.
5. A test asserts two items with mathematically identical expected answers but different declared per-item
   policy flags (e.g., `factored_expanded_equivalent` vs `factored_form_required`) produce different tier
   verdicts on the same submitted form — proving the per-item flag mechanism actually governs the outcome,
   not a hardcoded global rule.

**D8-WP3 — Grading policy engine**
1. `compute_completion`, `compute_participation_day` (+ `aggregate_participation`), `compute_extra_credit`,
   `compute_component_percentage`, `compute_assessment_aggregate`, `compute_work_aggregate`,
   `compute_quarter_grade`, and the display helpers `round_final_grade_for_display` /
   `final_grade_display_string` reproduce `grading_policy_ref.py`'s (v2.0) outputs byte-for-byte against
   `test_grading_policy_ref.py`'s existing fixture set (regression conformance). This supersedes v1.0's
   three-function list: `compute_work_aggregate`'s signature changed to the point-based formula
   (`packet_points_earned`/`_possible`, `participation_points_earned`/`_possible`,
   `extra_credit_points_earned` — no longer a three-scalar plain-addition signature), and
   `compute_quarter_grade` no longer accepts a `round_ndigits` parameter (`OPEN-09`).
2. An explicit boundary test asserts `completion == 0.40` exactly takes the `max` branch, never the average
   branch (`PREF-03.5`, inclusive gate).
3. A test asserts that any missing required input (completion, WORK aggregate, ASSESSMENT aggregate, or a
   participation-day input) yields `UNKNOWN` — never `0`, `False`, or a silently-picked branch
   (`GRADING_POLICY_SPEC.md` §6).
4. A test asserts a supplied teacher override is always the returned value, including when the computed
   result would otherwise have been `UNKNOWN` (§3.1).
5. A test suite asserts conformance to the **DECIDED** arithmetic RC's 2026-07-24 rulings settled for
   `OPEN-08`, `OPEN-09`, `OPEN-10`, `OPEN-11`, `OPEN-15`, `OPEN-16`, and `OPEN-19` — this criterion no longer
   greps for placeholder-behavior tokens; it checks the resolved behavior itself:
   - `OPEN-08`: the completion-threshold comparison uses the EXACT completion ratio, never a pre-rounded
     value, at the inclusive `>= 0.40` boundary.
   - `OPEN-09`: every internal computation (`compute_completion`, `compute_component_percentage`,
     `compute_assessment_aggregate`, `compute_work_aggregate`, `compute_quarter_grade`) returns full
     precision with no rounding; only `round_final_grade_for_display`/`final_grade_display_string` round, to
     one decimal, and only for student-facing display — the rounded value is never fed back into any
     computation or synced to Schoology.
   - `OPEN-10`: extra credit is capped at `+1.0`/student/class-day across the two currently-authorized
     sources (TI-84 `+0.5`, Equation Lab `+0.5`, stacking allowed); a request naming an unauthorized
     additional source raises `PolicyDecisionRequiredError` rather than silently exceeding the cap.
   - `OPEN-11`: `compute_participation_day` excludes non-class days from the participation requirement
     entirely (`0.0`/`0.0`, not an auto-zero); partial/absent/uncertain attendance never auto-zeroes and is
     excused/unknown unless the day is explicitly designated participation-eligible; UNKNOWN is distinct
     from zero throughout.
   - `OPEN-15`: WORK is point-based — `100 × (packet_pe + participation_pe + ec_pe) / (packet_pp +
     participation_pp)` — extra credit raises earned but never possible, and WORK may legitimately exceed
     100.
   - `OPEN-16`: a zero-eligible-denominator condition (in completion, WORK, or a component/assessment
     reduction) yields UNKNOWN, never zero, never a fabricated ratio.
   - `OPEN-19`: multi-item same-kind reduction (`compute_component_percentage`/`compute_assessment_aggregate`)
     is point-weighted (`100 × Σearned / Σpossible`); a test asserts an equal-average of differing-scale
     per-item percentages is rejected as non-conformant.
6. **Dependency-direction invariant, stated explicitly and enforced by a test.** This package's completion,
   WORK, and quarter-grade computations read only item-level, server-authoritative evidence and the
   teacher-designation flag attached to it (`PREF-03.9`, `PREF-04.6`) — **never** the Desk `completed` tile
   state produced by D8-WP1. A static/import-graph check asserts D8-WP3 has zero imports from D8-WP1.
   Consequence, stated as the invariant itself: `OPEN-17` is now RESOLVED — RC's ruling is exactly that
   `completed` is DECIDED terminal and a within-quarter retake is an orthogonal navigation-layer affordance
   (never a Desk-state transition, per `desk_state_model.v2.json`'s `retake_affordance` object) — and this
   invariant is precisely what makes that answer safe: because D8-WP3 has zero import/data dependency on
   D8-WP1's tile state, the retake affordance has no code path by which it could ever reach this package's
   arithmetic. The invariant no longer merely avoids depending on an unresolved question; it is the
   structural guarantee that keeps the now-decided navigation affordance from ever leaking into grade
   computation (`PROGRAM_DOSSIER.md` §15 item 4: the server ledger and stable student identity are
   authoritative; browser/client/projection state is never a source of record).

**D8-WP4 — Schoology projection engine**
1. `project_course()`/`_should_project()` reproduce `SCHOOLOGY_PROJECTION_CONTRACT.md` §3's release-gating
   table exactly, byte-for-byte against `test_parity_check.py`'s existing gating tests.
2. `external_key()` is verified pure: two calls with identical `(course_id, lesson_id, artifact_type,
   artifact_id)` inputs, run as separate invocations, return identical keys — no timestamp, no random id.
3. Two consecutive projection runs over identical input produce byte-identical output records (`run_1 ==
   run_2`), reproducing the existing convergence assertion.
4. `deep_link_for()` never fabricates a concrete Schoology course/assignment id — the
   `schoology_url_template`'s placeholder tokens remain literal in every output, reproducing the existing
   "never fabricates" test.
5. A runtime check (e.g., a test that monkeypatches/blocks socket and HTTP calls and asserts none occur)
   enforces zero network calls, zero HTTP requests, and zero CDP/browser automation anywhere in this
   package's code path — `SCHOOLOGY_PROJECTION_CONTRACT.md` §9's NO-LIVE-WRITE constraint, machine-verified,
   not merely asserted in prose.
6. A test reproduces the `student_0004_unknown_assessment_evidence.json` fixture behavior: when A2's
   authoritative computation is `UNKNOWN`, the reconciliation report is always flagged divergent, regardless
   of how complete Schoology's native figure looks.
7. **Display-rounding-aware reconciliation (`OPEN-09`).** A test asserts the reconciliation report compares
   A2's full-precision underlying WORK/ASSESSMENT/quarter-grade values against Schoology's native
   earned/possible totals — never the student-facing, one-decimal-rounded display value produced by
   `round_final_grade_for_display`/`final_grade_display_string` — and that a divergence produced solely by
   display rounding (e.g. A2's exact value is `87.96`, its rounded display is `88.0`, and Schoology's native
   figure is consistent with `87.96`) is never reported as a substantive divergence.
8. **No-fabricated-zero rule (`OPEN-16`).** A test asserts that when A2's authoritative computation for a
   student/lesson is `UNKNOWN` (zero-eligible-denominator per `OPEN-16`), the projection never synthesizes a
   zero-valued Schoology assignment or a zero-valued grade to force a comparison to run — the projection
   either reports the `UNKNOWN` state directly or reproduces the existing
   `student_0004_unknown_assessment_evidence.json` fixture's "always flagged divergent" behavior (criterion 6
   above), never a fabricated `0`.

**D8-WP5 — Reward-seam event stream**
1. Every emitted per-question evaluation-outcome event validates against a checked-in schema carrying:
   server-ledger stable student identity, `item_uid`, lesson identity, a monotonic per-student-per-item
   attempt number, the Tier verdict, and the teacher-designation flag (`PHASED_PRODUCT_SEQUENCE.md` §3.1).
2. The package's public API exposes no update/delete operation over a previously emitted event; a test
   asserts any attempted mutation of a prior event raises.
3. A replay test reconstructs a toy derived value (e.g., a test-double streak counter) twice — once by
   folding the full stream from position 0, once incrementally — and asserts both reconstructions agree,
   verifying no hidden non-replayable state.
4. An import-graph/static check asserts D8-WP1, D8-WP2, and D8-WP3 have zero imports from D8-WP5 — the
   one-directional-flow invariant (§3.5: "reward computation must never write to official evidence").
5. A denylist test greps the package for forbidden terms/APIs (candy balance, streak-counter business logic,
   gifting, Tetris, leaderboard, celebration/sound) and fails if any are present — enforcing
   `PHASED_PRODUCT_SEQUENCE.md` §3.6 ("Phase A does not build the economy") and `PREF-10.5`–`.8`.

**D8-WP6 — ELL/accessibility conformance pass**
1. A conformance script fails if any of D8-WP1–WP5's public interfaces lacks a documented vocabulary-support
   or worked-example-surfacing hook.
2. The checklist requires a paired "rigor-preserved" note for every simplified-language hook found
   (`PREF-12.3`); a hook without its pairing fails the check.
3. Each of D8-WP1–WP5's test suites includes at least one offline/degraded-connectivity test case
   demonstrating graceful fallback rather than a hard failure (`PREF-12.6`/`.7`); the conformance script
   fails if any package lacks one.
4. The conformance script's passing output explicitly records that `OPEN-05` (audio), `OPEN-06` (bilingual),
   and `OPEN-07` (AI integration for explanations) are **not** required for this tranche's pass/fail gate —
   a passing run must not silently require any of the three.

---

## 5. Open-item dependencies — critical

**Governing rule for this entire tranche, revised for NT16.** The v1.0 rule stated here — "no work package
may depend on `OPEN-17` (retake affordance) or on `OPEN-15`/`OPEN-19` (WORK-aggregate combination / same-kind
reduction) being resolved" — is **obsolete and retired**, not merely relaxed: RC's 2026-07-24 rulings resolved
`OPEN-17`, `OPEN-15`, `OPEN-18`, and `OPEN-19` (`OPEN_DECISIONS_REGISTER.md`). Every work package below now
**inherits** the decided arithmetic/policy those rulings settled — it builds directly against
`grading_policy.v2.json`/`grading_policy_ref.py` and `desk_state_model.v2.json`, not around a labeled
placeholder RC could still overturn. The remaining genuine open-item dependencies are narrow, and are listed
per package below; none of them touches D8-WP1's transition table, D8-WP3's WORK/quarter-grade arithmetic, or
D8-WP4's same-kind reduction, all three of which are now fully specified by decided policy.

| Work package | OPEN items it runs into | How it proceeds |
|---|---|---|
| D8-WP1 (Desk state) | None — `OPEN-17` and `OPEN-18` are both RESOLVED | Implements the model's DECIDED policy exactly as documented (`DESK_STATE_MODEL.md` §8, `desk_state_model.v2.json`): `completed` is terminal (zero legal exits, `OPEN-17`), and all eighteen transitions T1–T18 — including T7/T11/T12/T13, promoted out of the now-retired `transitions.provisional` bucket into `transitions.legal` — are decided legal transitions (`OPEN-18`). This package inherits both rulings directly; it does not implement a provisional/placeholder version of either, and does not need to choose between "omit" and "implement under a provisional label" the way the v1.0 rule required. |
| D8-WP2 (Answer evaluation) | `OPEN-12`, `OPEN-13` — still OPEN | Proceeds with baseline Tier-1 capability (commutativity/associativity, per-item policy flags) and routes anything requiring proof beyond that to Tier 2, per `ANSWER_EQUIVALENCE_CONTRACT.md`'s own guidance for pre-engine-choice operation, and per the NT16 interim operating rule recorded in both that contract's `## Open Items` section and `OPEN_DECISIONS_REGISTER.md`: clearly-deterministic cases may be accepted; unsupported symbolic/tolerance cases route to teacher review, never auto-fail. Numeric-tolerance boundary cases stay illustrative until `OPEN-12` is set; does not invent a tolerance value or select an engine (`OPEN-13`). |
| D8-WP3 (Grading policy) | None substantive — `OPEN-08`, `OPEN-09`, `OPEN-10`, `OPEN-11`, `OPEN-15`, `OPEN-16`, `OPEN-19` are all RESOLVED | Inherits the decided arithmetic directly from `grading_policy.v2.json`/`grading_policy_ref.py`: exact-ratio threshold comparison (`OPEN-08`), full-precision internals with display-only rounding (`OPEN-09`), the `+1.0`/day capped point-based extra-credit ledger (`OPEN-10`), the participation day-eligibility semantics (`OPEN-11`), the point-based WORK formula (`OPEN-15`), UNKNOWN-on-zero-denominator throughout (`OPEN-16`), and the point-weighted same-kind reduction (`OPEN-19`). No placeholder remains for any of these seven — this package is a straight conformance build against decided policy, not a scoped-around-the-gap build. As before, it has zero import/data dependency on D8-WP1's Desk `completed` tile state (§4 criterion 6), which is what makes `OPEN-17`'s resolution irrelevant to this package's arithmetic regardless of how the (now-decided) navigation-layer affordance is eventually built. |
| D8-WP4 (Schoology projection) | `OPEN-04` — still OPEN | Proceeds with placeholder category keys (`WORK`/`ASSESSMENT`) pending `OPEN-04` naming strings only. Inherits the decided point-weighted same-kind reduction directly from D8-WP3/`OPEN-19` — the prior `_average_percentage` simple-average placeholder is **retired**, not merely scoped around; this package's aggregation must match `compute_component_percentage`/`compute_assessment_aggregate` exactly, not an independent convention. |
| D8-WP5 (Reward-seam stream) | `OPEN-14` (adjacent, not blocking) | The seam's existence and shape do not depend on *when* Phase B activates (`OPEN-14` is a timing question for a later phase, not a structural one for this package). `OPEN-15`/`OPEN-17`/`OPEN-19` are resolved, and this package still does not read Desk-tile or grading-arithmetic internals regardless of their status. |
| D8-WP6 (ELL conformance) | `OPEN-05`, `OPEN-06`, `OPEN-07` | Conformance gate explicitly excludes these three from its pass/fail criteria (§4, criterion 4) — proceeds by scoping around the gap, not by guessing whether audio/bilingual/AI-integration support exists. |

**Confirmation, stated plainly.** `OPEN-17`, `OPEN-15`, `OPEN-18`, and `OPEN-19` are RESOLVED as of RC's
2026-07-24 rulings (`OPEN_DECISIONS_REGISTER.md`). None of D8-WP1 through D8-WP6 is blocked on any of them —
every package that touches their substance (D8-WP1 for `OPEN-17`/`OPEN-18`; D8-WP3 and D8-WP4 for
`OPEN-15`/`OPEN-19`) now builds directly against the decided policy those rulings settled, rather than
scoping around a gap. The remaining genuine open-item dependencies are narrow: `OPEN-04` (D8-WP4, naming
strings only), `OPEN-12`/`OPEN-13` (D8-WP2, with the NT16 interim operating rule), `OPEN-14` (D8-WP5, timing
only, not structural), and `OPEN-05`/`OPEN-06`/`OPEN-07` (D8-WP6, explicitly excluded from its pass/fail
gate).

**`OPEN-18` is now RESOLVED — D8-WP1 inherits the decided skip-transition table directly, not a provisional
labeling scheme.** RC's 2026-07-24 ruling promoted T7/T11/T12/T13 out of the retired `transitions.provisional`
bucket into `transitions.legal` (§4 criteria 2/2a above). D8-WP1 must implement all eighteen transitions —
including these four, T11's machine-readable pre-completion precondition, and every skip transition's
`teacher_only`/`student_may_initiate: false` markers — as ordinary conformance to decided policy. There is no
longer a provisional-labeling discharge path for this dependency; the dependency itself no longer exists.

**Callout — the rework risk this section previously flagged is now RETIRED, not merely reduced.**
`OPEN-15` (WORK-aggregate component combination), `OPEN-16` (zero-denominator semantics), and `OPEN-19`
(same-kind-item reduction) were previously singled out here as the three most likely to force a recompute of
every downstream consumer — the quarter grade itself, and everything D8-WP4 projects to Schoology — if RC's
eventual answer differed from the placeholder each package shipped with. RC has now ruled on all three
(`OPEN_DECISIONS_REGISTER.md`): the point-based WORK formula (`OPEN-15`), UNKNOWN-on-zero-denominator across
completion/WORK/quarter grade (`OPEN-16`), and the point-weighted same-kind reduction (`OPEN-19`) are DECIDED
policy, already implemented in `grading_policy.v2.json`/`grading_policy_ref.py`. The rework this callout
warned about is retired outright, not merely lowered in probability — D8-WP3 and D8-WP4 build against the
final formulas from the outset and never against a placeholder RC could still overturn. The remaining
naming/timing/ELL items (`OPEN-03`/`OPEN-04`, `OPEN-05`–`OPEN-07`) remain in their original, lower-risk
category — additive or display-only, never a recomputation of an existing number.

---

## 6. Explicitly out of scope for the first tranche

The following are **not** part of this recommended tranche, under any of the work packages in §3:

- **Deferred features** — step-by-step enforcement in Equation Lab (`PREF-09.6`), gifting, Tetris,
  leaderboards, celebration noise (`PREF-10.5`–`.8`), and intervention/makeup/enrichment subsystems
  (`PREF-13.6`). All `DEFERRED`, not `OPEN` — RC decided "not now," and this tranche does not build them.
- **The reward economy itself (Phase B).** D8-WP5 builds only the seams (§3.1–§3.5 of D6) — no candy
  balance, no candy-earning rule, no populated completion-calendar UI, no streak-counting logic. That is
  entirely Phase B's content and is not part of this proposal.
- **Phase C (TI-84 trainer) and Phase D (Equation Lab).** Sequenced after Phase A per D6 §5/§6; a future
  tranche proposal may recommend them once this tranche's extra-credit mechanism (D8-WP3) and Schoology
  deep-link contract (D8-WP4) exist. Not recommended here.
- **Live Schoology integration of any kind** — the actual `tools/schoology-publisher` apply path
  (`PROGRAM_DOSSIER.md` WP7, Gate ⛔3), any OAuth/API/CDP/DOM interaction with a real Schoology tenant, and
  any use of real course/section IDs (which do not exist yet).
- **Any AP Stats contact** — no network call, probe, read, or reference to the live AP Stats platform, its
  roster-server, its Supabase data, or its secrets, in any form (Gate ⛔0, deferred/user-accepted, not
  reopened).
- **Any deployment prior to P0** — deploying any of D8-WP1–WP6's packages to a live A2 Railway/Supabase
  environment, or completing any step of `algebra2-platform/BOOTSTRAP_HANDOFF.md`, is not part of this
  tranche. That remains entirely RC's own action (§2).

---

## 7. No dates or durations

Consistent with `PHASED_PRODUCT_SEQUENCE.md`'s own hard constraint and `PREF-13.2`–`.5` (RC designates
lessons directly; no fixed calendar; "~1 topic/quarter" is temporary; no hard-coded four topics or fixed
annual pace): **this document contains no calendar dates, no durations, no sprint counts, and no estimate of
how long any work package takes.** The ordering in §3's table is dependency order only — which package must
exist before which other package can be built, never when. Nothing above should be read as implying any
particular pace of delivery.

---

## Provenance summary

- The scope statement (§1) restates D6's own Phase-A ordering and cites `PREF-14.3`/`.4`–`.7` (RC decided;
  citation corrected from the dispatch instructions' `PREF-14.2` — see §0).
- The gating-reality split (§2) restates `PROGRAM_DOSSIER.md` §14.0's own P0 gate and Tranche-0 checklist
  structure, and cites the current on-disk state of `algebra2-platform/BOOTSTRAP_HANDOFF.md` (read-only
  grounding, not modified here) to state honestly that P0's staging work is already done and only RC's
  cloud-resource creation and secret-setting remain.
- **Everything in §3 (the six work packages, their ordering, and their proposed owned paths), §4 (the
  acceptance criteria), and the retired-rework-risk callout in §5 is this document's own
  recommendation** — none of it is RC's decision text, and none of it is asserted as already-authorized work.
  It is offered so a later reader (the NT15 manager, Fable, or RC) has something concrete to approve, amend,
  or reject, exactly as `PHASED_PRODUCT_SEQUENCE.md`'s own provenance summary describes for its reward-seam
  elaboration.
- §5's open-item table cites `OPEN-01` through `OPEN-19` only by their canonical register entries in
  `OPEN_DECISIONS_REGISTER.md`; no new open item is minted by this document.
- §6 restates D6 §3.6, §7, and the deferred-item table verbatim in substance; it does not narrow or expand
  any of them.

## Changelog — NT16 (v2.0)

**2026-07-24 (v2.0).** RC's nine 2026-07-24 rulings (`OPEN_DECISIONS_REGISTER.md`) resolved `OPEN-08` through
`OPEN-11` and `OPEN-15` through `OPEN-19`; this document updates its acceptance criteria and open-item
accounting to inherit those rulings rather than scope around them. Substantive changes:

- §4 D8-WP1 criterion 2: the decided legal-transition set is now **T1–T18, all eighteen** — no longer
  "T1–T6, T8–T10, T14–T18."
- §4 D8-WP1 criterion 2a: rewritten from "T7/T11/T12/T13 are not part of the decided transition table... may
  implement them, but only as explicitly-labeled provisional behavior pending RC" to the decided semantics —
  all four are now decided legal transitions, implemented and tested as ordinary conformance to decided
  policy; T11 carries a machine-readable pre-completion precondition; every skip transition is teacher-only
  and rejects a student-initiated attempt; `completed → skipped` is rejected unconditionally. A build
  omitting any of the four is no longer acceptable.
- §4 D8-WP1 criterion 5: zero exits from `completed` is now DECIDED (`OPEN-17`), not "the model's current
  provisional choice"; added an assertion that a retake becoming available never changes the tile's state.
- §4 D8-WP3 criterion 1: updated to the new function set/signatures (`compute_completion`,
  `compute_participation_day`/`aggregate_participation`, `compute_extra_credit`,
  `compute_component_percentage`, `compute_assessment_aggregate`, `compute_work_aggregate`,
  `compute_quarter_grade`, and the display helpers).
- §4 D8-WP3 criterion 5: rewritten entirely from a placeholder-behavior grep (six `OPEN-NN` docstring tokens,
  "no rounding by default, plain-addition WORK combination, no daily cap...") to conformance against the
  DECIDED arithmetic for `OPEN-08`, `OPEN-09`, `OPEN-10`, `OPEN-11`, `OPEN-15`, `OPEN-16`, and `OPEN-19`.
- §4 D8-WP3 criterion 6: the dependency-direction invariant is unchanged in mechanism (zero imports from
  D8-WP1) but its rationale now states that `OPEN-17` is answered and that this invariant is what makes that
  answer safe, rather than a hedge against an unresolved question.
- §4 D8-WP4: added criteria 7 (display-rounding-aware reconciliation, `OPEN-09`) and 8 (no-fabricated-zero
  rule, `OPEN-16`).
- §5 rewritten in full: the prior governing rule ("no work package may depend on `OPEN-17`/`OPEN-15`/
  `OPEN-19` being resolved") is obsolete and removed — all three (plus `OPEN-18`) are RESOLVED and every work
  package now inherits the decided arithmetic/policy directly. The long `OPEN-18` "live unresolved dependency
  / provisional labeling" passage is replaced with a short note that D8-WP1 now inherits the decided
  skip-transition table directly. The table's remaining genuine open-item dependencies are narrowed to:
  `OPEN-04` (D8-WP4, naming strings), `OPEN-12`/`OPEN-13` (D8-WP2, with the NT16 interim operating rule),
  `OPEN-14` (D8-WP5, timing only), and `OPEN-05`/`OPEN-06`/`OPEN-07` (D8-WP6, excluded from its pass/fail
  gate). The §5 "Callout" paragraph is rewritten: the rework risk `OPEN-15`/`OPEN-16`/`OPEN-19` previously
  described is retired outright, not merely reduced.
- No change to §0–§3, §6, or §7's substance — the scope statement, gating-reality split, and the six
  proposed work packages/owned paths are unaffected.
