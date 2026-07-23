# Owned-Path Matrix — parallel-workstream coordination policy

**Adopted 2026-07-19** after a namespace collision (two parallel workstreams shared
`Lesson_planning/inventory/`; one manager's cleanup deleted the other's legitimate
artifacts). Fable (head architect) owns this policy.

## Rules

1. **Every workstream is assigned an explicit OWNED PATH namespace before dispatch.**
   A workstream may create/edit/delete files ONLY within its owned namespace.
2. **No workstream may delete or "clean up" files outside its owned namespace** —
   not even files that look like scope-drift. If a workstream sees stray files it
   believes are wrong, it REPORTS them to Fable; it does not remove them.
3. **Shared-directory integration is Fable's job, performed AFTER the relevant
   managers finish** — never by a workstream mid-flight.
4. **Runner/byproduct artifacts** (`.git`, `.agents`, `state/`, `node_modules`,
   `__pycache__`, `.tmp`) are swept by Fable at integration, not by workstreams.
5. **Direct-report exception:** a Sonnet implementer that cannot resolve its Opus
   manager's agent id may report to Fable (main); Fable then forwards the report to
   the Opus manager for explicit re-verification/sign-off. The hierarchy
   (Fable synthesizes · Opus manages/verifies · Sonnet implements · Codex reviews)
   is preserved — the manager's sign-off is still required.

## Current namespaces

| Workstream | Owned path(s) | Manager |
|---|---|---|
| OCR/DOK content-readiness inventory | `Lesson_planning/inventory/` **excluding** `inventory/dedup/` | Opus |
| Duplicate-ID / item-UID remediation | `Lesson_planning/inventory/dedup/` | Opus |
| Canonical course-model fixtures + round-trip | `algebra2-platform/packages/course-model/` | Opus |
| identity-ledger item_uid contract consistency | `algebra2-platform/services/identity-ledger/src/server.js`, `.../src/validate-item-uid.js` (new), `.../test/server.test.mjs` | Opus |
| WS1 — Topic 4-1 stranded-ingest diagnosis + recovery plan | `Lesson_planning/inventory/topic-4-1/` | Opus |
| WS2 — visual-asset classification + broken-path repair prep | `Lesson_planning/inventory/visuals/` | Opus |
| WS3 — legacy-ID collision human-review queue | `Lesson_planning/inventory/review-queue/` (reads `inventory/dedup/` read-only) | Opus |
| WS4 — DOK verification workflow + review-interface design | `Lesson_planning/inventory/dok-workflow/` | Opus |
| WS5 — OCR inventory → topic/lesson/prereq/pacing map | `Lesson_planning/inventory/course-map/` | Opus |
| WS6 — content-readiness dashboard/spec (held until WS1–5 report) | `Lesson_planning/inventory/dashboard/` | Opus |
| NT1 — DOK review tool (per REVIEW_INTERFACE_SPEC, item_uid-keyed) | `Lesson_planning/tools/dok-review/` (reads `inventory/dok-workflow/` read-only) | Opus |
| NT2 — TikZ figure regeneration (75 regenerable visuals → STAGING, no student-facing change) | `Lesson_planning/inventory/tikz-staging/` (reads `inventory/visuals/`, `questionbank/registry.jsonl` read-only) | Opus |
| NT3 — Teacher Decision Console (decision-compression; proposals only, no registry mutation) | `Lesson_planning/inventory/decision-console/` (reads registry, dok-workflow, course-map, dashboard, visuals, tikz-staging, topic-4-1, review-queue, dedup — ALL read-only) | Opus |
| NT4 — RC revised export + rubric v0.2 + console zoom (NT3 closed; namespace reassigned). `teacher_decisions.json` (Grok draft, sha256 782aa051…) is PRESERVED byte-identical | `Lesson_planning/inventory/decision-console/` | Opus |
| NT5 — match_quality:none provenance audit (local-only; no live DB / AP Stats) | `Lesson_planning/inventory/provenance-audit/` (all sources read-only) | Opus |
| NT6 — dok-review tool ↔ rubric v0.2 semantic alignment (NT1 closed; namespace reassigned). Synthetic logs only; no registry mutation | `Lesson_planning/tools/dok-review/` + status-annotation-only edits to `inventory/decision-console/DOK_RUBRIC_v0.2.md` (reads rubric/wave plan/alias map read-only) | Opus |
| NT7 — semantic propagation: specs+generator → canonical projection; dependent rebuilds (WS4/WS6/NT4 namespaces reassigned; wave plan hash 5d3ff312 SUPERSEDED by this tranche). `tools/dok-review/` READ-ONLY (import-only; minimal export shim allowed with justification). Manifest stays empty; no real review log; registry byte-locked | `Lesson_planning/inventory/dok-workflow/` + `inventory/dashboard/` + `inventory/decision-console/` (rebuild + hash re-pin only, Grok draft + rc_v1 byte-locked) | Opus |
| NT7-R — remediation (Codex cross-consumer NEEDS-FIX): NAMESPACE EXPANSION — root inventory builder (`inventory/build_content_readiness_inventory.py` + `content_readiness_inventory.json`, CLOSED-since-tranche-1 status reassigned: it is the competing-predicate publisher) and `tools/dok-review/` (minimal: malformed-log fail-closed uniformity + disagreement-note enforcement + tests) now IN scope, plus all NT7 namespaces. Rubric doc: annotation-only. Same locks: registry, empty manifest, no real log, Grok draft + rc_v1 | NT7 paths + `inventory/{build_content_readiness_inventory.py, content_readiness_inventory.json}` + `tools/dok-review/` | Opus |
| NT8 — post-approval transition (RC approved v0.2 @ 2026-07-20T19:06:13-04:00; approval entry IMMUTABLE). Test hermeticity, current-state language APPROVED, zero-review regeneration. Rubric-doc status update now RC-AUTHORIZED. Locks: registry b7f9a040, Grok draft 782aa051, rc_v1 ad97b2ba, no real review log, no promotion | All NT7-R paths (tools/dok-review + dok-workflow + dashboard + decision-console + root inventory builder artifacts) | Opus |
| NT11 — MERGE EXECUTION (RC-authorized: RC_MERGE_AUTHORIZATION.json sha256 9ab0efa5…, 2026-07-23T00:48:13-04:00). FIRST registry mutation: v2 tombstones on exactly the 22 copy-A rows; copy-B byte-identical; resolved_alias enrichment; consumer updates to dual raw(900)/active(878) denominators. Manager defines disjoint sub-ownership (registry mutation / alias-map+resolver / consumer regeneration / verification). Pre-edit baseline + independent rollback payload preserved in scratchpad nt11_preservation/. Locks: authorization record + review log (39, 4b61fd3b) + approval entry + all teacher exports immutable; historical reports not rewritten; promotion proposals unapplied; return BEFORE any commit | `questionbank/registry.jsonl` (22 lines only) + `inventory/dedup/` + NT7-R consumer paths + `inventory/merge-proposal-5-4/` (wording fix + execution record) | Opus |
| NT10 — RC decision recording (39 batch confirmations → FIRST REAL review log; 22 pair-level merge-candidate decisions → rc_v2 export; regeneration + computed totals; promote = proposals-only; lossless merge PROPOSAL for the 22 pairs — NOT executed). Locks: registry b7f9a040 byte-locked; approval entry immutable; rc_v1 + Grok draft byte-locked (rc_v2 is a NEW file); no merge execution, no deletion, no renumbering | `tools/dok-review/` (log + possible resolver extension + test re-pins) + NT7-R regeneration paths + `inventory/decision-console/teacher_decisions_rc_v2.json` (new) + `inventory/merge-proposal-5-4/` (new) | Opus |
| NT9 — 5-4 TE transcription (§15a contract + RC source-sufficiency override 2026-07-22). Sources: calibration/sources/5-4_savvas_te_p258_{full_page,item_analysis_closeup}.png (af34c4d9…/273db411…, RC-approved provenance = page 258 + Topic 5/Lesson 4 identifiers; edition NOT independently re-confirmed — waived). WRITES: `questionbank/calibration/5-4.json` (item_analysis population — first RC-gated calibration write) + regeneration across NT7-R consumer paths + new comparison/proposal artifacts in `inventory/te-comparison-5-4/` (new). LOCKS: registry b7f9a040, approval entry immutable, drafts 782aa051/ad97b2ba, no review log, no promotion, no merge/conflict resolution, no OneDrive-original modification, copyrighted captures stay in private tree | `questionbank/calibration/5-4.json` + `inventory/te-comparison-5-4/` + NT7-R regeneration paths | Opus |

The content-readiness inventory root (`inventory/*.{json,md,py}`) and `inventory/dedup/`
are CLOSED, signed-off deliverables — no new workstream may modify them; WS3 reads
`inventory/dedup/` read-only. Registries (`questionbank/registry.jsonl`, `calibration/*`)
are preserved byte-for-byte by every workstream.

Any new parallel workstream MUST be given a disjoint owned path in this table
before it is dispatched.
