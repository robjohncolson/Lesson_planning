# Answer Equivalence Contract

**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24
**Source of authority:** RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications; NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
**Status:** Authoritative — gates all future Desk / grading / Schoology implementation.

**v2.0 supersedes v1.0.** This deliverable (D5) is substantively UNCHANGED by RC's nine 2026-07-24
rulings — `OPEN-12` and `OPEN-13` are not among the nine items RC resolved, and both remain `OPEN`,
owned by RC. This version bump records only the package-wide provenance update and RC's interim
operating rule for both open items (see `## Open Items` below and the `## Changelog — NT16 (v2.0)`
section at the end of this document).

## Scope

This contract governs how a submitted student answer is checked against the official (expected) answer
stored for a bank item, and — the point of the document — **who or what has authority to decide** at each
step. It is a decision-authority contract, not a math engine. It does not choose a CAS/symbolic library
(OPEN-13) and does not fix numeric-tolerance values (OPEN-12); see §5. It operationalizes **PREF-07 —
Answer evaluation authority**, and cross-references PREF-02 (classroom modality / digital capture), PREF-06
(attempts, recovery & reliability), and PREF-03.9 (clients never determine official credit). Sub-decision
IDs below (`PREF-07.1`–`PREF-07.7`) are the canonical ones already assigned in
`product-policy/RC_TEACHER_PREFERENCE_RECORD.md`; this document does not renumber or re-derive them.

Machine-readable test vectors for this contract live in `product-policy/answer_equivalence_vectors.json`;
`product-policy/test_answer_equivalence_vectors.py` checks the corpus's structural integrity.

## The Four-Tier Separation (PREF-07)

RC's Area 7 decision text states three things: (a) deterministic equivalence decides official correctness
where supported; (b) a teacher review/override path exists for unsupported or disputed forms; (c) AI may
explain but never alone decides correctness or credit. This contract names **four** operational tiers so the
authority boundary at each step is unambiguous. Tiers 2 and 3 both operationalize the single RC clause
`PREF-07.2` — unsupported-form routing and disputed-form human authority are two faces of one decision, not
two separate ones — named separately here only because they have different actors (engine routes vs.
teacher decides) and different failure modes.

**This separation of authority is the point of the document.** Only Tier 1 may act alone. Every other tier
either routes to a human or is explicitly forbidden from deciding credit alone.

### Tier 1 — Deterministic Symbolic/Numeric Equivalence (`PREF-07.1`)

- Where the equivalence check is **supported** for the item's declared policy flags (§4), official
  correctness is decided deterministically. RC's own example: `x + y ≡ y + x`.
- **This tier, and only this tier, can auto-award official credit** — and, symmetrically, it is the only
  tier that may auto-deny credit (a deterministic, provably-wrong submission is `auto-incorrect`, not routed
  to review). **Provenance note:** RC's Area 7 text states the auto-*award* side explicitly ("deterministic
  symbolic/numeric equivalence for official answers where supported"); it does not explicitly say the same
  engine may auto-*deny* (mark a submission incorrect). The auto-deny symmetry recorded here is a structural
  inference, not a direct RC statement — it is supported by `PREF-06.1`/`.2` (unlimited attempts + feedback
  given immediately after submission), which would otherwise require routing every wrong answer to a human
  before the student could see feedback and resubmit. A later reviewer should feel free to challenge this
  inference; it is flagged here so it is not mistaken for something RC said outright.
- Whether a given equivalence class is "supported" at all depends on which CAS/symbolic engine is eventually
  chosen (`OPEN-13`) and, for numeric answers, which tolerance default is set (`OPEN-12`); see §5.

### Tier 2 — Unsupported / Unrecognized Forms (`PREF-07.2`)

- Triggered when the submitted form cannot be parsed, or falls outside the equivalence classes the (not yet
  chosen, `OPEN-13`) engine can prove for this item.
- **Never auto-marked wrong.** This is the critical asymmetry of the whole contract: the **absence of a
  supported equivalence proof is not evidence of incorrectness** — it is only evidence that Tier 1 could not
  reach a verdict. The same shape of reasoning as dossier `PROGRAM_DOSSIER.md` §15 item 1 ("Unknown ≠ zero")
  applies here: absence of proof is not proof of absence.
- Routes to Tier 3. Never silently resolved by Tier 4 (AI is explanation-only, never a credit path — see
  Tier 4 below).

### Tier 3 — Teacher Review and Override (`PREF-07.2`)

- The human path for anything Tier 1 could not decide (Tier 2) or that is disputed.
- **The teacher's decision is authoritative: it overrides any computed result**, including a prior Tier-1
  `auto-incorrect` verdict.
- Composes with `PREF-06.5` (teacher overrides preserved/available) and `PREF-03.7` (teacher override of the
  computed quarter grade is preserved) — override authority is consistent across the answer-level and
  quarter-level surfaces; this document does not reopen either.

### Tier 4 — AI Explanation Only (`PREF-07.3`, `PREF-07.4`, `PREF-07.5`)

- AI may explain, hint, or rephrase why an answer is or is not correct (`PREF-07.3`) — a permitted,
  supporting role.
- **Hard prohibition:** AI **never**, alone, decides official correctness (`PREF-07.4`), and **never**, alone,
  decides grade credit (`PREF-07.5`). These are independent negative constraints — a system could in
  principle judge mathematical correctness without that judgment automatically becoming grade credit; both
  paths are closed here.
- This composes directly with `PREF-03.9`: clients (Desk, Schoology, or any other consumer) never determine
  official credit — that authority is server-side/A2 only. The same boundary applies to AI: an AI-produced
  judgment is a client-side (or client-adjacent) opinion, never the authority of record. Official credit can
  only ever originate from Tier 1's deterministic engine or Tier 3's teacher.
- Tier 4 never itself produces a graded outcome. Every vector in `answer_equivalence_vectors.json` whose
  `decision_authority` is `"ai"` resolves to `route-to-review` — the AI's contribution is advisory, never
  adjudicative.

## Digital Capture Scope (PREF-02)

- `PREF-02.1`/`.2`: classroom modality is paper-first; mathematical thinking and work happen on paper.
- `PREF-02.3`: only teacher-designated answers are entered digitally — not the full worked solution.
- `PREF-02.4`: digital capture of those designated answers **tolerates mathematically equivalent forms** —
  this is exactly what Tiers 1–3 above exist to adjudicate. `PREF-02.4` is the classroom-modality statement
  of the same rule PREF-07 operationalizes end-to-end.
- `PREF-02.5`: pure paper practice (not teacher-designated for digital capture) is **not** graded and **not**
  individually tracked — it never enters this pipeline at all. There is no test vector for "ungraded paper
  practice"; it is out of scope by construction, not an oversight.

## Attempts Interaction (PREF-06)

- `PREF-06.1`: unlimited attempts — no attempt cap.
- `PREF-06.2`: feedback is given after submission, then correction/resubmission. An evaluation (one of the
  four tiers above) always runs before the student's next attempt; it is never silently deferred.
- `PREF-06.6`–`.9` (citing `PROGRAM_DOSSIER.md` §15 items 1, "Unknown ≠ zero," and 2, "Unavailability may not
  relock"): an unknown/unavailable grade state must never render as zero, never as erased work, never as
  fabricated credit, and must never cause erroneous relocking.
- **Operational rule for this contract specifically:** when the evaluator itself cannot run at all
  (infrastructure unavailability — distinct from Tier 2's "engine reachable but form unsupported"), the
  outcome is `UNKNOWN`. `UNKNOWN` routes to Tier 3 (teacher review), the same destination as Tier 2, but it
  is reported and recorded as `UNKNOWN`, never silently folded into `incorrect`, `0`, or erased work. **An
  evaluation that cannot run yields UNKNOWN and routes to review — it never yields "incorrect."**

## What "Equivalent" Means, As Policy

**Provenance note, read before the rest of this section:** RC's Area 7 decision text (§2 of the NT15 shared
brief) establishes the *authority* model — deterministic equivalence decides correctness where supported;
unsupported-or-disputed forms get teacher review; AI never alone decides correctness or credit. It does
**not** enumerate the equivalence categories below, and it does not use the phrase "pedagogical, not
mathematical." Everything in this section — the four categories, the pedagogical-vs-mathematical framing,
and the per-item policy-flag mechanism itself — is this contract's operational elaboration of that authority
model, authorized by the NT15 tranche scope (not a restatement of RC's own words). None of it contradicts
RC's recorded decisions, but all of it is open to correction by RC without that correction touching
`PREF-07.1`–`.7` as recorded in `RC_TEACHER_PREFERENCE_RECORD.md`. In particular, the policy-flag mechanism
is a *mechanism choice* for expressing per-item pedagogical intent, not an RC decision — RC has not decided
that flags (vs. some other mechanism) is how this must be implemented, only that a global rule can't be
right when the same equivalence would be acceptable on one item and not another.

Some equivalence questions are purely mathematical (commutativity holds regardless of pedagogical intent).
Others are **pedagogical, not mathematical** — whether a given pair of forms *should* count as equivalent for
a specific item depends on what that item is assessing. This contract handles that split with a per-item
**policy flag**: each bank item declares, alongside its expected answer, which equivalence classes Tier 1 is
permitted to apply when checking a submission against it. Two items with mathematically identical expected
answers can have different accepted equivalence classes because they assess different skills.

Categories covered (at least):

- **Commutativity / associativity / ordering** — e.g. `x + y` vs `y + x`; `(x + y) + z` vs `x + (y + z)`.
  Essentially always acceptable regardless of item intent (no known item type would want to penalize term
  order in a sum).
- **Equivalent fractions vs. decimals, within a declared tolerance** — e.g. `1/3` vs `0.3333`. The tolerance
  *value* is not fixed by this contract (`OPEN-12`, §5); the *concept* — that a numeric submission within
  tolerance of the expected value is accepted — is part of this policy.
- **Factored vs. expanded form** — e.g. `(x + 2)(x + 3)` vs `x^2 + 5x + 6`. Mathematically equal always.
  Whether they should be treated as *equivalent for grading this item* is pedagogical: if the item's purpose
  is to practice simplifying/solving, expanded and factored forms may both be acceptable; **if the item
  specifically assesses factoring, an expanded answer is mathematically equal but pedagogically wrong** —
  the point of the item was the factoring step itself, and the submission didn't demonstrate it.
- **Unsimplified vs. simplified form** — e.g. `2/4` vs `1/2`. Typically acceptable unless the item is
  specifically assessing simplification.

**This is exactly why a per-item policy flag, not a single global rule, is required.** A global "always
accept factored ≡ expanded" rule would silently defeat every item whose point is the factoring step itself; a
global "never accept" rule would wrongly fail legitimate equivalent submissions on items that don't care
about form. The item's declared flags are the only place this pedagogical judgment is made.

One further distinction that follows directly from the tier model above: when an item's policy does **not**
accept a given form (e.g., "expanded form" on a factoring-assessment item), and the engine can determine
structurally that the submission is in the disallowed form, that is still a **Tier-1, deterministic**
verdict (`auto-incorrect`) — the form-check itself is a checkable fact, independent of whether the two forms
are mathematically equal. This is different from Tier 2, which is for submissions the engine **cannot
characterize at all** (unparseable, or outside every equivalence class it can prove). Do not confuse "policy
declines to accept an equivalence class" (Tier 1, deterministic, can be `auto-incorrect`) with "engine cannot
determine the relationship" (Tier 2, must route to review, never `auto-incorrect`).

The specific flag names used in `answer_equivalence_vectors.json` (e.g. `commutative`, `numeric_tolerance`,
`factored_expanded_equivalent`, `factored_form_required`, `unsimplified_equivalent`) are illustrative naming
for this contract, not a canonical vocabulary RC has fixed. Implementers may rename them as long as the
per-item accept/reject semantics persist.

## Open Items

### `OPEN-12` — Numeric-equivalence tolerance defaults (`PREF-07.6`)

Unresolved: the actual tolerance value(s) (absolute vs. relative, and the threshold) for treating a decimal
submission as equivalent to a fraction/exact-value expected answer. Until RC sets this, any test vector that
depends on a specific tolerance boundary carries the `OPEN-12` token and its `expected_outcome` is
illustrative, not settled policy. **What it unblocks:** the exact boundary between Tier-1 `auto-correct` and
Tier-1 `auto-incorrect` for every numeric-tolerance-bearing item. Without it, only clearly-inside or
clearly-outside cases can be handled by convention — the boundary itself is not settled.

**Interim operating rule (NT16, 2026-07-24 — NOT a resolution of this item).** RC stated an interim rule
that governs answer-evaluation behavior while this item remains open: clearly-deterministic cases may be
accepted; unsupported symbolic/tolerance cases route to teacher review, never auto-fail. This is an
operating rule for implementers to follow in the meantime — it does **not** settle the tolerance value(s)
asked by the Question above, and `OPEN-12` remains `OPEN` and owned by RC.
`product-policy/OPEN_DECISIONS_REGISTER.md`'s `OPEN-12` entry records this identical interim rule; the two
must stay consistent, and neither closes the item.

### `OPEN-13` — CAS / symbolic-equivalence engine choice (`PREF-07.7`)

Unresolved: which CAS/symbolic-equivalence engine or library Tier 1 runs on. This contract deliberately does
not choose one, and does not pick a vendor. **What it unblocks:** the actual boundary of what Tier 1 can
prove at all — e.g. whether factored-vs-expanded equivalence, trig-identity equivalence, or other symbolic
rewrites are provable deterministically depends entirely on engine capability. Until an engine is chosen, any
item requiring symbolic proof beyond simple arithmetic/commutativity should be treated as provisionally
Tier 2 in production, even though this contract's illustrative test vectors assume a baseline-capable engine
for clarity of exposition.

**Interim operating rule (NT16, 2026-07-24 — NOT a resolution of this item).** RC stated an interim rule
that governs answer-evaluation behavior while this item remains open: clearly-deterministic cases may be
accepted; unsupported symbolic/tolerance cases route to teacher review, never auto-fail. This is an
operating rule for implementers to follow in the meantime — it does **not** select an engine or settle the
capability boundary asked by the Question above, and `OPEN-13` remains `OPEN` and owned by RC.
`product-policy/OPEN_DECISIONS_REGISTER.md`'s `OPEN-13` entry records this identical interim rule; the two
must stay consistent, and neither closes the item.

## Cross-References (read-only; not reopened here)

- `PROGRAM_DOSSIER.md` §15, items 1 ("Unknown ≠ zero"), 2 ("Unavailability may not relock"), and 4 ("Server
  ledger + stable student identity are authoritative").
- `product-policy/RC_TEACHER_PREFERENCE_RECORD.md` — canonical `PREF-02`, `PREF-03`, `PREF-06`, `PREF-07`
  sub-decision text and status; this document cites, and does not renumber, those sub-ids.
- `product-policy/answer_equivalence_vectors.json` — machine-readable test-vector corpus for this contract.
- `product-policy/test_answer_equivalence_vectors.py` — exercises the corpus's structural integrity and the
  Tier-2/Tier-4 asymmetry properties (it is not a CAS and does not test symbolic math itself; `OPEN-13` is
  unresolved).

## Changelog — NT16 (v2.0)

**2026-07-24 (v2.0).** RC's nine 2026-07-24 rulings (recorded in `OPEN_DECISIONS_REGISTER.md`) resolved
`OPEN-08, 09, 10, 11, 15, 16, 17, 18, 19` — none of which belongs to this deliverable. `OPEN-12` and
`OPEN-13` are not among them and both remain `OPEN`, owned by RC, unchanged in status. This document is
therefore **substantively unchanged** by NT16 apart from two things:

- The package-wide provenance/version bump (header above; `answer_equivalence_vectors.json`'s top-level
  `version`/`source_of_authority`; `test_answer_equivalence_vectors.py`'s provenance assertions).
- Recording RC's interim operating rule for answer-evaluation behavior while `OPEN-12`/`OPEN-13` remain open
  — clearly-deterministic cases may be accepted; unsupported symbolic/tolerance cases route to teacher
  review, never auto-fail — in each of their `## Open Items` subsections above, mirrored verbatim in
  `OPEN_DECISIONS_REGISTER.md`'s `OPEN-12`/`OPEN-13` entries.

No tier, vector, category, or decision-authority boundary changed; no vector's `expected_outcome` changed;
`answer_equivalence_vectors.json`'s `decision_ids`, `open_item_ids` (`["OPEN-12", "OPEN-13"]`), and
`vectors` array are unchanged in substance. The Four-Tier Separation (§ above), the Digital Capture Scope,
the Attempts Interaction section, and the "What 'Equivalent' Means" section are all unchanged.
