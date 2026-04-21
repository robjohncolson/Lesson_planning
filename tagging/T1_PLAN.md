# Tier-1 polish plan — dedup + coverage-fill + diagnostics

**Goal.** Make the curriculum DAG rich enough that `qb_diagnose.py` emits *actionable swap recommendations* per lesson, not just drops. Three phases, run in order.

Self-contained for agent dispatch. Do not improvise outside the constraints.

---

## Phase 1 — Dedup (`dedup_registry.py`)

### Problem
`questionbank/registry.jsonl` contains ~200 rows that are re-ingests of the same Savvas source with `-2` suffix IDs. Left in, they (a) double-count every standards/DOK tally, (b) cause `qb_diagnose.py` to flag false "redundant practice" signals, (c) confuse prereq edges.

### Task
Write `dedup_registry.py` that:

1. Scan `questionbank/registry.jsonl` for **ID pairs** of shape `X` and `X-2` where both exist.
2. For each pair, verify the **duplicate condition**:
   - `prompt` equality after stripping whitespace and comparing normalized unicode (use `unicodedata.normalize('NFKC', ...)`)
   - Both have same `lesson`
3. **Resolve which to keep**, in priority order:
   - Whichever is referenced in any `build_L*_packets.py` (grep the builders for the ID — keep the referenced one).
   - Whichever has the populated `role` / `skill_tokens` / etc. v2 fields (keep the tagged one).
   - If truly tied, keep the non-`-2` variant.
4. For the **dropped** row, check nothing else references it (`prereq_ids`, `rehearses`, `echoes`, `used_in`). If it IS referenced anywhere, rewrite those references to point at the kept ID before deleting.
5. Emit `tagging/dedup_report.md`: table of (dropped_id, kept_id, reason, rewrites_performed).
6. Offer `--dry-run` flag; default to dry-run.

### Invariants (do not violate)
- **Never drop a row if prompts don't match after normalization.** Log as "suspicious pair, not dropped" instead.
- **Never drop a row that any builder imports.** Kept list always wins the builder reference check.
- **Rewrite references atomically** — if rewrites and drops are combined, do all rewrites first, then drop.

### Success criteria
- Dry-run first. Review `dedup_report.md` manually before non-dry-run.
- After non-dry-run: `python qb_graph.py` reports fewer nodes (match the dropped count), 0 edge-target errors.
- Pilot JSONLs in `tagging/*_pilot.jsonl` must be unaffected. If a pilot references a dropped ID, rewrite the pilot file too (this is part of step 4's reference-rewrite).

---

## Phase 2 — T1 coverage-fill tag pass

### Problem
Currently 148 items carry v2 fields (the "operational spine"). The remaining DOK≥2 Savvas items in the registry — roughly 150 more — are untagged. `qb_diagnose.py` needs these as **swap candidates** per lesson.

### Task

For each lesson in `[3-5, 4-1, 4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4, 6-5]`:

1. Enumerate **candidate items**: rows with that `lesson` field, `dok >= 2`, NOT already tagged (no `role` field), NOT an example/try-it duplicate (skip `-2` suffix if dedup incomplete).
2. For each candidate, produce a tagging row in `tagging/{lesson}_t1_coverage.jsonl` with:
   - `id`: registry ID
   - `role`: always `"explore-practice"` (these are pool items, not lesson-wired)
   - `standards`: infer from lesson (use the CCSS codes already used in the operational pilot for that lesson; don't invent new ones)
   - `prereq_ids`: **empty list** (don't invent prereq edges; pool items are unsequenced)
   - `rehearses`: **empty list**
   - `echoes`: **empty list** — do NOT add echoes. Only operational-spine items carry echoes. Adding echoes from pool items would dilute the cohesion signal.
   - `skill_tokens`: infer from prompt using the glossary in `tagging/skill_tokens.md`. If multiple tokens apply, include all. If none match, inspect the prompt and either (a) find the best existing token or (b) log to `tagging/skill_tokens_new_from_t1.md` as a proposed addition — do NOT invent new tokens inline.
   - `notes`: one line — what the item does, why it's tagged.

### Heuristics
- **Skill-token matching is keyword-based.** Examples:
  - `"\\sqrt"` or `"nth root"` → `evaluate-nth-root` / `simplify-nth-root-with-variables`
  - `"\\log"` → `evaluate-log` at minimum; `power-property-log` if "expand/condense"
  - `"extraneous"` → `identify-extraneous-solution`
  - `"inverse"` + `"variation"` → `recognize-inverse-variation` / `solve-for-k`
  - `"Error Analysis"` → `error-analysis-<domain>` (suffix by lesson family)
  - `"SAT/ACT"` → add `distractor-analysis` as a secondary token
- **Don't use the echoes field.** The whole point is to keep the cross-unit cohesion signal sparse and hand-curated.
- **When in doubt, tag conservatively** (fewer skill_tokens is safer than forcing a match).

### Output
- One JSONL per lesson: `tagging/{lesson}_t1_coverage.jsonl`.
- New-token proposals (if any): `tagging/skill_tokens_new_from_t1.md`.
- DO NOT merge into `registry.jsonl` yet. Leave that to a final `python merge_tags.py` run after Phase 2 completes.

### Success criteria
- Every DOK≥2 untagged Savvas item (per the filter above) has a tagging row.
- `python merge_tags.py --dry-run` reports all new rows resolve to registry IDs, zero missing.
- `python qb_graph.py` runs without errors after merge, `tagged` count ≈ 300.

---

## Phase 3 — Build `qb_diagnose.py`

### Task
Write `qb_diagnose.py` that reads the post-merge registry + shells and emits three reports under `graph/`:

1. **`graph/skill_bridge_gaps.md`** — Per lesson, list any `skill_token` that appears in a `dok3-driver` item's token list but does NOT appear in any earlier-role item (`do-now-*`, `launch-model-*`, `explore-tps`, `explore-practice`) in the SAME lesson. Format:
   ```
   ## Lesson 5-1
   - DOK-3 uses `rationalize-denominator` but no Practice item exercises it.
     Candidates from pool: [list IDs from T1 coverage with that token, same lesson]
   ```
2. **`graph/nominal_rehearsals.md`** — Per item tagged with `rehearses: ["topicX-assess-qY"]`, check whether the rehearsing item's `skill_tokens` overlap with the assessment shell's `skill_tokens`. Emit mismatches:
   ```
   - `4-1-savvas-q18` rehearses `topic4-lehs-q3` but token overlap is empty.
     Item tokens: [...]; Assessment tokens: [...]
   ```
3. **`graph/redundant_practice.md`** — Per lesson, find explore-practice / explore-tps items whose `skill_tokens` sets are **identical** (not just overlapping). Emit as candidate-drop lists with recommendations from pool:
   ```
   ## Lesson 4-3 P1
   Redundant group (same tokens):
   - `4-3-savvas-q22` [factor-polynomial, simplify-rational-expression]
   - `4-3-savvas-q24` [factor-polynomial, simplify-rational-expression]
   - `4-3-savvas-q25` [factor-polynomial, simplify-rational-expression]
   Suggestion: keep 1, drop 2. Candidate replacement from pool (with DOK-3-needed tokens):
   - `4-3-savvas-qNN` adds `ratio-modeling` (needed by DOK-3 q13)
   ```

### Invariants
- Pure-read. Never modifies `registry.jsonl` or any tag file.
- Do not fabricate suggestions — only recommend items that already exist in the registry with the needed tokens.
- Output must be markdown readable without tooling.

### Success criteria
- Runs cleanly: `python qb_diagnose.py` produces all three reports.
- `skill_bridge_gaps.md` is non-empty for at least 3 lessons (there ARE known gaps).
- `nominal_rehearsals.md` correctly identifies known-good rehearsals (empty is NOT a success; absence of output means absence of issues — but at least one is known to be mismatched per the schema review).

---

## Dependencies & execution order
1. Phase 1 runs first. Non-dry-run only after human review of `dedup_report.md`.
2. Phase 2 depends on Phase 1 being merged (else `-2` rows re-enter the tagging pool).
3. Phase 3 depends on Phase 2 being merged.

## Out of scope
- T2/T3 auto-tagging (DOK-1 Practice + Blooket pool). Defer until after diagnostics output is reviewed.
- Adding echo edges. Hand-curated only.
- Writing new curriculum content. All edits work from registry items that already exist.
- Any edit to builder scripts (`build_L*_packets.py`). Diagnostics output is *recommendations* for the human, not automated packet edits.
