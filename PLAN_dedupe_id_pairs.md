# Plan — Dedupe `-2` Re-ingest Pairs

## Why

Earlier dry-run of `scripts/normalize_ids.py` found 60 collisions: 30 pairs of items where the registry has BOTH `X` and `X-2` (e.g. `5-1-savvas-try-it-5-lesson-5-1` AND `5-1-savvas-try-it-5-lesson-5-1-2`). Both want to collapse to the same short form. The `-2` is a re-ingest artifact (CONTINUATION_PROMPT.md mentions "Topic 5 -2-suffixed registry rows" as a known issue).

To unblock normalization, we need to dedupe these pairs first: keep one full row under the canonical ID, drop the other, rewrite all references.

## Scope

**`scripts/dedupe_id_pairs.py`** — single tool. Default `--dry-run`; `--apply` to write.

**Targets ONLY pairs of items where:**
- Item `X` exists in registry, AND
- Item `X-2` (or `X-3`, `X-4` — handle any `-N` suffix where N≥2) exists in registry, AND
- Stripping the trailing `-N` yields the other item's id.

**Does NOT touch** items that share an id literally (the "85 duplicate-id" issue from seed.py — that's seed's own last-write-wins, leave alone). Different problem.

## Dedupe logic

For each detected pair `(canonical, suffixed)`:

1. **Score completeness** of each row:
   - Count of fields that are non-empty / non-null / non-default-list:
     - `prompt`, `dok`, `dok_rationale`, `correct`, `teacher_answer`, `notes`, `image`
     - `has_visual` true counts as +1
     - Non-empty arrays: `answers`, `topics`, `tags`, `skill_tokens`, `standards`, `prereq_ids`, `rehearses`, `echoes`
   - Score = total populated fields
2. **Pick winner**:
   - Higher score wins
   - Tie → canonical (no `-N`) wins
3. **Merge selectively** if the winner is missing fields the loser has:
   - For each field where winner is empty AND loser is non-empty, copy loser's value into winner
   - This is "best of both" without losing data
4. **Drop loser** from the registry
5. **Final id**: the winner is written under the canonical id (no `-N`). If the winner WAS the suffixed one, we still rename it to canonical.
6. **Rewrite references** to the loser (and to the suffixed id if winner was the canonical) → canonical id, across:
   - `questionbank/registry.jsonl` (prereq_ids, rehearses, echoes, used_in lists in OTHER rows)
   - `questionbank/assessment_shells.jsonl` 
   - `tex/*.tex` (skip `*_regen.tex`) — replace using `(?<![\w-])id(?![\w-])` boundary regex
   - `lessons/*.yaml`
   - `tagging/operational_ids.json` + `tagging/5-1_pilot.jsonl`

## Output

**Dry-run report:**
- Number of pairs detected
- For each pair: canonical id, suffixed id, scores, picked winner, fields merged
- Per-pair sample: print first 5 in detail
- Summary: rows to drop, references rewritten across each file

**Apply mode:**
- Atomic file writes (`.tmp` + replace)
- Post-write grep verification: zero hits for any dropped id

## Risks

- **Substring match in tex files**: same hazard as normalize_ids.py. Use `(?<![\w-]){escape(id)}(?![\w-])`.
- **Length-descending order**: process longest-id first so `id-2` is replaced before `id` gets replaced. (Actually since we're DELETING `id-2` and keeping `id`, the substring of `id-2` that contains `id` shouldn't be touched at all. But if winner was `id-2` and we're renaming → `id`, beware of pre-existing `id` references that should stay as-is. Reading the logic carefully: there are TWO sources of "old id" to rewrite to canonical:
  - The losing id (whichever it was)
  - The suffixed id (if winner was canonical, the suffixed id has refs that should now point at canonical; if winner was suffixed, the canonical id had refs that we're keeping pointing at canonical — no-op).
  Net: always rewrite suffixed → canonical. Then the losing id (if it was canonical, it's the same as canonical — no-op).
  Concretely: just rewrite ALL `<canonical>-N` references to `<canonical>`. Simple.
- **Don't double-merge**: if the same canonical has multiple suffixed siblings (X, X-2, X-3), iterate carefully. Probably handle X-3 vs X-2 vs X first by sorting all members of the equivalence class together; pick the highest-scoring; merge the rest into it.
- **No-op pairs**: if both rows are byte-for-byte identical, scoring ties, canonical wins, suffixed dropped. Still emit a "no merge needed" log.

## Verification (post-apply, run by user)

```powershell
# 1. No suffixed-id references leaked
git grep -E "[a-z]-[0-9]+(-[a-z][\w-]*)?-[2-9]\b" -- questionbank/ tex/ lessons/ tagging/
# Expected: very few hits (only legit IDs that happen to end in -2..-9 as content, not as dedupe artifacts)

# 2. Pair count went from 30 to 0
python -c "
import json
ids = {json.loads(l)['id'] for l in open('questionbank/registry.jsonl', encoding='utf-8')}
pairs = [i for i in ids if i.endswith('-2') and i[:-2] in ids]
print(f'remaining -2 pairs: {len(pairs)}')
"

# 3. normalize_ids.py dry-run should now show 0 collisions
python scripts/normalize_ids.py
```

## Then what

After dedupe applies cleanly:
1. Re-run `python scripts/normalize_ids.py` (dry-run) — collisions should be gone.
2. Run `python scripts/normalize_ids.py --apply`.
3. Run `python supabase/seed.py` to push everything to Supabase.
4. Run `python supabase/seed_lesson_phases.py --apply`.

## Non-goals

- Do NOT touch the 85 same-id literal duplicates that seed.py already last-write-wins.
- Do NOT touch IDs that don't have a sibling without the `-N` suffix.
- Do NOT touch Supabase tables directly — re-seed is the path.
- Do NOT batch-rebuild PDFs.

## Commit message

```
Registry: dedupe -N re-ingest pairs in lessons 5-1, 5-4, 5-5, 6-3-5

Per-lesson Try-It and Example items had paired entries from re-
ingestion (e.g. 5-1-savvas-try-it-5-lesson-5-1 + ...-lesson-5-1-2).
Picked the more-populated row, merged any unique fields from the
sibling, dropped the duplicate, rewrote references across registry/
tex/yaml/tagging.

Unblocks scripts/normalize_ids.py (which was halting on 60 collisions).
```
