# Continuation Prompt — Lesson_planning

Paste this into the next Claude Code / Codex session on the work machine
after `git pull`.

---

## Where we are (as of 2026-04-19, late session)

### Lesson cadence — Algebra 2, Topic 3-5 (Zeros of Polynomial Functions)

8-day packet. Current pacing:

| Packet day | Content | Status |
|---|---|---|
| Day 1 | What is a zero? + sign charts (Example 1, Try It 1a/1b) | **Taught — took 3 class periods.** Gallery walk + Leap were skipped. Optional Period A Monday DOK-3 supplement handout built (`Day_1_Period_A_Supplement_The_Leap.docx`). |
| Day 2 | Graphing from Factored Form | **Reworked to single-DOK3 spine.** Sole driver: Reverse Engineering (zeros + point → equation). 57 min. Practice #13 moved OUT (now Day 3 territory). |
| Day 3 | The Magic of Multiplicity | **Reworked to single-DOK3 spine.** Sole driver: Tonya Error Analysis. 55 min. Practice items pulled from bank. |
| Day 4 | Real & complex zeros | Not yet built |
| Day 5–8 | Modeling → equations → inequalities → assessment | Not yet built |

**Day 1 stretch evidence:** budgeted 1 period, ran 3. Use ~1.4× stretch
factor when sizing future days for this population.

### The design rule (locked in across all reworked days)

After observing Day 1 stretch + reviewing Day 2 against the user's intent,
every day from Day 2 onward follows the **single-DOK3 spine**:

1. **Entrance ticket (5 min, DOK 2)** — primes the DOK-3. Two or three
   prompts. Breathable page (no crowded sheets).
2. **Blooket login + game (2 + 7 min, DOK 1)** — PURE rule recall. Habits
   of mind from previous day + rules needed for today. **Procedural
   factoring items are banned** (DOK 2 problem solving doesn't belong on
   flashcards).
3. **Launch (~8–12 min, DOK 2)** — surface entrance-ticket predictions,
   name the new concept, set up the driver.
4. **The DOK-3 driver (15–25 min, DOK 3)** — ONE self-contained task. All
   rules the student needs are printed on the page so they can pick it up
   and work without waiting on the teacher. Teacher circulates with
   prompts only.
5. **Practice (optional, 10 min, DOK 2)** — Try It items consolidating
   the day's procedure. Pulled from the bank when Savvas anchors exist.
6. **Summary exit ticket (4–5 min, DOK 1–2)** — recap of what was learned.
   **NOT a CER** — walk-out task should summarize, not generate new
   argument. CER practice migrates to HW or next-day Do Now.

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
| `regen_blooket_csvs.py` | One-shot regenerator for Day 2 + Day 3 Blooket CSVs |
| `questionbank/INGEST_PROMPT.md` | The procedure Claude follows on ingest requests |

#### Tag scheme (lesson 3-5)

- `blooket-pool` — DOK 1 only; safe to export to Blooket warm-up CSV
- `do-now-bridge` — recall of previous-day rules (target ≥25% of warm-up)
- `today-preview` — single-concept preview of today's lesson (≈75% of warm-up)
- `seeded-from-blooket` — historical provenance (no behavior)
- `derived-from-day1` / `derived-from-teacher-prompt` — provenance for new bridge items
- `savvas-practice` / `try-it` / `lesson-quiz` / `rti-extend` / `rti-support` — Savvas source type
- `day{2,3,4,5,6,7}-...` — day binding for lesson selection

#### Blooket pool ratios (current, after re-tag)

- **Day 2 pool:** 16 items (5 bridge / 11 preview = 31% bridge)
- **Day 3 pool:** 27 items (7 bridge / 20 preview = 26% bridge)

5 items dropped from `blooket-pool` on 2026-04-19: procedural factoring
items (`*-q6` through `*-q10` in Day 2 graphing). These are DOK 2 problem
solving and don't belong on flashcards. They remain in the registry with
a `design-note` field explaining the removal.

Bridge items are rule-recall (NOT problem-solving), per the design rule
that Blooket runs right after the Do Now and should refresh rules that
make today's problems easier.

### Bank-driven packet builders

`qb.py` now exposes `get_for_packet(ids)` — fixed-order lookup that
raises `KeyError` if any id is missing (so a packet build fails loudly
rather than rendering placeholders).

`build_day3_packets.py` is wired to pull Practice items A and B from
`PRACTICE_IDS = ["3-5-tryit-2a", "3-5-tryit-2b"]`. The student packet
shows the Savvas polynomial; the teacher packet shows the bank's
`correct` field as the answer key plus `dok_rationale` plus the bank id
for traceability. Includes a tiny mojibake repair (fixes `â†’` → `→`
from the bank's earlier UTF-8/cp1252 ingest bug — bank stays unchanged
for round-tripping).

`build_day2_packets.py` was NOT migrated to bank — its DOK-3 driver
(Reverse Engineering) is custom prose, not a bank-anchored Try It. Day 2
stays bespoke.

### Materials on disk (top-level)

| File | Purpose |
|---|---|
| `Day_1_Student_Packet_v3 (1).docx`, `Day_1_Teacher_Packet.docx` | Day 1 (taught) |
| `Day_1_Period_A_Supplement_The_Leap.docx` | Optional Period A Monday DOK-3 handout (one page, self-contained) |
| `Day_2_*` (Do Now, Student, Teacher, Slides, Pacer) | Day 2 lesson — single-DOK3 spine |
| `Day_3_*` (Do Now, Student, Teacher, Slides, Pacer) | Day 3 lesson — single-DOK3 spine |
| `Blooket_Day{2,3}_*.csv` | Targeted warm-ups, regenerated from bank via `regen_blooket_csvs.py` |
| `aga_24_a2_na_0305_lq.docx` | Savvas Lesson Quiz 3-5 source |
| `Revised_Zeros_of_Polynomials_8-Day_Lesson_Packet_FINAL.docx` | Master 8-day plan |
| `build_day{1_supplement,2,3}_packets.py`, `build_day{2,3}_slides.py` | Generators |
| `regen_blooket_csvs.py` | Blooket CSV regenerator + ratio reporter |

## What's open

1. **Build Day 4 materials (Real & Complex Zeros).** Anchored to Savvas
   Example 3. Apply the same single-DOK3 spine. Bank already has Try It
   3a/3b (`3-5-tryit-3a`, `3-5-tryit-3b`), RtI extension items, and full
   answer keys — wire Practice from bank using the Day 3 pattern
   (`PRACTICE_IDS = [...]` + `qb.get_for_packet()`).
2. **Identify the Day 4 DOK-3 driver.** Likely candidate: "Why must
   non-real complex roots come in conjugate pairs?" — explain using a
   real-zero count + degree argument. Self-contained on the page with
   the conjugate-pair rule + degree rule + a worked synthetic-division
   example.
3. **Build Day 4 Blooket CSV.** Once Day 4 items are tagged
   `day4-real-complex` + `blooket-pool` + bridge/preview, extend
   `regen_blooket_csvs.py` to emit a third CSV.
4. **Lesson 3-6 ingest (eventually).** When 3-6 starts, repeat the
   workflow: create `calibration/3-6.json` with placeholder anchors,
   screenshot the Savvas Item Analysis table, replace placeholders,
   ingest practice + teacher addendums. Same `blooket-pool` /
   `do-now-bridge` / `today-preview` scheme.

## Constraints & preferences worth remembering

- **Single-DOK3 spine.** One DOK-3 driver per day. All info self-contained
  on the page. NEVER bundle two DOK-3 tasks in one period — Day 1's
  3-period stretch was caused by exactly that.
- **Summary exit, not CER.** Walk-out tasks recap the day. CER writing
  in 5 min is unrealistic; the DOK-3 generative work happens earlier.
- **Blooket = pure rule recall (DOK 1).** Habits of mind only. No
  procedural factoring. No problem solving.
- **Don't crowd the page.** Breathable whitespace > dense scaffolding.
  User explicitly flagged "483409808439 tasks all written in a crowded
  sheet" as the failure mode.
- **No API credits.** All vision / transcription runs inline in Claude
  Code or Codex sessions. Do not scaffold anything that calls the
  Anthropic API.
- **Windows + MSYS2 shell.** UTF-8 BOM on Blooket CSVs; reconfigure stdout
  on any Python script that prints unicode math
  (`PYTHONIOENCODING=utf-8` or `sys.stdout = io.TextIOWrapper(...)`).
- **Project CLAUDE.md** requires GitNexus impact analysis before editing
  symbols — for code edits only, not for static content (packets, CSVs,
  JSONL).
- **Framework mapping** (from `DOKframework.txt`): every lesson phase
  carries explicit `[Framework]` + `[DOK]` tags. Keep that convention
  for Day 4+.
- **Release valves are ordered.** When time is short, follow the order
  listed in each teacher packet's "REALISTIC PACING" section. Never cut
  the Summary Exit — it's the only artifact that documents learning.
- **Savvas terminology only.** Drop any "flatten" / "clean cross"
  wording — use only "crosses the x-axis" vs "touches and turns" (matches
  Savvas Ex 2). Day 3 packets accept "kisses / bounces / turns" for ELL
  flexibility but written instruction uses Savvas language.
- **Day 1 evidence:** budget × 1.4 = realistic time for this population.

## Quick commands

```bash
# Verify environment after pull
git log --oneline -5
python qb.py                       # registry stats

# Rebuild Day 2 / Day 3 materials after editing a builder
python build_day2_packets.py
python build_day2_slides.py
python build_day3_packets.py
python build_day3_slides.py
python build_day1_supplement.py

# Regenerate Blooket CSVs from the bank (with ratio reporting)
python regen_blooket_csvs.py

# Ingest screenshots (calibration is real for 3-5)
# Just tell Claude: "ingest questionbank/images/<file>.png"
```
