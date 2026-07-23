# TikZ Regeneration Pilot Report (NT2)

**Scope:** Proof-of-approach for re-rendering the ~75 "tikz_regenerable" absent Savvas figures as
standalone compilable TikZ/LaTeX, into a staging area for later teacher eyeball + wiring.
**Nothing student-facing was changed.** All 8 pilot files live only in `inventory/tikz-staging/`.
`questionbank/registry.jsonl` was read-only; sha256 `b7f9a040…4e56b8` unchanged before and after.

## Pilot set (8 figures, 8/8 compile PASS)

| bank_id | lesson | type | file | compile | pdf bytes |
|---|---|---|---|---|---|
| 6-4-ex-1 | 6-4 | graph | `6-4-ex-1.tex` | pass | 69,004 |
| 6-4-ex-2 | 6-4 | graph | `6-4-ex-2.tex` | pass | 69,858 |
| 5-4-ex-1 | 5-4 | graph | `5-4-ex-1.tex` | pass | 59,161 |
| 4-3-savvas-concept-summary-lesson-4-3 | 4-3 | table | `4-3-savvas-concept-summary-lesson-4-3.tex` | pass | 73,525 |
| 5-4-savvas-q44 | 5-4 | table | `5-4-savvas-q44.tex` | pass | 53,910 |
| 6-5-savvas-q37 | 6-5 | table | `6-5-savvas-q37.tex` | pass | 48,152 |
| 5-5-savvas-q36 | 5-5 | diagram | `5-5-savvas-q36.tex` | pass | 50,215 |
| 6-3-ex-1 | 6-3 | diagram | `6-3-ex-1.tex` | pass | 55,111 |

Chosen to span the three concentration clusters (6-x, 4-3, 5-x) and all three regenerable figure
types (graph×3, table×3, diagram×2). Every id traces to a real Savvas registry `id`. Independently
re-compiled by the manager to a scratch dir (byte-identical, deterministic) and the two hardest
(thermometer diagram, log/exp reflection graph) plus the callout diagram were rendered to PNG and
visually confirmed to match the spec.

## What worked

- **Toolchain is ready.** MiKTeX pdflatex 4.23 with `standalone.cls`, `tikz.sty`, `pgfplots.sty`
  (compat 1.18) all present. A minimal `\documentclass[border=6pt]{standalone}` + `tikz`/`pgfplots`
  (+ `amssymb` for `\square`, + `booktabs`/`array` for tables) compiles every pilot figure headless
  with `-halt-on-error`.
- **Tables are near-mechanical.** The registry prompt text already carries the full table content
  (`TABLE: … END_TABLE` blocks with every cell). Transcribing into `booktabs` + `p{}` columns is
  almost deterministic. Lowest-risk, highest-throughput class.
- **Function graphs are highly templatable.** The 6-4/6-5/5-4/5-1/4-5 graphs are the same machine:
  plot 1–2 named functions in pgfplots, mark a couple of given points, draw an asymptote / `y=x`
  reference line, label the curves. `log_2` → `ln(x)/ln(2)`, radicals → `sqrt(...)`, reciprocals →
  `1/(...)`. One shared style block will drive the whole batch.
- **Annotation "diagrams" (callouts) regenerate cleanly** as TikZ nodes + curved `-Stealth` arrows;
  verbatim callout wording and the `\log_b x = y \iff b^y = x` definition reproduced exactly.
- **The genuine schematic diagram (three thermometers) regenerates** with correct C/F/K ranges and a
  single red dashed `0°C = 32°F = 273K` reference line aligning all three tubes.

## Fidelity notes vs. the prompt spec

- **The registry prompt is a sufficient spec for this subset.** For all 8, the figure's *defining*
  data (equations, every table cell, labeled axis/scale values) is present in the prompt text, so the
  re-render is faithful, not invented. This is exactly why these are classed `tikz_regenerable`.
- **Layout details not in the spec require interpretive choices — flagged, never fabricated:**
  - `5-5-savvas-q36`: tube proportions and intermediate tick spacing aren't specified; a per-unit
    linear scale was derived so the three reference marks align on the red line. All *labeled* ticks
    (−40/0/60, −50/32/150, 230/273/330) match the spec exactly.
  - `6-4-ex-1`: plotted continuous curves in addition to the discrete spec table points so the
    reflection across `y=x` reads visually. All marked points match the spec tables.
  - `6-4-ex-2` needed 3 label-position passes (asymptote captions overlapped ticks / clipped off
    frame) before both `x=0`/`x=-3` labels sat in clear whitespace. No data changed.
  - `5-4-savvas-q44` failed first compile (`\square` needs `amssymb`, not `amsmath`); fixed by adding
    the package. Recommend baking `amssymb` into the shared preamble for the full run.
- **Minor cosmetic residue:** on the thermometer, the Fahrenheit `32` label sits right on the dashed
  line (slightly crossed). Cosmetic only; fine for a staging pilot, trivially nudged before wiring.

## Which figure types resist clean TikZ regeneration

- **None of the 8 truly resisted.** Within the pilot, tables were trivial, graphs templatable,
  diagrams bespoke-but-doable.
- **The class that *will* resist is already excluded from the tikz set** and must NOT be auto-drawn:
  the **14 `source_pdf_required`** items (unlabeled figure dimensions, an un-equationed curve, a
  specific student's wrong work) — their defining data lives only in the original Savvas figure, and
  all 14 are the `essential` items. And the **48 irreplaceable photos**. The classification correctly
  keeps both out of the 75.
- **A "number line" figure type does not exist in the absent set.** The registry `visual_type` enum
  is `graph / photo / table / diagram / map / none`; no number-line instances to pilot. (Interval /
  inequality content, if any surfaces, would render as a short TikZ axis — no special tooling needed.)

## Remaining work: concrete plan + effort estimate

The tikz set is **75 rows = 71 unique ids** (duplicate registry rows inflate the row count; dedup
saves real work). Pilot completed 8 unique ids, leaving **63 unique** to generate/triage:

| batch | unique remaining | approach | est. effort |
|---|---|---|---|
| **A — Tables** | 21 (of 24) | booktabs transcription of `TABLE:…END_TABLE` blocks; near-mechanical | ~5 min each; ~3 Sonnet dispatches of 7–8 |
| **B — Function graphs** | 28 (of 31) | one shared pgfplots style macro, then per-figure plot+labels; cluster by lesson (6-4, 6-5, 5-4, 5-1, 4-5) | ~8–10 min each; ~4 dispatches |
| **C — Diagrams** | 5 (of 7) | bespoke TikZ (carnival-box `4-3-q36-partA-build`, log callouts `6-3-ex-4/5/6`, `6-3-concept-box`, `6-5-ex-4`) | ~15 min each; ~1 dispatch |
| **D — photo→tikz** | 3 | `4-4-savvas-q36`, `5-1-savvas-q45`, `6-4-savvas-q30` (seismograph) — confirm the numeric givens are in-text first | teacher-confirm then ~10 min each |
| **Reclassify — no figure** | 5 | the `has_visual`+`visual_type==none` quirk rows (`6-3-ex-3`, `6-3-tryit-3/4/5`, `6-4-tryit-1`) are pure numeric eval / blank-grid — **generate nothing; flag "no asset needed"** | triage only |
| **Reclassify — map→table** | 1 | `4-5-savvas-concept-summary-lesson-4-5-2` is a concept-summary table mislabeled `map` — treat as Batch A | folds into A |

**Sequencing recommendation:**
1. **Batch A first** (tables) — fastest, de-risks the pipeline, immediately useful.
2. **Build the shared graph macro once**, then **Batch B by lesson** — biggest chunk, but repetitive.
3. **Batch C diagrams** last — most per-figure TikZ effort.
4. **Triage D + the 6 reclassify rows in parallel** with a teacher pass; do NOT auto-generate the 5
   "none" rows or anything `needs_teacher_confirmation` without a human look.
5. **Hold the 14 `source_pdf_required` + 48 photos entirely** — out of scope for TikZ; they need the
   Savvas SE/TE source PDF or the original photo, and the 14 essential ones especially must not be
   approximated.

**Total remaining ≈ 63 unique figures ≈ 8–9 Sonnet dispatches of 6–8 each.** No blockers surfaced;
the approach is validated. Recommended next step: run **Batch A (tables)** as the first production
dispatch, carrying `amssymb` in the shared preamble.
