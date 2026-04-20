"""One-off: backfill visual_type / visual_needs_cleanup / visual_clean_asset
on existing Lesson 4-1 registry entries. Idempotent — safe to re-run."""
import json
from pathlib import Path

REG = Path("questionbank/registry.jsonl")

# Mapping: id_suffix -> (visual_type, needs_cleanup, clean_asset)
# Ids are matched by substring on the full registry id (prefix 4-1-...).
# needs_cleanup=True means the source screenshot contains either:
#   (a) an answer-key leak (margin commentary revealing the answer), or
#   (b) multiple items on one page (e.g., Ex2 and TryIt2 share a page).
MAPPING = {
    # Launch
    "model-discuss-lesson-4-1-launch": ("diagram", False, None),

    # Examples (worked; teacher-reference): image shows answer in SE margin.
    # For intended use (modeling on teacher packet / pacer), leak is OK.
    "example-1-lesson-4-1-identify-inv":        ("table",   True,  None),
    "example-2-lesson-4-1-use-inverse-":        ("none",    True,  None),
    "example-3-lesson-4-1-use-an-inver":        ("photo",   True,  None),
    "example-4-lesson-4-1-understand-t":        ("graph",   True,  None),
    "example-5-lesson-4-1-graph-transl":        ("graph",   True,  None),

    # Try Its share a page with their Example → source leaks Example answer
    "try-it-1-lesson-4-1-matches-examp":        ("table",   False, None),  # standalone page
    "try-it-2-lesson-4-1-matches-examp":        ("none",    True,  None),  # same page as Ex 2
    "try-it-3-lesson-4-1-matches-examp":        ("none",    True,  None),  # same page as Ex 3
    "try-it-4-lesson-4-1-matches-examp":        ("none",    True,  None),  # same page as Ex 4
    "try-it-5-lesson-4-1-matches-examp":        ("none",    True,  None),  # same page as Ex 5

    # Concept / reference
    "concept-box-inverse-variation-les":        ("table",   False, None),

    # Teacher-Edition addenda (teacher-only; leaks OK)
    "teacher-s-edition-example-1-pose-":        ("none",    False, None),
    "teacher-s-edition-try-it-1-answer":        ("none",    False, None),
    "teacher-s-edition-example-2-conne":        ("none",    False, None),
    "teacher-s-edition-example-2-commo":        ("none",    False, None),
    "teacher-s-edition-habits-of-mind-":        ("none",    False, None),
    "teacher-s-edition-example-3-purpo":        ("none",    False, None),
    "teacher-s-edition-example-3-elici":        ("none",    False, None),
    "teacher-s-edition-ell-addendum-fo":        ("none",    False, None),
    "teacher-s-edition-example-4-purpo":        ("none",    False, None),
    "teacher-s-edition-try-it-4-answer":        ("graph",   False, None),
    "teacher-s-edition-rti-support-str":        ("none",    False, None),
    "teacher-edition-example-5-use-and":        ("graph",   False, None),
    "teacher-edition-example-5-elicit-":        ("none",    False, None),
    "teacher-edition-habits-of-mind-co":        ("none",    False, None),
    "teacher-edition-rti-extend-studen":        ("none",    False, None),

    # DOK-3 practice items
    "4-1-savvas-q20": ("none", False, None),
    "4-1-savvas-q22": ("none", False, None),
    "4-1-savvas-q25": ("none", False, None),
    "4-1-savvas-q26": ("map",  False, None),
}


def match(entry_id: str) -> tuple[str, bool, str | None] | None:
    # exact-id match first
    if entry_id in MAPPING:
        return MAPPING[entry_id]
    # else, substring match on the suffix keys
    for key, spec in MAPPING.items():
        if key.startswith("4-1-"):
            continue  # exact-only
        if key in entry_id:
            return spec
    return None


def main() -> None:
    lines = REG.read_text(encoding="utf-8").splitlines()
    changed = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("lesson") != "4-1":
            continue
        spec = match(entry["id"])
        if spec is None:
            print(f"WARN: no mapping for {entry['id']}")
            continue
        vt, cleanup, clean_asset = spec
        # only write if changed
        if (entry.get("visual_type") == vt
                and entry.get("visual_needs_cleanup") == cleanup
                and entry.get("visual_clean_asset") == clean_asset):
            continue
        entry["visual_type"] = vt
        entry["visual_needs_cleanup"] = cleanup
        entry["visual_clean_asset"] = clean_asset
        lines[i] = json.dumps(entry, ensure_ascii=False)
        changed += 1
    REG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {changed} Lesson 4-1 entries.")


if __name__ == "__main__":
    main()
