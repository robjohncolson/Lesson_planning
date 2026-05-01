# Pilot debrief — Lesson 6-5

Tagged **10 operational items**: 3 Do Now + 1 Launch (compressed) + 4 Practice + 2 paired DOK-3 drivers. No Try-Its (6-5 is a single-period quick; Do Now carries the warm-up).

## Schema revisions from 5-1 pilot — did they hold up?

**Yes to both.**
- `role` enum worked cleanly. 6-5 needed two new values: `do-now-bridge` (multiple Do Now items, each bridging a prior-lesson skill) and it shares `dok3-driver` with 5-1 (used twice because of the paired driver).
- `rehearses` as `list[str]` paid off immediately. Q5 rehearses BOTH q19 AND q21. Ex 3 rehearses both. Would have been lossy as a single-valued field.

## New finding — DOK-3 has flavors

This is the first real cross-lesson insight the tagging surfaced, and I did not expect it:

| Flavor | Definition | Pilot exemplars |
|---|---|---|
| **Derive-from-constraint** | Translate a physical/geometric setup to an equation, solve for a dimension, interpret | 3-5-q27 (Storage Box), 5-1-q50 (Cylinder) |
| **Prove-by-properties** | Establish a general algebraic fact by invoking defining relationships | 6-5-q13 (Power Property proof) |
| **Model-then-generalize** | From a numeric model-answer, produce the symbolic general form | 6-5-q40 Part C (Richter 150×) |

Once the DAG is built, a lesson-by-lesson view of `skill_tokens` ∩ {DOK-3 flavors} shows whether the year exposes students to all three flavors, or whether one dominates. **Cohesion is not just echoes — it's flavor balance.** If every DOK-3 driver is derive-from-constraint, students never learn to prove. If every one is prove-by-properties, they never model. This came out of tagging two lessons.

## `echoes` behaved correctly

6-5 pilot produced exactly ONE cross-unit echo (q40 ↔ 5-1-q50, both model-then-generalize). That's the right density — too many echoes means the token is too broad; too few means no cohesion. One per lesson, laddering backward, is the healthy rate.

Zero echoes for q13 (prove-by-properties) is *also* a useful signal: this flavor is new to Unit 6. If we don't plant a prove-by-properties seed earlier in the year, students meet proof cold.

## Remaining schema concerns

- **Forward-pointing `rehearses` to assessment items still dangle.** Both pilots reference `topic5-assess-*` / `topic6-formB-*` IDs that don't exist. Before the other 9 lessons get tagged, register assessment shells. Estimate: 15 min one-time.
- **The operational items in 6-5 were easy to find because the builder literally imports them by ID.** That's a good property — `qb_graph.py` can auto-derive `used_in` by parsing the builders and round-trip-verify tagging coverage.

## Decision point (for you)

You flagged earlier that you want to tag the remaining 900+ rows, not just the operational spine.

**Where I'd push back, gently:** the 900+ rows include ~6× duplication (most Examples/Try-Its were re-ingested with `-2` suffixes), and the full Savvas practice pool per lesson (most items unused by any builder). Tagging these has diminishing returns:
- Duplicates → dedup them first, don't tag both.
- Unused Savvas → tag only when you pull one into a future lesson.

**Where you're right:** the operational spine (~120 items) is not enough to show standards coverage accurately, because the standards assessment items cover ground the spine doesn't hit. A middle-tier tagging pass — the ~300 items that are either (a) in a builder OR (b) appear in any assessment OR (c) are the unique representative of a skill-token not yet covered — gives you standards coverage without tagging flashcard drill.

Recommend: **tag operational spine (120) now, then a 180-item "coverage fill" pass, total ≈300.** Skip the remaining 750, or auto-tag them with `skill_tokens` inferred from their prompt (regex) and `dok` from the existing field.

## Scale re-estimate

10 items × ~2 min each = **20 min for this pilot.** Faster than 5-1 because the schema was already set. At that rate:
- Operational spine (120): **4 hours**
- Coverage fill (180 more): **6 hours**
- Total for meaningful DAG: **10 hours**

## Recommended next step

1. 15-min: register Topic 3/4/5/6 assessment shells so `rehearses` edges resolve.
2. 10-min: apply schema v2 (add `role`, change `rehearses` to list) to `qb_append.py`.
3. Batch-tag the other 9 operational spines in one sitting (≈4 hrs) — no more pilots needed.
4. Build `qb_graph.py`. *Then* decide whether coverage-fill pass is worth it based on what the first DAG shows is missing.
