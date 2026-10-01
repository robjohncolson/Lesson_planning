"""check_te.py <file.tex> [expected_title] -- structural self-check for a2_X-Y_TE.tex files."""
import re, sys
from pathlib import Path

def expand(s):
    out = []
    for c in re.split(r"[;,]", re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)):
        c = c.strip()
        m = re.match(r"(\d+)\s*(?:--|-|–)\s*(\d+)$", c)
        if m: out += range(int(m[1]), int(m[2]) + 1)
        elif c.isdigit(): out.append(int(c))
    return out

def main():
    path = Path(sys.argv[1]); want_title = sys.argv[2] if len(sys.argv) > 2 else None
    tex = path.read_text(encoding="utf-8"); errs, warns = [], []
    m = re.match(r"a2_(\d+-\d+)_TE\.tex$", path.name)
    if not m: errs.append("filename must be a2_<topic>-<lesson>_TE.tex")
    code = m[1] if m else "?"
    body = re.sub(r"(?<!\\)%.*", "", tex)
    # preamble
    for line in ["\\newenvironment{lesson-meta}{}{}", "\\newenvironment{item-analysis}{}{}",
                 "\\newenvironment{model-discuss}{}{}", "\\newenvironment{concept-box}{}{}",
                 "\\newenvironment{concept-summary}{}{}", "\\newenvironment{example}[1]{}{}",
                 "\\newenvironment{tryit}[1]{}{}", "\\newenvironment{practice}[2]{}{}",
                 "\\newenvironment{te-addendum}[2]{}{}", "\\newcommand{\\answer}[1]{}",
                 "\\newcommand{\\placeholder}[2]{}", "\\newcommand{\\uncertain}[2]{#1}",
                 "\\newcommand{\\te}[1]{}"]:
        if line not in tex: errs.append(f"preamble missing: {line}")
    if "\\end{document}" not in tex: errs.append("missing \\end{document}")
    # begin/end balance per environment
    for env in ["lesson-meta", "item-analysis", "model-discuss", "concept-box", "concept-summary",
                "example", "tryit", "practice", "te-addendum", "tabular", "tikzpicture", "axis"]:
        b = len(re.findall(r"\\begin\{%s\}" % env, body)); e = len(re.findall(r"\\end\{%s\}" % env, body))
        if b != e: errs.append(f"\\begin{{{env}}} x{b} vs \\end{{{env}}} x{e}")
    # no nesting of the item-level environments inside each other
    stack = []
    for t in re.finditer(r"\\(begin|end)\{(example|tryit|practice|te-addendum|concept-summary|concept-box|model-discuss)\}", body):
        if t[1] == "begin":
            if stack: errs.append(f"{t[2]} opened inside {stack[-1]} (line {body[:t.start()].count(chr(10))+1})")
            stack.append(t[2])
        elif stack: stack.pop()
    # brace balance
    depth = 0
    for i, ch in enumerate(body):
        if ch == "{" and body[i-1:i] != "\\": depth += 1
        elif ch == "}" and body[i-1:i] != "\\": depth -= 1
        if depth < 0: errs.append(f"unbalanced }} near line {body[:i].count(chr(10))+1}"); break
    if depth > 0: errs.append(f"{depth} unclosed {{ in file")
    # lesson-meta explicit keys
    meta = re.search(r"\\begin\{lesson-meta\}(.*?)\\end\{lesson-meta\}", body, re.S)
    if not meta: errs.append("no lesson-meta block")
    else:
        mb = meta[1]
        for key in ["lesson", "title", "objective", "essential question", "standards"]:
            if not re.search(r"(?:^|\n)\s*%s\s*:" % key, mb, re.I): errs.append(f"lesson-meta missing '{key}:' line")
        lm = re.search(r"(?:^|\n)\s*lesson\s*:\s*(\S+)", mb, re.I)
        if lm and lm[1] != code: errs.append(f"lesson: {lm[1]} does not match filename {code}")
        tm = re.search(r"(?:^|\n)\s*title\s*:\s*([^\n]+)", mb, re.I)
        if want_title and tm and tm[1].strip().lower() != want_title.lower():
            warns.append(f"title '{tm[1].strip()}' differs from expected '{want_title}'")
        for key in ["objective", "essential question"]:
            km = re.search(r"(?:^|\n)\s*%s\s*:(.*?)(\n\n|$)" % key, mb, re.I | re.S)
            if km and "\n" in km[1].strip(): errs.append(f"'{key}:' must be one line followed by a blank line")
    # item analysis
    ia = re.search(r"\\begin\{item-analysis\}(.*?)\\end\{item-analysis\}", body, re.S)
    table = {}
    if not ia: errs.append("no item-analysis block")
    else:
        for row in re.split(r"\\\\\s*", ia[1]):
            row = re.sub(r"\\(?:hline|toprule|midrule|bottomrule|begin\{tabular\}\{[^}]*\}|end\{tabular\})", "", row)
            cells = [c.strip() for c in row.split("&")]
            if len(cells) == 3 and cells[0].isdigit() and cells[2] in "1234" and cells[2]:
                for n in expand(cells[1]):
                    if n in table: errs.append(f"item {n} listed twice in item-analysis")
                    table[n] = (int(cells[0]), int(cells[2]))
        if not table: errs.append("item-analysis parsed to zero rows (rows must end with \\\\, cells split by &)")
    # examples / try its
    ex = sorted(int(n) for n in re.findall(r"\\begin\{example\}\{(\d+)\}", body))
    ti = sorted(int(n) for n in re.findall(r"\\begin\{tryit\}\{(\d+)\}", body))
    if ex != list(range(1, len(ex) + 1)): errs.append(f"examples not numbered 1..n: {ex}")
    if ti != ex: warns.append(f"try-its {ti} vs examples {ex} (fine only if the TE really lacks a Try It)")
    if table and ex and max(e for e, _ in table.values()) > max(ex): errs.append("item-analysis names an example that was not transcribed")
    # practice
    pr = [(int(a), int(b)) for a, b in re.findall(r"\\begin\{practice\}\{(\d+)\}\{(\d)\}", body)]
    nums = [n for n, _ in pr]
    if len(nums) != len(set(nums)): errs.append("duplicate practice numbers")
    if nums and nums != sorted(nums): warns.append("practice items out of order")
    if nums:
        gaps = sorted(set(range(min(nums), max(nums) + 1)) - set(nums))
        if gaps: errs.append(f"practice numbers missing: {gaps}")
    for n, d in pr:
        if n in table and table[n][1] != d: errs.append(f"practice {n} DOK {d} but item-analysis says {table[n][1]}")
    missing = sorted(set(table) - set(nums))
    if missing: errs.append(f"item-analysis items with no practice block: {missing}")
    unmapped = sorted(set(nums) - set(table))
    if unmapped: warns.append(f"practice items not in item-analysis (ok for Assessment Practice/PT if the TE omits them): {unmapped}")
    # answers
    for env, args in [("example", 1), ("tryit", 1), ("practice", 2)]:
        for mm in re.finditer(r"\\begin\{%s\}((?:\{[^{}]*\}){%d})(.*?)\\end\{%s\}" % (env, args, env), body, re.S):
            if "\\answer{" not in mm[2]: errs.append(f"{env}{mm[1]} has no \\answer")
    if "\\begin{model-discuss}" not in body: warns.append("no model-discuss (Explore & Reason) block")
    if "\\begin{concept-summary}" not in body: warns.append("no concept-summary block")
    if "Lesson Quiz" not in body and "LESSON QUIZ" not in body: warns.append("lesson quiz not transcribed")
    if re.search(r"\\\(|\\\)|\\\[|\\\]|\$", body): warns.append("uses \\( \\) \\[ \\] or $ -- house style is bare parentheses (f(x)=x^2)")
    counts = dict(examples=len(ex), tryits=len(ti), practice=len(pr),
                  addenda=len(re.findall(r"\\begin\{te-addendum\}", body)),
                  placeholders=len(re.findall(r"\\placeholder\{", body)),
                  uncertain=len(re.findall(r"\\uncertain\{", body)), dok_rows=len(table))
    print(("PASS" if not errs else "FAIL") + f" {path.name} " + " ".join(f"{k}={v}" for k, v in counts.items()))
    for e in errs: print("  ERROR", e)
    for w in warns: print("  WARN ", w)
    sys.exit(1 if errs else 0)

main()
