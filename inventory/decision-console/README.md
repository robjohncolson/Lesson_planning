# NT3 Teacher Decision Console

Decision-compression tranche for the questionbank inventory work (NT3). The console **presents evidence and records teacher choices — it makes no pedagogical decisions itself.** Every judgment call (revive vs. retire, which DOK label is authoritative, which figure is acceptable, whether the rubric is approved) is made by the teacher, in the console, and captured as a proposal.

## How to open

Double-click `TEACHER_DECISION_CONSOLE.html`. It is self-contained — zero external references (no CDN, no fonts, no network calls) — and works fully offline from a `file://` URL.

## How to (re)build

```
python build_console.py
```

Run from `inventory/decision-console/`. The builder derives everything from read-only sources and does not write to any of them:

- `questionbank/registry.jsonl`
- `inventory/dok-workflow/dok_wave_plan.json`
- `inventory/course-map/course_map.json`
- `inventory/dedup/item_uid_alias_map.json`
- `inventory/dashboard/content_readiness.json`
- `inventory/visuals/visual_asset_classification.json`
- `inventory/topic-4-1/*`
- `inventory/tikz-staging/*`

Before rendering, the builder guard-asserts frozen sha256 hashes and locked counts against these sources, so a silent upstream edit fails the build instead of silently reshaping the console. It then renders the 64 staged figure PDFs to `thumbnails/` via `pdftoppm` (falling back to Ghostscript if `pdftoppm` is unavailable) and embeds them as data-URIs directly into the generated HTML — the shipped page carries its own copies and does not read `thumbnails/` at runtime.

## The six sections

1. **4-1 revive vs. retire** — evidence for reviving or retiring Lesson 4-1 content, with a clearly-labeled architect recommendation (confidence 0.7) kept visually separate from the neutral evidence.
2. **DOK-conflict pairs** — 22 pairs of registry rows that disagree on DOK level, shown side-by-side, with four equally-weighted actions per pair; `5-4-savvas-q41` is the sole DOK 2-vs-3 conflict (all others disagree on a different DOK combination).
3. **Figure contact sheet** — a contact sheet of all 64 staged figures, with the 2 teacher-flagged figures isolated at the top for separate review, and the 2 held + 5 no-asset rows listed explicitly so the full 71-id partition is visible at a glance.
4. **Essential missing visuals** — the 14 registry items whose visual is essential but absent, each needing the original Savvas source PDF before it can be resolved.
5. **DOK acceptance rubric v0.2 — APPROVED 2026-07-20T19:06:13-04:00** (v0.1: request-changes by RC 2026-07-20) — RC's five-rule authority hierarchy (`DOK_RUBRIC_v0.2.md`), the surviving v0.1 mechanics, and a not-recorded Wave-0 worked sample for calibration. The approval is recorded as a manifest entry in `tools/dok-review/rubric_approvals.json`; verification is active for review-log entries recorded at or after that approval, but zero have been recorded so far, so nothing is yet marked **verified** — this applies to the rubric, the console, and every downstream artifact.
6. **Export** — the machine-readable decisions export described below.

## Decision flow

```
console controls  →  in-page state  →  "Export decisions"
      →  teacher_decisions.json   (validates against decisions_export.schema.json)
      →  LATER, SEPARATE, TEACHER-GATED application step
      →  proposes changes to questionbank/registry.jsonl
      →  the registry is only ever written by its own gated tooling
         (qb_append.py / dok-review promote proposals) — never by this
         console and never by the export file itself
```

**Nothing in this console or its export writes `questionbank/registry.jsonl` or any other source file.** The export is proposals only. Turning a proposal into an actual registry change is a distinct, later, teacher-gated step that happens outside this console.

If the download fails (e.g. `Blob`/`file://` restrictions in some browsers), the console falls back to a copy-to-clipboard textarea containing the same JSON.

**Recorded RC decisions (Section 3) are seeded, shown, and excluded from new exports, not re-litigated.** `build_console.py` optionally reads `teacher_decisions_rc_v1.json` (read-only, same directory) and, for any Section-3 figure decision it already contains, attaches `recorded_context` to that row. The console renders that as display/counter state only — never as a new decision this session made: the nav counter and the "Unanswered decisions" count both report `recorded in rc_v1: N` separately from `decisions made` / `pending`, the row's own controls stay disabled, and `buildExportObject()` explicitly skips every recorded decision so a new export never re-includes a confirmation that already lives in `teacher_decisions_rc_v1.json`. Re-deciding one of those 2 confirmations requires producing a new export revision (editing `teacher_decisions_rc_v1.json` or the downstream promotion step) — this console does not offer an in-page way to un-record them. If `teacher_decisions_rc_v1.json` is absent, the builder degrades cleanly: no row carries `recorded_context`, nothing is excluded, and the counters behave exactly as before (all Section-3 decisions pending).

## Identity: item_uid vs. legacy id

All decisions key on **`item_uid`** — the only valid identity key in this system. Legacy/bank ids (e.g. `5-4-savvas-q41`) are **display-only**: 85 legacy ids are shared by two separate registry rows, so a legacy id alone cannot disambiguate a decision target. `decisions_export.schema.json` enforces this: `target_item_uids` entries must match the opaque uid pattern `^iu_[0-9a-f]{12}$`, so a legacy id submitted directly fails validation rather than silently passing. See `inventory/dedup/item_uid_alias_map.json` for the id-to-uid mapping — 4 staged-figure legacy ids there are themselves ambiguous (`5-1-savvas-q45`, `5-1-savvas-q48`, `5-4-savvas-q44`, `5-5-savvas-q36`), which is what the schema's `params.target_ambiguous` flag is for: both candidate uids go in `target_item_uids` and the flag records that the alias was ambiguous rather than one uid being silently pinned.

## Files in this directory

- `decisions_export.schema.json` — JSON Schema (draft 2020-12) for `teacher_decisions.json`.
- `teacher_decisions.template.json` — blank scaffold matching that schema; the console fills and downloads this shape.
- `thumbnails/` — build intermediates (rendered PDF → image files) produced by `build_console.py`. Not read at runtime; the shipped HTML embeds its own copies as data-URIs.
