"""Crop student-facing figures for an ingested lesson and write skeletons/<L>_image_map.json.

Usage: python te_crop_figures.py [--dry-run] 1-3 [1-4 ...]

Walks the \\placeholder commands of a2_<L>_TE.tex in order (the same order and
numbering as te-transcription/figures/<L>.json), keeps those that sit in a
practice / tryit block before its \\answer (student-facing), crops each one from
the topic PDF at 200 dpi using clip_frac, saves questionbank/images/<L>_savvas_q<N>_<type>[_k].png
(or _tryit<N>_), and writes an image map keyed by registry row id, the format
qb_patch_images.py reads. Rows are matched in questionbank/registry.jsonl by source.
"""
import importlib.util
import json, re, sys
from pathlib import Path
import pymupdf

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ingest", ROOT / "ingest_lesson_from_latex.py")
ing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ing)
LESSON = ""
PDF_DIR = Path("C:/Users/rober/Downloads")
BS = "\\"
ENV_RE = re.compile(re.escape(BS) + r"(begin|end)\{(practice|tryit|example|te-addendum|model-discuss|concept-box|concept-summary|item-analysis|lesson-meta)\}((?:\{[^}]*\})*)")


def placeholders_in_order(tex):
    """Yield (index, block, type, student_facing, practice_or_tryit_number)."""
    events = [(m.start(), "env", m) for m in ENV_RE.finditer(tex)]
    events += [(m.start(), "ph", m) for m in re.finditer(re.escape(BS + "placeholder{") + r"(\w+)\}\{", tex)]
    events += [(m.start(), "ans", m) for m in re.finditer(re.escape(BS + "answer{"), tex)]
    events.sort(key=lambda e: e[0])
    block, idx, nth = None, 0, 0
    for _, kind, m in events:
        if kind == "env":
            if m.group(1) == "begin":
                args = re.findall(r"\{([^}]*)\}", m.group(3) or "")
                block, nth = (m.group(2), args), 0
            else:
                block = None
        elif kind == "ph":
            idx += 1
            if block is None:
                yield idx, block, m.group(1), False
                continue
            nth += 1
            # Same classification as the ingest parser: label says answer, or figure_roles.json override.
            j = m.end()
            depth, k = 1, j
            while k < len(tex) and depth:
                depth += {"{": 1, "}": -1}.get(tex[k], 0)
                k += 1
            desc = " ".join(tex[j:k - 1].split())
            key = f"{block[0]}{{{block[1][0]}}}#{nth}" if block[1] else f"{block[0]}#{nth}"
            role = ing.FIGURE_ROLES.get(LESSON, {}).get(key) or (
                "answer" if ing.ANSWER_FIGURE_RE.search(ing.figure_label(desc)) else "question")
            yield idx, block, m.group(1), role == "question"


def run(lesson, dry):
    global LESSON
    LESSON = lesson
    tex = (ROOT / f"a2_{lesson}_TE.tex").read_text(encoding="utf-8")
    figs = json.loads((ROOT / f"te-transcription/figures/{lesson}.json").read_text(encoding="utf-8"))
    by_idx = {}
    for key, v in figs.items():
        n = int(key.rsplit("_", 1)[1])
        by_idx[n] = v
    topic = int(lesson.split("-")[0])
    pdf = pymupdf.open(PDF_DIR / f"Topic_{topic:02d}_Teacher_Edition.pdf")
    registry = [json.loads(l) for l in (ROOT / "questionbank/registry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = {r["source"]: r["id"] for r in registry if r.get("lesson") == lesson}
    plan, missing = {}, []
    for idx, block, ptype, student in placeholders_in_order(tex):
        if not student or block[0] not in ("practice", "tryit"):
            continue
        num = block[1][0]
        label = f"Savvas Practice #{num}" if block[0] == "practice" else f"Savvas Try It {num}"
        rid = next((i for s, i in rows.items() if s == label or s.startswith(label + " ")), None)
        fig = by_idx.get(idx)
        if not fig:
            missing.append(f"{label} placeholder #{idx}: no crop box"); continue
        if rid is None:
            missing.append(f"{label}: no registry row yet"); continue
        plan.setdefault(rid, []).append((fig, ptype, block[0], num))
    out_map = {}
    for rid, figs_for_row in plan.items():
        paths = []
        for k, (fig, ptype, kind, num) in enumerate(figs_for_row):
            tag = f"q{num}" if kind == "practice" else f"tryit{num}"
            name = f"{lesson}_savvas_{tag}_{ptype}{'' if k == 0 else '_' + str(k + 1)}.png"
            rel = f"questionbank/images/{name}"
            if not dry:
                page = pdf[fig["pdf_page"] - 1]
                x0, y0, x1, y1 = fig["clip_frac"]
                r = page.rect
                clip = pymupdf.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height, r.x0 + x1 * r.width, r.y0 + y1 * r.height)
                page.get_pixmap(dpi=200, clip=clip).save(ROOT / rel)
            paths.append(rel)
        vt = figs_for_row[0][1] if figs_for_row[0][1] in ("graph", "diagram", "photo", "illustration", "map", "table-image") else "graph"
        entry = {"image": paths[0], "has_visual": True, "visual_type": vt, "visual_needs_cleanup": False,
                 "shared_with": [], "crop_source": f"pdf-p{figs_for_row[0][0]['pdf_page']}", "crop_frac": figs_for_row[0][0]["clip_frac"]}
        if len(paths) > 1:
            entry["images"] = paths
        out_map[rid] = entry
    if not dry:
        (ROOT / f"skeletons/{lesson}_image_map.json").write_text(json.dumps(out_map, indent=2) + "\n", encoding="utf-8")
    print(f"{lesson}: {len(out_map)} rows with images, {sum(len(v) for v in plan.values())} crops" + (f"; issues: {missing}" if missing else ""))


dry = "--dry-run" in sys.argv
for lesson in [a for a in sys.argv[1:] if not a.startswith("--")]:
    run(lesson, dry)
