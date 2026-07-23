# Lesson 4-1 Recovery Plan (conditional — only IF revived)

This is a concrete, ordered ingestion plan for lesson 4-1, to be used **only if the teacher decides to
revive it**. It does not itself revive anything, append to the registry, or touch any source file — it is a
plan document only. See `DIAGNOSIS.md` for the full status/history writeup.

## Step 0 — TEACHER JUDGMENT GATE (do not skip this)

**L41 is currently department-skipped as of 2026-05-13** (`CONTINUATION_PROMPT.md:32`, confirmed:
"the department skipped L41 (Klimsara confirmed); cadence jumps directly to L43"). `CLAUDE.md:45` still
calls it "ready," but that line is stale and out of sync with the retirement. `A2LessonSelection.txt:4`
lists 4-1 as part of an earlier planned set.

**Before any step below is executed, the teacher must explicitly decide to revive lesson 4-1** (overriding
the 2026-05-13 department skip) and, separately, decide whether the stale `CLAUDE.md:45` "ready" entry
should instead just be corrected to reflect retirement. Neither decision is made by this plan. Do not begin
Step 2 onward without that explicit go-ahead.

## Step 1 — Calibration: already done, no re-authoring needed

`questionbank/calibration/4-1.json` already has a real, populated `item_analysis` (5 examples mapped to
Savvas practice-item numbers, DOK-tagged). **Do not re-author it.** Its `dok2_anchors` and `dok3_anchors`
arrays are currently empty by design — they are meant to be backfilled with actual anchor item content
*after* ingestion (Step 5 below), not before.

## Step 2 — Close the DOK-3 skeleton gap FIRST

Before touching q8-q19/q21/q23/q24, add skeleton stubs for **q20, q22, q25, q26** — the four Savvas items
calibration names as this lesson's DOK-3 anchors (`4-1.json` line 27: `"dok3": [20, 22, 25, 26]`, all
anchored to Example 3). Their `_question.png`/`_answer.png` screenshots already exist on disk
(`questionbank/images/4-1_savvas_q{20,22,25,26}_{question,answer}.png`) but no skeleton entry currently
covers them.

- Preferred: re-run `generate_practice_skeletons.py` against `4-1.json` so it emits stubs for all
  Savvas-numbered items referenced in `item_analysis` (confirm it picks up 20/22/25/26 — if the script only
  ever emitted 15 because it was run before the calibration's DOK-3 numbers were finalized, this may need
  a manual hand-add of 4 stub entries following the exact same shape as the existing 15).
- This must happen **first**, because without a stubbed-and-ingested DOK-3 item, the lesson has **no DOK-3
  driver at all**, which directly violates the project's Single-DOK3 spine rule (one DOK-3 driver per
  period, self-contained — see `CLAUDE.md` "Hard rules" and the wiki concept "Single-DOK3 Lesson Spine").

## Step 3 — SE/TE source decision (branch point — pick one, or neither)

No `a2_4-1_SE.*` / `a2_4-1_TE.*` exists anywhere (pdf or tex). Two independent paths, not mutually exclusive:

- **(a) Registry ingestion does NOT require an SE/TE PDF.** The 19 practice-item screenshots (question +
  answer images) plus the already-authored calibration are sufficient to transcribe and append each item
  directly, exactly as `questionbank/INGEST_PROMPT.md` describes (Read the image with the Read tool, no
  external API). This path can proceed with zero new source material.
- **(b) A full lesson rebuild** (new `tex/L41_P{1,2,3}_{student,teacher}.tex` packets, pacer, assessment
  alignment matching sibling lessons like 4-3/4-4/4-5) benefits from having SE/TE like those peer lessons do
  — per `CONTINUATION_PROMPT.md:100`, this would mean exporting SE/TE from Savvas and converting PDF→LaTeX
  (the **TE** conversion is called out as the high-value one because it "carries DOK labels per item"), then
  committing `a2_4-1_SE.{pdf,tex}` / `a2_4-1_TE.{pdf,tex}` at repo root, matching the pattern of the nine
  other lessons that have them.

**Decision point for the teacher/planner:** is (a) alone sufficient (registry-only revival, e.g. to recover
the practice bank for reuse elsewhere), or is (b) wanted too (full lesson-packet rebuild)? This plan does not
choose for you — it only notes that (a) is the lower-cost path and is NOT blocked by the missing SE/TE.

## Step 4 — Transcribe + ingest the 19 practice items, SERIALLY, one at a time

Covers q8 through q26 (19 items total, once Step 2's gap is closed). For each item, in order:

1. Read the `_question.png` (and `_answer.png` if present) with the Read tool.
2. Fill in `prompt` (transcribe verbatim, preserving math per `INGEST_PROMPT.md:27-29` conventions: `^` for
   exponents, `√` for roots, proper minus `−`, `·` for multiplication), `answers`, and `correct`.
3. Calibrate `dok` against the calibration's `item_analysis` anchors — do not guess; compare against the
   Example this item is mapped to (Step 1's table already tells you which Example/DOK each item maps to).
4. Draw `topics` from `4-1.json`'s `topic_vocabulary` list; add a new tag only if nothing existing fits.
5. Validate first: `python qb_append.py --dry-run <stub.json>` (or pipe via stdin). Fix any validation errors.
6. Append for real: `python qb_append.py <stub.json>` (drop `--dry-run`).
7. Confirm the assigned id before moving to the next item.

**This must be done ONE ITEM AT A TIME, in serial — never parallelized via subagents.** Per
`INGEST_PROMPT.md:59-64`: "each append depends on the previous `taken` id set, and the registry is
append-order sensitive." Running two ingests concurrently risks id collisions and lost appends.

**Never write to `registry.jsonl` directly.** Always go through `qb_append.py` — it validates required
fields (`lesson`, `prompt`, `dok`), enforces `ensure_calibration()` (already satisfied here — `4-1.json`
exists), and refuses duplicate prompts unless `--force` is passed.

## Step 5 — Backfill calibration anchors after ingest

Once real items are in the registry, backfill `4-1.json`'s `dok2_anchors` and `dok3_anchors` arrays (they
are intentionally empty until this point). Confirm the lesson's DOK-3 driver is one of Savvas #20/22/25/26
— per the calibration notes, the DOK-3 push is "subservient to Savvas fidelity," so the driver must be a
real Savvas item from that set, not an invented one.

## Step 6 — Rebuild downstream artifacts

- Re-create `tagging/4-1_*.jsonl` (documented as deleted during the 2026-05-13 cull —
  `CONTINUATION_PROMPT.md:192`) and any Supabase rows if the collaborative web app is in use for this lesson.
- Correct the stale `CLAUDE.md:45` "Lesson 4-1 (ready, Fri F / Mon A start)" table to reflect the lesson's
  true status (either "revived, rebuilt on \<date\>" or, if the teacher instead decides NOT to revive it,
  edit the entry to say retired — either way it should no longer silently claim "ready" while contradicting
  `CONTINUATION_PROMPT.md`).
- If pursuing the full rebuild path (Step 3b), follow the standard authoring loop already documented in
  `CONTINUATION_PROMPT.md`'s "Authoring workflow" section: draft `tex/L41_P{N}_student.tex` →
  `tex/L41_P{N}_teacher.tex` → pacer → Codex steelman review before commit.

## Step 7 — Savvas-only compliance (threaded through every step above)

Every transcribed item traces directly to a screenshot of the actual Savvas bank content (the screenshots
ARE the Savvas source) — this satisfies the project's Savvas-only hard rule. **Do not fabricate items** to
fill gaps, and do not invent DOK ratings without comparing against the calibration's anchors.

## Do NOT (recap)

- Do NOT write directly to `registry.jsonl` — always go through `qb_append.py`.
- Do NOT parallelize ingestion across subagents — the registry is append-order sensitive; process items one
  at a time, serially.
- Do NOT fabricate items or prompts — every item must trace to an actual Savvas screenshot on disk.
- Do NOT guess DOK levels without comparing against the calibration file's anchors; if anchors ever read as
  placeholder text, stop and ask rather than guessing (`INGEST_PROMPT.md:55-56`).
- Do NOT proceed past Step 0 without an explicit teacher decision to revive — reviving is not this plan's
  call to make.
