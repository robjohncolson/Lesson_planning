# L44_P1 Back-Extraction Scouting Report

**Date:** 2026-04-22
**Scouted by:** Claude Code (Sonnet 4.6)
**Source files:** `tex/L44_P1_student.tex` (8009 bytes), `tex/L44_P1_teacher.tex` (19018 bytes)
**YAML:** `lessons/L44_P1.yaml` (259 lines)
**Regen output:** `tex/L44_P1_student_regen.tex` (8216 bytes), `tex/L44_P1_teacher_regen.tex` (16998 bytes)
**pdflatex exit status:** 0 on both regen files (clean compile, 4 pages student / 9 pages teacher)

---

## What extracts cleanly (1:1 mapping)

1. **All structural metadata** — `lesson_id`, `title`, `label`, `period`, `cadence`, `objectives`, `framework_header`. Exact text recovery; table layout identical.
2. **Framework phase blocks** (`phases:`) — All five phases (`do_now`, `launch`, `explore`, `share_summary`, `exit`) with `framework_tag`, `dok`, `minutes`, `teacher_does[]`, `students_do[]`, `questions_to_ask[]`, `adult_role` recovered verbatim. The generator's `\frameworkphaseheader` + `\phasetag` macros reproduce the canonical output exactly.
3. **Callout blocks** — All 5 callouts (calloutgreen rules, calloutred warning, calloutpeach bridge, calloutblue bridge script, do_now bridge) recovered via `callouts: [{section, title, color, body}]`. Section-anchoring works correctly.
4. **Preflight block** — Teacher-only `preflight:` maps perfectly via `\IconPin\ ` + callout.
5. **Item ID list and ordering** — All 8 item IDs (`do_now`, 6 explore, 1 reinforcement) present in registry; generator correctly sequences and labels them.
6. **Sentence frames** — Single-frame pair + whole-class line recovers cleanly.
7. **Exit ticket** — 3 fill-in stems recover verbatim.
8. **Teacher callouts** (IEP / ELL / period variants) — All 3 blocks recover cleanly on the trailing `\clearpage`.

---

## What requires human judgment (fits schema but needs care)

1. **`\promptplaceholder{...}` vs `[IMAGE: ...]` encoding** — The canonical student tex uses a hand-styled `\promptplaceholder` macro (framed box with centered italic) to display image captions inline. The registry stores the same caption as plain `[IMAGE: ...]` text. The regen emits the registry literal, losing the visual framing. To preserve it, the generator would need to detect `[IMAGE:` tags in registry prompts and wrap them in `\promptplaceholder{...}`.
2. **`\phaseitems` vs `\begin{itemize}`** — The canonical teacher tex uses a hand-defined `\phaseitems{...}` convenience macro; the generator emits `\begin{itemize}[...]\item...\end{itemize}` directly. Both compile identically, but diffs are noisy.
3. **Teacher sentence-frames list markup** — Canonical teacher has `\begin{itemize}...\item` for multiple frames; generator emits plain newline-separated frames inside `sentenceframebox`. Compiles fine but typographic detail differs.
4. **`do_now` bridge-script placement** — In canonical teacher, the `\begin{callout}{\IconMic\ BRIDGE SCRIPT}` appears *after* the Do Now bank item; the generator places do_now-section callouts *before* bank items (callouts_by_section ordering). This is a schema gap: no way to control intra-phase ordering of callouts vs items.
5. **YAML `dok` values with `--` dashes** — `"1--2"` and `"2--3"` are YAML strings; the generator passes them as-is to `\frameworkphaseheader`. Canonical uses `1--2` LaTeX em-dash form. These match but are fragile — any integer-only validation would break them.

---

## What is lost in round-trip (pedagogically meaningful)

1. **`\resistancefigure` custom TikZ** — The canonical teacher tex defines a full TikZ circuit diagram (`\resistancefigure`) for Practice #32 showing two labeled circuit types (capacitor symbol for A, resistor box for B) with node-positioned resistance expressions. The registry stores this as `[GRAPH / TIKZ figure]` — a text placeholder. The regen student and teacher both render this as literal text inside `\begin{center}...\end{center}`. **The circuit figure is completely absent from the regen PDF.** This is the biggest pedagogical loss: students see `[GRAPH / TIKZ figure]` rather than the circuit diagram. To fix, the `visuals:` schema field (already used in L41_P2 for `pgfplot` and `tikz_boxes`) would need to support raw TikZ via a `kind: raw_tikz` type, and the registry would need to reference that visual by name.
2. **Answer keys in teacher edition** — Canonical teacher has inline `\teacheranswerbox` blocks with populated answers (e.g., `a. \(\dfrac{x+7}{(x+2)(x-3)}\)...`). Regen emits `(no answer key --- verify before class)` for every item because the registry's `answers:` field for L44 items is `[]`. The answer content exists only in the hand-authored tex, not the registry. To recover, the registry `notes` field (or a new `teacher_answers` field) would need to be populated for each item.
3. **`\IconMic`, `\IconClipboard`, `\IconTarget` macros** — Canonical teacher defines and uses three extra icon macros in the preamble. The generator emits only `\IconCheck` and `\phasetag`. The regen teacher callout uses `\IconMic\` in a callout title; this compiles because `\IconMic` is defined in `preamble.sty` (or falls back gracefully), but it is not declared in the generator preamble emit. Verify `preamble.sty` covers these before trusting the regen.
4. **Explore section inline instructions** — Canonical student tex has two `\textit{...}` italic instruction lines immediately below the `\sectionbanner{EXPLORE}` (work-with-partner and 45-min variant note). These are hand-authored prose not captured in any schema field. The regen omits them entirely. A `section_notes:` or `explore_instructions:` YAML field would be needed.
5. **`\checkbox` macro for reinforcement item** — Canonical student uses a hand-defined `\checkbox` TikZ macro to render selectable boxes for the compound-fraction multi-select (#34). The regen emits `\item[\square]` (pulled from registry prompt formatting). Both compile, but the checkbox appearance differs.

---

## Recommendation: Feasibility for bulk conversion

| Category | Lessons | Score | Notes |
|---|---|---|---|
| **Clean / high-confidence** | L41_P2 (already YAML-native), APStats_6-4_P1 (YAML-native) | — | Baseline: generator was designed for these |
| **Needs-touch** | L44_P1, lessons with TikZ-free items and populated answer keys | **7/10** | ~2 h per lesson: populate registry `notes` with answers, add `explore_instructions` field |
| **Requires-rewrite** | Any lesson with custom TikZ figures (circuits, graphs, box diagrams) | **4/10** | Must extend generator with `kind: raw_tikz` visual type OR pre-render TikZ to images |

**Bulk conversion of the other 17 lessons:** estimated 12 are "needs-touch" (single-file structure, no heavy custom TikZ), 5 are "requires-rewrite" (lessons with TikZ visuals similar to the resistance figure). Do not bulk-convert; do one lesson per pending edit as CLAUDE.md recommends.

---

## Top 3 extraction wins

1. **Phase blocks are a perfect fit** — All framework phase data (`teacher_does`, `students_do`, `questions_to_ask`, `adult_role`) extracts as valid YAML with no schema gaps. 0 manual judgment calls on L44.
2. **Callout blocks with section anchors** — Section-anchored callouts (including the do_now bridge script, which is teacher-only by convention) survive round-trip. The `callouts:` list with `section:` keys handles even non-standard teacher-only callouts cleanly.
3. **Exit ticket and sentence frames** — Both extract as direct YAML strings; generator emits them identically. These are the most student-visible elements and they round-trip correctly.

---

## Top 3 extraction losses

1. **Inline TikZ figures in registry prompts** — The `[GRAPH / TIKZ figure]` placeholder in the registry cannot regenerate the `\resistancefigure` circuit diagram. This is the single highest-priority gap for Q#32-class problems.
2. **Answer keys absent from registry** — All L44 `answers: []` and `notes:` fields are unpopulated. Teacher regen is functionally useless for answer-key lookup until registry is backfilled. Estimate: 30 min per lesson to transcribe from TE PDF.
3. **Free-form section prose** (explore instructions, image-caption styling) — Any hand-authored `\textit{...}` instructions or `\promptplaceholder` styled captions between phase banners and bank items are invisible to the schema. A `section_notes:` field per phase and a `[IMAGE:]` → `\promptplaceholder` transform in the generator would close this gap.
