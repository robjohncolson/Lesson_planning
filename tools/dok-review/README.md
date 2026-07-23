# dok_review.py

Local, testable DOK-verification review tool for the question bank. Reads
three **frozen, read-only** inputs and never writes to any of them:

- `inventory/dok-workflow/dok_wave_plan.json` (the review queue)
- `questionbank/registry.jsonl` (the question bank)
- `questionbank/calibration/*.json` (Savvas-anchor provenance sources)

It writes exactly two things, both inside this directory:

- `review_log.jsonl` — append-only, one JSON object per review decision.
- `rubric_approvals.json` — **edited by hand by a human, never by this
  tool.** See "Rubric-approvals manifest" below.

`promote` never writes the registry — it only ever emits a proposal JSON
file for a human to apply manually.

This tool implements the operational mechanics of **DOK Acceptance Rubric
v0.2** (`inventory/decision-console/DOK_RUBRIC_v0.2.md`). That rubric is now
**APPROVED** — effective 2026-07-20T19:06:13-04:00 — see "Rubric-approvals
manifest" for what that does and does not unlock today.

## Two-tier model: REVIEWED vs. VERIFIED

This tool tracks two distinct tiers. They are not the same thing.

- **REVIEWED** (tool_state `reviewed_once`) — the latest log entry for the
  item is *well-formed*: non-empty `reviewed_by`, a parseable `reviewed_at`,
  and a recognized `decision`. A reviewer having looked at an item and
  recorded *something well-formed* is REVIEWED. That is all it means.
- **invalid-entry** — the latest entry *fails* that baseline well-formedness
  bar (empty/whitespace `reviewed_by`, missing/unparseable `reviewed_at`, or
  an unrecognized `decision`). This is a distinct, worse-than-unreviewed-ish
  state — **not** `reviewed_once`. It normally only arises from a
  hand-crafted or corrupted log line, since the CLI's reject-at-entry gate
  refuses to append anything this malformed.
- **VERIFIED** — strictly stronger than REVIEWED. See `entry_is_verified()`
  in `dok_review.py` for the exact predicate; in prose, ALL of:
  1. well-formed (as above);
  2. a resolved, verification-grade disposition:
     - `decision == "confirm"` AND `confirmation_basis ==
       "rule-1-textbook-provenance"` — the confirm's `--provenance` resolved
       against `questionbank/calibration/` on disk (see "Provenance scheme"
       below). A confirm with **no** provenance is
       `"rule-2-adjacent-unsourced"`; a confirm with **free-text/unresolved**
       provenance is `"rule-2-adjacent-unsourced-claim"`. Only the resolved
       (rule-1) form is verification-grade.
     - OR `decision == "change"` AND `new_dok` in `{1, 2, 3}` AND `rationale`
       non-empty AND `provenance` non-empty (rule 5) AND `item_basis` in
       `ITEM_BASES` AND (`item_basis != "textbook-exact"` OR the provenance
       resolved on disk). See "item_basis" below.
     - `decision == "needs-source-check"` is **never** verified by itself
       (terminal-unresolved, rule 2).
  3. **no unresolved needs-source-check anywhere earlier in this item_uid's
     chain** (`prior_unresolved_nsc` is falsy) — see "NSC attestation" below;
  4. `rubric_version` is in the rubric-approvals manifest, **and** the
     entry's tool-generated `recorded_at` is not earlier than that version's
     `approved_at` — see "Rubric-approvals manifest" below. **No entry with
     no rubric_version at all (legacy-shaped) is ever verified.**

## Rubric-approvals manifest (read this before anything else)

`rubric_approvals.json` in this directory now ships as:

```json
{
  "_comment": "...",
  "approvals": [
    {
      "version": "v0.2",
      "approved_at": "2026-07-20T19:06:13-04:00"
    }
  ]
}
```

**One approval.** DOK rubric v0.2 was PROPOSED, then APPROVED by a teacher
through the console's Section 5 decision control, effective
2026-07-20T19:06:13-04:00 — that timestamp is the one recorded above. Any
FUTURE rubric version remains PROPOSED, not approved, until a teacher
approves it in turn. Per `DOK_RUBRIC_v0.2.md`, for any not-yet-approved
version:

> *"no review-log entry of any kind may be recorded under it, and nothing …
> may be described as having a recorded verified status"* until then.

**This tool's documented position:** recording a review-log entry *before*
a rubric version's approval is permitted and useful — a reviewer can get
the recording work done in parallel with the approval process. But
verification under that version is **impossible** until a teacher approves
it, and — this is the retroactivity guard — **a pre-approval record can
never convert to VERIFIED, even after approval happens.** It remains a
REVIEWED-tier record forever. To become eligible, the item must be
**RE-REVIEWED**: a brand-new log entry, appended (and therefore
`recorded_at`-stamped) after the approval, for the same `item_uid`. The
VERIFIED count is whatever the log + manifest compute at read time (run
`progress` for the current number); the first post-approval recordings
landed 2026-07-22 (NT10: RC's 39 lesson-5-4 batch confirmations), retiring
the earlier zero-entries state.

### Manifest mechanics

`load_rubric_approvals(path=None)` reads the manifest and returns
`{version: approved_at (datetime)}`. **Fail closed:**

| Condition | Result |
|---|---|
| File missing | `{}` (silent — "no approvals yet" is the normal pre-approval state) |
| Malformed JSON | `{}` + one stderr warning |
| Unexpected shape (not an object, or `approvals` not a list) | `{}` + one stderr warning |
| A non-object entry in `approvals` | `{}` + one stderr warning |
| An entry's `version` is not a non-empty string | `{}` + one stderr warning |
| An entry's `approved_at` is missing/unparseable | `{}` + one stderr warning |
| Valid | the parsed `{version: approved_at}` dict |

A single malformed entry poisons the **whole** load to `{}` — this tool
would rather treat everything as unapproved than guess at a
partially-trustworthy manifest.

### `recorded_at` vs. `reviewed_at`

- `reviewed_at` — supplied by the reviewer (`--reviewed-at`, defaults to
  "now"). This is *when the reviewer says they did the review* — a
  historical fact the reviewer controls, used for the append-only
  monotonicity check (see "Timestamp integrity" below).
- `recorded_at` — stamped by `append_review()` at the moment of the actual
  write, via `datetime.now().astimezone().isoformat()`. **There is no CLI
  flag for this and a reviewer cannot supply it.** This is what makes the
  retroactivity guard mechanically real: verification compares
  `recorded_at` (when the tool actually wrote the line) against the
  manifest's `approved_at`, not the reviewer-supplied `reviewed_at`, which a
  reviewer could otherwise backdate to smuggle a pre-approval entry into
  looking post-approval.

### `--approvals` flag / `approvals_path` parameter

Every verification-aware function (`entry_is_verified`, `tool_state_for`,
`get_queue_rows`, `compute_progress`, `build_report_html`,
`build_promotion_proposal`) also takes a trailing `approvals_path=None`
keyword parameter, threaded straight into `_resolve_approved_versions` /
`load_rubric_approvals`. The CLI exposes this as a global `--approvals`
flag (default: `tools/dok-review/rubric_approvals.json`, i.e.
`DEFAULT_APPROVALS`) — every subcommand accepts it, e.g.:

```bash
python -B dok_review.py --approvals /path/to/other_manifest.json progress
```

Passing an explicit `approvals_path` (or `--approvals`) does not change
what the tool writes — it only changes which manifest is read for the
approval check, exactly like `--plan`/`--registry`/`--log` do for their
respective inputs. `approvals_path` is ignored whenever
`_approved_versions_override` is given (see below).

### Test-only override

Every one of those same functions ALSO takes an
`_approved_versions_override=None` parameter, appended immediately before
`approvals_path`. When `None` (the ONLY way any `cmd_*` production entry
point ever calls these), the manifest is loaded from disk via
`approvals_path` (default: the real manifest). Tests pass a non-`None` dict
(`{version: datetime-or-ISO-string}`) to simulate a DIFFERENT approval
state **without ever touching a manifest file**. No `cmd_*` function ever
passes a non-`None` value here — grep the module for
`_approved_versions_override=` to confirm every call site.

## Provenance scheme

`--provenance` accepts free text, but only one shape *resolves* against
disk and earns rule-1 (verification) grade:

```
calibration-anchor:<lesson>:<item-ref>
```

**Item-bound resolution (NT6 round 3, G1).** Resolution
(`resolve_provenance(provenance, calibration_dir, item)`, read-only, never
writes) now takes the reviewed **item** as a required argument and requires
ALL of the following — not just "some anchor exists somewhere in the cited
lesson's file", but "an anchor for **this specific item**":

- the whole string is non-empty and matches the scheme literally
  (`calibration-anchor`);
- `<lesson>` is non-empty, matches `^[A-Za-z0-9._-]+$`, does **not** contain
  `".."` (a dedicated path-traversal guard — the regex alone would allow
  `".."` since `.` is a permitted character), and
  `questionbank/calibration/<lesson>.json` exists and parses;
- `<lesson>` is **exactly** the reviewed item's own `lesson` — a ref citing
  any *other* lesson never resolves, even if that other lesson's file has a
  perfectly real anchor;
- the item itself has a **derivable calibration identity**
  (`derive_item_calibration_identity(item)`), computed from its legacy `id`:
  - ids ending `-savvas-q<N>` (e.g. `3-5-savvas-q27`) → `("practice", N)`.
    Split/multi-part practice ids (e.g. `4-3-savvas-q36-partA-build`) do
    **not** match — they carry a suffix after the number, so they
    deliberately get **no** identity.
  - ids ending `-ex-<N>` / `-example-<N>` (e.g. `4-3-ex-1`) → `("example",
    N)`, matching an `item_analysis` key shaped `example_<N>`. This is
    anchored at the end and requires a real separator between `ex` and the
    digits, so RTI-support ids that merely *mention* an example number (e.g.
    `3-5-rti-ex3-1`, `3-5-rti-support-ex6-1` — support material *for*
    Example 3 / Example 6, not the example itself) do **not** false-match.
  - anything else (try-it ids, lesson-quiz ids like `3-5-lq-q2`, TE/concept-
    box slugs, ...) has **no** derivable identity — rule-1 is **impossible**
    for such an item under the current calibration corpus, no matter what
    `--provenance` is supplied. It can only ever be rule-2-adjacent.
- `<item-ref>` normalizes (`normalize_provenance_item_ref()`) to a number
  equal to the item's own identity number, and either specifies no kind or
  the item's own kind. Accepted ref shapes: `"27"`, `"#27"` (kind
  unspecified); `"q27"`, `"practice #27"`, `"practice-27"`, `"practice 27"`
  (kind `practice`); `"example_2"`, `"example 2"`, `"ex 2"`, `"ex-2"` (kind
  `example`). There is **no substring semantics** — a ref must parse to
  *exactly* one kind-optional number token, or it normalizes to `None` and
  never resolves (a bare `"a"` or the bare word `"practice"` with no number
  are both `None`, not a best-effort guess);
- and finally, the calibration file actually **contains** an entry for that
  same identity: an `example` identity requires `item_analysis` to have key
  `f"example_{N}"`; a `practice` identity requires **either** some anchor
  across `dok2_anchors` + `dok3_anchors` whose `"source"` string's **first**
  `"practice #<M>"` match (case-insensitive) has `M == N`, **or** (NT10,
  Fable-authorized semantic alignment, 2026-07-22) the item's own number
  `N` appearing in one of the lesson's `item_analysis` `dok<k>` lists —
  the **same** evidence source `gen_dok_wave_plan.py`'s `build_item_to_dok`
  reads for `te_bucket`/`match_quality`. This alignment exists because a
  calibration intake may transcribe the TE Item Analysis table without
  adding curated anchors (`questionbank/calibration/5-4.json` is the first
  such file: `item_analysis` populated, `dok2_anchors`/`dok3_anchors`
  deliberately empty); the tool must accept the same textbook evidence the
  generator does. The three-way item binding (lesson equality, exact
  number identity, an entry for that number) is unchanged — this only adds
  a second on-disk location where the number's entry may live. Never a bare
  substring scan, and never a number pulled out of an anchor's prose (an
  anchor sourced `"... anchors Example 4"` is not thereby a match for
  `example_4` — only `item_analysis` keys bind example identities).

**Examples**, against `questionbank/calibration/4-1.json` (which has
`"item_analysis": {"example_2": {...}, ...}`) and
`questionbank/calibration/3-5.json` (whose `dok3_anchors` includes an entry
sourced `"Savvas Practice #27 (Model With Mathematics, lesson 3-5, anchors
Example 4)"`):

- For the item `3-5-savvas-q27` (lesson `3-5`, own identity `("practice",
  27)`): `calibration-anchor:3-5:practice #27`, `...:27`, `...:q27` all
  → resolve (matches its own anchor) → rule-1-grade.
- For that **same** item: `calibration-anchor:4-1:example_2` → does **not**
  resolve — wrong lesson (`4-1` ≠ the item's own `3-5`), even though
  `4-1.json` really does have an `example_2` key.
- For that same item: `calibration-anchor:3-5:practice #999` (a different,
  nonexistent practice number) → does **not** resolve — number mismatch
  against the item's own identity (`27`).
- For a lesson-quiz item like `3-5-lq-q2` (no derivable identity at all):
  `calibration-anchor:3-5:practice #2`, even if `3-5.json` happened to have
  a real `"Practice #2"` anchor → **never** resolves — the item itself has
  no calibration identity, so rule-1 is structurally impossible for it.
- `calibration-anchor:3-5:a` or `calibration-anchor:3-5:practice` (no
  number) → does not resolve — underspecified ref, normalizes to `None`.
- `TE p.41, my own read` (free text, no scheme) → does not resolve →
  rule-2-adjacent-unsourced-claim.
- `` (empty) → rule-2-adjacent-unsourced.
- `calibration-anchor:..:example_2` (path-traversal attempt) → does not
  resolve → False / claim.

Every appended record stamps `provenance_resolved` (bool), computed once at
entry time via the resolver. **`promote` never trusts this stamp** — it
re-derives resolution live against disk (see "Promotion" below).

## Timestamp integrity

`parse_iso(value)` is a strict `datetime.fromisoformat` parse — `None` on
any failure (wrong type, empty, unparseable, **or naive**). No fuzzy
parsing.

**SINGLE TIMESTAMP POLICY (NT6 round 3, G2): every instant this tool reads
or writes must be offset-aware.** A naive datetime (no UTC offset —
`tzinfo is None` or `utcoffset() is None`) parses to `None`, exactly like a
malformed string. This flows everywhere `parse_iso` is used: entry
validation (`entry_is_malformed`, chain validation), the per-item
monotonicity check below, chain-order validation at `promote` time, the
rubric-approvals manifest's `approved_at`, and the retroactivity gate
(`recorded_at` vs. `approved_at`). Rejecting naive datetimes **at parse
time** is what makes every later ordering comparison between two parsed
timestamps safe — Python raises `TypeError` comparing a naive and an aware
datetime, and this policy makes that comparison unreachable by
construction. Every comparison site (`cmd_review`'s monotonicity check,
`promote`'s chain-order check, `entry_is_verified`'s and `promote`'s
`recorded_at`-vs-`approved_at` check) additionally wraps the comparison in
`try/except TypeError -> fail closed` as defense in depth, not as the
primary safeguard.

- At entry: the (supplied or defaulted) `--reviewed-at` must parse (and be
  aware), or the review is rejected before anything is appended.
- **Per-item monotonicity:** if the `item_uid` already has entries, the
  latest one's `reviewed_at` must parse (if it doesn't: `"existing log
  entry unparseable -- fail closed"`, refuse), and the new `reviewed_at`
  must **not be strictly earlier** (equal is allowed). Otherwise: `"predates
  the item's latest existing review"`, refuse. This kills a
  stale-timestamp spoof where a reviewer tries to backdate a `confirm` to
  before an unresolved `needs-source-check` in the same chain.
- **Chain order at `promote` time (NT6 round 3, G2):** after per-entry
  structural validation, `build_promotion_proposal` additionally validates
  that `reviewed_at` is non-decreasing along the FULL chain's append order
  — a crafted log with two individually well-formed entries that go
  backwards in time is rejected, naming the offending adjacent chain
  positions.
- Resolution accounting (`_chain_pending_nsc_states`, "latest wins" for
  display) stays **append-order**, not sorted-by-timestamp, as always.

## invalid-entry state

`TOOL_STATES = ("unreviewed", "invalid-entry", "reviewed_once", "verified")`.

`tool_state_for()` classifies the *latest* entry as `"invalid-entry"` when
ANY of: `reviewed_by` is missing/blank, `reviewed_at` is missing/unparseable,
or `decision` is not one of `DISPOSITIONS`. This state is **not**
`reviewed_once` — it is its own, worse bucket. `queue --state invalid-entry`
filters to it; `compute_progress()` reports it per-wave and overall as
`invalid_entry`, **excluded** from `reviewed_once_or_better`; the HTML
report shows it in the progress table and per-item in the queue table.

**Decision-specific malformedness (NT6 round 3, G3).** The well-formedness
bar is not just the three universal fields above — it is also
decision-specific, matching the same bar `promote`'s `_validate_chain_entry`
already holds crafted logs to:

| `decision` | Also required to NOT be `"invalid-entry"` |
|---|---|
| `change` | `new_dok` in `{1, 2, 3}` AND non-whitespace `rationale` AND non-whitespace `provenance` AND `item_basis` in `ITEM_BASES` |
| `needs-source-check` | non-whitespace `rationale` |
| `confirm` | `confirmation_basis` in `{"rule-1-textbook-provenance", "rule-2-adjacent-unsourced", "rule-2-adjacent-unsourced-claim"}` |

A `change` entry missing its rationale, provenance, a valid `new_dok`, or a
valid `item_basis` is a structurally incomplete record, not merely
"reviewed but unverified" — it is `"invalid-entry"`.

## `item_basis` (rule 3: R1/R2 vs. R3)

Every `change` **requires** `--item-basis`; it is **rejected** with
`confirm` or `needs-source-check` (item_basis only makes sense for a
change — it classifies *why* the DOK is being overridden).

| `item_basis` | Rubric rule | Verification-grade requirement |
|---|---|---|
| `textbook-exact` | R1/R2 — this "change" is actually a **source-dispute resolution**: the reviewer is asserting the textbook-confirmed DOK differs from what the wave plan has on file. | Only when `--provenance` **resolves on disk** (the `calibration-anchor` scheme). Free text is recorded but not verification-grade. |
| `adapted` / `split` / `extended` / `teacher-authored` | R3 — the item has been changed from its original textbook form; its DOK is set by its actual cognitive demand, not inherited textbook provenance. | `--rationale` and `--provenance` both non-empty (rule 5) — **free-text provenance is acceptable**, no on-disk resolution required. |

## NSC (needs-source-check) attestation

A `needs-source-check` is terminal-unresolved (rule 2). It is resolved
**only** by a LATER entry for the same `item_uid` that stamps BOTH:

- `resolves_source_check: true` (via `--resolves-source-check`), AND
- provenance that resolves on disk.

A plain later `confirm`/`change` **without** that explicit attestation does
**not** resolve it — `prior_unresolved_nsc` stays `true` on every
subsequent entry until the attestation appears, and `entry_is_verified()`
vetoes verification whenever `prior_unresolved_nsc` is truthy, **regardless
of how clean that later entry otherwise looks** (e.g. a resolving,
rule-1-grade confirm still won't verify if it sits on top of an
unresolved nsc without the attestation).

`--resolves-source-check`:

- Allowed only with `confirm`/`change` (rejected with `needs-source-check`).
- Rejected at entry if the item_uid's chain currently has **no** unresolved
  needs-source-check (`"nothing to resolve"`).
- Rejected at entry if `--provenance` does not resolve on disk (the
  attestation itself needs rule-1-grade provenance).

`_chain_pending_nsc_states()` implements this as a single boolean "pending"
toggle walked across the chain in order: a `needs-source-check` entry sets
it `True`; a later entry with a re-derived-resolving
`resolves_source_check` attestation clears it to `False`; anything else
leaves it unchanged. This same function backs the `prior_unresolved_nsc`
stamp at entry time, the `--resolves-source-check` "nothing to resolve"
check, and `promote`'s re-derived (never-trusted) nsc gate.

## DOK domain — R4: cognitive demand, not difficulty

> DOK measures cognitive demand, not difficulty. A long, multi-part, or
> context-heavy item is not automatically higher DOK than a short one, and
> a computationally hard item is not automatically higher DOK than an easy
> one. DOK tracks the kind of thinking required (recall vs. procedure vs.
> strategic reasoning vs. extended investigation), never how hard, how
> long, or how error-prone the item is to complete.

(Rubric rule 4, verbatim — copied from `DOK_RUBRIC_v0.2.md`'s Authority
Hierarchy with only the list numbering, bold markers, and the source
markdown's hard line-wraps stripped; no paraphrase, no added or removed
words.) This exact sentence (`dok_review.DOK_NOT_DIFFICULTY_NOTE`) appears
in the top-level CLI `--help` epilog, the `review` subcommand's `--help`
epilog, and here — each of those two epilogs follows it with a
clearly-separated tool-specific note, never blended into the quote itself.

`--chosen-dok` is restricted to `{1, 2, 3}` in **three independent places**
(defense in depth, not just argparse):

1. `argparse` `choices=[1, 2, 3]` on `--chosen-dok` (CLI-level; DOK 4 exits
   with code 2 before any Python of ours runs);
2. `_validate_review_args()` — returns an error string if a `chosen_dok`
   outside the domain is ever passed programmatically (bypassing argparse);
3. `build_review_record()` — raises `ValueError` for the same reason. This
   is a module-path guard: even a direct, non-CLI call to
   `build_review_record()` with `disposition="change", chosen_dok=4` is
   rejected.

## Disposition semantics

| Disposition | Meaning | reviewer_dok / new_dok | Requires |
|---|---|---|---|
| `confirm` | Reviewer agrees with the wave plan's `prior_dok`. | `reviewer_dok = prior_dok`, `new_dok = None` | `--provenance` optional; `confirmation_basis` derived from resolution (empty → unsourced; free text → unsourced-claim; resolves → rule-1). |
| `change` | Reviewer overrides `prior_dok` with `--chosen-dok` (1-3 only). | `reviewer_dok = new_dok = chosen_dok` | `--rationale`, `--provenance` (rule 5), and `--item-basis` (rule 3) all required. Rejected at entry if `--chosen-dok` equals `prior_dok` (that's a confirm, not a change). |
| `needs-source-check` | Terminal-unresolved (rule 2): provenance is contested or missing. | `reviewer_dok = new_dok = None` | `--rationale`. Never verified by itself; resolved only by a later `--resolves-source-check` attestation. |

**Reject-at-entry.** Every `review` invocation is fully validated *before*
`append_review` is ever called (`_validate_review_args()` plus the
timestamp/monotonicity checks in `cmd_review()`). Any validation failure
prints an `ERROR:` to stderr, exits nonzero, and appends **nothing** to the
log.

## `promote`: re-derives against disk

Unlike the "display" tier (`queue`, `progress`, `report` — fast, offline,
trust the stamps written at review time), `promote` **never trusts a
stamp** as authoritative. It walks the item_uid's FULL entry chain (every
line, in append order — not just the latest) and:

1. **Structural + on-disk re-derivation, per entry, in order** — rejects on
   the FIRST malformed entry, naming its 1-based chain position and the
   defect: unknown `decision`; blank `reviewed_by`; unparseable
   `reviewed_at`; a `change` missing `rationale`/`provenance`/valid
   `new_dok`/valid `item_basis`; a `change` with `item_basis ==
   "textbook-exact"` whose provenance does **not** re-resolve on disk; a
   `confirm` whose stamped `confirmation_basis ==
   "rule-1-textbook-provenance"` but whose provenance does **not**
   re-resolve (this is exactly what catches a **crafted** log line that
   lies about its own `confirmation_basis`); any entry whose
   `resolves_source_check` attestation does not re-resolve. Every
   `resolve_provenance` re-derivation here is **item-bound** (NT6 round 3,
   G1): a crafted entry citing a different item's (or a different
   practice/example number's) calibration anchor is rejected even if that
   anchor is perfectly real in the cited lesson's file — see "Provenance
   scheme" above.
2. **Chain order (NT6 round 3, G2)** — after per-entry validation,
   `reviewed_at` must be non-decreasing along the full chain's append
   order; a crafted log with two individually well-formed entries that go
   backwards in time is rejected, naming the offending adjacent positions.
3. **Re-derived needs-source-check chain state** — any unresolved nsc
   anywhere in the chain (recomputed live, ignoring any stored
   `prior_unresolved_nsc`/`provenance_resolved` stamps) → `"unresolved
   needs-source-check"`, refuse.
4. **Latest-entry confirm gate** — a `confirm` whose `confirmation_basis`
   isn't `rule-1-textbook-provenance` → `"lacks source provenance"` /
   `"not verification-grade"`, refuse.
5. **Rubric gate** — latest entry's `rubric_version` not in the manifest →
   exact phrase `"rubric version not approved"`. In the manifest but
   `recorded_at` missing/unparseable/earlier than that version's
   `approved_at` → exact phrase `"recorded before approval"` plus a note
   that re-review is required.
6. **FINAL authoritative gate** — `entry_is_verified(latest,
   _approved_versions_override=<the same approved mapping>)` must be `True`,
   or refuse with a generic `"not verification-grade"`. Verification-grade
   judgment is thereby delegated to the single predicate — no parallel
   logic, no unknown-decision fall-through.

`promote` never opens `registry.jsonl` for write. It only ever emits a
proposal JSON (`registry_written: false`, plus a `human_note` explaining a
human must apply the change manually).

## Example invocations

The examples below that need a REAL resolving anchor all use
`iu_3b42ab3340d5` (`3-5-savvas-q27`) — ONE available resolving example,
reused across several invocations purely for illustration. As of this
writing, the full set of shipped wave-plan items whose own
`calibration-anchor:` ref actually resolves under the item-bound resolver
is: TWO practice items via `questionbank/calibration/3-5.json`'s anchors —
`3-5-savvas-q27` (`iu_3b42ab3340d5`, the `"Savvas Practice #27 ..."`
dok3 anchor) and `3-5-savvas-q30` (`iu_7f589eaba8ad`, the `"Savvas
Practice #30 ..."` dok3 anchor) — plus 33 example items (`-ex-N` ids)
across lessons 4-3, 4-5, 5-1, 5-5, 6-3, and 6-4, which resolve via their
lesson file's `item_analysis` keys (`example_N`). The 3-5 file's other two
anchors (`"Savvas Practice #7"` and `"Savvas Practice #18"`, both
dok2 anchors) currently resolve for NO shipped item: the wave plan
contains no `3-5-savvas-q7` or `3-5-savvas-q18` row, so under the
item-bound rules nothing can cite them. Likewise, `4-1.json`'s populated
`item_analysis` contributes nothing today because the wave plan carries no
4-1 example items. `resolve_provenance` is item-bound (see "Provenance
scheme" above), so a resolving ref must cite the SAME lesson and
practice/example number as the item actually being reviewed.

```bash
# confirm, with resolving provenance (rule 1) -- REVIEWED now. IF this
# entry's recorded_at ends up BEFORE some rubric version's approved_at, it
# can NEVER become VERIFIED, even after that approval takes effect -- see
# "Rubric-approvals manifest" above: recorded_at is stamped at the moment
# of THIS write, and the retroactivity guard means an entry recorded
# before a version's approval never verifies, no matter how well-formed
# and rule-1-grade it is. (DOK rubric v0.2 is, in fact, already approved as
# of 2026-07-20T19:06:13-04:00 -- this example illustrates the general
# retroactivity mechanic, which applies the same way to any future rubric
# version's approval.)
python -B dok_review.py review \
  --item-uid iu_3b42ab3340d5 --reviewed-by lynn \
  --disposition confirm --provenance "calibration-anchor:3-5:practice #27" \
  --rationale "matches the TE verbatim" --rubric-version v0.2

# ... illustrating the retroactivity guard: suppose the entry above had
# been recorded BEFORE some rubric version's approval. Even after a
# teacher later approves that version (by hand-editing
# rubric_approvals.json -- adding {"version": ..., "approved_at": "<some
# ISO-8601 timestamp>"} to its "approvals" list), the entry recorded
# BEFORE still never verifies. To make THIS item verifiable, the SAME
# item_uid must be RE-REVIEWED -- a brand-new entry, appended (and
# therefore recorded_at-stamped) AFTER that approval -- which is what
# actually becomes eligible for VERIFIED:
python -B dok_review.py review \
  --item-uid iu_3b42ab3340d5 --reviewed-by lynn \
  --disposition confirm --provenance "calibration-anchor:3-5:practice #27" \
  --rationale "re-reviewed post-approval, still matches the TE verbatim" \
  --rubric-version v0.2

# confirm, WITHOUT provenance -- REVIEWED but rule-2-adjacent, never VERIFIED
python -B dok_review.py review \
  --item-uid iu_e32a6f7f8909 --reviewed-by lynn \
  --disposition confirm --rubric-version v0.2

# change, item_basis textbook-exact -- needs BOTH rationale AND resolving
# provenance (chosen-dok must differ from this item's prior_dok, which is 3)
python -B dok_review.py review \
  --item-uid iu_3b42ab3340d5 --reviewed-by lynn \
  --disposition change --chosen-dok 2 --item-basis textbook-exact \
  --rationale "this item requires strategic reasoning, not recall" \
  --provenance "calibration-anchor:3-5:practice #27" --rubric-version v0.2

# change, item_basis adapted -- free-text provenance is acceptable (rule 3);
# adapted/split/extended/teacher-authored items never need a resolving
# calibration-anchor ref, so the item's own lesson/identity don't matter here
python -B dok_review.py review \
  --item-uid iu_77d25e1e6131 --reviewed-by lynn \
  --disposition change --chosen-dok 3 --item-basis adapted \
  --rationale "adapted from the textbook item, now asks for a full model" \
  --provenance "reviewer judgment against DOKframework.txt rule 4" \
  --rubric-version v0.2

# needs-source-check -- terminal-unresolved until a later attested resolution
python -B dok_review.py review \
  --item-uid iu_3b42ab3340d5 --reviewed-by lynn \
  --disposition needs-source-check \
  --rationale "cannot find this exact item in the TE" --rubric-version v0.2

# ... later, the attestation that actually resolves it:
python -B dok_review.py review \
  --item-uid iu_3b42ab3340d5 --reviewed-by lynn \
  --disposition confirm --resolves-source-check \
  --provenance "calibration-anchor:3-5:practice #27" \
  --rationale "found it, TE confirms" --rubric-version v0.2
```

### Expected `promote` rejections for unreviewed items

The real manifest has v0.2 approved, and the real `review_log.jsonl` now
carries entries (first recordings 2026-07-22), but `promote` against any
item_uid that has NO log entry still refuses for that reason:

```bash
$ python -B dok_review.py promote --item-uid iu_3b42ab3340d5
ERROR: no review found for item_uid 'iu_3b42ab3340d5' -- cannot promote an unreviewed item
```

**Illustrative: the rubric gate itself.** Once an item HAS been reviewed
(so `promote` gets past the "no review found" gate above), the rubric gate
fires instead whenever the latest entry's `rubric_version` is NOT in the
effective approved manifest — either a genuinely future/hypothetical
rubric version, or v0.2 evaluated against an EMPTY manifest (point
`--approvals` at a fresh, empty-`"approvals"` file instead of the real,
now-approved one):

```bash
$ python -B dok_review.py --approvals /path/to/empty_manifest.json promote --item-uid <a REVIEWED item_uid>
ERROR: item_uid '<uid>' rubric version not approved (rubric_version='v0.2' is not in the approved manifest) -- refusing to promote until a teacher approves this rubric version
```

Neither example writes a proposal file. `promote` stays proposals-only
regardless of rubric state: even once a review IS recorded and its
rubric version IS approved with a post-approval `recorded_at`, the CLI
only ever emits a proposal JSON (`registry_written: false`) for a human to
apply by hand — see "`promote`: re-derives against disk" below. The test
suite exercises both the rubric-approved and rubric-unapproved paths by
calling `build_promotion_proposal(..., _approved_versions_override=...)`
directly, or by pointing `--approvals` at a hermetic temp fixture — never
by touching the real manifest.

## Identity rule

Every operation is keyed by `item_uid`, the opaque primary key from the wave
plan — never by the legacy `id` field, which is shared by two distinct
registry rows for 85 items (e.g. `5-4-savvas-q41` is both `iu_3c70a19c8d36`
and `iu_77d25e1e6131`, with different waves and different `prior_dok`
values). Reviewing one never affects the other.

## Threat model (NT6 round 3, G6)

This is a **local-file tool** with no authentication, no file locking, and
no cryptographic binding between `review_log.jsonl` and the process that
wrote it. `promote` necessarily **trusts that the log file it is pointed at
(`--log`) was actually written by this tool**: `recorded_at` is stamped by
`append_review()` at the moment of the real write, but nothing stops a user
(or another program) from hand-editing, or fabricating from scratch, a
`review_log.jsonl`-shaped file with any `reviewed_at`, `recorded_at`, or
other stamped field it likes.

The defenses in this tool — structural per-entry validation, chain-order
validation, item-bound on-disk re-derivation of provenance, re-derived
needs-source-check state — constrain what such a **crafted** log can get
away with (see `TestCraftedLogPromotions` in the test suite for the
adversarial shapes this is exercised against: unknown decisions, blank
`reviewed_by`, unparseable timestamps, a `confirm` that lies about its own
`confirmation_basis`, a chain that goes backwards in time, an entry that
cites another item's calibration anchor, ...). These are **consistency
checks**, not tamper-proofing: a crafted log that is internally consistent
and satisfies every structural and re-derivation rule can still promote,
because there is no signature or checksum tying a log line to a genuine
`dok_review.py review` invocation. That is the accepted local threat model
for a single-teacher, local-file tool — it is designed to catch malformed,
inconsistent, or incompletely-attested entries (the ordinary failure mode:
a typo, a copy-paste error, an incomplete hand-edit), not to resist a
determined author of its own log file.

## Testing

All tests operate on copies of the frozen inputs inside a fresh
`tempfile.TemporaryDirectory()` — the real `review_log.jsonl` is never
created by the suite, no source file is ever opened in a write mode, and
`rubric_approvals.json` is never mutated. The real, shipped
`rubric_approvals.json` now has DOK rubric v0.2 approved; the suite is
nonetheless fully hermetic. `DokReviewTestBase.setUp()` writes an explicit,
EMPTY temp manifest (`self.approvals_path`) and `run_cli()` always passes
`--approvals` pointing at it, so the CLI path never reads the real
manifest either; direct library calls pass `approvals_path=self.approvals_path`
or an explicit `_approved_versions_override=...` to simulate whatever
approval state a test needs. The ONE exception, deliberately marked, is
`TestRealManifestIntegrationOnly`, which reads the real manifest to confirm
it actually contains the expected v0.2 approval.

```bash
python -B -m unittest test_dok_review -v
```
