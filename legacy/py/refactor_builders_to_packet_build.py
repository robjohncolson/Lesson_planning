"""One-shot refactor: rewrite every build_L*_P*_packets.py to use packet_build.

Transformation applied:
  1. Replace the top-of-file imports block (docx imports + TABLE_STYLE constant)
     with a single `from packet_build import ...` line.
  2. Delete the four helper function definitions (set_cell, add_callout,
     bank_item_block, add_header_block) + the "# ── Helpers ──" banner.
  3. Insert a _header() wrapper that closes over the lesson's module-level
     LESSON_TITLE / LESSON_LABEL / OBJECTIVES / FRAMEWORK_HEADER.
  4. Replace every inline margin-setup block:
         doc = Document()
         for section in doc.sections:
             section.top_margin = Inches(T)
             ...
     with a `doc = new_packet_doc(top=T, bottom=B, left=L, right=R)` call.
  5. Rewrite `add_header_block(doc, for_teacher=X)` call sites → `_header(doc, for_teacher=X)`.

Each builder is then built; output docx's `word/document.xml` is hashed and
compared to its pre-refactor hash. Any mismatch is reported; on success the
refactor is kept.

Usage:  python refactor_builders_to_packet_build.py
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
BUILDERS = sorted(ROOT.glob("build_L*_packets.py"))

IMPORT_INSERT_AFTER = re.compile(r"^import packet_styles as ps\s*\n", re.MULTILINE)
IMPORT_INSERT = (
    "from packet_build import (\n"
    "    TABLE_STYLE, new_packet_doc,\n"
    "    set_cell, add_callout, bank_item_block, add_header_block,\n"
    ")\n"
)
TABLE_STYLE_LINE = re.compile(r"^TABLE_STYLE\s*=\s*\"Table Grid\"\s*\n", re.MULTILINE)
DOCX_CORE_IMPORTS = re.compile(
    r"^from docx import Document\s*\n"
    r"from docx\.shared import Pt, Inches, RGBColor\s*\n",
    re.MULTILINE,
)

# Helpers block: from `# ── Helpers` banner (optional) or first `def set_cell`,
# through end of `def add_header_block` body (up to the next banner/def/section).
HELPERS_BLOCK = re.compile(
    r"(?:# ── (?:Helpers|Low-level helpers)[^\n]*\n\s*\n)?"
    r"def set_cell\(.*?"
    r"(?=^# ── (?:Do Now|Student|Teacher|Main)\b|^def build_)",
    re.DOTALL | re.MULTILINE,
)

HEADER_WRAPPER_TEMPLATE = (
    "def _header(doc, *, for_teacher=False):\n"
    "    add_header_block(doc, lesson_title=LESSON_TITLE, lesson_label=LESSON_LABEL,\n"
    "                     objectives=OBJECTIVES, framework_header=FRAMEWORK_HEADER,\n"
    "                     for_teacher=for_teacher, day_number={day})\n"
    "\n\n"
)

DAY_NUMBER_IN_HEADER = re.compile(
    r"def add_header_block\(.*?ps\.day_banner\(doc,\s*(\d+),",
    re.DOTALL,
)

MARGIN_BLOCK = re.compile(
    r"    doc = Document\(\)\s*\n"
    r"    for section in doc\.sections:\s*\n"
    r"        section\.top_margin = Inches\(([\d.]+)\)\s*\n"
    r"        section\.bottom_margin = Inches\(([\d.]+)\)\s*\n"
    r"        section\.left_margin = Inches\(([\d.]+)\)\s*\n"
    r"        section\.right_margin = Inches\(([\d.]+)\)\s*\n"
)


def hash_docxml(docx: Path) -> str | None:
    if not docx.exists():
        return None
    try:
        with zipfile.ZipFile(docx) as z:
            return hashlib.sha256(z.read("word/document.xml")).hexdigest()
    except (KeyError, zipfile.BadZipFile):
        return None


def baseline_and_build(builder: Path) -> dict[str, str | None]:
    """Build and return {output_name: docxml_sha256} for .docx outputs."""
    subprocess.run([sys.executable, builder.name], cwd=ROOT, check=True,
                   capture_output=True, encoding="utf-8", errors="replace")
    prefix = re.match(r"build_(L\d+_P\d+)_packets\.py", builder.name).group(1)
    outs = {}
    for kind in ("Do_Now", "Student_Packet", "Teacher_Packet"):
        p = ROOT / f"{prefix}_{kind}.docx"
        outs[p.name] = hash_docxml(p)
    return outs


def refactor_source(src: str) -> str | None:
    """Apply the 5-step transform. Returns None if any step fails to match."""
    # 1. Imports — insert `from packet_build import ...` after the
    # `import packet_styles as ps` line, and strip the now-redundant
    # `from docx import Document`, `from docx.shared import ...`, and
    # `TABLE_STYLE = "Table Grid"` lines.
    if "from packet_build import" in src:
        return src  # already refactored
    if not IMPORT_INSERT_AFTER.search(src):
        return None
    src = IMPORT_INSERT_AFTER.sub(
        lambda m: m.group(0) + IMPORT_INSERT, src, count=1
    )
    src = DOCX_CORE_IMPORTS.sub("", src, count=1)
    src = TABLE_STYLE_LINE.sub("", src, count=1)

    # 2. Extract the day_number literal from the original add_header_block, then
    # remove the 4 helper functions and splice in a _header wrapper that passes
    # the original day_number through.
    m = DAY_NUMBER_IN_HEADER.search(src)
    day_number = int(m.group(1)) if m else 2
    header_wrapper = HEADER_WRAPPER_TEMPLATE.format(day=day_number)
    if not HELPERS_BLOCK.search(src):
        return None
    src = HELPERS_BLOCK.sub(header_wrapper, src, count=1)

    # 3. Margin blocks → new_packet_doc
    def _margin_sub(m):
        t, b, l, r = m.groups()
        return f"    doc = new_packet_doc(top={t}, bottom={b}, left={l}, right={r})\n"

    src = MARGIN_BLOCK.sub(_margin_sub, src)

    # 4. add_header_block(doc, for_teacher=...) → _header(doc, for_teacher=...)
    src = re.sub(
        r"\badd_header_block\(doc, for_teacher=",
        "_header(doc, for_teacher=",
        src,
    )

    return src


def main() -> int:
    print(f"Refactoring {len(BUILDERS)} builders...")
    failed = []
    for b in BUILDERS:
        src = b.read_text(encoding="utf-8")
        if "from packet_build import" in src and "def set_cell" not in src:
            print(f"  - {b.name}: already refactored, skipping")
            continue
        try:
            before = baseline_and_build(b)
        except subprocess.CalledProcessError as e:
            print(f"  ! {b.name}: baseline build failed: {e}")
            failed.append(b.name)
            continue

        new_src = refactor_source(src)
        if new_src is None:
            print(f"  ! {b.name}: refactor regex failed to match; skipped")
            failed.append(b.name)
            continue
        b.write_text(new_src, encoding="utf-8")

        try:
            after = baseline_and_build(b)
        except subprocess.CalledProcessError as e:
            print(f"  ! {b.name}: POST-REFACTOR BUILD FAILED, reverting. err={e}")
            b.write_text(src, encoding="utf-8")
            failed.append(b.name)
            continue

        if before == after:
            print(f"  + {b.name}: byte-identical ({len(src)} -> {len(new_src)} chars)")
        else:
            print(f"  ! {b.name}: OUTPUT DIFFERS — reverting")
            for k in before:
                if before[k] != after[k]:
                    print(f"      {k}: {before[k]} -> {after[k]}")
            b.write_text(src, encoding="utf-8")
            failed.append(b.name)

    print()
    print(f"Refactored {len(BUILDERS) - len(failed)}/{len(BUILDERS)} builders.")
    if failed:
        print("Failed:")
        for f in failed:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
