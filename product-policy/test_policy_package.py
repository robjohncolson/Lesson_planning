"""
test_policy_package.py -- NT15 product-policy Deliverable: package-wide consistency suite.

Package: NT15 product-policy · Version: 2.0 · Date: 2026-07-24
Source of authority: RC final decisions, 2026-07-24 (Grok preference interview + RC clarifications;
NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)
Status: Authoritative -- gates all future Desk / grading / Schoology implementation.

WHAT THIS MODULE IS
--------------------
This is NOT a test of any single deliverable's internal behavior -- D2-D5 already have their
own dedicated suites (test_grading_policy_ref.py, test_parity_check.py,
test_desk_state_model.py, test_answer_equivalence_vectors.py) and this module does not
duplicate or weaken any of them. This module is the package-wide CROSS-DOCUMENT consistency
check: it verifies that the eight deliverables, their four JSON companions, their fixtures,
and their provenance headers all agree with each other and with the shared vocabulary fixed
by the NT15 tranche brief (canonical PREF-NN ids, canonical OPEN-NN ids, the canonical seven
Desk lesson states, the DEFERRED-vs-OPEN boundary, and the no-live-write / no-network /
no-dates constraints).

NT16 UPDATE (v2.0): RC issued nine rulings on 2026-07-24 resolving OPEN-08, 09, 10, 11, 15,
16, 17, 18, and 19 (see OPEN_DECISIONS_REGISTER.md). This module's v1.0 "two normativity
tiers" guards (decided transitions.legal vs. provisional transitions.provisional) are
converted to DECIDED-state guards: transitions.provisional is now permanently empty (OPEN-18
resolved -- T7/T11/T12/T13 promoted into transitions.legal), and `completed` is DECIDED
terminal (OPEN-17 resolved). New guards check the register's 10-open/9-resolved inventory,
that every resolved id carries its provenance token and no open id does, that no resolved id
sits next to stale "still open" language outside historical context, that `completed` has
zero outbound legal transitions, and that grading_policy.v2.json carries no open items.

Where a test in this module finds a genuine cross-document inconsistency, it FAILS loudly with
a message describing what drifted -- it does not paper over the drift, and no sibling
deliverable is modified by this file to make a test pass.

Hermetic: standard library + pytest only. No network. Every file this suite reads lives inside
product-policy/ (located via pathlib.Path(__file__).parent), with the sole read-only exception
of the manifest check's directory listing, which never leaves this same directory tree.

Run: python -m pytest product-policy/ -q   (from the repo root)
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

import parity_check

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------------------
# Shared vocabulary (mirrors NT15_SHARED_BRIEF.md -- not re-derived from any single sibling
# deliverable, so this suite can catch a sibling drifting away from the brief's own fixed IDs).
# ---------------------------------------------------------------------------------------

CANONICAL_STATES = {
    "today",
    "released",
    "unreleased",
    "skipped",
    "optional-catalog",
    "completed",
    "temporarily-unavailable",
}

CANONICAL_PREF_IDS = [f"PREF-{i:02d}" for i in range(1, 15)]  # PREF-01 .. PREF-14
CANONICAL_OPEN_IDS = [f"OPEN-{i:02d}" for i in range(1, 20)]  # OPEN-01 .. OPEN-19

DEFERRED_PREF_IDS = {"PREF-09.6", "PREF-10.5", "PREF-10.6", "PREF-10.7", "PREF-10.8", "PREF-13.6"}

# NT16 (v2.0): RC ruled on nine of the nineteen OPEN-NN items on 2026-07-24. The remaining ten
# are still OPEN and owned by RC.
RESOLVED_OPEN_IDS = {
    "OPEN-08", "OPEN-09", "OPEN-10", "OPEN-11", "OPEN-15", "OPEN-16", "OPEN-17", "OPEN-18", "OPEN-19",
}
STILL_OPEN_IDS = set(CANONICAL_OPEN_IDS) - RESOLVED_OPEN_IDS
RESOLVED_PROVENANCE_TOKEN = "RESOLVED by RC 2026-07-24"

FORBIDDEN_NETWORK_MODULES = {"requests", "httpx", "socket", "aiohttp"}
FORBIDDEN_NETWORK_DOTTED_PREFIXES = ("urllib.request", "http.client")

EXPECTED_SOURCE_OF_AUTHORITY_JSON = (
    "RC final decisions 2026-07-24 (Grok preference interview + RC clarifications; "
    "NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)"
)

# ---------------------------------------------------------------------------------------
# File manifest -- every file this package is expected to contain.
# ---------------------------------------------------------------------------------------

DELIVERABLE_MD_FILES = [
    "RC_TEACHER_PREFERENCE_RECORD.md",       # D1
    "GRADING_POLICY_SPEC.md",                # D2
    "SCHOOLOGY_PROJECTION_CONTRACT.md",      # D3
    "DESK_STATE_MODEL.md",                   # D4
    "ANSWER_EQUIVALENCE_CONTRACT.md",        # D5
    "PHASED_PRODUCT_SEQUENCE.md",            # D6
    "OPEN_DECISIONS_REGISTER.md",            # D7
    "NEXT_TRANCHE_PROPOSAL.md",              # D8
]

# NT16 (v2.0): all three JSON artifacts that carry a version suffix are renamed .v1.json ->
# .v2.json package-wide. schoology_projection.v2.json is landed by a concurrent NT16 work
# package (D3); any failure below that traces only to that rename/landing is D3-attributable,
# not a defect in this suite -- see this implementer's final report.
JSON_ARTIFACT_FILES = [
    "grading_policy.v2.json",
    "desk_state_model.v2.json",
    "answer_equivalence_vectors.json",
    "schoology_projection.v2.json",
]

PYTHON_REFERENCE_FILES = [
    "grading_policy_ref.py",
    "parity_check.py",
]

TEST_MODULE_FILES = [
    "test_grading_policy_ref.py",
    "test_parity_check.py",
    "test_desk_state_model.py",
    "test_answer_equivalence_vectors.py",
    "test_rc_rulings_acceptance.py",
    "test_policy_package.py",
]

FIXTURE_FILES = [
    "fixtures/schoology/course_section_synthetic.json",
    "fixtures/schoology/student_0001_above_gate_convergent.json",
    "fixtures/schoology/student_0002_above_gate_divergent.json",
    "fixtures/schoology/student_0003_below_gate_divergent.json",
    "fixtures/schoology/student_0004_unknown_assessment_evidence.json",
    # Added by the D3 owner (Codex SOL review R-B, finding B1 -- fail-open optional-content
    # exposure in _should_project). As of this manifest update, parity_check.py's
    # _should_project already consults the real `availability` marker, but this fixture is
    # not yet loaded by any test in test_parity_check.py -- see this suite's manifest test
    # docstring / this implementer's final report for that observation.
    "fixtures/schoology/course_catalog_nt14_b1_edge_cases.json",
    # NT16 (v2.0) additions, landed by the concurrent D3 work package and already loaded by
    # test_parity_check.py and cited by SCHOOLOGY_PROJECTION_CONTRACT.md: student_0005 covers
    # OPEN-16's zero-eligible-denominator/no-fabricated-zero case; student_0006 covers
    # OPEN-09's display-rounding-only-difference (never a substantive divergence) case.
    "fixtures/schoology/student_0005_zero_denominator_no_eligible_evidence.json",
    "fixtures/schoology/student_0006_display_rounding_only_difference.json",
]

INDEX_FILES = ["INDEX.md"]

ALL_EXPECTED_FILES = (
    DELIVERABLE_MD_FILES
    + JSON_ARTIFACT_FILES
    + PYTHON_REFERENCE_FILES
    + TEST_MODULE_FILES
    + FIXTURE_FILES
    + INDEX_FILES
)


# =========================================================================================
# 1. FILE MANIFEST
# =========================================================================================


@pytest.mark.parametrize("relative_path", ALL_EXPECTED_FILES)
def test_expected_deliverable_file_exists(relative_path: str):
    path = HERE / relative_path
    assert path.is_file(), f"expected package file is missing: {relative_path}"


def test_fixtures_directory_contains_no_unexpected_extra_or_missing_files():
    fixtures_dir = HERE / "fixtures" / "schoology"
    assert fixtures_dir.is_dir(), "fixtures/schoology/ directory is missing"
    on_disk = {p.name for p in fixtures_dir.glob("*.json")}
    expected = {Path(f).name for f in FIXTURE_FILES}
    assert on_disk == expected, (
        f"fixtures/schoology/ contents drifted from the expected fixture set -- "
        f"missing={expected - on_disk}, unexpected={on_disk - expected}"
    )


# =========================================================================================
# 2. PROVENANCE HEADERS
# =========================================================================================


@pytest.mark.parametrize("relative_path", DELIVERABLE_MD_FILES + INDEX_FILES)
def test_md_deliverable_carries_provenance_header(relative_path: str):
    text = (HERE / relative_path).read_text(encoding="utf-8")
    assert "**Version:** 2.0" in text, f"{relative_path}: missing '**Version:** 2.0' header line"
    assert "**Date:** 2026-07-24" in text, f"{relative_path}: missing '**Date:** 2026-07-24' header line"
    assert "RC final decisions, 2026-07-24" in text, (
        f"{relative_path}: missing the RC 2026-07-24 source-of-authority line"
    )


@pytest.mark.parametrize("relative_path", JSON_ARTIFACT_FILES)
def test_json_artifact_carries_provenance_keys(relative_path: str):
    data = json.loads((HERE / relative_path).read_text(encoding="utf-8"))
    assert data.get("version") == "2.0", f"{relative_path}: top-level 'version' must be '2.0'"
    assert data.get("date") == "2026-07-24", f"{relative_path}: top-level 'date' must be '2026-07-24'"
    assert data.get("source_of_authority") == EXPECTED_SOURCE_OF_AUTHORITY_JSON, (
        f"{relative_path}: 'source_of_authority' does not match the canonical NT16 string"
    )


# =========================================================================================
# 3. CONSTANTS AGREE BETWEEN JSON AND PROSE (grading_policy.v2.json is the source of truth;
#    this test's job is to catch GRADING_POLICY_SPEC.md's prose drifting away from it)
# =========================================================================================


def test_grading_constants_agree_between_json_and_prose():
    policy = json.loads((HERE / "grading_policy.v2.json").read_text(encoding="utf-8"))
    constants = policy["constants"]

    assert constants["completion_threshold"] == 0.40
    assert constants["completion_threshold_inclusive"] is True
    assert constants["participation_point_per_class_day_present"] == 1.0
    assert constants["participation_point_per_class_day_absent"] == 0.0
    assert constants["ti84_extra_credit_points"] == 0.5
    assert constants["equation_lab_extra_credit_points"] == 0.5
    # NT16 (v2.0) additions -- OPEN-10 (daily cap) and OPEN-09 (display rounding).
    assert constants["extra_credit_daily_cap_points"] == 1.0
    assert constants["final_grade_display_decimals"] == 1
    assert set(constants["authorized_extra_credit_sources"]) == {"ti84", "equation_lab"}

    spec = (HERE / "GRADING_POLICY_SPEC.md").read_text(encoding="utf-8")

    # The 40% threshold, stated as the literal decimal, must appear in the prose, and the
    # prose must call out its inclusivity explicitly (never silently rounded/assumed).
    assert "0.40" in spec, "GRADING_POLICY_SPEC.md prose does not mention the 0.40 threshold literal"
    assert re.search(r"inclusive", spec, re.IGNORECASE), (
        "GRADING_POLICY_SPEC.md prose does not describe the 0.40 gate as inclusive"
    )
    assert "completion >= 0.40" in spec or "completion&nbsp;>=&nbsp;0.40" in spec, (
        "GRADING_POLICY_SPEC.md prose does not spell out the literal >= 0.40 comparison "
        "the JSON's constants block encodes"
    )

    # Participation present/absent literals.
    assert "`1.0`" in spec, "GRADING_POLICY_SPEC.md prose does not carry the participation-present literal `1.0`"
    assert "`0.0`" in spec, "GRADING_POLICY_SPEC.md prose does not carry the participation-absent literal `0.0`"

    # Both extra-credit literals (+0.5 each).
    assert spec.count("+0.5") >= 2, (
        "GRADING_POLICY_SPEC.md prose must state the +0.5 extra-credit literal for BOTH "
        "TI-84 and Equation Lab, matching grading_policy.v2.json's ti84_extra_credit_points "
        "and equation_lab_extra_credit_points"
    )

    # NT16 (v2.0): the +1.0/day extra-credit cap (OPEN-10) and the display-rounding constants
    # (OPEN-09) must be named in prose, JSON-first -- grading_policy.v2.json is the source of
    # truth; this test's job is to catch the prose drifting away from it.
    assert "+1.0" in spec, (
        "GRADING_POLICY_SPEC.md prose does not carry the +1.0/day extra-credit cap literal (OPEN-10)"
    )
    assert re.search(r"one decimal", spec, re.IGNORECASE), (
        "GRADING_POLICY_SPEC.md prose does not describe the display rounding as one decimal (OPEN-09)"
    )
    assert "extra_credit_daily_cap_points" in spec, (
        "GRADING_POLICY_SPEC.md prose does not name the extra_credit_daily_cap_points constant"
    )
    assert "final_grade_display_decimals" in spec, (
        "GRADING_POLICY_SPEC.md prose does not name the final_grade_display_decimals constant"
    )
    assert "authorized_extra_credit_sources" in spec, (
        "GRADING_POLICY_SPEC.md prose does not name the authorized_extra_credit_sources constant"
    )


# =========================================================================================
# 4. DESK STATES MATCH ACROSS DOCUMENTS
# =========================================================================================


def _extract_backtick_tokens(line: str) -> list[str]:
    return re.findall(r"`([^`]+)`", line)


def _extract_state_list_from_desk_state_model_md(text: str) -> list[str]:
    anchor = "Exactly these seven, spelled exactly this way"
    idx = text.index(anchor)  # raises ValueError (-> test failure) if the anchor sentence moved/vanished
    remainder = text[idx:]
    for line in remainder.splitlines()[1:]:
        tokens = _extract_backtick_tokens(line)
        if tokens:
            return tokens
    raise AssertionError("DESK_STATE_MODEL.md: could not locate the seven-state list line after the anchor sentence")


def _extract_state_list_from_pref_record_md(text: str) -> list[str]:
    idx = text.index("PREF-01.1")  # first occurrence is the canonical table row itself
    line_end = text.index("\n", idx)
    line = text[idx:line_end]
    tokens = _extract_backtick_tokens(line)
    assert tokens, "RC_TEACHER_PREFERENCE_RECORD.md: PREF-01.1 row has no backtick-quoted state tokens"
    return tokens


def test_desk_states_match_across_json_and_both_markdown_documents():
    json_states = json.loads((HERE / "desk_state_model.v2.json").read_text(encoding="utf-8"))["state_set"]

    desk_md_text = (HERE / "DESK_STATE_MODEL.md").read_text(encoding="utf-8")
    md_states = _extract_state_list_from_desk_state_model_md(desk_md_text)

    pref_md_text = (HERE / "RC_TEACHER_PREFERENCE_RECORD.md").read_text(encoding="utf-8")
    pref_states = _extract_state_list_from_pref_record_md(pref_md_text)

    for label, states in (
        ("desk_state_model.v2.json state_set", json_states),
        ("DESK_STATE_MODEL.md §2 state list", md_states),
        ("RC_TEACHER_PREFERENCE_RECORD.md PREF-01.1", pref_states),
    ):
        assert len(states) == 7, f"{label} does not list exactly seven states: {states!r}"
        assert len(set(states)) == 7, f"{label} contains a duplicate state: {states!r}"
        assert set(states) == CANONICAL_STATES, (
            f"{label} does not match the canonical seven-state set exactly.\n"
            f"  found:     {sorted(states)}\n"
            f"  canonical: {sorted(CANONICAL_STATES)}\n"
            f"  extra:     {set(states) - CANONICAL_STATES}\n"
            f"  missing:   {CANONICAL_STATES - set(states)}"
        )


RC_NAMED_STATES = {"today", "released", "unreleased", "skipped", "optional-catalog"}
NT15_ADDED_STATES = {"completed", "temporarily-unavailable"}


def test_pref_01_1_distinguishes_rc_named_states_from_nt15_operational_additions():
    """A4 provenance-fix regression guard. PREF-01.1 was relabeled so the five RC-named
    Area-1 states are distinguished inline from the two NT15 operational additions
    (`completed`, `temporarily-unavailable`). This test does not merely re-check the
    seven-state SET (that is test_desk_states_match_across_json_and_both_markdown_documents
    above) -- it checks that the row still POSITIONALLY separates "RC's own ... names"
    from "NT15 operational additions, not RC decisions", so a future edit that flattens the
    row back into a single undifferentiated list (re-attributing all seven to RC) fails
    here even though the state SET would still look correct."""
    text = (HERE / "RC_TEACHER_PREFERENCE_RECORD.md").read_text(encoding="utf-8")
    idx = text.index("PREF-01.1")
    line_end = text.index("\n", idx)
    row = text[idx:line_end]

    marker = re.search(r"NT15 operational additions?, not RC decisions:?", row, re.IGNORECASE)
    assert marker, (
        "PREF-01.1 row no longer carries the exact 'NT15 operational additions, not RC "
        "decisions' marker phrase -- the A4 provenance fix (distinguishing RC-named states "
        "from NT15-added ones) appears to have been reverted/flattened"
    )

    before_marker = row[: marker.start()]
    after_marker = row[marker.end() :]
    rc_named_tokens = set(_extract_backtick_tokens(before_marker))
    nt15_added_tokens = set(_extract_backtick_tokens(after_marker))

    assert rc_named_tokens == RC_NAMED_STATES, (
        f"states appearing BEFORE the NT15-addition marker (i.e. attributed to RC) drifted "
        f"from the expected five: found {sorted(rc_named_tokens)}, expected "
        f"{sorted(RC_NAMED_STATES)}"
    )
    assert nt15_added_tokens == NT15_ADDED_STATES, (
        f"states appearing AFTER the NT15-addition marker (i.e. NOT attributed to RC) "
        f"drifted from the expected two: found {sorted(nt15_added_tokens)}, expected "
        f"{sorted(NT15_ADDED_STATES)}"
    )
    # And the full row must still carry exactly the canonical seven when both halves are
    # combined -- ties this test back to the shared vocabulary rather than an isolated split.
    assert rc_named_tokens | nt15_added_tokens == CANONICAL_STATES


# =========================================================================================
# 5. OPEN-REGISTER COMPLETENESS (both directions)
# =========================================================================================

OPEN_TOKEN_RE = re.compile(r"\bOPEN-\d+\b")
REGISTER_HEADING_RE = re.compile(r"^### (OPEN-\d+)\b", re.MULTILINE)

D1_THROUGH_D5_FILES = [
    "RC_TEACHER_PREFERENCE_RECORD.md",   # D1
    "GRADING_POLICY_SPEC.md",            # D2
    "SCHOOLOGY_PROJECTION_CONTRACT.md",  # D3
    "DESK_STATE_MODEL.md",               # D4
    "ANSWER_EQUIVALENCE_CONTRACT.md",    # D5
]


def _open_tokens_used_in_d1_through_d5() -> set[str]:
    used: set[str] = set()
    for fname in D1_THROUGH_D5_FILES:
        text = (HERE / fname).read_text(encoding="utf-8")
        used.update(OPEN_TOKEN_RE.findall(text))
    return used


def _register_headings() -> list[str]:
    text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    return REGISTER_HEADING_RE.findall(text)


def _extract_register_section(register_text: str, open_id: str) -> str:
    heading_re = re.compile(rf"^### {re.escape(open_id)}\b.*$", re.MULTILINE)
    m = heading_re.search(register_text)
    assert m, f"OPEN_DECISIONS_REGISTER.md has no '### {open_id}' heading"
    next_heading = re.search(r"^### OPEN-\d+\b", register_text[m.end():], re.MULTILINE)
    end = m.end() + next_heading.start() if next_heading else len(register_text)
    return register_text[m.start():end]


def test_register_contains_exactly_open_01_through_open_19_no_gaps_no_duplicates():
    headings = _register_headings()
    assert len(headings) == len(set(headings)), (
        f"OPEN_DECISIONS_REGISTER.md has a duplicate '### OPEN-NN' heading: {headings}"
    )
    assert sorted(headings, key=lambda h: int(h.split("-")[1])) == CANONICAL_OPEN_IDS, (
        f"OPEN_DECISIONS_REGISTER.md's heading set does not equal exactly OPEN-01..OPEN-19 "
        f"with no gaps: found {sorted(headings)}"
    )


def test_every_open_token_used_in_d1_through_d5_has_a_register_heading():
    used = _open_tokens_used_in_d1_through_d5()
    headings = set(_register_headings())
    unregistered = used - headings
    assert not unregistered, (
        f"OPEN-NN token(s) used in D1-D5 with no matching '### OPEN-NN' heading in "
        f"OPEN_DECISIONS_REGISTER.md: {sorted(unregistered)}"
    )


def test_every_register_heading_is_used_at_least_once_in_d1_through_d5():
    used = _open_tokens_used_in_d1_through_d5()
    headings = set(_register_headings())
    unused = headings - used
    assert not unused, (
        f"OPEN_DECISIONS_REGISTER.md has heading(s) for open item(s) never referenced anywhere "
        f"in D1-D5, i.e. registered but never actually flagged where it applies: {sorted(unused)}"
    )


# =========================================================================================
# 5B. NT16 RESOLUTION INVENTORY -- the register's 10-open/9-resolved split, per-id provenance
#     tokens, and the stale-phrase guard. New for v2.0.
# =========================================================================================

REGISTER_SUMMARY_ROW_RE = re.compile(r"^\|\s*(OPEN-\d+)\s*\|.*\|\s*([^|]+?)\s*\|\s*$", re.MULTILINE)


def _register_summary_status_by_id() -> dict[str, str]:
    text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    statuses: dict[str, str] = {}
    for m in REGISTER_SUMMARY_ROW_RE.finditer(text):
        statuses[m.group(1)] = m.group(2).strip()
    return statuses


def test_register_inventory_is_exactly_ten_open_and_nine_resolved_with_the_expected_split():
    """NEW (v2.0). The register's summary table must carry a status for all nineteen ids,
    the resolved set must be exactly the nine RC ruled on 2026-07-24, and the open set must
    be exactly the remaining ten -- no silent disappearance of a heading, and no drift in
    which nine are resolved."""
    statuses = _register_summary_status_by_id()
    assert set(statuses.keys()) == set(CANONICAL_OPEN_IDS), (
        "OPEN_DECISIONS_REGISTER.md summary table does not carry a status row for every "
        f"OPEN-01..OPEN-19 heading: found {sorted(statuses.keys())}"
    )
    resolved = {oid for oid, status in statuses.items() if status.startswith("RESOLVED")}
    still_open = {oid for oid, status in statuses.items() if status == "OPEN"}
    assert resolved == RESOLVED_OPEN_IDS, (
        f"resolved id set drifted: found {sorted(resolved)}, expected {sorted(RESOLVED_OPEN_IDS)}"
    )
    assert still_open == STILL_OPEN_IDS, (
        f"still-open id set drifted: found {sorted(still_open)}, expected {sorted(STILL_OPEN_IDS)}"
    )
    assert len(resolved) == 9 and len(still_open) == 10, (
        f"expected 9 resolved / 10 open, found {len(resolved)} resolved / {len(still_open)} open"
    )
    # All nineteen headings must still exist -- no silent disappearance.
    headings = set(_register_headings())
    assert headings == set(CANONICAL_OPEN_IDS), (
        f"OPEN_DECISIONS_REGISTER.md headings drifted from the canonical OPEN-01..OPEN-19 "
        f"set: found {sorted(headings)}"
    )


def test_every_resolved_register_id_carries_the_provenance_token_and_no_open_id_does():
    """NEW (v2.0). Every one of the nine resolved ids must carry the 'RESOLVED by RC
    2026-07-24' provenance token in its own register section; none of the ten still-open
    ids may carry it (that would misrepresent an open item as settled)."""
    register_text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    for oid in sorted(RESOLVED_OPEN_IDS, key=lambda x: int(x.split("-")[1])):
        section = _extract_register_section(register_text, oid)
        assert RESOLVED_PROVENANCE_TOKEN in section, (
            f"{oid}: resolved register section must carry the "
            f"'{RESOLVED_PROVENANCE_TOKEN}' provenance token verbatim"
        )
    for oid in sorted(STILL_OPEN_IDS, key=lambda x: int(x.split("-")[1])):
        section = _extract_register_section(register_text, oid)
        assert RESOLVED_PROVENANCE_TOKEN not in section, (
            f"{oid}: still-open register section must NOT carry the "
            f"'{RESOLVED_PROVENANCE_TOKEN}' provenance token -- it is not resolved"
        )


STALE_UNRESOLVED_MARKERS_RE = re.compile(r"unresolved-pending-RC|PROVISIONAL", re.IGNORECASE)

# Markers whose presence near a stale "still open" phrase indicates the mention is framed
# historically (a superseded/changelog note about what used to be true), not a live claim
# that a now-resolved item is still open.
HISTORICAL_CONTEXT_MARKERS = (
    "historical",
    "supersede",
    "superseded",
    "changelog",
    "v1.0",
    "was ",
    "used to",
    "previously",
    "prior to rc",
    "before rc",
    "no longer",
    "retired",
    "decided policy",
    "not a provisional",
    "now resolved",
    # A row/paragraph that says a transition was PROMOTED OUT OF the provisional bucket is
    # describing the decided outcome of RC's ruling, not claiming the item is still open.
    # The full phrase is required deliberately -- the bare word "promoted" is not accepted,
    # so this cannot be used to wave through a genuinely stale "still provisional" claim.
    "promoted from provisional",
    "promoted from `transitions.provisional`",
)


def _enclosing_paragraph_or_row(text: str, match_start: int, match_end: int) -> str:
    """Scope a mention to its own markdown table row (if it sits in one) or to its
    enclosing prose paragraph (blank-line-delimited block) otherwise -- mirrors the
    row/paragraph scoping used elsewhere in this suite (see _enclosing_context below) so a
    neighboring row's or paragraph's own markers can never "leak" into an unrelated mention."""
    line_start = text.rfind("\n", 0, match_start) + 1
    line_end = text.find("\n", match_end)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    if line.lstrip().startswith("|"):
        return line
    para_start = text.rfind("\n\n", 0, match_start)
    para_start = 0 if para_start == -1 else para_start + 2
    para_end = text.find("\n\n", match_end)
    para_end = len(text) if para_end == -1 else para_end
    return text[para_start:para_end]


def test_no_resolved_open_id_appears_next_to_stale_unresolved_language_outside_historical_context():
    """NEW (v2.0). None of the nine resolved ids may appear adjacent to
    'unresolved-pending-RC' / 'PROVISIONAL' language in D1-D5 unless that mention's own
    row/paragraph is explicitly historical/changelog/superseded-note framing. A mention with
    no stale language nearby is trivially fine; a mention WITH stale language nearby must
    also carry a historical marker, or it is presenting a now-resolved item as still open."""
    for fname in D1_THROUGH_D5_FILES:
        text = (HERE / fname).read_text(encoding="utf-8")
        for oid in sorted(RESOLVED_OPEN_IDS, key=lambda x: int(x.split("-")[1])):
            for m in re.finditer(rf"\b{re.escape(oid)}\b", text):
                context = _enclosing_paragraph_or_row(text, m.start(), m.end())
                if not STALE_UNRESOLVED_MARKERS_RE.search(context):
                    continue  # no stale phrase nearby this specific mention -- fine
                context_lower = re.sub(r"\s+", " ", context).lower()
                assert any(marker in context_lower for marker in HISTORICAL_CONTEXT_MARKERS), (
                    f"{fname}: a mention of {oid} sits next to stale "
                    f"'unresolved-pending-RC'/'PROVISIONAL' language with no historical/"
                    f"superseded-note marker in its own row/paragraph -- it may be "
                    f"misrepresenting a RESOLVED item as still open. "
                    f"Context: ...{context.strip()}..."
                )


# =========================================================================================
# 6. NOTHING DECIDED LEAKED INTO THE REGISTER, AND NOTHING DEFERRED DID EITHER
# =========================================================================================


def test_register_excludes_the_three_deferred_matters():
    register_text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")

    # None of the three deferred matters' PREF ids appear as a register heading's own id
    # (deferred items are PREF-NN.M ids, never OPEN-NN ids -- there must be no OPEN-NN
    # heading whose title is actually about one of the deferred features).
    heading_lines = [
        line for line in register_text.splitlines() if line.startswith("### OPEN-")
    ]
    deferred_feature_terms = ("gifting", "tetris", "leaderboard", "celebration", "step-by-step", "intervention")
    for line in heading_lines:
        lowered = line.lower()
        for term in deferred_feature_terms:
            assert term not in lowered, (
                f"a deferred feature term ({term!r}) appears in a register heading -- deferred "
                f"items must never be entered as OPEN items: {line!r}"
            )

    # The three deferred PREF ids must not themselves appear inside a "### OPEN-NN" heading line.
    for pref_id in DEFERRED_PREF_IDS:
        for line in heading_lines:
            assert pref_id not in line, (
                f"deferred item {pref_id} appears inside a register heading line: {line!r}"
            )


def test_register_explicitly_distinguishes_deferred_from_open():
    register_text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    assert "DEFERRED" in register_text and "OPEN" in register_text
    assert re.search(r"DEFERRED\s*(?:≠|!=|is not (?:the )?same as)\s*OPEN", register_text), (
        "OPEN_DECISIONS_REGISTER.md must explicitly state that DEFERRED and OPEN are not "
        "the same status (e.g. 'DEFERRED ≠ OPEN')"
    )
    # And it must name all three deferred matters explicitly as excluded, with their reason.
    assert "step-by-step" in register_text.lower()
    assert "gifting" in register_text.lower()
    assert "intervention" in register_text.lower()


def test_forty_percent_inclusivity_is_not_presented_as_an_open_item():
    register_text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    headings = _register_headings()

    # No OPEN-NN heading title may be about the gate's inclusivity itself (only the
    # *rounding* of the completion ratio, OPEN-08, is open -- inclusivity at exactly 0.40
    # is DECIDED per PREF-03.5 and must never be reframed as unresolved).
    heading_lines = [line for line in register_text.splitlines() if line.startswith("### OPEN-")]
    for line in heading_lines:
        assert "inclusiv" not in line.lower(), (
            f"a register heading appears to reframe the 40% gate's DECIDED inclusivity as "
            f"an open item: {line!r}"
        )

    # The register must explicitly say so, not merely omit it by silence.
    assert re.search(r"inclusiv\w*", register_text, re.IGNORECASE), (
        "OPEN_DECISIONS_REGISTER.md does not explicitly address the 40% gate's inclusivity "
        "at all -- it must state that this is decided, not merely never mention it"
    )
    normalized_register_text = re.sub(r"\s+", " ", register_text)
    assert re.search(r"does not appear\s+in this register", normalized_register_text, re.IGNORECASE), (
        "OPEN_DECISIONS_REGISTER.md must explicitly state that a settled matter (like the "
        "40% gate's inclusivity) does not appear in the register"
    )


# =========================================================================================
# 7. PREF AREA COVERAGE
# =========================================================================================


def test_pref_record_contains_all_fourteen_area_headings_no_gaps():
    text = (HERE / "RC_TEACHER_PREFERENCE_RECORD.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (PREF-\d{2})\b", text, re.MULTILINE)
    assert headings == CANONICAL_PREF_IDS, (
        f"RC_TEACHER_PREFERENCE_RECORD.md's '## PREF-NN' area headings do not equal exactly "
        f"PREF-01..PREF-14 in order: found {headings}"
    )


# =========================================================================================
# 8. DEFERRED-FEATURE GUARD -- terms appear only within a deferred/out-of-scope context
# =========================================================================================

DEFERRED_TERM_RE = re.compile(
    r"gifting|tetris|leaderboard|celebration|step-by-step|intervention", re.IGNORECASE
)

# Any of these nearby (case-insensitive) is evidence the mention sits inside a
# deferred-or-out-of-scope context, not a live scheduling decision.
DEFERRED_CONTEXT_MARKERS = (
    "deferred",
    "explicitly exclude",
    "do not build",
    "does not build",
    "out of scope",
    "denylist",
    "forbidden",
    "not part of",
    "not scheduled",
    "not built",
)


def _assert_terms_only_appear_in_deferred_context(relative_path: str, window: int = 200):
    text = (HERE / relative_path).read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", text)
    matches = list(DEFERRED_TERM_RE.finditer(normalized))
    assert matches, f"{relative_path}: expected at least one deferred-feature mention, found none"
    for m in matches:
        start = max(0, m.start() - window)
        end = min(len(normalized), m.end() + window)
        surrounding = normalized[start:end].lower()
        assert any(marker in surrounding for marker in DEFERRED_CONTEXT_MARKERS), (
            f"{relative_path}: deferred-feature term {m.group()!r} appears without any "
            f"deferred/out-of-scope marker nearby -- context: ...{normalized[start:end]}..."
        )


def test_phased_product_sequence_mentions_deferred_features_only_in_deferred_context():
    _assert_terms_only_appear_in_deferred_context("PHASED_PRODUCT_SEQUENCE.md")


def test_next_tranche_proposal_mentions_deferred_features_only_in_deferred_context():
    _assert_terms_only_appear_in_deferred_context("NEXT_TRANCHE_PROPOSAL.md")


# =========================================================================================
# 9. NO-LIVE-WRITE + NO-NETWORK GUARD
# =========================================================================================


def test_schoology_contract_states_no_live_write_normatively():
    text = (HERE / "SCHOOLOGY_PROJECTION_CONTRACT.md").read_text(encoding="utf-8")
    assert re.search(r"NO-LIVE-WRITE constraint", text), (
        "SCHOOLOGY_PROJECTION_CONTRACT.md must carry a section normatively titled around "
        "the NO-LIVE-WRITE constraint"
    )
    assert "MUST NOT" in text, (
        "SCHOOLOGY_PROJECTION_CONTRACT.md's NO-LIVE-WRITE section must use normative "
        "'MUST NOT' language, not merely descriptive prose"
    )
    assert "network" in text.lower() and "Schoology tenant" in text


def test_schoology_projection_json_declares_no_live_write():
    data = json.loads((HERE / "schoology_projection.v2.json").read_text(encoding="utf-8"))
    assert data.get("no_live_write") is True
    assert "network" in data.get("no_live_write_statement", "").lower()


def _iter_imported_module_names(py_path: Path):
    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.module


def _is_forbidden_network_module(name: str) -> bool:
    if name in FORBIDDEN_NETWORK_MODULES:
        return True
    return any(name == prefix or name.startswith(prefix + ".") for prefix in FORBIDDEN_NETWORK_DOTTED_PREFIXES)


def test_no_python_file_in_package_imports_a_network_library():
    py_files = sorted(HERE.rglob("*.py"))
    assert py_files, "expected at least one .py file under product-policy/"
    offenders: list[str] = []
    for py_path in py_files:
        if "__pycache__" in py_path.parts:
            continue
        for name in _iter_imported_module_names(py_path):
            if _is_forbidden_network_module(name):
                offenders.append(f"{py_path.relative_to(HERE)} imports {name!r}")
    assert not offenders, "forbidden network import(s) found:\n" + "\n".join(offenders)


# =========================================================================================
# 10. D6 (PHASED_PRODUCT_SEQUENCE.md) HAS NO DATES
# =========================================================================================

ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

# Forbidden calendar/duration/sprint markers: a Q1-Q4 style label, a digit attached to a
# duration unit (e.g. "3 weeks", "2-day"), or the bare word "sprint".
FORBIDDEN_CALENDAR_RE = re.compile(
    r"\bQ[1-4]\b" r"|\b\d+\s*-?\s*(?:day|week|month|sprint|quarter|year)s?\b" r"|\bsprint\b",
    re.IGNORECASE,
)

# The sentences (Scope section + Provenance summary + any NT16 changelog restatement) that
# RESTATE the no-dates rule itself -- the only permitted place these forbidden markers may
# appear, per the brief's instruction to scope the assertion so it doesn't false-positive on
# the rule's own prose.
NO_DATES_RULE_SENTENCE_RE = re.compile(r"[^.]*no calendar dates[^.]*\.", re.IGNORECASE)


def test_d6_iso_dates_appear_only_in_the_provenance_header():
    text = (HERE / "PHASED_PRODUCT_SEQUENCE.md").read_text(encoding="utf-8")
    header_block = "\n".join(text.splitlines()[:6])

    all_dates = ISO_DATE_RE.findall(text)
    header_dates = ISO_DATE_RE.findall(header_block)

    assert all_dates, "expected the provenance header's 2026-07-24 date to be present at all"
    assert set(all_dates) == {"2026-07-24"}, (
        f"PHASED_PRODUCT_SEQUENCE.md contains a calendar-date-shaped string other than the "
        f"provenance header's 2026-07-24: {sorted(set(all_dates))}"
    )
    assert all_dates == header_dates, (
        "PHASED_PRODUCT_SEQUENCE.md contains a 2026-07-24-shaped date OUTSIDE its provenance "
        "header block -- D6 must carry no calendar dates in its body"
    )


def test_d6_body_has_no_durations_sprint_counts_or_quarter_labels_outside_the_rule_prose():
    text = (HERE / "PHASED_PRODUCT_SEQUENCE.md").read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", text)

    rule_sentences = NO_DATES_RULE_SENTENCE_RE.findall(normalized)
    assert len(rule_sentences) >= 2, (
        "expected to find the two 'no calendar dates ...' rule-restating sentences "
        "(Scope section + Provenance summary) in PHASED_PRODUCT_SEQUENCE.md"
    )

    stripped = NO_DATES_RULE_SENTENCE_RE.sub(" ", normalized)
    offenders = [m.group() for m in FORBIDDEN_CALENDAR_RE.finditer(stripped)]
    assert not offenders, (
        f"PHASED_PRODUCT_SEQUENCE.md's body contains calendar/duration/sprint-count content "
        f"outside its own no-dates-rule sentences (only the provenance header's 2026-07-24 "
        f"and prose describing the no-dates rule itself are permitted): {offenders}"
    )


# =========================================================================================
# 11. DESK TRANSITION NORMATIVITY -- NT16 (v2.0): DECIDED-state guards.
#     Historical note: Codex GPT-5.6 SOL review finding B2 (HIGH) found T7/T11/T12/T13
#     sitting in the decided `legal` table while simultaneously being marked
#     unresolved-pending-RC (OPEN-18) -- a contradictory-normativity defect. The D4 owner's
#     v1.0 fix moved them to a sibling `transitions.provisional` bucket, tagged
#     `"normative": false`. RC's 2026-07-24 ruling then RESOLVED OPEN-18 outright: all four
#     are promoted into `transitions.legal`, and `transitions.provisional` is now
#     permanently empty. The guards below check the DECIDED-state reality directly (empty
#     provisional bucket + retirement record; T7/T11/T12/T13 living in transitions.legal with
#     teacher-only actor markers and T11's pre-completion precondition; both DESK_STATE_MODEL.md
#     and NEXT_TRANCHE_PROPOSAL.md presenting them as decided). test_desk_state_model.py
#     already exercises this at the D4 level; the checks below are this package's own,
#     independent, cross-document verification.
# =========================================================================================

OPEN_18_TRANSITION_IDS = {"T7", "T11", "T12", "T13"}


def _desk_state_model_json() -> dict:
    return json.loads((HERE / "desk_state_model.v2.json").read_text(encoding="utf-8"))


def test_desk_transition_buckets_are_pairwise_disjoint_at_package_level():
    """No transition id may appear in more than one of legal / provisional / illegal --
    a transition is either decided, provisionally-allowed-but-unresolved, or forbidden;
    never two of those at once.

    NT16 note (why this was adjusted, not weakened): v1.0 additionally asserted
    transitions.provisional was non-empty, which was true when T7/T11/T12/T13 lived there.
    OPEN-18 is now RESOLVED and that bucket is deliberately, permanently empty (see
    test_desk_provisional_bucket_is_empty_and_retirement_is_recorded below for the dedicated
    guard on that) -- an empty provisional bucket is trivially disjoint from the other two,
    so requiring it to be non-empty here would fail against the correct, decided state. The
    substantive invariant this test exists for -- no transition id ever appears in more than
    one bucket -- is unchanged and still fully enforced below.
    """
    model = _desk_state_model_json()
    legal_ids = {t["id"] for t in model["transitions"]["legal"]}
    provisional_ids = {t["id"] for t in model["transitions"].get("provisional", [])}
    illegal_ids = {t["id"] for t in model["transitions"]["illegal"]}

    overlaps = {
        "legal & provisional": legal_ids & provisional_ids,
        "legal & illegal": legal_ids & illegal_ids,
        "provisional & illegal": provisional_ids & illegal_ids,
    }
    for label, overlap in overlaps.items():
        assert not overlap, f"transition id(s) appear in both buckets ({label}): {sorted(overlap)}"


def test_desk_provisional_bucket_is_empty_and_retirement_is_recorded():
    """INVERTED for NT16 (was test_desk_provisional_bucket_entries_are_non_normative_and_
    open_18_tagged, which required transitions.provisional to be non-empty and each entry
    tagged normative:false/open_item:"OPEN-18"). RC's 2026-07-24 ruling on OPEN-18 promoted
    all four entries into transitions.legal, so transitions.provisional must now be EMPTY,
    and a transitions.provisional_retirement object must exist carrying the RESOLVED
    provenance token and naming the four promoted transitions -- so a consumer can
    mechanically tell the bucket was deliberately retired, not silently emptied by
    accident."""
    model = _desk_state_model_json()
    provisional = model["transitions"].get("provisional", [])
    assert provisional == [], (
        f"transitions.provisional must be empty (retired) as of OPEN-18's resolution, "
        f"found: {provisional}"
    )
    retirement = model["transitions"].get("provisional_retirement")
    assert retirement, "transitions.provisional_retirement must exist recording the retirement"
    assert retirement.get("provenance") == RESOLVED_PROVENANCE_TOKEN, (
        f"transitions.provisional_retirement must carry the '{RESOLVED_PROVENANCE_TOKEN}' "
        f"provenance token, found {retirement.get('provenance')!r}"
    )
    assert set(retirement.get("promoted_transitions", [])) == OPEN_18_TRANSITION_IDS, (
        f"transitions.provisional_retirement must name exactly the four promoted "
        f"transitions, found {retirement.get('promoted_transitions')!r}"
    )


def test_desk_legal_table_carries_no_provisional_markers():
    """Nothing in the decided transitions.legal table may carry normative: false or an
    OPEN-18 tag -- that would let a provisional transition be silently read as decided by
    a consumer that only checks transitions.legal. Survives NT16 unchanged: it remains true
    (and newly load-bearing, since T7/T11/T12/T13 now LIVE in transitions.legal) that none
    of them may carry a stale provisional marker."""
    model = _desk_state_model_json()
    for t in model["transitions"]["legal"]:
        assert t.get("normative", True) is not False, (
            f"legal transition {t['id']} must not be marked non-normative"
        )
        assert t.get("open_item") != "OPEN-18", (
            f"legal transition {t['id']} must not carry the OPEN-18 tag -- OPEN-18 "
            f"transitions belong only in transitions.provisional"
        )


def test_desk_open_18_transitions_are_specifically_t7_t11_t12_t13_and_live_in_legal():
    """INVERTED for NT16 (was ..._and_live_in_provisional). RC's 2026-07-24 ruling promoted
    T7/T11/T12/T13 out of transitions.provisional (now empty) into transitions.legal. This
    test asserts: they are disjoint from the (now-empty) provisional bucket, they are all
    present in transitions.legal, none carries a stale normative:false/open_item marker,
    each carries actor == 'teacher_only' and student_may_initiate == False, and T11
    specifically carries a machine-readable pre-completion precondition guarding the
    completed boundary."""
    model = _desk_state_model_json()
    legal = {t["id"]: t for t in model["transitions"]["legal"]}
    provisional_ids = {t["id"] for t in model["transitions"].get("provisional", [])}

    assert OPEN_18_TRANSITION_IDS.isdisjoint(provisional_ids), (
        f"OPEN-18 transitions must not remain in transitions.provisional (retired): "
        f"{OPEN_18_TRANSITION_IDS & provisional_ids} still present"
    )
    assert OPEN_18_TRANSITION_IDS <= set(legal.keys()), (
        f"all four OPEN-18 transitions must be in transitions.legal: missing "
        f"{OPEN_18_TRANSITION_IDS - set(legal.keys())}"
    )

    for tid in sorted(OPEN_18_TRANSITION_IDS):
        entry = legal[tid]
        assert entry.get("normative", True) is not False, (
            f"legal transition {tid} must not carry a stale normative: false marker"
        )
        assert "open_item" not in entry, (
            f"legal transition {tid} must not carry a stale open_item marker "
            f"(found {entry.get('open_item')!r}) -- OPEN-18 is resolved, not still-open"
        )
        assert entry.get("actor") == "teacher_only", (
            f"legal transition {tid} must carry actor == 'teacher_only'"
        )
        assert entry.get("student_may_initiate") is False, (
            f"legal transition {tid} must carry student_may_initiate == False"
        )

    t11 = legal["T11"]
    assert "precondition" in t11, "T11 must carry a machine-readable pre-completion precondition"
    precondition = t11["precondition"]
    assert precondition.get("field") == "student_completion_state != 'completed'", (
        f"T11's precondition must guard the pre-completion boundary, found {precondition!r}"
    )


def test_open_18_has_a_register_heading_and_is_referenced_by_the_resolved_legal_transitions():
    """RE-SCOPED for NT16 (was ..._and_is_referenced_by_the_provisional_bucket). The
    register still carries a heading for OPEN-18 (already implied by the bidirectional
    open-register checks in section 5, but asserted independently here) -- and now the
    JSON's own DECIDED transitions.legal entries for T7/T11/T12/T13 are what carry
    resolved_open_item == 'OPEN-18', proving the link between the register entry and the
    promoted transitions is still machine-readable, not merely that the token appears
    somewhere in D4."""
    model = _desk_state_model_json()
    legal = model["transitions"]["legal"]
    open_18_legal_entries = [t for t in legal if t["id"] in OPEN_18_TRANSITION_IDS]
    assert len(open_18_legal_entries) == len(OPEN_18_TRANSITION_IDS), (
        f"expected all four OPEN-18 transitions in transitions.legal, found "
        f"{[t['id'] for t in open_18_legal_entries]}"
    )
    for t in open_18_legal_entries:
        assert t.get("resolved_open_item") == "OPEN-18", (
            f"legal transition {t['id']} must carry resolved_open_item == 'OPEN-18', "
            f"found {t.get('resolved_open_item')!r}"
        )

    headings = set(_register_headings())
    assert "OPEN-18" in headings, (
        "OPEN_DECISIONS_REGISTER.md has no '### OPEN-18' heading, but "
        "desk_state_model.v2.json's transitions.legal entries for T7/T11/T12/T13 "
        "reference it"
    )


# Markers whose presence near a T7/T11/T12/T13 mention indicates the mention is being
# handled as provisional/unresolved, not asserted as decided RC policy.
NON_NORMATIVE_CONTEXT_MARKERS = (
    "open-18",
    "provisional",
    "non-normative",
    "not decided",
    "unresolved",
    "not settled",
    "not part of the decided",
)

# Markers that indicate a stale-sounding mention (one of NON_NORMATIVE_CONTEXT_MARKERS
# above) is nonetheless legitimate -- either because the whole passage is explicitly
# historical/changelog/superseded-note framing, or because it directly cites RC's ruling.
DECIDED_OR_HISTORICAL_MARKERS = (
    "resolved by rc",
    "now resolved",
    "2026-07-24",
    "promoted",
    "confirmed",
    "no longer",
    "retired",
    "supersede",
    "historical",
    "changelog",
    "now empty",
    "decided policy",
)


def _enclosing_context(text: str, match_start: int, match_end: int) -> str:
    """Scope a mention to its OWN markdown table row (if the mention sits in one) or to
    its enclosing prose paragraph (blank-line-delimited block) otherwise. Deliberately NOT
    a fixed character window: a fixed window over a dense table (where T7/T11/T12/T13 sit
    on four consecutive rows a few dozen characters apart) can let a neighboring row's own
    marker "leak" into a mutated row that itself no longer carries one, which would make
    the guard pass even though that specific row was rewritten. Row/paragraph scoping
    closes that gap: a table row is checked against only its own cells, and a prose mention
    is checked against only its own paragraph."""
    line_start = text.rfind("\n", 0, match_start) + 1
    line_end = text.find("\n", match_end)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    if line.lstrip().startswith("|"):
        return line
    para_start = text.rfind("\n\n", 0, match_start)
    para_start = 0 if para_start == -1 else para_start + 2
    para_end = text.find("\n\n", match_end)
    para_end = len(text) if para_end == -1 else para_end
    return text[para_start:para_end]


def _assert_transition_ids_now_presented_as_decided(relative_path: str):
    """INVERTED for NT16 (was _assert_transition_ids_never_presented_as_decided, which
    required a non-normative marker near every mention of T7/T11/T12/T13). RC's ruling
    means both documents must now present these four AS decided: a mention carrying no
    stale marker at all is fine (neutral/decided framing); a mention that DOES carry a
    stale marker (e.g. 'provisional') is only acceptable if the same row/paragraph is
    explicitly historical/changelog/superseded-note framing (it may legitimately describe
    what v1.0 used to do) -- otherwise it is misrepresenting a now-decided transition as
    still open."""
    text = (HERE / relative_path).read_text(encoding="utf-8")

    assert "transitions.legal" in text, (
        f"{relative_path} does not refer to transitions.legal -- as of OPEN-18's resolution "
        f"T7/T11/T12/T13 live there, and cross-document agreement requires the same bucket "
        f"name be used everywhere"
    )

    found_any = False
    for tid in sorted(OPEN_18_TRANSITION_IDS):
        matches = list(re.finditer(rf"\b{tid}\b", text))
        assert matches, f"{relative_path}: expected at least one mention of {tid}, found none"
        for m in matches:
            found_any = True
            context = _enclosing_context(text, m.start(), m.end())
            context_lower = re.sub(r"\s+", " ", context).lower()
            has_stale_marker = any(marker in context_lower for marker in NON_NORMATIVE_CONTEXT_MARKERS)
            if not has_stale_marker:
                continue  # presented as decided (or neutral) -- fine
            assert any(marker in context_lower for marker in DECIDED_OR_HISTORICAL_MARKERS), (
                f"{relative_path}: a mention of {tid} carries non-normative/unresolved "
                f"language ('provisional'/'not decided'/etc) with no decided/historical "
                f"marker in its own row/paragraph -- it may be misrepresenting a "
                f"now-DECIDED transition as still open. Context: ...{context.strip()}..."
            )
    assert found_any


def test_desk_state_model_now_presents_open_18_transitions_as_decided():
    _assert_transition_ids_now_presented_as_decided("DESK_STATE_MODEL.md")


def test_next_tranche_proposal_now_presents_open_18_transitions_as_decided():
    _assert_transition_ids_now_presented_as_decided("NEXT_TRANCHE_PROPOSAL.md")


# =========================================================================================
# 11B. NT16 NEW GUARDS -- completed's zero-exit guarantee, grading_policy.v2.json's
#      no-open-items declaration.
# =========================================================================================


def test_completed_has_zero_outbound_legal_transitions_and_completed_to_skipped_is_illegal():
    """NEW (v2.0). `completed` is DECIDED terminal (OPEN-17, RESOLVED): it must never
    appear as a `from` state in transitions.legal, and `completed -> skipped` (X3) must be
    present in transitions.illegal -- the guard that keeps T11's pre-completion precondition
    meaningful."""
    model = _desk_state_model_json()
    outbound_from_completed = [t for t in model["transitions"]["legal"] if t["from"] == "completed"]
    assert outbound_from_completed == [], (
        f"transitions.legal must have zero outbound transitions from 'completed', found: "
        f"{[t['id'] for t in outbound_from_completed]}"
    )
    illegal_completed_to_skipped = [
        t for t in model["transitions"]["illegal"]
        if t["from"] == "completed" and t["to"] == "skipped"
    ]
    assert len(illegal_completed_to_skipped) == 1, (
        "transitions.illegal must contain exactly one completed -> skipped entry (X3)"
    )


def test_grading_policy_json_declares_no_open_items_and_no_provisional_block():
    """NEW (v2.0). grading_policy.v2.json must declare open_item_ids: [] and a non-empty
    resolved_open_item_ids, and must no longer carry the v1.0 provisional_implementation_
    choices block (replaced by resolved_open_items)."""
    policy = json.loads((HERE / "grading_policy.v2.json").read_text(encoding="utf-8"))
    assert policy.get("open_item_ids") == [], (
        f"grading_policy.v2.json's open_item_ids must be empty, found {policy.get('open_item_ids')!r}"
    )
    assert policy.get("resolved_open_item_ids"), (
        "grading_policy.v2.json must carry a non-empty resolved_open_item_ids"
    )
    assert "provisional_implementation_choices" not in policy, (
        "grading_policy.v2.json must no longer carry a provisional_implementation_choices block"
    )


# =========================================================================================
# 12. CODEX SOL REVIEW RE-CHECK RESIDUALS (R1-R6) -- guards for R3 (stale register wording),
#     R4 (D1's RC-verbatim phrase vs. D3's B3 fix), R5 (schoology_computation_mode reporting),
#     and R6 (no dangling ASSUMPTION-N reference). R1/R2 are covered by the sibling suites
#     (test_parity_check.py's test_b1_*/test_r2_* groups) and are not duplicated here; this
#     section is this package's own cross-document verification, plus one interaction check
#     tying D3+D4+D7's fail-closed/decided-teacher-authority story together.
# =========================================================================================

STALE_REPRODUCE_PHRASE_RE = re.compile(r"reproduce the intended result", re.IGNORECASE)
RECONCILING_ANNOTATION_ANCHOR = "**Reconciling annotation (NT15, not RC's words):**"


def test_reproduce_intended_result_phrase_absent_from_d3_but_preserved_verbatim_in_d1():
    """R4 stale-phrase guard. D3 must never carry RC's 'reproduce the intended result'
    phrase (removed under finding B3, since it reads as a native-parity claim D3's own
    §4.3 verdict refutes). D1 IS allowed to carry it -- but ONLY as RC's own verbatim
    PREF-05.9 decision text, AND only alongside the reconciling annotation that explains
    the resolution. A future edit that softens PREF-05.9's wording, OR that deletes the
    annotation and leaves the bare phrase unexplained, must fail here; the current,
    correct state (RC's words preserved + annotation present) must pass."""
    d3_contract = (HERE / "SCHOOLOGY_PROJECTION_CONTRACT.md").read_text(encoding="utf-8")
    d3_json_text = (HERE / "schoology_projection.v2.json").read_text(encoding="utf-8")
    d1_text = (HERE / "RC_TEACHER_PREFERENCE_RECORD.md").read_text(encoding="utf-8")

    assert not STALE_REPRODUCE_PHRASE_RE.search(d3_contract), (
        "SCHOOLOGY_PROJECTION_CONTRACT.md must not carry the 'reproduce the intended result' "
        "phrase -- this was removed under Codex SOL review finding B3"
    )
    assert not STALE_REPRODUCE_PHRASE_RE.search(d3_json_text), (
        "schoology_projection.v2.json must not carry the 'reproduce the intended result' "
        "phrase for the same reason as the .md contract"
    )

    # D1 must still carry RC's verbatim phrase (do NOT soften/reword her decision text)...
    matches = list(STALE_REPRODUCE_PHRASE_RE.finditer(d1_text))
    assert matches, (
        "RC_TEACHER_PREFERENCE_RECORD.md no longer carries RC's verbatim PREF-05.9 phrase "
        "'reproduce the intended result' -- this is RC's own recorded wording and must not "
        "be silently softened or reworded, even to resolve an apparent tension with D3"
    )

    # ...AND the reconciling annotation that explains it must still be present...
    assert RECONCILING_ANNOTATION_ANCHOR in d1_text, (
        "RC_TEACHER_PREFERENCE_RECORD.md must carry the reconciling annotation block "
        "explaining PREF-05.9's verbatim phrase against D3's NOT_NATIVELY_REPRESENTABLE "
        "verdict -- without it, the bare phrase is unexplained and reads as an "
        "unacknowledged tension with D3's finding"
    )
    annotation_idx = d1_text.index(RECONCILING_ANNOTATION_ANCHOR)

    # ...and every occurrence of the phrase in D1 must be accounted for: one inside
    # PREF-05.9's own row (before the annotation), and the rest inside the annotation
    # itself (which quotes the phrase back to explain it) -- never floating free elsewhere.
    before_annotation = [m for m in matches if m.start() < annotation_idx]
    annotation_window_end = annotation_idx + 1500
    within_annotation = [m for m in matches if annotation_idx <= m.start() < annotation_window_end]

    assert before_annotation, (
        "expected the verbatim phrase inside PREF-05.9's own decision-text row, before the "
        "reconciling annotation -- found no occurrence there"
    )
    assert within_annotation, (
        "expected the reconciling annotation to itself quote/reference the phrase it is "
        "explaining -- found no occurrence within the annotation"
    )
    accounted_for = {m.start() for m in before_annotation} | {m.start() for m in within_annotation}
    all_positions = {m.start() for m in matches}
    assert all_positions == accounted_for, (
        f"the verbatim phrase appears in D1 at unsanctioned location(s) -- outside "
        f"PREF-05.9's row and outside the reconciling annotation: "
        f"{sorted(all_positions - accounted_for)}"
    )

    # The annotation must actually engage with the tension, not just exist as boilerplate
    # near the phrase.
    annotation_window = d1_text[annotation_idx:annotation_window_end]
    assert "PREF-05.9" in annotation_window
    assert "PREF-05.14" in annotation_window
    assert "NOT_NATIVELY_REPRESENTABLE" in annotation_window


def test_register_open_18_section_reflects_promotion_into_legal():
    """R3 guard, INVERTED for NT16 (was ..._references_provisional_bucket_not_modeled_as_
    legal, which required the section to name transitions.provisional and forbade
    'modeled as legal' phrasing). RC's ruling means the OPEN-18 register section must now
    state it is RESOLVED, name transitions.legal as where T7/T11/T12/T13 currently live,
    and describe the promotion out of transitions.provisional (historical framing of the
    retired bucket is fine -- the register's job is to preserve the audit trail -- but the
    section must not present the four as still living in transitions.provisional today)."""
    register_text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    section = _extract_register_section(register_text, "OPEN-18")

    assert "RESOLVED" in section, "OPEN-18 register section must state it is RESOLVED"
    assert "transitions.legal" in section, (
        "OPEN_DECISIONS_REGISTER.md's OPEN-18 section must name transitions.legal as "
        "where T7/T11/T12/T13 now live"
    )
    assert re.search(r"promot\w*", section, re.IGNORECASE), (
        "OPEN-18 register section must describe the promotion from transitions.provisional "
        "into transitions.legal"
    )
    for tid in sorted(OPEN_18_TRANSITION_IDS):
        assert re.search(rf"\b{tid}\b", section), (
            f"OPEN-18 register section no longer names transition {tid}"
        )


def test_fail_closed_and_decided_teacher_authority_story_agrees_across_d3_d4_d7():
    """RE-SCOPED for NT16 (was test_fail_closed_and_provisional_story_agrees_across_d3_d4_
    d7). The interaction check: D4's desk_state_model.v2.json decided transitions.legal
    bucket, D3's contract §3 fail-closed release-gating convention, and D7's OPEN-18
    register text must tell the SAME story about T7/T11/T12/T13 (now DECIDED, teacher-only)
    and about optional-catalog fail-closed gating (unaffected by NT16) -- not merely be
    individually correct in isolation from each other. The fail-closed half of this story
    (optional-catalog gating) is unchanged; the provisional half is replaced by the
    decided/teacher-authority half."""
    # Leg 1 (D4): the four ids are now legal (decided) and carry teacher-only authority;
    # transitions.provisional is empty.
    model = _desk_state_model_json()
    legal_ids = {t["id"] for t in model["transitions"]["legal"]}
    provisional_ids = {t["id"] for t in model["transitions"].get("provisional", [])}
    assert OPEN_18_TRANSITION_IDS <= legal_ids, (
        f"D4 leg: expected {sorted(OPEN_18_TRANSITION_IDS)} in transitions.legal, "
        f"found {sorted(legal_ids)}"
    )
    assert not provisional_ids, (
        f"D4 leg: transitions.provisional must be empty (retired), found {sorted(provisional_ids)}"
    )
    for t in model["transitions"]["legal"]:
        if t["id"] in OPEN_18_TRANSITION_IDS:
            assert t.get("actor") == "teacher_only", (
                f"D4 leg: legal transition {t['id']} must carry actor == 'teacher_only'"
            )
            assert t.get("student_may_initiate") is False, (
                f"D4 leg: legal transition {t['id']} must carry student_may_initiate == False"
            )

    # Leg 2 (D3, prose): the contract states the fail-closed convention -- unaffected by
    # NT16 -- optional-catalog requires explicit assignment, unrecognized/malformed values
    # fail closed.
    d3_contract = (HERE / "SCHOOLOGY_PROJECTION_CONTRACT.md").read_text(encoding="utf-8")
    assert re.search(r"fail.closed", d3_contract, re.IGNORECASE), (
        "D3 leg: SCHOOLOGY_PROJECTION_CONTRACT.md does not state a fail-closed convention"
    )
    assert re.search(r"optional-catalog", d3_contract, re.IGNORECASE), (
        "D3 leg: fail-closed convention section must address optional-catalog"
    )
    assert re.search(r"explicit(ly)? (teacher )?assign", d3_contract, re.IGNORECASE), (
        "D3 leg: fail-closed convention must tie optional-catalog to requiring explicit "
        "teacher assignment"
    )
    assert re.search(r"unrecognized|malformed", d3_contract, re.IGNORECASE), (
        "D3 leg: fail-closed convention must address unrecognized/malformed values failing "
        "closed, never open"
    )

    # Leg 2b (D3, JSON): the machine-readable companion agrees structurally.
    projection_json = json.loads((HERE / "schoology_projection.v2.json").read_text(encoding="utf-8"))
    fail_closed = projection_json.get("release_gating", {}).get("fail_closed_convention")
    assert fail_closed, (
        "D3 leg: schoology_projection.v2.json is missing "
        "release_gating.fail_closed_convention"
    )

    # Leg 3 (D7): the register names transitions.legal for OPEN-18, not transitions.provisional.
    register_text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    open_18_section = _extract_register_section(register_text, "OPEN-18")
    assert "transitions.legal" in open_18_section, (
        "D7 leg: OPEN-18 register section does not name transitions.legal as where the "
        "four transitions now live"
    )

    # Agreement: all three legs must name the SAME four transition ids as now decided/legal
    # -- not a different set, not a partial one.
    register_ids = {tid for tid in OPEN_18_TRANSITION_IDS if re.search(rf"\b{tid}\b", open_18_section)}
    assert register_ids == OPEN_18_TRANSITION_IDS == (OPEN_18_TRANSITION_IDS & legal_ids), (
        f"the three legs disagree on which transition ids are now decided/legal: "
        f"D4(JSON)={sorted(legal_ids & OPEN_18_TRANSITION_IDS)}, "
        f"D7(register)={sorted(register_ids)}, expected={sorted(OPEN_18_TRANSITION_IDS)}"
    )


def test_schoology_projection_json_report_fields_include_computation_mode():
    """R5 coverage. Every reconciliation report must name the Schoology-native computation
    mode it used, so a reader never has to assume/guess which calculation
    schoology_native_quarter_grade represents."""
    data = json.loads((HERE / "schoology_projection.v2.json").read_text(encoding="utf-8"))
    report_fields = data["divergence_handling"]["report_fields"]
    assert "schoology_computation_mode" in report_fields, (
        "schoology_projection.v2.json's divergence_handling.report_fields must include "
        "'schoology_computation_mode' (R5)"
    )


ASSUMPTION_TOKEN_RE = re.compile(r"\bASSUMPTION-\d+\b")
ASSUMPTION_DEFINITION_RE = re.compile(r"Assumption to confirm \((ASSUMPTION-\d+)\)")


def test_every_assumption_referenced_in_parity_check_has_a_contract_prose_definition():
    """R6 coverage. Every ASSUMPTION-N token parity_check.py's code/comments actually rely
    on must have a corresponding prose definition in SCHOOLOGY_PROJECTION_CONTRACT.md --
    no dangling reference to an assumption number the contract never explains."""
    parity_text = (HERE / "parity_check.py").read_text(encoding="utf-8")
    contract_text = (HERE / "SCHOOLOGY_PROJECTION_CONTRACT.md").read_text(encoding="utf-8")

    referenced = set(ASSUMPTION_TOKEN_RE.findall(parity_text))
    assert referenced, "expected parity_check.py to reference at least one ASSUMPTION-N"

    defined = set(ASSUMPTION_DEFINITION_RE.findall(contract_text))
    missing = referenced - defined
    assert not missing, (
        f"parity_check.py references ASSUMPTION id(s) with no 'Assumption to confirm "
        f"(ASSUMPTION-N):' prose definition in SCHOOLOGY_PROJECTION_CONTRACT.md: "
        f"{sorted(missing)}"
    )


# =========================================================================================
# 13. NT16 WORK PACKAGE F -- the consolidated RC-rulings acceptance-proof suite
#     (test_rc_rulings_acceptance.py) is itself tamper-evident: exactly thirteen
#     explicitly-numbered test_proof_NN_* functions, 01-13, no gaps, no duplicates. A
#     reviewer relies on that file being complete and correctly numbered to confirm all
#     nine RC rulings are discriminatingly proven in one place -- this guard makes a
#     silently dropped, duplicated, or renumbered proof fail here rather than pass unnoticed.
# =========================================================================================

PROOF_FUNCTION_NAME_RE = re.compile(r"^test_proof_(\d{2})_")


def test_rc_rulings_acceptance_suite_defines_exactly_thirteen_numbered_proofs():
    tree = ast.parse(
        (HERE / "test_rc_rulings_acceptance.py").read_text(encoding="utf-8"),
        filename="test_rc_rulings_acceptance.py",
    )
    proof_numbers = [
        m.group(1)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        for m in [PROOF_FUNCTION_NAME_RE.match(node.name)]
        if m
    ]

    assert len(proof_numbers) == 13, (
        f"test_rc_rulings_acceptance.py must define exactly thirteen test_proof_NN_* "
        f"functions, found {len(proof_numbers)}: {proof_numbers}"
    )
    assert len(set(proof_numbers)) == 13, (
        f"test_rc_rulings_acceptance.py has a duplicate proof number: {proof_numbers}"
    )
    expected = {f"{i:02d}" for i in range(1, 14)}
    assert set(proof_numbers) == expected, (
        f"test_rc_rulings_acceptance.py's proof numbers do not run 01..13 with no gaps: "
        f"found {sorted(proof_numbers)}, expected {sorted(expected)}"
    )


# =========================================================================================
# 14. CODEX REVIEW REMEDIATION (C5, C6) -- C6: the package must carry no live-stale
#     *.v1.json reference (a mention presented as if a deleted file still exists) and the
#     three deleted v1 artifacts must actually be gone from disk. C5 (register half): RC's
#     OPEN-09 ruling fixed display-rounding PRECISION but never specified the rounding MODE;
#     the register's OPEN-09 entry must record that residual as a clearly labeled
#     implementation reading flagged for RC confirmation while staying RESOLVED, and
#     grading_policy.v2.json (landed by a concurrent sibling D2 work package) must declare a
#     display_rounding_mode value that is itself explicitly labeled the same way. These
#     guards reuse this suite's own row/paragraph-scoping helper
#     (_enclosing_paragraph_or_row) and HISTORICAL_CONTEXT_MARKERS rather than inventing a
#     second mechanism -- the same approach test_no_resolved_open_id_appears_next_to_stale_
#     unresolved_language_outside_historical_context already uses for the analogous
#     resolved-open-id check above.
# =========================================================================================

STALE_V1_ARTIFACT_NAMES = (
    "grading_policy.v1.json",
    "desk_state_model.v1.json",
    "schoology_projection.v1.json",
)

# A "<name>.v1.json ... -> <name>.v2.json" (or Unicode "->") rename-arrow mention is itself
# historical provenance -- it documents what a file used to be called, not a live pointer at
# a file that still exists. This is checked as an explicit, narrow addition alongside
# HISTORICAL_CONTEXT_MARKERS -- rather than adding a bare arrow character to that marker
# list -- because "->"/"->" is used package-wide for many unrelated pairs (state
# transitions, before/after prose) and would be far too broad a signal on its own; only the
# specific v1.json -> v2.json shape counts as historical here.
RENAME_ARROW_RE = re.compile(
    r"\.v1\.json[`'\"]?\s*(?:→|->)\s*[`'\"]?[\w./-]*\.v2\.json"
)


def test_no_live_stale_v1_reference_outside_historical_context():
    """Codex review C6. Every one of the three superseded *.v1.json filenames may still be
    MENTIONED in the package -- changelog notes, Supersedes blocks, and rename-arrow
    provenance are all legitimate historical record-keeping this guard must not break. What
    it must never do is appear as though it were still a live, current artifact. Scans every
    file in this suite's own ALL_EXPECTED_FILES manifest (the same file universe the
    file-manifest test above already checks exists) and, for each *.v1.json mention, requires
    either a rename-arrow shape or a HISTORICAL_CONTEXT_MARKERS hit in that mention's own
    enclosing paragraph/table row.

    Excludes this suite's own file (test_policy_package.py): STALE_V1_ARTIFACT_NAMES above
    must contain the three literal filenames verbatim so this guard has something to search
    for -- that tuple is the detection mechanism itself, not a live content claim about any
    of the three files still existing, so scanning this file for its own search targets would
    be a self-referential false positive rather than a real finding."""
    for relative_path in ALL_EXPECTED_FILES:
        if relative_path == "test_policy_package.py":
            continue
        text = (HERE / relative_path).read_text(encoding="utf-8")
        for stale_name in STALE_V1_ARTIFACT_NAMES:
            for m in re.finditer(re.escape(stale_name), text):
                context = _enclosing_paragraph_or_row(text, m.start(), m.end())
                if RENAME_ARROW_RE.search(context):
                    continue  # documented rename provenance -- historical by construction
                context_lower = re.sub(r"\s+", " ", context).lower()
                assert any(marker in context_lower for marker in HISTORICAL_CONTEXT_MARKERS), (
                    f"{relative_path}: {stale_name!r} is mentioned outside any historical/"
                    f"changelog/Supersedes/rename-arrow context -- this reads as a LIVE "
                    f"reference to a file that was deleted as of NT16 (v2.0). "
                    f"Context: ...{context.strip()}..."
                )


def test_stale_v1_artifact_files_do_not_exist_on_disk():
    """Codex review C6, disk-level companion to the text guard above: the three superseded
    v1 JSON artifacts must actually be gone, not merely correctly worded around in prose."""
    for stale_name in STALE_V1_ARTIFACT_NAMES:
        assert not (HERE / stale_name).exists(), (
            f"{stale_name} must not exist on disk -- superseded and deleted as of NT16 (v2.0)"
        )


def _find_key_anywhere(obj, key: str):
    """Recursively search a decoded JSON structure for the first value bound to `key` at any
    nesting depth. Used so the display_rounding_mode guard below does not have to assume
    exactly where the concurrent sibling D2 work package nests the field (top-level vs.
    inside `constants` vs. elsewhere)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = _find_key_anywhere(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_key_anywhere(item, key)
            if found is not None:
                return found
    return None


def test_grading_policy_json_declares_labeled_display_rounding_mode():
    """Codex review C5, implementation half -- AMENDED by RC 2026-07-24 (later same date;
    NT16-B). RC's original OPEN-09 ruling fixed display PRECISION (one decimal) but did not
    specify the rounding MODE; this package first labeled its Python-builtin-round half-even
    behavior as an implementation choice pending RC confirmation. RC has SINCE directly ruled
    on the mode: "Use conventional decimal ROUND_HALF_UP for the student-facing one-decimal
    display. Example: 89.25 -> 89.3. Do not use Python binary-float round() or half-even
    behavior for the display contract." grading_policy.v2.json must now declare a
    display_rounding_mode value that both (a) names the mode actually implemented (half-up /
    decimal ROUND_HALF_UP) and (b) carries the amendment's RC 2026-07-24 provenance --
    never silently presented as an unconfirmed implementation guess. This makes the labeling
    tamper-evident in both directions: the field must exist AND keep its provenance --
    stripping the provenance and presenting the mode as an untraceable default fails this
    guard just as surely as the field being absent or still naming half-even as current."""
    policy = json.loads((HERE / "grading_policy.v2.json").read_text(encoding="utf-8"))
    mode = _find_key_anywhere(policy, "display_rounding_mode")
    assert mode, (
        "grading_policy.v2.json must declare a display_rounding_mode value (landed by a "
        "concurrent sibling D2 work package -- see this implementer's final report if this "
        "is still failing)"
    )
    mode_lower = str(mode).lower()
    assert "half-up" in mode_lower, (
        f"display_rounding_mode must name half-up rounding explicitly (RC's 2026-07-24 "
        f"amendment), found: {mode!r}"
    )
    assert "amended by rc 2026-07-24" in mode_lower, (
        f"display_rounding_mode must carry RC's 2026-07-24 amendment provenance for the "
        f"rounding mode, found: {mode!r}"
    )


def test_open_09_register_entry_carries_residual_rounding_mode_note_while_staying_resolved():
    """Codex review C5, register half -- AMENDED by RC 2026-07-24 (later same date; NT16-B).
    RC's original OPEN-09 ruling settled display PRECISION but not the rounding MODE, and
    OPEN_DECISIONS_REGISTER.md's OPEN-09 section first recorded that residual as a clearly
    labeled implementation reading (half-even) flagged for RC confirmation. RC has SINCE
    directly amended the mode to half-up. This guard checks the section now requires: it
    remains RESOLVED (RESOLVED_PROVENANCE_TOKEN); it still names the residual "rounding
    mode" question; it still legitimately MENTIONS half-even (the historical reading is not
    erased, only superseded -- this guard does not forbid the word); it now ALSO names
    half-up as the amended mode, with the amendment's own RC 2026-07-24 provenance; and no
    new OPEN-NN id was minted for either the original residual or this amendment."""
    register_text = (HERE / "OPEN_DECISIONS_REGISTER.md").read_text(encoding="utf-8")
    section = _extract_register_section(register_text, "OPEN-09")
    section_lower = re.sub(r"\s+", " ", section).lower()

    assert RESOLVED_PROVENANCE_TOKEN in section, (
        "OPEN-09 must remain RESOLVED even after the residual rounding-mode note and its "
        "later amendment are added"
    )
    assert "rounding mode" in section_lower, (
        "OPEN-09 register section must name the residual rounding-MODE question explicitly"
    )
    assert "half-even" in section_lower, (
        "OPEN-09 register section must still name half-even as the historical reading the "
        "implementation originally chose -- history is not erased, only superseded"
    )
    assert "half-up" in section_lower, (
        "OPEN-09 register section must name half-up as RC's amended, confirmed rounding mode"
    )
    assert "amended by rc 2026-07-24" in section_lower, (
        "OPEN-09 register section must carry RC's 2026-07-24 amendment provenance for the "
        "rounding-mode question, not merely the original 'pending RC confirmation' label"
    )
    assert "display_rounding_mode" in section, (
        "OPEN-09 register section must point at grading_policy.v2.json's "
        "display_rounding_mode field"
    )
    assert not re.search(r"\bOPEN-20\b", register_text), (
        "no OPEN-20 id may be minted for the residual rounding-mode question or its amendment"
    )


# =========================================================================================
# 14B. NT16-B STALE-PHRASE GUARD -- OPEN-09's rounding-MODE reading and OPEN-11's
#     excused-vs-unknown reading were both directly resolved by RC (2026-07-24, later same
#     date): OPEN-09's mode is AMENDED to half-up; OPEN-11's reading is CONFIRMED. Neither
#     residual question is "pending RC confirmation" anymore. This guard fails if that
#     phrase reappears describing either question as though it were still unconfirmed,
#     anywhere outside a clearly historical or amendment-provenance context -- reusing this
#     suite's own _enclosing_paragraph_or_row scoping and HISTORICAL_CONTEXT_MARKERS
#     exemption (section 14 above) rather than inventing a second mechanism.
# =========================================================================================

PENDING_RC_CONFIRMATION_RE = re.compile(r"pending rc confirmation", re.IGNORECASE)

# Markers, in addition to HISTORICAL_CONTEXT_MARKERS, that specifically indicate a
# "pending RC confirmation" mention is historical because RC has since ruled on it.
AMENDMENT_CONTEXT_MARKERS = ("amended", "amendment", "confirmed by rc")


def _stale_pending_rc_confirmation_offenses(relative_path: str) -> list[str]:
    """Returns one offense description per live (non-historical) 'pending RC confirmation'
    mention found in relative_path -- empty if clean. Mirrors
    _rounding_forgiveness_offenses's structure (section 15 below) so this exact check can
    be re-run standalone during mutation-validation."""
    text = (HERE / relative_path).read_text(encoding="utf-8")
    offenses: list[str] = []
    for m in PENDING_RC_CONFIRMATION_RE.finditer(text):
        context = _enclosing_paragraph_or_row(text, m.start(), m.end())
        normalized = re.sub(r"\s+", " ", context).lower()
        if any(marker in normalized for marker in HISTORICAL_CONTEXT_MARKERS):
            continue
        if any(marker in normalized for marker in AMENDMENT_CONTEXT_MARKERS):
            continue
        offenses.append(
            f"{relative_path}: 'pending RC confirmation' appears outside historical/"
            f"amendment context: ...{normalized.strip()[:300]}..."
        )
    return offenses


def test_no_stale_pending_rc_confirmation_language_outside_historical_or_amendment_context():
    """NT16-B. RC directly resolved both residual readings this package had flagged as
    'pending RC confirmation': OPEN-09's display rounding MODE (AMENDED to half-up) and
    OPEN-11's excused-vs-unknown reading (CONFIRMED as already implemented). The phrase may
    still legitimately appear -- describing what this package used to say before RC ruled --
    but never as a live, current claim that either question remains unconfirmed. Excludes
    this suite's own file: PENDING_RC_CONFIRMATION_RE's literal search string is itself a
    match for its own pattern, which would be a self-referential false positive rather than
    a real finding (the same exclusion test_no_live_stale_v1_reference_outside_historical_
    context, section 14 above, applies to itself for the analogous reason)."""
    all_offenses: list[str] = []
    for relative_path in ALL_EXPECTED_FILES:
        if relative_path == "test_policy_package.py":
            continue
        all_offenses.extend(_stale_pending_rc_confirmation_offenses(relative_path))
    assert not all_offenses, (
        "stale 'pending RC confirmation' language found outside historical/amendment "
        "context (OPEN-09's rounding mode and OPEN-11's excused/unknown reading were both "
        "resolved by RC 2026-07-24, NT16-B):\n" + "\n".join(all_offenses)
    )


# =========================================================================================
# 15. V2 GUARD (Codex re-check residual, HIGH) -- the "rounding forgives a difference" rule
#     the C2 remediation deleted from parity_check.py's CODE must never reappear as
#     normative PROSE (or code) anywhere in the package. A sibling agent found it still
#     living as live normative text in GRADING_POLICY_SPEC.md's old §3.2 bullet; nothing
#     previously stopped it reappearing there, or in any other deliverable/artifact/module,
#     in the future. This guard detects the SEMANTIC formulation -- a difference that
#     disappears/vanishes once both sides are rounded is therefore declared "not a
#     substantive divergence" / "must not be reported as one" -- rather than one exact
#     sentence, so a rephrasing of the same defective claim is caught too.
#
#     Reuses this suite's own _enclosing_paragraph_or_row scoping and
#     HISTORICAL_CONTEXT_MARKERS exemption (section 5B above) rather than inventing a
#     second mechanism -- the same approach
#     test_no_resolved_open_id_appears_next_to_stale_unresolved_language_outside_
#     historical_context and test_no_live_stale_v1_reference_outside_historical_context
#     (section 14 above) already use for their own analogous stale-phrase checks.
# =========================================================================================

# Clause 1: a difference/divergence "disappearing"/"vanishing" (or an equivalent synonym)
# once/when/after both sides are rounded. Deliberately does NOT match RC's own correctly-
# worded ruling ("must not mistake display rounding for substantive divergence") or the
# CORRECTED semantics ("no amount of rounding ... can turn a genuine underlying difference
# into a non-divergence") -- neither uses "disappear/vanish/goes away/erased/eliminated ...
# rounded" phrasing, so this clause alone already excludes both of those.
ROUNDING_FORGIVENESS_ERASURE_RE = re.compile(
    r"(?:disappear\w*|vanish\w*|goes?\s+away|is\s+erased|is\s+eliminated)\s+"
    r"(?:once|when|after)\s+both\s+(?:sides|values|figures|numbers)\s+(?:are\s+)?rounded",
    re.IGNORECASE,
)

# Clause 2: the forgiveness CONCLUSION -- declaring the (erased) difference non-substantive
# and/or instructing that it must not be reported/flagged as divergent. Deliberately does
# NOT match the corrected semantics' vocabulary ("underlying convergence NOT established",
# "comparison_basis is DEGRADED", "a stated limitation") -- the corrected text always talks
# about convergence never being ESTABLISHED, never about a divergence being forgiven/
# unreported, so it cannot satisfy this clause.
ROUNDING_FORGIVENESS_CONCLUSION_RE = re.compile(
    r"not\s+a\s+substantive\s+divergen\w*"
    r"|must\s+not\s+be\s+reported\s+as\s+(?:one\b|a\s+divergen\w*|divergent)"
    r"|(?:should|must)\s+not\s+be\s+(?:flagged|reported|treated)\s+as\s+(?:divergent|a\s+divergen\w*)",
    re.IGNORECASE,
)

# Scope: exactly the file universe the finding named -- the .md deliverables, the .json
# policy artifacts, and the two Python reference modules (parity_check.py /
# grading_policy_ref.py). Deliberately reuses the manifest lists already defined above
# rather than a fresh list, so this guard's scope never silently drifts from the file
# manifest test's own idea of "every deliverable/artifact/module this package has."
ROUNDING_FORGIVENESS_SCAN_FILES = DELIVERABLE_MD_FILES + JSON_ARTIFACT_FILES + PYTHON_REFERENCE_FILES


def _rounding_forgiveness_offenses(relative_path: str) -> list[str]:
    """Returns one human-readable offense description per live (non-historical) mention of
    the rounding-forgiveness formulation found in `relative_path` -- empty if clean. A
    "hit" requires BOTH clauses (erasure AND forgiveness-conclusion) to appear within the
    SAME enclosing paragraph/table row, so a document can freely discuss rounding, or freely
    discuss divergence, without tripping this guard -- only the specific combined claim
    does. Factored out of the test function itself so this exact check can be re-run
    standalone during mutation-validation (see this implementer's final report)."""
    text = (HERE / relative_path).read_text(encoding="utf-8")
    offenses: list[str] = []
    for m in ROUNDING_FORGIVENESS_ERASURE_RE.finditer(text):
        context = _enclosing_paragraph_or_row(text, m.start(), m.end())
        normalized = re.sub(r"\s+", " ", context)
        if not ROUNDING_FORGIVENESS_CONCLUSION_RE.search(normalized):
            continue  # rounding-erasure language present, but no forgiveness conclusion nearby
        if any(marker in normalized.lower() for marker in HISTORICAL_CONTEXT_MARKERS):
            continue  # explicitly historical/changelog/superseded framing -- not a live claim
        offenses.append(
            f"{relative_path}: rounding-forgiveness formulation detected outside historical "
            f"context: ...{normalized.strip()[:400]}..."
        )
    return offenses


def test_rounding_forgiveness_rule_never_reappears_in_any_authoritative_document_or_module():
    """V2 guard (Codex re-check, HIGH). The C2 remediation deleted the "rounding forgives a
    difference" rule from parity_check.py's CODE (`_rounding_only_difference` and its
    forgiveness branch -- see test_parity_check.py's
    test_rounding_only_difference_helper_is_deleted / test_no_forgiveness_report_field_
    survives) -- but nothing previously stopped the identical rule reappearing as normative
    PROSE in any deliverable, which is exactly what a sibling agent found still live in
    GRADING_POLICY_SPEC.md's old §3.2 bullet. This guard fails if the semantic formulation
    -- a difference that disappears/vanishes once both sides are rounded is therefore "not
    a substantive divergence" / "must not be reported as one" -- appears anywhere in the
    .md deliverables, the .json policy artifacts, or the two Python reference modules,
    UNLESS that specific mention's own enclosing paragraph/row is explicitly historical/
    changelog/superseded framing (HISTORICAL_CONTEXT_MARKERS) -- e.g. a changelog entry that
    quotes the deleted rule verbatim while describing it as fixed/deleted/superseded.

    Deliberately does NOT trip on the CORRECTED semantics this same fix establishes:
    "underlying convergence is NEVER established from a display-rounded-only observation,
    only stated as a limitation" talks about convergence never being ESTABLISHED, not about
    a divergence being forgiven/unreported -- ROUNDING_FORGIVENESS_CONCLUSION_RE requires
    the divergence-forgiving conclusion, which the corrected wording never states."""
    all_offenses: list[str] = []
    for relative_path in ROUNDING_FORGIVENESS_SCAN_FILES:
        all_offenses.extend(_rounding_forgiveness_offenses(relative_path))
    assert not all_offenses, (
        "the deleted rounding-forgiveness rule has reappeared as normative prose/code -- "
        "see C2/V2 (product-policy NT16 residual, HIGH):\n" + "\n".join(all_offenses)
    )


def test_parity_check_exposes_no_rounding_only_difference_attribute_or_report_key():
    """V2 guard, belt-and-braces code half. Independent, package-level duplication of
    test_parity_check.py's own test_rounding_only_difference_helper_is_deleted /
    test_no_forgiveness_report_field_survives -- so a future edit that removes or weakens
    those two D3-suite tests is still caught here: `parity_check` must expose no
    `_rounding_only_difference` attribute at all, and no `check_student_parity` report
    (on either comparison basis) may carry a `rounding_only_difference` key."""
    assert not hasattr(parity_check, "_rounding_only_difference")

    fixtures_dir = HERE / "fixtures" / "schoology"
    catalog = json.loads((fixtures_dir / "course_section_synthetic.json").read_text(encoding="utf-8"))
    for fixture_name in (
        "student_0001_above_gate_convergent.json",
        "student_0006_display_rounding_only_difference.json",
    ):
        fixture = json.loads((fixtures_dir / fixture_name).read_text(encoding="utf-8"))
        for declared_rounded in (False, True):
            report = parity_check.check_student_parity(
                fixture, course_catalog=catalog, schoology_value_is_display_rounded=declared_rounded
            )
            assert "rounding_only_difference" not in report


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
