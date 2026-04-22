# Chains 3+ — Authoring Decision (2026-04-22)

## Decision

**Do not author Chain 3, 4, 5, 6, or 7.** Chain 1 and Chain 2 are sufficient.

## Rationale

Practical threshold for a coherent echo-chain narration is **≥4 anchor items across ≥3 lessons** (so the callback has genuine cross-unit weight, not just a within-unit repeat). All un-authored candidate chains fall below this.

## Archetype inventory (from tagging/BATCH_SYNTHESIS.md)

1. **Derive-from-constraint** (extract hidden variable by modeling) — Chain 1, shipped
2. **Prove-by-properties** (establish general fact via algebraic proof) — only 2 items (4-3 Rational Closure + 6-5 Power Property)
3. **Model-then-extract** (given model, solve for specific input) — Chain 2, shipped
4. **Read-structure-from-representation** (graphical/multi-rep reasoning) — only 1 clear exemplar (6-3-q15)

## Candidate chains scored

| Candidate | Theme | Items | Lessons | Verdict |
|---|---|---|---|---|
| Chain 3 | Rate-reciprocal modeling (intra-U4) | 3 | 4-1, 4-4, 4-5 | Below threshold; intra-unit scope |
| Chain 4 | Apply-physical-formula (mixed archetype) | 3 | 4-3, 4-4, 5-5 | Below threshold; no archetype cohesion |
| Chain 5 | Extraneous-check / error-analysis | 3 | 4-5, 5-4 | Below threshold; error-review flavor, not generative |
| Chain 6 | Prove-by-properties | 2 | 4-3, 6-5 | Far below threshold |
| Chain 7 | Graph-transformation (asymptotes → log) | 2 | 4-1, 6-4 | Far below threshold; forced rational-to-log analogy |

## Opportunistic follow-ups (not chain authoring)

- **Prove-by-properties is thin** (2 items, both late). A Unit 3 proof-flavor DOK-3 seed would enable a future Chain 6 — but this is speculative and not blocking.
- **Read-structure-from-representation is thinnest** (1 item at 6-3-q15). If future Topic 6 ingests surface more graph-reading items, revisit as Chain 7 candidate.

## What to do instead

For the un-authored archetypes, surface the connection as **teacher-packet callouts** (single `calloutpeach` blocks, not multi-lesson chains). These are already in place for Chain 1 and Chain 2 — pattern is reusable.
