# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

Canonical context lives elsewhere:
- `CLAUDE.md` — project rules, toolchain, class context, Klimsara pattern, LaTeX-canonical hard-rule
- `git log --oneline -30` — session-by-session narrative
- `tex/preamble.sty` + `tex/beamer_preamble.sty` — shared style packages
- `tagging/BATCH_SYNTHESIS.md` + `graph/` — the curriculum DAG, echo chains, coverage
- `graph/eye_check/*.md` + `graph/polish/*.md` — per-lesson intent briefs and polish worksheets
- `lessons/L41_P2.yaml` + `build_lesson_from_yaml.py` — YAML-driven generator (proof of concept)

This file carries only (a) the next concrete task and (b) open flags that aren't yet checked.

---

## Where we are (2026-04-22, after LaTeX-canonical pivot)

**LaTeX is canonical for student-facing output.** docx is retired to `legacy/docx/`. Python builders are retired to `legacy/py/`. Edits to lesson content go into `tex/*.tex` directly.

**36 lesson PDFs ship from `tex/`** covering 18 lessons × 2 editions (student + teacher). All compile with `pdflatex --miktex-enable-installer`. Plus 3 `tex/L35_P4_*` assessment-day packets (do_now, exit_ticket, teacher_notes) for Thu 4/30.

**9 chain-callback callouts integrated** into 8 teacher packets (`graph/chain{1,2}_callbacks.md` scripts are now spliced into the relevant `tex/L*_teacher.tex` files as `\IconSpeak`-tagged `calloutpeach` callouts positioned before the anchor bank item).

**`tex/L41_P2_slides.pdf`** proves the beamer slide path. `tex/beamer_preamble.sty` holds the shared slide style. Remaining 10 decks still emit `.pptx` via `build_L*_slides.py`; not migrated.

**YAML generator** (`build_lesson_from_yaml.py`) takes a `~220-line lesson spec and emits both student and teacher .tex. `lessons/L41_P2.yaml` is the proof. Existing 18 lessons NOT forcibly converted — the Codex-hand-crafted tex files have artisanal per-lesson touches the uniform generator doesn't reproduce. YAML is the authoring interface for NEW lessons (Alg 1 / APStats someday).

**Assessment-shell backfill: 11 → 34.** Every shipped-lesson rehearsal claim now has a concrete shell target in `questionbank/assessment_shells.jsonl`. One nominal mismatch surfaced: `6-5-savvas-q34` rehearses `topic6-formB-q16` with zero token overlap (needs a human read of Form B Q16 to resolve).

**Pacer HTML verified end-to-end via Selenium smoke test** — all tabs render, countdown timer works (05:00 → 04:59), zero browser console errors. `browser-harness` does NOT work on Windows (AF_UNIX unavailable). Template Selenium script captured in the auto-memory reference note.

**Registry mojibake fixed** — 12 L41 items had UTF-8 double-encoding (`Ã‚Â°` / `â€”`) repaired via ftfy. `fix_registry_mojibake.py` is idempotent and runnable whenever new items land.

## Tooling inventory

| Tool | Purpose | Status |
|---|---|---|
| `tex/preamble.sty` | Packet style (tcolorbox callouts, phase headers, bankitems) | Canonical |
| `tex/beamer_preamble.sty` | Slide style | Canonical |
| `build_lesson_from_yaml.py` | YAML → student+teacher .tex | Proof of concept |
| `fix_registry_mojibake.py` | ftfy registry cleanup | Idempotent |
| `qb_polish_worksheet.py` | Emit `graph/polish/L*.md` | Runs on frozen operational_ids.json |
| `qb_diagnose.py` | Emit `graph/{skill_bridge_gaps,nominal_rehearsals,redundant_practice}.md` | Live |
| `dispatch/parallel-batch.manifest.json` | 34-agent LaTeX manifest (scale-out) | Used; 40/40 final success rate |
| `dispatch/prompts/latex-scale/` | Per-agent prompt files | Runnable; answer-leak guardrail baked in |

## Failure modes catalogued from this session

1. **owned_paths must be glob `tex/{name}.*`** — pdflatex emits `.aux/.log/.pdf/.out` alongside the `.tex`; a single-file owned_path rejects them on ownership enforcement.
2. **MiKTeX-sandbox ownership trap** — some Codex agents defensively redirect MiKTeX cache into `tex/.miktex-sandbox/` to keep global filesystem clean, and the nested dir still trips ownership. Fallback: single-shot `cross-agent.py` dispatch.
3. **parallel-codex-runner discards uncommitted worktree state on failure** — always check `codex/*` branches BEFORE runner cleanup to salvage work.
4. **Answer-leak in format-conversion prompts** — Codex substituted `k=300000` into a TikZ graph label where the source said `w = k/f`. Prompt template now has explicit "do not substitute computed answers into prompt content" guardrail. Saved to auto-memory feedback.
5. **browser-harness on Windows** — Unix-socket AF_UNIX dependency; use Selenium + Edge headless. Saved to auto-memory reference with template.

## Next task (user pick)

In no particular priority order:

1. **Beamer slide scale-out** — 10 remaining decks (L35 P2/P3/P4 handled in pacer, or not at all? Check; L41 P1/P3; L43 P1/P2/P3; L44 P1; L45 P1; L51 P1; L54 P1/P2/P3; L55 P1; L63 P1; L64 P1; L65 P1). Dispatch pattern is proven. ~10× Codex dispatches via `parallel-codex-runner`.
2. **YAML tex→YAML back-extractor** — if you want the 18 existing lessons editable via YAML going forward. Risks losing artisanal per-lesson TikZ. Don't force it; convert lesson-by-lesson when a big edit is pending.
3. **Topic 6 Form B Q16 resolution** — read the actual Form B Q16 content, decide whether `topic6-formB-q16` shell's `skill_tokens` or `6-5-savvas-q34`'s `rehearses` claim is the one to retag.
4. **Chain-3-through-6 authoring** — `graph/chain{1,2}_callbacks.md` exist; the wiki `concepts/Curriculum DAG.md` notes four archetypes but only two chain-scripts. If any of those other archetypes has enough items to be a chain, author it.
5. **Topic 4 week-of prep** — Topic 4 close-out lands (L41 starts 4/30 F / 5/3 A). Verify L41 pacer loads via Selenium, re-run `graph/polish/L41_P*.md` if any new ingests arrive.
6. **New-subject onboarding proof** — write ONE hand-crafted lesson YAML for Algebra 1 or APStats as a vitality check on the generator. Not urgent.

## Deferred (still not blocking)

- **Topic 5 `-2`-suffixed registry rows** (128 suspicious pairs) — harmless, rename for clarity when you have idle time.
- **Assessment-shell backfill for retired Topic 3 lessons** (Q1, Q3, Q4, Q7, Q9, Q11 on the Topic 3 assessment) — shelled but `lesson_covered` points at retired 3-1/3-2/3-3/3-4 lessons with no shipped rehearsal, so inert.
- **Slides migration scale-out** (see above).
- **Chain-3+ scripts** (see above).

End of school: **2026-06-20**.

## Session gotchas worth re-reading

- **LaTeX is the authoring surface now.** Edit `tex/*.tex` directly, not the retired `legacy/py/build_*.py`.
- **When starting a new Codex LaTeX dispatch**, owned_paths MUST be glob `tex/{name}.*` (not `tex/{name}.tex` — pdflatex artifacts trip ownership).
- **Prompt template for LaTeX dispatches** lives at `dispatch/prompts/latex-scale/*.md` — re-use the shape (generate + validate + no-answer-leak guardrail) for new dispatches.
- **After any operational-item edit**, re-run `python qb_diagnose.py && python qb_polish_worksheet.py`. Pilot files under `tagging/` are the source of truth for v2 fields.
- **Cross-agent dispatch to Codex has a 600s hard timeout.** If a task is too big, split it or use `parallel-codex-runner` with a manifest.
- **Windows terminal mojibake** — math symbols display wrong in stdout; FILES are fine. Use `pdftotext -enc UTF-8` for text checks.
- **Registry mojibake survives from ingestion.** Run `python fix_registry_mojibake.py --apply` after any new item ingest.
- **Pacer HTMLs are JS-rendered single-page apps** — can't grep static HTML for content. Use Selenium + Edge headless to verify (template in project memory reference note).
- **`browser-harness` doesn't work on Windows** — always reach for Selenium instead. Fallback auto-installed template in `C:/Users/rober/.claude/projects/.../memory/reference_browser_automation_windows.md`.
