# Algebra 2 Platform — Bootstrap Staging, Round-3 Review Synthesis

**Date:** 2026-07-19 · **Author:** Fable (head architect) · **Status:** staged, NOT deployed. No cloud execution.
**Scope:** `C:\Users\rober\Downloads\Projects\algebra2-platform` (private A2 monorepo skeleton — untracked, not yet a repo).
**This is a review record, not self-certification.** Verdicts and findings below are Codex GPT-5.6 SOL's.

---

## 1. Three formal, model-verified verdicts

All three ran read-only on the corrected tree. Model + working dir verified from the Codex rollout logs (`~/.codex/sessions/2026/07/19/rollout-*.jsonl`): **`model: gpt-5.6-sol`, cwd `…\algebra2-platform`** for each.

| # | Bounded scope | Duration | **Formal verdict** |
|---|---|---|---|
| R1 | Configuration / database-destination contract (`config.js`, `test/config.test.mjs`, `.env.example`, `SECRETS_MANIFEST.md`) | 192.8 s | **NEEDS-FIX** |
| R2 | Ed25519 receipt format & verification (`receipt.js`, `test/receipt.test.mjs`) | 230.3 s | **NEEDS-FIX** |
| R3 | SQL/RLS, Docker, smoke route, bootstrap handoff (`0001_bootstrap.sql`, `rls_behavioral_test.sh`, `server.js`, `Dockerfile`, `BOOTSTRAP_HANDOFF.md`) | 396.2 s | **NEEDS-FIX** |

All three completed well inside the 560 s runner limit (no truncation). Result envelopes captured only the trailing `VERDICT:` line; full findings were recovered from each review's transcript.

**Key point:** the three *original* round-2 blockers are **confirmed resolved** by Codex — structural URL validation, canonical Ed25519 verification, and functional least-privilege RLS all work as intended. Every finding below is *new* hardening, not a regression.

---

## 2. Remaining blockers / warnings (most-severe first)

No BLOCKER-level findings. One HIGH, two MEDIUM, three LOW/INFO, two WARN.

| Sev | Review | Location | Finding | Concrete fix |
|---|---|---|---|---|
| **HIGH** | R3 | `sql/0001_bootstrap.sql:91,129`; `BOOTSTRAP_HANDOFF.md:124` | Only UPDATE/DELETE triggers exist. `REVOKE … FROM PUBLIC` does not remove the table **owner's** inherent TRUNCATE, so the owner can truncate either append-only table while the handoff implies mutation is blocked. | Add `BEFORE TRUNCATE` statement triggers on `item_ledger` + `receipts` (and owner-TRUNCATE assertions in the behavioral test), or explicitly document the trusted-owner escape and narrow the guarantee. |
| **MED** | R2 | `src/receipt.js:44` | `canonicalJsonStringify` is not total for exotic signer inputs (`{x:[undefined]}`→`{"x":[]}`, `Date`/`Map`→`{}`, `NaN`/`Infinity`→`null`); `signReceipt` could attest a payload that differs from the object it was asked to sign. | Validate the JSON domain **before signing**: require finite numbers, plain/null-proto objects, dense arrays; reject undefined, functions, symbols, bigint, sparse arrays, cycles, exotic objects. |
| **MED** | R3 | `test/db/rls_behavioral_test.sh:70,154` | Startup/teardown force-remove the fixed-name container/volume, so an unrelated resource with the same name could be destroyed. | Abort if a resource with that name pre-exists (or label-scope and delete only matching labels). |
| **LOW** | R3 | `src/server.js:113` | The smoke gate checks truthiness of the injected flag, not `=== true`; a truthy non-`'true'` value could enable writes. | Require `config.bootstrapSmokeEnabled === true` (config already parses env by exact equality). |
| **LOW** | R2 | `test/receipt.test.mjs:185` | Alternate-encoding tests pass only via `=` padding; no deterministic `+`/`/` or nonzero-tail-bit variant, no non-object payload case. | Add same-byte `+`/`/` and nonzero-tail-bit variants + signed primitive/array payload cases. |
| **INFO** | R1 | `test/config.test.mjs:165` | No regression tests for hostname parser edges (trailing dot, userinfo, uppercase, punycode, explicit ports). | Add assert.throws/pass cases matching the hostname-only policy. |
| **WARN** | R1 | `.env.example:43`; `docs/SECRETS_MANIFEST.md:21` | Stale substring wording contradicts the new structural enforcement; the manifest lists AP-Stats id literals outside the deny-list, making the "no literals outside guards" claim false. | Reword to structural language; reference the code deny-list instead of reproducing the ids. |

**Codex confirmed as substantive (already correct):** R1 structural `new URL()` validation and rejection tests; R2 header pin, per-segment canonical base64url, sig-length-64, canonical payload re-serialization, real public-key verification, and the header-substitution / extra-field / payload-tamper / sig-tamper / wrong-length / wrong-key / deterministic-round-trip tests; R3 RLS policies scoped to the runtime role (functional), receipts append-only for UPDATE/DELETE, no speculative grants, no password in SQL, smoke 404-gate, `/ready` + liveness `/health`, Dockerfile `npm ci`, and the behavioral test genuinely proving its claims.

---

## 3. Exact round-3 file delta (vs the round-2 tree)

**Added (1):**
- `services/identity-ledger/test/db/rls_behavioral_test.sh` — disposable named-Postgres RLS behavioral test.

**Modified (10):**
- `services/identity-ledger/src/config.js` — structural `new URL()` validation of both destinations (HTTPS `<ref>.supabase.co` for the API URL; postgres direct/pooler shape with ref derived from host/username for the DB URL); required `A2_EXPECTED_SUPABASE_REF`.
- `services/identity-ledger/test/config.test.mjs` — structural rejection tests (HTTPS-as-DB, wrong scheme, deceptive password/query ref, wrong host ref, non-`postgres` username, ref mismatch, malformed, non-https REST, wrong REST host).
- `services/identity-ledger/src/receipt.js` — canonical Ed25519: header pin, per-segment canonical base64url (charset + decode/re-encode equality), sig-length-64, canonical payload re-serialization, real public-key verify, fail-closed.
- `services/identity-ledger/test/receipt.test.mjs` — tamper/encoding/substitution tests with an ephemeral keypair.
- `services/identity-ledger/sql/0001_bootstrap.sql` — RLS policies scoped `TO a2_identity_ledger_rw` (item_ledger + receipts INSERT/SELECT only); receipts made append-only (BEFORE UPDATE/DELETE triggers + REVOKE); speculative roster/sequence/EXECUTE grants removed; NOLOGIN group role, no password in SQL.
- `.env.example` — two accepted DB shapes + https REST shape (placeholders only).
- `docs/SECRETS_MANIFEST.md` — structural-parsing wording for the DB/REST/ref rows.
- `docs/ISOLATION.md` — RLS-behaviorally-tested invariant.
- `BOOTSTRAP_HANDOFF.md` — two-role provisioning (NOLOGIN group via migration + separately provisioned LOGIN role, password never in SQL), receipts-append-only note.
- `package-lock.json` — regenerated (express 4.22.2, pg 8.22.0).

*(Correction, finding 7: an earlier draft of this list also included `src/server.js` and `Dockerfile`; those were round-2 changes, not round-3, so they are removed here — the round-3 modified set is exactly the 10 above + 1 added.)*

Tree total: **46 files**, no secrets (placeholders only), AP-Stats ids only in guard lists / isolation docs / test inputs.

---

## 4. Reproducible test commands + results

From `C:\Users\rober\Downloads\Projects\algebra2-platform`:

```bash
# 1. Unit/contract tests from a clean install
cd services/identity-ledger
rm -rf node_modules && npm ci          # 83 packages, 0 vulnerabilities
npm test                               # node --test
#   => tests 51 | pass 51 | fail 0

# 2. No-cache Docker image build (run from repo root; COPY paths are root-relative)
cd ../..
docker build --no-cache -f services/identity-ledger/Dockerfile -t a2-identity-ledger:test .
#   => exit 0; npm ci --omit=dev, 0 vulnerabilities; 1 non-fatal JSONArgsRecommended CMD warning

# 3. Config-failure startup (fail-closed)
docker run --rm --name a2-cfgfail-test a2-identity-ledger:test
#   => exit 1; prints: Missing required env var "A2_EXPECTED_SUPABASE_REF" … fails closed

# 4. Smoke kill-switch, both states (covered by step 1's server.test.mjs, injected fake db)
#   => DISABLED: POST /internal/smoke/run -> 404 ; ENABLED: -> 200 with a real Ed25519 receipt

# 5. Behavioral Postgres RLS (disposable named container; self-teardown)
cd services/identity-ledger
bash test/db/rls_behavioral_test.sh
#   => 31/31 assertions PASS: runtime role INSERT/SELECT succeed; UPDATE/DELETE/TRUNCATE denied on
#      both tables; anon+authenticated denied on all three; owner triggers block UPDATE/DELETE;
#      app transaction+receipt round-trip commits. Container a2-rls-behavioral-test + volume
#      a2-rls-behavioral-data auto-removed.

# 6. Cleanup after manual runs
cd ../..
docker rmi a2-identity-ledger:test
rm -rf services/identity-ledger/node_modules node_modules
```

Result summary: **51/51 unit** · no-cache Docker build **PASS** · config-failure **fail-closed (exit 1)** · smoke kill-switch **correct both states** · behavioral RLS **31/31**.

---

## 5. Cleanup confirmation (verified with commands)

- **Temporary containers:** `docker ps -a | grep a2-` → none.
- **Temporary volumes:** `docker volume ls | grep a2-` → none.
- **Test images:** `a2-identity-ledger-r3:test` and the stray `a2-identity-ledger-test:latest` removed → `docker images | grep a2-` → none.
- **node_modules:** removed from both the service dir and the workspace-hoisted repo root → `find … -name node_modules` → 0 dirs. Tree back to 46 files.
- Behavioral test tore down only its explicitly named `a2-rls-behavioral-test` container and `a2-rls-behavioral-data` volume (verified post-run).

---

## 6. AP Stats / Git / cloud untouched (verified)

- **AP Stats:** no writes, no live probes, no deploys against any AP Stats system this round. `school/follow-alongs` remains at its original HEAD `cb8ffd4` (read-only access only). Gate ⛔0 (the production `TEACHER_KEY` exposure) remains **DEFERRED / user-accepted** — not rotated, not tested, not modified; no live probes since you deferred it.
- **Git:** the A2 skeleton has **no `.git`** and is **untracked** in the parent `C:\Users\rober\Downloads\Projects` repo (`?? algebra2-platform/`) — nothing staged, nothing committed, no push. You will initialize it as its own private repo (U8) when ready.
- **Cloud:** no Railway/Supabase/Vercel project, service, database, or variable was created, configured, connected, or deployed. Empty isolated project creation remains your action (BOOTSTRAP_HANDOFF §Final checklist).

---

## 7. Disposition

The three original round-2 blockers are resolved and independently confirmed. What remains is a bounded hardening pass: **1 HIGH** (owner-TRUNCATE append-only gap), **2 MEDIUM** (sign-time JSON-domain validation; behavioral-test name-clobber safety), **3 LOW/INFO** + **2 doc WARN**. No fundamental rework. Awaiting your go for round 4 (fix the seven items → re-run the battery → final bounded `gpt-5.6-sol` reviews). No cloud execution until you authorize it.
