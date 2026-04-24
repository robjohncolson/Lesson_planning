"""Railway pdflatex build service for the Teacher Console.

Endpoints:
  GET  /health                        — smoke test
  POST /build/{lesson_id}             — read tex from Supabase, compile, upload PDFs
  PUT  /tex/{lesson_id}/{edition}     — write tex source back to Supabase

Auth: X-Passcode header must match REBUILD_PASSCODE env var.

Uses `requests` (HTTP/1.1) directly against Supabase REST + Storage APIs,
not supabase-py. supabase-py's httpx-based HTTP/2 client intermittently
trips StreamReset errors against Supabase's Cloudflare edge.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
REBUILD_PASSCODE = os.environ["REBUILD_PASSCODE"]

LESSON_ID_RE = re.compile(r"^L\d{2}_P\d$")
EDITIONS = {"student", "teacher", "slides", "do_now"}

HERE = Path(__file__).parent
PREAMBLE_STY = HERE / "preamble.sty"
BEAMER_STY = HERE / "beamer_preamble.sty"
YAML_BUILDER = HERE / "build_lesson_from_yaml.py"

SCHEMA = "lesson_planning"
BUCKET = "lesson-pdfs"

_REST_HEADERS_BASE = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept-Profile": SCHEMA,
    "Content-Profile": SCHEMA,
}


def _rest_headers(user_name: str | None = None) -> dict:
    h = dict(_REST_HEADERS_BASE)
    if user_name:
        h["x-user-name"] = user_name
    return h

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["Content-Type", "X-Passcode", "X-User-Name", "If-Match-Sha"],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
)


# ---------------------------------------------------------------------------
# Supabase REST helpers (plain requests — HTTP/1.1)
# ---------------------------------------------------------------------------

def _rest_get_lesson(lesson_id: str, user_name: str | None = None) -> dict | None:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/lessons",
        headers=_rest_headers(user_name),
        params={"id": f"eq.{lesson_id}",
                "select": "tex_student,tex_teacher,tex_slides,tex_do_now,yaml_text"},
        timeout=15,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


def _rest_update_lesson(lesson_id: str, patch: dict, user_name: str | None = None) -> None:
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/lessons",
        headers={**_rest_headers(user_name), "Content-Type": "application/json",
                 "Prefer": "return=minimal"},
        params={"id": f"eq.{lesson_id}"},
        json=patch,
        timeout=15,
    )
    r.raise_for_status()


def _rest_last_audit_changed_by(lesson_id: str) -> str | None:
    """Return the most recent changed_by for a lessons row, or None on any error."""
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/audit",
            headers=_rest_headers(),
            params={
                "table_name": "eq.lessons",
                "row_id": f"eq.{lesson_id}",
                "select": "changed_by",
                "order": "changed_at.desc",
                "limit": "1",
            },
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return None
        return rows[0].get("changed_by")
    except Exception:
        return None


def _storage_upload(object_path: str, body: bytes, content_type: str) -> None:
    """Upload (or replace) an object in Supabase Storage. x-upsert: true so a
    previous PDF is overwritten cleanly."""
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{object_path}",
        headers={
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
            "Content-Type": content_type,
            "x-upsert": "true",
        },
        data=body,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"storage upload {object_path}: {r.status_code} {r.text[:200]}")


def _storage_public_url(object_path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{object_path}"


# ---------------------------------------------------------------------------
# Validation + auth helpers
# ---------------------------------------------------------------------------

def _check_passcode(x_passcode: str | None) -> None:
    if x_passcode != REBUILD_PASSCODE:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Passcode")


def _validate_lesson_id(lesson_id: str) -> None:
    if not LESSON_ID_RE.match(lesson_id):
        raise HTTPException(status_code=400, detail="lesson_id must match L##_P# (e.g. L41_P2)")


def _validate_edition(edition: str) -> None:
    if edition not in EDITIONS:
        raise HTTPException(status_code=400, detail="edition must be 'student', 'teacher', 'slides', or 'do_now'")


# ---------------------------------------------------------------------------
# pdflatex runner
# ---------------------------------------------------------------------------

def _run_pdflatex(tex_name: str, work_dir: Path) -> tuple[bool, str]:
    """Run pdflatex twice on tex_name inside work_dir. Returns (ok, log_tail).

    TimeoutExpired is caught and treated as a build failure with a log tail —
    an uncaught exception 500s the request and skips the last_build_log write.
    """
    for _ in range(2):
        try:
            r = subprocess.run(
                ["pdflatex", "-halt-on-error", "-interaction=nonstopmode", tex_name],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            captured = (exc.stdout or "") + (exc.stderr or "")
            return False, (captured[-4096:] if captured else f"{tex_name}: pdflatex timed out after 60s")
        if r.returncode != 0:
            combined = r.stdout + r.stderr
            return False, (combined[-4096:] if len(combined) > 4096 else combined)
    return True, ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_build_status(
    lesson_id: str,
    *,
    ok: bool,
    log_tail: str,
    has_pdf_student: bool = False,
    has_pdf_teacher: bool = False,
    has_slides: bool = False,
    user_name: str | None = None,
) -> None:
    payload: dict = {
        "last_build_at": datetime.now(timezone.utc).isoformat(),
        "last_build_ok": ok,
        "last_build_log": log_tail if not ok else "",
    }
    if has_pdf_student or has_pdf_teacher:
        payload["has_pdf_student"] = has_pdf_student
        payload["has_pdf_teacher"] = has_pdf_teacher
    if has_slides:
        payload["has_slides_pdf"] = True
    try:
        _rest_update_lesson(lesson_id, payload, user_name)
    except Exception as exc:
        log.error("Failed to write build status for %s: %s", lesson_id, exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    r = subprocess.run(
        ["pdflatex", "--version"],
        capture_output=True,
        text=True,
    )
    first_line = r.stdout.splitlines()[0] if r.stdout else "pdflatex not found"
    return {"ok": True, "tex": first_line}


@app.post("/build/{lesson_id}")
def build(
    lesson_id: str,
    x_passcode: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
) -> dict:
    _validate_lesson_id(lesson_id)
    _check_passcode(x_passcode)

    row = _rest_get_lesson(lesson_id, x_user_name)
    if not row:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    tex_student = row.get("tex_student")
    tex_teacher = row.get("tex_teacher")
    tex_slides = row.get("tex_slides")
    tex_do_now = row.get("tex_do_now")
    yaml_text = row.get("yaml_text")

    if not yaml_text and not tex_student and not tex_teacher and not tex_slides and not tex_do_now:
        raise HTTPException(
            status_code=422,
            detail="Lesson has no yaml_text and no tex sources; nothing to build",
        )

    log_tail = ""
    student_ok = False
    teacher_ok = False
    slides_ok = False
    do_now_ok = False
    pdf_student_url = None
    pdf_teacher_url = None
    pdf_slides_url = None
    pdf_do_now_url = None

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # Shared style files into temp dir so pdflatex finds them
        if PREAMBLE_STY.exists():
            (tmp / "preamble.sty").write_bytes(PREAMBLE_STY.read_bytes())
        if BEAMER_STY.exists():
            (tmp / "beamer_preamble.sty").write_bytes(BEAMER_STY.read_bytes())

        # Source-of-truth policy:
        #   - Stored tex wins when present; web edits persist through rebuilds.
        #   - Only regenerate from YAML when neither tex edition is stored.
        if tex_student or tex_teacher:
            if tex_student:
                (tmp / f"{lesson_id}_student.tex").write_text(tex_student, encoding="utf-8")
            if tex_teacher:
                (tmp / f"{lesson_id}_teacher.tex").write_text(tex_teacher, encoding="utf-8")
        elif yaml_text:
            try:
                import yaml as _yaml
                parsed = _yaml.safe_load(yaml_text) or {}
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f"Invalid YAML: {exc}")
            yaml_lid = (parsed.get("lesson_id") or "").strip()
            if yaml_lid and yaml_lid != lesson_id:
                raise HTTPException(
                    status_code=422,
                    detail=f"YAML lesson_id ({yaml_lid!r}) must match route lesson_id ({lesson_id!r})",
                )

            yaml_path = tmp / f"{lesson_id}.yaml"
            yaml_path.write_text(yaml_text, encoding="utf-8")

            gen_result = subprocess.run(
                [sys.executable, str(YAML_BUILDER), str(yaml_path)],
                cwd=str(HERE),
                capture_output=True,
                text=True,
                timeout=60,
            )
            gen_out = gen_result.stdout + gen_result.stderr
            if gen_result.returncode != 0:
                log.error("build_lesson_from_yaml failed for %s", lesson_id)
                _write_build_status(lesson_id, ok=False, log_tail=gen_out[-4096:],
                                    user_name=x_user_name)
                return {"ok": False, "log_tail": gen_out[-4096:],
                        "pdf_student_url": None, "pdf_teacher_url": None,
                        "pdf_slides_url": None, "pdf_do_now_url": None}

            gen_student = HERE / "tex" / f"{lesson_id}_student.tex"
            gen_teacher = HERE / "tex" / f"{lesson_id}_teacher.tex"
            if gen_student.exists():
                (tmp / f"{lesson_id}_student.tex").write_bytes(gen_student.read_bytes())
            if gen_teacher.exists():
                (tmp / f"{lesson_id}_teacher.tex").write_bytes(gen_teacher.read_bytes())

        # --- student ---
        student_tex = tmp / f"{lesson_id}_student.tex"
        if student_tex.exists():
            student_ok, student_log = _run_pdflatex(student_tex.name, tmp)
            if not student_ok:
                log_tail = student_log
        else:
            student_ok = False
            log_tail = f"{lesson_id}_student.tex not found"

        # --- teacher ---
        teacher_tex = tmp / f"{lesson_id}_teacher.tex"
        if teacher_tex.exists():
            teacher_ok, teacher_log = _run_pdflatex(teacher_tex.name, tmp)
            if not teacher_ok and not log_tail:
                log_tail = teacher_log
        else:
            teacher_ok = False
            if not log_tail:
                log_tail = f"{lesson_id}_teacher.tex not found"

        # --- slides (independent: missing tex_slides is not a failure) ---
        if tex_slides:
            slides_tex_path = tmp / f"{lesson_id}_slides.tex"
            slides_tex_path.write_text(tex_slides, encoding="utf-8")
            slides_ok, slides_log = _run_pdflatex(slides_tex_path.name, tmp)
            if not slides_ok:
                log.warning("slides build failed for %s: %s", lesson_id, slides_log[-500:])
                if not log_tail:
                    log_tail = slides_log

        # --- do_now (independent: missing tex_do_now is not a failure) ---
        if tex_do_now:
            do_now_tex_path = tmp / f"{lesson_id}_do_now.tex"
            do_now_tex_path.write_text(tex_do_now, encoding="utf-8")
            do_now_ok, do_now_log = _run_pdflatex(do_now_tex_path.name, tmp)
            if not do_now_ok:
                log.warning("do_now build failed for %s: %s", lesson_id, do_now_log[-500:])
                if not log_tail:
                    log_tail = do_now_log

        # --- upload ---
        if student_ok:
            pdf_path = tmp / f"{lesson_id}_student.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_student.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_student_url = _storage_public_url(obj)

        if teacher_ok:
            pdf_path = tmp / f"{lesson_id}_teacher.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_teacher.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_teacher_url = _storage_public_url(obj)

        if slides_ok:
            pdf_path = tmp / f"{lesson_id}_slides.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_slides.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_slides_url = _storage_public_url(obj)

        if do_now_ok:
            pdf_path = tmp / f"{lesson_id}_do_now.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_do_now.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_do_now_url = _storage_public_url(obj)

    # overall_ok: only editions that were attempted must succeed; slides are
    # independent — a slides failure doesn't poison the overall flag when
    # student/teacher both succeeded (or weren't attempted).
    attempted_packet = bool(tex_student or tex_teacher or yaml_text)
    overall_ok = (not attempted_packet or (student_ok and teacher_ok))
    if tex_slides and not slides_ok:
        overall_ok = False
    if tex_do_now and not do_now_ok:
        overall_ok = False

    built_editions = [e for e, flag in [("student", student_ok),
                                         ("teacher", teacher_ok),
                                         ("slides", slides_ok),
                                         ("do_now", do_now_ok)] if flag]
    log.info("%s build done — built: %s", lesson_id,
             ", ".join(built_editions) if built_editions else "none")

    _write_build_status(
        lesson_id,
        ok=overall_ok,
        log_tail="" if overall_ok else log_tail,
        has_pdf_student=bool(pdf_student_url),
        has_pdf_teacher=bool(pdf_teacher_url),
        has_slides=bool(pdf_slides_url),
        user_name=x_user_name,
    )

    return {
        "ok": overall_ok,
        "pdf_student_url": pdf_student_url,
        "pdf_teacher_url": pdf_teacher_url,
        "pdf_slides_url": pdf_slides_url,
        "pdf_do_now_url": pdf_do_now_url,
        "log_tail": "" if overall_ok else log_tail,
    }


@app.put("/tex/{lesson_id}/{edition}")
async def put_tex(
    lesson_id: str,
    edition: str,
    request: Request,
    x_passcode: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
    if_match_sha: str | None = Header(default=None, alias="if-match-sha"),
) -> dict:
    _validate_lesson_id(lesson_id)
    _validate_edition(edition)
    _check_passcode(x_passcode)

    body = await request.body()
    tex_text = body.decode("utf-8")

    if if_match_sha:
        row = _rest_get_lesson(lesson_id)
        col = f"tex_{edition}"
        current_tex = (row.get(col) or "") if row else ""
        server_sha = hashlib.sha256(current_tex.encode("utf-8")).hexdigest()
        if server_sha != if_match_sha:
            changed_by = _rest_last_audit_changed_by(lesson_id)
            return JSONResponse(
                status_code=409,
                content={
                    "conflict": True,
                    "current_tex": current_tex,
                    "current_sha": server_sha,
                    "changed_by": changed_by,
                },
            )

    _rest_update_lesson(lesson_id, {f"tex_{edition}": tex_text}, x_user_name)
    return {"ok": True}
