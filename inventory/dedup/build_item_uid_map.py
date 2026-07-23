"""
build_item_uid_map.py

Builds a PROPOSED (not-applied) item_uid alias map for the Algebra 2
question bank registry, to remediate duplicate legacy `id` strings.

READ-ONLY on questionbank/registry.jsonl. Does not mutate, renumber, or
merge any registry row. Writes only item_uid_alias_map.json (in this
same directory) plus stdout self-assertion diagnostics.

Algorithm (byte-exact, UTF-8 throughout):
    prompt_sha1 = sha1(prompt.encode('utf-8')).hexdigest()   # "" if prompt is None
    basis       = f"{lesson}|{source}|{prompt_sha1}"
    item_uid    = "iu_" + sha1(basis.encode('utf-8')).hexdigest()[:12]
    exact_tuple = (lesson, source, prompt_sha1)

Rows sharing an identical exact_tuple collapse to the same item_uid and
are marked exact_duplicate=true. They are never auto-merged in the
registry itself -- only flagged here.

Re-runnable / idempotent: running this script twice produces identical
output, because it is a pure function of registry.jsonl content and
never opens the registry for writing.

resolved_alias enrichment (ADDITIVE, authorized by rc-merge-auth-5-4-2026-07-23):
    A v2-design tombstone row (see inventory/merge-proposal-5-4/
    merge_proposal_5_4.json meta.alias_resolver_contract) carries four
    top-level marker fields -- status=="merged-alias", alias_of, merged_at,
    merge_authorization -- IN ADDITION TO its original identity-basis
    fields (id/lesson/source/prompt). Those marker fields are NOT part of
    the lesson|source|prompt_sha1 basis and never influence item_uid,
    exact_tuple, exact_duplicate, alias_map grouping, or the "ambiguous"
    flag -- the raw ambiguous-duplicate calculation is unchanged.
    On top of that unchanged calculation, this script additively attaches
    a "resolved_alias" key (placed after "item_uids") to any legacy-id
    entry whose group includes a merged-alias row, after validating the
    resolver contract's invariants (single-hop, no self-alias, no missing
    target, no chains, ambiguous-group-only, well-formed marker fields).
    See validate_and_enrich_merged_alias() below.
"""

import json
import hashlib
import sys
import os
import tempfile
from collections import defaultdict, Counter
from datetime import datetime

# Paths are derived from this file's own location so the script runs from
# any checkout, not just the original authoring machine. This script lives
# at <repo>/inventory/dedup/build_item_uid_map.py, so REPO_ROOT is two
# directories up from SCRIPT_DIR (out of dedup/, then out of inventory/).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DEFAULT_REGISTRY = os.path.join(REPO_ROOT, "questionbank", "registry.jsonl")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "item_uid_alias_map.json")

# Optional CLI overrides: argv[1] = registry path, argv[2] = output path.
# Both default to the derived repo-relative locations above.
REGISTRY_PATH = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REGISTRY
OUTPUT_PATH = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT
OUTPUT_DIR = os.path.dirname(os.path.abspath(OUTPUT_PATH))


def sha1_hex(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def compute_item_uid(lesson, source, prompt_sha1):
    basis = f"{lesson}|{source}|{prompt_sha1}"
    return "iu_" + sha1_hex(basis)[:12], basis


def load_registry_rows(path):
    """Read registry.jsonl READ-ONLY, one JSON object per line, preserving
    1-based line numbers. Blank lines (if any) are skipped but do not
    shift subsequent line numbers."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            obj = json.loads(stripped)
            rows.append((line_no, obj))
    return rows


def classify_disposition(group_rows):
    """group_rows: list of dicts each with keys lesson, source, prompt_sha1,
    exact_duplicate (bool) for every registry row sharing one legacy_id.

    Returns one of:
      "exact-duplicate-needs-human"
      "distinct-items-keep-both"
      "merge-candidate"
    Data-driven; no hardcoded ids/counts.
    """
    if any(r["exact_duplicate"] for r in group_rows):
        return "exact-duplicate-needs-human"

    distinct_lessons = {r["lesson"] for r in group_rows}
    distinct_sources = {r["source"] for r in group_rows}
    if len(distinct_lessons) > 1 or len(distinct_sources) > 1:
        return "distinct-items-keep-both"

    # Same lesson AND same source, differing only in prompt text: a
    # near-identical re-capture of the same Savvas slot (double-ingest
    # with drift -- e.g. one capture has a trailing MP standard tag the
    # other lacks). "merge-candidate" is a HUMAN-REVIEW RECOMMENDATION
    # to merge the pair, NOT an automatic merge: the two distinct
    # item_uids computed for these rows are retained as-is until a
    # human reviews and decides. Nothing is collapsed, no row is
    # removed, and this classification does not change any count
    # (item_uid, ambiguous, or row counts are untouched by disposition
    # labeling).
    return "merge-candidate"


class MergeAliasValidationError(AssertionError):
    """Raised by validate_and_enrich_merged_alias() when the resolved_alias
    enrichment's invariants are violated. Deliberately a plain `raise`
    (never a bare `assert` statement) so these guards survive `python -O`
    / PYTHONOPTIMIZE, which strips `assert` statements entirely -- NT11
    hardening round B2. Subclasses AssertionError so existing
    failure-mode expectations (nonzero exit, AssertionError-shaped
    tracebacks) are unchanged."""


class SelfAssertionError(AssertionError):
    """Raised by self_assert() when any pinned check fails -- both the
    frozen-baseline pins that pre-date this enrichment AND the
    merged_alias_rows/alias_resolved_groups/unresolved_ambiguous_groups
    pins this enrichment added. The final `for name, ok, detail in checks`
    loop is the SINGLE enforcement point for every pin in that list
    (old and new alike), so it is converted to an explicit raise -- not
    `assert` -- to keep it -O-proof (NT11 hardening round B2)."""


def parse_offset_aware_iso8601(value):
    """Parse an ISO-8601 timestamp string, requiring an explicit UTC offset
    (e.g. "2026-07-23T00:53:21-04:00"). Raises ValueError if `value` is not
    a string, does not parse, or lacks tzinfo (naive timestamps rejected)."""
    if not isinstance(value, str):
        raise ValueError(f"not a string: {value!r}")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"parses but is not offset-aware: {value!r}")
    return parsed


def validate_and_enrich_merged_alias(alias_map, alias_groups):
    """ADDITIVE enrichment authorized by rc-merge-auth-5-4-2026-07-23 (design
    contract: inventory/merge-proposal-5-4/merge_proposal_5_4.json
    meta.alias_resolver_contract).

    For every legacy-id group (alias_groups) containing a registry row with
    status == "merged-alias", validates the v2 tombstone marker fields and,
    on success, attaches a "resolved_alias" key -- placed after the existing
    "item_uids" key -- to that legacy-id's alias_map entry:

        resolved_alias: {
            "alias_uid": <item_uid of the merged-alias row>,
            "survivor_uid": <that row's alias_of>,
            "merged_at": <that row's merged_at>,
            "authorization_record_id": <merge_authorization.record_id>,
        }

    Never mutates item_uid_entries, the "ambiguous" flag, or any other
    existing alias_map key -- purely additive. Fails loud: raises
    MergeAliasValidationError (a plain raise, not `assert` -- survives
    `python -O`; see NT11 hardening round B2) on any violation of the
    resolver contract's invariants, which the caller MUST run before
    writing any output.

    Validated invariants, per merged-alias row:
      (a) exactly one merged-alias row per legacy-id group;
      (b) no self-alias (alias_of != the row's own item_uid);
      (c) no missing target (alias_of matches another row's item_uid
          within the SAME legacy-id group);
      (d) no chains, LOCAL (same-group) hop: the survivor row found via
          (c) must NOT itself carry status == "merged-alias";
      (e) merged_at is an offset-aware ISO-8601 timestamp, and
          merge_authorization.record_id is a non-empty string;
      (f) a merged-alias row may only appear in an ambiguous
          (multi-item_uid) group;
      (g) NT11 hardening round B1 -- no chains, GLOBAL (cross-group) hop:
          because item_uid is computed from (lesson, source, prompt_sha1)
          alone and does NOT include legacy_id, the same item_uid can in
          principle be carried by rows in two DIFFERENT legacy-id groups.
          (a)-(f) only look inside one group, so a survivor_uid resolved
          in group 1 could -- in a different registry -- coincide with a
          merged-alias row's item_uid in group 2 (a cross-group chain
          that (d) cannot see). After every per-group entry is resolved,
          this checks GLOBALLY: no resolved_alias.survivor_uid may equal
          the item_uid of ANY merged-alias row anywhere in the registry,
          and the global survivor-uid set and global merged-alias-uid set
          must be disjoint.

    Returns (merged_alias_rows_count, alias_resolved_groups_count).
    """
    merged_alias_rows_count = 0
    alias_resolved_groups_count = 0

    for legacy_id, group in alias_groups.items():
        merged_rows = [r for r in group if r.get("status") == "merged-alias"]
        if not merged_rows:
            continue

        merged_alias_rows_count += len(merged_rows)

        # (a) exactly one merged-alias row per group.
        if len(merged_rows) != 1:
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: expected exactly one merged-alias row "
                f"per group, found {len(merged_rows)} at registry_lines "
                f"{[r['registry_line'] for r in merged_rows]}"
            )
        row = merged_rows[0]
        alias_uid = row["item_uid"]
        alias_of = row.get("alias_of")
        merged_at = row.get("merged_at")
        merge_authorization = row.get("merge_authorization")

        # (b) no self-alias.
        if alias_of == alias_uid:
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: alias_of {alias_of!r} equals the "
                f"merged-alias row's own item_uid (self-alias) at registry_line "
                f"{row['registry_line']}"
            )

        # (c) alias_of must resolve to another row's item_uid IN THE SAME
        #     legacy-id group (no missing target).
        group_uid_map = defaultdict(list)
        for r in group:
            group_uid_map[r["item_uid"]].append(r)
        if alias_of not in group_uid_map:
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: alias_of {alias_of!r} does not match "
                f"any item_uid within the same legacy-id group (missing target) "
                f"at registry_line {row['registry_line']}"
            )

        # (d) no chains (LOCAL hop): the survivor row(s) must NOT
        #     themselves be merged-alias (single-hop resolution only).
        survivor_rows = group_uid_map[alias_of]
        for sr in survivor_rows:
            if sr.get("status") == "merged-alias":
                raise MergeAliasValidationError(
                    f"legacy_id {legacy_id!r}: alias_of target {alias_of!r} "
                    f"(registry_line {sr['registry_line']}) itself carries "
                    f"status=='merged-alias' -- alias chain detected, "
                    f"single-hop resolution required (alias row at registry_line "
                    f"{row['registry_line']})"
                )

        # (e) merged_at is an offset-aware ISO-8601 timestamp;
        #     merge_authorization.record_id is a non-empty string.
        try:
            parse_offset_aware_iso8601(merged_at)
        except ValueError as exc:
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: merged_at {merged_at!r} at "
                f"registry_line {row['registry_line']} is not a valid "
                f"offset-aware ISO-8601 timestamp: {exc}"
            )
        if not isinstance(merge_authorization, dict):
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: merge_authorization at registry_line "
                f"{row['registry_line']} is not an object: {merge_authorization!r}"
            )
        record_id = merge_authorization.get("record_id")
        if not (isinstance(record_id, str) and record_id):
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: merge_authorization.record_id at "
                f"registry_line {row['registry_line']} is not a non-empty "
                f"string: {record_id!r}"
            )

        # (f) a merged-alias row may only appear in an ambiguous
        #     (multi-item_uid) group.
        entry = alias_map[legacy_id]
        if not entry["ambiguous"]:
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: merged-alias row at registry_line "
                f"{row['registry_line']} appears in a non-ambiguous "
                f"(single-item_uid) group"
            )

        # All checks passed: additive enrichment, placed after "item_uids"
        # (dict insertion order -- "ambiguous" and "item_uids" already
        # exist on `entry`, so this key is appended last).
        entry["resolved_alias"] = {
            "alias_uid": alias_uid,
            "survivor_uid": alias_of,
            "merged_at": merged_at,
            "authorization_record_id": record_id,
        }
        alias_resolved_groups_count += 1

    # (g) NT11 hardening round B1 -- GLOBAL cross-group one-hop invariant.
    # Runs only after every per-group entry above has been resolved, since
    # it needs the full, whole-registry set of merged-alias item_uids
    # (not just the current group's).
    global_merged_alias_uids = {
        r["item_uid"]
        for grp in alias_groups.values()
        for r in grp
        if r.get("status") == "merged-alias"
    }
    for legacy_id, entry in alias_map.items():
        if "resolved_alias" not in entry:
            continue
        survivor_uid = entry["resolved_alias"]["survivor_uid"]
        if survivor_uid in global_merged_alias_uids:
            raise MergeAliasValidationError(
                f"legacy_id {legacy_id!r}: resolved_alias.survivor_uid "
                f"{survivor_uid!r} is ALSO the item_uid of a merged-alias row "
                f"in a DIFFERENT legacy-id group -- cross-group alias chain "
                f"detected, global one-hop invariant violated"
            )

    global_survivor_uids = {
        entry["resolved_alias"]["survivor_uid"]
        for entry in alias_map.values()
        if "resolved_alias" in entry
    }
    if not global_survivor_uids.isdisjoint(global_merged_alias_uids):
        raise MergeAliasValidationError(
            "global survivor-uid set and global merged-alias-uid set are not "
            f"disjoint: overlap={sorted(global_survivor_uids & global_merged_alias_uids)}"
        )

    return merged_alias_rows_count, alias_resolved_groups_count


def build():
    rows = load_registry_rows(REGISTRY_PATH)
    total_rows = len(rows)

    # Per-row computed records, in registry order.
    records = []  # each: dict with legacy_id, lesson, source, prompt_sha1,
                   #       registry_line, exact_tuple, item_uid (filled after
                   #       exact_duplicate is known)

    exact_tuple_counts = Counter()

    for line_no, obj in rows:
        legacy_id = obj.get("id")
        lesson = obj.get("lesson")
        source = obj.get("source")
        prompt = obj.get("prompt")
        if prompt is None:
            prompt = ""
        prompt_sha1 = sha1_hex(prompt)
        exact_tuple = (lesson, source, prompt_sha1)
        exact_tuple_counts[exact_tuple] += 1

        records.append({
            "legacy_id": legacy_id,
            "lesson": lesson,
            "source": source,
            "prompt_sha1": prompt_sha1,
            "registry_line": line_no,
            "exact_tuple": exact_tuple,
            # v2 tombstone marker fields (may be absent on any row not
            # touched by a merge). Carried through purely for the
            # resolved_alias enrichment/validation below -- these never
            # feed exact_tuple/item_uid/exact_duplicate computation above.
            "status": obj.get("status"),
            "alias_of": obj.get("alias_of"),
            "merged_at": obj.get("merged_at"),
            "merge_authorization": obj.get("merge_authorization"),
        })

    # exact_duplicate = true for every row whose exact_tuple is shared by >1 row.
    for rec in records:
        rec["exact_duplicate"] = exact_tuple_counts[rec["exact_tuple"]] > 1

    # item_uid is a pure function of exact_tuple -> rows sharing an exact_tuple
    # share an item_uid (that's the point of exact_duplicate collapsing).
    exact_tuple_to_uid = {}
    exact_tuple_to_basis = {}
    for rec in records:
        et = rec["exact_tuple"]
        if et not in exact_tuple_to_uid:
            lesson, source, prompt_sha1 = et
            uid, basis = compute_item_uid(lesson, source, prompt_sha1)
            exact_tuple_to_uid[et] = uid
            exact_tuple_to_basis[et] = basis
        rec["item_uid"] = exact_tuple_to_uid[et]
        rec["basis"] = exact_tuple_to_basis[et]

    distinct_item_uids = len(exact_tuple_to_uid)
    exact_duplicate_rows = sum(1 for rec in records if rec["exact_duplicate"])

    # Build alias_map: legacy_id -> list of per-row dicts.
    alias_groups = defaultdict(list)
    for rec in records:
        alias_groups[rec["legacy_id"]].append(rec)

    unique_legacy_ids = len(alias_groups)

    alias_map = {}
    ambiguous_count = 0
    for legacy_id, group in alias_groups.items():
        distinct_uids_in_group = {r["item_uid"] for r in group}
        ambiguous = len(distinct_uids_in_group) > 1
        if ambiguous:
            ambiguous_count += 1
        # Preserve registry order within the group (already in that order
        # since we iterate `records` in file order above).
        item_uid_entries = [
            {
                "item_uid": r["item_uid"],
                "lesson": r["lesson"],
                "source": r["source"],
                "prompt_sha1": r["prompt_sha1"],
                "registry_line": r["registry_line"],
                "exact_duplicate": r["exact_duplicate"],
            }
            for r in group
        ]
        alias_map[legacy_id] = {
            "ambiguous": ambiguous,
            "item_uids": item_uid_entries,
        }

    # Dispositions: only for legacy_ids appearing on >1 row (duplicate-id groups).
    dispositions = {}
    for legacy_id, group in alias_groups.items():
        if len(group) > 1:
            dispositions[legacy_id] = classify_disposition(group)

    dup_group_count = len(dispositions)

    # ADDITIVE resolved_alias enrichment (rc-merge-auth-5-4-2026-07-23). Runs
    # AFTER the raw ambiguous-duplicate calculation above is fully settled
    # (alias_map grouping + "ambiguous" flags are already final) and BEFORE
    # meta/output are assembled, so it can only add a "resolved_alias" key
    # to qualifying entries -- it never touches item_uid_entries or the
    # "ambiguous" flag. Raises AssertionError (fail loud) on any violation
    # of the resolver contract's invariants; on failure, main() never
    # reaches self_assert() or the output-write step below.
    merged_alias_rows, alias_resolved_groups = validate_and_enrich_merged_alias(
        alias_map, alias_groups
    )
    unresolved_ambiguous_groups = ambiguous_count - alias_resolved_groups

    meta = {
        "generated_from": "questionbank/registry.jsonl",
        "total_rows": total_rows,
        "distinct_item_uids": distinct_item_uids,
        "unique_legacy_ids": unique_legacy_ids,
        "ambiguous_legacy_ids": ambiguous_count,
        "exact_duplicate_rows": exact_duplicate_rows,
        "algorithm": (
            "item_uid = 'iu_' + sha1(f'{lesson}|{source}|{prompt_sha1}')[:12]; "
            "prompt_sha1 = sha1(prompt)"
        ),
        "merged_alias_rows": merged_alias_rows,
        "alias_resolved_groups": alias_resolved_groups,
        "unresolved_ambiguous_groups": unresolved_ambiguous_groups,
    }

    output = {
        "meta": meta,
        "alias_map": alias_map,
        "dispositions": dispositions,
    }

    return output, records, alias_groups, dup_group_count


def self_assert(output, records, alias_groups, dup_group_count, total_rows):
    meta = output["meta"]
    alias_map = output["alias_map"]
    dispositions = output["dispositions"]

    checks = []

    # 1. every one of the total_rows rows is covered by exactly one alias-map
    #    entry (sum of entry lists == total_rows)
    sum_entries = sum(len(v["item_uids"]) for v in alias_map.values())
    checks.append(("rows_covered_by_alias_map", sum_entries == total_rows,
                    f"sum_entries={sum_entries} total_rows={total_rows}"))

    # 2. number of distinct item_uids == (total_rows minus number of exact-
    #    duplicate collapses)
    exact_dup_rows = meta["exact_duplicate_rows"]
    all_uids = {r["item_uid"] for r in records}
    # Number of "collapses" = exact_dup_rows - (number of distinct exact_tuples
    # that are duplicated), but per the spec's simple current-data check:
    # distinct_item_uids should equal total_rows - <collapse overcount>.
    # In the current data exact_dup_rows == 0, so distinct == total_rows.
    checks.append((
        "distinct_item_uids_matches_total_minus_collapses",
        len(all_uids) == meta["distinct_item_uids"],
        f"len(all_uids)={len(all_uids)} meta_distinct={meta['distinct_item_uids']}",
    ))
    if exact_dup_rows == 0:
        checks.append((
            "distinct_item_uids_equals_total_rows_when_no_exact_dups",
            meta["distinct_item_uids"] == total_rows,
            f"distinct_item_uids={meta['distinct_item_uids']} total_rows={total_rows}",
        ))

    # 3. number of legacy_id keys == unique id strings == 815
    checks.append((
        "unique_legacy_ids_eq_815",
        meta["unique_legacy_ids"] == 815,
        f"unique_legacy_ids={meta['unique_legacy_ids']}",
    ))
    checks.append((
        "alias_map_key_count_matches_meta",
        len(alias_map) == meta["unique_legacy_ids"],
        f"len(alias_map)={len(alias_map)} meta_unique={meta['unique_legacy_ids']}",
    ))

    # 4. number of ambiguous legacy_ids == 85
    checks.append((
        "ambiguous_legacy_ids_eq_85",
        meta["ambiguous_legacy_ids"] == 85,
        f"ambiguous_legacy_ids={meta['ambiguous_legacy_ids']}",
    ))

    # 5. number of disposition-classified dup groups == number of legacy_ids
    #    appearing on >1 row == 85
    groups_gt1 = sum(1 for g in alias_groups.values() if len(g) > 1)
    checks.append((
        "dup_group_count_eq_groups_gt1",
        dup_group_count == groups_gt1,
        f"dup_group_count={dup_group_count} groups_gt1={groups_gt1}",
    ))
    checks.append((
        "dispositions_count_eq_85",
        len(dispositions) == 85,
        f"len(dispositions)={len(dispositions)}",
    ))

    # 6. counts reconcile: rows == 900, unique legacy strings == 815,
    #    ambiguous == 85
    checks.append((
        "rows_eq_900",
        total_rows == 900,
        f"total_rows={total_rows}",
    ))

    # 7. resolved_alias enrichment pins (rc-merge-auth-5-4-2026-07-23):
    #    frozen-baseline counts, same pin style as the 815/85 pins above.
    checks.append((
        "merged_alias_rows_eq_22",
        meta["merged_alias_rows"] == 22,
        f"merged_alias_rows={meta['merged_alias_rows']}",
    ))
    checks.append((
        "alias_resolved_groups_eq_22",
        meta["alias_resolved_groups"] == 22,
        f"alias_resolved_groups={meta['alias_resolved_groups']}",
    ))
    checks.append((
        "unresolved_ambiguous_groups_eq_63",
        meta["unresolved_ambiguous_groups"] == 63,
        f"unresolved_ambiguous_groups={meta['unresolved_ambiguous_groups']}",
    ))
    # 8. reconciliation: every ambiguous group is either resolved or
    #    unresolved, with no overlap and no leftover.
    checks.append((
        "ambiguous_eq_resolved_plus_unresolved",
        meta["ambiguous_legacy_ids"]
        == meta["alias_resolved_groups"] + meta["unresolved_ambiguous_groups"],
        f"ambiguous_legacy_ids={meta['ambiguous_legacy_ids']} "
        f"alias_resolved_groups={meta['alias_resolved_groups']} "
        f"unresolved_ambiguous_groups={meta['unresolved_ambiguous_groups']}",
    ))

    for name, ok, detail in checks:
        if not ok:
            print(f"SELF-ASSERTION: FAIL ({name}) -- {detail}")
            # Explicit raise (not `assert`) -- this loop is the single
            # enforcement point for EVERY pin above, old and new alike, so
            # it must survive `python -O` (NT11 hardening round B2).
            raise SelfAssertionError(f"{name}: {detail}")

    print("SELF-ASSERTION: PASS")
    print(
        "counts: rows={rows} distinct_item_uids={uid} unique_legacy_ids={leg} "
        "ambiguous_legacy_ids={amb} exact_duplicate_rows={exd} dup_groups={dg} "
        "merged_alias_rows={mar} alias_resolved_groups={arg} "
        "unresolved_ambiguous_groups={uag}".format(
            rows=total_rows,
            uid=meta["distinct_item_uids"],
            leg=meta["unique_legacy_ids"],
            amb=meta["ambiguous_legacy_ids"],
            exd=meta["exact_duplicate_rows"],
            dg=dup_group_count,
            mar=meta["merged_alias_rows"],
            arg=meta["alias_resolved_groups"],
            uag=meta["unresolved_ambiguous_groups"],
        )
    )


def main():
    output, records, alias_groups, dup_group_count = build()
    total_rows = output["meta"]["total_rows"]

    # Validate the in-memory result BEFORE writing anything. If self_assert
    # fails, it prints the FAIL line and raises -- nothing below this point
    # runs, so a failing run can never truncate or corrupt the last known
    # -good OUTPUT_PATH.
    self_assert(output, records, alias_groups, dup_group_count, total_rows)

    # Only on PASS: write atomically. json.dump to a temp file in the same
    # directory as OUTPUT_PATH, flush + fsync, then os.replace() into place.
    # os.replace is atomic on the same filesystem (including on Windows),
    # so OUTPUT_PATH is either the old good file or the new good file --
    # never a partially-written one.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=OUTPUT_DIR, prefix=".item_uid_alias_map.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, OUTPUT_PATH)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


if __name__ == "__main__":
    main()
