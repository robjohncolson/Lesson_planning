"""test_optional_catalog_4_1.py -- regression suite for the NT14 Lesson 4-1
optional-catalog ingestion (nt14-ingest-4-1-2026-07-23).

WHAT THIS COVERS: the NT14 program is appending 19 new Lesson 4-1 rows to
questionbank/registry.jsonl (done separately, by the ingestion manager, NOT
by this test file). Every one of those rows carries a machine-readable
top-level field "availability": "optional-catalog". The binding pedagogical
rule: Lesson 4-1 is OPTIONAL CATALOG CONTENT -- it must never be
auto-scheduled, placed in pacing, counted toward completion, or emitted by
any default selection path that could feed required sequencing. Deliberate,
explicit access (by id, or via an explicit opt-in flag) must still work.

Before ingestion: 900 raw rows == 878 required-active + 22 merged-alias (0
optional-catalog). After ingestion: 919 raw == 878 required-active + 19
optional-catalog + 22 merged-alias.

STRUCTURE -- two classes, same hermetic/ambient split
test_merge_semantics_5_4.py uses:

  TestOptionalCatalogHermetic  -- builds synthetic registries inside a fresh
                                  tempfile.TemporaryDirectory(), monkeypatching
                                  qb.REGISTRY for the duration (see
                                  _patched_qb_registry below, the same seam
                                  test_merge_semantics_5_4.py uses). These
                                  tests pass RIGHT NOW, before the 4-1 rows
                                  exist, because they never depend on the
                                  real registry's content.

  TestAmbientPostIngestion      -- AMBIENT: reads the real, committed
                                  questionbank/registry.jsonl (read-only,
                                  never opened in a write mode). These
                                  describe the POST-ingestion state and are
                                  written now, but will only PASS once the
                                  ingestion manager has appended the 19
                                  Lesson 4-1 rows -- until then, expect
                                  failures (not necessarily errors) on most
                                  of them. That is the intended, documented
                                  state of this file prior to ingestion.

Run with:  python test_optional_catalog_4_1.py
   (or)    python -m pytest test_optional_catalog_4_1.py -q
"""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
import qb  # noqa: E402 -- module under test; REPO_ROOT is on sys.path above
import qb_append  # noqa: E402 -- module under test

REGISTRY_PATH = REPO_ROOT / "questionbank" / "registry.jsonl"
QB_APPEND_PATH = REPO_ROOT / "qb_append.py"

NT14_RECORD_ID = "nt14-ingest-4-1-2026-07-23"
FROZEN_RAW_BEFORE = 900
FROZEN_ACTIVE_BEFORE = 878
FROZEN_MERGED_ALIAS = 22
FROZEN_OPTIONAL_AFTER = 19
FROZEN_RAW_AFTER = 919
# RC acceptance correction (same record id): 2 of the 19 optional-catalog
# rows carry a machine-readable top-level "source_gap" marker for
# known-incomplete source material (q16 "given-illegible", q18
# "answer-truncated"). select() excludes them even with
# include_optional=True; only explicit-id access (the repair workflow's
# path) reaches them. Sub-split: 19 optional == 17 selectable + 2 source-gap.
FROZEN_SOURCE_GAP_ROWS = 2
FROZEN_OPTIONAL_SELECTABLE = 17
SOURCE_GAP_MARKERS = {
    "4-1-savvas-q16": "given-illegible",
    "4-1-savvas-q18": "answer-truncated",
}


# =============================================================================
# Shared helpers (mirrors test_merge_semantics_5_4.py's own helpers)
# =============================================================================

@contextmanager
def _patched_qb_registry(path):
    """Point qb.REGISTRY at a synthetic file for the duration of the `with`
    block, always restoring the real path afterward (even on exception) --
    the same hermetic seam test_merge_semantics_5_4.py uses."""
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


def make_row(id_, lesson, source, prompt, dok=1, **extra):
    row = {
        "id": id_, "lesson": lesson, "source": source, "page": None, "image": None,
        "has_visual": False, "visual_type": "none", "visual_needs_cleanup": False,
        "visual_clean_asset": None, "prompt": prompt, "answers": [], "correct": None,
        "dok": dok, "dok_rationale": "", "topics": [], "tags": [], "used_in": [],
        "notes": "", "created_at": "2026-01-01",
    }
    row.update(extra)
    return row


def make_optional_row(id_, lesson, source, prompt, dok=1, **extra):
    extra.setdefault("availability", "optional-catalog")
    return make_row(id_, lesson, source, prompt, dok=dok, **extra)


def make_alias_row(id_, lesson, source, prompt, alias_of, dok=1, **extra):
    extra["status"] = "merged-alias"
    extra["alias_of"] = alias_of
    return make_row(id_, lesson, source, prompt, dok=dok, **extra)


# =============================================================================
# 1. HERMETIC -- synthetic registries, pass before the 4-1 rows exist
# =============================================================================

class TestOptionalCatalogHermetic(unittest.TestCase):
    """All tests in this class build their own synthetic registry and
    monkeypatch qb.REGISTRY for the duration -- never the real
    questionbank/registry.jsonl. Must pass right now."""

    def test_select_excludes_optional_by_default(self):
        rows = [
            make_row("req-1", "4-1", "S", "required prompt 1", dok=1),
            make_optional_row("opt-1", "4-1", "S", "optional prompt 1", dok=2),
            make_alias_row("alias-1", "4-1", "S", "alias prompt (superseded)",
                            alias_of="iu_dummy0000000000"),
            make_row("req-2", "4-2", "S", "required prompt 2 other lesson", dok=1),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            write_registry(reg_path, rows)
            with _patched_qb_registry(reg_path):
                default_rows = qb.select()
                self.assertEqual({r["id"] for r in default_rows}, {"req-1", "req-2"})
                self.assertTrue(all(r.get("availability") != "optional-catalog" for r in default_rows))
                self.assertTrue(all(r.get("status") != "merged-alias" for r in default_rows))

                optin_rows = qb.select(include_optional=True)
                self.assertEqual({r["id"] for r in optin_rows}, {"req-1", "opt-1", "req-2"})
                self.assertTrue(all(r.get("status") != "merged-alias" for r in optin_rows))

                # filters still apply on top of include_optional=True
                self.assertEqual({r["id"] for r in qb.select(lesson="4-1")}, {"req-1"})
                self.assertEqual(
                    {r["id"] for r in qb.select(lesson="4-1", include_optional=True)},
                    {"req-1", "opt-1"},
                )

    def test_select_lesson_filter_does_not_bypass_exclusion(self):
        """THE NON-SCHEDULING PROOF CORE: no select() argument combination
        except the explicit include_optional=True flag can surface an
        optional-catalog row."""
        # Part A: a registry whose ONLY 4-1 rows are optional-catalog.
        narrow_rows = [
            make_row("req-x", "4-2", "S", "required other-lesson", dok=1),
            make_optional_row("4-1-opt-a", "4-1", "S", "optional 4-1 prompt A", dok=1),
            make_optional_row("4-1-opt-b", "4-1", "S", "optional 4-1 prompt B", dok=2),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            write_registry(reg_path, narrow_rows)
            with _patched_qb_registry(reg_path):
                self.assertEqual(qb.select(lesson="4-1"), [])
                optin = qb.select(lesson="4-1", include_optional=True)
                self.assertEqual({r["id"] for r in optin}, {"4-1-opt-a", "4-1-opt-b"})

        # Part B: a richer registry, sweep a grid of select() argument
        # combinations (all with the DEFAULT include_optional=False) and
        # assert zero optional-catalog rows leak out under ANY of them.
        grid_rows = [
            make_row("g-req-1", "4-1", "S", "grid required 1", dok=1,
                      topics=["t1"], tags=["tagA"], has_visual=False),
            make_row("g-req-2", "4-2", "S", "grid required 2", dok=2,
                      topics=["t2"], tags=["tagB"], has_visual=True),
            make_row("g-req-3", "4-3", "S", "grid required 3", dok=3,
                      topics=["t1", "t3"], tags=["tagC"], has_visual=False),
            make_optional_row("g-opt-1", "4-1", "S", "grid optional 1", dok=1,
                               topics=["t1"], tags=["tagA"], has_visual=False),
            make_optional_row("g-opt-2", "4-1", "S", "grid optional 2", dok=2,
                               topics=["t2"], tags=["tagB"], has_visual=True),
            make_optional_row("g-opt-3", "4-1", "S", "grid optional 3", dok=3,
                               topics=["t3"], tags=["tagC"], has_visual=True),
            make_alias_row("g-alias-1", "4-1", "S", "grid alias (superseded)",
                            alias_of="iu_dummy_grid_00000"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            write_registry(reg_path, grid_rows)
            with _patched_qb_registry(reg_path):
                lessons = [None, "4-1", "4-2", "4-3", "nope"]
                doks = [None, 1, 2, 3, (1, 2)]
                topics_opts = [None, ["t1"], ["t3"], ["t1", "t3"]]
                tags_opts = [None, ["tagA"], ["tagC"]]
                has_visual_opts = [None, True, False]
                limit_opts = [None, 1, 10]
                combo_count = 0
                for lesson, dok, topics, tags, has_visual, limit in itertools.product(
                    lessons, doks, topics_opts, tags_opts, has_visual_opts, limit_opts
                ):
                    combo_count += 1
                    result = qb.select(
                        lesson=lesson, dok=dok, topics=topics, tags=tags,
                        has_visual=has_visual, limit=limit,
                    )
                    leaked = [r["id"] for r in result if r.get("availability") == "optional-catalog"]
                    aliased = [r["id"] for r in result if r.get("status") == "merged-alias"]
                    with self.subTest(lesson=lesson, dok=dok, topics=topics,
                                       tags=tags, has_visual=has_visual, limit=limit):
                        self.assertEqual(leaked, [])
                        self.assertEqual(aliased, [])
                self.assertGreater(combo_count, 500)  # sanity: grid actually swept many combos

    def test_get_and_get_for_packet_return_optional_rows(self):
        """Explicit-id access works without any flag -- deliberate teacher
        access to optional-catalog content is unaffected by the select()
        exclusion."""
        rows = [
            make_optional_row("opt-A", "4-1", "S", "optional prompt A", dok=1),
            make_row("req-A", "4-1", "S", "required prompt A", dok=1),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            write_registry(reg_path, rows)
            with _patched_qb_registry(reg_path):
                got = qb.get("opt-A")
                self.assertIsNotNone(got)
                self.assertEqual(got.get("availability"), "optional-catalog")

                packet = qb.get_for_packet(["req-A", "opt-A"])
                self.assertEqual(len(packet), 2)
                self.assertEqual(packet[0]["id"], "req-A")
                self.assertEqual(packet[1]["id"], "opt-A")
                self.assertEqual(packet[1].get("availability"), "optional-catalog")

    def test_stats_triple_denominator(self):
        rows = [
            make_row("r1", "L1", "S", "p1", dok=1),
            make_row("r2", "L1", "S", "p2", dok=2),
            make_optional_row("o1", "L1", "S", "p3", dok=3),
            make_alias_row("a1", "L1", "S", "p6-alias", alias_of="iu_dummy_target_00", dok=4),
            make_optional_row("o2", "L2", "S", "p4", dok=1),
            make_optional_row("o3", "L2", "S", "p5", dok=1),
            make_row("r3", "L3", "S", "p7", dok=2),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            write_registry(reg_path, rows)
            with _patched_qb_registry(reg_path):
                stats = qb.stats()
                self.assertEqual(stats["raw_total"], 7)
                self.assertEqual(stats["total"], 7)
                self.assertEqual(stats["merged_alias_total"], 1)
                self.assertEqual(stats["optional_catalog_total"], 3)
                self.assertEqual(stats["active_total"], 3)
                self.assertEqual(
                    stats["raw_total"],
                    stats["active_total"] + stats["optional_catalog_total"] + stats["merged_alias_total"],
                )
                self.assertEqual(stats["by_lesson"]["L1"], {
                    "total": 4, "dok1": 1, "dok2": 1, "dok3": 1, "dok4": 1,
                    "visual": 0, "merged_alias": 1, "optional_catalog": 1, "source_gap": 0,
                })
                self.assertEqual(stats["by_lesson"]["L2"], {
                    "total": 2, "dok1": 2, "dok2": 0, "dok3": 0, "dok4": 0,
                    "visual": 0, "merged_alias": 0, "optional_catalog": 2, "source_gap": 0,
                })
                self.assertEqual(stats["by_lesson"]["L3"], {
                    "total": 1, "dok1": 0, "dok2": 1, "dok3": 0, "dok4": 0,
                    "visual": 0, "merged_alias": 0, "optional_catalog": 0, "source_gap": 0,
                })

    def test_qb_append_validates_availability(self):
        """Subprocess, --dry-run only -- never writes any repo file (that is
        --dry-run's whole contract). Reads the REAL registry/calibration
        read-only (existing-id/prompt dedup check, calibration existence
        check for lesson 4-1, which already has a committed calibration
        file) but appends nothing anywhere."""
        good_entry = {
            "id": "nt14-test-optional-availability-accept",
            "lesson": "4-1",
            "prompt": "NT14 TEST PROBE -- availability accept path -- "
                      "should never collide with a real registry prompt",
            "dok": 2,
            "availability": "optional-catalog",
        }
        proc = subprocess.run(
            [sys.executable, str(QB_APPEND_PATH), "--dry-run"],
            input=json.dumps(good_entry), capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nt14-test-optional-availability-accept", proc.stdout)

        bad_entry = {
            "id": "nt14-test-optional-availability-reject",
            "lesson": "4-1",
            "prompt": "NT14 TEST PROBE -- availability reject path -- "
                      "should never collide with a real registry prompt",
            "dok": 2,
            "availability": "bogus-value",
        }
        proc2 = subprocess.run(
            [sys.executable, str(QB_APPEND_PATH), "--dry-run"],
            input=json.dumps(bad_entry), capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(proc2.returncode, 0)
        self.assertIn("availability", (proc2.stdout + proc2.stderr).lower())

        # Belt-and-suspenders: confirm dry-run really wrote nothing.
        self.assertNotIn("nt14-test-optional-availability-accept",
                         REGISTRY_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("nt14-test-optional-availability-reject",
                         REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_qb_append_normalize_carries_availability(self):
        entry_with = {
            "lesson": "4-1",
            "prompt": "NT14 synthetic normalize-carries-availability prompt A",
            "dok": 2,
            "availability": "optional-catalog",
        }
        out_with = qb_append.normalize(dict(entry_with), taken=set(), existing_prompts=set(), force=False)
        self.assertIsNotNone(out_with)
        self.assertEqual(out_with.get("availability"), "optional-catalog")
        keys_with = list(out_with.keys())
        self.assertEqual(keys_with.index("availability"), keys_with.index("skill_tokens") + 1)

        entry_without = {
            "lesson": "4-1",
            "prompt": "NT14 synthetic normalize-carries-availability prompt B",
            "dok": 2,
        }
        out_without = qb_append.normalize(dict(entry_without), taken=set(), existing_prompts=set(), force=False)
        self.assertIsNotNone(out_without)
        self.assertNotIn("availability", out_without)

    def test_source_gap_exclusion_keys_on_marker_not_ids(self):
        """RC acceptance rule, hermetic proof: the exclusion keys on the
        source_gap MARKER, not on hardcoded ids. A synthetic row carrying
        source_gap is excluded even with include_optional=True; the SAME row
        with the marker removed becomes selectable. A required (non-optional)
        row carrying source_gap is likewise excluded from default select()."""
        gapped_opt = make_optional_row("syn-gap-opt", "9-9", "S", "synthetic gapped optional",
                                        source_gap="answer-truncated")
        clean_opt = make_optional_row("syn-clean-opt", "9-9", "S", "synthetic clean optional")
        gapped_req = make_row("syn-gap-req", "9-9", "S", "synthetic gapped required",
                               source_gap="given-illegible")
        clean_req = make_row("syn-clean-req", "9-9", "S", "synthetic clean required")
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            write_registry(reg_path, [gapped_opt, clean_opt, gapped_req, clean_req])
            with _patched_qb_registry(reg_path):
                self.assertEqual({r["id"] for r in qb.select()}, {"syn-clean-req"})
                self.assertEqual(
                    {r["id"] for r in qb.select(include_optional=True)},
                    {"syn-clean-req", "syn-clean-opt"},
                )
                # explicit-id repair path still reaches gapped rows
                self.assertIsNotNone(qb.get("syn-gap-opt"))
                self.assertIsNotNone(qb.get("syn-gap-req"))

            # SAME row, marker removed -> becomes selectable (proves the
            # exclusion is keyed on the marker, not the id).
            ungapped = dict(gapped_opt)
            del ungapped["source_gap"]
            write_registry(reg_path, [ungapped, clean_opt, clean_req])
            with _patched_qb_registry(reg_path):
                self.assertIn(
                    "syn-gap-opt",
                    {r["id"] for r in qb.select(include_optional=True)},
                )

    def test_qb_append_validates_source_gap(self):
        """qb_append carries a supplied source_gap and rejects a non-string
        value -- normalize()-level, no subprocess needed."""
        out = qb_append.normalize(
            {"lesson": "4-1", "prompt": "NT14 synthetic source-gap carry probe",
             "dok": 2, "availability": "optional-catalog",
             "source_gap": "answer-truncated"},
            taken=set(), existing_prompts=set(), force=False,
        )
        self.assertEqual(out.get("source_gap"), "answer-truncated")
        with self.assertRaises(SystemExit):
            qb_append.validate(
                {"lesson": "4-1", "prompt": "x", "dok": 2, "source_gap": 7})

    def test_append_writes_lf(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.jsonl"
            # Simulate the registry's real-world state: pre-existing lines
            # may carry stray CRLF from a historical text-mode write on
            # Windows (see qb.append()'s own comment) -- this test proves
            # the NEW append is clean LF regardless of what came before.
            write_registry(reg_path, [make_row("seed", "L", "S", "seed prompt")])
            with _patched_qb_registry(reg_path):
                qb.append(make_optional_row("new-1", "4-1", "Savvas", "new appended prompt", dok=2))
            data = reg_path.read_bytes()
            lines = data.split(b"\n")
            self.assertEqual(lines[-1], b"")  # file ends with a bare \n
            appended_line = lines[-2]
            self.assertTrue(data.endswith(b"\n"))
            self.assertFalse(appended_line.endswith(b"\r"))
            self.assertNotIn(b"\r", appended_line)
            self.assertIn(b'"new-1"', appended_line)


# =============================================================================
# 2. AMBIENT -- reads the real, committed registry (POST-ingestion state)
# =============================================================================

# NOTE: every test in this class reads the real, committed
# questionbank/registry.jsonl (read-only). They describe the POST-ingestion
# state (after the NT14 manager appends the 19 Lesson 4-1 rows) and are
# expected to FAIL until that ingestion has happened -- that is the intended
# state of this file today.
class TestAmbientPostIngestion(unittest.TestCase):

    def test_all_4_1_rows_carry_optional_marker(self):
        rows = [q for q in qb.load() if q.get("lesson") == "4-1"]
        self.assertEqual(len(rows), FROZEN_OPTIONAL_AFTER)
        self.assertTrue(all(r.get("availability") == "optional-catalog" for r in rows))
        expected_ids = {f"4-1-savvas-q{n}" for n in range(8, 27)}  # q8..q26 inclusive = 19
        self.assertEqual({r["id"] for r in rows}, expected_ids)
        # RC acceptance correction: EXACTLY q16/q18 carry the source_gap
        # marker, with exactly these values; the other 17 carry none.
        gap = {r["id"]: r["source_gap"] for r in rows if r.get("source_gap")}
        self.assertEqual(gap, SOURCE_GAP_MARKERS)

    def test_default_select_excludes_4_1(self):
        rows = qb.select()
        self.assertEqual(sum(1 for r in rows if r.get("lesson") == "4-1"), 0)
        self.assertEqual(sum(1 for r in rows if r.get("availability")), 0)
        self.assertEqual(len(rows), FROZEN_ACTIVE_BEFORE)

    def test_explicit_optin_returns_4_1(self):
        # NAMED update (RC acceptance correction): opt-in selection returns
        # the 17 SELECTABLE rows -- q16 (dok1) and q18 (dok2) carry
        # source_gap and are excluded even here, so the DOK histogram drops
        # from the full-catalog {1:5, 2:10, 3:4} to {1:4, 2:9, 3:4}.
        rows = qb.select(lesson="4-1", include_optional=True)
        self.assertEqual(len(rows), FROZEN_OPTIONAL_SELECTABLE)
        ids = {r["id"] for r in rows}
        self.assertEqual(
            ids,
            {f"4-1-savvas-q{n}" for n in range(8, 27)} - set(SOURCE_GAP_MARKERS),
        )
        histogram = {1: 0, 2: 0, 3: 0}
        for r in rows:
            histogram[r["dok"]] = histogram.get(r["dok"], 0) + 1
        self.assertEqual(histogram, {1: 4, 2: 9, 3: 4})

    def test_explicit_id_access_4_1(self):
        got = qb.get("4-1-savvas-q26")
        self.assertIsNotNone(got)
        self.assertEqual(got.get("availability"), "optional-catalog")

        packet = qb.get_for_packet([
            "4-1-savvas-q20", "4-1-savvas-q22", "4-1-savvas-q25", "4-1-savvas-q26",
        ])
        self.assertEqual(len(packet), 4)

        # RC acceptance correction: the two source-gap rows stay reachable
        # by explicit id -- that is the repair workflow's path, distinct
        # from selection.
        for qid, marker in SOURCE_GAP_MARKERS.items():
            with self.subTest(qid=qid):
                row = qb.get(qid)
                self.assertIsNotNone(row)
                self.assertEqual(row.get("source_gap"), marker)
        gap_packet = qb.get_for_packet(sorted(SOURCE_GAP_MARKERS))
        self.assertEqual(len(gap_packet), FROZEN_SOURCE_GAP_ROWS)

    def test_source_gap_rows_excluded_under_every_argument_combination(self):
        """RC acceptance rule: q16/q18 must not be selectable under ANY
        select() argument combination, INCLUDING include_optional=True --
        while the 17 complete rows ARE included under the opt-in."""
        lessons = [None, "4-1"]
        doks = [None, 1, 2, 3, (1, 2, 3)]
        include_opts = [False, True]
        limits = [None, 500]
        combo_count = 0
        for lesson, dok, include_optional, limit in itertools.product(
            lessons, doks, include_opts, limits
        ):
            combo_count += 1
            rows = qb.select(
                lesson=lesson, dok=dok, include_optional=include_optional, limit=limit,
            )
            leaked = [r["id"] for r in rows if r.get("source_gap")]
            with self.subTest(lesson=lesson, dok=dok,
                               include_optional=include_optional, limit=limit):
                self.assertEqual(leaked, [])
                self.assertNotIn("4-1-savvas-q16", {r["id"] for r in rows})
                self.assertNotIn("4-1-savvas-q18", {r["id"] for r in rows})
        self.assertGreaterEqual(combo_count, 40)
        # the 17 complete rows are all present under the plain opt-in
        optin_ids = {r["id"] for r in qb.select(lesson="4-1", include_optional=True)}
        self.assertEqual(
            optin_ids,
            {f"4-1-savvas-q{n}" for n in range(8, 27)} - set(SOURCE_GAP_MARKERS),
        )

    def test_stats_reconciles_919(self):
        stats = qb.stats()
        self.assertEqual(stats["raw_total"], FROZEN_RAW_AFTER)
        self.assertEqual(stats["active_total"], FROZEN_ACTIVE_BEFORE)
        self.assertEqual(stats["optional_catalog_total"], FROZEN_OPTIONAL_AFTER)
        self.assertEqual(stats["merged_alias_total"], FROZEN_MERGED_ALIAS)
        self.assertEqual(
            stats["raw_total"],
            stats["active_total"] + stats["optional_catalog_total"] + stats["merged_alias_total"],
        )
        # RC acceptance correction: the optional-catalog sub-split.
        self.assertEqual(stats["optional_catalog_selectable_total"], FROZEN_OPTIONAL_SELECTABLE)
        self.assertEqual(stats["source_gap_total"], FROZEN_SOURCE_GAP_ROWS)
        self.assertEqual(
            stats["optional_catalog_total"],
            stats["optional_catalog_selectable_total"] + stats["source_gap_total"],
        )
        self.assertEqual(stats["by_lesson"]["4-1"]["source_gap"], FROZEN_SOURCE_GAP_ROWS)


if __name__ == "__main__":
    unittest.main()
