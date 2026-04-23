"""Build the curriculum DAG from the tagged registry.

Reads questionbank/registry.jsonl + questionbank/assessment_shells.jsonl.
Emits three artifacts into graph/:
  - graph.html         — interactive vis-network view (CDN, no pip deps)
  - coverage_report.md — standards x lesson matrix, DOK-3 flavor matrix, orphans
  - chains.md          — echo-chains (transitively-connected cross-unit items)

Usage:
    python qb_graph.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REGISTRY = Path("questionbank/registry.jsonl")
SHELLS = Path("questionbank/assessment_shells.jsonl")
OUT = Path("graph")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ── HTML template for graph.html ─────────────────────────────────────────────
# Kept as a plain (non-f) string so JS braces don't need doubling. Placeholders:
#   __NODES__   — replaced with json.dumps(vis_nodes)
#   __EDGES__   — replaced with json.dumps(vis_edges)
DAG_HTML_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<title>Algebra 2 Curriculum DAG</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body { font-family: system-ui, sans-serif; margin: 0; background: #202124; color: #e8eaed;
         display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
  #legend { padding: 8px 16px; background: #303134; border-bottom: 1px solid #5f6368; flex-shrink: 0; }
  #legend span { margin-right: 16px; font-size: 13px; }
  .sw { display: inline-block; width: 12px; height: 12px; margin-right: 4px; vertical-align: middle; border-radius: 2px; }
  #main { display: flex; flex: 1; min-height: 0; }
  #net { flex: 1; background: #202124; min-width: 0; }
  #detail {
    width: 360px; flex-shrink: 0; overflow: auto;
    background: #292b2f; border-left: 1px solid #444; padding: 18px 18px 40px 18px;
    box-sizing: border-box; font-size: 13px; line-height: 1.5;
  }
  #detail.empty { color: #7a828a; font-style: italic; padding-top: 40%; text-align: center; }
  #detail h2 { margin: 0 0 4px; font-size: 15px; color: #fbbc04; word-break: break-all; }
  #detail .meta-row { margin: 10px 0; }
  #detail .meta-row strong { color: #e8eaed; margin-right: 4px; }
  #detail .meta-row .value { color: #b8c0c8; }
  #detail .tag {
    display: inline-block; background: #3a3d42; color: #dadce0;
    padding: 2px 7px; border-radius: 3px; font-size: 11px; margin: 2px 4px 2px 0;
  }
  #detail .dok {
    display: inline-block; padding: 2px 7px; border-radius: 3px;
    font-size: 11px; font-weight: 600; color: #fff;
  }
  #detail .dok-1 { background: #8ab4f8; color: #202124; }
  #detail .dok-2 { background: #fbbc04; color: #202124; }
  #detail .dok-3 { background: #ea4335; }
  #detail .prompt {
    background: #1f2125; border-radius: 4px; padding: 10px 12px;
    margin-top: 12px; font-family: Consolas, Menlo, monospace;
    font-size: 12px; white-space: pre-wrap; color: #e8eaed;
  }
  #detail a.neighbor {
    display: inline-block; margin: 3px 4px 3px 0; padding: 3px 8px;
    background: #3a3d42; color: #8ab4f8; border-left: 3px solid #888;
    border-radius: 2px; cursor: pointer; font-size: 11px;
    font-family: Consolas, Menlo, monospace; text-decoration: none;
  }
  #detail a.neighbor:hover { background: #4a4d52; color: #fff; }
  #focus-badge {
    display: inline-block; background: #fbbc04; color: #202124;
    padding: 2px 8px; border-radius: 3px; font-size: 12px;
    font-weight: 600; margin-left: 12px; vertical-align: middle;
  }
</style>
</head><body>
<div id="legend">
  <strong>Curriculum DAG</strong>
  &nbsp;Nodes colored by role, bordered by DOK-3 flavor. Edges: <span style="color:#5f6368">prereq</span>, <span style="color:#1a73e8">rehearses</span>, <span style="color:#ea4335">echoes</span>.
  <br>
  <span><span class="sw" style="background:#ea4335"></span>dok3-driver</span>
  <span><span class="sw" style="background:#34a853"></span>launch</span>
  <span><span class="sw" style="background:#fbbc04"></span>try-it</span>
  <span><span class="sw" style="background:#f28b82"></span>practice</span>
  <span><span class="sw" style="background:#8ab4f8"></span>do-now</span>
  <span><span class="sw" style="background:#c084fc"></span>assessment</span>
  <span><span class="sw" style="background:#dadce0"></span>stretch</span>
</div>
<div id="main">
  <div id="net"></div>
  <aside id="detail" class="empty">Click a node to see its details.</aside>
</div>
<script>
  const nodes = new vis.DataSet(__NODES__);
  const edges = new vis.DataSet(__EDGES__);
  const network = new vis.Network(document.getElementById('net'), {nodes, edges}, {
    physics: { solver: 'forceAtlas2Based', stabilization: { iterations: 300 } },
    interaction: { hover: true, tooltipDelay: 999999 },  // native tooltip off
    nodes: { shape: 'dot', font: { color: '#e8eaed', size: 11 } },
    edges: { smooth: { type: 'continuous' }, arrows: { to: { scaleFactor: 0.5 } } },
    groups: {},
  });

  // Cache titles + strip from node data so vis-network doesn't render the
  // raw hover tooltip (literal \n characters).
  const titleById = {};
  nodes.get().forEach(n => { titleById[n.id] = n.title; });
  nodes.update(nodes.get().map(n => ({ id: n.id, title: undefined })));

  // Build adjacency for neighbor navigation in the detail panel.
  const EDGE_KIND = {
    "#5f6368": "prereq",
    "#1a73e8": "rehearses",
    "#ea4335": "echoes",
  };
  const neighborsByNode = {};
  edges.get().forEach(e => {
    const kind = EDGE_KIND[e.color] || "link";
    (neighborsByNode[e.from] = neighborsByNode[e.from] || []).push(
      { id: e.to, color: e.color, kind, direction: "out" }
    );
    (neighborsByNode[e.to] = neighborsByNode[e.to] || []).push(
      { id: e.from, color: e.color, kind, direction: "in" }
    );
  });

  function escHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderDetail(node) {
    const detail = document.getElementById("detail");
    if (!node) {
      detail.className = "empty";
      detail.innerHTML = "Click a node to see its details.";
      return;
    }
    // Titles embed literal "\n" two-char sequences, not real newlines.
    const rawTitle = titleById[node.id] || node.title || "";
    const raw = rawTitle.replace(/\\n/g, "\n").replace(/\r/g, "");
    const parts = raw.split(/\n\n/);
    const header = (parts[0] || "").split("\n");
    const prompt = parts.slice(1).join("\n\n").trim();

    const id = header[0] || node.id;
    const rows = [];
    for (const line of header.slice(1)) {
      const pairs = line.split(/\s{2,}/);
      for (const pair of pairs) {
        const m = /^([^:]+):\s*(.+)$/.exec(pair.trim());
        if (m) rows.push([m[1].trim().toLowerCase(), m[2].trim()]);
      }
    }
    const get = (k) => (rows.find(r => r[0] === k) || [])[1] || "";
    const dok  = get("dok");
    const role = get("role");
    const lesson = get("lesson");
    const standards = get("standards");
    const skills = get("skills");

    const neighbors = neighborsByNode[node.id] || [];
    const buckets = {
      "prereq-in":    { label: "Prerequisites (incoming)",   items: [] },
      "prereq-out":   { label: "Leads to (outgoing)",        items: [] },
      "rehearses-in": { label: "Rehearsed by",               items: [] },
      "rehearses-out":{ label: "Rehearses",                  items: [] },
      "echoes-in":    { label: "Echoed by",                  items: [] },
      "echoes-out":   { label: "Echoes",                     items: [] },
    };
    for (const n of neighbors) {
      const key = n.kind + "-" + n.direction;
      (buckets[key] || (buckets[key] = { label: n.kind + " (" + n.direction + ")", items: [] }))
        .items.push(n);
    }
    const neighborHtml = Object.entries(buckets)
      .filter(([_, b]) => b.items.length > 0)
      .map(([key, b]) => '<div class="meta-row"><strong>' + escHtml(b.label) + ':</strong> '
        + b.items.map(n =>
          '<a class="neighbor" data-target="' + escHtml(n.id) +
          '" style="border-left-color:' + escHtml(n.color || "#888") + ';">' + escHtml(n.id) + '</a>'
        ).join("")
        + '</div>').join("");

    detail.className = "";
    detail.innerHTML =
      '<h2>' + escHtml(id) + '</h2>' +
      '<div class="meta-row">' +
        (lesson ? '<span class="tag">lesson ' + escHtml(lesson) + '</span>' : "") +
        (role ? '<span class="tag">' + escHtml(role) + '</span>' : "") +
        (dok ? '<span class="dok dok-' + escHtml(dok) + '">DOK ' + escHtml(dok) + '</span>' : "") +
      '</div>' +
      (standards ? '<div class="meta-row"><strong>Standards:</strong> ' +
        standards.split(/,\s*/).map(s => '<span class="tag">' + escHtml(s) + '</span>').join("") + '</div>' : "") +
      (skills ? '<div class="meta-row"><strong>Skills:</strong> ' +
        skills.split(/,\s*/).map(s => '<span class="tag">' + escHtml(s) + '</span>').join("") + '</div>' : "") +
      (prompt ? '<div class="meta-row"><strong>Prompt:</strong><div class="prompt">' +
        escHtml(prompt) + '</div></div>' : "") +
      (neighborHtml || '<div class="meta-row" style="color:#7a828a;font-style:italic;">No connections.</div>');

    detail.querySelectorAll("a.neighbor").forEach(a => {
      a.addEventListener("click", () => {
        const target = a.dataset.target;
        const n = nodes.get(target);
        if (n) { network.selectNodes([target]); renderDetail(n); }
      });
    });
  }
  network.on("click", (params) => {
    if (params.nodes.length === 0) { renderDetail(null); return; }
    renderDetail(nodes.get(params.nodes[0]));
  });

  // Optional ?lesson=4-1 query param — fade non-focus nodes, fit to focused set.
  const _hl = new URLSearchParams(location.search).get("lesson");
  if (_hl) {
    const focus = nodes.get({ filter: n => n.group === _hl });
    if (focus.length) {
      nodes.update(nodes.get().map(n => n.group === _hl
        ? { id: n.id, opacity: 1, borderWidth: 3 }
        : { id: n.id, opacity: 0.18 }
      ));
      const focusIds = focus.map(n => n.id);
      network.once("stabilizationIterationsDone", () => {
        network.fit({ nodes: focusIds, animation: { duration: 400 } });
      });
      const badge = document.createElement("span");
      badge.id = "focus-badge";
      badge.textContent = "Focused: lesson " + _hl + " (" + focus.length + " nodes)";
      document.getElementById("legend").appendChild(badge);
    }
  }
</script>
</body></html>
"""


# --- DOK-3 flavor classifier --------------------------------------------------
# Flavor inference from skill_tokens. Order matters: first match wins.
FLAVOR_RULES = [
    ("prove-by-properties", {"prove-via-exponent-laws", "closure-argument"}),
    ("read-from-representation",
     {"estimate-log-from-graph", "read-graph-values", "compare-graphs-y-equals-x-reflection"}),
    ("model-then-extract",
     {"extract-time-from-model", "generalize-numerical-result", "model-decay",
      "model-continuous-compound", "interpret-root-in-context"}),
    ("derive-from-constraint",
     {"build-equation-from-constraint", "extract-dimension-from-volume",
      "model-mixture-context", "find-inverse-function"}),
]


def classify_flavor(tokens: list[str]) -> str | None:
    t = set(tokens or [])
    for flavor, key in FLAVOR_RULES:
        if t & key:
            return flavor
    return None


# --- load ---------------------------------------------------------------------
def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    registry = load_jsonl(REGISTRY)
    shells = load_jsonl(SHELLS)
    all_items = registry + shells
    by_id = {r["id"]: r for r in all_items}

    tagged = [r for r in registry if r.get("role") or r.get("skill_tokens") or r.get("standards")]
    print(f"Registry: {len(registry)} rows, {len(tagged)} tagged, {len(shells)} assessment shells.")

    OUT.mkdir(exist_ok=True)

    # --- coverage report -----------------------------------------------------
    standards_by_lesson: dict[str, Counter] = defaultdict(Counter)
    for r in tagged:
        for s in r.get("standards", []) or []:
            standards_by_lesson[r["lesson"]][s] += 1
    all_standards = sorted({s for c in standards_by_lesson.values() for s in c})
    all_lessons = sorted(standards_by_lesson.keys())

    # DOK-3 flavor matrix
    flavor_by_lesson: dict[str, Counter] = defaultdict(Counter)
    for r in tagged:
        if r.get("role") == "dok3-driver" or r.get("dok") == 3:
            fl = classify_flavor(r.get("skill_tokens", []))
            if fl:
                flavor_by_lesson[r["lesson"]][fl] += 1
    all_flavors = ["derive-from-constraint", "prove-by-properties",
                   "model-then-extract", "read-from-representation"]

    # orphans = tagged items with no inbound edges (not listed in any prereq_ids, rehearses, echoes)
    inbound: set[str] = set()
    for r in all_items:
        for f in ("prereq_ids", "rehearses", "echoes"):
            for target in r.get(f, []) or []:
                inbound.add(target)
    orphans = [r["id"] for r in tagged
               if r["id"] not in inbound
               and r.get("role") not in ("do-now-bridge", "do-now-explore", "launch-model-1", "launch-model-2")]

    lines: list[str] = []
    lines.append("# Coverage report\n")
    lines.append(f"Tagged items: **{len(tagged)}**. Assessment shells: **{len(shells)}**.\n")

    lines.append("## Standards × Lesson\n")
    lines.append("| Lesson | " + " | ".join(all_standards) + " | total |")
    lines.append("|" + "---|" * (len(all_standards) + 2))
    for L in all_lessons:
        row = [L]
        total = 0
        for s in all_standards:
            n = standards_by_lesson[L].get(s, 0)
            total += n
            row.append(str(n) if n else ".")
        row.append(f"**{total}**")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    thin = [s for s in all_standards if sum(standards_by_lesson[L].get(s, 0) for L in all_lessons) <= 1]
    if thin:
        lines.append(f"**Thinly-covered standards** (≤1 tagged item): {', '.join(thin)}\n")

    lines.append("## DOK-3 flavor × Lesson\n")
    lines.append("| Lesson | " + " | ".join(all_flavors) + " |")
    lines.append("|" + "---|" * (len(all_flavors) + 1))
    for L in all_lessons:
        row = [L]
        for f in all_flavors:
            n = flavor_by_lesson[L].get(f, 0)
            row.append(str(n) if n else ".")
        lines.append("| " + " | ".join(row) + " |")
    flavor_totals = Counter()
    for L in all_lessons:
        flavor_totals.update(flavor_by_lesson[L])
    lines.append("")
    lines.append("**Flavor totals:** " + ", ".join(f"{f}={flavor_totals[f]}" for f in all_flavors))
    cold = [f for f in all_flavors if flavor_totals[f] <= 1]
    if cold:
        lines.append(f"\n**Cold flavors** (≤1 exemplar): {', '.join(cold)} — plant a seed earlier.\n")

    lines.append("## Orphans\n")
    lines.append(f"Items with no inbound edges and no do-now/launch role (unexpected): **{len(orphans)}**")
    if orphans:
        for oid in orphans:
            r = by_id[oid]
            role = r.get("role", "?")
            lines.append(f"- `{oid}` (lesson {r['lesson']}, role={role})")

    (OUT / "coverage_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT / 'coverage_report.md'}")

    # --- chains (echo connected components) ----------------------------------
    # Walk echoes as an undirected graph over tagged items.
    adj: dict[str, set[str]] = defaultdict(set)
    for r in tagged:
        for t in r.get("echoes", []) or []:
            adj[r["id"]].add(t)
            adj[t].add(r["id"])
    seen: set[str] = set()
    chains: list[list[str]] = []
    for node in adj:
        if node in seen:
            continue
        stack = [node]
        comp: list[str] = []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.append(cur)
            stack.extend(adj[cur] - seen)
        if len(comp) >= 2:
            chains.append(sorted(comp))

    chain_lines: list[str] = ["# Echo chains\n",
                              "Each chain = a connected component of the echoes graph. ",
                              "A chain crossing two or more lessons is a cross-unit through-line — the strongest cohesion signal in the DAG.\n"]
    chains.sort(key=lambda c: (-len({by_id[i]["lesson"] for i in c if i in by_id}), -len(c)))
    for i, comp in enumerate(chains, 1):
        lessons = sorted({by_id[iid]["lesson"] for iid in comp if iid in by_id})
        chain_lines.append(f"## Chain {i} — {len(comp)} items across {len(lessons)} lesson(s): {', '.join(lessons)}\n")
        flavors = Counter()
        for iid in comp:
            if iid in by_id:
                fl = classify_flavor(by_id[iid].get("skill_tokens", []))
                if fl:
                    flavors[fl] += 1
        if flavors:
            chain_lines.append(f"Flavors: {dict(flavors)}\n")
        for iid in comp:
            r = by_id.get(iid, {})
            prompt = (r.get("prompt") or "[shell]")[:100].replace("\n", " ")
            prompt = re.sub(r"[^\x20-\x7e]", "?", prompt)
            chain_lines.append(f"- `{iid}` (L{r.get('lesson', '?')}, dok={r.get('dok', '?')}): {prompt}")
        chain_lines.append("")

    (OUT / "chains.md").write_text("\n".join(chain_lines), encoding="utf-8")
    print(f"Wrote {OUT / 'chains.md'} ({len(chains)} chains)")

    # --- interactive graph ---------------------------------------------------
    ROLE_COLORS = {
        "do-now-explore": "#8ab4f8",
        "do-now-bridge": "#8ab4f8",
        "launch-model-1": "#34a853",
        "launch-model-2": "#34a853",
        "explore-tps": "#fbbc04",
        "explore-practice": "#f28b82",
        "optional-stretch": "#dadce0",
        "dok3-driver": "#ea4335",
        "exit-recap": "#9aa0a6",
        "assessment-rehearsal": "#a78bfa",
        "assessment-shell": "#c084fc",
    }
    FLAVOR_BORDER = {
        "derive-from-constraint": "#b91c1c",
        "prove-by-properties": "#047857",
        "model-then-extract": "#1d4ed8",
        "read-from-representation": "#9333ea",
    }

    vis_nodes = []
    vis_edges = []

    nodes_to_include = {r["id"] for r in tagged} | {s["id"] for s in shells}
    for r in list(tagged) + list(shells):
        rid = r["id"]
        if rid not in nodes_to_include:
            continue
        role = r.get("role") or "explore-practice"
        color = ROLE_COLORS.get(role, "#dadce0")
        dok = r.get("dok") or 1
        size = 10 + 6 * int(dok)
        flavor = classify_flavor(r.get("skill_tokens", [])) if r.get("role") == "dok3-driver" else None
        border = FLAVOR_BORDER.get(flavor, "#202124") if flavor else "#202124"
        prompt = (r.get("prompt") or "")[:140].replace("\n", " ")
        prompt = re.sub(r"[^\x20-\x7e]", "?", prompt)
        tokens = ", ".join(r.get("skill_tokens", []) or [])
        standards = ", ".join(r.get("standards", []) or [])
        title = (f"{rid}\\nlesson: {r.get('lesson','?')}  dok: {dok}  role: {role}"
                 f"\\nstandards: {standards}\\nskills: {tokens}\\n\\n{prompt}")
        vis_nodes.append({
            "id": rid,
            "label": rid.replace("-savvas-", "-").replace("-lesson-", "-")[:28],
            "title": title,
            "color": {"background": color, "border": border},
            "borderWidth": 3 if flavor else 1,
            "size": size,
            "group": r.get("lesson", "?"),
        })

    for r in tagged:
        rid = r["id"]
        for t in r.get("prereq_ids", []) or []:
            if t in nodes_to_include:
                vis_edges.append({"from": t, "to": rid, "color": "#5f6368", "arrows": "to"})
        for t in r.get("rehearses", []) or []:
            if t in nodes_to_include:
                vis_edges.append({"from": rid, "to": t, "color": "#1a73e8", "arrows": "to", "dashes": True})
        for t in r.get("echoes", []) or []:
            if t in nodes_to_include:
                vis_edges.append({"from": rid, "to": t, "color": "#ea4335", "dashes": [2, 4]})

    # Template is a plain (non-f) string so JS braces don't need doubling.
    # Two placeholders (__NODES__ / __EDGES__) get filled via replace().
    html = DAG_HTML_TEMPLATE \
        .replace("__NODES__", json.dumps(vis_nodes)) \
        .replace("__EDGES__", json.dumps(vis_edges))
    (OUT / "graph.html").write_text(html, encoding="utf-8")
    print(f"Wrote {OUT / 'graph.html'} ({len(vis_nodes)} nodes, {len(vis_edges)} edges)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
