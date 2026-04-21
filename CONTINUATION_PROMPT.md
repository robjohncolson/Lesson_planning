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

**New in 2026-04-21 session:** built the **Curriculum DAG**. 148 operational-spine items tagged with v2 schema fields (`role`, `standards`, `prereq_ids`, `rehearses`, `echoes`, `skill_tokens`). 11 assessment shells registered, 7 echo chains auto-discovered. Two teacher-facing callback scripts drafted (`graph/chain1_callbacks.md`, `graph/chain2_callbacks.md`).

**New in 2026-04-22 session (T1 polish pass — Sonnet impl, human validation):**
- **Dedup:** 3 `-2`-suffix duplicate rows dropped, 4 reference rewrites, registry 1054 → 1051. Idempotent on re-run.
- **T1 coverage-fill:** 475 additional pool items tagged across 11 lessons (`tagging/{lesson}_t1_coverage.jsonl`), bringing merged-view total to 674. Pool items get `role=explore-practice` + standards + skill_tokens; no prereq/rehearses/echoes (those stay spine-only).
- **`qb_diagnose.py`:** three reports under `graph/`:
  - `skill_bridge_gaps.md` — 27 gaps where DOK-3 drivers use skills no earlier-role item in the lesson exercises.
  - `nominal_rehearsals.md` — 1 mismatch (a token-glossary issue worth resolving: `translate-parent-function` vs `describe-translation`).
  - `redundant_practice.md` — 88 redundant groups with swap candidates from the T1 pool.
- **`merge_tags.py` defects fixed:** glob now matches `*_pilot.jsonl` AND `*_t1_coverage.jsonl` (was dropping 504 T1 rows silently); normalizes `rehearses: "string"` → `rehearses: [list]` at merge time to bridge early-vs-late pilot schema.
- **Codex validation timed out** at 600s on a 7-point checklist; validation done inline instead. If dispatching Codex for multi-step validation, chunk into smaller calls.

Tooling:
- `merge_tags.py` — fold `tagging/*_pilot.jsonl` + `tagging/*_t1_coverage.jsonl` into `registry.jsonl`
- `qb_graph.py` — emit `graph/coverage_report.md`, `graph/chains.md`, `graph/graph.html`
- `qb_diagnose.py` — emit skill-bridge / nominal-rehearsal / redundant-practice reports
- `qb_append.py` — validates v2 fields (`role` enum + five list fields)
- `dedup_registry.py` — idempotent `-2`-suffix dedup
- `generate_t1_coverage.py` — rescaffolds T1 coverage files from registry
- `questionbank/assessment_shells.jsonl` — forward-pointer targets for `rehearses`

**DAG-level findings** (see `tagging/BATCH_SYNTHESIS.md`, `tagging/T1_PLAN.md`, wiki: `Curriculum DAG`):
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
5. **Act on diagnostic reports.** Three concrete classes of edit, each from an existing `graph/` report:
   - `skill_bridge_gaps.md` — 27 gaps. For each DOK-3 driver skill with no in-lesson rehearsal, decide: swap a Practice item in, or teach the skill explicitly in Launch.
   - `redundant_practice.md` — 88 groups. Drop a redundant item, swap in a pool candidate that adds a DOK-3-needed token.
   - `nominal_rehearsals.md` — 1 mismatch. Resolve the `translate-parent-function` ↔ `describe-translation` token-glossary question.
6. **T2/T3 auto-tag pass** (~650 DOK-1 Practice + Blooket leaves). Scripted regex tagging. Only worth running if diagnostic coverage still shows blind spots after the T1 pass.

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
