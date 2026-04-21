# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

Canonical context lives elsewhere:
- `CLAUDE.md` — project rules, toolchain, class context, Klimsara pattern
- `git log --oneline -20` — session-by-session narrative
- `WIKI_UPDATES_PENDING.md` — Obsidian wiki updates to paste on home laptop

This file carries only (a) the next concrete task and (b) open flags that aren't yet checked.

---

## Where we are (2026-04-21)

Topic 4 is **complete end-to-end**: L41 + L43 + L44 + L45 packets + L46 assessment-day shell + pacers + slides. Topic 6 (L63/L64/L65) and Topic 5 (L51/L54/L55) packets are built. All DOK-3 spines are Savvas-declared and rehearse specific assessment items. Unicode pre-render pass is live across every builder.

**Nothing is eye-checked yet.**

## Next task (user pick)

In priority order:

1. **Eye-check the regenerated Word packets.** Critical files first:
   - `L54_P2_Teacher_Packet.docx` — Topic 5 DOK-3 spine (Q#41 half-life).
   - `L44_P1_Teacher_Packet.docx` — Topic 4 DOK-3 spine (Q#32 electrical resistance).
   - `L45_P1_Teacher_Packet.docx` — Topic 4 DOK-3 spine (Q#33 chemistry mixture).
   - `L46_P1_Teacher_Packet.docx` — 8-item intervention table for Topic 4 assessment day.
   - Every Topic 6 packet (`L63/L64/L65_P1_*`) — never eye-checked.
2. **Visual audit.** Savvas source PDFs are in repo. Verify flagged items:
   - Topic 4: L44 visuals checklist (Q#32 circuit graph) + L45 (Q#33 chemist photo).
   - Topic 5: 7 flags on L51 (2), L54 (3), L55 (2) — see each `L5N_PN_Visuals_Checklist.md`.
   - Topic 6: per `L6N_P1_Visuals_Checklist.md`.
   - L43 P3 Example 6 SA/V diagram.
3. **Browser-verify pacers.** Hard refresh (Ctrl+F5) to bypass cache. Timer + ⭐ styling.
4. **4-1 reconstructed items.** q16 y-value `2/3` and q18 domain tail "real numbers except 0" need eye-check against Savvas source.

## Deferred (not blocking)

- **Topic 5 `-2`-suffixed registry rows.** Duplicate IDs from pre-2026-04-20 two-pass ingest. Harmless for `qb.get_for_packet` but should be cleaned. Topic 4 and Topic 6 are clean.

End of school: **2026-06-20**.

## Session gotchas worth re-reading

- Windows terminal prints UTF-8 math as mojibake in stdout; FILES are fine. Ignore console display.
- Every new builder MUST route prompt strings through `packet_styles.render_prompt()`. Raw `\frac`, `\sqrt`, `\log_` in a docx means the render step was skipped. (See wiki: `Unicode Pre-Render for docx`.)
- Every builder should end with `emit_visuals_checklist(_ALL_IDS, "L{NN}_P{N}_Visuals_Checklist.md")`.
- `packet_styles.framework_phase_header` requires all six keyword-only fields: `dok`, `minutes`, `teacher_does`, `students_do`, `questions_to_ask`, `adult_role`.
- **Chat-UI chrome** on pasted LaTeX — strip every line before `\documentclass` before ingest. Savvas SE `.tex` files routinely have 5 chrome lines; TE files are usually clean.
- **Item-analysis table failures fall through to inline DOK.** When `\begin{item-analysis}` is empty/malformed, DOK is read from the second arg of `\begin{practice}{N}{dok}` in the TE. Verified working on Topic 4-4 (table empty, DOK-3 items still populated correctly). Still verify Savvas-declared DOK-3 items have `dok=3` in the registry after any ingest.
- Large pushes (100+ files) may hit `send-pack: unexpected disconnect`. Fix: `git config http.postBuffer 524288000` then retry.
- **Assessment day shell** is a separate artifact from the assessment itself. Student packet = cover + policy + formula reference + tracker, zero assessment items. Teacher packet = 8-row Q#→lesson intervention table, "never say aloud" flagged. Pattern lives in `build_L46_P1_assessment_day.py` (Topic 4) and `build_L35_P4_assessment_day.py` (Topic 3).
