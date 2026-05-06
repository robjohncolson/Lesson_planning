import {
  api, pdfUrl, getTex, saveTex, rebuildPdf, sha256Hex,
  topicPdfUrl, docxUrl, pptxUrl, screenshotUrl, lessonIdToTopic, uploadAsset,
} from "/js/api.js";
import { passcode } from "/js/passcode.js";
import { username } from "/js/username.js";
import { createLessonList } from "/js/lesson-list.js";
import { renderItemList, renderItemDetail } from "/js/item-detail.js";
import { subscribeLesson } from "/js/realtime.js";
import { openMergeView } from "/js/merge.js";

// ── DOM refs ────────────────────────────────────────────────────────────────

const healthEl      = document.getElementById("health-indicator");
const errorBanner   = document.getElementById("error-banner");
const detailEmpty   = document.getElementById("detail-empty");
const detailHeader  = document.getElementById("detail-header");
const detailTitle   = document.getElementById("detail-title");
const btnStudentPdf = document.getElementById("btn-student-pdf");
const btnTeacherPdf = document.getElementById("btn-teacher-pdf");
const btnSlides     = document.getElementById("btn-slides");
const btnDoNowPdf   = document.getElementById("btn-do-now-pdf");
const btnPacer      = document.getElementById("btn-pacer");
const btnPacerPdf   = document.getElementById("btn-pacer-pdf");
const btnItems      = document.getElementById("btn-items");
const btnYaml       = document.getElementById("btn-yaml");
const btnTexStudent = document.getElementById("btn-tex-student");
const btnTexTeacher = document.getElementById("btn-tex-teacher");
const btnTexSlides  = document.getElementById("btn-tex-slides");
const btnTexDoNow   = document.getElementById("btn-tex-do-now");
const texLastEdited = document.getElementById("tex-last-edited");
const yamlContent   = document.getElementById("yaml-content");
const texContent    = document.getElementById("tex-content");   // now a <textarea>
const texEditLabel  = document.getElementById("tex-editing-label");
const btnTexSave    = document.getElementById("btn-tex-save");
const btnTexRebuild = document.getElementById("btn-tex-rebuild");
const texSaveStatus = document.getElementById("tex-save-status");
const texLog        = document.getElementById("tex-log");
const itemList      = document.getElementById("item-list");
const itemDetail    = document.getElementById("item-detail");
const btnBack           = document.getElementById("btn-back-to-items");
const texPresence       = document.getElementById("tex-presence");
const texRemoteBanner   = document.getElementById("tex-remote-banner");
const remoteBannerMsg   = document.getElementById("remote-banner-msg");
const btnTakeTheirs     = document.getElementById("btn-take-theirs");
const btnDismissBanner  = document.getElementById("btn-dismiss-banner");

// ── New asset section DOM refs ───────────────────────────────────────────────
const textbookSection   = document.getElementById("textbook-section");
const docxSection       = document.getElementById("docx-section");

const SUB_VIEWS = ["yaml-view", "tex-view", "pdf-view", "merge-view", "item-list-view", "item-detail-view"];

const pdfEmbed     = document.getElementById("pdf-embed");
const pdfLabel     = document.getElementById("pdf-view-label");
const pdfOpenTab   = document.getElementById("pdf-open-tab");

// ── State ───────────────────────────────────────────────────────────────────

let activeLessonId      = null;
let activeLesson        = null;
let activeTexEdition    = null;   // "student" | "teacher" | "slides"
let texDirty            = false;
let baseSha             = null;   // sha256 of the tex content as loaded/last-saved
let unsubscribeRealtime = null;
let pendingRemoteValue  = null;

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
  btnTexSlides.classList.toggle("active",  active === "tex-slides");
  btnTexDoNow.classList.toggle("active",   active === "tex-do_now");
}

// ── Relative time formatter ──────────────────────────────────────────────────

function formatWhen(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins || 1} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr${hrs > 1 ? "s" : ""} ago`;
  const d = new Date(iso);
  return d.toLocaleString("en-US", { month: "short", day: "numeric",
    hour: "numeric", minute: "2-digit" });
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

// ── Asset-upload helper ──────────────────────────────────────────────────────
// Shared upload flow: open file picker, POST to railway, then re-run refresh.
function triggerUpload({ accept, endpoint, onSuccess, onError }) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = accept;
  input.addEventListener("change", async () => {
    const file = input.files[0];
    if (!file) return;
    const pc = passcode.get();
    const un = username.get();
    try {
      const r = await uploadAsset(endpoint, file, pc, un);
      if (r.status === 401) { passcode.clear(); throw new Error("Wrong passcode"); }
      if (!r.ok) throw new Error(`Upload failed: HTTP ${r.status}`);
      if (onSuccess) onSuccess();
    } catch (err) {
      if (onError) onError(err.message);
      else showError(err.message);
    }
  });
  input.click();
}

// ── Textbook section (Savvas) ────────────────────────────────────────────────

async function renderTextbookSection(lessonId) {
  if (!textbookSection) return;
  const topic = lessonIdToTopic(lessonId);
  if (!topic) {
    // APStats or unrecognised → hide the whole section
    textbookSection.style.display = "none";
    return;
  }
  textbookSection.style.display = "";

  const seUrl = topicPdfUrl(topic, "SE");
  const teUrl = topicPdfUrl(topic, "TE");

  // HEAD-probe both editions in parallel
  const [seOk, teOk] = await Promise.all([
    fetch(seUrl, { method: "HEAD" }).then(r => r.ok).catch(() => false),
    fetch(teUrl, { method: "HEAD" }).then(r => r.ok).catch(() => false),
  ]);

  // Capture the active lesson at probe time so stale callbacks are ignored.
  if (lessonId !== activeLessonId) return;

  function makeEditionRow(label, exists, url, edition) {
    const row = document.createElement("div");
    row.className = "asset-row";
    if (exists) {
      const btn = document.createElement("a");
      btn.className = "btn btn-teal";
      btn.href = url;
      btn.target = "_blank";
      btn.rel = "noopener";
      btn.textContent = label;
      row.appendChild(btn);
    } else {
      const hint = document.createElement("span");
      hint.className = "asset-missing";
      hint.textContent = `${label} (not yet uploaded)`;
      row.appendChild(hint);
    }
    const upBtn = document.createElement("button");
    upBtn.className = "btn btn-muted btn-sm";
    upBtn.textContent = "Upload";
    upBtn.addEventListener("click", () => {
      triggerUpload({
        accept: ".pdf",
        endpoint: `/upload/topic-pdf/${encodeURIComponent(topic)}/${edition}`,
        onSuccess: () => renderTextbookSection(activeLessonId),
      });
    });
    row.appendChild(upBtn);
    return row;
  }

  const body = textbookSection.querySelector(".asset-section-body");
  body.innerHTML = "";
  body.appendChild(makeEditionRow("Student Edition (PDF)", seOk, seUrl, "SE"));
  body.appendChild(makeEditionRow("Teacher Edition (PDF)", teOk, teUrl, "TE"));
}

// ── DOCX / PPTX section ──────────────────────────────────────────────────────

async function renderDocxSection(lessonId) {
  if (!docxSection) return;
  docxSection.style.display = "";

  const slots = [
    { label: "Student DOCX",  url: docxUrl(lessonId, "student"),  endpoint: `/upload/docx/${encodeURIComponent(lessonId)}/student`,  accept: ".docx" },
    { label: "Teacher DOCX",  url: docxUrl(lessonId, "teacher"),  endpoint: `/upload/docx/${encodeURIComponent(lessonId)}/teacher`,  accept: ".docx" },
    { label: "Slides PPTX",   url: pptxUrl(lessonId),             endpoint: `/upload/docx/${encodeURIComponent(lessonId)}/slides`,   accept: ".pptx" },
  ];

  // Probe all three in parallel
  const exists = await Promise.all(
    slots.map(s => fetch(s.url, { method: "HEAD" }).then(r => r.ok).catch(() => false))
  );

  if (lessonId !== activeLessonId) return;

  const body = docxSection.querySelector(".asset-section-body");
  body.innerHTML = "";

  slots.forEach((slot, i) => {
    const row = document.createElement("div");
    row.className = "asset-row";

    if (exists[i]) {
      const btn = document.createElement("a");
      btn.className = "btn btn-navy";
      btn.href = slot.url;
      btn.target = "_blank";
      btn.rel = "noopener";
      btn.textContent = `${slot.label} ↓`;
      row.appendChild(btn);
    } else {
      const hint = document.createElement("span");
      hint.className = "asset-missing";
      hint.textContent = `${slot.label} (not yet uploaded)`;
      row.appendChild(hint);
    }

    const upBtn = document.createElement("button");
    upBtn.className = "btn btn-muted btn-sm";
    upBtn.textContent = "Upload";
    const slotSnapshot = slot;
    upBtn.addEventListener("click", () => {
      triggerUpload({
        accept: slotSnapshot.accept,
        endpoint: slotSnapshot.endpoint,
        onSuccess: () => renderDocxSection(activeLessonId),
      });
    });
    row.appendChild(upBtn);
    body.appendChild(row);
  });
}

// ── Lesson selection ─────────────────────────────────────────────────────────

async function selectLesson(id) {
  clearError();
  // Reset asset sections immediately so stale content doesn't linger during re-probe
  if (textbookSection) {
    textbookSection.style.display = "none";
    const b = textbookSection.querySelector(".asset-section-body");
    if (b) b.innerHTML = "";
  }
  if (docxSection) {
    docxSection.style.display = "none";
    const b = docxSection.querySelector(".asset-section-body");
    if (b) b.innerHTML = "";
  }
  if (unsubscribeRealtime) {
    await unsubscribeRealtime();
    unsubscribeRealtime = null;
  }
  try {
    const lesson = await api.getLesson(id);
    if (!lesson) { showError(`Lesson ${id} not found.`); return; }

    activeLessonId = id;
    activeLesson   = lesson;

    // Carry the active lesson into the DAG nav link so clicking "DAG"
    // opens focused on this lesson instead of the full graph.
    const navDag = document.getElementById("nav-dag");
    if (navDag) navDag.href = `/dag.html?lesson=${encodeURIComponent(id)}`;

    detailEmpty.style.display  = "none";
    detailHeader.style.display = "";
    detailTitle.textContent    = `${lesson.id}${lesson.title ? " — " + lesson.title : ""}`;

    setPdfButtons(lesson);

    // Do Now PDF: no flag in the lessons row, so HEAD-probe the public URL.
    // Fire-and-forget — don't block selectLesson on this.
    btnDoNowPdf.style.display = "none";
    const doNowLesson = id;
    fetch(pdfUrl(id, "do_now"), { method: "HEAD" })
      .then((r) => {
        if (r.ok && doNowLesson === activeLessonId) {
          btnDoNowPdf.style.display = "";
        }
      })
      .catch(() => {});

    // Textbook + DOCX sections — fire-and-forget, parallel with Do Now probe
    renderTextbookSection(id).catch(() => {});
    renderDocxSection(id).catch(() => {});

    // Pacer link: derive L{NN} prefix from lesson id (e.g. L41_P2 -> L41)
    const pacerPrefix = (id.match(/^L\d+/) || [])[0];
    if (pacerPrefix && btnPacer) {
      btnPacer.href = `/pacers/${pacerPrefix}_Pacer.html`;
      btnPacer.style.display = "";
    } else if (btnPacer) {
      btnPacer.style.display = "none";
    }

    // Per-period printable Pacer PDF (static asset under /pacers/).
    // HEAD-probe so the button only shows for lessons that actually have a PDF
    // (currently just L35_P3_obs). Fire-and-forget — don't block selectLesson.
    if (btnPacerPdf) {
      btnPacerPdf.style.display = "none";
      const pacerPdfPath = `/pacers/${id}_pacer.pdf`;
      const pacerPdfLesson = id;
      fetch(pacerPdfPath, { method: "HEAD" })
        .then((r) => {
          if (r.ok && pacerPdfLesson === activeLessonId) {
            btnPacerPdf.href = pacerPdfPath;
            btnPacerPdf.style.display = "";
          }
        })
        .catch(() => {});
    }

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
  texLastEdited.textContent = "";
  texLog.style.display = "none";
  texLog.textContent   = "";
  texPresence.textContent = "";
  texRemoteBanner.style.display = "none";
  pendingRemoteValue = null;

  // Fire tex fetch and audit lookup in parallel. Capture the lesson id at
  // call time — if the teacher clicks a different lesson before the audit
  // fetch resolves, don't paint the old lesson's audit onto the new view.
  const requestedLesson = activeLessonId;
  const auditPromise = api.getLastAudit(requestedLesson).then((row) => {
    if (requestedLesson !== activeLessonId) return;
    if (row) {
      const who = row.changed_by || "(anonymous)";
      texLastEdited.textContent = `Last edit: ${who} · ${formatWhen(row.changed_at)}`;
    }
  }).catch(() => {});

  try {
    const src = await getTex(activeLessonId, edition);
    texContent.value = src ?? "";
    baseSha = await sha256Hex(src ?? "");
    if (!src) {
      texSaveStatus.textContent = `(no ${edition} tex stored yet)`;
    }
    // Enable buttons now that content is loaded; actual save requires dirty
    btnTexSave.disabled    = false;
    btnTexRebuild.disabled = false;
  } catch (err) {
    texContent.value = "";
    baseSha = null;
    showError(err.message);
  }

  // Let audit run; ignore its outcome (already caught above)
  auditPromise;

  // Tear down any existing subscription, then subscribe to the newly opened lesson.
  if (unsubscribeRealtime) {
    await unsubscribeRealtime();
    unsubscribeRealtime = null;
  }
  const currentEdition = activeTexEdition;
  const currentLesson  = activeLessonId;
  const currentUser    = username.get() || "(anonymous)";

  unsubscribeRealtime = subscribeLesson({
    lessonId: currentLesson,
    username: currentUser,

    onPresenceChange(users) {
      // Only render when others are also present
      const others = users.filter((u) => u !== currentUser);
      if (others.length === 0) {
        texPresence.textContent = "";
      } else {
        const total = others.length + 1;
        texPresence.textContent = `${total} editing: ${others.join(", ")}`;
      }
    },

    onRemoteSave({ field, new_value, changed_at }) {
      // Only react when the changed field matches what's currently open
      if (field !== `tex_${currentEdition}`) return;
      // Filter own-save echoes: if new_value matches what's in the textarea
      // and it's not dirty, this is almost certainly our own save bouncing back.
      if (new_value === texContent.value && !texDirty) return;
      pendingRemoteValue = new_value;
      const edition = currentEdition;
      const when = changed_at ? formatWhen(changed_at) : "";
      remoteBannerMsg.textContent = `Someone just saved ${edition}.tex${when ? " (" + when + ")" : ""}.`;
      texRemoteBanner.style.display = "";
    },
  });
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

// Returns an async onApply handler for openMergeView. Named function so it can
// reference itself for the rare double-conflict case without arguments.callee.
function makeMergeApplyHandler() {
  async function applyHandler(mergedText, newBaseSha) {
    setStatus("Saving merged…");
    try {
      await saveTex(activeLessonId, activeTexEdition, mergedText, newBaseSha);
      texContent.value = mergedText;
      baseSha = await sha256Hex(mergedText);
      texDirty = false;
      showView("tex-view");
      setStatus("Merged and saved");
    } catch (saveErr) {
      if (saveErr.name === "TexConflict") {
        // A further conflict during apply — open merge view again with newer server state.
        openMergeView({
          theirs:    saveErr.current_tex,
          yours:     mergedText,
          changedBy: saveErr.changed_by,
          onApply:   applyHandler,
          onDismiss: () => { showView("tex-view"); },
        });
        setStatus("Conflict again — review merge view", true);
      } else {
        setStatus(saveErr.message, true);
        showView("tex-view");
      }
    }
  }
  return applyHandler;
}

async function doSave() {
  if (!activeLessonId || !activeTexEdition) return;
  const body = texContent.value;
  setStatus("Saving…");
  try {
    await saveTex(activeLessonId, activeTexEdition, body, baseSha);
    texDirty = false;
    baseSha = await sha256Hex(body);
    setStatus("Saved");
  } catch (err) {
    if (err.name === "TexConflict") {
      openMergeView({
        theirs:    err.current_tex,
        yours:     texContent.value,
        changedBy: err.changed_by,

        onApply: makeMergeApplyHandler(),

        onDismiss() {
          showView("tex-view");
        },
      });
      setStatus("Conflict — review merge view", true);
    } else if (err.name === "WrongPasscode") {
      // re-prompt once: passcode.clear() already called inside saveTex
      setStatus("Wrong passcode — retrying…", true);
      await saveTex(activeLessonId, activeTexEdition, body, baseSha);
      texDirty = false;
      baseSha = await sha256Hex(body);
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
btnTexSlides.addEventListener("click",  () => openTexView("slides"));
btnTexDoNow.addEventListener("click",   () => openTexView("do_now"));

btnTexSave.addEventListener("click",    () => doSave().catch(() => {}));
btnTexRebuild.addEventListener("click", () => doRebuild().catch(() => {}));

btnBack.addEventListener("click", openItemsView);

btnTakeTheirs.addEventListener("click", () => {
  if (pendingRemoteValue !== null) {
    texContent.value = pendingRemoteValue;
    texDirty = false;
    pendingRemoteValue = null;
  }
  texRemoteBanner.style.display = "none";
});

btnDismissBanner.addEventListener("click", () => {
  pendingRemoteValue = null;
  texRemoteBanner.style.display = "none";
});

btnStudentPdf.addEventListener("click", () => openPdfView("student"));
btnTeacherPdf.addEventListener("click", () => openPdfView("teacher"));
btnSlides.addEventListener("click",     () => openPdfView("slides"));
btnDoNowPdf.addEventListener("click",   () => openPdfView("do_now"));

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

  // Deep-link support: /?lesson=L35_P2 auto-selects on load (used by schedule page)
  const deepLink = new URLSearchParams(location.search).get("lesson");
  if (deepLink) {
    lessonList.setActive(deepLink);
    selectLesson(deepLink);
  }
}

boot();
