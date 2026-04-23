# web/ — Phase A frontend spec

Read-only web mirror of the local Teacher Console, hosted on Vercel, data from Supabase.

## Stack (fixed — do not deviate)

- Plain static HTML + ES modules. **No Vite, no bundler, no React.** Matches `console_static/` style.
- Supabase JS v2 via `https://esm.sh/@supabase/supabase-js@2`.
- vis-network via `https://unpkg.com/vis-network/standalone/umd/vis-network.min.js`.
- No CodeMirror in Phase A — YAML viewer is `<pre>` (read-only until Phase B).

## Directory layout

```
web/
  SPEC.md             — this file
  README.md           — deploy guide (CLI, env vars)
  index.html          — lesson-list + detail SPA
  dag.html            — DAG view
  config.example.js   — template (committed; user fills config.js locally)
  config.js           — GITIGNORED. SUPABASE_URL + SUPABASE_ANON_KEY
  .gitignore
  vercel.json         — rewrites, security headers
  styles/
    console.css       — dark-palette ported from console_static/console.css
  js/
    api.js            — Supabase read wrappers (also exports pdfUrl helper)
    main.js           — entry for index.html
    lesson-list.js    — sidebar component
    item-detail.js    — detail pane
    dag.js            — entry for dag.html
```

## DOM contract (index.html)

Element IDs referenced by JS — **match these exactly**.

| ID | Purpose |
|---|---|
| `#app-header`        | Top bar |
| `#health-indicator`  | Small status dot/label for Supabase connectivity |
| `#sidebar`           | Left column |
| `#filter-input`      | Search box for lesson list |
| `#lesson-list`       | Container rendered by lesson-list.js |
| `#detail`            | Right column |
| `#detail-empty`      | Empty state (shown before a lesson is clicked) |
| `#detail-header`     | Title + action bar (hidden until a lesson is selected) |
| `#detail-title`      | Lesson title |
| `#btn-student-pdf`, `#btn-teacher-pdf`, `#btn-slides` | `<a target=_blank>` links |
| `#btn-items`         | Toggle "show items in this lesson" view |
| `#btn-yaml`          | Toggle YAML view |
| `#yaml-view`         | Wraps `#yaml-content` (pre) |
| `#item-list-view`    | Wraps `#item-list` (container for per-item cards) |
| `#item-detail-view`  | Wraps `#item-detail` (single item) |

Three detail sub-views (`yaml-view`, `item-list-view`, `item-detail-view`) are mutually exclusive — show one, hide the others.

## DOM contract (dag.html)

Same layout as current `graph/graph.html`: flex column body, `#legend` at top, `#main` flex row containing `#net` (left, fills) and `#detail` (right, 360px). No `<script>` block embedding nodes/edges — `web/js/dag.js` fetches from Supabase on load.

## API contract (js/api.js)

```js
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { SUPABASE_URL, SUPABASE_ANON_KEY } from "/config.js";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  db: { schema: "lesson_planning" },
});

export const api = {
  async listLessons()             // → [{id, cadence, title, has_pdf_*, ...}, ...]
  async getLesson(id)             // → {id, yaml_text, ...} | null
  async itemsForLesson(lesson)    // → [items in lesson, ordered by id]
  async getItem(id)               // → item | null
  async listAllItems()            // → all ~1006 items (for DAG)
  async listAllEdges()            // → all ~244 edges (for DAG)
  async checkHealth()             // → bool, does not throw
};

export function pdfUrl(lessonId, kind)  // kind: "student" | "teacher" | "slides"
```

All methods `throw` on error except `checkHealth`.

`pdfUrl` returns a raw GitHub URL pointing at the current `main` branch in this repo, e.g.
`https://raw.githubusercontent.com/robjohncolson/Lesson_planning/main/tex/L41_P2_student.pdf`.
This is a placeholder until Railway pdflatex service is wired up (Phase A step 3).

## Router (js/main.js)

No history API / no URL routing. Views are swapped by toggling `display: none` on the three detail sub-views. Sidebar selection state held in a module-scope `activeLessonId`.

## Error handling

- `api.js` throws on query errors.
- `main.js` / `dag.js` wrap calls in try/catch and show a visible banner in `#health-indicator` + body region on failure.
- No silent swallowing. No retry logic (out of scope).

## Styling

Port `console_static/console.css` palette (blue/gold/teal on white for index.html; dark for dag.html). Maintain `.btn`, `.btn-navy`, `.btn-teal`, `.btn-gold`, `.lesson-row` class conventions so code intuition transfers.

## Out of scope for Phase A step 2

- YAML editing (read-only MVP)
- Regenerate button / pdflatex (Phase A step 3: Railway)
- Tagging UI (Phase B)
- Auth / passcode (Phase B — reads are currently public)

## Phase A step 3 — tex editing + rebuild (DOM additions)

New IDs added to `index.html` inside `#tex-view`:

| ID | Purpose |
|---|---|
| `#tex-editing-label` | Displays current `lessonId / edition` being edited |
| `#btn-tex-save` | Saves tex to Railway (`PUT /tex/{id}/{edition}`) |
| `#btn-tex-rebuild` | Saves then triggers Railway build (`POST /build/{id}`) |
| `#tex-save-status` | Inline status text (Saved / Building… / error messages) |
| `#tex-log` | Scrollable build log pane; hidden when empty |

Config addition: `RAILWAY_URL` exported from `config.js` / `config.example.js`.
Passcode stored in `localStorage` under key `lp.passcode` (`web/js/passcode.js`).

## Phase 1 — usernames + slides editing + last-edited display

### New DOM IDs

| ID | Purpose |
|---|---|
| `#btn-tex-slides` | Opens slides `.tex` editor (adjacent to Student/Teacher .tex in toolbar) |
| `#tex-last-edited` | Span inside `.tex-toolbar`; shows "Last edit: Name · time" or empty |

### `/js/username.js`

Exports `{ username }`. Storage key: `lp.username` in `localStorage`.
- `username.get()` — returns stored name or prompts until valid; strips whitespace; rejects empty, >40 chars, or strings containing `\r`/`\n` (HTTP header safety). Returns `""` if user cancels prompt.
- `username.clear()` — removes stored name; next `.get()` re-prompts.

### `api.getLastAudit(lessonId)`

Queries `lesson_planning.audit` (same supabase client, schema already scoped):
```
select action, changed_at, changed_by from audit
where table_name = 'lessons' and row_id = lessonId
order by changed_at desc limit 1
```
Returns `{ action, changed_at, changed_by }` or `null`. **Never throws** — catches all errors and network failures, returning `null` silently.

### `X-User-Name` header

`saveTex` and `rebuildPdf` include `"X-User-Name": username.get()` alongside `X-Passcode`. Railway forwards this to the Supabase audit trigger as the `x-user-name` request header, which the trigger stores in `audit.changed_by`.

## Phase 2 — Realtime presence

### New DOM IDs

| ID | Purpose |
|---|---|
| `#tex-presence` | Span inside `.tex-toolbar`; shows "N editing: X, Y" when others are present (hidden when alone) |
| `#tex-remote-banner` | Banner above `.tex-toolbar` inside `#tex-view`; shown when a remote save lands on the active edition |
| `#remote-banner-msg` | Text inside the banner ("Someone just saved {edition}.tex") |
| `#btn-take-theirs` | Replaces textarea content with `pendingRemoteValue`; clears `texDirty` |
| `#btn-dismiss-banner` | Hides banner; discards `pendingRemoteValue` |

### Channel naming

One channel per open lesson: `lesson:{lessonId}` (e.g. `lesson:L41_P2`).

### Presence payload shape

`{ username: string, joined_at: ISO-string }` — tracked on `SUBSCRIBED`.

### `onRemoteSave` firing rule

Fires only when the changed field matches `tex_{activeTexEdition}` (e.g. `tex_student`). Changes to other editions or `yaml_text` while a different edition is open are silently ignored. Own-save echoes are filtered when `new_value === texContent.value && !texDirty`.
