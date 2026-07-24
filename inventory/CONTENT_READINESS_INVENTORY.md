# Content Readiness Inventory — Lesson_planning Questionbank

Purpose: a definitive, per-lesson inventory of what content-readiness material actually exists on disk for all 37 Algebra 2 lesson slots (Topics 1 through 6), covering Savvas SE/TE source availability, questionbank registry coverage, answer-key evidence, visual-asset resolution, DOK review status, calibration status, and known data-quality risks (duplicate ids, source-coordinate collisions, missing topic tags). Everything here is a snapshot of CURRENT on-disk state; where a pattern suggests a history or cause, that history/cause is explicitly marked UNKNOWN rather than asserted.

**generated_at:** 2026-07-24T04:00:08.721581+00:00

**Computed from disk, read-only, snapshot-only. No registry or source file was modified.** Every number in this report is computed directly from questionbank/registry.jsonl, questionbank/calibration/*.json, questionbank/images/, questionbank/calibration/sources/, and repo-root/source SE-TE files at generation time — nothing here is hand-entered or hardcoded.

## 1. Baseline Reconciliation

Every metric below was independently computed from disk and checked against the pre-investigated ground truth. All should read CONFIRMED.

| metric | claimed | computed | verdict |
|---|---|---|---|
| total registry rows (required content only; see identity_reconciliation for raw) | 900 | 900 | CONFIRMED |
| unique ids | 834 | 834 | CONFIRMED |
| duplicate id strings (ids appearing more than once) | 85 | 85 | CONFIRMED |
| known-auto DOK rows | 421 | 421 | CONFIRMED |
| missing-answer rows across the nine | 339 | 339 | CONFIRMED |
| source-coordinate review-queue excess rows (global) | 176 | 176 | CONFIRMED |
| topics nonempty across the nine | 0 | 0 | CONFIRMED |
| calibrated lessons | 1 | 1 | CONFIRMED |
| verified rows | 39 | 39 | CONFIRMED |
| real screenshots | 114 | 114 | CONFIRMED |
| merged-alias rows (rc-merge-auth-5-4-2026-07-23) | 22 | 22 | CONFIRMED |

## 1b. Identity Reconciliation (raw / active / optional-catalog / merged-alias)

raw_registry_identities=919, active_canonical_items=878, optional_catalog_identities=19, merged_alias_identities=22 (reconciles: 878 + 19 + 22 == 919).

raw_registry_identities (919, all rows currently in registry.jsonl) splits three ways: merged_alias_identities (22, lesson 5-4, rc-merge-auth-5-4-2026-07-23) -- STUDENT-FACING selection (qb.py) resolves each of these DELIBERATELY to its survivor (via alias_of) and never selects or counts the alias row itself; optional_catalog_identities (19, lesson 4-1, nt14-ingest-4-1-2026-07-23) -- these rows exist in the registry but were deliberately excluded from every completion/readiness metric in this report (registry_rows, dok_status_totals, missing_answers, readiness gates, etc. above are all computed over required rows only and never see them; see lessons[] '4-1' entry's own 'optional_catalog' block), never auto-scheduled, never placed in pacing, and never described as required or ready-to-teach -- a later, separate course-policy decision governs student-facing appearance; and active_canonical_items (878) -- what a packet/quiz build actually draws from. Reconciliation is exact: raw_registry_identities == active_canonical_items + optional_catalog_identities + merged_alias_identities (919 == 878 + 19 + 22).

Every OTHER metric in this report (registry_rows, dok_status, readiness gates, etc.) is computed over REQUIRED rows only (900 total: 878 active_canonical_items + 22 merged-alias rows carried audit-style, exactly as before this ingestion) -- the 19 optional-catalog rows (lesson 4-1) are never blended into them. Per-lesson breakdown (lessons with a nonzero merged_alias_rows, plus 4-1's optional-catalog rows shown separately below):

| lesson | registry_rows | merged_alias_rows | active_registry_rows |
|---|---|---|---|
| 5-4 | 132 | 22 | 110 |

Optional-catalog rows (excluded from the table above -- not merged-alias, a distinct category): lesson 4-1 carries 19 rows (nt14-ingest-4-1-2026-07-23), reported on its own lesson block ('optional_catalog') and never in its top-level registry_rows/dok_status/etc fields above (which read 0 for 4-1, matching required-rows-only accounting).

## 2. The 37-Lesson-Slot Matrix

`src-collisions (excess)` and `dup-id (strings)` are single numbers standing in for a fuller triplet each — see `aggregate.source_coordinate_review` / `aggregate.duplicate_id_review` in the JSON, and Section 4 (Method Notes) below, for the full coordinates/excess_rows/participating_rows breakdown per metric.

| lesson | SE.pdf | TE.pdf | SE.tex | TE.tex | rows | ans(evid) | miss | visual | vis_absent | vis_broken | vis_miss(total) | topics | dok known-auto/unrev/calib/verif | item_analysis | src-collisions (excess) | dup-id (strings) | shots | readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-1 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 1-2 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 1-3 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 1-4 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 1-5 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 1-6 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 1-7 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 2-1 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 2-2 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 2-3 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 2-4 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 2-5 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 2-6 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 2-7 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 3-1 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 3-2 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 3-3 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 3-4 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 3-5 | ✓ | ✓ | – | – | 42 | 10 | 32 | 37 | 0 | 7 | 7 | 42 | 0/0/42/0 | none | 0 | 0 | 53 | partial |
| 3-6 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 4-1 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | real | 0 | 0 | 61 | optional-catalog |
| 4-2 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 4-3 | ✓ | ✓ | ✓ | ✓ | 74 | 57 | 17 | 8 | 8 | 0 | 8 | 0 | 40/34/0/0 | real | 7 | 0 | 0 | partial |
| 4-4 | ✓ | ✓ | ✓ | ✓ | 91 | 50 | 41 | 11 | 11 | 0 | 11 | 0 | 55/36/0/0 | empty | 16 | 0 | 0 | partial |
| 4-5 | ✓ | ✓ | ✓ | ✓ | 81 | 60 | 21 | 14 | 14 | 0 | 14 | 0 | 48/33/0/0 | real | 8 | 0 | 0 | partial |
| 4-6 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 5-1 | ✓ | ✓ | ✓ | ✓ | 132 | 68 | 64 | 21 | 21 | 0 | 21 | 0 | 50/82/0/0 | real | 41 | 32 | 0 | partial |
| 5-2 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 5-3 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 5-4 | ✓ | ✓ | ✓ | ✓ | 132 | 67 | 65 | 19 | 19 | 0 | 19 | 0 | 57/36/0/39 | real | 47 | 29 | 0 | partial |
| 5-5 | ✓ | ✓ | ✓ | ✓ | 96 | 48 | 48 | 13 | 13 | 0 | 13 | 0 | 47/49/0/0 | real | 33 | 24 | 0 | partial |
| 5-6 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 6-1 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 6-2 | – | – | – | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0/0 | none | 0 | 0 | 0 | absent |
| 6-3 | ✓ | ✓ | ✓ | ✓ | 100 | 64 | 36 | 17 | 17 | 0 | 17 | 0 | 42/58/0/0 | real | 7 | 0 | 0 | partial |
| 6-4 | ✓ | ✓ | ✓ | ✓ | 69 | 38 | 31 | 23 | 23 | 0 | 23 | 0 | 36/33/0/0 | real | 9 | 0 | 0 | partial |
| 6-5 | ✓ | ✓ | ✓ | ✓ | 83 | 67 | 16 | 11 | 11 | 0 | 11 | 0 | 46/37/0/0 | empty | 8 | 0 | 0 | partial |

### Readiness reasons (non-absent slots)

- **3-5** (partial): missing_answers=32>0; visuals_missing_asset=7>0; dok_status.verified=0<42
- **4-1** (optional-catalog): 19 registry row(s) ingested 2026-07-23 (nt14-ingest-4-1-2026-07-23) but carrying availability=='optional-catalog' -- lesson 4-1 was deliberately cut from the department's prior-year course sequence; that history is not reversed or reinterpreted by this ingestion, and no course-policy decision has been made to revive it as required/ready-to-teach content. This lesson is therefore held OUT of the ready/partial/blocked/absent distribution entirely (reported separately), never auto-scheduled, never placed in pacing, and never counted toward any completion percentage. See this lesson's 'optional_catalog' block for the 19-row breakdown.
- **4-3** (partial): missing_answers=17>0; topics_nonempty=0<74; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=8>0; dok_status.verified=0<74
- **4-4** (partial): missing_answers=41>0; topics_nonempty=0<91; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=11>0; dok_status.verified=0<91
- **4-5** (partial): missing_answers=21>0; topics_nonempty=0<81; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=14>0; dok_status.verified=0<81
- **5-1** (partial): missing_answers=64>0; topics_nonempty=0<132; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=21>0; dok_status.verified=0<132
- **5-4** (partial): missing_answers=65>0; topics_nonempty=0<132; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=19>0; dok_status.verified=39<132
- **5-5** (partial): missing_answers=48>0; topics_nonempty=0<96; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=13>0; dok_status.verified=0<96
- **6-3** (partial): missing_answers=36>0; topics_nonempty=0<100; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=17>0; dok_status.verified=0<100
- **6-4** (partial): missing_answers=31>0; topics_nonempty=0<69; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=23>0; dok_status.verified=0<69
- **6-5** (partial): missing_answers=16>0; topics_nonempty=0<83; lesson not calibrated (no real dok2/dok3 anchors); visuals_missing_asset=11>0; dok_status.verified=0<83

## 3. Readiness Legend & Rubric

- `✓` = present/true, `–` = absent/false, for boolean columns.
- **absent**: no se_pdf AND no te_pdf AND no se_tex AND no te_tex AND registry_rows==0 AND not has_calibration AND screenshots==0. Zero material of any kind.
- **blocked**: some material exists (has_calibration OR screenshots>0 OR se_tex OR te_tex OR se_pdf OR te_pdf) BUT registry_rows==0 — nothing usable to teach from yet.
- **ready**: registry_rows>0 AND missing_answers==0 AND topics_nonempty==registry_rows AND the lesson is calibrated (real dok2/dok3 anchors) AND visuals_missing_asset==0 AND dok_status.verified==registry_rows.
- **partial**: registry_rows>0 but at least one ready-gate fails.
- **optional-catalog** (NT14, nt14-ingest-4-1-2026-07-23): registry rows exist for this lesson but ALL of them carry availability=='optional-catalog' -- ingested, but by binding course policy never auto-scheduled, never placed in pacing, and never counted toward the ready/partial/blocked/absent distribution below (currently only lesson 4-1; see its own 'optional_catalog' block for the 19-row breakdown, and identity_reconciliation above for the registry-wide split).

Distribution across the 37 slots: ready=0, partial=10, blocked=0, absent=26, optional-catalog=1 (4-1; reported separately, excluded from the ready/partial/blocked/absent counts above).

## 4. Method Notes Per Column

- **lesson**: One of the 37 fixed slot ids (Topic-Lesson), in curriculum order.
- **se_pdf**: os.path.exists('a2_{lesson}_SE.pdf') at repo root.
- **te_pdf**: os.path.exists('a2_{lesson}_TE.pdf') at repo root.
- **se_tex**: os.path.exists('a2_{lesson}_SE.tex') at repo root OR os.path.exists('source/{lesson}_savvas_SE.tex').
- **te_tex**: os.path.exists('a2_{lesson}_TE.tex') at repo root OR os.path.exists('source/{lesson}_savvas_TE.tex').
- **registry_rows**: count of rows in questionbank/registry.jsonl where row['lesson'] == this lesson.
- **answers_with_evidence**: count of rows where (row['teacher_answer'] is present and str(...).strip() != '') OR ('Answer key (from source):' literal substring appears in row['notes']).
- **missing_answers**: registry_rows - answers_with_evidence.
- **visual_items**: count of rows where row['has_visual'] is truthy.
- **visuals_absent**: count of rows where has_visual is truthy AND row['image'] is empty/None — the reference itself is absent, so there is no path to even check on disk. Global=137, all in the nine.
- **visuals_broken_path**: count of rows where has_visual is truthy AND row['image'] is non-empty BUT the referenced file does not currently exist on disk relative to repo root — a broken path, not an absent reference. Global=7, all in lesson 3-5. See proposed_path_fixes for which of these are repairable.
- **visuals_missing_asset**: = visuals_absent + visuals_broken_path. Kept as a single total for continuity with earlier reports; use the two split columns above for the precise breakdown (they mean different things and call for different remediation).
- **topics_nonempty**: count of rows where (row['topics'] or []) is a non-empty list.
- **dok_status**: BASE bucket precedence (pure function of the registry row + its lesson's calibration status): (1) known_auto if 'Auto-assigned DOK' appears in row['dok_rationale']; (2) calibrated if the row's lesson has REAL calibration anchors (non-empty dok2_anchors or dok3_anchors in its calibration file — only 3-5 qualifies) AND the row was not auto-assigned; (3) unreviewed otherwise. 'calibrated' is a LESSON-LEVEL property gating a ROW-LEVEL count: a row only counts as calibrated if BOTH its lesson has real anchors AND its own DOK was not auto-assigned. 'verified' is NOT part of that base precedence — it is an OVERLAY applied afterward from the canonical DOK review-log projection: each row's item_uid (joined via inventory/dedup/item_uid_alias_map.json by 1-based registry line, mirroring inventory/dok-workflow/gen_dok_wave_plan.py's identical join, computed independently here rather than read from its output) is looked up in tools/dok-review/dok_review.py's tool_state_for(); a row is 'verified' iff that returns 'verified' (see dok_review.py's entry_is_verified for the exact fail-closed predicate), and a verified row LEAVES its base bucket for 'verified' instead. Registry 'reviewed_by'/'reviewed_at' fields are application-time metadata and are NEVER read here. See aggregate.dok_verification_note for the exact review-log/approvals-manifest paths and counts used this run. The four counts always sum to registry_rows.
- **item_analysis**: 'none' = calibration file absent OR the 'item_analysis' key is absent from it; 'empty' = key present but {} or []; 'real' = key present and non-empty.
- **source_coordinate_groups**: REVIEW QUEUE metric ('coordinates' in the triplet). Within the lesson, group rows by identical row['source']; count the groups with size > 1. Global=125.
- **source_coordinate_collisions**: REVIEW QUEUE metric ('excess_rows' in the triplet; field name kept from earlier reports). Within the lesson, group rows by identical row['source']; sum over each group of (group_size - 1). This does NOT mean the prompts are duplicate content — see the anomaly below. Global=176.
- **source_coordinate_participating_rows**: REVIEW QUEUE metric ('participating_rows' in the triplet). Within the lesson, group rows by identical row['source']; for each group with size > 1, sum the FULL group size (not just the excess). Global=301.
- **duplicate_id_strings**: Within the lesson, group rows by identical row['id']; count the distinct id strings that appear more than once. Global=85.
- **duplicate_id_excess_rows**: Within the lesson, group rows by identical row['id']; sum over each group of (group_size - 1). Replaces the field name duplicate_id_rows used in earlier reports. Global=85 (every duplicated id currently appears in exactly 2 rows, so strings==excess_rows numerically).
- **duplicate_id_participating_rows**: Within the lesson, group rows by identical row['id']; for each group with size > 1, sum the FULL group size. Global=170.
- **screenshots**: count of files in questionbank/images/ whose filename matches the regex ^{lesson}(?=[_.]) (i.e. a '3-5_...' or '3-5.png' style prefix).
- **has_calibration**: os.path.exists('questionbank/calibration/{lesson}.json').
- **readiness**: 'absent' = zero material of any kind (no se/te pdf/tex, no calibration, no screenshots, 0 registry rows). 'blocked' = some staged material exists but 0 registry rows (nothing to teach from yet). 'ready' = registry_rows>0 AND missing_answers==0 AND topics_nonempty==registry_rows AND lesson calibrated (real anchors) AND visuals_missing_asset==0 AND dok_status.verified==registry_rows. 'partial' = registry_rows>0 but any ready gate fails. 'optional-catalog' (NT14, nt14-ingest-4-1-2026-07-23) = the lesson's registry rows all carry availability=='optional-catalog' -- ingested, but by binding course policy never auto-scheduled, never placed in pacing, and never counted toward this or any other readiness/completion denominator; a fifth value, disjoint from ready/partial/blocked/absent, reported separately in aggregate.readiness_distribution.optional_catalog (currently only lesson 4-1; see its own 'optional_catalog' block for the breakdown).
- **readiness_reason**: Human-readable list of the specific gates that failed (or the no-material explanation for absent, or the staged-material-but-zero-registry-rows explanation for blocked — worded as a snapshot observation, not a causal claim).

## 5. Anomalies & Risks (snapshot observations; cause/history UNKNOWN unless stated)

### 4-1: NT14 named update -- 19 optional-catalog rows ingested 2026-07-23 (supersedes: "0 registry rows / ingestion status UNKNOWN")

NT14 (nt14-ingest-4-1-2026-07-23, 2026-07-23) ingested 19 Savvas practice rows for lesson 4-1 (4-1-savvas-q8..q26; DOK split 5x DOK-1 / 10x DOK-2 / 4x DOK-3), every one carrying top-level availability=='optional-catalog'. This supersedes the prior snapshot's finding that 0 registry rows existed and that ingestion status was unknown. 4-1's calibration file still has empty dok2_anchors/dok3_anchors (not a calibrated lesson) and no SE/TE pdf or tex exists on disk. The lesson's readiness now reads 'optional-catalog' -- distinct from ready/partial/blocked/absent -- and it is explicitly EXCLUDED from every required-content readiness/completion denominator in this report; see the lessons[] '4-1' entry's own 'optional_catalog' sub-block and aggregate.identity_reconciliation for the full accounting. Department-skip history is unchanged; a course-policy decision on reviving 4-1 for required, student-facing use remains open and is NOT made by this ingestion.

### Visual-asset gap splits into two distinct issues: absent references vs. repairable broken paths

137 registry rows have has_visual=true but an EMPTY image field — there is no asset reference to resolve at all. By lesson: {'4-3': 8, '4-4': 11, '4-5': 14, '5-1': 21, '5-4': 19, '5-5': 13, '6-3': 17, '6-4': 23, '6-5': 11}. Only 3-5 and 4-1 have any screenshots in questionbank/images/ at all, so every has_visual row in the other nine-lesson slots is unresolved by construction. Separately, 7 rows (all in lesson 3-5) have has_visual=true AND a non-empty image field, but the referenced file does not currently exist at that path. In summary: 137 references are genuinely ABSENT (empty image field, all in the nine); 7 are REPAIRABLE broken paths in 3-5 whose PNGs already exist under questionbank/calibration/sources/ — a path-fix, not missing content. See proposed_path_fixes for the corrected paths (analysis only; registry.jsonl was not modified).

### Duplicate-id strings concentrated in 5-1 / 5-4 / 5-5

85 duplicate-id strings involving 170 participating rows (85 excess rows) exist across the full registry, and all of them are within exactly three lessons: {'5-1': {'strings': 32, 'participating_rows': 64}, '5-4': {'strings': 29, 'participating_rows': 58}, '5-5': {'strings': 24, 'participating_rows': 48}}. No other lesson has any duplicate id, and every duplicated id currently appears in exactly 2 rows. This pattern is consistent with duplicated bulk-ingest appends having hit only those three lessons, but the actual CAUSE is UNKNOWN from the data alone — these files show only the current state, not how it arose.

### Topics absent on the nine (current state)

As of this snapshot, 0 of 858 registry rows across the nine currently carry a non-empty topics list, even though each of those lessons' calibration files has a populated topic_vocabulary list. Whether topics were ever copied from topic_vocabulary into per-row topics during ingest is UNKNOWN from these files; only the current absence is observable. (3-5 is the exception: all 42 of its rows currently have non-empty topics.)

### DOK review pipeline: current state is almost entirely unreviewed

421/900 rows currently have auto-assigned DOK (dok_rationale contains 'Auto-assigned DOK'); 39 rows currently verify under the canonical DOK review-log projection (tools/dok-review/dok_review.py's entry_is_verified, applied per row via tool_state_for() over the review log and rubric-approvals manifest actually used this run — see aggregate.dok_verification_note for the exact paths/counts); only 3-5 is currently a calibrated lesson (real dok2_anchors/dok3_anchors). Registry 'reviewed_by'/'reviewed_at' fields are application-time metadata and are never read for this derivation.

### Source-coordinate collisions are a REVIEW QUEUE, not confirmed duplicates

176 excess rows across 125 (lesson, source) coordinates / 301 participating rows currently share an identical (lesson, source) coordinate with at least one other row in the same lesson. This does NOT mean the prompts are duplicate content — it means multiple registry rows point at the same named Savvas source location (e.g. the same 'Model & Discuss' launch prompt got registered more than once, or several sub-parts of one source share one coordinate label) and need human disambiguation before they can be trusted as distinct items. See aggregate.source_coordinate_review for the full coordinates/excess_rows/participating_rows triplet, and each lesson's source_coordinate_groups / source_coordinate_collisions / source_coordinate_participating_rows fields for the per-lesson breakdown.

## 6. Secondary Aggregates

- total registry rows: 900
- total answers_with_evidence: 529
- total missing_answers (all 37 lessons): 371
- total missing_answers (the nine): 339
- total visual_items: 174
- total visuals_absent (all lessons): 137 (the nine only: 137)
- total visuals_broken_path (all lessons): 7 (the nine only: 0)
- total visuals_missing_asset (all lessons, incl. 3-5): 144
- total visuals_missing_asset (the nine only): 137
  - visuals_missing_asset (144 all-lessons / 137 the-nine) is visuals_absent + visuals_broken_path, kept for continuity with earlier reports. Split: 137 rows are visuals_absent (empty image field; all 137 of them are in the nine) and 7 rows are visuals_broken_path (non-empty image field pointing at a file that is not currently on disk; all 7 of them are in lesson 3-5, and all are repairable — see proposed_path_fixes).
- total topics_nonempty (all lessons): 42
- total topics_nonempty (the nine only): 0
- dok_status totals: known_auto=421, unreviewed=398, calibrated=42, verified=39 (sum=900)
- source-coordinate review queue (full triplet): coordinates=125, excess_rows=176, participating_rows=301 (176 excess rows across 125 coordinates / 301 participating rows)
- duplicate-id metric (full triplet): strings=85, excess_rows=85, participating_rows=170 (85 duplicate-id strings involving 170 rows)
- calibrated lessons: ['3-5']

## 7. Proposed Path Fixes (analysis only — registry.jsonl NOT modified)

Analysis only. Lists, for every visuals_broken_path row, whether a file with the same basename currently exists under questionbank/calibration/sources/ and what the corrected path would be. registry.jsonl was NOT modified by this script or by this analysis.

7 rows affected, all in lesson 3-5:

| id | lesson | current image path | repairable | proposed path |
|---|---|---|---|---|
| 3-5-tryit-3a | 3-5 | questionbank/images/3-5_savvas_example-3.png | yes | questionbank/calibration/sources/3-5_savvas_example-3.png |
| 3-5-tryit-3b | 3-5 | questionbank/images/3-5_savvas_example-3.png | yes | questionbank/calibration/sources/3-5_savvas_example-3.png |
| 3-5-tryit-4 | 3-5 | questionbank/images/3-5_savvas_example-4.png | yes | questionbank/calibration/sources/3-5_savvas_example-4.png |
| 3-5-tryit-5a | 3-5 | questionbank/images/3-5_savvas_example-5.png | yes | questionbank/calibration/sources/3-5_savvas_example-5.png |
| 3-5-tryit-5b | 3-5 | questionbank/images/3-5_savvas_example-5.png | yes | questionbank/calibration/sources/3-5_savvas_example-5.png |
| 3-5-tryit-6a | 3-5 | questionbank/images/3-5_savvas_example-6.png | yes | questionbank/calibration/sources/3-5_savvas_example-6.png |
| 3-5-tryit-6b | 3-5 | questionbank/images/3-5_savvas_example-6.png | yes | questionbank/calibration/sources/3-5_savvas_example-6.png |

## 8. UNKNOWN / Absent Evidence

The following 26 slots are `absent` (zero material found on disk for any of se_pdf/te_pdf/se_tex/te_tex/has_calibration/screenshots/registry_rows):

1-1, 1-2, 1-3, 1-4, 1-5, 1-6, 1-7, 2-1, 2-2, 2-3, 2-4, 2-5, 2-6, 2-7, 3-1, 3-2, 3-3, 3-4, 3-6, 4-2, 4-6, 5-2, 5-3, 5-6, 6-1, 6-2

> Every SE/TE/tex/screenshot/registry/calibration column resolved to a concrete boolean or count from files actually present or absent on disk at generation time — no column value itself is UNKNOWN. The 26 'absent' lesson slots are a definite finding (confirmed zero matching files of any kind), not an unknown. NT14 NAMED UPDATE (nt14-ingest-4-1-2026-07-23, 2026-07-23): whether 4-1 ingestion was attempted is no longer unknown — 19 rows were deliberately ingested as optional-catalog content (see the '4-1' anomaly above and this lesson's own 'optional_catalog' block); that is a known, current fact, not a snapshot inference. What remains unknown, and is called out explicitly in the anomalies above, is HISTORY and CAUSE unrelated to this ingestion: whether topics were ever propagated from topic_vocabulary, and what produced the 5-1/5-4/5-5 duplicate ids. These files only prove current state, not how that state came to be.
