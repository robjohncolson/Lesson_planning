# Prerequisite Gaps

Three distinct kinds of gap/flag, kept separate on purpose (see `COURSE_MAP.md` Section 4):

- **Part A** — cross-lesson gaps: an edge in the registry points at an item that is not in the
  built 10-lesson set. Split into **retirement-gap** (target lesson was built, then pulled —
  4-1), **frontload-gap** (target lesson genuinely never built yet — 3-1), and **retired-missing**
  (target lesson is built, but this specific item id is simply absent). These are build-order
  gaps between lessons, on different timelines depending on the subtype.
- **Part B** — intra-lesson gaps: within a single built lesson, a DOK-3 driver item exercises a
  skill_token that no earlier-role item in that *same* lesson rehearses first. These are
  scaffolding gaps inside a lesson, unrelated to what's built elsewhere.
- **Ambiguous-target edges** (not a "gap" — an identity-collision flag): a *resolved* edge
  (source and target both exist in the registry) whose target legacy id is shared by two
  different rows, so the edge can't be pinned to one specific `item_uid`. Pending WS-dedup
  collision review, not a build-order or scaffolding problem.

Source data: `dropped_edges` (reason `"retirement-gap"` / `"frontload-gap"` / `"retired-missing"`)
and `prereq_edges` (`target_ambiguous: true`) in `course_map.json`, plus
`graph/skill_bridge_gaps.md` and `inventory/dedup/item_uid_alias_map.json` (read-only, not
modified).

---

## Part A — Cross-lesson dependency gaps

**6 edges total** in the non-assessment slice of the 18 dropped edges: 4 `retirement-gap` + 1
`frontload-gap` + 1 `retired-missing`. (Revised from an earlier single `frontload-gap` bucket of
5 — Codex integration-gate Finding 2 pointed out that 4-1 is retired-pending-teacher-revival
(WS1), not a never-built front-of-year lesson like 3-1, so its 4 dangling edges get their own
subsection.)

### Retirement-gap: dangling edges into 4-1 (4)

4-1 (Inverse Variation and the Reciprocal Function) has a calibration file but currently 0
registry rows — it was built, then pulled from the registry pending teacher revival (WS1). These
4 edges will re-resolve once 4-1 is re-ingested; they are not "never built," just "not built
right now."

| Source item | Edge | Target id | Plain-English dependency |
|---|---|---|---|
| `4-3-tryit-1` | `--prereq-->` | `4-1-savvas-q10` | 4-3 (Multiplying/Dividing Rational Expressions) leans on 4-1 (Inverse Variation) content that has been retired from the registry. |
| `6-3-savvas-q54` | `--echoes-->` | `4-1-savvas-q17` | Richter-magnitude item echoes 4-1's radio-wave inverse-variation item (extract-hidden-dimension chain, `COURSE_MAP.md` Section 2). |
| `6-4-savvas-q13` | `--echoes-->` | `4-1-savvas-q19` | Log-transformation item echoes 4-1's reciprocal-function asymptote item. |
| `4-5-savvas-q25` | `--echoes-->` | `4-1-savvas-q26` | Work-rate puzzle (Kenji/Oscar) echoes 4-1's Ramón road-trip rate-reciprocal item (intra-Unit-4 chain). |

### Frontload-gap: dangling edge into 3-1 (1)

3-1 is a genuinely never-yet-built front-of-year Topic-3 lesson (not a retirement — nothing to
revive, it needs a first build):

| Source item | Edge | Target id | Plain-English dependency |
|---|---|---|---|
| `5-1-savvas-model-discuss-lesson-5-1-launch` | `--prereq-->` | `3-1-savvas-squares-recall` | The 5-1 (nth Roots/Rational Exponents) launch discussion leans on a perfect-squares recall skill nominally seated in 3-1, a front-of-year Topic-3 lesson not yet built. |

### Retired-missing: intra-Topic-6 gap (1)

| Source item | Edge | Target id | Plain-English dependency |
|---|---|---|---|
| `6-5-savvas-q12` | `--prereq-->` | `6-4-change-of-base-intro` | 6-5 (Properties of Logarithms) expects a "change of base" intro item id that is not present anywhere in the registry (not a frontload gap — 6-4 itself is built, the specific item id is simply missing/retired). |

**Total Part A: 4 retirement-gap + 1 frontload-gap + 1 retired-missing = 6.** (The remaining 12
of the 18 dropped edges are `assessment-forward-ref` — forward pointers into assessment shells,
not gaps; see `COURSE_MAP.md` Section 4 for why those are treated differently.)

---

## Ambiguous-target edges (collision review queue)

`registry.jsonl` has 900 rows but only 815 unique legacy `id` strings — **85 legacy ids are each
shared by 2 rows with genuinely different content**, all confined within a single lesson (5-1,
5-4, or 5-5; never spanning lessons). See `inventory/dedup/item_uid_alias_map.json` (the
canonical-identity map) and `inventory/dedup/DUPLICATE_ID_REMEDIATION.md` (the human-review
queue, all 85 pairs currently dispositioned `merge-candidate`).

Of the 193 resolved edges in `course_map.json`, **17 point at a target legacy id that is one of
those 85 ambiguous ones** — the edge carries no target prompt text, so there is no way to tell
which of the two lesson-mate rows is meant. These 17 are **not** silently attached to either
candidate: they carry `target_uid: null`, `target_ambiguous: true`, both candidate `item_uid`s
under `target_uid_candidates`, and `review_ref: "inventory/dedup/DUPLICATE_ID_REMEDIATION.md"`.
All 17 targets land in the three lessons that hold every duplicate-id collision: **9 in 5-1, 5
in 5-5, 3 in 5-4** — the highest-fan-in rehearses/echoes targets in the built set. This is an
item-identity cleanup task for the dedup workstream, not a course-structure gap — 176 of the 193
resolved edges are unaffected and fully resolve to one unambiguous `item_uid`.

---

## Part B — Intra-lesson skill-bridge gaps

Summarized from `graph/skill_bridge_gaps.md`: **28 gaps across the same 10 built lessons**,
where a lesson's DOK-3 driver item uses a `skill_token` that no earlier-role item (do-now,
launch, explore-tps, or explore-practice) in that same lesson exercises first.

### Per-lesson gap counts

| Lesson | Gap count | DOK-3 driver(s) |
|---|---|---|
| 3-5 | 3 | `3-5-savvas-q27` |
| 4-3 | 4 | `4-3-savvas-q13`, `4-3-savvas-q36-partC-evaluate-fairness` |
| 4-4 | 1 | `4-4-savvas-q32` |
| 4-5 | 2 | `4-5-savvas-q33` |
| 5-1 | 4 | `5-1-savvas-q50` (listed twice in source — same 2 gaps duplicated) |
| 5-4 | 4 | `5-4-savvas-q41` (listed twice in source — same 2 gaps duplicated) |
| 5-5 | 2 | `5-5-savvas-q32` (listed twice in source — same 1 gap duplicated) |
| 6-3 | 2 | `6-3-savvas-q15` |
| 6-4 | 3 | `6-4-savvas-q28` |
| 6-5 | 3 | `6-5-savvas-q13`, `6-5-savvas-q40` |
| **Total** | **28** | across 10 lessons |

Note: `graph/skill_bridge_gaps.md` lists the DOK-3 section for `5-1-savvas-q50`,
`5-4-savvas-q41`, and `5-5-savvas-q32` twice each with identical gap content — reproduced as-is
from the source (not de-duplicated) since this deliverable does not modify or reinterpret
`graph/` output, only summarizes it.

### Notable call-outs

- **3-5 `q27` (Storage Box DOK-3)** needs `extract-dimension-from-volume` and
  `interpret-answer-in-context` — neither has ANY earlier-role candidate anywhere in lesson 3-5
  (pool is empty for both), the two least-scaffolded tokens in the whole gap list.
- **6-4 `q28`** needs `solve-exponential-equation` with no earlier-role item in 6-4 exercising it
  (also needs `interpret-answer-in-context`, and `model-physical-context` — the latter at least
  has one candidate in-pool, `6-4-savvas-q33`).
- **`build-equation-from-constraint`** recurs as a gap across four different lessons — 3-5
  (`q27`), 4-4 (`q32`), 4-5 (`q33`), and 5-1 (`q50`) — suggesting this skill is never explicitly
  rehearsed before its DOK-3 use in any of these lessons; it is the single most common
  cross-lesson-repeated gap token in Part B.
- **6-5** is the one lesson where two DOK-3 items (`q13`, `q40`) each partially cover for the
  other's gap (`generalize-numerical-result` lists the other as an in-pool candidate) — the
  weakest gap in the list, unlike the "no candidates anywhere" gaps above.
