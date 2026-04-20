# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

---

## Machine context

**This repo exists on two machines.** Home laptop (`C:/Users/rober/...`) is where code/tooling iteration happens with no student materials present. Work laptop (`C:/Users/ColsonR/...`) is where actual Savvas screenshots live and where packet building against real source material happens. **Lesson 3-5 was built on the home laptop; Lesson 4-1 onward will be built on the work laptop** because the user captures Savvas screenshots there. Always `git pull` on the machine you pick up on.

## Next curriculum target: Unit 4 → selected Unit 5 → Trig → Unit 6

**Not Lesson 3-6.** User's explicit roadmap (from `A2LessonSelection.txt`):

1. **Unit 4 (all four)**: 4-1, 4-3, 4-4, 4-5 → culminates in **LEHS 8-question assessment**
2. **Unit 5 (selected)**: 5-1 (quick), 5-4, 5-5 (quick)
3. **Right-triangle trig**: SOH CAH TOA
4. **Unit 6**: 6-3, 6-4, 6-5

Skips 3-6, 4-2, 5-2, 5-3, 6-1, 6-2. Same Savvas-only + single-DOK-3 + pacer-v2 pattern applies to every lesson.

### First task on next session (work laptop)

User will drop Savvas screenshots into `questionbank/images/` for **Lesson 4-1** (naming convention `4-1_savvas_qNN_question.png` / `..._answer.png`, teacher addendum pages `4-1_te_addendum_pNN.png`). Ingest procedure:

1. Read `questionbank/INGEST_PROMPT.md`.
2. Create `calibration/4-1.json` (Savvas Item Analysis table — DOK mix, Example anchors, multiplicity of practice items).
3. Ingest screenshots with vision, append to `questionbank/registry.jsonl` using `qb_append.py`. Tag scheme: `savvas-practice`, `try-it`, `lesson-quiz`, `do-now-bridge`, `today-preview`, `blooket-pool`, `rti-support`, `rti-extend`, `day{N}-...`, plus `lesson-4-1`.
4. Identify the Savvas-declared DOK-3 item(s) for 4-1. That becomes the single DOK-3 driver for the corresponding day.
5. Build packets + pacer v2 + slides using the same `build_day*.py` / `packet_styles.py` / `build_pacer_qr.py` toolchain.

## Where we are (as of 2026-04-20, end of session)

### Hard rules (locked in)

1. **Savvas-only for student-facing work.** Every item on a student packet must trace to a Savvas bank ID in `questionbank/registry.jsonl`. No fabricated problems. Ingest missing items from `questionbank/images/` screenshots before using them.
2. **Single-DOK3 spine.** One DOK-3 driver per period, self-contained on the page. See wiki `concepts/Single-DOK3 Lesson Spine.md`.
3. **Savvas terminology is authoritative.** "Crosses the x-axis" for odd multiplicity; "tangent to the x-axis" / "turning point" for even multiplicity. "Touches and turns back" is an accepted synonym. **Do not use "flatten" / "flatten-through"** — not Savvas.
4. **Summary exit, not CER.** Walk-out tasks recap; they don't generate new argument. Fill-in-the-blank + one open "biggest thing learned" sentence.
5. **Blooket = DOK-1 rule recall only.** No procedural factoring items.
6. **Savvas's editorial stance on DOK-3:** in Lesson 3-5, Savvas puts DOK-3 demand on modeling applications only (Practice #25 firework, #27 storage box, #30 Venetta — all Example 4 anchors). Multiplicity and complex zeros are DOK 1–2 procedural skills in Savvas's framing.
7. **Student-facing artifacts must not leak answer keys.** If a bank image was cropped from the teacher's key, generate a clean student version (e.g., via matplotlib).
8. **Solo teacher, ≤10 students.** No "aide" language anywhere. Cold-call phrasing is low-stakes — no grades or candy tied to individual answers.
9. **Teacher packet is optional when the pacer is self-contained.** See wiki `concepts/Self-Contained Pacer Pattern.md`. All new pacers Day 2-3 through Day 8 use v2 pattern.

### Current packet structure — 8 days, ALL BUILT (2026-04-20 session)

| Combined Day | Source days folded | DOK-3 driver | Status |
|---|---|---|---|
| Day 1 | — | — (DOK-3 supplement optional) | **Taught**, ran 3 periods. Optional `Day_1_Period_A_Supplement_The_Leap.docx`. |
| **Day 2-3** | Day 2 (factored-form graphing) + Day 3 (multiplicity) | none (DOK 1-2 practice day) | **Built, Savvas-only. Pacer v2.** LQ Q4 · Example 2 · Try It 2a/2b + Practice #14/#15/#16 · LQ Q5 |
| **Day 4-5** | Day 4 (real+complex zeros) + Day 5 (modeling) | **Savvas Practice #27** (storage box) | **Built, Savvas-only. Pacer v2 (upgraded 2026-04-20).** Practice #28 · Example 3 · Try It 3a/3b · Practice #27 · Practice #17 |
| **Day 6** | polynomial inequalities | none (DOK 1-2 practice day) | **Built 2026-04-20, Savvas-only, pacer v2.** Launch Try It 6a sign-chart · Practice Try It 6b + #22/#23/#24 · Exit = summary recap (no LQ). |
| **Day 7** | synthesis + performance task | **Savvas Practice #30** (Venetta) | **Built 2026-04-20, Savvas-only, pacer v2.** Do Now #29 SAT-style · Launch 3-concept rapid review · Explore Venetta 26 min · Exit summary recap. |
| **Day 8** | quiz + stations | — (no DOK-3; mixed DOK 1-2 quiz) | **Built 2026-04-20, Savvas-only, pacer v2 (no Blooket).** Do Now #28 vocab · LQ Q1a/Q1b/Q2/Q3/Q4/Q5 · 3-station rotation (Support/Core/Extend, all Savvas-prefixed). |
| Short variants | Day 2-3 + Day 4-5 compressed | same drivers | **Built 2026-04-20.** 45-min F Wed variants, both total 2700s exactly. |

**Legacy per-day packets** (Day 2, Day 3, Day 3 short) remain in the repo marked "Legacy" in `index.html`. They contain fabricated items (Reverse Engineering, Tonya error analysis) and do not satisfy the Savvas-only rule.

### Question bank — lesson 3-5

**90 total items.** Three Savvas-declared DOK-3 items (all now in use):
- `3-5-savvas-q25` — firework height model (Example 4) — unused directly; was proposed as Day 8 Extend station but removed to honor single-DOK-3 rule.
- `3-5-savvas-q27` — storage box volume (Example 4, **Day 4-5 DOK-3 driver**)
- `3-5-savvas-q30` — Venetta deli profit (performance task, **Day 7 DOK-3 driver**)

Plus: 2 DOK-2 items (lesson quiz), 87 DOK-1 items. 12 with visuals.

**Tag scheme:** `blooket-pool`, `do-now-bridge`, `today-preview`, `seeded-from-blooket`, `savvas-practice`, `try-it`, `lesson-quiz`, `rti-extend`, `rti-support`, `day{N}-...` (day binding), `savvas-declared-dok3`, `savvas-language-corrected-2026-04-20`.

### Pacer v2 pattern (self-contained teaching tool)

All pacers Day 2-3 through Day 8 now use the v2 pattern. Reference implementation: `Day_23_Pacer.html`. Characteristics:

- **Nested sub-step timers**: each phase carries a `substeps[]` array; side panel tracks current sub-step with its own countdown; completed sub-steps struck through.
- **Inline answer keys** (green callouts), **teacher scripts** (navy callouts), **warnings/gotchas** (red), **rules** (teal).
- **Blooket: single 6-min round** + 1-min **Blooket Wrap** phase (candy pass + class repeats lowest-scored rule aloud). Day 8 has no Blooket (quiz day).
- **Mode toggle** for Blooket: Fishing Frenzy (default) vs Racing (repeat days).
- **QR overlay** (72 px, auto-hides on narrow viewport) pointing to the pacer's own GitHub Pages URL.
- **Day 8 has a 5-min quiz warning banner** that auto-renders when the Quiz phase has ≤300s remaining.

Teacher runs the full 55-min (or 45-min for short variants) lesson from the pacer alone — the printed teacher packet is for evaluators/archival.

### Tooling state

| Tool | Purpose |
|---|---|
| `qb.py` | Registry accessor. `get_for_packet(ids)` wires Practice into builders. `teacher_prompts(lesson, anchor_example, types)` pulls Savvas TE content. |
| `qb_append.py` / `import_blooket_csv.py` | Bank mutation helpers. |
| `packet_styles.py` | Shared docx formatting helpers (day banner, teal sections, summary-exit box, sentence-frame callout, running header, framework phase header). |
| `build_day{23,45,6,7,8}_packets.py` | **Recommended packet builders (Savvas-only).** |
| `build_day{23,45,6,7,8}_slides.py` | Projection decks. |
| `build_day{2,3}_packets.py` | Legacy per-day builders (fabricated items). |
| `build_day1_supplement.py` | Optional Day 1 Period A handout. |
| `build_pacer_qr.py` | `segno`-powered offline SVG QR generator. 11 pacers total. |
| `regen_blooket_csvs.py` | Regenerates Blooket CSVs from bank with ratio reporting. |
| `build_blank_grid.py` | Generates `assets/blank_grid.png` for student sketch space. |
| `build_lq_q4_graph.py` | Generates `assets/lq_q4_student_graph.png` — clean student-facing LQ Q4 graph. |
| `index.html` | GitHub Pages landing page with QR card grid: Recommended + Short (F Wed) + Legacy sections. |
| `questionbank/INGEST_PROMPT.md` | Procedure for ingesting new source screenshots. |

### Artifacts on disk (Lesson 3-5)

**Recommended (Savvas-only, all pacer v2):**
- Day 2-3: `Day_23_Do_Now.docx`, `Day_23_Student_Packet.docx`, `Day_23_Teacher_Packet.docx`, `Day_23_Pacer.html`, `Day_23_Slides.pptx`, `qr_day23_pacer.svg`
- Day 4-5: `Day_45_Do_Now.docx`, `Day_45_Student_Packet.docx`, `Day_45_Teacher_Packet.docx`, `Day_45_Pacer.html`, `Day_45_Slides.pptx`, `qr_day45_pacer.svg`
- Day 6: `Day_6_Do_Now.docx`, `Day_6_Student_Packet.docx`, `Day_6_Teacher_Packet.docx`, `Day_6_Pacer.html`, `Day_6_Slides.pptx`, `qr_day6_pacer.svg`
- Day 7: `Day_7_Do_Now.docx`, `Day_7_Student_Packet.docx`, `Day_7_Teacher_Packet.docx`, `Day_7_Pacer.html`, `Day_7_Slides.pptx`, `qr_day7_pacer.svg`
- Day 8: `Day_8_Do_Now.docx`, `Day_8_Quiz.docx` (separate), `Day_8_Student_Packet.docx`, `Day_8_Teacher_Packet.docx`, `Day_8_Pacer.html`, `Day_8_Slides.pptx`, `qr_day8_pacer.svg`

**Short (45-min F Wed variants):**
- `Day_23_Pacer_short.html`, `qr_day23_pacer_short.svg`
- `Day_45_Pacer_short.html`, `qr_day45_pacer_short.svg`

**Assets:** `assets/blank_grid.png`, `assets/lq_q4_student_graph.png`

**Legacy (fabricated DOK-3 items):** `Day_2_*` (Reverse Engineering), `Day_3_*` (Tonya), `Day_3_Pacer_short.html`.

**Day 1 materials:** `Day_1_Student_Packet_v3 (1).docx`, `Day_1_Teacher_Packet.docx`, `Day_1_Period_A_Supplement_The_Leap.docx`.

**Master references:** `Revised_Zeros_of_Polynomials_8-Day_Lesson_Packet_FINAL.docx`, `lesson35_8day.tex`, `DOKframework.txt`, `aga_24_a2_na_0305_lq.docx`.

**Blooket CSVs:** `Blooket_Day2_GraphingFactoredForm.csv`, `Blooket_Day3_Multiplicity.csv` (regenerate via `regen_blooket_csvs.py`). No new Day 6/7/8 Blooket CSVs yet — the existing decks cover whole-topic review.

### Class context

- Two sections: **Period A** and **Period F**.
- **Week of 2026-04-27 schedule** saved in project memory (`memory/schedule_2026-spring.md`): Mon A 65 / Tue F 65 + A 55 / Wed A 65 + F **45** / Thu F 65 + A 55 / Fri F 65.
- Wednesday F = 45 min (short period) → use `Day_23_Pacer_short.html` and `Day_45_Pacer_short.html`.
- Day 1 evidence: ~1.4× stretch factor when sizing lessons for this population.
- School's lesson framework sub-phases the Do Now into A / B / C. See wiki `concepts/Do Now A-B-C Framework.md`.
- **Solo teacher, no aide, class ≤10.** All packet + pacer language reflects this.
- **Blooket tradition:** candy pass at end of game; whole-class verbalization of lowest-scored dashboard rule. Formalized into the Blooket Wrap phase across all Days 2-3 → 7.

## What's open (next session)

1. **Day 8 Support station has only 1 Savvas item** after the Savvas-only filter narrowed the pool. If you want 2 items per station, hand-pick a second `3-5-savvas-*` ID in `build_day8_packets.py:62` or widen the tag filter.
2. **Day 6/7/8 Blooket CSVs.** Currently no dedicated CSVs for these days; the Day 2/Day 3 decks cover procedural items. If you want day-specific rule-recall decks, use `regen_blooket_csvs.py` with a new tag filter.
3. **Classroom test:** run Day 6 (or a combined day) live and note timing drift. Day 7 Explore (Venetta) was widened to 26 min based on timing audit — verify it lands.
4. **Lesson 4-1 ingest** (next). User will take Savvas screenshots on the work laptop and drop them into `questionbank/images/`. See "Next curriculum target" section above for the full roadmap (4-1, 4-3, 4-4, 4-5 → LEHS assessment → 5-1/5-4/5-5 → SOH CAH TOA → 6-3/6-4/6-5). **Not 3-6.**

## Cross-agent review (2026-04-20)

Codex reviewed the Day 6/7/8 + short-variant build via `cross-agent.py` and flagged 5 FAIL verdicts; all fixed before commit:
- Day 7 had hard-coded items (now `qb.get_for_packet`).
- Day 8 Support pulled a Blooket item (now filtered to `3-5-savvas-*`).
- Day 8 Extend had the firework DOK-3 item (removed; replaced with Savvas #24 inequality).
- Day 6 Exit was LQ Q3 not a recap (now fill-in + synthesis sentence).
- `Day_23_Pacer_short.html` exit substeps undershoot by 60s (fixed).
- Plus a bonus fix: Day 7 timing 53 vs 57 min (extended Explore buffer to 26 min).

Review log and final report: `state/cross-agent/fcd2d55e15aa.result.json` (not committed; regenerate on demand).

## Constraints & preferences worth remembering

- **No API credits.** All vision / transcription runs inline in Claude Code or Codex sessions.
- **Windows + MSYS2 shell.** UTF-8 BOM on Blooket CSVs; `PYTHONIOENCODING=utf-8` or `sys.stdout = io.TextIOWrapper(...)` on any Python script that prints unicode math.
- **Don't crowd the page.** Breathable whitespace > dense scaffolding.
- **Release valves ordered** per teacher packet. Never cut the Summary Exit.
- **Framework alignment for evaluators.** Every phase carries `Questions to ask:` and `Adult role:` lines.
- **Solo teacher.** No aide-based release valves. Single-teacher circulation (4 laps for ~10 students).

## Quick commands

```bash
# Verify environment after pull
git log --oneline -5
python qb.py                       # registry stats (expect 90 items as of 2026-04-20)

# Rebuild recommended (Savvas-only) materials — whole 8-day set
python build_day23_packets.py && python build_day23_slides.py
python build_day45_packets.py && python build_day45_slides.py
python build_day6_packets.py  && python build_day6_slides.py
python build_day7_packets.py  && python build_day7_slides.py
python build_day8_packets.py  && python build_day8_slides.py

# Regenerate all 11 pacer QR codes
python build_pacer_qr.py

# Regenerate Blooket CSVs from the bank (with ratio reporting)
python regen_blooket_csvs.py

# Regenerate student-facing graph assets
python build_blank_grid.py
python build_lq_q4_graph.py

# Cross-agent review (CC → Codex) — read-only, generates report JSON
python "C:/Users/rober/Downloads/Projects/Agent/runner/cross-agent.py" \
  --direction cc-to-codex --task-type review --read-only \
  --working-dir "C:/Users/rober/Downloads/Projects/Lesson_planning" \
  --timeout 600 --prompt "..."

# Ingest a Savvas screenshot (Lesson 4-1 is the next target, not 3-6)
# Tell Claude: "ingest questionbank/images/4-1_savvas_q<NN>_question.png"
```
