# DOK Acceptance Rubric v0.2

## v0.2 — APPROVED 2026-07-20T19:06:13-04:00

This rubric is APPROVED. The approval is recorded as a manifest entry —
`{"version": "v0.2", "approved_at": "2026-07-20T19:06:13-04:00"}` — hand-added to
`tools/dok-review/rubric_approvals.json` after the teacher exercised the console's Section 5
decision control. Verification under this rubric is active only for review-log entries whose
tool-stamped `recorded_at` is at or after that `approved_at` (no retroactive verification). Zero
review-log entries have been recorded under this rubric as of this writing, so the verified count
under it is 0 today; it rises only as real, post-approval reviews are recorded.

## Status context

- **v0.1-PROPOSED** received **request-changes by RC (2026-07-20)**. That decision is recorded in
  the RC export (`teacher_decisions_rc_v1.json`, decision `s5-rubric-v0.1`); it is not re-recorded
  here — this document only carries it forward as status context so the revision history is visible
  in one place.
- **v0.2-PROPOSED** (this document) is the requested revision. RC's request-changes note asked that
  the flat v0.1 criteria list be replaced by an explicit authority hierarchy; that hierarchy is the
  core of this document (below). v0.2 remains PROPOSED, awaiting a fresh teacher decision.
- **Status annotation (2026-07-20, NT6):** reopened as PROPOSED 2026-07-20; tool alignment in
  progress; approval not yet requested. `tools/dok-review/` is being aligned to this rubric's
  semantics (two-tier reviewed-vs-verified, verification gated on an approved-rubric-versions set
  that is deliberately EMPTY while this rubric is PROPOSED). The sentence under *Surviving v0.1
  mechanics* stating the tool "is NOT modified" described the state at v0.2 drafting time and is
  superseded by that alignment; the substance of this rubric is unchanged by the alignment, and
  nothing may be recorded as verified under it until a teacher approves it.
- **Status annotation (2026-07-20, NT6 remediation) — recording vs. verification:** this
  document's sentence "no review-log entry of any kind may be recorded under it" is read, for
  tooling purposes, as governing VERIFICATION standing, not the mere act of recording: the aligned
  tool permits recording review-log entries stamped with a proposed rubric version (they are
  reviews — working notes of a reviewer), while making verification under that version mechanically
  impossible until the version appears in the tool's approvals manifest with a teacher's
  approval date. Entries recorded before the approval date can never become verified
  (no retroactive verification); they must be re-reviewed after approval. This annotation
  clarifies status and tool behavior only; it does not amend the rubric's criteria, and no
  approval is requested or recorded by it.
- **Status annotation (2026-07-20, NT7-R):** this supersedes *Surviving v0.1 mechanics*' (below)
  "strict-AND verified predicate ... an entry counts only when BOTH `reviewed_by` AND
  `reviewed_at` are present" description, and its 15-field record-shape list (lines ~74–82,
  left unedited below) — the aligned tool's ACTUAL predicate is the two-tier `entry_is_verified`:
  a verification-grade disposition (a resolved rule-1 confirm, or a complete rule-3/rule-5
  change), an unresolved-needs-source-check veto, an approved `rubric_version`, and a
  tool-stamped `recorded_at` not earlier than that version's `approved_at` (no retroactivity) —
  strictly stronger than "reviewed_by AND reviewed_at present." The record shape now includes
  the full field set actually written by `tools/dok-review/dok_review.py`: `rubric_version`,
  `rationale`, `provenance`, `provenance_resolved`, `confirmation_basis`, `item_basis`,
  `resolves_source_check`, `prior_unresolved_nsc`, and `recorded_at`, in addition to the fifteen
  already listed. Status/description only — this annotation changes no criteria and requests or
  records no approval.
- **Status annotation (2026-07-20, NT8) — approval recorded:** a teacher approval of this rubric
  is now recorded as a manifest entry, `{"version": "v0.2", "approved_at":
  "2026-07-20T19:06:13-04:00"}`, hand-added to `tools/dok-review/rubric_approvals.json` per the
  approval procedure in `DOK_VERIFICATION_WORKFLOW.md`. The present-tense "remains PROPOSED" /
  "awaiting a fresh teacher decision" / "AWAITING TEACHER APPROVAL" phrasing in the status-context
  bullets above (and in the header line this document carried before this annotation) is superseded
  as of that timestamp; it is left in place unedited as historical context, per this document's own
  established pattern of superseding a bullet's substance without deleting it. No-retroactivity
  still governs what this approval actually unlocks: no review-log entry recorded before
  `approved_at` can ever become verified under this version, and since zero entries were recorded
  before this approval, the verified count under v0.2 remains 0 today — it rises only as real
  reviews are recorded after this timestamp.

## Authority hierarchy

DOK determinations for every item in the registry are governed by exactly one of the following five
rules. Where more than one could plausibly apply, the earlier-numbered rule controls.

1. **Confirmed textbook DOK governs exact, unchanged textbook items.** If an item is taken from the
   textbook (or its Teacher Edition) without modification, and its DOK label traces cleanly to that
   source, the confirmed textbook DOK stands — it is not re-litigated by a reviewer's independent
   judgment.
2. **Conflicting or provenance-missing textbook labels remain UNRESOLVED pending source
   verification.** If a textbook item's DOK label is contested (e.g. two registry copies disagree)
   or its provenance cannot be traced to a specific textbook source, no DOK is accepted as confirmed.
   The item is held as UNRESOLVED until source verification — checking the original textbook/Teacher
   Edition material — settles the question.
3. **Adapted, split, extended, and teacher-authored items are rated by their actual cognitive
   demand.** Once an item has been changed from its original textbook form — adapted, split into
   parts, extended, or written by the teacher — it no longer inherits a textbook-confirmed label.
   Its DOK is set by evaluating what the item actually asks a student to do.
4. **DOK measures cognitive demand, not difficulty.** A long, multi-part, or context-heavy item is
   not automatically higher DOK than a short one, and a computationally hard item is not
   automatically higher DOK than an easy one. DOK tracks the kind of thinking required (recall vs.
   procedure vs. strategic reasoning vs. extended investigation), never how hard, how long, or how
   error-prone the item is to complete.
5. **Any teacher override requires rationale and provenance.** A teacher may override any DOK
   produced by rules 1–4, but the override must be accompanied by both a rationale (why the
   reviewer's judgment differs) and provenance (what source or reasoning the override rests on). An
   override with rationale but no provenance, or provenance but no rationale, is incomplete.

## Surviving v0.1 mechanics

These operational mechanics carried forward from v0.1 unchanged — the hierarchy above governs *what
DOK gets assigned*; these mechanics govern *how the assignment is recorded*:

- Every review-log entry still requires: reviewer id, ISO 8601 timestamp, a disposition of
  `confirm` / `change+new-DOK` / `needs-source-check`, a chosen DOK (only when disposition is
  `change+new-DOK`), a rationale note required on every disagreement, and `rubric_version` recorded
  on every future log entry.
- The strict-AND verified predicate, as already implemented in
  `tools/dok-review/dok_review.py::entry_is_verified` — an entry counts only when BOTH `reviewed_by`
  AND `reviewed_at` are present — remains the tool's existing mechanism for this determination. That
  tool is NOT modified by this rubric or by this console. No entry may be recorded under this rubric
  until the rubric itself is approved by the teacher.
- Continued consistency with `tools/dok-review`'s append-only `review_log.jsonl` record shape:
  `{item_uid, registry_line, item_id, lesson, reviewed_by, reviewed_at, prior_dok, reviewer_dok,
  current_dok, new_dok, decision, te_bucket, match_quality, disagreement_resolved, note}`.

## v0.1 → v0.2 mapping

Every v0.1 criterion is accounted for below. None is silently dropped.

| # | v0.1 criterion (verbatim) | v0.2 disposition | Rationale |
|---|---|---|---|
| 1 | "TE cross-check where available (te_bucket + match_quality from the wave plan)" | **Subsumed** as an evidence input under hierarchy rules 1–2 | TE cross-check is no longer a standalone criterion; it becomes one way of establishing or refuting a textbook label's provenance — corroborating evidence feeds rule 1 (confirms the textbook DOK), a mismatch or absence feeds rule 2 (provenance-missing / UNRESOLVED pending source verification). |
| 2 | "Reviewer id + ISO timestamp on every entry" | **Kept** verbatim (mechanics) | Pure record-keeping requirement, independent of which hierarchy rule produced the DOK. Carried forward unchanged under "Surviving v0.1 mechanics" above. |
| 3 | "Disposition: confirm / change+new-DOK / needs-source-check" | **Kept** verbatim (mechanics) | The three-way disposition vocabulary still describes every possible reviewer action regardless of which rule (1–5) governed the item; unaffected by the move to a hierarchy. |
| 4 | "Rationale note REQUIRED on every disagreement (any change, any needs-source-check, any TE-bucket mismatch)" | **Kept, and strengthened** by hierarchy rule 5 | v0.1 already required a note on every disagreement. Rule 5 extends this specifically for teacher overrides: an override now needs both rationale (why the reviewer disagrees) and provenance (what it rests on) — provenance is new; rationale is the same requirement carried forward. |
| 5 | "rubric_version recorded on every log entry" | **Kept** verbatim (mechanics) | Every future log entry still stamps which rubric version produced it, which is what makes the v0.1 → v0.2 (and any future) transition auditable. Unaffected by the hierarchy's content. |

---

*Pointer for reviewers: this document is the source of record for the DOK Acceptance Rubric.
`inventory/decision-console/TEACHER_DECISION_CONSOLE.html` Section 5 presents a summary of it plus
a not-recorded Wave-0 worked illustration; the console does not restate this document's full
prose and is not itself an approval mechanism until the teacher exercises its decision control.*
