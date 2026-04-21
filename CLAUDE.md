# Lesson_planning — Project Guidance

High school Algebra 2 lesson materials — Topic 3 (Polynomials) closing, Topic 4 (Rational Functions + Inverse Variation) beginning, then selected 5-x / trig / 6-x through end of school year (2026-06-20).

## Hard rules

- **Savvas-only for student-facing work.** Every problem, Try It, Do Now, Practice, or Exit item on a student packet MUST trace to a Savvas bank ID in `questionbank/registry.jsonl`. No fabricated items. If the right Savvas item isn't in the bank, ingest it first (screenshots live in `questionbank/images/`).
- **Single-DOK3 spine, per period.** One DOK-3 driver per period, self-contained with all rules printed on the page. A lesson's P3 may have no DOK-3 driver (pure DOK-2 mastery day) when P2 already carried the spine. See wiki `concepts/Single-DOK3 Lesson Spine.md`.
- **Summary exit, not CER.** Walk-out tasks recap the day's learning with fill-in + one "biggest thing learned" sentence. Full CER writing in 5 min is unrealistic.
- **Blooket is DEPRECATED** for all lessons from Unit 4 onward. Do Now now carries DOK-1 recall load. Existing Blooket CSVs moved to `legacy/`.
- **Try-Its stay in-class as Think-Pair-Share.** Student homework completion is unreliable. The Lynn DOK framework wants 35–40 min of student heavy lifting in Explore — Try-Its fill that. Back-of-packet HW is OPTIONAL REINFORCEMENT only.
- **Klimsara-adapted 3-period cadence** (default going forward). Each lesson = 3 teaching periods. Teacher models ONE Example in Launch; Explore is the 35-min TPS block; student-centered, not teacher-modeled-end-to-end.
- **Framework phases** (non-negotiable, per `DOKframework.txt`): Do Now (≤10) · Launch (10–15) · Explore (35–40) · Share/Summary (5–15) · Exit Ticket. Teacher packet carries explicit `Questions to ask:` and `Adult role:` per phase for evaluators.

## Current structure — Klimsara-adapted (Unit 4+)

Each lesson picks ONE cadence:

- **Full 3-period** = `L{NN}_P1_*` + `L{NN}_P2_*` + `L{NN}_P3_*`. Pacer has three sub-tabs.
- **Single-period quick** = `L{NN}_P1_*` only. Condensed Klimsara, DOK-3 spine inside the one period. Functionally complete — NOT a stub awaiting P2/P3. File naming keeps `_P1_` for builder-output consistency.

To tell which cadence a lesson uses, read the builder docstring (`build_L{NN}_P1_packets.py` line 1–24). Assessment-day shells follow `L{topic_close+1}_*` (e.g. `L35_P4_*`, `L46_*`).

The three-period template below describes the full cadence:

| Period | Role | DOK arc | Typical Explore load |
|---|---|---|---|
| **P1** | Conceptual introduction | 1 → 2 | Do Now (bridge) + 2 Examples modeled + 5–7 Practice/Try-It items in TPS |
| **P2** | Applications + DOK-3 spine | 2 → 3 | Bridge + 1 Example modeled + 4 Practice + **⭐ DOK-3 driver** |
| **P3** | Mastery / assessment-critical | 2 | Bridge + 2 Examples paired in Launch + 5–6 Practice (assessment-aligned) |

**Wednesday F 45-min variant**: Explore cut to 25 min (drop 2 practice items), Launch/Share/Exit unchanged. Framework phases never cut.

### Lesson 3-5 (closed)

Originally 8 days. Retired to `legacy/`. Replaced by Klimsara close-out:

| Period | File prefix | DOK-3 driver | Content |
|---|---|---|---|
| P2 (Tue 4/28) | `L35_P2_*` | — | Multiplicity + factored-form graphing |
| P3 (Wed 4/29) | `L35_P3_*` | **Practice #27 (Storage Box)** | Real+complex zeros + modeling |
| P4 (Thu 4/30) | `L35_P4_*` | — | Topic 3 Assessment (11 Qs, external `a2topic3assess.docx`) |

### Lesson 4-1 (ready, Fri F / Mon A start)

| Period | File prefix | DOK-3 driver | Content |
|---|---|---|---|
| P1 | `L41_P1_*` | — | Inverse variation introduction (xy = k, y = k/x) |
| P2 | `L41_P2_*` | **Practice #26 (Ramón road trip — direct-vs-inverse)** | Applications + DOK-3 performance task |
| P3 | `L41_P3_*` | — | Reciprocal function + translations (**assessment-critical**: Topic 4 LEHS Q#3 + Q#5) |

## Naming conventions

- **Artifacts:** `L{NN}_P{N}_{Do_Now,Student_Packet,Teacher_Packet,Slides,Visuals_Checklist}.{docx,pptx,md}`. Replaces legacy `Day_N_*`.
- **Bank IDs:** `{lesson}-savvas-q{N}` for practice items (e.g. `4-1-savvas-q26`); longer auto-slugs for Examples/Try-Its/TE addendums.

## Standard toolchain

- `qb.py` — registry accessor. `qb.get_for_packet(ids)` wires items into builders. `qb.visuals_for(ids)` + `qb.write_visuals_checklist(ids, path)` emit pre-print checklists.
- `qb_append.py` — validates + appends registry entries. Required fields: `lesson`, `prompt`, `dok`. Optional schema includes `visual_type` (enum: `none`/`photo`/`graph`/`table`/`diagram`/`map`), `visual_needs_cleanup` (bool), `visual_clean_asset` (path).
- `generate_practice_skeletons.py` — given a lesson's calibration file, emits pre-filled JSON stubs for every Savvas practice item. Cuts per-item ingest time from ~90s to ~20s. `python generate_practice_skeletons.py <lesson>` writes `skeletons/<lesson>_practice_skeletons.json`.
- `packet_styles.py` — shared docx formatting helpers + `framework_phase_header` (with DOK/minutes/teacher_does/students_do/Qs/adult_role) + `emit_visuals_checklist()` hook for builders.
- `build_L{35,41}_P{N}_packets.py` — lesson builders. Each emits Do Now + Student Packet + Teacher Packet + Visuals Checklist.
- `build_L{35,41}_slides.py` — per-lesson slide decks (one builder, N deck functions).
- `L{35,41}_Pacer.html` — single-file pacer per lesson, 3 sub-tabs (one per period), countdown timer, inline teacher scripts / answer keys / rules / bridges / warnings.
- `backfill_visuals_4-1.py` — historical one-off that populated visual_type fields on already-ingested 4-1 items. Kept for reference; re-runnable.
- `legacy/` — retired Day 2-8 artifacts + Blooket CSVs from pre-Klimsara Lesson 3-5.

## Class context (as of 2026-04-20)

- Two sections: **Period A** and **Period F**.
- **Week of 2026-04-27 schedule** (saved in project memory): Mon A 65 / Tue F 65 + A 55 / Wed A 65 + F **45** / Thu F 65 + A 55 / Fri F 65.
- **Period A** is one period behind Period F at start of 3-5 close-out. Both finish Topic 3 Thu 4/30. Period F starts 4-1 on Fri 5/1; Period A starts 4-1 on Mon 5/4.
- **Wednesday F = 45 min** — short variant with Explore cut.
- **Solo teacher, class ≤10.** No aide-based release valves. Single-teacher circulation (4–6 laps during Explore).
- **ELL-heavy** — sentence frames on student packet are non-negotiable.

## Assessment coverage

- **Topic 3 assessment (Thu 4/30)** — `a2topic3assess.docx`. 11 Qs spanning 3-1 through 3-5. Of these, 4 are Lesson 3-5 content: Q#2 (conjugate pairs — preped via Tue→Wed bridge prompt), Q#5 (zeros + end behavior), Q#6 (Lucy's tray volume model — paralleled by Storage Box #27 on Wed), Q#10 (identify zeros).
- **Topic 4 LEHS 8-Q assessment** — `a2topic4assess.docx`, 8 selected items: #2, #3, #4, #5, #6, #7, #15, #19. Of these, 2 are Lesson 4-1 content: Q#3 (H/V asymptotes, from Ex 4/5), Q#5 (translation description, from Ex 5). **Practice #19 is the rehearsal item** for these.

## Related wiki pages (obsidian-wiki, home laptop)

- `concepts/Klimsara-Adapted Lesson Pattern.md` — 3-period template, phase timings, TPS rule, Wed-F variant
- `concepts/Single-DOK3 Lesson Spine.md` — updated: per-period, not per-lesson
- `concepts/Self-Contained Pacer Pattern.md` — v3 tabbed pattern
- `concepts/Do Now A-B-C Framework.md` — the school's Do Now sub-phasing convention

---

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Lesson_planning** (29 symbols, 71 relationships, 6 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Lesson_planning/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Lesson_planning/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Lesson_planning/clusters` | All functional areas |
| `gitnexus://repo/Lesson_planning/processes` | All execution flows |
| `gitnexus://repo/Lesson_planning/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->