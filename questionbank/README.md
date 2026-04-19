# Question Bank

Single source of truth for lesson-builder questions. Screenshots are
transcribed and classified by **Claude Code (this assistant) or Codex
using the built-in vision**, not by an external API call — no API credits
required.

## Layout

```
questionbank/
  images/                    PNG screenshots (committed; kept for visual questions)
  calibration/<lesson>.json  Savvas-declared DOK2/DOK3 anchors per lesson
  schemas/question.json      JSON Schema for registry entries
  registry.jsonl             one question per line, append-only
```

## Files above the directory

| File | Role |
|---|---|
| `qb.py` | Load/select/to-Blooket-CSV, no API needed |
| `qb_append.py` | Validates a JSON entry and appends to `registry.jsonl` |
| `import_blooket_csv.py` | Bulk-seeds the registry from an existing Blooket CSV |

## Workflow (in-session, no API)

1. **Populate calibration first.** Before bulk-ingesting a lesson,
   screenshot that lesson's Savvas-declared DOK2 and DOK3 questions and
   hand-curate them into `calibration/<lesson>.json`. Claude's DOK
   classifications are only as good as these anchors.
2. Drop screenshots into `questionbank/images/`.
3. Tell Claude Code (or Codex): **"ingest `questionbank/images/foo.png`"**.
   Claude will:
   - Read the image directly with the Read tool.
   - Read `questionbank/calibration/<lesson>.json` for DOK anchors.
   - Draft a JSON stub matching `schemas/question.json`.
   - Pipe it through `qb_append.py` to validate and append.
4. Review the proposed stub before it's appended (Claude will show it).
   If it's wrong, say "redo with DOK 3" or "change the topic tags" and
   Claude will re-emit without re-running vision.

## Manual ingestion (when you're alone with the terminal)

Draft the JSON yourself, then:

```bash
python qb_append.py < stub.json
# or inline:
echo '{"lesson":"3-5","prompt":"...","answers":[...],"correct":1,"dok":2,"source":"Savvas Ex 4"}' | python qb_append.py
```

The script:
- Refuses if no calibration file exists for the lesson.
- Assigns a stable id from the source hint if you don't provide one.
- Skips duplicates (same prompt text) unless you pass `--force`.
- Validates `dok`, `correct` range, and required fields.

## Using the bank

```python
from qb import select, to_blooket_csv
dok2_mult = select(lesson="3-5", dok=2, topics=["multiplicity"])
to_blooket_csv([q["id"] for q in dok2_mult], "Blooket_Day3_Multiplicity.csv")
```

Existing Blooket CSVs have already been seeded into the registry with
`dok=1` and `seeded-from-blooket` tag. Upgrade their DOK and add topic
tags as you encounter them in the wild.

## DOK calibration principle

DOK levels aren't self-evident from a prompt. We anchor them to
**Savvas-declared DOK2/DOK3 examples for the exact lesson being ingested**.
When Claude classifies a new question, it compares cognitive demand to
those anchors — not to a general rubric. Keep calibration files short
(2–5 anchors per level) and concrete.

If the anchors are placeholders, the classifications will be wrong.
Populate them first.
