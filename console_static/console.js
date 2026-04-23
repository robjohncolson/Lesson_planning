/**
 * Klimsara Teacher Console — console.js
 * CodeMirror 6 editor bundled into /static/vendor/codemirror.js.
 * Rebuild via `npm run build` in console_vendor/.
 */
import {
  EditorView,
  EditorState,
  Compartment,
  basicSetup,
  keymap,
  yaml,
  indentWithTab,
} from "/static/vendor/codemirror.js";

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
const btnDiff       = $("btn-diff");
const btnPacer      = $("btn-pacer");
const btnRegistry   = $("btn-registry");
const btnDag        = $("btn-dag");
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
let editorView = null;          // CodeMirror 6 EditorView
let regenInProgress = false;
let lastDiff = null;            // { student_tex, teacher_tex } from last regen
let editorMode = "yaml";        // "yaml" | "tex" — which source type the editor is showing
const toolbarLabel = document.querySelector("#editor-toolbar .toolbar-label");

const readOnlyCompartment = new Compartment();

// ── Editor setup (CodeMirror 6) ─────────────────────────────────────────────
function createEditor(doc = "") {
  if (editorView) { editorView.destroy(); editorView = null; }
  cmHost.innerHTML = "";

  const state = EditorState.create({
    doc,
    extensions: [
      basicSetup,
      yaml(),
      readOnlyCompartment.of(EditorState.readOnly.of(false)),
      keymap.of([
        indentWithTab,
        { key: "Ctrl-s", preventDefault: true, run: () => { saveYaml(); return true; } },
        { key: "Ctrl-Enter", preventDefault: true, run: () => { triggerRegen(); return true; } },
      ]),
      EditorView.theme({
        "&": { height: "100%", fontSize: "0.84rem", background: "#fafbfc" },
        "&.cm-focused": { outline: "none", background: "#fff" },
        ".cm-scroller": { fontFamily: "'Consolas', 'Menlo', 'Courier New', monospace", lineHeight: "1.45" },
        ".cm-content": { padding: "10px 0" },
        ".cm-gutters": { background: "#f0f3f7", border: "0", color: "#8892a0" },
      }),
    ],
  });
  editorView = new EditorView({ state, parent: cmHost });
}

function setEditorReadonly(readonly) {
  if (!editorView) return;
  editorView.dispatch({
    effects: readOnlyCompartment.reconfigure(EditorState.readOnly.of(readonly)),
  });
  cmHost.classList.toggle("readonly", !!readonly);
}

function getEditorDoc() {
  return editorView ? editorView.state.doc.toString() : "";
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

  // Reset error / save status / diff
  hideError();
  saveStatus.textContent = "";
  saveStatus.className   = "";
  lastDiff = null;
  btnDiff.disabled = true;

  // Default preview edition
  previewEdition = "student";
  btnToggleStudent.classList.add("active");
  btnToggleTeacher.classList.remove("active");

  // Load editor source (YAML if it exists, else tex of current edition)
  await loadEditor(lesson.lesson_id);
  loadPdfPreview();
}

// Try YAML first; fall back to the student tex if no YAML exists. Updates
// `editorMode` so save/regen know which endpoint to hit.
async function loadEditor(lessonId) {
  cmHost.style.display    = "block";
  noYamlMsg.style.display = "none";

  // Attempt YAML
  try {
    const r = await fetch(`/api/lesson/${encodeURIComponent(lessonId)}/yaml`);
    if (r.ok) {
      editorMode = "yaml";
      toolbarLabel.textContent = "YAML spec";
      createEditor(await r.text());
      return;
    }
    if (r.status !== 404) throw new Error(`HTTP ${r.status}`);
  } catch (e) {
    showError(`Failed to load YAML: ${e.message}`);
    createEditor("");
    return;
  }

  // No YAML — load tex of the active edition
  await loadTex(lessonId, previewEdition);
}

async function loadTex(lessonId, edition) {
  try {
    const r = await fetch(`/api/lesson/${encodeURIComponent(lessonId)}/tex/${edition}`);
    if (r.status === 404) {
      cmHost.style.display    = "none";
      noYamlMsg.style.display = "block";
      noYamlMsg.innerHTML = `
        <p><strong>No source files found for ${escHtml(lessonId)}.</strong></p>
        <p style="margin-top:8px;color:var(--muted);font-size:0.85rem;">
          Neither <code>lessons/${escHtml(lessonId)}.yaml</code> nor
          <code>tex/${escHtml(lessonId)}_${escHtml(edition)}.tex</code> exists on disk.
        </p>`;
      return;
    }
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    editorMode = "tex";
    toolbarLabel.textContent = `${edition === "student" ? "Student" : "Teacher"} tex`;
    createEditor(await r.text());
  } catch (e) {
    showError(`Failed to load tex: ${e.message}`);
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

  const body = getEditorDoc();
  hideError();
  saveStatus.textContent = "Saving…";
  saveStatus.className   = "";

  const url = editorMode === "yaml"
    ? `/api/lesson/${encodeURIComponent(activeLessonId)}/yaml`
    : `/api/lesson/${encodeURIComponent(activeLessonId)}/tex/${previewEdition}`;

  try {
    const r = await fetch(url, {
      method: "PUT",
      headers: { "Content-Type": "text/plain" },
      body,
    });
    if (r.status === 400) {
      const detail = await r.text();
      showError(`${editorMode === "yaml" ? "YAML" : "Save"} error:\n${detail}`);
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
      // Capture diff for review
      lastDiff = d.diff || null;
      const hasDiff = lastDiff && (lastDiff.student_tex || lastDiff.teacher_tex);
      btnDiff.disabled = !hasDiff;

      // Reload PDF with cache-bust
      loadPdfPreview(true);
      // Refresh lesson list to update artifact indicators
      await loadLessons();
      saveStatus.textContent = hasDiff ? "PDF updated (diff available)" : "PDF updated (no tex changes)";
      setTimeout(() => { saveStatus.textContent = ""; }, 3500);
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

// ── Diff modal ────────────────────────────────────────────────────────────────
function openDiff() {
  if (!lastDiff) return;
  const student = lastDiff.student_tex || "";
  const teacher = lastDiff.teacher_tex || "";

  modalTitle.textContent = `Diff — ${activeLessonId} (last regenerate)`;
  modalBody.innerHTML = `
    <div id="diff-tabs" role="tablist">
      <button type="button" class="diff-tab active" data-side="student"
        ${student ? "" : "disabled"}>Student ${student ? "" : "(no change)"}</button>
      <button type="button" class="diff-tab" data-side="teacher"
        ${teacher ? "" : "disabled"}>Teacher ${teacher ? "" : "(no change)"}</button>
    </div>
    <pre id="diff-view" class="diff-view"></pre>`;

  const pickSide = (side) => {
    const txt = side === "student" ? student : teacher;
    modalBody.querySelectorAll(".diff-tab").forEach(el =>
      el.classList.toggle("active", el.dataset.side === side));
    const view = $("diff-view");
    if (!txt) {
      view.innerHTML = `<span class="diff-empty">(no changes)</span>`;
      return;
    }
    view.innerHTML = txt.split("\n").map(line => {
      const cls =
        line.startsWith("+++") || line.startsWith("---") ? "diff-meta"
        : line.startsWith("@@")  ? "diff-hunk"
        : line.startsWith("+")   ? "diff-add"
        : line.startsWith("-")   ? "diff-del"
        : "diff-ctx";
      return `<span class="diff-line ${cls}">${escHtml(line) || "&nbsp;"}</span>`;
    }).join("\n");
  };

  modalBody.querySelectorAll(".diff-tab").forEach(el =>
    el.addEventListener("click", () => {
      if (!el.disabled) pickSide(el.dataset.side);
    }));

  pickSide(student ? "student" : "teacher");
  modalOverlay.classList.add("visible");
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
btnDiff.addEventListener("click", openDiff);

// Map console lesson IDs (L41_P2) to DAG group IDs (4-1)
function lessonIdToGroup(lid) {
  const m = /^L(\d)(\d)/.exec(lid || "");
  return m ? `${m[1]}-${m[2]}` : null;
}
btnDag.addEventListener("click", () => {
  const group = lessonIdToGroup(activeLessonId);
  const qs = group ? `?lesson=${encodeURIComponent(group)}` : "";
  window.open(`/api/graph${qs}`, "_blank");
});

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

async function switchEdition(edition) {
  if (previewEdition === edition) return;
  previewEdition = edition;
  btnToggleStudent.classList.toggle("active", edition === "student");
  btnToggleTeacher.classList.toggle("active", edition === "teacher");
  // In tex mode, also swap the editor contents. YAML mode: preview only.
  if (editorMode === "tex" && activeLessonId) {
    await loadTex(activeLessonId, edition);
  }
  loadPdfPreview();
}
btnToggleStudent.addEventListener("click", () => switchEdition("student"));
btnToggleTeacher.addEventListener("click", () => switchEdition("teacher"));

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
