# Registry schema v2 — DAG fields (proposal)

Additive. No existing tool breaks. Fields default to empty list / null.

## New fields

| Field | Type | Purpose | Example |
|---|---|---|---|
| `standards` | `list[str]` | State/CCSS codes the item addresses. Enables standards-coverage queries. | `["A-APR.B.3", "F-IF.C.7c"]` |
| `prereq_ids` | `list[str]` | Registry IDs a student must already have grasped to attempt this. Drives the DAG edges. | `["3-5-savvas-q14", "4-1-savvas-q19"]` |
| `rehearses` | `str \| null` | Pointer to the assessment item this prepares, OR a future-lesson item it is laddering into. Makes through-lines explicit. | `"topic3-assess-q6"` or `"5-4-savvas-q22"` |
| `echoes` | `list[str]` | Conceptual parallels across units — the **cohesion** signal. "Storage Box (#27 in 3-5) and Cylinder Capstone (#50 in 5-1) both ask: derive a dimension from a constraint equation." | `["3-5-savvas-q27"]` |
| `skill_tokens` | `list[str]` | Atomic moves the item exercises. Let the DAG cluster by skill rather than by topic label. | `["extract-rational-root", "rationalize-denominator"]` |

All five are optional; an untagged item still works in every existing builder.

## What the DAG unlocks

Once ≥80% of items carry `prereq_ids` + `standards` + `skill_tokens`, `qb_graph.py` (one afternoon) gives you:

1. **Standards-coverage heatmap** — where the year is thin.
2. **DOK-3 desert detector** — lessons whose DOK-3 driver has no prereq path from prior lessons are cohesion-failures.
3. **Through-line view** — given an assessment item, show every registry item that feeds it via `rehearses` or transitive `prereq_ids`.
4. **Skill-token reuse** — if `rationalize-denominator` appears in 5-1, 5-4, and 6-3, you have a spine. If it appears once, it's orphaned.
5. **Echo graph** — renders `echoes` edges separately. This is the "integrated year" picture.

## Before / after

**Before** (current, real row from registry):

```json
{"id": "3-5-savvas-q27", "lesson": "3-5", "prompt": "Storage box ...", "dok": 3, "topics": ["modeling", "volume"]}
```

**After** (v2-tagged):

```json
{"id": "3-5-savvas-q27", "lesson": "3-5", "prompt": "Storage box ...", "dok": 3,
 "topics": ["modeling", "volume"],
 "standards": ["A-CED.A.1", "A-APR.B.3"],
 "prereq_ids": ["3-5-savvas-q14", "3-5-savvas-q15"],
 "rehearses": "topic3-assess-q6",
 "echoes": ["5-1-savvas-q50", "6-4-savvas-qNN"],
 "skill_tokens": ["build-polynomial-from-constraint", "interpret-root-in-context"]}
```

## Tagging template — per-item worksheet

Use during the dry-run (5 → 6 → 4 → 3). Copy this block per item as you read:

```
id:              <paste>
lesson:          <paste>
one-line prompt: <paste>
---
standards:       [                          ]   # 1–3 codes. If unsure, leave empty.
prereq_ids:      [                          ]   # items a student needs FIRST
rehearses:       <assessment-id or lesson-id>   # what this laddens toward
echoes:          [                          ]   # cross-unit conceptual parallels
skill_tokens:    [                          ]   # atomic moves, kebab-case
notes:           <one line: why this item earns DOK-3 / why it's echo-worthy>
```

## Tagging heuristics

- **Do not tag every item.** Do `dok ≥ 2` first, plus anything flagged as a DOK-3 driver or assessment-rehearsal. Target: ~30% coverage buys 80% of the DAG value.
- **`prereq_ids` is the edge**; everything else is a node label. If you tag nothing else, tag this.
- **`echoes` is the expensive one**, and the one the DAG actually exists for. Err toward recording a suspected echo; pruning is cheap.
- **`skill_tokens` emerges from the read.** Start a `skill_tokens.md` glossary on day one so you don't invent three names for the same move.

## Migration

- `qb_append.py` already validates optional fields — add the five to its accepted schema (10-line patch).
- Back-fill is additive: `jq` or a 20-line script merges tagged rows into `registry.jsonl` without rewriting unchanged items.
- `qb_graph.py` (new, ~80 lines) reads the registry and emits:
  - `graph.html` — Pyvis or Mermaid, clickable node → prompt
  - `coverage_report.md` — standards × lesson matrix, DOK-3-desert list, orphan items
