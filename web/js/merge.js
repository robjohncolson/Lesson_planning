import { diffLines } from "https://esm.sh/diff@5";
import { sha256Hex } from "/js/api.js";

// ── HTML escaping ─────────────────────────────────────────────────────────────

function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── renderDiffPane ────────────────────────────────────────────────────────────
// text:      full text to render (used for context; actual lines come from parts)
// diffParts: result of diffLines(theirs, yours)
// which:     "theirs" | "yours"
//
// "theirs" pane highlights parts where removed=true (lines only in theirs).
// "yours"  pane highlights parts where added=true  (lines only in yours).
// Common lines (neither added nor removed) render without a wrapper.
//
// Returns an HTML string suitable for pane.innerHTML.

export function renderDiffPane(text, diffParts, which) {
  let html = "";
  for (const part of diffParts) {
    // Determine whether this part is highlighted in this pane.
    const highlight =
      (which === "theirs" && part.removed) ||
      (which === "yours"  && part.added);

    // Skip parts that belong entirely to the other side (would appear blank).
    // "theirs" pane skips added-only parts; "yours" pane skips removed-only parts.
    if (which === "theirs" && part.added)   continue;
    if (which === "yours"  && part.removed) continue;

    const cls = highlight
      ? (which === "theirs" ? "diff-removed" : "diff-added")
      : null;

    // Split value into lines, preserving trailing newlines as separate entries.
    // diffLines preserves trailing newlines inside each part's value string.
    const escaped = escHtml(part.value);
    if (cls) {
      html += `<span class="${cls}">${escaped}</span>`;
    } else {
      html += escaped;
    }
  }
  return html;
}

// ── openMergeView ─────────────────────────────────────────────────────────────
// theirs:    current server tex body (conflict payload)
// yours:     what was in the editor when the conflict fired
// changedBy: server's last-editor name (or null)
// onApply(mergedText, newBaseSha): called when user clicks "Apply merged"
// onDismiss():                     called on "Cancel"

export function openMergeView({ theirs, yours, changedBy, onApply, onDismiss }) {
  // Grab DOM refs
  const mergeView     = document.getElementById("merge-view");
  const mergeMsg      = document.getElementById("merge-msg");
  const mergeTheirs   = document.getElementById("merge-theirs");
  const mergeYours    = document.getElementById("merge-yours");
  const mergeMerged   = document.getElementById("merge-merged");
  const btnApply      = document.getElementById("btn-apply-merged");
  const btnTakeTheirs = document.getElementById("btn-take-theirs-m");
  const btnKeepYours  = document.getElementById("btn-keep-yours");
  const btnCancel     = document.getElementById("btn-cancel-merge");

  // Header message
  mergeMsg.textContent =
    `Conflict: ${changedBy || "someone"} saved while you were editing. Review and choose.`;

  // Compute diff once; reuse in both panes
  const parts = diffLines(theirs, yours);

  // Populate read-only panes
  mergeTheirs.innerHTML = renderDiffPane(theirs, parts, "theirs");
  mergeYours.innerHTML  = renderDiffPane(yours,  parts, "yours");

  // Editable merge pane starts with yours
  mergeMerged.value = yours;

  // Show the merge view (showView in main.js will handle hiding siblings)
  // We reveal it directly here so merge.js stays self-contained.
  for (const id of ["yaml-view", "tex-view", "pdf-view", "item-list-view",
                     "item-detail-view"]) {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  }
  mergeView.style.display = "";

  // ── Button handlers ───────────────────────────────────────────────────────

  // Clone nodes to remove any previous event listeners before re-attaching.
  function rewire(el, handler) {
    const fresh = el.cloneNode(true);
    el.parentNode.replaceChild(fresh, el);
    fresh.addEventListener("click", handler);
    return fresh;
  }

  rewire(btnApply, async () => {
    const mergedText = document.getElementById("merge-merged").value;
    // The base sha the user reconciled against is sha(theirs) — the version
    // they have now reviewed. This lets the server detect a *further* conflict
    // if someone else saves again between the user's review and their re-save.
    const newBaseSha = await sha256Hex(theirs);
    onApply(mergedText, newBaseSha);
  });

  rewire(btnTakeTheirs, () => {
    document.getElementById("merge-merged").value = theirs;
    document.getElementById("merge-merged").focus();
  });

  rewire(btnKeepYours, () => {
    document.getElementById("merge-merged").value = yours;
    document.getElementById("merge-merged").focus();
  });

  rewire(btnCancel, () => {
    onDismiss();
  });
}
