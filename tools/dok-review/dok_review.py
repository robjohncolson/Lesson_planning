#!/usr/bin/env python3
"""dok_review.py -- local, testable DOK-verification review tool.

Reads THREE FROZEN, READ-ONLY inputs and never writes to any of them:
  - inventory/dok-workflow/dok_wave_plan.json  (the review queue + item metadata)
  - questionbank/registry.jsonl                (the source-of-truth question bank)
  - questionbank/calibration/*.json            (Savvas-anchor provenance sources)

Writes exactly two things, both inside its own directory:
  - tools/dok-review/review_log.jsonl          (append-only; one JSON object
                                                 per review decision)
  - tools/dok-review/rubric_approvals.json     (edited by hand by a human,
                                                 NEVER by this tool -- see the
                                                 "Rubric-approvals manifest"
                                                 section below)

Identity rule (non-negotiable): every operation is keyed by `item_uid`, the
opaque primary key from the wave plan. The legacy `id` field is DISPLAY-ONLY --
85 legacy ids are each shared by two distinct registry rows/item_uids (e.g.
`5-4-savvas-q41` is both iu_3c70a19c8d36, wave 3, dok 3, role dok3-driver AND
iu_77d25e1e6131, wave 4, dok 2, role None). Reviewing one must never affect
the other. Never key any lookup, grouping, or counting off `id` alone.

Append-only invariant: review_log.jsonl is only ever opened in "a" mode. A
re-review of the same item_uid is a NEW line with a later reviewed_at; the
LATEST line in file order (append order, not sorted by timestamp) wins for
"latest entry per item_uid" display purposes (queue/progress/report). Full
CHAIN order (every line for a uid, in append order) is what `promote`
re-validates against disk -- see "Promotion: re-derives against disk" below.

`promote` never opens registry.jsonl in a write mode -- it only reads the one
row identified by the frozen registry_line join and emits a proposal JSON
file elsewhere. It never modifies the registry. `promote` stays proposals-only
regardless of rubric state.

-------------------------------------------------------------------------------
DOK Acceptance Rubric v0.2 -- two-tier model (see
inventory/decision-console/DOK_RUBRIC_v0.2.md for the full authority hierarchy)
-------------------------------------------------------------------------------

This tool tracks TWO distinct tiers, and they are not the same thing:

  REVIEWED  -- a log entry exists for the item_uid with a non-empty
              reviewed_by AND a non-empty, parseable reviewed_at, a
              recognized `decision`, and (for change) a valid new_dok
              (tool_state "reviewed_once" -- the state name is kept from the
              prior version of this tool, but it now denotes the rubric's
              REVIEWED tier, nothing more). A reviewer having looked at an
              item and recorded *something well-formed* is REVIEWED. It is
              NOT, by itself, VERIFIED. A latest entry that fails even this
              baseline well-formedness bar is "invalid-entry" (see below) --
              NOT "reviewed_once".

  VERIFIED  -- strictly stronger than REVIEWED. An entry is VERIFIED only
              when `entry_is_verified()` returns True -- see that function's
              docstring for the exact predicate. In prose: the entry must be
              well-formed, carry a resolved verification-grade disposition
              (a confirm with resolved calibration provenance, or a complete
              change whose item_basis-appropriate provenance requirement is
              met), have no unresolved needs-source-check anywhere earlier in
              its item_uid's chain, AND be stamped with a rubric_version that
              (a) appears in the rubric-approvals manifest, and (b) whose
              tool-generated recorded_at is not earlier than that version's
              approved_at.

  Rubric-approvals manifest (rubric_approvals.json) -- NO retroactive
  verification. DOK rubric v0.2 was PROPOSED, then APPROVED by a teacher
  effective 2026-07-20T19:06:13-04:00 (see `rubric_approvals.json`'s single
  entry). Any FUTURE rubric version remains PROPOSED, not approved, until a
  teacher approves it in turn -- see DOK_RUBRIC_v0.2.md: "no review-log
  entry of any kind may be recorded under it, and nothing ... may be
  described as having a recorded verified status" until then. This tool's
  position (see README.md "Doc honesty" section for the full statement): a
  review-log entry MAY be recorded before a rubric version's approval
  (recording is permitted and useful for getting reviews done in parallel
  with the approval process), but it can NEVER become VERIFIED under that
  version until a teacher approves it, AND -- this is the retroactivity
  guard -- even after approval, an entry recorded BEFORE the approval
  timestamp never converts to VERIFIED. It remains a REVIEWED-tier record
  forever and must be RE-REVIEWED (a new log entry, with a new recorded_at,
  after approval) to become eligible. `rubric_approvals.json` in this
  directory now ships with exactly one entry -- v0.2, approved_at
  2026-07-20T19:06:13-04:00 -- hand-edited in by a human after the real
  teacher approval; this tool never writes to it. The VERIFIED count is
  whatever the log + manifest compute at read time (run `progress` for the
  current number) -- the first post-approval recordings landed 2026-07-22
  (NT10: RC's 39 lesson-5-4 batch confirmations), retiring the earlier
  zero-entries state. See
  `load_rubric_approvals()` for the fail-closed loading rules, and
  `_approved_versions_override` (TEST-ONLY -- see that name's docstring) for
  how tests simulate a DIFFERENT approval state (e.g. a hypothetical future
  version, or "nothing approved") without touching the manifest or a module
  constant. `approvals_path` (also threaded through every function below,
  from the CLI's `--approvals` flag) lets a caller point at a DIFFERENT
  on-disk manifest instead -- still real disk I/O, just not the default
  file.

  Disposition semantics (rubric "surviving v0.1 mechanics"):
    - confirm               -- reviewer agrees with the wave-plan's prior_dok.
                                reviewer_dok = prior_dok, new_dok = None.
                                `--provenance` optional; `confirmation_basis`
                                is derived (see `build_review_record`):
                                  * empty provenance -> "rule-2-adjacent-unsourced"
                                  * non-empty but does not resolve on disk ->
                                    "rule-2-adjacent-unsourced-claim"
                                  * resolves on disk (see `resolve_provenance`)
                                    -> "rule-1-textbook-provenance"
                                Only the last is verification-grade.
    - change                -- reviewer overrides the prior_dok with a chosen
                                DOK (1-3 only; DOK 4 is not assignable on this
                                platform and does not appear in the bank).
                                reviewer_dok = new_dok = chosen_dok. Requires
                                BOTH --rationale and --provenance (rule 5),
                                and REQUIRES --item-basis (rule 3: is this a
                                source-dispute resolution -- textbook-exact --
                                or an actual-cognitive-demand item -- adapted /
                                split / extended / teacher-authored?).
                                item_basis == "textbook-exact" is
                                verification-grade ONLY when the provenance
                                resolves on disk; the other bases are
                                verification-grade with free-text provenance,
                                provided rationale+provenance are non-empty.
    - needs-source-check    -- terminal-unresolved (rule 2): reviewer_dok =
                                new_dok = None. Requires --rationale (every
                                disagreement needs one). Never verified by
                                itself. Resolved ONLY by a LATER entry for the
                                same item_uid that stamps BOTH
                                `resolves_source_check: true` AND provenance
                                that resolves on disk (`--resolves-source-check`,
                                see `_chain_pending_nsc_states`). A plain later
                                confirm/change WITHOUT that attestation does
                                NOT resolve it -- the item stays permanently
                                un-verifiable (`prior_unresolved_nsc: true`)
                                until the explicit attestation appears.

  DOK measures cognitive demand, not difficulty (rubric rule 4): a long,
  multi-part, or computationally hard item is not automatically higher DOK
  than a short, easy one. See DOK_NOT_DIFFICULTY_NOTE below, echoed verbatim
  in the CLI epilogs and README.md.

  Reject-at-entry: every `review` invocation is fully validated BEFORE
  append_review is ever called -- see `_validate_review_args` plus the
  timestamp/monotonicity checks in `cmd_review`. Any validation failure
  prints an ERROR to stderr, exits nonzero, and appends NOTHING to the log --
  there is no code path that can append a partial or invalid record.

  Promotion: re-derives against disk. `build_promotion_proposal` does NOT
  trust any stamp on the log entries it reads (`provenance_resolved`,
  `confirmation_basis`, `prior_unresolved_nsc`, ...) as authoritative by
  itself -- it walks the FULL entry chain for the item_uid, re-validates
  every entry structurally, RE-DERIVES provenance resolution live against
  the calibration directory for every confirm/textbook-exact-change/
  resolves_source_check entry, RE-DERIVES the needs-source-check chain state,
  and finally re-asserts `entry_is_verified()` on the latest entry as the
  single authoritative gate. Contrast this with the "display" tier (queue,
  progress, report) which DOES trust the stamps written at review time --
  those are fast, cheap, offline views; only `promote` re-verifies against
  disk before proposing a change a human might act on.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths. Derived from __file__ so no absolute user path is ever hardcoded.
# Script lives at <repo>/tools/dok-review/dok_review.py.
# ---------------------------------------------------------------------------

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parent.parent

DEFAULT_PLAN = REPO_ROOT / "inventory" / "dok-workflow" / "dok_wave_plan.json"
DEFAULT_REGISTRY = REPO_ROOT / "questionbank" / "registry.jsonl"
DEFAULT_CALIBRATION_DIR = REPO_ROOT / "questionbank" / "calibration"
DEFAULT_LOG = TOOL_DIR / "review_log.jsonl"
DEFAULT_PROPOSALS_DIR = TOOL_DIR / "proposals"
DEFAULT_REPORT = TOOL_DIR / "review_report.html"
DEFAULT_APPROVALS = TOOL_DIR / "rubric_approvals.json"

WAVE_KEYS = ["0", "1", "2", "3", "4"]
TOOL_STATES = ("unreviewed", "invalid-entry", "reviewed_once", "verified")
DISPOSITIONS = ("confirm", "change", "needs-source-check")
VALID_CHOSEN_DOKS = (1, 2, 3)  # DOK domain is 1-3 on this platform; 4 is rejected.
ITEM_BASES = ("textbook-exact", "adapted", "split", "extended", "teacher-authored")

# Rubric rule 4, VERBATIM (NT6 round 3, G5) -- copied from
# inventory/decision-console/DOK_RUBRIC_v0.2.md's Authority Hierarchy, rule
# 4, with ONLY the list numbering ("4. "), the bold ** markers, and the
# source markdown's hard line-wraps (each replaced by a single space)
# stripped. No paraphrase, no added/removed words. This exact sentence must
# appear verbatim in the top-level CLI --help epilog, the `review`
# subcommand's --help epilog, and README.md -- a tool-specific sentence may
# FOLLOW it (clearly separated, e.g. "(Rubric rule 4, verbatim.) Tool note:
# ..."), but nothing may be blended INTO the quote itself.
DOK_NOT_DIFFICULTY_NOTE = (
    "DOK measures cognitive demand, not difficulty. A long, multi-part, or "
    "context-heavy item is not automatically higher DOK than a short one, "
    "and a computationally hard item is not automatically higher DOK than "
    "an easy one. DOK tracks the kind of thinking required (recall vs. "
    "procedure vs. strategic reasoning vs. extended investigation), never "
    "how hard, how long, or how error-prone the item is to complete."
)


# ---------------------------------------------------------------------------
# Small shared helpers.
# ---------------------------------------------------------------------------

def parse_iso(value):
    """Strict ISO-8601 parse via datetime.fromisoformat. Returns a datetime,
    or None on ANY failure (wrong type, empty, unparseable, OR NAIVE). No
    fuzzy parsing, no fallback formats -- a value that fromisoformat rejects
    is simply not a valid timestamp for this tool's purposes.

    SINGLE TIMESTAMP POLICY (NT6 round 3, G2): every instant this tool
    reads or writes must be OFFSET-AWARE. A naive datetime (no UTC offset --
    `tzinfo is None` or `utcoffset() is None`) parses to None here, exactly
    like a malformed string. This is deliberate and flows everywhere this
    function is used: entry validation (`entry_is_malformed`, chain
    validation), monotonicity checks, chain order validation, the
    rubric-approvals manifest (`approved_at`), and the retroactivity gate
    (`recorded_at` vs. `approved_at`). Rejecting naive datetimes AT PARSE
    TIME is what makes every later ordering comparison between two
    `parse_iso(...)` results safe to perform -- Python raises TypeError when
    comparing a naive and an aware datetime, and this policy makes that
    comparison unreachable by construction (see also the defensive
    try/except TypeError guards at each comparison site, kept as
    defense-in-depth rather than as the primary safeguard)."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _nonempty_str(value):
    """True iff value is a string with non-whitespace content. Used
    everywhere this module used to do bare truthiness on a string field
    (reviewed_by, rationale, provenance, ...) -- strip-based, not just
    truthy, so a whitespace-only value is correctly treated as empty."""
    return isinstance(value, str) and bool(value.strip())


# ---------------------------------------------------------------------------
# Rubric-approvals manifest (rubric_approvals.json). See module docstring's
# "Rubric-approvals manifest" section for the model. This tool NEVER writes
# to this file -- a human edits it by hand after a real teacher approval.
# ---------------------------------------------------------------------------

def load_rubric_approvals(path=None):
    """Load and validate the rubric-approvals manifest.

    Returns {version(str): approved_at(datetime)}.

    FAIL CLOSED: a missing file returns {} (silently -- a missing manifest
    just means "no approvals recorded yet", not an error). Any OTHER problem
    -- malformed JSON, an unexpected top-level shape (not a dict, or
    "approvals" not a list), a non-dict approval entry, a non-string or
    empty `version`, an `approved_at` that is missing/not-a-string/
    unparseable, or the SAME `version` string appearing MORE THAN ONCE in
    "approvals" (NT6 round 3, G4) -- prints ONE warning line to stderr and
    returns {} for the WHOLE manifest (not a best-effort partial parse). A
    single malformed entry poisons the whole load; this tool would rather
    treat everything as unapproved than guess at a partially-valid manifest.
    The duplicate-version check exists because a duplicate could otherwise
    let an earlier (looser) `approved_at` for the same version silently win
    or lose depending on list order, moving the effective approval boundary
    backward without anyone intending it.
    """
    manifest_path = Path(path) if path is not None else DEFAULT_APPROVALS

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        print(
            f"WARNING: rubric approvals manifest at {manifest_path} is malformed "
            f"JSON ({exc}) -- treating as NO approvals",
            file=sys.stderr,
        )
        return {}

    if not isinstance(raw, dict) or not isinstance(raw.get("approvals"), list):
        print(
            f"WARNING: rubric approvals manifest at {manifest_path} has an "
            "unexpected shape (expected an object with an 'approvals' list) "
            "-- treating as NO approvals",
            file=sys.stderr,
        )
        return {}

    result = {}
    for entry in raw["approvals"]:
        if not isinstance(entry, dict):
            print(
                f"WARNING: rubric approvals manifest at {manifest_path} has a "
                "non-object approval entry -- treating as NO approvals",
                file=sys.stderr,
            )
            return {}

        version = entry.get("version")
        if not isinstance(version, str) or not version.strip():
            print(
                f"WARNING: rubric approvals manifest at {manifest_path} has an "
                "approval entry with a non-string/empty version -- treating as "
                "NO approvals",
                file=sys.stderr,
            )
            return {}

        approved_at = parse_iso(entry.get("approved_at"))
        if approved_at is None:
            print(
                f"WARNING: rubric approvals manifest at {manifest_path} has an "
                f"unparseable approved_at for version {version!r} -- treating "
                "as NO approvals",
                file=sys.stderr,
            )
            return {}

        if version in result:
            print(
                f"WARNING: rubric approvals manifest at {manifest_path} has "
                f"version {version!r} more than once in 'approvals' -- "
                "treating as NO approvals (a duplicate could move the "
                "effective approval boundary backward)",
                file=sys.stderr,
            )
            return {}

        result[version] = approved_at

    return result


def _resolve_approved_versions(_approved_versions_override=None, approvals_path=None):
    """Resolve the effective {version: approved_at datetime} mapping.

    `_approved_versions_override` is TEST-ONLY. When None (the only way any
    `cmd_*` production entry point ever calls this), the manifest is loaded
    from disk via `load_rubric_approvals(approvals_path)` -- by default the
    real `rubric_approvals.json` (which now ships with one entry: v0.2,
    approved_at 2026-07-20T19:06:13-04:00), or whatever `approvals_path`
    points at when given. `approvals_path` is threaded down from the CLI's
    `--approvals` flag (default `DEFAULT_APPROVALS`) through every
    verification-aware function; no `cmd_*` function ever passes a non-None
    `_approved_versions_override` -- grep the module for
    `_approved_versions_override=` to confirm. When a test passes a
    non-None dict of {version: datetime-or-ISO-string} as
    `_approved_versions_override`, it is normalized (ISO strings parsed via
    `parse_iso`) and used INSTEAD of any on-disk manifest, to simulate a
    DIFFERENT approval state without ever touching a manifest file or a
    module constant. `approvals_path` is ignored whenever
    `_approved_versions_override` is not None.
    """
    if _approved_versions_override is None:
        return load_rubric_approvals(approvals_path)
    normalized = {}
    for version, approved_at in _approved_versions_override.items():
        if isinstance(approved_at, str):
            normalized[version] = parse_iso(approved_at)
        else:
            normalized[version] = approved_at
    return normalized


# ---------------------------------------------------------------------------
# Read-only data loading (wave plan + registry + calibration).
# ---------------------------------------------------------------------------

def load_plan(path):
    """Read the frozen wave plan. Read-only; never opened for writing."""
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def load_registry_line(path, line_no):
    """Return the parsed JSON object at 1-based line_no in the registry JSONL
    file, or None if that line doesn't exist / is blank. Read-only; never
    opened for writing."""
    with open(Path(path), "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if i == line_no:
                line = line.strip()
                return json.loads(line) if line else None
    return None


def iter_queue_items(plan):
    """Yield (wave, lesson, item) in wave-plan authoritative order: waves
    '0'..'4', lessons in stored dict order, items in stored list order."""
    waves = plan["waves"]
    for wave in WAVE_KEYS:
        lessons = waves.get(wave, {})
        for lesson, items in lessons.items():
            for item in items:
                yield wave, lesson, item


def build_uid_index(plan):
    """Return (uid_to_item, uid_to_registry_line, duplicate_uids).

    uid_to_item values are shallow copies of the plan item augmented with
    'wave' and 'lesson' (needed to build a review record). duplicate_uids
    lists any item_uid seen more than once -- should be empty for a
    well-formed plan (900 distinct item_uids); checked defensively by
    `promote` before it ever proposes a change.
    """
    uid_to_item = {}
    uid_to_line = {}
    seen_counts = {}
    for wave, lesson, item in iter_queue_items(plan):
        uid = item["item_uid"]
        seen_counts[uid] = seen_counts.get(uid, 0) + 1
        augmented = dict(item)
        augmented["wave"] = wave
        augmented["lesson"] = lesson
        uid_to_item[uid] = augmented
        uid_to_line[uid] = item["registry_line"]
    duplicates = [uid for uid, count in seen_counts.items() if count > 1]
    return uid_to_item, uid_to_line, duplicates


def build_id_index(plan):
    """Legacy id -> list of item_uids sharing that id. Demonstrates why the
    legacy `id` is ambiguous as a lookup key (e.g. '5-4-savvas-q41' maps to
    two distinct item_uids)."""
    id_to_uids = {}
    for _wave, _lesson, item in iter_queue_items(plan):
        id_to_uids.setdefault(item["id"], []).append(item["item_uid"])
    return id_to_uids


# ---------------------------------------------------------------------------
# review_log.jsonl: read (any code path) and write (review command only).
# ---------------------------------------------------------------------------

def read_log_entries(path):
    """Read all entries from the append-only log, in file order.

    FAIL CLOSED, mirroring load_rubric_approvals()'s policy for the
    rubric-approvals manifest EXACTLY (same shape, deliberately): a MISSING
    file means "no reviews yet" and returns [] silently -- not an error,
    and it is NOT created by reading. Any OTHER structural problem -- the
    file exists but cannot be read (OSError/UnicodeDecodeError), a line
    that fails json.loads, a parsed line that is not a JSON object (a
    list, string, number, bool, or null instead of a dict), or a parsed
    dict whose "item_uid" is not a non-empty (stripped) string -- prints
    ONE warning line to stderr naming the path and the FIRST defect found,
    and returns [] for the WHOLE log. This is deliberately NOT a
    best-effort partial parse: one poisoned line poisons the whole log,
    exactly like load_rubric_approvals does for rubric_approvals.json --
    there is no code path here that returns some-but-not-all entries.

    WHY fail-closed and uniform across every caller: every code path in
    this module that needs "the log" -- cmd_queue, cmd_review (via
    entries_for_uid over prior_entries_for_uid), cmd_progress,
    build_promotion_proposal, build_report_html -- and every external
    consumer (gen_dok_wave_plan.py's cross-consumer projection, and any
    future downstream reader) calls this one function and must see the
    SAME log, with the SAME meaning, every time. A tool that silently
    skipped just the bad line would let a single corrupted line quietly
    hide reviews that DID happen (best-effort skip masks data loss); a
    tool that let json.JSONDecodeError or a bare KeyError/TypeError escape
    uncaught out of latest_entries_by_uid/entries_for_uid (a non-dict
    entry, or a dict with no "item_uid") would crash the whole CLI with a
    traceback instead of a clear diagnosis, or worse, let a malformed
    entry be silently misread as belonging to some accidental item_uid.
    Returning [] for the whole log is the SAFEST possible state here --
    REVIEWED/VERIFIED are additive tiers that assume nothing by default,
    so "as if nothing were reviewed yet" is always a safe under-approximation,
    never a false positive. No caller needs to change anything to inherit
    this policy: they all just call read_log_entries() and get [] (with a
    printed warning) exactly as if the log were empty.
    """
    path = Path(path)
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except (OSError, UnicodeDecodeError) as exc:
        print(
            f"WARNING: review log at {path} could not be read ({exc}) -- "
            "treating as NO review entries -- fail closed, zero verified",
            file=sys.stderr,
        )
        return []

    entries = []
    for line_no, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            print(
                f"WARNING: review log at {path} has invalid JSON on line "
                f"{line_no} ({exc}) -- treating as NO review entries -- "
                "fail closed, zero verified",
                file=sys.stderr,
            )
            return []

        if not isinstance(parsed, dict):
            print(
                f"WARNING: review log at {path} has a non-object entry on "
                f"line {line_no} (parsed as {type(parsed).__name__}, not an "
                "object) -- treating as NO review entries -- fail closed, "
                "zero verified",
                file=sys.stderr,
            )
            return []

        if not _nonempty_str(parsed.get("item_uid")):
            print(
                f"WARNING: review log at {path} has an entry on line "
                f"{line_no} with a missing or blank item_uid -- treating as "
                "NO review entries -- fail closed, zero verified",
                file=sys.stderr,
            )
            return []

        entries.append(parsed)

    return entries


def latest_entries_by_uid(entries):
    """Latest entry per item_uid, by append order (later line wins). Do NOT
    sort by reviewed_at -- append order is authoritative."""
    latest = {}
    for entry in entries:
        latest[entry["item_uid"]] = entry
    return latest


def entries_for_uid(entries, uid):
    """The FULL chain of log entries for one item_uid, in append order."""
    return [e for e in entries if e.get("item_uid") == uid]


# ---------------------------------------------------------------------------
# Rule-1 provenance: must resolve on disk against questionbank/calibration/,
# AND must be BOUND to the item actually being reviewed (NT6 round 3, G1).
#
# A provenance string no longer resolves just because SOME anchor or
# item_analysis key exists anywhere in the cited lesson's calibration file --
# it must identify the SAME item that is being reviewed. This closes the
# hole where a reviewer (or a crafted log line) could cite another item's
# anchor -- or an unrelated Savvas practice/example number in the same
# lesson -- and have it read as textbook-confirmed provenance for a
# DIFFERENT item.
# ---------------------------------------------------------------------------

_PROVENANCE_SCHEME = "calibration-anchor"
_LESSON_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# Item id -> calibration identity. Matched against the wave-plan item's
# legacy `id` field (display-only elsewhere, but here it is the ONLY signal
# this tool has for "which calibration entry, if any, is this item's own").
#
# - Savvas practice items end in "-savvas-q<N>" (e.g. "3-5-savvas-q27").
#   Split/multi-part practice ids (e.g. "4-3-savvas-q36-partA-build") do
#   NOT match -- they carry extra suffix after the number, so this pattern
#   deliberately does not bind them to a calibration identity; a split part
#   is not "the same item" as the calibration corpus's single anchor entry
#   for that practice number.
# - Worked-example ids end in "-ex-<N>" / "-ex_<N>" / "-example-<N>" (e.g.
#   "4-3-ex-1"), matching calibration's `item_analysis` keys shaped
#   "example_<N>". Anchored at the END of the id and requiring a real
#   separator between "ex"/"example" and the digits -- this is deliberately
#   conservative so RTI-support ids that merely MENTION an example number
#   (e.g. "3-5-rti-ex3-1", "3-5-rti-support-ex6-1" -- RTI material FOR
#   Example 3 / Example 6, not the example itself) do NOT false-match: those
#   ids have no separator between "ex" and the digit ("ex3", not "ex-3"), so
#   they fail this pattern by construction (verified against the real wave
#   plan -- see the test suite).
# - Anything else (try-it ids, lesson-quiz ids like "3-5-lq-q2", TE/concept-
#   box slugs, ...) has NO derivable calibration identity. Rule-1 is
#   IMPOSSIBLE for such an item under the current calibration corpus -- it
#   can only ever be rule-2-adjacent (unsourced or an unresolved claim).
_PRACTICE_ID_RE = re.compile(r"-savvas-q(\d+)$")
_EXAMPLE_ID_RE = re.compile(r"(?:^|-)ex(?:ample)?[-_](\d+)$", re.IGNORECASE)

# A resolving anchor's "source" string is expected to contain "Practice
# #<N>" somewhere (e.g. "Savvas Practice #27 (Model With Mathematics,
# lesson 3-5, anchors Example 4)"). The FIRST such match in the string is
# authoritative -- a source that also happens to mention a DIFFERENT
# example/practice number later in its prose (e.g. "... anchors Example 4")
# must never be misread as identifying that later number.
_PRACTICE_SOURCE_RE = re.compile(r"practice\s*#\s*(\d+)", re.IGNORECASE)

# --provenance item-ref shapes that normalize to a (kind, N) pair. Anchored
# start-to-end (no substring semantics): an item-ref must parse to EXACTLY
# one kind-optional number token, or it does not resolve at all -- e.g. a
# bare "a" or the bare word "practice" (no number) normalizes to None, not
# a best-effort guess.
_EXAMPLE_REF_RE = re.compile(r"^(?:example|ex)[\s_-]+(\d+)$", re.IGNORECASE)
_PRACTICE_KEYWORD_REF_RE = re.compile(r"^practice[\s_-]*#?[\s_-]*(\d+)$", re.IGNORECASE)
_Q_PREFIX_REF_RE = re.compile(r"^q[\s_-]*#?[\s_-]*(\d+)$", re.IGNORECASE)
_BARE_NUMBER_REF_RE = re.compile(r"^#?(\d+)$")


def derive_item_calibration_identity(item):
    """Return (kind, N) -- kind is "practice" or "example", N is an int --
    derived from `item`'s legacy `id` field, or None if the id carries no
    derivable calibration identity at all.

    Read-only string inspection; never touches disk. See the comment block
    above `_PRACTICE_ID_RE` for the exact id shapes recognized and why
    RTI-support ids that merely mention an example number do not
    false-match. An item with no derivable identity (try-it, lesson-quiz,
    TE/concept-box slugs, ...) can NEVER be rule-1 -- see
    `resolve_provenance`.
    """
    item_id = item.get("id")
    if not isinstance(item_id, str):
        return None
    match = _PRACTICE_ID_RE.search(item_id)
    if match:
        return ("practice", int(match.group(1)))
    match = _EXAMPLE_ID_RE.search(item_id)
    if match:
        return ("example", int(match.group(1)))
    return None


def normalize_provenance_item_ref(item_ref):
    """Return (kind_or_None, N:int) parsed from a free-form --provenance
    item-ref, or None if it does not parse to exactly one kind-optional
    number token.

    Accepted shapes (case-insensitive, whitespace-tolerant):
      - "27", "#27"                            -> (None, 27)
      - "q27"                                  -> ("practice", 27)
      - "practice #27", "practice-27",
        "practice 27"                          -> ("practice", 27)
      - "example_2", "example 2", "ex 2",
        "ex-2"                                 -> ("example", 2)

    A `kind` of None means "unspecified" -- `resolve_provenance` accepts it
    against ANY item identity kind, as long as N matches. Anything that does
    not parse to one of these shapes (a bare "a", the bare word "practice"
    with no number, free text, ...) returns None -- there is no substring or
    fuzzy fallback.
    """
    if not isinstance(item_ref, str):
        return None
    ref = item_ref.strip()
    if not ref:
        return None

    match = _EXAMPLE_REF_RE.match(ref)
    if match:
        return ("example", int(match.group(1)))

    match = _PRACTICE_KEYWORD_REF_RE.match(ref)
    if match:
        return ("practice", int(match.group(1)))

    match = _Q_PREFIX_REF_RE.match(ref)
    if match:
        return ("practice", int(match.group(1)))

    match = _BARE_NUMBER_REF_RE.match(ref)
    if match:
        return (None, int(match.group(1)))

    return None


def resolve_provenance(provenance, calibration_dir, item):
    """Return True iff `provenance` resolves to a real, on-disk calibration
    anchor that is BOUND TO `item` itself (read-only; never writes
    anything). `item` is REQUIRED (NT6 round 3, G1) -- a provenance string
    is no longer evaluated in isolation from the item it is supposed to
    source.

    Scheme: "calibration-anchor:<lesson>:<item-ref>" (split on ':',
    maxsplit=2, so <item-ref> may itself contain colons). True only when ALL
    of the following hold:

      1. `provenance` strips to non-empty and matches the scheme exactly
         (literal "calibration-anchor"); <lesson> strips to non-empty,
         matches ^[A-Za-z0-9._-]+$, and does NOT contain ".." (path-
         traversal guard -- the regex alone would allow ".." since '.' is a
         permitted character, so this is checked separately);
         <calibration_dir>/<lesson>.json exists and parses as JSON.
      2. <lesson> is EXACTLY `item["lesson"]` -- a provenance ref citing ANY
         other lesson never resolves, even a real anchor in that other
         lesson's own file.
      3. `item` has a derivable calibration identity at all (see
         `derive_item_calibration_identity`) -- try-it/lesson-quiz/TE-slug
         items have none and can NEVER resolve rule-1.
      4. <item-ref> normalizes (see `normalize_provenance_item_ref`) to a
         number equal to the item's own identity number, AND either
         specifies no kind or the SAME kind as the item's identity (an
         "example_2" ref can never bind a practice-27 item, even if the
         numbers happened to coincide).
      5. the calibration file actually CONTAINS an entry for that same
         identity: an "example" identity requires `item_analysis` to have
         key f"example_{N}"; a "practice" identity requires EITHER some
         anchor across `dok2_anchors` + `dok3_anchors` whose "source"
         string's FIRST "practice #<M>" match (case-insensitive) has
         M == N, OR (NT10, Fable-authorized semantic alignment,
         2026-07-22) the item's own number N appearing in one of the
         lesson's `item_analysis` dok<k> lists (`item_analysis` values
         shaped {example_<E>: {"dok<k>": [practice numbers]}} -- the SAME
         evidence source gen_dok_wave_plan.py's build_item_to_dok reads
         for te_bucket/match_quality). This alignment exists because a
         calibration intake may transcribe the TE Item Analysis table
         (practice-number -> DOK bucket) without adding curated
         dok2_anchors/dok3_anchors entries (lesson 5-4 is the first such
         file); the tool must accept the same textbook evidence the
         generator does. The three-way item binding above (lesson
         equality, exact number identity, an entry for that number) is
         UNCHANGED -- this only adds a second on-disk location where the
         practice number's entry may live. This is never a bare substring
         scan, and it never reads an example number out of an anchor's
         prose (an anchor sourced "... anchors Example 4" is not thereby
         a match for example_4 -- only `item_analysis` keys bind example
         identities).

    Free text, an unknown scheme, a wrong-lesson ref, an item with no
    calibration identity, an underspecified ref ("a", "practice" with no
    number), a ref for a different item/number, or a ref whose identity has
    no matching entry in the file -- ALL return False.
    """
    if not isinstance(provenance, str):
        return False
    provenance = provenance.strip()
    if not provenance:
        return False

    parts = provenance.split(":", 2)
    if len(parts) != 3:
        return False
    scheme, lesson, item_ref = parts
    if scheme != _PROVENANCE_SCHEME:
        return False

    lesson = lesson.strip()
    if not lesson or ".." in lesson or not _LESSON_RE.match(lesson):
        return False

    item_ref = item_ref.strip()
    if not item_ref:
        return False

    calibration_path = Path(calibration_dir) / f"{lesson}.json"
    if not calibration_path.exists():
        return False
    try:
        with open(calibration_path, "r", encoding="utf-8") as f:
            calibration = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return False
    if not isinstance(calibration, dict):
        return False

    if lesson != item.get("lesson"):
        return False

    identity = derive_item_calibration_identity(item)
    if identity is None:
        return False
    item_kind, item_n = identity

    parsed_ref = normalize_provenance_item_ref(item_ref)
    if parsed_ref is None:
        return False
    ref_kind, ref_n = parsed_ref
    if ref_n != item_n:
        return False
    if ref_kind is not None and ref_kind != item_kind:
        return False

    if item_kind == "example":
        item_analysis = calibration.get("item_analysis")
        return isinstance(item_analysis, dict) and f"example_{item_n}" in item_analysis

    # item_kind == "practice"
    for key in ("dok2_anchors", "dok3_anchors"):
        anchors = calibration.get(key)
        if not isinstance(anchors, list):
            continue
        for anchor in anchors:
            if not isinstance(anchor, dict):
                continue
            source = anchor.get("source")
            if not isinstance(source, str):
                continue
            source_match = _PRACTICE_SOURCE_RE.search(source)
            if source_match and int(source_match.group(1)) == item_n:
                return True

    # NT10 (Fable-authorized semantic alignment, 2026-07-22): a practice
    # identity also binds when its number appears in one of the lesson's
    # item_analysis dok<k> lists -- the SAME evidence source
    # gen_dok_wave_plan.py's build_item_to_dok reads (item_analysis values
    # shaped {"dok<k>": [practice numbers]}). All prior gates (lesson
    # equality, exact number identity vs. the item's OWN id-derived number,
    # kind match) have already passed by this point -- this only adds a
    # second on-disk location where the entry for that number may live.
    # Mirrors build_item_to_dok's reading exactly: dict-shaped example
    # buckets, keys matching ^dok\d+$, list values.
    item_analysis = calibration.get("item_analysis")
    if isinstance(item_analysis, dict):
        for buckets in item_analysis.values():
            if not isinstance(buckets, dict):
                continue
            for dok_key, numbers in buckets.items():
                if not isinstance(dok_key, str) or not re.match(r"^dok\d+$", dok_key):
                    continue
                if isinstance(numbers, list) and item_n in numbers:
                    return True

    return False


def _chain_pending_nsc_states(chain, calibration_dir, item):
    """Walk `chain` (a list of entries for ONE item_uid, oldest first) and
    return a list, aligned to `chain`, of whether an unresolved
    needs-source-check is pending AS OF AND INCLUDING each entry. `item` is
    the (augmented) wave-plan item this chain belongs to -- REQUIRED so the
    re-derived `resolve_provenance` check below stays item-bound (NT6 round
    3, G1); every entry in `chain` is for the same item_uid, so the same
    `item` applies to the whole chain.

    Single-toggle model: a `needs-source-check` entry sets pending True. A
    LATER entry that stamps `resolves_source_check` truthy AND whose
    `provenance` resolves on disk (re-derived live via `resolve_provenance`
    -- this function never trusts a stored `provenance_resolved` stamp)
    clears pending to False. Any other entry leaves pending exactly as it
    was (a generic confirm/change over an unresolved nsc does NOT resolve
    it). This same function is used both at review-entry time (to compute
    the `prior_unresolved_nsc` stamp and to validate `--resolves-source-check`)
    and at promote time (to re-derive, never trusting stamps, whether the
    chain has any unresolved needs-source-check left).
    """
    pending = False
    states = []
    for entry in chain:
        if entry.get("decision") == "needs-source-check":
            pending = True
        elif entry.get("resolves_source_check") and resolve_provenance(
            entry.get("provenance"), calibration_dir, item
        ):
            pending = False
        states.append(pending)
    return states


# ---------------------------------------------------------------------------
# VERIFIED predicate + display-tier tool_state (trusts stamps -- see module
# docstring's "Promotion: re-derives against disk" section for the contrast).
# ---------------------------------------------------------------------------

def entry_is_malformed(entry):
    """True when a latest entry doesn't clear the baseline well-formedness
    bar -- classifies tool_state as 'invalid-entry' rather than
    'reviewed_once'. This is deliberately independent of verification-grade
    status: an entry can be well-formed (not malformed) and still not
    VERIFIED (that's ordinary 'reviewed_once').

    NT6 round 3, G3: the well-formedness bar is now DECISION-SPECIFIC, not
    just the three universal fields (reviewed_by / reviewed_at / decision).
    A `change` missing rationale/provenance/a valid new_dok/a valid
    item_basis is malformed, not merely "reviewed but unverified" -- those
    are structurally incomplete records, the same bar `_validate_chain_entry`
    already holds crafted logs to at promote time. Likewise a
    `needs-source-check` missing rationale, or a `confirm` whose
    `confirmation_basis` isn't one of the three recognized values, is
    malformed."""
    if not _nonempty_str(entry.get("reviewed_by")):
        return True
    if parse_iso(entry.get("reviewed_at")) is None:
        return True
    decision = entry.get("decision")
    if decision not in DISPOSITIONS:
        return True

    if decision == "change":
        if entry.get("new_dok") not in VALID_CHOSEN_DOKS:
            return True
        if not _nonempty_str(entry.get("rationale")):
            return True
        if not _nonempty_str(entry.get("provenance")):
            return True
        if entry.get("item_basis") not in ITEM_BASES:
            return True
    elif decision == "needs-source-check":
        if not _nonempty_str(entry.get("rationale")):
            return True
    elif decision == "confirm":
        if entry.get("confirmation_basis") not in (
            "rule-1-textbook-provenance",
            "rule-2-adjacent-unsourced",
            "rule-2-adjacent-unsourced-claim",
        ):
            return True

    return False


def entry_is_verified(entry, _approved_versions_override=None, approvals_path=None):
    """VERIFIED predicate under DOK Acceptance Rubric v0.2's two-tier model.
    This is THE single authoritative predicate for "is this entry
    verification-grade" -- `build_promotion_proposal`'s final gate asserts
    this directly rather than duplicating parallel logic.

    VERIFIED only when ALL hold:
      1. reviewed_by is a non-empty (stripped) string AND reviewed_at
         parses (strict ISO-8601, `parse_iso`);
      2. the entry records a resolved, verification-grade disposition:
           - decision == "confirm" AND confirmation_basis ==
             "rule-1-textbook-provenance" (the confirm's provenance
             resolved on disk at entry time); OR
           - decision == "change" AND new_dok in {1, 2, 3} AND rationale
             non-empty AND provenance non-empty (rule 5) AND item_basis in
             ITEM_BASES AND (item_basis != "textbook-exact" OR
             provenance_resolved is True) -- a textbook-exact change is a
             source-dispute resolution and needs resolved provenance; the
             other bases are rated by actual cognitive demand and accept
             free-text provenance (rule 3);
         decision == "needs-source-check" is NEVER verified (falls through
         to the `else` branch below, terminal-unresolved per rule 2).
      3. `entry.get("prior_unresolved_nsc")` is NOT truthy -- an unresolved
         needs-source-check anywhere earlier in this item_uid's chain vetoes
         verification regardless of how clean the latest entry otherwise is
         (this is what makes a plain confirm/change over an unresolved nsc
         permanently non-verifying until an explicit
         `resolves_source_check` attestation appears).
      4. `entry.get("rubric_version")` is a key of the approved mapping
         (the manifest at `approvals_path`, defaulting to the real
         `rubric_approvals.json`, unless `_approved_versions_override` is
         given in tests) AND `parse_iso(entry.get("recorded_at"))` is not
         None AND is NOT earlier than that version's approved_at -- NO
         RETROACTIVE VERIFICATION: an entry recorded before its rubric
         version was approved never verifies, even after approval.

    `approvals_path` (new keyword, appended at the end, default None) is
    ignored whenever `_approved_versions_override` is not None; see
    `_resolve_approved_versions`'s docstring.
    """
    approved = _resolve_approved_versions(_approved_versions_override, approvals_path)

    if not (_nonempty_str(entry.get("reviewed_by")) and parse_iso(entry.get("reviewed_at")) is not None):
        return False

    decision = entry.get("decision")
    if decision == "confirm":
        if entry.get("confirmation_basis") != "rule-1-textbook-provenance":
            return False
    elif decision == "change":
        if entry.get("new_dok") not in VALID_CHOSEN_DOKS:
            return False
        if not _nonempty_str(entry.get("rationale")):
            return False
        if not _nonempty_str(entry.get("provenance")):
            return False
        item_basis = entry.get("item_basis")
        if item_basis not in ITEM_BASES:
            return False
        if item_basis == "textbook-exact" and entry.get("provenance_resolved") is not True:
            return False
    else:
        # needs-source-check (or any unrecognized/legacy decision) -- never verified.
        return False

    if entry.get("prior_unresolved_nsc"):
        return False

    version = entry.get("rubric_version")
    if version not in approved:
        return False
    approved_at = approved[version]
    recorded_at = parse_iso(entry.get("recorded_at"))
    if recorded_at is None or approved_at is None:
        return False
    try:
        if recorded_at < approved_at:
            return False
    except TypeError:
        # Defense in depth (NT6 round 3, G2): with the aware-only parse_iso
        # policy this should be unreachable (both operands are aware
        # datetimes here, None already excluded above), but a comparison
        # between an aware and a naive datetime must never escape as an
        # uncaught TypeError -- fail closed, exactly like an unresolved
        # comparison should.
        return False

    return True


def tool_state_for(uid, latest_by_uid, _approved_versions_override=None, approvals_path=None):
    entry = latest_by_uid.get(uid)
    if entry is None:
        return "unreviewed"
    if entry_is_malformed(entry):
        return "invalid-entry"
    return (
        "verified"
        if entry_is_verified(entry, _approved_versions_override, approvals_path)
        else "reviewed_once"
    )


def compute_disagreement_resolved(rationale_or_note, match_quality, reviewer_dok, prior_dok, te_bucket):
    judgment_case = bool(
        match_quality != "exact"
        or reviewer_dok != prior_dok
        or (bool(te_bucket) and prior_dok not in te_bucket)
    )
    return bool(rationale_or_note.strip()) and judgment_case


# ---------------------------------------------------------------------------
# R5 (Codex cross-review, remediation stage R1): the workflow spec promises
# that reviewer judgment on anything but a rock-solid TE signal gets WRITTEN
# DOWN. Enforced only for `confirm` (a confirm re-asserts prior_dok, i.e.
# item["dok"], as reviewer_dok -- there is nothing else to check it against).
# ---------------------------------------------------------------------------

def _confirm_disagreement_requires_rationale(item):
    """True iff a `confirm` disposition on `item` requires a non-empty
    --rationale documenting the reviewer's judgment.

    Applies ONLY to these two match_quality shapes (Fable-locked scope --
    deliberately narrow, do not extend without re-authorization):

      - match_quality == "derived" -- the item's TE bucket was INFERRED,
        not read directly off a TE page; a confirm here is trusting a
        weaker signal and must say why that trust is warranted.
      - match_quality == "exact" AND item["dok"] is NOT among
        item["te_bucket"] -- the "exact-disagreement" case: the TE match
        itself is exact, but the wave plan's own dok falls outside what
        that TE bucket actually supports. Zero real items are in this
        state in the current wave plan, but the predicate must still
        catch a future or hand-crafted one.

    OUT OF SCOPE (rationale stays optional, unchanged from before this
    fix):
      - match_quality == "none" -- te_bucket is None/absent; there is no
        TE signal at all to disagree with.
      - match_quality == "exact" with item["dok"] actually inside
        item["te_bucket"] -- the ordinary AGREEING case.

    A falsy/malformed te_bucket on an "exact" item is treated the same
    way `compute_disagreement_resolved` treats it (`bool(te_bucket) and
    ... not in te_bucket`) -- no te_bucket to disagree with means no
    forced rationale, not a crash on `in None`.
    """
    match_quality = item.get("match_quality")
    if match_quality == "derived":
        return True
    if match_quality == "exact":
        te_bucket = item.get("te_bucket")
        if te_bucket and item.get("dok") not in te_bucket:
            return True
    return False


# ---------------------------------------------------------------------------
# Building + appending review_log.jsonl records.
# ---------------------------------------------------------------------------

def build_review_record(
    item,
    reviewed_by,
    disposition,
    chosen_dok,
    rationale,
    provenance,
    rubric_version,
    note,
    reviewed_at,
    calibration_dir,
    item_basis=None,
    resolves_source_check=False,
):
    """Build one review_log.jsonl record for `item` (an augmented item from
    build_uid_index, i.e. it has 'lesson'). Does not write anything. Does NOT
    stamp `recorded_at` (that is `append_review`'s job, so it is always
    tool-generated at the moment of the actual write) or
    `prior_unresolved_nsc` (that needs the item_uid's full existing chain,
    computed by the caller -- see `cmd_review`).

    Defensive module-path guard (NT6 fix F7b): raises ValueError if
    disposition == "change" and chosen_dok is outside the DOK domain
    {1, 2, 3}, even when called directly and bypassing argparse /
    `_validate_review_args` entirely. DOK measures cognitive demand, not
    difficulty -- DOK 4 is not assignable on this platform.
    """
    if disposition == "change" and chosen_dok not in VALID_CHOSEN_DOKS:
        raise ValueError(
            f"chosen_dok {chosen_dok!r} is outside the DOK domain {VALID_CHOSEN_DOKS} "
            "-- DOK measures cognitive demand, not difficulty; DOK 4 is not "
            "assignable on this platform"
        )

    if disposition != "change":
        item_basis = None

    prior_dok = item["dok"]
    te_bucket = item.get("te_bucket")
    match_quality = item.get("match_quality")

    provenance_resolved = resolve_provenance(provenance, calibration_dir, item)

    if disposition == "confirm":
        reviewer_dok = prior_dok
        new_dok = None
        if not provenance.strip():
            confirmation_basis = "rule-2-adjacent-unsourced"
        elif provenance_resolved:
            confirmation_basis = "rule-1-textbook-provenance"
        else:
            confirmation_basis = "rule-2-adjacent-unsourced-claim"
    elif disposition == "change":
        reviewer_dok = chosen_dok
        new_dok = chosen_dok
        confirmation_basis = None
    else:  # needs-source-check
        reviewer_dok = None
        new_dok = None
        confirmation_basis = None

    rationale_or_note = rationale if rationale.strip() else note
    disagreement_resolved = compute_disagreement_resolved(
        rationale_or_note, match_quality, reviewer_dok, prior_dok, te_bucket
    )

    return {
        "item_uid": item["item_uid"],
        "registry_line": item["registry_line"],
        "item_id": item["id"],
        "lesson": item.get("lesson"),
        "reviewed_by": reviewed_by,
        "reviewed_at": reviewed_at,
        "prior_dok": prior_dok,
        "reviewer_dok": reviewer_dok,
        "current_dok": prior_dok,
        "new_dok": new_dok,
        "decision": disposition,
        "te_bucket": te_bucket,
        "match_quality": match_quality,
        "disagreement_resolved": disagreement_resolved,
        "note": note,
        "rubric_version": rubric_version,
        "rationale": rationale,
        "provenance": provenance,
        "provenance_resolved": provenance_resolved,
        "confirmation_basis": confirmation_basis,
        "item_basis": item_basis,
        "resolves_source_check": bool(resolves_source_check),
    }


def append_review(log_path, record):
    """THE ONLY code path that writes review_log.jsonl. Append-mode only;
    never reads-modifies-writes the whole file; never rewrites prior lines.

    Stamps a TOOL-GENERATED `recorded_at` = datetime.now().astimezone().isoformat()
    onto a COPY of `record` at the moment of the actual write -- the reviewer
    cannot supply this value (there is no CLI flag for it; `build_review_record`
    never sets it). This is what makes the rubric-approval retroactivity
    check in `entry_is_verified` meaningful: `recorded_at` reflects when the
    tool actually wrote the line, not any value a caller could fabricate.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(record)
    record["recorded_at"] = datetime.now().astimezone().isoformat()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.write("\n")
        f.flush()
    return record


# ---------------------------------------------------------------------------
# queue
# ---------------------------------------------------------------------------

def get_queue_rows(plan, log_path, _approved_versions_override=None, approvals_path=None):
    """Per NT11 (rc-merge-auth-5-4-2026-07-23): each row now additively
    carries 'status' ('active' / 'merged-alias', defaulting to 'active' for
    a plan predating this overlay) and 'alias_of' (the survivor's item_uid,
    None for non-alias rows) -- carried straight through from the wave-plan
    item, never re-derived. This is an AUDIT-style surface (see
    DOK_VERIFICATION_WORKFLOW.md's dual-denominator note): merged-alias
    items stay IN the queue, explicitly marked, never dropped -- reviewing
    an alias row's history is still a legitimate audit action even though it
    is no longer a live selection target for any student-facing consumer."""
    entries = read_log_entries(log_path)
    latest = latest_entries_by_uid(entries)
    approved = _resolve_approved_versions(_approved_versions_override, approvals_path)
    rows = []
    for wave, lesson, item in iter_queue_items(plan):
        uid = item["item_uid"]
        rows.append({
            "wave": wave,
            "lesson": lesson,
            "item_uid": uid,
            "id": item["id"],
            "dok": item["dok"],
            "role": item.get("role"),
            "dok_status": item.get("dok_status"),
            "status": item.get("status", "active"),
            "alias_of": item.get("alias_of"),
            "tool_state": tool_state_for(uid, latest, approved),
        })
    return rows


def cmd_queue(args):
    plan = load_plan(args.plan)
    rows = get_queue_rows(plan, args.log, approvals_path=args.approvals)

    no_flags = (
        args.wave is None
        and args.state is None
        and args.limit is None
        and not args.next
    )

    state_filter = args.state
    limit = args.limit
    if args.next or no_flags:
        if state_filter is None:
            state_filter = "unreviewed"
        if limit is None:
            limit = 20

    filtered = rows
    if args.wave is not None:
        filtered = [r for r in filtered if r["wave"] == str(args.wave)]
    if state_filter is not None:
        filtered = [r for r in filtered if r["tool_state"] == state_filter]
    if limit is not None:
        filtered = filtered[:limit]

    if args.json:
        print(json.dumps(filtered, indent=2, ensure_ascii=False))
        return

    if not filtered:
        print("(no matching items)")
        return

    header = (
        f"{'WAVE':<5} {'ITEM_UID':<18} {'ID':<32} {'LESSON':<8} "
        f"{'DOK':<4} {'ROLE':<14} {'DOK_STATUS':<12} {'STATE':<14} {'MERGE_STATUS':<26}"
    )
    print(header)
    print("-" * len(header))
    for r in filtered:
        merge_display = (
            f"ALIAS->{r['alias_of']}" if r["status"] == "merged-alias" else "active"
        )
        print(
            f"{r['wave']:<5} {r['item_uid']:<18} {r['id']:<32} {r['lesson']:<8} "
            f"{str(r['dok']):<4} {str(r['role'] or ''):<14} "
            f"{str(r['dok_status'] or ''):<12} {r['tool_state']:<14} {merge_display:<26}"
        )
    print(f"\n{len(filtered)} item(s) shown.")


# ---------------------------------------------------------------------------
# review
# ---------------------------------------------------------------------------

def _validate_review_args(args, prior_dok, calibration_dir, prior_entries_for_uid, item):
    """Validate all CLI inputs for `review` BEFORE anything is appended.
    Returns None on success, or an error message string on failure. Reject-
    at-entry: this (plus the timestamp/monotonicity checks in `cmd_review`)
    is the ONLY gate -- if it passes, build+append proceeds; if it fails,
    cmd_review must exit nonzero without appending anything.

    `item` (the augmented wave-plan item being reviewed) is REQUIRED (NT6
    round 3, G1) -- it is threaded into every `resolve_provenance` /
    `_chain_pending_nsc_states` call below so provenance resolution stays
    bound to the item actually under review."""
    if not _nonempty_str(args.reviewed_by):
        return "--reviewed-by is required and must be non-empty"

    if not _nonempty_str(args.rubric_version):
        return "--rubric-version is required"

    disposition = args.disposition
    rationale = args.rationale or ""
    provenance = args.provenance or ""
    chosen_dok = args.chosen_dok
    item_basis = args.item_basis
    resolves_source_check = bool(getattr(args, "resolves_source_check", False))

    if chosen_dok is not None and chosen_dok not in VALID_CHOSEN_DOKS:
        return (
            f"--chosen-dok {chosen_dok!r} is outside the DOK domain {VALID_CHOSEN_DOKS} "
            "-- DOK measures cognitive demand, not difficulty; DOK 4 is not "
            "assignable on this platform"
        )

    if disposition == "change":
        if item_basis is None:
            return (
                "--item-basis is required when --disposition is 'change' "
                "(rule 3: is this a source-dispute resolution -- textbook-exact "
                "-- or an actual-cognitive-demand item?)"
            )
    else:
        if item_basis is not None:
            return "--item-basis is only valid when --disposition is 'change'"

    if resolves_source_check and disposition == "needs-source-check":
        return "--resolves-source-check is not valid with --disposition needs-source-check"

    if disposition == "change":
        if chosen_dok is None:
            return "--chosen-dok is required when --disposition is 'change'"
        if not rationale.strip():
            return "--rationale is required (non-empty) when --disposition is 'change'"
        if not provenance.strip():
            return "--provenance is required (non-empty) when --disposition is 'change' (rule 5: override needs BOTH rationale and provenance)"
        if chosen_dok == prior_dok:
            return (
                f"--chosen-dok {chosen_dok} is the same DOK as the wave plan "
                f"(prior_dok={prior_dok}) -- record a confirm, not a change"
            )
    else:
        if chosen_dok is not None:
            return "a chosen DOK is only valid when disposition is change"
        if disposition == "needs-source-check" and not rationale.strip():
            return "--rationale is required (non-empty) when --disposition is 'needs-source-check'"
        if (
            disposition == "confirm"
            and _confirm_disagreement_requires_rationale(item)
            and not rationale.strip()
        ):
            return (
                "--rationale is required (non-empty): a confirm on a "
                "derived-match (or exact-disagreement) item requires "
                "--rationale documenting the judgment (the item has only a "
                "weak/conflicting TE signal)"
            )
        # confirm (agreeing exact / none match_quality): rationale optional, provenance optional.

    if resolves_source_check:
        pending_states = _chain_pending_nsc_states(prior_entries_for_uid, calibration_dir, item)
        currently_pending = pending_states[-1] if pending_states else False
        if not currently_pending:
            return (
                "--resolves-source-check: nothing to resolve (no unresolved "
                "needs-source-check for this item_uid)"
            )
        if not resolve_provenance(provenance, calibration_dir, item):
            return (
                "--resolves-source-check requires --provenance that resolves "
                "on disk (calibration-anchor scheme)"
            )

    return None


def cmd_review(args):
    plan = load_plan(args.plan)
    uid_to_item, _uid_to_line, _duplicates = build_uid_index(plan)
    item = uid_to_item.get(args.item_uid)
    if item is None:
        print(
            f"ERROR: unknown item_uid: {args.item_uid!r} (not found in wave plan)",
            file=sys.stderr,
        )
        sys.exit(1)

    all_entries = read_log_entries(args.log)
    prior_entries_for_uid = entries_for_uid(all_entries, args.item_uid)

    reviewed_at_raw = args.reviewed_at or datetime.now().astimezone().isoformat()
    reviewed_at_parsed = parse_iso(reviewed_at_raw)
    if reviewed_at_parsed is None:
        print(
            f"ERROR: --reviewed-at {reviewed_at_raw!r} is not a valid ISO-8601 timestamp",
            file=sys.stderr,
        )
        sys.exit(1)

    if prior_entries_for_uid:
        latest_existing = prior_entries_for_uid[-1]
        existing_reviewed_at = parse_iso(latest_existing.get("reviewed_at"))
        if existing_reviewed_at is None:
            print(
                f"ERROR: item_uid {args.item_uid!r} has an existing log entry "
                "with an unparseable reviewed_at -- fail closed, refusing to append",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            predates_existing = reviewed_at_parsed < existing_reviewed_at
        except TypeError:
            # Defense in depth (NT6 round 3, G2): with the aware-only
            # parse_iso policy this should be unreachable, but a naive/aware
            # comparison must never escape uncaught -- fail closed.
            print(
                f"ERROR: --reviewed-at {reviewed_at_raw!r} could not be "
                f"compared against item_uid {args.item_uid!r}'s latest "
                "existing review timestamp -- fail closed, refusing to append",
                file=sys.stderr,
            )
            sys.exit(1)
        if predates_existing:
            print(
                f"ERROR: --reviewed-at {reviewed_at_raw!r} predates the item's "
                f"latest existing review ({latest_existing.get('reviewed_at')!r}) "
                f"for item_uid {args.item_uid!r}",
                file=sys.stderr,
            )
            sys.exit(1)

    error = _validate_review_args(
        args,
        prior_dok=item["dok"],
        calibration_dir=args.calibration_dir,
        prior_entries_for_uid=prior_entries_for_uid,
        item=item,
    )
    if error is not None:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    record = build_review_record(
        item=item,
        reviewed_by=args.reviewed_by,
        disposition=args.disposition,
        chosen_dok=args.chosen_dok,
        rationale=args.rationale or "",
        provenance=args.provenance or "",
        rubric_version=args.rubric_version,
        note=args.note or "",
        reviewed_at=reviewed_at_raw,
        calibration_dir=args.calibration_dir,
        item_basis=args.item_basis,
        resolves_source_check=args.resolves_source_check,
    )

    extended_chain = prior_entries_for_uid + [record]
    pending_states = _chain_pending_nsc_states(extended_chain, args.calibration_dir, item)
    record["prior_unresolved_nsc"] = pending_states[-1]

    written = append_review(args.log, record)
    print(
        f"Recorded review for {written['item_uid']} (id={written['item_id']}, "
        f"lesson={written['lesson']}): decision={written['decision']} "
        f"prior_dok={written['prior_dok']} reviewer_dok={written['reviewer_dok']} "
        f"new_dok={written['new_dok']} rubric_version={written['rubric_version']}"
    )


# ---------------------------------------------------------------------------
# progress
# ---------------------------------------------------------------------------

def compute_progress(plan, log_path, _approved_versions_override=None, approvals_path=None):
    entries = read_log_entries(log_path)
    latest = latest_entries_by_uid(entries)
    approved = _resolve_approved_versions(_approved_versions_override, approvals_path)

    wave_totals = {wk: 0 for wk in WAVE_KEYS}
    wave_reviewed_once = {wk: 0 for wk in WAVE_KEYS}
    wave_verified = {wk: 0 for wk in WAVE_KEYS}
    wave_invalid_entry = {wk: 0 for wk in WAVE_KEYS}
    dok_status_counts = {}
    merged_alias_total = 0

    for wave, _lesson, item in iter_queue_items(plan):
        uid = item["item_uid"]
        wave_totals[wave] += 1
        state = tool_state_for(uid, latest, approved)
        if state in ("reviewed_once", "verified"):
            wave_reviewed_once[wave] += 1
        if state == "verified":
            wave_verified[wave] += 1
        if state == "invalid-entry":
            wave_invalid_entry[wave] += 1
        status = item.get("dok_status")
        dok_status_counts[status] = dok_status_counts.get(status, 0) + 1
        if item.get("status") == "merged-alias":
            merged_alias_total += 1

    overall_total = sum(wave_totals.values())
    overall_reviewed_once = sum(wave_reviewed_once.values())
    overall_verified = sum(wave_verified.values())
    overall_invalid_entry = sum(wave_invalid_entry.values())

    return {
        "waves": {
            wk: {
                "total": wave_totals[wk],
                "reviewed_once_or_better": wave_reviewed_once[wk],
                "verified": wave_verified[wk],
                "invalid_entry": wave_invalid_entry[wk],
            }
            for wk in WAVE_KEYS
        },
        "overall": {
            "total": overall_total,
            "reviewed_once_or_better": overall_reviewed_once,
            "verified": overall_verified,
            "invalid_entry": overall_invalid_entry,
        },
        "dok_status_counts": dok_status_counts,
        # Dual-denominator identity (rc-merge-auth-5-4-2026-07-23, additive):
        # this is an AUDIT surface (queue/progress/report all keep every
        # merged-alias row, explicitly marked) -- raw_total is this plan's
        # full row count (900 for the real committed plan), active_total
        # excludes the merged_alias_total rows a student-facing consumer
        # (qb.py) would resolve away. Computed dynamically from whatever
        # `plan` was passed (never hardcoded), so a synthetic/fixture plan
        # with a different shape reports its own true counts.
        "identity": {
            "raw_total": overall_total,
            "active_total": overall_total - merged_alias_total,
            "merged_alias_total": merged_alias_total,
        },
    }


def cmd_progress(args):
    plan = load_plan(args.plan)
    progress = compute_progress(plan, args.log, approvals_path=args.approvals)

    if args.json:
        print(json.dumps(progress, indent=2, ensure_ascii=False))
        return

    print("Review-log progress (keyed by item_uid, latest entry wins)")
    print(f"{'WAVE':<6}{'REVIEWED_ONCE+':<16}{'VERIFIED':<12}{'INVALID':<10}{'TOTAL':<8}")
    for wk in WAVE_KEYS:
        w = progress["waves"][wk]
        reviewed_str = f"{w['reviewed_once_or_better']}/{w['total']}"
        verified_str = f"{w['verified']}/{w['total']}"
        invalid_str = f"{w['invalid_entry']}/{w['total']}"
        print(f"{wk:<6}{reviewed_str:<16}{verified_str:<12}{invalid_str:<10}{w['total']:<8}")
    o = progress["overall"]
    print("-" * 44)
    reviewed_str = f"{o['reviewed_once_or_better']}/{o['total']}"
    verified_str = f"{o['verified']}/{o['total']}"
    invalid_str = f"{o['invalid_entry']}/{o['total']}"
    print(f"{'ALL':<6}{reviewed_str:<16}{verified_str:<12}{invalid_str:<10}{o['total']:<8}")

    print()
    print("wave-plan dok_status (registry-derived, not review-log):")
    for status, count in sorted(progress["dok_status_counts"].items(), key=lambda kv: str(kv[0])):
        print(f"  {status}: {count}")

    identity = progress["identity"]
    print()
    print(
        "dual-denominator identity (rc-merge-auth-5-4-2026-07-23): "
        f"raw_total={identity['raw_total']} "
        f"active_total={identity['active_total']} "
        f"merged_alias_total={identity['merged_alias_total']} "
        f"(active + merged_alias == raw: "
        f"{identity['active_total']} + {identity['merged_alias_total']} == {identity['raw_total']})"
    )

    approved = _resolve_approved_versions(None, args.approvals)
    print()
    if not approved:
        print(
            "NOTE: no rubric version approved (tools/dok-review/rubric_approvals.json "
            "has zero entries in 'approvals') -- the VERIFIED column above cannot "
            "advance past 0 until a teacher approval is recorded there. This is the "
            "intended fail-safe, not a bug."
        )
    else:
        versions_str = ", ".join(
            f"{v} (approved_at={dt.isoformat()})" for v, dt in sorted(approved.items())
        )
        print(f"NOTE: approved rubric versions: {versions_str}")


# ---------------------------------------------------------------------------
# promote
# ---------------------------------------------------------------------------

def resolve_registry_row_for_uid(plan, registry_path, uid):
    """Resolve item_uid -> exactly one registry row via the frozen
    line->uid join (uid -> registry_line -> 1-based line in registry.jsonl).
    Returns (registry_line, registry_row, item). Raises ValueError on any
    failure to resolve exactly one row -- never writes anything."""
    uid_to_item, uid_to_line, duplicates = build_uid_index(plan)
    if uid in duplicates:
        raise ValueError(
            f"item_uid {uid!r} appears more than once in the wave plan "
            "(should be impossible for a well-formed plan) -- refusing to promote"
        )
    item = uid_to_item.get(uid)
    if item is None:
        raise ValueError(f"unknown item_uid: {uid!r} (not found in wave plan)")

    registry_line = uid_to_line[uid]
    row = load_registry_line(registry_path, registry_line)
    if row is None:
        raise ValueError(
            f"registry_line {registry_line} for item_uid {uid!r} did not resolve "
            "to a row in the registry -- refusing to promote"
        )
    return registry_line, row, item


def _validate_chain_entry(entry, position, calibration_dir, item):
    """Structural + on-disk re-derivation validation for ONE chain entry at
    1-based `position`. Returns None if OK, else an error string naming the
    position and the defect. `promote` walks the FULL chain with this
    before trusting anything -- it does not just check the latest entry.

    `item` (the augmented wave-plan item this chain belongs to) is REQUIRED
    (NT6 round 3, G1) so every `resolve_provenance` re-derivation below
    stays bound to the item actually being promoted -- a crafted entry that
    cites a DIFFERENT item's (or a different practice/example number's)
    calibration anchor is rejected here, not just accepted because some
    anchor happens to exist somewhere in the cited lesson's file.
    """
    decision = entry.get("decision")
    if decision not in DISPOSITIONS:
        return f"chain entry #{position}: unknown decision {decision!r}"

    if not _nonempty_str(entry.get("reviewed_by")):
        return f"chain entry #{position}: reviewed_by is missing or blank"

    if parse_iso(entry.get("reviewed_at")) is None:
        return f"chain entry #{position}: reviewed_at is missing or unparseable"

    if decision == "change":
        if not _nonempty_str(entry.get("rationale")):
            return f"chain entry #{position}: change entry is missing rationale"
        if not _nonempty_str(entry.get("provenance")):
            return f"chain entry #{position}: change entry is missing provenance"
        if entry.get("new_dok") not in VALID_CHOSEN_DOKS:
            return f"chain entry #{position}: change entry has an invalid new_dok"
        if entry.get("item_basis") not in ITEM_BASES:
            return f"chain entry #{position}: change entry is missing/has an invalid item_basis"
        if entry.get("item_basis") == "textbook-exact":
            if not resolve_provenance(entry.get("provenance"), calibration_dir, item):
                return (
                    f"chain entry #{position}: change entry claims item_basis "
                    "'textbook-exact' but its provenance does not resolve on disk"
                )
    elif decision == "needs-source-check":
        if not _nonempty_str(entry.get("rationale")):
            return f"chain entry #{position}: needs-source-check entry is missing rationale"
    elif decision == "confirm":
        if entry.get("confirmation_basis") == "rule-1-textbook-provenance":
            if not resolve_provenance(entry.get("provenance"), calibration_dir, item):
                return (
                    f"chain entry #{position}: confirm claims confirmation_basis "
                    "'rule-1-textbook-provenance' but lacks source provenance on "
                    "disk -- not verification-grade"
                )
        # R5 (Codex cross-review, remediation stage R1): a confirm on a
        # derived-match (or exact-disagreement) item must have the
        # reviewer's judgment written down. Deliberate choice: this is a
        # promotion chain-validation gate ONLY -- entry_is_malformed /
        # entry_is_verified (the display-tier well-formedness bar and the
        # VERIFIED predicate) are NOT touched by this fix. The display
        # tier still trusts the stamps written at review time (queue /
        # progress / report stay fast, cheap, offline reads); `promote` is
        # exactly where this module already re-derives against the
        # wave-plan item instead of trusting anything stamped on the
        # entry, so that is where a crafted log line skipping this
        # rationale gets caught -- it can still show as "reviewed_once" on
        # the display tier, but it can never promote.
        if _confirm_disagreement_requires_rationale(item) and not _nonempty_str(entry.get("rationale")):
            return (
                f"chain entry #{position}: confirm on a derived-match (or "
                "exact-disagreement) item is missing --rationale documenting "
                "the judgment (the item has only a weak/conflicting TE signal)"
            )

    if entry.get("resolves_source_check"):
        if not resolve_provenance(entry.get("provenance"), calibration_dir, item):
            return (
                f"chain entry #{position}: resolves_source_check attestation "
                "lacks provenance that re-resolves on disk"
            )

    return None


def _validate_chain_order(chain, uid):
    """Validate that `reviewed_at` is non-decreasing along `chain`'s append
    order (NT6 round 3, G2). Returns None if OK, else an error string naming
    the 1-based offending ADJACENT positions. Called only after every entry
    has already passed `_validate_chain_entry` (so every `reviewed_at` is
    guaranteed parseable and aware) -- the try/except below is defense in
    depth, not the primary safeguard: with the aware-only `parse_iso` policy
    a TypeError here should be unreachable, but it must never escape
    uncaught if it somehow occurred."""
    for idx in range(1, len(chain)):
        prev_entry = chain[idx - 1]
        curr_entry = chain[idx]
        prev_ts = parse_iso(prev_entry.get("reviewed_at"))
        curr_ts = parse_iso(curr_entry.get("reviewed_at"))
        try:
            out_of_order = curr_ts < prev_ts
        except TypeError:
            return (
                f"chain entries #{idx} and #{idx + 1} have reviewed_at "
                "timestamps that could not be compared for order"
            )
        if out_of_order:
            return (
                f"chain entries #{idx} and #{idx + 1} are out of order "
                f"(reviewed_at goes backwards: {prev_entry.get('reviewed_at')!r} "
                f"-> {curr_entry.get('reviewed_at')!r})"
            )
    return None


def build_promotion_proposal(
    plan, registry_path, log_path, uid, calibration_dir=None,
    _approved_versions_override=None, approvals_path=None,
):
    """Build (but do not write) a promotion proposal dict for `uid`. Raises
    ValueError if any rejection-ladder gate fails, checked in this order:
      1. unresolvable uid / duplicate uid / missing registry row (existing);
      2. no review-log entry(-ies) yet;
      3. FULL entry chain, walked in order: every entry must be structurally
         valid AND re-derive correctly against disk (see
         `_validate_chain_entry`, item-bound per G1) -- rejects on the FIRST
         malformed entry, naming its 1-based position and the defect;
      4. CHAIN ORDER: `reviewed_at` must be non-decreasing along append
         order (NT6 round 3, G2) -- rejects naming the offending adjacent
         positions if it ever goes backwards;
      5. re-derived (never trusted) needs-source-check chain state -- any
         unresolved nsc anywhere in the chain blocks promotion;
      6. latest entry is a confirm that is not rule-1-grade (rule-2-adjacent,
         unsourced or an unresolved claim) -- not verification-grade;
      7. rubric gate: latest entry's rubric_version not in the approved
         manifest, OR in the manifest but recorded_at is missing/unparseable/
         earlier than that version's approved_at (NO retroactive
         verification -- re-review required);
      8. FINAL authoritative gate: `entry_is_verified(latest, ...)` must be
         True, using the SAME approved mapping -- no parallel logic, no
         unknown-decision fall-through.
    Never opens registry.jsonl for write; proposals-only regardless of
    rubric state.

    `approvals_path` (new keyword, appended at the end, default None) is
    threaded straight into `_resolve_approved_versions` and ignored whenever
    `_approved_versions_override` is not None.
    """
    calibration_dir = Path(calibration_dir) if calibration_dir is not None else DEFAULT_CALIBRATION_DIR
    approved = _resolve_approved_versions(_approved_versions_override, approvals_path)

    registry_line, row, item = resolve_registry_row_for_uid(plan, registry_path, uid)

    all_entries = read_log_entries(log_path)
    chain = entries_for_uid(all_entries, uid)
    if not chain:
        raise ValueError(
            f"no review found for item_uid {uid!r} -- cannot promote an unreviewed item"
        )

    for position, entry in enumerate(chain, start=1):
        defect = _validate_chain_entry(entry, position, calibration_dir, item)
        if defect is not None:
            raise ValueError(f"item_uid {uid!r} {defect} -- refusing to promote")

    order_defect = _validate_chain_order(chain, uid)
    if order_defect is not None:
        raise ValueError(f"item_uid {uid!r} {order_defect} -- refusing to promote")

    pending_states = _chain_pending_nsc_states(chain, calibration_dir, item)
    if pending_states[-1]:
        raise ValueError(
            f"item_uid {uid!r} has an unresolved needs-source-check -- "
            "refusing to promote until a later confirm or change resolves it"
        )

    entry = chain[-1]
    decision = entry.get("decision")

    if decision == "confirm" and entry.get("confirmation_basis") != "rule-1-textbook-provenance":
        raise ValueError(
            f"item_uid {uid!r} confirm lacks source provenance -- it is "
            "rule-2-adjacent (unsourced or an unresolved claim), not "
            "verification-grade -- refusing to promote"
        )

    version = entry.get("rubric_version")
    if version not in approved:
        raise ValueError(
            f"item_uid {uid!r} rubric version not approved "
            f"(rubric_version={version!r} is not in the approved manifest) "
            "-- refusing to promote until a teacher approves this rubric version"
        )
    approved_at = approved[version]
    recorded_at = parse_iso(entry.get("recorded_at"))
    if recorded_at is None or approved_at is None:
        raise ValueError(
            f"item_uid {uid!r} review was recorded before approval "
            f"(recorded_at={entry.get('recorded_at')!r}, version {version!r} "
            f"approved_at={approved_at.isoformat() if approved_at else None!r}) "
            "-- re-review required after approval"
        )
    try:
        recorded_before_approval = recorded_at < approved_at
    except TypeError:
        # Defense in depth (NT6 round 3, G2): should be unreachable under the
        # aware-only parse_iso policy, but never let a naive/aware
        # comparison escape uncaught -- fail closed (refuse to promote).
        raise ValueError(
            f"item_uid {uid!r} recorded_at/approved_at timestamps could not "
            "be compared -- refusing to promote"
        )
    if recorded_before_approval:
        raise ValueError(
            f"item_uid {uid!r} review was recorded before approval "
            f"(recorded_at={entry.get('recorded_at')!r}, version {version!r} "
            f"approved_at={approved_at.isoformat() if approved_at else None!r}) "
            "-- re-review required after approval"
        )

    if not entry_is_verified(entry, _approved_versions_override=approved):
        raise ValueError(
            f"item_uid {uid!r} latest review is not verification-grade -- "
            "refusing to promote"
        )

    current_dok = row.get("dok")
    proposed_new_dok = entry.get("new_dok") if decision == "change" else current_dok

    return {
        "item_uid": uid,
        "registry_line": registry_line,
        "legacy_id": row.get("id"),
        "current_dok": current_dok,
        "proposed_reviewed_by": entry.get("reviewed_by"),
        "proposed_reviewed_at": entry.get("reviewed_at"),
        "proposed_new_dok": proposed_new_dok,
        "decision": decision,
        "note": entry.get("note", ""),
        "rubric_version": version,
        "rationale": entry.get("rationale", ""),
        "provenance": entry.get("provenance", ""),
        "item_basis": entry.get("item_basis"),
        "confirmation_basis": entry.get("confirmation_basis"),
        "registry_written": False,
        "human_note": (
            "PROPOSAL ONLY. questionbank/registry.jsonl was NOT modified by "
            "this tool. A human must apply this change manually if approved."
        ),
    }


def cmd_promote(args):
    plan = load_plan(args.plan)
    try:
        proposal = build_promotion_proposal(
            plan, args.registry, args.log, args.item_uid,
            calibration_dir=args.calibration_dir, approvals_path=args.approvals,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = DEFAULT_PROPOSALS_DIR / f"promotion_{args.item_uid}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote promotion proposal (registry NOT modified) to: {out_path}")


# ---------------------------------------------------------------------------
# report (static read-only HTML viewer)
# ---------------------------------------------------------------------------

def _html_escape(value):
    if value is None:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_report_html(plan, log_path, _approved_versions_override=None, approvals_path=None):
    rows = get_queue_rows(plan, log_path, _approved_versions_override, approvals_path)
    progress = compute_progress(plan, log_path, _approved_versions_override, approvals_path)
    approved = _resolve_approved_versions(_approved_versions_override, approvals_path)

    progress_rows = "".join(
        "<tr><td>{wave}</td><td>{ro}/{total}</td><td>{v}/{total}</td><td>{inv}/{total}</td></tr>".format(
            wave=_html_escape(wk),
            ro=progress["waves"][wk]["reviewed_once_or_better"],
            v=progress["waves"][wk]["verified"],
            inv=progress["waves"][wk]["invalid_entry"],
            total=progress["waves"][wk]["total"],
        )
        for wk in WAVE_KEYS
    )

    queue_rows = "".join(
        "<tr><td>{wave}</td><td>{uid}</td><td>{id_}</td><td>{lesson}</td>"
        "<td>{dok}</td><td>{role}</td><td>{dok_status}</td><td>{state}</td>"
        "<td>{merge_status}</td></tr>".format(
            wave=_html_escape(r["wave"]),
            uid=_html_escape(r["item_uid"]),
            id_=_html_escape(r["id"]),
            lesson=_html_escape(r["lesson"]),
            dok=_html_escape(r["dok"]),
            role=_html_escape(r["role"]),
            dok_status=_html_escape(r["dok_status"]),
            state=_html_escape(r["tool_state"]),
            merge_status=(
                _html_escape(f"ALIAS -> {r['alias_of']}")
                if r["status"] == "merged-alias"
                else "active"
            ),
        )
        for r in rows
    )

    generated_at = _html_escape(datetime.now().astimezone().isoformat())

    if not approved:
        rubric_note = (
            "no rubric version approved -- tools/dok-review/rubric_approvals.json "
            "has zero entries in 'approvals', so no item can show VERIFIED yet. "
            "This is the intended fail-safe, not a bug."
        )
    else:
        rubric_note = "Approved rubric versions: " + ", ".join(
            f"{v} (approved_at={dt.isoformat()})" for v, dt in sorted(approved.items())
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DOK Review Report (read-only)</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
th, td {{ border: 1px solid #ccc; padding: 4px 8px; font-size: 0.85rem; text-align: left; }}
th {{ background: #eee; }}
h1, h2 {{ margin-top: 2rem; }}
.note {{ color: #555; font-style: italic; }}
</style>
</head>
<body>
<h1>DOK Review Report</h1>
<p class="note">Static read-only view. Generated {generated_at}. No forms, no writes,
no network calls -- this file is a snapshot, not a live app. Display tiers (this
report, `queue`, `progress`) trust the stamps written at review time;
`promote` re-derives everything against disk before proposing a change.</p>
<p class="note">{_html_escape(rubric_note)}</p>

<h2>Progress by wave (review-log, item_uid-keyed)</h2>
<table>
<tr><th>Wave</th><th>Reviewed once or better</th><th>Verified</th><th>Invalid entry</th></tr>
{progress_rows}
</table>

<h2>Queue ({len(rows)} items)</h2>
<p class="note">Audit surface (rc-merge-auth-5-4-2026-07-23): merged-alias items stay in this
queue, explicitly marked in the "Merge status" column -- they are never dropped here, even
though student-facing selection (qb.py) resolves them to their survivor and never selects
the alias row itself.</p>
<table>
<tr><th>Wave</th><th>item_uid</th><th>id</th><th>Lesson</th><th>DOK</th><th>Role</th><th>dok_status</th><th>Tool state</th><th>Merge status</th></tr>
{queue_rows}
</table>
</body>
</html>
"""


def cmd_report(args):
    plan = load_plan(args.plan)
    html = build_report_html(plan, args.log, approvals_path=args.approvals)
    out_path = Path(args.out) if args.out else DEFAULT_REPORT
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote report to: {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="dok_review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Local DOK-verification review tool (DOK Acceptance Rubric v0.2 "
            "two-tier model). Reads the frozen wave plan, registry, and "
            "calibration files read-only; writes only its own append-only "
            "review_log.jsonl. REVIEWED (a reviewer recorded something "
            "well-formed) and VERIFIED (a resolved, verification-grade "
            "disposition under an APPROVED rubric version, recorded AFTER "
            "that approval) are DIFFERENT tiers -- see the module docstring "
            "and README.md for the full model. "
            "tools/dok-review/rubric_approvals.json ships with one approval "
            "(DOK rubric v0.2, approved_at 2026-07-20T19:06:13-04:00); the "
            "VERIFIED count is whatever the log + manifest compute at read "
            "time -- run `progress` for the current number."
        ),
        epilog=(
            "DOK domain is 1-3 on this platform (--chosen-dok accepts only "
            "1, 2, or 3; DOK 4 is not assignable and does not appear in the "
            "current bank). " + DOK_NOT_DIFFICULTY_NOTE + " "
            "(Rubric rule 4, verbatim.) Tool note: "
            "'needs-source-check' is terminal-unresolved until a LATER entry "
            "stamps --resolves-source-check with provenance that resolves on "
            "disk -- a plain later confirm/change does NOT resolve it. A "
            "confirm without resolving --provenance is recorded and REVIEWED "
            "but is rule-2-adjacent (unsourced or an unresolved claim) -- "
            "never verified, never promotable. Invalid `review` invocations "
            "are rejected AT ENTRY before anything is appended to the log. "
            "`promote` never trusts stored stamps -- it re-derives provenance "
            "resolution and needs-source-check state against disk before "
            "proposing anything."
        ),
    )
    parser.add_argument("--plan", default=str(DEFAULT_PLAN), help="Path to dok_wave_plan.json (read-only).")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Path to registry.jsonl (read-only).")
    parser.add_argument(
        "--calibration-dir", default=str(DEFAULT_CALIBRATION_DIR),
        help="Path to questionbank/calibration/ (read-only; used to resolve calibration-anchor provenance).",
    )
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="Path to this tool's review_log.jsonl (append-only).")
    parser.add_argument(
        "--approvals", default=str(DEFAULT_APPROVALS),
        help="Path to rubric_approvals.json, read-only.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_queue = sub.add_parser("queue", help="Print the review queue in wave-plan authoritative order.")
    p_queue.add_argument("--wave", type=int, choices=[0, 1, 2, 3, 4], default=None)
    p_queue.add_argument("--state", choices=list(TOOL_STATES), default=None)
    p_queue.add_argument("--limit", type=int, default=None)
    p_queue.add_argument("--next", action="store_true", help="Show only the next N unreviewed items.")
    p_queue.add_argument("--json", action="store_true")
    p_queue.set_defaults(func=cmd_queue)

    p_review = sub.add_parser(
        "review",
        help="Append exactly one review decision line (reject-at-entry: invalid input appends nothing).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Record one review decision for one item_uid.",
        epilog=(
            DOK_NOT_DIFFICULTY_NOTE + " "
            "(Rubric rule 4, verbatim.) Tool note: "
            "--item-basis is REQUIRED when --disposition=change and REJECTED "
            "otherwise: 'textbook-exact' is a rule-1/rule-2 source-dispute "
            "resolution (verification-grade only when --provenance resolves "
            "on disk); the other bases (adapted/split/extended/"
            "teacher-authored) are rule-3 items rated by actual cognitive "
            "demand (free-text provenance is acceptable there). "
            "--resolves-source-check attests that THIS entry's --provenance "
            "resolves the item_uid's most recent unresolved "
            "needs-source-check; rejected at entry if there is nothing to "
            "resolve, or if the provenance does not resolve on disk. "
            "--reviewed-at must be strict ISO-8601 (datetime.fromisoformat); "
            "it may not predate the item_uid's latest existing review entry."
        ),
    )
    p_review.add_argument("--item-uid", required=True)
    p_review.add_argument("--reviewed-by", required=True, help="Must be non-empty/non-whitespace.")
    p_review.add_argument(
        "--disposition",
        required=True,
        choices=list(DISPOSITIONS),
        help="confirm (agree with prior_dok) / change (override, needs rationale+provenance+item-basis) / needs-source-check (terminal-unresolved, needs rationale).",
    )
    p_review.add_argument(
        "--chosen-dok",
        type=int,
        choices=list(VALID_CHOSEN_DOKS),
        default=None,
        help="DOK 1-3 only. REQUIRED when --disposition=change; rejected with confirm or needs-source-check.",
    )
    p_review.add_argument(
        "--rationale",
        default="",
        help="Required (non-empty) for change and needs-source-check; optional for confirm.",
    )
    p_review.add_argument(
        "--provenance",
        default="",
        help=(
            "calibration-anchor:<lesson>:<item-ref> resolves on disk against "
            "questionbank/calibration/ (rule-1-grade); free text is recorded "
            "but is rule-2-adjacent for a confirm. Required (non-empty) for "
            "change (rule 5: override needs BOTH rationale and provenance). "
            "Optional for confirm and needs-source-check."
        ),
    )
    p_review.add_argument(
        "--item-basis",
        choices=list(ITEM_BASES),
        default=None,
        help=(
            "Required (and ONLY valid) when --disposition=change. "
            "'textbook-exact' = source-dispute resolution (rules 1/2) -- "
            "verification-grade only when --provenance resolves on disk. "
            "adapted/split/extended/teacher-authored = rule-3 items rated by "
            "actual cognitive demand -- free-text provenance is acceptable."
        ),
    )
    p_review.add_argument(
        "--resolves-source-check",
        action="store_true",
        help=(
            "Attest that this entry's --provenance resolves the item_uid's "
            "most recent unresolved needs-source-check. Allowed only with "
            "confirm/change. Rejected at entry if there is no unresolved "
            "needs-source-check for this item_uid, or if --provenance does "
            "not resolve on disk."
        ),
    )
    p_review.add_argument(
        "--rubric-version",
        required=True,
        help='Recorded verbatim on the entry, e.g. "v0.2".',
    )
    p_review.add_argument("--note", default="")
    p_review.add_argument(
        "--reviewed-at", default=None,
        help="Strict ISO 8601 (datetime.fromisoformat); defaults to now (local, with offset). May not predate this item_uid's latest existing review.",
    )
    p_review.set_defaults(func=cmd_review)

    p_progress = sub.add_parser("progress", help="Print per-wave and overall review progress.")
    p_progress.add_argument("--json", action="store_true")
    p_progress.set_defaults(func=cmd_progress)

    p_promote = sub.add_parser(
        "promote",
        help="Emit a read-only promotion PROPOSAL (never writes the registry; re-derives everything against disk; proposals-only regardless of rubric state).",
    )
    p_promote.add_argument("--item-uid", required=True)
    p_promote.add_argument("--out", default=None, help="Override the proposal output path.")
    p_promote.set_defaults(func=cmd_promote)

    p_report = sub.add_parser("report", help="Write a static read-only HTML report.")
    p_report.add_argument("--out", default=None, help="Override the report output path.")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
