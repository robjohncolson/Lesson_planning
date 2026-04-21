# Continuation Prompt — Lesson_planning

Paste into the next Claude Code / Codex session after `git pull`.

Canonical context lives elsewhere:
- `CLAUDE.md` — project rules, toolchain, class context, Klimsara pattern
- `git log --oneline -20` — session-by-session narrative
- `WIKI_UPDATES_PENDING.md` — Obsidian wiki updates to paste on home laptop
- `tagging/BATCH_SYNTHESIS.md` + `graph/` — the curriculum DAG, echo chains, coverage

This file carries only (a) the next concrete task and (b) open flags that aren't yet checked.

---

## Where we are (2026-04-21)

Topic 4 is **complete end-to-end**: L41 + L43 + L44 + L45 packets + L46 assessment-day shell + pacers + slides. Topic 6 (L63/L64/L65) and Topic 5 (L51/L54/L55) packets are built. All DOK-3 spines are Savvas-declared and rehearse specific assessment items. Unicode pre-render pass is live across every builder.

**New this session (2026-04-21):** built the **Curriculum DAG**. All 11 operational-spine lessons tagged with v2 schema fields (`role`, `standards`, `prereq_ids`, `rehearses`, `echoes`, `skill_tokens`). 148 items tagged, 11 assessment shells registered, 7 echo chains auto-discovered across the year. Tooling:
- `merge_tags.py` — fold `tagging/*_pilot.jsonl` into `registry.jsonl`
- `qb_graph.py` — emit `graph/coverage_report.md`, `graph/chains.md`, `graph/graph.html`
- `qb_append.py` — now validates v2 fields (`role` enum + five list fields)
- `questionbank/assessment_shells.jsonl` — forward-pointer targets for `rehearses`

**DAG-level findings** (see `tagging/BATCH_SYNTHESIS.md`):
- **DOK-3 flavors are lopsided.** Four archetypes surfaced (derive-from-constraint, prove-by-properties, model-then-extract, read-from-representation). Totals: 6/2/4/1. `read-from-representation` is a cold flavor (6-3-q15 only). Prove-by-properties doesn't appear until 4-3 — students meet proof-flavor DOK-3 mid-year.
- **Chain 1 runs through six lessons.** 3-5-q27 → 4-1-q17 → 5-1-q50 → 6-3-q54 → 6-4-q28/q33 → 6-5-q40. Same "extract a hidden variable from a model" archetype across polynomial → rational → rational-exponent → log → exponential-inverse representations. This is the year's structural spine.
- **Unit 4 has its own intra-unit chain** (rate-reciprocal: 4-1-q26 → 4-4-q26 → 4-5-q25).

**Nothing is eye-checked yet.**

## Next task (user pick)

In priority order:

1. **Eye-check the regenerated Word packets.** Critical files first:
   - `L54_P2_Teacher_Packet.docx` — Topic 5 DOK-3 spine (Q#41 half-life).
   - `L44_P1_Teacher_Packet.docx` — Topic 4 DOK-3 spine (Q#32 electrical resistance).
   - `L45_P1_Teacher_Packet.docx` — Topic 4 DOK-3 spine (Q#33 chemistry mixture).
   - `L46_P1_Teacher_Packet.docx` — 8-item intervention table for Topic 4 assessment day.
   - Every Topic 6 packet (`L63/L64/L65_P1_*`) — never eye-checked.
2. **Visual audit.** Savvas source PDFs are in repo. Verify flagged items per each `L*_Visuals_Checklist.md`.
3. **Browser-verify pacers.** Hard refresh (Ctrl+F5) to bypass cache.
4. **Act on DAG findings (optional but compounding).**
   - Plant a `read-from-representation`-flavor DOK-3 seed earlier (candidate: re-cast one existing Unit 5 item).
   - Name Chain 1 aloud to students when planting L51 q50 (Cylinder Capstone): "remember Storage Box? Same move."
   - Decide whether `4-3-q13` (prove-by-properties DOK-3) needs an earlier warm-up item in Unit 3.
5. **Tier-1 coverage-fill tagging** (~120 more items, ~4 hrs). See `tagging/PILOT_DEBRIEF_6-5.md` for the tier plan. Only worth doing before the DAG drives a curricular decision.

## Deferred (not blocking)

- **Topic 5 `-2`-suffixed registry rows.** Duplicate IDs from pre-2026-04-20 two-pass ingest. Harmless for `qb.get_for_packet` but should be cleaned. `qb_graph.py` currently counts both.
- **Assessment-shell backfill.** Topic 3/4/5/6 assessment items registered only for items referenced by `rehearses` in the 148-item pilot. A full shell pass is cheap and would make the DAG honest.

End of school: **2026-06-20**.

## Session gotchas worth re-reading

- Windows terminal prints UTF-8 math as mojibake in stdout; FILES are fine. Ignore console display.
- Every new builder MUST route prompt strings through `packet_styles.render_prompt()`. Raw `\frac`, `\sqrt`, `\log_` in a docx means the render step was skipped. (See wiki: `Unicode Pre-Render for docx`.)
- Every builder should end with `emit_visuals_checklist(_ALL_IDS, "L{NN}_P{N}_Visuals_Checklist.md")`.
- `packet_styles.framework_phase_header` requires all six keyword-only fields: `dok`, `minutes`, `teacher_does`, `students_do`, `questions_to_ask`, `adult_role`.
- **Chat-UI chrome** on pasted LaTeX — strip every line before `\documentclass` before ingest. Savvas SE `.tex` files routinely have 5 chrome lines; TE files are usually clean.
- **Item-analysis table failures fall through to inline DOK.** When `\begin{item-analysis}` is empty/malformed, DOK is read from the second arg of `\begin{practice}{N}{dok}` in the TE.
- Large pushes (100+ files) may hit `send-pack: unexpected disconnect`. Fix: `git config http.postBuffer 524288000` then retry.
- **Assessment day shell** is a separate artifact from the assessment itself. Pattern lives in `build_L46_P1_assessment_day.py` (Topic 4) and `build_L35_P4_assessment_day.py` (Topic 3).
- **Tag before edit.** When modifying a lesson's operational items, re-run `python merge_tags.py && python qb_graph.py` so the DAG matches reality. Pilot files under `tagging/` are the source of truth for v2 fields.
