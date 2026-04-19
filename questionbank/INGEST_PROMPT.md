# Question-Bank Ingestion Procedure

When the user says **"ingest `<image>`"**, **"add this to the question bank"**,
or similar — follow these steps.

## Steps

1. **Resolve the lesson code** from the image filename (pattern `N-N`, e.g.
   `3-5`). If the filename has none, ask the user.
2. **Read the calibration file** `questionbank/calibration/<lesson>.json`.
   If it does not exist, stop and tell the user to populate it first. Do
   not invent DOK labels without anchors.
3. **Read the image** with the Read tool.
4. **Draft a JSON entry** with these fields:
   - `lesson` — lesson code, e.g. `"3-5"`
   - `source` — best guess: `"Savvas Practice #N"`, `"Savvas Example N"`,
     `"Lesson Quiz"`, etc.
   - `image` — path relative to repo root, e.g. `"questionbank/images/foo.png"`
   - `has_visual` — true only if solving requires reading a graph/figure
   - `prompt` — transcribed text. Preserve math as plain text:
     `^` for exponents, `√` for roots, proper minus `−` (U+2212), `·` for
     multiplication where useful.
   - `answers` — list of MC options in order. Empty if open-response.
   - `correct` — 1-based index into `answers`, or null if not visible.
   - `dok` — 1, 2, or 3. **Calibrate by comparing to the anchors** in the
     calibration file. Pick the anchor your question most resembles.
   - `dok_rationale` — one sentence citing the anchor you compared to.
   - `topics` — tags drawn from `topic_vocabulary` in the calibration file.
     Add a new tag only if no existing tag fits.
   - `tags` — optional free-form (e.g. `"error-analysis"`, `"sat-style"`).
   - `notes` — misconceptions, common stalls. Optional.
5. **Show the draft to the user** as fenced JSON before appending.
6. **Append** by piping the JSON to `qb_append.py`:
   ```
   echo '<json>' | python qb_append.py
   ```
   Or write the JSON to a temp file and pass the path. The script
   validates required fields, checks calibration exists, and refuses
   duplicate prompts (unless `--force`).
7. **Confirm the append** by showing the assigned id.

## What NOT to do

- Do not call any external API. All vision happens via the Read tool on
  the image file.
- Do not bypass `qb_append.py` by writing to `registry.jsonl` directly.
  The append script does validation and dedup.
- Do not guess DOK when the calibration file still has `placeholder`
  text in its anchors — stop and tell the user to populate real anchors.
- Do not invent new topic tags without checking `topic_vocabulary` first.

## Batch ingestion

For "ingest all of these" with multiple images:
1. Process them one at a time (Read image → draft JSON → append).
2. Do not parallelize via subagents; each append depends on the
   previous `taken` id set, and the registry is append-order sensitive.
3. At the end, print a summary: total appended, skipped, any DOK-3
   candidates the user might want to double-check.
