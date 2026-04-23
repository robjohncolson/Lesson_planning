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

**This file carries only what's NOT in those sources:** currently-pending tasks, durable failure modes, and pointers. It is NOT a repo tour.

## Where we are

LaTeX is canonical for student-facing output. YAML → tex → PDF pipeline proven on L41_P2 and APStats. Every shipped Algebra 2 lesson has matching student/teacher packets, a beamer projection deck, and a pacer HTML. Teacher Console MVP (Flask + static frontend) exposes the workflow in a browser.

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
| Teacher Console | `console.py` (Flask) + `console_static/` + `INSTALL.md` |
| Parallel dispatch (legacy) | `dispatch/parallel-batch.manifest.json` + `dispatch/prompts/latex-scale/` |

## Open tasks (as of 2026-04-22 post-session)

**Time-critical — user handles:**
- Topic 4 week-of prep (L41 starts Fri 5/1 F / Mon 5/4 A). Verify L41_Pacer via Selenium, re-run `qb_polish_worksheet.py` on latest registry.

**Backlog — pick when idle:**
- **Registry answer backfill** (~130 items across ~17 lessons). Surfaced by L44_P1 back-extraction: most pre-Klimsara registry rows have `answers:[]`, so regen teacher packets emit `(no answer key --- verify before class)` placeholders. Biggest real gap for back-extraction feasibility. See `lessons/L44_P1_back_extraction_notes.md`.
- **Generator schema gaps** — `kind: raw_tikz` for custom per-lesson TikZ (L44 circuit, L45 chemistry, L51 cylinder), `section_notes:` per-phase for free-form `\textit{...}` prose under section banners.
- **Teacher Console Phase 2:**
  - CodeMirror via bundled distribution or pinned import map (CDN dual-load of `@codemirror/state` broke Phase 1; textarea fallback ships now).
  - Streaming `/api/registry` (current full-load is fine at 1057 rows; will matter at 5000+).
  - Curriculum DAG visualization (d3.js).
  - Diff viewer (regen vs canonical).
  - Auth gate for remote hosting + teacher verification.
  - Real install screenshots (`docs/install_screenshots/`).
- **Deferred (harmless):** Topic 5 `-2`-suffixed registry rows (128 pairs, rename for clarity); retired Topic 3 assessment shells (Q1/Q3/Q4/Q7/Q9/Q11 point at retired lessons, inert).

**Not blocking:**
- New-subject scale-out (APStats or Algebra 1). Generator is subject-agnostic (proven). Author-when-teaching-that-subject.
- Chain-3+ scripts. Researched and filed as no-go per `graph/chain3plus_research.md` — archetypes have ≤3 anchor items each, below the ≥4 threshold.

## Durable failure modes (re-read before dispatching)

1. **`owned_paths` for LaTeX must be glob `tex/{name}.*`** — pdflatex emits `.aux/.log/.pdf/.out` alongside `.tex`; single-file ownership rejects them.
2. **MiKTeX-sandbox ownership trap** — Codex agents sometimes redirect MiKTeX cache into `tex/.miktex-sandbox/`, which trips ownership. Fallback: single-shot `cross-agent.py`.
3. **`parallel-codex-runner` discards uncommitted worktree on failure** — always check `codex/*` branches BEFORE cleanup to salvage work.
4. **Answer-leak in format-conversion prompts** — format converters/renderers must keep symbolic form (`w = k/f`, `g(x) = 1/(x-h) + k`); never substitute computed answers into student-facing prompt content. Known violations: L41_P2 slide TikZ (`k=300000`), L54_P3 slide Example 2 (`y ≈ 224 ft`), L54_P3 pacer Exit teacher (`5.44 mL`). Every LaTeX/Beamer/pacer dispatch prompt now carries this guardrail.
5. **`browser-harness` doesn't work on Windows** — AF_UNIX unavailable. Use Selenium + Edge headless. Template in `~/.claude/projects/.../memory/reference_browser_automation_windows.md`.
6. **Pacer HTMLs are JS-rendered** — can't grep static HTML for rendered content. Use Selenium smoke-test pattern (see `L41_Pacer.html` or any pacer rebuild commit for reference).
7. **Windows terminal mojibake** — math symbols display wrong in stdout; FILES are fine. Use `pdftotext -enc UTF-8` for text checks.
8. **Registry mojibake survives ingestion** — run `python fix_registry_mojibake.py --apply` after any new item ingest.
9. **Cross-agent dispatch to Codex has 600s hard timeout** — split or use `parallel-codex-runner` with a manifest.
10. **CodeMirror 6 via CDN double-loads `@codemirror/state`** on both jsdelivr `+esm` and esm.sh without an import-map — breaks `instanceof` checks silently. For bundled editors, use a build step or pinned import map. MVP uses `<textarea>`.
11. **Template literal → string-concat regressions** — sonnet agents rewriting pacer HTMLs sometimes convert ```` ` `` ``` template literals to `'...' + var + '...'` concat, and escape-quote wrong (`('` + `'tabId`' + `')'` → `startPhase(tabId)` without string quoting). Detect with `grep -q "panel.innerHTML = \`"`.
12. **Emoji → HTML-entity drift** — sonnet sometimes replaces `⭐` with `&#11088;` in copied JS. Detect with `grep "&#11088;\|&#127908;"`. Fixup is a straight text substitution.

## Session-gotchas worth reading once

- **LaTeX is the authoring surface now.** Edit `tex/*.tex` directly, not the retired `legacy/py/build_*.py`.
- **Prompt template for LaTeX dispatches** lives at `dispatch/prompts/latex-scale/*.md` — re-use the shape (generate + validate + no-answer-leak guardrail) for new dispatches.
- **After any operational-item edit**, re-run `python qb_diagnose.py && python qb_polish_worksheet.py`. Pilot files under `tagging/` are the source of truth for v2 fields.
- **Teacher Console launch**: `python console.py` → `http://127.0.0.1:5173`. Localhost-only. `INSTALL.md` covers Windows install.

## Note for future LLMs

**If you want to know "what did the last session do?" run `git log --oneline -30` — don't ask the user, and don't try to summarize this file as a substitute.**

**If you want to know "what's already shipped in tex/?" run `ls tex/*_slides.pdf | wc -l` — artifact counts drift in markdown and are always accurate on disk.**

**If the wiki is relevant** (cross-project patterns, domain knowledge, routing observations), read `obsidian-wiki/wiki/hot.md` first. The wiki exists precisely so context survives across sessions; use it.

**Only update this file** when the open-tasks list or durable failure modes change. Don't use it as a session diary — `git log` does that job better.

End of school: **2026-06-20**.
