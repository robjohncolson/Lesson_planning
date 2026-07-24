# Algebra 2 Course Map — Topic → Lesson → Item Tree

Generated from `course_map.json` (built by `build_course_map.py`). All content is sourced
read-only from `questionbank/registry.jsonl`, `questionbank/calibration/*.json`,
`questionbank/assessment_shells.jsonl`, and `graph/*`. Nothing here is fabricated: a null
title/objective/essential_question means the source has no such field for that lesson.

- **6 topics, 37 lessons total.**
- **900 registry items** live in exactly **10 lessons** (3-5, 4-3, 4-4, 4-5, 5-1, 5-4, 5-5,
  6-3, 6-4, 6-5). The other **27 lessons are structural placeholders** with 0 items — either
  front-of-year build targets not yet ingested, or department-skipped/assessment-shell slots.
- **193 resolved prerequisite/rehearsal/echo edges**, **18 dangling edges** that point outside
  the built set (see `prereq_gaps.md` for the full breakdown).

---

## 1. Topic / Lesson Outline

Readiness legend: **calibrated** = has calibration + full item set · **partial** = has items,
partial/no calibration fields · **absent** = 0 items (retired, dept-skipped, or
assessment-shell placeholder) · **frontload-blocked** = front-of-year lesson not yet built.

### Topic 1 — Linear Functions and Systems (inferred — front-of-year)
| Lesson | Title | Items | Readiness |
|---|---|---|---|
| 1-1 | (placeholder) | 0 | frontload-blocked |
| 1-2 | Transformations of Functions (inferred) | 0 | frontload-blocked |
| 1-3 | (placeholder) | 0 | frontload-blocked |
| 1-4 | (placeholder) | 0 | frontload-blocked |
| 1-5 | (placeholder) | 0 | frontload-blocked |
| 1-6 | (placeholder) | 0 | frontload-blocked |
| 1-7 | (placeholder) | 0 | frontload-blocked |

### Topic 2 — Quadratic Functions and Complex Numbers (inferred — front-of-year)
| Lesson | Title | Items | Readiness |
|---|---|---|---|
| 2-1 | (placeholder) | 0 | frontload-blocked |
| 2-2 | (placeholder) | 0 | frontload-blocked |
| 2-3 | Factoring / Solving Quadratic Equations (inferred) | 0 | frontload-blocked |
| 2-4 | Complex Numbers (inferred) | 0 | frontload-blocked |
| 2-5 | (placeholder) | 0 | frontload-blocked |
| 2-6 | (placeholder) | 0 | frontload-blocked |
| 2-7 | (placeholder) | 0 | frontload-blocked |

### Topic 3 — Polynomial Functions
| Lesson | Title | Items | Readiness |
|---|---|---|---|
| 3-1 | Polynomial operations (feeds 5-1) (inferred) | 0 | frontload-blocked |
| 3-2 | (placeholder) | 0 | frontload-blocked |
| 3-3 | (placeholder) | 0 | frontload-blocked |
| 3-4 | (placeholder) | 0 | frontload-blocked |
| **3-5** | **Zeros of Polynomial Functions** | **42** | **calibrated** |
| 3-6 | (placeholder) | 0 | absent (dept-skipped/shell) |

### Topic 4 — Rational Functions and Inverse Variation
| Lesson | Title | Items | Readiness |
|---|---|---|---|
| 4-1 | Inverse Variation and the Reciprocal Function | 19 | **optional-catalog** (nt14-ingest-4-1-2026-07-23 — catalog only, never scheduled/paced/counted; cut 2026-05-13 remains the recorded history) |
| 4-2 | (placeholder) | 0 | absent (dept-skipped) |
| **4-3** | **Multiplying and Dividing Rational Expressions** | **74** | **partial** |
| **4-4** | **Adding and Subtracting Rational Expressions** | **91** | **partial** |
| **4-5** | **Solving Rational Equations** | **81** | **partial** |
| 4-6 | (placeholder) | 0 | absent (assessment-day shell) |

### Topic 5 — Rational Exponents and Radical Functions
| Lesson | Title | Items | Readiness |
|---|---|---|---|
| **5-1** | **$n$th Roots, Radicals, and Rational Exponents** | **132** | **partial** |
| 5-2 | (placeholder) | 0 | absent (dept-skipped) |
| 5-3 | (placeholder) | 0 | absent (dept-skipped) |
| **5-4** | **Solving Radical Equations** | **132** | **partial** |
| **5-5** | **Function Operations** | **96** | **partial** |
| 5-6 | (placeholder) | 0 | absent (dept-skipped/shell) |

### Topic 6 — Exponential and Logarithmic Functions
| Lesson | Title | Items | Readiness |
|---|---|---|---|
| 6-1 | (placeholder) | 0 | absent (dept-skipped) |
| 6-2 | (placeholder) | 0 | absent (dept-skipped) |
| **6-3** | **Logarithms** | **100** | **partial** |
| **6-4** | **Logarithmic Functions** | **69** | **partial** |
| **6-5** | **Properties of Logarithms** | **83** | **partial** |

**Totals:** 37 lessons · 10 with items (900 rows) · 27 placeholders (1 calibrated, 9 partial,
9 absent, 18 frontload-blocked).

---

## 2. Prerequisite Structure

**Node identity note:** tree nodes are keyed by an opaque `item_uid` (900 total, one per
registry row/line, always unique) rather than by the registry's human-readable `id`.
`registry.jsonl` has only **815 unique `id` strings among its 900 rows** — 85 legacy ids are
each shared by 2 rows with genuinely different content (all 85 collisions sit within a single
lesson: 5-1, 5-4, or 5-5 — never spanning lessons). `legacy_id` is kept on every node as a
possibly-ambiguous alias. See `inventory/dedup/item_uid_alias_map.json` and
`inventory/dedup/DUPLICATE_ID_REMEDIATION.md` for the full dedup workstream.

The registry encodes three edge types per item: `prereq_ids` (must-come-before),
`rehearses` (this item is rehearsed later by / feeds into an assessment or later item), and
`echoes` (a deliberate cross-unit through-line — same modeling structure recurring in a later
unit). Of every listed target across all 900 rows, **193 resolve inside the built set** (129
prereq, 42 rehearses, 22 echoes), and **16 of those 193 cross a unit boundary** (source lesson's
unit digit ≠ target lesson's unit digit).

Of the 193 resolved edges, **176 fully resolve to a single unambiguous target `item_uid`**.
The remaining **17 have an ambiguous target** — the edge's target legacy id is one of the 85
duplicated ids, and the edge itself carries no target prompt text to say which of the two
lesson-mate rows is meant. Those 17 are flagged `target_uid=null`, `target_ambiguous=true`,
with both candidate `item_uid`s listed, and are **pending WS-dedup collision review**
(cross-ref `inventory/dedup/DUPLICATE_ID_REMEDIATION.md`) rather than being silently pinned to
one candidate. All 17 happen to involve 5-1/5-4/5-5 targets (the three lessons where the
duplicate-id collisions live).

### Known cross-unit dependencies (stated explicitly, not just inferred from resolved edges)

- **(a) 2-3 (factoring) + 2-4 (complex numbers) feed 3-5 and the Topic-4 rational lessons.**
  These are Topic-2 front-of-year lessons not yet built, so this dependency does not show up as
  a *resolved* edge yet — it is a structural fact about the course sequence that will surface as
  real prereq edges once Topic 1–2 are ingested.
- **(b) 1-2 (transformations) feeds 4-1 and 6-4** — graph translations of the reciprocal parent
  (4-1) and the log parent (6-4) both lean on the transformation vocabulary introduced in 1-2.
  Same front-of-year caveat as (a).
- **(c) Inverse-functions feeds 5-5 (Function Operations / composition) and 6-4 (logs as the
  inverse of exponentials).** The exact lesson code for "inverse functions" is not confirmed in
  the current build (Savvas edition ambiguity — see Section 4, item iii); it is a real gate on
  both 5-5 and 6-4 but is not itself in the built 10-lesson set.

### Strongest cross-unit through-lines (from `graph/chains.md`)

These are the `echoes`-graph connected components that span the most lessons — the clearest
cohesion signal in the whole DAG:

- **Extract-hidden-dimension chain (7 items, 6 lessons: 3-5, 4-1, 5-1, 6-3, 6-4, 6-5):**
  `3-5-savvas-q27` (storage-box DOK-3) → `4-1-savvas-q17` (radio-wave inverse variation) →
  `5-1-savvas-q50` (milk-container performance task) → `6-3-savvas-q54` (Richter magnitude) →
  `6-4-savvas-q28` / `6-4-savvas-q33` (log performance tasks) → `6-5-savvas-q40` (Richter scale).
  All share the "derive an equation from a geometric/physical constraint, then extract a hidden
  dimension" move.
- **Model-then-extract chain (4 items, 4 lessons: 3-5, 4-5, 5-4, 6-3):**
  `3-5-savvas-q30` (deli-franchise profit model) → `4-5-savvas-q33` (alcohol-solution
  concentration) → `5-4-savvas-q41` (soft-drink half-life) → `6-3-savvas-q52` (compound-interest
  time-to-grow). Shared move: build a model, then solve for time/rate.
- **Intra-Unit-4 rate-reciprocal chain (3 items, 3 lessons: 4-1, 4-4, 4-5):**
  `4-1-savvas-q26` (Ramón's road trip — direct vs. inverse rate) → `4-4-savvas-q26` (Ahmed's bike
  ride — rational-expression rate sum) → `4-5-savvas-q25` (Kenji/Oscar puzzle — work-rate
  equation). This one stays inside Unit 4. [NT14 update, nt14-ingest-4-1-2026-07-23: 4-1's rows
  now exist as optional-catalog content, so these edges no longer dangle — they resolve as
  optional-catalog references in `optional_catalog_edges`, deliberately outside the required
  `prereq_edges` chain. The pre-NT14 text here read "retired from the registry (0 rows) …
  currently dangle"; see the NT14 addendum below.]

**16 cross-unit resolved edges total** — smaller through-lines not named above still connect
3-5↔5-1, 3-5↔5-4, 3-5↔6-3, 3-5↔6-4, 3-5↔4-5, 4-3↔6-5, 5-4↔4-5, 5-4↔6-3, 5-5↔4-4, 6-3↔5-4,
6-4↔5-1, 6-5↔5-1 — all fully listed in `course_map.json` → `prereq_edges` (`cross_unit: true`).

---

## 3. INITIAL PACING CANDIDATES

> **CANDIDATES for teacher review — advisory, not prescriptive.** This is a proposed teaching
> order + days-per-lesson, built from the teacher's re-baselined roadmap memory
> (`roadmap_post_3-5.md`) and the Klimsara 3-period cadence. It is not derived from the item
> tree itself and should be checked against actual pacing as the term progresses.

| Lesson | Cadence | Candidate days |
|---|---|---|
| 3-5 close-out (P2 multiplicity, P3 Storage-Box DOK-3) | multi-day | ~2–3 |
| Topic 3 Assessment (L35_P4) | assessment | 1 |
| 4-3 | single-period quick | 1 |
| 4-4 | single-period quick | 1 |
| 4-5 | single-period quick | 1 |
| Topic 4 LEHS Assessment (8-Q external) | assessment | 1 |
| 5-1 | single-period quick | 1 |
| 5-4 | single-period quick | 1 |
| 5-5 | single-period quick | 1 |
| 6-3 | single-period quick | 1 |
| 6-4 | single-period quick | 1 |
| 6-5 | DROP / float as bonus (first to cut if pacing slips) | 0–1 |

**Outside pacing — optional catalog (nt14-ingest-4-1-2026-07-23):** 4-1 Inverse
Variation & Reciprocal is deliberately NOT in the pacing table above. It was cut by
the department on 2026-05-13 (historical evidence, not permanent policy); its 19
practice items now exist in the registry as optional-catalog content only — never
scheduled, paced, or counted toward completion. A later course-policy decision
governs any student-facing revival. See the NT14 addendum at the bottom of this
document.

**Skips:** 3-6, 4-2, 4-6, 5-2, 5-3, 5-6, 6-1, 6-2, and SOH-CAH-TOA (deprecated) are not taught
this cycle.

**Context:** two sections (Period A trails Period F by ~1 day), Wednesday F is a compressed
45-minute period, the school year ends 2026-06-20, and roughly 9–10 class days per section
remain. Compressing most Topic 4–6 lessons to single-period-quick cadence is a deliberate
trade — coverage sacrificed for pacing realism, not an oversight.

**Cut order if pacing slips further:** 6-5 first, then 6-4, then 5-5 — in that order, to protect
Unit 4 content ahead of the LEHS assessment.

---

## 4. Teacher-Judgment Items

Flagged for the teacher to confirm — none of these are resolved by the data alone:

1. **Pacing order and days-per-lesson (Section 3) are candidates only.** They come from the
   teacher's own roadmap memory + cadence convention, not from any dependency analysis in
   `course_map.json`. Adjust freely.
2. **Prereq-gap interpretation — two distinct kinds, now split.** The dangling edges into
   not-yet-built or retired lessons (`prereq_gaps.md` Part A) split into **`retirement-gap`**
   (historically, 4 edges into 4-1 — 4-1 was calibrated and then pulled from the registry, per
   WS1. [NT14 update: those 4 edges HAVE now resolved — as optional-catalog references in
   `optional_catalog_edges`, NOT as required prereqs; `edges_dropped_by_reason` no longer
   contains `retirement-gap`. See the NT14 addendum.]) and
   **`frontload-gap`** (1 edge into 3-1 — a genuinely never-yet-built front-of-year lesson). Both
   are *true* upstream dependencies that will need attention, but on different timelines — 4-1
   is a revival, 3-1 is a from-scratch build. The `assessment-forward-ref` edges (12) are a
   different thing entirely: forward rehearsal pointers into assessment shells that don't exist
   as tree items by design (they're assessment items, not lesson items) — not gaps to close.
3. **Inverse-functions placement is unconfirmed.** Per known cross-unit dependency (c) above,
   an "inverse functions" lesson feeds both 5-5 (Function Operations / composition) and 6-4
   (logs as inverse of exponentials) — but it is not in the built 10-lesson set, and Savvas
   edition ambiguity (this content is FRONTLOAD-blocked) means its exact lesson code is not yet
   confirmed. The teacher needs to confirm where it lands in the Topic 1–2 sequence before that
   dependency can be wired into the tree.
4. **17 resolved edges have an ambiguous target, pending WS-dedup collision review.** These
   point at one of the 85 duplicated legacy ids (all in 5-1/5-4/5-5) and cannot be pinned to a
   specific `item_uid` without a human call on the collision (see `inventory/dedup/DUPLICATE_ID_REMEDIATION.md`).
   Not a course-structure gap — an item-identity cleanup task for the dedup workstream.

---

## NT14 addendum (nt14-ingest-4-1-2026-07-23) — Lesson 4-1 optional catalog

19 Lesson 4-1 rows (`4-1-savvas-q8`..`q26`) were ingested as **optional
catalog content** (`availability: "optional-catalog"` on every row). The
counts above this addendum describe the pre-NT14 900-row map; the live
`course_map.json` now reports the triple split **919 raw = 878
required-active + 19 optional-catalog + 22 merged-alias** (unique legacy ids
815 → 834; ambiguous 85 unchanged). 4-1's node carries the new distinct
readiness state `optional-catalog` — it is **not** READY, not required, not
in pacing, and not counted toward completion. The 4 former `retirement-gap`
dropped edges (targets `4-1-savvas-q10/q17/q19/q26`) now resolve as
optional-catalog **references** in the new `optional_catalog_edges` list —
deliberately never added to `prereq_edges` (the required chain, unchanged at
193). The department's 2026-05-13 skip of L41 remains the recorded history;
a later course-policy decision governs any student-facing appearance.
