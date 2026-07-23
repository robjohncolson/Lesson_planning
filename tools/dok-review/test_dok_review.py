"""Tests for dok_review.py (DOK Acceptance Rubric v0.2 -- two-tier model,
NT6 remediation round 2: rubric-approvals manifest, on-disk provenance
resolution, timestamp integrity, invalid-entry state, promotion hardening,
item_basis + NSC attestation).

All tests operate on COPIES of the real (frozen) inventory/dok-workflow/
dok_wave_plan.json, questionbank/registry.jsonl, and questionbank/calibration/
inside a fresh tempfile.TemporaryDirectory(), and always point
--plan/--registry/--calibration-dir/--log at paths inside that same temp
directory. The real review_log.jsonl and the real rubric_approvals.json are
NEVER created, written, or otherwise touched by this suite; no source file
(real or copied) is ever opened in a write mode by the tool.

DOK rubric v0.2 is now APPROVED (approved_at 2026-07-20T19:06:13-04:00) --
the REAL, shipped tools/dok-review/rubric_approvals.json has exactly that
one entry. This suite is nonetheless fully HERMETIC: no test reads that
ambient real file. `DokReviewTestBase.setUp()` writes an explicit, EMPTY
(unapproved) temp manifest (`self.approvals_path`) and `run_cli()` always
passes `--approvals` pointing at it, so the CLI path never sees the real
manifest either. Tests that need to see the VERIFIED tier "unlock" do so by
passing `_approved_versions_override=` (a dict of
{version: datetime-or-ISO-string}) directly to the verification-aware
functions, or by pointing `dr.load_rubric_approvals()` at a hand-written
TEMP manifest file -- never by reading the real manifest or mutating a
module constant (there is no longer a module constant to mutate:
APPROVED_RUBRIC_VERSIONS was removed by an earlier round of fixes). The
ONE exception is `TestRealManifestIntegrationOnly`, a standalone,
explicitly-marked integration test that deliberately reads the real
manifest to confirm it actually ships the expected approval.

DokReviewTestBase's setUp() copies the real questionbank/calibration/ tree
into the temp dir and then, for EVERY item in the (temp-copied) wave plan
that has a derivable calibration identity (NT6 round 3, G1 --
dr.derive_item_calibration_identity), makes sure its own temp calibration
file actually contains a matching entry -- injecting one only if the real,
ingested calibration file doesn't already have it (a TEMP-COPY-ONLY
mutation; the real calibration files are never touched). This replaces the
old blanket "test-anchor" key: resolve_provenance() is now item-bound, so a
provenance ref only resolves when it identifies the SAME item being
reviewed -- a generic key that any lesson/any item could cite no longer
means anything. `resolving_provenance_for(uid)` builds a ref matching that
item's OWN identity (its own practice/example number), so it resolves
deterministically for any item_uid in the plan with a derivable identity,
without depending on which lessons happen to have real Savvas anchors
ingested yet.

Run with:  python -B -m unittest test_dok_review -v
   (or)    python -B test_dok_review.py
"""

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dok_review as dr  # noqa: E402


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _has_matching_practice_anchor(anchors, n):
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        source = anchor.get("source")
        if not isinstance(source, str):
            continue
        match = dr._PRACTICE_SOURCE_RE.search(source)
        if match and int(match.group(1)) == n:
            return True
    return False


def _inject_identity_matched_fixtures(plan, calibration_dir):
    """TEMP-COPY-ONLY fixture helper (NT6 round 3, G1 rewrite).
    resolve_provenance() is now item-bound: a provenance ref only resolves
    when it identifies the SAME item being reviewed (see
    dr.derive_item_calibration_identity / dr.resolve_provenance). The old
    blanket "test-anchor" key (any lesson, any item) no longer means
    anything under this model.

    Instead: for EVERY item in `plan` that has a derivable calibration
    identity, make sure its OWN temp calibration file actually contains a
    matching entry -- an `item_analysis` key for an "example" identity, or a
    "Practice #N (test fixture)" anchor for a "practice" identity -- only
    injecting one if the real, ingested calibration file doesn't already
    have it. This lets `resolving_provenance_for(uid)` build a ref that
    resolves for ANY item_uid in the plan with a derivable identity, without
    depending on which lessons happen to have real Savvas anchors ingested.
    Items with no derivable identity (try-it, lesson-quiz, TE-slug ids) get
    nothing injected -- they are correctly never resolvable via
    calibration-anchor provenance, matching production behavior exactly.
    Never touches the real questionbank/calibration/.
    """
    calibration_dir = Path(calibration_dir)
    needed_by_lesson = {}
    for _wave, lesson, item in dr.iter_queue_items(plan):
        identity = dr.derive_item_calibration_identity(item)
        if identity is None:
            continue
        needed_by_lesson.setdefault(lesson, set()).add(identity)

    for lesson, identities in needed_by_lesson.items():
        path = calibration_dir / f"{lesson}.json"
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        item_analysis = data.get("item_analysis")
        if not isinstance(item_analysis, dict):
            item_analysis = {}
        dok3_anchors = data.get("dok3_anchors")
        if not isinstance(dok3_anchors, list):
            dok3_anchors = []

        for kind, n in identities:
            if kind == "example":
                key = f"example_{n}"
                if key not in item_analysis:
                    item_analysis[key] = {"dok2": [], "dok3": []}
            elif not _has_matching_practice_anchor(dok3_anchors, n):
                dok3_anchors.append(
                    {"source": f"Practice #{n} (test fixture, lesson {lesson})"}
                )

        data["item_analysis"] = item_analysis
        data["dok3_anchors"] = dok3_anchors
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)


FAR_PAST_APPROVAL = "2000-01-01T00:00:00+00:00"  # safe "approved long ago" anchor


class DokReviewTestBase(unittest.TestCase):
    """Copies the real frozen inputs (plan, registry, calibration/) into a
    temp dir so no test ever reads or writes the real repo files, and never
    touches the real rubric_approvals.json."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        tmp = Path(self.tmpdir.name)

        self.plan_path = tmp / "dok_wave_plan.json"
        self.registry_path = tmp / "registry.jsonl"
        self.calibration_dir = tmp / "calibration"
        shutil.copy2(dr.DEFAULT_PLAN, self.plan_path)
        shutil.copy2(dr.DEFAULT_REGISTRY, self.registry_path)
        shutil.copytree(dr.DEFAULT_CALIBRATION_DIR, self.calibration_dir)

        # Deliberately NOT created here -- a missing log means "no reviews
        # yet". Only `review` (via append_review) should ever create it.
        self.log_path = tmp / "review_log.jsonl"
        self.proposals_dir = tmp / "proposals"
        self.report_path = tmp / "review_report.html"

        # Hermetic rubric-approvals fixture: an explicit, EMPTY (unapproved)
        # temp manifest. The real tools/dok-review/rubric_approvals.json now
        # ships with one real approval (v0.2) -- no unit test may read that
        # ambient file; every test that needs "unapproved" behavior gets it
        # from THIS fixture (via run_cli()'s --approvals below, or by
        # passing approvals_path=self.approvals_path / an explicit
        # _approved_versions_override directly to a library call).
        self.approvals_path = tmp / "rubric_approvals.json"
        with open(self.approvals_path, "w", encoding="utf-8") as f:
            json.dump(
                {"_comment": "test fixture -- EMPTY manifest (unapproved state)", "approvals": []},
                f,
            )

        self.plan = dr.load_plan(self.plan_path)
        # Must run AFTER self.plan is loaded -- it needs the plan's items to
        # know which calibration identities to inject (NT6 round 3, G1).
        _inject_identity_matched_fixtures(self.plan, self.calibration_dir)

    def run_cli(self, *sub_args):
        """Invoke dok_review.main() with the temp-dir global paths plus the
        given subcommand args. --calibration-dir always points at the temp
        copy -- the real questionbank/calibration/ is never passed to a
        write-capable code path. --approvals always points at the temp,
        EMPTY manifest fixture -- the real rubric_approvals.json (which now
        has v0.2 approved) is never read by the CLI path either."""
        dr.main([
            "--plan", str(self.plan_path),
            "--registry", str(self.registry_path),
            "--calibration-dir", str(self.calibration_dir),
            "--log", str(self.log_path),
            "--approvals", str(self.approvals_path),
            *sub_args,
        ])

    def resolving_provenance_for(self, uid):
        """Build a --provenance string that resolves as THIS item's OWN
        rule-1 anchor, under the item-bound resolve_provenance() model (NT6
        round 3, G1). Only valid for a uid with a derivable calibration
        identity -- see _inject_identity_matched_fixtures, which guarantees
        the temp calibration fixture for that item's lesson actually
        contains a matching entry."""
        uid_to_item, _uid_to_line, _duplicates = dr.build_uid_index(self.plan)
        item = uid_to_item[uid]
        identity = dr.derive_item_calibration_identity(item)
        assert identity is not None, (
            f"{uid} (id={item['id']!r}) has no derivable calibration identity -- "
            "resolving_provenance_for() cannot build a resolving ref for it"
        )
        kind, n = identity
        ref = f"example_{n}" if kind == "example" else f"practice #{n}"
        return f"calibration-anchor:{item['lesson']}:{ref}"

    def prior_dok_for(self, uid):
        uid_to_item, _uid_to_line, _duplicates = dr.build_uid_index(self.plan)
        return uid_to_item[uid]["dok"]

    def a_different_dok(self, prior_dok):
        for candidate in (1, 2, 3):
            if candidate != prior_dok:
                return candidate
        raise AssertionError("no alternate DOK value available")  # pragma: no cover

    def log_bytes_or_none(self):
        return self.log_path.read_bytes() if self.log_path.exists() else None

    def assert_log_unchanged(self, before):
        if before is None:
            self.assertFalse(self.log_path.exists(), "log must not have been created")
        else:
            self.assertTrue(self.log_path.exists())
            self.assertEqual(self.log_path.read_bytes(), before, "log bytes must be unchanged")

    def latest_for(self, uid):
        entries = dr.read_log_entries(self.log_path)
        return dr.latest_entries_by_uid(entries).get(uid)

    def write_manifest(self, approvals):
        """Write a hand-crafted rubric_approvals.json-shaped file to a TEMP
        path (never the real tools/dok-review/rubric_approvals.json) and
        return its path. `approvals` is whatever should go under that key."""
        path = Path(self.tmpdir.name) / "test_rubric_approvals.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"_comment": "test fixture", "approvals": approvals}, f)
        return path

    def craft_log_lines(self, lines):
        """Write raw dicts directly to self.log_path, one JSON object per
        line, bypassing the CLI/append_review entirely -- for crafted-log
        promotion tests that need to hand-construct a malformed entry."""
        with open(self.log_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(json.dumps(line, ensure_ascii=False))
                f.write("\n")


# ---------------------------------------------------------------------------
# 1. item_uid keying / q41 independence (preserved intent, updated CLI).
# ---------------------------------------------------------------------------

class TestUidKeyingQ41Independence(DokReviewTestBase):
    UID_WAVE3 = "iu_3c70a19c8d36"  # registry_line 328, dok 3, role dok3-driver, wave 3
    UID_WAVE4 = "iu_77d25e1e6131"  # registry_line 299, dok 2, role None,        wave 4
    LEGACY_ID = "5-4-savvas-q41"

    def test_legacy_id_lookup_is_ambiguous(self):
        id_index = dr.build_id_index(self.plan)
        uids = id_index[self.LEGACY_ID]
        self.assertEqual(len(uids), 2, "legacy id must be ambiguous (shared by 2 item_uids)")
        self.assertIn(self.UID_WAVE3, uids)
        self.assertIn(self.UID_WAVE4, uids)

    def test_prior_dok_values_are_distinct(self):
        uid_to_item, uid_to_line, duplicates = dr.build_uid_index(self.plan)
        self.assertEqual(duplicates, [])
        self.assertEqual(uid_to_item[self.UID_WAVE3]["dok"], 3)
        self.assertEqual(uid_to_item[self.UID_WAVE4]["dok"], 2)
        self.assertEqual(uid_to_line[self.UID_WAVE3], 328)
        self.assertEqual(uid_to_line[self.UID_WAVE4], 299)

    def test_independent_review_state_no_cross_credit(self):
        self.run_cli(
            "review", "--item-uid", self.UID_WAVE3,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", self.resolving_provenance_for(self.UID_WAVE3),
            "--rationale", "wave-3 copy matches the anchor",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T10:00:00-04:00",
        )
        self.run_cli(
            "review", "--item-uid", self.UID_WAVE4,
            "--reviewed-by", "lynn", "--disposition", "change",
            "--chosen-dok", "3", "--item-basis", "adapted",
            "--rationale", "wave-4 copy actually requires strategic reasoning",
            "--provenance", "reviewer judgment against DOKframework.txt rule 4",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T10:05:00-04:00",
        )

        entries = dr.read_log_entries(self.log_path)
        self.assertEqual(len(entries), 2)
        latest = dr.latest_entries_by_uid(entries)

        e3 = latest[self.UID_WAVE3]
        e4 = latest[self.UID_WAVE4]

        self.assertEqual(e3["decision"], "confirm")
        self.assertIsNone(e3["new_dok"])
        self.assertEqual(e3["prior_dok"], 3)
        self.assertEqual(e3["registry_line"], 328)

        self.assertEqual(e4["decision"], "change")
        self.assertEqual(e4["new_dok"], 3)
        self.assertEqual(e4["prior_dok"], 2)
        self.assertEqual(e4["registry_line"], 299)

        self.assertEqual(e3["item_id"], self.LEGACY_ID)
        self.assertEqual(e4["item_id"], self.LEGACY_ID)
        self.assertNotEqual(e3["decision"], e4["decision"])

        self.assertEqual(
            dr.tool_state_for(self.UID_WAVE3, latest, approvals_path=self.approvals_path), "reviewed_once",
        )
        self.assertEqual(
            dr.tool_state_for(self.UID_WAVE4, latest, approvals_path=self.approvals_path), "reviewed_once",
        )

        other_uid = "iu_3b42ab3340d5"
        self.assertEqual(
            dr.tool_state_for(other_uid, latest, approvals_path=self.approvals_path), "unreviewed",
        )


# ---------------------------------------------------------------------------
# 2. entry_is_verified: strict-AND + verification-grade disposition + nsc
#    veto + rubric-approval/retroactivity gate. Pure unit tests.
# ---------------------------------------------------------------------------

class TestEntryIsVerifiedPredicate(unittest.TestCase):
    APPROVED = {"v0.2": FAR_PAST_APPROVAL}

    def _base(self, **overrides):
        entry = {
            "reviewed_by": "lynn",
            "reviewed_at": "2026-07-19T10:00:00-04:00",
            "recorded_at": "2026-07-19T10:00:05-04:00",
            "rubric_version": "v0.2",
            "prior_unresolved_nsc": False,
        }
        entry.update(overrides)
        return entry

    def _confirm_entry(self, confirmation_basis, **overrides):
        return self._base(decision="confirm", confirmation_basis=confirmation_basis, **overrides)

    def _change_entry(self, new_dok=2, rationale="reviewer judgment", provenance="TE p.1",
                       item_basis="adapted", provenance_resolved=False, **overrides):
        return self._base(
            decision="change", new_dok=new_dok, rationale=rationale, provenance=provenance,
            item_basis=item_basis, provenance_resolved=provenance_resolved, **overrides
        )

    def _nsc_entry(self, **overrides):
        return self._base(decision="needs-source-check", **overrides)

    def test_reviewed_by_only(self):
        self.assertFalse(dr.entry_is_verified(
            {"reviewed_by": "lynn", "reviewed_at": ""}, _approved_versions_override={},
        ))

    def test_reviewed_at_only(self):
        self.assertFalse(dr.entry_is_verified(
            {"reviewed_by": "", "reviewed_at": "2026-07-19T10:00:00-04:00"}, _approved_versions_override={},
        ))

    def test_both_empty(self):
        self.assertFalse(dr.entry_is_verified({"reviewed_by": "", "reviewed_at": ""}, _approved_versions_override={}))

    def test_missing_keys(self):
        self.assertFalse(dr.entry_is_verified({}, _approved_versions_override={}))

    def test_unparseable_reviewed_at_never_verified(self):
        entry = self._confirm_entry("rule-1-textbook-provenance", reviewed_at="not-a-timestamp")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_legacy_shaped_entry_never_verified(self):
        entry = {"reviewed_by": "lynn", "reviewed_at": "2026-07-19T10:00:00-04:00"}
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_confirm_rule1_unapproved_not_verified(self):
        # Explicit empty-approvals state (hermetic -- never the ambient real
        # manifest, which now has v0.2 approved).
        entry = self._confirm_entry("rule-1-textbook-provenance")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override={}))

    def test_confirm_rule1_with_injected_approval_verified(self):
        entry = self._confirm_entry("rule-1-textbook-provenance")
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_confirm_rule2_unsourced_never_verified(self):
        entry = self._confirm_entry("rule-2-adjacent-unsourced")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_confirm_rule2_unsourced_claim_never_verified(self):
        entry = self._confirm_entry("rule-2-adjacent-unsourced-claim")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_change_adapted_free_text_with_approval_verified(self):
        entry = self._change_entry(item_basis="adapted", provenance_resolved=False)
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_change_missing_provenance_not_verified(self):
        entry = self._change_entry(provenance="")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_change_missing_rationale_not_verified(self):
        entry = self._change_entry(rationale="")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_change_invalid_new_dok_not_verified(self):
        entry = self._change_entry(new_dok=None)
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_change_missing_item_basis_not_verified(self):
        entry = self._change_entry(item_basis=None)
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_change_textbook_exact_without_resolved_provenance_not_verified(self):
        entry = self._change_entry(item_basis="textbook-exact", provenance_resolved=False)
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_change_textbook_exact_with_resolved_provenance_verified(self):
        entry = self._change_entry(item_basis="textbook-exact", provenance_resolved=True)
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_needs_source_check_never_verified_even_with_approval(self):
        entry = self._nsc_entry()
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_unapproved_rubric_version_string_not_verified(self):
        entry = self._confirm_entry("rule-1-textbook-provenance", rubric_version="v0.1")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_prior_unresolved_nsc_vetoes_otherwise_complete_change(self):
        entry = self._change_entry(item_basis="adapted", prior_unresolved_nsc=True)
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_prior_unresolved_nsc_vetoes_otherwise_complete_confirm(self):
        entry = self._confirm_entry("rule-1-textbook-provenance", prior_unresolved_nsc=True)
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_recorded_before_approval_not_verified(self):
        entry = self._confirm_entry("rule-1-textbook-provenance", recorded_at="2010-01-01T00:00:00+00:00")
        approved = {"v0.2": "2026-01-01T00:00:00+00:00"}  # approved AFTER this entry's recorded_at
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=approved))

    def test_recorded_at_missing_not_verified(self):
        entry = self._confirm_entry("rule-1-textbook-provenance")
        del entry["recorded_at"]
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))

    def test_recorded_at_unparseable_not_verified(self):
        entry = self._confirm_entry("rule-1-textbook-provenance", recorded_at="not-a-timestamp")
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=self.APPROVED))


# ---------------------------------------------------------------------------
# Reviewed-not-verified-by-default via the real CLI path.
# ---------------------------------------------------------------------------

class TestReviewedNotVerifiedByDefault(DokReviewTestBase):
    UID = "iu_3d5d21133498"  # wave 1

    def test_confirm_with_resolving_provenance_empty_manifest_fixture(self):
        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "matches the anchor",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T12:00:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "reviewed_once",
        )

        progress = dr.compute_progress(self.plan, self.log_path, approvals_path=self.approvals_path)
        self.assertEqual(progress["overall"]["verified"], 0)


# ---------------------------------------------------------------------------
# needs-source-check blocks verify AND promote (by itself, no attestation).
# ---------------------------------------------------------------------------

class TestNeedsSourceCheckBlocksVerifyAndPromote(DokReviewTestBase):
    UID = "iu_3c70a19c8d36"  # wave 3, q41 wave-3 copy, dok 3

    def test_nsc_blocks_both(self):
        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "needs-source-check",
            "--rationale", "cannot find this exact item in the TE",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T13:30:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        entry = latest[self.UID]

        self.assertEqual(entry["decision"], "needs-source-check")
        self.assertIsNone(entry["reviewer_dok"])
        self.assertIsNone(entry["new_dok"])

        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, _approved_versions_override={}), "reviewed_once",
        )
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=approved))

        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir, _approved_versions_override=approved,
            )
        self.assertIn("unresolved needs-source-check", str(cm.exception))

        out_path = self.proposals_dir / "promotion_nsc.json"
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("promote", "--item-uid", self.UID, "--out", str(out_path))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(out_path.exists())


# ---------------------------------------------------------------------------
# Invalid change rejected AT ENTRY, nothing appended.
# ---------------------------------------------------------------------------

class TestInvalidChangeRejectedAtEntry(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # wave 0, dok 3

    def test_missing_chosen_dok(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "change",
                "--item-basis", "adapted",
                "--rationale", "seems more procedural", "--provenance", "reviewer judgment",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:00:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_missing_rationale(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "change",
                "--chosen-dok", "2", "--item-basis", "adapted", "--provenance", "reviewer judgment",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:05:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_missing_provenance(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "change",
                "--chosen-dok", "2", "--item-basis", "adapted", "--rationale", "seems more procedural",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:10:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_whitespace_only_rationale_rejected(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "change",
                "--chosen-dok", "2", "--item-basis", "adapted", "--rationale", "   ",
                "--provenance", "reviewer judgment",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:11:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_missing_item_basis(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "change",
                "--chosen-dok", "2", "--rationale", "seems more procedural",
                "--provenance", "reviewer judgment",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:12:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)


# ---------------------------------------------------------------------------
# --chosen-dok 4 (argparse), confirm+chosen-dok, change==prior_dok, empty
# --reviewed-by.
# ---------------------------------------------------------------------------

class TestArgValidationRejections(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # wave 0, dok 3

    def test_chosen_dok_4_rejected_by_argparse(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "change",
                "--chosen-dok", "4", "--item-basis", "adapted", "--rationale", "x", "--provenance", "y",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:20:00-04:00",
            )
        self.assertEqual(ctx.exception.code, 2)  # argparse usage error, not our cmd_review exit(1)
        self.assert_log_unchanged(before)

    def test_chosen_dok_with_confirm_rejected(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "confirm",
                "--chosen-dok", "2",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:25:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_change_with_chosen_dok_equal_prior_rejected(self):
        prior = self.prior_dok_for(self.UID)
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "lynn", "--disposition", "change",
                "--chosen-dok", str(prior), "--item-basis", "adapted",
                "--rationale", "x", "--provenance", "y",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:30:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_empty_reviewed_by_rejected(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID,
                "--reviewed-by", "   ", "--disposition", "confirm",
                "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:35:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)


# ---------------------------------------------------------------------------
# confirm WITHOUT provenance -- rule-2-adjacent, never verified/promotable.
# ---------------------------------------------------------------------------

class TestConfirmWithoutProvenanceRuleTwoAdjacent(DokReviewTestBase):
    UID = "iu_e32a6f7f8909"  # wave 0

    def test_confirm_without_provenance_reviewed_but_never_verified(self):
        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T13:20:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        entry = latest[self.UID]

        self.assertEqual(entry["decision"], "confirm")
        self.assertEqual(entry["confirmation_basis"], "rule-2-adjacent-unsourced")

        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override={}))
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=approved))
        self.assertEqual(dr.tool_state_for(self.UID, latest, approved), "reviewed_once")

        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir, _approved_versions_override=approved,
            )
        msg = str(cm.exception)
        self.assertIn("lacks source provenance", msg)
        self.assertIn("not verification-grade", msg)

        out_path = self.proposals_dir / "promotion_unsourced.json"
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("promote", "--item-uid", self.UID, "--out", str(out_path))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(out_path.exists())


# ---------------------------------------------------------------------------
# rubric-unapproved blocks promotion of an otherwise-complete review.
# ---------------------------------------------------------------------------

class TestRubricUnapprovedBlocksPromotion(DokReviewTestBase):
    UID = "iu_3d5d21133498"  # wave 1

    def test_promote_fails_rubric_not_approved(self):
        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "confirmed against the anchor",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T13:10:00-04:00",
        )
        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir, approvals_path=self.approvals_path,
            )
        self.assertIn("rubric version not approved", str(cm.exception))

        out_path = self.proposals_dir / "promotion_unapproved.json"
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("promote", "--item-uid", self.UID, "--out", str(out_path))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(out_path.exists())


# ---------------------------------------------------------------------------
# Simulated approval unlocks verification (test-only override; hermetic
# empty-manifest fixture, never the ambient real manifest).
# ---------------------------------------------------------------------------

class TestSimulatedApprovalUnlocksVerification(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # wave 0, dok 3, registry_line 41

    def test_empty_manifest_fixture_yields_zero_approvals(self):
        self.assertEqual(dr.load_rubric_approvals(self.approvals_path), {})

    def test_injected_approval_unlocks_verified_and_promote(self):
        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "matches the anchor verbatim",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T13:00:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        entry = latest[self.UID]

        # Default (hermetic empty-manifest fixture): not verified.
        self.assertFalse(dr.entry_is_verified(entry, approvals_path=self.approvals_path))
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "reviewed_once",
        )

        # Simulated approval via a test-only override.
        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=approved))
        self.assertEqual(dr.tool_state_for(self.UID, latest, approved), "verified")

        progress_default = dr.compute_progress(self.plan, self.log_path, approvals_path=self.approvals_path)
        progress_approved = dr.compute_progress(self.plan, self.log_path, _approved_versions_override=approved)
        self.assertEqual(progress_default["overall"]["verified"], 0)
        self.assertEqual(progress_approved["overall"]["verified"], 1)

        proposal = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID,
            calibration_dir=self.calibration_dir, _approved_versions_override=approved,
        )
        out_path = self.proposals_dir / "promotion_approved.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(proposal, indent=2, ensure_ascii=False), encoding="utf-8")

        self.assertEqual(proposal["registry_written"], False)
        self.assertEqual(proposal["rubric_version"], "v0.2")
        self.assertIn("rationale", proposal)
        self.assertIn("provenance", proposal)
        self.assertIn("confirmation_basis", proposal)
        self.assertEqual(proposal["confirmation_basis"], "rule-1-textbook-provenance")

        # The CLI-level path (--approvals pointed at the same hermetic
        # empty-manifest fixture via run_cli()) still refuses.
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "promote", "--item-uid", self.UID,
                "--out", str(self.proposals_dir / "promotion_cli.json"),
            )
        self.assertNotEqual(ctx.exception.code, 0)


# ---------------------------------------------------------------------------
# q41 dual-copy isolation across the NEW states.
# ---------------------------------------------------------------------------

class TestQ41DualCopyIsolationNewStates(DokReviewTestBase):
    UID_WAVE3 = "iu_3c70a19c8d36"  # wave 3, prior dok 3 -- gets needs-source-check
    UID_WAVE4 = "iu_77d25e1e6131"  # wave 4, prior dok 2 -- gets confirm+resolving provenance
    LEGACY_ID = "5-4-savvas-q41"

    def test_independent_states_no_cross_credit(self):
        self.run_cli(
            "review", "--item-uid", self.UID_WAVE3,
            "--reviewed-by", "lynn", "--disposition", "needs-source-check",
            "--rationale", "wave-3 copy: provenance unclear, needs a check",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T15:00:00-04:00",
        )
        self.run_cli(
            "review", "--item-uid", self.UID_WAVE4,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", self.resolving_provenance_for(self.UID_WAVE4),
            "--rationale", "wave-4 copy checks out against the anchor",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T15:05:00-04:00",
        )

        entries = dr.read_log_entries(self.log_path)
        self.assertEqual(len(entries), 2)
        latest = dr.latest_entries_by_uid(entries)
        e3 = latest[self.UID_WAVE3]
        e4 = latest[self.UID_WAVE4]

        self.assertEqual(e3["item_id"], self.LEGACY_ID)
        self.assertEqual(e4["item_id"], self.LEGACY_ID)
        self.assertEqual(e3["decision"], "needs-source-check")
        self.assertEqual(e4["decision"], "confirm")

        self.assertEqual(
            dr.tool_state_for(self.UID_WAVE3, latest, approvals_path=self.approvals_path), "reviewed_once",
        )
        self.assertEqual(
            dr.tool_state_for(self.UID_WAVE4, latest, approvals_path=self.approvals_path), "reviewed_once",
        )

        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertEqual(dr.tool_state_for(self.UID_WAVE3, latest, approved), "reviewed_once")
        self.assertEqual(dr.tool_state_for(self.UID_WAVE4, latest, approved), "verified")

        with self.assertRaises(ValueError) as cm3:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID_WAVE3,
                calibration_dir=self.calibration_dir, _approved_versions_override=approved,
            )
        self.assertIn("unresolved needs-source-check", str(cm3.exception))

        # Explicit empty-manifest fixture -- intent is "unapproved state
        # blocks promotion", never the ambient real (now-approved) manifest.
        with self.assertRaises(ValueError) as cm4:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID_WAVE4,
                calibration_dir=self.calibration_dir, approvals_path=self.approvals_path,
            )
        self.assertIn("rubric version not approved", str(cm4.exception))

        proposal4 = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID_WAVE4,
            calibration_dir=self.calibration_dir, _approved_versions_override=approved,
        )
        self.assertEqual(proposal4["registry_written"], False)

        other_uid = "iu_3b42ab3340d5"
        self.assertEqual(
            dr.tool_state_for(other_uid, latest, approvals_path=self.approvals_path), "unreviewed",
        )


# ---------------------------------------------------------------------------
# append-only invariant, extended to the new CLI (item_basis on change).
# ---------------------------------------------------------------------------

class TestAppendOnlyInvariant(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # 3-5-savvas-q27, wave 0, dok 3

    def test_two_reviews_append_two_lines_first_line_unchanged(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)

        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "first pass, matches the anchor",
            "--rubric-version", "v0.2",
            "--note", "first pass", "--reviewed-at", "2026-07-19T09:00:00-04:00",
        )
        with open(self.log_path, "r", encoding="utf-8") as f:
            after_first_write = f.read()
        self.assertEqual(len(after_first_write.splitlines()), 1)

        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "change",
            "--chosen-dok", str(chosen), "--item-basis", "adapted",
            "--rationale", "revised on re-review, actually needs strategic reasoning",
            "--provenance", "reviewer judgment against DOKframework.txt rule 4",
            "--rubric-version", "v0.2",
            "--note", "revised on re-review", "--reviewed-at", "2026-07-19T09:30:00-04:00",
        )
        with open(self.log_path, "r", encoding="utf-8") as f:
            full_contents = f.read()

        self.assertEqual(len(full_contents.splitlines()), 2)
        self.assertTrue(full_contents.startswith(after_first_write))

        lines = full_contents.splitlines()
        first_entry = json.loads(lines[0])
        second_entry = json.loads(lines[1])

        self.assertEqual(first_entry["decision"], "confirm")
        self.assertEqual(first_entry["reviewer_dok"], prior)
        self.assertEqual(first_entry["note"], "first pass")
        self.assertEqual(first_entry["confirmation_basis"], "rule-1-textbook-provenance")

        self.assertEqual(second_entry["decision"], "change")
        self.assertEqual(second_entry["reviewer_dok"], chosen)
        self.assertEqual(second_entry["new_dok"], chosen)

        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(latest[self.UID]["decision"], "change")
        self.assertEqual(latest[self.UID]["note"], "revised on re-review")


# ---------------------------------------------------------------------------
# Per-wave progress math -- totals preserved (42/4/220/7/627 = 900).
# ---------------------------------------------------------------------------

class TestPerWaveProgressMath(DokReviewTestBase):
    def test_progress_matches_hand_computed_values(self):
        verified_intended = [
            ("iu_3b42ab3340d5", "2026-07-19T08:00:00-04:00"),  # wave 0
            ("iu_3d5d21133498", "2026-07-19T08:02:00-04:00"),  # wave 1
            ("iu_9d7bab718966", "2026-07-19T08:03:00-04:00"),  # wave 3
            ("iu_77d25e1e6131", "2026-07-19T08:05:00-04:00"),  # wave 4 (q41 wave-4 copy)
        ]
        reviewed_once_only = [
            ("iu_e32a6f7f8909", "2026-07-19T08:01:00-04:00"),  # wave 0
            ("iu_3c70a19c8d36", "2026-07-19T08:04:00-04:00"),  # wave 3 (q41 wave-3 copy, unsourced)
        ]

        for uid, reviewed_at in verified_intended:
            self.run_cli(
                "review", "--item-uid", uid,
                "--reviewed-by", "lynn", "--disposition", "confirm",
                "--provenance", self.resolving_provenance_for(uid), "--rationale", "matches the anchor",
                "--rubric-version", "v0.2", "--reviewed-at", reviewed_at,
            )
        for uid, reviewed_at in reviewed_once_only:
            self.run_cli(
                "review", "--item-uid", uid,
                "--reviewed-by", "lynn", "--disposition", "confirm",
                "--rubric-version", "v0.2", "--reviewed-at", reviewed_at,
            )

        expected_totals = {"0": 42, "1": 4, "2": 220, "3": 7, "4": 627}
        expected_reviewed_once = {"0": 2, "1": 1, "2": 0, "3": 2, "4": 1}
        expected_verified_if_approved = {"0": 1, "1": 1, "2": 0, "3": 1, "4": 1}

        progress_default = dr.compute_progress(self.plan, self.log_path, approvals_path=self.approvals_path)
        for wk, total in expected_totals.items():
            self.assertEqual(progress_default["waves"][wk]["total"], total, f"wave {wk} total")
        self.assertEqual(sum(expected_totals.values()), 900)
        self.assertEqual(progress_default["overall"]["total"], 900)
        for wk in dr.WAVE_KEYS:
            self.assertEqual(
                progress_default["waves"][wk]["reviewed_once_or_better"],
                expected_reviewed_once[wk], f"wave {wk} reviewed_once_or_better",
            )
            self.assertEqual(progress_default["waves"][wk]["verified"], 0, f"wave {wk} verified (default)")
            self.assertEqual(progress_default["waves"][wk]["invalid_entry"], 0, f"wave {wk} invalid_entry (default)")
        self.assertEqual(progress_default["overall"]["reviewed_once_or_better"], 6)
        self.assertEqual(progress_default["overall"]["verified"], 0)
        self.assertEqual(progress_default["overall"]["invalid_entry"], 0)

        approved = {"v0.2": FAR_PAST_APPROVAL}
        progress_approved = dr.compute_progress(self.plan, self.log_path, _approved_versions_override=approved)
        for wk in dr.WAVE_KEYS:
            self.assertEqual(
                progress_approved["waves"][wk]["verified"],
                expected_verified_if_approved[wk], f"wave {wk} verified (approved)",
            )
        self.assertEqual(progress_approved["overall"]["verified"], sum(expected_verified_if_approved.values()))
        self.assertEqual(progress_approved["overall"]["verified"], 4)


# ---------------------------------------------------------------------------
# No source file written -- plan, registry, AND calibration fixture files
# byte-identical through review / promote-reject / report.
# ---------------------------------------------------------------------------

class TestNoSourceFileWritten(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # 3-5-savvas-q27, wave 0, dok 3, registry_line 41

    def test_plan_registry_and_calibration_byte_identical_after_full_workflow(self):
        plan_sha_before = sha256_of(self.plan_path)
        registry_sha_before = sha256_of(self.registry_path)
        calibration_shas_before = {
            p.name: sha256_of(p) for p in sorted(self.calibration_dir.glob("*.json"))
        }

        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", self.resolving_provenance_for(self.UID), "--rationale", "matches",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T11:00:00-04:00",
        )

        proposal_out = self.proposals_dir / "promotion_test.json"
        # run_cli() points --approvals at the hermetic EMPTY manifest fixture
        # (never the real, now-approved rubric_approvals.json), so v0.2 is
        # unapproved here -- CLI-level promote must refuse (the intended
        # fail-safe), and must not write a proposal.
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("promote", "--item-uid", self.UID, "--out", str(proposal_out))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(proposal_out.exists())

        self.run_cli("report", "--out", str(self.report_path))

        plan_sha_after = sha256_of(self.plan_path)
        registry_sha_after = sha256_of(self.registry_path)
        calibration_shas_after = {
            p.name: sha256_of(p) for p in sorted(self.calibration_dir.glob("*.json"))
        }

        self.assertEqual(plan_sha_before, plan_sha_after, "dok_wave_plan.json must be byte-identical")
        self.assertEqual(registry_sha_before, registry_sha_after, "registry.jsonl must be byte-identical")
        self.assertEqual(
            calibration_shas_before, calibration_shas_after,
            "calibration fixture files must be byte-identical (read-only reference)",
        )

        tmp_root = Path(self.tmpdir.name)
        registry_files = list(tmp_root.rglob("registry.jsonl"))
        self.assertEqual(registry_files, [self.registry_path])

        self.assertTrue(self.report_path.exists())


# ---------------------------------------------------------------------------
# promote: row resolution (preserved intent) + failure paths.
# ---------------------------------------------------------------------------

class TestPromote(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # 3-5-savvas-q27, wave 0, dok 3, registry_line 41

    def test_promote_row_resolution_succeeds_only_with_simulated_approval(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)
        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "change",
            "--chosen-dok", str(chosen), "--item-basis", "adapted",
            "--rationale", "downgraded after discussion",
            "--provenance", "reviewer judgment against DOKframework.txt rule 4",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T12:00:00-04:00",
        )

        out_path = self.proposals_dir / "promotion_valid.json"
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("promote", "--item-uid", self.UID, "--out", str(out_path))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(out_path.exists())

        approved = {"v0.2": FAR_PAST_APPROVAL}
        proposal = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID,
            calibration_dir=self.calibration_dir, _approved_versions_override=approved,
        )
        self.assertEqual(proposal["item_uid"], self.UID)
        self.assertEqual(proposal["registry_line"], 41)
        self.assertEqual(proposal["legacy_id"], "3-5-savvas-q27")
        self.assertEqual(proposal["current_dok"], 3)
        self.assertEqual(proposal["decision"], "change")
        self.assertEqual(proposal["proposed_new_dok"], chosen)
        self.assertEqual(proposal["registry_written"], False)
        self.assertEqual(proposal["rubric_version"], "v0.2")
        self.assertEqual(proposal["rationale"], "downgraded after discussion")
        self.assertIn("PROPOSAL ONLY", proposal["human_note"])

    def test_promote_unknown_uid_fails_no_proposal_written(self):
        out_path = self.proposals_dir / "promotion_unknown.json"
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("promote", "--item-uid", "iu_does_not_exist", "--out", str(out_path))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(out_path.exists())

    def test_promote_unreviewed_uid_fails_no_proposal_written(self):
        out_path = self.proposals_dir / "promotion_unreviewed.json"
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("promote", "--item-uid", self.UID, "--out", str(out_path))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(out_path.exists())

    def test_build_promotion_proposal_raises_valueerror_directly(self):
        # Raises early (unknown uid) before the rubric gate is ever reached
        # -- but _resolve_approved_versions() is still called first inside
        # build_promotion_proposal, so pass the explicit empty fixture
        # anyway (hermetic even though it can't affect the outcome here).
        with self.assertRaises(ValueError):
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, "iu_does_not_exist",
                calibration_dir=self.calibration_dir, approvals_path=self.approvals_path,
            )


# ---------------------------------------------------------------------------
# NT6 F1: retroactivity -- an entry recorded before a version's approved_at
# never verifies, even after that version is later approved.
# ---------------------------------------------------------------------------

class TestRetroactivity(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # wave 0, lesson 3-5

    def test_recorded_before_approval_never_verifies_recorded_after_does(self):
        provenance = self.resolving_provenance_for(self.UID)
        self.run_cli(
            "review", "--item-uid", self.UID,
            "--reviewed-by", "lynn", "--disposition", "confirm",
            "--provenance", provenance, "--rationale", "matches the anchor",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2020-01-01T00:00:00-04:00",
        )
        entry = self.latest_for(self.UID)
        self.assertEqual(entry["confirmation_basis"], "rule-1-textbook-provenance")
        recorded_at = dr.parse_iso(entry["recorded_at"])
        self.assertIsNotNone(recorded_at)

        # Manifest approving v0.2 AFTER this entry's recorded_at -> never verifies.
        after_approval = {"v0.2": (recorded_at + timedelta(hours=1)).isoformat()}
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=after_approval))

        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir, _approved_versions_override=after_approval,
            )
        self.assertIn("recorded before approval", str(cm.exception))

        # Manifest approving v0.2 BEFORE this entry's recorded_at -> verifies + promotes.
        before_approval = {"v0.2": (recorded_at - timedelta(hours=1)).isoformat()}
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=before_approval))

        proposal = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID,
            calibration_dir=self.calibration_dir, _approved_versions_override=before_approval,
        )
        self.assertEqual(proposal["registry_written"], False)


# ---------------------------------------------------------------------------
# NT6 F1: rubric-approvals manifest loader -- fail-closed behavior.
# ---------------------------------------------------------------------------

class TestManifestLoader(DokReviewTestBase):
    def test_missing_file_returns_empty(self):
        missing = Path(self.tmpdir.name) / "does_not_exist.json"
        self.assertEqual(dr.load_rubric_approvals(missing), {})

    def test_malformed_json_returns_empty(self):
        path = Path(self.tmpdir.name) / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_bad_approved_at_returns_empty(self):
        path = self.write_manifest([{"version": "v0.2", "approved_at": "not-a-timestamp"}])
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_missing_approved_at_returns_empty(self):
        path = self.write_manifest([{"version": "v0.2"}])
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_wrong_top_level_shape_returns_empty(self):
        path = Path(self.tmpdir.name) / "wrong_shape.json"
        path.write_text(json.dumps({"approvals": "not-a-list"}), encoding="utf-8")
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_non_object_entry_returns_empty(self):
        path = Path(self.tmpdir.name) / "non_object_entry.json"
        path.write_text(json.dumps({"approvals": ["v0.2"]}), encoding="utf-8")
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_non_string_version_returns_empty(self):
        path = self.write_manifest([{"version": 2, "approved_at": FAR_PAST_APPROVAL}])
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_empty_string_version_returns_empty(self):
        path = self.write_manifest([{"version": "", "approved_at": FAR_PAST_APPROVAL}])
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_one_malformed_entry_poisons_whole_manifest(self):
        path = self.write_manifest([
            {"version": "v0.1", "approved_at": FAR_PAST_APPROVAL},
            {"version": "v0.2", "approved_at": "not-a-timestamp"},
        ])
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_valid_manifest_parses(self):
        path = self.write_manifest([{"version": "v0.2", "approved_at": FAR_PAST_APPROVAL}])
        result = dr.load_rubric_approvals(path)
        self.assertEqual(set(result.keys()), {"v0.2"})
        self.assertEqual(result["v0.2"], dr.parse_iso(FAR_PAST_APPROVAL))

    def test_naive_approved_at_returns_empty(self):
        # NT6 round 3, G2: parse_iso now rejects naive (no UTC offset)
        # datetimes -- this flows straight into the manifest loader's
        # existing "unparseable approved_at" fail-closed path.
        path = self.write_manifest([{"version": "v0.2", "approved_at": "2026-01-01T00:00:00"}])
        self.assertEqual(dr.load_rubric_approvals(path), {})

    def test_duplicate_version_returns_empty(self):
        # NT6 round 3, G4: the SAME version appearing twice poisons the
        # whole manifest (fail closed), even if both entries are otherwise
        # individually well-formed -- a duplicate could otherwise move the
        # effective approval boundary backward depending on list order.
        path = self.write_manifest([
            {"version": "v0.2", "approved_at": FAR_PAST_APPROVAL},
            {"version": "v0.2", "approved_at": "2026-06-01T00:00:00+00:00"},
        ])
        self.assertEqual(dr.load_rubric_approvals(path), {})

    # NOTE: this class no longer asserts anything about the REAL shipped
    # rubric_approvals.json (it now ships with v0.2 approved, not empty --
    # that premise is obsolete). The real manifest is instead covered by the
    # single, explicitly-marked integration test:
    # TestRealManifestIntegrationOnly, below.


# ---------------------------------------------------------------------------
# INTEGRATION test -- the ONE test in this whole suite permitted to read the
# real tools/dok-review/rubric_approvals.json. Every other test in this file
# is hermetic (DokReviewTestBase's empty temp fixture, or an explicit
# _approved_versions_override). Deliberately NOT a DokReviewTestBase
# subclass -- it must not inherit the empty-manifest fixture, since its
# whole point is to look at the real file.
# ---------------------------------------------------------------------------

class TestRealManifestIntegrationOnly(unittest.TestCase):
    """INTEGRATION test -- the single test permitted to read the real
    tools/dok-review/rubric_approvals.json; every other test in this suite
    is hermetic and never touches that ambient file.

    Confirms the real, shipped manifest actually contains the DOK rubric
    v0.2 approval recorded by RC (approved_at 2026-07-20T19:06:13-04:00)
    and that `load_rubric_approvals()` (called with NO arguments, i.e. the
    real default path) parses it into an offset-aware datetime with the
    expected UTC offset.
    """

    EXPECTED_APPROVED_AT = datetime(2026, 7, 20, 19, 6, 13, tzinfo=timezone(timedelta(hours=-4)))

    def test_real_manifest_exactly_one_v0_2_approval_and_default_path_load(self):
        # (1) Raw JSON: EXACTLY one approval entry, exact strings.
        self.assertTrue(dr.DEFAULT_APPROVALS.exists())
        with open(dr.DEFAULT_APPROVALS, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.assertEqual(
            raw.get("approvals"),
            [{"version": "v0.2", "approved_at": "2026-07-20T19:06:13-04:00"}],
        )

        # (2) NO arguments -- exercises the real default path
        # (DEFAULT_APPROVALS) -- and returns exactly that one approval as an
        # offset-aware datetime.
        result = dr.load_rubric_approvals()
        self.assertEqual(set(result.keys()), {"v0.2"})
        approved_at = result["v0.2"]
        self.assertEqual(approved_at, self.EXPECTED_APPROVED_AT)
        self.assertIsNotNone(approved_at.tzinfo)
        self.assertEqual(approved_at.utcoffset(), timedelta(hours=-4))


# ---------------------------------------------------------------------------
# NT6 F3: stale-timestamp spoof via CLI is rejected at entry.
# ---------------------------------------------------------------------------

class TestStaleTimestampSpoof(DokReviewTestBase):
    UID = "iu_9d7bab718966"  # wave 3

    def test_confirm_before_nsc_timestamp_rejected(self):
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "needs-source-check", "--rationale", "need to check",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T13:00:00-04:00",
        )
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--provenance", self.resolving_provenance_for(self.UID),
                "--rationale", "actually fine", "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T12:00:00-04:00",  # earlier than the nsc
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_equal_timestamp_is_allowed(self):
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "needs-source-check", "--rationale", "need to check",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T13:00:00-04:00",
        )
        # Same timestamp (equal, not strictly earlier) is allowed.
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "confirm", "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "resolved immediately", "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T13:00:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        self.assertEqual(len(entries), 2)

    def test_unparseable_reviewed_at_rejected(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--rubric-version", "v0.2",
                "--reviewed-at", "not-a-timestamp",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_existing_unparseable_reviewed_at_fails_closed(self):
        self.craft_log_lines([{
            "item_uid": self.UID, "registry_line": 200, "item_id": "4-4-savvas-q32",
            "lesson": "4-4", "reviewed_by": "lynn", "reviewed_at": "garbage-timestamp",
            "recorded_at": "2026-07-19T09:00:00-04:00", "prior_dok": 3, "reviewer_dok": 3,
            "current_dok": 3, "new_dok": None, "decision": "confirm", "te_bucket": None,
            "match_quality": "none", "disagreement_resolved": False, "note": "",
            "rubric_version": "v0.2", "rationale": "x", "provenance": "",
            "provenance_resolved": False, "confirmation_basis": "rule-2-adjacent-unsourced",
            "item_basis": None, "resolves_source_check": False, "prior_unresolved_nsc": False,
        }])
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T14:00:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)


# ---------------------------------------------------------------------------
# NT6 round 3, G2: single aware-only timestamp policy + chain order.
# ---------------------------------------------------------------------------

class TestChainTimestampOrderAndAwareOnly(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # 3-5-savvas-q27, lesson 3-5, dok 3, registry_line 41

    def _base_entry(self, **overrides):
        entry = {
            "item_uid": self.UID, "registry_line": 41, "item_id": "3-5-savvas-q27",
            "lesson": "3-5", "reviewed_by": "lynn",
            "reviewed_at": "2026-07-19T09:00:00-04:00",
            "recorded_at": "2026-07-19T09:00:01-04:00",
            "prior_dok": 3, "reviewer_dok": 3, "current_dok": 3, "new_dok": None,
            "decision": "confirm", "te_bucket": None, "match_quality": "none",
            "disagreement_resolved": False, "note": "", "rubric_version": "v0.2",
            "rationale": "matches", "provenance": "calibration-anchor:3-5:practice #27",
            "provenance_resolved": True, "confirmation_basis": "rule-1-textbook-provenance",
            "item_basis": None, "resolves_source_check": False, "prior_unresolved_nsc": False,
        }
        entry.update(overrides)
        return entry

    def test_chain_out_of_order_rejected_naming_positions(self):
        # Both entries are individually well-formed (valid rule-1 confirms
        # against the item's own real anchor) -- only their ORDER is wrong.
        first = self._base_entry(
            reviewed_at="2026-07-19T10:00:00-04:00", recorded_at="2026-07-19T10:00:01-04:00",
        )
        second = self._base_entry(
            reviewed_at="2026-07-19T09:00:00-04:00", recorded_at="2026-07-19T10:05:00-04:00",
        )
        self.craft_log_lines([first, second])
        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir,
                _approved_versions_override={"v0.2": FAR_PAST_APPROVAL},
            )
        msg = str(cm.exception)
        self.assertIn("#1", msg)
        self.assertIn("#2", msg)
        self.assertIn("out of order", msg)

    def test_naive_reviewed_at_rejected_at_cli_entry(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T09:00:00",  # naive -- no UTC offset
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_naive_reviewed_at_in_crafted_entry_is_invalid_entry(self):
        self.craft_log_lines([self._base_entry(reviewed_at="2026-07-19T09:00:00")])  # naive
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "invalid-entry",
        )

    def test_naive_reviewed_at_in_crafted_chain_rejected_by_promote(self):
        self.craft_log_lines([self._base_entry(reviewed_at="2026-07-19T09:00:00")])  # naive
        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir,
                _approved_versions_override={"v0.2": FAR_PAST_APPROVAL},
            )
        self.assertIn("#1", str(cm.exception))
        self.assertIn("reviewed_at", str(cm.exception))

    def test_parse_iso_rejects_naive_datetime(self):
        self.assertIsNone(dr.parse_iso("2026-07-19T09:00:00"))
        self.assertIsNotNone(dr.parse_iso("2026-07-19T09:00:00-04:00"))
        self.assertIsNotNone(dr.parse_iso("2026-07-19T09:00:00+00:00"))


# ---------------------------------------------------------------------------
# NT6 F5: crafted-log promotions -- structural + on-disk re-derivation.
# ---------------------------------------------------------------------------

class TestCraftedLogPromotions(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # wave 0, lesson 3-5, registry_line 41

    def _base_entry(self, **overrides):
        entry = {
            "item_uid": self.UID,
            "registry_line": 41,
            "item_id": "3-5-savvas-q27",
            "lesson": "3-5",
            "reviewed_by": "lynn",
            "reviewed_at": "2026-07-19T09:00:00-04:00",
            "recorded_at": "2026-07-19T09:00:01-04:00",
            "prior_dok": 3,
            "reviewer_dok": 3,
            "current_dok": 3,
            "new_dok": None,
            "decision": "confirm",
            "te_bucket": None,
            "match_quality": "none",
            "disagreement_resolved": False,
            "note": "",
            "rubric_version": "v0.2",
            "rationale": "matches",
            "provenance": "",
            "provenance_resolved": False,
            "confirmation_basis": "rule-2-adjacent-unsourced",
            "item_basis": None,
            "resolves_source_check": False,
            "prior_unresolved_nsc": False,
        }
        entry.update(overrides)
        return entry

    def _promote_rejects(self, approved=None):
        # Hermetic default: when no `approved` override is given, resolve
        # against the (empty) temp fixture via approvals_path -- never the
        # ambient real manifest.
        with self.assertRaises(ValueError) as cm:
            if approved is None:
                dr.build_promotion_proposal(
                    self.plan, self.registry_path, self.log_path, self.UID,
                    calibration_dir=self.calibration_dir, approvals_path=self.approvals_path,
                )
            else:
                dr.build_promotion_proposal(
                    self.plan, self.registry_path, self.log_path, self.UID,
                    calibration_dir=self.calibration_dir, _approved_versions_override=approved,
                )
        return str(cm.exception)

    def test_unknown_decision_rejected_with_position(self):
        self.craft_log_lines([self._base_entry(decision="bogus-decision")])
        msg = self._promote_rejects()
        self.assertIn("#1", msg)
        self.assertIn("unknown decision", msg)

    def test_whitespace_reviewed_by_rejected_with_position(self):
        self.craft_log_lines([self._base_entry(reviewed_by="   ")])
        msg = self._promote_rejects()
        self.assertIn("#1", msg)
        self.assertIn("reviewed_by", msg)

    def test_unparseable_reviewed_at_rejected_with_position(self):
        self.craft_log_lines([self._base_entry(reviewed_at="not-a-timestamp")])
        msg = self._promote_rejects()
        self.assertIn("#1", msg)
        self.assertIn("reviewed_at", msg)

    def test_change_missing_item_basis_rejected_with_position(self):
        self.craft_log_lines([self._base_entry(
            decision="change", new_dok=2, rationale="x", provenance="y",
            item_basis=None, confirmation_basis=None,
        )])
        msg = self._promote_rejects()
        self.assertIn("#1", msg)
        self.assertIn("item_basis", msg)

    def test_crafted_confirm_rule1_claim_with_free_text_rejected(self):
        self.craft_log_lines([self._base_entry(
            provenance="just my word for it, no scheme",
            confirmation_basis="rule-1-textbook-provenance",
        )])
        msg = self._promote_rejects()
        self.assertIn("#1", msg)
        self.assertIn("lacks source provenance", msg)

    def test_second_position_defect_named_correctly(self):
        good = self._base_entry(reviewed_at="2026-07-19T09:00:00-04:00")
        bad = self._base_entry(reviewed_at="2026-07-19T10:00:00-04:00", decision="also-bogus")
        self.craft_log_lines([good, bad])
        msg = self._promote_rejects()
        self.assertIn("#2", msg)
        self.assertIn("unknown decision", msg)

    def test_crafted_confirm_rule1_citing_another_items_real_anchor_rejected(self):
        # NT6 round 3, G1: this item_uid's own identity is practice-27
        # (id "3-5-savvas-q27"). 3-5.json really has a "Practice #30" anchor
        # (a DIFFERENT item's anchor, not this one's) -- a crafted entry
        # that stamps rule-1-textbook-provenance while citing it must be
        # rejected, exactly like citing free text with no scheme.
        self.craft_log_lines([self._base_entry(
            provenance="calibration-anchor:3-5:practice #30",
            confirmation_basis="rule-1-textbook-provenance",
        )])
        msg = self._promote_rejects()
        self.assertIn("#1", msg)
        self.assertIn("lacks source provenance", msg)


# ---------------------------------------------------------------------------
# NT6 round 3, G1: item-bound provenance resolution, dedicated fixture.
# resolve_provenance() now REQUIRES an `item` -- a ref only resolves when it
# identifies the SAME item being reviewed, not just "some anchor exists
# somewhere in the cited lesson's file".
# ---------------------------------------------------------------------------

class TestProvenanceResolution(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.calibration_dir = Path(self.tmpdir.name) / "calibration"
        self.calibration_dir.mkdir()

        lesson_3_5 = {
            "lesson": "3-5",
            "item_analysis": {},
            "dok2_anchors": [],
            "dok3_anchors": [
                {"source": "Savvas Practice #2 (fixture, lesson 3-5)"},
                {"source": "Savvas Practice #27 (Model With Mathematics, lesson 3-5, anchors Example 4)"},
                {"source": "Savvas Practice #99 (fixture, lesson 3-5)"},
            ],
        }
        lesson_4_1 = {
            "lesson": "4-1",
            "item_analysis": {"example_2": {"dok2": [1]}, "example_5": {"dok3": [1]}},
            "dok2_anchors": [],
            "dok3_anchors": [],
        }
        lesson_9_9 = {
            "lesson": "9-9",
            "item_analysis": {"example_2": {}},
            "dok2_anchors": [],
            "dok3_anchors": [],
        }
        # NT10 (Fable-authorized semantic alignment, 2026-07-22): shaped like
        # the REAL questionbank/calibration/5-4.json -- item_analysis
        # transcribed from the TE Item Analysis table (practice numbers in
        # dok<k> lists), dok2_anchors/dok3_anchors deliberately EMPTY. A
        # practice identity must bind via item_analysis here, exactly the
        # evidence gen_dok_wave_plan.py's build_item_to_dok reads.
        lesson_5_4 = {
            "lesson": "5-4",
            "item_analysis": {
                "example_1": {"dok1": [21, 22], "dok2": [18]},
                "example_4": {"dok1": [33], "dok3": [19, 41]},
            },
            "dok2_anchors": [],
            "dok3_anchors": [],
        }
        for name, data in (("3-5.json", lesson_3_5), ("4-1.json", lesson_4_1), ("9-9.json", lesson_9_9), ("5-4.json", lesson_5_4)):
            with open(self.calibration_dir / name, "w", encoding="utf-8") as f:
                json.dump(data, f)

        # A real Savvas practice item, lesson 3-5, own identity ("practice", 27)
        # -- matches the shape of the REAL 3-5.json anchor used elsewhere in
        # this suite (3-5-savvas-q27, iu_3b42ab3340d5).
        self.item_practice_27 = {
            "item_uid": "iu_p27", "registry_line": 41, "id": "3-5-savvas-q27",
            "lesson": "3-5", "dok": 3, "te_bucket": None, "match_quality": None,
        }
        # A worked-example item, lesson 4-1, own identity ("example", 2).
        self.item_example_2 = {
            "item_uid": "iu_ex2", "registry_line": 2, "id": "4-1-ex-2",
            "lesson": "4-1", "dok": 2, "te_bucket": None, "match_quality": None,
        }
        # A lesson-quiz item -- NO derivable calibration identity at all,
        # even though 3-5.json (above) has a real "Practice #2" anchor
        # sitting right there.
        self.item_lq = {
            "item_uid": "iu_lq", "registry_line": 3, "id": "3-5-lq-q2",
            "lesson": "3-5", "dok": 2, "te_bucket": None, "match_quality": None,
        }
        # A Savvas practice item in the anchors-empty, item_analysis-only
        # lesson (5-4 shape) -- own identity ("practice", 21); 21 appears in
        # lesson_5_4's item_analysis example_1 dok1 list.
        self.item_practice_21_54 = {
            "item_uid": "iu_p21_54", "registry_line": 308, "id": "5-4-savvas-q21",
            "lesson": "5-4", "dok": 1, "te_bucket": [1], "match_quality": "exact",
        }

    # -- syntax gates: fail before item-binding is even reached --

    def test_free_text_does_not_resolve(self):
        self.assertFalse(dr.resolve_provenance(
            "just some free text, no scheme", self.calibration_dir, self.item_practice_27,
        ))

    def test_empty_does_not_resolve(self):
        self.assertFalse(dr.resolve_provenance("", self.calibration_dir, self.item_practice_27))
        self.assertFalse(dr.resolve_provenance("   ", self.calibration_dir, self.item_practice_27))

    def test_path_traversal_lesson_rejected(self):
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:..:practice #27", self.calibration_dir, self.item_practice_27,
        ))

    def test_nonexistent_lesson_file_does_not_resolve(self):
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:0-0:practice #27", self.calibration_dir, self.item_practice_27,
        ))

    def test_wrong_scheme_does_not_resolve(self):
        self.assertFalse(dr.resolve_provenance(
            "some-other-scheme:3-5:practice #27", self.calibration_dir, self.item_practice_27,
        ))

    # -- item-bound identity checks (G1 core) --

    def test_wrong_lesson_ref_not_resolved(self):
        # Item's own lesson is 3-5; the ref cites 4-1, which really DOES
        # have an example_2 key -- must not resolve for THIS item.
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:4-1:example_2", self.calibration_dir, self.item_practice_27,
        ))

    def test_wrong_item_different_practice_number_with_real_anchor_present_not_resolved(self):
        # 3-5.json really has a "Practice #99" anchor -- but this item's own
        # identity is practice-27, so citing #99 must not resolve.
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:3-5:practice #99", self.calibration_dir, self.item_practice_27,
        ))

    def test_underspecified_ref_not_resolved(self):
        for ref in ("a", "practice", "example"):
            with self.subTest(ref=ref):
                self.assertFalse(dr.resolve_provenance(
                    f"calibration-anchor:3-5:{ref}", self.calibration_dir, self.item_practice_27,
                ))

    def test_exact_match_practice_ref_variants_resolve(self):
        for ref in ("27", "#27", "q27", "practice #27", "practice-27", "practice 27"):
            with self.subTest(ref=ref):
                self.assertTrue(dr.resolve_provenance(
                    f"calibration-anchor:3-5:{ref}", self.calibration_dir, self.item_practice_27,
                ))

    def test_nonexistent_practice_number_does_not_resolve(self):
        # This item's own identity IS practice-999 (matches the ref's
        # number), but no anchor for #999 exists anywhere in the file.
        item_999 = dict(self.item_practice_27, id="3-5-savvas-q999", item_uid="iu_p999")
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:3-5:practice #999", self.calibration_dir, item_999,
        ))

    def test_example_binding_via_item_analysis_key(self):
        for ref in ("example_2", "example 2", "ex 2", "ex-2"):
            with self.subTest(ref=ref):
                self.assertTrue(dr.resolve_provenance(
                    f"calibration-anchor:4-1:{ref}", self.calibration_dir, self.item_example_2,
                ))

    # -- NT10 (Fable-authorized semantic alignment, 2026-07-22): practice
    #    identities also bind via item_analysis dok<k> lists -- the same
    #    evidence source gen_dok_wave_plan.py's build_item_to_dok reads.
    #    Exercised against the anchors-empty 5-4-shaped fixture. --

    def test_practice_binding_via_item_analysis_dok_lists(self):
        # 21 sits in lesson_5_4's item_analysis example_1 dok1 list;
        # dok2_anchors/dok3_anchors are EMPTY -- must resolve anyway.
        for ref in ("21", "#21", "q21", "practice #21", "practice-21", "practice 21"):
            with self.subTest(ref=ref):
                self.assertTrue(dr.resolve_provenance(
                    f"calibration-anchor:5-4:{ref}", self.calibration_dir, self.item_practice_21_54,
                ))

    def test_practice_binding_via_item_analysis_dok3_list(self):
        # Numbers under a dok3 list bind too (19 in example_4's dok3).
        item_19 = dict(self.item_practice_21_54, id="5-4-savvas-q19", item_uid="iu_p19_54", dok=3)
        self.assertTrue(dr.resolve_provenance(
            "calibration-anchor:5-4:practice #19", self.calibration_dir, item_19,
        ))

    def test_practice_item_analysis_wrong_number_still_fails(self):
        # The ref cites #22 (a REAL number in the file) but this item's own
        # identity is practice-21 -- exact number identity is unchanged.
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:5-4:practice #22", self.calibration_dir, self.item_practice_21_54,
        ))

    def test_practice_item_analysis_absent_number_still_fails(self):
        # Own identity matches the ref (practice-999) but 999 appears in NO
        # item_analysis dok list and no anchor exists -- must not resolve.
        item_999 = dict(self.item_practice_21_54, id="5-4-savvas-q999", item_uid="iu_p999_54")
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:5-4:practice #999", self.calibration_dir, item_999,
        ))

    def test_practice_item_analysis_wrong_lesson_still_fails(self):
        # A 3-5 item citing 5-4's real item_analysis entry must not resolve
        # (lesson equality unchanged) ...
        item_35_21 = dict(self.item_practice_21_54, id="3-5-savvas-q21", item_uid="iu_p21_35", lesson="3-5")
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:5-4:practice #21", self.calibration_dir, item_35_21,
        ))
        # ... and the 5-4 item citing lesson 3-5 must not resolve either.
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:3-5:practice #21", self.calibration_dir, self.item_practice_21_54,
        ))

    def test_example_ref_never_binds_via_item_analysis_dok_lists(self):
        # An "example" ref/kind still binds ONLY via item_analysis KEYS
        # (example_<N>), never via a number inside a dok list: lesson_5_4
        # has no example_21 key, so an example-kind ref for 21 must fail
        # (kind mismatch against a practice item, and no such example key).
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:5-4:example_21", self.calibration_dir, self.item_practice_21_54,
        ))

    def test_split_practice_id_still_has_no_identity_in_item_analysis_lesson(self):
        # A split/multi-part practice id gets NO identity even when its base
        # number is right there in item_analysis -- unchanged by NT10.
        split_item = dict(self.item_practice_21_54, id="5-4-savvas-q21-partA-build", item_uid="iu_split_54")
        self.assertIsNone(dr.derive_item_calibration_identity(split_item))
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:5-4:practice #21", self.calibration_dir, split_item,
        ))

    def test_example_ref_against_practice_item_kind_mismatch_not_resolved(self):
        # Same number (27), but wrong KIND -- an "example" ref can never
        # bind a "practice" item, even if the numbers coincide.
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:3-5:example_27", self.calibration_dir, self.item_practice_27,
        ))

    def test_lq_item_never_resolves_even_with_matching_practice_anchor_present(self):
        # 3-5.json has a REAL "Practice #2" anchor -- but 3-5-lq-q2 has no
        # derivable calibration identity at all (lesson-quiz id shape), so
        # rule-1 is impossible for it regardless of what anchor exists.
        self.assertIsNone(dr.derive_item_calibration_identity(self.item_lq))
        self.assertFalse(dr.resolve_provenance(
            "calibration-anchor:3-5:practice #2", self.calibration_dir, self.item_lq,
        ))

    # -- derive_item_calibration_identity / normalize_provenance_item_ref
    #    unit coverage --

    def test_derive_item_calibration_identity_practice(self):
        self.assertEqual(
            dr.derive_item_calibration_identity(self.item_practice_27), ("practice", 27),
        )

    def test_derive_item_calibration_identity_example(self):
        self.assertEqual(
            dr.derive_item_calibration_identity(self.item_example_2), ("example", 2),
        )

    def test_derive_item_calibration_identity_split_practice_part_is_none(self):
        self.assertIsNone(dr.derive_item_calibration_identity({"id": "4-3-savvas-q36-partA-build"}))

    def test_derive_item_calibration_identity_rti_support_ids_are_none(self):
        # RTI-support ids MENTION an example number but are not the example
        # itself -- "ex3"/"ex6" here have no separator before the digit, so
        # they must not false-match the "-ex-<N>" identity pattern.
        for rti_id in ("3-5-rti-ex3-1", "3-5-rti-ex3-2", "3-5-rti-support-ex6-1"):
            with self.subTest(rti_id=rti_id):
                self.assertIsNone(dr.derive_item_calibration_identity({"id": rti_id}))

    def test_derive_item_calibration_identity_lesson_quiz_and_tryit_are_none(self):
        for other_id in ("3-5-lq-q2", "3-5-tryit-2a"):
            with self.subTest(other_id=other_id):
                self.assertIsNone(dr.derive_item_calibration_identity({"id": other_id}))

    def test_normalize_provenance_item_ref_bare_letter_is_none(self):
        self.assertIsNone(dr.normalize_provenance_item_ref("a"))

    def test_normalize_provenance_item_ref_bare_keyword_is_none(self):
        self.assertIsNone(dr.normalize_provenance_item_ref("practice"))

    def test_normalize_provenance_item_ref_variants(self):
        self.assertEqual(dr.normalize_provenance_item_ref("27"), (None, 27))
        self.assertEqual(dr.normalize_provenance_item_ref("#27"), (None, 27))
        self.assertEqual(dr.normalize_provenance_item_ref("q27"), ("practice", 27))
        self.assertEqual(dr.normalize_provenance_item_ref("practice #27"), ("practice", 27))
        self.assertEqual(dr.normalize_provenance_item_ref("practice-27"), ("practice", 27))
        self.assertEqual(dr.normalize_provenance_item_ref("practice 27"), ("practice", 27))
        self.assertEqual(dr.normalize_provenance_item_ref("example_2"), ("example", 2))
        self.assertEqual(dr.normalize_provenance_item_ref("example 2"), ("example", 2))
        self.assertEqual(dr.normalize_provenance_item_ref("ex 2"), ("example", 2))
        self.assertEqual(dr.normalize_provenance_item_ref("ex-2"), ("example", 2))

    def test_confirmation_basis_via_build_review_record(self):
        # id "9-9-ex-2" (not the old placeholder "x-1") so this item HAS a
        # derivable calibration identity (("example", 2)) matching the
        # fixture's 9-9.json item_analysis["example_2"] -- required under
        # the new item-bound resolve_provenance() semantics (G1).
        item = {
            "item_uid": "iu_x", "registry_line": 1, "id": "9-9-ex-2", "lesson": "9-9",
            "dok": 2, "te_bucket": None, "match_quality": None,
        }

        resolved = dr.build_review_record(
            item=item, reviewed_by="lynn", disposition="confirm", chosen_dok=None,
            rationale="", provenance="calibration-anchor:9-9:example_2",
            rubric_version="v0.2", note="", reviewed_at="2026-01-01T00:00:00-04:00",
            calibration_dir=self.calibration_dir,
        )
        self.assertTrue(resolved["provenance_resolved"])
        self.assertEqual(resolved["confirmation_basis"], "rule-1-textbook-provenance")

        claim = dr.build_review_record(
            item=item, reviewed_by="lynn", disposition="confirm", chosen_dok=None,
            rationale="", provenance="calibration-anchor:9-9:practice #999",
            rubric_version="v0.2", note="", reviewed_at="2026-01-01T00:00:00-04:00",
            calibration_dir=self.calibration_dir,
        )
        self.assertFalse(claim["provenance_resolved"])
        self.assertEqual(claim["confirmation_basis"], "rule-2-adjacent-unsourced-claim")

        unsourced = dr.build_review_record(
            item=item, reviewed_by="lynn", disposition="confirm", chosen_dok=None,
            rationale="", provenance="",
            rubric_version="v0.2", note="", reviewed_at="2026-01-01T00:00:00-04:00",
            calibration_dir=self.calibration_dir,
        )
        self.assertEqual(unsourced["confirmation_basis"], "rule-2-adjacent-unsourced")


# ---------------------------------------------------------------------------
# NT6 round 3, G1: --resolves-source-check rejected at entry when the
# supplied --provenance -- though syntactically valid, and even a REAL
# anchor in the cited lesson's file -- is not bound to the reviewed item
# itself.
# ---------------------------------------------------------------------------

class TestFalseResolvesSourceCheckRejectedAtEntry(DokReviewTestBase):
    UID = "iu_e32a6f7f8909"  # 3-5-lq-q1a -- lesson-quiz, NO derivable identity

    def test_unrelated_real_anchor_rejected_at_entry(self):
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "needs-source-check", "--rationale", "need to check",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:00:00-04:00",
        )
        before = self.log_bytes_or_none()
        # "calibration-anchor:3-5:practice #27" is a REAL, resolving anchor
        # in the (temp-copied) real 3-5.json -- but this item_uid's id
        # ("3-5-lq-q1a") has no derivable calibration identity at all, so it
        # must still be rejected at entry.
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--resolves-source-check",
                "--provenance", "calibration-anchor:3-5:practice #27",
                "--rationale", "citing an unrelated real anchor",
                "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:05:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)


# ---------------------------------------------------------------------------
# NT6 F6: item_basis matrix (R1/R2 vs. R3).
# ---------------------------------------------------------------------------

class TestItemBasisMatrix(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # wave 0, dok 3

    def test_change_adapted_free_text_verification_grade_under_approval(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "change", "--chosen-dok", str(chosen),
            "--item-basis", "adapted",
            "--rationale", "adapted, now needs strategic reasoning",
            "--provenance", "reviewer judgment, free text",
            "--rubric-version", "v0.2",
        )
        entry = self.latest_for(self.UID)
        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=approved))

        proposal = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID,
            calibration_dir=self.calibration_dir, _approved_versions_override=approved,
        )
        self.assertEqual(proposal["registry_written"], False)

    def test_change_textbook_exact_free_text_not_verification_grade(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "change", "--chosen-dok", str(chosen),
            "--item-basis", "textbook-exact",
            "--rationale", "textbook actually says otherwise",
            "--provenance", "reviewer judgment, free text",
            "--rubric-version", "v0.2",
        )
        entry = self.latest_for(self.UID)
        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=approved))
        with self.assertRaises(ValueError):
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir, _approved_versions_override=approved,
            )

    def test_change_textbook_exact_resolving_provenance_promotes(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "change", "--chosen-dok", str(chosen),
            "--item-basis", "textbook-exact",
            "--rationale", "textbook actually confirms a different DOK",
            "--provenance", self.resolving_provenance_for(self.UID),
            "--rubric-version", "v0.2",
        )
        entry = self.latest_for(self.UID)
        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=approved))
        proposal = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID,
            calibration_dir=self.calibration_dir, _approved_versions_override=approved,
        )
        self.assertEqual(proposal["registry_written"], False)

    def test_item_basis_with_confirm_rejected(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--item-basis", "adapted",
                "--rubric-version", "v0.2",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_change_without_item_basis_rejected(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "change", "--chosen-dok", str(chosen),
                "--rationale", "x", "--provenance", "y",
                "--rubric-version", "v0.2",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_bad_item_basis_value_argparse_exit_2(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "change", "--chosen-dok", str(chosen),
                "--item-basis", "bogus-basis",
                "--rationale", "x", "--provenance", "y",
                "--rubric-version", "v0.2",
            )
        self.assertEqual(ctx.exception.code, 2)
        self.assert_log_unchanged(before)


# ---------------------------------------------------------------------------
# NT6 F6: NSC (needs-source-check) attestation.
# ---------------------------------------------------------------------------

class TestNscAttestation(DokReviewTestBase):
    UID = "iu_9d7bab718966"  # wave 3

    def test_generic_confirm_over_unresolved_nsc_does_not_verify_and_blocks_promote(self):
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "needs-source-check", "--rationale", "need to check first",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:00:00-04:00",
        )
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "confirm", "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "actually checked it out, looks fine",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:05:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        entry = latest[self.UID]
        self.assertEqual(entry["decision"], "confirm")
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "reviewed_once",
        )
        self.assertTrue(entry["prior_unresolved_nsc"])

        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertFalse(dr.entry_is_verified(entry, _approved_versions_override=approved))

        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.UID,
                calibration_dir=self.calibration_dir, _approved_versions_override=approved,
            )
        self.assertIn("unresolved needs-source-check", str(cm.exception))

    def test_attested_resolution_via_confirm_verifies_and_promotes(self):
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "needs-source-check", "--rationale", "need to check first",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:00:00-04:00",
        )
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "confirm", "--resolves-source-check",
            "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "checked it, resolves the outstanding flag",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:05:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        entry = latest[self.UID]
        self.assertFalse(entry["prior_unresolved_nsc"])
        self.assertTrue(entry["resolves_source_check"])

        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=approved))

        proposal = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID,
            calibration_dir=self.calibration_dir, _approved_versions_override=approved,
        )
        self.assertEqual(proposal["registry_written"], False)

    def test_attested_resolution_via_change_also_verifies_and_promotes(self):
        prior = self.prior_dok_for(self.UID)
        chosen = self.a_different_dok(prior)
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "needs-source-check", "--rationale", "need to check first",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:10:00-04:00",
        )
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "change", "--chosen-dok", str(chosen), "--item-basis", "adapted",
            "--resolves-source-check",
            "--provenance", self.resolving_provenance_for(self.UID),
            "--rationale", "checked it, this actually needs strategic reasoning",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:15:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        entry = latest[self.UID]
        self.assertEqual(entry["decision"], "change")
        self.assertFalse(entry["prior_unresolved_nsc"])

        approved = {"v0.2": FAR_PAST_APPROVAL}
        self.assertTrue(dr.entry_is_verified(entry, _approved_versions_override=approved))

        proposal = dr.build_promotion_proposal(
            self.plan, self.registry_path, self.log_path, self.UID,
            calibration_dir=self.calibration_dir, _approved_versions_override=approved,
        )
        self.assertEqual(proposal["registry_written"], False)

    def test_resolves_source_check_with_no_nsc_rejected_at_entry(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--resolves-source-check",
                "--provenance", self.resolving_provenance_for(self.UID),
                "--rationale", "nothing to resolve here",
                "--rubric-version", "v0.2",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_resolves_source_check_with_nonresolving_provenance_rejected_at_entry(self):
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "needs-source-check", "--rationale", "need to check first",
            "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:00:00-04:00",
        )
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--resolves-source-check",
                "--provenance", "just my word, no scheme",
                "--rationale", "checked it",
                "--rubric-version", "v0.2", "--reviewed-at", "2026-07-19T09:05:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_resolves_source_check_rejected_with_needs_source_check_disposition(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "needs-source-check", "--resolves-source-check",
                "--rationale", "cannot both raise and resolve in one entry",
                "--rubric-version", "v0.2",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)


# ---------------------------------------------------------------------------
# NT6 F7b: DOK domain (4) is rejected in three independent places.
# ---------------------------------------------------------------------------

class TestDokDomainModulePathGuard(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"

    def test_build_review_record_raises_on_dok4(self):
        uid_to_item, _uid_to_line, _duplicates = dr.build_uid_index(self.plan)
        item = uid_to_item[self.UID]
        with self.assertRaises(ValueError):
            dr.build_review_record(
                item=item, reviewed_by="lynn", disposition="change", chosen_dok=4,
                rationale="x", provenance="y", rubric_version="v0.2", note="",
                reviewed_at="2026-01-01T00:00:00-04:00", calibration_dir=self.calibration_dir,
                item_basis="adapted",
            )

    def test_validate_review_args_rejects_dok4(self):
        uid_to_item, _uid_to_line, _duplicates = dr.build_uid_index(self.plan)
        item = uid_to_item[self.UID]
        args = types.SimpleNamespace(
            reviewed_by="lynn", rubric_version="v0.2", chosen_dok=4,
            disposition="change", rationale="x", provenance="y",
            item_basis="adapted", resolves_source_check=False,
        )
        error = dr._validate_review_args(
            args, prior_dok=3, calibration_dir=self.calibration_dir,
            prior_entries_for_uid=[], item=item,
        )
        self.assertIsNotNone(error)
        self.assertIn("DOK", error)

    def test_cli_argparse_rejects_dok4_exit_2(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
                "--disposition", "change", "--chosen-dok", "4",
                "--item-basis", "adapted", "--rationale", "x", "--provenance", "y",
                "--rubric-version", "v0.2",
            )
        self.assertEqual(ctx.exception.code, 2)
        self.assert_log_unchanged(before)


# ---------------------------------------------------------------------------
# NT6 F4: invalid-entry state.
# ---------------------------------------------------------------------------

class TestInvalidEntryState(DokReviewTestBase):
    UID = "iu_e32a6f7f8909"  # wave 0

    def _craft(self, **overrides):
        entry = {
            "item_uid": self.UID, "registry_line": 34, "item_id": "3-5-lq-q1a",
            "lesson": "3-5", "reviewed_by": "lynn", "reviewed_at": "2026-07-19T09:00:00-04:00",
            "recorded_at": "2026-07-19T09:00:01-04:00", "prior_dok": 2, "reviewer_dok": 2,
            "current_dok": 2, "new_dok": None, "decision": "confirm", "te_bucket": None,
            "match_quality": "none", "disagreement_resolved": False, "note": "",
            "rubric_version": "v0.2", "rationale": "", "provenance": "",
            "provenance_resolved": False, "confirmation_basis": "rule-2-adjacent-unsourced",
            "item_basis": None, "resolves_source_check": False, "prior_unresolved_nsc": False,
        }
        entry.update(overrides)
        return entry

    def test_empty_reviewer_is_invalid_entry(self):
        self.craft_log_lines([self._craft(reviewed_by="   ")])
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "invalid-entry",
        )

    def test_unknown_decision_is_invalid_entry(self):
        self.craft_log_lines([self._craft(decision="mystery")])
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "invalid-entry",
        )

    def test_bad_timestamp_is_invalid_entry(self):
        self.craft_log_lines([self._craft(reviewed_at="not-a-timestamp")])
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "invalid-entry",
        )

    def test_invalid_entry_is_not_reviewed_once(self):
        self.craft_log_lines([self._craft(decision="mystery")])
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        state = dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path)
        self.assertNotEqual(state, "reviewed_once")
        self.assertEqual(state, "invalid-entry")

    def test_compute_progress_counts_invalid_entry_separately(self):
        self.craft_log_lines([self._craft(decision="mystery")])
        progress = dr.compute_progress(self.plan, self.log_path, approvals_path=self.approvals_path)
        self.assertEqual(progress["overall"]["invalid_entry"], 1)
        self.assertEqual(progress["waves"]["0"]["invalid_entry"], 1)
        self.assertEqual(progress["overall"]["reviewed_once_or_better"], 0)

    def test_queue_state_filter_accepts_invalid_entry(self):
        self.craft_log_lines([self._craft(decision="mystery")])
        rows = dr.get_queue_rows(self.plan, self.log_path, approvals_path=self.approvals_path)
        row = next(r for r in rows if r["item_uid"] == self.UID)
        self.assertEqual(row["tool_state"], "invalid-entry")


# ---------------------------------------------------------------------------
# NT6 round 3, G3: entry_is_malformed is DECISION-SPECIFIC, not just the
# three universal fields (reviewed_by / reviewed_at / decision).
# ---------------------------------------------------------------------------

class TestDecisionSpecificMalformedness(DokReviewTestBase):
    UID = "iu_e32a6f7f8909"  # 3-5-lq-q1a, wave 0, lesson 3-5, dok 2

    def _craft(self, **overrides):
        entry = {
            "item_uid": self.UID, "registry_line": 34, "item_id": "3-5-lq-q1a",
            "lesson": "3-5", "reviewed_by": "lynn", "reviewed_at": "2026-07-19T09:00:00-04:00",
            "recorded_at": "2026-07-19T09:00:01-04:00", "prior_dok": 2, "reviewer_dok": 2,
            "current_dok": 2, "new_dok": None, "decision": "confirm", "te_bucket": None,
            "match_quality": "none", "disagreement_resolved": False, "note": "",
            "rubric_version": "v0.2", "rationale": "", "provenance": "",
            "provenance_resolved": False, "confirmation_basis": "rule-2-adjacent-unsourced",
            "item_basis": None, "resolves_source_check": False, "prior_unresolved_nsc": False,
        }
        entry.update(overrides)
        return entry

    def _assert_invalid_entry(self, **overrides):
        self.craft_log_lines([self._craft(**overrides)])
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "invalid-entry",
        )
        progress = dr.compute_progress(self.plan, self.log_path, approvals_path=self.approvals_path)
        self.assertEqual(progress["overall"]["invalid_entry"], 1)
        self.assertEqual(progress["overall"]["reviewed_once_or_better"], 0)

    def test_change_missing_rationale_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="change", new_dok=2, rationale="", provenance="y",
            item_basis="adapted", confirmation_basis=None,
        )

    def test_change_whitespace_only_rationale_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="change", new_dok=2, rationale="   ", provenance="y",
            item_basis="adapted", confirmation_basis=None,
        )

    def test_change_missing_provenance_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="change", new_dok=2, rationale="x", provenance="",
            item_basis="adapted", confirmation_basis=None,
        )

    def test_change_missing_item_basis_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="change", new_dok=2, rationale="x", provenance="y",
            item_basis=None, confirmation_basis=None,
        )

    def test_change_invalid_item_basis_value_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="change", new_dok=2, rationale="x", provenance="y",
            item_basis="bogus-basis", confirmation_basis=None,
        )

    def test_change_bad_new_dok_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="change", new_dok=None, rationale="x", provenance="y",
            item_basis="adapted", confirmation_basis=None,
        )

    def test_change_new_dok_out_of_domain_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="change", new_dok=4, rationale="x", provenance="y",
            item_basis="adapted", confirmation_basis=None,
        )

    def test_change_complete_shape_is_not_invalid_entry(self):
        # Sanity check: a fully complete change is "reviewed_once", not
        # "invalid-entry" -- this rule only catches structurally incomplete
        # shapes, not merely unverified ones.
        self.craft_log_lines([self._craft(
            decision="change", new_dok=2, rationale="x", provenance="y",
            item_basis="adapted", confirmation_basis=None,
        )])
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "reviewed_once",
        )

    def test_nsc_missing_rationale_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="needs-source-check", rationale="", confirmation_basis=None,
        )

    def test_nsc_whitespace_only_rationale_is_invalid_entry(self):
        self._assert_invalid_entry(
            decision="needs-source-check", rationale="   ", confirmation_basis=None,
        )

    def test_confirm_unknown_confirmation_basis_is_invalid_entry(self):
        self._assert_invalid_entry(confirmation_basis="bogus-basis")

    def test_confirm_missing_confirmation_basis_is_invalid_entry(self):
        self._assert_invalid_entry(confirmation_basis=None)

    def test_confirm_valid_confirmation_basis_is_not_invalid_entry(self):
        # Sanity check: confirm doesn't require rationale/provenance, only
        # a recognized confirmation_basis -- this crafted entry (empty
        # rationale/provenance, valid confirmation_basis) is "reviewed_once".
        self.craft_log_lines([self._craft()])
        entries = dr.read_log_entries(self.log_path)
        latest = dr.latest_entries_by_uid(entries)
        self.assertEqual(
            dr.tool_state_for(self.UID, latest, approvals_path=self.approvals_path), "reviewed_once",
        )


# ---------------------------------------------------------------------------
# NT6 round 3, G5: DOK_NOT_DIFFICULTY_NOTE is rubric rule 4, VERBATIM, and
# appears in both CLI --help epilogs (and README.md, checked by the manager
# independently).
# ---------------------------------------------------------------------------

class TestDokNotDifficultyNoteRubricRule4Verbatim(unittest.TestCase):
    def test_contains_rule4_phrasing_not_old_paraphrase(self):
        # "context-heavy" only appears in the real rubric-rule-4 wording;
        # the OLD paraphrase's "KIND of thinking an item requires" phrasing
        # must be gone (the verbatim text says "kind of thinking required").
        self.assertIn("context-heavy", dr.DOK_NOT_DIFFICULTY_NOTE)
        self.assertNotIn("KIND of thinking an item requires", dr.DOK_NOT_DIFFICULTY_NOTE)
        self.assertIn("kind of thinking required", dr.DOK_NOT_DIFFICULTY_NOTE)

    def test_appears_verbatim_in_top_level_and_review_help_epilogs(self):
        parser = dr.build_arg_parser()
        top_level_help = parser.format_help()
        self.assertIn(dr.DOK_NOT_DIFFICULTY_NOTE, top_level_help)

        review_parser = None
        for sub in parser._subparsers._group_actions:
            if "review" in sub.choices:
                review_parser = sub.choices["review"]
                break
        self.assertIsNotNone(review_parser)
        review_help = review_parser.format_help()
        self.assertIn(dr.DOK_NOT_DIFFICULTY_NOTE, review_help)


# ---------------------------------------------------------------------------
# NT6 F1: recorded_at is tool-generated, present, parseable, and distinct
# from the reviewer-supplied reviewed_at.
# ---------------------------------------------------------------------------

class TestRecordedAtStamp(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"

    def test_recorded_at_present_parseable_and_distinct_from_reviewed_at(self):
        historical = "2020-05-01T00:00:00-04:00"
        self.run_cli(
            "review", "--item-uid", self.UID, "--reviewed-by", "lynn",
            "--disposition", "confirm", "--rubric-version", "v0.2",
            "--reviewed-at", historical,
        )
        entry = self.latest_for(self.UID)
        self.assertIn("recorded_at", entry)
        recorded_at = dr.parse_iso(entry["recorded_at"])
        self.assertIsNotNone(recorded_at)
        self.assertEqual(entry["reviewed_at"], historical)
        self.assertNotEqual(entry["recorded_at"], historical)
        self.assertGreater(recorded_at, dr.parse_iso(historical))

    def test_no_cli_flag_can_set_recorded_at(self):
        parser = dr.build_arg_parser()
        review_actions = {
            action.dest for sub in parser._subparsers._group_actions
            for choice_parser in sub.choices.values()
            for action in choice_parser._actions
        }
        self.assertNotIn("recorded_at", review_actions)


# ---------------------------------------------------------------------------
# R4 (NT7-R remediation, Fix R4): read_log_entries fails CLOSED on any
# structural log problem, mirroring load_rubric_approvals()'s policy for
# rubric_approvals.json EXACTLY -- one poisoned line poisons the WHOLE log
# (never a best-effort partial parse). A MISSING file is the sole exception
# (still silently [], and with NO warning printed).
# ---------------------------------------------------------------------------

class TestReadLogEntriesFailsClosed(DokReviewTestBase):
    UID = "iu_3b42ab3340d5"  # wave 0, dok 3, lesson 3-5, registry_line 41

    def _good_line(self):
        return {
            "item_uid": self.UID, "registry_line": 41, "item_id": "3-5-savvas-q27",
            "lesson": "3-5", "reviewed_by": "lynn", "reviewed_at": "2026-07-19T09:00:00-04:00",
            "recorded_at": "2026-07-19T09:00:01-04:00", "prior_dok": 3, "reviewer_dok": 3,
            "current_dok": 3, "new_dok": None, "decision": "confirm", "te_bucket": None,
            "match_quality": "none", "disagreement_resolved": False, "note": "",
            "rubric_version": "v0.2", "rationale": "matches", "provenance": "",
            "provenance_resolved": False, "confirmation_basis": "rule-2-adjacent-unsourced",
            "item_basis": None, "resolves_source_check": False, "prior_unresolved_nsc": False,
        }

    def _write_raw_lines(self, *raw_lines):
        with open(self.log_path, "w", encoding="utf-8") as f:
            for raw in raw_lines:
                f.write(raw)
                f.write("\n")

    def test_invalid_json_line_poisons_whole_log(self):
        # (a) one invalid-JSON line among otherwise-valid lines.
        self._write_raw_lines(
            json.dumps(self._good_line(), ensure_ascii=False),
            "{not valid json",
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            entries = dr.read_log_entries(self.log_path)
        self.assertEqual(entries, [])
        warning = stderr.getvalue()
        self.assertIn(str(self.log_path), warning)
        self.assertIn("treating as NO review entries", warning)
        self.assertIn("fail closed, zero verified", warning)

    def test_non_dict_json_line_poisons_whole_log(self):
        # (b) a syntactically-valid, non-dict JSON line (a list).
        self._write_raw_lines(
            json.dumps(self._good_line(), ensure_ascii=False),
            json.dumps([1, 2]),
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            entries = dr.read_log_entries(self.log_path)
        self.assertEqual(entries, [])
        self.assertIn("non-object entry", stderr.getvalue())

    def test_non_dict_json_scalars_also_poison_whole_log(self):
        # (b) continued: a bare string and a bare number are also non-dict.
        for raw in ('"just a string"', "42"):
            with self.subTest(raw=raw):
                self._write_raw_lines(raw)
                entries = dr.read_log_entries(self.log_path)
                self.assertEqual(entries, [])

    def test_missing_item_uid_poisons_whole_log(self):
        # (c) a dict line missing item_uid entirely.
        bad = self._good_line()
        del bad["item_uid"]
        self._write_raw_lines(
            json.dumps(self._good_line(), ensure_ascii=False),
            json.dumps(bad, ensure_ascii=False),
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            entries = dr.read_log_entries(self.log_path)
        self.assertEqual(entries, [])
        self.assertIn("missing or blank item_uid", stderr.getvalue())

    def test_blank_item_uid_poisons_whole_log(self):
        # (c) continued: item_uid present but blank/whitespace-only.
        bad = self._good_line()
        bad["item_uid"] = "   "
        self._write_raw_lines(json.dumps(bad, ensure_ascii=False))
        entries = dr.read_log_entries(self.log_path)
        self.assertEqual(entries, [])

    def test_missing_file_returns_empty_with_no_warning(self):
        # (d) missing file still means "no reviews yet" -- silently, no warning.
        missing = Path(self.tmpdir.name) / "does_not_exist_log.jsonl"
        self.assertFalse(missing.exists())
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            entries = dr.read_log_entries(missing)
        self.assertEqual(entries, [])
        self.assertEqual(stderr.getvalue(), "")

    def test_poisoned_log_yields_unreviewed_for_uid_with_otherwise_valid_entry(self):
        # (e) end-to-end: the SAME log has one perfectly good entry for
        # self.UID plus one poisoned line elsewhere in the file -- the
        # whole log must still fail closed, so self.UID reads back as
        # "unreviewed" (zero verified), not "reviewed_once".
        self._write_raw_lines(
            json.dumps(self._good_line(), ensure_ascii=False),
            "{not valid json",
        )
        rows = dr.get_queue_rows(self.plan, self.log_path, approvals_path=self.approvals_path)
        row = next(r for r in rows if r["item_uid"] == self.UID)
        self.assertEqual(row["tool_state"], "unreviewed")

        progress = dr.compute_progress(self.plan, self.log_path, approvals_path=self.approvals_path)
        self.assertEqual(progress["overall"]["reviewed_once_or_better"], 0)
        self.assertEqual(progress["overall"]["verified"], 0)

    # (f) NOTE: no existing test in this suite asserted the OLD
    # json.JSONDecodeError-raises-uncaught behavior for read_log_entries --
    # grep confirms no test constructed a genuinely invalid-JSON log line
    # before this fix, so nothing needed reconciling.


# ---------------------------------------------------------------------------
# R5 (NT7-R remediation, Fix R5): a `confirm` on a derived-match item, or on
# an "exact-disagreement" item (match_quality == "exact" but the wave plan's
# own dok falls outside te_bucket), REQUIRES a non-empty --rationale
# documenting the reviewer's judgment. Enforced at both reject-at-entry
# (_validate_review_args) and promotion chain-validation (_validate_chain_entry).
# ---------------------------------------------------------------------------

class TestConfirmRationaleRequiredForWeakTeSignal(DokReviewTestBase):
    # Real wave-plan item, match_quality "derived" (one of exactly 4 in the
    # current plan -- see the module-level audit run during this fix):
    # wave 1, lesson 4-3, dok 3, te_bucket [2], id has no derivable
    # calibration identity (split-part practice id), so provenance is
    # irrelevant to this test -- only --rationale is under test.
    DERIVED_UID = "iu_c4927f55e313"

    # Real wave-plan item, match_quality "exact" with dok INSIDE te_bucket --
    # the ordinary AGREEING case, unaffected by R5.
    EXACT_AGREE_UID = "iu_3d5d21133498"

    def test_rationale_less_confirm_on_derived_match_rejected_at_entry(self):
        before = self.log_bytes_or_none()
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(
                "review", "--item-uid", self.DERIVED_UID, "--reviewed-by", "lynn",
                "--disposition", "confirm", "--rubric-version", "v0.2",
                "--reviewed-at", "2026-07-19T09:00:00-04:00",
            )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assert_log_unchanged(before)

    def test_confirm_on_derived_match_with_rationale_accepted(self):
        self.run_cli(
            "review", "--item-uid", self.DERIVED_UID, "--reviewed-by", "lynn",
            "--disposition", "confirm",
            "--rationale", "TE bucket here was inferred, not read directly off the TE page; checked by hand and it holds",
            "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T09:00:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["decision"], "confirm")
        self.assertEqual(entries[0]["item_uid"], self.DERIVED_UID)

    def test_rationale_less_confirm_on_exact_agreeing_item_still_accepted(self):
        # match_quality "exact" with dok INSIDE te_bucket -- unaffected by
        # R5, rationale stays optional (unchanged from before this fix).
        self.run_cli(
            "review", "--item-uid", self.EXACT_AGREE_UID, "--reviewed-by", "lynn",
            "--disposition", "confirm", "--rubric-version", "v0.2",
            "--reviewed-at", "2026-07-19T09:00:00-04:00",
        )
        entries = dr.read_log_entries(self.log_path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["decision"], "confirm")

    def _synthetic_exact_disagreement_item(self):
        # Zero real items are in the "exact" + dok-outside-te_bucket state
        # in the current wave plan (verified during this fix) -- craft one
        # directly (bypassing the CLI/plan) to prove the gate still catches
        # a future or hand-crafted one, per the Fable-locked scope.
        return {
            "item_uid": "iu_synthetic_exact_disagreement", "registry_line": 41,
            "id": "3-5-savvas-q27", "lesson": "3-5", "dok": 3,
            "te_bucket": [1, 2], "match_quality": "exact",
        }

    def test_rationale_less_confirm_on_synthetic_exact_disagreement_item_rejected(self):
        item = self._synthetic_exact_disagreement_item()
        args = types.SimpleNamespace(
            reviewed_by="lynn", rubric_version="v0.2", chosen_dok=None,
            disposition="confirm", rationale="", provenance="",
            item_basis=None, resolves_source_check=False,
        )
        error = dr._validate_review_args(
            args, prior_dok=item["dok"], calibration_dir=self.calibration_dir,
            prior_entries_for_uid=[], item=item,
        )
        self.assertIsNotNone(error)
        self.assertIn("--rationale", error)
        self.assertIn("exact-disagreement", error)

    def test_confirm_on_synthetic_exact_disagreement_item_with_rationale_accepted(self):
        item = self._synthetic_exact_disagreement_item()
        args = types.SimpleNamespace(
            reviewed_by="lynn", rubric_version="v0.2", chosen_dok=None,
            disposition="confirm",
            rationale="TE bucket says 1/2 but the wave plan carries dok 3 -- judgment call, prior_dok stands",
            provenance="", item_basis=None, resolves_source_check=False,
        )
        error = dr._validate_review_args(
            args, prior_dok=item["dok"], calibration_dir=self.calibration_dir,
            prior_entries_for_uid=[], item=item,
        )
        self.assertIsNone(error)

    def test_promote_rejects_crafted_rationale_less_derived_confirm_naming_position(self):
        entry = {
            "item_uid": self.DERIVED_UID, "registry_line": 900,
            "item_id": "4-3-savvas-q36-partC-evaluate-fairness", "lesson": "4-3",
            "reviewed_by": "lynn", "reviewed_at": "2026-07-19T09:00:00-04:00",
            "recorded_at": "2026-07-19T09:00:01-04:00", "prior_dok": 3, "reviewer_dok": 3,
            "current_dok": 3, "new_dok": None, "decision": "confirm", "te_bucket": [2],
            "match_quality": "derived", "disagreement_resolved": False, "note": "",
            "rubric_version": "v0.2", "rationale": "", "provenance": "",
            "provenance_resolved": False, "confirmation_basis": "rule-2-adjacent-unsourced",
            "item_basis": None, "resolves_source_check": False, "prior_unresolved_nsc": False,
        }
        self.craft_log_lines([entry])
        with self.assertRaises(ValueError) as cm:
            dr.build_promotion_proposal(
                self.plan, self.registry_path, self.log_path, self.DERIVED_UID,
                calibration_dir=self.calibration_dir, approvals_path=self.approvals_path,
            )
        msg = str(cm.exception)
        self.assertIn("#1", msg)
        self.assertIn("derived-match", msg)


if __name__ == "__main__":
    unittest.main()
