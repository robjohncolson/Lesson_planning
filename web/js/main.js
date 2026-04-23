import { api, pdfUrl, getTex } from "/js/api.js";
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
const texContent    = document.getElementById("tex-content");
const itemList      = document.getElementById("item-list");
const itemDetail    = document.getElementById("item-detail");
const btnBack       = document.getElementById("btn-back-to-items");

const SUB_VIEWS = ["yaml-view", "tex-view", "item-list-view", "item-detail-view"];

// ── State ───────────────────────────────────────────────────────────────────

let activeLessonId = null;
let activeLesson   = null;

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

// ── PDF link helpers ─────────────────────────────────────────────────────────

function setPdfLinks(lesson) {
  // Grey out links for PDFs that don't exist; still set href so nothing is broken
  btnStudentPdf.href = pdfUrl(lesson.id, "student");
  btnTeacherPdf.href = pdfUrl(lesson.id, "teacher");
  btnSlides.href     = pdfUrl(lesson.id, "slides");

  btnStudentPdf.classList.toggle("unavailable", !lesson.has_pdf_student);
  btnTeacherPdf.classList.toggle("unavailable", !lesson.has_pdf_teacher);
  btnSlides.classList.toggle("unavailable",     !lesson.has_slides_pdf);
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

    setPdfLinks(lesson);

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
  highlightToolbarBtn(`tex-${edition}`);
  showView("tex-view");
  texContent.textContent = "Loading…";
  try {
    const src = await getTex(activeLessonId, edition);
    texContent.textContent = src ?? `(no ${edition} tex on the CDN yet — may still be building or absent)`;
  } catch (err) {
    texContent.textContent = "";
    showError(err.message);
  }
}

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

btnBack.addEventListener("click", openItemsView);

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
