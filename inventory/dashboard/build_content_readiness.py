#!/usr/bin/env python3
"""
build_content_readiness.py — WS6 content-readiness dashboard/spec synthesis.

Reads six read-only, already-signed-off WS inputs under inventory/ and
computes a consolidated per-lesson readiness record for all 37 Algebra 2
lessons. Writes:
  - content_readiness.json                 (this directory)
  - content_readiness_dashboard.html        (this directory, self-contained)

STDLIB ONLY. No network. No writes outside this script's own directory
(inventory/dashboard/). All six inputs are opened read-only.

Run: python build_content_readiness.py
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent          # .../inventory/dashboard
INVENTORY_DIR = HERE.parent                     # .../inventory

INPUT_FILES = {
    "base": "content_readiness_inventory.json",
    "wave_plan": "dok-workflow/dok_wave_plan.json",
    "collisions": "review-queue/collision_review_queue.json",
    "visual_class": "visuals/visual_asset_classification.json",
    "broken_repair": "visuals/broken_path_repair.json",
    "four_one": "topic-4-1/inventory-4-1-assets.json",
    "course_map": "course-map/course_map.json",
}


def load(relpath):
    p = INVENTORY_DIR / relpath
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def wave_plan_item_review_state(item):
    """Fail-closed read of a wave-plan item's canonical review_state (NT7).
    Absent/unknown values read as 'unreviewed' (never verified)."""
    state = item.get("review_state")
    return state if state in ("unreviewed", "invalid-entry", "reviewed_once", "verified") else "unreviewed"


def main():
    inv = load(INPUT_FILES["base"])
    wave_plan = load(INPUT_FILES["wave_plan"])
    collisions = load(INPUT_FILES["collisions"])
    visual_class = load(INPUT_FILES["visual_class"])
    broken_repair = load(INPUT_FILES["broken_repair"])
    four_one = load(INPUT_FILES["four_one"])
    course_map = load(INPUT_FILES["course_map"])

    # -------------------------------------------------------------------
    # Curriculum order / topic / title / placeholder / course-map readiness
    # -------------------------------------------------------------------
    LESSON_ORDER = []
    TOPIC_OF = {}
    TITLE_OF = {}
    PLACEHOLDER_OF = {}
    COURSE_READINESS_OF = {}
    for t in course_map["topics"]:
        for l in t["lessons"]:
            LESSON_ORDER.append(l["lesson"])
            TOPIC_OF[l["lesson"]] = t["topic"]
            TITLE_OF[l["lesson"]] = l.get("title")
            PLACEHOLDER_OF[l["lesson"]] = l["placeholder"]
            COURSE_READINESS_OF[l["lesson"]] = l["readiness"]

    assert len(LESSON_ORDER) == 37, f"expected 37 lessons, got {len(LESSON_ORDER)}"

    INV_BY_LESSON = {rec["lesson"]: rec for rec in inv["lessons"]}
    assert set(INV_BY_LESSON.keys()) == set(LESSON_ORDER), "lesson set mismatch base inventory vs course_map"

    # -------------------------------------------------------------------
    # DOK wave plan: per-id dok occurrences (for conflict detection),
    # per-lesson wave membership, assessment-feeding set
    # -------------------------------------------------------------------
    ASSESSMENT_FEEDING = set(wave_plan["assessment_feeding_lessons"])
    # Per-legacy-id occurrences, keyed by the shared LEGACY id (r["id"]) —
    # this is what drives DOK-conflict detection below. Each occurrence
    # carries its own dok plus the re-keyed primary-identity fields
    # (item_uid, registry_line) so conflicting copies can be told apart
    # even though they share a legacy id. The DOK-conflict join itself is
    # still purely legacy-id -> dok, unchanged by the re-key: it never
    # needed item_uid to detect a conflict, only to report which copy is
    # which afterward. NT7 R3b: this SAME per-row loop separately reads each
    # row's review_state field (via wave_plan_item_review_state(), keyed by
    # item_uid, never by the shared legacy id) to build this dashboard's own
    # single-sourced, per-item verified-uid tally below — that read is
    # independent of, and does not change, the legacy-id -> dok join.
    id_occurrences = defaultdict(list)
    lesson_waves = defaultdict(set)
    total_wave_rows = 0
    # NT7: per-item review_state tally, read via the fail-closed helper above,
    # across all 900 wave-plan rows -- the wave plan's canonical verification
    # projection (see wave_plan_item_review_state's docstring).
    wave_plan_review_state_totals = Counter()
    # NT7 R3b: single-sourced published verification. These uid sets are the
    # ONLY place this script decides "which item_uids are verified" for
    # publication -- every downstream verified count (per-lesson dok.verified,
    # aggregates.dok.verified, derive_ws6_state's verified input) is sourced
    # from these sets, never from content_readiness_inventory.json's own
    # lessons[].dok_status.verified.
    wave_plan_verified_uids_by_lesson = defaultdict(set)
    wave_plan_verified_uids_all = set()
    # NT7-R Stage R4: per-item_uid sets for the three NON-"unreviewed"
    # review_state values, published below as aggregates.dok.review_state_uid_sets.
    # "unreviewed" is deliberately NOT carried as its own set here -- it is by
    # far the largest bucket (the majority of the 900 rows) and is fully recoverable
    # as "any of the wave plan's 900 item_uids not present in one of these
    # three sets," so leaving it implicit keeps the published artifact small.
    # "verified" here is exactly wave_plan_verified_uids_all (same predicate,
    # same loop) -- kept as its own accumulator so this dict is a complete,
    # self-contained three-way partition read straight off review_state,
    # independent of the verified-specific accumulators above.
    review_state_uid_sets = {"invalid-entry": set(), "reviewed_once": set(), "verified": set()}
    # Dual-denominator identity (rc-merge-auth-5-4-2026-07-23, additive): 22
    # of the 900 wave-plan rows now carry status=='merged-alias' (carried
    # verbatim from the registry by gen_dok_wave_plan.py -- see that
    # script's "Merged-alias overlay" docstring section). Tracked here,
    # per-lesson and globally, purely as a NEW, additive overlay -- every
    # OTHER aggregate/count in this script (dok totals, ws6 distribution,
    # ready/partial gates, etc.) stays registry-row-count based (audit-
    # style, unchanged), exactly as the untouched EXPECTED_* pins in
    # gen_dok_wave_plan.py prove this merge never touched dok/role/wave
    # content.
    merged_alias_uids_by_lesson = defaultdict(set)
    merged_alias_uids_all = set()
    for wave_key, lessons_dict in wave_plan["waves"].items():
        wnum = int(wave_key)
        for lesson, rows in lessons_dict.items():
            lesson_waves[lesson].add(wnum)
            total_wave_rows += len(rows)
            for r in rows:
                id_occurrences[r["id"]].append(
                    {
                        "dok": r["dok"], "item_uid": r["item_uid"], "registry_line": r["registry_line"],
                        "status": r.get("status", "active"), "alias_of": r.get("alias_of"),
                    }
                )
                r_review_state = wave_plan_item_review_state(r)
                wave_plan_review_state_totals[r_review_state] += 1
                if r_review_state in review_state_uid_sets:
                    review_state_uid_sets[r_review_state].add(r["item_uid"])
                if r_review_state == "verified":
                    wave_plan_verified_uids_by_lesson[lesson].add(r["item_uid"])
                    wave_plan_verified_uids_all.add(r["item_uid"])
                if r.get("status") == "merged-alias":
                    merged_alias_uids_by_lesson[lesson].add(r["item_uid"])
                    merged_alias_uids_all.add(r["item_uid"])

    # A merged-alias row must never itself be verified (it was resolved away
    # in favor of its survivor, never reviewed as an alias) -- fail loudly,
    # not silently, if this invariant is ever violated.
    assert not (merged_alias_uids_all & wave_plan_verified_uids_all), (
        "merged-alias item_uid(s) unexpectedly appear in the verified set: "
        f"{sorted(merged_alias_uids_all & wave_plan_verified_uids_all)}"
    )

    # -------------------------------------------------------------------
    # Collision review queue: groups by lesson
    # -------------------------------------------------------------------
    collision_groups_by_lesson = defaultdict(list)
    for g in collisions["groups"]:
        collision_groups_by_lesson[g["lesson"]].append(g)

    # DOK-conflict ids: declared method is a JOIN, not a free scan of the
    # wave plan. Start from the collision review queue's ambiguous
    # legacy_ids (the queue has no dok field of its own), look up each
    # legacy_id's per-copy dok values FROM the wave plan
    # (id_dok_occurrences), and keep it as a conflict only if that
    # legacy_id has more than one distinct dok across its wave-plan copies.
    missing_from_wave_plan = sorted(
        g["legacy_id"] for g in collisions["groups"] if g["legacy_id"] not in id_occurrences
    )
    assert not missing_from_wave_plan, (
        f"collision legacy_id(s) not found in dok_wave_plan id_occurrences: {missing_from_wave_plan}"
    )

    dok_conflict_rows = []
    for g in collisions["groups"]:
        id_ = g["legacy_id"]
        occs = id_occurrences[id_]
        doks = [o["dok"] for o in occs]
        uniq = sorted(set(doks))
        if len(uniq) > 1:
            # Additive enrichment (item_uid re-key): pair the lower-dok copy
            # as A and the higher-dok copy as B, consistent with
            # dok_a<=dok_b. This assumes exactly 2 wave-plan occurrences per
            # conflicting legacy id (per dok_wave_plan.json's identity_note:
            # every legacy id shared across 2 rows is shared by exactly 2),
            # asserted here so a future data shape change fails loudly
            # instead of silently mis-pairing A/B.
            assert len(occs) == 2, (
                f"expected exactly 2 wave-plan occurrences for conflicting legacy id {id_}, "
                f"got {len(occs)}"
            )
            low = min(occs, key=lambda o: o["dok"])
            high = max(occs, key=lambda o: o["dok"])
            # rc-merge-auth-5-4-2026-07-23 additive annotation: exactly one
            # of this pair's two occurrences carries status=='merged-alias'
            # for all 22 of these rows (every dok_conflict_rows entry IS one
            # of the 22 merge-authorized pairs -- see the len==22/all-5-4
            # asserts just below). Which of low/high (uid_a/uid_b) is the
            # alias is NOT positionally fixed (it depends on which absolute
            # dok value the merge kept as survivor), so it is looked up
            # explicitly per row, never assumed.
            alias_occ = next((o for o in occs if o["status"] == "merged-alias"), None)
            survivor_occ = next((o for o in occs if o["status"] != "merged-alias"), None)
            if alias_occ is not None:
                assert survivor_occ is not None and alias_occ["alias_of"] == survivor_occ["item_uid"], (
                    f"legacy_id {id_}: merged-alias occurrence's alias_of does not match its "
                    "sibling occurrence's item_uid within this same conflict pair"
                )
            dok_conflict_rows.append({
                "id": id_,
                "dok_a": uniq[0],
                "dok_b": uniq[-1],
                "uid_a": low["item_uid"],
                "line_a": low["registry_line"],
                "uid_b": high["item_uid"],
                "line_b": high["registry_line"],
                "merged_alias_item_uid": alias_occ["item_uid"] if alias_occ else None,
                "survivor_item_uid": survivor_occ["item_uid"] if alias_occ else None,
            })
    dok_conflict_rows.sort(key=lambda r: r["id"])
    dok_conflict_ids = {r["id"] for r in dok_conflict_rows}

    # Guards: fail loudly if a future input change breaks the shape of the
    # locked reconciliation, rather than silently producing a different
    # (unverified) subset.
    assert len(dok_conflict_rows) == 22, f"expected 22 DOK-conflict rows, got {len(dok_conflict_rows)}"
    assert all(r["id"].startswith("5-4-") for r in dok_conflict_rows), (
        "expected all DOK-conflict rows to be in lesson 5-4"
    )
    dok1v2 = sum(1 for r in dok_conflict_rows if (r["dok_a"], r["dok_b"]) == (1, 2))
    dok2v3 = sum(1 for r in dok_conflict_rows if (r["dok_a"], r["dok_b"]) == (2, 3))
    assert dok1v2 == 21, f"expected 21 dok1-vs-dok2 conflict rows, got {dok1v2}"
    assert dok2v3 == 1, f"expected 1 dok2-vs-dok3 conflict row, got {dok2v3}"
    q41_row = next((r for r in dok_conflict_rows if r["id"] == "5-4-savvas-q41"), None)
    assert q41_row is not None and (q41_row["dok_a"], q41_row["dok_b"]) == (2, 3), (
        "expected 5-4-savvas-q41 to be the sole dok2-vs-dok3 conflict row"
    )
    # rc-merge-auth-5-4-2026-07-23: every one of the 22 DOK-conflict rows IS
    # one of the merge-authorized pairs -- each must carry a resolved
    # merged_alias_item_uid/survivor_item_uid annotation.
    unresolved_conflict_rows = [r["id"] for r in dok_conflict_rows if r["merged_alias_item_uid"] is None]
    assert not unresolved_conflict_rows, (
        f"expected all 22 dok_conflict_rows to have a merged-alias occurrence, but these do not: "
        f"{unresolved_conflict_rows}"
    )

    def lesson_collision_stats(lesson):
        groups = collision_groups_by_lesson.get(lesson, [])
        n = len(groups)
        dokc = sum(1 for g in groups if g["legacy_id"] in dok_conflict_ids)
        return n, dokc, n - dokc

    # -------------------------------------------------------------------
    # Visual asset classification: rows by lesson (137 absent rows only)
    # -------------------------------------------------------------------
    visual_rows_by_lesson = defaultdict(list)
    for r in visual_class["rows"]:
        visual_rows_by_lesson[r["lesson"]].append(r)

    # Broken-path counts: derived from broken_path_repair.json's fixes[]
    # (not hardcoded). Cross-checked per-lesson and in total against
    # content_readiness_inventory.json's visuals_broken_path figures.
    broken_by_lesson = Counter(fix["lesson"] for fix in broken_repair["fixes"])
    assert broken_repair["count"] == len(broken_repair["fixes"]), (
        "broken_path_repair.json count field does not match len(fixes)"
    )
    assert broken_repair["count"] == 7, f"expected 7 broken visual paths, got {broken_repair['count']}"
    for lesson in LESSON_ORDER:
        base_broken = INV_BY_LESSON[lesson].get("visuals_broken_path", 0)
        derived_broken = broken_by_lesson.get(lesson, 0)
        assert derived_broken == base_broken, (
            f"broken_path_repair.json vs content_readiness_inventory.json mismatch for {lesson}: "
            f"{derived_broken} != {base_broken}"
        )

    def lesson_visual_stats(lesson):
        rows = visual_rows_by_lesson.get(lesson, [])
        absent = len(rows)
        essential = sum(1 for r in rows if r["importance"] == "essential")
        supporting = sum(1 for r in rows if r["importance"] == "supporting")
        decorative = sum(1 for r in rows if r["importance"] == "decorative")
        tikz = sum(1 for r in rows if r["recoverability"] == "tikz_regenerable")
        pdf_req = sum(1 for r in rows if r["recoverability"] == "source_pdf_required")
        photo = sum(1 for r in rows if r["recoverability"] == "irreplaceable_photo")
        needs_conf = sum(1 for r in rows if "needs_teacher_confirmation" in r.get("flags", []))
        broken = broken_by_lesson.get(lesson, 0)
        return {
            "absent": absent,
            "broken_path": broken,
            "essential": essential,
            "supporting": supporting,
            "decorative": decorative,
            "tikz_regenerable": tikz,
            "source_pdf_required": pdf_req,
            "irreplaceable_photo": photo,
            "needs_teacher_confirmation": needs_conf,
        }

    # -------------------------------------------------------------------
    # Course map: dangling (dropped) edges, split upstream/downstream per lesson
    #
    # GAP_FAMILY_REASONS is the set of dropped-edge reasons that represent a
    # genuine "something should feed into this lesson but doesn't exist yet"
    # gap, as opposed to assessment-forward-ref (a forward reference to a
    # not-yet-written assessment item, which is expected and not a gap in
    # this lesson's own prerequisite chain). A sibling workstream re-cut
    # course_map.json's dropped-edge taxonomy and split what used to be one
    # "frontload-gap" reason into "frontload-gap" (genuinely front-of-year,
    # never built) vs. "retirement-gap" (built, then retired — e.g. 4-1).
    # Deriving this filter from a reason SET, not a single hardcoded label,
    # keeps the build robust to that kind of relabeling.
    # -------------------------------------------------------------------
    dropped_edges = course_map["dropped_edges"]
    GAP_FAMILY_REASONS = ("frontload-gap", "retirement-gap", "retired-missing")

    def edge_touches(node_id, lesson):
        return node_id == lesson or node_id.startswith(lesson + "-")

    upstream_dangling_by_lesson = defaultdict(list)
    downstream_dangling_by_lesson = defaultdict(list)
    for e in dropped_edges:
        src, tgt, reason = e["source"], e["target"], e["reason"]
        for lesson in LESSON_ORDER:
            if edge_touches(tgt, lesson) and reason in GAP_FAMILY_REASONS:
                upstream_dangling_by_lesson[lesson].append(e)
            if edge_touches(src, lesson):
                downstream_dangling_by_lesson[lesson].append(e)

    # -------------------------------------------------------------------
    # WS6 reconciled readiness state — DERIVED per lesson from source
    # signals (per manager brief; see SPEC.md section 2), not a hardcoded
    # per-lesson lookup. Precedence matters: CALIBRATED is tested BEFORE
    # the generic base-readiness "partial" branch, because 3-5's base
    # readiness is "partial" (its answers/visuals gates are still open)
    # even though it already has cal==rr (all rows carry real calibrated
    # DOK anchors) — that is what promotes it out of the "partial" bucket
    # the other 9 partial lessons stay in.
    # -------------------------------------------------------------------
    def derive_ws6_state(base_readiness, registry_rows, calibrated, verified, course_readiness):
        if base_readiness == "ready" and registry_rows > 0 and verified == registry_rows:
            return "VERIFIED"       # 0 today (aspirational)
        elif base_readiness == "ready":
            return "READY"          # 0 today (aspirational)
        elif registry_rows > 0 and calibrated == registry_rows:
            return "CALIBRATED"     # 3-5 (all rows calibrated, real anchors)
        elif base_readiness == "partial":
            return "INCOMPLETE"     # the nine
        elif base_readiness == "blocked":
            return "BLOCKED"        # 4-1 staged-not-ingested
        elif course_readiness == "frontload-blocked":
            return "PROVISIONAL"    # 18 front-of-year
        else:
            return "ABSENT"         # 8 deprecated/skipped/shell

    WS6_STATE = {}
    for lesson in LESSON_ORDER:
        base = INV_BY_LESSON[lesson]
        dok_status = base["dok_status"]
        # NT7 R3b: verified is fed in from the wave-plan-derived per-lesson
        # uid set (single-sourced, see above), NOT base["dok_status"]["verified"].
        lesson_verified_for_ws6 = len(wave_plan_verified_uids_by_lesson.get(lesson, set()))
        WS6_STATE[lesson] = derive_ws6_state(
            base["readiness"], base["registry_rows"],
            dok_status["calibrated"], lesson_verified_for_ws6,
            COURSE_READINESS_OF[lesson],
        )
    assert set(WS6_STATE.keys()) == set(LESSON_ORDER), "WS6_STATE mapping incomplete"

    ws6_dist = defaultdict(int)
    for v in WS6_STATE.values():
        ws6_dist[v] += 1

    # Guard: fail loudly if the derivation stops matching the locked
    # reconciliation distribution from the manager brief.
    expected_ws6_dist = {"CALIBRATED": 1, "INCOMPLETE": 9, "BLOCKED": 1, "PROVISIONAL": 18, "ABSENT": 8}
    actual_ws6_dist = {k: ws6_dist[k] for k in expected_ws6_dist}
    assert actual_ws6_dist == expected_ws6_dist, (
        f"WS6 state distribution mismatch: computed={actual_ws6_dist} expected={expected_ws6_dist}. "
        "DELIBERATE FROZEN-BASELINE PIN, not a bug: this distribution changes at the FIRST "
        "verified Wave-0 item, not only when a whole lesson fully verifies -- 3-5 demotes "
        "CALIBRATED->INCOMPLETE via the canonical verified overlay (a verified row leaves its "
        "registry-derived base bucket, so 3-5's calibrated count drops below registry_rows and "
        "derive_ws6_state falls through to base readiness 'partial' -> INCOMPLETE). Update "
        "expected_ws6_dist deliberately per "
        "inventory/dok-workflow/DOK_VERIFICATION_WORKFLOW.md, "
        "\"Approval procedure (operational, named updates)\", step 3(c2) -- this failure means "
        "that step was skipped, not that the pin is wrong."
    )

    # -------------------------------------------------------------------
    # Dimension-status rubric (deterministic; see SPEC.md section 3 for
    # the documented resolution of the visuals grey/green wording overlap)
    # -------------------------------------------------------------------
    def dim_content(registry_rows, base_readiness, coll_groups):
        if registry_rows == 0 and base_readiness == "absent":
            return "grey"
        if registry_rows == 0 and base_readiness == "blocked":
            return "red"
        if registry_rows > 0 and coll_groups > 0:
            return "amber"
        if registry_rows > 0 and coll_groups == 0:
            return "green"
        return "grey"  # defensive fallback (should not be reached)

    def dim_answers(registry_rows, missing, with_evidence, coverage_pct):
        if registry_rows == 0:
            return "grey"
        if missing == 0:
            return "green"
        if with_evidence == 0:
            return "red"
        return "amber"  # partial coverage, 0 < coverage_pct < 100

    def dim_dok(registry_rows, calibrated):
        if registry_rows == 0:
            return "grey"
        if calibrated == registry_rows:
            return "green"
        return "amber"

    def dim_visuals(registry_rows, absent, broken, essential):
        # Resolution of brief wording overlap (grey vs green both said
        # "if none absent/broken"): grey gates on no registry rows at all
        # (nothing to have visuals on), green gates on rows existing with
        # zero absent/broken. See SPEC.md section 3.
        if registry_rows == 0:
            return "grey"
        if (absent + broken) == 0:
            return "green"
        if essential > 0:
            return "red"
        return "amber"

    def dim_prereqs(lesson, placeholder, upstream, downstream):
        if lesson == "4-1":
            return "red"
        if upstream:
            return "red"
        if downstream:
            return "amber"
        if placeholder:
            return "grey"
        return "green"

    # -------------------------------------------------------------------
    # Top blockers (human-readable, per lesson)
    # -------------------------------------------------------------------
    def top_blockers(base_readiness, readiness_reason, coll_groups, coll_dokc,
                      upstream, downstream):
        blockers = []
        if readiness_reason:
            if base_readiness in ("absent", "blocked"):
                blockers.append(readiness_reason)
            else:
                blockers.extend(p.strip() for p in readiness_reason.split(";") if p.strip())
        if coll_dokc:
            blockers.append(f"{coll_dokc} DOK-conflict collision pair(s) (higher priority than prompt-drift)")
        elif coll_groups:
            blockers.append(f"{coll_groups} prompt-drift collision group(s) (same-DOK, advisory merge)")
        if upstream:
            blockers.append(
                f"{len(upstream)} upstream prereq/echo edge(s) dangling into this lesson "
                f"(frontload-gap/retirement-gap/retired-missing)"
            )
        if downstream:
            blockers.append(f"{len(downstream)} downstream edge(s) dropped from this lesson (dangling reference)")
        return blockers

    # -------------------------------------------------------------------
    # Assemble per-lesson records
    # -------------------------------------------------------------------
    lessons_out = []
    total_registry_rows = 0
    dok_totals = defaultdict(int)
    answers_with_evidence_total = 0
    answers_missing_total = 0
    # NT7 R3b: the union, across all lessons, of every per-lesson verified-uid
    # set that actually gets folded into this script's OWN published
    # dok.verified counts below -- i.e. what this dashboard is telling a
    # reader is verified, not merely what it read. Compared against
    # wave_plan_verified_uids_all (built independently above, directly from
    # the wave-plan iteration) and against the base inventory's own
    # aggregate.dok_verified_item_uids in the reconciliation checks section.
    dashboard_published_verified_uids = set()
    # NOT published anywhere -- kept only so the reconciliation checks below
    # can still cross-check the wave plan's canonical review_state COUNT
    # against the base inventory's OWN (independently, canonically computed
    # per Stage R2) dok_status.verified count. This is a coarser, count-level
    # echo of the finer per-item UID-set gate added by NT7 R3b; both are kept
    # because a count match does not imply a uid match (or vice versa).
    base_dok_verified_total = 0

    for lesson in LESSON_ORDER:
        base = INV_BY_LESSON[lesson]
        registry_rows = base["registry_rows"]
        total_registry_rows += registry_rows

        has_any_source = bool(base["se_pdf"] or base["te_pdf"] or base["se_tex"] or base["te_tex"])

        with_evidence = base["answers_with_evidence"]
        missing = base["missing_answers"]
        coverage_pct = round(with_evidence / registry_rows * 100, 1) if registry_rows > 0 else None
        answers_with_evidence_total += with_evidence
        answers_missing_total += missing

        dok_status = base["dok_status"]
        # NT7 R3b: SINGLE-SOURCE published verification. known_auto/unreviewed/
        # calibrated stay sourced from the base inventory (registry-derived
        # buckets, unchanged) -- but verified is no longer read from
        # dok_status["verified"] at all. It is instead this lesson's
        # wave-plan-derived verified-uid count (single source: the wave
        # plan's canonical review_state, read via wave_plan_item_review_state
        # above), so the dashboard never republishes a second, potentially
        # stale copy of the base inventory's own verified number.
        for k in ("known_auto", "unreviewed", "calibrated"):
            dok_totals[k] += dok_status[k]
        base_dok_verified_total += dok_status["verified"]
        lesson_waveplan_verified_uids = wave_plan_verified_uids_by_lesson.get(lesson, set())
        lesson_waveplan_verified_count = len(lesson_waveplan_verified_uids)
        dashboard_published_verified_uids |= lesson_waveplan_verified_uids
        dok_totals["verified"] += lesson_waveplan_verified_count

        # NT7 R3b: per-lesson sum coherence. Stage R2 canonicalized the base
        # inventory builder so a row promoted to 'verified' by the canonical
        # projection LEAVES its base dok_status bucket (known_auto/
        # unreviewed/calibrated) -- the base builder's overlay removes it,
        # it does not double-count it. So summing the three non-verified
        # base buckets plus THIS lesson's wave-plan-derived verified count
        # must reconstruct the lesson's full registry_rows. Now that real
        # verifications exist (first: NT10's 39 lesson-5-4 rows, 2026-07-22),
        # this assert is what proves the base rebuild and the wave-plan
        # recording stayed in lockstep for this lesson, rather than
        # double-counting or dropping a row.
        assert (
            dok_status["known_auto"] + dok_status["unreviewed"] + dok_status["calibrated"]
            + lesson_waveplan_verified_count == registry_rows
        ), (
            f"{lesson}: base dok bucket sum ({dok_status['known_auto']}+{dok_status['unreviewed']}+"
            f"{dok_status['calibrated']}) + wave-plan verified ({lesson_waveplan_verified_count}) "
            f"!= registry_rows ({registry_rows})"
        )

        waves = sorted(lesson_waves.get(lesson, set()))
        assessment_feeding = lesson in ASSESSMENT_FEEDING

        coll_groups, coll_dokc, coll_drift = lesson_collision_stats(lesson)

        vis = lesson_visual_stats(lesson)

        upstream = upstream_dangling_by_lesson.get(lesson, [])
        downstream = downstream_dangling_by_lesson.get(lesson, [])

        overall_readiness = base["readiness"]
        ws6_state = WS6_STATE[lesson]

        d_content = dim_content(registry_rows, overall_readiness, coll_groups)
        d_answers = dim_answers(registry_rows, missing, with_evidence, coverage_pct)
        d_dok = dim_dok(registry_rows, dok_status["calibrated"])
        d_visuals = dim_visuals(registry_rows, vis["absent"], vis["broken_path"], vis["essential"])
        d_prereqs = dim_prereqs(lesson, PLACEHOLDER_OF[lesson], upstream, downstream)

        blockers = top_blockers(
            overall_readiness, base.get("readiness_reason", ""),
            coll_groups, coll_dokc, upstream, downstream,
        )

        lessons_out.append({
            "lesson": lesson,
            "topic": TOPIC_OF[lesson],
            "title": TITLE_OF[lesson],
            "registry_rows": registry_rows,
            "source": {
                "se_pdf": base["se_pdf"],
                "te_pdf": base["te_pdf"],
                "se_tex": base["se_tex"],
                "te_tex": base["te_tex"],
                "has_any_source": has_any_source,
            },
            "answers": {
                "with_evidence": with_evidence,
                "missing": missing,
                "coverage_pct": coverage_pct,
            },
            "dok": {
                "known_auto": dok_status["known_auto"],
                "unreviewed": dok_status["unreviewed"],
                "calibrated": dok_status["calibrated"],
                # NT7 R3b: single-sourced from the wave plan's canonical
                # review_state (NOT base["dok_status"]["verified"]).
                "verified": lesson_waveplan_verified_count,
                "waves": waves,
                "assessment_feeding": assessment_feeding,
            },
            # rc-merge-auth-5-4-2026-07-23 (additive): registry_rows above
            # stays the raw, audit-style row count (unchanged by this merge);
            # active_registry_rows is what a student-facing consumer (qb.py)
            # actually selects from for this lesson.
            "merged_alias_rows": len(merged_alias_uids_by_lesson.get(lesson, ())),
            "active_registry_rows": registry_rows - len(merged_alias_uids_by_lesson.get(lesson, ())),
            "visuals": vis,
            "collisions": {
                "groups": coll_groups,
                "dok_conflict": coll_dokc,
                "prompt_drift": coll_drift,
            },
            "prereqs": {
                "upstream_dangling": upstream,
                "downstream_dangling": downstream,
            },
            "overall_readiness": overall_readiness,
            "ws6_state": ws6_state,
            "dimension_status": {
                "content": d_content,
                "answers": d_answers,
                "dok": d_dok,
                "visuals": d_visuals,
                "prereqs": d_prereqs,
            },
            "top_blockers": blockers,
        })

    # -------------------------------------------------------------------
    # Aggregates
    # -------------------------------------------------------------------
    total_visuals_absent = sum(len(v) for v in visual_rows_by_lesson.values())
    total_visuals_broken = broken_repair["count"]  # derived; all in 3-5 today per broken_repair.json fixes[]

    importance_totals = defaultdict(int)
    recoverability_totals = defaultdict(int)
    needs_conf_total = 0
    for r in visual_class["rows"]:
        importance_totals[r["importance"]] += 1
        recoverability_totals[r["recoverability"]] += 1
        if "needs_teacher_confirmation" in r.get("flags", []):
            needs_conf_total += 1

    coll_meta = collisions["meta"]
    total_collision_groups = coll_meta["group_count"]
    per_lesson_counts = coll_meta["per_lesson_counts"]
    confidence_dist = coll_meta["recommendation_confidence_distribution"]
    total_dok_conflict = len(dok_conflict_rows)
    total_prompt_drift = total_collision_groups - total_dok_conflict

    edges_dropped_by_reason = course_map["stats"]["edges_dropped_by_reason"]

    course_map_readiness_dist = defaultdict(int)
    for lesson in LESSON_ORDER:
        course_map_readiness_dist[COURSE_READINESS_OF[lesson]] += 1

    base_readiness_dist = inv["aggregate"]["readiness_distribution"]

    wave_counts_raw = wave_plan["wave_counts"]
    wave_counts = {int(k): v for k, v in wave_counts_raw.items()}

    aggregates = {
        "total_registry_rows": total_registry_rows,
        "dok": {
            "known_auto": dok_totals["known_auto"],
            "unreviewed": dok_totals["unreviewed"],
            "calibrated": dok_totals["calibrated"],
            "verified": dok_totals["verified"],
            # NT7 additive field: per-item review_state totals from the wave
            # plan's canonical verification projection (dok-workflow's
            # gen_dok_wave_plan.py, aligned to tools/dok-review/dok_review.py's
            # entry_is_verified). Whatever the review log + approvals
            # manifest compute at build time is what publishes here.
            "wave_plan_review_state_totals": {
                "unreviewed": wave_plan_review_state_totals["unreviewed"],
                "invalid-entry": wave_plan_review_state_totals["invalid-entry"],
                "reviewed_once": wave_plan_review_state_totals["reviewed_once"],
                "verified": wave_plan_review_state_totals["verified"],
            },
            # NT7-R Stage R4 additive field: per-item_uid sets for the three
            # NON-"unreviewed" review_state values, read via the same
            # fail-closed wave_plan_item_review_state() helper as
            # wave_plan_review_state_totals above. "unreviewed" is
            # deliberately NOT its own key here -- it is implicit: any of the
            # wave plan's 900 item_uids not present in one of these three
            # sets is unreviewed. The sets hold whatever the canonical
            # projection computes at build time. Sorted for determinism.
            "review_state_uid_sets": {
                "invalid-entry": sorted(review_state_uid_sets["invalid-entry"]),
                "reviewed_once": sorted(review_state_uid_sets["reviewed_once"]),
                "verified": sorted(review_state_uid_sets["verified"]),
            },
        },
        "dok_waves": wave_counts,
        "visuals": {
            "absent": total_visuals_absent,
            "broken_path": total_visuals_broken,
            "essential": importance_totals["essential"],
            "supporting": importance_totals["supporting"],
            "decorative": importance_totals["decorative"],
            "tikz_regenerable": recoverability_totals["tikz_regenerable"],
            "source_pdf_required": recoverability_totals["source_pdf_required"],
            "irreplaceable_photo": recoverability_totals["irreplaceable_photo"],
            "needs_teacher_confirmation": needs_conf_total,
        },
        "collisions": {
            "groups": total_collision_groups,
            "per_lesson": per_lesson_counts,
            "dok_conflict": total_dok_conflict,
            "prompt_drift": total_prompt_drift,
            "confidence": confidence_dist,
        },
        "answers": {
            "with_evidence": answers_with_evidence_total,
            "missing_all": answers_missing_total,
            "missing_the_nine": inv["aggregate"]["total_missing_answers_the_nine"],
        },
        "edges": {
            "resolved": course_map["stats"]["edges_resolved_total"],
            "dropped": course_map["stats"]["edges_dropped_total"],
            # One key per reason actually present in course_map's current
            # edges_dropped_by_reason (reason string with "-" -> "_"), not a
            # hardcoded list of reason names. This is what makes the new
            # "retirement-gap" reason (and any future relabeling) show up
            # automatically without a code change.
            **{reason.replace("-", "_"): count for reason, count in edges_dropped_by_reason.items()},
        },
        "readiness_ws6": {
            "CALIBRATED": ws6_dist["CALIBRATED"],
            "INCOMPLETE": ws6_dist["INCOMPLETE"],
            "BLOCKED": ws6_dist["BLOCKED"],
            "PROVISIONAL": ws6_dist["PROVISIONAL"],
            "ABSENT": ws6_dist["ABSENT"],
        },
        # Dual-denominator identity (rc-merge-auth-5-4-2026-07-23, additive).
        # Every OTHER aggregate above (total_registry_rows, dok totals, ws6
        # distribution, etc.) is registry-row-count based (audit-style: all
        # 900 rows, alias rows included, unchanged by this merge). This is
        # the authoritative place to read the RC-mandated active/alias split
        # from this dashboard: STUDENT-FACING selection (qb.py) resolves
        # each merged-alias row DELIBERATELY to its survivor and never
        # selects/counts the alias row itself.
        "identity_reconciliation": {
            "raw_registry_identities": total_wave_rows,
            "merged_alias_identities": len(merged_alias_uids_all),
            "active_canonical_items": total_wave_rows - len(merged_alias_uids_all),
            "merged_alias_item_uids": sorted(merged_alias_uids_all),
            "authorization_record_id": "rc-merge-auth-5-4-2026-07-23",
            "statement": (
                "raw_registry_identities == active_canonical_items + merged_alias_identities "
                "(900 == 878 + 22). None of the 22 merged_alias_item_uids ever appear in "
                "aggregates.dok.review_state_uid_sets.verified (asserted at build time) or in "
                "any other readiness/verified/actionable set published by this dashboard."
            ),
        },
    }

    readiness_reconciliation = {
        "base_inventory_distribution": {
            "ready": base_readiness_dist["ready"],
            "partial": base_readiness_dist["partial"],
            "blocked": base_readiness_dist["blocked"],
            "absent": base_readiness_dist["absent"],
        },
        "course_map_distribution": {
            "frontload_blocked": course_map_readiness_dist["frontload-blocked"],
            "calibrated": course_map_readiness_dist["calibrated"],
            "absent": course_map_readiness_dist["absent"],
            "partial": course_map_readiness_dist["partial"],
        },
        "note": (
            "Base inventory counts 3-5 as 'partial' (missing_answers/visuals/verified gates unmet) "
            "and 4-1 as 'blocked' (staged material, 0 registry rows). Course-map counts 3-5 as "
            "'calibrated' (real DOK anchors exist) and 4-1 as 'absent' (no items array populated). "
            "WS6 reconciles both: 3-5 is promoted to its own CALIBRATED state (the only lesson with "
            "real DOK-2/DOK-3 anchors, even though answer/visual gates remain open), and 4-1 keeps "
            "its own BLOCKED state distinct from the 8 truly ABSENT (deprecated/skipped) lessons and "
            "the 18 PROVISIONAL front-of-year lessons, because 4-1 uniquely has staged-but-uningested "
            "material (calibration file, 61 screenshots, 15 skeleton stubs)."
        ),
    }

    # -------------------------------------------------------------------
    # dok_conflict_subset
    # -------------------------------------------------------------------
    dok_conflict_subset = {
        "count": len(dok_conflict_rows),
        "all_in_lesson": "5-4",
        "note": (
            "22 of the 85 collision groups have two registry copies carrying DIFFERENT DOK levels "
            "in dok_wave_plan.json (all 22 are in lesson 5-4; 21 are dok1-vs-dok2, and "
            "5-4-savvas-q41 is dok2-vs-dok3). These are higher priority to resolve than the "
            "remaining 63 same-DOK prompt-drift collisions, because merging the wrong copy would "
            "also corrupt the DOK label and wave assignment, not just the prompt text. Each row "
            "also carries the two copies' item_uid/registry_line (uid_a/line_a for the lower-dok "
            "copy, uid_b/line_b for the higher-dok copy) from WS4's re-key, since item_uid — not "
            "the shared legacy id used to detect this conflict — is the correct primary key for "
            "actually resolving which copy to keep."
        ),
        "rows": dok_conflict_rows,
    }

    # -------------------------------------------------------------------
    # four_one_stranded
    #
    # dangling_into_4_1 is filtered by TARGET touching 4-1 and reason in the
    # gap family (GAP_FAMILY_REASONS, i.e. NOT assessment-forward-ref) —
    # not by a single hardcoded reason string. That is what keeps this
    # correct regardless of whether the source labels these edges
    # "frontload-gap" or "retirement-gap": today all 4 read "retirement-gap"
    # (4-1 was built, then retired, so its dangling references are a
    # retirement gap, not a front-of-year gap).
    #
    # dangling_into_3_1 stays narrowly "frontload-gap" targeting 3-1 — that
    # one edge (5-1's launch prereq) really is a front-of-year gap, not a
    # 4-1 retirement artifact, so it must NOT be folded into the 4-1 count.
    # -------------------------------------------------------------------
    dangling_into_4_1 = [e for e in dropped_edges if edge_touches(e["target"], "4-1")
                          and e["reason"] in GAP_FAMILY_REASONS]
    dangling_into_3_1 = [e for e in dropped_edges if edge_touches(e["target"], "3-1")
                          and e["reason"] == "frontload-gap"]
    assert len(dangling_into_4_1) == 4, (
        f"expected 4 gap-family edges (frontload-gap/retirement-gap/retired-missing) into 4-1, "
        f"got {len(dangling_into_4_1)}"
    )
    assert len(dangling_into_3_1) == 1, f"expected 1 frontload-gap edge into 3-1, got {len(dangling_into_3_1)}"
    assert all(edge_touches(e["target"], "3-1") for e in dangling_into_3_1), (
        "fifth_frontload_gap_edge_into_3_1 candidate does not actually target 3-1"
    )

    four_one_stranded = {
        "state": four_one["overall_state"],
        "staged": {
            "calibration": four_one["assets"]["calibration"]["present"] and
                           four_one["assets"]["calibration"]["item_analysis_populated"],
            "screenshots": four_one["assets"]["images"]["count"],
            "skeleton_stubs": four_one["assets"]["skeleton"]["entry_count"],
            "registry_rows": four_one["assets"]["registry"]["rows_for_4-1"],
            "se_te": any(four_one["assets"]["se_te_source"][k] for k in
                         ("se_pdf", "se_tex", "te_pdf", "te_tex")),
        },
        "dangling_edges_into_4_1": dangling_into_4_1,
        "fifth_frontload_gap_edge_into_3_1": dangling_into_3_1[0],
        "teacher_judgment_items": four_one["teacher_judgment_items"],
    }

    # -------------------------------------------------------------------
    # provenance
    # -------------------------------------------------------------------
    provenance = {
        "lesson/topic/title/placeholder/overall course-map readiness":
            "course-map/course_map.json (topics[].lessons[])",
        "registry_rows, source.{se_pdf,te_pdf,se_tex,te_tex}, answers.{with_evidence,missing}, "
        "overall_readiness, readiness_reason":
            "content_readiness_inventory.json (lessons[])",
        "dok.{known_auto,unreviewed,calibrated}":
            "content_readiness_inventory.json (lessons[].dok_status), cross-checked against "
            "dok-workflow/dok_wave_plan.json row counts",
        "dok.verified":
            "NT7 R3b: SINGLE-SOURCED from dok-workflow/dok_wave_plan.json's per-item review_state "
            "field, read via this script's fail-closed wave_plan_item_review_state() helper -- "
            "NEVER from content_readiness_inventory.json's own lessons[].dok_status.verified, even "
            "though that value is (post Stage R2) itself canonically computed. The wave plan's "
            "review_state is the canonical projection of tools/dok-review/dok_review.py's "
            "entry_is_verified(), reached through dok-workflow/gen_dok_wave_plan.py's generator "
            "call; this script never re-derives verification, it only reads that label. Both this "
            "script's per-lesson/aggregate published verified counts AND the ws6 VERIFIED gate "
            "(derive_ws6_state's verified input) come from this single wave-plan-derived source. "
            "Published verified item_uids are then SET-GATED, per item, against the base "
            "inventory's OWN independently computed canonical projection "
            "(aggregate.dok_verified_item_uids) -- a three-way per-item set-equality check plus a "
            "symmetric-difference assert at build time (see the reconciliation checks section). "
            "registry.jsonl's reviewed_by/reviewed_at fields are application-time metadata written "
            "by a future, deliberate promotion step (qb_promote.py, not built) -- they are NEVER "
            "read by this script and NEVER verification authority for any consumer.",
        "dok.wave_plan_review_state_totals":
            "Derived (NT7) from dok-workflow/dok_wave_plan.json (waves[][].review_state per item), read "
            "via this script's fail-closed wave_plan_item_review_state() helper. Per-item verification "
            "state now comes from the wave plan's canonical projection (review_state); the ONLY "
            "verification predicate anywhere in this pipeline is tools/dok-review/dok_review.py's "
            "entry_is_verified, applied through the wave-plan generator's (gen_dok_wave_plan.py) own "
            "projection -- this script never re-derives verification itself, it only reads the label. "
            "Cross-checked at build time against content_readiness_inventory.json's OWN, "
            "independently computed aggregate.dok_review_state_totals (that builder derives it from "
            "registry + alias map + review log + approvals manifest, never from this wave-plan file) "
            "-- two independent computations of the same projection agreeing is the real "
            "cross-consumer proof, not merely each one summing to 900 internally.",
        "dok.waves, dok.assessment_feeding":
            "dok-workflow/dok_wave_plan.json (waves, assessment_feeding_lessons)",
        "visuals.{absent,essential,supporting,decorative,tikz_regenerable,source_pdf_required,"
        "irreplaceable_photo,needs_teacher_confirmation}":
            "visuals/visual_asset_classification.json (rows[], summary{})",
        "visuals.broken_path":
            "Derived: visuals/broken_path_repair.json (fixes[] grouped by lesson for the per-lesson "
            "count, count for the total); cross-checked per-lesson and in total against "
            "content_readiness_inventory.json (lessons[].visuals_broken_path, "
            "aggregate.total_visuals_broken_path_all_lessons). All 7 are in lesson 3-5 today as a "
            "data fact, not a hardcoded rule.",
        "collisions.{groups,dok_conflict,prompt_drift}":
            "review-queue/collision_review_queue.json (groups[], meta{}) joined against "
            "dok-workflow/dok_wave_plan.json per-id dok values (queue has no dok field itself)",
        "prereqs.{upstream_dangling,downstream_dangling}":
            "course-map/course_map.json (dropped_edges[]); upstream_dangling = edges whose TARGET "
            "touches this lesson and whose reason is in the gap family {frontload-gap, "
            "retirement-gap, retired-missing} (i.e. not assessment-forward-ref); downstream_dangling "
            "= edges whose SOURCE touches this lesson, any reason. Filtered by reason SET, not a "
            "single hardcoded label, so relabeling within the gap family (e.g. the frontload-gap -> "
            "retirement-gap split for 4-1) does not require a code change.",
        "ws6_state, readiness_ws6 distribution":
            "Derived per lesson (this script's derive_ws6_state, per the WS6 precedence rule locked "
            "by the manager brief; see SPEC.md section 2) from four source signals: "
            "content_readiness_inventory.json (lessons[].readiness, lessons[].dok_status.calibrated, "
            "lessons[].registry_rows); this script's own wave-plan-derived per-lesson verified count "
            "(NT7 R3b -- single-sourced from dok-workflow/dok_wave_plan.json's review_state, NOT "
            "lessons[].dok_status.verified); and course-map/course_map.json "
            "(topics[].lessons[].readiness). Not a hardcoded per-lesson lookup.",
        "four_one_stranded":
            "topic-4-1/inventory-4-1-assets.json (assets{}, teacher_judgment_items[]) joined "
            "against course-map/course_map.json (dropped_edges[], filtered by TARGET touching 4-1 "
            "and reason in the gap family {frontload-gap, retirement-gap, retired-missing} — "
            "currently all 4 read reason=='retirement-gap', since 4-1 was built then retired, not "
            "front-of-year-unbuilt; the 5th gap-family edge targets 3-1 instead, with "
            "reason=='frontload-gap', and is reported separately as "
            "fifth_frontload_gap_edge_into_3_1). Derived live from current dropped_edges, robust to "
            "reason relabeling.",
    }

    # -------------------------------------------------------------------
    # Final document
    # -------------------------------------------------------------------
    generated_at = datetime.now(timezone.utc).isoformat()

    doc = {
        "generated_by": "WS6 Sonnet implementer (build_content_readiness.py)",
        "generated_at": generated_at,
        "method": "Computed read-only from six signed-off WS inputs; no source modified.",
        "source_artifacts": [
            {"path": "inventory/content_readiness_inventory.json",
             "role": "Base per-lesson join spine: SE/TE presence, registry rows, answers, "
                     "visuals-absent/broken split, DOK-status totals, readiness enum (37 lessons)."},
            {"path": "inventory/dok-workflow/dok_wave_plan.json",
             "role": "900-row DOK review-wave assignment (waves 0-4) per item id, plus the "
                     "assessment-feeding lesson set (4-3, 4-5, 6-4)."},
            {"path": "inventory/review-queue/collision_review_queue.json",
             "role": "85 duplicate-legacy-id collision groups (5-1/5-4/5-5) with diff + "
                     "merge-recommendation confidence; no DOK field of its own."},
            {"path": "inventory/visuals/visual_asset_classification.json",
             "role": "137 visually-absent registry rows classified by importance, "
                     "recoverability, and teacher-confirmation need."},
            {"path": "inventory/visuals/broken_path_repair.json",
             "role": "7 repairable broken image paths, all in lesson 3-5, with proposed fixes."},
            {"path": "inventory/topic-4-1/inventory-4-1-assets.json",
             "role": "4-1 stranded-asset diagnosis: staged calibration/screenshots/skeleton "
                     "vs. 0 registry rows and no SE/TE source; 3 teacher-judgment items."},
            {"path": "inventory/course-map/course_map.json",
             "role": "6-topic/37-lesson course map: per-lesson items, 193 resolved edges, "
                     "18 dropped (dangling) prereq/rehearses/echoes edges."},
        ],
        "aggregates": aggregates,
        "readiness_reconciliation": readiness_reconciliation,
        "lessons": lessons_out,
        "dok_conflict_subset": dok_conflict_subset,
        "four_one_stranded": four_one_stranded,
        "provenance": provenance,
    }

    # -------------------------------------------------------------------
    # Self-verification (locked reconciliation targets from manager brief)
    # -------------------------------------------------------------------
    checks = []

    def check(name, actual, expected):
        ok = actual == expected
        checks.append((name, actual, expected, ok))

    check("sum(registry_rows)", total_registry_rows, 900)
    # NT10 named pin update (c1) per DOK_VERIFICATION_WORKFLOW.md step 3(c),
    # 2026-07-22: dok.verified 0 -> 39 (RC's 39 lesson-5-4 rule-1 batch
    # confirmations, the first canonical verified set |S|). All 39 rows'
    # BASE bucket was 'unreviewed', so the displayed unreviewed total drops
    # 437 -> 398 (verified rows LEAVE their base bucket in displayed totals
    # -- see the workflow doc's "What totals change" section); known_auto
    # (421) and calibrated (42) are untouched, and the ws6 pinned
    # distribution is UNCHANGED (no Wave-0/3-5 row verified -- (c2) not
    # triggered).
    check("dok.known_auto", dok_totals["known_auto"], 421)
    check("dok.unreviewed", dok_totals["unreviewed"], 398)
    check("dok.calibrated", dok_totals["calibrated"], 42)
    check("dok.verified", dok_totals["verified"], 39)
    # NT7 cross-consumer coherence gate (count-level): the wave plan's
    # canonical review_state projection total and the base inventory's OWN
    # canonical dok_status.verified total must agree. The rubric approval
    # landed at NT8 (v0.2, 2026-07-20T19:06:13-04:00) and the first real
    # post-approval recordings at NT10 (2026-07-22); whenever new reviews
    # verify items in the wave plan, this pair of checks fails loudly until
    # the base inventory rebuild is ALSO done, in the documented order --
    # it is not possible for this dashboard to silently drift out of sync
    # with the wave plan's verification state.
    check(
        "dok.wave_plan_verified_equals_base_inventory_verified",
        wave_plan_review_state_totals["verified"] == base_dok_verified_total,
        True,
    )

    # -------------------------------------------------------------------
    # NT7 R3b: PER-ITEM UID-SET GATE (replaces the old zero hard-pin
    # check("dok.wave_plan_verified_rows", ..., 0)). A count-based zero-pin
    # only proves a COUNT is zero; it would not catch two DIFFERENT item_uids
    # becoming verified while the total count coincidentally matched, or the
    # wrong uid being promoted. Coherence must be gated per-item (identity),
    # not by count, per the Fable-locked design.
    #
    # Three independent computations of "which item_uids are verified" must
    # agree, uid-for-uid, everywhere:
    #   (1) base_verified_uids -- content_readiness_inventory.json's own
    #       aggregate.dok_verified_item_uids, computed by ITS builder from
    #       registry + alias-map + review log + approvals manifest,
    #       independently of this script.
    #   (2) wave_plan_verified_uids_all -- built earlier in this script,
    #       directly from iterating dok_wave_plan.json's 900 rows via the
    #       fail-closed wave_plan_item_review_state() helper.
    #   (3) dashboard_published_verified_uids -- the union of every
    #       per-lesson verified-uid set actually folded into THIS script's
    #       own published lessons_out[*].dok.verified counts above, i.e.
    #       what this dashboard is telling a reader is verified, not merely
    #       what it read.
    # The gate is exercised at the identity level on whatever the current
    # verified set is (first nonempty set: NT10's 39 lesson-5-4 uids) --
    # it is impossible for this dashboard to publish a verified item_uid
    # that the base inventory or the wave plan itself don't also agree is
    # verified, without this failing loudly and naming the offending
    # uid(s).
    # -------------------------------------------------------------------
    base_verified_uids = set(inv["aggregate"]["dok_verified_item_uids"])
    check(
        "dok.verified_item_uid_sets_three_way "
        "(base inventory == wave plan == dashboard published, sorted lists)",
        (
            sorted(base_verified_uids) == sorted(wave_plan_verified_uids_all)
            == sorted(dashboard_published_verified_uids)
        ),
        True,
    )
    _verified_uid_sym_diff = (
        (base_verified_uids ^ wave_plan_verified_uids_all)
        | (wave_plan_verified_uids_all ^ dashboard_published_verified_uids)
        | (base_verified_uids ^ dashboard_published_verified_uids)
    )
    assert not _verified_uid_sym_diff, (
        "dok verified item_uid sets diverge across base inventory / wave plan / "
        f"dashboard published tally -- symmetric-difference uid(s): {sorted(_verified_uid_sym_diff)}"
    )
    check(
        "aggregates.dok.verified == len(three-way-agreed verified uid set)",
        aggregates["dok"]["verified"], len(wave_plan_verified_uids_all),
    )
    # Two independent computations of the same review-state projection: this
    # script derives wave_plan_review_state_totals from its OWN iteration
    # over dok_wave_plan.json (above); content_readiness_inventory.json's
    # builder derives dok_review_state_totals from registry + alias-map +
    # review log + approvals manifest, never reading the wave plan file at
    # all. Equality here is the real cross-consumer proof, at build time,
    # that both independent readers of tools/dok-review/dok_review.py's
    # canonical entry_is_verified projection still agree.
    check(
        "dok.wave_plan_review_state_totals == base_inventory.dok_review_state_totals",
        aggregates["dok"]["wave_plan_review_state_totals"],
        inv["aggregate"]["dok_review_state_totals"],
    )
    # NT7-R Stage R4: the newly-published per-item review_state_uid_sets must
    # be internally consistent with wave_plan_review_state_totals -- same
    # per-row loop, but one accumulates via a Counter and the other via a
    # set-union, so this is a genuine (if today trivial) cross-check that the
    # two accumulations never silently diverge (e.g. via a duplicate
    # item_uid, which the wave plan's own 900-distinct-uids invariant rules
    # out, but this check does not simply assume that).
    check(
        "dok.review_state_uid_sets counts == wave_plan_review_state_totals "
        "(invalid-entry, reviewed_once, verified)",
        {
            "invalid-entry": len(aggregates["dok"]["review_state_uid_sets"]["invalid-entry"]),
            "reviewed_once": len(aggregates["dok"]["review_state_uid_sets"]["reviewed_once"]),
            "verified": len(aggregates["dok"]["review_state_uid_sets"]["verified"]),
        },
        {
            "invalid-entry": aggregates["dok"]["wave_plan_review_state_totals"]["invalid-entry"],
            "reviewed_once": aggregates["dok"]["wave_plan_review_state_totals"]["reviewed_once"],
            "verified": aggregates["dok"]["wave_plan_review_state_totals"]["verified"],
        },
    )

    check("wave0", wave_counts[0], 42)
    check("wave1", wave_counts[1], 4)
    check("wave2", wave_counts[2], 220)
    check("wave3", wave_counts[3], 7)
    check("wave4", wave_counts[4], 627)
    check("wave_rows_total", total_wave_rows, 900)
    check("visuals.absent", total_visuals_absent, 137)
    check("visuals.broken_path", total_visuals_broken, 7)
    check("visuals.essential", importance_totals["essential"], 14)
    check("visuals.supporting", importance_totals["supporting"], 70)
    check("visuals.decorative", importance_totals["decorative"], 53)
    check("visuals.needs_teacher_confirmation", needs_conf_total, 27)
    check("collisions.groups", total_collision_groups, 85)
    check("collisions.dok_conflict", total_dok_conflict, 22)
    check("collisions.dok_conflict_all_in_5-4",
          all(r["id"].startswith("5-4-") for r in dok_conflict_rows), True)
    q41 = next((r for r in dok_conflict_rows if r["id"] == "5-4-savvas-q41"), None)
    check("collisions.q41_dok_pair", (q41["dok_a"], q41["dok_b"]) if q41 else None, (2, 3))
    check("answers.with_evidence", answers_with_evidence_total, 529)
    check("answers.missing_all", answers_missing_total, 371)
    check("ws6.CALIBRATED", ws6_dist["CALIBRATED"], 1)
    check("ws6.INCOMPLETE", ws6_dist["INCOMPLETE"], 9)
    check("ws6.BLOCKED", ws6_dist["BLOCKED"], 1)
    check("ws6.PROVISIONAL", ws6_dist["PROVISIONAL"], 18)
    check("ws6.ABSENT", ws6_dist["ABSENT"], 8)
    check("edges.resolved", aggregates["edges"]["resolved"], 193)
    check("edges.dropped", aggregates["edges"]["dropped"], 18)
    # Edge reason-count checks: pinned to the current course_map.json's
    # edges_dropped_by_reason (a sibling workstream re-cut the dropped-edge
    # taxonomy, splitting the old single frontload-gap==5 bucket into
    # frontload-gap==1 (into 3-1, genuinely front-of-year) + the new
    # retirement-gap==4 (into 4-1, built-then-retired)). aggregates["edges"]
    # itself is derived generically from edges_dropped_by_reason (see
    # aggregates assembly above), so these checks guard against the
    # underlying course-map numbers silently drifting again, not against
    # the derivation logic (which has no hardcoded reason list left to break).
    check("edges.frontload_gap", aggregates["edges"].get("frontload_gap", 0), 1)
    check("edges.retirement_gap", aggregates["edges"].get("retirement_gap", 0), 4)
    check("edges.retired_missing", aggregates["edges"].get("retired_missing", 0), 1)
    check("edges.assessment_forward_ref", aggregates["edges"].get("assessment_forward_ref", 0), 12)
    check("four_one.dangling_into_4-1_count", len(dangling_into_4_1), 4)
    check("four_one.dangling_into_3-1_count", len(dangling_into_3_1), 1)
    # rc-merge-auth-5-4-2026-07-23: dual-denominator identity.
    check("identity_reconciliation.raw_registry_identities", aggregates["identity_reconciliation"]["raw_registry_identities"], 900)
    check("identity_reconciliation.merged_alias_identities", aggregates["identity_reconciliation"]["merged_alias_identities"], 22)
    check("identity_reconciliation.active_canonical_items", aggregates["identity_reconciliation"]["active_canonical_items"], 878)

    print("=" * 78)
    print("RECONCILIATION CHECK RESULTS")
    print("=" * 78)
    all_pass = True
    for name, actual, expected, ok in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{status}] {name}: computed={actual!r} expected={expected!r}")
        if name == "dok.verified" and not ok:
            print(
                "    -> DELIBERATE FROZEN-BASELINE PIN, not a bug: dok.verified is pinned "
                "to 0 on purpose (see inventory/dok-workflow/DOK_VERIFICATION_WORKFLOW.md, "
                "\"Approval procedure (operational, named updates)\", step 3(c1)). When the "
                "canonical verified count first rises above 0, update the literal 0 in "
                "check(\"dok.verified\", dok_totals[\"verified\"], 0) to N per step 3(c1) -- "
                "this failure means that step was skipped, not that the pin is wrong."
            )
    print("=" * 78)
    if not all_pass:
        fail("one or more reconciliation checks failed — see above")
    print("ALL RECONCILIATION CHECKS PASS")
    print("=" * 78)

    # -------------------------------------------------------------------
    # Write content_readiness.json
    # -------------------------------------------------------------------
    out_json_path = HERE / "content_readiness.json"
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_json_path}")

    # -------------------------------------------------------------------
    # Build HTML dashboard (self-contained)
    # -------------------------------------------------------------------
    html = build_html(doc)
    out_html_path = HERE / "content_readiness_dashboard.html"
    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {out_html_path}")

    return doc


def build_html(doc):
    data_json = json.dumps(doc, ensure_ascii=False)
    # Escape </script> sequences so the inlined JSON can't break out of its block.
    data_json_safe = data_json.replace("</", "<\\/")

    template = HTML_TEMPLATE
    template = template.replace("__CR_DATA_JSON__", data_json_safe)
    template = template.replace("__GENERATED_AT__", doc["generated_at"])
    return template


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Content Readiness Dashboard &mdash; Algebra 2 (37 lessons)</title>
<style>
  :root {
    --bg: #f4f5f7;
    --panel: #ffffff;
    --text: #1b1f24;
    --muted: #55606b;
    --border: #d7dce1;
    --accent: #2456a6;
    --green: #2e7d32;
    --green-bg: #e5f3e6;
    --amber: #a86800;
    --amber-bg: #fdf1d8;
    --red: #c62828;
    --red-bg: #fbe4e4;
    --grey: #616161;
    --grey-bg: #eceeef;
    --code-bg: #eef0f3;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #14171b;
      --panel: #1d2126;
      --text: #e7ebef;
      --muted: #9aa5b1;
      --border: #333a42;
      --accent: #7aa2e3;
      --green: #6fcf7a;
      --green-bg: #16321a;
      --amber: #f0b93d;
      --amber-bg: #3a2c0c;
      --red: #ef7070;
      --red-bg: #3a1414;
      --grey: #aab2ba;
      --grey-bg: #262b31;
      --code-bg: #262b31;
    }
  }
  :root[data-theme="dark"] {
    --bg: #14171b; --panel: #1d2126; --text: #e7ebef; --muted: #9aa5b1; --border: #333a42;
    --accent: #7aa2e3; --green: #6fcf7a; --green-bg: #16321a; --amber: #f0b93d;
    --amber-bg: #3a2c0c; --red: #ef7070; --red-bg: #3a1414; --grey: #aab2ba;
    --grey-bg: #262b31; --code-bg: #262b31;
  }
  :root[data-theme="light"] {
    --bg: #f4f5f7; --panel: #ffffff; --text: #1b1f24; --muted: #55606b; --border: #d7dce1;
    --accent: #2456a6; --green: #2e7d32; --green-bg: #e5f3e6; --amber: #a86800;
    --amber-bg: #fdf1d8; --red: #c62828; --red-bg: #fbe4e4; --grey: #616161;
    --grey-bg: #eceeef; --code-bg: #eef0f3;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    max-width: 100%; overflow-x: hidden;
  }
  .wrap { max-width: 1400px; margin: 0 auto; padding: 20px 20px 60px; }
  header h1 { font-size: 1.5rem; margin: 0 0 4px; }
  header .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 18px; }
  code { background: var(--code-bg); padding: 1px 5px; border-radius: 4px; font-size: 0.85em; }

  .kpi-row {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px; margin-bottom: 24px;
  }
  .kpi {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px;
  }
  .kpi .num { font-size: 1.6rem; font-weight: 700; }
  .kpi .label { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
  .kpi .src { font-size: 0.68rem; color: var(--muted); margin-top: 6px; }

  section { margin-bottom: 30px; }
  h2 { font-size: 1.15rem; border-bottom: 1px solid var(--border); padding-bottom: 6px; }

  .topic-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;
  }
  .topic-card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px;
  }
  .topic-card h3 { margin: 0 0 6px; font-size: 0.95rem; }
  .topic-card .row { display: flex; justify-content: space-between; font-size: 0.8rem; margin: 2px 0; }

  .controls { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; align-items: center; }
  .controls input[type="text"], .controls select {
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 6px 10px; font-size: 0.9rem;
  }
  .table-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }
  table { border-collapse: collapse; width: 100%; min-width: 980px; font-size: 0.85rem; }
  thead th {
    position: sticky; top: 0; background: var(--panel); border-bottom: 1px solid var(--border);
    text-align: left; padding: 8px 10px; cursor: pointer; user-select: none; white-space: nowrap;
  }
  thead th:hover { color: var(--accent); }
  tbody td { padding: 6px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
  tbody tr:hover { background: var(--grey-bg); }

  .pill {
    display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600;
  }
  .pill.CALIBRATED { background: var(--green-bg); color: var(--green); }
  .pill.INCOMPLETE { background: var(--amber-bg); color: var(--amber); }
  .pill.BLOCKED { background: var(--red-bg); color: var(--red); }
  .pill.PROVISIONAL { background: var(--grey-bg); color: var(--grey); }
  .pill.ABSENT { background: var(--grey-bg); color: var(--grey); }

  .cell-dim {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 22px; border-radius: 5px; font-weight: 700; font-size: 0.75rem;
    margin-right: 3px;
  }
  .cell-dim.green { background: var(--green-bg); color: var(--green); }
  .cell-dim.amber { background: var(--amber-bg); color: var(--amber); }
  .cell-dim.red { background: var(--red-bg); color: var(--red); }
  .cell-dim.grey { background: var(--grey-bg); color: var(--grey); }

  .legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 0.8rem; margin: 8px 0 14px; color: var(--muted); }
  .legend span.cell-dim { margin-right: 6px; }

  .blockers { font-size: 0.78rem; color: var(--muted); }
  .blockers ul { margin: 0; padding-left: 16px; }

  .panel {
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px;
  }
  .panel + .panel { margin-top: 14px; }
  .panel h3 { margin-top: 0; }
  .panel p.note { color: var(--muted); font-size: 0.85rem; }

  .conflict-table td, .conflict-table th { padding: 4px 10px; font-size: 0.82rem; }
  .edge-list { font-size: 0.82rem; }
  .edge-list li { margin-bottom: 4px; }

  footer { color: var(--muted); font-size: 0.75rem; margin-top: 30px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Content Readiness Dashboard &mdash; Algebra 2 (37 lessons)</h1>
    <div class="meta">
      Generated __GENERATED_AT__ &middot;
      Computed read-only from six signed-off WS inputs; no source modified. &middot;
      Offline, self-contained (no network calls).
    </div>
  </header>

  <section id="kpi-section">
    <div class="kpi-row" id="kpiRow"></div>
  </section>

  <section>
    <h2>Topic rollups</h2>
    <div class="topic-grid" id="topicGrid"></div>
  </section>

  <section>
    <h2>Per-lesson readiness matrix</h2>
    <div class="controls">
      <input type="text" id="filterText" placeholder="Filter by lesson or title&hellip;">
      <select id="filterState">
        <option value="">All WS6 states</option>
        <option value="CALIBRATED">CALIBRATED</option>
        <option value="INCOMPLETE">INCOMPLETE</option>
        <option value="BLOCKED">BLOCKED</option>
        <option value="PROVISIONAL">PROVISIONAL</option>
        <option value="ABSENT">ABSENT</option>
      </select>
    </div>
    <div class="legend" id="legend"></div>
    <div class="table-scroll">
      <table id="lessonTable">
        <thead>
          <tr>
            <th data-key="lesson">Lesson</th>
            <th data-key="topic">Topic</th>
            <th data-key="title">Title</th>
            <th data-key="registry_rows">Rows</th>
            <th data-key="ws6_state">WS6 State</th>
            <th data-key="dim_content">Content</th>
            <th data-key="dim_answers">Answers</th>
            <th data-key="dim_dok">DOK</th>
            <th data-key="dim_visuals">Visuals</th>
            <th data-key="dim_prereqs">Prereqs</th>
            <th data-key="blockers">Top Blocker(s)</th>
          </tr>
        </thead>
        <tbody id="lessonBody"></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Synthesis</h2>
    <div class="panel">
      <h3>DOK-conflict collisions (higher priority than prompt-drift)</h3>
      <p class="note" id="dokConflictNote"></p>
      <div class="table-scroll">
        <table class="conflict-table" id="dokConflictTable">
          <thead><tr>
            <th>Legacy ID</th>
            <th>DOK (copy A)</th><th>item_uid (copy A)</th><th>registry_line (copy A)</th>
            <th>DOK (copy B)</th><th>item_uid (copy B)</th><th>registry_line (copy B)</th>
            <th>Merge status (rc-merge-auth-5-4-2026-07-23)</th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
    <div class="panel">
      <h3>4-1 stranded blocker</h3>
      <p class="note" id="fourOneState"></p>
      <div id="fourOneStaged"></div>
      <p><strong>Dangling edges into 4-1 (dependency-gap family: frontload-gap / retirement-gap / retired-missing):</strong></p>
      <ul class="edge-list" id="fourOneEdges"></ul>
      <p><strong>5th gap-family edge, frontload-gap (into 3-1, not 4-1):</strong></p>
      <ul class="edge-list" id="fourOneFifthEdge"></ul>
      <p><strong>Teacher-judgment items:</strong></p>
      <ul class="edge-list" id="fourOneJudgment"></ul>
    </div>
  </section>

  <footer>
    Data inlined below (client-side rendering only, vanilla JS). Source: content_readiness.json (same generation run).
  </footer>
</div>

<script id="cr-data" type="application/json">__CR_DATA_JSON__</script>
<script>
(function () {
  var raw = document.getElementById('cr-data').textContent;
  var DATA = JSON.parse(raw);

  var DIM_GLYPH = { green: 'OK', amber: '!', red: 'X', grey: '-' };
  var DIM_LABEL = { green: 'Green', amber: 'Amber', red: 'Red', grey: 'Grey (n/a)' };

  function dimCell(status) {
    var span = document.createElement('span');
    span.className = 'cell-dim ' + status;
    span.title = DIM_LABEL[status] || status;
    span.textContent = DIM_GLYPH[status] || '?';
    return span;
  }

  // ---------------- KPI row ----------------
  function renderKpis() {
    var agg = DATA.aggregates;
    var kpis = [
      { num: agg.total_registry_rows, label: 'Registry rows total', src: 'content_readiness_inventory.json' },
      { num: agg.dok.known_auto + ' / ' + agg.dok.unreviewed + ' / ' + agg.dok.calibrated + ' / ' + agg.dok.verified,
        label: 'DOK auto / unreviewed / calibrated / verified', src: 'dok_wave_plan.json' },
      { num: agg.visuals.absent + ' absent + ' + agg.visuals.broken_path + ' broken',
        label: 'Visual assets missing', src: 'visual_asset_classification.json' },
      { num: agg.collisions.groups + ' (' + agg.collisions.dok_conflict + ' DOK-conflict)',
        label: 'Collision groups', src: 'collision_review_queue.json' },
      { num: '4-1 STRANDED', label: 'Staged, not ingested', src: 'inventory-4-1-assets.json' },
      { num: agg.readiness_ws6.PROVISIONAL, label: 'Front-of-year blocked (PROVISIONAL)', src: 'course_map.json' }
    ];
    var row = document.getElementById('kpiRow');
    kpis.forEach(function (k) {
      var div = document.createElement('div');
      div.className = 'kpi';
      div.innerHTML = '<div class="num">' + k.num + '</div><div class="label">' + k.label +
        '</div><div class="src">source: ' + k.src + '</div>';
      row.appendChild(div);
    });
  }

  // ---------------- Topic rollups ----------------
  function renderTopics() {
    var byTopic = {};
    DATA.lessons.forEach(function (l) {
      byTopic[l.topic] = byTopic[l.topic] || { lessons: [], states: {} };
      byTopic[l.topic].lessons.push(l.lesson);
      byTopic[l.topic].states[l.ws6_state] = (byTopic[l.topic].states[l.ws6_state] || 0) + 1;
    });
    var grid = document.getElementById('topicGrid');
    Object.keys(byTopic).sort(function (a, b) { return a - b; }).forEach(function (t) {
      var card = document.createElement('div');
      card.className = 'topic-card';
      var states = byTopic[t].states;
      var rows = Object.keys(states).sort().map(function (s) {
        return '<div class="row"><span>' + s + '</span><span>' + states[s] + '</span></div>';
      }).join('');
      card.innerHTML = '<h3>Topic ' + t + ' (' + byTopic[t].lessons.length + ' lessons)</h3>' + rows;
      grid.appendChild(card);
    });
  }

  // ---------------- Legend ----------------
  function renderLegend() {
    var legend = document.getElementById('legend');
    ['green', 'amber', 'red', 'grey'].forEach(function (s) {
      var wrap = document.createElement('span');
      wrap.appendChild(dimCell(s));
      var label = document.createElement('span');
      label.textContent = DIM_LABEL[s];
      wrap.appendChild(label);
      legend.appendChild(wrap);
    });
  }

  // ---------------- Lesson table ----------------
  var sortKey = 'lesson';
  var sortDir = 1;

  function rowMatches(l, textFilter, stateFilter) {
    if (stateFilter && l.ws6_state !== stateFilter) return false;
    if (!textFilter) return true;
    var hay = (l.lesson + ' ' + (l.title || '')).toLowerCase();
    return hay.indexOf(textFilter.toLowerCase()) !== -1;
  }

  function sortVal(l, key) {
    switch (key) {
      case 'dim_content': return l.dimension_status.content;
      case 'dim_answers': return l.dimension_status.answers;
      case 'dim_dok': return l.dimension_status.dok;
      case 'dim_visuals': return l.dimension_status.visuals;
      case 'dim_prereqs': return l.dimension_status.prereqs;
      case 'blockers': return (l.top_blockers || []).join('; ');
      default: return l[key];
    }
  }

  function renderTable() {
    var textFilter = document.getElementById('filterText').value.trim();
    var stateFilter = document.getElementById('filterState').value;
    var rows = DATA.lessons.filter(function (l) { return rowMatches(l, textFilter, stateFilter); });
    rows.sort(function (a, b) {
      var va = sortVal(a, sortKey), vb = sortVal(b, sortKey);
      if (va < vb) return -1 * sortDir;
      if (va > vb) return 1 * sortDir;
      return 0;
    });
    var body = document.getElementById('lessonBody');
    body.innerHTML = '';
    rows.forEach(function (l) {
      var tr = document.createElement('tr');

      var tdLesson = document.createElement('td'); tdLesson.textContent = l.lesson;
      var tdTopic = document.createElement('td'); tdTopic.textContent = l.topic;
      var tdTitle = document.createElement('td'); tdTitle.textContent = l.title || '(untitled placeholder)';
      var tdRows = document.createElement('td'); tdRows.textContent = l.registry_rows;
      var tdState = document.createElement('td');
      var pill = document.createElement('span');
      pill.className = 'pill ' + l.ws6_state;
      pill.textContent = l.ws6_state;
      tdState.appendChild(pill);

      var tdContent = document.createElement('td'); tdContent.appendChild(dimCell(l.dimension_status.content));
      var tdAnswers = document.createElement('td'); tdAnswers.appendChild(dimCell(l.dimension_status.answers));
      var tdDok = document.createElement('td'); tdDok.appendChild(dimCell(l.dimension_status.dok));
      var tdVisuals = document.createElement('td'); tdVisuals.appendChild(dimCell(l.dimension_status.visuals));
      var tdPrereqs = document.createElement('td'); tdPrereqs.appendChild(dimCell(l.dimension_status.prereqs));

      var tdBlockers = document.createElement('td');
      tdBlockers.className = 'blockers';
      if (l.top_blockers && l.top_blockers.length) {
        var ul = document.createElement('ul');
        l.top_blockers.forEach(function (b) {
          var li = document.createElement('li');
          li.textContent = b;
          ul.appendChild(li);
        });
        tdBlockers.appendChild(ul);
      } else {
        tdBlockers.textContent = '(none)';
      }

      [tdLesson, tdTopic, tdTitle, tdRows, tdState, tdContent, tdAnswers, tdDok, tdVisuals, tdPrereqs, tdBlockers]
        .forEach(function (td) { tr.appendChild(td); });
      body.appendChild(tr);
    });
  }

  function wireControls() {
    document.getElementById('filterText').addEventListener('input', renderTable);
    document.getElementById('filterState').addEventListener('change', renderTable);
    document.querySelectorAll('#lessonTable thead th').forEach(function (th) {
      th.addEventListener('click', function () {
        var key = th.getAttribute('data-key');
        if (sortKey === key) { sortDir *= -1; } else { sortKey = key; sortDir = 1; }
        renderTable();
      });
    });
  }

  // ---------------- Synthesis panels ----------------
  function renderDokConflict() {
    var sub = DATA.dok_conflict_subset;
    document.getElementById('dokConflictNote').textContent =
      sub.count + ' groups, all in lesson ' + sub.all_in_lesson + '. ' + sub.note;
    var tbody = document.querySelector('#dokConflictTable tbody');
    sub.rows.forEach(function (r) {
      var tr = document.createElement('tr');
      var mergeStatus = r.merged_alias_item_uid
        ? ('ALIAS: <code>' + r.merged_alias_item_uid + '</code> &rarr; survivor <code>' + r.survivor_item_uid + '</code>')
        : '(unresolved)';
      tr.innerHTML =
        '<td><code>' + r.id + '</code></td>' +
        '<td>DOK ' + r.dok_a + '</td><td><code>' + r.uid_a + '</code></td><td>' + r.line_a + '</td>' +
        '<td>DOK ' + r.dok_b + '</td><td><code>' + r.uid_b + '</code></td><td>' + r.line_b + '</td>' +
        '<td>' + mergeStatus + '</td>';
      tbody.appendChild(tr);
    });
  }

  function renderFourOne() {
    var f = DATA.four_one_stranded;
    document.getElementById('fourOneState').textContent =
      'State: ' + f.state + ' &mdash; staged calibration=' + f.staged.calibration +
      ', screenshots=' + f.staged.screenshots + ', skeleton stubs=' + f.staged.skeleton_stubs +
      ', registry rows=' + f.staged.registry_rows + ', SE/TE source present=' + f.staged.se_te;
    var stagedDiv = document.getElementById('fourOneStaged');
    stagedDiv.innerHTML = '';

    var edgesUl = document.getElementById('fourOneEdges');
    f.dangling_edges_into_4_1.forEach(function (e) {
      var li = document.createElement('li');
      li.innerHTML = '<code>' + e.source + '</code> &rarr; <code>' + e.target + '</code> (' + e.type + ', ' + e.reason + ')';
      edgesUl.appendChild(li);
    });

    var fifthUl = document.getElementById('fourOneFifthEdge');
    var e5 = f.fifth_frontload_gap_edge_into_3_1;
    var li5 = document.createElement('li');
    li5.innerHTML = '<code>' + e5.source + '</code> &rarr; <code>' + e5.target + '</code> (' + e5.type + ', ' + e5.reason + ')';
    fifthUl.appendChild(li5);

    var judgUl = document.getElementById('fourOneJudgment');
    f.teacher_judgment_items.forEach(function (item) {
      var li = document.createElement('li');
      li.textContent = item;
      judgUl.appendChild(li);
    });
  }

  renderKpis();
  renderTopics();
  renderLegend();
  wireControls();
  renderTable();
  renderDokConflict();
  renderFourOne();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
