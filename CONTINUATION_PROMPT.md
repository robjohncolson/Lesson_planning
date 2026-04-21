# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

Most context lives in:
- `CLAUDE.md` — project rules + toolchain + class context
- `git log --oneline -20` — session-by-session narrative
- `WIKI_UPDATES_PENDING.md` — Obsidian wiki updates to paste on home laptop

This file captures only (a) the next task and (b) session-transient details that don't belong in the above.

---

## Machine context

Work laptop (`C:/Users/ColsonR/...`). Student materials + Savvas PDFs live here. Home laptop has the Obsidian wiki.

## Next task: Topic 6 build (priority shift on 2026-04-20)

**Framing:** The goal has shifted from "what I need to teach next" to "curriculum other teachers can actually use." One peer teacher is already on Topic 5, so shipping DOK-framework-aligned Topic 5 (done) + Topic 6 (next) materials positions the user as a curriculum leader rather than someone behind pace. Topic 4 backlog waits until after Topic 6 is built.

**Topic 6 lessons to build:** 6-3, 6-4, 6-5 (per CLAUDE.md roadmap).

### Sources inventory

| Lesson | SE | TE | Notes |
|---|---|---|---|
| 6-3 | `a2_6-3_SE.tex` | `a2_6-3_TE.tex` | Ready to ingest |
| 6-4 | `a2_6-4_SE.tex` | **MISSING** | User must supply before ingest |
| 6-5 | `a2_6-5_SE.tex` | **MISSING** | User must supply before ingest |

Topic 6 assessment:
- `Topic6Assess.docx` (full text)
- `Topic6AssessAnswer.pdf` (answer key)
- `Topic6AssessFormB.tex` (typeset LaTeX — use this, same pattern as Topic 5 Form B)

### Workflow for next session

1. **Ask user for 6-4 TE and 6-5 TE** before starting. Don't ingest partial lessons.
2. **Detect workflow mode.** Open `Topic6AssessFormB.tex`:
   - If it's a single Performance Assessment with chained items (like Topic 5) → DOK-3-forward workflow.
   - If it's 8+ discrete items (like Topic 4) → assessment-forward workflow.
   - See wiki `concepts/Assessment-Forward vs DOK-3-Forward Workflow.md` (pending on home laptop) or `WIKI_UPDATES_PENDING.md` section 4.
3. **Sanity-scan DOK-3 candidates** across 6-3 / 6-4 / 6-5 BEFORE committing to a spine. Decide which lesson is the "main focus" of Topic 6 (full 3-period) and which are "quick" (single-period compressed Klimsara).
4. **Ingest via LaTeX pipeline** (`source/6-{3,4,5}_savvas_{SE,TE}.tex` → `ingest_lesson_from_latex.py` → `qb_append.py`). Remember to strip chat-UI chrome ("code Latex download content_copy expand_less") from the top of each `.tex` file before ingest.
5. **Build packets + slides + pacers.** Clone from L43 (3-period) or L51/L55 (single-period compressed). Preserve star styling on DOK-3 capstones and ⭐ on assessment-rehearsal items.

### Pitch framing (for the "other teachers can use" lens)

The packets need to be immediately usable by a teacher who didn't write them:

- Teacher packet carries `Questions to ask:` and `Adult role:` per phase (already in `packet_styles.framework_phase_header`).
- Do Now answer keys visible on teacher packet, hidden on student packet (existing convention).
- Pacer HTML is the self-contained "lesson plan in a browser tab" — another teacher opens it, hits the timer, and runs the period. Keep this promise.
- Rules cards are the per-lesson cheat-sheet. Write them so a substitute could teach from them.

## Topic 5 — BUILT (2026-04-20) but open flags before teaching

All 5 periods (L54 P1/P2/P3 + L51 + L55) committed as `fff7cd8`. NOT eye-checked. Before any period goes live:

1. **Eye-check L54 P2 teacher packet** — carries the Topic 5 DOK-3 spine (Q#41 half-life). Most important artifact in Topic 5.
2. **Browser-verify `L54_Pacer.html`** (3-tab) and `L51_Pacer.html` / `L55_Pacer.html` (single-pane, tab-stripped). Confirm timer + ⭐ styling renders.
3. **Clean 7 visuals flagged `needs_cleanup`** across L51 (2), L54 (3), L55 (2) checklists. See each `L5N_PN_Visuals_Checklist.md` for specifics.
4. **Registry has `-2`-suffixed duplicates** (SE+TE both got ingested). Not breaking anything, but clean when time permits.

## Topic 4 backlog — deferred past Topic 6

- **Lesson 4-4** (LEHS Q#19): `lesson_4-4_rational_expressions.{tex,pdf}` in repo.
- **Lesson 4-5** (LEHS Q#6, Q#7): `envAlg2_04_05_LessonPacket.{tex,pdf}`.
- **Topic 4 LEHS assessment day** — 8 Qs from `a2topic4assess.docx` (#2, 3, 4, 5, 6, 7, 15, 19).

## Topic 4-3 — BUILT but open flags (2026-04-20)

- Eye-check P2 teacher packet (DOK-3 Q#13 closure argument) + P3 teacher packet.
- Browser-verify `L43_Pacer.html`.
- Clean Example 6 SA/V diagram (`L43_P3_Visuals_Checklist.md` flagged).
- 4-1 open: q16 y-value `2/3` and q18 domain tail "real numbers except 0" both reconstructed — user eye-check.

## Roadmap

1. **Topic 6** (THIS NEXT SESSION) — 6-3/6-4/6-5 packets once TE files land.
2. **Topic 4 backlog** — 4-4, 4-5, Topic 4 assessment day.
3. **Trig SOH CAH TOA** — external-to-textbook; curated problem set needed.
4. **Eye-check + print prep** all built lessons (4-3, 5-1, 5-4, 5-5, 6-x).

End of school: **2026-06-20**.

## Class calendar pinned

- Two sections: Period A (one period behind Period F at start of Unit 4).
- Wednesday F = **45 min** — short variant with Explore cut 8 min.
- Solo teacher, class ≤10, ELL-heavy.

## Gotchas worth remembering

- Windows terminal prints UTF-8 math as mojibake in stdout; FILES are fine. Ignore the console display.
- `git mv` is preferred over delete+add for legacy moves (preserves history).
- Every builder should end with `emit_visuals_checklist(_ALL_IDS, "L{NN}_P{N}_Visuals_Checklist.md")`.
- `packet_styles.framework_phase_header` requires `dok`, `minutes`, `teacher_does`, `students_do`, `questions_to_ask`, `adult_role` — all keyword-only.
- Pacer HTML tabs: browser cache can show stale version. Hard refresh (Ctrl+F5).
- **Chat-UI chrome on pasted LaTeX** — strip lines before `\documentclass` before ingest. See `WIKI_UPDATES_PENDING.md` section 6.
- **SE+TE ingest creates `-2` duplicates** — reference only non-`-2` IDs in builders.
- **Item-analysis table parse failures silently default DOK to 2** — verify Savvas-declared DOK-3 items have `dok=3` in registry after ingest.
