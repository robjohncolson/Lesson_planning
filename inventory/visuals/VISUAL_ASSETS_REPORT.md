# Visual Asset Inventory -- 137 Absent + 7 Broken-Path (WS2)

Scope: **137 ABSENT rows** (`has_visual==True` AND `image` field empty/None -- the inventory's authoritative `visuals_absent` definition) across nine lessons (4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5), plus **7 BROKEN-PATH rows** in lesson 3-5 whose `image` field points at a file that no longer exists on disk.

> **This is analysis only.** `questionbank/registry.jsonl` was read-only throughout and was NOT modified. Path repairs below are PROPOSED for human review, not applied. registry.jsonl sha256: `b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8` (unchanged before/after this run).

## Definition and reconciliation

- **has_visual definition:** ABSENT = has_visual==True AND image field empty/None (inventory visuals_absent definition). Total 137 across nine lessons.
- **137 vs 132 reconciliation:** 137 uses has_visual (matches inventory). The alternative 'visual_type!=none' reading yields 132; the 5-row gap is the has_visual_true_but_visual_type_none quirk rows (6-3-ex-3, 6-3-tryit-3, 6-3-tryit-4, 6-3-tryit-5, 6-4-tryit-1), which are retained here.

## Per-lesson summary

| lesson | rows | essential | supporting | decorative | tikz | source_pdf | irreplaceable_photo |
|---|---|---|---|---|---|---|---|
| 4-3 | 8 | 3 | 4 | 1 | 4 | 3 | 1 |
| 4-4 | 11 | 4 | 2 | 5 | 2 | 4 | 5 |
| 4-5 | 14 | 0 | 5 | 9 | 5 | 0 | 9 |
| 5-1 | 21 | 1 | 9 | 11 | 10 | 1 | 10 |
| 5-4 | 19 | 2 | 7 | 10 | 7 | 2 | 10 |
| 5-5 | 13 | 0 | 5 | 8 | 5 | 0 | 8 |
| 6-3 | 17 | 0 | 12 | 5 | 16 | 0 | 1 |
| 6-4 | 23 | 4 | 16 | 3 | 16 | 4 | 3 |
| 6-5 | 11 | 0 | 10 | 1 | 10 | 0 | 1 |
| **TOTAL** | **137** | **14** | **70** | **53** | **75** | **14** | **48** |

## Per-visual-type summary

| visual_type | count |
|---|---|
| graph | 45 |
| photo | 52 |
| table | 26 |
| diagram | 8 |
| map | 1 |
| none | 5 |
| **TOTAL** | **137** |

## Recoverability breakdown

Of the 137 absent-visual rows: **75 are TikZ-regenerable** (the figure's content -- a stated equation, a fully-specified table, or a labeled geometric solid with all dimensions given in text -- can be redrawn without the original asset), **14 require the Savvas SE/TE source PDF** (the defining data -- unlabeled figure dimensions, an unequationed curve, or a specific student error -- exists only in the original figure), and **48 are irreplaceable photos** (a real-world scene, object, or person that would need the original photographic asset, even though most of these are decorative/supporting because their numeric givens are also transcribed into the prompt text).

Cross-tab of importance x recoverability:

| importance | tikz_regenerable | source_pdf_required | irreplaceable_photo | row total |
|---|---|---|---|---|
| essential | 0 | 14 | 0 | 14 |
| supporting | 70 | 0 | 0 | 70 |
| decorative | 5 | 0 | 48 | 53 |
| **column total** | **75** | **14** | **48** | **137** |

## Teacher-judgment items (`needs_teacher_confirmation`)

27 of the 137 rows are flagged for a human second look. This always includes the 5 `has_visual`/`visual_type==none` quirk rows and the 1 mislabeled-map concept-summary row, plus other borderline importance/recoverability calls.

| id | lesson | registry_line | why it needs confirming |
|---|---|---|---|
| 4-3-savvas-q34 | 4-3 | 79 | 'Find and simplify the ratio of the volume of Figure A to the volume of Figure B' gives no dimensions or expressions for either figure anywhere in the prompt text. |
| 4-3-savvas-q35 | 4-3 | 80 | The cylindrical structures A and B are described only as 'shown'; no radius or height values appear in the prompt text. |
| 4-3-savvas-q37 | 4-3 | 82 | The parallelogram's height is described only as 'shown' in the figure; no numeric or symbolic height value appears in the prompt text. |
| 5-1-savvas-q20 | 5-1 | 146 | This is an error-analysis item ('Describe and correct the error a student made') whose specific incorrect student work is not reproduced anywhere in the prompt text. |
| 5-1-savvas-q50 | 5-1 | 176 | The container's volume (169.65 ft^3) and the height=diameter relationship are both stated in text/placeholder. |
| 5-1-savvas-q50 | 5-1 | 208 | Duplicate occurrence: the container's volume (169.65 ft^3) and height=diameter relationship are both stated in text/image label. |
| 5-4-savvas-q18 | 5-4 | 276 | 'Find the point of intersection of the two graphs' gives no equations for either curve anywhere in the prompt text. |
| 5-4-savvas-q46 | 5-4 | 304 | Earth's radius (6,371,000 m) needed for Part B is given in the placeholder; the escape-velocity formula and G are already in the main text. |
| 5-4-savvas-q18 | 5-4 | 307 | Duplicate occurrence: 'Find the point of intersection of the two graphs' gives no equations for either curve anywhere in the prompt text. |
| 5-4-savvas-q46 | 5-4 | 333 | Duplicate occurrence: Earth's radius needed for Part B is given in the placeholder; the escape-velocity formula and G are already in the main text. |
| 6-3-ex-3 | 6-3 | 477 | Pure numeric evaluation of log_5 125, log_(1/4) 16, log_3 0, log_2 2^8 -- no image content is actually needed; visual_type is recorded as none despite has_visual=True. |
| 6-3-tryit-3 | 6-3 | 483 | Pure numeric evaluation (log_3(1/81), log_7(-7), log_5 5^9) -- no image content is needed; visual_type recorded as none despite has_visual=True. |
| 6-3-tryit-4 | 6-3 | 484 | Pure numeric evaluation (log 321, ln 1215, log 0.17) -- no image content is needed; visual_type recorded as none despite has_visual=True. |
| 6-3-tryit-5 | 6-3 | 485 | Pure equation solving (log(3x-2)=2, e^(x+2)=8) -- no image content is needed; visual_type recorded as none despite has_visual=True. |
| 6-4-savvas-model-discuss-lesson-6-4-launch | 6-4 | 573 | 'Compare the graphs...Which two graphs represent the inverse of each other?' gives no equations for any of the three graphs in the prompt text. |
| 6-4-savvas-model-discuss-lesson-6-4-launch-2 | 6-4 | 574 | Duplicate occurrence (single-graph variant): no equations for the compared graphs appear in the prompt text. |
| 6-4-tryit-1 | 6-4 | 579 | Per spec: students graph the stated functions y=ln x and y=log_(1/2) x on a blank grid; visual_type recorded as none despite has_visual=True. |
| 6-4-savvas-q9 | 6-4 | 589 | 'Are the logarithmic and exponential functions shown inverses of each other?' gives no equations for either function in the prompt text. |
| 6-4-savvas-q13 | 6-4 | 597 | 'The graph shows a transformation of the parent graph f(x)=log_3 x. Write an equation for the graph' -- the specific shift/transformation is not stated anywhere in text. |
| 6-4-savvas-q30 | 6-4 | 614 | The focus/epicenter/seismograph-station geometry (F, E, S, arc ES) is explained fully in prose, and Part A's numeric givens (A=700, T=2, D=100 deg) are all stated in text; the cutaway diagram illustrates the same relationships. |
| 6-5-ex-4 | 6-5 | 647 | The acid-rain pH (4.5) needed to solve is captured in the reference chart's data (Acid rain pH=4.5), and the formula pH=log(1/[H+]) is given in text; the chart is a simple reference of four solutions' pH values. |
| 4-4-savvas-q11 | 4-4 | 749 | 'Find the perimeter of the quadrilateral in simplest form' -- no side lengths or expressions for the quadrilateral appear anywhere in the prompt text. |
| 4-4-savvas-q14 | 4-4 | 752 | 'Find the slope of the line that passes through the points shown' -- no point coordinates appear anywhere in the prompt text. |
| 4-4-savvas-q32 | 4-4 | 770 | 'The resistance of electrical circuits A and B are shown' -- no resistance values or circuit diagrams appear in the prompt text. |
| 4-4-savvas-concept-summary-lesson-4-4-2 | 4-4 | 788 | Items 1-10 are fully self-contained text, but the closing item 11 ('Find the perimeter of the quadrilateral in simplest form') repeats the same undimensioned quadrilateral figure as 4-4-savvas-q11, with no side lengths given in text. |
| 4-5-savvas-q7 | 4-5 | 834 | The river current (4 km/h) needed to solve is captured in the image label, and the 6 km/12 km distances are in the main text. |
| 4-3-savvas-q36-partA-build | 4-3 | 898 | This DOK-1 scaffold ('Write the rational expression for the probability of winning') is a build-up step tied to the same carnival-box diagram as 4-3-savvas-q36, whose dimensions are known. |

### The 5 has_visual/visual_type=none quirk rows

These rows have `has_visual==True` but `visual_type=="none"` in the registry -- they are part of the 137 by definition (dropping them via a `visual_type!=none` filter would wrongly shrink the count to 132) but need a teacher's confirmation that no visual asset is actually needed.

| id | lesson | importance | recoverability |
|---|---|---|---|
| 6-3-ex-3 | 6-3 | decorative | tikz_regenerable |
| 6-3-tryit-3 | 6-3 | decorative | tikz_regenerable |
| 6-3-tryit-4 | 6-3 | decorative | tikz_regenerable |
| 6-3-tryit-5 | 6-3 | decorative | tikz_regenerable |
| 6-4-tryit-1 | 6-4 | supporting | tikz_regenerable |

### The mislabeled map row

- `4-5-savvas-concept-summary-lesson-4-5-2` (lesson 4-5, registry_line 866): visual_type recorded as `map` but content is a concept-summary table/word-problem. Per spec, this is the mislabeled map row -- a concept-summary table (algebra worked fully in text) plus a closing text-only word problem restating the same 6 km/12 km/4 km/h boat scenario already resolvable from its own text.

## Broken-path set (lesson 3-5, 7 rows)

These 7 rows have `has_visual==True` and a non-empty `image` field, but the referenced file does not exist on disk. All 7 point at `questionbank/images/3-5_savvas_example-N.png`, and the corresponding file exists at `questionbank/calibration/sources/3-5_savvas_example-N.png` instead. This is a PROPOSED path repair only -- see `broken_path_repair.json` for the machine-readable version; `registry.jsonl` was NOT edited.

| id | current_image | current_exists | proposed_image | proposed_exists |
|---|---|---|---|---|
| 3-5-tryit-3a | `questionbank/images/3-5_savvas_example-3.png` | False | `questionbank/calibration/sources/3-5_savvas_example-3.png` | True |
| 3-5-tryit-3b | `questionbank/images/3-5_savvas_example-3.png` | False | `questionbank/calibration/sources/3-5_savvas_example-3.png` | True |
| 3-5-tryit-4 | `questionbank/images/3-5_savvas_example-4.png` | False | `questionbank/calibration/sources/3-5_savvas_example-4.png` | True |
| 3-5-tryit-5a | `questionbank/images/3-5_savvas_example-5.png` | False | `questionbank/calibration/sources/3-5_savvas_example-5.png` | True |
| 3-5-tryit-5b | `questionbank/images/3-5_savvas_example-5.png` | False | `questionbank/calibration/sources/3-5_savvas_example-5.png` | True |
| 3-5-tryit-6a | `questionbank/images/3-5_savvas_example-6.png` | False | `questionbank/calibration/sources/3-5_savvas_example-6.png` | True |
| 3-5-tryit-6b | `questionbank/images/3-5_savvas_example-6.png` | False | `questionbank/calibration/sources/3-5_savvas_example-6.png` | True |

## Appendix: full per-row table (all 137)

| id | lesson | visual_type | importance | recoverability | flags |
|---|---|---|---|---|---|
| 4-3-savvas-model-discuss-lesson-4-3-launch | 4-3 | graph | supporting | tikz_regenerable |  |
| 4-3-ex-6 | 4-3 | photo | supporting | tikz_regenerable |  |
| 4-3-savvas-q34 | 4-3 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 4-3-savvas-q35 | 4-3 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 4-3-savvas-q36 | 4-3 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-3-savvas-q37 | 4-3 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 4-3-savvas-concept-summary-lesson-4-3 | 4-3 | table | supporting | tikz_regenerable |  |
| 5-1-savvas-model-discuss-lesson-5-1-launch | 5-1 | graph | supporting | tikz_regenerable |  |
| 5-1-savvas-model-discuss-lesson-5-1-launch-2 | 5-1 | graph | supporting | tikz_regenerable |  |
| 5-1-ex-5 | 5-1 | graph | supporting | tikz_regenerable |  |
| 5-1-ex-6 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-ex-1 | 5-1 | graph | supporting | tikz_regenerable |  |
| 5-1-ex-3 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-savvas-q19 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-savvas-q20 | 5-1 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 5-1-savvas-q43 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-savvas-q44 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-savvas-q45 | 5-1 | photo | decorative | tikz_regenerable |  |
| 5-1-savvas-q48 | 5-1 | table | supporting | tikz_regenerable |  |
| 5-1-savvas-q50 | 5-1 | photo | decorative | irreplaceable_photo | needs_teacher_confirmation |
| 5-1-savvas-q19 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-savvas-q43 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-savvas-q44 | 5-1 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-1-savvas-q45 | 5-1 | graph | supporting | tikz_regenerable |  |
| 5-1-savvas-q48 | 5-1 | table | supporting | tikz_regenerable |  |
| 5-1-savvas-q50 | 5-1 | photo | decorative | irreplaceable_photo | needs_teacher_confirmation |
| 5-1-savvas-concept-summary-lesson-5-1-2 | 5-1 | table | supporting | tikz_regenerable |  |
| 5-1-savvas-teacher-edition-learntogether-les-5 | 5-1 | graph | supporting | tikz_regenerable |  |
| 5-4-ex-1 | 5-4 | graph | supporting | tikz_regenerable |  |
| 5-4-ex-2 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-ex-3 | 5-4 | graph | supporting | tikz_regenerable |  |
| 5-4-ex-5 | 5-4 | graph | supporting | tikz_regenerable |  |
| 5-4-ex-6 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-savvas-q18 | 5-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 5-4-savvas-q39 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-savvas-q40 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-savvas-q43 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-savvas-q44 | 5-4 | table | supporting | tikz_regenerable |  |
| 5-4-savvas-q46 | 5-4 | photo | decorative | irreplaceable_photo | needs_teacher_confirmation |
| 5-4-savvas-q18 | 5-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 5-4-savvas-q39 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-savvas-q40 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-savvas-q43 | 5-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-4-savvas-q44 | 5-4 | table | supporting | tikz_regenerable |  |
| 5-4-savvas-q46 | 5-4 | photo | decorative | irreplaceable_photo | needs_teacher_confirmation |
| 5-4-savvas-concept-summary-lesson-5-4 | 5-4 | graph | supporting | tikz_regenerable |  |
| 5-4-savvas-concept-summary-lesson-5-4-2 | 5-4 | graph | supporting | tikz_regenerable |  |
| 5-5-savvas-model-discuss-lesson-5-5-launch | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-savvas-model-discuss-lesson-5-5-launch-2 | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-ex-2 | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-ex-4 | 5-5 | table | supporting | tikz_regenerable |  |
| 5-5-ex-6 | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-savvas-q30 | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-savvas-q32 | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-savvas-q36 | 5-5 | diagram | supporting | tikz_regenerable |  |
| 5-5-savvas-q30 | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-savvas-q32 | 5-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 5-5-savvas-q36 | 5-5 | graph | supporting | tikz_regenerable |  |
| 5-5-savvas-concept-summary-lesson-5-5 | 5-5 | table | supporting | tikz_regenerable |  |
| 5-5-savvas-concept-summary-lesson-5-5-2 | 5-5 | table | supporting | tikz_regenerable |  |
| 6-3-savvas-model-discuss-lesson-6-3-launch | 6-3 | table | supporting | tikz_regenerable |  |
| 6-3-savvas-model-discuss-lesson-6-3-launch-2 | 6-3 | table | supporting | tikz_regenerable |  |
| 6-3-ex-1 | 6-3 | diagram | supporting | tikz_regenerable |  |
| 6-3-ex-3 | 6-3 | none | decorative | tikz_regenerable | has_visual_true_but_visual_type_none, needs_teacher_confirmation |
| 6-3-ex-4 | 6-3 | diagram | supporting | tikz_regenerable |  |
| 6-3-ex-5 | 6-3 | diagram | supporting | tikz_regenerable |  |
| 6-3-ex-6 | 6-3 | diagram | supporting | tikz_regenerable |  |
| 6-3-tryit-3 | 6-3 | none | decorative | tikz_regenerable | has_visual_true_but_visual_type_none, needs_teacher_confirmation |
| 6-3-tryit-4 | 6-3 | none | decorative | tikz_regenerable | has_visual_true_but_visual_type_none, needs_teacher_confirmation |
| 6-3-tryit-5 | 6-3 | none | decorative | tikz_regenerable | has_visual_true_but_visual_type_none, needs_teacher_confirmation |
| 6-3-savvas-q58 | 6-3 | table | supporting | tikz_regenerable |  |
| 6-3-savvas-q15 | 6-3 | graph | supporting | tikz_regenerable |  |
| 6-3-savvas-q54 | 6-3 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 6-3-savvas-q57 | 6-3 | table | supporting | tikz_regenerable |  |
| 6-3-savvas-concept-box-lesson-6-3 | 6-3 | diagram | supporting | tikz_regenerable |  |
| 6-3-savvas-concept-summary-lesson-6-3 | 6-3 | table | supporting | tikz_regenerable |  |
| 6-3-savvas-concept-summary-lesson-6-3-2 | 6-3 | table | supporting | tikz_regenerable |  |
| 6-4-savvas-model-discuss-lesson-6-4-launch | 6-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 6-4-savvas-model-discuss-lesson-6-4-launch-2 | 6-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 6-4-ex-1 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-ex-2 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-ex-3 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-ex-4 | 6-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 6-4-tryit-1 | 6-4 | none | supporting | tikz_regenerable | has_visual_true_but_visual_type_none, needs_teacher_confirmation |
| 6-4-savvas-q9 | 6-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 6-4-savvas-q32 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-q7 | 6-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 6-4-savvas-q8 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-q11 | 6-4 | table | supporting | tikz_regenerable |  |
| 6-4-savvas-q13 | 6-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 6-4-savvas-q14 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-q15 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-q16 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-q17 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-q28 | 6-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 6-4-savvas-q29 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-q30 | 6-4 | photo | supporting | tikz_regenerable | needs_teacher_confirmation |
| 6-4-savvas-concept-summary-lesson-6-4 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-concept-summary-lesson-6-4-2 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-4-savvas-teacher-edition-learntogether-les-2 | 6-4 | graph | supporting | tikz_regenerable |  |
| 6-5-savvas-model-discuss-lesson-6-5-launch | 6-5 | graph | supporting | tikz_regenerable |  |
| 6-5-savvas-model-discuss-lesson-6-5-launch-2 | 6-5 | graph | supporting | tikz_regenerable |  |
| 6-5-ex-4 | 6-5 | diagram | supporting | tikz_regenerable | needs_teacher_confirmation |
| 6-5-savvas-q9 | 6-5 | graph | supporting | tikz_regenerable |  |
| 6-5-savvas-q36 | 6-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 6-5-savvas-q37 | 6-5 | table | supporting | tikz_regenerable |  |
| 6-5-savvas-q38 | 6-5 | table | supporting | tikz_regenerable |  |
| 6-5-savvas-concept-box-lesson-6-5 | 6-5 | table | supporting | tikz_regenerable |  |
| 6-5-savvas-concept-box-lesson-6-5-2 | 6-5 | table | supporting | tikz_regenerable |  |
| 6-5-savvas-concept-summary-lesson-6-5 | 6-5 | table | supporting | tikz_regenerable |  |
| 6-5-savvas-concept-summary-lesson-6-5-2 | 6-5 | table | supporting | tikz_regenerable |  |
| 4-4-savvas-model-discuss-lesson-4-4-launch | 4-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-4-savvas-model-discuss-lesson-4-4-launch-2 | 4-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-4-ex-5 | 4-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-4-savvas-q11 | 4-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 4-4-savvas-q14 | 4-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 4-4-savvas-q26 | 4-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-4-savvas-q31 | 4-4 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-4-savvas-q32 | 4-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 4-4-savvas-q36 | 4-4 | photo | supporting | tikz_regenerable |  |
| 4-4-savvas-concept-summary-lesson-4-4 | 4-4 | table | supporting | tikz_regenerable |  |
| 4-4-savvas-concept-summary-lesson-4-4-2 | 4-4 | graph | essential | source_pdf_required | needs_teacher_confirmation |
| 4-5-savvas-model-discuss-lesson-4-5-launch | 4-5 | table | supporting | tikz_regenerable |  |
| 4-5-savvas-model-discuss-lesson-4-5-launch-2 | 4-5 | table | supporting | tikz_regenerable |  |
| 4-5-ex-2 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-ex-3 | 4-5 | graph | supporting | tikz_regenerable |  |
| 4-5-ex-5 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-savvas-q7 | 4-5 | photo | decorative | irreplaceable_photo | needs_teacher_confirmation, photo_solvable_from_text |
| 4-5-savvas-q19 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-savvas-q20 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-savvas-q26 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-savvas-q27 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-savvas-q31 | 4-5 | table | supporting | tikz_regenerable |  |
| 4-5-savvas-q32 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-savvas-q33 | 4-5 | photo | decorative | irreplaceable_photo | photo_solvable_from_text |
| 4-5-savvas-concept-summary-lesson-4-5-2 | 4-5 | map | supporting | tikz_regenerable | visual_type_map_is_concept_summary |
| 4-3-savvas-q36-partA-build | 4-3 | diagram | supporting | tikz_regenerable | needs_teacher_confirmation |

## Registry integrity

`questionbank/registry.jsonl` sha256 was `b7f9a040017b8b7c45c1a88f0a089c04db483baf585c95392d983c677d4e56b8` both before and after this analysis run. The file was opened read-only; no writes were made to it or to any other file under `questionbank/`.
