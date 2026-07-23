# Provenance Audit — Why the 22 Lesson 5-4 DOK-Conflict Pairs Carry `match_quality: "none"`

NT5, local-only, read-only. Produced by
`inventory/provenance-audit/audit_match_quality.py`, which re-runs the exact
functions from `inventory/dok-workflow/gen_dok_wave_plan.py` (imported, not
reimplemented) and writes its full row-level evidence to
`inventory/provenance-audit/provenance_audit_data.json`. All figures below
were read from that JSON or computed live during this audit; none are
estimated. `questionbank/registry.jsonl` sha256 was verified unchanged
before and after this audit
(`b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8`).

## 1. Executive answer

`match_quality` is not a check against "does this item have a DOK label."
Every one of the 900 registry rows already has a `dok` value from ingest.
`match_quality` instead measures a narrower, second thing: does the row's
Savvas item number appear in that **lesson's own `item_analysis` table**
inside `questionbank/calibration/{lesson}.json` — a hand/LLM-transcribed
map of "Savvas Teacher's Edition says item #N is DOK-bucket B" built from
the TE item-analysis page. `questionbank/calibration/5-4.json` exists on
disk (confirmed), but its `item_analysis` field is `{}` — an empty
dict, not missing data mid-lookup. Since `item_to_dok['5-4']` is
therefore empty, no lookup against it can ever succeed for any item
number, so **all 132 lesson-5-4 rows** get `match_quality: "none"`, not
just the 44 rows in the 22 conflicting pairs — via two distinct code
branches, not one (see §2 and §3 for the exact split: 75 of the 132 rows
reach the empty lookup itself, 57 never reach it at all because their
`id` doesn't match the `{lesson}-savvas-q{N}` pattern the matcher
requires). The 22 pairs are not special cases of a matching failure (no
id typo, no prompt-normalization miss, no wrong key) — they simply
inherit the same lesson-wide gap every other 5-4 row has: in the current
snapshot, lesson 5-4's Savvas TE item-analysis table is not transcribed,
and `questionbank/calibration/sources/` (the folder of TE screenshot
source images) contains **zero** files for lesson 5-4 (it holds only nine
`3-5_savvas_*.png` files). The registry's `dok` values for these 44 rows
are real, human/LLM-authored claims — each carries a `dok_rationale`
string like `"Savvas-declared DOK-2 item..."` — but those claims are not
verifiable against any on-disk textbook source, because no such source
is present on disk for lesson 5-4. That is precisely the distinction
`match_quality` is designed to expose, and it is working as designed
here.

## 2. How `match_quality` is computed (code citations)

All line numbers refer to `inventory/dok-workflow/gen_dok_wave_plan.py`.

**Source read** (`load_calibration`, lines 214–223): every `*.json` file
in `questionbank/calibration/` is loaded, keyed by lesson (filename minus
`.json`). This is the *only* place calibration data enters the pipeline.

**TE-bucket map build** (`build_item_to_dok`, lines 236–273): for each
lesson's calibration entry, it reads `cal_entry['item_analysis']`
(defaulting to `{}` if absent — line 252: `ia = (cal_entry or {}).get('item_analysis') or {}`),
iterates every `example_N` key, and inside each looks for keys matching
`^dok(\d+)$` (line 258), collecting the Savvas item numbers listed under
each bucket into `mapping[num] = dok_bucket` (first occurrence wins;
line 263–267). The result, `item_to_dok[lesson]`, is a plain
`{savvas_item_number: dok_bucket}` dict. **If a lesson's `item_analysis`
is `{}` or missing, `item_to_dok[lesson]` is `{}` — every lookup against
it returns `None`, unconditionally, for every item number.**

**Per-row matching** (`compute_te_match`, lines 293–316) — the function
that actually assigns `match_quality`. Critically, this function checks
the **id shape first** and only ever reaches the calibration lookup for
rows that pass that check — so "none" is produced by **two distinct
branches**, and for lesson 5-4 both are populated (see the branch-split
table below):
- Line 297: `exact_prefix = f'{lesson}-savvas-q'`.
- Lines 299–301: if the row's `id` starts with that prefix **and** the
  remainder starts with digits (`re.match(r'^(\d+)(.*)$', rest)`), it is
  split into a numeric item number and an optional suffix, and execution
  falls through to the lookup below. **If either check fails — no
  prefix match, or a prefix match whose remainder isn't
  digit-led — execution skips the lookup entirely** and falls to lines
  312–316 (the no-prefix branch, described below).
- Line 305 (**only reached by prefix+digit rows**): `te =
  item_to_dok.get(lesson, {}).get(item_number)` — the **only** lookup
  against calibration data in the whole function.
- Lines 306–307: **if `te is None`, return `match_quality = 'none'`.**
  For lesson 5-4, `item_to_dok['5-4']` is `{}` (built from an empty
  `item_analysis`), so every prefix+digit row's lookup returns `None`
  here without exception.
- Lines 308–309: if `te` is found and there's no suffix (bare
  `{lesson}-savvas-q{N}`), `match_quality = 'exact'` (224 rows overall).
- Line 310: if `te` is found and there's a suffix (e.g.
  `-partc-design`), `match_quality = 'derived'` (4 rows overall).
- Lines 312–316 (**the no-prefix branch — reached by rows that never
  pass the line 299–301 check, so item_to_dok is never consulted for
  them at all**): if the `id` doesn't match the `{lesson}-savvas-q{N}`
  shape, `match_quality` also becomes `'none'`, but for a completely
  different reason than the lookup-miss above — the row was never
  looked up in the first place.

**Verified branch split for lesson 5-4** (recomputed by
`audit_match_quality.py`, `branch_population_by_lesson` in
`provenance_audit_data.json`): of the 132 lesson-5-4 registry rows, **75
are prefix+digit rows** (bare `5-4-savvas-q{N}` or
`5-4-savvas-q{N}<suffix>` ids — these reach line 305's lookup and get
`'none'` because `item_to_dok['5-4']` is empty) and **57 are non-prefix
rows** (ids like `5-4-ex-1`, `5-4-tryit-3`,
`5-4-savvas-model-discuss-lesson-5-4-launch` — these never reach line
305 at all; they fall to the lines 312–316 branch regardless of what
`item_to_dok['5-4']` contains). 75 + 57 = 132, matching the per-lesson
table in §3. **All 44 rows in the 22 conflict pairs are in the
prefix+digit population** — every one of their ids is a bare
`5-4-savvas-q{N}` string (confirmed by assertion in
`audit_match_quality.py`) — so for these specific 44 rows the mechanism
*is* uniformly the line-305 empty-lookup branch; the two-branch
structure only matters when describing the other 57 non-conflict rows
in lesson 5-4, or when generalizing this explanation to other lessons.

**What is matched against**: the *lesson's own* `item_analysis` inside
`questionbank/calibration/{lesson}.json` — nothing else. Calibration's
`dok2_anchors` / `dok3_anchors` fields (used only by `compute_dok_status`,
lines 279–287, to decide the separate `dok_status` value `'calibrated'`)
play **no role** in `match_quality`. This is why 3-5 is `dok_status:
'calibrated'` (its `dok2_anchors`/`dok3_anchors` are non-empty — the only
lesson where that's true) yet **also** has `match_quality: 'none'` for
all 42 of its rows: 3-5's calibration file has no `item_analysis` key at
all. `dok_status` and `match_quality` are two independent signals reading
two different fields of the same file, and only `match_quality` is a
textbook cross-check.

**Matching key**: Savvas item *number*, parsed out of the registry row's
`id` string, matched against the lesson's `item_analysis` bucket
listings. It is not a prompt-text match, not a hash match, and not the
`item_uid`/registry-line identity key used elsewhere in the pipeline.

## 3. Per-lesson source-coverage table (all 900 rows)

Reproduced live by `audit_match_quality.py` from
`questionbank/calibration/*.json` + `questionbank/registry.jsonl`. Totals
reconcile exactly to 224 / 4 / 672 / 900.

| Lesson | exact | derived | none | total | `item_analysis` state in `questionbank/calibration/{lesson}.json` |
|---|---:|---:|---:|---:|---|
| 3-5 | 0 | 0 | 42 | 42 | **missing key** (file has no `item_analysis` field at all) |
| 4-3 | 30 | 4 | 40 | 74 | populated (6 examples, 30 item numbers) |
| 4-4 | 0 | 0 | 91 | 91 | **present but empty (`{}`)** |
| 4-5 | 26 | 0 | 55 | 81 | populated (5 examples, 26 item numbers) |
| 5-1 | 65 | 0 | 67 | 132 | populated (6 examples, 33 item numbers) |
| **5-4** | **0** | **0** | **132** | **132** | **present but empty (`{}`)** |
| 5-5 | 49 | 0 | 47 | 96 | populated (6 examples, 25 item numbers) |
| 6-3 | 37 | 0 | 63 | 100 | populated (6 examples, 37 item numbers) |
| 6-4 | 17 | 0 | 52 | 69 | populated (5 examples, 17 item numbers) |
| 6-5 | 0 | 0 | 83 | 83 | **present but empty (`{}`)** |
| **Total** | **224** | **4** | **672** | **900** | |

Four lessons (3-5, 4-4, 5-4, 6-5) have zero TE cross-check coverage —
every one of their rows is `match_quality: 'none'`, regardless of
whether the individual item is a duplicate, a conflict, or a perfectly
ordinary single-copy row. Lesson 5-4 is simply the lesson where the
85-collision double-ingest pattern (see §6) *also* happens to land, which
is why the 22 DOK-disagreeing pairs are visible there — but the "none"
match_quality itself has nothing to do with the collision; it is a
lesson-wide TE-transcription gap that would be identical even if 5-4 had
no duplicate rows at all.

`questionbank/calibration/sources/` — the folder of captured Savvas TE
screenshot images that this `item_analysis` data is transcribed from —
contains exactly 9 files, and all 9 are `3-5_savvas_*.png`. There is no
source image for 4-4, 5-4, or 6-5 either, consistent with those three
lessons' `item_analysis` being empty in the current snapshot.

## 4. The 22-pair evidence table (44 rows)

Every row below has `dok_status: "unreviewed"`, `te_bucket: null`,
`match_quality: "none"`, `reason_code: "NO_ITEM_ANALYSIS_DATA_FOR_LESSON"`
— confirmed for all 44 rows by `audit_match_quality.py`'s assertions.
`line_a`/`dok_a` = the lower-DOK copy; `line_b`/`dok_b` = the higher-DOK
copy (same `_a`/`_b` convention as
`inventory/dashboard/content_readiness.json`'s `dok_conflict_subset`,
against which this table was cross-checked and matches exactly, 22/22).

| legacy id | line_a | dok_a | uid_a | line_b | dok_b | uid_b |
|---|---:|---:|---|---:|---:|---|
| 5-4-savvas-q21 | 308 | 1 | iu_c470845cd9f5 | 279 | 2 | iu_bf2e53fb5aaa |
| 5-4-savvas-q22 | 309 | 1 | iu_2687f61c33c5 | 280 | 2 | iu_84131456696f |
| 5-4-savvas-q23 | 310 | 1 | iu_e067aeabdb5e | 281 | 2 | iu_5d11f886423f |
| 5-4-savvas-q24 | 311 | 1 | iu_da8e33db9d06 | 282 | 2 | iu_e106ef5ef48e |
| 5-4-savvas-q25 | 312 | 1 | iu_cd45fbec9dbc | 283 | 2 | iu_8e4e2787396a |
| 5-4-savvas-q26 | 313 | 1 | iu_323815e656c9 | 284 | 2 | iu_68d1a5b3e8f8 |
| 5-4-savvas-q27 | 314 | 1 | iu_26a15cb256cd | 285 | 2 | iu_9681eda37337 |
| 5-4-savvas-q28 | 315 | 1 | iu_d2eb395dfeee | 286 | 2 | iu_18cac1a8167a |
| 5-4-savvas-q29 | 316 | 1 | iu_6eb3a7c167c0 | 287 | 2 | iu_e7638fcec56e |
| 5-4-savvas-q30 | 317 | 1 | iu_3646823c6297 | 288 | 2 | iu_32a6c3b34ca1 |
| 5-4-savvas-q31 | 318 | 1 | iu_d8950c94a8bc | 289 | 2 | iu_beec9e3bdf89 |
| 5-4-savvas-q32 | 319 | 1 | iu_c1771afa2a7f | 290 | 2 | iu_74cca3783f59 |
| 5-4-savvas-q33 | 320 | 1 | iu_c6ab822e227b | 291 | 2 | iu_3adc6df8b95d |
| 5-4-savvas-q34 | 321 | 1 | iu_748071c541b9 | 292 | 2 | iu_a96e5311a459 |
| 5-4-savvas-q35 | 322 | 1 | iu_22bcc429d37c | 293 | 2 | iu_3b2700252892 |
| 5-4-savvas-q36 | 323 | 1 | iu_3c4458af5f01 | 294 | 2 | iu_5663d63244d2 |
| 5-4-savvas-q37 | 324 | 1 | iu_994890f62b0f | 295 | 2 | iu_c8710e0538db |
| 5-4-savvas-q38 | 325 | 1 | iu_b04e59b85637 | 296 | 2 | iu_80622035e09c |
| 5-4-savvas-q39 | 326 | 1 | iu_6826655b6fe7 | 297 | 2 | iu_6afe9c1960b0 |
| 5-4-savvas-q41 | 299 | 2 | iu_77d25e1e6131 | 328 | 3 | iu_3c70a19c8d36 |
| 5-4-savvas-q44 | 331 | 1 | iu_097a1fc43439 | 302 | 2 | iu_25b106c19a20 |
| 5-4-savvas-q45 | 332 | 1 | iu_b69ba77e28bf | 303 | 2 | iu_57481c4ff850 |

21 pairs are dok1-vs-dok2; exactly 1 (`5-4-savvas-q41`, lines 299/328) is
dok2-vs-dok3. Full per-row detail (source string, `dok_rationale`,
`prompt`, both stored and recomputed `prompt_sha1`) is in
`provenance_audit_data.json`'s `rows` array (44 entries).

## 5. Registry-DOK-presence vs. source-confirmation — the distinction RC is asking about

**(a) Does the registry carry a DOK claim for these 44 rows?** Yes,
unambiguously. Every one of the 44 rows has a non-null `dok` field (1, 2,
or 3) and a populated `dok_rationale` string, e.g. line 279:
`"Savvas-declared DOK-2 item. Routine multi-step procedure."` and line
308 (same legacy id, different registry row): `"Savvas-declared DOK-1
item. Single-step recall/recognition."` Both rationale strings *assert*
Savvas provenance in their own text. Neither row's `dok_status` is
`'verified'` (no row in the entire 900-row registry has both
`reviewed_by` and `reviewed_at` set — `EXPECTED_DOK_STATUS_TOTALS`
confirms 0 `verified` rows plan-wide) or `'known_auto'` (the rationale
text doesn't contain the literal string `'Auto-assigned DOK'`, the
marker `compute_dok_status` checks for at line 283). Since lesson 5-4
also isn't in `calibrated_lessons` (no `dok2_anchors`/`dok3_anchors`),
every 5-4 row's `dok_status`, including these 44, computes to
`'unreviewed'` — the lowest-confidence status the pipeline emits.

**(b) Is that DOK label confirmed against an on-disk textbook source?**
No — for any of the 132 lesson-5-4 rows, not just these 44. Confirmation
would require lesson 5-4's item number to appear in
`questionbank/calibration/5-4.json`'s `item_analysis`, and that field is
`{}`. There is nothing to compare the registry's claimed `dok` value
against, because no TE item-analysis transcription and no TE source
image exist on disk for lesson 5-4 (unlike 3-5's 9 source PNGs, or 4-3 /
4-5 / 5-1 / 5-5 / 6-3 / 6-4's populated `item_analysis` tables).

So: **the registry does carry a DOK label from ingest** (part a) — RC's
"expected to contain textbook DOK" is correct in the sense that these
rows already claim Savvas provenance in their own rationale text — but
**that label is not verifiable against a captured textbook source in the
current snapshot** (part b), because lesson 5-4's TE material is not
present in calibration data on disk. `match_quality: "none"` reports
exactly (b), correctly, and says nothing about whether (a) is
trustworthy.

## 6. Double-ingest analysis (snapshot language only)

`registry.jsonl` carries no ingest-batch id and no fine-grained
timestamp. All 44 rows in the 22 pairs share the identical `created_at:
"2026-04-20"` (date-only precision) — this field cannot distinguish
which copy was authored first. The only ordering signal available is
each row's **position in the file** (`registry_line` / append order),
which is evidence of file layout, not proof of chronological ingest
order; no field in the data proves that the lower line number was
written before the higher one, only that it currently sits earlier in
the file.

With that caveat, here is what the snapshot *does* show, verified across
all 22 pairs by `audit_match_quality.py`:

- In every one of the 22 pairs, the **earlier-line copy** (registry
  lines 279–303) has: no `role` field, no `standards` field, no
  `prereq_ids`/`rehearses`/`echoes`, no `teacher_answer` field, a bare
  LaTeX-only `prompt` (e.g. line 279: `"\sqrt[3]{x} + 8 = 13"`), and a
  templated-looking `dok_rationale` ("Savvas-declared DOK-N item.
  <generic DOK-band description>."). Its `dok` is 2 for 21 of the 22
  pairs, and 2 for the 22nd (`q41`).
- In every one of the 22 pairs, the **later-line copy** (registry lines
  308–332) has: a `role` field (e.g. `"optional-stretch"`,
  `"dok3-driver"`), a `standards` field (e.g. `["A-REI.A.2"]`), populated
  `prereq_ids`/`rehearses`/`echoes`/`skill_tokens` arrays, a fuller
  `notes` field (often an answer-key transcription), and a fuller, more
  instructional `prompt` (e.g. line 308:
  `"Solve each radical equation. (\sqrt[3]{x}+8=13)"`). A
  `teacher_answer` field is additionally present on 8 of the 22
  later-line copies (including `q21` line 308) and absent on the other
  14 (e.g. `q23` line 310); it appears on none of the 22 earlier-line
  copies. Its `dok` is 1 for 21 of the 22 pairs, and 3 for `q41`.
- `inventory/review-queue/collision_review_queue.json` independently
  captured this same pair (e.g. `5-4-savvas-q21`, `capture_a` = line 279,
  `capture_b` = line 308) with a similarity ratio of 0.4776, tagged
  `drift_tags: ["other_textual"]`, and a `medium`-confidence
  recommendation to keep the longer/more-complete capture
  (`canonical_keep: "iu_c470845cd9f5"`, i.e. the later-line, richer-schema
  copy) — but explicitly as a **recommendation**, with
  `"both_item_uids_retained": true` and no merge applied.

This is a structurally consistent split (leaner-schema/higher-dok copy
earlier in the file vs. richer-schema/lower-dok copy later in the file,
with `q41` as the sole DOK-direction outlier), consistent with two
distinct ingestion passes over the same 22+ Savvas Practice items landing
at two different points in the file — but the data does not contain a
field proving *when* each pass ran or *which* pass is authoritative. Read
this as "two snapshots currently coexist and disagree," not "the second
batch overwrote the first" — no field in the registry asserts an
overwrite ever happened; both rows are live, both are retained, and
`inventory/dedup/DUPLICATE_ID_REMEDIATION.md` explicitly classifies all
85 groups (these 22 included) as `merge-candidate` — a human-review
recommendation; in the current snapshot no merge is applied and both
copies of every pair remain live registry rows (all 44 lines present).

## 7. What would resolve each pair — source verification spec

`match_quality: "none"` will only become `"exact"` or `"derived"` for
lesson 5-4 once `questionbank/calibration/5-4.json`'s `item_analysis`
field is populated with real Savvas TE item-analysis data, following the
same shape already used for 4-3/4-5/5-1/5-5/6-3/6-4 (an `example_N` ->
`{"dok1": [...], "dok2": [...], "dok3": [...]}` mapping of item numbers
to DOK buckets, transcribed from the Savvas Algebra 2 Teacher's Edition
item-analysis page for Lesson 5-4, "Solving Radical Equations").

Concretely, for each of the 22 pairs, resolution requires consulting the
Savvas Algebra 2 Teacher's Edition item-analysis table for **Lesson 5-4,
Practice #N** (N = 21–39, 41, 44, 45 — the 22 item numbers in the table
above; the registry's `source` string for every one of the 44 rows reads
`"Savvas Practice #N (lesson 5-4)"` with `page: null` — no page number is
recorded on either copy, so the TE page itself, not just the item number,
still needs to be located):

1. Look up Savvas Practice #N in the Lesson 5-4 TE item-analysis table
   and record its declared DOK bucket (this is the missing on-disk
   source `match_quality` needs — currently absent for all of 5-4).
2. Compare that TE-declared bucket against the two registry copies'
   claimed `dok` values (dok_a vs dok_b in §4) to determine which copy's
   `dok` — if either — the textbook actually supports.
3. Resolve the `merge-candidate` disposition per
   `inventory/dedup/DUPLICATE_ID_REMEDIATION.md`'s existing human-review
   process (keep one copy, retire the other, or keep both if the TE
   analysis shows both prompts are genuinely distinct sub-items) — this
   step is about *which registry row* to keep, and is independent of but
   informed by step 2.
4. Once `item_analysis` for 5-4 is populated and
   `gen_dok_wave_plan.py` is re-run, these rows will surface as `'exact'`
   (bare `5-4-savvas-q{N}` ids) with a concrete `te_bucket`, and any
   remaining disagreement between the TE bucket and either copy's `dok`
   will register as an `exact_disagreement` — the analogous mechanism
   already flags **`derived`** disagreements today, specifically for
   three `4-3` ids (`4-3-savvas-q35-partc-design`,
   `4-3-savvas-q36-partA-build`, `4-3-savvas-q36-partC-evaluate-fairness`
   — see `EXPECTED_DERIVED_DISAGREEMENT_IDS`, `gen_dok_wave_plan.py:181-185`;
   there are zero `4-5` ids in that set, `exact` disagreements are
   separately asserted at 0 plan-wide via `EXPECTED_EXACT_DISAGREEMENTS`).

Until step 1 happens for lesson 5-4, all 22 pairs (44 rows) remain, per
the project's stated rubric, **conflicting, provenance-missing textbook
labels — unresolved pending source verification.**
