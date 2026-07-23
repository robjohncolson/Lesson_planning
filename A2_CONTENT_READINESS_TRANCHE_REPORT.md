# Algebra 2 Content-Readiness Tranche — Integration Report

**Date:** 2026-07-19 · **Author:** Fable (head architect) · **Status:** integration gate (Codex reviewed; remediation of review findings in flight).
**Hierarchy honored:** Fable (architecture/prioritization/synthesis) · Opus (bounded-workstream managers, independent verification) · Sonnet (file creation/scripts/tests) · Codex GPT-5.6 SOL (adversarial review at the gate). All local: no cloud, git init, commits, Schoology/CDP, AP Stats, secrets, or automatic content decisions. All source registries byte-for-byte preserved (`questionbank/registry.jsonl` sha256 `b7f9a040…4e56b8` unchanged throughout).

---

## 1. Dispatch ledger (actual model roles)

| WS | Workstream | Manager (model) | Implementer (model) | Reviewer (model) | Owned path | Manager sign-off |
|---|---|---|---|---|---|---|
| 1 | Topic 4-1 stranded-ingest diagnosis + recovery plan | Opus | Sonnet | Codex gpt-5.6-sol | `inventory/topic-4-1/` | ✅ |
| 2 | 137 absent visuals classification + 7 broken-path repair prep | Opus | Sonnet | Codex gpt-5.6-sol | `inventory/visuals/` | ✅ |
| 3 | 85 legacy-ID collision human-review queue | Opus | Sonnet | Codex gpt-5.6-sol | `inventory/review-queue/` | ✅ |
| 4 | DOK verification workflow + review-interface design | Opus | Sonnet | Codex gpt-5.6-sol | `inventory/dok-workflow/` | ✅ |
| 5 | OCR inventory → topic/lesson/prereq/pacing map | Opus | Sonnet | Codex gpt-5.6-sol | `inventory/course-map/` | ✅ |
| 6 | Content-readiness dashboard/spec (synthesis) | Opus | Sonnet | Codex gpt-5.6-sol | `inventory/dashboard/` | ✅ (survived a transient API-500 mid-run; deliverables intact, resumed to sign off) |

Every Opus manager independently re-derived its numbers from source (not trusting the Sonnet self-reports) before signing off. Owned paths are disjoint and registered in `OWNED_PATHS.md`; no workstream deleted/cleaned outside its namespace (the earlier collision that prompted the policy did not recur).

## 2. Artifacts produced (all under `Lesson_planning/inventory/`)

- **topic-4-1/**: `DIAGNOSIS.md`, `RECOVERY_PLAN.md`, `inventory-4-1-assets.json`
- **visuals/**: `visual_asset_classification.json`, `VISUAL_ASSETS_REPORT.md`, `broken_path_repair.json` (+ build helpers)
- **review-queue/**: `collision_review_queue.json`, `COLLISION_REVIEW_QUEUE.md`, `build_collision_review_queue.py`, `README.md`
- **dok-workflow/**: `DOK_VERIFICATION_WORKFLOW.md`, `REVIEW_INTERFACE_SPEC.md`, `dok_wave_plan.json`, `gen_dok_wave_plan.py`
- **course-map/**: `course_map.json`, `COURSE_MAP.md`, `prereq_gaps.md`, `build_course_map.py`
- **dashboard/**: `content_readiness.json`, `content_readiness_dashboard.html` (self-contained, offline), `CONTENT_READINESS_DASHBOARD_SPEC.md`, `build_content_readiness.py`

## 3. Computed findings & discrepancies

### Confirmed baselines (independently recomputed, all reconcile)
900 registry rows · **815 unique ids (85 duplicated with differing content)** · DOK **421 known-auto / 437 unreviewed / 42 calibrated / 0 verified** · answers 529 with-evidence / 371 missing · visuals **137 absent + 7 broken** · prereq edges **193 resolved (129/42/22, 16 cross-unit) / 18 dropped** · readiness **1 calibrated (3-5) / 9 incomplete / 1 blocked (4-1) / 18 provisional-frontload / 8 absent = 37**.

### Cross-workstream syntheses (findings no single input had alone)
- **DOK-conflict collisions:** of the 85 legacy-id collisions, **22 have two copies with DIFFERENT DOK — all in lesson 5-4** (21 are dok1-vs-2; `5-4-savvas-q41` is dok2-vs-3). Merging the wrong copy would corrupt the DOK label *and* its wave assignment — so these **must be DOK-resolved before any merge**, and rank above the 63 pure prompt-drift collisions.
- **Visual risk is ~14, not 137:** importance-weighting shows only **14 essential visuals** (all source-PDF-required, concentrated in 6-4/4-3/5-x) actually gate content; the other 123 are **75 TikZ-regenerable** from prompt text + 48 decorative/irreplaceable-photo (numeric givens already in text). The 7 broken 3-5 paths are trivially repairable (files exist under `calibration/sources/`).
- **4-1 stranded blocker with graph reach:** 4-1 has calibration + 61 screenshots + 15 skeleton stubs but 0 registry rows and no SE/TE — pipeline stalled at the transcribe→`qb_append` stage (proximate cause the 5/13 dept-skip); critically its four DOK-3 anchors (q20/22/25/26) have screenshots but **no** skeleton stub. Its retirement leaves **4 dangling edges into 4-1** (from 4-3/6-3/6-4/4-5) plus 1 genuine front-of-year gap (5-1→3-1) — so reviving-vs-cutting 4-1 is also a graph-integrity decision.

### Codex gate-review findings (all 3 verdicts NEEDS-FIX — remediation routed to managers)
- **Review A (WS4 + WS6):** WS4 — 3 HIGH: `verified` predicate fail-open (accepts `reviewed_by` alone; must require `reviewed_by AND reviewed_at`); `calibrated` state ambiguous (per-row vs lesson-wide meanings conflict); safeguards not uniformly fail-safe (quiz-selection "proceed-anyway" + Desk provisional-weighting escape hatches contradict the locked ban). WS6 — 2 MEDIUM: DOK-conflict code scans wave-plan dups instead of the *declared* collision-legacy-id join (coincidentally-correct today); the 7 broken-count + readiness states are hardcoded (the "fully recomputes" claim overstated).
- **Review B (WS5 + WS1):** WS5 — 1 HIGH: node identity keyed by the ambiguous `item.id` (43 of 193 edges touch a duplicated id) → must key by the opaque `item_uid` from the dedup alias map; 1 MEDIUM: retirement-gap mislabeled as frontload-gap. WS1 — 1 LOW: 4-1 file count 44-vs-46 + drifted CONTINUATION_PROMPT line citations.
- **Review C (WS3 + WS2):** essentially clean — all data-integrity checks pass (85 groups, 170 distinct uids retained, nothing merged; 137+7 reconcile, every broken-path target exists, essential↔source-PDF coupling correct, registry unmutated). 1 LOW: 3 collision recommendation rationales (5-1 q18/q21/q22) mis-branch on a trailing-tag-only difference.

## 4. Decisions Fable can make without you (technical/architectural — being applied via the managers)

1. **Key the course-map (and all downstream identity) by `item_uid`, not the legacy `item.id`** — this is exactly what the locked opaque-uid decision (L25) is for; resolves the 43 ambiguous edges. *(Dispatched to WS5.)*
2. **`is_verified := reviewed_by AND reviewed_at`, fail-safe everywhere** — correctness of the DOK gate. *(WS4.)*
3. **Safeguards hard-block unverified DOK — no proceed-anyway / provisional-weight escape hatches** — enforces the locked rule that unverified DOK never drives selection/grades (U7/L23). *(WS4.)*
4. **Disambiguate `calibrated` vs a per-row reviewed state**; **implement the declared DOK-conflict join**; **derive (not hardcode) the broken-count + readiness states**. *(WS4/WS6.)*
5. **Split retirement-gap from frontload-gap** in the course-map taxonomy. *(WS5.)*
6. **Fix the WS1 file-count/citations and the 3 WS3 rationale texts.** *(WS1/WS3 — LOW.)*
7. **Readiness taxonomy** (promote 3-5 to CALIBRATED; keep 4-1 as its own BLOCKED state) — I made this reconciliation call; you may confirm or override (§5).

## 5. Smallest set of genuine teacher judgments needed from you

These require pedagogy / grading / source-interpretation / external-system judgment I will not make:

1. **4-1: revive or permanently retire?** (It's dept-skipped 5/13, yet `A2LessonSelection.txt` lists it and `CLAUDE.md` still says "ready".) If revive: **ingestion-only from the existing screenshots** vs **full rebuild** (needs SE/TE). This also decides whether 4-3/6-3/6-4/4-5 keep dead references.
2. **The 5-4 DOK-conflict pairs (22):** which DOK is authoritative — dok1-vs-2 for 21, and **dok2-vs-3 for `q41`** — *before* any collision merge. Subject-matter call.
3. **The 3 4-3 TE-disagreement DOK resolutions** (incl. keeping `q36-partC` at DOK 3) — these set student-facing DOK-3 spine claims.
4. **DOK acceptance-criteria bar** (TE cross-check + reviewer id/timestamp + note on every disagreement) and **Wave-0 placement** (3-5 as a reviewer warm-up vs straight to the assessment-feeders).
5. **The 14 essential (source-PDF-required) visuals** — provide the SE/TE figures, accept the gap, or reclassify; plus the ~21 borderline importance calls.
6. **Inverse-functions placement** (feeds 5-5 / 6-4; no clean Topic-1 slot) — front-load a mini-lesson or leave where enVision puts it.
7. **Pacing order** — confirm the advisory candidate order (cut order 6-5→6-4→5-5, protecting Unit 4 for LEHS).
8. **The 85 collision merges** — the final keep-both / merge decision per group stays yours (the queue only recommends).

## 6. Codex review verdicts

Review A (WS4+WS6): **NEEDS-FIX** (3 HIGH + 2 MEDIUM) · Review B (WS5+WS1): **NEEDS-FIX** (1 HIGH + 1 MEDIUM + 1 LOW) · Review C (WS3+WS2): **NEEDS-FIX** (1 LOW only; otherwise SHIP-quality). All models verified `gpt-5.6-sol`. Every finding is dispositioned and routed to its Opus manager; the substantive ones (WS4 DOK safeguards, WS5 identity) are genuine and worth the fix. No finding indicated a source mutation.

## 7. Recommended next tranche

**Immediate (in flight):** the five managers' remediation of the Codex findings → a short re-review confirms the tranche is clean.

**Then, local-only, no teacher judgment required:**
- Regenerate the **75 TikZ-recoverable visuals** from prompt text (Savvas-traceable, no new source) — biggest cheap win against the visual gap.
- Build the **DOK review tool** per `REVIEW_INTERFACE_SPEC.md` (local, writes only the append-only review-log) so the wave-based verification can actually run.
- Apply the **7 broken-path repairs** (proposed, one-line each) once you approve the registry touch.

**Blocked on your judgment (§5) — I'll prep the mechanics so a decision is one step from execution:**
- 4-1 recovery execution (if revived); the 5-4 DOK-conflict resolution + collision merges; the 14 essential-visual source recovery; DOK Wave-0 kickoff.

**Program-level, unchanged:** the bootstrap gate is OPEN — the isolated A2 Supabase + Railway project creation remains your manual step; and the **Grok preference interview** (grade policy, Desk UX, TI-84/Equation-Lab scope) still gates the grade-policy and Desk decisions.

---

## 8. Remediation close-out (adjusted 5-step sequence) — TRANCHE CLEAN

All Codex gate findings remediated and re-verified under the head architect's adjusted sequence + four hard-stop gates (no UID change · no wave/DOK value change · DOK-conflict = 22 · nothing changed outside WS4/WS6 paths). **No stop-gate tripped.**

| WS | Finding(s) | Resolution | Sign-off |
|---|---|---|---|
| 1 | 1 LOW (file count, citations) | count 44→46; `:32/:97/:192` | ✅ manager (disk-verified) |
| 2 | clean | — | ✅ |
| 3 | 1 LOW (3 rationales) | rationale branch fixed (3 records) | ✅ (CLOSED) |
| 4 | 3 HIGH (predicate/state/safeguard) **+ new HIGH (legacy-id identity collision)** | strict-AND `verified`; `calibrated`/`reviewed_once` split; no-escape-hatch safeguards; **re-keyed all identity surfaces to opaque `item_uid`** (mirrors WS5) | ✅ manager (recompute-from-source) |
| 5 | 1 HIGH (node identity) + 1 MED (gap taxonomy) | nodes keyed by `item_uid`; 176+17=193; dropped split 12/4/1/1 | ✅ manager (from-scratch recompute) |
| 6 | 2 MED (declared join, hardcodes) + input drift | declared collision-queue join (22); derived states; rebuilt vs frozen wave plan; +per-copy uid enrichment on the 22 | ✅ manager (recompute-from-disk) |

**The load-bearing find:** the WS5 node-identity fix exposed that WS4's DOK wave plan / review-log / promotion contract carried the *same* legacy-id collision (85 ids shared by 2 rows = 170 rows; e.g. `5-4-savvas-q41` is DOK2/wave4 **and** DOK3/wave3). Applying the locked opaque-uid decision (L25) to WS4 closed it: all 900 wave-plan `item_uid`s now match the frozen alias map per registry line (0 mismatches); the spec keys every identity surface by `item_uid` so the *next-tranche* review tool can't inherit the collision.

**Freeze ledger (final):** `registry.jsonl` `b7f9a040…4e56b8` · `assessment_shells.jsonl` `3a50fe9a…` · `item_uid_alias_map.json` `be4b507b…` · frozen WS4 input `dok_wave_plan.json` `5d3ff312…` · `course_map.json` `c8274dfb…` — all byte-identical end-to-end. Owned-path diff: only `inventory/dok-workflow/` (4 files) + `inventory/dashboard/` (4 files) changed; **nothing out-of-path**.

**Codex integration verdict (gpt-5.6-sol, read-only): SHIP** (conf 0.99) — Area A (WS4 keying) RESOLVED, no reachable legacy-id path remains, (a)(b)(c) intact; Area B (WS4→WS6) RESOLVED, conflict count 22 with additive uid enrichment, all numbers reconcile. One INFO/**not-reachable** doc typo (`DOK_VERIFICATION_WORKFLOW.md:164` "85 rows" → "85 ambiguous ids / 170 rows") → **backlog** per the refined convergence rule; to be swept when the next tranche edits that spec to build the review tool.

**Tranche status: CLEAN.** All six workstreams closed; both substantive HIGH areas (WS4 keying, WS5 identity) independently confirmed RESOLVED.

## 9. Post-tranche local build (NT1, NT2) — both CLOSED

Continuing local no-teacher-judgment work after the tranche cleared. Two workstreams, disjoint owned paths, no source mutation, no student-facing change; each Opus-managed → Sonnet, Fable-verified.

**NT1 — DOK review tool** (`tools/dok-review/`): `dok_review.py` CLI (queue/review/progress/promote/report) + `test_dok_review.py`. **item_uid-keyed throughout** (so the 85 shared-legacy-id / 170-row collisions never cross-credit — proven on the `5-4-savvas-q41` pair: two uids → two different registry rows, no cross-credit). `verified` = strict-AND(reviewed_by, reviewed_at); append-only log; `promote` writes a proposal, never the registry. **15/15 tests** (Fable re-ran). Frozen hashes intact. *Integration note:* log defaults to `tools/dok-review/review_log.jsonl` (in-bounds) vs the spec's `inventory/dok-workflow/` path — a one-line location decision at adoption. The tool now unblocks the teacher actually running wave-based DOK verification.

**NT2 — TikZ figure regeneration** (`inventory/tikz-staging/`, staging only): 71 tikz-regenerable ids fully partitioned — **63 regenerated+compile-pass · 1 reclassified map→table (compiles) · 2 held-teacher (no-fabrication) · 5 no-asset = 71**; **64 `.tex`→64 `.pdf`, all compile clean** (Pilot 8/8, A 22/22, B 25+1-held, C/D 9/9). Manager re-compiled a per-batch spot-check (byte-identical/deterministic) + PNG-confirmed fidelity; every id traces to a real Savvas registry row; no numeric data invented. Registry byte-unchanged, `git status tex/ questionbank/` clean, only `inventory/tikz-staging/` touched. The out-of-scope 14 essential (source-PDF) + 48 photos untouched.

**New teacher-judgment flags from NT2** (compile fine; human confirms before any packet wiring): `4-3-ex-6` needs_teacher_disambiguation (prism-as-cube reading; shows both package options); `6-4-savvas-q30` needs_teacher_confirmation (schematic seismograph); the 2 held rows (`4-3-savvas-q36-partA-build`, `5-1-teacher-edition`) whose defining data isn't in their own prompt. One trivial staging cosmetic deferred to the wiring step: `4-5-concept-summary-2` Algebra column clips (needs a `p{}` width tweak). Program note: add `\RequirePackage{amssymb}` to `tex/preamble.sty` at the teacher-gated wiring step (one-line; staging snippets already carry it locally).

**Local no-teacher-judgment queue is now substantially drained.** The remaining critical path runs through teacher judgment (§5, sharpened below) and the manual A2 cloud bootstrap (user's step).

## 10. NT3 — Teacher Decision Console (decision-compression tranche) — CLOSED, Codex SHIP

**Deliverable:** `inventory/decision-console/TEACHER_DECISION_CONSOLE.html` (890 KB, self-contained, opens from file://) + `console_data.json` + `decisions_export.schema.json` / `teacher_decisions.template.json` + `build_console.py` + `README.md`. Built Opus→3 parallel Sonnets; manager ran 43/43 + 54/54 harness checks + a 40-decision DOM behavioral pass; **two Codex gpt-5.6-sol reviews**.

**Six sections:** (1) 4-1 revive/retire — parallel evidence cards + labeled architect recommendation (revive-via-ingestion, conf 0.7); (2) the 22 DOK-conflict pairs side-by-side, both copies' full registry context, four equal actions (keep-both / reconcile-labels / merge-candidate / needs-source-check); (3) 64-figure contact sheet (embedded thumbnails), the 2 confirmation-flagged figures isolated on top; (4) the 14 essential source-PDF visuals with per-item source requirements; (5) DOK rubric v0.1-PROPOSED (awaiting approval watermark) + un-recorded Wave-0 sample; (6) proposals-only decision export (Blob download + clipboard), schema-enforced.

**First Codex review: NEEDS-FIX** — 1 BLOCKER (S3 figure rows exported legacy ids as item_uid) + 1 HIGH schema (any-string targets) + 2 HIGH neutrality (S2 survivor-framing copy; flagged panels rendering "Verified visually"). All four remediated via the manager: every S3 row resolved through the frozen alias map (67 unambiguous + **4 ambiguous figure ids carrying both candidate uids** — 5-1-q45, 5-1-q48, 5-4-q44, 5-5-q36 — never silently pinned); schema enforces `^iu_[0-9a-f]{12}$` + conditional minItems (global actions exempt); neutral S2 intro; console-authored neutral provenance. **Re-review: SHIP** (all four RESOLVED, no new defects).

**Invariants:** all 8 input hashes byte-unchanged end-to-end (registry `b7f9a040…4e56b8`); zero changes outside `inventory/decision-console/`; no review log exists; "verified" renders only inside the required approval watermark; export is proposals-only — nothing writes the registry.

**Program state: STOPPED FOR TEACHER DECISIONS.** The console is the interface for §5's judgment queue; the export JSON is the return channel.

## 11. NT4 + NT5 — RC decision round (2026-07-20) — CLOSED, Codex SHIP

RC confirmed decisions; two workstreams executed them (Opus→Sonnet, Codex adversarial review + scoped re-check, both ending **SHIP**):

**NT4 — RC revised export + rubric v0.2 + console zoom** (`inventory/decision-console/`):
- `teacher_decisions_rc_v1.json` — 40 decisions, reviewer RC, fresh 2026-07-20 timestamps, schema-valid (validator proven live): S1 revive-ingestion-only (4-1 deliberately cut, NOT permanently excluded; restored as OPTIONAL CATALOG, no auto-scheduling) · S2 needs-source-check ×22 · S3 confirm ×2 (6-4 vector PDF readable and accepted) · S4 provide-source ×14 · S5 **request-changes**. Codex: export fidelity INFO-clean, zero mismatches.
- The Grok draft `teacher_decisions.json` preserved byte-identical (sha256 `782aa051…`).
- `DOK_RUBRIC_v0.2.md` — **v0.2-PROPOSED, awaiting RC approval**; RC's five-rule authority hierarchy verbatim in substance + v0.1→v0.2 criterion map; console §5 presents v0.2 with the Wave-0 sample re-annotated to apply the hierarchy CORRECTLY (only anchor-traced q27 illustrates rule 1; the four provenance-missing samples show rule 2 UNRESOLVED — the Codex HIGH that the first draft upgraded them).
- Console: click-to-zoom lightbox (Selenium-verified from file://), flagged figures re-rendered at 180 DPI, RC's 2 confirmations seeded as recorded state (0 made / 2 recorded / 38 pending; excluded from new exports by explicit code path).

**NT5 — provenance audit** (`inventory/provenance-audit/`): **Why match_quality:none despite registry DOK?** `match_quality` measures TE-source cross-check, not DOK presence: it looks up the Savvas item number in `calibration/{lesson}.json`'s `item_analysis`; `5-4.json` exists but `item_analysis` is `{}` (its own note says the LaTeX-transcription step was left incomplete), so all 132 lesson-5-4 rows are "none" — 75 prefix rows hit the empty lookup, 57 non-prefix rows short-circuit before it; **all 44 conflict rows are in the empty-lookup population** (`NO_ITEM_ANALYSIS_DATA_FOR_LESSON`). The registry DOES carry ingest-time Savvas DOK claims — they're just unverifiable on disk. Zero-TE-coverage lessons: 3-5, 4-4, 5-4, 6-5. **Resolution path:** transcribe the Savvas TE 5-4 item-analysis (Practice #21–39, 41, 44, 45) into `5-4.json` → re-run the generator → rows flip to "exact" and TE-vs-registry disagreements surface via the existing mechanism. Snapshot language throughout (no invented history); audit script performs a real 900/900 row-level cross-check against the frozen plan.

**Invariants held across the round:** registry `b7f9a040…4e56b8` byte-identical; Grok draft byte-identical; wave plan/course map/alias map frozen hashes unchanged; changes confined to the two owned namespaces; everything remains proposals-only and PROPOSED — nothing applied to the registry, nothing marked verified.

**Awaiting RC:** (a) rubric v0.2 approval (nothing gets marked verified until then); (b) the SE/TE source material for the 14 provide-source items and the 5-4 TE item-analysis transcription (which also unblocks the 22 needs-source-check pairs); (c) 4-1 ingestion-only execution is authorized as optional catalog content — ready to run as a gated registry-append workstream when RC wants it.

## 12. NT6 — dok-review tool ↔ rubric v0.2 semantic alignment — CLOSED, R1–R5 FAITHFUL

RC directive: align `tools/dok-review/` with rubric v0.2 (kept PROPOSED; approval deliberately not sought). Three Codex-reviewed rounds (initial NEEDS-FIX with R1–R5 all DIVERGENT → F1–F8 → G1–G6 → one LOW doc fix). **Final Codex table: R1–R5 ALL FAITHFUL.** GitNexus impact analysis ran per modified symbol every round (index refreshed 29→4,788 nodes; all LOW except two intended-MEDIUM chokepoints; auto-managed CLAUDE.md/AGENTS.md gitnexus blocks regenerated as a disclosed byproduct — verified confined to those blocks).

**The semantic model now enforced (141 tests):**
- **Two-tier**: reviewer + timestamp ⇒ REVIEWED, never verified. VERIFIED requires: version in the on-disk `rubric_approvals.json` manifest (ships EMPTY, fail-closed loader, duplicate versions poison the load) AND tool-stamped `recorded_at` ≥ `approved_at` — **no retroactive verification**: pre-approval entries are permanently non-verification-grade; the only path is re-review after approval.
- **`needs-source-check`** terminal-unresolved; resolvable only via explicit `--resolves-source-check` attestation + item-bound on-disk provenance — a generic later confirm (even with genuine rule-1 provenance) does not resolve it.
- **Rule-1 provenance is item-bound three ways** (lesson equality; kind-aware exact number identity — only `-savvas-qN` binds to practice anchors, only `-ex-N` to `item_analysis` keys, lq/try-it/TE ids can never be rule-1; calibration entry for that same number). Empirical resolving set over the shipped corpus: 35 of 900 items (3-5 q27+q30 via DOK-3 anchors + 33 example items in 4-3/4-5/5-1/5-5/6-3/6-4).
- **Changes** require chosen_dok∈{1,2,3} (module-level, not just argparse) + rationale + provenance + reviewer-attested `item_basis`; textbook-exact changes are source-dispute resolutions requiring resolving provenance; other bases rate actual cognitive demand (R3). R4 quoted verbatim in all reviewer-facing surfaces. Aware-only ISO timestamps, per-item monotonicity, promotion full-chain validation through the single `entry_is_verified` predicate, decision-specific malformed-entry classification, documented local-file threat model.

**Invariants:** registry `b7f9a040…` and wave plan `5d3ff312…` byte-identical throughout; calibration git-clean; approvals manifest empty (guard-tested); nothing approved, nothing verified-in-fact; owned scope exactly `tools/dok-review/` + two status-only rubric annotations. **Carry-forwards flagged** (future gated pass): `inventory/dok-workflow/` specs + `gen_dok_wave_plan.py` still use the older reviewed⇒verified predicate; decision-console artifacts still say "tool is NOT modified".

**Awaiting RC (unchanged + one addition):** rubric v0.2 approval is now operationalized — approving = adding `{version, approved_at}` to `rubric_approvals.json`, after which verification requires fresh post-approval reviews under the aligned tool.

## 13. NT7 + NT7-R — semantic propagation: ONE canonical verification projection — CLOSED, every consumer agrees

RC directive: propagate the tool's v0.2 semantics to all upstream consumers; one canonical projection; fail-closed; prove identity across consumers; Codex reviews cross-consumer consistency; return the approval procedure only after every consumer agrees. Executed as NT7 (propagation) + NT7-R (Codex-driven remediation, P1–P8, with a Fable-authorized namespace expansion to the root inventory builder — the competing predicate's publisher — and minimal tool hardening).

**End state (all Codex-confirmed across four bounded reviews + Fable-verified):**
- **One predicate:** `dok_review.entry_is_verified` (via `tool_state_for`) is the only executable verification logic anywhere. The wave-plan generator AND the base-inventory builder each derive it **independently** (generator via the tool's loaders; base builder via its own registry+alias-map join → same tool functions — deliberately not via the wave plan), giving a genuine two-path cross-check. The dashboard single-sources all published verified surfaces from the wave plan's `review_state` and gates with a **three-way per-item UID-set equality** (symmetric difference named on failure — proven discriminating by a same-cardinality wrong-UID negative). The console guards manifest/plan coherence (empty manifest ⇒ zero verified rows, fail-loud) with manifest-keyed copy.
- **Fail-closed uniformly:** missing/malformed log or manifest ⇒ zero verified everywhere; whole-log and whole-manifest poisoning (proven by a discriminating mixed valid+malformed fixture); never a registry-field fallback — the old `reviewed_by`-alone branch is deleted from the base builder.
- **Proof:** 11-test cross-consumer suite subprocessing the REAL builders end-to-end (positive + negative legs) across an 8-case fixture matrix incl. pre-approval-never-verifies, decisive NSC-veto, invalid-entry, and q41 dual-uid isolation — per-item identity across tool API / plan artifact / dashboard / console for all 900 uids. Tool suite 154. Totals byte-invariant: waves 42/4/220/7/627 · dok_status 421/437/42/**0** · match_quality 672/224/4 · wave plan `0e6426bc…` deterministic.
- **Self-documenting fail-loud pins:** the three deliberate frozen-baseline pins (dashboard `dok.verified`, ws6 distribution, base-builder reconciliation) abort with guidance naming their authorizing approval-procedure step — a skipped step is a guided abort, never a mystery. Key discovered semantics, now documented: the **first** verified Wave-0 item demotes 3-5 CALIBRATED→INCOMPLETE (overlay pulls it from the base bucket) — ws6 pins change at first item, not lesson completion.
- **Docs accurate to code:** specs rewritten to the two-tier model; the operational approval procedure (named updates (a)–(f), code-enforced vs conventional orderings, fail-loud enumeration) lives in `DOK_VERIFICATION_WORKFLOW.md`; rubric doc untouched except status-only annotations.
- **Process notes (disclosed):** the NT7-R manager twice corrected its own reporting (procedure not actually mirrored to spec until P1; a mislabeled finding provenance) — both surfaced by Codex/Fable cross-checks and fixed; it implemented the final two line-level doc corrections directly rather than via Sonnet (disclosed, docs-only, code-diffed). One runner defect found and memorized: the cross-agent envelope can clobber Codex's result file with a stub — real analysis recovered from the rollout patch call.
- **Locks held end-to-end:** registry `b7f9a040…` · approvals manifest EMPTY `c63cbcf9…` · Grok draft `782aa051…` · rc_v1 `ad97b2ba…` · no real review log ever existed · v0.2 remains PROPOSED, approval not sought.
- **Named future pass:** `inventory/provenance-audit/audit_match_quality.py` recomputes registry-derived status and will correctly flag verified rows after the first real approval — canonicalize it in its own namespace then (procedure step 3(f)).

## 15. NT8 — POST-APPROVAL TRANSITION — CLOSED GREEN (Codex-reviewed)

RC directive after approving v0.2: make tests hermetic, update current-state language, run the zero-review regeneration, full battery, Codex review of lifecycle-transition correctness + test isolation. Executed as NT8 + one Codex-driven fix round.

- **Hermeticity (proven adversarially):** all unit tests isolated from the real manifest via an explicit `approvals_path`/`--approvals` surface (7 functions, appended defaults); tool suite passes with the ambient manifest absent AND poisoned; cross-consumer hermetic tests pass absent/poisoned/extended-with-v0.3. Exactly TWO named integration tests are the only ambient readers: `TestRealManifestIntegrationOnly` (tool) and `test_integration_ambient_repo_state_pins` (cross-consumer, which also carries the committed-artifact drift pins — genuine drift fails only this test, prompting a deliberate re-pin per the named-update procedure). The autouse repo-state guard is snapshot-based (before==after ⇒ tests mutated nothing; no pinned constants).
- **Language:** every false current-state PROPOSED/AWAITING/EMPTY claim flipped to APPROVED @ 2026-07-20T19:06:13-04:00 across the rubric doc (header + one dated annotation; criteria + historical annotations untouched), manifest `_comment`, tool README/docstrings, console (renders APPROVED branch, 0 AWAITING occurrences), and both workflow specs. Historical notes and conditional branches preserved; both teacher exports byte-identical (contemporaneous "proposed" notes are historical facts).
- **Zero-review regeneration:** wave plan `0e6426bc` → `4fc6baa4` (tree-diff: exactly one change — `approved_rubric_versions` []→["v0.2"]); inventory/dashboard/console regenerated in order; **every consumer reports v0.2 APPROVED @ timestamp / 900 unreviewed / 0 verified**; all totals byte-invariant; the three frozen-baseline pins passed untouched; console FROZEN_HASHES re-pinned (named 3(d) update).
- **Battery:** tool 154/OK · cross-consumer 12 (11 hermetic + 1 integration) · determinism proven by out-of-tree rebuild · GitNexus re-analyzed (MCP impact tools unavailable — documented manual sweep, all changes in owned paths) · registry `b7f9a040…` and both exports byte-locked · approval entry immutable · no review log ever existed.
- **Codex verdict path:** first review NEEDS-FIX (cross-consumer guard read the ambient manifest — a genuine isolation catch; two stale comments); fix round closed both with a three-way adversarial re-proof; lifecycle correctness, artifacts, pins, immutability all INFO-clean-confirmed.

**SYSTEM STATE: GREEN.** The verification pipeline is live: any verification-grade review recorded after 19:06:13-04:00 will verify; drift fails loudly in exactly one named place per suite. **TE-transcription gate now OPEN per RC's sequencing.**

### §15a — 5-4 TE transcription contract (pre-registered by RC, 2026-07-20; workstream dispatches on source receipt)

1. **Source intake spec:** full pages (not tight crops) showing the 5-4 lesson heading, the item-analysis table header, Practice #21–39/#41/#44/#45 with DOK labels, printed page numbers, the edition/copyright page once (provenance anchor), overlap where the table spans pages. Drop location: `questionbank/calibration/sources/` (`5-4_savvas_*.png` pattern) or as directed.
2. **Match-quality reporting:** report `exact` / `derived` / `none` counts separately, **as computed by the generator's actual suffix rule** — no predeclared counts (the earlier "75 flip to exact" phrasing was an overclaim; the 75 is the prefix-branch population, not a predicted exact count).
3. **Evidence only:** transcription + TE agreement create *evidence*; they write **no review-log entries** and confer **no VERIFIED status**. Verification still requires post-approval reviews through the tool.
4. **Disposition routing:** exact TE-registry agreements → one **RC batch-confirmation proposal** (RC confirms in bulk; nothing auto-recorded). Genuine disagreements → presented **individually** for RC's judgment through the v0.2 pipeline.
5. **Registry untouched** throughout; the 22 conflicts are not manually resolved by Fable; the drift-pin integration test's expected single failure gets its named re-pin per procedure.

## 16. NT9 — LESSON 5-4 TE TRANSCRIPTION — CLOSED, both Codex reviews SHIP (2026-07-22)

§15a contract executed on RC's source-sufficiency override. **Four independent readings of the TE p.258 Item Analysis table agree cell-for-cell** (implementer, manager pre-recorded, Fable, Codex-refutation pass): Ex1 21–24,44→1/18→2 · Ex2 25–28→1/16,17,40,43,46→2 · Ex3 29–32→1/15→2 · Ex4 33–35,45→1/**19,41→3** · Ex5 36–38→1/20→2 · Ex6 39→1/42→2. Same-table confirmed across both captures (`af34c4d9…` full page w/ TOPIC 5 | 258 | LESSON 4 footer; `273db411…` closeup); provenance recorded with the honest edition caveat (RC override); OneDrive originals untouched; captures confined to the private tree.

**Generator-computed results (not predicted):** global match_quality **exact 285 / derived 4 / none 611** (was 224/4/672); lesson 5-4: **61 exact / 71 none** (q1–q14 + 57 non-prefix correctly stay none); **22 exact_disagreements** — all copy-A rows (q21–q39 dok2-vs-TE1, q41 dok2-vs-TE3, q44/q45 dok2-vs-TE1). dok_status totals, wave counts, verified=0, 900 identities all unchanged — proven by byte-level reverse-reconstruction (reverting the 61 rows reproduces the old plan hash exactly). Three named re-pins only (generator count pins, cross-consumer plan pin, console FROZEN_HASHES). Plan `4fc6baa4…` → `f1dbdd19…`.

**TE-vs-registry comparison (22 conflict pairs):** te-agrees-with-copy-B: **22** · copy-A: 0 · both: 0 · genuine-disagreement: 0. TE sides with the richer, role-assigned later copy in every pair. Non-conflict: 7 pairs + 3 singletons agree. 39 agree / 22 differ = the generator's 22.

**Routing (neutral, NOT recorded):** `inventory/te-comparison-5-4/` — 39-row RC batch-confirmation proposal (PROPOSAL — NOT RECORDED, records_decisions:false) + 22 individual undecided disagreement items with full evidence, RC's four options open. **No review-log entries, no VERIFIED status, no registry mutation, no conflict resolved by Fable.**

**Verification:** suites 154 + 12 (named plan re-pin only); determinism; all byte-locks (registry `b7f9a040…`, approval entry immutable in `a889b88e…`, drafts `782aa051…`/`ad97b2ba…`); audit_match_quality.py fails its stale pin as anticipated — named future pass, untouched. **Codex (model-verified gpt-5.6-sol): review V (fidelity+provenance) SHIP, zero findings; review D (joins+semantics+neutrality+scope) SHIP, zero findings** (first combined attempt timed out at the runner limit; split per precedent). Also this tranche: PROGRAM_DOSSIER.md §15 — the RC incident-derived 11-point A2 reliability addendum recorded as binding architecture.

**AT THE TEACHER-DECISION GATE:** RC's batch confirmation of the 39 agreements + 22 individual judgments through rubric v0.2 are the first real reviews the approved pipeline will record.

## 17. NT10 — RC DECISIONS RECORDED: THE FIRST 39 VERIFIED ITEMS + MERGE PROPOSAL — CLOSED (2026-07-23)

RC's gate decisions executed. **The system's first real reviews now exist**: `tools/dok-review/review_log.jsonl` — exactly 39 tool-written entries (sha `4b61fd3b…`), reviewer RC, rubric v0.2, `calibration-anchor:5-4:practice #N` provenance, all 39 computing **VERIFIED** (Codex live re-derivation confirmed). One prerequisite fix en route: `resolve_provenance` couldn't bind practice ids via `item_analysis` (anchor-only) — a genuine tool↔generator evidence divergence 5-4 exposed first; the minimal extension was made with all G1 gates intact (adversarially probed clean), tool suite 154→161.

**Computed post-recording state, reconciled across every consumer** (per-item UID-set gates green): dok_status **421 known_auto / 398 unreviewed / 42 calibrated / 39 verified** (base invariants 421/437/42 pre-overlay held); review_state 861/39; ws6 unchanged (no 3-5/Wave-0 rows involved); waves 3:1 + 4:38. Plan `4fc6baa4` → `14c49acf`. All frozen-baseline pins tripped unmodified first, verified as exactly the recording effect, then named-updated. **39 promotion proposals staged (registry_written:false — registry byte-identical `b7f9a040…`).** The provenance audit's named 3(f) pass was performed (canonical overlay + re-pins; ALL ASSERTIONS PASSED, byte-stable).

**The 22 merge-candidate decisions** recorded in `teacher_decisions_rc_v2.json` (schema-valid; both uids per pair; copy-B preferred survivor; explicit NOT-a-merge-authorization; copy-A rows: zero review entries, zero intersection with the log — Codex-proven). rc_v1 + Grok draft byte-locked history.

**The lossless merge proposal** (`inventory/merge-proposal-5-4/`, PROPOSAL — NOT EXECUTED): survivor/alias per pair; copy-A confirmed a **strict field-subset** in all 22 pairs (q44's malformed table shown honestly; q41 notation-only); full reference sweep (accuracy Codex-verified); q45's old queue-heuristic disagreement disclosed. Codex R2b caught two design defects **before execution could**: the v1 tombstone would have broken the dedup-map generator's top-level identity recomputation, and byte-for-byte rollback wasn't actually encoded. Fixed as v2: additive top-level markers (empirically proven — a tombstoned scratch registry regenerates a **byte-identical** alias map `be4b507b…`), raw-line byte captures with terminator fidelity (whole-line rollback empirically reproduces registry `b7f9a040…` exactly), A→B resolver contract + six machine-checkable post-merge invariants.

**Codex verdicts (gpt-5.6-sol):** R1 recording/resolver/regeneration — all PASS (2 side findings fixed: audit 3(f), doc-state sweep) · R2a rc_v2 fidelity — SHIP zero findings · R2b merge proposal — 2 defects found and closed with empirical proofs. Suites 161 + 12 green; audit passes; all five locks intact; AP Stats boundary fully honored.

**AT THE MERGE-APPROVAL GATE:** the corrected proposal awaits RC's separate authorization. Nothing merges until then.

## 18. NT11 — THE MERGE, EXECUTED (RC-authorized) — ALL GATES + 4 CODEX REVIEWS RESOLVED, UNCOMMITTED (2026-07-23)

**The program's first registry mutation, executed exactly within RC's authorization** (`RC_MERGE_AUTHORIZATION.json`, `9ab0efa5…`, immutable; referenced by every tombstone; one execution timestamp 2026-07-23T00:53:21-04:00).

**Executed state:** registry `b7f9a040` → `a2fe2782` — 900 lines, exactly 22 v2 tombstones at the proposal's line numbers (Codex review A verified ALL 900 lines: the other 878 byte-identical, every tombstone lossless with exactly the 4 markers, registry-wide rollback reproduces `b7f9a040` byte-for-byte — SHIP, zero findings). Alias map `be4b507b` → `27b8c13b` (22 `resolved_alias` entries; raw ambiguous calc unchanged: 85 = 22 resolved + 63 unresolved). All consumers regenerated with **dual denominators everywhere: 900 raw = 878 active + 22 alias** (wave plan, base inventory, dashboard, console, audit, `qb.stats`). Gates I1–I7 + four proofs + the 29-file full-operation rollback drill: PASS. The 39 VERIFIED records all bind survivors and remain verified; 39 promotion proposals UNAPPLIED and valid; historical artifacts byte-identical.

**Codex round (all four resolved):** A SHIP zero findings · B two validator hardenings (global cross-group one-hop enforcement + `-O`-proof guards; shipped map byte-identical throughout) · C the round's sharpest catch — `get_for_packet` had broken the 63 unresolved-ambiguous ids (reachable from legacy builders); fixed to two-regime behavior (deliberate resolution ONLY for merged groups; 63/63 pre-merge equivalence proven against a hash-verified sandbox) + console now renders MERGED resolution and locks the 22 executed pairs out of new exports · D durable coverage — new `test_merge_semantics_5_4.py` (29 tests: selector semantics, global one-hop fixtures, historical lookup, dual denominators, console exclusion) + the change-sweep now FAILS on unlisted paths backed by a frozen 296-entry hash manifest (closing git's untracked-`inventory/` blind spot; it caught Fable's own transient pycache byproducts during final verification — working as designed).

**Process deviations disclosed:** qb.py entered scope mid-flight with post-hoc CRITICAL impact analysis (compensated, then adversarially re-reviewed by Codex C which found the real residual defect — now fixed); console_template.html's Stage-0 LOCKED designation legitimately superseded by the authorized C2 fix (operation delta reconciled to 24 modified + 2 new, all bundle-covered).

**Final battery (Fable-verified):** dok-review 161 OK · cross-consumer 12 · audit ALL ASSERTIONS · durable 27+2 (sweep-on: 29/29) · locks: review log 39 (`4b61fd3b`), approval entry, all teacher exports, course map, TE comparison, collision queue, RC record — intact · **NO COMMIT** (HEAD `314affe`). Full rollback authority preserved independently (scratchpad `nt11_preservation/` + 29-pre-image bundle).

**AT THE PRE-COMMIT GATE:** the merge is executed, verified, and reversible; the working tree awaits RC's commit decision.

## 14. RC APPROVAL OF RUBRIC v0.2 — EXECUTED 2026-07-20T19:06:13-04:00

RC approved DOK Acceptance Rubric v0.2 effective immediately and directed the bounded approval act. Executed by Fable exactly as instructed: **one** approval entry `{"version": "v0.2", "approved_at": "2026-07-20T19:06:13-04:00"}` added to `tools/dok-review/rubric_approvals.json`; `_comment` byte-identical; keys unchanged; verified through the tool's own `load_rubric_approvals` (returns v0.2, offset-aware, no poisoning). Manifest hash `c63cbcf9…` → `1279d8ca…`. **Nothing else done, per RC's bounds:** no review entries (log still absent), no artifact regeneration, no promotion, registry byte-identical (`b7f9a040…`), both decision exports byte-identical. Per the no-retroactivity rule, only reviews recorded after 19:06:13-04:00 can ever qualify as verified; nothing is verified today. Known cosmetic lag (procedure-named, deliberately not run as part of the act): console/rubric-doc copy still reads AWAITING APPROVAL until their named artifact refreshes. **Next priority (RC):** obtain/transcribe the Lesson 5-4 TE item-analysis table (Practice #21–39, 41, 44, 45) into `questionbank/calibration/5-4.json` — the single source that unlocks the 22 DOK conflicts. The Step-3 regeneration procedure activates only when post-approval reviews create actual verified items.

---
*I will continue all local work that needs no teacher judgment and ask only where a decision changes pedagogy, grading, source interpretation, or external systems.*
