# Question Bank

Single source of truth for lesson-builder questions. Ingest textbook screenshots,
transcribe + classify with Claude vision, select by DOK / topic / lesson for
packets, slides, and Blooket CSVs.

## Layout

```
questionbank/
  images/                    PNG screenshots (committed; kept for visual questions)
  calibration/<lesson>.json  Savvas-declared DOK2/DOK3 anchors per lesson
  schemas/question.json      JSON Schema for registry entries
  registry.jsonl             one question per line, append-only
```

## Workflow

1. Drop screenshots into `questionbank/images/`. Filename is free-form; the
   ingest script assigns a stable `id`.
2. **Before bulk-ingesting a lesson**, screenshot and hand-curate that
   lesson's Savvas-declared DOK2 and DOK3 questions into
   `calibration/<lesson>.json`. These are the calibration anchors.
3. Run `python ingest_question.py <image>...` — Claude vision transcribes
   the prompt + answer choices and proposes DOK / topic tags by comparing
   against the calibration anchors.
4. Review the proposed JSON stub printed to stdout. If it looks right, the
   script appends to `registry.jsonl`. Otherwise rerun with `--edit` or
   edit the line in place.
5. Builders (packets, slides, Blooket CSVs) import `qb` and select by
   filter:

```python
from qb import select, to_blooket_csv
dok2_mult = select(lesson="3-5", dok=2, topics=["multiplicity"])
to_blooket_csv([q["id"] for q in dok2_mult], "Blooket_Day3_Multiplicity.csv")
```

## DOK calibration principle

DOK levels aren't self-evident from a prompt. We anchor them to
**Savvas-declared DOK2/DOK3 examples for the exact lesson being ingested**.
The ingest script sends those anchors to Claude as reference before asking
it to classify a new question. This keeps judgments consistent with how the
textbook itself labels rigor.

If no calibration file exists for a lesson, ingest will refuse and ask you
to populate it first.

## Commands

| Task | Command |
|---|---|
| Ingest one or more screenshots | `python ingest_question.py images/3-5_ex4.png [...]` |
| Ingest a whole folder | `python ingest_question.py images/*.png` |
| Import an existing Blooket CSV into the registry | `python import_blooket_csv.py Blooket_Day3_Multiplicity.csv --lesson 3-5 --default-dok 1` |
| Select questions programmatically | `from qb import select` |
| Export Blooket CSV from registry | `from qb import to_blooket_csv` |
| List all lessons with questions | `python -c "from qb import lessons; print(lessons())"` |
