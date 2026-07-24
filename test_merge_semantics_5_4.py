"""test_merge_semantics_5_4.py -- durable regression suite for the
RC-authorized 22-pair Lesson 5-4 merge (rc-merge-auth-5-4-2026-07-23).

WHY THIS FILE EXISTS (NT11 SUB-D, D1-HIGH remediation): the acceptance-gate
proofs for the merge were originally built as a one-off scratchpad harness
(nt11_gates/run_gates.py) -- useful for a single verification run, but a
future edit to qb.py, the dedup builder, or any consumer artifact could
silently reintroduce a leaked merged-alias row or a chained/dangling alias
with nothing in the normal test suite to catch it. This module PORTS those
proofs into a durable, repo-committed test so `python -m pytest` (or
`python test_merge_semantics_5_4.py`) catches that regression going forward,
the same way tools/dok-review/test_dok_review.py and
inventory/dok-workflow/test_cross_consumer_projection.py already guard their
own surfaces.

STRUCTURE -- one class per surface (so later review findings can slot in as
extra test methods without restructuring):
  TestQbSelectorSemantics        -- qb.py's get/select/get_for_packet, both
                                     regimes (22 merge-resolved vs. 63
                                     untouched-ambiguous), plus hermetic
                                     negatives.
  TestAliasMapInvariants         -- committed item_uid_alias_map.json's
                                     resolved_alias entries + global one-hop
                                     invariants, plus hermetic negatives run
                                     against the HARDENED builder
                                     (inventory/dedup/build_item_uid_map.py)
                                     via subprocess with explicit scratch
                                     in/out paths.
  TestHistoricalLookupEitherUid  -- either uid (alias or survivor) of a
                                     merged pair resolves to the correct live
                                     registry row via the committed map.
  TestDualDenominatorReconciliation -- the five committed consumer artifacts
                                     (+ the alias map + qb.stats()) all agree
                                     900 == 878 + 22 (and 85 == 22 + 63).
  TestConsoleResolvedPairs       -- console_data.json's section2 pairs carry
                                     resolved_alias (ambient); the
                                     HTML-embedding-of-resolved-payloads
                                     check is SKIPPED pending a concurrent,
                                     not-yet-landed console-template change
                                     (see the class docstring for exactly
                                     why and how to un-skip it).
  TestChangeDetectionSweep       -- env-gated (NT11_CHANGE_SWEEP=1), skipped
                                     by default so normal lesson-prep work
                                     isn't disrupted; for merge-operation
                                     windows only.

HERMETICITY: every test that needs a registry it can corrupt on purpose
(dangling alias, self-alias, cross-group chain, alias-row-never-emitted)
builds a SYNTHETIC registry inside a fresh tempfile.TemporaryDirectory() --
never the real questionbank/registry.jsonl. qb.py locates its registry via
the module-level `qb.REGISTRY` Path (set once at import time from
`Path(__file__).resolve().parent`); hermetic qb-facing tests monkeypatch
that attribute for the duration of one test and restore it in a `finally`
block (see `_patched_qb_registry`). The dedup-builder hermetic tests never
monkeypatch anything -- they invoke the builder as a subprocess with
explicit `argv[1]` (registry) / `argv[2]` (output) scratch paths, exactly as
its own CLI contract supports, so the real
inventory/dedup/item_uid_alias_map.json is never opened for writing.

Tests NOT marked hermetic in their docstring are AMBIENT: they read the
real, committed repository files (questionbank/registry.jsonl,
inventory/dedup/item_uid_alias_map.json, the five consumer artifacts, qb.py
itself via `import qb`). They are still read-only -- nothing in this module
ever opens a real repository file in a write mode.

NAMED FROZEN-BASELINE PINS (rc-merge-auth-5-4-2026-07-23; re-pinned as a
NAMED update for nt14-ingest-4-1-2026-07-23 -- the NT14 Lesson 4-1
optional-catalog ingestion appended 19 rows, availability=="optional-catalog",
at registry lines 901-919; the first 900 lines are byte-identical to the
pre-NT14 registry. If the registry is ever touched again by an authorized
change these numbers may legitimately move -- re-derive and re-pin
deliberately, don't just bump the constant to make the suite pass):
    919 registry rows == 878 required-active + 19 optional-catalog
                          + 22 merged-alias
    85 ambiguous legacy ids = 22 resolved (this merge) + 63 unresolved
       (the 19 new 4-1 ids are all unambiguous single-uid groups)
    merged_at        == "2026-07-23T00:53:21-04:00"  (offset-aware ISO-8601)
    authorization_record_id == "rc-merge-auth-5-4-2026-07-23"
    optional-catalog record id == "nt14-ingest-4-1-2026-07-23"

Run with:  python test_merge_semantics_5_4.py
   (or)    python -m pytest test_merge_semantics_5_4.py -q
Merge-operation change sweep (opt-in, not run by default):
           NT11_CHANGE_SWEEP=1 python -m pytest test_merge_semantics_5_4.py -q
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
import qb  # noqa: E402  -- the module under test; REPO_ROOT is on sys.path above

REGISTRY_PATH = REPO_ROOT / "questionbank" / "registry.jsonl"
ALIAS_MAP_PATH = REPO_ROOT / "inventory" / "dedup" / "item_uid_alias_map.json"
BUILDER_PATH = REPO_ROOT / "inventory" / "dedup" / "build_item_uid_map.py"
WAVE_PLAN_PATH = REPO_ROOT / "inventory" / "dok-workflow" / "dok_wave_plan.json"
CONTENT_READINESS_INVENTORY_PATH = REPO_ROOT / "inventory" / "content_readiness_inventory.json"
DASHBOARD_PATH = REPO_ROOT / "inventory" / "dashboard" / "content_readiness.json"
CONSOLE_DATA_PATH = REPO_ROOT / "inventory" / "decision-console" / "console_data.json"
CONSOLE_HTML_PATH = REPO_ROOT / "inventory" / "decision-console" / "TEACHER_DECISION_CONSOLE.html"
CONSOLE_HTML_TEMPLATE_PATH = REPO_ROOT / "inventory" / "decision-console" / "console_template.html"
PROVENANCE_AUDIT_PATH = REPO_ROOT / "inventory" / "provenance-audit" / "provenance_audit_data.json"
MERGE_WINDOW_MANIFEST_PATH = REPO_ROOT / "nt11_merge_window_manifest.json"
MANIFEST_ROOT_DIRS = ("inventory", "tools")

# ---- frozen baseline pins (rc-merge-auth-5-4-2026-07-23; TOTAL_ROWS and the
# new OPTIONAL_CATALOG_ROWS re-pinned as a NAMED update for
# nt14-ingest-4-1-2026-07-23: 919 == 878 + 19 + 22) ---------------------------
FROZEN_MERGED_AT = "2026-07-23T00:53:21-04:00"
FROZEN_AUTH_RECORD_ID = "rc-merge-auth-5-4-2026-07-23"
NT14_RECORD_ID = "nt14-ingest-4-1-2026-07-23"
FROZEN_TOTAL_ROWS = 919
FROZEN_MERGED_ALIAS_ROWS = 22
FROZEN_ACTIVE_ROWS = 878
FROZEN_OPTIONAL_CATALOG_ROWS = 19
FROZEN_AMBIGUOUS_LEGACY_IDS = 85
FROZEN_UNRESOLVED_AMBIGUOUS = 63


# =============================================================================
# Shared helpers
# =============================================================================

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_registry_rows():
    """1-based line_no -> parsed dict, read fresh from the live registry."""
    rows = {}
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rows[line_no] = json.loads(line)
    return rows


def compute_item_uid(lesson, source, prompt):
    """Same published algorithm as qb.py's _item_uid_for_row() and
    inventory/dedup/build_item_uid_map.py's compute_item_uid() -- kept as an
    independent local implementation (rather than reaching into qb's
    "private" helper) so this suite doesn't silently start testing itself
    if qb.py's internals are ever refactored."""
    if prompt is None:
        prompt = ""
    prompt_sha1 = hashlib.sha1(prompt.encode("utf-8")).hexdigest()
    basis = f"{lesson}|{source}|{prompt_sha1}"
    return "iu_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


def resolved_pairs_from_committed_map():
    """The 22 merge-resolved pairs, derived ENTIRELY from the committed
    inventory/dedup/item_uid_alias_map.json (never hardcoded), each with its
    two registry lines cross-referenced from the entry's own item_uids list."""
    alias_map = load_json(ALIAS_MAP_PATH)["alias_map"]
    pairs = []
    for legacy_id, entry in alias_map.items():
        ra = entry.get("resolved_alias")
        if ra is None:
            continue
        by_uid = {u["item_uid"]: u["registry_line"] for u in entry["item_uids"]}
        pairs.append({
            "legacy_id": legacy_id,
            "alias_uid": ra["alias_uid"],
            "survivor_uid": ra["survivor_uid"],
            "merged_at": ra["merged_at"],
            "authorization_record_id": ra["authorization_record_id"],
            "alias_line": by_uid.get(ra["alias_uid"]),
            "survivor_line": by_uid.get(ra["survivor_uid"]),
        })
    return pairs


def unresolved_ambiguous_entries():
    """legacy_id -> alias_map entry, for every ambiguous group the merge did
    NOT resolve (no resolved_alias key)."""
    alias_map = load_json(ALIAS_MAP_PATH)["alias_map"]
    return {
        legacy_id: entry
        for legacy_id, entry in alias_map.items()
        if entry.get("ambiguous") and "resolved_alias" not in entry
    }


@contextmanager
def _patched_qb_registry(path):
    """Point qb.REGISTRY at a synthetic file for the duration of the `with`
    block, always restoring the real path afterward (even on exception) --
    qb.py locates its registry via this single module-level Path attribute,
    re-read fresh on every load() call, so this is the clean hermetic seam."""
    original = qb.REGISTRY
    try:
        qb.REGISTRY = Path(path)
        yield
    finally:
        qb.REGISTRY = original


def write_registry(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def make_row(id_, lesson, source, prompt, **extra):
    row = {
        "id": id_, "lesson": lesson, "source": source, "page": None, "image": None,
        "has_visual": False, "visual_type": "none", "visual_needs_cleanup": False,
        "visual_clean_asset": None, "prompt": prompt, "answers": [], "correct": None,
        "dok": 1, "dok_rationale": "", "topics": [], "tags": [], "used_in": [],
        "notes": "", "created_at": "2026-01-01",
    }
    row.update(extra)
    return row


def marker_fields(alias_of, merged_at=FROZEN_MERGED_AT, record_id=FROZEN_AUTH_RECORD_ID,
                   sha256="0" * 64):
    return {
        "status": "merged-alias",
        "alias_of": alias_of,
        "merged_at": merged_at,
        "merge_authorization": {"record_id": record_id, "sha256": sha256},
    }


def _sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_manifest_files():
    """Yield (relpath_posix, abspath) for every file under inventory/ and
    tools/ (recursive), excluding any __pycache__ directory. The manifest
    file itself lives at REPO_ROOT (not inside either root dir), so there
    is no self-reference to guard against."""
    for root_name in MANIFEST_ROOT_DIRS:
        root_dir = REPO_ROOT / root_name
        if not root_dir.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in sorted(filenames):
                abspath = Path(dirpath) / fn
                relpath = abspath.relative_to(REPO_ROOT).as_posix()
                yield relpath, abspath


def _diff_manifest_files(expected_files, current_files):
    """Pure diff helper over two {relpath: sha256} dicts -> (new_on_disk,
    missing_on_disk, mismatched), each a sorted list of relpaths. Factored
    out from TestChangeDetectionSweep.test_manifest_hash_layer so its
    correctness can be unit-tested directly against synthetic in-memory
    dicts (see TestManifestDiffLogic below) without touching disk or
    needing NT11_CHANGE_SWEEP=1."""
    missing_on_disk = sorted(set(expected_files) - set(current_files))
    new_on_disk = sorted(set(current_files) - set(expected_files))
    mismatched = sorted(
        relpath for relpath in (set(expected_files) & set(current_files))
        if expected_files[relpath] != current_files[relpath]
    )
    return new_on_disk, missing_on_disk, mismatched


def generate_merge_window_manifest():
    """Regenerate nt11_merge_window_manifest.json (repo root) -- a frozen
    hash snapshot of every file under inventory/ and tools/, for THIS merge
    window (rc-merge-auth-5-4-2026-07-23).

    WHY: TestChangeDetectionSweep's git-status check wholesale-allows the
    `inventory` and `tools` directory tokens, because both are wholly
    untracked in git (never git-added) -- git collapses an entirely
    untracked directory to a single "?? inventory/" line with no per-file
    diff capability, so a change to any ONE file inside either tree is
    invisible to git status alone (Codex review D2). This manifest closes
    that blind spot: TestChangeDetectionSweep.test_manifest_hash_layer
    hashes every file under both roots and diffs against this snapshot.

    Deliberately invoked ONLY via `python test_merge_semantics_5_4.py
    --regen-manifest` -- NEVER during a normal test run (see the __main__
    guard at the bottom of this file) -- so a failing
    test_manifest_hash_layer can never be silently made to pass by an
    automatic regeneration. A future, legitimate merge window regenerates
    this deliberately, as a NAMED update -- the same discipline the other
    suites use for their frozen pins (rc-merge-auth-5-4-2026-07-23 cited
    throughout this module)."""
    files = {relpath: _sha256_of(abspath) for relpath, abspath in _iter_manifest_files()}
    manifest = {
        "generated_by": "test_merge_semantics_5_4.py --regen-manifest",
        "generated_at": datetime.now().astimezone().isoformat(),
        "authorization_record_id": FROZEN_AUTH_RECORD_ID,
        # nt14-ingest-4-1-2026-07-23: this snapshot was deliberately
        # regenerated as the NAMED update closing the NT14 optional-catalog
        # ingestion window (19 Lesson 4-1 rows; dedup map, wave plan, base
        # inventory, dashboard, console, provenance audit, and course map
        # all regenerated within it).
        "nt14_record_id": NT14_RECORD_ID,
        "note": (
            "Frozen hash snapshot of every file under inventory/ and tools/ "
            "(recursive, __pycache__ excluded), captured for the "
            "rc-merge-auth-5-4-2026-07-23 merge window -- closes the blind "
            "spot where git status collapses a wholly-untracked directory to "
            "one line and so cannot see a content change inside it (Codex "
            "review D2). TestChangeDetectionSweep.test_manifest_hash_layer "
            "hashes every file under these two roots and compares against "
            "this manifest; any addition, removal, or hash mismatch relative "
            "to THIS snapshot fails loudly. Regenerate deliberately for a NEW "
            "merge window (`python test_merge_semantics_5_4.py "
            "--regen-manifest`) -- never regenerate just to make a failing "
            "sweep pass; that defeats the entire point of this file."
        ),
        "root_dirs": list(MANIFEST_ROOT_DIRS),
        "excluded": ["__pycache__"],
        "file_count": len(files),
        "files": dict(sorted(files.items())),
    }
    with open(MERGE_WINDOW_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return manifest


def run_builder(registry_path, output_path, extra_args=()):
    """Invoke the hardened dedup builder as a subprocess with EXPLICIT
    scratch registry/output paths (its own argv[1]/argv[2] CLI contract) --
    never the real inventory/dedup/item_uid_alias_map.json."""
    return subprocess.run(
        [sys.executable, *extra_args, str(BUILDER_PATH), str(registry_path), str(output_path)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


# =============================================================================
# 1. qb.py selector semantics
# =============================================================================

class TestQbSelectorSemantics(unittest.TestCase):
    """qb.get / qb.select / qb.get_for_packet over the real, committed
    registry (AMBIENT) plus hermetic negatives over synthetic registries.

    Two regimes (qb.py's own module docstring, "Codex review C1 fix"):
      - a legacy id whose group contains a merged-alias row (the 22
        RC-authorized pairs): resolves DELIBERATELY to the survivor via
        alias_of, fails loudly on any data-integrity problem.
      - a legacy id whose group has NO merged-alias row (all other
        ambiguous ids, including the 63 still-unresolved of the 85): keeps
        the EXACT pre-merge tie-break -- get() first-match, get_for_packet()
        last-wins, select() retains every row -- unauthorized-for-resolution
        territory, unchanged by rc-merge-auth-5-4-2026-07-23.
    """

    @classmethod
    def setUpClass(cls):
        cls.registry_rows = load_registry_rows()
        cls.alias_meta = load_json(ALIAS_MAP_PATH)["meta"]
        cls.pairs = resolved_pairs_from_committed_map()
        cls.unresolved = unresolved_ambiguous_entries()

    def test_select_returns_878_active_rows_zero_alias(self):
        rows = qb.select()
        self.assertEqual(len(rows), FROZEN_ACTIVE_ROWS)
        self.assertEqual(sum(1 for r in rows if r.get("status") == "merged-alias"), 0)
        # nt14-ingest-4-1-2026-07-23: select() also excludes optional-catalog
        # rows by default, so the default surface stays exactly the 878
        # required-active rows.
        self.assertEqual(
            sum(1 for r in rows if r.get("availability") == "optional-catalog"), 0)
        # self-explaining cross-check against the committed alias map's own meta,
        # so this test doesn't just repeat a magic number (NAMED update for
        # nt14-ingest-4-1-2026-07-23 -- triple split): 878 == 919 - 22 - 19.
        self.assertEqual(
            self.alias_meta["total_rows"]
            - self.alias_meta["merged_alias_rows"]
            - FROZEN_OPTIONAL_CATALOG_ROWS,
            FROZEN_ACTIVE_ROWS,
        )

    def test_all_22_merged_ids_resolve_to_survivor_via_get(self):
        self.assertEqual(len(self.pairs), FROZEN_MERGED_ALIAS_ROWS)
        for pair in self.pairs:
            with self.subTest(legacy_id=pair["legacy_id"]):
                survivor_row = self.registry_rows[pair["survivor_line"]]
                got = qb.get(pair["legacy_id"])
                self.assertIsNotNone(got)
                self.assertNotEqual(got.get("status"), "merged-alias")
                self.assertEqual(got.get("prompt"), survivor_row.get("prompt"))
                self.assertEqual(got.get("dok"), survivor_row.get("dok"))

    def test_all_22_merged_ids_resolve_to_survivor_via_get_for_packet(self):
        ids = [p["legacy_id"] for p in self.pairs]
        rows = qb.get_for_packet(ids)
        self.assertEqual(len(rows), FROZEN_MERGED_ALIAS_ROWS)
        for pair, row in zip(self.pairs, rows):
            with self.subTest(legacy_id=pair["legacy_id"]):
                survivor_row = self.registry_rows[pair["survivor_line"]]
                self.assertNotEqual(row.get("status"), "merged-alias")
                self.assertEqual(row.get("prompt"), survivor_row.get("prompt"))

    def test_hermetic_dangling_alias_of_raises(self):
        """A synthetic registry whose merged-alias row's alias_of points at
        an item_uid that exists nowhere in the registry must make qb raise
        wherever it actually ATTEMPTS resolution (get / get_for_packet),
        never silently emit the alias row's own content or fabricate a
        result. select() is a different contract: it never attempts alias
        resolution at all -- it unconditionally DROPS every
        status=='merged-alias' row before any other filter (see qb.select's
        own comment) -- so for a registry containing only a dangling alias
        row, select() correctly returns an empty list without raising;
        that's the exclusion contract working exactly as designed, not a
        gap in it."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            alias_row = make_row("x-dangle", "U", "S", "prompt-A", **marker_fields("iu_doesnotexist000000"))
            write_registry(reg_path, [alias_row])
            with _patched_qb_registry(reg_path):
                with self.assertRaises((KeyError, ValueError)):
                    qb.get("x-dangle")
                self.assertEqual(qb.select(), [])  # dropped outright, not resolved -- see docstring above
                with self.assertRaises((KeyError, ValueError)):
                    qb.get_for_packet(["x-dangle"])

    def test_hermetic_alias_row_content_never_emitted(self):
        """A synthetic registry with one valid (non-dangling) merged-alias
        pair: get()/select()/get_for_packet() must surface the SURVIVOR's
        prompt, never the alias row's own (superseded) prompt."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            survivor_uid = compute_item_uid("U", "S", "survivor prompt text")
            survivor = make_row("x-pair", "U", "S", "survivor prompt text")
            alias = make_row("x-pair", "U", "S", "ALIAS SUPERSEDED PROMPT -- must never appear",
                              **marker_fields(survivor_uid))
            write_registry(reg_path, [alias, survivor])
            with _patched_qb_registry(reg_path):
                got = qb.get("x-pair")
                self.assertEqual(got["prompt"], "survivor prompt text")
                rows = qb.select()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["prompt"], "survivor prompt text")
                packet = qb.get_for_packet(["x-pair"])
                self.assertEqual(packet[0]["prompt"], "survivor prompt text")
                for r in rows + packet + [got]:
                    self.assertNotIn("ALIAS SUPERSEDED", r["prompt"])

    def test_unresolved_ambiguous_get_for_packet_last_wins_no_exception(self):
        """For a legacy id among the 63 still-unresolved ambiguous groups,
        get_for_packet keeps the EXACT pre-merge tie-break: the row at the
        group's MAX registry_line, no exception (Codex review C1 spec)."""
        self.assertEqual(len(self.unresolved), FROZEN_UNRESOLVED_AMBIGUOUS)
        ids = list(self.unresolved.keys())
        rows = qb.get_for_packet(ids)
        for legacy_id, row in zip(ids, rows):
            with self.subTest(legacy_id=legacy_id):
                entry = self.unresolved[legacy_id]
                max_line = max(u["registry_line"] for u in entry["item_uids"])
                expected = self.registry_rows[max_line]
                self.assertEqual(row.get("prompt"), expected.get("prompt"))
                self.assertEqual(row.get("dok"), expected.get("dok"))

    def test_unresolved_ambiguous_get_returns_first_line_row(self):
        """get() keeps its original loop-and-return-on-first-match
        behavior for the 63: the row at the group's MIN registry_line."""
        for legacy_id, entry in self.unresolved.items():
            with self.subTest(legacy_id=legacy_id):
                min_line = min(u["registry_line"] for u in entry["item_uids"])
                expected = self.registry_rows[min_line]
                got = qb.get(legacy_id)
                self.assertEqual(got.get("prompt"), expected.get("prompt"))

    def test_unresolved_ambiguous_select_retains_both_copies(self):
        """select() (no filters) must retain EVERY row of an unresolved
        ambiguous group -- none of the 63 carry status=='merged-alias', so
        none are dropped by select()'s alias filter."""
        all_rows = qb.select()
        for legacy_id, entry in self.unresolved.items():
            with self.subTest(legacy_id=legacy_id):
                n_expected = len(entry["item_uids"])
                n_got = sum(1 for r in all_rows if r.get("id") == legacy_id)
                self.assertEqual(n_got, n_expected)
                self.assertGreaterEqual(n_got, 2)


# =============================================================================
# 2. alias-map invariants
# =============================================================================

class TestAliasMapInvariants(unittest.TestCase):
    """inventory/dedup/item_uid_alias_map.json's resolved_alias entries
    (AMBIENT) plus hermetic negatives run against the HARDENED builder
    (inventory/dedup/build_item_uid_map.py, NT11 hardening round B1/B2:
    MergeAliasValidationError, global cross-group chain check, -O-proof
    explicit `raise` instead of `assert`)."""

    @classmethod
    def setUpClass(cls):
        cls.meta = load_json(ALIAS_MAP_PATH)["meta"]
        cls.pairs = resolved_pairs_from_committed_map()

    def test_counts_22_resolved_63_unresolved_85_ambiguous(self):
        self.assertEqual(self.meta["ambiguous_legacy_ids"], FROZEN_AMBIGUOUS_LEGACY_IDS)
        self.assertEqual(self.meta["alias_resolved_groups"], FROZEN_MERGED_ALIAS_ROWS)
        self.assertEqual(self.meta["unresolved_ambiguous_groups"], FROZEN_UNRESOLVED_AMBIGUOUS)
        self.assertEqual(
            self.meta["alias_resolved_groups"] + self.meta["unresolved_ambiguous_groups"],
            self.meta["ambiguous_legacy_ids"],
        )

    def test_resolved_alias_fields_complete(self):
        self.assertEqual(len(self.pairs), FROZEN_MERGED_ALIAS_ROWS)
        for pair in self.pairs:
            with self.subTest(legacy_id=pair["legacy_id"]):
                self.assertTrue(pair["alias_uid"])
                self.assertTrue(pair["survivor_uid"])
                self.assertEqual(pair["merged_at"], FROZEN_MERGED_AT)
                self.assertEqual(pair["authorization_record_id"], FROZEN_AUTH_RECORD_ID)

    def test_global_one_hop_invariants(self):
        alias_uids = {p["alias_uid"] for p in self.pairs}
        survivor_uids = {p["survivor_uid"] for p in self.pairs}
        self.assertTrue(alias_uids.isdisjoint(survivor_uids))
        alias_map = load_json(ALIAS_MAP_PATH)["alias_map"]
        for pair in self.pairs:
            entry = alias_map[pair["legacy_id"]]
            entry_uids = {u["item_uid"] for u in entry["item_uids"]}
            self.assertIn(pair["survivor_uid"], entry_uids)
            self.assertIn(pair["alias_uid"], entry_uids)

    def test_hermetic_self_alias_rejected(self):
        """A merged-alias row whose alias_of equals its OWN item_uid must
        be rejected by the hardened builder (nonzero exit,
        MergeAliasValidationError, no output file written)."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            out_path = Path(tmp) / "alias_map.out.json"
            self_uid = compute_item_uid("U", "S", "self-alias prompt")
            row_alias = make_row("y-self", "U", "S", "self-alias prompt", **marker_fields(self_uid))
            row_other = make_row("y-self", "U", "S", "a different prompt to keep the group ambiguous")
            write_registry(reg_path, [row_alias, row_other])
            proc = run_builder(reg_path, out_path)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("MergeAliasValidationError", proc.stdout + proc.stderr)
            self.assertFalse(out_path.exists())

    def test_hermetic_cross_group_chain_rejected(self):
        """NT11 hardening round B1: g1's resolved survivor_uid must not
        collide with the item_uid of a DIFFERENT group's merged-alias row.
        g1: A (merged-alias) -> B. g2: B' (merged-alias, SAME uid basis as
        g1's survivor B) -> C. The cross-group chain must be rejected
        (nonzero exit, MergeAliasValidationError, no output file)."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            out_path = Path(tmp) / "alias_map.out.json"
            uid_b = compute_item_uid("U", "S-B", "prompt-B")  # shared basis
            row_a = make_row("g1", "U", "S-A", "prompt-A", **marker_fields(uid_b))
            row_b = make_row("g1", "U", "S-B", "prompt-B")  # g1 survivor; uid == uid_b
            row_b2 = make_row("g2", "U", "S-B", "prompt-B",  # SAME (lesson,source,prompt) -> SAME uid_b
                               **marker_fields(compute_item_uid("U", "S-C", "prompt-C")))
            row_c = make_row("g2", "U", "S-C", "prompt-C")  # g2 survivor
            write_registry(reg_path, [row_a, row_b, row_b2, row_c])
            proc = run_builder(reg_path, out_path)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("MergeAliasValidationError", proc.stdout + proc.stderr)
            self.assertIn("cross-group", (proc.stdout + proc.stderr).lower())
            self.assertFalse(out_path.exists())

    def test_hermetic_self_alias_rejected_under_dash_O(self):
        """The builder's guards use an explicit `raise` (not `assert`)
        specifically so they survive `python -O` / PYTHONOPTIMIZE -- confirm
        that directly: the self-alias fixture must still fail under -O."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            out_path = Path(tmp) / "alias_map.out.json"
            self_uid = compute_item_uid("U", "S", "self-alias prompt (O)")
            row_alias = make_row("z-self-O", "U", "S", "self-alias prompt (O)", **marker_fields(self_uid))
            row_other = make_row("z-self-O", "U", "S", "a different prompt (O)")
            write_registry(reg_path, [row_alias, row_other])
            proc = run_builder(reg_path, out_path, extra_args=["-O"])
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("MergeAliasValidationError", proc.stdout + proc.stderr)
            self.assertFalse(out_path.exists())


# =============================================================================
# 3. historical lookup by either uid
# =============================================================================

class TestHistoricalLookupEitherUid(unittest.TestCase):
    """AMBIENT: for each of the 22 committed pairs, looking a row up by
    EITHER its alias uid or its survivor uid (via the committed dedup map)
    must land on the correct, correctly-shaped live registry row."""

    def test_alias_and_survivor_uid_both_resolve_correctly(self):
        pairs = resolved_pairs_from_committed_map()
        rows = load_registry_rows()
        self.assertEqual(len(pairs), FROZEN_MERGED_ALIAS_ROWS)
        for pair in pairs:
            with self.subTest(legacy_id=pair["legacy_id"]):
                alias_row = rows[pair["alias_line"]]
                self.assertEqual(alias_row.get("status"), "merged-alias")
                self.assertEqual(alias_row.get("alias_of"), pair["survivor_uid"])

                survivor_row = rows[pair["survivor_line"]]
                self.assertNotEqual(survivor_row.get("status"), "merged-alias")
                self.assertEqual(survivor_row.get("id"), pair["legacy_id"])
                self.assertEqual(alias_row.get("id"), pair["legacy_id"])


# =============================================================================
# 4. dual-denominator reconciliation
# =============================================================================

class TestDualDenominatorReconciliation(unittest.TestCase):
    """AMBIENT: every committed consumer artifact that reports an
    identity_reconciliation block must reconcile 900 == 878 + 22; the alias
    map must reconcile 85 == 22 + 63; qb.stats() must agree. Missing the
    reconciliation block on any surface IS the regression signal -- this
    test fails loudly rather than skipping a surface it can't find one on."""

    def _assert_reconciles(self, label, block):
        # NAMED update for nt14-ingest-4-1-2026-07-23: every consumer
        # artifact now reconciles the TRIPLE split
        # raw == required-active + optional-catalog + merged-alias
        # (919 == 878 + 19 + 22). A missing optional_catalog_identities
        # field IS the regression signal, same as a missing block.
        self.assertIsNotNone(block, f"{label}: missing identity_reconciliation block")
        self.assertEqual(block.get("raw_registry_identities"), FROZEN_TOTAL_ROWS, label)
        self.assertEqual(block.get("merged_alias_identities"), FROZEN_MERGED_ALIAS_ROWS, label)
        self.assertEqual(
            block.get("optional_catalog_identities"), FROZEN_OPTIONAL_CATALOG_ROWS, label)
        self.assertEqual(block.get("active_canonical_items"), FROZEN_ACTIVE_ROWS, label)
        self.assertEqual(
            block["raw_registry_identities"],
            block["active_canonical_items"]
            + block["optional_catalog_identities"]
            + block["merged_alias_identities"],
            label,
        )

    def test_wave_plan_reconciles(self):
        wave = load_json(WAVE_PLAN_PATH)
        self._assert_reconciles("dok_wave_plan.json", wave.get("identity_reconciliation"))

    def test_content_readiness_inventory_reconciles(self):
        cri = load_json(CONTENT_READINESS_INVENTORY_PATH)
        self._assert_reconciles(
            "content_readiness_inventory.json",
            cri.get("aggregate", {}).get("identity_reconciliation"),
        )

    def test_dashboard_reconciles(self):
        dash = load_json(DASHBOARD_PATH)
        self._assert_reconciles(
            "dashboard content_readiness.json",
            dash.get("aggregates", {}).get("identity_reconciliation"),
        )

    def test_console_reconciles(self):
        console = load_json(CONSOLE_DATA_PATH)
        self._assert_reconciles("console_data.json meta", console.get("meta", {}).get("identity_reconciliation"))
        lc = console["meta"]["locked_counts"]
        self.assertEqual(lc["registry_rows"], FROZEN_TOTAL_ROWS)
        self.assertEqual(lc["active_registry_rows"], FROZEN_ACTIVE_ROWS)
        self.assertEqual(lc["merged_alias_rows"], FROZEN_MERGED_ALIAS_ROWS)
        # nt14-ingest-4-1-2026-07-23: the console's locked counts carry the
        # optional-catalog rows distinctly.
        self.assertEqual(lc["optional_catalog_rows"], FROZEN_OPTIONAL_CATALOG_ROWS)

    def test_provenance_audit_reconciles(self):
        prov = load_json(PROVENANCE_AUDIT_PATH)
        self._assert_reconciles("provenance_audit_data.json", prov.get("identity_reconciliation"))

    def test_alias_map_meta_reconciles(self):
        meta = load_json(ALIAS_MAP_PATH)["meta"]
        self.assertEqual(
            meta["ambiguous_legacy_ids"],
            meta["alias_resolved_groups"] + meta["unresolved_ambiguous_groups"],
        )
        self.assertEqual(meta["ambiguous_legacy_ids"], FROZEN_AMBIGUOUS_LEGACY_IDS)
        self.assertEqual(meta["unresolved_ambiguous_groups"], FROZEN_UNRESOLVED_AMBIGUOUS)

    def test_qb_stats_reconciles(self):
        # NAMED update for nt14-ingest-4-1-2026-07-23: triple split.
        stats = qb.stats()
        self.assertEqual(stats["total"], FROZEN_TOTAL_ROWS)
        self.assertEqual(stats["active_total"], FROZEN_ACTIVE_ROWS)
        self.assertEqual(stats["optional_catalog_total"], FROZEN_OPTIONAL_CATALOG_ROWS)
        self.assertEqual(stats["merged_alias_total"], FROZEN_MERGED_ALIAS_ROWS)
        self.assertEqual(
            stats["total"],
            stats["active_total"]
            + stats["optional_catalog_total"]
            + stats["merged_alias_total"],
        )


# =============================================================================
# 5. decision console -- resolved pairs
# =============================================================================

def _extract_console_data_blob(html_text):
    """Extract and parse the `window.CONSOLE_DATA = {...};` object literal
    embedded in the built TEACHER_DECISION_CONSOLE.html -- it's plain JSON
    (build_console.py's own json.dump output), so a straight string-slice
    between the two known `window.X = ` markers plus a trailing-`;` strip
    is enough; no HTML/JS parser needed."""
    start_marker = "window.CONSOLE_DATA = "
    end_marker = "window.THUMBS = "
    start = html_text.index(start_marker) + len(start_marker)
    end = html_text.index(end_marker)
    blob = html_text[start:end].strip()
    if blob.endswith(";"):
        blob = blob[:-1]
    return json.loads(blob)


def _extract_js_function_body(js_text, func_name):
    """Best-effort slice of a top-level (2-space-indented) JS function's
    body text, from its opening brace up to the next top-level `function`
    keyword (or EOF). Good enough for substring/ordering checks on this
    file's consistently-formatted source -- not a real JS parser."""
    m = re.search(r"\n  function " + re.escape(func_name) + r"\([^)]*\)\{", js_text)
    if not m:
        return None
    start = m.end()
    next_m = re.search(r"\n  function \w+\(", js_text[start:])
    end = start + next_m.start() if next_m else len(js_text)
    return js_text[start:end]


class TestConsoleResolvedPairs(unittest.TestCase):
    """console_data.json section2's 22 pairs, plus the console UI's
    resolved-pair rendering/exclusion logic (SUB-C's C1/C2 work, landed):
    a "MERGED" badge on the alias copy column and in the pair decision
    control (both via the `recorded-context-badge` pattern already used for
    section 3's recorded-context notes), a `renderSection2()` code path that
    derives `merged: !!pair.resolved_alias` per pair into `decisionRegistry`,
    and `updateCounters()` / `buildExportObject()` both explicitly bucketing
    /excluding `d.merged` entries (client-side; NOT a "pending"-named field
    in console_data.json -- there is no such field, the counters are
    computed at render time in the browser from section2.pairs, so these
    tests assert on the JS code paths that do that, not a data field)."""

    def test_section2_pairs_carry_resolved_alias(self):
        console = load_json(CONSOLE_DATA_PATH)
        s2 = console["section2"]
        self.assertEqual(s2["count"], FROZEN_MERGED_ALIAS_ROWS)
        self.assertEqual(len(s2["pairs"]), FROZEN_MERGED_ALIAS_ROWS)
        for pair_entry in s2["pairs"]:
            with self.subTest(legacy_id=pair_entry["legacy_id"]):
                ra = pair_entry.get("resolved_alias")
                self.assertIsNotNone(ra)
                self.assertTrue(ra.get("survivor_uid"))
                self.assertEqual(ra.get("merged_at"), FROZEN_MERGED_AT)
                self.assertEqual(ra.get("authorization_record_id"), FROZEN_AUTH_RECORD_ID)

    def test_html_embeds_resolved_payloads_and_exclusion_markers(self):
        template_text = CONSOLE_HTML_TEMPLATE_PATH.read_text(encoding="utf-8")
        html_text = CONSOLE_HTML_PATH.read_text(encoding="utf-8")

        # The badge text + CSS class both files render for a merged pair --
        # stable, meaningful strings (not a brittle full-line/whitespace match).
        for text in (template_text, html_text):
            self.assertIn("recorded-context-badge", text)
            self.assertIn("MERGED -- already resolved (rc-merge-auth-5-4-2026-07-23)", text)
            self.assertIn("MERGED (alias copy) -- see resolution below", text)

        # The code path that derives the `merged` flag from `pair.resolved_alias`
        # inside renderSection2(), present in both the source template and the
        # built HTML (build_console.py embeds the template's JS verbatim).
        for text in (template_text, html_text):
            body = _extract_js_function_body(text, "renderSection2")
            self.assertIsNotNone(body, "renderSection2() not found")
            self.assertIn("merged: !!pair.resolved_alias", body)

        # The 22 resolved_alias payloads actually embedded in the built HTML's
        # window.CONSOLE_DATA blob (not just present in the separate committed
        # console_data.json) -- proves the artifact teachers actually open
        # carries the real data, not just the app-data file alongside it.
        embedded = _extract_console_data_blob(html_text)
        pairs = embedded["section2"]["pairs"]
        self.assertEqual(len(pairs), FROZEN_MERGED_ALIAS_ROWS)
        for pair_entry in pairs:
            with self.subTest(legacy_id=pair_entry["legacy_id"]):
                ra = pair_entry["resolved_alias"]
                self.assertEqual(ra["authorization_record_id"], FROZEN_AUTH_RECORD_ID)
                self.assertEqual(ra["merged_at"], FROZEN_MERGED_AT)

    def test_pending_counters_exclude_resolved_pairs(self):
        # No "pending"-named field exists in console_data.json -- the pending/
        # made/recorded/merged counters are computed client-side, at render
        # time, from decisionRegistry (built by renderSection2() et al., see
        # test_html_embeds_resolved_payloads_and_exclusion_markers above). So
        # this asserts on the CLIENT-SIDE exclusion logic itself: updateCounters()
        # must bucket a merged pair into `merged` BEFORE it could ever fall
        # through to the pending/made counters, and buildExportObject() must
        # return (skip) a merged pair BEFORE the isAnswered() check that would
        # otherwise let it be (re-)exported as a new decision.
        template_text = CONSOLE_HTML_TEMPLATE_PATH.read_text(encoding="utf-8")

        counters_body = _extract_js_function_body(template_text, "updateCounters")
        self.assertIsNotNone(counters_body, "updateCounters() not found")
        merged_check_pos = counters_body.find("if(d.merged){")
        pending_incr_pos = counters_body.find("pending++")
        self.assertNotEqual(merged_check_pos, -1, "updateCounters() has no d.merged bucket")
        self.assertNotEqual(pending_incr_pos, -1, "updateCounters() has no pending++ ")
        self.assertLess(
            merged_check_pos, pending_incr_pos,
            "d.merged must be bucketed BEFORE pending is incremented, so a "
            "merged pair can never inflate the pending count",
        )
        self.assertIn("rc-merge-auth-5-4-2026-07-23", counters_body)

        export_body = _extract_js_function_body(template_text, "buildExportObject")
        self.assertIsNotNone(export_body, "buildExportObject() not found")
        merged_return_pos = export_body.find("if(d.merged) return;")
        answered_check_pos = export_body.find("isAnswered(d.decision_id)")
        self.assertNotEqual(merged_return_pos, -1, "buildExportObject() has no d.merged exclusion")
        self.assertNotEqual(answered_check_pos, -1, "buildExportObject() has no isAnswered() gate")
        self.assertLess(
            merged_return_pos, answered_check_pos,
            "a merged pair must be excluded BEFORE the isAnswered() gate, so "
            "it can never be (re-)exported as a new decision",
        )


# =============================================================================
# D2 -- change-detection sweep (env-gated; merge-operation windows only)
# =============================================================================

# The 22 files this merge operation is authorized to have changed (bundle
# MANIFEST minus the 7 named-update-only files that stayed byte-identical),
# rc-merge-auth-5-4-2026-07-23. This list is a FROZEN historical record of
# THIS merge window -- it is not meant to grow for unrelated future work; a
# later, unrelated change to the repo legitimately SHOULD trip this sweep
# (that's the point), which is exactly why the class is skipped by default.
MERGE_TOUCHED_FILES = {
    "questionbank/registry.jsonl",
    "inventory/merge-proposal-5-4/merge_proposal_5_4.json",
    "inventory/merge-proposal-5-4/MERGE_PROPOSAL.md",
    "inventory/dedup/build_item_uid_map.py",
    "inventory/dedup/item_uid_alias_map.json",
    "inventory/dok-workflow/gen_dok_wave_plan.py",
    "inventory/dok-workflow/dok_wave_plan.json",
    "inventory/dok-workflow/test_cross_consumer_projection.py",
    "inventory/dok-workflow/DOK_VERIFICATION_WORKFLOW.md",
    "inventory/build_content_readiness_inventory.py",
    "inventory/content_readiness_inventory.json",
    "inventory/CONTENT_READINESS_INVENTORY.md",
    "inventory/dashboard/build_content_readiness.py",
    "inventory/dashboard/content_readiness.json",
    "inventory/dashboard/content_readiness_dashboard.html",
    "inventory/decision-console/build_console.py",
    "inventory/decision-console/console_data.json",
    "inventory/decision-console/TEACHER_DECISION_CONSOLE.html",
    "tools/dok-review/dok_review.py",
    "inventory/provenance-audit/audit_match_quality.py",
    "inventory/provenance-audit/provenance_audit_data.json",
    "qb.py",
}
ADDITIONAL_ALLOWED_FILES = {
    "test_merge_semantics_5_4.py",  # this file, added by the NT11 SUB-D remediation
    "nt11_merge_window_manifest.json",  # this file's hash-manifest, D2 remediation
}
EXACT_IGNORED_FILES = {"AGENTS.md", "CLAUDE.md", "CONTINUATION_PROMPT.md", ".gitignore"}
IGNORE_PREFIXES = (
    "state/",
    "grade-monitor/",
    ".claude/skills/gitnexus/",
    "questionbank/calibration/",
    ".pytest_cache/",
    ".gitnexus/",
)
# inventory/ and tools/ are, as a whole, still untracked in git (never
# git-added even once) -- git collapses an entirely-untracked directory to a
# single "?? inventory/" line rather than listing files inside it, so there
# is no per-file historical baseline to diff against for their contents. The
# per-file MERGE_TOUCHED_FILES list above remains the source of truth for
# what THIS merge changed; this sweep additionally allows the two directory
# tokens wholesale (matching the same reasoning already used in the NT11
# SUB-D scratchpad harness, nt11_gates/run_gates.py).
IGNORE_DIR_TOKENS = {"inventory", "tools"}


def _classify_git_status_path(code, path):
    norm = path.replace("\\", "/")
    if "__pycache__" in norm:
        return True
    if norm in MERGE_TOUCHED_FILES or norm in ADDITIONAL_ALLOWED_FILES:
        return True
    if norm in EXACT_IGNORED_FILES:
        return True
    if norm.rstrip("/") in IGNORE_DIR_TOKENS:
        return True
    if any(norm.startswith(pref) for pref in IGNORE_PREFIXES):
        return True
    if code.strip() == "??":
        if "/" not in norm and norm.endswith(".md"):
            return True  # untracked top-level working doc
        if norm.endswith(".png"):
            return True  # untracked calibration/source image
    return False


@unittest.skipUnless(
    os.environ.get("NT11_CHANGE_SWEEP") == "1",
    "opt-in only (set NT11_CHANGE_SWEEP=1); for merge-operation windows, not daily lesson prep",
)
class TestChangeDetectionSweep(unittest.TestCase):
    """D2 fold-in (Codex review D1-HIGH remediation). Runs `git status
    --porcelain` (read-only) and fails if any changed/untracked path is not
    covered by: the 22 merge-touched files, this test file, or a documented
    pre-existing-churn allowlist (state/, grade-monitor/,
    .claude/skills/gitnexus/, AGENTS.md, CLAUDE.md, CONTINUATION_PROMPT.md,
    .gitignore, questionbank/calibration/, untracked top-level docs/pngs,
    .pytest_cache). Skipped by default -- opt in with NT11_CHANGE_SWEEP=1
    only during an actual merge-operation review window."""

    def test_no_unlisted_repo_changes(self):
        proc = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        unlisted = []
        for raw_line in proc.stdout.splitlines():
            if not raw_line.strip():
                continue
            code, path = raw_line[:2], raw_line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ")[-1]
            path = path.strip('"')
            if not _classify_git_status_path(code, path):
                unlisted.append(f"{code} {path}")
        self.assertEqual(
            unlisted, [],
            "Unlisted repo changes outside the merge's expected/documented "
            "footprint:\n  " + "\n  ".join(unlisted),
        )

    def test_manifest_hash_layer(self):
        """D2 (Codex review, mandated): closes the inventory/tools blind
        spot that test_no_unlisted_repo_changes above cannot see -- git
        status collapses a wholly-untracked directory to one line, so a
        content change to any ONE file inside inventory/ or tools/ never
        shows up as its own git-status entry. This hashes every file
        CURRENTLY under both roots and diffs against the frozen
        nt11_merge_window_manifest.json snapshot (see
        generate_merge_window_manifest()'s docstring for the regeneration
        discipline), failing loudly on any addition, removal, or hash
        mismatch relative to that snapshot."""
        self.assertTrue(
            MERGE_WINDOW_MANIFEST_PATH.exists(),
            "nt11_merge_window_manifest.json is missing -- regenerate with "
            "`python test_merge_semantics_5_4.py --regen-manifest`",
        )
        manifest = load_json(MERGE_WINDOW_MANIFEST_PATH)
        expected_files = manifest["files"]
        current_files = {relpath: _sha256_of(abspath) for relpath, abspath in _iter_manifest_files()}

        new_on_disk, missing_on_disk, mismatched = _diff_manifest_files(expected_files, current_files)
        problems = []
        if new_on_disk:
            problems.append("present but NOT in manifest: " + ", ".join(new_on_disk))
        if missing_on_disk:
            problems.append("in manifest but MISSING on disk: " + ", ".join(missing_on_disk))
        if mismatched:
            problems.append("hash MISMATCH vs manifest: " + ", ".join(mismatched))
        self.assertEqual(problems, [], "\n".join(problems))


class TestManifestDiffLogic(unittest.TestCase):
    """Cheap, ALWAYS-RUN (not env-gated) negative proof for the hash-manifest
    comparison logic itself -- TestChangeDetectionSweep.test_manifest_hash_layer
    uses this exact _diff_manifest_files() helper against real disk hashes;
    this class instead feeds it synthetic in-memory {relpath: sha256} dicts,
    so it can prove the comparison correctly flags a new file, a missing
    file, and a hash mismatch without any disk I/O and without needing
    NT11_CHANGE_SWEEP=1 -- runs every time this module runs."""

    def test_diff_detects_new_missing_and_mismatched(self):
        expected = {"a.txt": "hash_a", "b.txt": "hash_b", "c.txt": "hash_c"}
        current = {"a.txt": "hash_a", "b.txt": "TAMPERED_HASH", "d.txt": "hash_d"}
        new_on_disk, missing_on_disk, mismatched = _diff_manifest_files(expected, current)
        self.assertEqual(new_on_disk, ["d.txt"])
        self.assertEqual(missing_on_disk, ["c.txt"])
        self.assertEqual(mismatched, ["b.txt"])

    def test_diff_clean_when_identical(self):
        same = {"a.txt": "hash_a", "b.txt": "hash_b"}
        new_on_disk, missing_on_disk, mismatched = _diff_manifest_files(same, dict(same))
        self.assertEqual((new_on_disk, missing_on_disk, mismatched), ([], [], []))


if __name__ == "__main__":
    if "--regen-manifest" in sys.argv:
        # Guarded, explicit-only path: a normal test run (no flag) NEVER
        # reaches this branch, so test_manifest_hash_layer's failure can
        # never be silently papered over by an automatic regeneration.
        m = generate_merge_window_manifest()
        print(f"Wrote {MERGE_WINDOW_MANIFEST_PATH} -- {m['file_count']} files under {m['root_dirs']}")
    else:
        unittest.main()
