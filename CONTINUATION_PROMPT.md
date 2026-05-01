# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

## READ THESE FIRST (don't re-derive what's already written)

Before you ask "what's going on in this repo?", check these sources:

- **`git log --oneline -30`** — recent work, in order. Commit messages are detailed.
- **`CLAUDE.md`** (this repo) — hard rules, framework phases, class context, Klimsara pattern, LaTeX-canonical pivot, standard toolchain.
- **`obsidian-wiki/` at `C:/Users/rober/Downloads/Projects/obsidian-wiki/`** — persistent domain knowledge. Read `wiki/hot.md` first (~500 tokens) for recent context; `wiki/index.md` if more needed.
- **`tex/preamble.sty` + `tex/beamer_preamble.sty`** — shared LaTeX + Beamer style packages (all macros live here).
- **`tagging/BATCH_SYNTHESIS.md` + `graph/`** — curriculum DAG, echo chains, skill-bridge coverage, chain-3+ no-go decision.
- **`lessons/*.yaml` + `build_lesson_from_yaml.py`** — YAML-driven generator. Proof-of-concepts: `L41_P2.yaml` (Algebra 2), `APStats_6-4_P1.yaml` (cross-subject vitality), `L44_P1.yaml` (back-extracted; see `L44_P1_back_extraction_notes.md`).
- **`web/SPEC.md`** — the shared contract for the Vercel-hosted frontend (DOM ids, api.js surface, Phase 1/2/3 notes).
- **`railway/README.md`** — deploy + env var sheet for the pdflatex build service.
- **`supabase/README.md` + `supabase/migrations/*.sql`** — schema, run-order, seed script, migration history.

**This file carries only what's NOT in those sources:** currently-pending tasks, durable failure modes, and pointers. It is NOT a repo tour.

## Where we are

LaTeX is canonical for student-facing output. YAML → tex → PDF pipeline proven on L41_P2 and APStats. Every shipped Algebra 2 lesson has matching student/teacher packets, a beamer projection deck, and a pacer HTML.

**The collaborative web app ships and runs (as of 2026-04-23):**

- **Supabase** (project `bzqbhtrurzzavhqbgqrs`, schema `lesson_planning`) holds items, edges, lessons, audit. `tex_student/tex_teacher/tex_slides` columns on `lessons` are the source of truth for tex source. RLS: public SELECT, writes via service_role only.
- **Railway** (`https://lessonplanning-production.up.railway.app`) runs a FastAPI + TeXLive service that rebuilds PDFs (`POST /build/:id`) and takes tex writes (`PUT /tex/:id/:edition`). Auth: shared `REBUILD_PASSCODE` header `X-Passcode`; writer identity via `X-User-Name` → forwarded to PostgREST → captured by the audit trigger.
- **Vercel** (`https://lessonplanning-lyart.vercel.app`) serves the static frontend. Plain HTML + ES modules, no bundler. Supabase Realtime for presence + "someone just saved" banners. Sha-based optimistic concurrency on save → 3-pane merge view on conflict. **Deploys on push to `main` via the Vercel GitHub integration** — project → Settings → Git, root directory `web/`. Do NOT use `vercel --prod` manually; push to main instead so the source-of-truth matches what's deployed.
- **Local Flask console** (`console.py`) is still the fastest path for the owner. Localhost-only; not shared.

**For current artifact counts, shipped decks, or "what's in tex/", run `ls tex/` and `git log --oneline` — do not re-summarize here, it drifts.**

## Active toolchain pointers

| Purpose | File |
|---|---|
| LaTeX style | `tex/preamble.sty`, `tex/beamer_preamble.sty` |
| YAML → tex generator | `build_lesson_from_yaml.py` |
| Registry accessor | `qb.py` |
| Registry validator | `qb_append.py` |
| Registry encoding fix | `fix_registry_mojibake.py` |
| DAG diagnostics | `qb_diagnose.py` → `graph/skill_bridge_gaps.md` + `graph/nominal_rehearsals.md` + `graph/redundant_practice.md` |
| Polish worksheets | `qb_polish_worksheet.py` → `graph/polish/` |
| Local Flask console | `console.py` + `console_static/` + `INSTALL.md` |
| Web frontend (Vercel) | `web/` (see `web/SPEC.md`) |
| Railway pdflatex service | `railway/` (see `railway/README.md`) |
| Supabase schema + seed | `supabase/schema.sql`, `supabase/seed.py`, `supabase/migrations/*.sql` |
| One-off PDF bulk upload | `supabase/upload_pdfs.py` |
| Parallel dispatch (legacy) | `dispatch/parallel-batch.manifest.json` + `dispatch/prompts/latex-scale/` |

## Open tasks (as of 2026-04-30)

**Current pacing (re-baselined 2026-04-30, see `supabase/seed_schedule.py`):**
- Still on **L35_P2** as of 4/30 (behind original plan). P2 stretches through Thu 5/7.
- **Fri 5/8 F = TEACHER OBSERVATION** = `L35_P3_obs` (canonical P3, gradual-release Launch + DOK-3 Mystery Graph). The obs files were originally misnamed `L35_P2_obs_*` — renamed in commit `7573061`.
- Week of 5/11 (Mon-Wed): L35_P3 continuation (Storage Box DOK-3 follow-up, uses existing non-obs `L35_P3_*` tex).
- **Thu 5/14 = Topic 3 Assessment** for both periods (compressed onto one day, was 5/15 F + 5/18 A).
- **L41 (full 3-period) starts F 5/15 / A 5/18**, runs through ~5/27.

**Time-critical — user handles:**
- Push the rebaselined schedule live: `python supabase/seed_schedule.py` (no `--dry-run`) once SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set. Schedule is idempotent upsert on (class_date, period).
- Rotate the Supabase service-role key (it's been pasted in chat logs multiple times). Dashboard → Settings → API → Reset. Then `railway variables --set "SUPABASE_SERVICE_ROLE_KEY=<new_one_line>"`.
- Delete the Railway project access token `cc-debug-session` at https://railway.com/account/tokens once debugging sessions wrap.

**Completed 2026-04-22 (local Flask console Phase 2):**
- ✅ CodeMirror 6 bundled locally (`console_vendor/` → `console_static/vendor/codemirror.js`, 412 KB min.).
- ✅ Diff viewer — regen endpoint returns unified diff; frontend shows tabbed modal with colored +/- lines.
- ✅ Curriculum DAG viz — reused `graph/graph.html`, console opens with lesson focus param.
- ✅ Teacher-answer backfill (88 → 128 rows with `teacher_answer`).
- ✅ Generator schema extensions: `kind: raw_tikz` + `section_notes:` optional fields.

**Completed 2026-04-23 (collaborative web app):**
- ✅ **Phase A step 2**: Vercel read-only mirror (lesson list, YAML viewer, items browser, DAG from Supabase). Commit `c441f33`.
- ✅ **Phase A step 3**: Railway pdflatex service + tex editor + save/rebuild flow. Shared `LEHS` passcode. Commit `1ce4687`.
- ✅ **Phase 1** (identity): usernames (`web/js/username.js`, X-User-Name header), slides .tex editor, last-edited-by line from audit trail. Commit `af48a12`.
- ✅ **Phase 2** (presence): Supabase Realtime per-lesson channel. "X editing" badge + remote-save banner with Take theirs / Keep mine. Commit `799fdca`.
- ✅ **Phase 3** (merge): sha-based optimistic concurrency on save. 409 → 3-pane merge view (Theirs | Yours on top, editable Merge below). Commit `6864f49` + `86d11e5` (layout polish).
- ✅ Bulk-uploaded 54 existing PDFs (18 × student/teacher/slides) to Supabase Storage `lesson-pdfs` bucket via `supabase/upload_pdfs.py`.

**Backlog — pick when idle:**
- **Phase 4 voting** — explicit voting on conflicts (Brian vs Peter, quorum resolution). Specified but deferred — same-room sessions can resolve by talking. Skip unless remote/async collab emerges.
- **Standalone diff viewer in the web app** — diff rendering already exists inside the merge view; could be exposed as its own button ("see what changed since I opened this"). ~30 min.
- **Google OAuth + RLS gating** — currently the anon Vercel URL exposes all `teacher_answer` fields + teacher tex with answer keys. Safe to share with trusted staff only; NOT safe to link from a student-reachable page. ~2-3 hours.
- **Side-by-side PDF preview under tex editor** — see rebuild without leaving the editor view. ~30 min.
- **Autosave on pause** — debounced 3-second idle save, so Rebuild feels instant. ~20 min.
- **New-subject scale-out** (APStats or Algebra 1). Generator is subject-agnostic. Author-when-teaching.

**Deferred (harmless):**
- Topic 5 `-2`-suffixed registry rows (85 duplicate ids, collapsed by seed last-writer-wins).
- Retired Topic 3 assessment shells (Q1/Q3/Q4/Q7/Q9/Q11 point at retired lessons, inert).
- Chain-3+ scripts (filed as no-go per `graph/chain3plus_research.md`).

## Durable failure modes (re-read before dispatching)

### LaTeX + dispatch

1. **`owned_paths` for LaTeX must be glob `tex/{name}.*`** — pdflatex emits `.aux/.log/.pdf/.out` alongside `.tex`; single-file ownership rejects them.
2. **MiKTeX-sandbox ownership trap** — Codex agents sometimes redirect MiKTeX cache into `tex/.miktex-sandbox/`, which trips ownership. Fallback: single-shot `cross-agent.py`.
3. **`parallel-codex-runner` discards uncommitted worktree on failure** — always check `codex/*` branches BEFORE cleanup to salvage work.
4. **Answer-leak in format-conversion prompts** — format converters/renderers must keep symbolic form (`w = k/f`, `g(x) = 1/(x-h) + k`); never substitute computed answers into student-facing prompt content. Every LaTeX/Beamer/pacer dispatch prompt now carries this guardrail.
5. **Cross-agent dispatch to Codex has 600s hard timeout** — split or use `parallel-codex-runner` with a manifest.
6. **Cross-agent runner crashes on non-UTF-8 bytes in codex output** — Windows-1252 bytes (e.g. 0x92 = typographic apostrophe) in the codex response break the runner's JSON decode. When reviewing, self-review is a reliable fallback.

### Windows / Git Bash / PowerShell

7. **`browser-harness` doesn't work on Windows** — AF_UNIX unavailable. Use Selenium + Edge headless. Template in `~/.claude/projects/.../memory/reference_browser_automation_windows.md`.
8. **Pacer HTMLs are JS-rendered** — can't grep static HTML for rendered content. Use Selenium smoke-test pattern.
9. **Windows terminal mojibake** — math symbols display wrong in stdout; FILES are fine. Use `pdftotext -enc UTF-8` for text checks.
10. **Registry mojibake survives ingestion** — run `python fix_registry_mojibake.py --apply` after any new item ingest.
11. **`pkill -f` is unreliable on Git Bash / Windows** — it reports success but Windows python.exe keeps running. Use `taskkill //F //IM python.exe`. Better: track PIDs explicitly.
12. **PowerShell line continuation (`` ` `` + newline) embeds literal `\n` in env var values.** If you `railway variables --set "KEY=val1\ncontinued"` across lines, the value includes a newline. `requests` library rejects headers with `\n` (HTTP header injection guard) → service 500s with `InvalidHeader`. Always paste secrets as ONE LINE.

### Web stack specifics

13. **Railway CMD must be shell-form so `$PORT` expands.** Exec-form `CMD ["uvicorn","--port","$PORT"]` passes literal `$PORT` to uvicorn. Use `CMD uvicorn ... --port ${PORT:-8080}`. `startCommand` in `railway.toml` also reserves literal unless wrapped in `/bin/sh -c`.
14. **`railway.toml` must sit at repo root** (where `railway init` runs), not inside `railway/`. Railway CLI looks at the project root for config.
15. **Railway `redeploy` re-uses the previous image** — if you need a code change to take effect, run `railway up`, not `redeploy`.
16. **Supabase schemas must be added to "Exposed schemas"** (Project Settings → Data API) before PostgREST will route to them. Default is `public, graphql_public`. Add `lesson_planning`.
17. **PostgREST caps `.select()` at 1000 rows by default.** `items` has 1006. `api.listAllItems` and `listAllEdges` paginate via `.range()` — preserve that pattern for any large table.
18. **supabase-py's bundled httpx client negotiates HTTP/2 → intermittent `StreamReset` errors against Supabase's Cloudflare edge.** Railway server uses plain `requests` (HTTP/1.1) instead. If you re-introduce supabase-py, expect flakes.
19. **Supabase Storage `upload` wants `x-upsert: "true"` as a string**, not bool `True`. Passing `{"upsert": True}` sometimes silently fails the upsert path.
20. **Audit trigger reads x-user-name from two places.** `current_setting('request.header.x-user-name', true)` works only with specific PostgREST flags; on Supabase you need the fallback via `current_setting('request.headers', true)::jsonb->>'x-user-name'`. Migration 002 sets both.
21. **Realtime needs REPLICA IDENTITY FULL** on tables where you want OLD+NEW in UPDATE payloads. Migration 003 applies this on `lesson_planning.lessons`.
22. **Vercel default respects `.gitignore`.** `web/.gitignore` ignores `config.js`. First `vercel --prod` will miss the config unless you either (a) commit `config.js` (anon key is safe to embed) or (b) remove it from `.gitignore` / add a prebuild step. Currently: committed per Phase A step 2 README option 1.
23. **Vercel static deploy routes `/dag.html` through a 308 → `/dag`** because of `cleanUrls: true`. Both resolve; the internal nav href uses `/dag.html` for now.
24. **GitHub raw PDFs force-download** (Content-Disposition: attachment); jsdelivr CDN serves them inline. `pdfUrl` used to fall back to jsdelivr; now all three kinds come from Supabase Storage which also serves inline.
25. **CodeMirror 6 via CDN double-loads `@codemirror/state`** on both jsdelivr `+esm` and esm.sh without an import-map — breaks `instanceof` checks silently. Local console uses a bundled build. Web app uses plain `<textarea>` (no CM on the hosted path).
26. **Template literal → string-concat regressions** — sonnet agents rewriting JS sometimes convert template literals `` ` `` to `'...' + var + '...'`. Detect with `grep "panel.innerHTML = \`"`.
27. **Emoji → HTML-entity drift** — sonnet sometimes replaces `⭐` with `&#11088;` in copied JS. Detect with `grep "&#11088;\|&#127908;"`.

### Deploy sequencing

28. **Vercel GitHub integration expects `web/` as the project root.** If a previous session used `vercel --prod` from the repo root, the project was probably configured with root=`.` and a manual `vercel.json` — confirm Project Settings → General → Root Directory = `web/` before relying on push-to-deploy, or builds will fail / serve the wrong directory.
29. **When the web app breaks with "Failed to fetch" on save/rebuild**, the most common causes in order: (a) Railway env var missing or has embedded `\n`, (b) Railway container failing to start (check deploy logs, not just /health), (c) CORS preflight OK but POST rejected server-side — needs the full Python traceback from `railway logs`. The CLI needs a project-scoped token (set via `RAILWAY_TOKEN` env) — see `state/cross-agent/*.request.json` for example commands.

## Session-gotchas worth reading once

- **LaTeX is the authoring surface now.** Edit `tex/*.tex` directly, not the retired `legacy/py/build_*.py`.
- **Prompt template for LaTeX dispatches** lives at `dispatch/prompts/latex-scale/*.md` — re-use the shape.
- **After any operational-item edit**, re-run `python qb_diagnose.py && python qb_polish_worksheet.py`.
- **Local Flask console launch**: `python console.py` → `http://127.0.0.1:5173`.
- **Web app URL**: https://lessonplanning-lyart.vercel.app. Railway URL: https://lessonplanning-production.up.railway.app.
- **Shared passcode** for web writes is `LEHS` at time of writing. Weak — if you broaden the audience, rotate via `railway variables --set "REBUILD_PASSCODE=..."`.
- **Do not link the Vercel URL from student-reachable pages.** Teacher answer fields are exposed via the items + teacher tex views. Add OAuth + RLS column gating before that becomes appropriate.
- **Seed is safe to re-run.** `supabase/seed.py` is idempotent upsert. It does NOT overwrite web-edited tex because the Railway `/tex` PUT path is the only write surface for `tex_*` columns during normal operation — but if a user has edited tex in the browser AND then someone re-runs seed from local filesystem files, the local wins. Export-back-to-git is a future feature; for now, treat seed as "re-bootstrap from local git" and only run when you intend that.
- **Supabase SQL migrations**: apply via Dashboard SQL editor, in order (`001_`, `002_`, `003_`). Idempotent. Re-running is safe.

## Note for future LLMs

**If you want to know "what did the last session do?" run `git log --oneline -30` — don't ask the user, and don't try to summarize this file as a substitute.**

**If you want to know "what's already shipped in tex/?" run `ls tex/*_slides.pdf | wc -l` — artifact counts drift in markdown and are always accurate on disk.**

**If the wiki is relevant** (cross-project patterns, domain knowledge, routing observations), read `obsidian-wiki/wiki/hot.md` first.

**Only update this file** when the open-tasks list or durable failure modes change. Don't use it as a session diary — `git log` does that job better.

End of school: **2026-06-20**.
