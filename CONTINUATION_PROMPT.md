# Continuation Prompt — Lesson_planning

Paste this into the next Claude Code / Codex session on the work machine
after `git pull`.

---

## Where we are (as of 2026-04-18)

### Lesson cadence — Algebra 2, Topic 3-5 (Zeros of Polynomial Functions)

8-day packet, 50–65 min periods. Current pacing:

| Packet day | Content | Status |
|---|---|---|
| Day 1 | Hook / intro to zeros | Taught (pre-break) |
| Day 2 | Graphing from Factored Form | **Next lesson — Monday A, post-April-break** |
| Day 3 | Multiplicity | Built but not taught — runs the day AFTER Day 2 |
| Day 4 | Real & complex zeros | Not yet built |
| Day 5–8 | Modeling → inequalities → synthesis → assessment | Not yet built |

**Class periods** this cycle:
- Monday A: 7:45–8:50 (65 min) — Day 2 lesson
- Tuesday F: 7:45–8:50 (65 min) — Day 3 lesson (Multiplicity)
- Tuesday A: 8:55–9:50 (55 min) — Day 3 lesson

Day 3 was sized for the 55-min period (fits F and A); 65-min days spend
the extra 10 min on Desmos depth + written Tonya CER, not new tasks.

### Materials on disk

| File | Purpose |
|---|---|
| `Day_2_*` (Do Now, Student, Teacher, Slides, Pacer) | Monday A lesson |
| `Blooket_Day2_GraphingFactoredForm.csv` | 20 Q targeted Day 2 warm-up |
| `Day_3_*` (Do Now, Student, Teacher, Slides, Pacer) | Tuesday lessons |
| `Blooket_Day3_Multiplicity.csv` | 24 Q targeted Day 3 warm-up |
| `Blooket_Import_Zeros_of_Polynomials.csv` | 40 Q generic bank |
| `Revised_Zeros_of_Polynomials_8-Day_Lesson_Packet_FINAL.docx` | Master 8-day plan |
| `build_day{2,3}_packets.py`, `build_day{2,3}_slides.py` | Generators |

### Question bank (new this session)

Scaffold is live at `questionbank/`. Key pieces:

| File | Role |
|---|---|
| `qb.py` | Load, select, export Blooket CSV |
| `qb_append.py` | Validate JSON on stdin, append to registry |
| `import_blooket_csv.py` | Bulk-seed registry from an existing Blooket CSV |
| `questionbank/registry.jsonl` | 44 entries seeded from Day 2 + Day 3 Blookets (all `dok=1`, tag `seeded-from-blooket`) |
| `questionbank/calibration/3-5.json` | **HAS PLACEHOLDER ANCHORS — must be replaced before ingesting anything new** |
| `questionbank/schemas/question.json` | JSON Schema |
| `questionbank/images/` | Screenshots go here |
| `questionbank/INGEST_PROMPT.md` | The procedure Claude follows on ingest requests |
| `questionbank/README.md` | Usage overview |

**Ingest workflow (no API credits needed):** Claude Code or Codex reads
the screenshot inline via the Read tool, reads the lesson's calibration
file, drafts a JSON stub, shows it for approval, then pipes it through
`qb_append.py`. Detailed steps in `questionbank/INGEST_PROMPT.md`.

## What's open

1. **Replace placeholder anchors in `questionbank/calibration/3-5.json`.**
   The file currently has two placeholder DOK2 and two placeholder DOK3
   anchors. These must be real Savvas-declared problems before any new
   screenshots are ingested — otherwise DOK classifications will be
   miscalibrated. Easiest flow: screenshot the Savvas DOK2/DOK3 problems,
   ask Claude to transcribe them into the JSON anchors directly.

2. **Backfill DOK and topic tags on the 44 seeded registry entries.**
   All are currently `dok=1` with empty `topics`. Walk the registry once
   calibration anchors are real; bump DOK on the harder questions and
   add topic tags (multiplicity, factoring, sign-chart, etc.). Can be
   done inline via a script or by hand.

3. **Day 4 materials (Real & Complex Zeros).** Not yet built. Will run
   after Day 3 on whichever class day comes next. Use
   `build_day3_packets.py` and `build_day3_slides.py` as templates;
   revised packet tables 23–27 describe Day 4 content.

4. **Migrate builders to pull from the bank (low priority).** Builders
   currently hardcode question text. Once the registry has real DOK tags,
   `build_day3_packets.py` could call `qb.select(lesson="3-5", dok=2,
   topics=["multiplicity"], limit=4)` for the Try It section. Do lazily.

## Constraints & preferences worth remembering

- **No API credits.** All vision / transcription runs inline in
  Claude Code or Codex sessions. Do not scaffold anything that calls
  the Anthropic API.
- **Windows + MSYS2 shell.** Use UTF-8 BOM on CSVs written for Blooket;
  reconfigure stdout on any Python script that prints unicode math.
- **Project CLAUDE.md** requires GitNexus impact analysis before
  editing symbols — honored for code edits, not needed for static
  content files (packets, CSVs, JSONL).
- **Framework mapping** (from `DOKframework.txt`): every lesson phase
  carries explicit `[Framework]` + `[DOK]` tags. Keep that convention
  for Day 4+ materials.
- **Release valve pattern**: when time is short, the written CER on the
  DOK-3 task moves to homework; the verbal partner justification stays
  in class. Applied across Day 2 and Day 3. Carry forward.

## Quick commands

```bash
# Verify environment after pull
git log --oneline -5
python qb.py                       # prints registry stats

# Ingest screenshots (once calibration is real)
# Just tell Claude: "ingest questionbank/images/<file>.png"

# Build a targeted Blooket CSV from the registry
python -c "
import qb
ids = [q['id'] for q in qb.select(lesson='3-5', tags=['day3-multiplicity'])]
qb.to_blooket_csv(ids, 'out.csv')
"

# Rebuild a packet / deck after editing its generator
python build_day3_packets.py
python build_day3_slides.py
```

## Recent git history (for orientation)

```
6def3da Reframe ingest for Claude-Code-native workflow (no API credits needed)
779109e Scaffold question bank: registry, calibration, ingest, Blooket round-trip
a2e67b9 Add targeted Day 2 Blooket CSV
0c15759 Add Day 3 Multiplicity lesson materials
ffab7df blooket 3-5-1
ef2471f ap stats 2019 practice exam
998db8d Split Do Now from packet, add CER scaffold, build slide deck
fe3c77b Add DOKframework.txt as canonical lesson-plan framework reference
```
