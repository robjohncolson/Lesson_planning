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

## Next task: Lesson 4-3 packet build

**Lesson 4-3 bank is ingested** (70 items, committed). Next: build the 3-period Klimsara packets + slides + pacer, same pattern as L41.

### Known before starting

| Decision | Value |
|---|---|
| **DOK-3 driver** (single-spine, P2) | **Practice #13** — the only Savvas-declared DOK-3 item; anchors to Example 5 (Divide Rational Expressions). Multiplies rational expressions through a specific algebraic manipulation. |
| **Assessment-critical period** | **P3** — Topic 4 LEHS 8-Q assessment items #2 (domain), #4 (simplify + domain) both come from 4-3 Examples 1 and 2. Lean P3 hard on Ex 2 simplification + domain restrictions. |
| **Likely P1 scope** | Example 1 (write equivalent rational expressions) + Example 2 (simplify). Foundation for domain work. |
| **Likely P2 scope** | Example 3 (multiply) + Example 4 (multiply by polynomial) + Example 5 + ⭐ DOK-3 Practice #13. |
| **Likely P3 scope** | Example 6 (division modeling, SA/V ratio) + Concept Summary review + assessment-aligned Practice items (#2, #4 prep). |

### Workflow

Copy the L41 builder pattern:
- `build_L43_P1_packets.py`, `build_L43_P2_packets.py`, `build_L43_P3_packets.py`
- `build_L43_slides.py` (3 deck functions)
- `L43_Pacer.html` (single file, 3 tabs)

Phase timings per the Klimsara template (Do Now 5, Launch 12, Explore 33, Share 5, Exit 2–3). Framework fields (DOK / minutes / teacher_does / students_do / Qs / adult_role) per `DOKframework.txt`.

### Open flags carried from prior ingests

- **4-1 q16** — y-value reconstructed as `2/3` (source image cut off). User to eye-check.
- **4-1 q18** — domain tail reconstructed as "real numbers except 0". User to eye-check.
- **4-3 Practice #1-#10** — concept-review items in SE not in TE; not yet ingested. Low priority unless a packet needs them.
- **4-3 Example 6** — one image placeholder (rectangular prism + cylinder diagrams). Manual image staging if the packet uses it.

## Roadmap after 4-3

1. **4-4** (Topic 4 LEHS Q#19: length from area/width). Has `lesson_4-4_rational_expressions.{tex,pdf}` already in repo as reference.
2. **4-5** (Topic 4 LEHS Q#6 solve rational equation, Q#7 work-rate). Klimsara reference: `envAlg2_04_05_LessonPacket.{tex,pdf}`.
3. **Topic 4 LEHS assessment day** — 8 Qs from `a2topic4assess.docx` (#2, 3, 4, 5, 6, 7, 15, 19). Build an L4X_Assessment_Day wrapper like `L35_P4_*`.
4. **Unit 5** (5-1 quick, 5-4, 5-5 quick) — pilot the unit-at-a-time Gemini/GPT ingest if 4-3/4-4/4-5 go smoothly.
5. **Trig SOH CAH TOA** — external-to-textbook topic. Will need a curated problem set.
6. **Unit 6** (6-3, 6-4, 6-5).

End of school: **2026-06-20**.

## Class calendar pinned

- Week of 4/27 (Topic 3 close-out): Mon A 65, Tue F 65 + A 55, Wed A 65 + F **45**, Thu F 65 + A 55, Fri F 65.
- Thursday 4/30: Topic 3 Assessment both sections.
- Friday 5/1: Period F starts L41 P1.
- Monday 5/4: Period A starts L41 P1.
- After L41: both sections on L43 (this session's build).

## Gotchas worth remembering

- Windows terminal prints UTF-8 math as mojibake in stdout; FILES are fine. Ignore the console display.
- `git mv` is preferred over delete+add for legacy moves (preserves history).
- Every builder should end with `emit_visuals_checklist(_ALL_IDS, "L{NN}_P{N}_Visuals_Checklist.md")`.
- `packet_styles.framework_phase_header` requires `dok`, `minutes`, `teacher_does`, `students_do`, `questions_to_ask`, `adult_role` — all keyword-only.
- Pacer HTML tabs: browser cache can show stale version. Hard refresh (Ctrl+F5).
