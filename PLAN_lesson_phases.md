# Plan — Per-period phase mapping (Task C)

## Why

Web UI currently shows all ~90 items for a lesson code (e.g. `3-5`) in a flat list when viewing any lesson-period (`L35_P2`, `L35_P3`). The teacher cannot see which item is the Do Now for the period they opened. We need per-period phase structure.

Also: `role` on `items` is modeled as a **global** property but items are reused across periods (e.g. `3-5-savvas-q11` is `explore-practice` in one period and Do Now in another). Don't overwrite `role` — add a new table.

## Scope

Three deliverables. Each MUST be idempotent and safe to re-run.

### 1. Migration — `supabase/migrations/005_lesson_phases.sql`

```sql
CREATE TABLE IF NOT EXISTS lesson_planning.lesson_phases (
  id          SERIAL PRIMARY KEY,
  lesson_id   TEXT NOT NULL REFERENCES lesson_planning.lessons(id) ON DELETE CASCADE,
  phase       TEXT NOT NULL CHECK (phase IN (
                 'do_now','launch','explore','share_summary','exit','reinforcement'
               )),
  position    INT NOT NULL,
  item_id     TEXT REFERENCES lesson_planning.items(id) ON DELETE SET NULL,
  label       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (lesson_id, phase, position)
);

CREATE INDEX IF NOT EXISTS lesson_phases_lesson_idx ON lesson_planning.lesson_phases (lesson_id);
CREATE INDEX IF NOT EXISTS lesson_phases_item_idx   ON lesson_planning.lesson_phases (item_id);

ALTER TABLE lesson_planning.lesson_phases ENABLE ROW LEVEL SECURITY;
-- policies: public SELECT via anon, service_role ALL
-- (follow same pattern as 004_schedule.sql, which is in the repo)
```

Grant SELECT to anon, authenticated. Grant ALL to service_role. Grant USAGE on sequence to service_role.

### 2. Seed — `supabase/seed_lesson_phases.py`

Parser requirements:

- Scan every `tex/L*_teacher.tex` and `tex/APStats_*_teacher.tex` (SKIP `*_regen.tex`).
- Derive `lesson_id` from filename: `L35_P2_teacher.tex` → `L35_P2`; `APStats_6-4_P1_teacher.tex` → `APStats_6-4_P1`. Derive `lesson_code` (for ID lookups in items): `L35_P2` → `3-5`; `APStats_6-4_P1` → `APStats-6-4`.
- Identify phase-sections. Look for in this priority order:
  1. `\sectionbanner{<PHASE>}` — current canonical macro
  2. `\frameworkphaseheader{<PHASE>}{...}` — teacher-packet variant (first arg is phase name)
  3. `\phasetag{<PHASE>}` — older variant
  Normalize the raw phase string (case-insensitive, strip punctuation, unescape LaTeX) to one of the six enum values:
    - "do now" / "donow" → `do_now`
    - "launch" → `launch`
    - "explore" → `explore`
    - "share" / "summary" / "share/summary" / "share & summary" → `share_summary`
    - "exit" / "exit ticket" → `exit`
    - "reinforcement" / "optional" / "back of packet" → `reinforcement`
- Within each phase section, find `\bankitem{LABEL}{BODY}` occurrences **in order**. Use a brace-balanced extractor — regex alone is not enough because LABEL/BODY contain nested braces. See `backfill_from_teacher_tex.py:find_brace_group` for a working implementation (copy it).
- For each bankitem, emit row: `{lesson_id, phase, position (0-indexed within phase), item_id (nullable), label}`.
- Resolve LABEL → `item_id` via these rules in order, return first that matches a known registry id:
  1. **Parenthesized id**: extract `([A-Za-z0-9][\w-]+)` from inside parens; if it matches a known id, use it. (Handles `Do Now (3-5-savvas-q13)`.)
  2. **Try It N**: if LABEL contains `Try It <N>[a-z]?`, scan known ids for `<lesson_code>` membership AND substring `try-it-<N>` or `tryit-<N>`. First hit wins. (Handles both `3-5-tryit-2a` and `4-1-savvas-try-it-1-lesson-...` formats.)
  3. **Practice #N**: if LABEL contains `Practice \\#<N>` or `Practice #<N>`, try `<lesson_code>-savvas-q<N>`.
  4. **Optional #N (Savvas Practice)**: same as Practice #N — scan for `<lesson_code>-savvas-q...` matching the spelled-out number. If that fails, emit row with `item_id=NULL` and the `label` field populated.
- **Unmatched items are fine** — emit with `item_id=NULL` and keep `label`. The UI will render the label so the teacher can still see what's there.
- Print a report: rows emitted per lesson_id, unmatched labels with source file.
- Upsert to `lesson_planning.schedule`-style endpoint: `POST /rest/v1/lesson_phases` with `Prefer: resolution=merge-duplicates`. Unique key is `(lesson_id, phase, position)`.
- Support `--dry-run` (default? or explicit?) — follow the pattern in `supabase/seed_schedule.py`.

**Before running seed, the script MUST delete all existing rows for each lesson_id it's about to re-seed** — otherwise old positions from a previous run leak in. Use `DELETE /rest/v1/lesson_phases?lesson_id=eq.<id>` per lesson before insert. Keep this guarded by `--apply` (skip in dry-run).

### 3. Web UI — `web/js/api.js` + `web/js/item-detail.js` + `web/js/main.js`

**`web/js/api.js`** — add:

```js
async listPhasesForLesson(lessonId) {
  const { data, error } = await supabase
    .from("lesson_phases")
    .select("id, lesson_id, phase, position, item_id, label")
    .eq("lesson_id", lessonId)
    .order("phase")
    .order("position");
  if (error) raise("listPhasesForLesson", error);
  return data;
}
```

**`web/js/item-detail.js`** — `renderItemList(lessonId, container, onItemClick)` currently does `api.itemsForLesson(lessonOrId)`. Update it to:

1. In parallel, fetch both `itemsForLesson(lessonId)` and `listPhasesForLesson(lessonId)`.
2. If phases is empty → fall back to current flat-list rendering (with a note "No phase data yet for this period").
3. If phases is non-empty → group phases into ordered sections with headers. Use this order: `do_now`, `launch`, `explore`, `share_summary`, `exit`, `reinforcement`.
4. For each phase, list rows. Each row shows:
   - if `item_id` + `item` found in items: existing `item-row` rendering (id, role badge, dok, truncated prompt). Click → `onItemClick(item_id)`.
   - if `item_id` null: show `<label>` as a plain text row with a muted "(unmatched)" tag. Non-clickable.
5. After the phase-grouped list, show "Other items in this lesson code" as a collapsed `<details>` with the items that are in `itemsForLesson` but NOT in any phase row. This preserves access to the full bank.

**Phase header style**: use an `<h3>` with phase-specific CSS class (`phase-header phase-do_now` etc.). Keep it compact. No need for a color explosion — a left-border accent per phase is plenty. Feel free to add a small block to `web/styles/console.css` OR inline-style (match the existing style of the file).

**`web/js/main.js`** — no changes strictly required. But the call site is `renderItemList(activeLessonId, itemList, openItemDetailView)` — verify signature still matches.

## Testing

After migration applied and seed run, visiting `/?lesson=L35_P2` should show:
- **Do Now** (1 item — `3-5-savvas-q13`)
- **Launch** (Example items — may be 0 if not bankitems)
- **Explore** (5-7 items — `3-5-tryit-2a`, `3-5-tryit-2b`, practice #14/15/16...)
- **Share / Summary** (0-1 items)
- **Exit** (0 items usually — exit tickets are prose)
- **Reinforcement** (0-2 items — practice #11, #12)
- `<details>`: Other items in this lesson code — ~80 other items

L44_P1 should similarly show a Do Now, Try-Its, Practice items.

## Non-goals (do NOT do in this task)

- Do NOT normalize registry IDs (that's Task B).
- Do NOT run the teacher_answer backfill (deleted task).
- Do NOT modify `items.role` column.
- Do NOT touch the Schedule page (separate feature).
- Do NOT add edit UI for phases — read-only for now.

## Watch for these failure modes

- **Brace matching**: `\bankitem{Practice \#32 \IconStar\ DOK-3 ELECTRICAL RESISTANCE}{...}` — the label contains `\#` and `\IconStar\`. Regex like `\\bankitem\{([^}]+)\}` breaks. USE a brace-depth counter.
- **Phase detection**: sections may appear as `\sectionbanner{\IconBolt\ EXPLORE}` with icon macros in the name. Strip `\\Icon[A-Za-z]+\\s*` before normalizing.
- **L44_P1 has two Example bankitems in Launch** (deviation from one-example rule). They'll show in Launch phase. Correct behavior.
- **Some teacher packets have \textbf{BRIDGE SCRIPT}** inside a callout that looks like a header but is NOT a phase. Only look at `\sectionbanner` / `\frameworkphaseheader` / `\phasetag` — ignore text inside callouts.
- **APStats_6-4_P1** uses slightly different macro conventions — test it explicitly, report if parser fails cleanly.
- **Windows line endings**: the tex files are CRLF. Use `.read_text(encoding='utf-8')` — Python strips CRLF on text read by default.
- **Seed must not crash if registry has no items for a lesson** — emit rows with item_id=NULL + label.

## Commit message (after user-verified working)

```
Web: per-period phase mapping (Do Now, Launch, Explore, ...)

- supabase/migrations/005_lesson_phases.sql: new lesson_phases table
- supabase/seed_lesson_phases.py: parses tex/L*_teacher.tex into
  (lesson_id, phase, position, item_id, label) rows
- web: items list grouped by phase when phase data exists; falls back
  to flat list otherwise. Unmatched items render as non-clickable rows
  with their literal bankitem label.

Addresses the "I can't find the Do Now in the web UI" problem without
touching items.role (global property issue).
```
