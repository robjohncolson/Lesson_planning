# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

Canonical context lives elsewhere:
- `CLAUDE.md` — project rules, toolchain, class context, Klimsara pattern
- `git log --oneline -20` — session-by-session narrative (what was built, when)
- `WIKI_UPDATES_PENDING.md` — Obsidian wiki updates to paste on home laptop

This file carries only (a) the next concrete task and (b) open flags that aren't yet checked.

---

## Where we are (2026-04-21)

Topic 6 (6-3/6-4/6-5) and Topic 5 (5-1/5-4/5-5) packets are **built but not eye-checked**. Topic 6 Form B assessment is trimmed to 8 items and compiled. Unicode pre-render pass is live across all builders (docx files no longer leak raw LaTeX).

## Next task (user pick)

In priority order:

1. **Eye-check regenerated Word packets.** Unicode render is live, so `log₃ x` and `⁶√(729a²⁴b¹⁸)` should display properly in Word. Critical files to open first:
   - `L54_P2_Teacher_Packet.docx` — carries the Topic 5 DOK-3 spine (Q#41 half-life).
   - `L63_P1_*`, `L64_P1_*`, `L65_P1_*` — every Topic 6 packet, never eye-checked.
2. **Visual audit.** Savvas source PDFs are now in the repo. Verify:
   - q15 graph (lesson TBD — check visuals checklists for `needs_cleanup`).
   - q54 Richter photo.
   - q28 sales-revenue photo.
   - 7 flags on Topic 5: L51 (2), L54 (3), L55 (2) — see each `L5N_PN_Visuals_Checklist.md`.
   - Example 6 SA/V diagram on L43 P3.
3. **Browser-verify pacers.** `L43_Pacer.html`, `L54_Pacer.html` (3-tab), `L51/L55/L63/L64/L65_Pacer.html` (single-pane). Timer + ⭐ styling. Hard refresh (Ctrl+F5) to bypass browser cache.
4. **4-1 reconstructed items.** q16 y-value `2/3` and q18 domain tail "real numbers except 0" need eye-check against Savvas source.

## Deferred (not blocking)

- **Topic 5 `-2`-suffixed registry rows.** Duplicate IDs from pre-2026-04-20 two-pass ingest. Harmless for `qb.get_for_packet` but should be cleaned. Topic 6 lessons are clean (ingested after the dedup fix).
- **Topic 4 backlog.** 4-4 (LEHS Q#19), 4-5 (LEHS Q#6, Q#7), Topic 4 LEHS assessment day (8 Qs). Source LaTeX + PDFs already in repo.
- **Trig SOH CAH TOA** — external-to-textbook, needs curated problem set.

End of school: **2026-06-20**.

## Session gotchas worth re-reading

- Windows terminal prints UTF-8 math as mojibake in stdout; FILES are fine. Ignore console display.
- Every new builder MUST route prompt strings through `packet_styles.render_prompt()`. Raw `\frac`, `\sqrt`, `\log_` in a docx means the render step was skipped. (See wiki: `Unicode Pre-Render for docx`.)
- Every builder should end with `emit_visuals_checklist(_ALL_IDS, "L{NN}_P{N}_Visuals_Checklist.md")`.
- `packet_styles.framework_phase_header` requires all six keyword-only fields: `dok`, `minutes`, `teacher_does`, `students_do`, `questions_to_ask`, `adult_role`.
- **Chat-UI chrome** on pasted LaTeX — strip every line before `\documentclass` before ingest.
- **SE+TE ingest dedupes practice/example/try-it blocks by number** (fixed 2026-04-20). Lessons ingested before that may have `-2`-suffixed registry rows; reference non-`-2` IDs in builders for those.
- **Item-analysis table parse failures** silently default every practice item to DOK 2. After any ingest, verify Savvas-declared DOK-3 items have `dok=3` in the registry.
- Large pushes (100+ files) may hit `send-pack: unexpected disconnect`. Fix: `git config http.postBuffer 524288000` then retry.
