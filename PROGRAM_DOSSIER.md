# Algebra 2 Curriculum Platform — Program Dossier (Discovery Phase)

**Date:** 2026-07-19 · **Author:** Fable (head architect) · **Status:** DISCOVERY — no implementation authorized
**Method:** 8 read-only discovery agents + 3 design-draft agents (11 agents, ~1.9M tokens, 417 tool calls), synthesized by the head architect; adversarial review by Codex GPT-5.6 SOL appended in §13.
**Ground rules honored:** no file mutations in any source repo, no commits, no deployments, no Schoology writes, no schema/grade changes. All four+ source worktrees are dirty with the user's in-flight work and were not touched.
**Amendment revision:** R3 2026-07-19 — user decisions U1–U8 locked (§3 L20–L26, §4.1); amendments 1–8 applied (R2); then user correction (R3): Gate 0 reclassified DEFERRED / user-accepted AP Stats risk, no further live AP Stats probes, A2 Railway Bootstrap inserted as the new first prerequisite (§14.0), secrets-by-purpose inventory added (§5.5). Provisional approval; implementation NOT authorized.

> **DEFERRED — USER-ACCEPTED AP STATS RISK (2026-07-19):** the earlier check showed production roster-server still accepts the public-repo default teacher key. **By explicit user decision this is NOT being remediated** — do not rotate/replace/test `TEACHER_KEY`/`ROSTER_TEACHER_SECRET`, its clients, deployment, or backups, and run **no further live AP Stats probes**. The primary objective is to break as little of live AP Stats as possible. This risk is *contained*, not *cleared* (§14 gate ⛔0): the A2 platform is fully isolated and **never reuses the AP Stats teacher key, database, issuer identity, or service-role credential** (§5.5). It does not block read-only A2 planning or bootstrap.

---

## 1. Executive understanding

We are building a **unified Algebra 2 curriculum-development, delivery, practice, assessment, and evidence platform** by porting the proven AP Statistics platform *as a shell* and replacing its content, taxonomies, and mappings with Algebra 2 equivalents driven by **one canonical course model**.

This is **not** "copy AP Stats and rename it." Three things make it a different program:

1. **One canonical course model** (new — it does not exist today, in either codebase). The AP Stats "model" is a constellation of overlapping files (`SCHEDULE_DEFS` hard-coded in a 21,095-line Desk HTML, `roadmap-data.json`, `lessons-index.json`, `skill-map.json`, crosswalks); the Algebra 2 side has a question-bank registry + Supabase tables with **no Topic/Lesson entity and no external-ID mapping**. The canonical model is a *build target*. It must drive BOTH the student-facing Desk AND the Schoology folder/item projection, and issue the stable IDs consumed by quiz items, Equation Lab skills, TI-84 skills, evidence records, grades, OCR provenance, and DOK calibration.
2. **Evidence ≠ grades, with designation.** The AP Stats platform already separates a per-item evidence ledger (Ed25519-signed receipts, practice/proctored tiers derived server-side) from rollup-time grade computation behind config gates that ship OFF. The port must preserve this discipline and generalize it: only *designated* evidence counts toward official grades.
3. **Content is the long pole, not code.** The engines (Desk shell, quiz renderer, TI-84 trainer, Formula Lab, roster/ledger server) are largely subject-agnostic and data-driven. But 100% of TI-84 procedures, quiz items, Formula Lab workflows/oracles, and skill taxonomies are AP Stats content that must be authored fresh — and the Algebra 2 question bank is gated by a strictly-serial Savvas ingestion pipeline that is itself blocked on two teacher actions (edition confirmation + SE/TE PDFs).

**A critical live-safety constraint shapes everything:** the AP Stats platform is LIVE right now (Summer Foundations Unit 1, voluntary, Jun 16–Aug 25 2026; nightly Supabase backups feed a teacher-private grade monitor that runs 1,000-case parity checks). The migration is therefore designed as *copy-from, never move*, with AP Stats deploy cutover deferred to a school-year boundary.

---

## 2. Current-system map

### 2.1 Repositories (all verified on disk 2026-07-19)

| Local path | Remote | Dirty | Role |
|---|---|---|---|
| `school/follow-alongs` | `robjohncolson/apstats-live-worksheet` (**public**, GH Pages) | ~44 paths | **Live AP Stats platform**: Desk (`ap_stats_roadmap_square_mode.html`, 21,095 lines), `roster-server/` (identity/ledger/grades), `ti84-trainer-v2/`, cartridges in `data/`, Schoology **grade-sync** tooling in `tools/` |
| `Lesson_planning` | `robjohncolson/Lesson_planning` (private) | 7 paths | Algebra 2 authoring: LaTeX packets (`tex/`), questionbank (`registry.jsonl`, 900 rows), Supabase `lesson_planning` schema, Railway pdflatex service, Vercel web console, untracked `grade-monitor/`, **committed copyrighted Savvas PDFs** |
| `school/curriculum_render` | (own repo) | dirty | Quiz engine: 367-item inline bank, PWA/offline outbox, Railway AI-grading proxy, PC26 server-scored secure bank client |
| `tmux-trainer` | (own repo) | ~clean (docs only) | Formula Defense game (EXCLUDED) + **Formula Lab** (the Equation Lab adaptation target) |
| `Agent` | (own repo) | dirty (non-Schoology) | **Schoology materials publisher** (Node Playwright over Edge CDP): post/reconcile/heal/scrape — committed & clean |
| `school/algebra2` | `robjohncolson/algebra2` | 18 paths | Legacy Algebra 2 content + `SCHOOLOGY_POSTING_GUIDE.md` |
| `school/apstats` | `robjohncolson/apstats` | 14 paths | AP Stats curriculum content (stays in place) |
| `school/ti84-transpile` | (own repo) | clean | eZ80 ROM-lifting research (~214MB) — out of scope |

### 2.2 Live deployments

| # | Surface | Source | Notes |
|---|---|---|---|
| D1 | GitHub Pages `robjohncolson.github.io/apstats-live-worksheet/` | follow-alongs root, `master` | Public; the AP Stats Desk |
| D2 | Railway `roster-production-12c1.up.railway.app` | `follow-alongs/roster-server/` | **The** identity/ledger/grade service. bcrypt cost-12, HMAC session tokens, Ed25519 receipt issuer |
| D3 | Supabase project **A** `bzqbhtrurzzavhqbgqrs` | **Verified shared**: roster tables + `item_ledger` + doge (roster-server) · `answers`/`users` (quiz server) · `lesson_planning` schema (this repo) — three schemas, one project | Supabase project **B** `hgvnytaqmuybzbotosyj` = ti84/tmux legacy sync (ROM signed URLs, `lesson_urls`) |
| D4 | Railway `lessonplanning-production.up.railway.app` | `Lesson_planning/railway/` | FastAPI + TeXLive pdflatex build service (X-Passcode/X-User-Name auth). *Missed by one design agent — it is real and hosted* |
| D5 | Vercel `lessonplanning-lyart.vercel.app` | `Lesson_planning/web/` | Teacher collab console (exposes answer keys — not student-safe) |
| D6 | Vercel `lrsl-driller.vercel.app` | separate repo | Drills; stays in place |
| D7 | Nightly grade-monitor | `Lesson_planning/grade-monitor/run.mjs` (untracked) | Consumes `~/grade-backups/latest.json`; Racket Monte-Carlo + 1000-case engine parity. LIVE this summer |
| D8 | Schoology automation | `Agent/scripts/*` (materials) + `follow-alongs/tools/*` (grade-sync, `daily_schoology_sync.ps1`) | Manual/scheduled CLI, drives Edge CDP on 127.0.0.1:9222 against `lynnschools.schoology.com` |

### 2.3 Cross-app contracts (verified, load-bearing)

- **`POST /ledger/record` (FROZEN CONTRACT 2)** — `roster-server/ledger.js:99-201`. Body `{token, source, itemId, response, unit?, topic?, skill?, score?, attempt?=1, grant?}`; `evidence_tier` (practice|proctored) derived **server-side** from `x-proctor-secret`; upsert on `(student_id, source, item_id, attempt)`; returns `{ok, ledgerId, evidenceTier, receipt}`. **`item_ledger` DDL (migrations 0002/0018):** `ledger_id uuid PK, student_id uuid FK, source text CHECK-enum, item_id, unit, topic, skill, response jsonb, score numeric, evidence_tier, attempt int, recorded_at, graded_at, receipt_id, receipt_compact; UNIQUE(student_id, source, item_id, attempt)`. Source enum: `worksheet, frq, curriculum_quiz, pc, blooket, quiz_exception, quiz_review, trainer` — unknown source → 503 ("source not provisioned").
- **Ed25519 signed receipts** — `roster-server/receipts.js`; canonical JSON → `receiptId = sha256(payload)`, compact `payloadB64url.sigB64url`; verified client-side by `receipt-verify.js` against a public issuer registry ("Quiz Server", "The Desk"). Content-addressed CRDT G-Set for the offline mesh.
- **`window.gradebookClient.record()` (FROZEN CONTRACT 3)** — fire-and-forget, never throws, no-op without identity, offline outbox fallback. Used identically by quiz engine, TI-84 trainer, Formula Lab.
- **Roster REST identity** — `/roster/verify|claim|enroll|change-password`, `/roster/section/:period`; session in localStorage (`apstats_roster.v1` / `td-roster.v1`); shared by Desk, quiz, trainers.
- **Grade engine** — all tunables in `grade-config.js` PHASE3_CONFIG. **Current official unit grade (gates OFF): `max(min(B, C=85), P)`** — B = feeder blend (FRQ quality W : quiz correctness Q = 1:2), C = flat 85 completion ceiling (all practice banks at most 85), P = proctored Progress-Check % through a graduated-trust curve — **the only path above 85**. The v3 two-track quarter model (`computeQuarterV3/combineV3`, Work = lessons .30/quizzes .30/posters .30/blooket .10, 0.40/0.70 gates) and the PC track are env-gated and **ship OFF** (`USE_V3_GRADING`, `PC_TRACK_ENABLED`), so production is byte-identical to the pre-PC engine until fall activation. Client≡server parity pinned by tests; a Racket formal model (`formal/grade-model/`) cross-checks ~1000 cases. **Subtle but critical: `evidence_tier` is grade-INERT** — no grade file reads it; the practice-vs-official boundary in the arithmetic is the C=85 cap + the `pc` source, with tier used only for review/restore provenance.
- **`/trainer/state/:deckId`** — cloud save for trainer fleet (256KB cap, optimistic concurrency, deck allowlist). Display/engagement data, **never** grade evidence.
- **Quiz item schema** — `data/curriculum.js` `{id:"U#-L#-Q##", type, prompt, answerKey, attachments{choices,table,chartType+series,image}, solution.parts}`; figures are data-driven Chart.js arrays (only 2 raster images in the whole bank); Supabase `answers` PK = `(username, question_id)`.
- **Lesson_planning registry** — `{lesson}-savvas-q{N}` item IDs assigned serially against a running taken-set; `qb_append.py` SystemExits without a calibration file; LaTeX-canonical output; Supabase tables `items/edges/lessons/lesson_phases/schedule/audit`.
- **Schoology (Agent repo)** — scrape → `state/schoology-tree.json`; pure reconcile lib emitting typed drift issues; `--heal` idempotent apply (post-only-missing, verify-each, root-posting guard); material identity = **title string**; courses `B=7945275782, E=7945275798` (AP Stats).
- **Schoology (follow-alongs tools/)** — Python grade-sync (`schoology_ops.py`, `schoology_sync_lib.py`, migration `0010_schoology_sync.sql`, `test_schoology_reconcile_idempotency.py`); scheduled via `daily_schoology_sync.ps1`. **Note:** one discovery agent reported a false negative here; corrected by direct disk verification.

### 2.4 What a "follow-along" is (so its behavior can be adapted without the format)

A video-paced live worksheet (single HTML) whose fill-in-blank inputs (`data-answer`) and FRQ reflection textareas emit per-item evidence to the server (69 worksheets, 2,373 blanks, 281 FRQ textareas). The **evidence-gathering behavior** is the portable core; the video format is not mandatory for Algebra 2 (locked).

### 2.5 Formula Defense exclusion boundary (clean)

Formula Defense is the tower-defense game in `tmux-trainer` (`index.html`, `tmux-tower-defense.html`). The Desk links to it only as a legacy Apps-menu URL; it has **no APP_REGISTRY entry**. Formula Lab does **not** depend on it — the only shared runtime artifact is read-only `ap-stats-cartridge.js`. Exclusion is trivial and verified.

---

## 3. Locked-decision ledger (user decisions — none may be overridden by agents)

| # | Decision | Status |
|---|---|---|
| L1 | Port the AP Stats Desk substantially as a complete shell | LOCKED |
| L2 | Replace AP Stats content, mappings, labels, taxonomies with Algebra 2 | LOCKED |
| L3 | Preserve Desk behaviors: pacing, schedule, tiles, applications, identity, evidence, grades, completion, teacher visibility | LOCKED |
| L4 | Students are expected to use the Algebra 2 Desk (retract "students rarely visit") | LOCKED |
| L5 | Schoology duplicates the Desk's course structure via a shared canonical model; Schoology is a projection, never a second source of truth | LOCKED |
| L6 | Consolidate relevant apps/services into one monorepo (one repo, possibly many deployments) | LOCKED |
| L7 | Repurpose the quiz engine for Algebra 2 | LOCKED |
| L8 | Build Algebra 2 TI-84 practice | LOCKED |
| L9 | Build an Algebra 2 Formula/Equation Lab | LOCKED |
| L10 | Preserve and generalize identity, evidence, ledger, grading concepts | LOCKED |
| L11 | Do NOT port Formula Defense | LOCKED |
| L12 | Follow-alongs not mandatory as a format; adapt their evidence-gathering behavior into A2 activities | LOCKED |
| L13 | DOK is a first-class organizing axis | LOCKED |
| L14 | OCR/source ingestion becomes a visible, auditable pipeline | LOCKED |
| L15 | Statistics-as-A2-expansion is possible later, not a prerequisite | LOCKED |
| L16 | Schoology publisher uses teacher's authenticated Edge session via CDP; designed as a safe reconciler (preview, stable IDs, idempotency, drift detection, resumability, confirmation before destructive changes) | LOCKED |
| L17 | Evidence separate from official grades; only designated evidence counts | LOCKED |
| L18 | (Pre-existing, this repo) LaTeX canonical for student output; Savvas-only items; serial ingestion; single-DOK3 spine; framework phases | LOCKED |
| L19 | (Frontload, 2026-06-24) Build all 18 front-of-year lessons, 4 full anchors (1-2, 2-3, 2-4, 3-1), waves B1–B5 | LOCKED |
| L20 | (2026-07-19) A2 backend = separate deployment, shared codebase, fresh secrets (U1) | LOCKED |
| L21 | (2026-07-19) Gamification seams retained, economy stubbed initially (U2); web-only initially, no APK/mesh (U3) | LOCKED |
| L22 | (2026-07-19) 4-1 source retained, `in_scope=false` pending dept confirmation (U4); explicit per-topic assessment containers created (U5) | LOCKED |
| L23 | (2026-07-19) Systematic wave-based DOK remediation; unverified DOK may not drive student-facing claims, item selection, or grading (U7) | LOCKED |
| L24 | (2026-07-19) New clean private `algebra2-platform` monorepo with audited imports and no copyrighted-PDF history; never evolve Lesson_planning in place (U8) | LOCKED |
| L25 | (2026-07-19) Universal relational key = opaque `item_uid`; every `item.id` preserved as `legacy_id` alias with provenance; no renumbering, no silent merges | LOCKED |
| L26 | (2026-07-19) Evidence designation is server-derived from a versioned assignment/grading policy; clients submit evidence but never decide official credit | LOCKED |

---

## 4. Open-decision ledger

### 4.1 NEEDS USER — DECIDED 2026-07-19 (locked; recommendations shown for the record)

| # | Question | **DECISION (locked)** |
|---|---|---|
| U1 | Shared vs separate backend for A2 evidence/grades | **Separate deployment, shared codebase, fresh secrets.** New issuer/token/proctor/PW-enc keys minted for A2 (never copy AP Stats secrets); `course_id` dimension still in the schema for possible later consolidation. |
| U2 | Gamification port depth (candy/DOGE/Tetris) | **Retain gamification seams, stub the economy initially.** No Dogecoin node / real economy in v1; UI hooks preserved for later. |
| U3 | Android APK + P2P mesh | **Web-only initially.** Mesh deferred (heavy, security-sensitive, partly untested). |
| U4 | 4-1 status (retired vs revivable) | **Retain source material, set `in_scope=false`** until the department/course sequence confirms. 61 screenshots + 15 skeletons + item_analysis kept, not culled. |
| U5 | Assessment-day containers (`4-6`/`5-6` gap) | **Create explicit `assessment` containers** per topic; teacher confirms cadence (U6). |
| U6 | A2 grade policy (quarters/weights/floors) | **Deferred until the Grok preference interview (§11).** |
| U7 | DOK remediation for the nine shipped lessons | **Systematic wave-based remediation program (WP12), not opportunistic.** Unverified DOK must not drive student-facing claims, item selection, or grading — enforced in the Desk/packet/quiz layers. |
| U8 | Clean private `algebra2-platform` monorepo vs evolve Lesson_planning in place | **New clean private monorepo** with audited imports and no copyrighted-PDF history. Lesson_planning is never evolved-in-place into the platform repo. |

### 4.2 NEEDS RESEARCH (discoverable; assigned to workstreams in §9)

| # | Question | How |
|---|---|---|
| R1 | ~~Supabase topology~~ **RESOLVED**: project A `bzqbhtrurzzavhqbgqrs` hosts roster+ledger+quiz+`lesson_planning` (3 schemas); project B `hgvnytaqmuybzbotosyj` = ti84/legacy sync | Verified via config grep across repos |
| R2 | ~~Ledger DDL~~ **RESOLVED**: `item_ledger` enumerated (§2.3). Residual AP Stats env questions (`USE_V3_GRADING`/`PC_TRACK_ENABLED`, `TEACHER_KEY` override) are **DROPPED from A2 scope** — checking them means touching live AP Stats, now forbidden (§14 ⛔0). A2 sets its own values. | N/A — deferred/accepted |
| R3 | Schoology: does Lynn Schools allow user-scoped API keys ("Access Schoology API" permission)? Would eliminate most DOM risk | Teacher checks My Resources → Apps; low confidence external research says maybe |
| R4 | Algebra 2 Schoology course/section IDs for next year (A/F periods) | Teacher's Schoology once fall courses exist |
| R5 | Are Agent-repo Schoology DOM selectors (probed 2026-03-09) still valid? | Read-only re-probe against live Schoology before any apply path is trusted |
| R6 | Does a second live Vercel deploy of follow-alongs exist (vercel.json present) or is it vestigial? | Teacher's Vercel dashboard |
| R7 | Where does the nightly grade-monitor actually run (scheduler/host)? | Teacher confirms (likely local Task Scheduler) |
| R8 | enVision edition ©2018 vs ©2024 (FRONTLOAD gate) | Teacher checks copyright page — already on their list |

### 4.3 GROK INTERVIEW (preference questions — shuttle prompt in §11)

Desk experience & look for A2 students · what counts toward grades · assessment cadence · TI-84 scope (which A2 procedures) · Equation Lab interaction style (numeric drills vs multi-step scaffolds vs symbolic manipulation) · Schoology folder naming/structure & DOK visibility · which AP Stats behaviors should NOT carry over · calibration/verification appetite.

---

## 5. Target architecture

### 5.1 Monorepo layout (strawman evaluated, amended)

One **private** repo `algebra2-platform`, npm workspaces (match follow-alongs' npm + ESM + vitest):

```
apps/
  desk/              # A2 Desk (ported shell)
  quiz/              # repurposed quiz engine
  equation-lab/      # Formula Lab fork, A2 subject layer
  ti84-trainer/      # engine reused; A2 cartridges net-new
  web-console/       # teacher collab console (from Lesson_planning/web)
  apstats-desk/      # OPTIONAL reference shell (may stay in archived repo)
services/
  identity-ledger/   # roster-server, generalized (course-parameterized) — deployed per-course (U1)
  build-service/     # Railway pdflatex/TeXLive service (KEPT — it is real and hosted; one design draft
                     # wrongly deleted it by conflating it with follow-alongs' build.mjs)
tools/
  schoology-publisher/  # CDP CLI (triggered, NOT hosted) — merged from Agent repo + follow-alongs/tools
  ocr-ingest/           # the visible, auditable ingestion pipeline (qb_append + provenance)
packages/
  course-model/      # ★ the linchpin: canonical schema + resolvers; Desk & Schoology are projections
  evidence-client/   # gradebook-client + /ledger/record contract
  roster-client/
  grading-contracts/
  shared-ui/         # deferred — start minimal
content/algebra2/
  source-pdfs/       # GITIGNORED (copyright) — private bucket + teacher disk only
  extracted-text/  question-bank/  calibration/  visuals/  course-tree/  schedules/
```

Amendments to the strawman: `schoology-publisher` is a **tool**, not a service (it is a triggered CDP CLI); `build-service` **stays** (Railway pdflatex is live); `ocr-ingest` added as a first-class tool per L14; `web-console` added.

### 5.2 Canonical course model (adopting design draft with architect rulings)

**Central verified fact:** three hierarchy levels are conflated today — content-lesson (`4-3`, exists only as `item.lesson` string), teaching-instance (`L43_P1[_obs]`, the `lessons` table PK), and phase (`lesson_phases`). `L43 ↔ 4-3` is naming convention, never a foreign key. The model makes all three first-class.

**Entities:** `course` (subject, school_year, topic_vocab) → `unit` (Savvas Topic) → `lesson` (Savvas lesson, code `4-3`, readiness, in_scope) → `lesson_instance` (today's `lessons` table + FK to lesson, period_num, variant, cadence) → `phase` (ordered, minutes, adult_role) → `item` (registry rows, IDs preserved verbatim). Plus: `skill` (unifying skill_tokens / standards / TI-84 procedures / Equation Lab formulas / AP practices, with `skill_alias` carrying confidence+provenance), `asset` (sha-identified binaries replacing filename-convention + boolean flags), `source_ref` (OCR provenance: source PDF asset + page + screenshot + ingest tool/date + verified_by — the L14 auditable pipeline), `assessment` (containers with `is_official`; shells become items with `assessment_id`), `schedule_entry` (as-is), `external_mapping` (entity ↔ system ↔ external_id ↔ checksum — the ONLY place Schoology IDs live), and `evidence` (in the ledger service, gaining a `course_id` dimension + `designated` flag).

**Stable-ID rule:** never renumber, never silently merge. The opaque `item_uid` is the universal join atom; `item.id` (`4-3-savvas-q36`) becomes a provenance-tagged `legacy_id` alias (see the canonical identity model below). New tables FK to `item_uid`; `external_mapping` absorbs cross-system IDs (CED crosswalk, ti84-lesson-map, Schoology).

**DOK first-class (L13):** add `dok_status`, `dok_provenance (auto-structure|savvas-declared|item-analysis|hand-verified)`, `dok_confidence`, `dok_candidates`, `calibration_ref` — generalizing the AP skill-map's confidence/provenance pattern. **Status vocabulary (amended per Codex review C):** `known-auto` (the 421 rows carrying the literal auto-ingest marker) | `unreviewed` (the other 437 later-lesson rows — NOT thereby verified) | `calibrated` (3-5: real anchors exist, but no `reviewed_by/reviewed_at` evidence) | `verified` (reserved for future explicit human review with reviewer+date). Nothing in the repo today reaches `verified`.

**Canonical identity model (RULED, amended per user decision + Codex review B):** the universal relational key is an **opaque `item_uid`** (server-minted, stable, meaningless — e.g. `iu_<ulid>`), NOT the human-readable `item.id`. Every current `item.id` is preserved as a **`legacy_id` alias with provenance** (`{legacy_id, source_scheme, first_seen_commit, minted_at}`) in an `item_alias` table; a single `item_uid` may carry multiple legacy aliases. **No renumbering, no silent merging of distinct items.** The registry's **85 duplicate `id` values (815 unique of 900)** (known-deferred: CONTINUATION_PROMPT "Topic 5 `-2`-suffixed rows, seed last-writer-wins) are therefore *distinct items that happen to share a legacy string* — each gets its own `item_uid`; the shared string becomes an ambiguous alias flagged for human disambiguation, never an automatic merge. All tex `\bankitem`, `edges`, receipts, and evidence references resolve through the alias table. This is a hard precondition of WP1 and is distinct from the 176 *source-coordinate collisions* (§6). See WP11 for the duplicate-ID remediation package.

**Storage ruling (HYBRID — adopted):** Supabase `lesson_planning` schema is canonical for the relational model + designation authority (evolve via additive migrations 007–014); **git stays canonical for authored source** (tex/yaml/cartridges), SHA-reconciled into Supabase (the existing If-Match-Sha protocol); **evidence stays in the roster/ledger service** keyed by model IDs, surfaced to the Desk via a rollup view. Rejected: all-in-git (loses the live collab console) and all-in-Supabase (violates LaTeX-canonical; bloats content DB with ledger volume).

**Projections:**
- *Desk:* `desk_tiles` view (instance, lesson_code, cadence, DOK badge, assets, completion); pacing from `phase` rows; completion from evidence rollup by skill; deep links `#unit/#lesson/#instance/#item/#skill`.
- *Schoology:* deterministic tree map (course→Course, unit→Folder, lesson→Folder, instance artifact→ungraded Page, official assessment→graded item). Idempotent sync keyed by stored `external_mapping.external_id` + content checksum; **model always wins; never DELETE on model change** (orphans reported); only `is_designated` items in `is_official` assessments create graded columns (L17).

### 5.3 Identity / evidence / grade contract

Preserved behaviors (from the live system, verified): bcrypt cost-12 + generated usernames + 30-day HMAC tokens + teacher view-as; server-derived practice/proctored tier; Ed25519 receipts binding grading fields to the signature; rollup-time grade computation (never stored grades); two-track model with floors/anti-gaming ceilings and null-tolerance for "nothing due yet"; **ship-inert-then-activate** discipline (grade gates default OFF); offline-first with client≡server engine parity; no answer keys or policy values in public client code.

**Designation is server-derived (RULED, amendment 7).** Whether a piece of evidence counts toward an official grade is decided **server-side** from a **versioned assignment/grading policy** (`policy_version` stamped on the decision), NEVER by the client. Clients may *submit* evidence (`/ledger/record`) but may not assert that it counts — the server resolves `(course, assignment, source, item, tier)` against the active policy and stamps a point-in-time `designation` + `policy_version` on the row/receipt. This closes the gap where today's `evidence_tier` is client-adjacent and grade-inert: the A2 model gives designation defined arithmetic driven by policy, and a re-tuned policy re-resolves history at rollup without rewriting evidence. Receipt v2 binds `course`, `policy_version`, `designation`, `tier`, and `score-scale` so a harvested receipt cannot be re-stapled to claim official credit.

Generalizations required: `course_id` on evidence rows and localStorage namespaces (`a2_roster.v1`, `A2TI84-` item prefixes — today three different session keys exist: `apstats_roster.v1`, `td-roster.v1`, the Desk's own; unify or define an explicit handoff); `designated` flag per L17 — **and it must be given defined arithmetic**, because today's `evidence_tier` is grade-inert and the real boundary is the C-cap + `pc` source (i.e., "designated" should map to a grade-feeder role in config, not just a stored flag); grade config course-parameterized (PHASE3_CONFIG quarters/anchors are AP-exam-specific); **all secrets minted fresh for A2** (never copy issuer/token/proctor secrets; `TEACHER_KEY` default `<redacted — see AP Stats deployment env>` is a public-repo literal and must be replaced/env-overridden).

**Live-safety freeze list (verified: the nightly grade-monitor dynamically imports the production engine from `../school/follow-alongs/roster-server/` and FAILS CLOSED on receipt-chain verification + 1000/1000 Racket parity).** Do not change without coordinated updates: `/ledger/record` request/response shape; `item_ledger` columns; Ed25519 receipt payload field names (`v,t,sid,u,src,i,a,e,ah,ts,n,sc,g`); engine module signatures (`grade.js`, `lesson-grade.js`, `grade-config.js`, `snapshot-verify.js`, `scoring.js`); the nightly snapshot schema; PHASE3_CONFIG semantics + `crosscheck.rkt` cases; the issuer trust set (append-only rotation). **Repo moves also break the monitor's sibling-path import** (`config.paths.followAlongs` default `../school/follow-alongs/roster-server/`) — Tranche 5 must update the monitor config in the same step.

Known weaknesses to fix in the A2 deployment (not retrofitted into live AP Stats — the AP Stats deployment is preserved exactly per user decision): curriculum_render's `/api/submit-answer` accepts any username unauthenticated (peer-answer spoofable — A2 quiz writes must bind to authenticated `sid`); reversible AES-256-GCM password cipher exists for teacher recovery (decide whether A2 keeps it); non-timing-safe token compare in curriculum_render `token.js`; `.env.example` files omit several required secrets; the AP Stats public-default teacher key (deferred/accepted, §14 ⛔0) — A2 does not inherit it (§5.5).

### 5.5 Secrets by purpose (inventory before copying — never treat these as interchangeable "keys")

The A2 deployment reuses the AP Stats **codebase**, not its **secrets or data destinations**. Before copying any value, classify it by purpose. Human-facing access values MAY be temporarily reused for teacher continuity — but always copied into an **independent A2 variable**, never a shared reference, so later A2 rotation cannot touch AP Stats. Cryptographic material, database destinations, service-role credentials, and issuer identities are **freshly minted for A2** and never point at the live AP Stats database.

| Env / secret | Purpose class | A2 handling |
|---|---|---|
| Supabase project URL (`bzqbhtrurzzavhqbgqrs`) | **Database destination** | A2 uses its OWN new Supabase project (§14.0 B1). **Never** point A2 at project A. |
| Supabase service-role key | **DB write auth (RLS bypass)** | Fresh, from the A2 project only. |
| Supabase anon key | **Public client read key** | Fresh, from the A2 project only. |
| `ROSTER_TOKEN_SECRET` | **Session-token HMAC signing** | Fresh-mint — independent identity domain. |
| `RECEIPT_ISSUER_PRIVATE_KEY` | **Issuer identity / receipt provenance** | Fresh-mint a NEW A2 issuer ("The A2 Desk"); the A2 verifier trusts the A2 issuer only. Not interchangeable with AP Stats's issuer. |
| `ROSTER_PW_ENC_KEY` | **AES-256-GCM password-cipher key** | Fresh-mint. |
| `x-proctor-secret` | **Proctored-evidence-tier gate** | Fresh-mint. |
| `TEACHER_KEY` / teacher access | **Human-facing teacher passphrase** | Copy into an independent `A2_TEACHER_KEY` variable. ⚠ The current AP Stats value is the public-repo default — for A2, set a fresh teacher-chosen value in that independent variable rather than copying the leaked default (still human-facing, still the teacher's choice, but not public). |
| `REBUILD_PASSCODE` (pdflatex build, `LEHS`) | **Human-facing build passcode** | If the A2 build service reuses it, copy the value into an independent A2 variable. |

Principle: an A2 rotation must never modify AP Stats, and A2 must never read the live AP Stats database merely to reuse configuration.

### 5.4 Schoology publisher (safe reconciler; merges two proven prior-art stacks)

Prior art (both verified on disk): **(a)** `Agent/scripts/*` — Node Playwright over Edge CDP (127.0.0.1:9222, dedicated `.edge-debug-profile`), scrape→plan→preview/apply split, `--heal` idempotent apply, typed drift issues, root-posting guard, title-string identity, live target `lynnschools.schoology.com` (spec's `lps.schoology.com` is stale); **(b)** `follow-alongs/tools/*` — Python grade-sync with pure idempotent planner, property-tested reconcile, Supabase sync-state migration 0010, scheduled daily task.

Adopted design: three-tier **Transport** interface — REST/OAuth *if verified available* (R3) > **observed-XHR replay** through the authenticated session (drift-resilient; the assignment-create endpoint shape is already captured) > versioned page-object DOM fallback with startup selector health-check. **Three-hash model** (desired/published/observed) in Supabase mapping + **write-ahead journal** (journal row precedes every write; crash → roll-forward resume). Plan approval freezes a `plan_hash` with TTL; apply refuses on mismatch. Destructive ops: **archive-not-delete default**; delete/move are second-gate with named confirmation; never delete anything carrying grades/submissions. The publisher **never touches grades** (grade-sync is a separate, existing path) — enforced in code by not importing grade-write functions. Failure-mode table covers DOM drift, session expiry, CDP disconnect, duplicate publication, partial folder creation, maintenance windows.

Net-new critical-path unknown: Schoology **folder create/move endpoints** are not yet reverse-engineered (the existing tools do flat gradebook columns and materials links); one manual folder-create session with Network capture resolves it (P0 of the publisher workstream). Selector re-probe (R5) is a precondition regardless.

Constraint (verified): CrowdStrike Falcon + school firewall block remote-driving the school machine; the publisher runs **locally on the machine holding the Edge session**.

**Amendments after adversarial review (Codex C, accepted):** (a) the journal uses four states — `prepared / sent / confirmed / ambiguous` — with a client-generated idempotency key per action; a crash between remote commit and local confirmation leaves `ambiguous`, which is resolved by **re-observation** (find-by-marker), never by blind roll-forward (prior art logged three duplicate columns from exactly this gap, `schoology_ops.py:297-300,441-452`); (b) plan-approval TTL is supplemented with a **per-course lease** (no concurrent publishers) and single-use approval bound to actor+course+desired-and-observed snapshots+transport version, plus a pre-write re-observe/CAS check; (c) one folder-create XHR capture is necessary but not sufficient — edit/move/archive/upload/graded-item verbs each need capture before their apply paths are trusted. **Amendment (Codex A, accepted): the materials publisher and the existing grade-sync remain two separate tools** — `tools/schoology-publisher` (materials/folders only) and the untouched grade-sync path; "merged prior art" means shared transport/DOM libraries only, never shared write surfaces.

---

## 6. OCR/DOK inventory (computed from disk, not estimated)

**Registry: 900 rows** (was 949 on 2026-04-30; −49 from the L41 retirement cull — both figures verified via `git show`). 10 lesson codes populated: 3-5 (42) + nine Topic-4/5/6 lessons (858). Calibration files: 11. Screenshots: 114 real (53 × `3-5_*`, 61 × `4-1_*`, **zero** for the nine built lessons). All ten baseline claims recomputed: **all confirmed** (four exactly; methods identified), one **adjusted** (registry total 949→900).

Aggregate quality findings on the nine built lessons (packets already shipped from this data):
- **421/858 (49%) provisional DOK** — the literal auto-ingest default string; never reconciled because `dok2_anchors`/`dok3_anchors` are empty in all nine calibration files. Only 3-5 has real hand-authored anchors.
- **339/858 (40%) lack answer evidence** in the registry (ground truth requires re-opening the TE PDF/tex — the `source_ref` entity addresses this).
- **137 visual items, 100% missing assets** (no clean asset, no screenshot — worse than the "~137 lack" phrasing implied).
- **176 source-coordinate collisions** (125 groups; 5-1 and 5-4 worst at 31–36% of rows) — rows sharing an identical `lesson`+`source` citation. **Amended per Codex C: these are NOT all duplicates** — every group has distinct prompts (zero exact lesson+source+prompt duplicates; some are legitimate multi-entry Concept Boxes). Treat as a review queue, not a delete list. **Separately: 85 literal duplicate-ID rows exist (815 unique IDs of 900)** — the actual dedup blocker for the ID-atom design (§5.2).
- **Topic tags 0/858** (total emptiness, not "broadly empty").
- `item_analysis` literal `{}` for 4-4, 5-4, 6-5.

Matrix (SE/TE = PDF+tex present · Reg = registry rows · Ans = with answer evidence · DOK prov = provisional rows · Dup = duplicate-source excess · Anchors = calibration anchor quality):

| Lesson | SE/TE | Reg | Ans | DOK prov | Dup | Anchors | Item-analysis | Screenshots | Readiness |
|---|---|---|---|---|---|---|---|---|---|
| 1-1 … 1-7 | none | 0 | — | — | — | none | no | 0 | **blocked** (FRONTLOAD B1–B5) |
| 2-1 … 2-7 | none | 0 | — | — | — | none | no | 0 | **blocked** |
| 3-1 … 3-4 | none | 0 | — | — | — | none | no | 0 | **blocked** |
| 3-5 | PDF only | 42 | 42 | 0 | 0 | **real** (only one) | no (older schema) | 53 | **calibrated, not human-verified** |
| 3-6 | — | 0 | — | — | — | — | — | 0 | absent (dept-deprecated) |
| 4-1 | — | 0 | — | — | — | placeholder | yes | 61 | absent (retired 5/13; residue: 15 skeletons) |
| 4-2 | — | 0 | — | — | — | none | no | 0 | absent (dept-skipped) |
| 4-3 | PDF+tex | 74 | 57 | 40 | 7 | placeholder | yes | 0 | partial |
| 4-4 | PDF+tex | 91 | 50 | 55 | 16 | placeholder | **{}** | 0 | partial |
| 4-5 | PDF+tex | 81 | 60 | 48 | 8 | placeholder | yes | 0 | partial |
| 4-6 | — | 0 | — | — | — | — | — | 0 | absent (topic-level shells only: `topic4-lehs-q*`) |
| 5-1 | PDF+tex | 132 | 68 | 50 | **41** | placeholder | yes | 0 | partial |
| 5-2, 5-3 | — | 0 | — | — | — | none | no | 0 | absent (dept-skipped) |
| 5-4 | PDF+tex | 132 | 67 | **57** | **47** | placeholder | **{}** | 0 | partial |
| 5-5 | PDF+tex | 96 | 48 | 47 | 33 | placeholder | yes | 0 | partial |
| 5-6 | — | 0 | — | — | — | — | — | 0 | absent (shells only) |
| 6-1, 6-2 | — | 0 | — | — | — | none | no | 0 | absent (dept-skipped) |
| 6-3 | PDF+tex | 100 | 64 | 42 | 7 | placeholder | yes | 0 | partial |
| 6-4 | PDF+tex | 69 | 38 | 36 | 9 | placeholder | yes | 0 | partial (worst answer rate 55%-missing; 1 TRANSCRIPTION-UNCERTAIN item) |
| 6-5 | PDF+tex | 83 | 67 | 46 | 8 | placeholder | **{}** | 0 | partial |

`text_review` and `dok_verification`: **UNKNOWN/no for every lesson** — no positive evidence of systematic human verification exists anywhere in-repo. **Beyond Topic 6:** no in-repo evidence of any Topic 7+ content or intent (`A2LessonSelection.txt` ends at 6-5; repo-wide grep for topic/unit 7 = zero hits).

**Readiness verdict: "text extracted" ≠ "DOK-ready."** Only 3-5 is genuinely DOK-calibrated. The nine "parsed" lessons are usable-for-drafting but carry unreviewed DOK on half their rows, missing answers on 40%, no visual assets, and undeduped variants. The 18 front-of-year lessons are 0% and hard-blocked on teacher actions (R8 + PDFs).

---

## 7. Migration strategy (staged; live platform never breaks)

Adopted from the monorepo design draft with corrections (§5.1). Guiding principle: **the monorepo is built off to the side; AP Stats is copied-from and frozen; only the Algebra 2 Vercel console cuts over early.**

- **Tranche 0 — Freeze & baseline (USER ACTIONS, hard precondition; REWRITTEN per Codex review A):** ⚠ **Do NOT "commit and push master"** — follow-alongs' GitHub Pages workflow deploys on every push to master (uploads `path: '.'`), and Railway auto-deploys roster-server; a naive baseline push would republish the live site mid-summer with 40+ unreviewed changes. Instead, per repo: (1) build an **inclusion manifest** (tracked-modified + untracked worth keeping; explicitly exclude node_modules, PII paths, ignored files); (2) commit reviewed work to a **non-deploy branch** (`baseline/pre-monorepo-2026-07`); (3) create **annotated tags on the currently-deployed SHAs** and `git bundle` archives as offline backups; (4) **pin or disable auto-deploy** (Pages workflow guard / Railway "wait for CI") for the duration of any later cutover work; (5) master is never force-updated. Commit `grade-monitor/` **code** to the baseline branch (README/run.mjs/example config/rkt), keeping `config.private.json` + `reports/` gitignored; secrets/PII go to a separate **encrypted** backup, never git. Data baseline: `admin-snapshot.js` is **not a full backup** (it omits password hashes, keys, wallets, trainer state, submissions; per-student read failures degrade to empty arrays) — take a **native full-schema Supabase export** with table counts/checksums + Storage export + issuer-key escrow, and **rehearse a restore into an isolated project** before trusting it as the rollback anchor.
- **Tranche 1 — Empty private monorepo + packages:** extract `evidence-client`, `roster-client`, `grading-contracts`, first `course-model` schema as **copies** (source of truth unchanged). CI only, no deploys.
- **Tranche 2 — Engine in via subtree** (`follow-alongs` history preserved — its FROZEN-CONTRACT/test history is load-bearing for auditing the port). D1/D2 still deploy from the old repo.
- **Tranche 3 — Build A2 apps; cut over ONLY the A2 Vercel console (D5):** port Desk shell with namespace renames; fresh-import Lesson_planning content (**severs the copyrighted-PDF blob history**); PDFs gitignored + private bucket. **Publish guard strengthened per Codex A:** public deploys ship only an **allowlisted `dist-public/` artifact** (deny-by-default), with MIME/path/content-class checks plus secret/PII/license scanning — a filename grep alone misses renamed PDFs, ~94 DOCX, ~25 PPTX, 159 images, extracted text, and `roster-server/data/answer-key.json` (Pages currently uploads the entire repo). Subtree imports come from a **filtered, secret-scanned mirror** with the import-base SHA recorded, re-synced until final freeze + parity diff. Rollback = flip the Vercel Git source back (one setting).
- **Tranche 4 — Generalize identity-ledger + promote course-model to source of truth.** Railway roster cutover explicitly deferred; internals refactored and mirrored only.
- **Tranche 5 — School-year boundary only:** cut D1/D2 over; archive old repos (private forever — PDF blobs live in Lesson_planning history).

Git-history strategy: **subtree-merge follow-alongs** (engine history preserved) / **fresh-import Lesson_planning + algebra2** (severs PDF blobs, discards mojibake churn) / **copy-from apstats, Agent scripts** / **ti84-transpile does not move**. What does NOT move: Formula Defense, `legacy/`, doge-wallet economy (pending U2), Blooket (deprecated), lrsl-driller (stays deployed), AP Stats curriculum content.

---

## 8. Workstream dependency graph

```
Teacher actions (edition + SE/TE PDFs) ──► FRONTLOAD ingestion (serial) ──► A2 content packs
Teacher action (commit dirty trees) ─────► Tranche 1+ (monorepo mechanics)
R1/R2 (Supabase topology + ledger DDL) ──► evidence contract finalization ──► identity-ledger generalization
Course-model migration design + CLONE-ONLY execution (live DDL behind gate ⛔1) ──► Desk tiles view ──► Desk shell port
                                        └─► external_mapping ──► Schoology publisher plan side
R5 selector re-probe + P0 folder-XHR capture ──► publisher apply path
Grok interview (preferences) ──► grade policy config, Desk UX, Equation Lab style, Schoology naming
Quiz/TI-84/Equation Lab engine work: parallel-safe after Tranche 1 packages exist; content packs blocked by ingestion
```

Parallel-safe now (no teacher input needed): course-model **migration design and clone-only execution** (⚠ no DDL on shared Supabase project A without gate ⛔1 + explicit approval); the WP9 collision-review queue design and WP11 duplicate-ID remediation design; publisher plan-side modeling; Codex-reviewed specs.
Blocked on teacher: FRONTLOAD content (R8 + PDFs); Schoology course IDs (R4); API permission check (R3); dirty-tree commits (Tranche 0); all preference questions (§11).

---

## 9. Delegation plan (work packages; discovery-phase → build-phase)

Org: **Fable** = architecture/acceptance · **Opus** = workstream manager/spec author · **Sonnet** = implementation · **Codex GPT-5.6 SOL** = adversarial reviewer (read-only, no commits) · **Grok** = user-preference interviews.

| WP | Scope | Mgr | Impl | Reviewer | Owned paths (build phase) | Acceptance criteria | Non-goals |
|---|---|---|---|---|---|---|---|
| WP1 | Course-model migrations 007–014 + backfills + `item_dok_signals` view | Opus | Sonnet | Codex | `supabase/migrations/00[7-9]*,01[0-4]*`, `packages/course-model/` | Additive-only; every existing tool/seed/console works unchanged; DOK view reproduces 421/verified-only-3-5; unmatched-backfill review list empty or dispositioned | No renumbering; no writes to live tables outside migrations |
| WP2 | Ledger DDL enumeration + evidence contract finalization (R2) then identity-ledger generalization spec | Opus | Sonnet (read-only first) | Codex | `roster-server/` (read), later `services/identity-ledger/` | Documented `item_ledger` DDL; course_id + designated added additively; grade-invariance tests still pass byte-identical | Never flip grade gates; never touch live secrets |
| WP3 | Desk shell port (A2 Desk) | Opus | Sonnet | Codex | `apps/desk/` | Renders A2 course tree from model views; namespaces renamed (`a2_roster.v1`, `A2TI84-`); zero references to AP Stats content/URLs; evidence writes no-op without identity | No gamification economy (pending U2); no mesh (U3) |
| WP4 | Quiz engine A2 content pack + DOK fields | Opus | Sonnet | Codex | `apps/quiz/`, `content/algebra2/question-bank/` | Same item schema + added `dok/bankId`; ID scheme decision implemented consistently (parser+crosswalk+frameworks together); function-graph figure path decided and working | No changes to AP Stats bank |
| WP5 | Equation Lab (Formula Lab fork, A2 subject layer) | Opus | Sonnet | Codex | `apps/equation-lab/` | Engine reused (templates/scaffolding/retention/roster/ledger); A2 oracle scoped per Grok answer (numeric-first vs CAS-lite); renderer/validator maps extracted to a subject module | Formula Defense untouched |
| WP6 | TI-84 A2 cartridges | Opus | Sonnet | Codex | `apps/ti84-trainer/`, `content/algebra2/course-tree/` | CEmu backend reused; A2 procedures data-authored (graphing/table/intersect per Grok scope); evidence `A2TI84-*` | No native-engine A2 screens in v1 (CEmu covers all skills) |
| WP7 | Schoology publisher (A2) | Opus | Sonnet | **Codex (mandatory, BLOCKED gate)** | `tools/schoology-publisher/` | P0 folder-XHR captured; selector re-probe green; plan/preview/apply with plan_hash TTL; journal resume proven; archive-not-delete; zero grade-write imports; dry-run against real A2 course produces sane plan **before any apply** | Never touches grades/submissions; no apply without fresh approved preview |
| WP8 | OCR ingest pipeline (`tools/ocr-ingest`) + source_ref provenance + FRONTLOAD execution when unblocked | Opus | Sonnet (serial ingestion stays serial) | Codex | `tools/ocr-ingest/`, `content/algebra2/{question-bank,calibration,visuals}` | Every ingest writes source_ref rows; calibration-first enforced; mojibake pass run; per-wave C/I/P tracker updated | Never parallelize appends |
| WP9 | **Source-coordinate collision review queue** (the 176) + visual-asset backfill plan | Opus | Sonnet | Codex | `questionbank/` (read + report only) | Produce a *reviewed disposition queue*, one row per collision group, each labeled keep-both (legit multi-entry, e.g. Concept Box) / merge-candidate / needs-source-check — **NO automatic deletion or merge**; teacher/architect signs off each merge before it happens; visual-asset gaps enumerated with source_ref targets | Never auto-dedupe; never edit content; the 176 are a queue, not a delete list |
| WP11 | **Literal duplicate-ID remediation** (the 85 duplicate `id` values / 815 unique) | Opus | Sonnet | Codex | `questionbank/`, `packages/course-model/` (alias table) | Each duplicate string resolved to distinct `item_uid`s with `legacy_id` aliases + provenance; ambiguous aliases flagged for human disambiguation; tex/edge/evidence references rewired through the alias table; zero silent merges; before/after count reconciles to 900 items / 900 uids | No renumbering; no merging distinct items; no content edits |
| WP12 | **Systematic DOK remediation program** (wave-based, per U7) | Opus | Sonnet (fast review UI) + teacher | Codex | `questionbank/calibration/`, `registry.jsonl` (DOK fields) | Per wave: reconcile every item's DOK against Savvas TE item-analysis + anchors; set `dok_status`/`reviewed_by`/`reviewed_at`; **gate: unverified DOK may not drive student-facing claims, item selection, or grading** (enforced in the Desk/packet/quiz layers, not just labeled); progress tracked per wave | Not opportunistic; not a one-pass batch; never present provisional DOK as authoritative |
| WP10 | Monorepo mechanics (Tranches 1–3) — **new clean private `algebra2-platform` repo (U8)** with audited imports, no copyrighted-PDF history | Opus | Sonnet | Codex | new repo | Each tranche one-flip rollback; allowlisted `dist-public/` publish guard proven by test; import manifests hashed + secret-scanned; AP Stats deploys untouched | No Tranche 5 without explicit user approval; never evolve Lesson_planning in place |

Reporting rule for every WP: findings carry evidence path:line, confidence, fact/inference/recommendation; disagreements surfaced, not buried.

---

## 10. Risk register

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| K1 | **Dirty worktrees** (~83 paths across 6 repos) silently dropped by subtree/import, or clobbered by agents | HIGH | Tranche 0 user commit+tag precondition; agents read-only until then |
| K2 | **Live AP Stats platform corruption** (summer session + nightly monitor running) | CRITICAL | Copy-from-never-move; separate A2 backend (U1 rec); AP cutover only at year boundary; roster data snapshot first |
| K3 | **Grade integrity**: naive port flips `USE_V3_GRADING`/`PC_TRACK_ENABLED` or copies fall-activated config → un-taken assessments cap quarters | CRITICAL | Preserve ship-inert discipline; grade-invariance tests must pass byte-identical in any port; Codex gate on WP2/WP3 |
| K4 | **Secrets**: issuer private key, token secret, proctor/teacher secrets, ROM signed-URL token committed in `rom-config.js`; `TEACHER_KEY` default is public | HIGH | **Mint all-new independent secrets for A2 (§5.5); never copy AP Stats `.env` or point A2 at AP Stats stores.** The audited monorepo import (U8) secret-scans and scrubs committed tokens rather than carrying them. Do **not** rotate secrets on the live AP Stats/ti84 deployments (preserve exactly, §14 ⛔0) — the exposure is contained by A2 isolation, not by mutating live AP Stats |
| K5 | **Student PII** in curriculum_render (`csv/`, `fix_justin/`, `student2username.csv`) and grade backups (`~/grade-backups/`) | HIGH | Fresh-import excludes; PII paths never enter monorepo; grade-monitor stays aggregate-only + gitignored config |
| K6 | **Copyright**: Savvas PDFs committed in Lesson_planning history; follow-alongs is public | HIGH | Private monorepo; fresh-import severs blobs; source-pdfs gitignored; CI publish guard; archived repo stays private forever |
| K7 | **OCR/DOK overstatement**: "9 lessons parsed" reads as ready; actually 49% provisional DOK, 40% missing answers, 0 visual assets | MED | §6 matrix is the ground truth; `dok_status` surfaces provisional in every UI; packets trace to source_ref |
| K8 | **Incorrect DOK assignments** propagate into packets/assessments | MED | Anchor backfill priority on assessment-feeding lessons (U7); item_dok_signals view; single-DOK3-spine remains human-enforced |
| K9 | **Schoology DOM drift** (selectors 4+ months stale) / **CDP interruption mid-publish** | HIGH | R5 re-probe precondition; XHR-replay transport preferred; write-ahead journal + roll-forward; archive-not-delete |
| K10 | **Duplicate publication** (title-string identity is fragile) | MED | external_mapping stored IDs replace title-matching as primary identity; title convention designed before first apply; pre-flight existence checks |
| K11 | **Deployment coupling**: Supabase project topology unverified (R1); two Railway services conflatable | MED | R1 resolves before Tranche 4; deployment inventory (§2.2) is the checklist |
| K12 | **Loss of working AP Stats behavior** in the port (Desk is a 21k-line monolith; content baked into JS) | HIGH | Subtree-preserved history; behaviors_to_preserve list (§5.3) is the acceptance checklist; parity tests ported with the engine |
| K13 | **Visual asset provenance**: 137 visual items with no linked asset; screenshots absent for all nine lessons | MED | asset + source_ref entities; backfill plan in WP9; never fabricate visuals |
| K14 | **Serial-ingestion throughput** (~210–260 items) misplanned as parallelizable | MED | WP8 enforces serial; waves B1–B5 already sequenced |
| K15 | Registry↔DB drift (900 on disk vs ~1091 seeded; no export-back script) | MED | WP1 decides ownership per-field; export.py written before any DB-side edits count as truth |
| K16 | Cross-course evidence contamination on shared origins (`apstats_roster.v1`, `TI84-` prefixes) | MED | course_id dimension + renamed namespaces (§5.3) |
| K17 | Six discovery agents' structured outputs failed on a harness limit (recovered from transcripts; identity-evidence re-run completed) — synthesis could have inherited gaps | LOW | Full-text recovery verified; one false negative (follow-alongs Schoology tooling) caught and corrected by disk check; Codex review as backstop |
| K18 | **Grade-monitor sibling-path coupling**: `run.mjs` imports the production grade engine from `../school/follow-alongs/roster-server/` and fails closed on parity — any repo move/rename breaks nightly monitoring | HIGH | Freeze list (§5.3); Tranche 5 updates monitor `config.paths.followAlongs` atomically with any move; never move follow-alongs mid-summer |
| K19 | **Public-repo default teacher key** (`teacher-auth.js:25`): confirmed accepted on prod (K22) | HIGH → **DEFERRED (user-accepted)** | Not remediated on live AP Stats by user decision (§14 ⛔0); A2 uses a fresh independent key from day one (§5.5); no further probes |
| K20 | **Quiz-server identity spoofing**: `/api/submit-answer` upserts for any asserted username without auth; `answer` receipts can attest unauthenticated names | MED | A2 quiz path binds writes to authenticated `sid`; retire or auth-gate the peer-answer lane in the port |
| K21 | Reversible password cipher (`password_cipher`, AES-256-GCM) — teacher-recoverable plaintext passwords | MED | Deliberate design; decide per-course whether A2 keeps it; key isolation per U1 (fresh `ROSTER_PW_ENC_KEY`) |
| **K22** | Confirmed 2026-07-19: production `TEACHER_KEY` NOT overridden — default public literal grants `/roster/list` (decrypted passwords + PII), grades, teacher elevation | CRITICAL, but **DEFERRED — USER-ACCEPTED** | Per user decision the live AP Stats deployment is preserved exactly and **not** rotated/tested; risk contained by A2 isolation (A2 never reuses this key/DB/issuer, §5.5); no further live probes. Revisit only if the user later chooses to remediate AP Stats |

---

## 11. Grok shuttle prompt (user-preference interview)

*Copy everything between the fences to Grok; bring its report back.*

```
You are interviewing a high-school math teacher (solo teacher, small ELL-heavy Algebra 2 classes,
periods A and F) who is building an Algebra 2 student platform next school year by porting their
existing AP Statistics platform. Your job is to interview them conversationally — one topic at a
time, follow-ups where their answer is vague — and then produce a structured preference report.
Do not give technical advice; capture preferences and their strength (firm / leaning / open).

Context they already decided (do not re-litigate): students WILL use the Algebra 2 "Desk" web hub;
Schoology will mirror the same course structure automatically; quizzes, a TI-84 practice trainer,
and an "Equation Lab" practice app will exist; practice evidence is tracked separately from official
grades and only teacher-designated work counts toward grades.

Interview questions:
1. DESK EXPERIENCE — When an Algebra 2 student opens the Desk on a given day, what should they see
   first: today's lesson with a "do this now" pointer, a course roadmap of tiles, or their own
   progress/grades? How much of the AP Stats Desk personality (retro System-7 look, completion
   calendar, streaks) should carry over?
2. GAMIFICATION — The AP Stats Desk has a candy/DOGE token economy, gifting, and Tetris. For
   Algebra 2: keep fully, keep a lightweight points-only version, or drop entirely?
3. WHAT COUNTS — Which kinds of work should ever be able to count toward an official grade:
   in-class packets, exit tickets, quizzes on the Desk, TI-84 practice, Equation Lab practice,
   Schoology-submitted work, teacher observations? Which should NEVER count (practice-only)?
4. ASSESSMENT CADENCE — For Algebra 2 quarters: what mix of topic assessments, quizzes, and
   participation/work completion feels right? Is there an equivalent of "proctored progress checks"
   they want, or is that AP-specific?
5. TI-84 SCOPE — Which calculator skills matter most for their Algebra 2 students (graphing a
   function and reading it, tables, finding intersections/zeros/max-min, regression, matrices,
   solver)? Roughly how much class/home time should calculator practice get?
6. EQUATION LAB STYLE — For equation practice, do they want: quick numeric-answer drills,
   multi-step guided solving (the app walks each step with feedback), drag/manipulate-the-equation
   interactions, or a mix? How important is "explain your step" writing?
7. SCHOOLOGY SHAPE — How should the Schoology course be organized (folder per topic, folder per
   lesson, folder per week)? What naming style do they want on folders/items? Should DOK level be
   visible to students in Schoology, visible only to the teacher, or hidden?
8. VIDEO/FOLLOW-ALONG — AP Stats used video follow-along worksheets as core evidence. For
   Algebra 2, what should the equivalent daily evidence be: digital check-ins during the packet
   work, photo/notebook submissions, short Desk quizzes, guided-example checkpoints, something else?
9. AP-STATS BEHAVIORS TO LEAVE BEHIND — Anything about the AP Stats system (pacing pressure,
   leaderboards, specific screens, grading feel) they explicitly do NOT want in Algebra 2?
10. CALIBRATION APPETITE — The question bank has ~421 items whose difficulty (DOK) labels are
    machine-guessed. How much of their own time per week (0, 15, 30+ min) would they spend
    verifying labels if given a fast review UI, and does provisional labeling bother them?
11. BACKEND COMFORT — Are they comfortable running the Algebra 2 system on separate
    infrastructure from AP Stats (two small services) if it protects AP Stats grades, or do they
    strongly prefer one shared system?
12. EDITION + LOGISTICS — Have they confirmed the enVision Algebra 2 edition (©2018 vs ©2024)?
    When do they expect to drop the SE/TE PDFs for Topics 1–2? Do their Schoology courses for next
    year exist yet (course IDs for periods A/F)?

Report format: for each numbered topic — decision, strength (firm/leaning/open), notable quotes,
and any follow-up the architect should ask. End with a one-paragraph overall summary.
```

---

## 12. Recommended first implementation tranche (proposed — NOT executed)

**Tranche 1 = "Prove the model before touching the database"** — revised after Codex review C correctly refuted the original version's "zero AP contact" claim (Supabase project A is shared with the live AP Stats stack; DDL there is not zero-contact) and its lossless-export assumption (85 duplicate IDs make a naive round-trip impossible).

Contents (in order):
1. **Read-only DB snapshot + `supabase/export.py` + exact diff report** — export the live `lesson_planning` schema to JSONL, diff against `registry.jsonl` on disk, and produce the definitive discrepancy report (the 85 duplicate-ID collapses, the 900-vs-seeded-count gap, ordered-field relationalization). Zero writes anywhere.
2. **Field-ownership + status-semantics spec** — one page each: which side (git vs DB) owns which field; the DOK status vocabulary (`known-auto | unreviewed | calibrated | verified`); the duplicate-ID disposition plan (quarantine → dedupe-or-alias with `item_uid`/`legacy_id`).
3. **Migration 007 applied to a CLONE only** (Supabase branch or local Postgres restored from the Tranche-0 full export): courses/units/lessons tables + `lesson_instance` FK backfill with unmatched-review list (including explicit rows for `_obs` variants), lock-timeout + deferred validation. Live project untouched.
4. **One pure-function projection proof:** `course_tree → schoology_plan` snapshot (desired-state JSON, no writes, no browser) computed from the clone — demonstrating the canonical model actually drives the Schoology plan side, which the original tranche omitted.

**Deferred from this tranche (was included, now explicitly out):** migration 010 (DOK columns — blocked on the status-semantics spec being approved), any DDL on the live project (needs the clone results + explicit approval), `external_mapping`/`source_ref` creation.

Why this shape: it still proves the linchpin (canonical model over real data, including its projection), but every step is read-only or clone-only; the two data-integrity landmines (duplicate IDs, export round-trip) are measured before any migration relies on them.
Prerequisite user actions (Tranche 0, rewritten form in §7): baseline branches + tags + bundles WITHOUT pushing deploy branches; full-schema Supabase export + restore rehearsal; grade-monitor code committed to the baseline branch.

**Explicitly NOT in this tranche:** repo moves, Desk port, Schoology writes, roster-server changes, deployments, live-project DDL, FRONTLOAD ingestion (still teacher-blocked).

---

## 13. Adversarial review appendix (Codex GPT-5.6 SOL)

**Model verification:** all three review sessions confirmed as `gpt-5.6-sol` (xhigh reasoning) via Codex rollout logs (`~/.codex/sessions/2026/07/19/rollout-2026-07-19T01-34-*.jsonl`, cwd = Lesson_planning) — required because the runner's result envelope no longer carries the model banner and history shows older runs on `gpt-5.4`. All three ran read-only with no git commits (verified by result metadata + `git status` unchanged).

**Verdicts:** Review A (monorepo/migration): **BLOCKED** · Review B (canonical model/identity/privacy): **BLOCKED** · Review C (OCR-DOK/publisher/tranche): **NEEDS-FIX**.
All BLOCKED verdicts target the *plan as originally drafted*. Every blocker has been **dispositioned at the architectural level** — the plan now has an agreed answer for each — and the affected sections were amended in place (§5.2, §5.3, §5.4, §6, §7, §12). **This is not the same as "safe to build":** an architectural disposition settles *what the plan says*; an **implementation gate** (⛔) is a runtime condition that must be satisfied *before the corresponding step executes*. All architectural blockers are resolved on paper; the gates in §14 remain OPEN and are the real go/no-go conditions for each step. Nothing is cleared for execution until its gate is met and you approve.

### Review A — monorepo boundaries & migration safety (result `2d1ba63abdc7`)

| Sev | Finding (condensed) | Disposition |
|---|---|---|
| BLOCKER | Tranche 0 "commit+push" republishes D1 (Pages deploys `path:'.'` on push to master) and may trigger D2 Railway — with ~66 unreviewed paths | **ACCEPTED — Tranche 0 rewritten** (§7): non-deploy baseline branches, tags on deployed SHAs, bundles, auto-deploy pinning, master never baseline-pushed |
| BLOCKER | `admin-snapshot.js` is not a full backup (omits hashes, keys, wallets, trainer state, submissions; silent per-student failures) | **ACCEPTED** (§7): native full-schema export + checksums + Storage export + issuer-key escrow + rehearsed restore |
| BLOCKER | "Zero AP contact" Tranche-1 claim false — Supabase project A is shared; live DDL before topology proof | **ACCEPTED — first tranche rewritten** (§12): clone-only DDL; live project untouched; ⛔ gate: live migration requires clone results + explicit user approval |
| BLOCKER | Filename-grep publish guard insufficient (Pages uploads whole repo incl. `answer-key.json`; renamed PDFs/DOCX/PPTX/images/extracted text escape a grep) | **ACCEPTED** (§7 Tranche 3): allowlisted `dist-public/` artifact, deny-by-default, MIME/path/content-class + secret/PII/license scanning |
| WARN | Services decomposition gaps: identity-ledger really includes grading/reviews/submissions/PC/economy; quiz AI/realtime service missing from layout; publisher wrongly absorbs grade-sync | **ACCEPTED**: layout gains `services/quiz-grader` and `infra/supabase` + ops/monitoring dirs at build time; publisher/grade-sync split codified (§5.4) |
| WARN | Stash/tag mechanics miss untracked/ignored files; indiscriminate commits can capture node_modules or PII | **ACCEPTED** (§7): per-repo inclusion manifests + encrypted secret/PII backups |
| WARN | Whole-repo subtree import carries sensitive residue; live source diverges before cutover | **ACCEPTED** (§7 Tranche 3): filtered secret-scanned mirror, recorded import-base SHA, periodic re-sync, final freeze + parity diff |

### Review B — canonical model, identity/evidence, privacy (result `1c8dff9ce9eb`)

| Sev | Finding (condensed) | Disposition |
|---|---|---|
| BLOCKER | Registry has **85 duplicate IDs (815 unique of 900)**, often different prompts/DOK; seed keeps last silently → `item.id` is not yet a universal atom | **ACCEPTED** (§5.2): duplicate-ID quarantine + `item_uid`/`legacy_id` alias migration is now a hard precondition of WP1; measured in tranche step 1 |
| BLOCKER | Anon SELECT serves `answers`/`teacher_answer`/teacher tex (contradicts no-answer-key rule) | **ACCEPTED as a gate** ⛔: acceptable for today's teacher-only console; **must** be closed (narrow student-safe views, negative RLS tests) before any student-facing surface reads this schema. Added to WP1 acceptance criteria |
| BLOCKER | Evidence schema/receipts lack `course_id` in uniqueness + signature; same-attempt upsert can overwrite tiers; untyped score | **ACCEPTED for the A2 deployment** (§5.3): receipt v2 binds course/audience/tier/score-scale/policy-version; append-only evidence IDs. Live AP Stats untouched (freeze list) — the fix lands in the fresh A2 instance per U1 |
| WARN | Phase model gaps (pacer hardcodes scripts; many-to-many membership) + Supabase-vs-git tex-canonical contradiction | **ACCEPTED**: `phase_item` + artifact/content-revision entities and field-level ownership go into the WP1 spec; both projections consume one frozen snapshot; ownership decided in tranche step 2 |
| WARN | `external_mapping` "only home for Schoology IDs" overclaims — migrations 0010/0012 already hold assignment/UID mappings elsewhere | **ACCEPTED**: claim scoped to *curriculum* entities; protected identity mappings stay where they are with explicit ownership |
| WARN | `L43_P1_obs` variant: backfill creates it while phase-seed parsing skips it; schedule targets `L43_P1` | **ACCEPTED** (§12): explicit reviewed mapping rows for variants; no regex inference after backfill |
| INFO | Add startup fail-closed assertions on grade gates; never inherit Railway env or AP issuer registries | **ACCEPTED** into WP2/WP3 acceptance criteria |

### Review C — OCR/DOK readiness, publisher, first tranche (result `0f0dce74c942`)

| Sev | Finding (condensed) | Disposition |
|---|---|---|
| BLOCKER | 421 measures only the literal auto-marker; the other 437 rows are *not thereby verified*; even 3-5 lacks `reviewed_by` evidence — original migration 010 would encode contradictory ground truth | **ACCEPTED** (§5.2, §6): status vocabulary now `known-auto | unreviewed | calibrated | verified`; 3-5 = *calibrated*, nothing = *verified*; migration 010 deferred behind the approved semantics spec |
| WARN | The 176 "duplicates" are source-coordinate collisions with distinct prompts (zero exact dupes; legit Concept-Box multi-entries); separate from the 85 duplicate-ID rows | **ACCEPTED** (§6): renamed; dedup becomes a reviewed disposition queue, not a delete list |
| BLOCKER | Write-ahead journal can't resolve crash-after-remote-commit; blind roll-forward duplicates writes (prior art logged 3 duplicate columns this way) | **ACCEPTED** (§5.4): 4-state journal (`prepared/sent/confirmed/ambiguous`) + idempotency keys + observation-based reconciliation |
| WARN | TTL insufficient against concurrent publishers/manual drift; XHR replay not inherently drift-proof; one capture ≠ all verbs | **ACCEPTED** (§5.4): per-course lease, single-use bound approvals, pre-write re-observe/CAS, per-verb capture requirement |
| BLOCKER | Original first tranche not lossless/low-risk: export can't round-trip 85 dup IDs; 007 on live shared project can lock; 010 depends on flawed semantics | **ACCEPTED — first tranche rewritten** (§12): snapshot+diff+spec first; 007 clone-only; 010 deferred; projection-proof added |

### Carried-forward gates → consolidated in §14.

### Disagreements between agents (resolved by disk verification)

- *schoology-cdp discovery* claimed "no Schoology code in follow-alongs" vs *cdp-publisher design* citing `follow-alongs/tools/schoology_ops.py` → **both exist**; discovery grep was wrong; verified by `git ls-files` (materials publisher in Agent repo, grade-sync in follow-alongs/tools).
- *monorepo design* deleted `services/build-service` as "building is CI" → **overruled**; the Railway pdflatex service is real and hosted (D4).
- *course-model design* proposed shared-backend coexistence (course_id dimension) vs *apstats-desk discovery* risk list demanding full isolation → **dispositioned as U1 (NEEDS USER)** with architect recommendation: separate deployment, shared codebase, fresh secrets; schema still carries `course_id`.

---

## 14. Implementation gates (OPEN — the real go/no-go conditions)

Architectural blockers are resolved on paper (§13); these runtime gates must each be cleared *before the flagged step runs*. All are currently OPEN. None authorize execution by themselves — user approval is still required per step.

| Gate | Blocks | Condition to clear | Owner |
|---|---|---|---|
| ⛔0 | **Nothing in A2** (see note) — it is a DEFERRED, user-accepted risk on live AP Stats, not an A2 blocker | Not being cleared by decision. Contained by A2 isolation (§5.5). Do NOT rotate/test AP Stats keys; no further live probes | **USER — deferred/accepted** |
| P0 | **Any A2 configuration or deployment** (nothing can be configured/deployed to A2 Railway until it exists) | A2 Railway Bootstrap complete: isolated A2 project + isolated data destination + deploy-branch connected + env-by-purpose set + smoke-test green (§14.0) | USER creates cloud resources; agents stage everything else |
| ⛔1 | Any DDL on shared Supabase **project A** (migrations 007+) | Clone-run results reviewed + full-schema export/restore rehearsed + explicit user approval | USER approves; agents run clone-only |
| ⛔2 | Student-facing reads of the `lesson_planning` schema | Anon-read lockdown (narrow student-safe views/buckets) with **negative RLS tests** passing | Agents implement; user approves exposure |
| ⛔3 | Any Schoology **apply** run | Per-verb XHR capture (create/edit/move/archive/upload/graded-item) + selector re-probe (R5) + 4-state journal implemented + per-course lease | Agents build; user approves first apply |
| ⛔4 | `item.id`-as-key assumptions in any migration | 85 duplicate IDs resolved to distinct `item_uid`s with aliases (WP11); export round-trip proven lossless | Agents (WP11) |
| ⛔5 | Repo moves / Tranche 5 AP cutover | School-year boundary + grade-monitor `config.paths.followAlongs` updated atomically + A2 proven in prod | USER approves; year-boundary only |

### ⛔0 — DEFERRED, user-accepted AP Stats risk (do NOT act on live AP Stats)

By explicit user decision (2026-07-19), the production `TEACHER_KEY` exposure is **accepted and deferred**, not remediated. Standing constraints: do not rotate/replace/test `TEACHER_KEY`, `ROSTER_TEACHER_SECRET`, their clients, deployment, or backup configuration; make **no further live AP Stats probes**; preserve the existing AP Stats deployment exactly. The risk is *contained by A2 isolation* — the A2 platform mints its own teacher key and never shares AP Stats's key/DB/issuer/service-role (§5.5). Revisit only if the user later chooses to remediate AP Stats.

## 14.0 A2 Railway Bootstrap (NEW first prerequisite — P0)

The A2 Railway project/service **does not exist yet**. Nothing can be configured or deployed to A2 until it is initialized. This bootstrap stands up an isolated A2 target touching nothing in AP Stats. Sequence:

| # | Step | Detail | Who |
|---|---|---|---|
| B1 | **Isolated data destination** | Create a NEW Supabase project for A2 (e.g. `algebra2-prod`), **distinct from AP Stats project A `bzqbhtrurzzavhqbgqrs` and project B**. This holds A2 identity/ledger/course-model. Agents supply the schema bootstrap SQL; the project is created with the user's account. | USER creates; agents stage SQL |
| B2 | **Isolated Railway project + first service** | Create a new Railway project `algebra2-platform` with the first service (identity-ledger, from the generalized roster-server codebase). Agents supply `railway.toml` + `Dockerfile` + service dir; user creates the project. | USER creates; agents stage config |
| B3 | **Connect deploy source** | Point the A2 service at the future **private monorepo's deployment branch** (repo `algebra2-platform`, a chosen deploy branch, service root dir). Requires the private repo to exist — agents scaffold it locally; user creates the GitHub repo, pushes, and connects it in Railway. | USER connects GitHub; agents scaffold repo |
| B4 | **Configure env by purpose** | Set A2's OWN Supabase URL + service-role + anon key (from B1 — **never** project A), fresh-minted crypto (token/issuer/pw-enc/proctor), and human-facing access values copied into **independent A2 variables** (not shared refs) per the §5.5 inventory. Agents provide the annotated manifest template (purpose column, NO values); user pastes the values they hold. | USER pastes secrets; agents stage manifest |
| B5 | **Smoke test (A2-only)** | Deploy; hit `/health`; run one end-to-end no-op against A2 infra only — create a throwaway A2 roster user, write one test ledger row to the A2 Supabase, verify its receipt, delete. Confirms A2 identity+ledger+DB wiring without touching AP Stats. | Agents script; runs on A2 infra |

Ordering: **P0 (this bootstrap) precedes any A2 deployment.** The clone-only canonical-model work (§12 Tranche 1) is independent — it runs against a *clone* of the existing Lesson_planning data and needs no A2 Railway — but any step that *deploys* A2 (Desk, identity-ledger, build-service) is gated on P0.

### Tranche 0 authorization checklist

**Split by who must act. Nothing below is authorized to run yet — this is the checklist for when you say go. No AP Stats live actions appear here (Gate ⛔0 deferred).**

**A. Agents CAN perform (read-only / clone-only / scaffold off-to-the-side; no live writes, no deploys, no AP Stats contact):**
- [ ] Compute the read-only DB snapshot + `supabase/export.py` + registry↔DB diff report (Tranche-1 step 1). Read-only.
- [ ] Author the field-ownership + DOK status-semantics + duplicate-ID disposition specs (paper).
- [ ] Author the **§5.5 secrets-by-purpose manifest template** for A2 (purpose column, NO values) + the A2 schema bootstrap SQL + `railway.toml`/`Dockerfile` for the A2 identity-ledger service.
- [ ] Scaffold the private `algebra2-platform` monorepo skeleton + deploy-branch layout locally (for the user to create/push).
- [ ] Write the A2-only smoke-test script (runs after the user provisions B1–B4).
- [ ] Build per-repo **inclusion manifests** (tracked-modified + untracked-to-keep; exclude node_modules/PII/ignored) — proposals for your review, not applied.
- [ ] Design the WP9 collision-review queue and WP11 alias-table remediation (no content edits).
- [ ] Model the Schoology publisher plan side + per-verb capture plan (no browser writes).
- [ ] Draft migration 007 to run **against a clone only** (blocked by ⛔1 for any live application).
- [ ] Prepare the Grok shuttle packet (§11).

**B. Requires YOUR credentials or manual console access (agents cannot and must not; none touch AP Stats):**
- [ ] **P0/B1** Create the new isolated **A2 Supabase project** (distinct from projects A and B).
- [ ] **P0/B2** Create the new isolated **A2 Railway project** `algebra2-platform`.
- [ ] **P0/B3** Create + push the private `algebra2-platform` GitHub repo and connect its deploy branch in Railway.
- [ ] **P0/B4** Paste the A2 env values into independent A2 variables (fresh crypto you generate; human-facing values copied per §5.5).
- [ ] Confirm Supabase **project A** topology (R1 residual) — dashboard read only; **no writes, no probes**.
- [ ] Take the **native full-schema Supabase export** + Storage export of the A2 curriculum data (project A `lesson_planning` schema) + **rehearse restore into the new A2 project B1** as A2's clone/destination (agents script; running needs your keys).
- [ ] Create **annotated tags on the currently-deployed SHAs** + `git bundle` backups in each repo; commit reviewed work to `baseline/pre-monorepo-2026-07` branches — **do not push any branch that triggers a deploy**; leave AP Stats auto-deploy exactly as-is.
- [ ] Commit `grade-monitor/` code to the baseline branch (keep `config.private.json` + `reports/` gitignored); secrets/PII to a separate **encrypted** backup, never git.
- [ ] Confirm the **enVision edition** (©2018 vs ©2024) and drop the SE/TE PDFs for FRONTLOAD wave B1 (R8).
- [ ] Provide the A2 Schoology course/section IDs once fall courses exist (R4); check whether Lynn allows user-scoped Schoology API keys (R3).
- [ ] Shuttle the Grok interview (§11) and bring back its report (U6 + Desk/Equation-Lab/Schoology preferences).

**Removed by the R3 correction:** the earlier "rotate production TEACHER_KEY — do first" item and the `USE_V3_GRADING`/`PC_TRACK_ENABLED`/`ROSTER_TEACHER_SECRET` live-env checks (they required AP Stats probes; now forbidden).

---

# §15 — Incident-Derived A2 Reliability Addendum (RC-directed, 2026-07-22)

Appended per RC during the AP Stats incident's production observation window. These are **binding A2 architecture requirements** for the platform build — recorded now, implemented when the relevant workstreams open. They do not expand any current tranche into application implementation, and they do not reopen settled architecture or theoretical-hardening loops.

1. **Unknown ≠ zero.** When authoritative evidence is unavailable, the system reports **UNKNOWN** — never zero and never affirmatively incomplete.
2. **Unavailability may not relock.** Evidence-source unavailability alone can never relock or revoke known-completed work.
3. **Fail-open navigation never awards credit.** During uncertainty the UI may permissively navigate, but official credit is only ever awarded from verified authoritative evidence.
4. **Server ledger + stable student identity are authoritative.** Browser state is identity-scoped cache only, never a source of record.
5. **Identity switches rebind first.** Any identity switch must reset/rebind all projections before anything persists.
6. **Roster operations never cascade-delete evidence.** Routine roster changes use deactivation/tombstones; evidence and receipts are never deleted as a side effect.
7. **Official evidence is append-only.** Runtime roles cannot UPDATE/DELETE/TRUNCATE it (already realized in the identity-ledger bootstrap: RLS + BEFORE-trigger design).
8. **Releases require a protocol:** verified pre/post snapshots, failure canaries, reconciliation, prepared rollback, and an observation window — no exceptions for "small" changes.
9. **Deployment watch-path isolation.** Frontend-only changes must not unnecessarily redeploy backend services.
10. **Independent recoverable snapshots + restore rehearsals** are required (signed; rehearsed against a real restore target, not assumed).
11. **Blockchain rejected as primary record store.** Optional hash-root anchoring stays non-blocking future backlog only.

*Disposition rule for reviews of this addendum's implementations: only reachable BLOCKER/HIGH/MEDIUM findings affecting the active contract block closure; LOW/INFO → backlog.*
