# DOK Verification Workflow

Scope: the 900 registry rows across the 10 lessons that currently have
questionbank content (`3-5, 4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5`).
The current dok_status totals live in
`inventory/content_readiness_inventory.json` (regenerated per this
document's approval procedure; the registry-derived BASE totals
`known_auto=421, unreviewed=437, calibrated=42` are invariant while the
registry stays frozen, and the displayed totals move as rows verify —
the first real verifications landed 2026-07-22, NT10: RC's 39 lesson-5-4
batch confirmations). This document defines the order in
which rows get reviewed, the precise bar for calling a row's DOK
`verified`, and the enforcement points that keep unverified DOK from
reaching students or grades in the meantime.

Machine-readable source of truth: **`inventory/dok-workflow/dok_wave_plan.json`**,
produced by **`inventory/dok-workflow/gen_dok_wave_plan.py`** (read-only against
`questionbank/registry.jsonl` + `questionbank/calibration/*.json` +
`inventory/dedup/item_uid_alias_map.json` for the BASE `dok_status`, plus
`tools/dok-review/review_log.jsonl` + `tools/dok-review/rubric_approvals.json`
— via an import of `tools/dok-review/dok_review.py`, never a local
reimplementation — for the `verified` overlay and the additive
`review_state` field; none of these five inputs are ever mutated).
Re-run the generator any time the registry OR the review log OR the
approvals manifest changes to refresh the plan. The generator asserts its
own wave counts, BASE `dok_status` totals, and canonical-projection
fail-closed invariants against the figures in this document before it will
write the file — if the assertions fail, treat that as the plan being
wrong, not this document.

**For the full operational procedure that actually produces a real
approval and a real verified item** — the manifest hand-edit, how reviews
get recorded, the exact regeneration order across all five downstream
consumers once the first item verifies, and what fails loudly (and how) if
a step is skipped or misordered — see
"[Approval procedure (operational, named updates)](#approval-procedure-operational-named-updates)"
near the end of this document.

## Identity key

`item_uid` — not the legacy `id` — is the primary identity key across this
entire workflow: the wave plan, the review log, progress accounting, and
promotion onto the registry. `questionbank/registry.jsonl` has 900 rows but
only 815 unique legacy `id` strings; 85 ids are each shared by 2 distinct
rows (170 rows total), always at different DOK/wave. Concretely,
`5-4-savvas-q41` is registry line 299 (`dok=2`, `role=None`, wave 4) **and**
registry line 328 (`dok=3`, `role=dok3-driver`, wave 3) — two different
rows. Keying any part of this workflow off legacy `id` alone would treat
those as one item and let a single review/promotion silently credit both
rows at two different DOK/wave values.

`gen_dok_wave_plan.py` resolves this by joining each registry row (by its
1-based line number) to the opaque, per-row `item_uid` recorded in
`inventory/dedup/item_uid_alias_map.json` (900 distinct uids for 900 rows —
mirroring `inventory/course-map/build_course_map.py`'s identical node-identity
join). Every item in `dok_wave_plan.json` therefore carries `item_uid` as
its primary key, plus `registry_line`, with the legacy `id` retained only
for display. The two `5-4-savvas-q41` rows now carry two different
`item_uid`s (one at wave 3, one at wave 4), so they can never be conflated.
`REVIEW_INTERFACE_SPEC.md`'s data model (review log, queue, progress views,
and the `qb_promote.py` sketch) keys on `item_uid` for exactly this reason —
see its "Identity key" note for the full detail.

## (a) Wave Order

Every row is assigned to exactly one wave, first rule that matches wins:

| Wave | Name | Rule | Rows |
|---|---|---|---|
| 0 | Calibration / tool-validation | `lesson == 3-5` | 42 |
| 1 | Assessment-feeding DOK-3 spines | `lesson in {4-3,4-5,6-4}` AND `role == dok3-driver` | 4 |
| 2 | Assessment-feeding lesson bodies | `lesson in {4-3,4-5,6-4}` (all remaining rows) | 220 |
| 3 | Remaining DOK-3 spines | `role == dok3-driver` (outside the assessment-feeding lessons) | 7 |
| 4 | Remaining lesson bodies | everything else | 627 |

**900 rows total.**

Per-(wave, lesson) breakdown:

| Wave | Lesson | Rows |
|---|---|---|
| 0 | 3-5 | 42 |
| 1 | 4-3 | 2 |
| 1 | 4-5 | 1 |
| 1 | 6-4 | 1 |
| 2 | 4-3 | 72 |
| 2 | 4-5 | 80 |
| 2 | 6-4 | 68 |
| 3 | 4-4 | 1 |
| 3 | 5-1 | 1 |
| 3 | 5-4 | 1 |
| 3 | 5-5 | 1 |
| 3 | 6-3 | 1 |
| 3 | 6-5 | 2 |
| 4 | 4-4 | 90 |
| 4 | 5-1 | 131 |
| 4 | 5-4 | 131 |
| 4 | 5-5 | 95 |
| 4 | 6-3 | 99 |
| 4 | 6-5 | 81 |

### Rationale per wave

- **Wave 0 (3-5, 42 rows).** 3-5 is the only lesson with a real hand-authored
  calibration file (non-empty `dok2_anchors`/`dok3_anchors`) — every other
  lesson's calibration file has empty anchors. Verifying 3-5 first is a fast,
  high-confidence confirm pass (all 3-5 rows are `dok_status=calibrated`,
  the strongest pre-verification signal available) that also validates the
  review tool end-to-end and calibrates reviewer judgment before touching
  any lesson where DOK is still provisional (`known_auto`/`unreviewed`).
- **Wave 1 (4 rows: the assessment-feeding DOK-3 spine items).** These are
  the highest-criticality items in the whole registry: each is the
  `dok3-driver` for its lesson (the item that anchors the lesson's
  single-DOK3-spine claim to students) **and** its lesson feeds a
  downstream LEHS/topic assessment (4-3, 4-5, 6-4). Includes the 4-3 derived
  disagreement (`4-3-savvas-q36-partC-evaluate-fairness`, see (b) below).
- **Wave 2 (220 rows: the rest of 4-3/4-5/6-4).** Same three
  assessment-feeding lessons, all remaining rows (mostly
  `explore-practice`). Still highest downstream criticality, just not the
  DOK-3 spine item itself.
- **Wave 3 (7 rows: remaining DOK-3 spines).** The `dok3-driver` rows in
  the six non-assessment-feeding lessons (4-4, 5-1, 5-4, 5-5, 6-3, 6-5).
  Still the highest-leverage single item per lesson (the DOK-3 claim
  everything else in that lesson's Explore/Share phase is built around),
  just lower downstream criticality than Wave 1.
- **Wave 4 (627 rows: everything else).** The bulk of `explore-practice`,
  `explore-tps`, `optional-stretch`, `launch-model-*`, `do-now-*` rows in
  the six non-assessment-feeding lessons.

`dok3-driver` items always sort to the front of their tier (Wave 1 before
the rest of Wave 2's lesson body, Wave 3 before Wave 4's lesson body), and
assessment-feeding lessons (4-3/4-5/6-4) always clear before any
non-assessment-feeding lesson. Full intra-wave ordering used by the
generator: (a) assessment-linked lessons first, (b) role rank
(`dok3-driver` < `launch-model-1` < `launch-model-2` < `do-now-bridge` <
`do-now-explore` < `explore-practice` < `explore-tps` < `optional-stretch`
< other), (c) `dok_status` risk rank (`known_auto` < `unreviewed` <
`calibrated` < `verified` — weakest signal reviewed first), (d) lesson
curriculum order, (e) Savvas item number ascending. See the generator's
docstring for the exact composite sort key.

### What each wave unblocks

- **Wave 0** unblocks: confidence that the review tool/workflow itself
  works, using the one lesson where "correct" is already known.
- **Wave 1** unblocks: the four DOK-3 claims that most directly touch
  assessment content — sign off here before any assessment-facing lesson
  can honestly present its DOK-3 driver as reviewed.
- **Wave 2** unblocks: the full 4-3/4-5/6-4 lesson bodies — after this wave,
  the three assessment-feeding lessons are fully reviewed end to end.
- **Wave 3** unblocks: the DOK-3 spine claim in each of the remaining six
  lessons — the single highest-leverage item per lesson.
- **Wave 4** unblocks: full registry coverage — once this clears, `verified`
  should equal `registry_rows` for every lesson in scope.

## (b) Acceptance Criteria for DOK -> `verified`

### The canonical projection

**A DOK is `verified` iff the item_uid's LATEST entry in
`tools/dok-review/review_log.jsonl` (append order — the last line for that
item_uid wins, never sorted by timestamp) satisfies
`entry_is_verified()` in `tools/dok-review/dok_review.py`, evaluated under
the rubric-approvals manifest at `tools/dok-review/rubric_approvals.json`.**
This is the ONE canonical predicate. Every consumer — the review tool
itself (`tools/dok-review/dok_review.py`'s `queue`/`progress`/`report`
commands), the wave-plan generator
(`inventory/dok-workflow/gen_dok_wave_plan.py`, which imports
`dok_review.py` rather than reimplementing any part of this), and this
document — agree on it because there is exactly one implementation, not
three parallel ones.

`gen_dok_wave_plan.py` computes this by: reading the log
(`dok_review.read_log_entries`), reducing to one latest entry per item_uid
(`dok_review.latest_entries_by_uid`), loading the approvals manifest
(`dok_review.load_rubric_approvals`), and calling
`dok_review.tool_state_for(item_uid, latest, approved)` for every item. The
result is surfaced on the wave plan as a NEW, additive per-item field,
`review_state`, and the plan's `dok_status` reads `'verified'` exactly when
`review_state == 'verified'` — never otherwise.

### The two-tier model: REVIEWED vs. VERIFIED

`dok_review.py`'s module docstring and its `entry_is_verified` /
`entry_is_malformed` / `tool_state_for` docstrings are the source of truth
for this section; what follows mirrors them. Two tiers, and they are not
the same thing:

- **REVIEWED** (`tool_state` `reviewed_once`) — a log entry exists for the
  item_uid that clears the baseline well-formedness bar
  (`entry_is_malformed()` returns False): non-empty `reviewed_by`, a
  parseable aware ISO-8601 `reviewed_at`, a recognized `decision`
  (`confirm` / `change` / `needs-source-check`), and decision-specific
  completeness (a `change` needs a valid `new_dok` in {1,2,3}, non-empty
  `rationale` and `provenance`, and a valid `item_basis`; a
  `needs-source-check` needs non-empty `rationale`; a `confirm` needs a
  recognized `confirmation_basis`). A reviewer having looked at an item and
  recorded *something well-formed* is REVIEWED. It is NOT, by itself,
  VERIFIED.
  - A latest entry that fails even this baseline bar reports `tool_state`
    `invalid-entry` — NOT `reviewed_once`. This is a distinct failure mode
    from "reviewed but not yet verification-grade."
- **VERIFIED** (`tool_state` `verified`) — strictly stronger than REVIEWED.
  `entry_is_verified()` returns True only when ALL of the following hold on
  the item_uid's latest entry:
  1. The entry is well-formed (reviewed_by/reviewed_at as above) and
     records a **resolved, verification-grade disposition**:
     - `decision == "confirm"` AND `confirmation_basis ==
       "rule-1-textbook-provenance"` — the confirm's `--provenance` (scheme
       `calibration-anchor:<lesson>:<item-ref>`) resolved, at entry time,
       to a real on-disk calibration anchor **bound to that same item**
       (see "Item-bound rule-1 provenance" below); OR
     - `decision == "change"` AND `new_dok` in {1,2,3} AND non-empty
       `rationale` AND non-empty `provenance` (rule 5: an override needs
       both) AND `item_basis` in `{textbook-exact, adapted, split,
       extended, teacher-authored}`, where `textbook-exact` is
       verification-grade ONLY when `provenance_resolved is True` (a
       source-dispute resolution needs resolved provenance), and the other
       four bases are rated by actual cognitive demand and accept
       free-text provenance (rule 3).
     - `decision == "needs-source-check"` is **NEVER** verified by itself
       (terminal-unresolved, rule 2 — see below).
  2. `prior_unresolved_nsc` is NOT truthy on that entry — an unresolved
     needs-source-check anywhere EARLIER in the item_uid's full chain vetoes
     verification outright, however clean the latest entry otherwise looks.
  3. The entry's `rubric_version` is a key in the approvals manifest AND
     its tool-stamped `recorded_at` is not earlier than that version's
     `approved_at` — **no retroactive verification**: an entry recorded
     before its rubric version was approved never converts to verified,
     even after approval; it must be re-reviewed (a NEW log entry, with a
     new `recorded_at`, after approval) to become eligible.

### Invalid-entry classification (decision-specific well-formedness)

A latest entry's `tool_state` is `invalid-entry`, not `reviewed_once`,
whenever it fails `entry_is_malformed()`'s bar — this is checked BEFORE
`entry_is_verified()` is even evaluated. The bar is decision-specific: the
three universal fields (non-empty `reviewed_by`, parseable `reviewed_at`, a
recognized `decision`) are necessary for every disposition, but a `change`
additionally needs a valid `new_dok`/`rationale`/`provenance`/`item_basis`,
a `needs-source-check` needs `rationale`, and a `confirm` needs a
recognized `confirmation_basis`. A structurally incomplete record for its
own disposition is `invalid-entry`, not a milder "reviewed but unverified."

### NSC (needs-source-check) attestation semantics

`needs-source-check` is **terminal-unresolved by rule 2**: recording it
requires `rationale` (every disagreement needs one), and it is never
verified by itself. It is resolved **only** by a LATER entry for the SAME
item_uid that stamps BOTH `resolves_source_check: true` AND `provenance`
that re-resolves on disk (via `resolve_provenance`, re-derived live, never
trusting a stored stamp). A plain later `confirm`/`change` WITHOUT that
explicit attestation does **not** resolve it — the item's chain carries
`prior_unresolved_nsc: true` forward and stays permanently un-verifiable
until the explicit attestation appears (see `dok_review.py`'s
`_chain_pending_nsc_states`). This is why an item whose latest entry is a
well-formed `needs-source-check` shows `review_state` `reviewed_once` on
the wave plan — **not** a separate `nsc-pending` value; `dok_review.py`'s
`TOOL_STATES` has exactly four values
(`unreviewed`/`invalid-entry`/`reviewed_once`/`verified`), and this
document does not introduce a fifth.

### Item-bound rule-1 provenance

A `--provenance` string of the form `calibration-anchor:<lesson>:<item-ref>`
resolves ONLY when it is bound to the item actually under review, not
merely to some anchor that exists somewhere in the cited lesson's
calibration file: the `<lesson>` must equal the item's own `lesson`; the
item must have a derivable calibration identity from its legacy `id`
(Savvas practice ids matching `-savvas-q<N>$`, or worked-example ids
matching an end-anchored `ex(ample)?[-_]<N>` — split/multi-part practice
ids and try-it/lesson-quiz/TE-slug ids have NO derivable identity and can
never be rule-1); and the `<item-ref>` must normalize to the SAME number
(and, if specified, the same kind) as that identity. A citation of a real
anchor for a *different* item, or for an unrelated Savvas number in the
same lesson, never resolves for this item.

### Timestamps and the approvals manifest

Every timestamp this workflow reads or writes — `reviewed_at`,
`recorded_at`, `approved_at` — must be **aware ISO-8601** (`tzinfo` present,
`datetime.fromisoformat` parseable); a naive timestamp is treated exactly
like a malformed one. `recorded_at` is **tool-stamped**: the reviewer
cannot supply it; `dok_review.py`'s `append_review` stamps it at the moment
of the actual write, which is what makes the no-retroactivity check
meaningful. The manifest (`rubric_approvals.json`) loads **fail-closed**:
missing file -> no approvals (silently, not an error); malformed JSON,
wrong shape, a non-dict entry, a non-string/empty `version`, an
unparseable `approved_at`, or the SAME version appearing more than once ->
ONE warning and the WHOLE manifest is treated as no approvals (never a
best-effort partial parse).

### State machine

Two distinct axes are in play, and the words "calibrated" and "reviewed"
must not be read as describing the same per-row progression:

- **(A) Registry-derived BASE `dok_status`** — a pure function of the
  registry row (plus its lesson's calibration file), computed by
  `compute_dok_status()` in `gen_dok_wave_plan.py` and mirrored by
  `inventory/build_content_readiness_inventory.py`. Values:
  `known_auto`, `unreviewed`, `calibrated`. Here `calibrated` is
  **lesson-level provenance** (the lesson's calibration file has real
  `dok2_anchors`/`dok3_anchors` — only 3-5 qualifies today) applied to that
  lesson's non-auto rows. It is NOT a per-row "this item was reviewed"
  record, and it is never earned by a single row being reviewed.
  `compute_dok_status()` no longer computes `verified` at all — see (B).
- **(B) Review-log-derived per-item state** — lives in
  `tools/dok-review/review_log.jsonl` (see `REVIEW_INTERFACE_SPEC.md`), and
  is the ONLY source of the wave plan's `verified` overlay. Values (see
  "The two-tier model" above): `unreviewed` (no log entry) /
  `invalid-entry` / `reviewed_once` (REVIEWED tier) / `verified` (VERIFIED
  tier, via the canonical projection). The wave plan surfaces ALL FOUR as
  the additive `review_state` field on every item; `dok_status` only ever
  reads `verified` when `review_state == 'verified'`, and otherwise falls
  back to the base status from (A).

```
(A) registry-derived BASE dok_status (from the row + its lesson's calibration):
    known_auto  /  unreviewed  /  calibrated (lesson-level; 3-5 rows only)

(B) review-log-derived per-item review_state, via the canonical projection
    (tools/dok-review/dok_review.py, keyed by item_uid):
    unreviewed (no log entry)
        | reviewer records confirm / change / needs-source-check, keyed by item_uid
        v
    invalid-entry   (fails baseline well-formedness -- entry_is_malformed())
        or
    reviewed_once   (well-formed, but not verification-grade -- includes a
        |            well-formed needs-source-check, and any entry with an
        |            unresolved prior needs-source-check in its chain)
        | entry_is_verified(): resolved disposition + no unresolved prior
        | NSC + rubric_version approved + recorded_at >= approved_at
        v
    verified        (VERIFIED tier -- review_state == 'verified')

Wave-plan output, per item:
    dok_status   = 'verified' if review_state == 'verified' else BASE status (A)
    review_state = the full four-value projection from (B), always emitted
```

The registry's own `reviewed_by` / `reviewed_at` fields are **DEMOTED** to
application-time metadata bookkeeping, repo-wide: a future, deliberate
promotion step (`qb_promote.py`, sketched in `REVIEW_INTERFACE_SPEC.md`,
not built) may someday write them onto a row for record-keeping purposes,
but **no consumer — this document, the wave plan, the review tool, or any
future tooling — ever again treats those two registry fields as
verification authority.** The only verification authority is the canonical
projection described above. **RESOLVED (NT7-R Stage R2):**
`inventory/build_content_readiness_inventory.py` now derives its own
`verified` via this SAME canonical projection (`dok_review.entry_is_verified`
via `tool_state_for`), computed INDEPENDENTLY from registry + alias map +
review log + approvals manifest — it never reads `dok_wave_plan.json`, so
this is a real cross-check against the wave plan's own projection, not a
copy of it (see `inventory/dashboard/build_content_readiness.py`'s
cross-consumer coherence checks, and
`inventory/dok-workflow/test_cross_consumer_projection.py`, for where the
two independent computations are proved to agree, per item_uid, across
every consumer). Registry `reviewed_by`/`reviewed_at` are no longer read by
that builder either.

**Named step — PERFORMED (NT10 canonicalization pass, 2026-07-22,
Fable-authorized):**
`inventory/provenance-audit/audit_match_quality.py` cross-checks the
frozen wave plan's `dok_status` field, row by row, against its own
recomputation. Through NT9 it recomputed only the pure BASE precedence
(`known_auto`/`calibrated`/`unreviewed`, never `verified`), which — as
this document predicted — started failing the moment step 3(a) first ran
with a nonempty verified set (NT10). The named pass has now been
performed: the audit re-pinned its match_quality totals to the NT9
present (285/4/611) and now applies the SAME canonical review-state
overlay every other consumer uses (importing
`tools/dok-review/dok_review.py`'s projection over the real review log +
approvals manifest) before comparing like-with-like against the plan's
`dok_status` (and, additionally, its `review_state`). The audit remains
read-only/no-network and passes byte-stably. **See item (f) of step 3 in
"[Approval procedure (operational, named updates)](#approval-procedure-operational-named-updates)"
below (retained for the historical design rationale).**

A DOK becomes `verified` only when **all three** of the following hold:

1. **Cross-checked against the TE item-analysis bucket** for that item,
   using the three-way match model:
   - **EXACT** (`id` is exactly `{lesson}-savvas-q{N}`, and `N` is in a TE
     bucket for that lesson): direct, high-confidence signal. Across the
     224 EXACT-matched rows in the current registry, all 224 agree with
     their TE bucket (0 disagreements) — because DOK was largely seeded
     from `item_analysis` in the first place. **Agreement is still a fast
     confirm, not a rubber stamp: a reviewer must still read the item and
     sign off.** A hypothetical EXACT disagreement would require the same
     resolution step as below.
   - **DERIVED** (`id` is `{lesson}-savvas-q{N}<suffix>`, e.g.
     `-partc-design`, `-partA-build`): the base item's TE bucket is only a
     **weak hint** — a sub-part of a Savvas problem can legitimately sit at
     a different DOK than the whole problem. Reviewer judgment is
     *required*, not optional, even when the derived row's DOK happens to
     match the base bucket. There are exactly 3 DERIVED disagreements in
     the current registry, all in lesson 4-3 (worked below).
   - **NONE** (`id` has no `q{N}` suffix at all — Examples, Try-Its,
     Launch/Model & Discuss items — or the number falls outside the
     analyzed TE range, 228 such rows): no direct TE signal. Reviewer
     judgment required; may infer DOK from the Example the item anchors to
     (`dok_rationale` / `source` usually name the anchoring Example).
2. **Reviewer id + timestamp recorded, at verification grade** — a human,
   not a script, made the call, and that fact is attached to the specific
   item as a `review_log.jsonl` entry keyed by `item_uid`, carrying a
   non-empty `reviewed_by` and a parseable aware `reviewed_at`. That alone
   only reaches the REVIEWED tier (`reviewed_once`); reaching VERIFIED
   additionally requires the entry to record a resolved, verification-grade
   disposition, carry no unresolved prior needs-source-check, and be
   stamped with an approved, non-retroactive `rubric_version` — see "The
   canonical projection" and "The two-tier model" above for the exact
   predicate (`dok_review.entry_is_verified`). This is evaluated directly
   on the log entry; there is no separate registry-promotion step in the
   verification path (a promotion step may still exist later purely as
   application-time bookkeeping — see the state machine above).
3. **Every disagreement between `row['dok']` and the TE bucket is explicitly
   resolved with a written note** — silence is not resolution. "I checked
   and they happen to agree" still needs a note when match_quality is
   DERIVED or NONE, because there was no TE bucket (or only a weak one) to
   silently defer to.

### Worked examples: the 3 real 4-3 DERIVED disagreements

All three come from the scaffolded Practice #35/#36 arc in lesson 4-3,
where a single Savvas base problem was split into authored sub-parts with
their own DOK:

| id | row DOK | TE base-item bucket | Resolution |
|---|---|---|---|
| `4-3-savvas-q35-partc-design` | 2 | item 35 -> dok1 | Base item 35 is TE dok1, but this authored part adds an interpretive "design implication" step (translate an algebraic comparison into engineering meaning) that raises it to routine multi-step + contextual translation. Resolves in favor of the authored dok=2, with a note that the TE bucket describes the bare base item, not this extended part. |
| `4-3-savvas-q36-partA-build` | 1 | item 36 -> dok2 | This authored part is the *build* step of a 3-part scaffold: identify two areas and form the unsimplified ratio — single-step recall/identification, genuinely simpler than the TE's rating of the whole item 36. Resolves in favor of the authored dok=1, with a note that the TE bucket rates the base item as a whole, of which this is only the easiest sub-step. |
| `4-3-savvas-q36-partC-evaluate-fairness` | 3 | item 36 -> dok2 | **Fully worked:** this is the DOK-3 spine item for the 4-3 OBS lesson (`role=dok3-driver`). It is the *evaluate* step of the same 3-part #36 scaffold as the row above: substitute x=4 to get 4/(6*5) = 2/15 ~= 13%, then render a qualitative fairness judgment the student must articulate and defend. That is strategic reasoning + critique-of-context, not the routine-procedure level the TE's item-36-as-a-whole bucket (dok2) implies. **Resolution:** the disagreement resolves in favor of the authored dok=3. The written note on this item must say, explicitly: *"TE bucket (dok2) describes base item 36 as a whole; this is a derived sub-part ('evaluate fairness') that is a distinct, higher-DOK task than the base item, so the TE bucket does not apply directly."* This is the pattern every DERIVED disagreement should follow — state which TE bucket was checked, why it doesn't transfer cleanly to the sub-part, and what DOK-level reasoning the derived row actually requires. |

The general lesson: **the cross-check is a signal, not an oracle.** EXACT
agreement still needs a human's eyes; DERIVED and NONE always need a human's
judgment, and every disagreement — however it resolves — needs a note that
a future reviewer (or the teacher, mid-lesson) can read without redoing the
analysis.

## (c) Safeguards

**Locked rule: unverified DOK must not drive student-facing claims, item
selection, or grading.** This is *fail-safe* everywhere it's checked: an
absent, malformed, or otherwise-unrecognized state is treated as
unverified, never as verified. The single predicate every layer below
checks is now the canonical projection, not a registry field:

```
is_verified(item) := the item_uid's latest tools/dok-review/review_log.jsonl
                      entry passes tools/dok-review/dok_review.py's
                      entry_is_verified() under the current
                      tools/dok-review/rubric_approvals.json manifest

                      (equivalently, on a wave plan regenerated from the
                      current review log + approvals manifest:
                      review_state == 'verified' for that item_uid)
```

This predicate is **strictly TIGHTER** than the registry-field predicate
this document used to describe (`reviewed_by` AND `reviewed_at` on the
row): it additionally requires a resolved verification-grade disposition,
no unresolved prior needs-source-check, and an approved, non-retroactive
`rubric_version`. It is checked fail-safe end to end: an absent review
log, an absent or malformed approvals manifest, a malformed log entry, or
any `review_state` other than `verified` (`unreviewed`, `invalid-entry`,
`reviewed_once`) => **NOT** verified => blocked/quarantined. There is no
scenario in which a missing or malformed input yields a verified state.

**RESOLVED (NT7-R Stage R2):** `inventory/build_content_readiness_inventory.py`
now keys its own `verified` off the SAME canonical projection named above
(`dok_review.entry_is_verified` via `tool_state_for`), computed
independently from registry + alias map + review log + approvals manifest
— never from a registry field, and never by reading `dok_wave_plan.json`
itself. See the State-machine section above for the full resolution note
and the one named future step still open (`audit_match_quality.py`).

Anything other than `review_state == 'verified'` — `unreviewed`,
`invalid-entry`, `reviewed_once`, a missing field, an unexpected value —
is **not** verified and must be blocked or quarantined at each of these
layers:

- **`tex/*.tex` packet build (LaTeX authoring).** A student packet must
  never print a bare "DOK 3" claim sourced from an unverified item. If DOK
  is surfaced on the page at all (e.g. a driver callout box), it is
  VISIBLY QUARANTINED: it appears only under an unmistakable UNVERIFIED
  label until `is_verified(item)` is true, and is never used to drive a
  student-facing DOK claim, item selection, or a grade — no silent
  promotion from "the registry says dok=3" to "this is officially a DOK-3
  task" in front of students.
- **Pacer (`L*_Pacer.html`).** Teacher-facing scripts may reference DOK
  internally (e.g. "this is intended as the DOK-3 driver") for lesson-plan
  purposes, but the same VISIBLE QUARANTINE applies: DOK from an unverified
  item is never presented as a verified fact to the teacher, and appears
  only under the same unmistakable UNVERIFIED label. The pacer is
  teacher-only, so the bar is lower than the student packet, but the
  predicate is identical: don't claim `verified` when `is_verified(item)`
  is false.
- **Quiz / item-selection / DOK-3-spine selection.** Selecting "the DOK-3
  driver for this lesson," or assembling an assessment from registry
  items, **HARD-BLOCKS**: it requires `is_verified(item) == True` for every
  item it selects, full stop. An unverified item CANNOT be selected —
  there is no proceed-anyway path (the earlier draft's "or explicitly
  surface a provisional flag ... proceed anyway?" escape hatch is removed).
  If no verified item is available for a required role (e.g. the lesson's
  `dok3-driver`), selection FAILS outright and surfaces the gap to the
  teacher as a blocked/missing selection. It never silently selects on
  `row['dok']` alone as if it were ground truth, and it never proceeds on
  an unverified item.
- **Desk mastery / grade rollup.** Any mastery or grade computation that
  buckets student performance by DOK level **HARD-EXCLUDES** items whose
  DOK is unverified from that bucketing entirely — there is no
  provisional-weighting path (the earlier draft's "or explicitly
  weight/label them as provisional in the rollup" escape hatch is
  removed). A grade must never incorporate an unverified DOK label at any
  weight, however small or clearly labeled.

**All four layers are uniform under one fail-safe predicate.** None of the
four has a proceed-anyway or provisional-weight path. tex-packet build and
the pacer VISIBLY QUARANTINE unverified DOK (a lesson still needs to render
and be teachable before every item is verified): if DOK from an unverified
item is shown at all, it appears only under an unmistakable UNVERIFIED
marker and is NEVER used to drive a student-facing DOK claim, item
selection, or a grade. Quiz/item-selection and desk mastery/grade rollup
HARD-BLOCK or HARD-EXCLUDE instead, because those are exactly the
"drive item selection" / "drive grading" cases the locked rule names —
there is nothing to visibly quarantine when the action itself (select this
item, count this toward a grade) is what must not happen.

Every layer's gate is the same single predicate (`is_verified(item)`,
i.e. `dok_review.entry_is_verified()` via `tool_state_for()`), checked
fail-safe (unknown/missing/malformed => unverified => blocked/quarantined),
so there is exactly one place to fix if the rule is ever violated: the
canonical projection in `tools/dok-review/dok_review.py`, full stop.

## Approval procedure (operational, named updates)

This section is the operational companion to (b) above: not what makes a
DOK "verified" in principle, but the exact sequence of hand-edits, tool
invocations, and regenerations that takes this workflow from "0 verified,
rubric version unapproved" to a real, human-approved, non-retroactive verification —
and what fails loudly, and how, at every point that sequence is skipped or
run out of order.

### Step 1 — manifest hand-edit (human only)

A teacher/reviewer approval of a rubric version is recorded by hand-adding
one entry to the `approvals` list in
`tools/dok-review/rubric_approvals.json`:

```json
{"version": "v0.2", "approved_at": "<offset-aware ISO-8601>"}
```

This file is never written by any tool — a human edits it directly. Two
rules govern this edit, and they fail in **different ways** — only the
second is manifest-poisoning:

- The `version` string must **exactly match** the `--rubric-version` value
  reviewers actually stamped their entries with via the tool. A mismatch
  does **NOT** poison anything: an otherwise-valid approval entry whose
  version matches no review entry loads fine (`load_rubric_approvals`
  returns it normally) — it simply approves a version string nobody
  reviewed under, so the mismatched review entries stay unapproved and
  can never verify. The failure mode is silent non-verification, not a
  loader error — which is exactly why the exact-match discipline is
  called out here.
- A **NAIVE** (offset-less) `approved_at`, or a **DUPLICATE** `version`
  entry anywhere in the list, poisons the **WHOLE manifest** to zero
  approvals (`load_rubric_approvals`'s fail-closed policy: one warning,
  the entire manifest treated as empty — never a best-effort partial
  parse that keeps the other, well-formed entries). Malformed JSON, a
  wrong top-level shape, or a non-string/empty `version` poison the whole
  manifest the same way.

Rebuilding the console (`inventory/decision-console/build_console.py`)
after this hand-edit flips the section-5 watermark from AWAITING to
APPROVED — this is a **named artifact refresh**, not a verification event
by itself: verified counts everywhere are still 0 at this point. Nothing
verifies until Step 2 records a review *after* this approval is in effect.

### Step 2 — reviews (tool only)

Reviews are recorded **only** through `tools/dok-review/dok_review.py`'s
`review` subcommand — never by hand-editing `review_log.jsonl`. There is
**no retroactivity**: any log entry whose tool-stamped `recorded_at` is
earlier than its `rubric_version`'s `approved_at` stays REVIEWED-tier
(`reviewed_once`) forever — it can never later convert to verified once
the manifest catches up. The only way to make such an item verification-
grade is a brand-new entry, RE-RECORDED after the approval, with a new
`recorded_at`.

Verification-grade additionally requires (see "The two-tier model" and
"Item-bound rule-1 provenance" above for the full predicate):

- a **resolved disposition** — either an item-bound rule-1 confirm (the
  `--provenance` resolves, at entry time, to a real on-disk calibration
  anchor bound to that same item), or a `change` with a valid `new_dok`,
  non-empty `rationale`, non-empty `provenance`, and an `item_basis`-
  appropriate provenance requirement (`textbook-exact` needs *resolved*
  provenance; the other four bases accept free text);
- a **non-empty rationale** whenever the disposition is a derived-match
  confirm or an exact-disagreement confirm — silence is never resolution;
- a **clear needs-source-check chain** — no unresolved prior NSC anywhere
  earlier in the item_uid's chain (the veto is permanent until an explicit
  `resolves_source_check: true` + re-resolving `provenance` entry appears);
- an **approved rubric_version**, non-retroactively, per the no-
  retroactivity rule above.

### Step 3 — when the canonical verified uid set `S` first goes nonempty

The moment `|S| > 0` for the first time (the canonical verified uid set —
the set of item_uids whose latest log entry passes `entry_is_verified()`
under the approved manifest), regenerate **in this order**, with **every**
named update below. Skipping a named update is caught **in code** by the
gate named for it in the "fail-loud behavior" subsection after this list.
Reordering is code-enforced only where a real data dependency exists —
(3a) before (3b) is enforced by the dashboard's per-item set gate, (3a)
before (3d) by the console's frozen-hash guard, and Step 1 before any
verified plan by the console's coherence guard; the relative order of
(3c) and (3d) themselves is **procedural convention only** (neither
consumes the other's output — running them swapped merely leaves the
console's informational `content_readiness` sha recording the pre-(3c)
dashboard artifact until the next rebuild, which no guard checks).

**(a) `inventory/dok-workflow/gen_dok_wave_plan.py`.** NO code edits
needed: its base invariants (421/437/42 — `EXPECTED_BASE_DOK_STATUS_TOTALS`
— and the 42/4/220/7/627 wave counts) assert **pre-overlay**, before the
verified overlay is applied, so a real verified item never trips them; the
verified overlay itself and the intra-wave re-sort it can trigger are
automatic. Produces a new plan — a new plan hash, call it `H1`.

**(b) `inventory/build_content_readiness_inventory.py`.** No assert edits
needed to its logic, BUT:

- **(b1)** its `baseline_reconciliation` entry
  `{'metric': 'verified rows', 'claimed': 0, ...}` (the literal `claimed: 0`
  pin, and the corresponding row in `CONTENT_READINESS_INVENTORY.md`'s
  reconciliation table) is a **NAMED prose/pin update**: `claimed` becomes
  `N` (the new `|S|`), and the reconciliation verdict for that row must be
  **re-confirmed deliberately** — the all-CONFIRMED gate this builder
  enforces (every `baseline_reconciliation` entry must read CONFIRMED, or
  the build fails) is not something to silently let flip; a human
  re-confirms it as part of this step, not merely lets the number change.

This builder now publishes `dok_verified_item_uids == S`.

**(c) `inventory/dashboard/build_content_readiness.py`.** No assert *logic*
edits needed (the per-item uid-set gates below are the acceptance
criterion, not something to patch), but two **NAMED pin updates**:

- **(c1)** `check("dok.verified", dok_totals["verified"], 0)` — the literal
  `0` becomes `N`.
- **(c2)** the ws6 pinned distribution (`CALIBRATED 1 / INCOMPLETE 9 /
  BLOCKED 1 / PROVISIONAL 18 / ABSENT 8`) changes **at the FIRST verified
  Wave-0 item**, not only when a whole lesson fully verifies. Reason: the
  canonical overlay removes a verified row from its registry-derived base
  bucket, so lesson 3-5's per-lesson `calibrated` count drops below
  `registry_rows` (42 → 41) at the very first verified 3-5 item; the
  `calibrated == registry_rows` branch of `derive_ws6_state` then fails
  and 3-5 falls through to its base readiness (`"partial"`) →
  **INCOMPLETE**. The pinned distribution therefore becomes
  `CALIBRATED 0 / INCOMPLETE 10 / …` on the first Wave-0 verification —
  a NAMED pin update at that moment (this exact interaction is what the
  same-cardinality negative in `test_cross_consumer_projection.py` has to
  compensate for in its fixtures; see that test's docstring). The other
  transitions follow `derive_ws6_state`'s existing precedence, not a new
  rule: a lesson maps to **VERIFIED** only when its base readiness is
  already `"ready"` AND every row is verified (aspirational — no lesson is
  base-`"ready"` today); non-calibrated lessons' verified items come out
  of `known_auto`/`unreviewed` buckets, which no lower branch reads, so
  their WS6 bucket is unchanged until their base readiness changes.
  **READY** remains exactly what it always was: the
  base-ready-but-not-fully-verified fallback branch (stated explicitly in
  `inventory/dashboard/CONTENT_READINESS_DASHBOARD_SPEC.md`'s state
  table) — it is not itself created or removed by this step.

The per-item three-way uid-set gates (base inventory `S` == wave-plan `S`
== published `S`, per item_uid) need **no edits** — they are the
acceptance criterion this whole step is proved against, not something to
adjust to fit a new number.

**(d) `inventory/decision-console/build_console.py`.** **NAMED re-pin**:
the `FROZEN_HASHES` wave-plan entry updates to `H1`. The manifest-coherence
guards pass automatically once the manifest is non-empty (they exist to
block an empty-manifest/verified-plan mismatch, not to block a genuinely
approved one). `meta.locked_counts.canonical_verified_count` becomes `N`.

**(e) `inventory/dok-workflow/test_cross_consumer_projection.py`.**
**NAMED update**: scenario 1's all-unreviewed baseline
(`test_scenario1_baseline_all_unreviewed_four_way_identity`) must be
re-scoped to a pinned, empty-log fixture — it currently asserts against
the real, committed `review_log.jsonl` path being absent-and-therefore-
all-unreviewed, but once a real approval + review lands, the real
canonical log is no longer empty, so that test's premise must move to an
explicit empty-log fixture rather than relying on the real log's absence.

**(f) NAMED PASS — PERFORMED (NT10, 2026-07-22, Fable-authorized):**
`inventory/provenance-audit/audit_match_quality.py` used to recompute
registry-derived `dok_status` only (the pure BASE precedence, which never
returns `verified`) and cross-check it against the frozen wave plan, row
by row. As designed, it became **OPERATIONALLY REACHABLE** (started
failing) on the FIRST verified overlay — immediately after step 3(a)
first ran with a nonempty `S` (NT10's 39-row recording). The pass was
performed at that moment: stale match_quality pins re-pinned
(224/4/672 → 285/4/611, the NT9 calibration effect), and the row-level
cross-check made like-with-like by applying the canonical review-state
overlay (imported from `tools/dok-review/dok_review.py`, the same
projection every other consumer uses) on top of the recomputed base
status before comparing to the plan's `dok_status`/`review_state`. The
canonical (overlaid) totals are deliberately NOT pinned in the audit —
they move with every recording batch; drift is caught by the row-level
cross-check against the frozen plan instead. The audit stays read-only,
no-network, byte-stable.

### Fail-loud behavior when a step is skipped or misordered

- **Skip the manifest edit (Step 1) but record reviews (Step 2) anyway** —
  nothing verifies anywhere; the fail-closed predicate (`entry_is_verified`
  requiring an approved, non-retroactive `rubric_version`) simply never
  fires, everything stays at REVIEWED tier at best.
- **Regenerate the plan (3a) but not the base inventory (3b)** — the
  dashboard's three-way per-item set gate exits nonzero, naming the
  symmetric difference between the wave plan's verified-uid set and the
  base inventory's stale (empty) one.
- **Regenerate both (3a, 3b) but skip the dashboard pin update (3c)** —
  the dashboard's `dok.verified == 0` baseline pin (c1 above) exits
  nonzero — the computed value (`N`) no longer matches the still-`0`
  pinned expectation.
- **Update (c1) but skip (c2)** — if any verified item is a Wave-0 (3-5)
  row, the ws6 pinned-distribution **assert fires first** (it is a raw
  assert that runs before the check table is even printed), with its
  guided step-3(c2) message: 3-5's `calibrated` count drops below 42
  under the overlay, demoting it CALIBRATED→INCOMPLETE, so the pinned
  `CALIBRATED 1 / INCOMPLETE 9 / …` distribution no longer matches even
  though the (c1) `dok.verified` pin was correctly updated.
- **Skip the console re-pin (3d)** — the console's `FROZEN_HASHES` guard
  exits nonzero at start, before any other console logic runs, because the
  regenerated wave-plan file's hash (`H1`, the new one) no longer matches
  the stale hash `FROZEN_HASHES` was left pinned to.
- **Hand-verify a plan without an approved manifest, or roll back the
  manifest after regenerating** — the console's empty-manifest coherence
  guard exits nonzero, naming both the empty manifest path and the
  offending verified uid(s): an empty approvals manifest can never coexist
  with a wave plan claiming a verified item.
- **Skip the scenario-1 re-scope (3e)** — the cross-consumer suite fails,
  because the real, no-longer-empty review log no longer matches that
  test's all-unreviewed premise.

### Step 4 — later, and separately human-gated: registry promotion

This step is deliberately **out of scope for the verification path
itself** and gated separately — verification is already complete before
this ever runs. `qb_promote.py`-style promote-proposals apply here;
`reviewed_by`/`reviewed_at` are written onto the registry row as
**application-time METADATA**, never as verification authority (see the
State-machine section above — this has not changed). The registry
byte-lock is lifted **only by Fable**, at that point, not by this
procedure. If any change-disposition alters DOK bucketing at this stage,
the `EXPECTED_BASE` totals (421/437/42) in `gen_dok_wave_plan.py` and the
base builder are a **NAMED invariant review** — i.e. a human deliberately
re-derives and re-pins them, not a silent drift.

### What totals change (and what never does)

- `dok_status` totals: `verified` moves `0 -> N`; the items that verify
  **leave** their prior base bucket (`known_auto`/`unreviewed`/
  `calibrated`) in every displayed total — Stage R2's overlay removes them
  from the base bucket, it does not double-count them.
- `review_state` totals shift correspondingly (`unreviewed`/
  `invalid-entry`/`reviewed_once` counts fall as items move to `verified`).
- Wave counts, `match_quality`, and every item's identity (`item_uid`,
  `registry_line`, legacy `id`, `dok`, `role`) **never change** while the
  registry stays frozen — only `dok_status` and `review_state` move.

## NT11: merged-alias identity overlay (rc-merge-auth-5-4-2026-07-23)

**Named update — PERFORMED (2026-07-23, RC-authorized 22-pair merge).** A
Fable/RC-authorized action resolved 22 of the 85 ambiguous-legacy-id groups
this document's "Identity key" section describes (all in lesson 5-4 — the
same 22 rows the collision review queue already flagged as DOK-conflict
pairs, see (b)'s worked examples above): the registry row chosen as each
pair's non-survivor now carries four additive tombstone fields —
`status=="merged-alias"`, `alias_of` (the survivor's `item_uid`),
`merged_at`, `merge_authorization` (`{"record_id":
"rc-merge-auth-5-4-2026-07-23", ...}`) — written onto the row in place; no
row was deleted, and no `dok`/`role`/`wave`/`lesson` content changed on
either row of any pair. `inventory/dedup/build_item_uid_map.py` was
re-run and additively enriches each resolved legacy-id's `alias_map` entry
with a `resolved_alias` key (`{alias_uid, survivor_uid, merged_at,
authorization_record_id}`) — the join-level source every downstream
consumer reads for "which of these two rows is the alias."

**What changed (all additive overlays; no existing pin was
re-derived except the file hashes themselves):**

- `gen_dok_wave_plan.py` carries the registry's `status`/`alias_of`
  verbatim onto every plan item (`'active'`/`None` for the 878 untouched
  rows) and publishes a new `identity_reconciliation` block: raw
  registry identities (900) = active canonical items (878) + merged-alias
  identities (22), asserted before the plan is written. New pins
  `EXPECTED_MERGED_ALIAS_ROWS = 22` / `EXPECTED_ACTIVE_CANONICAL_ITEMS =
  878`. Every PRE-EXISTING `EXPECTED_*` pin (wave counts, per-(wave,lesson)
  counts, base `dok_status` totals, `match_quality` totals/disagreements)
  passed **unmodified** — proof that the merge touched no `dok`/`role`/
  `wave` content.
- `inventory/build_content_readiness_inventory.py`,
  `inventory/dashboard/build_content_readiness.py`, and
  `inventory/decision-console/build_console.py` each publish the same
  `identity_reconciliation` (or `locked_counts`-adjacent) shape additively;
  every pre-existing readiness/dok/ws6/collision pin is unchanged (registry-
  row-count based, audit-style, exactly as above). The dashboard's
  `dok_conflict_subset` rows and the console's `section2.pairs` are
  additionally annotated per-pair with the resolved alias/survivor
  `item_uid`s, sourced from the dedup map's `resolved_alias` (join-level),
  never guessed from row position.
- `inventory/provenance-audit/audit_match_quality.py` recomputes
  `status`/`alias_of` independently from the registry row (never from the
  frozen plan) and added them to its row-level cross-check
  (`CROSS_CHECK_FIELDS`) against `dok_wave_plan.json` — the 22 merged-alias
  rows are carried and explicitly marked in this audit surface, never
  dropped, per this document's audit/history-surface convention.
- `qb.py` (the student-facing packet/slide selector) is the one place this
  merge changes *behavior*, not just reporting: `get()` / `select()` /
  `get_for_packet()` now resolve a `status=="merged-alias"` row
  DELIBERATELY to its survivor via `alias_of` (never by legacy-id
  first-match or dict-last-wins) and fail loudly on a dangling or chained
  alias; `select()` drops alias rows outright. `stats()` reports raw
  (900) / active (878) / merged-alias (22).
- **Named re-pins** (file hashes only — see each file's own inline
  comment naming `rc-merge-auth-5-4-2026-07-23`): the registry hash and the
  regenerated wave-plan hash in
  `inventory/decision-console/build_console.py`'s `FROZEN_HASHES` and in
  `inventory/dok-workflow/test_cross_consumer_projection.py`'s
  `REGISTRY_SHA256`/`COMMITTED_PLAN_SHA256`, plus the alias-map hash in
  `FROZEN_HASHES`. `REAL_REVIEW_LOG_SHA256`/`REAL_APPROVALS_SHA256` (and
  every other file this document's "Locked" surfaces name) are untouched —
  this merge never wrote the review log or the approvals manifest.

**What never moved:** the canonical verified-uid set (RC's 39 lesson-5-4
rows, all copy-B survivors) is set-identical before and after — none of
the 22 merged-alias rows were ever in that set (proved by symmetric-
difference against a preserved pre-merge snapshot of the dashboard's
published `content_readiness.json`), so the merge could not have promoted
or demoted a verification.
