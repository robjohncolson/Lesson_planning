# NT14 Source-Gap Report — Lesson 4-1 Optional-Catalog Ingestion

Record id: `nt14-ingest-4-1-2026-07-23`. Companion to
`inventory/topic-4-1/nt14_source_inventory.json`. Every gap below is an
honest unresolved record per the NT14 no-invention rule: nothing was
back-solved, inferred, or fabricated to fill it. DOK transcription in this
ingestion is EVIDENCE ONLY — nothing here is VERIFIED; the DOK review log
(`tools/dok-review/review_log.jsonl`, 39 entries) was not touched.

## 1. Items NOT ingested — no DOK provenance (10 items)

The registry schema requires `dok`. NT14's DOK provenance rule admits only
(a) membership in `questionbank/calibration/4-1.json` `item_analysis` (which
covers practice numbers 8–26 only) or (b) a DOK printed in-source. A
dedicated vision audit of all 24 non-practice screenshots (6 SE example/
try-it, 3 concept/launch, 15 TE addenda) found **zero printed DOK labels
anywhere** — no "DOK", "Depth of Knowledge", or numeric DOK tag on any of
the 24 images. (One near-miss: `4-1_te_ex3_ell_addendum.png` contains a
bracketed `[2]` that is a pointer to dictionary definition (2) printed in
the same box, not a DOK marker.)

| Item | Prompt evidence on disk | Answer evidence on disk | DOK evidence | Disposition |
|---|---|---|---|---|
| Example 1 | `4-1_savvas_example1_question.png` | worked solution shown in SE frame | none | source-gap; not ingested |
| Example 2 | `4-1_savvas_example2_tryit2_question.png` | worked solution shown in SE frame | none | source-gap; not ingested |
| Example 3 | `4-1_savvas_example3_tryit3_question.png` | worked solution shown in SE frame | none | source-gap; not ingested |
| Example 4 | `4-1_savvas_example4_tryit4_question.png` | worked solution shown in SE frame | none | source-gap; not ingested |
| Example 5 | `4-1_savvas_example5_tryit5_question.png` | worked solution shown in SE frame | none | source-gap; not ingested |
| Try-It 1 | `4-1_savvas_tryit1_question.png` | `4-1_te_tryit1_answers_elicit.png` (legible) | none | source-gap; not ingested |
| Try-It 2 | `4-1_savvas_example2_tryit2_question.png` | `4-1_te_ex2_connect_tryit2_answers.png` (legible) | none | source-gap; not ingested |
| Try-It 3 | `4-1_savvas_example3_tryit3_question.png` | `4-1_te_ex3_purposeful_tryit3_answer.png` (legible) | none | source-gap; not ingested |
| Try-It 4 | `4-1_savvas_example4_tryit4_question.png` | `4-1_te_ex4_tryit4_answer_elicit.png` (legible) | none | source-gap; not ingested |
| Try-It 5 | `4-1_savvas_example5_tryit5_question.png` | `4-1_te_ex5_connect_tryit5_answer.png` (legible) | none | source-gap; not ingested |

Note the asymmetry: prompt and (for Try-Its) answer evidence EXISTS and is
fully legible — only the DOK provenance is missing. If a future SE/TE
export (per `RECOVERY_PLAN.md` Step 3b: the TE "carries DOK labels per
item") supplies printed DOK values, these ten become transcribable without
re-photography. Sibling lessons ingested Examples/Try-Its with TE-sourced
DOK; 4-1 has no SE/TE PDF/tex anywhere in the repo (see `DIAGNOSIS.md`).

## 2. Ingested items with in-band partial gaps (2 of 19)

Both rows were ingested as `transcribable-partial` with the gap marked
explicitly in-band — never filled by inference.

### 2.1 `4-1-savvas-q16` — question value cropped out of source
`4-1_savvas_q16_question.png` (sha256 `d69e5c0c…`) is cropped at the right
edge: the given y-value in "If x and y vary inversely and x = 3 when
y = ___" is absent from the image (manager re-verified at source and 4x
upscale). The prompt carries `[ILLEGIBLE — value cropped out of the right
edge of the source screenshot]` at the gap. The answer evidence is complete
("When x = −1, y = −2."). The missing given is algebraically recoverable
(y = 2/3) but was deliberately NOT back-solved — that would be invention,
not transcription. **Remedy: one wider re-screenshot of SE Practice #16.**

### 2.2 `4-1-savvas-q18` — answer key truncated in source
`4-1_savvas_q18_answer.png` (sha256 `d03b550e…`) cuts off mid-sentence
after "domain: the set of real". The rest of the domain clause and the
entire range clause (explicitly requested by the question) are captured
nowhere in the repo. `correct` preserves the legible fragment with an
explicit `[TRUNCATED IN SOURCE SCREENSHOT …]` marker; the parallel
structure of #19's answer was NOT used to complete it. **Remedy: one
re-screenshot of the TE answer column for Practice #18.**

## 3. Minor unresolved source ambiguity (ingested verbatim)

- `4-1-savvas-q24`: the MC stem's numerator prints as "Ai" (glyph could be
  A·i, A_i, or a typographic quirk; inspected at 6x/10x without resolution;
  the answer options reference plain "A"). Transcribed verbatim as
  `\frac{Ai}{B} = k`. Does not affect the keyed answer (option B, index 2,
  confirmed from `4-1_savvas_q24_answer.png`). Check against a
  higher-fidelity source if one is ever exported.

## 4. Non-item assets (no registry candidacy)

2 concept-box images, 1 launch image, and 15 TE-addenda images are support
material, not bank items; per repo convention TE prompts would live in
`questionbank/teacher_prompts/4-1.jsonl` (a separate, future task — not
part of NT14's registry scope). Full hashes in
`nt14_source_inventory.json` → `non_item_assets`.

## 5. What is NOT a gap

- All 19 practice items q8–q26 had question evidence, answer evidence
  (q14/q15 via the shared `4-1_savvas_q14q15_answers.png`), and calibration
  DOK coverage — there were no source-gap practice items.
- The filename sweep's one substring false-positive
  (`3-5_savvas_q14-16_question.png`) was excluded by prefix matching.
