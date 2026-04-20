# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

---

## Machine context

**Dual-machine setup.** Home laptop (`C:/Users/rober/...`) is where code/tooling iteration happens with no student materials present. Work laptop (`C:/Users/ColsonR/...`) is where Savvas screenshots live and where packet building against real source material happens. This session ran on the **work laptop** and covered the Klimsara-adapted pivot + Lesson 3-5 close-out + full Lesson 4-1 build. Always `git pull` on the machine you pick up on.

**Obsidian wiki** lives on the home laptop only (not tracked in git from this repo). See `WIKI_UPDATES_PENDING.md` in repo root for pending wiki-page updates to apply when back on home laptop.

## Major pivot this session (2026-04-20)

**From day-by-day (8-day Lesson 3-5) to Klimsara-adapted 3-period structure.** Triggered by the reality that we have ~7 teaching weeks for 11 lessons. 8-day cadence would require 17 weeks. New pattern aligns with Lynn's DOK framework (Explore = 35–40 min student heavy lifting, not teacher modeling) AND with Klimsara's already-passed-admin-review packets.

**Key policy changes:**
- **Blooket dropped** from Unit 4+ (and retroactively from 3-5 close-out). Do Now carries DOK-1 load now.
- **Try-Its stay in-class as Think-Pair-Share.** Student homework completion unreliable; Explore phase requires TPS density.
- **Single-DOK-3 rule clarified**: per period, not per lesson. P3 can be DOK-2 mastery day.
- **HW back-of-packet = optional reinforcement**, not required/graded.
- **Naming convention**: `L{NN}_P{N}_*.docx` replaces `Day_N_*`.

## Next curriculum target: Unit 4 → selected Unit 5 → Trig → Unit 6

User's explicit roadmap (from `A2LessonSelection.txt`):

1. **Unit 4 (all four)**: **4-1 DONE**, next 4-3, 4-4, 4-5 → culminates in **Topic 4 LEHS 8-Q assessment** (8 selected items: #2, 3, 4, 5, 6, 7, 15, 19 from `a2topic4assess.docx`)
2. **Unit 5 (selected)**: 5-1 (quick), 5-4, 5-5 (quick)
3. **Right-triangle trig**: SOH CAH TOA
4. **Unit 6**: 6-3, 6-4, 6-5

Skips 3-6, 4-2, 5-2, 5-3, 6-1, 6-2. Klimsara-adapted 3-period pattern applies to every lesson.

### First task next session: Lesson 4-3 ingest

1. User will drop Savvas screenshots for **Lesson 4-3** into `questionbank/images/` (naming convention `4-3_savvas_qNN_question.png` / `..._answer.png`, teacher addendum pages `4-3_te_addendum_pNN.png`).
2. Workflow same as 4-1:
   - Read `questionbank/INGEST_PROMPT.md`.
   - User supplies DOK-Example Item Analysis table → create `questionbank/calibration/4-3.json` (with objective, essential question, vocab, item_analysis, topic_vocabulary).
   - Ingest Example screenshots + TE addendums one example at a time.
   - Ingest Practice items using `generate_practice_skeletons.py 4-3` → fill in prompts + answer keys → batch append.
3. Build `L43_P{1,2,3}_packets.py` + `L43_P{1,2,3}_Slides.pptx` + `L43_Pacer.html` (single file, 3 tabs) using L41 as template.

**Topic 4 LEHS 8-Q assessment coverage** — 4-3 responsible for Q#2 (domain), Q#4 (simplify + domain), possibly Q#15. Emphasis on rational expression simplification + domain restrictions.

## Where we are (end of session 2026-04-20)

### Lesson 3-5 close-out (3 periods, teaching Tue-Thu of week of 4/27)

| Period | Day | Duration | Content | File prefix | DOK-3 driver |
|---|---|---|---|---|---|
| Mon catch-up | Mon 4/27 (A only, 65m) | Period A only | Finish Ex 1 Try-Its (sign chart → graph) | (existing Day 1 materials) | — |
| P2 | Tue 4/28 (F 65 / A 55) | 55 min base | Multiplicity + factored-form graphing | `L35_P2_*` | — |
| P3 | Wed 4/29 (A 65 / F **45 short**) | 55 min base | Real+complex zeros + modeling | `L35_P3_*` | **3-5-savvas-q27** (Storage Box) |
| P4 | Thu 4/30 (F 65 / A 55) | 55 min | Topic 3 Assessment (11 Qs) | `L35_P4_*` | — |

Thu assessment is external (`a2topic3assess.docx`, 11 Qs). `L35_P4_*` provides warm-up Do Now + post-test self-reflection + teacher proctoring notes.

**Single pacer**: `L35_Pacer.html` with 3 tabs (P2/P3/P4).
**Slide decks**: `L35_P2_Slides.pptx`, `L35_P3_Slides.pptx` (no slides for P4 assessment day).

### Lesson 4-1 (3 periods, teaching week of 5/4; F starts Fri 5/1)

**Registry: 47 items** covering all 19 Practice items + Examples/Try-Its + Concept Summary + TE addendums + Model & Discuss opener + ELL addendum.

| Period | File prefix | Content | DOK-3 driver | Assessment weight |
|---|---|---|---|---|
| P1 | `L41_P1_*` | Inverse variation introduction (xy = k) | — | — |
| P2 | `L41_P2_*` | Applications + Performance Task | **4-1-savvas-q26** (Ramón direct-vs-inverse) | — |
| P3 | `L41_P3_*` | Reciprocal function + translations | — | **2 of 8 LEHS Qs** (Q#3 asymptotes, Q#5 translations) |

**P3 is assessment-critical.** Practice #19 is THE rehearsal item (asymptotes + intercepts).

**Single pacer**: `L41_Pacer.html` with 3 tabs (P1/P2/P3).
**Slide decks**: `L41_P{1,2,3}_Slides.pptx`.

### Tooling changes this session

New files:
- `build_L35_P2_packets.py`, `build_L35_P3_packets.py`, `build_L35_P4_assessment_day.py`
- `build_L35_slides.py` (builds P2 + P3)
- `L35_Pacer.html` (3-tab single file)
- `build_L41_P1_packets.py`, `build_L41_P2_packets.py`, `build_L41_P3_packets.py`
- `build_L41_slides.py` (builds P1 + P2 + P3)
- `L41_Pacer.html` (3-tab single file)
- `generate_practice_skeletons.py` — skeleton stub generator for any lesson
- `backfill_visuals_4-1.py` — one-off, already run, kept for reference
- `questionbank/calibration/4-1.json` — Lesson 4-1 calibration (item_analysis table, objective, EQ, vocab)
- `skeletons/4-1_practice_skeletons.json` — now shows "all items ingested"

Extended files:
- `qb.py` — added `visuals_for(qids)`, `write_visuals_checklist(qids, path)`. `stats()` includes visual_type breakdown.
- `qb_append.py` — validates 3 new fields: `visual_type` (enum), `visual_needs_cleanup` (bool), `visual_clean_asset` (path). Warns when has_visual=true but type=none.
- `packet_styles.py` — added `emit_visuals_checklist(ids, path)` helper.
- `questionbank/INGEST_PROMPT.md` — documents the 3 new fields.

Retired to `legacy/` (18 files):
- Day 2 + Day 3 legacy per-day packets (fabricated items)
- Day 8 Quiz (superseded by Thu Topic 3 assessment)
- Blooket CSVs (both Day 2 + Day 3)
- Corresponding `build_day2_*` and `build_day3_*` scripts

Still in repo root but effectively deprecated (used only for Day 1-1 catch-up):
- `build_day23_*`, `build_day45_*`, `build_day6_*`, `build_day7_*`, `build_day8_*` — reference implementations only; not run going forward.

## Hard rules (locked in)

1. **Savvas-only for student-facing work** — every item traces to a registry bank ID.
2. **Single-DOK3 spine, per period** — one DOK-3 driver per period (P3 of a lesson may have none).
3. **Savvas terminology is authoritative** — "crosses the x-axis" (odd mult), "tangent" (even mult), no "flatten".
4. **Summary exit, not CER** — fill-in + one "biggest thing learned" sentence.
5. **Blooket is DEPRECATED** (Unit 4+). Do Now carries DOK-1 load.
6. **Try-Its stay in-class as Think-Pair-Share.**
7. **Student-facing artifacts must not leak answer keys.** If a bank image has margin answer commentary, generate a clean version OR use the image only on teacher-facing pages.
8. **Solo teacher, ≤10 students.** No "aide" language anywhere.
9. **Evaluator-required framework phases.** Teacher packet carries `Questions to ask:` and `Adult role:` per phase per `DOKframework.txt`.
10. **Klimsara-adapted 3-period cadence** is the default going forward.

## Class context

- Two sections: **Period A** and **Period F**. Both ≤10 students, ELL-heavy.
- Week of 4/27: Mon A 65 / Tue F 65 + A 55 / Wed A 65 + F **45** / Thu F 65 + A 55 / Fri F 65.
- Period A starts week behind Period F on 3-5 close-out; both finish Thu. F starts 4-1 Fri; A starts 4-1 Mon of week 5/4.
- Wednesday F = 45 min short variant — Explore cut.
- Blooket tradition (candy pass, whole-class verbalize lowest rule) is retired.

## What's open (next session)

1. **Lesson 4-3 ingest** — user provides screenshots. Use `generate_practice_skeletons.py 4-3` workflow.
2. **Pending `L41_P1` flag:** 4-1 Practice item #16 was reconstructed (the y-value in setup was cut off in source image). User asked to eye-check; if different from `y = 2/3`, run a patch script (see `questionbank/registry.jsonl` entry id `4-1-savvas-q16`).
3. **Pending `4-1-savvas-q18` flag:** answer key reconstruction of "domain: set of real numbers except 0" (image cut off). User asked to eye-check.
4. **`index.html` landing page** — stale (still references legacy Day 2-8 pacers). Low priority; pacers are opened directly, not via landing page.
5. **Wiki page updates** — pending on home laptop. See `WIKI_UPDATES_PENDING.md`.
6. **Mojibake in `source` fields** of some older registry entries (pre-new-schema ingest). Cosmetic — does not affect functionality.
7. **3-5 item backfill for visual_type** — not done; low priority since 3-5 artifacts are fixed and don't get rebuilt.

## Quick commands

```bash
# Verify environment after pull
git log --oneline -5
python qb.py                        # registry stats

# Rebuild any Lesson 3-5 close-out artifact
python build_L35_P2_packets.py
python build_L35_P3_packets.py
python build_L35_P4_assessment_day.py
python build_L35_slides.py          # builds both P2 + P3 decks

# Rebuild any Lesson 4-1 artifact
python build_L41_P1_packets.py
python build_L41_P2_packets.py
python build_L41_P3_packets.py
python build_L41_slides.py          # builds P1 + P2 + P3 decks

# Ingest workflow for a new lesson (e.g. 4-3)
# 1. Populate questionbank/calibration/4-3.json with item_analysis table
# 2. Generate practice skeletons:
python generate_practice_skeletons.py 4-3
# 3. Per item: fill in prompt + notes in the skeleton, then:
python qb_append.py skeletons/4-3_practice_skeletons.json

# Single-item stub:
python generate_practice_skeletons.py 4-3 --item 17

# Pacers are static files, open directly:
# start L35_Pacer.html  OR  start L41_Pacer.html
```

## Constraints & preferences worth remembering

- **No API credits.** All vision / transcription runs inline in Claude Code or Codex sessions.
- **Transcription protocol:** flag any Claude-vision uncertainty → user Gemini-verifies.
- **Windows + MSYS2 shell.** `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')` at top of any Python script that prints unicode math.
- **Don't crowd the page.** Breathable whitespace > dense scaffolding.
- **Framework alignment for evaluators.** Every teacher-packet phase carries DOK + minutes + teacher_does + students_do + Questions to ask + Adult role.
- **Solo teacher.** No aide-based release valves.
