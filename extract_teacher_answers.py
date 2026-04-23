"""Extract `\\teacheranswerbox{...}{BODY}` content from tex/*_teacher.tex and
match to registry item IDs via the `(lesson-id)` parenthetical in the preceding
`\\bankitem{LABEL (ID)}{...}{...}`.

Usage:
    python extract_teacher_answers.py           # dry-run: prints coverage + diffs
    python extract_teacher_answers.py --apply   # writes teacher_answer: field to registry
"""
from __future__ import annotations
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).parent
TEX = REPO / "tex"
REG = REPO / "questionbank" / "registry.jsonl"

ID_RX = re.compile(r"\(([0-9A-Za-z][\w\-\.]*)\)\s*\}")  # matches "(4-1-savvas-q23)}"


def find_matching_brace(text: str, open_idx: int) -> int:
    """Given index of an opening '{', return index of matching '}'."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def extract_block(text: str, macro: str, start: int) -> tuple[str, list[str], int] | None:
    """Find next `\\macro{arg1}{arg2}...` after position `start`.
    Returns (macro, [args], end_idx) or None."""
    pat = re.compile(r"\\" + re.escape(macro) + r"\s*\{")
    m = pat.search(text, start)
    if not m:
        return None
    args = []
    i = m.end() - 1  # points at the '{'
    while i < len(text) and text[i] == "{":
        end = find_matching_brace(text, i)
        if end < 0:
            return None
        args.append(text[i + 1 : end])
        i = end + 1
        # skip whitespace (and possibly trailing `%`) between arg groups
        while i < len(text) and text[i] in " \t\n%":
            if text[i] == "%":
                nl = text.find("\n", i)
                i = nl + 1 if nl >= 0 else len(text)
            else:
                i += 1
    return (macro, args, i)


def normalize_prompt(s: str) -> str:
    """Strip LaTeX junk + punctuation for fuzzy prompt matching.

    Registry prompts (plain text with unicode math like √) and tex prompts
    (\\sqrt{x}, \\(...\\)) must reduce to the same tokens so short prompts
    like `\\sqrt{4x}=11` can match their registry counterpart.
    """
    s = re.sub(r"\\[A-Za-z]+\*?\s*", " ", s)   # drop \macro names
    s = re.sub(r"\\[^A-Za-z\s]", " ", s)        # drop \( \) \[ \] \# \% etc
    s = re.sub(r"[{}%^_$]", " ", s)             # LaTeX structural chars
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)  # drop punctuation, keep alnum + unicode letters
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def fuzzy_match(norm_tex: str, prompt_idx: dict[str, str]) -> str | None:
    """Pick best registry id for a tex-prompt, or None if ambiguous.

    Two passes: (1) substring hit on the first 40 chars of a registry prompt
    (fast, high-confidence); (2) SequenceMatcher ratio on the full string,
    requiring top score ≥ 0.80 AND a margin ≥ 0.06 over second-best
    (ambiguous matches are refused to avoid false-positive clusters).
    """
    if not norm_tex:
        return None
    for norm_reg, rid in prompt_idx.items():
        if len(norm_reg) >= 40 and norm_reg[:80] in norm_tex:
            return rid
    top, second = (0.0, None), (0.0, None)
    for norm_reg, rid in prompt_idx.items():
        if len(norm_reg) < 12:
            continue
        score = SequenceMatcher(None, norm_reg, norm_tex).ratio()
        if score > top[0]:
            second = top
            top = (score, rid)
        elif score > second[0]:
            second = (score, rid)
    if top[0] >= 0.80 and (top[0] - second[0]) >= 0.06:
        return top[1]
    return None


def pairs_for(tex_path: Path, by_id: dict) -> list[tuple[str, str]]:
    """Return [(item_id, teacher_answer_body), ...] for one teacher .tex.

    Two-pass matching: first try `(id)` suffix in the bankitem label,
    then fall back to fuzzy prompt match against rows in the same lesson.
    """
    txt = tex_path.read_text(encoding="utf-8")
    # infer lesson from filename: L43_P2_teacher.tex -> 4-3
    m = re.match(r"L(\d)(\d)_P(\d)_teacher\.tex", tex_path.name)
    lesson = f"{m.group(1)}-{m.group(2)}" if m else None
    lesson_rows = (
        [r for r in by_id.values() if r.get("lesson") == lesson] if lesson else []
    )
    prompt_idx = {normalize_prompt(r.get("prompt", "")): r["id"] for r in lesson_rows}

    out: list[tuple[str, str]] = []
    pos = 0
    while True:
        got = extract_block(txt, "bankitem", pos)
        if not got:
            break
        _, args, end = got
        label = args[0] if args else ""
        prompt_body = args[1] if len(args) >= 2 else ""
        pos = end

        item_id = None
        idm = re.search(r"\(([\w\-\.]+)\)\s*$", label.strip())
        if idm and idm.group(1) in by_id:
            item_id = idm.group(1)
        else:
            item_id = fuzzy_match(normalize_prompt(prompt_body), prompt_idx)

        next_bank = re.search(r"\\bankitem\s*\{", txt[pos:])
        scan_end = pos + (next_bank.start() if next_bank else len(txt))
        ans = extract_block(txt[:scan_end], "teacheranswerbox", pos)
        if not ans:
            continue
        _, ans_args, _ = ans
        # \teacheranswerbox is defined [2] in most files (header + body) but [1]
        # in L54_P1 (body only). Fall back to arg 0 when only one arg was parsed.
        body = (
            ans_args[1] if len(ans_args) >= 2
            else ans_args[0] if len(ans_args) == 1
            else ""
        )
        body = body.strip().strip("%").strip()
        if body and item_id:
            out.append((item_id, body))

    # Dedupe within a single tex file: if an id was matched by multiple
    # bankitems (happens when fuzzy matches converge), drop it entirely —
    # we can't tell which body is the right one.
    id_counts: dict[str, int] = {}
    for iid, _ in out:
        id_counts[iid] = id_counts.get(iid, 0) + 1
    return [(iid, body) for iid, body in out if id_counts[iid] == 1]


def main() -> int:
    apply = "--apply" in sys.argv

    # load registry
    rows = [json.loads(l) for l in REG.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_id = {r["id"]: r for r in rows}

    all_pairs: dict[str, str] = {}
    collision_log: list[tuple[str, str, str]] = []  # (id, first-source, second-source)
    per_file: list[tuple[str, int]] = []
    source_of: dict[str, str] = {}
    for tex_path in sorted(TEX.glob("L*_teacher.tex")):
        pairs = pairs_for(tex_path, by_id)
        per_file.append((tex_path.name, len(pairs)))
        for iid, body in pairs:
            if iid in all_pairs:
                if all_pairs[iid] != body:
                    collision_log.append((iid, source_of[iid], tex_path.name))
                # first-writer-wins: do not overwrite
                continue
            all_pairs[iid] = body
            source_of[iid] = tex_path.name
    collisions = len(collision_log)

    in_reg = {iid: body for iid, body in all_pairs.items() if iid in by_id}
    missing = [iid for iid in all_pairs if iid not in by_id]
    would_fill = [iid for iid in in_reg if not by_id[iid].get("teacher_answer")]

    print("=== per-file extraction ===")
    for name, n in per_file:
        print(f"  {name}: {n}")
    print()
    print(f"unique ids extracted: {len(all_pairs)}")
    print(f"collisions (same id, different body — first-writer-wins): {collisions}")
    for iid, first, second in collision_log:
        print(f"    {iid}: kept {first}, skipped {second}")
    print(f"in registry: {len(in_reg)}  | not in registry: {len(missing)}")
    print(f"would backfill teacher_answer on: {len(would_fill)} rows")
    if missing:
        print("sample missing ids:", missing[:6])

    if not apply:
        print("\n(dry-run) re-run with --apply to write")
        return 0

    # Only fill empties — never overwrite an existing teacher_answer. Existing
    # values may have been hand-polished (\textbf, \dfrac) after earlier runs;
    # re-extraction should not downgrade them.
    for iid, body in in_reg.items():
        if not by_id[iid].get("teacher_answer"):
            by_id[iid]["teacher_answer"] = body

    with REG.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nWrote {REG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
