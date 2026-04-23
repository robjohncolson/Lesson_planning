"""Klimsara Teacher Console — localhost-only Flask backend.
Usage: python console.py [--no-open] [--port PORT]
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

import yaml
from flask import Flask, Response, abort, jsonify, request, send_file

REPO_ROOT = Path(__file__).resolve().parent
TEX_DIR = REPO_ROOT / "tex"
LESSONS_DIR = REPO_ROOT / "lessons"
STATIC_DIR = REPO_ROOT / "console_static"
REGISTRY_PATH = REPO_ROOT / "questionbank" / "registry.jsonl"

app = Flask(__name__, static_folder=None)
_LESSON_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")  # must start alphanumeric — blocks `-flag`-style injection into pdflatex argv


def _validate_lesson_id(lesson_id: str) -> None:
    if not _LESSON_ID_RE.match(lesson_id):
        abort(400, description=f"Invalid lesson_id: {lesson_id!r}")


def _safe_path(base: Path, *parts: str) -> Path:
    """Resolve path and abort 403 if it escapes base."""
    candidate = base.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        abort(403, description="Path traversal denied")
    return candidate


def _read_yaml_meta(lesson_id: str) -> dict:
    """Return parsed YAML dict for lesson_id, or {} on any error."""
    p = LESSONS_DIR / f"{lesson_id}.yaml"
    if not p.exists():
        return {}
    try:
        with p.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _scan_lessons() -> list[dict]:
    """Build lesson catalogue from tex/ and lessons/."""
    lesson_ids: set[str] = set()
    if TEX_DIR.exists():
        for f in TEX_DIR.glob("*_student.tex"):
            lesson_ids.add(f.stem.removesuffix("_student"))
    if LESSONS_DIR.exists():
        for f in LESSONS_DIR.glob("*.yaml"):
            lesson_ids.add(f.stem)

    results = []
    for lid in sorted(lesson_ids):
        meta = _read_yaml_meta(lid)
        has_yaml = bool(meta) or (LESSONS_DIR / f"{lid}.yaml").exists()
        results.append({
            "lesson_id": lid,
            "cadence": meta.get("cadence", "unknown") if meta else "unknown",
            "has_yaml": has_yaml,
            "has_student_pdf": (TEX_DIR / f"{lid}_student.pdf").exists(),
            "has_teacher_pdf": (TEX_DIR / f"{lid}_teacher.pdf").exists(),
            "has_slides_pdf": (TEX_DIR / f"{lid}_slides.pdf").exists(),
            "has_pacer_html": (REPO_ROOT / f"{lid}_Pacer.html").exists(),
            "title": meta.get("title") or None,
        })
    return results


def _load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    rows = []
    with REGISTRY_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def _registry_row_to_api(row: dict) -> dict:
    topics = row.get("topics") or []
    tags = row.get("tags") or []
    return {
        "id": row.get("id", ""),
        "lesson": row.get("lesson", ""),
        "source": row.get("source", ""),
        "dok": row.get("dok"),
        "role": row.get("role", ""),
        "skill_tokens": list(set(topics + tags)),
        "prompt": (row.get("prompt") or "")[:200],
        "has_answers": bool(row.get("answers")),
    }



# ── Routes ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    idx = _safe_path(STATIC_DIR, "index.html")
    if not idx.exists():
        return Response(
            "<h1>Teacher Console</h1><p>Frontend not yet installed.</p>",
            mimetype="text/html",
        )
    return send_file(idx)


@app.route("/static/<path:filename>")
def static_files(filename):
    path = _safe_path(STATIC_DIR, filename)
    if not path.exists():
        abort(404)
    return send_file(path)


@app.route("/api/health")
def api_health():
    lessons = _scan_lessons()
    registry = _load_registry()
    return jsonify({"ok": True, "lessons": len(lessons), "registry_rows": len(registry)})


@app.route("/api/lessons")
def api_lessons():
    return jsonify(_scan_lessons())


@app.route("/api/lesson/<lesson_id>/yaml", methods=["GET"])
def api_lesson_yaml_get(lesson_id: str):
    _validate_lesson_id(lesson_id)
    yaml_path = _safe_path(LESSONS_DIR, f"{lesson_id}.yaml")
    if not yaml_path.exists():
        abort(404, description="No YAML spec for this lesson")
    return Response(yaml_path.read_text(encoding="utf-8"), mimetype="text/plain")


@app.route("/api/lesson/<lesson_id>/yaml", methods=["PUT"])
def api_lesson_yaml_put(lesson_id: str):
    _validate_lesson_id(lesson_id)
    yaml_path = _safe_path(LESSONS_DIR, f"{lesson_id}.yaml")
    raw = request.get_data(as_text=True)
    # Validate YAML before writing
    try:
        yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    # Atomic write: temp file in same dir, then os.replace (avoids truncated YAML on crash / disk-full)
    tmp_path = yaml_path.with_suffix(yaml_path.suffix + ".tmp")
    tmp_path.write_text(raw, encoding="utf-8")
    os.replace(tmp_path, yaml_path)
    return jsonify({"ok": True})


def _read_tex(stem: str) -> str:
    p = TEX_DIR / f"{stem}.tex"
    try:
        return p.read_text(encoding="utf-8") if p.exists() else ""
    except OSError:
        return ""


def _unified_diff(before: str, after: str, label: str) -> str:
    """Return unified diff, or empty string if no change."""
    if before == after:
        return ""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{label} (before)",
            tofile=f"{label} (after)",
            n=3,
        )
    )


@app.route("/api/lesson/<lesson_id>/regenerate", methods=["POST"])
def api_lesson_regenerate(lesson_id: str):
    _validate_lesson_id(lesson_id)

    yaml_path = _safe_path(LESSONS_DIR, f"{lesson_id}.yaml")
    if not yaml_path.exists():
        return jsonify({"ok": False, "error": "No YAML spec found"}), 404

    # Capture pre-regen tex for diff
    before_student = _read_tex(f"{lesson_id}_student")
    before_teacher = _read_tex(f"{lesson_id}_teacher")

    log_tail: list[str] = []
    build_result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "build_lesson_from_yaml.py"), str(yaml_path)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        shell=False,
        timeout=60,
    )
    if build_result.returncode != 0:
        err_lines = (build_result.stdout + build_result.stderr).splitlines()
        return jsonify(
            {
                "ok": False,
                "error": "build_lesson_from_yaml failed",
                "log_tail": err_lines[-50:],
            }
        ), 500

    def run_pdflatex(stem: str) -> "tuple[bool, list[str]]":
        tex_file = TEX_DIR / f"{stem}.tex"
        if not tex_file.exists():
            return False, [f"{tex_file} not found after YAML build"]
        for _pass in range(2):
            r = subprocess.run(
                ["pdflatex", "--miktex-enable-installer", "-halt-on-error",
                 "-interaction=nonstopmode", tex_file.name],
                cwd=str(TEX_DIR), capture_output=True, text=True,
                shell=False, timeout=30,
            )
            if r.returncode != 0:
                return False, r.stdout.splitlines()[-50:]
        return True, []

    student_ok, student_log = run_pdflatex(f"{lesson_id}_student")
    teacher_ok, teacher_log = run_pdflatex(f"{lesson_id}_teacher")

    overall_ok = student_ok and teacher_ok
    if not overall_ok:
        log_tail = student_log if not student_ok else teacher_log

    student_pdf = str(TEX_DIR / f"{lesson_id}_student.pdf") if student_ok else None
    teacher_pdf = str(TEX_DIR / f"{lesson_id}_teacher.pdf") if teacher_ok else None

    # Diff post-regen tex against pre-regen snapshot
    after_student = _read_tex(f"{lesson_id}_student")
    after_teacher = _read_tex(f"{lesson_id}_teacher")
    diff = {
        "student_tex": _unified_diff(before_student, after_student, f"{lesson_id}_student.tex"),
        "teacher_tex": _unified_diff(before_teacher, after_teacher, f"{lesson_id}_teacher.tex"),
    }

    return jsonify(
        {
            "ok": overall_ok,
            "student_pdf": student_pdf,
            "teacher_pdf": teacher_pdf,
            "log_tail": log_tail,
            "diff": diff,
        }
    )


def _serve_pdf(path: Path) -> Response:
    if not path.exists():
        abort(404)
    return send_file(path, mimetype="application/pdf", as_attachment=False,
                     download_name=path.name)


@app.route("/api/pdf/<lesson_id>/<edition>")
def api_pdf(lesson_id: str, edition: str):
    _validate_lesson_id(lesson_id)
    if edition not in ("student", "teacher"):
        abort(400, description="edition must be 'student' or 'teacher'")
    return _serve_pdf(_safe_path(TEX_DIR, f"{lesson_id}_{edition}.pdf"))


@app.route("/api/slides/<lesson_id>")
def api_slides(lesson_id: str):
    _validate_lesson_id(lesson_id)
    return _serve_pdf(_safe_path(TEX_DIR, f"{lesson_id}_slides.pdf"))


@app.route("/api/pacer/<lesson_id>")
def api_pacer(lesson_id: str):
    _validate_lesson_id(lesson_id)
    pacer_path = _safe_path(REPO_ROOT, f"{lesson_id}_Pacer.html")
    if not pacer_path.exists():
        abort(404)
    return send_file(pacer_path, mimetype="text/html")


@app.route("/api/registry")
def api_registry():
    rows = _load_registry()
    lesson_f = request.args.get("lesson", "").strip()
    skill_f = request.args.get("skill", "").strip().lower()
    dok_f = request.args.get("dok", "").strip()
    q_f = request.args.get("q", "").strip().lower()

    dok_int: "int | None" = None
    if dok_f:
        try:
            dok_int = int(dok_f)
        except ValueError:
            return jsonify({"error": "dok must be 1, 2, or 3"}), 400

    results = []
    for row in rows:
        if lesson_f and not str(row.get("lesson", "")).startswith(lesson_f):
            continue
        if dok_int is not None and row.get("dok") != dok_int:
            continue
        if skill_f:
            tokens = [t.lower() for t in (row.get("topics") or []) + (row.get("tags") or [])]
            if not any(skill_f in t for t in tokens):
                continue
        if q_f and q_f not in (row.get("prompt") or "").lower():
            continue
        results.append(_registry_row_to_api(row))
        if len(results) >= 200:
            break
    return jsonify(results)



@app.after_request
def add_cache_control(response: Response) -> Response:
    if request.path.startswith(("/api/pdf/", "/api/slides/")):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def json_error(exc):
    code = getattr(exc, "code", 500)
    desc = getattr(exc, "description", str(exc))
    return jsonify({"error": desc}), code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Klimsara Teacher Console")
    parser.add_argument("--no-open", action="store_true", help="Skip browser launch")
    parser.add_argument("--port", type=int, default=5173, help="Port (default 5173)")
    args = parser.parse_args()

    url = f"http://127.0.0.1:{args.port}"
    print(f"Teacher Console running at {url}  (Ctrl+C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    app.run(host="127.0.0.1", port=args.port, debug=False)
