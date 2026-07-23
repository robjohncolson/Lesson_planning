# Duplicate Legacy-ID Remediation — Question Bank `registry.jsonl`

## 1. Summary

`questionbank/registry.jsonl` holds 900 rows, but only **815 distinct
`id` strings**. **85 legacy id strings are shared by more than one row**
— i.e. 85 "duplicate-id groups" account for the gap between 900 rows
and 815 unique ids. In every case found in the current data, each
group has exactly 2 rows sharing one id string, and in every case the
two rows are genuinely different registry entries (different
`prompt` text) that happen to have been assigned the same legacy `id`
during authoring — not a single item accidentally duplicated verbatim.
All 85 groups are classified `merge-candidate`: a **human-review
recommendation** to merge each near-identical pair, not an automatic
merge (see Section 4).

**Locked canonical-identity decision** (this document does not
relitigate it, only implements it): the universal relational key going
forward is an opaque `item_uid`. Every existing `item.id` is preserved
as a `legacy_id` alias with full provenance (lesson, source,
prompt hash, registry line number). When distinct items share a legacy
id string, **each gets its own `item_uid`** — the shared id string
becomes an *ambiguous* alias flagged for human disambiguation. There is
**no renumbering and no silent merging** of registry rows. This
document and its companion script (`inventory/dedup/build_item_uid_map.py`)
only *propose* the mapping; `registry.jsonl` itself is untouched (read
read-only, never opened for writing).

## 2. Counts

| Metric | Count |
|---|---|
| Total registry rows | 900 |
| Unique legacy `id` strings | 815 |
| Duplicate-id groups (id shared by >1 row) | 85 |
| Distinct `item_uid`s assigned | 900 |
| Rows flagged `exact_duplicate` (identical `lesson`\|`source`\|`prompt_sha1`) | 0 |
| Ambiguous legacy ids (span >1 distinct `item_uid`) | 85 |

Every duplicate-id group in the current data spans exactly 2 rows, and
every one of those rows is a genuinely distinct item (no row is byte-for-byte
identical to another on `lesson` + `source` + `prompt`), so
`exact_duplicate_rows = 0` and all 85 groups are ambiguous.

## 3. The `item_uid` Algorithm

For each registry row (UTF-8 throughout):

```
prompt_sha1 = sha1(prompt.encode('utf-8')).hexdigest()      # "" if prompt is None; full 40-char hex
basis       = f"{lesson}|{source}|{prompt_sha1}"             # pipe-joined, in this order
item_uid    = "iu_" + sha1(basis.encode('utf-8')).hexdigest()[:12]
exact_tuple = (lesson, source, prompt_sha1)
```

Rows whose `exact_tuple` collides with another row's `exact_tuple`
necessarily hash to the same `item_uid` and are marked
`exact_duplicate=true` (this is what "exact-duplicate-needs-human"
would flag). No such collisions exist in the current 900 rows.

### Worked example (real row, `registry.jsonl` line 1)

```
id:          3-5-tryit-1a
lesson:      3-5
source:      Savvas Try It #1a (anchors Example 1)
prompt:      Factor each function. Then use the zeros to sketch its graph: f(x) = 4x^3 + 4x^2 - 24x.

prompt_sha1: a40e55be53e73915e460c87e5a1ae40b086a8ffe

basis:       3-5|Savvas Try It #1a (anchors Example 1)|a40e55be53e73915e460c87e5a1ae40b086a8ffe

item_uid:    iu_d3a3c0d48248
```

This row is not part of any duplicate-id group, so its alias-map entry
has `"ambiguous": false` and a single `item_uids` entry.

## 4. Disposition Report

Disposition rules applied to each of the 85 duplicate-id groups
(data-driven, computed from the registry — not hardcoded):

1. **`exact-duplicate-needs-human`** — the group contains a same-`exact_tuple`
   collision (rows collapse to one `item_uid`).
2. **`distinct-items-keep-both`** — no collision, but the group spans more
   than one distinct `lesson` OR more than one distinct `source` (clearly
   different items that merely collide on the id string).
3. **`merge-candidate`** — no collision, same `lesson` AND same `source`
   across the group, differing only in prompt text (a near-identical
   re-capture of the same Savvas slot — double-ingest with drift). This
   label is a **human-review recommendation to merge** the pair; it is
   **NOT an automatic merge**. The two distinct `item_uid`s already
   computed for these rows are **retained as-is** — nothing is
   collapsed, no row is removed, and no count (rows, item_uids, unique
   legacy ids, ambiguous count) changes as a result of this label. A
   human reviews the pair and decides whether to keep both, retire one,
   or otherwise reconcile them.

### Disposition tally

| Disposition | Count |
|---|---|
| `exact-duplicate-needs-human` | 0 |
| `distinct-items-keep-both` | 0 |
| `merge-candidate` | 85 |

**Why all 85 land in `merge-candidate`:** every duplicate-id group in
this dataset shares both the same `lesson` and the same `source` string
(e.g. `Savvas Practice #18 (lesson 5-1, anchors Example 4)`), and the two
rows differ only in minor capture text — a trailing MP standards tag, a
stray parenthesis, or a spacing/LaTeX-escape variant. This pattern —
double-ingest with drift — is exactly the case the `merge-candidate`
label exists for: the same Savvas slot was captured twice (once with,
once without a minor annotation), producing two registry rows that a
human should review and likely merge, without the tooling ever guessing
which capture is canonical. Confirmed examples from the data:

- `5-1-savvas-q18` (lines 144 vs 177) — one capture ends with `"... Explain
  your reasoning. MP.3"`, the other omits the `MP.3` tag.
- `5-4-savvas-q16` (lines 274 vs 305) — `"Use s to represent..."` vs
  `"Use (s) to represent..."` (parenthesization of the variable).
- `5-5-savvas-q12` (lines 391 vs 416) — `f \circ g` vs `f\circ g` (a
  whitespace/LaTeX-escape difference around `\circ`).

None of the 85 groups span more than one `lesson` or more than one
`source`, so `distinct-items-keep-both` is empty for this dataset. None
collapse to a shared `exact_tuple`, so `exact-duplicate-needs-human` is
also empty. **No group in the current data is claimed to be an exact
duplicate** — the data genuinely has zero exact-tuple collisions. All 85
`merge-candidate` pairs keep **two distinct `item_uid`s** until a human
disambiguates — this label recommends review, it does not perform a
merge.

### All 85 duplicate-id groups

All groups below have exactly 2 rows, a single lesson, and a single
source string per group (hence disposition `merge-candidate` for
every row — human review recommended, distinct `item_uid`s retained,
nothing auto-collapsed). Full per-row detail (registry line,
`prompt_sha1`, `item_uid`) lives in `item_uid_alias_map.json` under
`alias_map.<legacy_id>`.

| legacy_id | lesson(s) | source(s) | disposition | note |
|---|---|---|---|---|
| 5-1-savvas-q18 | 5-1 | Savvas Practice #18 (lesson 5-1, anchors Example 4) | merge-candidate | prompt differs only by trailing MP tag |
| 5-1-savvas-q19 | 5-1 | Savvas Practice #19 (lesson 5-1, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q20 | 5-1 | Savvas Practice #20 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q21 | 5-1 | Savvas Practice #21 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q22 | 5-1 | Savvas Practice #22 (lesson 5-1, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q23 | 5-1 | Savvas Practice #23 (lesson 5-1, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q25 | 5-1 | Savvas Practice #25 (lesson 5-1, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q26 | 5-1 | Savvas Practice #26 (lesson 5-1, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q27 | 5-1 | Savvas Practice #27 (lesson 5-1, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q28 | 5-1 | Savvas Practice #28 (lesson 5-1, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q29 | 5-1 | Savvas Practice #29 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q30 | 5-1 | Savvas Practice #30 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q31 | 5-1 | Savvas Practice #31 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q32 | 5-1 | Savvas Practice #32 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q33 | 5-1 | Savvas Practice #33 (lesson 5-1, anchors Example 3) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q34 | 5-1 | Savvas Practice #34 (lesson 5-1, anchors Example 3) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q35 | 5-1 | Savvas Practice #35 (lesson 5-1, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q36 | 5-1 | Savvas Practice #36 (lesson 5-1, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q37 | 5-1 | Savvas Practice #37 (lesson 5-1, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q38 | 5-1 | Savvas Practice #38 (lesson 5-1, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q39 | 5-1 | Savvas Practice #39 (lesson 5-1, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q40 | 5-1 | Savvas Practice #40 (lesson 5-1, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q41 | 5-1 | Savvas Practice #41 (lesson 5-1, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q42 | 5-1 | Savvas Practice #42 (lesson 5-1, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q43 | 5-1 | Savvas Practice #43 (lesson 5-1, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q44 | 5-1 | Savvas Practice #44 (lesson 5-1, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q45 | 5-1 | Savvas Practice #45 (lesson 5-1, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q46 | 5-1 | Savvas Practice #46 (lesson 5-1, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q47 | 5-1 | Savvas Practice #47 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q48 | 5-1 | Savvas Practice #48 (lesson 5-1, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q49 | 5-1 | Savvas Practice #49 (lesson 5-1, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-1-savvas-q50 | 5-1 | Savvas Practice #50 (lesson 5-1, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q16 | 5-4 | Savvas Practice #16 (lesson 5-4) | merge-candidate | prompt differs only by `s` vs `(s)` |
| 5-4-savvas-q17 | 5-4 | Savvas Practice #17 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q18 | 5-4 | Savvas Practice #18 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q21 | 5-4 | Savvas Practice #21 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q22 | 5-4 | Savvas Practice #22 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q23 | 5-4 | Savvas Practice #23 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q24 | 5-4 | Savvas Practice #24 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q25 | 5-4 | Savvas Practice #25 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q26 | 5-4 | Savvas Practice #26 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q27 | 5-4 | Savvas Practice #27 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q28 | 5-4 | Savvas Practice #28 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q29 | 5-4 | Savvas Practice #29 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q30 | 5-4 | Savvas Practice #30 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q31 | 5-4 | Savvas Practice #31 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q32 | 5-4 | Savvas Practice #32 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q33 | 5-4 | Savvas Practice #33 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q34 | 5-4 | Savvas Practice #34 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q35 | 5-4 | Savvas Practice #35 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q36 | 5-4 | Savvas Practice #36 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q37 | 5-4 | Savvas Practice #37 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q38 | 5-4 | Savvas Practice #38 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q39 | 5-4 | Savvas Practice #39 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q40 | 5-4 | Savvas Practice #40 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q41 | 5-4 | Savvas Practice #41 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q42 | 5-4 | Savvas Practice #42 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q43 | 5-4 | Savvas Practice #43 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q44 | 5-4 | Savvas Practice #44 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q45 | 5-4 | Savvas Practice #45 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-4-savvas-q46 | 5-4 | Savvas Practice #46 (lesson 5-4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q12 | 5-5 | Savvas Practice #12 (lesson 5-5, anchors Example 5) | merge-candidate | prompt differs only by whitespace around `\circ` |
| 5-5-savvas-q14 | 5-5 | Savvas Practice #14 (lesson 5-5, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q15 | 5-5 | Savvas Practice #15 (lesson 5-5, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q16 | 5-5 | Savvas Practice #16 (lesson 5-5, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q17 | 5-5 | Savvas Practice #17 (lesson 5-5, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q18 | 5-5 | Savvas Practice #18 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q19 | 5-5 | Savvas Practice #19 (lesson 5-5, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q20 | 5-5 | Savvas Practice #20 (lesson 5-5, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q21 | 5-5 | Savvas Practice #21 (lesson 5-5, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q22 | 5-5 | Savvas Practice #22 (lesson 5-5, anchors Example 2) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q23 | 5-5 | Savvas Practice #23 (lesson 5-5, anchors Example 3) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q24 | 5-5 | Savvas Practice #24 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q25 | 5-5 | Savvas Practice #25 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q26 | 5-5 | Savvas Practice #26 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q27 | 5-5 | Savvas Practice #27 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q28 | 5-5 | Savvas Practice #28 (lesson 5-5, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q29 | 5-5 | Savvas Practice #29 (lesson 5-5, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q30 | 5-5 | Savvas Practice #30 (lesson 5-5, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q31 | 5-5 | Savvas Practice #31 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q32 | 5-5 | Savvas Practice #32 (lesson 5-5, anchors Example 6) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q33 | 5-5 | Savvas Practice #33 (lesson 5-5, anchors Example 1) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q34 | 5-5 | Savvas Practice #34 (lesson 5-5, anchors Example 5) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q35 | 5-5 | Savvas Practice #35 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |
| 5-5-savvas-q36 | 5-5 | Savvas Practice #36 (lesson 5-5, anchors Example 4) | merge-candidate | same-slot re-capture |

All 85 rows above involve lessons **5-1**, **5-4**, and **5-5** only —
these appear to be the lessons where the Savvas practice sets were
captured/re-captured twice during authoring (once with, once without
minor annotation like the `MP.3` tag), landing two distinct registry
rows under the same `q##` slot number.

## 5. Proposed Migration Note (PROPOSED / NOT APPLIED)

This section describes how downstream references *would* rewire
through the alias table. **Nothing described here has been applied.**
`registry.jsonl` is unmodified; no row has been renumbered or merged.

- **`tex` `\bankitem{<legacy_id>}` lookups** resolve `legacy_id ->
  item_uid` via `alias_map`. For a non-ambiguous legacy id, this is a
  1:1 lookup. For one of the 85 **ambiguous** legacy ids, the lookup
  cannot bind to a single `item_uid` automatically — it must be
  resolved by matching on `(lesson, source, prompt_sha1)` (i.e. the
  calling context already knows which prompt text it wants) or by a
  human explicitly picking the correct `item_uid` from the 2 candidates
  in `alias_map.<legacy_id>.item_uids`.
- **Graph edges / evidence references** (e.g. `rehearses`, `prereq_ids`,
  `echoes` fields in the registry, or any external graph keyed by
  legacy id) migrate to `item_uid` keys. Edges currently pointing at one
  of the 85 ambiguous legacy ids are held pending human disambiguation
  — they are not auto-assigned to either candidate `item_uid`.
- **`merge-candidate` disposition (all 85 groups)**: flags a pair as a
  human-review recommendation to merge — it does **not** trigger any
  automatic action. Both candidate `item_uid`s stay live and resolvable
  through the alias table until a human reviews the pair in
  `alias_map.<legacy_id>.item_uids` and either confirms a merge (a
  future, separate, explicitly-applied step) or confirms both should
  stand. Nothing in this build/report performs that merge.
- **Invariants that must hold after migration:**
  - 900 registry rows -> 900 `item_uid`s (1:1, no collapsing, since
    `exact_duplicate_rows = 0` in this data).
  - All 815 legacy id strings retained as aliases (nothing dropped).
  - All 85 ambiguous aliases (all classified `merge-candidate`) remain
    mapped to their **distinct** `item_uid`s and pending human
    disambiguation until someone picks the canonical capture, merges
    them, or confirms both are needed — **never auto-collapsed**.
  - No registry row is renumbered, deleted, or merged with another row.

This note is **PROPOSED / NOT APPLIED**. No downstream file (`tex/*`,
graph data, or `registry.jsonl` itself) has been changed by this work.

## 6. How to Reproduce

From the repo root:

```bash
python inventory/dedup/build_item_uid_map.py
```

The script re-reads `questionbank/registry.jsonl` **read-only**,
recomputes everything in this document from scratch, rewrites
`inventory/dedup/item_uid_alias_map.json`, and reprints the
`SELF-ASSERTION: PASS` line plus the counts summary shown in Section 2.
Running it any number of times produces byte-identical output (verified
by diffing two consecutive runs).
