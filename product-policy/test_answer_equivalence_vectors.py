"""Structural-integrity tests for the D5 Answer Equivalence Contract test-vector corpus.

Scope note: this suite does NOT implement or exercise a CAS / symbolic-equivalence engine
(OPEN-13 is unresolved -- see ANSWER_EQUIVALENCE_CONTRACT.md Sec. "Open Items"). It tests the
CONTRACT's integrity: that every vector is well-formed, that the Tier-2 "never auto-incorrect"
asymmetry holds across the whole corpus, that the Tier-4 "AI never alone decides credit"
prohibition holds across the whole corpus, that UNKNOWN vectors never resolve to zero/incorrect,
that tolerance-dependent vectors are tagged OPEN-12, and that the four tiers named in the JSON
match the four tiers described in the .md contract.

Hermetic: standard library + pytest only, no network, loads its JSON sibling via
pathlib.Path(__file__).parent.
"""

import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).parent
VECTORS_PATH = HERE / "answer_equivalence_vectors.json"
CONTRACT_PATH = HERE / "ANSWER_EQUIVALENCE_CONTRACT.md"

# Canonical vocabulary this suite enforces independent of what the JSON claims for itself --
# this guards against the JSON silently drifting from the brief's fixed vocabulary.
CANONICAL_OUTCOMES = {"auto-correct", "auto-incorrect", "route-to-review", "unknown"}
CANONICAL_TIERS = {"tier1", "tier2", "tier3", "tier4", "unavailable"}
CANONICAL_AUTHORITIES = {"engine", "teacher", "ai", "unavailable"}

# The categories the NT15 brief explicitly requires coverage for.
REQUIRED_CATEGORIES = {
    "commutativity",
    "associativity",
    "tolerance-fraction-decimal",
    "factored-vs-expanded",
    "unsupported-form",
    "genuinely-wrong",
    "unknown-unavailable",
}

OPEN_NN_RE = re.compile(r"^OPEN-\d+$")


@pytest.fixture(scope="module")
def data():
    with VECTORS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def vectors(data):
    return data["vectors"]


@pytest.fixture(scope="module")
def contract_text():
    return CONTRACT_PATH.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Provenance / header
# --------------------------------------------------------------------------

def test_top_level_provenance_keys(data):
    assert data["version"] == "2.0"
    assert data["date"] == "2026-07-24"
    assert data["source_of_authority"] == (
        "RC final decisions 2026-07-24 (Grok preference interview + RC clarifications; "
        "NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)"
    )


def test_contract_md_header(contract_text):
    assert "**Package:** NT15 product-policy · **Version:** 2.0 · **Date:** 2026-07-24" in contract_text
    assert (
        "**Source of authority:** RC final decisions, 2026-07-24 "
        "(Grok preference interview + RC clarifications; "
        "NT16 rulings 2026-07-24 resolving OPEN-08/09/10/11/15/16/17/18/19)"
    ) in contract_text
    assert "**Status:** Authoritative" in contract_text


def test_decision_ids_are_canonical_pref07_subids(data):
    # PREF-07.1 .. PREF-07.7 only -- no invented/renumbered sub-ids.
    expected = {f"PREF-07.{i}" for i in range(1, 8)}
    assert set(data["decision_ids"]) == expected
    assert set(data["sub_decisions"].keys()) == expected


# --------------------------------------------------------------------------
# Vocabulary self-consistency
# --------------------------------------------------------------------------

def test_declared_vocabularies_match_canonical(data):
    assert set(data["allowed_outcomes"]) == CANONICAL_OUTCOMES
    assert set(data["allowed_tiers"]) == CANONICAL_TIERS
    assert set(data["allowed_decision_authorities"]) == CANONICAL_AUTHORITIES


def test_open_item_ids_are_exactly_open12_and_open13(data):
    assert set(data["open_item_ids"]) == {"OPEN-12", "OPEN-13"}


# --------------------------------------------------------------------------
# The four tiers: JSON <-> markdown agreement
# --------------------------------------------------------------------------

def test_json_declares_exactly_four_tiers(data):
    assert set(data["tiers"].keys()) == {"tier1", "tier2", "tier3", "tier4"}


def test_tier_names_in_json_match_names_in_contract_md(data, contract_text):
    """The four tiers named in the JSON must match the four described in the .md."""
    for tier_key, tier_obj in data["tiers"].items():
        name = tier_obj["name"]
        assert name, f"{tier_key} has no name"
        assert name in contract_text, (
            f"Tier name {name!r} (from JSON key {tier_key}) not found verbatim in "
            "ANSWER_EQUIVALENCE_CONTRACT.md"
        )


def test_only_tier1_can_auto_award_credit_or_incorrect(data):
    for tier_key, tier_obj in data["tiers"].items():
        if tier_key == "tier1":
            assert tier_obj["can_auto_award_credit"] is True
        else:
            assert tier_obj["can_auto_award_credit"] is False


def test_tier4_never_decides_official_correctness_or_credit(data):
    tier4 = data["tiers"]["tier4"]
    assert tier4["can_auto_award_credit"] is False
    assert tier4["decides_official_correctness"] is False
    assert tier4["decides_grade_credit"] is False


# --------------------------------------------------------------------------
# Per-vector well-formedness
# --------------------------------------------------------------------------

REQUIRED_VECTOR_FIELDS = {
    "id",
    "category",
    "description",
    "tier",
    "decision_authority",
    "policy_flags",
    "expected_answer",
    "submitted_answer",
    "expected_outcome",
    "open_items",
    "notes",
}


def test_vectors_nonempty(vectors):
    assert len(vectors) > 0


def test_every_vector_is_well_formed(vectors):
    seen_ids = set()
    for v in vectors:
        missing = REQUIRED_VECTOR_FIELDS - set(v.keys())
        assert not missing, f"vector {v.get('id')} missing fields: {missing}"

        assert isinstance(v["id"], str) and v["id"], "id must be a non-empty string"
        assert v["id"] not in seen_ids, f"duplicate vector id: {v['id']}"
        seen_ids.add(v["id"])

        assert v["tier"] in CANONICAL_TIERS, f"{v['id']}: invalid tier {v['tier']!r}"
        assert v["decision_authority"] in CANONICAL_AUTHORITIES, (
            f"{v['id']}: invalid decision_authority {v['decision_authority']!r}"
        )
        assert v["expected_outcome"] in CANONICAL_OUTCOMES, (
            f"{v['id']}: invalid expected_outcome {v['expected_outcome']!r}"
        )
        assert isinstance(v["policy_flags"], list)
        assert isinstance(v["open_items"], list)
        for token in v["open_items"]:
            assert OPEN_NN_RE.match(token), f"{v['id']}: malformed OPEN token {token!r}"
            assert token in {"OPEN-12", "OPEN-13"}, (
                f"{v['id']}: open item {token!r} is not in the canonical D5 open-item set"
            )
        assert isinstance(v["expected_answer"], str) and v["expected_answer"]
        assert isinstance(v["submitted_answer"], str) and v["submitted_answer"]


def test_required_categories_are_covered(vectors):
    present = {v["category"] for v in vectors}
    missing = REQUIRED_CATEGORIES - present
    assert not missing, f"missing required vector categories: {missing}"


# --------------------------------------------------------------------------
# The load-bearing asymmetries (corpus-wide properties)
# --------------------------------------------------------------------------

def test_tier2_is_never_auto_incorrect_corpus_wide(vectors):
    """The Tier-2 asymmetry: unsupported/unrecognized forms are never auto-marked wrong."""
    tier2_vectors = [v for v in vectors if v["tier"] == "tier2"]
    assert tier2_vectors, "expected at least one Tier-2 (unsupported-form) vector"
    for v in tier2_vectors:
        assert v["expected_outcome"] != "auto-incorrect", (
            f"{v['id']}: Tier-2 vector must never be auto-incorrect "
            "(absence of a supported equivalence proof is not evidence of incorrectness)"
        )
        assert v["expected_outcome"] == "route-to-review", (
            f"{v['id']}: Tier-2 vector must route to review"
        )


def test_no_vector_grants_credit_on_ai_only_path_corpus_wide(vectors):
    """The Tier-4 prohibition: AI alone never decides official correctness or grade credit."""
    for v in vectors:
        if v["decision_authority"] == "ai":
            assert v["expected_outcome"] not in {"auto-correct", "auto-incorrect"}, (
                f"{v['id']}: an AI-only decision_authority must never resolve to a "
                "credit-granting or credit-denying outcome"
            )
        if v["tier"] == "tier4":
            assert v["expected_outcome"] not in {"auto-correct", "auto-incorrect"}, (
                f"{v['id']}: Tier 4 must never resolve to an auto-* (credit-deciding) outcome"
            )


def test_unknown_vectors_never_zero_or_incorrect(vectors):
    unknown_vectors = [v for v in vectors if v["expected_outcome"] == "unknown"]
    assert unknown_vectors, "expected at least one UNKNOWN/evaluator-unavailable vector"
    for v in unknown_vectors:
        assert v["decision_authority"] == "unavailable", (
            f"{v['id']}: UNKNOWN vectors should reflect an unavailable evaluator, "
            f"got decision_authority={v['decision_authority']!r}"
        )
        # An UNKNOWN outcome must never be representable as auto-incorrect or a bare "0"/"".
        assert v["expected_outcome"] not in {"auto-incorrect"}
        assert v["expected_outcome"] == "unknown"


def test_tolerance_dependent_vectors_are_tagged_open12(vectors):
    for v in vectors:
        if v["category"] == "tolerance-fraction-decimal" or "tolerance" in v["description"].lower():
            assert "OPEN-12" in v["open_items"], (
                f"{v['id']}: numeric-tolerance-dependent vector must be tagged OPEN-12 "
                "so its expected_outcome is not mistaken for settled policy"
            )


def test_no_vector_is_tagged_open12_without_being_tolerance_related(vectors):
    # Guards the inverse direction: OPEN-12 shouldn't be sprinkled on unrelated vectors,
    # which would dilute its meaning as "this specific outcome is tolerance-dependent."
    for v in vectors:
        if "OPEN-12" in v["open_items"]:
            assert v["category"] == "tolerance-fraction-decimal", (
                f"{v['id']}: OPEN-12 tag should be reserved for tolerance-dependent vectors"
            )


def test_factored_vs_expanded_policy_flag_flips_outcome(vectors):
    """Same mathematical pair, opposite policy flags, opposite expected outcomes."""
    fve = [v for v in vectors if v["category"] == "factored-vs-expanded"]
    assert len(fve) >= 2, "need both an accepting and a rejecting factored/expanded vector"

    accepted = [v for v in fve if v.get("policy_position") == "accepted"]
    rejected = [v for v in fve if v.get("policy_position") == "rejected"]
    assert accepted and rejected, "need one 'accepted' and one 'rejected' policy_position vector"

    a, r = accepted[0], rejected[0]
    assert a["expected_answer"] == r["expected_answer"]
    assert a["submitted_answer"] == r["submitted_answer"]
    assert a["policy_flags"] != r["policy_flags"]
    assert a["expected_outcome"] == "auto-correct"
    assert r["expected_outcome"] == "auto-incorrect"


def test_genuinely_wrong_answer_is_auto_incorrect(vectors):
    wrong = [v for v in vectors if v["category"] == "genuinely-wrong"]
    assert wrong, "expected a genuinely-wrong-answer vector"
    for v in wrong:
        assert v["expected_outcome"] == "auto-incorrect"
        assert v["tier"] == "tier1"


def test_unsupported_form_is_distinct_from_genuinely_wrong(vectors):
    """A parse failure (Tier 2) must not be conflated with a deterministic wrong answer (Tier 1)."""
    unsupported = next(v for v in vectors if v["category"] == "unsupported-form")
    wrong = next(v for v in vectors if v["category"] == "genuinely-wrong")
    assert unsupported["tier"] == "tier2"
    assert wrong["tier"] == "tier1"
    assert unsupported["expected_outcome"] != wrong["expected_outcome"]


# --------------------------------------------------------------------------
# Sanity: this suite is not secretly implementing a CAS
# --------------------------------------------------------------------------

def test_this_suite_does_not_implement_symbolic_evaluation():
    """Guard against scope creep: OPEN-13 (CAS/engine choice) is unresolved, so this test
    module must not contain an actual equivalence-checking implementation."""
    forbidden_imports = ("sympy", "numpy")
    source = Path(__file__).read_text(encoding="utf-8")
    for name in forbidden_imports:
        assert f"import {name}" not in source
