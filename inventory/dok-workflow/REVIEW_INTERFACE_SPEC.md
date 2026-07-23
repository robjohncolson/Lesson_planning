# Review Interface Spec (built — `tools/dok-review/dok_review.py`)

**This interface is implemented.** `tools/dok-review/dok_review.py` is a
local, testable CLI (141 passing tests in
`tools/dok-review/test_dok_review.py`) that lets a human reviewer walk the
wave queue in `dok_wave_plan.json`, record DOK confirm/change/needs-source-check
decisions, and — for a rubric version a teacher has actually approved —
have those decisions become VERIFIED under the canonical projection this
document and `DOK_VERIFICATION_WORKFLOW.md` describe. There is no UI, no
server: it is a CLI over three JSON/JSONL files on disk, no network calls,
no auth (solo-teacher tool).

## Purpose + non-mutation invariant

The tool's job is to let a human reviewer walk the wave queue, see each
item's current DOK plus its TE cross-check signal, and record a decision.

**Non-mutation invariant: the tool NEVER writes to `questionbank/registry.jsonl`
or any `questionbank/calibration/*.json` file.** Those stay exactly as they
are today (registry.jsonl sha256 =
`b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8` at the
time this spec was written — verify unchanged before and after any tool
work; it remains unchanged as of this rewrite). The tool reads
`dok_wave_plan.json`, `questionbank/registry.jsonl` (one row at a time, by
`registry_line`, for `promote`'s re-derivation), and
`questionbank/calibration/*.json` (for provenance resolution) — all
read-only. It writes exactly two things, both inside its own directory:

- **`tools/dok-review/review_log.jsonl`** — append-only, one JSON object per
  review decision. The tool's `review` command is the ONLY code path that
  writes it (`append_review`), and it only ever opens the file in `"a"`
  mode — never rewrites, never truncates. `read_log_entries()` treats a
  missing file as "no reviews yet" and does NOT create it.
- **`tools/dok-review/rubric_approvals.json`** — the tool NEVER writes to
  this file. It is edited BY HAND by a human, only after a real teacher
  approval. It currently contains exactly one approval —
  `{"version": "v0.2", "approved_at": "2026-07-20T19:06:13-04:00"}` — hand-added
  after the teacher approved DOK rubric v0.2; the file is still only ever
  hand-edited, never written by this or any other tool.

## Identity key

`questionbank/registry.jsonl` has 900 rows but only 815 unique legacy `id`
strings — 85 ids are each shared by 2 distinct rows (170 rows total),
always at different DOK/wave. Example: `5-4-savvas-q41` is registry line
299 (`dok=2`, `role=None`, wave 4) **and** registry line 328 (`dok=3`,
`role=dok3-driver`, wave 3) — two different rows, one legacy id. If the
review log (or the queue/progress views, or `promote`) matched on
`item_id` alone, a single confirm/change decision for `5-4-savvas-q41`
would silently get credited to **both** rows, at two different DOK values.
`item_uid` — the opaque identity `dok_wave_plan.json` carries on every item
(see `gen_dok_wave_plan.py`'s identity-key join against
`inventory/dedup/item_uid_alias_map.json`) — is unique per registry row/line
and resolves this: the two `5-4-savvas-q41` rows carry two different
`item_uid`s. Every piece of this workflow (review log, latest-decision
lookup, queue completion, progress accounting, promotion) keys by
`item_uid`, never by legacy `id` alone — see `build_uid_index` /
`build_id_index` in `dok_review.py`, and the non-negotiable identity rule
in its module docstring.

## Data model — the actual record shape

**`tools/dok-review/review_log.jsonl`** — append-only, one JSON object per
line, one line per reviewer decision. Never edited in place; never
truncated; a correction is a new, later line, not a rewrite of an earlier
one. The **canonical log location** is `tools/dok-review/review_log.jsonl`
(overridable via `--log` on every subcommand, and via `gen_dok_wave_plan.py`'s
`--review-log`, for testing only).

**Latest-line-wins for display; full chain re-derived at promote.**
`latest_entries_by_uid()` takes the LAST line per `item_uid` in APPEND
order (never sorted by `reviewed_at`) for all "display tier" reads: the
`queue`, `progress`, and `report` commands, and `gen_dok_wave_plan.py`'s
`review_state` overlay all trust this fast, cheap, offline projection.
`promote`, by contrast, walks the FULL chain for one `item_uid` (every line
for that uid, in append order) and re-derives everything live against disk
(`build_promotion_proposal`) — see "Promotion: proposals-only" below.

Each record `append_review()` actually writes (built by
`build_review_record`, then stamped with `recorded_at` at write time):

| Field | Type | Meaning |
|---|---|---|
| `item_uid` | string | opaque canonical identity from `inventory/dedup/item_uid_alias_map.json` (the wave plan item's `item_uid`); **THE join key to the registry row.** |
| `registry_line` | int | 1-based line number in `questionbank/registry.jsonl`, from the wave-plan item. |
| `item_id` | string | legacy display id (registry row's `id`); **NOT unique** — 85 ids are shared by 2 rows; never used alone to match. |
| `lesson` | string | the lesson slot, e.g. `"4-3"`, from the wave-plan item. |
| `reviewed_by` | string | reviewer identifier (`--reviewed-by`, required non-empty). |
| `reviewed_at` | string | strict aware ISO-8601 (`--reviewed-at`, defaults to now with local offset). May not predate this item_uid's latest existing entry. |
| `prior_dok` | int | the wave-plan item's `dok` at review time (1/2/3) — snapshot, not a live reference. |
| `reviewer_dok` | int or null | `prior_dok` for `confirm`; the chosen DOK for `change`; `null` for `needs-source-check`. |
| `current_dok` | int | same as `prior_dok` (kept for the field the earlier draft named). |
| `new_dok` | int or null | the reviewer's chosen DOK (1–3) when `decision == "change"`; `null` otherwise. |
| `decision` | `"confirm"` \| `"change"` \| `"needs-source-check"` | which of the three dispositions this entry records. |
| `te_bucket` | list[int] or null | the TE bucket(s) for this item at review time, from the wave-plan item. |
| `match_quality` | `"exact"` \| `"derived"` \| `"none"` | the three-way match category at review time. |
| `disagreement_resolved` | bool | true iff there was a real disagreement (non-exact match, or reviewer_dok disagrees with prior_dok/te_bucket) AND `rationale`-or-`note` is non-empty. |
| `note` | string | free text (`--note`, defaults to `""`). |
| `rubric_version` | string | required (`--rubric-version`), e.g. `"v0.2"`. Recorded verbatim; gates VERIFIED via the approvals manifest. |
| `rationale` | string | required for `change`/`needs-source-check`; optional for `confirm` (`--rationale`, defaults to `""`). |
| `provenance` | string | free-form source citation (`--provenance`); required (non-empty) for `change`; optional for `confirm`; the `calibration-anchor:<lesson>:<item-ref>` scheme is what can resolve on disk. |
| `provenance_resolved` | bool | `resolve_provenance(provenance, calibration_dir, item)` evaluated AT ENTRY TIME — item-bound (see `DOK_VERIFICATION_WORKFLOW.md`'s "Item-bound rule-1 provenance"). |
| `confirmation_basis` | `"rule-1-textbook-provenance"` \| `"rule-2-adjacent-unsourced"` \| `"rule-2-adjacent-unsourced-claim"` \| `null` | derived for `confirm` only (empty provenance / non-resolving / resolving); `null` for `change`/`needs-source-check`. |
| `item_basis` | `"textbook-exact"` \| `"adapted"` \| `"split"` \| `"extended"` \| `"teacher-authored"` \| `null` | REQUIRED (and ONLY valid) when `decision == "change"` (`--item-basis`, rule 3). |
| `resolves_source_check` | bool | `--resolves-source-check`; attests this entry's `provenance` resolves the item_uid's most recent unresolved needs-source-check. Rejected at entry if nothing is pending, or if `provenance` doesn't resolve on disk. |
| `prior_unresolved_nsc` | bool | computed by `cmd_review` over `prior_entries_for_uid + [this record]` via `_chain_pending_nsc_states`; vetoes VERIFIED when true. |
| `recorded_at` | string | **tool-stamped**, NOT reviewer-suppliable — `append_review` sets it to `datetime.now().astimezone().isoformat()` at the moment of the actual write. This is what the no-retroactivity check in `entry_is_verified` compares against `approved_at`. |

Example record (a rule-1 confirm on `3-5-savvas-q27`, the 3-5 dok3-driver
— `item_uid iu_3b42ab3340d5`, `registry_line 41`, `te_bucket null`,
`match_quality "none"`, all read verbatim from the committed
`dok_wave_plan.json` — with provenance bound to and resolving against that
same item's own `dok3_anchors` entry, Practice #27):

```json
{"item_uid": "iu_3b42ab3340d5", "registry_line": 41, "item_id": "3-5-savvas-q27", "lesson": "3-5", "reviewed_by": "lynn", "reviewed_at": "2026-07-19T14:32:07-04:00", "prior_dok": 3, "reviewer_dok": 3, "current_dok": 3, "new_dok": null, "decision": "confirm", "te_bucket": null, "match_quality": "none", "disagreement_resolved": true, "note": "", "rubric_version": "v0.2", "rationale": "Practice #27 (Storage Box) is the 3-5 dok3-driver; confirmed directly against the lesson's own dok3_anchors entry for Practice #27.", "provenance": "calibration-anchor:3-5:practice #27", "provenance_resolved": true, "confirmation_basis": "rule-1-textbook-provenance", "item_basis": null, "resolves_source_check": false, "prior_unresolved_nsc": false, "recorded_at": "2026-07-19T14:32:08-04:00"}
```

That entry is well-formed AND verification-grade; whether it actually
reads as `verified` still depends on whether `"v0.2"` is present in
`rubric_approvals.json`'s approvals with an `approved_at` at or before
`2026-07-19T14:32:08-04:00` — see "Three dispositions" and "Two-tier
reviewed/verified" below. Derived-suffix ids (e.g.
`4-3-savvas-q36-partC-evaluate-fairness`) can **never** resolve rule-1 at
all — `derive_item_calibration_identity` only matches an end-anchored
`-savvas-q<N>` or `ex(ample)?[-_]<N>` id, and a split/sub-part suffix
breaks that match by construction — and a confirm on a `match_quality ==
"derived"` item now requires a non-empty `--rationale` at entry
(`_confirm_disagreement_requires_rationale`), so an example built on such
an id with `confirmation_basis: "rule-1-textbook-provenance"` and an empty
`rationale` (as an earlier draft of this example did) was impossible on
both counts.

## Three dispositions (`--disposition`)

- **`confirm`** — reviewer agrees with the wave-plan's `prior_dok`.
  `reviewer_dok = prior_dok`, `new_dok = None`. `--provenance` optional;
  `confirmation_basis` is derived: empty provenance ->
  `rule-2-adjacent-unsourced`; non-empty but doesn't resolve on disk ->
  `rule-2-adjacent-unsourced-claim`; resolves on disk (item-bound) ->
  `rule-1-textbook-provenance`. Only the last is verification-grade.
- **`change`** — reviewer overrides `prior_dok` with a chosen DOK (1–3
  only; DOK 4 is not assignable on this platform and does not appear in
  the bank). `reviewer_dok = new_dok = chosen_dok`. Requires BOTH
  `--rationale` and `--provenance` (rule 5) and REQUIRES `--item-basis`
  (rule 3): `textbook-exact` is verification-grade only when provenance
  resolves on disk; `adapted`/`split`/`extended`/`teacher-authored` are
  verification-grade with free-text provenance, provided rationale and
  provenance are both non-empty.
- **`needs-source-check`** — terminal-unresolved (rule 2): `reviewer_dok =
  new_dok = None`. Requires `--rationale`. Never verified by itself.
  Resolved ONLY by a LATER entry for the same `item_uid` that stamps BOTH
  `resolves_source_check: true` AND provenance that resolves on disk. A
  plain later confirm/change WITHOUT that attestation does NOT resolve it
  — the item stays permanently un-verifiable (`prior_unresolved_nsc: true`)
  until the explicit attestation appears.

DOK measures cognitive demand, not difficulty (rubric rule 4) — this exact
sentence (see `dok_review.DOK_NOT_DIFFICULTY_NOTE`) appears verbatim in the
CLI's `--help` epilogs and `tools/dok-review/README.md`.

## Reject-at-entry

Every `review` invocation is fully validated (`_validate_review_args`, plus
timestamp/monotonicity checks in `cmd_review`) BEFORE `append_review` is
ever called. Any validation failure prints an ERROR to stderr, exits
nonzero, and appends NOTHING to the log — there is no code path that can
append a partial or invalid record.

## Two-tier reviewed/verified

See `DOK_VERIFICATION_WORKFLOW.md`'s "The canonical projection" and "The
two-tier model" sections for the full predicate (mirrors
`dok_review.py`'s `entry_is_verified` / `entry_is_malformed` /
`tool_state_for` docstrings exactly). In one line: `tool_state_for(uid,
latest, approved)` returns `"unreviewed"` (no entry), `"invalid-entry"`
(latest entry fails baseline well-formedness), `"reviewed_once"`
(well-formed but not verification-grade), or `"verified"` (passes
`entry_is_verified` — resolved disposition, no unresolved prior NSC,
rubric version approved and non-retroactive).

## Screens / flow (as built)

Three views over the same two data sources (`dok_wave_plan.json` +
`review_log.jsonl`), no network calls, no auth:

1. **`review` (per-item decision).** `dok_review.py review --item-uid <uid>
   --reviewed-by <name> --disposition {confirm,change,needs-source-check}
   [--chosen-dok N] [--rationale ...] [--provenance ...] [--item-basis ...]
   [--resolves-source-check] --rubric-version <v> [--note ...]
   [--reviewed-at <iso>]`. Validates fully, builds the record, computes
   `prior_unresolved_nsc` over the full existing chain, appends exactly one
   line, and prints a one-line confirmation.
2. **`queue`** — driven directly by `dok_wave_plan.json`'s stored order
   (`iter_queue_items`: waves `"0"`..`"4"`, lessons in stored dict order,
   items in stored list order — the plan's own wave + intra-wave sort).
   `--wave`, `--state` (any `TOOL_STATES` value), `--limit`, `--next`
   (defaults to `unreviewed`, limit 20), `--json`. Each row shows
   `tool_state_for(uid, latest, approved)` — never masquerading as the
   wave plan's registry-derived `dok_status`.
3. **`progress`** — per-wave and overall counts by `tool_state`
   (`compute_progress`), using the log's latest-entry-per-`item_uid`
   projection — never per-`item_id` (85 ids each cover 2 rows and would
   double-count).
4. **`promote`** — emits a read-only promotion PROPOSAL for one
   `--item-uid` (never writes the registry); see below.
5. **`report`** — writes a static, read-only HTML snapshot.

## Promotion: proposals-only, re-derives against disk

`promote` does NOT trust any stamp on the log entries it reads
(`provenance_resolved`, `confirmation_basis`, `prior_unresolved_nsc`, ...)
as authoritative by itself. `build_promotion_proposal` walks the FULL entry
chain for the `item_uid`, re-validates every entry structurally,
RE-DERIVES provenance resolution live against the calibration directory
for every confirm / textbook-exact-change / resolves_source_check entry,
RE-DERIVES the needs-source-check chain state, and finally re-asserts
`entry_is_verified()` on the latest entry as the single authoritative gate.
It reads the one registry row identified by the frozen `registry_line`
join and emits a **proposal JSON file** elsewhere (`tools/dok-review/proposals/`
by default) — it never opens `registry.jsonl` in a write mode and never
modifies it, regardless of rubric state. Turning a proposal into an actual
registry edit remains a **separate, deliberate, human-reviewed,
git-committed step** — never a side effect of running `promote`, and
outside this tool's own write surface.

## Flow-back to registry: `reviewed_by`/`reviewed_at` are metadata, not authority

`questionbank/registry.jsonl`'s own `reviewed_by` (string) and
`reviewed_at` (ISO-8601 string) fields — if a future, deliberate promotion
step ever writes them onto a row — are **application-time bookkeeping
only**. They are NEVER read as verification authority by this tool, by
`gen_dok_wave_plan.py`, or by any consumer described in this document.
**The single verification authority for every consumer is the canonical
projection**: the item_uid's latest `review_log.jsonl` entry passing
`dok_review.entry_is_verified()` under the current `rubric_approvals.json`
manifest — equivalently, the wave plan's `review_state == 'verified'` for
that item_uid, since `gen_dok_wave_plan.py`'s `dok_status` and
`review_state` fields come from this exact same projection (imported, not
reimplemented) rather than from any separate computation. One canonical
projection; every consumer agrees, because there is exactly one
implementation of it.

**RESOLVED (NT7-R Stage R2):** `inventory/build_content_readiness_inventory.py`
now derives its own `verified` via this SAME canonical projection
(`dok_review.entry_is_verified` via `tool_state_for`), computed
INDEPENDENTLY from registry + alias map + review log + approvals manifest
— never from registry `reviewed_by`/`reviewed_at`, and never by reading
`dok_wave_plan.json` itself, so the two builders' agreement is a real
cross-check, not a copy. See `DOK_VERIFICATION_WORKFLOW.md`'s Safeguards
section for the full resolution note and the one named future step still
open (`inventory/provenance-audit/audit_match_quality.py`).
