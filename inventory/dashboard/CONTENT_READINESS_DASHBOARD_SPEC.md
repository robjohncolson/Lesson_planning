# Content Readiness Dashboard — Spec (WS6)

## 1. Purpose & scope

This is the WS6 synthesis workstream: it does not generate new inventory data.
It consumes six already-signed-off, read-only workstream outputs (base
content-readiness inventory, DOK wave plan, collision review queue, visual
asset classification, broken-path repair proposal, 4-1 stranded-asset
diagnosis, and the course map) and joins them into one consolidated,
per-lesson readiness record for all 37 Algebra 2 lessons (Topics 1–6).

The deliverables are:

- `build_content_readiness.py` — the join/compute script (stdlib only,
  read-only on all six inputs, writes only inside `inventory/dashboard/`).
- `content_readiness.json` — the consolidated data, machine-readable.
- `content_readiness_dashboard.html` — a single self-contained offline page
  (no network calls; the JSON is inlined) that renders a sortable/filterable
  per-lesson matrix plus two synthesis panels.
- This spec.

Scope is content readiness only: whether a lesson has source material,
transcribed answers, reviewed DOK levels, resolvable visuals, and intact
prerequisite/rehearsal/echo links to the rest of the course. It does not
judge pedagogy, pacing, or classroom delivery.

## 2. Readiness taxonomy

Two upstream artifacts each carry their own readiness enum for the same 37
lessons, and they disagree on two lessons (3-5 and 4-1). WS6 defines a third,
reconciled taxonomy — the **WS6 state** — that is what the dashboard and
`ws6_state` field in `content_readiness.json` actually show.

### WS6 states (7 defined; 5 populated today)

| WS6 state | Meaning | Count today |
|---|---|---|
| **VERIFIED** | Base-inventory readiness is already `ready` (see READY below) **AND** every row in the lesson has `review_state=='verified'` under the canonical projection (`tools/dok-review/dok_review.py`'s `entry_is_verified`, reached via `dok-workflow/dok_wave_plan.json`'s per-item `review_state`, under an approved rubric version). Tested *first* in `derive_ws6_state()`'s precedence, before READY — see below. | **0** — item-level verification has begun (first: NT10's 39 lesson-5-4 rows, recorded 2026-07-22; current numbers live in `content_readiness.json`), but no lesson is base-`ready` with *every* row verified, so no lesson reaches this state yet. Registry `reviewed_by`/`reviewed_at` are application-time metadata written by a later, separate promotion step — never verification authority. |
| **READY** | Base-inventory readiness reads `ready` in full (`registry_rows>0` AND `missing_answers==0` AND all topics tagged AND lesson calibrated AND no visuals missing) **but NOT** every row yet verified (`verified < registry_rows`). This is the **fallback** branch of `derive_ws6_state()`'s precedence: VERIFIED is checked first (`base_readiness=='ready' AND verified==registry_rows`); a lesson that clears every other readiness gate but hasn't finished DOK verification falls through to READY instead. The two states are mutually exclusive by construction, never contradictory: same `base_readiness=='ready'` gate, split only by whether verification is complete. | **0** — no lesson clears every gate simultaneously today. Aspirational top state. |
| **CALIBRATED** | Lesson has *real* DOK-2/DOK-3 calibration anchors (not auto-assigned), even though other gates (answers, visuals, verification) remain open. | **1** (3-5) |
| **INCOMPLETE** | Lesson has registry rows and *some* source material but is missing answers, DOK review, and/or visual assets — the "partial, actively worked" bucket. | **9** (4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5) |
| **BLOCKED** | Lesson has staged material (calibration file, screenshots, skeleton stubs) but **zero** registry rows — ingestion never completed (or was undone). Distinct from ABSENT because real work product already exists on disk. | **1** (4-1) |
| **PROVISIONAL** | Lesson is a front-of-year placeholder: no material yet, but it is an active build target (Topics 1–2 and 3-1..3-4), not a deprecated slot. | **18** (1-1..1-7, 2-1..2-7, 3-1..3-4) |
| **ABSENT** | Lesson has zero material AND is not on the front-of-year build list — deprecated, department-skipped, or an assessment-day shell. | **8** (3-6, 4-2, 4-6, 5-2, 5-3, 5-6, 6-1, 6-2) |

`1 + 9 + 1 + 18 + 8 = 37`.

### How `ws6_state` is computed

`ws6_state` is **derived per lesson from source signals**, not a hardcoded
per-lesson lookup list. `build_content_readiness.py`'s `derive_ws6_state()`
takes four input signals per lesson —

- `base_readiness` (`content_readiness_inventory.json` → `lessons[].readiness`: `ready`/`partial`/`blocked`/`absent`),
- `registry_rows`, `calibrated` (same file → `lessons[].registry_rows`, `lessons[].dok_status.calibrated`),
- `verified` — **NOT** the same file's `lessons[].dok_status.verified` (this script never reads that field for this purpose). Single-sourced (NT7 R3b) from `dok-workflow/dok_wave_plan.json`'s per-item `review_state`: this is `build_content_readiness.py`'s own wave-plan-derived **per-lesson verified-uid count** (`len(wave_plan_verified_uids_by_lesson[lesson])`), matching the file's post-R3b implementation and consistent with the `dok.verified` / `ws6_state` provenance rows in §4 below, and
- `course_readiness` (`course-map/course_map.json` → `topics[].lessons[].readiness`: `frontload-blocked`/`calibrated`/`absent`/`partial`)

— and applies this precedence, in order:

```
if base_readiness == "ready" and registry_rows > 0 and verified == registry_rows:
    -> VERIFIED     # 0 today (aspirational)
elif base_readiness == "ready":
    -> READY        # 0 today (aspirational)
elif registry_rows > 0 and calibrated == registry_rows:
    -> CALIBRATED   # 3-5 (all rows calibrated, real anchors)
elif base_readiness == "partial":
    -> INCOMPLETE   # the nine
elif base_readiness == "blocked":
    -> BLOCKED      # 4-1 staged-not-ingested
elif course_readiness == "frontload-blocked":
    -> PROVISIONAL  # 18 front-of-year
else:
    -> ABSENT       # 8 deprecated/skipped/shell
```

**Order matters.** CALIBRATED is tested *before* the `base_readiness ==
"partial"` branch, specifically because 3-5's base readiness is `partial`
(its answers/visuals gates are still open) even though it already has
`calibrated == registry_rows` — that earlier CALIBRATED test is what
promotes it out of the `partial`/INCOMPLETE bucket the other 9 partial
lessons fall into. The resulting per-lesson mapping is asserted at build
time to still equal `{CALIBRATED:1, INCOMPLETE:9, BLOCKED:1,
PROVISIONAL:18, ABSENT:8}` — that assertion is a safety guard against a
silently-broken derivation, not evidence that the states are hand-listed.

### Mapping from the base-inventory enum (`ready`/`partial`/`blocked`/`absent`)

The base inventory (`content_readiness_inventory.json`) computes readiness
purely from what is on disk, lesson-by-lesson, with no course-wide context:

| Base enum | Count | WS6 disposition |
|---|---|---|
| `ready` | 0 | — (no lesson qualifies) |
| `partial` | 10 | 3-5 → promoted to **CALIBRATED**; the other 9 (4-3..6-5) → **INCOMPLETE** |
| `blocked` | 1 | 4-1 → stays **BLOCKED** (its own state) |
| `absent` | 26 | split by course-map's front-of-year distinction into **PROVISIONAL** (18) vs **ABSENT** (8) |

### Mapping from the course-map enum (`frontload-blocked`/`calibrated`/`absent`/`partial`)

The course map (`course_map.json`) adds curriculum context (front-of-year
build plan, which lessons have an `items[]` array at all) but uses a
different vocabulary:

| Course-map enum | Count | WS6 disposition |
|---|---|---|
| `frontload-blocked` | 18 | → **PROVISIONAL** (matches 1:1 — these are exactly the 18 front-of-year placeholders) |
| `calibrated` | 1 | → **CALIBRATED** (3-5, matches 1:1) |
| `absent` | 9 | → 4-1 (**BLOCKED**, own state) + the 8 truly deprecated lessons (**ABSENT**) |
| `partial` | 9 | → **INCOMPLETE** (matches 1:1 — the 9 lessons with registry rows but open gates) |

### Why WS6 reconciles the two disagreements the way it does

- **3-5 → CALIBRATED, not merely "partial".** It is the *only* lesson in the
  entire course with real, human-set DOK-2/DOK-3 calibration anchors (not
  auto-assigned). That is qualitatively different from the other 9 lessons,
  which have registry rows but zero calibrated DOK — so WS6 gives it a state
  the other 9 cannot claim, even though its answer/visual gates are still
  open (it is not `READY`).
- **4-1 → its own BLOCKED state, not "absent".** Unlike the 8 truly-ABSENT
  lessons (zero material of any kind) and unlike the 18 PROVISIONAL
  front-of-year lessons (also zero material, but not yet attempted), 4-1 has
  *staged, non-trivial work product*: a calibration file with a real
  `item_analysis` (5 examples mapped to Savvas practice numbers), 61
  screenshots, and 15 skeleton stubs — but 0 registry rows and no SE/TE
  source. Collapsing it into ABSENT or PROVISIONAL would hide that
  ingestion work already happened and stalled; collapsing it into
  INCOMPLETE (with the other 9) would hide that it has *zero* registry
  rows to work from. It gets its own state precisely because "staged but
  never ingested" is a different failure mode than either.

## 3. Dimension model

Every lesson is scored on 5 independent dimensions, each colored
green / amber / red / grey. Grey always means "not enough registry rows to
evaluate this dimension" (or, for prereqs, "an untouched placeholder with no
edges pointing at or from it") — it is not a failing grade, it is "N/A".

| Dimension | Grey | Green | Amber | Red |
|---|---|---|---|---|
| **Content** | `registry_rows==0` and base readiness is `absent` | `registry_rows>0` and 0 collision groups | `registry_rows>0` and ≥1 collision group | `registry_rows==0` and base readiness is `blocked` (i.e. 4-1: staged but uningested) |
| **Answers** | `registry_rows==0` | `missing==0` and rows>0 (full coverage) | partial coverage (`0 < coverage_pct < 100`) | `with_evidence==0` and rows>0 (no transcribed answers at all) |
| **DOK** | `registry_rows==0` | `calibrated==registry_rows` (whole lesson has real anchors — only 3-5 today) | rows exist but not fully calibrated (mostly `known_auto`/`unreviewed`) | *(not used — `dim_dok()` takes only `(registry_rows, calibrated)` and returns only grey/green/amber; it has no `verified` input and no red branch. Verification does not surface in this dimension at all: it surfaces at the WS6 layer (`derive_ws6_state`, fed the wave-plan `review_state`-derived per-lesson verified count) and in `dok.verified`/`aggregates.dok`. Giving this dimension a verified-aware state would be a deliberate future code+spec change, not a latent state already defined here)* |
| **Visuals** | `registry_rows==0` (nothing to have a visual reference at all) | `registry_rows>0` and `absent+broken_path==0` | `absent+broken_path>0` but `essential==0` (missing visuals are all supporting/decorative) | `essential>0` (at least one *essential*, source-PDF-required visual is missing — the answer cannot be derived from text alone) |
| **Prereqs** | placeholder lesson (course-map `placeholder==true`) with no dangling edges touching it | not a placeholder, no dangling edges touching it | ≥1 *downstream* dangling edge only (this lesson's own items feed something that got dropped, e.g. an assessment-forward-reference) | this lesson **is** the stranded blocker (4-1), OR it has ≥1 *upstream* dangling edge whose reason is in the gap family `frontload-gap`/`retirement-gap`/`retired-missing` (something that should feed **into** this lesson is missing — as opposed to `assessment-forward-ref`, which is not a gap in this lesson's own prerequisite chain) |

**Note on a wording ambiguity in the original rubric, resolved in code:**
the brief's plain-English rubric stated both "grey if visual_items
(absent+broken)==0" and "green if none absent/broken" — the same literal
condition for two different colors. `build_content_readiness.py` resolves
this the same way the `answers` and `dok` dimensions are structured
elsewhere in the same rubric: **grey gates on `registry_rows==0`** (there
are no rows to have `has_visual` on), and **green gates on
`absent+broken_path==0` given `registry_rows>0`** (a lesson with real
content and zero missing visuals). No lesson currently lands in the visuals
green state — all 9 INCOMPLETE lessons have `visuals_absent>0`, and 3-5 has
`broken_path=7` — so this is a defined-but-currently-empty state, not a bug.

## 4. Data-join provenance table

| Field / dimension | Fed by |
|---|---|
| `lesson`, `topic`, `title`, `placeholder`, course-map readiness | `course-map/course_map.json` → `topics[].lessons[]` |
| `registry_rows`, `source.{se_pdf,te_pdf,se_tex,te_tex}`, `answers.{with_evidence,missing}`, `overall_readiness`, `readiness_reason` | `content_readiness_inventory.json` → `lessons[]` |
| `dok.{known_auto,unreviewed,calibrated}` | `content_readiness_inventory.json` → `lessons[].dok_status` |
| `dok.verified` | **Single-sourced (NT7 R3b)**: `dok-workflow/dok_wave_plan.json` → per-item `review_state` (never `content_readiness_inventory.json`'s own `lessons[].dok_status.verified`, even though that value is itself, post Stage R2, canonically computed). `review_state` is the canonical projection of `tools/dok-review/dok_review.py`'s `entry_is_verified()`, reached through the wave-plan generator (`gen_dok_wave_plan.py`); this dashboard only reads that label, it never re-derives verification. Published verified item_uids are set-gated, per item, against the base inventory's own independently computed `aggregate.dok_verified_item_uids` at build time (a three-way per-item set-equality check plus a symmetric-difference assert — see `build_content_readiness.py`'s reconciliation checks). Registry `reviewed_by`/`reviewed_at` are application-time metadata only, never verification authority. |
| `dok.waves`, `dok.assessment_feeding` | `dok-workflow/dok_wave_plan.json` → `waves`, `assessment_feeding_lessons` |
| `visuals.{absent,essential,supporting,decorative,tikz_regenerable,source_pdf_required,irreplaceable_photo,needs_teacher_confirmation}` | `visuals/visual_asset_classification.json` → `rows[]` filtered by lesson |
| `visuals.broken_path` | **Derived**: `visuals/broken_path_repair.json` → `fixes[]` grouped by `lesson` (per-lesson counts) and `count` (total); cross-checked per-lesson and in total against `content_readiness_inventory.json` (`lessons[].visuals_broken_path`, `aggregate.total_visuals_broken_path_all_lessons`). All 7 land in lesson 3-5 today — that is a data fact read off `fixes[]`, not a hardcoded `if lesson == "3-5"` rule. |
| `collisions.{groups,dok_conflict,prompt_drift}` | `review-queue/collision_review_queue.json` → `groups[]`, joined against `dok-workflow/dok_wave_plan.json` per-id `dok` values (the collision queue itself carries no DOK field) |
| `prereqs.{upstream_dangling,downstream_dangling}` | `course-map/course_map.json` → `dropped_edges[]`, split by whether the dangling edge's `target` (upstream) or `source` (downstream) id-prefix-matches this lesson. `upstream_dangling` additionally requires the edge's `reason` to be in the **gap family** `{frontload-gap, retirement-gap, retired-missing}` (i.e. *not* `assessment-forward-ref`) — filtered by a reason **set**, not a single hardcoded label, so it stays correct if course_map.json's dropped-edge taxonomy is relabeled again (as it was: the 4 edges into 4-1 moved from `frontload-gap` to the new `retirement-gap` reason without any code change needed here). |
| `ws6_state`, headline `readiness_ws6` distribution | **Derived**: `derive_ws6_state()` in `build_content_readiness.py`, computed per lesson from `content_readiness_inventory.json` (`lessons[].readiness`, `lessons[].dok_status.calibrated`, `lessons[].registry_rows`), this script's own wave-plan-derived per-lesson verified count (NT7 R3b — single-sourced from `dok_wave_plan.json`'s `review_state`, not `lessons[].dok_status.verified`), and `course-map/course_map.json` (`topics[].lessons[].readiness`), combined via the fixed precedence rule in §2 (locked by the manager brief — the *precedence order* is fixed, but every lesson's state is computed from these signals, not looked up from a per-lesson list) |
| `four_one_stranded` | `topic-4-1/inventory-4-1-assets.json` → `assets{}`, `teacher_judgment_items[]`, joined against `course-map/course_map.json` → `dropped_edges[]` **filtered by TARGET touching 4-1 and `reason` in the gap family** `{frontload-gap, retirement-gap, retired-missing}` (not a single hardcoded reason string). Today all 4 of those edges read `reason=="retirement-gap"` (4-1 was built, then retired — a *retirement* gap, not a front-of-year gap). The one remaining gap-family edge targeting 3-1 instead (still `reason=="frontload-gap"`, genuinely front-of-year) is reported separately as `fifth_frontload_gap_edge_into_3_1`, filtered by target touching 3-1 AND `reason=="frontload-gap"` specifically — it is not folded into the 4-1 count. `aggregates.edges` is derived the same way: one output key per reason actually present in `course_map["stats"]["edges_dropped_by_reason"]` (`reason.replace("-","_")`), so a new/relabeled reason shows up automatically. |

## 5. Synthesis findings

### (a) DOK-conflict subset of the 85 collisions

85 legacy ids in the registry are duplicated (appear as 2 rows each — every
duplicate currently appears in exactly 2 rows). The collision review queue
groups all 85 as `merge-candidate`, but the queue itself has no DOK field —
DOK conflict was found by joining each `legacy_id` against
`dok_wave_plan.json`'s per-id `dok` value.

WS4's re-key added `item_uid` (opaque, primary identity) and `registry_line`
to every one of the 900 wave-plan rows, without changing any wave or DOK
value. That re-key does not change *how* the 22 DOK-conflict rows are found
— the join is still legacy-id -> dok, deliberately, because the legacy id is
what makes two rows collide in the first place — but each conflict row in
`dok_conflict_subset.rows` now additionally carries the two copies'
`item_uid`/`registry_line` (`uid_a`/`line_a` for the lower-DOK copy,
`uid_b`/`line_b` for the higher-DOK copy, consistent with `dok_a<=dok_b`),
since `item_uid` — not the shared legacy id — is the correct key for
actually resolving which copy to keep.

**22 of the 85 groups have two copies carrying *different* DOK levels.**
All 22 are in lesson **5-4**: 21 are DOK-1-vs-DOK-2 (`5-4-savvas-q21`
through `q39` contiguous, plus `q44` and `q45`), and one —
`5-4-savvas-q41` — is DOK-2-vs-DOK-3. The remaining 63 collisions (across
5-1, 5-4, 5-5) are same-DOK prompt-drift only (near-identical prompt text,
different capture).

**Why the 22 DOK-conflict rows are higher priority than the 63 prompt-drift
rows:** for a prompt-drift pair, picking either copy preserves the correct
DOK level and wave assignment — only the exact prompt wording is at stake,
and the review queue's own confidence-scored recommendation (`canonical_keep`
/ `drifted_duplicate`) is usually enough to resolve it unattended. For a
DOK-conflict pair, merging the *wrong* copy doesn't just keep a slightly
worse prompt — it silently corrupts the DOK label and, downstream, the
review-wave assignment that the whole `dok-workflow` review pipeline uses to
prioritize human review. That is a data-integrity risk the prompt-drift
group does not carry, so all 22 should be resolved by a human before any
bulk auto-merge of the other 63.

### (b) 4-1 stranded + the 6-edge non-assessment slice of the 18 dropped edges

4-1 (Inverse Variation and the Reciprocal Function) is `stranded_staged_not_ingested`:
a calibration file exists with a *real* `item_analysis` (5 worked examples
mapped to Savvas practice-item numbers #8–#26) and 61 screenshots and 15
untranscribed skeleton stubs sit in `questionbank/images/` /
`skeletons/4-1_practice_skeletons.json` — but the registry has 0 rows tagged
`lesson=="4-1"`, and there is no SE/TE pdf or tex anywhere on disk. Whether
ingestion was ever attempted, is pending, or was abandoned during the
documented 2026-05-13 department skip of L41 is **not determinable from disk
alone** (see `inventory-4-1-assets.json`'s `epistemic_note`).

**The course map now distinguishes two different reasons for this**, where
an earlier cut of `course_map.json` used one shared `frontload-gap` label
for both:

- **4 `retirement-gap` edges into 4-1** — dangling because 4-1 was *built,
  then retired* (department skip), not because it was never front-loaded.
- **1 `frontload-gap` edge into 3-1** — dangling because 3-1 is genuinely
  front-of-year and has never been built at all.

The dashboard derives both sets **live from `course_map.json`'s current
`dropped_edges[]`**, filtered by the edge's *target* and its reason, so it
is robust to this kind of relabeling: `dangling_edges_into_4_1` selects
edges whose target touches 4-1 and whose reason is in the gap family
`{frontload-gap, retirement-gap, retired-missing}` (i.e. anything except
`assessment-forward-ref`), and `fifth_frontload_gap_edge_into_3_1` selects
the one edge whose target touches 3-1 with `reason=="frontload-gap"`
specifically.

**The 4 retirement-gap edges into 4-1** are:

1. `4-3-tryit-1` → `4-1-savvas-q10` (`prereq`)
2. `6-3-savvas-q54` → `4-1-savvas-q17` (`echoes`)
3. `6-4-savvas-q13` → `4-1-savvas-q19` (`echoes`)
4. `4-5-savvas-q25` → `4-1-savvas-q26` (`echoes`)

These 4 are exactly why 4-1 is a coherent stranded blocker: 1 prereq edge
from 4-3 plus 3 cross-unit echo edges from 6-3/6-4/4-5 all terminate at
retired 4-1 items — three *already-built* lessons each expect to reference
specific 4-1 practice items (`echoes`/`prereq` relationships) that cannot
resolve until 4-1 is either revived (ingested) or those references are
formally retired.

**The 1 frontload-gap edge into 3-1** is a related but separate gap and
should not be conflated with the 4-1 revival decision:

5. `5-1-savvas-model-discuss-lesson-5-1-launch` → `3-1-savvas-squares-recall` (`prereq`) — **into 3-1, not 4-1**

Together, "the 5 dependency-gap edges" (4 retirement-gap into 4-1 + 1
frontload-gap into 3-1) plus 1 `retired-missing` edge
(`6-5-savvas-q12` → `6-4-change-of-base-intro`) make up the **6-edge
non-assessment slice** of the course map's 18 dropped edges — the other 12
are all `assessment-forward-ref` (forward references to not-yet-written
assessment items, which are expected and not prerequisite gaps).

Three teacher-judgment items are open (from `inventory-4-1-assets.json`,
verbatim):

1. Whether to revive lesson 4-1 at all, given the department's 2026-05-13
   skip decision versus its earlier inclusion in `A2LessonSelection.txt`
   and `CLAUDE.md`'s still-present (stale) "ready" entry.
2. If revived: registry-ingestion-only vs. a full lesson-packet rebuild
   requiring SE/TE export from Savvas and PDF-to-LaTeX conversion.
3. Whether to correct the stale `CLAUDE.md` "ready" table now, independent
   of the revival decision.

## 6. How the dashboard updates as workstreams progress

Re-running `build_content_readiness.py` after any of the six inputs changes
always re-reads all six files fresh and rewrites both JSON and HTML from
scratch — there is no manual reconciliation step, and nothing is cached
across runs.

Within that fresh run, fields fall into two categories:

- **Computed / derived fields** — the value is built at build time from
  more primitive per-row, per-id, or per-edge facts via a join or
  precedence rule (documented per-field in §4). This includes `ws6_state`
  (via `derive_ws6_state()`'s precedence over base/course-map readiness and
  DOK-status counts, §2) and `visuals.broken_path` (grouped from
  `broken_path_repair.json`'s `fixes[]` by lesson) — neither is a
  hardcoded per-lesson lookup, so both move automatically as their
  upstream inputs change. It also includes `aggregates.edges` (one key per
  reason actually present in `course_map["stats"]["edges_dropped_by_reason"]`)
  and `four_one_stranded.{dangling_edges_into_4_1,fifth_frontload_gap_edge_into_3_1}`
  (filtered from `dropped_edges[]` by target + reason-family membership, not
  a hardcoded reason string) — both are read live from `course_map.json`'s
  *current* `dropped_edges[]`/`edges_dropped_by_reason` on every run, which
  is what let this build survive the sibling course-map re-cut that split
  the old single `frontload-gap` reason into `frontload-gap` (3-1, still
  front-of-year) vs. the new `retirement-gap` (4-1, built-then-retired)
  without any code change to the filter logic itself — only the reason-set
  membership list needed to grow by one name.
- **Verbatim passthrough fields** — the value is copied as-is from a
  source file rather than computed from something more primitive.
  `four_one_stranded.teacher_judgment_items` and the `four_one_stranded.staged.*`
  narrative fields (e.g. `calibration`, `screenshots`, `skeleton_stubs`)
  are read directly out of `inventory-4-1-assets.json`'s `assets{}` /
  `teacher_judgment_items[]` on every run — they will reflect whatever
  that file says next time it changes, but the dashboard does not
  reinterpret or recompute that narrative; it is a snapshot of the
  source file's own wording/counts.

What moves, and where to look:

| Workstream progress | What changes in the dashboard |
|---|---|
| **DOK review advances** (an item's `review_state` in the wave plan advances to `verified` under an approved rubric version — via `tools/dok-review/dok_review.py`'s canonical `entry_is_verified` projection) | `dok_status_totals.verified` (single-sourced from the wave plan, gated per item_uid against the base inventory's own independent projection) rises above 0 for the first time. `dimension_status.dok` does NOT change — `dim_dok()` has no verified input and defines no verified state (see the dimension table above). What actually moves at the WS6 layer: the first verified Wave-0 (3-5) item demotes 3-5 CALIBRATED→INCOMPLETE (the overlay drops its `calibrated` count below `registry_rows`); `readiness_ws6` gains a VERIFIED count only when a lesson satisfies `derive_ws6_state`'s full precedence — base readiness `"ready"` AND every row verified — so clearing DOK review alone is NOT sufficient (no lesson is base-`"ready"` today). Registry `reviewed_by`/`reviewed_at` are written separately, by a later promotion step, and are never what drives this transition. |
| **Answers get transcribed** (a row's `teacher_answer`/evidence gets filled in) | That lesson's `answers.with_evidence` rises, `coverage_pct` rises, and `dimension_status.answers` can move red→amber→green; `aggregates.answers.with_evidence`/`missing_all` shift course-wide. |
| **Visuals regenerated or re-pathed** (a TikZ figure built, or a broken path fixed like the 7 in 3-5) | That id drops out of `visual_asset_classification.rows` (or, for 3-5, `broken_path_repair.json`'s count drops from 7); `dimension_status.visuals` can move red/amber→green once `absent+broken_path==0` for that lesson; `aggregates.visuals.absent`/`broken_path` fall course-wide. |
| **Collisions get merged** (a `merge-candidate` group resolved, one `item_uid` retired) | The group count for that lesson drops in `collision_review_queue.json`; if it was one of the 22 DOK-conflict groups, `aggregates.collisions.dok_conflict` and `dok_conflict_subset.rows` shrink; `dimension_status.content` can move amber→green once a lesson's `collisions.groups` reaches 0. |
| **4-1 revived (registry-ingested) or formally retired** | If ingested: `registry_rows` for 4-1 goes above 0, `ws6_state` moves out of BLOCKED (likely to INCOMPLETE once it has rows but open gates), and the 4 dangling edges into 4-1 should resolve (move from `dropped_edges` to `prereq_edges` on the next course-map rebuild), clearing 4-1's `prereqs` red state and the upstream-red states on 4-3/6-3/6-4/4-5's downstream side. The course map has *already* taken the first half-step here: the taxonomy re-cut relabeled these 4 edges' reason from `frontload-gap` to the more specific `retirement-gap` (4-1 was built, then retired — not merely never-built), even though `registry_rows` and `ws6_state` are unchanged (BLOCKED, 0 rows) until an actual ingestion or formal-retirement decision is made. If 4-1 is instead formally retired (not revived), the expectation this spec had for that case — "the 4 edges should be deliberately dropped with a different, terminal reason rather than left as `frontload-gap`" — is exactly what `retirement-gap` now is; the remaining step is `ws6_state` moving to ABSENT once that decision is made explicit elsewhere (course-map readiness, `inventory-4-1-assets.json`). |
| **Front-of-year lessons get built** (Topics 1–2, 3-1..3-4) | Each lesson moves from PROVISIONAL to (at minimum) INCOMPLETE once it has registry rows; `readiness_ws6.PROVISIONAL` falls and `INCOMPLETE` rises; the `3-1` upstream-dangling edge (from 5-1) should resolve once 3-1 is built, moving 3-1's `prereqs` from red to green/amber. |

Because every number is recomputed from the six inputs rather than hand-maintained, the correct operational habit is: **update the source
artifact, re-run the build script, regenerate the dashboard** — never hand-edit `content_readiness.json` or the HTML directly.

## 7. Reconciliation appendix

All figures below are asserted by `build_content_readiness.py` at build time
(PASS/FAIL printed to stdout) and were locked by the WS6 manager brief before
this implementation began.

| Metric | Value | Confirmed by |
|---|---|---|
| Total registry rows | 900 | `content_readiness_inventory.json` (`aggregate.total_registry_rows`), `dok_wave_plan.json` (900 rows across all waves), `course_map.json` (`stats.items_total`) |
| DOK status totals | known_auto=421, unreviewed=398, calibrated=42, verified=39 (as of the 2026-07-22 NT10 recording; displayed totals move as rows verify — the registry-derived BASE invariant stays 421/437/42, and `content_readiness_inventory.json` is the source of the current numbers) | known_auto/unreviewed/calibrated: `content_readiness_inventory.json` (`aggregate.dok_status_totals`). verified: single-sourced (NT7 R3b) from `dok_wave_plan.json`'s per-item `review_state`, set-gated per item_uid against `content_readiness_inventory.json`'s independently computed `aggregate.dok_verified_item_uids` |
| DOK wave counts | wave0=42, wave1=4, wave2=220, wave3=7, wave4=627 | `dok_wave_plan.json` (`wave_counts`) |
| Assessment-feeding lessons | 4-3, 4-5, 6-4 | `dok_wave_plan.json` (`assessment_feeding_lessons`) |
| Visuals absent | 137 (by lesson: 4-3:8, 4-4:11, 4-5:14, 5-1:21, 5-4:19, 5-5:13, 6-3:17, 6-4:23, 6-5:11) | `visual_asset_classification.json` (`summary.by_lesson`), cross-checked against `content_readiness_inventory.json` |
| Visuals broken-path | 7 (all 3-5, all repairable) | `broken_path_repair.json` (`count`), `content_readiness_inventory.json` (`lessons[3-5].visuals_broken_path`) |
| Visuals importance | essential=14, supporting=70, decorative=53 | `visual_asset_classification.json` (`summary.by_importance`) |
| Visuals recoverability | tikz_regenerable=75, source_pdf_required=14, irreplaceable_photo=48 | `visual_asset_classification.json` (`summary.by_recoverability`) |
| Needs-teacher-confirmation | 27 | `visual_asset_classification.json` (`summary.needs_teacher_confirmation_count`) |
| Collision groups | 85 (5-1:32, 5-4:29, 5-5:24), all `merge-candidate`; confidence high15/med68/low2 | `collision_review_queue.json` (`meta`) |
| DOK-conflict collision subset | 22, all in 5-4 (21 dok1-vs-dok2, 1 dok2-vs-dok3: `5-4-savvas-q41`) | computed join of `collision_review_queue.json` `legacy_id` against `dok_wave_plan.json` per-id `dok` |
| Answers with evidence / missing | 529 / 371 (missing "the nine" = 339) | `content_readiness_inventory.json` (`aggregate.total_answers_with_evidence` etc.) |
| Course-map edges | 193 resolved (prereq129/rehearses42/echoes22), 18 dropped (assessment-forward-ref12/retirement-gap4/frontload-gap1/retired-missing1) | `course_map.json` (`stats`); `aggregates.edges` derives one key per reason present, so this row updates itself as reasons are relabeled |
| WS6 readiness distribution | CALIBRATED=1, INCOMPLETE=9, BLOCKED=1, PROVISIONAL=18, ABSENT=8 | WS6 reconciliation (§2), locked by manager brief, asserted in build script |
| 4-1 dangling edges | 4 into 4-1 (all `retirement-gap`) + 1 into 3-1 (`frontload-gap`) = the "5 dependency-gap edges"; plus 1 `retired-missing` (6-5→6-4) = the 6-edge non-assessment slice of the 18 dropped edges | `course_map.json` (`dropped_edges` filtered by TARGET touching 4-1/3-1 and `reason` in the gap family `{frontload-gap, retirement-gap, retired-missing}` — not a single hardcoded reason string; see §5(b)) |
