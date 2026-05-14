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
- **`tex/L43_P1_obs_{student,teacher}.tex`** + **`web/pacers/L43_Pacer.html`** — **THE TARGET STYLE for all future lessons.** See "Target lesson style" section below. Visual reference: `L35_P3_obs_student.docx` at repo root.

**This file carries only what's NOT in those sources:** currently-pending tasks, durable failure modes, and pointers. It is NOT a repo tour.

## Where we are

LaTeX is canonical for student-facing output; the YAML → tex → PDF pipeline is proven (originally on L41_P2 and APStats — both now retired). **As of 2026-05-13 the department skipped L41 (Klimsara confirmed); cadence jumps directly to L43.** L41_P1/P2/P3 tex moved to `legacy/tex/`; APStats_6-4 fully retired (lessons/yaml, 6 registry+Supabase items, tagging/4-1_*.jsonl deleted); L41 and `APStats_6-4_P1` lesson rows deleted from Supabase, with L41 schedule rows having `lesson_id` nulled to preserve calendar dates. L43_P1_obs is the first shipped L43 artifact (see Open tasks).

**The collaborative web app ships and runs (as of 2026-04-23):**

- **Supabase** (project `bzqbhtrurzzavhqbgqrs`, schema `lesson_planning`) holds items, edges, lessons, audit. `tex_student/tex_teacher/tex_slides` columns on `lessons` are the source of truth for tex source. RLS: public SELECT, writes via service_role only.
- **Railway** (`https://lessonplanning-production.up.railway.app`) runs a FastAPI + TeXLive service that rebuilds PDFs (`POST /build/:id`) and takes tex writes (`PUT /tex/:id/:edition`). Auth: shared `REBUILD_PASSCODE` header `X-Passcode`; writer identity via `X-User-Name` → forwarded to PostgREST → captured by the audit trigger.
- **Vercel** (`https://lessonplanning-lyart.vercel.app`) serves the static frontend. Plain HTML + ES modules, no bundler. Supabase Realtime for presence + "someone just saved" banners. Sha-based optimistic concurrency on save → 3-pane merge view on conflict. **Deploys on push to `main` via the Vercel GitHub integration** — project → Settings → Git, root directory `web/`. Do NOT use `vercel --prod` manually; push to main instead so the source-of-truth matches what's deployed.
- **Local Flask console** (`console.py`) is still the fastest path for the owner. Localhost-only; not shared.

**For current artifact counts, shipped decks, or "what's in tex/", run `ls tex/` and `git log --oneline` — do not re-summarize here, it drifts.**

## Target lesson style (L43_P1_obs is the template — replicate for every future lesson)

**Going forward, every lesson is authored in the L43_P1_obs format.** Three artifacts per lesson:

1. **Student packet** — `tex/L{NN}_P{N}{,_obs}_student.tex/.pdf`
2. **Teacher packet** — `tex/L{NN}_P{N}{,_obs}_teacher.tex/.pdf`
3. **Pacer** — `web/pacers/L{NN}_Pacer.html` (single tab if OBS, multi-tab if 3-period)

The DOCX `L35_P3_obs_student.docx` at repo root is the canonical **visual** reference; `tex/L43_P1_obs_*.tex` is the canonical **structural** reference. Read both before authoring a new lesson.

### Required structure for the student packet (4 problems, mirrors the DOCX)

| Page | Section | Role | Default DOK |
|---|---|---|---|
| 1 | Title + 3-row objectives table (Math / Language / Essential Question) + **Do Now** | Conceptual gateway / Explore & Reason | 2 |
| 2 | **Apply — Make Sense and Persevere** | Multi-step modeling | 2 |
| 3 | **Performance Task** | DOK-3 spine (the period's only DOK-3) | **3** |
| 4 | Name field + **Exit Ticket** + 2 reflection prompts ("learned" / "liked") | DOK-2 reflective summary (NOT CER) | 2 |

**Visual hard-rules:**
- 4 pages, one section per page (`\newpage` between)
- White-space-as-writing-room (NO ruled lines on free-response — use `\writeline` macro = invisible 12pt strut)
- Plain bold section heads (NOT tcolorbox-banner)
- Ruled lines OK only on the Name field and inline `\frameblank` slots inside printed sentence frames
- TikZ figures for every problem (no rasterized images unless specifically required)
- Sentence frames printed inline next to every long-explanation prompt (ELL hard-rule)
- En-dash `--` in section headings, not bullet `\bullet`

### Required structure for the teacher packet (admin's 3-column lesson plan)

- Landscape, 0.5–0.55in margins, ~10pt font
- Header tables (4 stacked tabularx blocks): Date/Subject/Grade, CCSS+Topic Goals+EQ+Materials, Content Obj+criteria, Language Obj+criteria, IEP/ELL supports
- Body table (`xltabular`, 4 cols): **Lesson Part | Teachers will… | Students will… | Questions to consider…**
- One row per phase: Do Now / Launch+Apply / Explore+PT / Share-Summary / Exit
- **3-Reads routine encoded explicitly**: full scaffold on Apply (Read 1: T reads aloud, Read 2: S read + highlight); gradual release on PT (S read first, pair share, T re-reads if needed)
- **Group A/B/C cadence**: groups of 2–3 labeled A, B, C; teacher circulates with iPad noting interesting work; gathers responses by group letter; doesn't reveal answers
- **In-cell line breaks use `\newline` not `\\` (failure mode #25a)**

### Required structure for the pacer

- Single `tex/L{NN}_Pacer.html` based on the L43_Pacer.html pattern (`web/pacers/L43_Pacer.html`)
- One tab per period (single tab for OBS day)
- Per-phase chips with countdown timer, sticky timer bar
- Per-phase callouts (in this order): 📖 3-Reads (where applicable) · 🎤 Teachers · 🎓 Students · ❓ Questions · 📘 Rules · ✅ Answer key · 🔗 Bridge · ⚠️ Warning
- Inline answer keys (the math worked out so teacher doesn't need to re-derive mid-lesson)
- DOK-3 item flagged with ⭐ in the items list
- QR code in header pointing at the pacer's own URL (scan-to-open from projector/print)

### Pre-requisites for authoring a new lesson (L{XX} where XX is the next topic)

You **must** have the Savvas SE/TE LaTeX files for that topic. They live at the repo root as `a2_X-Y_SE.tex` (Student Edition — problem statements, page-level structure) and `a2_X-Y_TE.tex` (Teacher Edition — DOK labels, teaching notes, ground-truth answers).

**Already committed (9 pairs, verified 2026-05-14):** `4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5`. Confirm with:
```bash
git ls-files 'a2_*_SE.tex' 'a2_*_TE.tex'
```

**Missing (would need export from Savvas + add to repo):** `5-2, 5-3, 6-1, 6-2`. These are likely department-skipped same as 4-1/4-2. If a future lesson needs them, convert PDF → LaTeX via web-claude / ChatGPT / aistudio (the **TE** conversion is the high-value one — it carries DOK labels per item) and commit at repo root. The school machine at `C:\Users\ColsonR\` is the typical staging point if you have access.

These files are the **ground truth** for the Savvas-only hard rule: "is this prompt actually in the Savvas bank?" Codex steelman reads them directly during review.

### Authoring workflow (the loop)

1. **Verify SE/TE tex is in repo** — `git ls-files 'a2_X-Y_*.tex'`. For 4-3 through 6-5 (minus 4-1/4-2/5-2/5-3/6-1/6-2 which are dept-skipped) it already is. If missing, see Pre-requisites above.
2. **Pick problems from TE** for the 4 slots:
   - Do Now: Savvas Model & Discuss / "Explore and Reason" (DOK-2 conceptual gateway). May be the launch prompt for the Savvas lesson.
   - Apply: a Savvas Practice item tagged Make Sense and Persevere (DOK-2 multi-step), often anchors a numbered Example.
   - Performance Task: a Savvas Practice item tagged Higher Order Thinking, Model with Mathematics, or Performance Task. Verify it's the period's **only** DOK-3 (single-DOK3-spine hard-rule).
   - Exit Ticket: a short Savvas reflective prompt (DOK-2 — Use Appropriate Tools, Generalize, etc.). NOT another DOK-3.
3. **Cull DAG/registry** of any items from skipped lessons (e.g., when 4-1 was skipped, all `4-1-*` items were removed from registry + Supabase + tagging). See "ingest-as-derived" pattern below for adding scaffolds.
4. **Draft `tex/L{NN}_P{N}{,_obs}_student.tex`** matching the visual hard-rules above. Compile, eyeball, iterate.
5. **Draft `tex/L{NN}_P{N}{,_obs}_teacher.tex`** in admin 3-column format. Compile, eyeball, iterate.
6. **Draft `web/pacers/L{NN}_Pacer.html`** based on L43_Pacer.html. Inline the answer keys.
7. **Codex steelman review** via `cross-agent.py` (see toolchain pointer). Standard prompt structure: Section A (defend each design choice) → B (3-7 risks) → C (concrete fixes) → D (verdict). Apply BLOCKER + WARN fixes before commit.
8. **Update Supabase** — PATCH the lessons row with new `tex_student/tex_teacher`; **null `tex_do_now` and `tex_slides` if you're not shipping those** (failure mode #25b); DELETE+INSERT lesson_phases for the new structure; trigger `POST /build/{lesson_id}` to regenerate PDFs.
9. **Commit + push** — Vercel + Railway auto-deploy from `main`.

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
| Codex steelman review (OBS packets) | `cross-agent.py --task-type review --read-only --timeout 600`; most recent result: `state/cross-agent/32b207239f9d.result.json` |

**Ingest-as-derived registry pattern (new as of 2026-05-13):** When scaffolding a Savvas item into sub-prompts (build → simplify → interpret), ingest each sub-prompt as a separate registry item with `-partA`/`-partB`/`-partC` suffix. DOK reflects the cognitive demand of the sub-step. `notes` field MUST cite the parent ID + source of scaffolding. Prereq edges link `parent → partA → partB → partC`. Example: `4-3-savvas-q36` → `q36-partA-build` (DOK-1), `q36-partB-simplify-domain` (DOK-2), `q36-partC-evaluate-fairness` (DOK-3 spine). This satisfies the Savvas-only hard rule while preserving OBS-day scaffolding visibility.

## Open tasks (as of 2026-05-13)

**Current pacing (re-baselined 2026-05-13):**
- **Thu 5/14 = Topic 3 Assessment** for both periods (compressed onto one day).
- **Fri 5/15 F = TEACHER OBSERVATION** = `L43_P1_obs` (single-period 65 min; Lupe carnival DOK-3 spine). Supabase lesson row + 9 lesson_phases live.
- **L43 (Rational Functions — Simplifying)** starts F 5/15 / A 5/18; L43_P2 and L43_P3 packets TBD.
- L41 is fully skipped. APStats_6-4 fully retired. No more L41 or APStats_6-4 rows in Supabase.

**Completed 2026-05-13 (L41 retirement + L43_P1_obs shipped + new registry pattern):**
- ✅ **L41 retired**: L41_P1/P2/P3 tex → `legacy/tex/`; APStats_6-4 yaml + 6 registry items removed; `tagging/4-1_*.jsonl` deleted; L41 + APStats_6-4_P1 Supabase lesson rows deleted; schedule lesson_id nulled.
- ✅ **L43_P1_obs student packet** (`tex/L43_P1_obs_student.tex/.pdf`): 4 pages, white-space-as-writing-room (no ruled lines), mirrors `L35_P3_obs_student.docx` visual structure.
- ✅ **L43_P1_obs teacher packet** (`tex/L43_P1_obs_teacher.tex/.pdf`): 3 pages landscape, admin's 3-column lesson plan format, encodes 3-Reads routine + group A/B/C cadence + iPad circulation pattern.
- ✅ **L43_Pacer.html** (`web/pacers/L43_Pacer.html`): single-period OBS pacer, countdown timer, 3-Reads callouts (full scaffold on Apply, gradual release on PT), inline answer keys, QR code in header pointing at pacer URL.
- ✅ **L35_P3_obs tex deprecated** to `legacy/` — `L35_P3_obs_student.docx` at repo root is the canonical visual reference for that lesson.
- ✅ **Supabase L43_P1 row** updated: tex_student/tex_teacher fields live, 9 lesson_phases (do_now / launch×2 / explore×4 / share_summary / exit), PDFs rebuilt via Railway, `has_slides_pdf=false`.
- ✅ **Ingest-as-derived pattern applied**: `4-3-savvas-q36` → `q36-partA-build` / `q36-partB-simplify-domain` / `q36-partC-evaluate-fairness`; `4-3-savvas-q35-partc-design` also ingested. See toolchain pointer above for pattern spec.
- ✅ **Codex steelman review** dispatched before committing L43_P1_obs — flagged 2 ship-blockers + 4 soft risks, all addressed. Result: `state/cross-agent/32b207239f9d.result.json`.

**Completed 2026-05-01 (asset upload pipeline — textbook PDFs / DOCX / per-item screenshots):**
- ✅ **Three new Supabase Storage buckets** (auto-created on Railway startup, idempotent): `topic-pdfs` (Savvas SE/TE chapter PDFs as `a2_<topic>_<SE|TE>.pdf`), `lesson-docx` (`<lesson_id>_<student|teacher>.docx` + `<lesson_id>_slides.pptx`), `item-screenshots` (`<item_id>.<png|jpg>` for textbook source images of registry items).
- ✅ **Three new Railway endpoints** in `railway/server.py` (X-Passcode + X-User-Name auth like existing /tex and /build): `POST /upload/topic-pdf/{topic}/{edition}`, `POST /upload/docx/{lesson_id}/{kind}`, `POST /upload/screenshot/{item_id}`. Path-traversal-safe (regex validation BEFORE storage path construction). MIME enforced per endpoint. `x-upsert: "true"` literal string per failure mode #19.
- ✅ **Web UI** (`web/index.html` + `web/js/main.js` + `web/js/item-detail.js` + `web/js/api.js` + `web/styles/console.css`): two new lesson-page sections — "Textbook (Savvas)" linking to topic SE/TE PDFs (Algebra 2 only; APStats hidden via `lessonIdToTopic`==null) and "Editable formats" with Student DOCX / Teacher DOCX / Slides PPTX slots. Items browser shows per-item screenshot thumbnails (HEAD-probed in parallel via `Promise.all`). All sections gracefully degrade on 404 (upload button instead of download).
- ✅ **Bulk uploaders** at `supabase/upload_topic_pdfs.py` and `supabase/upload_docx.py` — run on home machine where the source PDFs live (`a2_4-3_SE.pdf` through `a2_6-5_TE.pdf` etc.). Idempotent, 50MB guard, ASCII-safe console output.
- ✅ **Pull-back utility** at `supabase/pull_screenshots.py` — pulls Supabase `item-screenshots/*` to local `questionbank/images/<item_id>.<ext>`, paginated (1000-row Storage list cap), size-skip if local matches remote Content-Length. Keeps the on-disk pattern in sync without requiring Railway to write to your laptop.
- Note: web uploads go through Railway → Supabase only. Local `questionbank/images/` is updated via `pull_screenshots.py` (pull model, not push).

**Time-critical — user handles:**
- ⚠️ **Service-role JWT still on the OLD `eyJ...` (legacy) format** in Railway env + local `.env`. The 5/3 smoke test (real DOCX upload through `/upload/docx/L35_P3_obs/student`) returned 200 with a valid Storage URL — Storage operations are confirmed working under the old key. However, the user noted earlier that the JWT was "disabled during a connect-repo cleanup". Whether REST writes on the curriculum project still succeed is uncertain; the Storage path is healthy. Rotate at leisure to the new `sb_secret_*` model:
  1. https://supabase.com/dashboard/project/bzqbhtrurzzavhqbgqrs/settings/api-keys → "Create new secret key" (Supabase migrated this project to the new `sb_publishable_*` / `sb_secret_*` model — JWT secret rotation control is gone for this project).
  2. `cd railway && railway variables --set "SUPABASE_SERVICE_ROLE_KEY=sb_secret_..."` (one line, no continuations — see failure mode #12). Auto-redeploys.
  3. Update local `.env` (gitignored): `SUPABASE_SERVICE_ROLE_KEY=sb_secret_...`
  4. No code changes — `sb_secret_*` is a drop-in bearer-token replacement.
- Delete the Railway project access token `cc-debug-session` at https://railway.com/account/tokens once debugging sessions wrap.
- (Optional) Audit `Lesson_planning` for any plaintext-committed legacy `eyJ...` service-role JWT — same audit pattern that flagged it in the `connect` repo.

**Completed 2026-05-03 (Railway GitHub auto-deploy + obs slides + lesson_phases + first textbook PDFs):**
- ✅ **Railway GitHub auto-deploy configured** — pushes to `main` now auto-build + deploy. Same model as Vercel for `web/`. **Dashboard config**: service → Settings → Source → connected to `robjohncolson/Lesson_planning`, branch `main`, **Root Directory BLANK** (repo root), Deploy on Push: ON, Wait for CI: OFF. Manual `railway up` is obsolete (failure mode #15 superseded). End-to-end smoke test (real `POST /upload/docx`) returned 200 with valid Storage URL.
- ✅ **L35_P3_obs slides authored** — `tex/L35_P3_obs_slides.{tex,pdf}`, 16-page Beamer deck specific to the observation lesson (gradual-release Launch sub-slides, Touch/Cross rule callout, Mystery Graph DOK-3 with reused TikZ, sentence frames, exit ticket). Replaces the reused non-obs P3 deck. Uploaded to `lesson-pdfs/L35_P3_obs_slides.pdf` and `tex_slides` synced to lessons row.
- ✅ **`lesson_phases` populated for L35_P3_obs** — 11 rows: 1 do_now / 4 launch / 4 explore (2 with Savvas item ids: `3-5-savvas-q12`, `3-5-tryit-2b`) / 1 share_summary / 1 exit. Teacher console + web phase view now shows structured skeleton instead of empty list. Pattern: explicit DELETE-by-lesson_id then INSERT, matching migration 005's idempotent intent.
- ✅ **First two textbook PDFs uploaded** to `topic-pdfs` bucket: `a2_3-5_SE.pdf` (2.9 MB) + `a2_3-5_TE.pdf` (6.2 MB). Remaining 16 (4-3 → 6-5 SE/TE) on home machine — user runs `python supabase/upload_topic_pdfs.py <dir>`. Verification agent `trig_01G2vzz2Bw8p2a6uXfAzFnpm` fires Sun 2026-05-03 13:00 UTC to check what landed.
- ✅ **Bucket-check 400/404 fix** in `upload_topic_pdfs.py` + `upload_docx.py` (failure mode 24a — Supabase returns HTTP 400 with `404` in JSON body for missing buckets, not real 404).
- ✅ **`.env` workflow** for local secrets — gitignored at repo root, contains `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `REBUILD_PASSCODE=LEHS`. Use `set -a && source .env && set +a` in Git Bash before running upload/seed scripts. Avoids re-pasting secrets into chat each session.

**Completed 2026-04-30 (L35_P3_obs polish + Blooket destructive strip):**
- ✅ **Schedule live** in Supabase: 64 rows pushed; 5/8 F = `L35_P3_obs`, 5/14 = Topic 3 Assess (both periods), L41 starts F 5/15 / A 5/18. `seed_schedule.py` now uses `?on_conflict=class_date,period` + nulled-out the L35_P1 FK.
- ✅ **L35_P3_obs lesson row** + **PDFs in Storage** (4 files: student/teacher rebuilt + slides/do_now reused from non-obs L35_P3).
- ✅ **Student packet** (`tex/L35_P3_obs_student.tex`): Day 3 label, tcolorbox 3-section objectives header (Math Obj / Language Obj / Essential Understanding), 18 write-space doublings, You-do + grid pinned to same page via `samepage`, Mystery Graph TikZ clipped to y∈[-2,2] (curve no longer plunges off-page).
- ✅ **Teacher packet** (`tex/L35_P3_obs_teacher.tex`): xltabular `\hsize`-multiplier columns replaced with explicit `p{}` widths on pages 3-6 (root cause of narrow-prose-stretched-vertically). Doc went 7 → 6 pages. Page 2 metadata fixed (was "L35_P2 student packet" / "Period 2", now "L35_P3_obs" / "Day 3 / Period 3 Observation").
- ✅ **Metadata yaml** at `lessons/L35_P3_obs.yaml` (back-extracted, 233 lines). Schema parity with `L41_P2.yaml` (`questions_to_ask` not `teacher_questions`, `minutes` not `duration_min`). Header comment notes: METADATA only, NOT a generator input — the tex stays hand-canonical. New top-level fields `day_of_cadence` and `topic` added (day_of_cadence is decoupled from calendar drift — P3 = Day 3 even if you're on calendar day 8).
- ✅ **Blooket destructive strip**: 48 items removed from `questionbank/registry.jsonl` (40 with `*-blooket-*` ids, 8 `*-bridge-day*` tagged `blooket-pool`). 25+ supporting files cleaned (pacers, slide builders, qb.py, web/js/dag.js, tagging docs). `import_blooket_csv.py` + `Blooket_Import_Zeros_of_Polynomials.csv` moved to `legacy/`. Supabase items table also cleaned via direct DELETE on `id ilike '*blooket*'`. Final count: 949 registry rows, 898 items in DB.
- Codex cross-review (via cross-agent.py) caught the `teacher_questions` schema-drift BLOCKER + cross-prong "Period 2" leftover, both fixed before commit.

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
- **Tunnel bouncer on Railway** — ✅ **DEPLOYED AND WORKING (2026-05-03, `connect` repo @ `957a3a0`)**. Vanilla openssh-server in a debian-slim container, reachable from the work laptop via SSH ProxyJump despite CrowdStrike Falcon blocking cloudflared/tailscale binaries. End-to-end verified: `connect-sish.bat` from work laptop → ProxyJump through bouncer → Athena's WSL shell prompt. **Architecture**: `Athena ssh -N -R 9000:[::1]:2223 tunnel@bouncer:2222` (note: WSL sshd is IPv6-only on Athena — `127.0.0.1:2223` is refused, must target `[::1]`); work laptop `ssh -J tunnel@bouncer:39326 rober@localhost -p 9000`. **Files**: `connect/sish/{Dockerfile,sshd_config,entrypoint.sh,README.md,pubkeys/{athena,worklaptop}.pub,railway.json}` + `connect/athena/{sish-reverse.sh,sish-reverse.service,install-sish.sh}` + `connect/connect-sish.bat`. **Bouncer config**: Railway service `sish`, image-built from `connect/sish/`, GitHub auto-deploy from `main`, single TCP Proxy mapping (internal :2222 → external `shinkansen.proxy.rlwy.net:39326`), `/host-keys` Railway volume for persistent host key, ZERO env vars (vanilla sshd needs no config beyond sshd_config). The legacy cloudflared+Supabase path in connect.bat stays in place as a fallback transport, untouched. **Lessons learned for future sessions**: (a) sish has 50 features and a brittle config matrix — vanilla openssh + textbook bastion pattern is dramatically more reliable, would skip sish entirely next time; (b) Debian's `useradd` creates locked accounts (`!` in /etc/shadow), sshd refuses pubkey login pre-auth — must `passwd -d <user>` after useradd; (c) WSL2 sshd is IPv6-only by default — use `[::1]` not `127.0.0.1` for reverse-forward targets; (d) Railway only allows ONE TCP Proxy per service — use SSH ProxyJump with `PermitOpen localhost:9000` instead of trying to expose multiple ports; (e) Cross-agent codex review timed out 3× this session in xhigh reasoning mode (matches CLAUDE.md gotcha #5) — self-review with WebFetch verification of upstream-source claims is the documented and reliable fallback. **Adding more clients**: drop their `*.pub` in `connect/sish/pubkeys/`, commit, push — GitHub auto-deploy rebuilds the image with new authorized_keys.
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
8a. **Edge's PDF viewer ignores `#page=N` URL fragments** — driving `driver.get("file://...pdf#page=3")` returns page 1 every time. For per-page PDF screenshots, render via pdftoppm/MuPDF or use the Read tool's `pages:` parameter directly instead.
9. **Windows terminal mojibake** — math symbols display wrong in stdout; FILES are fine. Use `pdftotext -enc UTF-8` for text checks.
10. **Registry mojibake survives ingestion** — run `python fix_registry_mojibake.py --apply` after any new item ingest.
11. **`pkill -f` is unreliable on Git Bash / Windows** — it reports success but Windows python.exe keeps running. Use `taskkill //F //IM python.exe`. Better: track PIDs explicitly.
12. **PowerShell line continuation (`` ` `` + newline) embeds literal `\n` in env var values.** If you `railway variables --set "KEY=val1\ncontinued"` across lines, the value includes a newline. `requests` library rejects headers with `\n` (HTTP header injection guard) → service 500s with `InvalidHeader`. Always paste secrets as ONE LINE.

### Web stack specifics

12a. **PostgREST upsert defaults to PRIMARY KEY conflict resolution.** If your unique constraint is on a non-PK column (e.g. `(class_date, period)` on `schedule`), `Prefer: resolution=merge-duplicates` alone returns 409 — you must also pass `?on_conflict=col1,col2` on the endpoint. Fixed in `seed_schedule.py`.
12b. **Lessons table FK can block schedule seed.** A row in `schedule` with `lesson_id` that has no matching `lessons.id` fails the FK constraint. If a legacy lesson_id has no yaml/tex (e.g. `L35_P1`), null the schedule lesson_id and keep the date+notes for the historical record.

13. **Railway CMD must be shell-form so `$PORT` expands.** Exec-form `CMD ["uvicorn","--port","$PORT"]` passes literal `$PORT` to uvicorn. Use `CMD uvicorn ... --port ${PORT:-8080}`. `startCommand` in `railway.toml` also reserves literal unless wrapped in `/bin/sh -c`.
14. **`railway.toml` must sit at repo root** (where `railway init` runs), not inside `railway/`. Railway CLI looks at the project root for config.
15. **Railway auto-deploys from GitHub on push to `main`** (configured 2026-05-03 — see Settings → Source → Deploy on Push). Manual `railway up` is no longer required for normal pushes. If a deploy doesn't trigger after a push, check Settings → Source. Historical: prior to the GitHub integration, `redeploy` button reused the previous image and required `railway up` for code changes — that's obsolete now.
15a. **Railway "Root Directory" must be BLANK (repo root), NOT `railway/`.** The `railway/Dockerfile` uses `COPY tex/preamble.sty .`, `COPY questionbank/registry.jsonl ...`, etc. — paths that resolve relative to the build context. With Root Directory set to `railway/`, the build context shrinks to `railway/` and `tex/beamer_preamble.sty` etc. become invisible — build fails with `failed to compute cache key: "/tex/beamer_preamble.sty": not found`. Caching can mask the problem until a NEW COPY step runs uncached. The `railway.toml` at repo root already specifies `dockerfilePath = "railway/Dockerfile"` correctly.
16. **Supabase schemas must be added to "Exposed schemas"** (Project Settings → Data API) before PostgREST will route to them. Default is `public, graphql_public`. Add `lesson_planning`.
17. **PostgREST caps `.select()` at 1000 rows by default.** `items` has 1006. `api.listAllItems` and `listAllEdges` paginate via `.range()` — preserve that pattern for any large table.
18. **supabase-py's bundled httpx client negotiates HTTP/2 → intermittent `StreamReset` errors against Supabase's Cloudflare edge.** Railway server uses plain `requests` (HTTP/1.1) instead. If you re-introduce supabase-py, expect flakes.
19. **Supabase Storage `upload` wants `x-upsert: "true"` as a string**, not bool `True`. Passing `{"upsert": True}` sometimes silently fails the upsert path.
20. **Audit trigger reads x-user-name from two places.** `current_setting('request.header.x-user-name', true)` works only with specific PostgREST flags; on Supabase you need the fallback via `current_setting('request.headers', true)::jsonb->>'x-user-name'`. Migration 002 sets both.
21. **Realtime needs REPLICA IDENTITY FULL** on tables where you want OLD+NEW in UPDATE payloads. Migration 003 applies this on `lesson_planning.lessons`.
22. **Vercel default respects `.gitignore`.** `web/.gitignore` ignores `config.js`. First `vercel --prod` will miss the config unless you either (a) commit `config.js` (anon key is safe to embed) or (b) remove it from `.gitignore` / add a prebuild step. Currently: committed per Phase A step 2 README option 1.
23. **Vercel static deploy routes `/dag.html` through a 308 → `/dag`** because of `cleanUrls: true`. Both resolve; the internal nav href uses `/dag.html` for now.
24. **GitHub raw PDFs force-download** (Content-Disposition: attachment); jsdelivr CDN serves them inline. `pdfUrl` used to fall back to jsdelivr; now all three kinds come from Supabase Storage which also serves inline.
24a. **Supabase Storage `GET /bucket/{name}` returns HTTP 400 with body `{"statusCode":"404","error":"Bucket not found"}` for missing buckets** — not an HTTP 404 as expected. Bucket-check helpers must inspect both the status code AND the response body for "Bucket not found" / `"404"` substring before deciding to error. Patched `supabase/upload_topic_pdfs.py` and `supabase/upload_docx.py` 2026-05-01.

25. **Bash heredoc + Python `'\\newline'` mangling**: When running `python <<'PY' ... PY` from bash, `\\\\` escapes can mangle to literal `\n` bytes. Symptom: rendered file contains literal "ewline" with no leading backslash. Fix: write Python to a real `.py` file (e.g., `.scratch/`) when literal backslash chars are involved.
25a. **`xltabular`/`tabularx` in-cell line breaks**: use `\newline` not `\\` for line breaks INSIDE a cell. `\\` is the row terminator and leaks cell content into the next column. Symptom: cell content appears in the wrong column.
25b. **Railway `/build/{lesson_id}` compiles ALL `tex_*` fields**, not just student/teacher. If `tex_do_now` or `tex_slides` holds stale content with unescaped `&` (e.g., "EXPLORE & REASON"), the build fails with "Misplaced alignment tab character &" and produces no PDF. Fix: when retiring or re-purposing a lessons row, null ALL `tex_*` columns explicitly, not just the ones being updated.

26. **CodeMirror 6 via CDN double-loads `@codemirror/state`** on both jsdelivr `+esm` and esm.sh without an import-map — breaks `instanceof` checks silently. Local console uses a bundled build. Web app uses plain `<textarea>` (no CM on the hosted path).
27. **Template literal → string-concat regressions** — sonnet agents rewriting JS sometimes convert template literals `` ` `` to `'...' + var + '...'`. Detect with `grep "panel.innerHTML = \`"`.
28. **Emoji → HTML-entity drift** — sonnet sometimes replaces `⭐` with `&#11088;` in copied JS. Detect with `grep "&#11088;\|&#127908;"`.

### Deploy sequencing

29. **Vercel GitHub integration expects `web/` as the project root.** If a previous session used `vercel --prod` from the repo root, the project was probably configured with root=`.` and a manual `vercel.json` — confirm Project Settings → General → Root Directory = `web/` before relying on push-to-deploy, or builds will fail / serve the wrong directory.
30. **When the web app breaks with "Failed to fetch" on save/rebuild**, the most common causes in order: (a) Railway env var missing or has embedded `\n`, (b) Railway container failing to start (check deploy logs, not just /health), (c) CORS preflight OK but POST rejected server-side — needs the full Python traceback from `railway logs`. The CLI needs a project-scoped token (set via `RAILWAY_TOKEN` env) — see `state/cross-agent/*.request.json` for example commands.

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
