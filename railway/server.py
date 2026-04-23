"""Railway pdflatex build service for the Teacher Console.

Endpoints:
  GET  /health                        — smoke test
  POST /build/{lesson_id}             — read tex from Supabase, compile, upload PDFs
  PUT  /tex/{lesson_id}/{edition}     — write tex source back to Supabase

Auth: X-Passcode header must match REBUILD_PASSCODE env var.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
# Explicit required — no default. An unset passcode with CORS=* would let the
# whole internet hit /build and /tex. Refuse to start.
REBUILD_PASSCODE = os.environ["REBUILD_PASSCODE"]

LESSON_ID_RE = re.compile(r"^L\d{2}_P\d$")
EDITIONS = {"student", "teacher"}

# Bundled assets copied alongside server.py in the container
HERE = Path(__file__).parent
PREAMBLE_STY = HERE / "preamble.sty"
BEAMER_STY = HERE / "beamer_preamble.sty"
YAML_BUILDER = HERE / "build_lesson_from_yaml.py"

BUCKET = "lesson-pdfs"

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["Content-Type", "X-Passcode"],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
)


def _db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _check_passcode(x_passcode: str | None) -> None:
    if x_passcode != REBUILD_PASSCODE:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Passcode")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_lesson_id(lesson_id: str) -> None:
    if not LESSON_ID_RE.match(lesson_id):
        raise HTTPException(status_code=400, detail="lesson_id must match L##_P# (e.g. L41_P2)")


def _validate_edition(edition: str) -> None:
    if edition not in EDITIONS:
        raise HTTPException(status_code=400, detail="edition must be 'student' or 'teacher'")


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
def build(lesson_id: str, x_passcode: str | None = Header(default=None)) -> dict:
    _validate_lesson_id(lesson_id)
    _check_passcode(x_passcode)

    db = _db()

    # Read lesson row
    resp = (
        db.schema("lesson_planning")
        .table("lessons")
        .select("tex_student, tex_teacher, yaml_text")
        .eq("id", lesson_id)
        .single()
        .execute()
    )
    row = resp.data
    if not row:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found in Supabase")

    tex_student: str | None = row.get("tex_student")
    tex_teacher: str | None = row.get("tex_teacher")
    yaml_text: str | None = row.get("yaml_text")

    if not yaml_text and not tex_student and not tex_teacher:
        raise HTTPException(
            status_code=422,
            detail="Lesson has no yaml_text and no tex sources; nothing to build",
        )

    log_tail = ""
    student_ok = False
    teacher_ok = False
    pdf_student_url = None
    pdf_teacher_url = None

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # Copy shared style files into temp dir so pdflatex finds them
        if PREAMBLE_STY.exists():
            (tmp / "preamble.sty").write_bytes(PREAMBLE_STY.read_bytes())
        if BEAMER_STY.exists():
            (tmp / "beamer_preamble.sty").write_bytes(BEAMER_STY.read_bytes())

        # Source-of-truth policy:
        #   - If stored tex exists, compile it. Web edits persist through
        #     rebuilds this way (the whole point of the tex-editor flow).
        #   - Only regenerate from YAML when neither tex edition is stored,
        #     i.e. a fresh lesson that has only a YAML spec.
        if tex_student or tex_teacher:
            if tex_student:
                (tmp / f"{lesson_id}_student.tex").write_text(tex_student, encoding="utf-8")
            if tex_teacher:
                (tmp / f"{lesson_id}_teacher.tex").write_text(tex_teacher, encoding="utf-8")
        elif yaml_text:
            # Parse YAML first to defense-in-depth validate its lesson_id — the
            # generator writes files named after YAML's lesson_id field, which
            # would otherwise allow path traversal via a malicious YAML value.
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
                _write_build_status(db, lesson_id, ok=False, log_tail=gen_out[-4096:])
                return {"ok": False, "log_tail": gen_out[-4096:],
                        "pdf_student_url": None, "pdf_teacher_url": None}

            # Generator writes to tex/ relative to HERE; move outputs into tmp
            gen_student = HERE / "tex" / f"{lesson_id}_student.tex"
            gen_teacher = HERE / "tex" / f"{lesson_id}_teacher.tex"
            if gen_student.exists():
                (tmp / f"{lesson_id}_student.tex").write_bytes(gen_student.read_bytes())
            if gen_teacher.exists():
                (tmp / f"{lesson_id}_teacher.tex").write_bytes(gen_teacher.read_bytes())

        # Compile student
        student_tex = tmp / f"{lesson_id}_student.tex"
        if student_tex.exists():
            student_ok, student_log = _run_pdflatex(student_tex.name, tmp)
            if not student_ok:
                log_tail = student_log
        else:
            student_ok = False
            log_tail = f"{lesson_id}_student.tex not found in temp dir"

        # Compile teacher
        teacher_tex = tmp / f"{lesson_id}_teacher.tex"
        if teacher_tex.exists():
            teacher_ok, teacher_log = _run_pdflatex(teacher_tex.name, tmp)
            if not teacher_ok and not log_tail:
                log_tail = teacher_log
        else:
            teacher_ok = False
            if not log_tail:
                log_tail = f"{lesson_id}_teacher.tex not found in temp dir"

        # Upload PDFs to Supabase Storage
        if student_ok:
            pdf_path = tmp / f"{lesson_id}_student.pdf"
            if pdf_path.exists():
                storage_key = f"{lesson_id}_student.pdf"
                db.storage.from_(BUCKET).upload(
                    storage_key,
                    pdf_path.read_bytes(),
                    {"content-type": "application/pdf", "upsert": "true"},
                )
                pdf_student_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_key}"

        if teacher_ok:
            pdf_path = tmp / f"{lesson_id}_teacher.pdf"
            if pdf_path.exists():
                storage_key = f"{lesson_id}_teacher.pdf"
                db.storage.from_(BUCKET).upload(
                    storage_key,
                    pdf_path.read_bytes(),
                    {"content-type": "application/pdf", "upsert": "true"},
                )
                pdf_teacher_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_key}"

    overall_ok = student_ok and teacher_ok
    _write_build_status(
        db,
        lesson_id,
        ok=overall_ok,
        log_tail="" if overall_ok else log_tail,
        has_pdf_student=bool(pdf_student_url),
        has_pdf_teacher=bool(pdf_teacher_url),
    )

    return {
        "ok": overall_ok,
        "pdf_student_url": pdf_student_url,
        "pdf_teacher_url": pdf_teacher_url,
        "log_tail": "" if overall_ok else log_tail,
    }


@app.put("/tex/{lesson_id}/{edition}")
async def put_tex(
    lesson_id: str,
    edition: str,
    request: Request,
    x_passcode: str | None = Header(default=None),
) -> dict:
    _validate_lesson_id(lesson_id)
    _validate_edition(edition)
    _check_passcode(x_passcode)

    body = await request.body()
    tex_text = body.decode("utf-8")

    db = _db()
    db.schema("lesson_planning").table("lessons").update(
        {f"tex_{edition}": tex_text}
    ).eq("id", lesson_id).execute()

    return {"ok": True}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_build_status(
    db: Client,
    lesson_id: str,
    *,
    ok: bool,
    log_tail: str,
    has_pdf_student: bool = False,
    has_pdf_teacher: bool = False,
) -> None:
    payload: dict = {
        "last_build_at": datetime.now(timezone.utc).isoformat(),
        "last_build_ok": ok,
        "last_build_log": log_tail if not ok else "",
    }
    if has_pdf_student or has_pdf_teacher:
        payload["has_pdf_student"] = has_pdf_student
        payload["has_pdf_teacher"] = has_pdf_teacher
    try:
        db.schema("lesson_planning").table("lessons").update(payload).eq(
            "id", lesson_id
        ).execute()
    except Exception as exc:
        log.error("Failed to write build status for %s: %s", lesson_id, exc)
