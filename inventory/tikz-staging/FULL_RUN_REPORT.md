# TikZ Regeneration — FULL RUN Report (NT2)

Follows the 8-figure pilot (see `PILOT_REPORT.md`). This run completes the remaining
tikz-regenerable Savvas figures into the staging area for teacher eyeball + later wiring.
**Nothing student-facing changed.** All work is under `inventory/tikz-staging/` only.
`questionbank/registry.jsonl` sha256 `b7f9a040…4e56b8` unchanged before and after. No git, no network.

## 71-id master accounting (see `MANIFEST.json`)

The tikz_regenerable universe is **71 unique ids** (75 registry rows; 4 are duplicate rows).
Every one of the 71 is listed in `MANIFEST.json` with a `status`. Clean partition:

| status | count | which |
|---|---:|---|
| `regenerated+compile-pass` | 63 | 8 pilot + 22 Batch A + 25 Batch B + 8 Batch C/D |
| `reclassified-map->table` | 1 | `4-5-savvas-concept-summary-lesson-4-5-2` (was `visual_type=map`; rendered as a Words/Algebra table, compiles pass) |
| `held-teacher` | 2 | `4-3-savvas-q36-partA-build`, `5-1-savvas-teacher-edition-learntogether-les-5` |
| `no-asset` | 5 | `6-3-ex-3`, `6-3-tryit-3`, `6-3-tryit-4`, `6-3-tryit-5`, `6-4-tryit-1` |
| **TOTAL** | **71** | |

**Regenerated & compiling total = 64** (the 63 `regenerated+compile-pass` **plus** the 1
`reclassified-map->table`, which also compiles). 64 compiling + 5 no-asset + 2 held = **71.** ✓

**Out of scope (NOT in the 71, untouched):** the 14 `source_pdf_required` (all the `essential`
items) and the 48 irreplaceable photos. These need the Savvas SE/TE PDF or the original photo and
must not be approximated.

## Per-batch compile tallies

| batch | scope | result |
|---|---|---|
| Pilot | 8 (graph×3, table×3, diagram×2) | **8 pass** |
| A — Tables | 22 (incl. the map→table reclass) | **22 pass**, 0 held |
| B — Graphs | 26 | **25 pass, 1 held** |
| C/D — Diagrams | 9 (6 diagrams + 3 photo→tikz schematics; +`4-3-ex-6`) | **9 pass**, 0 held |
| **Regenerated total** | | **64 .tex → 64 non-empty .pdf** |

**Manager re-verification:** the manager independently re-compiled a spot-check sample from every
batch to a scratch output dir (byte-identical, deterministic) — pilot ×8, Batch A ×4, Batch B ×4,
Batch C/D ×9 — all `rc=0`, non-empty PDFs. Every id was traced to a real Savvas registry `id`.
Selected graphs/diagrams/tables were rendered to PNG and visually confirmed to match the spec.

## Batch-D pre-check verdict (photo→tikz)

The manager read each of the 3 photo-classified rows and checked whether the figure's *defining*
givens live in the prompt text (regenerable) or only in the original photo (hold). **All 3 had their
givens fully in-text → all 3 regenerated (0 held):**

| id | defining givens | verdict |
|---|---|---|
| `4-4-savvas-q36` | lens equation `1/f=1/d_i+1/d_o` + all distances in text; image is a *labeled* optics schematic (Object, Lens, Image screen, d_o, d_i, f) | **in-text → regenerated** |
| `5-1-savvas-q45` | box dims `x`,`x`,`2x` + volume 3,456 in³ all in text | **in-text → regenerated** |
| `6-4-savvas-q30` | magnitude formula + A/T/D givens in text; F/E/S/arc-ES geometry fully described in prose | **in-text → regenerated as schematic** (flagged `needs_teacher_confirmation`) |

## Interpretive choices / teacher-judgment items

All regenerations used only data present in the prompt text; no problem values were fabricated.
Two regenerated-and-compiling figures carry a teacher flag in `MANIFEST.json` (compile fine, but a
human should confirm before wiring):

- **`4-3-ex-6` — needs_teacher_disambiguation.** Source says "rectangular prism with a **square
  base**"; rendered as a **cube** (all edges `2x`) because the given volume `(2x)^3` implies
  height = base side = 2x. The single figure shows **both** package options (Option 1 prism +
  Option 2 cylinder `r=x, h=2x`), as the "cylinders or rectangular prisms?" prompt compares both.
  Schematic drawing-scale constants (ellipse/arc radii) are layout picks, not problem data.
- **`6-4-savvas-q30` — needs_teacher_confirmation.** Seismograph cutaway is schematic; E/S placement
  on the surface arc is illustrative.

Other non-fabricating interpretive notes (full detail per-figure in `MANIFEST.json`):
- Batch B reverse-engineered closed forms from given value tables where the prompt supplied points
  (`6-4-savvas-q8` → `h=10^{x-2}`, `g=log x+2`; `6-4-savvas-q29` → `r=90-25log(t+1)`), each verified
  against every given row before plotting; rational/radical graphs (`4-5-ex-3`, `5-4-ex-3`) split at
  named vertical asymptotes with domain clipping.
- **Minor cosmetic to fix before wiring:** `4-5-savvas-concept-summary-lesson-4-5-2` (map→table) —
  the Algebra column slightly overflows/clips at the right edge (e.g. "Domain: x≠0" truncated).
  Needs a `p{}` width tweak. Compiles pass; content is present, just clipped in the tight standalone
  crop.
- Two decorative-art omissions (noted in manifest): `6-3-ex-6` (cracked-landscape drawing) and
  `5-1-savvas-q45` (gifts-flowing-out art) — only the data-bearing figure element was drawn.

## Held items (produced no figure — correct, per no-fabrication rule)

- **`4-3-savvas-q36-partA-build`** — its own prompt ("Write the rational expression for the
  probability of winning") states no carnival-box dimensions; the defining data lives only in the
  sibling `4-3-savvas-q36` figure (itself an irreplaceable photo). Held for teacher/source.
- **`5-1-savvas-teacher-edition-learntogether-les-5`** — a cube-wrapping word problem
  (`384=6(x+3)^2`); no function/table/point set for a coordinate graph is named in text. Held.

## Recommendation: `amssymb` in the shared preamble

Every staging snippet carries `\usepackage{amssymb}` in its own standalone preamble (needed for
`\square` answer boxes in the yes/no and complete-the-table figures). **`tex/preamble.sty` was NOT
edited** — it is student-facing/canonical. Recommendation for the later teacher-gated wiring step:
add `\RequirePackage{amssymb}` to `tex/preamble.sty` (or confirm it is already transitively loaded)
before any of these figures are `\input` into a shipped packet, so `\square` resolves in the packet
build. This is a one-line integration change to be made by the teacher/Fable pass, not here.

## Integrity / scope

- `questionbank/registry.jsonl` sha256 **byte-unchanged**: `b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8`.
- **Only `inventory/tikz-staging/` was created/modified.** `git status tex/ questionbank/` is clean —
  nothing student-facing moved. No git commands mutated the repo; no network/cloud.
- Deliverables under `inventory/tikz-staging/`: 64 `.tex` + 64 `.pdf`, `MANIFEST.json` (71-id master),
  `PILOT_REPORT.md`, `FULL_RUN_REPORT.md`, and the per-batch manifests
  (`BATCH_A_manifest.json`, `BATCH_B_manifest.json`, `BATCH_CD_manifest.json`).
