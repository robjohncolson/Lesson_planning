# Algebra 2 Platform — Post-Gate Next-Work Integration Report

**Date:** 2026-07-19 · **Author:** Fable (head architect) · **Status:** integration gate.
**Hierarchy:** Fable synthesizes · Opus manages/verifies · Sonnet implements · Codex (gpt-5.6-sol) reviews.
All work local-only: no git init, cloud, Schoology/CDP, secrets, or AP Stats contact. AP Stats `follow-alongs` untouched at `cb8ffd4`.

---

## 1. Executive status

- **Bootstrap release gate (identity-ledger service):** was declared OPEN after 6 rounds of receipt-boundary hardening; now **OPEN-PENDING** one small reachable fix (Unicode-whitespace `item_uid`, in final remediation — §5). No reflection-hardening rounds reopened.
- **Next-work tranche (4 workstreams):** inventory, dedup, course-model **complete + manager-signed-off**; item_uid **manager-signed-off**, one MEDIUM from its Codex review now being remediated.

## 2. Dispatch ledger

| Workstream | Manager | Implementer | Reviewer | Outcome |
|---|---|---|---|---|
| OCR/DOK content-readiness inventory | Opus | Sonnet | Codex | **CLOSED** — 4 MEDIUM fixed, signed off |
| Duplicate-ID / item-UID remediation | Opus | Sonnet | Codex | **CLOSED** — 2 MEDIUM + disposition, final sign-off |
| Canonical course-model fixtures + round-trip | Opus | Sonnet | Codex | **CLOSED** — 3 deeper HIGH closed by single-pass refactor; 31/31 |
| identity-ledger item_uid contract consistency | Opus | Sonnet | Codex | **1 MEDIUM in remediation** — gate OPEN-PENDING |

Fable performed objective-setting, dispatch, read-only synthesis checks, shared-directory integration, and byproduct sweeps only — no direct file implementation.

## 3. Workstream outcomes

### 3.1 OCR/DOK content-readiness inventory — CLOSED
Artifacts: `Lesson_planning/inventory/{content_readiness_inventory.json, CONTENT_READINESS_INVENTORY.md, build_content_readiness_inventory.py}`.
All 10 baselines independently reconfirmed by the Opus manager: **900 rows · 815 unique ids · 85 duplicate-id strings · 421 known-auto DOK · 0/858 topics on the nine · 114 images (53 for 3-5, 61 for 4-1)**. DOK status vocabulary: **421 known-auto / 437 unreviewed / 42 calibrated / 0 verified = 900**. Readiness across 37 slots: **0 ready / 10 partial / 1 blocked / 26 absent**.
4 MEDIUM (Codex) fixed + re-verified: (1) visuals split into **137 genuinely absent** vs **7 repairable broken paths** in 3-5 (PNGs exist under `questionbank/calibration/sources/`) + a proposed-path-fix block (analysis-only, registry unmodified); (2) review-queue triplets stated precisely — source-coordinate queue **125 coordinates / 176 excess rows / 301 participating**, duplicate-id **85 strings / 85 excess / 170 rows**; (3) all history/causation claims reworded to snapshot/UNKNOWN (zero "never/ever/double-append"); (4) validate-before-atomic-write (no `.tmp` leftovers). Registry byte-unchanged.

### 3.2 Duplicate-ID / item-UID remediation — CLOSED (final sign-off)
Artifacts: `Lesson_planning/inventory/dedup/{item_uid_alias_map.json, DUPLICATE_ID_REMEDIATION.md, build_item_uid_map.py}`.
Deterministic `item_uid = 'iu_'+sha1(lesson|source|sha1(prompt))[:12]`. Invariants (manager recomputed from scratch, 0 mismatches across 900 rows): **900 rows → 900 distinct item_uids · 815 legacy strings · 85 ambiguous (each 2 distinct uids) · 0 exact-duplicate**. Registry sha1 `37daea…974f` unchanged; map sha1 `86af18d…` byte-stable across re-runs.
2 MEDIUM generator fixes: `__file__`-derived paths + CLI overrides (portability tested in a scratch checkout); compute+self-assert-in-memory then atomic `mkstemp`+`fsync`+`os.replace` (failure-path tested, output preserved on failure).
**Disposition (locked rule applied):** all 85 collisions relabeled `needs-source-check` → **`merge-candidate`** — a human-review recommendation to merge the near-identical same-lesson/same-source pairs (the 5-1/5-4/5-5 double-ingest-with-drift pattern), **distinct item_uids retained, nothing auto-collapsed**.

### 3.3 Canonical course-model fixtures + lossless round-trip — CLOSED
Artifacts under `algebra2-platform/packages/course-model/` (9 files). **31/31 tests.** Fixtures cover all 14 §5.2 entities (item_uid as universal key, legacy_id multi-alias + ambiguous flag, both DOK vocabularies, ordered phases, `SCHOOLOGY_PLACEHOLDER::` external mappings — no real ids).
Codex review escalated through 5 HIGH data-integrity findings across rounds (record-field validation, JSON-safe scalar domain, `__proto__`-safe construction, exotic-object rejection, then three deeper array/collection/TOCTOU/tree-shape gaps). **Resolved decisively** by porting the proven single-pass `validateAndSnapshot` boundary from the sealed `receipt.js`: descriptor-only single-read capture into deep-frozen `Object.create(null)` nodes; proxy/symbol/accessor/non-enumerable/sparse-hole/extra-array-prop/exotic-prototype rejection; capture-once-emit-from-snapshot; exact top-level collection-shape validation. Manager's 12 structural probes confirmed a getter is **never invoked (reads=0)** and a Proxy trap **never fires**. Per the convergence rule this is the class-closing fix; residual purely-theoretical hostile-input hardening is **reachability backlog** (fixtures scaffold, no request/DB ingress).

### 3.4 identity-ledger item_uid contract consistency — gate-critical, MEDIUM in remediation
Artifacts: new `services/identity-ledger/src/validate-item-uid.js`, edits to `src/server.js` + `test/server.test.mjs`. **89/89 tests** (+10). Central invariant **confirmed correct by Codex**: `item.item_uid` is validated/normalized **exactly once** into a single immutable scalar used identically in the ledger INSERT (`$4`) and `buildReceiptPayload` — no re-derivation, no divergence; invalid shapes (object/array/null/number/boolean/empty/whitespace/>256) return **400 before any DB write**; the equality test verifies the receipt with the issuer public key.
Codex VERDICT NEEDS-FIX for: **1 MEDIUM [data-integrity]** — `trim()` doesn't strip U+0085 (Unicode White_Space), so a whitespace-only-U+0085 uid is accepted (fix: Unicode-correct whitespace rejection `/^\p{White_Space}+$/u` + test) — **now in remediation**; plus 2 LOW (boolean test cases; equality test asserts INSERT-bound param vs storage read-back) and 1 INFO (untracked subtree). Once the MEDIUM lands + sign-off, the gate closes.

## 4. Required disclosures

- **Namespace collision + recovery:** the inventory and dedup workstreams were both (my dispatch error) given the shared `Lesson_planning/inventory/` directory. The inventory manager's Sonnet drifted into producing dedup-named files; the manager then deleted `item_uid_alias_map.json` / `DUPLICATE_ID_REMEDIATION.md` / a builder as "scope drift" — which also removed the **dedup workstream's legitimate deliverables**. **Recovery:** I had the dedup Opus manager regenerate its artifacts into a disjoint `inventory/dedup/` namespace; deterministic regeneration produced a byte-identical map (sha1 `86af18d…`); registry unchanged. Root cause was a missing owned-path partition — now fixed by policy (below).
- **Direct-report exception:** several Sonnet implementers could not resolve their Opus manager's agent id (generic label) and reported **directly to Fable**. Per policy I forwarded each report to the owning Opus manager for explicit re-verification; the hierarchy and manager sign-off were preserved in every case.
- **Manager re-verifications:** every workstream closure carries an **independent Opus-manager re-verification** (recompute-from-source, not trusting child reports) — dedup (0 uid mismatches across 900 rows; final sign-off after the disposition change), inventory (all baselines reconfirmed), course-model (12 structural probes), item_uid (89/89 run by the manager; sign-off).
- **Owned-path policy (new):** `Lesson_planning/OWNED_PATHS.md` — every parallel workstream gets a disjoint owned namespace; no workstream may delete/clean files outside it (stray files are reported to Fable, not removed); shared-directory integration and byproduct sweeps (`.git`/`.agents`/`state`/`node_modules`/`__pycache__`) are Fable's, performed after managers finish; the direct-report exception is codified with manager sign-off preserved.

## 5. Bootstrap gate — **OPEN**

The item_uid Unicode-whitespace MEDIUM is **closed** (manager sign-off + final Codex re-review: `normalizeItemUid` rejects every all-Unicode-White_Space value incl. U+0085/U+00A0/U+2028 before any DB write/receipt/sign; interior/ordinary/256-char accepted; one immutable scalar feeds both the ledger INSERT and the signed receipt with no divergence; **94/0 tests**). No reachable BLOCKER/HIGH/MEDIUM remains → **gate OPEN**. The 6 completed receipt reflection-hardening rounds were not reopened.
The final re-review's literal verdict was NEEDS-FIX for **two LOW only**, both dispositioned to backlog per the refined convergence rule (§6): (a) a test-**label** nit ("stored ledger item_uid" for the INSERT-bound param) — reachability none; (b) an all-`U+200B` zero-width string accepted — U+200B is **not** Unicode whitespace, so it is outside the stated requirement, with no ledger≠receipt divergence.
Fable integration completed this pass: reconciled the root `package-lock.json` (course-model workspace had been added without regenerating it — now includes both workspaces, 0 vulnerabilities); swept runner byproducts; A2 tree pristine (55 files, no `.git`/`node_modules`/`state`).

## 6. Retained backlog (non-blocking)

- **Reflection-hardening (reachability backlog):** `canonicalJsonStringify` in `receipt.js` trusting mutable `Array.prototype` (needs a separate prototype-pollution flaw; no current ingress); course-model serializer residual theoretical hostile-input hardening (fixtures scaffold, no ingress).
- **Deployment/bootstrap LOW:** shell-form Dockerfile CMD → SIGTERM (exec-form staged for when graceful shutdown is added); docker-name TOCTOU on labeled disposable volumes.
- **item_uid LOW (from the final re-review, reachability none):** (a) rename the test description at `server.test.mjs:208` from "stored ledger item_uid" to "ledger INSERT-bound item_uid" (or add a persisted read-back) — the equality is correctly proven as application-binding, and storage-level equality is already covered by the behavioral Postgres test; (b) optionally reject all-zero-width-format strings (e.g. `U+200B`) if "semantically nonempty" is later defined to require *visible* content — currently out of scope of the Unicode-whitespace requirement.
- **Content escalations (from the inventory):** **4-1 stranded** (calibration + 61 screenshots on disk, 0 registry rows, no SE/TE — CLAUDE.md's "ready" is stale); **137 visual rows genuinely asset-less** + **7 repairable 3-5 broken paths**; **DOK-verification debt** (421 known-auto, 437 unreviewed, only 3-5 calibrated, 0 verified); **85 merge-candidate double-ingest pairs** (5-1/5-4/5-5) awaiting human review. All are *measured* here; remediation would be separate non-destructive workstreams under the owned-path policy.
- **WP10/versioning:** `algebra2-platform/` is an untracked subdir (U8 clean-private-repo pending); no aggregate workspace test script yet.

## 7. Next

On the item_uid sign-off, the gate opens; the two irreducible manual cloud-resource creations (isolated A2 Supabase + Railway projects, `BOOTSTRAP_HANDOFF.md`) remain the user's step, with nothing executed on the Fable side.
