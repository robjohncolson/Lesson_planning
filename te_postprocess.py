"""Add Lesson Quiz calibration to a fresh ingest of a2_<lesson>_TE.tex (2024 TE transcription).

Usage: python te_postprocess.py 1-3 [1-4 ...]

Adds lesson_quiz_item_analysis {item: DOK} and lesson_quiz_skills_review {item: [codes]}
from the Lesson Quiz Item Analysis table in the te-addendum{Assess}{...} blocks, plus a
provenance note, to questionbank/calibration/<lesson>.json. Figure roles (question figure
vs answer graph) are decided in ingest_lesson_from_latex.py, not here.
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
BS = "\\"


def blocks(tex, env, nargs):
    pat = re.escape(BS + "begin{" + env + "}") + r"((?:\{[^}]*\}){%d})(.*?)" % nargs + re.escape(BS + "end{" + env + "}")
    return re.finditer(pat, tex, re.S)


def quiz_item_analysis(tex):
    dok, skills = {}, {}
    for m in blocks(tex, "te-addendum", 2):
        if "{Assess}" not in m.group(1):
            continue
        for t in re.finditer(re.escape(BS + "begin{tabular}") + r"\{[^}]*\}(.*?)" + re.escape(BS + "end{tabular}"), m.group(2), re.S):
            rows = [r.strip() for r in t.group(1).split(BS + BS)]
            if not rows or not re.match(r"Item\s*&\s*DOK", rows[0]):
                continue
            for r in rows[1:]:
                cells = [c.strip() for c in r.split("&")]
                if len(cells) >= 2 and cells[0].isdigit() and cells[1].strip()[:1].isdigit():
                    dok[cells[0]] = int(cells[1].strip()[0])
                    if len(cells) >= 3 and cells[2]:
                        skills[cells[0]] = [c.strip() for c in re.split(r"[,;]", cells[2]) if c.strip()]
    return dok, skills


def run(lesson):
    tex = (ROOT / f"a2_{lesson}_TE.tex").read_text(encoding="utf-8")
    cal_p = ROOT / f"questionbank/calibration/{lesson}.json"
    cal = json.loads(cal_p.read_text(encoding="utf-8"))
    dok, skills = quiz_item_analysis(tex)
    cal["lesson_quiz_item_analysis"] = dok
    cal["lesson_quiz_skills_review"] = skills
    cal["notes"] = (f"Generated 2026-10-01 from a2_{lesson}_TE.tex, the Codex transcription of the 2024 enVision "
                    f"Algebra 2 Teacher Edition (te-transcription/manifest_topic{int(lesson.split('-')[0]):02d}.json "
                    f"gives the PDF pages). item_analysis is the Practice & Problem Solving Item Analysis table; "
                    f"lesson_quiz_* come from the Lesson Quiz Item Analysis table.")
    cal_p.write_text(json.dumps(cal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{lesson}: quiz items {len(dok)} (DOK {dok}), skills {skills}")


for lesson in sys.argv[1:]:
    run(lesson)
