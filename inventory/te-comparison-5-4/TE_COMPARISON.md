# TE-vs-Registry DOK Comparison — Lesson 5-4 (Solving Radical Equations)

> **PROPOSAL / EVIDENCE ONLY — NOT RECORDED as any decision; no registry mutation; awaiting RC confirmation through the rubric v0.2 review flow.**


Generated: 2026-07-22

## Sources

| Path | sha256 | Role |
|---|---|---|
| `questionbank/calibration/5-4.json` | `ad41a82f03d5a972b44626c9b572ee350bf8ed4e0600ed17e485698954953033` | TE Item Analysis transcription (item_analysis field). Treated as the verified TE transcription per task instructions. |
| `questionbank/registry.jsonl` | `b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8` | Registry rows. Lesson 5-4 has 132 total rows; the 61 savvas-q practice rows joined here to the TE table sit at 1-based lines 273-333. |
| `inventory/dedup/item_uid_alias_map.json` | `be4b507b7fb7aee904fead8515686d2583c2732e948aaf3ced134e63d97c7ff1` | legacy_id -> item_uid join table. Every row below is joined to its item_uid via registry_line through this map, never by legacy id alone. |
| `inventory/dok-workflow/dok_wave_plan.json` | `f1dbdd19dcbf35c7f40fc2ab9e4a4336990ae7185edf1a7de82b87fda8df7266` | Cross-check source for te_bucket/match_quality per registry row (lesson 5-4: 61 rows te_bucket-exact, 71 rows te_bucket-none). Used only to verify this comparison's own independent computation; zero mismatches found. |

## Conventions

- **copy_a**: the copy of a duplicated legacy id at the LOWER registry line
- **copy_b**: the copy of a duplicated legacy id at the HIGHER registry line
- **identity_key**: item_uid, joined by registry_line through inventory/dedup/item_uid_alias_map.json. Legacy id (e.g. '5-4-savvas-q41') is display-only and is NOT unique — 29 of the 32 transcribed item numbers each have two registry rows.

## Provenance cite (applies to every TE-sourced field in this document)

```
Savvas TE printed page 258, Item Analysis table, Example {example number — see each row} row (page footer "TOPIC 5 | 258 | LESSON 4"); captures questionbank/calibration/sources/5-4_savvas_te_p258_full_page.png (sha256 af34c4d9469a88b372d7d09b03b724b15c83abe18a83c5f03a820992a2ba3786) and questionbank/calibration/sources/5-4_savvas_te_p258_item_analysis_closeup.png (sha256 273db411184a07e8c92e8b72cdd527f7977bb507a13a43b70fdf6ba710d6ab46); edition caveat: exact TE edition/copyright page not independently re-confirmed in this intake (RC override 2026-07-22).
```

## Classification enum (pair-level, for the 22 conflict pairs)

- `te-agrees-with-copy-A`
- `te-agrees-with-copy-B`
- `te-agrees-with-both`
- `genuine-disagreement`

No recommendation language (no "should"/"recommend"/"suggest"/"likely correct") appears anywhere in this artifact. Facts and classifications only; no default resolution is implied.

## Full TE transcription — all 32 item numbers (Savvas TE p.258 Item Analysis table)

| Item # | TE DOK | TE Example |
|---|---|---|
| 15 | 2 | Example 3 |
| 16 | 2 | Example 2 |
| 17 | 2 | Example 2 |
| 18 | 2 | Example 1 |
| 19 | 3 | Example 4 |
| 20 | 2 | Example 5 |
| 21 | 1 | Example 1 |
| 22 | 1 | Example 1 |
| 23 | 1 | Example 1 |
| 24 | 1 | Example 1 |
| 25 | 1 | Example 2 |
| 26 | 1 | Example 2 |
| 27 | 1 | Example 2 |
| 28 | 1 | Example 2 |
| 29 | 1 | Example 3 |
| 30 | 1 | Example 3 |
| 31 | 1 | Example 3 |
| 32 | 1 | Example 3 |
| 33 | 1 | Example 4 |
| 34 | 1 | Example 4 |
| 35 | 1 | Example 4 |
| 36 | 1 | Example 5 |
| 37 | 1 | Example 5 |
| 38 | 1 | Example 5 |
| 39 | 1 | Example 6 |
| 40 | 2 | Example 2 |
| 41 | 3 | Example 4 |
| 42 | 2 | Example 6 |
| 43 | 2 | Example 2 |
| 44 | 1 | Example 1 |
| 45 | 1 | Example 4 |
| 46 | 2 | Example 2 |

Total transcribed item numbers: **32**

## 22 conflict pairs (registry Copy A DOK != registry Copy B DOK)

| Legacy ID | Item # | Copy A (line / DOK / role) | Copy B (line / DOK / role) | TE DOK | TE Example | Classification |
|---|---|---|---|---|---|---|
| 5-4-savvas-q21 | 21 | L279 / 2 / — | L308 / 1 / optional-stretch | 1 | Example 1 | `te-agrees-with-copy-B` |
| 5-4-savvas-q22 | 22 | L280 / 2 / — | L309 / 1 / explore-practice | 1 | Example 1 | `te-agrees-with-copy-B` |
| 5-4-savvas-q23 | 23 | L281 / 2 / — | L310 / 1 / explore-practice | 1 | Example 1 | `te-agrees-with-copy-B` |
| 5-4-savvas-q24 | 24 | L282 / 2 / — | L311 / 1 / explore-practice | 1 | Example 1 | `te-agrees-with-copy-B` |
| 5-4-savvas-q25 | 25 | L283 / 2 / — | L312 / 1 / explore-practice | 1 | Example 2 | `te-agrees-with-copy-B` |
| 5-4-savvas-q26 | 26 | L284 / 2 / — | L313 / 1 / explore-practice | 1 | Example 2 | `te-agrees-with-copy-B` |
| 5-4-savvas-q27 | 27 | L285 / 2 / — | L314 / 1 / explore-practice | 1 | Example 2 | `te-agrees-with-copy-B` |
| 5-4-savvas-q28 | 28 | L286 / 2 / — | L315 / 1 / explore-practice | 1 | Example 2 | `te-agrees-with-copy-B` |
| 5-4-savvas-q29 | 29 | L287 / 2 / — | L316 / 1 / explore-practice | 1 | Example 3 | `te-agrees-with-copy-B` |
| 5-4-savvas-q30 | 30 | L288 / 2 / — | L317 / 1 / explore-practice | 1 | Example 3 | `te-agrees-with-copy-B` |
| 5-4-savvas-q31 | 31 | L289 / 2 / — | L318 / 1 / explore-practice | 1 | Example 3 | `te-agrees-with-copy-B` |
| 5-4-savvas-q32 | 32 | L290 / 2 / — | L319 / 1 / explore-practice | 1 | Example 3 | `te-agrees-with-copy-B` |
| 5-4-savvas-q33 | 33 | L291 / 2 / — | L320 / 1 / explore-practice | 1 | Example 4 | `te-agrees-with-copy-B` |
| 5-4-savvas-q34 | 34 | L292 / 2 / — | L321 / 1 / explore-practice | 1 | Example 4 | `te-agrees-with-copy-B` |
| 5-4-savvas-q35 | 35 | L293 / 2 / — | L322 / 1 / explore-practice | 1 | Example 4 | `te-agrees-with-copy-B` |
| 5-4-savvas-q36 | 36 | L294 / 2 / — | L323 / 1 / explore-practice | 1 | Example 5 | `te-agrees-with-copy-B` |
| 5-4-savvas-q37 | 37 | L295 / 2 / — | L324 / 1 / explore-practice | 1 | Example 5 | `te-agrees-with-copy-B` |
| 5-4-savvas-q38 | 38 | L296 / 2 / — | L325 / 1 / explore-practice | 1 | Example 5 | `te-agrees-with-copy-B` |
| 5-4-savvas-q39 | 39 | L297 / 2 / — | L326 / 1 / explore-practice | 1 | Example 6 | `te-agrees-with-copy-B` |
| 5-4-savvas-q41 | 41 | L299 / 2 / — | L328 / 3 / dok3-driver | 3 | Example 4 | `te-agrees-with-copy-B` |
| 5-4-savvas-q44 | 44 | L302 / 2 / — | L331 / 1 / launch-model-2 | 1 | Example 1 | `te-agrees-with-copy-B` |
| 5-4-savvas-q45 | 45 | L303 / 2 / — | L332 / 1 / explore-practice | 1 | Example 4 | `te-agrees-with-copy-B` |

**Classification counts (22 pairs total):**

- `te-agrees-with-copy-A`: **0** — no pair falls in this class; reported explicitly as 0.
- `te-agrees-with-copy-B`: **22**
- `te-agrees-with-both`: **0** — no pair falls in this class; reported explicitly as 0.
- `genuine-disagreement`: **0** — no pair falls in this class; reported explicitly as 0.

Every item_uid above is joined to its registry row via `registry_line` through `inventory/dedup/item_uid_alias_map.json`; item_uid values are omitted from this table for readability and are listed in `te_comparison_5_4.json` and `individual_disagreements.md`.

## 7 agreeing pairs (registry Copy A DOK == registry Copy B DOK)

| Legacy ID | Item # | Copy A (line / DOK / role) | Copy B (line / DOK / role) | TE DOK | TE Example | TE matches registry DOK? |
|---|---|---|---|---|---|---|
| 5-4-savvas-q16 | 16 | L274 / 2 / — | L305 / 2 / explore-practice | 2 | Example 2 | True |
| 5-4-savvas-q17 | 17 | L275 / 2 / — | L306 / 2 / explore-practice | 2 | Example 2 | True |
| 5-4-savvas-q18 | 18 | L276 / 2 / — | L307 / 2 / explore-practice | 2 | Example 1 | True |
| 5-4-savvas-q40 | 40 | L298 / 2 / — | L327 / 2 / explore-practice | 2 | Example 2 | True |
| 5-4-savvas-q42 | 42 | L300 / 2 / — | L329 / 2 / explore-practice | 2 | Example 6 | True |
| 5-4-savvas-q43 | 43 | L301 / 2 / — | L330 / 2 / explore-practice | 2 | Example 2 | True |
| 5-4-savvas-q46 | 46 | L304 / 2 / — | L333 / 2 / optional-stretch | 2 | Example 2 | True |

## 3 singleton rows (item numbers with exactly one registry row: 15, 19, 20)

| Legacy ID | Item # | item_uid | Registry line | Registry DOK | Role | TE DOK | TE Example | Agreement |
|---|---|---|---|---|---|---|---|---|
| 5-4-savvas-q15 | 15 | `iu_426cc3017f2c` | 273 | 2 | explore-practice | 2 | Example Example 3 | True |
| 5-4-savvas-q19 | 19 | `iu_e2a361f675b8` | 277 | 3 | optional-stretch | 3 | Example Example 4 | True |
| 5-4-savvas-q20 | 20 | `iu_0910bde55379` | 278 | 2 | explore-practice | 2 | Example Example 5 | True |

## Summary

- Total transcribed item numbers: **32**
- Total registry rows joined: **61**
- Singleton rows: **3**
- Agreeing pairs: **7** (14 rows)
- Conflict pairs: **22** (44 rows)
- Rows where registry DOK == TE DOK: **39**
- Rows where registry DOK != TE DOK: **22**
- Arithmetic check against task expectation (39 agree / 22 disagree, cross-checked against the wave plan's exact_disagreement count of 22): computed agree = 39, computed disagree = 22, matches expected = **True**. Wave-plan cross-check errors: none.
- Decomposition of the 39 exact rows: both copies of the 7 agreeing pairs (14 rows) + copy-B of conflict pairs matching TE (22 rows) + copy-A of conflict pairs matching TE (0 rows) + singletons matching TE (3 rows) = 39.

> **PROPOSAL / EVIDENCE ONLY — NOT RECORDED as any decision; no registry mutation; awaiting RC confirmation through the rubric v0.2 review flow.**

