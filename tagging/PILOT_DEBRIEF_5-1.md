# Pilot debrief — Lesson 5-1

Tagged **11 operational items** (the ones wired into the L51_P1 builder): 1 Do Now + 2 Launch Examples + 2 Try-Its + 4 Practice + 1 optional stretch + 1 DOK-3 driver. Ignored the other ~130 items (duplicates/unused).

## What worked

1. **`prereq_ids` as the load-bearing edge is correct.** The 11 items form a clean chain:
   `do-now → Ex1 → TryIt1 → q28` (nth-root track)
   `Ex1 → Ex3 → TryIt3 → q30 → q48` (rational-exp track)
   `q30 + Ex4 → q37 → q49` (algebraic-simplification track)
   `Ex3 + q37 + 3-5-q27 → q50` (DOK-3 convergence)
   The DAG shape already tells you: q50 is the ONLY place where all three tracks merge. That's why it's the driver.

2. **`echoes` delivered on its promise.** Q50 ↔ 3-5-q27 is a real through-line: both build a polynomial from a volume constraint, then extract a dimension. The ONLY cohesion signal I care about is: *which items echo across unit boundaries?* Within-unit `prereq_ids` will always be dense; cross-unit `echoes` will always be sparse. That asymmetry is the integrated-year signal.

3. **`rehearses` needs a second edge.** Discovered a second relationship during tagging: Launch Examples "rehearse" their paired Try-Its in the immediate next phase. I added a `role` field (do-now-explore, launch-model-1, explore-tps, explore-practice, optional-stretch, dok3-driver) to capture phase position — this is not in the v2 proposal but is earning its keep. Recommend adding.

## What broke

1. **`rehearses` forward pointers dangle.** Q50 rehearses `topic5-assess-q1a`, which isn't in the registry. For cross-unit and assessment-rehearsal pointers to be valid DAG edges, assessment items need their own registry presence (even if just shell rows). Cheap fix.

2. **Duplicate items are noise.** 5-1 has 143 rows because Examples/Try-Its were re-ingested with `-2` suffixes. The `-2` versions are what the builders reference; the un-suffixed versions are orphans. `qb_graph.py` should flag "items with no `used_in` and no `prereq_ids` pointing in" as candidates for dedup or deletion.

3. **`standards` tagging went fast because I already know N-RN / A-CED.** For lessons in less-familiar strands it will be the slow step. Recommend starting a `standards_quickref.md` that maps each Savvas lesson to its 1–3 CCSS codes — do it once per lesson, not once per item.

## Schema revisions earned

Add to v2:

- **`role`** (enum): `do-now-explore`, `do-now-bridge`, `launch-model-1`, `launch-model-2`, `explore-tps`, `explore-practice`, `optional-stretch`, `dok3-driver`, `exit-recap`, `assessment-rehearsal`. Replaces the fuzzy "position in lesson" understanding scattered across tags.
- **`rehearses`** should be `list[str]`, not `str | null`. Ex 3 rehearses BOTH Try-It 3 AND (downstream) q30 — the chain is real.

## Scale estimate

11 items × ~3 min each = **33 min for the pilot.** At that rate, tagging the operational spine of all 11 roadmap lessons (≈120 items total, skipping duplicates) = **6 hours** — one weekend afternoon per unit, which matches the "dry-run as tagging" premise. The full 1054 registry is not worth tagging; the operational 120 are.

## Recommended next step

Apply the revised schema (add `role`, change `rehearses` to list) and pilot **Lesson 6-5** next — it's the furthest from 5-1 in the roadmap and the last teachable, so it stresses the `echoes` field hardest. If 6-5 → 5-1 echo linkages come out cleanly, the schema is stable and we batch the remaining 9 lessons.
