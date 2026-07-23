# Lesson 4-1 Content-Readiness Diagnosis

Generated 2026-07-19 as part of WS1 (topic-4-1 investigation). Read-only diagnosis — no source files were
modified to produce this document. All facts below were independently spot-verified against disk in this
session; see the "Verification" note at the end of each section for what was re-checked.

## Summary

Lesson 4-1 (Inverse Variation and the Reciprocal Function) is **stranded mid-pipeline**: its Savvas source
material was staged (61 screenshots) and its calibration was fully authored (a real 5-example item-analysis
mapping to Savvas practice numbers), but the transcribe-and-append step that turns staged screenshots into
registry rows was **never completed and retained** — all 15 generated skeleton stubs are still literal
un-edited `"TODO: transcribe..."` placeholders, and `questionbank/registry.jsonl` currently holds **0 rows**
for lesson `4-1`. The documented proximate cause is that the department **skipped L41 on 2026-05-13**
(`CONTINUATION_PROMPT.md:32`), which halted the lesson's build before ingestion was finished and triggered a
cull of 4-1-tagged assets from the registry/Supabase/tagging layers. No `a2_4-1_SE`/`a2_4-1_TE` source (PDF
or LaTeX) exists anywhere in the repo, unlike nine sibling lessons that each have both. Whether reviving 4-1
is worthwhile given the department's skip decision is a **teacher judgment**, not resolved here.

## What exists on disk

### Calibration — `questionbank/calibration/4-1.json` (47 lines)

Fully authored, not a placeholder. Structure:

- `lesson_vocabulary` (4 terms) and `topic_vocabulary_unit` (10 terms) — standard Topic 4 unit vocabulary.
- `item_analysis` (lines 24-30) — maps each of Savvas's 5 worked Examples to the practice-item numbers that
  anchor to it, split by DOK:
  - `example_1`: dok1 = [9, 14, 15], dok2 = [10]
  - `example_2`: dok1 = [13, 16], dok2 = [24]
  - `example_3`: dok2 = [12, 17, 23], **dok3 = [20, 22, 25, 26]**
  - `example_4`: dok2 = [11, 18, 21]
  - `example_5`: dok2 = [8, 19]
- `notes` (line 31) names practice items **#20, #22, #25, #26** (all anchored to Example 3 — reciprocal
  function translations) as the Savvas-declared DOK-3 anchors, and states the DOK-3 push is "subservient to
  Savvas fidelity" — i.e., per the project's Single-DOK3 spine rule, whichever item becomes this lesson's
  DOK-3 driver must be one of those four.
- `dok2_anchors` (line 32) and `dok3_anchors` (line 33) — **both empty arrays**. These are meant to be
  backfilled with the actual anchor item text/ids once ingested; that backfill never happened.
- `topic_vocabulary` (lines 34-46) — 11 tags for use on ingested items' `topics` field.

**Verification:** Read in full this session; matches the manager's brief exactly, including the empty
anchor arrays and the #20/22/25/26 naming.

### Screenshots — `questionbank/images/4-1_*` (61 files)

Independently counted (`ls questionbank/images/ | grep -c '^4-1_'` → 61) and enumerated. Grouped by role:

| Role | Count | Files |
|---|---|---|
| Concept | 2 | `4-1_savvas_concept_inverse_variation.png`, `4-1_savvas_concept_summary.png` |
| Launch | 1 | `4-1_launch_model_discuss.png` |
| Example / Try-It (question only) | 6 | `4-1_savvas_example1_question.png`, `4-1_savvas_example2_tryit2_question.png`, `4-1_savvas_example3_tryit3_question.png`, `4-1_savvas_example4_tryit4_question.png`, `4-1_savvas_example5_tryit5_question.png`, `4-1_savvas_tryit1_question.png` |
| Practice items q8-q26 | 37 | `4-1_savvas_q{8-26}_question.png` for all 19 numbers 8-26; `_answer.png` for all except q14/q15 (which share one combined `4-1_savvas_q14q15_answers.png`) and q9-q13/q16-q26 individually — net: 19 `_question.png` + 17 individual `_answer.png` + 1 shared `q14q15_answers.png` = 37 |
| Teacher Edition (TE) addenda | 15 | `4-1_te_ex1_purposeful_questions.png`, `4-1_te_ex2_common_error.png`, `4-1_te_ex2_connect_tryit2_answers.png`, `4-1_te_ex2_habits_of_mind.png`, `4-1_te_ex3_elicit_learn_together.png`, `4-1_te_ex3_ell_addendum.png`, `4-1_te_ex3_purposeful_tryit3_answer.png`, `4-1_te_ex4_purposeful_questions.png`, `4-1_te_ex4_rti_support.png`, `4-1_te_ex4_tryit4_answer_elicit.png`, `4-1_te_ex5_connect_tryit5_answer.png`, `4-1_te_ex5_elicit_evidence.png`, `4-1_te_ex5_habits_of_mind.png`, `4-1_te_ex5_rti_extend.png`, `4-1_te_tryit1_answers_elicit.png` |

Total: 2 + 1 + 6 + 37 + 15 = 61. Full enumeration is in `inventory-4-1-assets.json`.

**Critically:** practice items **q20, q22, q25, q26** — the exact four items calibration names as DOK-3
anchors — DO have both `_question.png` and `_answer.png` screenshots on disk (confirmed:
`4-1_savvas_q20_question.png`, `4-1_savvas_q20_answer.png`, `4-1_savvas_q22_question.png`,
`4-1_savvas_q22_answer.png`, `4-1_savvas_q25_question.png`, `4-1_savvas_q25_answer.png`,
`4-1_savvas_q26_question.png`, `4-1_savvas_q26_answer.png`). The screenshots exist; see below for why they
were never stubbed.

**Verification:** Full sorted directory listing re-generated and cross-checked this session; count and
grouping match the manager's brief.

### Skeleton stubs — `skeletons/4-1_practice_skeletons.json` (15 entries, 389 lines)

Read in full. Contains exactly 15 entries, ids: `4-1-savvas-q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`,
`q15`, `q16`, `q17`, `q18`, `q19`, `q21`, `q23`, `q24` — i.e. q8 through q19, plus q21/q23/q24. Every entry
has:
- `"prompt": "TODO: transcribe Savvas Practice #N prompt from screenshot."` (literal, un-edited)
- `"answers": []`
- `"correct": null`
- `"notes": "TODO: add answer key from TE. ..."`

All 15 are confirmed un-transcribed stubs — not a single one has been filled in.

**Missing from the skeleton entirely: q20, q22, q25, q26** — the four DOK-3 anchor items. They were never
even stubbed by `generate_practice_skeletons.py`, despite their screenshots existing on disk. This means the
lesson's DOK-3 spine driver has no scaffold at all — the gap is one step earlier than "un-transcribed," it's
"not yet generated."

**Verification:** Read in full this session; entry count, id list, and TODO/empty/null pattern all match
the manager's brief exactly. The q20/22/25/26 omission was independently confirmed against the image
enumeration above.

## What is missing

- **0 registry rows for lesson 4-1.** Independently verified: `grep -c '"lesson": *"4-1"' questionbank/registry.jsonl` → `0`. Registry totals (unchanged, see Verification section of `RECOVERY_PLAN.md`/final report): 900 lines, 920200 bytes, sha256
  `b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8`.
- **No `a2_4-1_SE.*` or `a2_4-1_TE.*` anywhere** (pdf or tex): `find . -iname 'a2_4-1_*'` returned nothing.
  By contrast, `CONTINUATION_PROMPT.md:97` (`git ls-files 'a2_*_SE.tex' 'a2_*_TE.tex'`) documents that
  4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5 each have committed SE+TE tex/pdf, and 3-5 has SE+TE pdf. 4-1's
  total absence of source material (not even a PDF export) is conspicuous against that pattern.
  `CONTINUATION_PROMPT.md:100` separately lists 5-2/5-3/6-1/6-2 as "likely department-skipped same as
  4-1/4-2" for missing SE/TE — grouping 4-1 with other skipped/never-built lessons.
- **No `tagging/4-1_*.jsonl`.** `find ./tagging -iname '4-1*'` returned nothing. (See "Why it's stranded"
  below — this file is documented as having existed and been deleted, not merely never created.)
- **L41 lesson tex lives only in `legacy/tex/`**, not `tex/`. Confirmed 46 files at
  `legacy/tex/L41_P{1,2,3}_{do_now,slides,student,teacher}.{tex,pdf,aux,log,...}`: P1 = 14, P2 = 18, P3 = 14
  (14 + 18 + 14 = 46). P2 carries 4 extra build sidecars that P1/P3 don't (`L41_P2_student.aux`,
  `L41_P2_student.log`, `L41_P2_teacher.aux`, `L41_P2_teacher.log`), which is why the periods aren't a
  symmetric 3 x 14 = 42. Of the 46, only 24 are substantive (12 `.tex` source + 12 `.pdf` output, one pair
  each for do_now/slides/student/teacher x 3 periods); the remaining 22 are LaTeX build artifacts
  (`.aux/.log/.nav/.out/.snm/.toc`). `tex/` has zero `L41_*` files.

## Why it's stranded

**The intended pipeline** (per `questionbank/INGEST_PROMPT.md` and `generate_practice_skeletons.py`'s role
in the toolchain) is: stage screenshots → author calibration (`item_analysis`) →
`generate_practice_skeletons.py` emits per-item TODO stubs → a person/agent transcribes each stub's
prompt/answers/correct from its screenshot and calibrates DOK against the calibration's anchors →
`qb_append.py` validates and appends the finished entry to `registry.jsonl` one at a time (append-order
sensitive; `INGEST_PROMPT.md:59-66` explicitly forbids parallelizing this step).

**For 4-1, the pipeline stopped at the skeleton-stub stage.** Calibration was authored (real content, not a
placeholder). 15 stubs were generated. But zero of them were ever transcribed, and the 4 DOK-3 anchor items
(q20/22/25/26) were never even stubbed. No completed, retained ingestion into `registry.jsonl` exists today.

**Proximate cause — documented department skip, 2026-05-13:**
- `CONTINUATION_PROMPT.md:32`: "As of 2026-05-13 the department skipped L41 (Klimsara confirmed); cadence
  jumps directly to L43." Same line: "L41_P1/P2/P3 tex moved to `legacy/tex/`... L41 and `APStats_6-4_P1`
  lesson rows deleted from Supabase, with L41 schedule rows having `lesson_id` nulled to preserve calendar
  dates."
- `CONTINUATION_PROMPT.md:192` (the "Completed 2026-05-13" log): "✅ **L41 retired**: L41_P1/P2/P3 tex →
  `legacy/tex/`; APStats_6-4 yaml + 6 registry items removed; `tagging/4-1_*.jsonl` deleted; L41 +
  APStats_6-4_P1 Supabase lesson rows deleted; schedule lesson_id nulled."

**Important epistemic note — calibrated confidence, not certainty:** The on-disk files alone cannot fully
distinguish "4-1 was never ingested" from "4-1 was briefly/partially ingested (at least at the
tagging/Supabase layer) and then culled on skip." Two things pull in different directions:

1. `CONTINUATION_PROMPT.md:112` (general authoring-workflow notes, step 3: "Cull DAG/registry") states, as a
   worked example: *"when 4-1 was skipped, all `4-1-*` items were removed from registry + Supabase +
   tagging."* Read literally, this says 4-1 items existed in the registry and were removed — not merely
   "never added." The `tagging/4-1_*.jsonl deleted` bullet at line 192 corroborates that at least the
   tagging layer had 4-1 content that was subsequently deleted.
2. Against that: the skeleton file (`skeletons/4-1_practice_skeletons.json`) sitting on disk **today** is
   100% pristine, un-transcribed TODO stubs — if a completed transcription had once existed and been fed
   through `qb_append.py`, it is not obvious why this staging file would still read as untouched (it's
   plausible the real transcribed drafts, if they ever existed, were authored elsewhere and never written
   back into this file — but that can't be confirmed from disk).
3. The root inventory itself flags this as genuinely unresolved:
   `inventory/content_readiness_inventory.json:814` — *"Whether ingestion was ever attempted, is pending, or
   was abandoned is UNKNOWN from these files."* — and the matching anomaly entry at
   `inventory/content_readiness_inventory.json:1387-1388` repeats the same hedge.

**Net calibrated statement:** What is certain — (a) no completed, currently-retained transcription-to-registry
ingestion exists for 4-1 today; (b) the observable current state is 0 registry rows, and no SE/TE source;
(c) the documented proximate cause of the current state is the 2026-05-13 department skip of L41, which
triggered deletion of at least `tagging/4-1_*.jsonl` (and, per `:112`, possibly registry/Supabase rows too)
during the retirement cull. What remains open — whether a *fuller* ingestion (transcribed registry rows,
not just tagging) briefly existed and was wiped, versus the pipeline simply never got past the skeleton
stage before the skip made further work moot. Frame this as **"never completed/retained, halted by the
dept-skip"** — not as a certain "never ingested at all."

## Documented status conflict (teacher judgment required)

Three sources disagree on 4-1's status, from oldest to newest:

1. **`A2LessonSelection.txt:4`** (undated, appears to be an early planning note): lists
   `"4-1,4-3,4-4,4-5 (LEHS 8 question assessment)"` — 4-1 **included** in the planned lesson set.
2. **`CLAUDE.md:45`**: still reads `"### Lesson 4-1 (ready, Fri F / Mon A start)"`, with a full P1/P2/P3 table
   (lines 45-53) describing it as ready to teach — this is **stale** and contradicts the actual repo state
   (no registry rows, tex retired to `legacy/`).
3. **`CONTINUATION_PROMPT.md:32`** (dated 2026-05-13, the most recent authoritative record): L41 fully
   skipped/retired, cadence moved to L43.

**This three-way conflict — whether 4-1 should be revived, left retired, or the stale `CLAUDE.md` entry
simply corrected to reflect retirement — is a TEACHER JUDGMENT.** It is not resolved by this diagnosis and
should not be inferred from file recency alone; the newest document (`CONTINUATION_PROMPT.md`) records a
department-level pedagogical decision (the Klimsara-confirmed skip), which is a different kind of authority
than a stale table in `CLAUDE.md` simply not having been updated.
