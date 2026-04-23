import { api, pdfUrl, getTex, saveTex, rebuildPdf } from "/js/api.js";
import { passcode } from "/js/passcode.js";
import { createLessonList } from "/js/lesson-list.js";
import { renderItemList, renderItemDetail } from "/js/item-detail.js";

// ── DOM refs ────────────────────────────────────────────────────────────────

const healthEl      = document.getElementById("health-indicator");
const errorBanner   = document.getElementById("error-banner");
const detailEmpty   = document.getElementById("detail-empty");
const detailHeader  = document.getElementById("detail-header");
const detailTitle   = document.getElementById("detail-title");
const btnStudentPdf = document.getElementById("btn-student-pdf");
const btnTeacherPdf = document.getElementById("btn-teacher-pdf");
const btnSlides     = document.getElementById("btn-slides");
const btnItems      = document.getElementById("btn-items");
const btnYaml       = document.getElementById("btn-yaml");
const btnTexStudent = document.getElementById("btn-tex-student");
const btnTexTeacher = document.getElementById("btn-tex-teacher");
const yamlContent   = document.getElementById("yaml-content");
const texContent    = document.getElementById("tex-content");   // now a <textarea>
const texEditLabel  = document.getElementById("tex-editing-label");
const btnTexSave    = document.getElementById("btn-tex-save");
const btnTexRebuild = document.getElementById("btn-tex-rebuild");
const texSaveStatus = document.getElementById("tex-save-status");
const texLog        = document.getElementById("tex-log");
const itemList      = document.getElementById("item-list");
const itemDetail    = document.getElementById("item-detail");
const btnBack       = document.getElementById("btn-back-to-items");

const SUB_VIEWS = ["yaml-view", "tex-view", "pdf-view", "item-list-view", "item-detail-view"];

const pdfEmbed     = document.getElementById("pdf-embed");
const pdfLabel     = document.getElementById("pdf-view-label");
const pdfOpenTab   = document.getElementById("pdf-open-tab");

// ── State ───────────────────────────────────────────────────────────────────

let activeLessonId   = null;
let activeLesson     = null;
let activeTexEdition = null;   // "student" | "teacher"
let texDirty         = false;

// ── Helpers ─────────────────────────────────────────────────────────────────

function showView(id) {
  for (const v of SUB_VIEWS) {
    document.getElementById(v).style.display = v === id ? "" : "none";
  }
}

function showError(msg) {
  errorBanner.textContent = msg;
  errorBanner.classList.add("visible");
}

function clearError() {
  errorBanner.classList.remove("visible");
}

function highlightToolbarBtn(active) {
  btnItems.classList.toggle("active", active === "items");
  btnYaml.classList.toggle("active",  active === "yaml");
  btnTexStudent.classList.toggle("active", active === "tex-student");
  btnTexTeacher.classList.toggle("active", active === "tex-teacher");
}

// ── PDF inline preview ─────────────────────────────────────────────────────
// Buttons are <button> (not <a>) so we can open the preview pane in-app
// instead of jumping out to a new tab. A separate "Open in new tab" link
// lives inside the preview pane as an escape hatch.

function setPdfButtons(lesson) {
  btnStudentPdf.disabled = !lesson.has_pdf_student;
  btnTeacherPdf.disabled = !lesson.has_pdf_teacher;
  btnSlides.disabled     = !lesson.has_slides_pdf;
}

function openPdfView(kind) {
  if (!activeLessonId) return;
  const url = pdfUrl(activeLessonId, kind) + `?t=${Date.now()}`; // cache-bust
  pdfLabel.textContent = `${activeLessonId} / ${kind}`;
  pdfOpenTab.href = url;
  pdfEmbed.src = url;
  showView("pdf-view");
}

// ── Lesson selection ─────────────────────────────────────────────────────────

async function selectLesson(id) {
  clearError();
  try {
    const lesson = await api.getLesson(id);
    if (!lesson) { showError(`Lesson ${id} not found.`); return; }

    activeLessonId = id;
    activeLesson   = lesson;

    detailEmpty.style.display  = "none";
    detailHeader.style.display = "";
    detailTitle.textContent    = `${lesson.id}${lesson.title ? " — " + lesson.title : ""}`;

    setPdfButtons(lesson);

    // YAML button disabled if no spec yet; Items always available
    btnYaml.disabled = !lesson.yaml_text;

    openItemsView();
  } catch (err) {
    showError(err.message);
  }
}

// ── Sub-view openers ─────────────────────────────────────────────────────────

function openItemsView() {
  highlightToolbarBtn("items");
  showView("item-list-view");
  renderItemList(activeLessonId, itemList, openItemDetailView);
}

async function openItemDetailView(itemId) {
  showView("item-detail-view");
  try {
    await renderItemDetail(itemId, itemDetail);
  } catch (err) {
    showError(err.message);
  }
}

function openYamlView() {
  if (!activeLesson) return;
  highlightToolbarBtn("yaml");
  showView("yaml-view");
  yamlContent.textContent = activeLesson.yaml_text ?? "(no YAML spec for this lesson)";
}

async function openTexView(edition) {
  if (!activeLessonId) return;
  activeTexEdition = edition;
  texDirty = false;
  highlightToolbarBtn(`tex-${edition}`);
  showView("tex-view");
  texContent.value = "Loading…";
  texEditLabel.textContent = `${activeLessonId} / ${edition}`;
  btnTexSave.disabled    = true;
  btnTexRebuild.disabled = true;
  texSaveStatus.textContent = "";
  texLog.style.display = "none";
  texLog.textContent   = "";
  try {
    const src = await getTex(activeLessonId, edition);
    texContent.value = src ?? "";
    if (!src) {
      texSaveStatus.textContent = `(no ${edition} tex stored yet)`;
    }
    // Enable buttons now that content is loaded; actual save requires dirty
    btnTexSave.disabled    = false;
    btnTexRebuild.disabled = false;
  } catch (err) {
    texContent.value = "";
    showError(err.message);
  }
}

// ── Tex dirty tracking ───────────────────────────────────────────────────────

texContent.addEventListener("input", () => {
  texDirty = true;
});

// ── Save / Rebuild helpers ───────────────────────────────────────────────────

let _statusTimer = null;
function setStatus(msg, isError = false) {
  clearTimeout(_statusTimer);
  texSaveStatus.textContent = msg;
  texSaveStatus.className   = isError ? "tex-status-error" : "tex-status-ok";
  if (!isError && msg) {
    _statusTimer = setTimeout(() => { texSaveStatus.textContent = ""; }, 3000);
  }
}

async function doSave() {
  if (!activeLessonId || !activeTexEdition) return;
  const body = texContent.value;
  setStatus("Saving…");
  try {
    await saveTex(activeLessonId, activeTexEdition, body);
    texDirty = false;
    setStatus("Saved");
  } catch (err) {
    if (err.name === "WrongPasscode") {
      // re-prompt once: passcode.clear() already called inside saveTex
      setStatus("Wrong passcode — retrying…", true);
      await saveTex(activeLessonId, activeTexEdition, body);
      texDirty = false;
      setStatus("Saved");
    } else {
      setStatus(err.message, true);
      throw err;
    }
  }
}

async function _doRebuildOnce() {
  setStatus("Building…");
  btnTexRebuild.disabled = true;
  const result = await rebuildPdf(activeLessonId);
  if (result.log_tail) {
    texLog.textContent   = result.log_tail;
    texLog.style.display = "";
    const hasError = /error/i.test(result.log_tail);
    texLog.className = "tex-log" + (hasError ? " tex-log-error" : " tex-log-ok");
  } else {
    texLog.style.display = "none";
  }
  // Fresh build — flip the PDF embed if it's currently showing this lesson,
  // otherwise the teacher re-opens Student/Teacher PDF and gets the new file.
  if (result.ok && pdfEmbed.src && pdfEmbed.src.includes(activeLessonId)) {
    const t = Date.now();
    const cur = pdfEmbed.src.includes("_student.pdf") ? "student" : "teacher";
    pdfEmbed.src = pdfUrl(activeLessonId, cur) + `?t=${t}`;
  }
  setStatus(result.ok ? "Build complete" : "Build finished with errors", !result.ok);
}

async function doRebuild() {
  if (!activeLessonId) return;
  clearError();
  try {
    if (texDirty) await doSave();
    try {
      await _doRebuildOnce();
    } catch (err) {
      if (err.name === "WrongPasscode") {
        // Mirror doSave's retry: passcode already cleared inside rebuildPdf
        setStatus("Wrong passcode — retrying…", true);
        await _doRebuildOnce();
      } else {
        throw err;
      }
    }
  } catch (err) {
    setStatus(err.message, true);
    showError(err.message);
  } finally {
    btnTexRebuild.disabled = false;
  }
}

// ── Keyboard shortcuts (Ctrl+S, Ctrl+Enter) ─────────────────────────────────

texContent.addEventListener("keydown", (e) => {
  if (!e.ctrlKey && !e.metaKey) return;
  if (e.key === "s") {
    e.preventDefault();
    doSave().catch(() => {});
  } else if (e.key === "Enter") {
    e.preventDefault();
    doRebuild().catch(() => {});
  }
});

// ── Toolbar event listeners ──────────────────────────────────────────────────

btnItems.addEventListener("click", () => {
  if (!activeLessonId) return;
  openItemsView();
});

btnYaml.addEventListener("click", () => {
  if (!activeLessonId) return;
  openYamlView();
});

btnTexStudent.addEventListener("click", () => openTexView("student"));
btnTexTeacher.addEventListener("click", () => openTexView("teacher"));

btnTexSave.addEventListener("click",    () => doSave().catch(() => {}));
btnTexRebuild.addEventListener("click", () => doRebuild().catch(() => {}));

btnBack.addEventListener("click", openItemsView);

btnStudentPdf.addEventListener("click", () => openPdfView("student"));
btnTeacherPdf.addEventListener("click", () => openPdfView("teacher"));
btnSlides.addEventListener("click",     () => openPdfView("slides"));

// ── Boot ─────────────────────────────────────────────────────────────────────

async function boot() {
  const ok = await api.checkHealth();
  healthEl.textContent  = ok ? "Connected" : "Offline";
  healthEl.className    = ok ? "ok" : "error";

  const lessonList = createLessonList({ onSelect: selectLesson });
  try {
    await lessonList.init();
  } catch (err) {
    showError("Could not load lessons: " + err.message);
  }
}

boot();
