# Product Policy Package Index

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

## 1. What this package is

This is the NT15 product-policy package: the authoritative conversion of RC's 2026-07-24 final
decisions (the Grok preference interview plus RC's direct clarifications on its output) into
machine-checkable contracts that gate all future Desk / grading / Schoology implementation work.
Every decision recorded here traces to RC's own interview text or clarifications — nothing in
this package invents policy. Where RC's text does not settle a question, that question is
recorded as `OPEN` (owner: RC) rather than guessed at; where RC explicitly decided **not** to
build something now, it is recorded as `DEFERRED` (a settled decision, not a pending one). See
`OPEN_DECISIONS_REGISTER.md` for the full distinction and the complete open-item set.

This package is **policy, not implementation**. It specifies structure, rules, contracts, and
verdicts machine-checked against a local reference implementation and synthetic fixtures. It
does not deploy anything, does not connect to any live service, and is not itself dispatched as
build work by virtue of existing (see §6 below).

## 2. The eight deliverables

| Deliverable | File(s) | What it governs | RC area(s) |
|---|---|---|---|
| D1 — RC Teacher Preference Record | `RC_TEACHER_PREFERENCE_RECORD.md` | The fourteen canonical `PREF-NN` decision areas, decomposed into atomic `PREF-NN.M` sub-decisions with `DECIDED`/`OPEN`/`DEFERRED` status. The fidelity anchor for the whole package — every other deliverable cites this document's sub-decision ids rather than restating RC's words. PREF-05.9 preserves RC's own verbatim "reproduce the intended result" phrasing unedited, paired with a clearly delimited **Reconciling annotation (NT15, not RC's words)** block that explains how D3's NOT_NATIVELY_REPRESENTABLE verdict satisfies that intent (answers *how*, not *whether*) without softening or reopening RC's decision text. | PREF-01 … PREF-14 (all) |
| D2 — Grading Policy Specification | `GRADING_POLICY_SPEC.md`, `grading_policy.v2.json`, `grading_policy_ref.py`, `test_grading_policy_ref.py` | Grade composition (WORK / ASSESSMENT aggregates), the 40%-inclusive quarter rule, participation and extra-credit unit values, teacher-override precedence, and UNKNOWN semantics. The JSON is the machine-readable constants source of truth; the `.py` is a runnable reference implementation; the test module is its regression suite. As of NT16 (v2.0), `OPEN-08, 09, 10, 11, 15, 16, 19` are RESOLVED: the exact-ratio threshold comparison, display-only rounding, the `+1.0`/day capped point-based extra-credit ledger, the participation day-eligibility semantics, the point-based WORK formula, UNKNOWN-on-zero-denominator, and the point-weighted same-kind reduction are all DECIDED policy, not placeholders. | PREF-03, PREF-04 |
| D3 — Schoology Projection & Reconciliation Contract | `SCHOOLOGY_PROJECTION_CONTRACT.md`, `schoology_projection.v2.json`, `parity_check.py`, `test_parity_check.py`, `fixtures/schoology/course_section_synthetic.json`, `fixtures/schoology/student_0001_above_gate_convergent.json`, `fixtures/schoology/student_0002_above_gate_divergent.json`, `fixtures/schoology/student_0003_below_gate_divergent.json`, `fixtures/schoology/student_0004_unknown_assessment_evidence.json`, `fixtures/schoology/course_catalog_nt14_b1_edge_cases.json` | The "one policy, two calculations, explicit reconciliation" principle; the native-feasibility verdict on the 40%-conditional formula (NOT natively representable in Schoology's category/weight model); assignment/category mapping; the deep-link contract; idempotency rules; divergence handling; the **fail-closed release-gating convention** (`_classify_entry`/`_should_project` — a missing/unrecognized `lesson_state` or a present-but-malformed `availability`/`explicitly_assigned` value never defaults to permission; the real NT14 `availability` marker is honored independently of, and with priority over, a permissive `lesson_state`); **anomaly surfacing** (`detect_projection_anomalies()` — a malformed record fails closed AND is reported to RC as a structured anomaly, never silently dropped); every reconciliation report names its `schoology_computation_mode` so no comparison runs under an unstated assumption. Synthetic-fixture-only — see §6's NO-LIVE-WRITE constraint. NT16 (v2.0) target: inherits D2's now-decided `OPEN-15`/`OPEN-19` arithmetic and the `OPEN-09` display-vs-internal rounding split (landed by a concurrent NT16 work package). | PREF-05, PREF-11, PREF-03 (projected) |
| D4 — Desk Lesson-State Model | `DESK_STATE_MODEL.md`, `desk_state_model.v2.json`, `test_desk_state_model.py` | The seven canonical Desk lesson states; the transition table — as of NT16 (v2.0), **decided** `transitions.legal` now holds all eighteen transitions T1–T18 (T7/T11/T12/T13 promoted per RC's 2026-07-24 `OPEN-18` ruling; T11 carries a machine-readable pre-completion precondition) and `transitions.provisional` is permanently empty, retired with a `transitions.provisional_retirement` provenance object — plus illegal transitions (X1–X19); the two-view visibility matrix; the optional-catalog rule; and the reliability invariants (unknown ≠ zero, no relock, fail-open-never-credits). `completed` is DECIDED terminal (`OPEN-17`) with an orthogonal `retake_affordance` object. | PREF-01, PREF-06, PREF-13, PREF-14 |
| D5 — Answer Equivalence Contract | `ANSWER_EQUIVALENCE_CONTRACT.md`, `answer_equivalence_vectors.json`, `test_answer_equivalence_vectors.py` | The four-tier answer-evaluation authority separation (deterministic engine / unsupported-form routing / teacher review / AI-explanation-only), the pedagogical-vs-mathematical equivalence framing, and a machine-readable test-vector corpus. Substantively unchanged by NT16 — `OPEN-12`/`OPEN-13` remain OPEN; the only NT16 addition is RC's interim operating rule (clearly-deterministic cases may be accepted; unsupported symbolic/tolerance cases route to teacher review, never auto-fail). | PREF-07 (with PREF-02, PREF-06 cross-cutting) |
| D6 — Phased Product Sequence | `PHASED_PRODUCT_SEQUENCE.md` | Dependency-ordered build phases (A: academic core, B: reward economy, C: TI-84 trainer, D: Equation Lab), the reward-seam architecture Phase A must preserve for Phase B, and the deferred-item list. Contains no calendar dates, durations, sprint counts, or quarter labels by design — sequence and dependency order only. As of NT16 (v2.0), §2's dependency-direction note reflects `OPEN-17` as RESOLVED (`completed` terminal; retake orthogonal, implementation deferred to the work packages). | PREF-01, PREF-03–PREF-14 (sequencing) |
| D7 — Open Decisions Register | `OPEN_DECISIONS_REGISTER.md` | The single canonical list of every question ever raised across the package (`OPEN-01`…`OPEN-19`) — **10 still OPEN, 9 RESOLVED** as of RC's 2026-07-24 rulings — each with its question, owner (always RC), status, and (once resolved) RC's ruling and what it supersedes. OPEN-18's entry describes RC's ruling promoting T7/T11/T12/T13 from D4's now-retired `transitions.provisional` bucket into `transitions.legal` (never presented as still-provisional). Also states explicitly which matters are `DEFERRED` (not open) and which are already `DECIDED` (also not open), and — new as of NT16 — that a `RESOLVED` entry keeps its heading, question, and original reasoning permanently, alongside its ruling. | Cross-cutting (traces back to whichever PREF area raised each item) |
| D8 — Next Tranche Proposal | `NEXT_TRANCHE_PROPOSAL.md` | A **proposal, not an authorization** — the recommended first implementation tranche (Phase A only), six work packages with acceptance criteria, and an explicit accounting of which OPEN items each work package can proceed without resolving. As of NT16 (v2.0), the acceptance criteria for D8-WP1/D8-WP3/D8-WP4 and the §5 open-item table are rewritten to inherit RC's 2026-07-24 rulings (`OPEN-08/09/10/11/15/16/17/18/19`) directly rather than scope around a placeholder. | PREF-01–PREF-14 (recommends scope; decides nothing) |
| Package index (this file) | `INDEX.md` | Orientation and navigation for the whole package. | — |
| Package consistency suite | `test_policy_package.py` | Machine-checks cross-document consistency across all of the above (see §5). | — |
| RC-rulings acceptance-proof suite (NT16 work package F) | `test_rc_rulings_acceptance.py` | Thirteen explicitly-numbered, docstring-cited proofs (`test_proof_01`…`test_proof_13`) — one small, auditable file a reviewer can read start to finish to confirm each of RC's nine 2026-07-24 rulings (`OPEN-08/09/10/11/15/16/17/18/19`) is discriminatingly demonstrated by calling the real reference implementations (`grading_policy_ref.py`, `parity_check.py`) and reading the real artifacts (`desk_state_model.v2.json`) and fixtures, never by re-implementing a formula and comparing it to itself. Duplicates no sibling suite's regression job — it is the consolidated acceptance layer on top of it. | PREF-03, PREF-04, PREF-01, PREF-06, PREF-13 |

## 3. Reading order

1. **Start with D1** (`RC_TEACHER_PREFERENCE_RECORD.md`) — it is the fidelity anchor. Every
   `PREF-NN.M` id cited anywhere else in this package traces back to a row in this document, and
   its provenance section explains the `DECIDED` / `OPEN` / `DEFERRED` vocabulary used
   throughout.
2. **Check D7** (`OPEN_DECISIONS_REGISTER.md`) before assuming any value RC's text doesn't
   spell out verbatim. If a question isn't settled in D1, it has exactly one entry here
   (`OPEN-01`…`OPEN-19`), owned by RC. No other document in this package — and no downstream
   implementer — may guess a value for something listed here.
3. **Then the deliverable relevant to your work**: D2 for grading, D3 for Schoology, D4 for
   Desk navigation/state, D5 for answer evaluation.
4. **D6 and D8** for sequencing: D6 is the dependency-ordered phase plan; D8 is a proposed
   first tranche against it (not an authorization — see §6).

## 4. How to run the tests

From the repository root:

```
python -m pytest product-policy/ -q
```

Standard library + pytest only; no extra dependencies; no network access required or
performed. Each `.py`/`.json` pair (D2–D5) has its own dedicated regression suite;
`test_policy_package.py` is the package-wide cross-document consistency suite (see §5).

## 5. Package invariants — what `test_policy_package.py` enforces

- **File manifest.** Every deliverable file, JSON artifact, fixture, and test module listed in
  §2 actually exists on disk.
- **Provenance headers.** Every `.md` deliverable carries `**Version:** 2.0`, `**Date:**
  2026-07-24`, and the RC 2026-07-24 source-of-authority line (including the NT16-rulings clause);
  every `.json` policy/contract artifact carries matching `version` / `date` / `source_of_authority`
  top-level keys.
- **Constants agree, JSON-first.** `grading_policy.v2.json`'s constants (0.40 inclusive
  threshold, 1.0/0.0 participation, 0.5/0.5 extra credit, the `+1.0`/day extra-credit cap, and the
  one-decimal final-grade display rounding) are the source of truth; `GRADING_POLICY_SPEC.md`'s
  prose is checked against them, not the reverse.
- **Desk states match everywhere.** The same seven, identically spelled, in
  `desk_state_model.v2.json`, `DESK_STATE_MODEL.md`, and `RC_TEACHER_PREFERENCE_RECORD.md`'s
  PREF-01.1 row — and that row itself still distinguishes the five RC-named Area-1 states from
  the two NT15 operational additions (`completed`, `temporarily-unavailable`); a row that
  re-flattens all seven into a single undifferentiated "RC decided" list is a regression.
- **Desk transitions are now fully decided, and the retired provisional bucket stays retired.**
  `desk_state_model.v2.json`'s `transitions.legal` table contains all eighteen transitions
  (T1–T18) — including T7, T11, T12, and T13, promoted by RC's 2026-07-24 ruling resolving
  `OPEN-18` — each carrying an `actor` field (`teacher` / `system_evidence` / `teacher_only`), and
  every skip/unskip transition (T3, T7, T11, T12, T13) additionally carrying
  `student_may_initiate: false`. `transitions.provisional` is permanently empty; its
  `transitions.provisional_retirement` object records the promotion history rather than silently
  losing it. The three buckets (`legal`, `provisional`, `illegal`) remain pairwise disjoint;
  nothing in `transitions.legal` may carry a stale `normative: false` or `open_item` tag, and
  T11's machine-readable pre-completion `precondition` must be present and enforced.
  `DESK_STATE_MODEL.md` and `NEXT_TRANCHE_PROPOSAL.md` both present T7/T11/T12/T13 as decided
  policy, never as provisional/unresolved/non-normative, outside an explicitly historical
  changelog or superseded-note context — this was the direct resolution of Codex GPT-5.6 SOL
  review finding B2 (HIGH), which is no longer a live concern now that RC has ruled.
- **The register inventory is exactly 10 open / 9 resolved.** `OPEN_DECISIONS_REGISTER.md` carries
  all nineteen `OPEN-NN` headings, with the resolved set being exactly `{OPEN-08, 09, 10, 11, 15,
  16, 17, 18, 19}` and the open set exactly `{OPEN-01…07, 12, 13, 14}` — no silent disappearance of
  a heading, and no drift in which nine are resolved.
- **Every resolved item carries its provenance token; no open item does.** Each of the nine
  resolved ids carries the `RESOLVED by RC 2026-07-24` token in the register; none of the ten
  still-open ids does.
- **No stale "still open" phrasing survives next to a resolved id.** None of the nine resolved
  ids appears adjacent to "unresolved-pending-RC" / "PROVISIONAL" language in D1–D5 outside an
  explicitly historical changelog / superseded-note context.
- **`completed` has zero outbound legal transitions, and `completed → skipped` is illegal.**
  `completed` never appears as a `from` state in `transitions.legal`, and `completed → skipped`
  (X3) appears in `transitions.illegal` — both DECIDED per `OPEN-17`/`OPEN-18`.
- **`grading_policy.v2.json` carries no open grading items.** Its `open_item_ids` is `[]` and its
  `resolved_open_item_ids` is non-empty; the old `provisional_implementation_choices` block is
  gone, replaced by `resolved_open_items`.
- **The open register is complete in both directions.** Every `OPEN-NN` token used anywhere in
  D1–D5 has a register heading; every register heading is used at least once; the register is
  exactly `OPEN-01`…`OPEN-19` with no gaps or duplicates.
- **DEFERRED and DECIDED never leak into the register as OPEN.** The three deferred matters
  (step-by-step enforcement, gifting/Tetris/leaderboards/celebration noise, intervention/makeup/
  enrichment) have no register heading; the 40%-gate's DECIDED inclusivity is not presented as
  unresolved.
- **All fourteen PREF areas are covered**, `PREF-01` through `PREF-14`, no gaps, in
  `RC_TEACHER_PREFERENCE_RECORD.md`.
- **Deferred features stay deferred in the sequencing documents.** Every mention of gifting,
  Tetris, leaderboards, celebration noise, step-by-step enforcement, or intervention/makeup/
  enrichment in D6/D8 sits inside a deferred-or-out-of-scope context — never scheduled into a
  live phase.
- **NO-LIVE-WRITE and no-network are real, checked properties**, not just prose promises: the
  Schoology contract's NO-LIVE-WRITE constraint is stated normatively, and no `.py` file
  anywhere in this package imports a network library (`requests`, `httpx`, `urllib.request`,
  `socket`, `http.client`, `aiohttp`).
- **D6 carries no dates.** `PHASED_PRODUCT_SEQUENCE.md` contains no calendar dates, durations,
  sprint counts, or quarter labels anywhere in its body — sequence and dependency order only,
  consistent with RC's pacing decisions (`PREF-13`).
- **RC's verbatim words are never silently softened, and never left unexplained either.**
  PREF-05.9's "reproduce the intended result" phrase is RC's own recorded wording and stays
  exactly as she said it — but it never appears in D3 (`SCHOOLOGY_PROJECTION_CONTRACT.md` /
  `schoology_projection.v2.json`), where it would misstate D3's own NOT_NATIVELY_REPRESENTABLE
  finding as native parity. D1's reconciling annotation, which explains that D3 answers *how*
  RC's intent is satisfied rather than *whether*, must stay present alongside the verbatim
  phrase — deleting the annotation while keeping the bare phrase is as much a regression as
  softening the phrase itself.
- **The fail-closed / decided-teacher-authority story agrees across D3, D4, and D7 — not just
  within each document alone.** D4's `desk_state_model.v2.json` now places T7/T11/T12/T13 in the
  decided `transitions.legal` table, each carrying `actor: "teacher_only"`; D3's contract §3 and
  its JSON's `release_gating` state the fail-closed convention that produced the same discipline
  for optional-catalog gating (unrecognized/malformed values never default to permission) — that
  half of the story is unchanged by NT16; D7's OPEN-18 register entry names the same promotion,
  from the retired `transitions.provisional` bucket into `transitions.legal`, with the same four
  ids and the same teacher-only authority. All three must agree that these four ids are now
  decided and teacher-only, not merely each be self-consistent in isolation.
- **Every reconciliation report names its computation mode and cites no dangling assumption.**
  `schoology_projection.v2.json`'s `divergence_handling.report_fields` includes
  `schoology_computation_mode`; every `ASSUMPTION-N` `parity_check.py` relies on has a
  corresponding "Assumption to confirm (ASSUMPTION-N):" prose definition in
  `SCHOOLOGY_PROJECTION_CONTRACT.md` — no code comment points at an assumption number the
  contract never explains.
- **The RC-rulings acceptance-proof suite is itself tamper-evident.**
  `test_rc_rulings_acceptance.py` must define exactly thirteen `test_proof_NN_*` functions,
  numbered `01` through `13` with no gaps or duplicates (parsed with `ast`) — a silently
  dropped, duplicated, or renumbered proof fails this guard rather than passing unnoticed.
- **No live stale `v1.json` reference survives anywhere in the package.** Every mention of
  `grading_policy.v1.json`, `desk_state_model.v1.json`, or `schoology_projection.v1.json` across
  every `.md`/`.py`/`.json` file must sit inside an explicitly historical context (a changelog
  section, a `Supersedes` block, a rename-arrow note, or similar) — reusing this suite's own
  row/paragraph-scoping helper and historical-marker list rather than a second mechanism; a bare
  mention with no such marker nearby reads as a live pointer at a file that no longer exists and
  fails the guard. The three `.v1.json` files are also asserted absent from disk directly. (Codex
  review C6.)
- **`grading_policy.v2.json`'s display rounding MODE is declared and explicitly labeled, once the
  sibling D2 work landing it.** RC's `OPEN-09` ruling fixed display *precision* (one decimal) but
  never specified the rounding MODE; the `display_rounding_mode` field must name half-even
  rounding AND explicitly mark that reading as an implementation choice pending RC confirmation
  (checked for both substrings) — never presented as if RC had settled the mode herself. This
  guard is tamper-evident in the other direction too: stripping the caveat and presenting the
  mode as settled policy fails it. (Codex review C5, implementation half.)
- **The register's `OPEN-09` entry names its residual rounding-mode question while staying
  `RESOLVED`.** `OPEN_DECISIONS_REGISTER.md`'s `OPEN-09` section must carry both the
  `RESOLVED by RC 2026-07-24` token and a clearly labeled residual note naming the half-even
  reading and flagging it as pending RC confirmation, pointing at `display_rounding_mode` — a
  resolved item may carry a flagged residual sub-question without reopening. (Codex review C5,
  register half.)
- **AMENDMENT/CONFIRMATION NOTE (2026-07-24, later same date; NT16-B) — historical guards above,
  now superseded.** Both residual "pending RC confirmation" readings the two bullets above
  describe were later directly resolved by RC, the same date: `display_rounding_mode`'s
  half-even reading is AMENDED to half-up (decimal `ROUND_HALF_UP`, RC's own worked example
  `89.25 -> 89.3`), and OPEN-11's excused-vs-unknown reading is CONFIRMED as already
  implemented. See `GRADING_POLICY_SPEC.md` §4.1/§9 and `OPEN_DECISIONS_REGISTER.md`'s
  OPEN-09/OPEN-11 sections for RC's verbatim rulings. `test_policy_package.py`'s two guards
  described above are updated accordingly: they now require the half-up mode and the
  amendment's provenance, rather than half-even and "pending RC confirmation" — the bullets
  above are left as the historical record of what those guards ONCE required, not a live
  description of their current wording.

## 6. Status and scope boundary

- **This package is policy, not implementation.** Nothing in `product-policy/` is deployed, and
  nothing here is itself a build instruction. D8's work packages are a **recommendation**
  requiring separate sign-off before dispatch (see `NEXT_TRANCHE_PROPOSAL.md` §0).
- **The Schoology contract (D3) is synthetic-fixture-only, under a binding NO-LIVE-WRITE
  constraint.** Real Schoology course/section identifiers do not exist yet. No file in this
  package performs, or is permitted to perform, a network call, HTTP request, OAuth handshake,
  or CDP/browser automation step against a live Schoology tenant — see
  `SCHOOLOGY_PROJECTION_CONTRACT.md` §9.
- **This package is not committed by this tranche.** Its existence on disk does not constitute
  approval to build against it; it is offered so a later reader (the NT15 manager, Fable, or RC)
  has something concrete to review, amend, or authorize.

## Changelog — NT16 (v2.0)

**2026-07-24 (v2.0).** RC issued nine rulings resolving `OPEN-08, 09, 10, 11, 15, 16, 17, 18, 19`
(`OPEN_DECISIONS_REGISTER.md`). Substantive changes by deliverable:

- **D1 — RC_TEACHER_PREFERENCE_RECORD.md.** Updated in place by its own owning agent (see that
  document's own provenance/changelog); this package-wide index cites its new status but does not
  itself modify D1.
- **D2 — Grading Policy Specification.** Substantive. `grading_policy.v1.json` →
  `grading_policy.v2.json`: resolves `OPEN-08` (exact-ratio threshold comparison), `OPEN-09`
  (display-only rounding), `OPEN-10` (`+1.0`/day extra-credit cap), `OPEN-11` (participation
  day-eligibility semantics), `OPEN-15` (point-based WORK formula), `OPEN-16` (UNKNOWN on zero
  denominator), and `OPEN-19` (point-weighted same-kind reduction).
- **D3 — Schoology Projection & Reconciliation Contract.** Substantive (landed by a concurrent
  NT16 work package; not owned by this update) — `schoology_projection.v1.json` →
  `schoology_projection.v2.json`.
- **D4 — Desk Lesson-State Model.** Substantive. `desk_state_model.v1.json` →
  `desk_state_model.v2.json`: resolves `OPEN-17` (`completed` DECIDED terminal; retake is an
  orthogonal affordance) and `OPEN-18` (T7, T11, T12, T13 promoted from the now-retired
  `transitions.provisional` bucket into `transitions.legal`; T3 and X3 confirmed).
- **D5 — Answer Equivalence Contract.** Version-bump only. `OPEN-12`/`OPEN-13` remain OPEN; the
  only content change is recording RC's NT16 interim operating rule in the `## Open Items` section
  (clearly-deterministic cases may be accepted; unsupported symbolic/tolerance cases route to
  teacher review, never auto-fail) — not a resolution of either item.
- **D6 — Phased Product Sequence.** Version-bump plus one substantive update: §2's
  dependency-direction note now reflects `OPEN-17` as resolved (`completed` terminal; retake
  orthogonal, implementation deferred to the work packages) rather than open. No calendar dates,
  durations, sprint counts, or quarter labels were introduced.
- **D7 — Open Decisions Register.** Substantive (landed by a concurrent NT16 work package; not
  owned by this update) — register status moves from 19 open / 0 resolved to 10 open / 9 resolved.
- **D8 — Next Tranche Proposal.** Substantive. §4's acceptance criteria for D8-WP1 (criteria 2,
  2a, 5) and D8-WP3 (criteria 1, 5, 6) updated to the decided semantics; D8-WP4 gained criteria
  7–8 (display-rounding-aware reconciliation, no-fabricated-zero); §5's open-item dependency table
  and governing rule rewritten — the "no package may depend on `OPEN-17`/`OPEN-15`/`OPEN-19`"
  rule is retired, and the rework-risk callout for `OPEN-15`/`OPEN-16`/`OPEN-19` is marked retired
  rather than merely reduced.
- **INDEX.md (this file) and `test_policy_package.py`.** Version-bump, file-manifest update to the
  `.v2.json` names, and the package-invariants section (§5 above) rewritten from a
  two-normativity-tier (decided-vs-provisional) story to a fully-decided-state story, with new
  guards for the register's 10-open/9-resolved inventory, provenance-token presence, stale-phrase
  absence, `completed`'s zero-exit guarantee, and `grading_policy.v2.json`'s empty
  `open_item_ids`.

**D3 note.** As of this changelog entry, the D3 work package
(`SCHOOLOGY_PROJECTION_CONTRACT.md`, `schoology_projection.v2.json`, `parity_check.py`,
`test_parity_check.py`, its fixtures) is a concurrent, separately-owned NT16 update; this index
cites its target `.v2.json` name and resolved-item set for completeness but does not itself
modify any D3 file.

**NT16 work package F addition.** `test_rc_rulings_acceptance.py` was added: the consolidated,
explicitly-numbered thirteen-proof acceptance suite for RC's nine 2026-07-24 rulings
(`OPEN-08/09/10/11/15/16/17/18/19`), registered in `test_policy_package.py`'s file manifest
(`TEST_MODULE_FILES`) alongside a new tamper-evidence guard checking its proof count/numbering.

**Codex-review remediation round (C5 register half, C6).** `NEXT_TRANCHE_PROPOSAL.md`'s one
remaining live-stale `desk_state_model.v1.json` reference (§2, D2–D5 reference-implementation
list) is corrected to `desk_state_model.v2.json` (C6); every other `.v1.json` mention in the
package was re-swept and confirmed to already sit in legitimate historical/rename-provenance
context, left unchanged. `OPEN_DECISIONS_REGISTER.md`'s `OPEN-09` entry gains a clearly labeled
residual note recording that RC's ruling settled display rounding *precision* but not the
rounding *mode*, that the implementation reads the mode as half-even and flags that reading for
RC confirmation (pointing at `grading_policy.v2.json`'s `display_rounding_mode` field, landed by
a concurrent sibling D2 work package), and that this residual does not reopen `OPEN-09` or change
the 10-open/9-resolved inventory — following the same labeled-reading precedent already
established for `OPEN-11`'s excused-vs-unknown case. The register's purpose section gained one
paragraph making that resolved-entry-with-a-flagged-residual pattern explicit. `test_policy_
package.py` gained three new guards (see §5 above): the stale-`v1.json` sweep, the labeled
`display_rounding_mode` check (expected red until the sibling D2 work lands the field), and the
`OPEN-09` residual-note check.

**NT16-B amendment/confirmation (2026-07-24, later same date) — forward pointer, history above
left unchanged.** RC directly resolved both residual readings the Codex-review remediation round
above had flagged as "pending RC confirmation": OPEN-09's display rounding MODE is AMENDED to
half-up (decimal `ROUND_HALF_UP`; RC's own worked example, `89.25 -> 89.3`), and OPEN-11's
excused-vs-unknown reading is CONFIRMED as already correctly implemented. Neither reopens its
OPEN-NN id nor mints a new one. `grading_policy_ref.py`'s `round_final_grade_for_display` is
rewritten accordingly; `grading_policy.v2.json`'s `rounding_rules.display_rounding_mode`,
`GRADING_POLICY_SPEC.md` (§4.1, §9), and `OPEN_DECISIONS_REGISTER.md` (`OPEN-09`, `OPEN-11`)
carry RC's verbatim rulings with provenance. `test_policy_package.py`'s `display_rounding_mode`
guard and `OPEN-09` residual-note guard (§5 above) are updated to require the half-up/amendment
language instead of half-even/pending-confirmation — the historical half-even mention itself is
not forbidden, only no longer presented as current, unconfirmed policy.
