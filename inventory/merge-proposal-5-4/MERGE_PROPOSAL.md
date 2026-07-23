# MERGE PROPOSAL — Lesson 5-4 DOK-Conflict Duplicate Pairs

**PROPOSAL — NOT EXECUTED; NO MERGE PERFORMED; AWAITING RC AT THE MERGE-APPROVAL GATE**

**NO MERGE HAS BEEN PERFORMED. NOTHING IN `questionbank/registry.jsonl`, `tools/dok-review/review_log.jsonl`, ANY CONSUMER ARTIFACT (`tex/`, `web/pacers/`, `legacy/`, `tools/dok-review/proposals/`), OR ANY OTHER `inventory/` FILE HAS BEEN MODIFIED. THIS DOCUMENT AND ITS MACHINE-READABLE COMPANION (`merge_proposal_5_4.json`) ARE THE ONLY TWO NEW FILES CREATED.**

Generated: 2026-07-22

## Scope

22 lesson 5-4 DOK-conflict duplicate pairs. For each pair, RC decided **MERGE-CANDIDATE**: copy B (higher registry line, source-enriched, agrees with the Savvas TE) is the preferred canonical survivor; copy A (lower line, older sparse ingestion) would become a retained alias/tombstone. **This is a proposal only — it awaits RC at a future merge-approval gate.**

## RC's rationale (verbatim, per decision note in `teacher_decisions_rc_v2.json`)

> same Savvas item number (#N) in both copies; copy B agrees with the TE Item Analysis (TE DOK) -- as it does in all 22 conflict pairs; copy B is the source-enriched record; copy A is the older sparse ingestion, sometimes omitting directions or malformed; rubric rule 1 must not certify a sparse/malformed copy as an exact unchanged textbook item; defective duplicate content resolves through identity/content remediation, not relabeling. This decision authorizes NO merge, NO delete, NO renumber, NO registry mutation, and NO discarding of either item_uid; both uids and all provenance are preserved. Any actual merge requires a separate future RC approval at the merge-approval gate.

Source: inventory/decision-console/teacher_decisions_rc_v2.json (sha256 `d4bd81f2ce3865a4771ac93dc65ceeb47d22f990eb2e66fbb1b015ff53981637`), one `note` field per pair, item number substituted for `#N`.

## Naming conventions (read this before the table)

- **copy_a** = the copy at the LOWER registry line (matches te_comparison_5_4.json's convention) -- becomes the retained_alias / tombstone candidate.
- **copy_b** = the copy at the HIGHER registry line -- becomes the preferred_survivor.
- **Caveat:** Two OTHER surfaces use a/b labels with DIFFERENT meanings and must not be confused with the above: (1) inventory/dashboard/content_readiness.json's dok_conflict_subset uses uid_a/uid_b keyed by DOK (uid_a = lower-DOK copy, uid_b = higher-DOK copy) -- the reverse convention; (2) inventory/review-queue/collision_review_queue.json's capture_a/capture_b IS keyed by registry line like this proposal (capture_a = lower line), but its OWN 'recommendation.canonical_keep' is an independent confidence-scored heuristic that disagrees with RC's decision for one pair (5-4-savvas-q45) -- flagged per-pair in that pair's references.collision_review_queue.discrepancy_note.

## The 22 pairs

| Legacy ID | Survivor (copy B) uid / line / DOK | Alias (copy A) uid / line / DOK | TE DOK | Prompt similarity | Unique-to-A fields | References found |
|---|---|---|---|---|---|---|
| 5-4-savvas-q21 | `iu_c470845cd9f5` / L308 / DOK1 | `iu_bf2e53fb5aaa` / L279 / DOK2 | 1 | 0.3750 (eq: no) | 0 | 44 |
| 5-4-savvas-q22 | `iu_2687f61c33c5` / L309 / DOK1 | `iu_84131456696f` / L280 / DOK2 | 1 | 0.2564 (eq: no) | 0 | 40 |
| 5-4-savvas-q23 | `iu_e067aeabdb5e` / L310 / DOK1 | `iu_5d11f886423f` / L281 / DOK2 | 1 | 0.3111 (eq: no) | 0 | 34 |
| 5-4-savvas-q24 | `iu_da8e33db9d06` / L311 / DOK1 | `iu_e106ef5ef48e` / L282 / DOK2 | 1 | 0.4000 (eq: no) | 0 | 34 |
| 5-4-savvas-q25 | `iu_cd45fbec9dbc` / L312 / DOK1 | `iu_8e4e2787396a` / L283 / DOK2 | 1 | 0.5882 (eq: no) | 0 | 41 |
| 5-4-savvas-q26 | `iu_323815e656c9` / L313 / DOK1 | `iu_68d1a5b3e8f8` / L284 / DOK2 | 1 | 0.6061 (eq: no) | 0 | 41 |
| 5-4-savvas-q27 | `iu_26a15cb256cd` / L314 / DOK1 | `iu_9681eda37337` / L285 / DOK2 | 1 | 0.6500 (eq: no) | 0 | 41 |
| 5-4-savvas-q28 | `iu_d2eb395dfeee` / L315 / DOK1 | `iu_18cac1a8167a` / L286 / DOK2 | 1 | 0.5806 (eq: no) | 0 | 34 |
| 5-4-savvas-q29 | `iu_6eb3a7c167c0` / L316 / DOK1 | `iu_e7638fcec56e` / L287 / DOK2 | 1 | 0.1449 (eq: no) | 0 | 34 |
| 5-4-savvas-q30 | `iu_3646823c6297` / L317 / DOK1 | `iu_32a6c3b34ca1` / L288 / DOK2 | 1 | 0.2078 (eq: no) | 0 | 34 |
| 5-4-savvas-q31 | `iu_d8950c94a8bc` / L318 / DOK1 | `iu_beec9e3bdf89` / L289 / DOK2 | 1 | 0.1867 (eq: no) | 0 | 34 |
| 5-4-savvas-q32 | `iu_c1771afa2a7f` / L319 / DOK1 | `iu_74cca3783f59` / L290 / DOK2 | 1 | 0.1690 (eq: no) | 0 | 34 |
| 5-4-savvas-q33 | `iu_c6ab822e227b` / L320 / DOK1 | `iu_3adc6df8b95d` / L291 / DOK2 | 1 | 0.7429 (eq: no) | 0 | 41 |
| 5-4-savvas-q34 | `iu_748071c541b9` / L321 / DOK1 | `iu_a96e5311a459` / L292 / DOK2 | 1 | 0.7059 (eq: no) | 0 | 40 |
| 5-4-savvas-q35 | `iu_22bcc429d37c` / L322 / DOK1 | `iu_3b2700252892` / L293 / DOK2 | 1 | 0.6429 (eq: no) | 0 | 34 |
| 5-4-savvas-q36 | `iu_3c4458af5f01` / L323 / DOK1 | `iu_5663d63244d2` / L294 / DOK2 | 1 | 0.1818 (eq: no) | 0 | 34 |
| 5-4-savvas-q37 | `iu_994890f62b0f` / L324 / DOK1 | `iu_c8710e0538db` / L295 / DOK2 | 1 | 0.2025 (eq: no) | 0 | 34 |
| 5-4-savvas-q38 | `iu_b04e59b85637` / L325 / DOK1 | `iu_80622035e09c` / L296 / DOK2 | 1 | 0.1558 (eq: no) | 0 | 34 |
| 5-4-savvas-q39 | `iu_6826655b6fe7` / L326 / DOK1 | `iu_6afe9c1960b0` / L297 / DOK2 | 1 | 0.6872 (eq: no) | 0 | 45 |
| 5-4-savvas-q41 | `iu_3c70a19c8d36` / L328 / DOK3 | `iu_77d25e1e6131` / L299 / DOK2 | 3 | 0.9981 (eq: no) | 0 | 70 |
| 5-4-savvas-q44 | `iu_097a1fc43439` / L331 / DOK1 | `iu_25b106c19a20` / L302 / DOK2 | 1 | 0.7735 (eq: no) | 0 | 49 |
| 5-4-savvas-q45 | `iu_b69ba77e28bf` / L332 / DOK1 | `iu_57481c4ff850` / L303 / DOK2 | 1 | 0.8339 (eq: no) | 0 | 33 |

Total reference-surface hits across all 22 pairs (core structured surfaces + tex/ + other repo hits): **859**.

None of the 22 pairs has prompts that are normalized-equal (lowercased, whitespace-collapsed, punctuation-stripped) — every pair differs in wording and/or LaTeX notation, which is exactly why they show up as DOK-conflict duplicates rather than harmless re-captures. Similarity ranges from the lowest-overlap pair (0.1449, 5-4-savvas-q29) to the near-identical wording pair (0.9981, 5-4-savvas-q41, which differs only in LaTeX fraction notation).

### Notable prompt-diff findings

- **`5-4-savvas-q44`** — copy A's table is genuinely malformed (3-column header, 4-value data rows — an off-by-one misalignment), the clearest concrete instance of RC's "sometimes malformed" description of copy A.
- **`5-4-savvas-q45`** — formatting-only difference (LaTeX `itemize` vs plain `A./B./...` lines); no wording change.
- **`5-4-savvas-q39`** — copy A omits the "Solve using the formula (BSA=...)" instruction stem and lacks an answer key in `notes`; copy B has both.
- **`5-4-savvas-q41`** — wording is identical; only the exponent-fraction LaTeX notation differs (highest similarity of the 22, 0.9981).
- Most other pairs (`q21-24`, `q29-32`, `q36-38`) follow the same shape: copy A is the bare equation, copy B prepends the Savvas directions sentence ("Solve each radical equation[. Check for extraneous solutions.]").
- `q25-28` and `q33-35` follow "Solve for (y)." / "Solve." stems the same way.

### Field-level finding (all 22 pairs)

`fields_only_in_copy_a` is **empty in all 22 pairs** — copy A contributes zero fields that copy B lacks. Copy A contributes no field absent from copy B: copy B carries `role`, `standards`, `prereq_ids`, `rehearses`, `echoes`, `skill_tokens` (and, for most pairs, `teacher_answer`) that copy A never has at all, but copy A's prompt and DOK values differ and remain preserved in the alias row. Copy A's only distinctive content in every pair is its own (superseded) prompt phrasing and its own DOK label — both already outvoted by the TE in all 22 pairs.

## Tombstone / reversal design — v2 (applies to all 22 pairs; see each pair's `tombstone_design` in the JSON for the pair-specific raw-line capture)

> **Amended 2026-07-23 (NT10 Codex-R2b, findings M1 + M2).** The original v1 design (replace the row with a nested `original_row` tombstone) is **SUPERSEDED**: it would have moved the item_uid identity basis (`id`, `lesson`, `source`, `prompt`) off the top level, and `inventory/dedup/build_item_uid_map.py` recomputes uids from **top-level** `lesson`/`source`/`prompt` and groups by **top-level** `id` — a post-merge regeneration would have collapsed every tombstone to the same null identity and destroyed the alias joins. v2 keeps the generator's contract and is verified empirically (below).

At a **future, separately-gated** merge execution (not performed by this proposal):

1. Copy A's registry row is **never deleted and never restructured**. Its **entire original field set stays in place at top level** — including the identity basis (`id`, `lesson`, `source`, `prompt`) the dedup-map generator recomputes uids from.
2. The merge **ADDS exactly four top-level marker fields** to the row (nothing moved, nested, or removed):

   ```json
   {
     ...copy A's full current row, all fields unchanged at top level...,
     "status": "merged-alias",
     "alias_of": "<copy B uid>",
     "merged_at": "<execution timestamp>",
     "merge_authorization": "<the future RC merge-approval-gate record, NOT this proposal>"
   }
   ```

   Consumers that must exclude alias rows filter on `status == "merged-alias"`.
3. **Reversal — whole-line replacement (byte-for-byte)**: each pair's `tombstone_design.registry_row_copy_a_raw` in the JSON stores the **original raw JSONL line** captured from `questionbank/registry.jsonl`'s bytes (`raw_line_utf8` without the terminator, plus `raw_line_base64_with_terminator` and its sha256; the registry is UTF-8, no BOM, LF-terminated except 4 CRLF lines at 897–900, none of them a copy-A line). Rollback = replace the tombstone line in its entirety with the base64-decoded original bytes. Because the stored value is the raw line itself — not a re-serialization of a parsed object — restoration is exact at the byte level (key order, whitespace, escape spelling, terminator). v1's delete-the-marker-fields procedure (which also miscounted its own field list) is superseded; no field-by-field deletion is involved.

**Empirical verification (scratch only — the real registry was never touched):**

- **M1 (identity survives regeneration):** a scratch registry with all 22 copy-A lines replaced by v2-shaped tombstones was run through `build_item_uid_map.py` — SELF-ASSERTION PASS (900 rows / 900 uids / 815 legacy ids / 85 ambiguous), and the regenerated alias map is **byte-identical** to the committed `item_uid_alias_map.json` (`sha256 be4b507b…`). Every copy-A uid and legacy-id grouping reproduced unchanged.
- **M2 (rollback is truly byte-for-byte):** applying the 22 stored whole-line replacements to that tombstoned scratch registry reproduces the locked registry **exactly** (`sha256 b7f9a040…`).

### A→B resolver contract (where alias resolution lives)

- **Row level (authoritative):** the tombstone row's top-level `alias_of` names the surviving copy-B uid — resolvable from the registry row alone. Alias chains are forbidden (an `alias_of` target must never itself be a `merged-alias` row; single-hop only).
- **Join level:** the dedup map keeps listing BOTH uids under the legacy id (identity basis unchanged — proven above). At merge execution, `build_item_uid_map.py` gains an **additive** enrichment: entries whose rows include a `merged-alias` row get `resolved_alias: {alias_uid, survivor_uid, merged_at}`; `ambiguous` stays computed exactly as today, and consumers switch on the annotation — never on uid deletion.
- **Consumer paths:** wave plan / review tool key by item_uid via the registry-line join (both uids stay addressable); course-map edges naming a copy-A uid resolve via `alias_of` (and the 3 currently target-ambiguous incoming edges become resolvable); dashboard/console verified sets already reference only copy-B uids; tex/ and human surfaces cite legacy ids, which keep resolving through the alias map unchanged.

### Post-merge invariants (machine-checkable; a verifier runs all six before the execution is accepted)

I1 tombstone shape per pair (markers present + identity basis equal to the parsed capture) · I2 dedup-map regeneration reproduces 900/900/815/85 and every pair's two uids at the same lines · I3 every copy-A uid resolves in one hop to a live, non-alias survivor · I4 no join surface dangles (review log 39, proposals 39, wave plan 900, course map, dashboard uid sets, console section 2, dedup map — every reference hits a non-alias row or resolves via I3) · I5 rollback capability intact (stored raw lines hash-verify; applying all 22 reproduces `b7f9a040…`) · I6 consumer regeneration green in documented order. Full text in `merge_proposal_5_4.json` → `meta.post_merge_invariants`.

## Preservation plan (all 22 pairs)

- **Survivor (copy B)** keeps its own prompt, answers, dok, dok_rationale, notes/teacher_answer, role, standards, prereq_ids, rehearses, echoes, skill_tokens, and visual fields exactly as they stand — nothing about copy B changes.
- **Alias (copy A)** keeps its full original row **in place at top level on the tombstone row itself** (v2: the merge only adds the four marker fields), plus the byte-exact original raw line preserved in this proposal's `registry_row_copy_a_raw` capture for whole-line rollback — not blended into copy B.
- **Copy-over candidates from A to B**: **none, in any of the 22 pairs** — `fields_only_in_copy_a` is empty everywhere, so there is nothing on copy A that copy B lacks and would need copying forward.

## Proof of no dangling evidence (per surface)

| Surface | Count | Finding |
|---|---|---|
| `tools/dok-review/review_log.jsonl` | 39 entries total | 22 match copy-B survivors (all VERIFIED); 0 match copy-A aliases (zero); 17 belong to the 7 agreeing pairs + 3 singletons (unrelated to this proposal) |
| `tools/dok-review/proposals/` | 39 files total | 22 match copy-B survivors; 0 match copy-A aliases (zero); 17 belong to other uids |
| `dashboard.aggregates.dok.review_state_uid_sets.verified` | 39 uids total | 22 copy-B survivors present; 0 copy-A aliases present (zero) |
| `course_map.json` prereq/rehearses/echoes edges | 193 resolved edges repo-wide | 14 edge-refs touch these 22 pairs (9 of 22 legacy ids have any edge); 11 use copy-B as source, 0 use copy-A as source (zero); 3 incoming edges are currently target-ambiguous and get RESOLVED (not orphaned) by the merge |
| `console_data.json` section 2 | 22 pairs | all 22 already listed as decision-UI rows |
| `item_uid_alias_map.json` | 22 of 85 ambiguous groups | all 22 legacy ids ambiguous:true, exactly 2 uids each, both retained |
| `teacher_decisions_rc_v2.json` | 22 decisions | one merge-candidate decision per pair — the authorizing record for this proposal |
| `tex/*.tex` built packets | 9 of 22 pairs cited | all citations bind to copy-B's verbatim text (confirmed by inspection); 13 pairs have no individual tex citation yet |
| Every other repo file (generated reports, frozen-legacy builders, graph/tagging/skeleton tooling snapshots, archived agent-session logs) | 98 distinct files, 1376 line hits | 0 files bind to a copy-A uid WITHOUT also carrying the legacy id or copy-B uid — nothing is uniquely anchored to a copy-A identity |

**Conclusion: every join in every surface either (a) already targets the surviving copy-B uid directly, or (b) targets the copy-A uid only inside historical/comparison records that a merge does not rewrite, or (c) is currently ambiguous between both candidates and gets resolved — never orphaned — by the merge. Nothing dangles.**

## Summary

- Pair count: **22**
- Survivor set: **22** copy-B uids
- Alias set: **22** copy-A uids
- Copy-A-unique fields found across all 22 pairs: **0**
- Wave-plan consistency: All 22 pairs: copy_b review_state=verified/dok_status=verified; copy_a review_state=unreviewed/dok_status=unreviewed. 0 mismatches found.

**NONE. No merge, alias, or tombstone has been created or executed by this proposal. registry.jsonl, review_log.jsonl, and all consumer artifacts are unchanged.**

---

## AWAITING RC AT THE MERGE-APPROVAL GATE

This proposal performs no execution. It exists so RC can review the pair-by-pair evidence, the tombstone/reversal design, and the proof of no dangling evidence, and decide at a future, separate merge-approval gate whether to authorize actually writing the 22 tombstone records into `questionbank/registry.jsonl`.
