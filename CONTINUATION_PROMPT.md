# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

---

## Where we are (as of 2026-04-20, end of session)

### Hard rules (locked in)

1. **Savvas-only for student-facing work.** Every item on a student packet must trace to a Savvas bank ID in `questionbank/registry.jsonl`. No fabricated problems. Ingest missing items from `questionbank/images/` screenshots before using them.
2. **Single-DOK3 spine.** One DOK-3 driver per period, self-contained on the page. See wiki `concepts/Single-DOK3 Lesson Spine.md`.
3. **Savvas terminology is authoritative.** "Crosses the x-axis" for odd multiplicity; "tangent to the x-axis" / "turning point" for even multiplicity. "Touches and turns back" is an accepted synonym. **Do not use "flatten" / "flatten-through"** — not Savvas.
4. **Summary exit, not CER.** Walk-out tasks recap; they don't generate new argument.
5. **Blooket = DOK-1 rule recall only.** No procedural factoring items.
6. **Savvas's editorial stance on DOK-3:** in Lesson 3-5, Savvas puts DOK-3 demand on modeling applications only (Practice #25 firework, #27 storage box, #30 Venetta — all Example 4 anchors). Multiplicity and complex zeros are DOK 1–2 procedural skills in Savvas's framing.
7. **Student-facing artifacts must not leak answer keys.** If a bank image was cropped from the teacher's key, generate a clean student version (e.g., via matplotlib). See `assets/lq_q4_student_graph.png`.
8. **Solo teacher, ≤10 students.** No "aide" language anywhere. Cold-call phrasing is low-stakes ("thanks, anyone want to build on that?") — no grades or candy tied to individual answers.
9. **Teacher packet is optional when the pacer is self-contained.** See wiki `concepts/Self-Contained Pacer Pattern.md` + `Day_23_Pacer.html` for the pattern.

### Current packet structure — 8 days → 6–7 teachable days

| Combined Day | Source days folded | DOK-3 driver | Status |
|---|---|---|---|
| Day 1 | — | — (DOK-3 supplement optional) | **Taught**, ran 3 periods. Optional `Day_1_Period_A_Supplement_The_Leap.docx`. |
| **Day 2-3** | Day 2 (factored-form graphing) + Day 3 (multiplicity) | none (DOK 1-2 practice day) | **Built, Savvas-only. Pacer v2 (self-contained).** LQ Q4 · Example 2 · Try It 2a/2b + Practice #14/#15/#16 · LQ Q5 |
| **Day 4-5** | Day 4 (real+complex zeros) + Day 5 (modeling) | **Savvas Practice #27** (storage box) | **Built, Savvas-only DOK-3. Pacer v1 (not yet upgraded to v2).** Practice #28 · Example 3 · Try It 3a/3b · Practice #27 · Practice #17 |
| Day 6 | polynomial inequalities | not yet built | TBD |
| Day 7 | synthesis + performance task | **Savvas Practice #30** (Venetta) | TBD |
| Day 8 | quiz + stations | — | TBD |

**Legacy per-day packets** (Day 2, Day 3, Day 3 short) remain in the repo marked "Legacy" in `index.html`. They contain fabricated items (Reverse Engineering, Tonya error analysis) and do not satisfy the Savvas-only rule.

### Question bank — lesson 3-5

**90 total items.** Three Savvas-declared DOK-3 items ingested:
- `3-5-savvas-q25` — firework height model (Example 4, Day 5 topic)
- `3-5-savvas-q27` — storage box volume (Example 4, **Day 4-5 DOK-3 driver**)
- `3-5-savvas-q30` — Venetta deli profit (performance task, **Day 7 DOK-3 driver**)

Plus: 2 DOK-2 items (lesson quiz), 87 DOK-1 items. 12 with visuals.

**Savvas-language audit complete:** all "flatten" language removed from packets and Blooket bank items. Items `3-5-blooket-day3-multiplicity-q12` and `q16` rewritten with Savvas vocabulary and tagged `savvas-language-corrected-2026-04-20`.

**Tag scheme:** `blooket-pool`, `do-now-bridge`, `today-preview`, `seeded-from-blooket`, `savvas-practice`, `try-it`, `lesson-quiz`, `rti-extend`, `rti-support`, `day{N}-...` (day binding), `savvas-declared-dok3`, `savvas-language-corrected-2026-04-20`.

### Pacer v2 pattern (self-contained teaching tool)

`Day_23_Pacer.html` is the reference implementation. Characteristics:

- **Nested sub-step timers**: each phase carries a `substeps[]` array; side panel tracks current sub-step with its own countdown; completed sub-steps struck through.
- **Inline answer keys** (green callouts), **teacher scripts** (navy callouts), **warnings/gotchas** (red), **rules** (teal).
- **Blooket: single 6-min round** + 1-min **Blooket Wrap** phase (candy pass + class repeats lowest-scored rule aloud).
- **Mode toggle** for Blooket: Fishing Frenzy (default) vs Racing (repeat days).
- **QR overlay** (72 px, auto-hides on narrow viewport) pointing to the pacer's own GitHub Pages URL.

Teacher runs the full 55-min lesson from the pacer alone — the printed teacher packet is for evaluators/archival.

### Tooling state

| Tool | Purpose |
|---|---|
| `qb.py` | Registry accessor. `get_for_packet(ids)` wires Practice into builders. `teacher_prompts(lesson, anchor_example, types)` pulls Savvas TE content. |
| `qb_append.py` / `import_blooket_csv.py` | Bank mutation helpers. |
| `packet_styles.py` | Shared docx formatting helpers (day banner, teal sections, summary-exit box, sentence-frame callout, running header). |
| `build_day{23,45}_packets.py` | **Recommended packet builders (Savvas-only).** |
| `build_day{23,45}_slides.py` | Projection decks for combined days. |
| `build_day{2,3}_packets.py` | Legacy per-day builders (fabricated items). |
| `build_day{2,3}_slides.py` | Legacy per-day slide decks. |
| `build_day1_supplement.py` | Optional Day 1 Period A handout. |
| `build_pacer_qr.py` | `segno`-powered offline SVG QR generator. |
| `regen_blooket_csvs.py` | Regenerates Blooket CSVs from bank with ratio reporting. |
| `build_blank_grid.py` | Generates `assets/blank_grid.png` for student sketch space. |
| `build_lq_q4_graph.py` | Generates `assets/lq_q4_student_graph.png` — clean student-facing LQ Q4 graph (no answer indication). |
| `index.html` | GitHub Pages landing page with QR card grid. |
| `questionbank/INGEST_PROMPT.md` | Procedure for ingesting new source screenshots. |

### Artifacts on disk (Lesson 3-5)

**Recommended (Savvas-only):**
- `Day_23_Do_Now.docx`, `Day_23_Student_Packet.docx`, `Day_23_Teacher_Packet.docx`, **`Day_23_Pacer.html` (v2 — self-contained)**, `Day_23_Slides.pptx`, `qr_day23_pacer.svg`
- `Day_45_Do_Now.docx`, `Day_45_Student_Packet.docx`, `Day_45_Teacher_Packet.docx`, `Day_45_Pacer.html` (v1), `Day_45_Slides.pptx`, `qr_day45_pacer.svg`
- `assets/blank_grid.png`, `assets/lq_q4_student_graph.png`

**Legacy (fabricated DOK-3 items):**
- `Day_2_*` — Reverse Engineering
- `Day_3_*` — Tonya error analysis
- `Day_3_Pacer_short.html` — 45-min F Wed variant of legacy Day 3

**Day 1 materials:** `Day_1_Student_Packet_v3 (1).docx`, `Day_1_Teacher_Packet.docx`, `Day_1_Period_A_Supplement_The_Leap.docx`.

**Master references:** `Revised_Zeros_of_Polynomials_8-Day_Lesson_Packet_FINAL.docx`, `lesson35_8day.tex`, `DOKframework.txt`, `aga_24_a2_na_0305_lq.docx`.

**Blooket CSVs:** `Blooket_Day2_GraphingFactoredForm.csv`, `Blooket_Day3_Multiplicity.csv` (regenerate via `regen_blooket_csvs.py`).

### Class context

- Two sections: **Period A** and **Period F**.
- **Week of 2026-04-27 schedule** saved in project memory (`memory/schedule_2026-spring.md`): Mon A 65 / Tue F 65 + A 55 / Wed A 65 + F **45** / Thu F 65 + A 55 / Fri F 65.
- Wednesday F = 45 min (short period). Needs compressed variants that drop Practice and fold Share/Summary into Exit.
- Day 1 evidence: ~1.4× stretch factor when sizing lessons for this population.
- School's lesson framework sub-phases the Do Now into A / B / C (solo paper DOK 2 + login + Blooket DOK 1). See wiki `concepts/Do Now A-B-C Framework.md`.
- **Solo teacher, no aide, class ≤10.** All packet + pacer language reflects this.
- **Blooket tradition:** candy pass at end of game (everyone gets one; top finisher gets extra); whole-class verbalization of the lowest-scored dashboard rule. Formalized into the Day 2-3 Pacer v2 "Blooket Wrap" phase.

## What's open (next session)

1. **Port pacer v2 pattern to Day_45_Pacer.html.** Add nested sub-step timers, inline answer keys, Blooket Wrap phase. See `Day_23_Pacer.html` as the reference + wiki `concepts/Self-Contained Pacer Pattern.md` for the schema.
2. **Build Combined Day 6** (polynomial inequalities). Bank items: `3-5-tryit-6a`, `3-5-tryit-6b`, `3-5-savvas-q22/q23/q24`, `3-5-lq-q3`, plus RtI support items. No DOK-3 driver on Day 6 specifically — DOK-3 is on Day 7.
3. **Build Combined Day 7** (synthesis + performance task). DOK-3 driver = **Savvas Practice #30** Venetta deli (already in bank as `3-5-savvas-q30`). Apply pacer v2 pattern.
4. **Build Day 8** (quiz + differentiated stations). Quiz items already in bank (`3-5-lq-q1a/b`, `q2`, `q3`, `q4`, `q5`).
5. **Compressed 45-min variants** for Wednesday F period (for Day 2-3 and Day 4-5). Pattern: drop Practice, fold Share/Summary into Exit transition. Reference: `Day_3_Pacer_short.html` (legacy).
6. **Lesson 3-6 ingest** (eventually). When 3-6 starts: create `calibration/3-6.json`, screenshot Savvas Item Analysis table, replace placeholders, ingest practice + teacher addendums. Same tag scheme + Savvas-only rule applies.

## Constraints & preferences worth remembering

- **No API credits.** All vision / transcription runs inline in Claude Code or Codex sessions.
- **Windows + MSYS2 shell.** UTF-8 BOM on Blooket CSVs; `PYTHONIOENCODING=utf-8` or `sys.stdout = io.TextIOWrapper(...)` on any Python script that prints unicode math.
- **Don't crowd the page.** Breathable whitespace > dense scaffolding.
- **Release valves ordered** per teacher packet. Never cut the Summary Exit.
- **Framework alignment for evaluators.** Every phase carries `Questions to ask:` and `Adult role:` lines.
- **Solo teacher.** No aide-based release valves. Single-teacher circulation (4 laps for ~10 students).
- **Project CLAUDE.md** requires GitNexus impact analysis before editing code symbols — for `*.py` edits only, not for static content.

## Quick commands

```bash
# Verify environment after pull
git log --oneline -5
python qb.py                       # registry stats (expect 90 items as of 2026-04-20)

# Rebuild recommended (Savvas-only) materials
python build_day23_packets.py
python build_day23_slides.py
python build_day45_packets.py
python build_day45_slides.py

# Rebuild legacy per-day materials
python build_day2_packets.py
python build_day2_slides.py
python build_day3_packets.py
python build_day3_slides.py

# Regenerate Blooket CSVs from the bank (with ratio reporting)
python regen_blooket_csvs.py

# Regenerate all pacer QR codes
python build_pacer_qr.py

# Regenerate student-facing graph assets
python build_blank_grid.py
python build_lq_q4_graph.py

# Ingest a Savvas screenshot (e.g., for Day 6 / Day 7 items)
# Tell Claude: "ingest questionbank/images/3-5_savvas_q<NN>_question.png"
```
