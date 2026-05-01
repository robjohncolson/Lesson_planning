# Plan — Registry ID Normalization (Try-Its + Examples)

## Why

Registry IDs were ingested at different times with different conventions. Consequence: the `Try It N → <lesson>-tryit-N` heuristic in `backfill_from_teacher_tex.py` matched lesson 3-5 (whose Try-Its use the short form) but not 4-1 (whose Try-Its use `4-1-savvas-try-it-1-lesson-4-1-matches-examp`). The teacher-answer backfill was only able to backfill 3 of 929 missing answers because of this.

Normalizing to short forms unblocks future tooling, makes the registry humanly inspectable, and keeps tex bank-item labels short.

## Scope (TIGHT)

**Rename only Try-It and Example IDs.** Skip everything else (Savvas Practice items are already short; teacher-edition addendums are rarely-referenced and have meaningful suffixes; concept-box items are launch-side and lower-value).

| Old form | New form | Count |
|---|---|---|
| `<L>-savvas-try-it-N-lesson-<L>` | `<L>-tryit-N` | ~51 |
| `<L>-savvas-try-it-N-lesson-<L>-N` | `<L>-tryit-N` | ~26 |
| `<L>-savvas-try-it-N-lesson-<L>-matches-examp` | `<L>-tryit-N` | ~5 |
| `<L>-savvas-example-N-lesson-<L>` | `<L>-ex-N` | ~51 |
| `<L>-savvas-example-N-lesson-<L>-N` | `<L>-ex-N` | ~34 |
| `<L>-savvas-example-N-lesson-<L>-<suffix>` | `<L>-ex-N` (only if no collision) | ~6 |

`<L>` is a lesson-code in the form `D-D` (e.g. `4-1`). Numbers like `try-it-1a` → `tryit-1a`.

**Do NOT rename:**
- `<L>-savvas-qN` (already short)
- `<L>-savvas-teacher-edition-*` (teacher addendums — keep verbose suffixes; they encode role)
- `<L>-savvas-concept-box-*`, `<L>-savvas-concept-summary-*`
- `<L>-bridge-*`, `<L>-rti-*`, `<L>-lq-*`
- APStats and assessment shell IDs

## Deliverable

### `scripts/normalize_ids.py`

Single tool. Default `--dry-run`; explicit `--apply` to write.

Logic:

1. **Load registry.jsonl** + assessment_shells.jsonl.
2. **Build rename map** by regex over IDs:
   - `^([0-9]+-[0-9]+)-savvas-try-it-([0-9]+[a-z]?)(-lesson-[\d-]+(-[a-z][a-z\-]*)?)?$` → `\1-tryit-\2`
   - `^([0-9]+-[0-9]+)-savvas-example-([0-9]+[a-z]?)(-lesson-[\d-]+(-[a-z][a-z\-]*)?)?$` → `\1-ex-\2`
3. **Collision detection**:
   - If two old IDs map to the same new ID → STOP. Print all collisions, exit 1. The user must resolve manually before proceeding.
   - If a new ID already exists in the registry as a separate item → STOP same way.
4. **Print summary** (always, dry-run or not):
   - Number of renames per pattern
   - First 10 examples of each
   - Any items skipped because they have a suffix that didn't fit the regex (so user can review)
5. **Apply phase** (only if `--apply`):

   For each file pass:
   - **`questionbank/registry.jsonl`** — for each row: rewrite `id` field; rewrite any item in `prereq_ids`, `rehearses`, `echoes`, `used_in` lists.
   - **`questionbank/assessment_shells.jsonl`** — same.
   - **`tex/*.tex`** (skip `*_regen.tex`) — string-replace each old_id with new_id. Whole-token match (use word boundary or surrounding non-id chars to avoid partial substring matches like `4-1-savvas-try-it-1-lesson-4-1-matches-examp` being a substring of `4-1-savvas-try-it-1-lesson-4-1-matches-example-extension`). Use the `\b<id>\b` strategy or, since IDs contain hyphens (which `\b` doesn't bound), use `(?<![\w-])<id>(?![\w-])`.
   - **`lessons/*.yaml`** — same string-replace pattern.
   - **`tagging/operational_ids.json`** + `tagging/5-1_pilot.jsonl` — same.
6. **Atomic write**: write each modified file via `path.with_suffix(path.suffix + '.tmp')` + replace.
7. **Verify pass**: after writing, grep all old_ids across the same file set; report any leftover hits (should be zero).
8. **Stat report**: files modified; references rewritten per file.

**Do NOT** touch:
- Supabase tables — re-run `seed.py` afterward, that's the path
- `state/`, `legacy/`, `graph/`, `obsidian-wiki/`, `*.pdf`, `*.aux`, `*.log`
- `build_*_packets.py` (legacy, retired)
- `tex/.miktex-sandbox/`
- Generator scripts — they read the registry by id, no hardcoded id strings to update

## Verification (post-apply, the user runs these)

```powershell
# 1. No old IDs leaked anywhere
git grep -E "savvas-(try-it|example)-[0-9]+-lesson-[0-9]+-[0-9]+" -- questionbank/ tex/ lessons/ tagging/
# Expected: zero hits

# 2. New IDs are now in registry
python -c "import json; ids=[json.loads(l)['id'] for l in open('questionbank/registry.jsonl', encoding='utf-8')]; print('tryit:', sum(1 for i in ids if '-tryit-' in i)); print('ex:', sum(1 for i in ids if '-ex-' in i))"

# 3. Re-seed Supabase to push renamed items + edges
python supabase/seed.py
python supabase/seed_lesson_phases.py --apply

# 4. Rebuild any tex packets via web "Save & Rebuild" — should still compile
#    OR locally: pdflatex tex/L41_P2_teacher.tex (etc.) for spot-check
```

## Risks

- **Subtle: substring match in tex files**. If `4-1-savvas-try-it-1-lesson-4-1` appears inside another id like `4-1-savvas-try-it-1-lesson-4-1-deep`, naive replace breaks it. Use the `(?<![\w-])id(?![\w-])` boundary.
- **Sort old IDs by length DESCENDING before replace** so longest-prefix matches first. (e.g. process `4-1-savvas-try-it-1-lesson-4-1-matches-examp` BEFORE `4-1-savvas-try-it-1-lesson-4-1`.) The collision check at step 3 covers semantic collision; the length-sort covers substring overlap.
- **YAML and tagging JSON have IDs as values inside lists** — string replace on the whole file body is fine (we're replacing exact ID strings, not parsing structure).
- **Edges in registry**: prereq_ids/rehearses/echoes are list-of-strings inside each row. Walk them.
- **Don't rename anything that doesn't appear as a current registry id** — if an old `prereq_ids` entry references a now-deleted item, leave the dangling ref alone (seed.py already drops them with a warning; confirmed in the existing seed log).
- **Hand-authored `tex/L35_P4_do_now.tex`** has its own `\bankitem` labels but does not reference Try-It IDs. Confirm by greppping `tex/L35_P4_*` for any old-form IDs before/after.

## Non-goals

- Do NOT rename `*-savvas-teacher-edition-*` IDs.
- Do NOT rename `*-savvas-concept-box-*` IDs.
- Do NOT update Supabase tables directly — let `seed.py` do it.
- Do NOT touch the build scripts.
- Do NOT batch-rebuild PDFs in this task — verify-by-spot-rebuild only.

## Commit message

```
Registry: normalize Try-It and Example IDs to short forms

Replaces verbose Savvas-derived IDs like `4-1-savvas-try-it-1-lesson-
4-1-matches-examp` with `4-1-tryit-1`, and `5-4-savvas-example-4-
lesson-5-4` with `5-4-ex-4`.

Affected: ~170 IDs in registry.jsonl + every reference across
tex/*.tex bankitem labels, lessons/*.yaml item lists, and
tagging/operational_ids.json.

Unblocks the teacher-answer backfill (which was matching 3/929
items because the Try-It heuristic only worked for short-form
lessons). Also makes the registry humanly inspectable.

scripts/normalize_ids.py was used to perform the rewrite; safe to
re-run idempotently.
```

## Watch points for sonnet

- The regex MUST anchor with `^` and `$` to avoid matching IDs that have a recognizable Try-It prefix but a non-trivial suffix (e.g. `4-1-savvas-try-it-1-lesson-4-1-matches-example-extension`). If your regex doesn't match, leave the ID alone (skip into "review" bucket).
- For the file-replace pass, use `re.sub` with the boundary pattern `(?<![\w-]){escape(old)}(?![\w-])`. Don't use `str.replace` — it's substring-prone.
- Double-check teacher-edition addendum IDs (e.g. `4-1-savvas-teacher-s-edition-try-it-1-answer-elici`) DO NOT match the regex — they have `teacher-s-edition` or `teacher-edition` between lesson code and `try-it`. Verify a spot-check.
