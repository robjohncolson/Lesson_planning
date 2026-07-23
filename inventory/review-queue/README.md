# Collision Review Queue -- README

## What this is

The (closed, frozen) dedup workstream identified 85 legacy question-bank IDs, all in lessons 5-1, 5-4, and 5-5, that each resolve to two distinct `item_uid`s in `questionbank/registry.jsonl` -- a "double-ingest-with-drift" pattern where the same source item was captured twice, with small textual differences between the two captures. This directory builds a practical, human-workable review queue over those 85 groups so a teacher (or reviewer) can look at both captures side by side and decide what, if anything, to do.

## Files

- `build_collision_review_queue.py` -- the generator. Reads the two read-only sources below and writes the three deliverables. Deterministic and reproducible.
- `collision_review_queue.json` -- 85 machine-readable records, sorted by lesson then confidence then legacy id. Use this for tooling, spreadsheets, or further sorting/filtering.
- `COLLISION_REVIEW_QUEUE.md` -- the human-workable queue. Open this file to work through the 85 groups by hand: each group shows both full prompts side by side, an exact character-level diff, a suggested (advisory) recommendation, and a checkbox block to record the actual decision.
- `README.md` -- this file.

## NEVER-AUTO-MERGE GUARANTEE

**Nothing in this workstream merges, collapses, renumbers, or deletes any registry row or item_uid.** Both distinct item_uids for every one of the 85 groups remain live and resolvable in `questionbank/registry.jsonl` exactly as they were before this queue was built. The "canonical keep" recommendation attached to each group is **advisory only** -- it is a suggestion for which capture is likely the cleaner/more complete one, not an action taken. The teacher makes the final merge/keep-both decision, recorded via the checkboxes in `COLLISION_REVIEW_QUEUE.md`. `questionbank/registry.jsonl` and everything under `inventory/dedup/` are read-only inputs to this workstream and are byte-unchanged by it.

## How the recommendation and confidence are computed

For each group, the two captures (A = lower registry line, B = higher registry line) are compared with Python's stdlib `difflib.SequenceMatcher` on the raw prompt text, producing a similarity ratio and the exact non-equal character-level opcodes. A set of drift tags is then computed (subset relation, trailing `MP.x` standards tag, whitespace/`\circ` spacing, differing visual encoding, differing LaTeX formatting, or generic textual drift). A fixed, deterministic ladder picks the recommendation from these tags, in this priority order:

1. **trailing_standards_tag** (captures are identical except one carries a trailing `MP.x` tag) -> keep the tagged capture. Confidence: high.
2. **subset_relation** (one capture's normalized text is fully contained in the other's, and the gap is NOT just a dropped `MP.x` tag) -> keep the longer/complete capture. Confidence: high.
3. **whitespace_or_spacing / circ_spacing** (captures are identical once whitespace is normalized) -> cosmetic only; suggested keep is the longer capture. Confidence: low.
4. Otherwise, substantive drift (visual_encoding / latex_formatting / other_textual) -> suggested keep is the longer capture as the richer/more-complete one. Confidence: medium.

**A "high" confidence recommendation still requires human confirmation.** Confidence describes how mechanically clear-cut the drift pattern is, not a green light to act automatically -- no step in this workstream ever merges anything on its own.

## How to regenerate

From the repo root:

```
python inventory/review-queue/build_collision_review_queue.py
```

The generator reads `questionbank/registry.jsonl` and `inventory/dedup/item_uid_alias_map.json` read-only (never opened for writing) and re-writes the three files listed above. Output is reproducible/byte-stable aside from the `generated_at_utc` timestamp in the JSON meta block.

## Reconciliation

900 registry rows / 815 unique legacy ids / 85 ambiguous groups. `group_count` in `collision_review_queue.json` must equal 85 -- the generator aborts before writing any output if this (or any other consistency check) fails.
