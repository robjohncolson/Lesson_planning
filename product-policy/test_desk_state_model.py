"""Consistency tests for the Desk lesson-state model (NT15 deliverable D4).

Hermetic: loads desk_state_model.v2.json from this same directory via
pathlib.Path(__file__).parent. No network, no dependency on any file outside
product-policy/. Standard library + pytest only.

v2.0 (NT16 work package B): RC's 2026-07-24 rulings resolved OPEN-17 (retakes)
and OPEN-18 (skip transitions). This suite enforces the DECIDED semantics
those rulings settled, replacing the provisional-semantics tests that guarded
v1.0's placeholder choices.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

HERE = Path(__file__).parent
MODEL_PATH = HERE / "desk_state_model.v2.json"

CANONICAL_STATES = [
    "today",
    "released",
    "unreleased",
    "skipped",
    "optional-catalog",
    "completed",
    "temporarily-unavailable",
]

CANONICAL_VIEWS = ["primary_view", "roadmap_view"]

PROVENANCE = "RESOLVED by RC 2026-07-24"

SKIP_TRANSITION_IDS = {"T3", "T7", "T11", "T12", "T13"}
PROMOTED_OPEN_18_IDS = {"T7", "T11", "T12", "T13"}


@pytest.fixture(scope="module")
def model() -> dict:
    with MODEL_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def all_transitions(model: dict) -> list[dict]:
    """legal + illegal + provisional. provisional is empty in v2.0 but is
    still included for the well-formedness/coverage checks below, in case a
    future version ever repopulates it."""
    return (
        model["transitions"]["legal"]
        + model["transitions"]["illegal"]
        + model["transitions"].get("provisional", [])
    )


def _transition_by_id(model: dict, tid: str) -> dict:
    for t in model["transitions"]["legal"]:
        if t["id"] == tid:
            return t
    raise AssertionError(f"transition {tid!r} not found in transitions.legal")


# ----------------------------------------------------------------------
# Top-level shape / provenance
# ----------------------------------------------------------------------

def test_provenance_header(model: dict):
    assert model["version"] == "2.0"
    assert model["date"] == "2026-07-24"
    assert model["source_of_authority"] == (
        "RC final decisions 2026-07-24 (Grok preference interview + RC clarifications; "
        "NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)"
    )


def test_seven_canonical_states_exact(model: dict):
    """The state list must be exactly these seven, spelled exactly this way,
    matching brief §6 and RC_TEACHER_PREFERENCE_RECORD.md's PREF-01.1 --
    this is the machine-checked cross-document consistency point."""
    assert model["state_set"] == CANONICAL_STATES
    assert len(model["state_set"]) == 7
    assert len(set(model["state_set"])) == 7  # no duplicates


def test_views_are_exactly_primary_and_roadmap(model: dict):
    assert model["views"] == CANONICAL_VIEWS


def test_states_dict_defines_every_canonical_state(model: dict):
    assert set(model["states"].keys()) == set(CANONICAL_STATES)


# ----------------------------------------------------------------------
# Requirement: every state has a defined visibility in BOTH views
# ----------------------------------------------------------------------

def test_every_state_has_visibility_defined_in_both_views(model: dict):
    visibility = model["visibility"]
    assert set(visibility.keys()) == set(CANONICAL_STATES), (
        "every one of the seven states must appear in the visibility matrix"
    )
    for state in CANONICAL_STATES:
        entry = visibility[state]
        for view in CANONICAL_VIEWS:
            assert view in entry, f"{state} has no {view} entry"
            view_entry = entry[view]
            assert "visible" in view_entry and isinstance(view_entry["visible"], bool), (
                f"{state}/{view} missing a boolean 'visible' flag"
            )
            assert "openable" in view_entry and isinstance(view_entry["openable"], bool), (
                f"{state}/{view} missing a boolean 'openable' flag"
            )


# ----------------------------------------------------------------------
# Requirement: unreleased is invisible in both views
# ----------------------------------------------------------------------

def test_unreleased_invisible_in_both_views(model: dict):
    vis = model["visibility"]["unreleased"]
    for view in CANONICAL_VIEWS:
        assert vis[view]["visible"] is False, f"unreleased must not appear in {view}"
        assert vis[view]["openable"] is False, f"unreleased must not be openable in {view}"


def test_no_transition_makes_unreleased_visible_by_side_channel(all_transitions):
    """Nothing should transition INTO unreleased from an already-exposed state
    via a legal, ordinary trigger -- unreleased is the initial default, not a
    state reached by legal transition in this model."""
    legal_into_unreleased = [t for t in all_transitions if t.get("to") == "unreleased"]
    # every transition that *targets* unreleased must be one we've explicitly
    # enumerated as illegal (defends against silently adding a legal one later).
    for t in legal_into_unreleased:
        assert t in _illegal_list(), (
            f"transition {t['id']} legally re-enters 'unreleased' -- this contradicts "
            "unreleased being hidden/unavailable and the initial default state only"
        )


def _illegal_list():
    with MODEL_PATH.open(encoding="utf-8") as f:
        return json.load(f)["transitions"]["illegal"]


# ----------------------------------------------------------------------
# Requirement: skipped appears only in roadmap view, and is inert there
# ----------------------------------------------------------------------

def test_skipped_only_in_roadmap_view_and_inert_there(model: dict):
    vis = model["visibility"]["skipped"]
    assert vis["primary_view"]["visible"] is False, "skipped must not appear in the primary view"
    assert vis["roadmap_view"]["visible"] is True, "skipped must appear in the roadmap view"
    assert vis["roadmap_view"]["openable"] is False, "skipped must be inert (not openable) in the roadmap"
    assert vis["roadmap_view"].get("grey_inert") is True, "skipped must be flagged grey/inert"


# ----------------------------------------------------------------------
# Requirement: optional-catalog is not exposed in the normal path, and
# exposure requires explicit assignment
# ----------------------------------------------------------------------

def test_optional_catalog_not_exposed_in_normal_path(model: dict):
    vis = model["visibility"]["optional-catalog"]
    for view in CANONICAL_VIEWS:
        assert vis[view]["visible"] is False, f"optional-catalog must not be exposed in {view}"
        assert vis[view]["openable"] is False, f"optional-catalog must not be openable in {view}"


def test_optional_catalog_exposure_requires_explicit_assignment(model: dict):
    legal = model["transitions"]["legal"]
    illegal = model["transitions"]["illegal"]

    outbound_legal = [t for t in legal if t["from"] == "optional-catalog"]
    assert outbound_legal, "there must be at least one legal way out of optional-catalog"
    for t in outbound_legal:
        assert t["to"] in ("released", "today")
        assert t["trigger"] == "explicit_teacher_assignment", (
            "the only legal exit trigger from optional-catalog must be explicit "
            "teacher assignment -- never an ordinary release/designation trigger"
        )

    # the ordinary triggers must be explicitly forbidden for this origin state
    forbidding_entries = [
        t for t in illegal
        if t["from"] == "optional-catalog" and t.get("trigger_forbidden")
    ]
    assert forbidding_entries, (
        "must explicitly record that ordinary teacher_release/teacher_designate_today "
        "triggers are forbidden from optional-catalog (no auto-scheduling)"
    )
    forbidden = set()
    for t in forbidding_entries:
        forbidden.update(t["trigger_forbidden"])
    assert "teacher_release" in forbidden
    assert "teacher_designate_today" in forbidden
    assert "explicit_teacher_assignment" not in forbidden

    # cross-check against optional_catalog_rule block
    rule = model["optional_catalog_rule"]
    assert rule["required_transition_trigger_out_of_state"] == "explicit_teacher_assignment"
    assert "teacher_release" in rule["forbidden_transition_triggers_out_of_state"]
    assert "teacher_designate_today" in rule["forbidden_transition_triggers_out_of_state"]
    assert rule["desk_level_consequence"]["never_auto_scheduled"] is True
    assert rule["desk_level_consequence"]["never_enters_pacing"] is True
    assert rule["desk_level_consequence"]["never_counts_toward_completion"] is True
    assert rule["desk_level_consequence"]["never_surfaces_in_normal_path_absent_explicit_assignment"] is True


# ----------------------------------------------------------------------
# Requirement: temporarily-unavailable never demotes/erases completed, and
# never renders as zero
# ----------------------------------------------------------------------

def test_completed_to_temporarily_unavailable_is_illegal(model: dict):
    legal_pairs = {(t["from"], t["to"]) for t in model["transitions"]["legal"]}
    illegal_pairs = {(t["from"], t["to"]) for t in model["transitions"]["illegal"]}
    assert ("completed", "temporarily-unavailable") not in legal_pairs
    assert ("completed", "temporarily-unavailable") in illegal_pairs


def test_completed_has_no_legal_demotion_at_all(model: dict):
    """No legal transition may leave 'completed' for any of the other six
    states -- completed is sticky/terminal in this model. As of v2.0 (RC's
    2026-07-24 ruling, OPEN-17) this is DECIDED policy, not a conservative
    placeholder: zero legal exits from completed, full stop."""
    outbound_legal = [t for t in model["transitions"]["legal"] if t["from"] == "completed"]
    assert outbound_legal == [], "completed must have zero legal outbound transitions"


def test_completed_state_description_is_decided_not_pending(model: dict):
    """OPEN-17 is resolved: completed's description must present terminality
    as DECIDED policy, never as unresolved-pending-RC, and must not carry the
    old 'open_item' marker."""
    completed = model["states"]["completed"]
    description = completed["description"].lower()
    assert "unresolved-pending-rc" not in description
    assert "pending that decision" not in description
    assert "decided" in description
    assert completed.get("open_item") is None, (
        "completed must not carry the old 'open_item': 'OPEN-17' marker -- "
        "OPEN-17 is resolved, not open"
    )
    assert completed.get("resolved_open_item") == "OPEN-17"
    assert completed.get("provenance") == PROVENANCE
    assert completed["sticky"] is True


def test_open_17_and_open_18_resolved_not_open(model: dict):
    """OPEN-17 and OPEN-18 are resolved as of v2.0: open_item_ids must be
    empty, and both ids must appear in resolved_open_item_ids instead --
    the identifiers are preserved, never silently dropped."""
    assert model["open_item_ids"] == []
    assert "OPEN-17" in model["resolved_open_item_ids"]
    assert "OPEN-18" in model["resolved_open_item_ids"]

    # bare tokens must still be greppable somewhere in the JSON text -- the
    # identifiers must never silently disappear even though they are resolved.
    raw = json.dumps(model)
    assert "OPEN-17" in raw
    assert "OPEN-18" in raw

    # the invariant OPEN-17 documents (zero legal exits from completed) must
    # still hold now that it is resolved -- resolving the question must never
    # itself become a loophole that adds an exit.
    outbound_legal = [t for t in model["transitions"]["legal"] if t["from"] == "completed"]
    assert outbound_legal == [], (
        "completed must still have zero legal outbound transitions after "
        "resolving OPEN-17"
    )

    # the seven-state set, visibility matrix, and reliability invariants must
    # be byte-for-byte the same shape as before this amendment.
    assert model["state_set"] == CANONICAL_STATES
    assert set(model["visibility"].keys()) == set(CANONICAL_STATES)
    assert {r["id"] for r in model["reliability_invariants"]} == {"RI-1", "RI-2", "RI-3"}


def test_resolved_open_items_replaces_provisional_implementation_choices(model: dict):
    assert "provisional_implementation_choices" not in model, (
        "v1.0's provisional_implementation_choices must be replaced by "
        "resolved_open_items in v2.0"
    )
    resolved = model["resolved_open_items"]
    for open_id in ("OPEN-17", "OPEN-18"):
        entry = resolved[open_id]
        assert entry["status"] == "RESOLVED"
        assert entry["provenance"] == PROVENANCE
        assert entry["ruling"]
        assert entry["supersedes"]


def test_open_items_affecting_this_policy_retitled(model: dict):
    """v1.0's open_items_affecting_this_policy presented OPEN-17/18 as
    affecting-and-unresolved; v2.0 must not present them that way any longer."""
    assert "open_items_affecting_this_policy" not in model
    resolved_map = model["resolved_items_affecting_this_policy"]
    assert "OPEN-17" in resolved_map
    assert "OPEN-18" in resolved_map
    for text in resolved_map.values():
        assert "RESOLVED" in text.upper()


# ----------------------------------------------------------------------
# retake_affordance (OPEN-17)
# ----------------------------------------------------------------------

def test_retake_affordance_is_orthogonal_and_completed_stays_terminal(model: dict):
    retake = model["retake_affordance"]
    assert retake["demotes_completion"] is False
    assert retake["relocks"] is False
    assert retake["erases_history"] is False
    assert retake["alters_grading_engine_via_navigation_state"] is False
    assert retake["completed_is_terminal"] is True
    assert retake["implementation_deferred_to"]
    assert retake["provenance"] == PROVENANCE
    assert retake.get("resolved_open_item") == "OPEN-17"


# ----------------------------------------------------------------------
# OPEN-18 (skip transitions): T7/T11/T12/T13 promoted to legal; T3
# confirmed; teacher-only actor + no student initiation on all five.
# ----------------------------------------------------------------------

def test_provisional_bucket_is_empty_and_retirement_documented(model: dict):
    assert model["transitions"]["provisional"] == [], (
        "transitions.provisional must be permanently empty in v2.0 -- all "
        "four OPEN-18 transitions were promoted to transitions.legal"
    )
    retirement = model["transitions"]["provisional_retirement"]
    assert retirement["provenance"] == PROVENANCE
    assert set(retirement["promoted_transitions"]) == PROMOTED_OPEN_18_IDS
    assert retirement["promoted_to"] == "transitions.legal"


def test_promoted_open_18_transitions_present_in_legal_without_provisional_markers(model: dict):
    """T7, T11, T12, T13 must each be present in transitions.legal, carrying
    no 'normative': false and no 'open_item' marker -- those v1.0 tags are
    gone now that OPEN-18 is resolved."""
    legal_ids = {t["id"] for t in model["transitions"]["legal"]}
    assert PROMOTED_OPEN_18_IDS <= legal_ids, (
        f"missing promoted transitions in transitions.legal: "
        f"{PROMOTED_OPEN_18_IDS - legal_ids}"
    )
    for tid in PROMOTED_OPEN_18_IDS:
        t = _transition_by_id(model, tid)
        assert t.get("normative") is not False, f"{tid} must not carry 'normative': false"
        assert "open_item" not in t, f"{tid} must not carry an 'open_item' marker"
        assert t.get("provenance") == PROVENANCE

    # and the specific (from, to) pairs are the expected ones
    by_id = {t["id"]: t for t in model["transitions"]["legal"] if t["id"] in PROMOTED_OPEN_18_IDS}
    assert (by_id["T7"]["from"], by_id["T7"]["to"]) == ("released", "skipped")
    assert (by_id["T11"]["from"], by_id["T11"]["to"]) == ("today", "skipped")
    assert (by_id["T12"]["from"], by_id["T12"]["to"]) == ("skipped", "released")
    assert (by_id["T13"]["from"], by_id["T13"]["to"]) == ("skipped", "today")


def test_t3_confirmed_not_duplicated(model: dict):
    """T3 (unreleased -> skipped) was already legal in v1.0. RC's ruling
    CONFIRMS it -- no duplicate transition id may be minted for the same
    (from, to, trigger)."""
    legal = model["transitions"]["legal"]
    t3_matches = [t for t in legal if t["id"] == "T3"]
    assert len(t3_matches) == 1
    t3 = t3_matches[0]
    assert t3["from"] == "unreleased"
    assert t3["to"] == "skipped"

    # no duplicate id covering the same (from, to) pair as T3
    same_pair_ids = {
        t["id"] for t in legal
        if t["from"] == "unreleased" and t["to"] == "skipped"
    }
    assert same_pair_ids == {"T3"}, (
        f"expected only T3 for unreleased->skipped, found {same_pair_ids}"
    )


def test_t11_carries_machine_readable_precondition(model: dict):
    """today -> skipped (T11) is allowed only BEFORE the lesson reaches
    completed for that student. This must be encoded machine-readably, not
    just as prose."""
    t11 = _transition_by_id(model, "T11")
    assert "precondition" in t11, "T11 must carry a machine-readable precondition"
    precondition = t11["precondition"]
    assert isinstance(precondition, dict)
    # some machine-checkable field must reference the completed boundary
    joined = json.dumps(precondition).lower()
    assert "completed" in joined
    assert precondition.get("note"), "precondition must also carry a plain-language note"


def test_skip_transitions_carry_teacher_only_actor_and_no_student_initiation(model: dict):
    """T3, T7, T11, T12, T13 each carry actor: teacher_only and
    student_may_initiate: false -- RC's ruling is explicit that students
    cannot initiate skip or unskip."""
    for tid in SKIP_TRANSITION_IDS:
        t = _transition_by_id(model, tid)
        assert t.get("actor") == "teacher_only", f"{tid} must have actor 'teacher_only'"
        assert t.get("student_may_initiate") is False, (
            f"{tid} must have student_may_initiate: false"
        )


def test_every_legal_transition_carries_an_actor_field(model: dict):
    for t in model["transitions"]["legal"]:
        assert "actor" in t, f"legal transition {t['id']} missing an 'actor' field"
        assert t["actor"], f"legal transition {t['id']} has an empty 'actor' field"


def test_actor_field_derived_correctly_from_trigger(model: dict):
    """Non-skip teacher-triggered transitions get actor 'teacher'; evidence/
    system-triggered transitions get actor 'system_evidence'; the five skip
    transitions get the stricter 'teacher_only' (checked separately above)."""
    teacher_triggers = {
        "teacher_release",
        "teacher_designate_today",
        "teacher_redesignate_today",
        "explicit_teacher_assignment",
    }
    system_triggers = {
        "evidence_verified_complete",
        "evidence_source_unreachable",
        "evidence_source_recovered_incomplete",
        "evidence_source_recovered_complete",
    }
    for t in model["transitions"]["legal"]:
        if t["id"] in SKIP_TRANSITION_IDS:
            continue
        if t["trigger"] in teacher_triggers:
            assert t["actor"] == "teacher", f"{t['id']} ({t['trigger']}) should be actor 'teacher'"
        elif t["trigger"] in system_triggers:
            assert t["actor"] == "system_evidence", (
                f"{t['id']} ({t['trigger']}) should be actor 'system_evidence'"
            )


def test_skip_authority_object_present_and_consistent(model: dict):
    skip_authority = model["skip_authority"]
    assert skip_authority["actor"] == "teacher_only"
    assert skip_authority["student_may_initiate"] is False
    assert set(skip_authority["applies_to_transitions"]) == SKIP_TRANSITION_IDS
    assert skip_authority["forbidden_target_from_completed"] is True
    assert skip_authority["provenance"] == PROVENANCE


def test_no_student_actor_may_initiate_any_skip_transition(model: dict):
    """Cross-check across three independent sources of truth: the per-
    transition student_may_initiate flags, the skip_authority object, and
    the fact that none of the five skip transitions ever carries a 'student'
    or 'system_evidence' actor."""
    for tid in SKIP_TRANSITION_IDS:
        t = _transition_by_id(model, tid)
        assert t["student_may_initiate"] is False
        assert t["actor"] != "student"
        assert t["actor"] != "system_evidence"
    assert model["skip_authority"]["student_may_initiate"] is False


# ----------------------------------------------------------------------
# completed -> skipped stays illegal (X3), and is the guard for T11
# ----------------------------------------------------------------------

def test_completed_to_skipped_illegal_not_legal(model: dict):
    legal_pairs = {(t["from"], t["to"]) for t in model["transitions"]["legal"]}
    illegal_pairs = {(t["from"], t["to"]) for t in model["transitions"]["illegal"]}
    assert ("completed", "skipped") not in legal_pairs
    assert ("completed", "skipped") in illegal_pairs

    x3 = next(x for x in model["transitions"]["illegal"] if x["id"] == "X3")
    assert x3["from"] == "completed"
    assert x3["to"] == "skipped"
    assert x3.get("provenance") == PROVENANCE
    assert "OPEN-18" in x3["reason"] or "OPEN-18" in " ".join(x3["cites"])


# ----------------------------------------------------------------------
# transitions.unresolved is empty; U1/U2/U3 preserved in resolved
# ----------------------------------------------------------------------

def test_unresolved_bucket_empty_and_u1_u2_u3_preserved_in_resolved(model: dict):
    assert model["transitions"]["unresolved"] == [], (
        "transitions.unresolved must be permanently empty in v2.0"
    )
    resolved = {u["id"]: u for u in model["transitions"]["resolved"]}
    assert set(resolved.keys()) == {"U1", "U2", "U3"}, (
        "U1/U2/U3 must be preserved -- no silent identifier disappearance"
    )

    u1 = resolved["U1"]
    assert u1["from"] == "completed"
    assert "within-quarter retake" in u1["topic"]
    assert u1["status"] == PROVENANCE
    assert u1.get("provenance") == PROVENANCE

    u2 = resolved["U2"]
    assert u2["from"] == "released"
    assert u2["to"] == "skipped"
    assert u2["status"] == PROVENANCE

    u3 = resolved["U3"]
    assert u3["from"] == "skipped"
    assert u3["to"] == "released"
    assert u3["status"] == PROVENANCE


# ----------------------------------------------------------------------
# Reliability invariants (unaffected by NT16, still enforced)
# ----------------------------------------------------------------------

def test_reliability_invariant_declares_completed_sticky(model: dict):
    invariants = model["reliability_invariants"]
    ri2 = next(
        (r for r in invariants if r.get("forbidden_transition")
         == {"from": "completed", "to": "temporarily-unavailable"}),
        None,
    )
    assert ri2 is not None, "must have a reliability invariant forbidding completed -> temporarily-unavailable"
    assert any("PROGRAM_DOSSIER.md" in c for c in ri2["cites"])


def test_temporarily_unavailable_never_renders_as_zero(model: dict):
    text_blobs = [
        model["states"]["temporarily-unavailable"]["description"],
        " ".join(r["statement"] for r in model["reliability_invariants"]),
    ]
    combined = " ".join(text_blobs).lower()
    assert "never zero" in combined or "unknown" in combined, (
        "temporarily-unavailable must be documented as rendering UNKNOWN, never zero"
    )
    # and explicitly, not just implicitly: the sentinel token is declared
    assert model["unknown_sentinel_token"] == "UNKNOWN"


def test_states_are_not_flattened_to_numeric_zero_somewhere(model: dict):
    """Sanity check: none of the JSON's state definitions encode a lesson
    state as a bare numeric 0 -- the model must be able to represent UNKNOWN
    distinctly from a numeric zero anywhere completion is discussed. (bool is
    deliberately excluded: False is a legitimate flag value, e.g. sticky=False,
    and is not the "renders as zero" failure mode this guards against.)"""
    for state_name, state_def in model["states"].items():
        for value in state_def.values():
            if isinstance(value, bool):
                continue
            assert value != 0, f"state {state_name} must not encode any facet as literal 0"


# ----------------------------------------------------------------------
# Requirement: work-ahead permitted only into released material, refused
# for unreleased
# ----------------------------------------------------------------------

def test_work_ahead_rule_scoped_to_released_material(model: dict):
    rule = model["work_ahead_rule"]
    assert rule["permitted"] is True
    assert set(rule["eligible_states"]) == {"released", "today"}
    assert "unreleased" in rule["refused_states"]
    assert "unreleased" not in rule["eligible_states"]
    assert "optional-catalog" in rule["refused_states"]
    assert "optional-catalog" not in rule["eligible_states"]


def test_work_ahead_eligible_and_refused_states_are_canonical_and_disjoint(model: dict):
    rule = model["work_ahead_rule"]
    eligible = set(rule["eligible_states"])
    refused = set(rule["refused_states"])
    assert eligible <= set(CANONICAL_STATES)
    assert refused <= set(CANONICAL_STATES)
    assert eligible & refused == set(), "a state cannot be both work-ahead eligible and refused"


# ----------------------------------------------------------------------
# Requirement: the transition table is total and well-formed
# ----------------------------------------------------------------------

def test_every_transition_references_only_canonical_states(all_transitions):
    valid = set(CANONICAL_STATES)
    for t in all_transitions:
        assert t["from"] in valid, f"transition {t['id']} has unknown 'from' state {t['from']!r}"
        assert t["to"] in valid, f"transition {t['id']} has unknown 'to' state {t['to']!r}"


def test_every_canonical_state_appears_as_a_transition_origin(all_transitions):
    """No state may be left with zero defined outbound transitions (legal or
    illegal) -- that would leave part of the table silently undefined."""
    froms = {t["from"] for t in all_transitions}
    assert froms == set(CANONICAL_STATES), (
        f"states missing any 'from' entry: {set(CANONICAL_STATES) - froms}"
    )


def test_every_canonical_state_appears_as_a_transition_target(all_transitions):
    tos = {t["to"] for t in all_transitions}
    assert tos == set(CANONICAL_STATES), (
        f"states missing any 'to' entry: {set(CANONICAL_STATES) - tos}"
    )


def test_transition_ids_are_unique(all_transitions):
    ids = [t["id"] for t in all_transitions]
    assert len(ids) == len(set(ids)), "transition ids must be unique across legal + illegal"


def test_no_transition_pair_appears_in_both_legal_and_illegal(model: dict):
    """Legal and illegal buckets remain pairwise disjoint, with the single
    pre-existing, trigger-scoped exception on optional-catalog -> released/
    today (X16 forbids only the ordinary triggers; T14/T15 remain legal via
    explicit_teacher_assignment specifically)."""
    legal_pairs = {(t["from"], t["to"]) for t in model["transitions"]["legal"]}
    illegal_pairs = {(t["from"], t["to"]) for t in model["transitions"]["illegal"]}
    # X16 legitimately shares a (from, to) pair with T14 -- it forbids a
    # *specific trigger* on that pair, not the pair itself, so overlap there
    # is expected and fine. Assert every OTHER overlap is exactly that case.
    overlap = legal_pairs & illegal_pairs
    for pair in overlap:
        illegal_entries = [
            t for t in model["transitions"]["illegal"]
            if (t["from"], t["to"]) == pair
        ]
        assert all("trigger_forbidden" in t for t in illegal_entries), (
            f"unexpected legal/illegal overlap on {pair} without a trigger-scoped reason"
        )

    # in particular, none of the five newly-legal skip pairs may also appear
    # as an unscoped illegal pair
    assert ("released", "skipped") not in illegal_pairs
    assert ("today", "skipped") not in illegal_pairs
    assert ("skipped", "released") not in illegal_pairs
    assert ("skipped", "today") not in illegal_pairs


def test_legal_transitions_have_triggers_and_illegal_have_reasons(all_transitions, model: dict):
    for t in model["transitions"]["legal"]:
        assert t.get("trigger"), f"legal transition {t['id']} missing a trigger"
    for t in model["transitions"]["illegal"]:
        assert t.get("reason"), f"illegal transition {t['id']} missing a reason"


def test_sticky_states_declared_consistently(model: dict):
    """completed.sticky True must line up with it having zero legal exits;
    every other state's sticky flag must be False (only completed is sticky
    in this model)."""
    for name, definition in model["states"].items():
        if name == "completed":
            assert definition["sticky"] is True
        else:
            assert definition["sticky"] is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
