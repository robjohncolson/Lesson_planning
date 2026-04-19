# Continuation Prompt — Lesson_planning

Paste this into the next Claude Code / Codex session on the work machine
after `git pull`.

---

## Where we are (as of 2026-04-19)

### Lesson cadence — Algebra 2, Topic 3-5 (Zeros of Polynomial Functions)

8-day packet. Current pacing:

| Packet day | Content | Status |
|---|---|---|
| Day 1 | What is a zero? + sign charts (Example 1, Try It 1a/1b) | Taught (across two periods) |
| Day 2 | Graphing from Factored Form | **Next: Tuesday F (7:45–8:50, 65 min) + Tuesday A (8:55–9:50, 55 min)** |
| Day 3 | Multiplicity | Built; runs the day after Day 2 |
| Day 4 | Real & complex zeros | Not yet built |
| Day 5–8 | Modeling → equations → inequalities → assessment | Not yet built |

Day 3 sized for 55-min period; 65-min Tuesday F has 10 min slack for Desmos
depth + written Tonya CER. Day 5–7 anchored to Savvas Examples 4–6.

### Question bank state — lesson 3-5 only

87 entries total. Provenance fully traceable. Layout:

| Path | Role |
|---|---|
| `questionbank/registry.jsonl` | Student-facing items (87) |
| `questionbank/teacher_prompts/3-5.jsonl` | 23 ETP / ELL / habits-of-mind / common-error prompts (teacher-facing) |
| `questionbank/calibration/3-5.json` | Real Savvas-declared anchors: DOK 2 = #7, #18; DOK 3 = #27, #30 |
| `questionbank/calibration/sources/` | Reference screenshots (Savvas item-analysis tables) |
| `questionbank/images/` | Per-question/per-addendum screenshots |
| `qb.py` / `qb_append.py` / `import_blooket_csv.py` | Bank tooling |
| `questionbank/INGEST_PROMPT.md` | The procedure Claude follows on ingest requests |

#### Tag scheme (lesson 3-5)

- `blooket-pool` — DOK 1 only; safe to export to Blooket warm-up CSV
- `do-now-bridge` — recall of previous-day rules (target ≥25% of warm-up)
- `today-preview` — single-concept preview of today's lesson (≈75% of warm-up)
- `seeded-from-blooket` — historical provenance (no behavior)
- `derived-from-day1` / `derived-from-teacher-prompt` — provenance for new bridge items
- `savvas-practice` / `try-it` / `lesson-quiz` / `rti-extend` / `rti-support` — Savvas source type
- `day{2,3,4,5,6,7}-...` — day binding for lesson selection

#### Blooket pool ratios (current)

- **Day 2 pool:** 21 items (7 bridge / 14 preview = 33%)
- **Day 3 pool:** 27 items (7 bridge / 20 preview = 26%)

Bridge items are rule-recall (NOT problem-solving), per the design rule that
Blooket runs right after the Do Now and should refresh rules that make today's
problems easier.

### Materials on disk (top-level)

| File | Purpose |
|---|---|
| `Day_1_Student_Packet_v3 (1).docx`, `Day_1_Teacher_Packet.docx` | Day 1 (taught) |
| `Day_2_*` (Do Now, Student, Teacher, Slides, Pacer) | Day 2 lesson |
| `Day_3_*` (Do Now, Student, Teacher, Slides, Pacer) | Day 3 lesson |
| `Blooket_Day{2,3}_*.csv` | Targeted warm-ups (built from old hand-tuned items; can now be regenerated from the bank) |
| `aga_24_a2_na_0305_lq.docx` | Savvas Lesson Quiz 3-5 source |
| `Revised_Zeros_of_Polynomials_8-Day_Lesson_Packet_FINAL.docx` | Master 8-day plan |
| `build_day{2,3}_packets.py`, `build_day{2,3}_slides.py` | Generators |

## What's open

1. **Regenerate Day 2 + Day 3 Blooket CSVs from the bank.** The current CSVs
   were built before the bank had real DOK/topic tags. With `blooket-pool` +
   `do-now-bridge` + `today-preview` now in place, the round-trip should be:
   ```python
   import qb
   ids = [q['id'] for q in qb.select(lesson='3-5', tags=['blooket-pool','day2-graphing'])]
   qb.to_blooket_csv(ids, 'Blooket_Day2_GraphingFactoredForm.csv')
   ```
   Verify ratio (~25% bridge / ~75% preview) is preserved in the export.

2. **Build Day 4 materials (Real & Complex Zeros).** Anchored to Example 3.
   Use `build_day3_*.py` as templates. Bank already has Try It 3a/3b, RtI
   extension 1/2, practice #17 with full answer keys + DOK rationale.

3. **Migrate `build_day*_packets.py` to pull from the bank.** Builders still
   hardcode question text. Once Day 4 is built, refactor the Try It section
   to call `qb.select(lesson='3-5', tags=[...])` instead.

4. **Lesson 3-6 ingest (eventually).** When 3-6 starts, repeat the workflow:
   create `calibration/3-6.json` with placeholder anchors, screenshot the
   Savvas Item Analysis table, replace placeholders, ingest practice +
   teacher addendums. Same `blooket-pool` / `do-now-bridge` / `today-preview`
   scheme.

## Constraints & preferences worth remembering

- **No API credits.** All vision / transcription runs inline in Claude Code or
  Codex sessions. Do not scaffold anything that calls the Anthropic API.
- **Windows + MSYS2 shell.** UTF-8 BOM on Blooket CSVs; reconfigure stdout on
  any Python script that prints unicode math.
- **Project CLAUDE.md** requires GitNexus impact analysis before editing
  symbols — for code edits only, not for static content (packets, CSVs, JSONL).
- **Framework mapping** (from `DOKframework.txt`): every lesson phase carries
  explicit `[Framework]` + `[DOK]` tags. Keep that convention for Day 4+.
- **Release valve pattern**: when time is short, written CER on the DOK-3 task
  moves to homework; verbal partner justification stays in class.
- **Savvas terminology only.** Drop any "flatten" / "clean cross" wording —
  use only "crosses the x-axis" vs "touches and turns" (matches Savvas Ex 2).
- **Blooket = rule recall, not problem solving.** Bridge items refresh the
  rules from the previous day. Preview items are single-concept primers for
  today. Multi-step problem-solving items stay out of `blooket-pool`.

## Quick commands

```bash
# Verify environment after pull
git log --oneline -5
python qb.py                       # registry stats

# Ingest screenshots (calibration is real for 3-5)
# Just tell Claude: "ingest questionbank/images/<file>.png"

# Build a targeted Blooket CSV from the bank
python -c "
import qb
ids = [q['id'] for q in qb.select(lesson='3-5', tags=['blooket-pool','day3-multiplicity'])]
qb.to_blooket_csv(ids, 'Blooket_Day3_Multiplicity.csv')
"

# Rebuild a packet / deck after editing its generator
python build_day3_packets.py
python build_day3_slides.py
```
