import { api } from "/js/api.js";

function escHtml(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// Returns three colored squares indicating which PDFs exist for this lesson
function artifactSquares(lesson) {
  const sq = (cls, label, present) =>
    `<span class="artifact-sq ${cls}${present ? "" : " absent"}" title="${label}"></span>`;
  return (
    sq("sq-student", "Student PDF", lesson.has_pdf_student) +
    sq("sq-teacher", "Teacher PDF", lesson.has_pdf_teacher) +
    sq("sq-slides",  "Slides PDF",  lesson.has_slides_pdf)
  );
}

function buildRow(lesson, onSelect) {
  const row = document.createElement("div");
  row.className = "lesson-row";
  row.setAttribute("role", "option");
  row.dataset.id = lesson.id;
  row.innerHTML =
    `<span class="lesson-id">${escHtml(lesson.id)}</span>` +
    `<span class="lesson-title">${escHtml(lesson.title ?? "")}</span>` +
    `<span class="lesson-artifacts">${artifactSquares(lesson)}</span>`;
  row.addEventListener("click", () => onSelect(lesson.id));
  return row;
}

export function createLessonList({ onSelect }) {
  const container = document.getElementById("lesson-list");
  const filterInput = document.getElementById("filter-input");
  let allLessons = [];
  let activeId = null;

  function render(lessons) {
    container.innerHTML = "";
    for (const lesson of lessons) {
      const row = buildRow(lesson, (id) => {
        setActive(id);
        onSelect(id);
      });
      if (lesson.id === activeId) row.classList.add("active");
      container.appendChild(row);
    }
  }

  function setActive(id) {
    activeId = id;
    for (const row of container.querySelectorAll(".lesson-row")) {
      row.classList.toggle("active", row.dataset.id === id);
    }
  }

  function applyFilter(query) {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? allLessons.filter(l =>
          l.id.toLowerCase().includes(q) ||
          (l.title ?? "").toLowerCase().includes(q)
        )
      : allLessons;
    render(filtered);
  }

  filterInput.addEventListener("input", e => applyFilter(e.target.value));

  async function init() {
    allLessons = await api.listLessons();
    render(allLessons);
  }

  return { init, setActive };
}
