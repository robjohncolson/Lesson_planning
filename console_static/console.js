/**
 * Klimsara Teacher Console — console.js
 * Vanilla JS, no bundler, no external deps.
 *
 * Phase 1 MVP uses a plain <textarea> editor. CodeMirror 6 was attempted
 * but its CDN-only ESM distribution double-loaded @codemirror/state,
 * breaking instanceof checks. Phase 2 will add CodeMirror properly via
 * a bundled file (or pin to an import-map of matched versions).
 */

// ── DOM handles ──────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const healthDot     = $("health-dot");
const healthLabel   = $("health-label");
const serverBanner  = $("server-banner");
const lessonList    = $("lesson-list");
const filterInput   = $("filter-input");
const detailEmpty   = $("detail-empty");
const detailHeader  = $("detail-header");
const detailTitle   = $("detail-title");
const workspace     = $("workspace");
const cmHost        = $("cm-host");
const noYamlMsg     = $("no-yaml-msg");
const errorPanel    = $("error-panel");
const saveStatus    = $("save-status");
const pdfFrame      = $("pdf-frame");
const previewPlaceholder = $("preview-placeholder");
const modalOverlay  = $("modal-overlay");
const modalTitle    = $("modal-title");
const modalBody     = $("modal-body");

const btnSave       = $("btn-save");
const btnRegen      = $("btn-regen");
const btnPacer      = $("btn-pacer");
const btnRegistry   = $("btn-registry");
const btnStudentPdf = $("btn-student-pdf");
const btnTeacherPdf = $("btn-teacher-pdf");
const btnSlides     = $("btn-slides");
const btnToggleStudent = $("toggle-student");
const btnToggleTeacher = $("toggle-teacher");
const btnModalClose = $("btn-modal-close");

// ── App state ────────────────────────────────────────────────────────────────
let allLessons = [];            // full list from /api/lessons
let activeLessonId = null;      // currently selected lesson_id
let activeMeta = null;          // metadata object for active lesson
let previewEdition = "student"; // "student" | "teacher"
let editorEl = null;            // HTMLTextAreaElement for the YAML editor
let regenInProgress = false;

// ── Editor setup (plain textarea — Phase 1) ─────────────────────────────────
function createEditor(doc = "") {
  cmHost.innerHTML = "";
  editorEl = document.createElement("textarea");
  editorEl.className = "yaml-editor";
  editorEl.value = doc;
  editorEl.spellcheck = false;
  editorEl.autocomplete = "off";
  editorEl.autocapitalize = "off";
  editorEl.wrap = "off";
  editorEl.addEventListener("keydown", e => {
    if (e.ctrlKey && e.key === "s") { e.preventDefault(); saveYaml(); }
    else if (e.ctrlKey && e.key === "Enter") { e.preventDefault(); triggerRegen(); }
  });
  cmHost.appendChild(editorEl);
}

function setEditorReadonly(readonly) {
  if (editorEl) editorEl.readOnly = readonly;
}

// ── Health check ─────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const r = await fetch("/api/health");
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const d = await r.json();
    healthDot.className = "ok";
    healthLabel.textContent = `${d.lessons} lessons · ${d.registry_rows} bank items`;
    serverBanner.classList.remove("visible");
    return true;
  } catch {
    healthDot.className = "error";
    healthLabel.textContent = "Server unreachable";
    serverBanner.classList.add("visible");
    return false;
  }
}

// ── Lesson list ───────────────────────────────────────────────────────────────
async function loadLessons() {
  try {
    const r = await fetch("/api/lessons");
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    allLessons = await r.json();
    renderLessonList(allLessons);
  } catch (e) {
    console.error("Failed to load lessons:", e);
  }
}

function renderLessonList(lessons) {
  lessonList.innerHTML = "";
  const q = filterInput.value.trim().toLowerCase();
  const filtered = q
    ? lessons.filter(l =>
        l.lesson_id.toLowerCase().includes(q) ||
        (l.title || "").toLowerCase().includes(q))
    : lessons;

  if (filtered.length === 0) {
    lessonList.innerHTML = `<div style="padding:14px;color:var(--muted);font-size:0.85rem;">No lessons match.</div>`;
    return;
  }

  for (const lesson of filtered) {
    const row = document.createElement("div");
    row.className = "lesson-row" + (lesson.lesson_id === activeLessonId ? " active" : "");
    row.dataset.id = lesson.lesson_id;

    // Artifact squares: student PDF, teacher PDF, slides
    const sq = (present, cls) =>
      `<span class="art-sq ${present ? "present" : ""} ${cls}" title="${cls}"></span>`;

    row.innerHTML = `
      <span class="lesson-id">${escHtml(lesson.lesson_id)}</span>
      <span class="lesson-title">${escHtml(lesson.title || "")}</span>
      <span class="artifacts">
        ${sq(lesson.has_student_pdf, "student")}
        ${sq(lesson.has_teacher_pdf, "teacher")}
        ${sq(lesson.has_slides_pdf,  "slides")}
      </span>`;

    row.addEventListener("click", () => selectLesson(lesson));
    lessonList.appendChild(row);
  }
}

// ── Select a lesson ───────────────────────────────────────────────────────────
async function selectLesson(lesson) {
  activeLessonId = lesson.lesson_id;
  activeMeta = lesson;

  // Update sidebar active state
  document.querySelectorAll(".lesson-row").forEach(r =>
    r.classList.toggle("active", r.dataset.id === activeLessonId));

  // Show detail area
  detailEmpty.style.display   = "none";
  detailHeader.style.display  = "flex";
  workspace.style.display     = "grid";

  // Update title
  const cadence = lesson.cadence ? ` · ${lesson.cadence}` : "";
  detailTitle.textContent = `${lesson.lesson_id}${cadence}${lesson.title ? "  —  " + lesson.title : ""}`;

  // Update toolbar button availability
  btnStudentPdf.disabled = !lesson.has_student_pdf;
  btnTeacherPdf.disabled = !lesson.has_teacher_pdf;
  btnSlides.disabled     = !lesson.has_slides_pdf;
  btnPacer.disabled      = !lesson.has_pacer_html;

  // Reset error / save status
  hideError();
  saveStatus.textContent = "";
  saveStatus.className   = "";

  // Load YAML
  await loadYaml(lesson.lesson_id);

  // Load PDF preview (default: student)
  previewEdition = "student";
  btnToggleStudent.classList.add("active");
  btnToggleTeacher.classList.remove("active");
  loadPdfPreview();
}

async function loadYaml(lessonId) {
  cmHost.style.display   = "block";
  noYamlMsg.style.display = "none";

  try {
    const r = await fetch(`/api/lesson/${encodeURIComponent(lessonId)}/yaml`);
    if (r.status === 404) {
      cmHost.style.display    = "none";
      noYamlMsg.style.display = "block";
      noYamlMsg.innerHTML = `
        <p><strong>No YAML spec found for ${escHtml(lessonId)}.</strong></p>
        <p style="margin-top:8px;">
          The LaTeX source files may exist — use the
          ${activeMeta?.has_student_pdf ? `<a href="/api/pdf/${encodeURIComponent(lessonId)}/student" target="_blank">Student PDF</a>` : "Student PDF (missing)"}
          or
          ${activeMeta?.has_teacher_pdf ? `<a href="/api/pdf/${encodeURIComponent(lessonId)}/teacher" target="_blank">Teacher PDF</a>` : "Teacher PDF (missing)"}
          buttons to view them.
        </p>`;
      return;
    }
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const text = await r.text();
    createEditor(text);
  } catch (e) {
    showError(`Failed to load YAML: ${e.message}`);
    createEditor("");
  }
}

// ── PDF preview ───────────────────────────────────────────────────────────────
function loadPdfPreview(cacheBust = false) {
  if (!activeLessonId) return;
  const hasPdf = previewEdition === "student"
    ? activeMeta?.has_student_pdf
    : activeMeta?.has_teacher_pdf;

  if (!hasPdf) {
    pdfFrame.style.display = "none";
    previewPlaceholder.style.display = "flex";
    previewPlaceholder.textContent = `No ${previewEdition} PDF available.`;
    return;
  }

  pdfFrame.style.display = "block";
  previewPlaceholder.style.display = "none";
  const ts = cacheBust ? `?t=${Date.now()}` : "";
  pdfFrame.src = `/api/pdf/${encodeURIComponent(activeLessonId)}/${previewEdition}${ts}`;
}

// ── Save YAML ─────────────────────────────────────────────────────────────────
async function saveYaml() {
  if (!activeLessonId || regenInProgress) return;
  if (cmHost.style.display === "none") return;   // no editor visible

  const body = editorEl ? editorEl.value : "";
  hideError();
  saveStatus.textContent = "Saving…";
  saveStatus.className   = "";

  try {
    const r = await fetch(`/api/lesson/${encodeURIComponent(activeLessonId)}/yaml`, {
      method: "PUT",
      headers: { "Content-Type": "text/plain" },
      body,
    });
    if (r.status === 400) {
      const detail = await r.text();
      showError(`YAML error:\n${detail}`);
      saveStatus.textContent = "Error";
      saveStatus.className   = "error";
      return;
    }
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    saveStatus.textContent = "Saved";
    saveStatus.className   = "";
    setTimeout(() => { saveStatus.textContent = ""; }, 2500);
  } catch (e) {
    showError(`Save failed: ${e.message}`);
    saveStatus.textContent = "Error";
    saveStatus.className   = "error";
  }
}

// ── Regenerate PDF ────────────────────────────────────────────────────────────
async function triggerRegen() {
  if (!activeLessonId || regenInProgress) return;

  regenInProgress = true;
  hideError();
  saveStatus.textContent = "";
  btnRegen.disabled = true;
  btnSave.disabled  = true;
  setEditorReadonly(true);
  btnRegen.innerHTML = `<span class="spinner"></span> Building…`;

  try {
    const r = await fetch(`/api/lesson/${encodeURIComponent(activeLessonId)}/regenerate`, {
      method: "POST",
    });
    const d = await r.json();
    if (!r.ok || !d.ok) {
      const tail = d.log_tail || "(no log output)";
      showError(`Regeneration failed:\n${tail}`);
    } else {
      // Reload PDF with cache-bust
      loadPdfPreview(true);
      // Refresh lesson list to update artifact indicators
      await loadLessons();
      saveStatus.textContent = "PDF updated";
      setTimeout(() => { saveStatus.textContent = ""; }, 3000);
    }
  } catch (e) {
    showError(`Regenerate failed: ${e.message}`);
  } finally {
    regenInProgress = false;
    btnRegen.disabled = false;
    btnSave.disabled  = false;
    setEditorReadonly(false);
    btnRegen.innerHTML = "Regenerate &#x21BB;";
  }
}

// ── Registry modal ────────────────────────────────────────────────────────────
async function openRegistry() {
  if (!activeLessonId) return;

  // Extract lesson prefix: e.g. "L41_P2" → "4-1" (best-effort)
  // We pass lesson_id as the ?lesson= query parameter and let server filter.
  const prefix = activeLessonId;

  modalTitle.textContent = `Registry — ${prefix}`;
  modalBody.innerHTML    = `<p style="color:var(--muted);font-size:0.85rem;">Loading…</p>`;
  modalOverlay.classList.add("visible");

  try {
    const r = await fetch(`/api/registry?lesson=${encodeURIComponent(prefix)}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const items = await r.json();
    renderRegistryItems(items);
  } catch (e) {
    modalBody.innerHTML = `<p style="color:var(--red);">Failed: ${escHtml(e.message)}</p>`;
  }
}

function renderRegistryItems(items) {
  if (!items.length) {
    modalBody.innerHTML = `<p style="color:var(--muted);font-size:0.85rem;">No registry items found for this lesson.</p>`;
    return;
  }
  modalBody.innerHTML = items.map(item => `
    <div class="registry-item">
      <div>
        <span class="ri-id">${escHtml(item.id || item.lesson_id || "")}</span>
        <span class="ri-dok">DOK ${escHtml(String(item.dok ?? "?"))}</span>
        ${item.skill ? `<span style="font-size:0.72rem;color:var(--teal);margin-left:6px;">${escHtml(item.skill)}</span>` : ""}
      </div>
      <div class="ri-prompt">${escHtml(truncate(item.prompt || item.question || "(no prompt)", 180))}</div>
    </div>`).join("");
}

// ── Error panel ───────────────────────────────────────────────────────────────
function showError(msg) {
  errorPanel.textContent = msg;
  errorPanel.classList.add("visible");
}
function hideError() {
  errorPanel.textContent = "";
  errorPanel.classList.remove("visible");
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function truncate(s, n) {
  return s.length > n ? s.slice(0, n) + "…" : s;
}

// ── Event wiring ──────────────────────────────────────────────────────────────
filterInput.addEventListener("input", () => renderLessonList(allLessons));

btnSave.addEventListener("click", saveYaml);
btnRegen.addEventListener("click", triggerRegen);

btnPacer.addEventListener("click", () => {
  if (activeLessonId) window.open(`/api/pacer/${encodeURIComponent(activeLessonId)}`, "_blank");
});

btnRegistry.addEventListener("click", openRegistry);

btnStudentPdf.addEventListener("click", () => {
  if (activeLessonId && activeMeta?.has_student_pdf)
    window.open(`/api/pdf/${encodeURIComponent(activeLessonId)}/student`, "_blank");
});

btnTeacherPdf.addEventListener("click", () => {
  if (activeLessonId && activeMeta?.has_teacher_pdf)
    window.open(`/api/pdf/${encodeURIComponent(activeLessonId)}/teacher`, "_blank");
});

btnSlides.addEventListener("click", () => {
  if (activeLessonId && activeMeta?.has_slides_pdf)
    window.open(`/api/slides/${encodeURIComponent(activeLessonId)}`, "_blank");
});

btnToggleStudent.addEventListener("click", () => {
  if (previewEdition === "student") return;
  previewEdition = "student";
  btnToggleStudent.classList.add("active");
  btnToggleTeacher.classList.remove("active");
  loadPdfPreview();
});

btnToggleTeacher.addEventListener("click", () => {
  if (previewEdition === "teacher") return;
  previewEdition = "teacher";
  btnToggleTeacher.classList.add("active");
  btnToggleStudent.classList.remove("active");
  loadPdfPreview();
});

btnModalClose.addEventListener("click", () => modalOverlay.classList.remove("visible"));
modalOverlay.addEventListener("click", e => {
  if (e.target === modalOverlay) modalOverlay.classList.remove("visible");
});

document.addEventListener("keydown", e => {
  if (e.key === "Escape") modalOverlay.classList.remove("visible");
});

// ── Boot ──────────────────────────────────────────────────────────────────────
(async () => {
  const healthy = await checkHealth();
  if (healthy) await loadLessons();
  // Recheck health every 30 s
  setInterval(checkHealth, 30_000);
})();
