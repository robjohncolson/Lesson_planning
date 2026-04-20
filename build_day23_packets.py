"""Generate Combined Day 2-3 materials \u2014 Savvas-only multiplicity practice day.

Design: folds old Day 2 (Graphing from Factored Form) + old Day 3 (Multiplicity)
into ONE period.  Pure Savvas content throughout \u2014 every student-facing work
item traces to a Savvas Practice number, Try It, or Lesson Quiz item in the bank.

Savvas's editorial choice is that multiplicity is a DOK 1\u20132 procedural skill;
DOK 3 lives in Example 4 modeling applications (Practice #25, #27, #30).  So
Combined Day 2-3 is honestly a DOK 1\u20132 practice day.  No fabricated tasks.
The DOK 3 capstone moves to Combined Day 4-5 (Savvas Practice #27 storage box).

Phases (55 min, fits 55-min Tue A; 65-min F gets slack for Practice #14/#15/#16):
  0\u20135    Do Now A : LQ q4 \u2014 zeros + multiplicities from graph         [DOK 1]
  5\u20137    Do Now B : Blooket login                                       [\u2014]
  7\u201314   Do Now C : Blooket rule recall                                 [DOK 1]
  14\u201326  Launch    : Savvas Example 2 \u2014 name multiplicity               [DOK 2]
  26\u201346  Practice  : Try It 2a, 2b + Savvas #14/#15/#16 (choose 3)      [DOK 2]
  46\u201350  Share/Sum : Synthesis + self-rating                            [DOK 2]
  50\u201355  Exit      : LQ q5 \u2014 zeros + behavior                          [DOK 2]
"""
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.table import WD_ALIGN_VERTICAL

import qb
import packet_styles as ps

TABLE_STYLE = "Table Grid"

# Every work item on this packet routes through the bank.
DO_NOW_ID   = "3-5-lq-q4"
PRACTICE_IDS = ["3-5-tryit-2a", "3-5-tryit-2b",
                "3-5-savvas-q14", "3-5-savvas-q15", "3-5-savvas-q16"]
EXIT_ID     = "3-5-lq-q5"

OBJECTIVES = [
    ("Math Objective",
     "Identify the zeros of a polynomial function from factored form, "
     "determine the multiplicity of each zero, and use multiplicity to "
     "predict whether the graph crosses, touches, or flattens through "
     "the x-axis."),
    ("Language Objective",
     "Students will use the frame \u201cThe multiplicity is ___, so the "
     "graph ___ at x = ___\u201d to justify graph behavior."),
    ("Essential Understanding",
     "The zeros of a polynomial function can be determined using factoring. "
     "A repeated factor creates a zero of higher multiplicity. Even "
     "multiplicity causes the graph to touch and turn; odd multiplicity "
     "causes it to cross."),
]

FRAMEWORK_HEADER = [
    ("Topic Goals",
     "Students factor a polynomial, read multiplicity from the factored "
     "form, and predict graph behavior at each zero before verifying in Desmos."),
    ("Essential Question",
     "How does the factored form of a polynomial tell you everything you "
     "need to sketch its graph \u2014 zeros AND behavior at each zero?"),
    ("Materials",
     "Student laptops with Desmos; pencils; Blooket access. No chart paper."),
]


def set_cell(cell, lines, bold_first=False):
    if isinstance(lines, str):
        lines = [lines]
    cell.text = ""
    for i, line in enumerate(lines):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        run = p.add_run(line)
        if i == 0 and bold_first:
            run.bold = True
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP


def add_two_col(doc, rows):
    t = doc.add_table(rows=len(rows), cols=2)
    t.style = TABLE_STYLE
    t.columns[0].width = Inches(1.8)
    t.columns[1].width = Inches(4.7)
    for i, (label, content) in enumerate(rows):
        set_cell(t.rows[i].cells[0], label, bold_first=True)
        if isinstance(content, str):
            content = [content]
        set_cell(t.rows[i].cells[1], content)
    doc.add_paragraph()


def add_callout(doc, title, lines):
    t = doc.add_table(rows=1, cols=1)
    t.style = TABLE_STYLE
    cell = t.rows[0].cells[0]
    cell.text = ""
    p = cell.paragraphs[0]
    p.add_run(title).bold = True
    for line in lines:
        cell.add_paragraph(line)
    doc.add_paragraph()


def header_line(doc, text, size=14, bold=True):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)


def blank_lines(doc, n=1):
    for _ in range(n):
        p = doc.add_paragraph()
        p.add_run("______________________________________________________________")


# ----------------------------------------------------------------------
# Bank-prompt formatter \u2014 clean ASCII \u2192 unicode superscripts + \u2212.
# Repairs cp1252-mojibake in rationales inherited from earlier ingests.
# ----------------------------------------------------------------------

def _format_unicode(prompt: str) -> str:
    prompt = (prompt
              .replace("\u00e2\u2020\u2019", "\u2192")
              .replace("\u00e2\u20ac\u201d", "\u2014")
              .replace("\u00e2\u20ac\u201c", "\u2013"))
    SUPS = {"2": "\u00b2", "3": "\u00b3", "4": "\u2074",
            "5": "\u2075", "6": "\u2076"}
    out, i = [], 0
    while i < len(prompt):
        ch = prompt[i]
        if ch == "^" and i + 1 < len(prompt) and prompt[i+1] in SUPS:
            out.append(SUPS[prompt[i+1]])
            i += 2
            continue
        out.append("\u2212" if ch == "-" else ch)
        i += 1
    return "".join(out)


def _strip_stem(prompt: str) -> str:
    """Return just the polynomial or problem content from a bank prompt."""
    txt = _format_unicode(prompt)
    if ":" in txt:
        txt = txt.split(":", 1)[-1].strip()
    return txt.rstrip(".")


# ----------------------------------------------------------------------
# Student packet
# ----------------------------------------------------------------------

def _practice_lines() -> list[str]:
    items = qb.get_for_packet(PRACTICE_IDS)
    lines = [
        "For each polynomial: list the zeros, the multiplicity of each, and "
        "describe the behavior of the graph at each zero (cross / touch / "
        "flatten-through).  Teacher circulates with sentence-frame prompts.",
        "",
    ]
    labels = ["A.", "B.", "C.", "D.", "E."]
    for label, q in zip(labels, items):
        src_tag = ""
        for t in q.get("tags", []):
            if t in ("try-it", "savvas-practice", "lesson-quiz"):
                src_tag = t
                break
        lines.append(f"{label}  {_strip_stem(q['prompt'])}")
        lines.append("    Zeros & multiplicities:  ____________________________________")
        lines.append("    Behavior at each:        ____________________________________")
        lines.append("")
    lines.append("Every item above is Savvas-anchored.  Bank IDs: " +
                 ", ".join(PRACTICE_IDS) + ".")
    return lines


def _do_now_lines() -> list[str]:
    q = qb.get_for_packet([DO_NOW_ID])[0]
    return [
        _format_unicode(q["prompt"]),
        "",
        "Graph is reproduced on the Do Now sheet.",
        "",
        f"(Savvas Lesson Quiz, item " + DO_NOW_ID.rsplit("-", 1)[-1].upper() + ".)",
        "",
        "Zeros:  _____________________________________________________",
        "",
        "Multiplicities:  ____________________________________________",
        "",
        "Behavior of the graph at each zero:",
        "____________________________________________________________",
        "____________________________________________________________",
    ]


def _exit_lines() -> list[str]:
    q = qb.get_for_packet([EXIT_ID])[0]
    return [
        "Savvas Lesson Quiz " + EXIT_ID.rsplit("-", 1)[-1].upper() + ":",
        _format_unicode(q["prompt"]),
        "",
        "Zeros:  _____________________________________________________",
        "",
        "Behavior at each zero:",
        "____________________________________________________________",
        "____________________________________________________________",
        "____________________________________________________________",
    ]


SHARE_SUMMARY_STUDENT = [
    "Self-check  \u2014  circle one for each:",
    "1.  I can read the multiplicity of each zero from the factored form.  \u2713    partly    not yet",
    "2.  I can predict cross vs. touch from the multiplicity.              \u2713    partly    not yet",
    "3.  I can factor a polynomial in standard form before using the rule.  \u2713    partly    not yet",
    "",
    "Preview Day 4-5:  real + complex zeros + modeling with volume (Savvas Practice #27 storage box).",
]


# ----------------------------------------------------------------------
# DO NOW SHEET
# ----------------------------------------------------------------------

def build_do_now(path):
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.7)
        sec.bottom_margin = Inches(0.7)
        sec.left_margin = Inches(0.9)
        sec.right_margin = Inches(0.9)

    header_line(doc, "ALGEBRA 2  |  LESSON 3-5", size=14)
    header_line(doc, "Combined Day 2-3  |  DO NOW  \u2014  Zeros + Multiplicities", size=13)

    p = doc.add_paragraph()
    r = p.add_run("Name: _____________________________________     Date: _____________")
    r.font.size = Pt(11)
    doc.add_paragraph()

    add_callout(doc, "\u270d\ufe0f  5 minutes. Silent. Pencil only. No Desmos.", [
        "Use the graph shown on the board (Savvas Lesson Quiz Q4).",
        "Find each zero and its multiplicity, and describe what the graph "
        "does at each zero.",
    ])

    q = qb.get_for_packet([DO_NOW_ID])[0]
    header_line(doc, "Savvas Lesson Quiz Q4:", size=12)
    p = doc.add_paragraph()
    p.add_run(_format_unicode(q["prompt"])).italic = True
    doc.add_paragraph()

    header_line(doc, "Zeros and their multiplicities:", size=12)
    blank_lines(doc, 3)
    doc.add_paragraph()

    header_line(doc, "Behavior at each zero:", size=12)
    blank_lines(doc, 3)

    doc.save(path)


# ----------------------------------------------------------------------
# STUDENT PACKET
# ----------------------------------------------------------------------

LAUNCH_INVESTIGATION = [
    "SAVVAS EXAMPLE 2 \u2014 Multiplicity",
    "",
    "In Desmos, graph both functions side by side:",
    "",
    "    (1)  y = (x + 2)\u00b2 (x \u2212 1)",
    "    (2)  y = (x + 2)\u00b3 (x \u2212 1)",
    "",
    "For each graph, look carefully at what happens at  x = \u22122:",
    "",
    "    Graph (1):  At x = \u22122 the graph _______________________________________",
    "    Graph (2):  At x = \u22122 the graph _______________________________________",
    "",
    "What stays the same between the two?",
    "_______________________________________________________________",
    "_______________________________________________________________",
    "",
    "THE WORD:  the number of times a factor appears in the factored form is "
    "called its  MULTIPLICITY.",
    "    (x + 2)\u00b2 has multiplicity 2 at x = \u22122.  (x + 2)\u00b3 has multiplicity 3 at x = \u22122.",
    "",
    "T-CHART  \u2014  fill in after the investigation:",
    "   ODD multiplicity (1, 3, 5\u2026)         |   EVEN multiplicity (2, 4, 6\u2026)",
    "   Behavior at the zero:                |   Behavior at the zero:",
    "   ____________________________         |   ____________________________",
    "   ____________________________         |   ____________________________",
    "",
    "Sentence frame:  \u201cThe multiplicity is ___, so the graph ___ at x = ___.\u201d",
]


def build_student(path):
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.6)
        sec.bottom_margin = Inches(0.6)
        sec.left_margin = Inches(0.7)
        sec.right_margin = Inches(0.7)

    ps.running_header_name_block(doc)
    header_line(doc, "ALGEBRA 2  |  LESSON 3-5", size=14)
    ps.day_banner(doc, "2-3", "Zeros + Multiplicity (Savvas-anchored)",
                  "Read multiplicity from factored form; predict graph "
                  "behavior at every zero. All work items come from Savvas.")

    add_two_col(doc, OBJECTIVES)
    add_two_col(doc, FRAMEWORK_HEADER)

    add_callout(doc, "\U0001F4C4  DO NOW  \u2014  separate sheet", [
        "You got the Zeros + Multiplicities sheet on entry (Savvas Lesson Quiz Q4).",
        "Hold onto it \u2014 we\u2019ll return to it during the Launch.",
    ])

    add_callout(doc, "\U0001F3AE  Blooket  \u2014  Rule Recall   [Do Now B+C]  [DOK 1]   (2 + 7 min)", [
        "Pure rule recall: ZPP, multiplicity = exponent, EVEN \u2192 touch, "
        "ODD \u2192 cross, highest-power \u2192 end behavior.  No procedural "
        "factoring items (that\u2019s practice work, not flashcards).",
    ])

    add_two_col(doc, [(
        "\U0001F4A1  Launch  \u2014  Name the Pattern (Savvas Example 2)   [Launch]  [DOK 2]   (12 min)",
        LAUNCH_INVESTIGATION,
    )])

    add_two_col(doc, [(
        "\u270F\uFE0F  Practice  \u2014  Savvas Try Its + Practice Items   [Practice]  [DOK 2]   (20 min)",
        _practice_lines(),
    )])

    add_callout(doc,
        "\U0001F501  SHARE / SUMMARY   [Share/Summary]  [DOK 2]   (4 min)",
        SHARE_SUMMARY_STUDENT)

    ps.summary_exit_box(doc,
        "\U0001F4E4  EXIT TICKET   [Exit Ticket]  [DOK 2]   (5 min)",
        _exit_lines())

    doc.save(path)


# ----------------------------------------------------------------------
# TEACHER PACKET
# ----------------------------------------------------------------------

CRITERIA_FOR_SUCCESS = [
    "Student-facing, revisited during Share/Summary:",
    "1.  I can read the multiplicity of each zero from the factored form.",
    "2.  I can predict cross vs. touch from the multiplicity.",
    "3.  I can factor a polynomial in standard form before using the rule.",
    "Formative evidence:",
    "\u2022  Do Now sheets (Savvas LQ Q4 \u2014 zeros + multiplicities from graph).",
    "\u2022  Blooket dashboard (DOK 1 rule recall).",
    "\u2022  Practice page (Try It 2a, 2b + Savvas Practice #14/#15/#16).",
    "\u2022  Exit ticket (Savvas LQ Q5 \u2014 zeros + behavior).",
]

BLOOKET_SCOPE = [
    "SCOPE (pure rule-recall, DOK 1).  Multiplicity rules + ZPP retention.",
    "Rules today\u2019s work depends on:",
    "\u2022  Zero Product Property: zero \u21d4 factor = 0.",
    "\u2022  Sign direction: zero at x = c gives factor (x \u2212 c).",
    "\u2022  Multiplicity = exponent on the factor.",
    "\u2022  EVEN multiplicity \u2192 TOUCH and turn.",
    "\u2022  ODD multiplicity \u2192 CROSS.",
    "\u2022  Highest power \u2192 end behavior (even \u2192 same direction; odd \u2192 opposite).",
    "NO procedural factoring items.  Dashboard diagnostic: note the two "
    "lowest items; 60-second board reset if a rule is cold.",
    "CSV: Blooket_Day3_Multiplicity.csv  (regenerate via regen_blooket_csvs.py).",
    "Questions to ask (after game): \u201cWhich rule had the lowest %?  Say it now.\u201d",
    "Adult role: teacher watches dashboard + runs board reset; aide "
    "troubleshoots Chromebook issues during login.",
]

LAUNCH_KEY = [
    "Savvas Example 2 target observations at x = \u22122:",
    "    (x + 2)\u00b2 (x \u2212 1)  \u2192  graph TOUCHES and turns at x = \u22122.",
    "    (x + 2)\u00b3 (x \u2212 1)  \u2192  graph CROSSES (flattens) at x = \u22122.",
    "Pattern: EVEN \u2192 touch/turn; ODD \u2192 cross; higher multiplicity \u2192 "
    "flatter at the zero.",
    "T-chart fill:",
    "  ODD: graph crosses the x-axis (1 = clean cross; 3, 5 = flatten-through).",
    "  EVEN: graph touches and turns (sign of f doesn\u2019t change at the zero).",
    "TEACHER MOVE \u2014 the naming:",
    "After Graph (1) is drawn, pause: \u201cWhat\u2019s the exponent on (x + 2)?  "
    "What\u2019s happening at x = \u22122?\u201d  Then: \u201cThe word for how many times "
    "a factor appears is MULTIPLICITY.\u201d  Write on board.  Continue with Graph (2).",
    "Questions to ask: \u201cWhat\u2019s the exponent on (x + 2) in each graph?\u201d / "
    "\u201cWhat\u2019s the same between the two graphs?  What\u2019s different?\u201d / "
    "\u201cWho predicted touch on the Do Now?  What made you predict that?\u201d",
    "Adult role: teacher runs script + cold-calls; aide walks to partners "
    "stuck loading Desmos.",
]


def _practice_key_lines() -> list[str]:
    items = qb.get_for_packet(PRACTICE_IDS)
    lines = []
    labels = ["A.", "B.", "C.", "D.", "E."]
    for label, q in zip(labels, items):
        lines.append(f"{label}  {_strip_stem(q['prompt'])}  [bank: {q['id']}, DOK {q.get('dok')}]")
        correct = _format_unicode(str(q.get("correct", "")))
        lines.append(f"    \u2705  {correct}")
        rationale = q.get("dok_rationale")
        if rationale:
            lines.append(f"    DOK rationale: {_format_unicode(rationale)}")
        lines.append("")
    lines.append("Questions to ask (circulating): \u201cWhich factor tells you the "
                 "behavior at this zero?\u201d / \u201cIs this multiplicity even or odd?\u201d")
    lines.append("Adult role: teacher circulates with prompts; aide scans for "
                 "students stuck on irreducible quadratics (Item B) and redirects "
                 "to the rule that x\u00b2 + positive has no real zero.")
    lines.append("Pacing: students complete A, B, and ONE of C/D/E (choice).  "
                 "65-min F period can complete all five.")
    return lines


def _exit_key_lines() -> list[str]:
    q = qb.get_for_packet([EXIT_ID])[0]
    return [
        f"[bank: {q['id']}, DOK {q.get('dok')}]",
        _format_unicode(q["prompt"]),
        "",
        f"\u2705  {_format_unicode(str(q.get('correct', '')))}",
        "",
        "DOK rationale: " + _format_unicode(str(q.get("dok_rationale", ""))),
        "",
        "Questions to ask: none during write time.  As papers come up: "
        "\u201cBiggest thing you learned?  Say it in one breath.\u201d",
        "Adult role: teacher collects at door; aide totals responses for "
        "Day 4-5 warm-up diagnostic.",
    ]


def _do_now_key_lines() -> list[str]:
    q = qb.get_for_packet([DO_NOW_ID])[0]
    return [
        f"[bank: {q['id']}, DOK {q.get('dok')}]",
        _format_unicode(q["prompt"]),
        "",
        f"\u2705  {_format_unicode(str(q.get('correct', '')))}",
        "",
        "DOK rationale: " + _format_unicode(str(q.get("dok_rationale", ""))),
        "",
        "DIAGNOSTIC scan as students hand sheets in:",
        "\u2022  Students who wrote only the zeros (no multiplicities) missed the "
        "repeated-factor cue \u2014 cold-call them in Launch.",
        "\u2022  Students who correctly identified multiplicity from the graph "
        "behavior are ahead \u2014 have them peer-teach during Practice.",
        "Questions to ask (circulating silently): none aloud. Scan only.",
        "Adult role: teacher hands sheets at door, circulates silently; aide "
        "supports processing-speed accommodations without prompting content.",
    ]


IEP_MODS = [
    "\u2022  Do Now uses a Savvas-printed graph (low reading load).",
    "\u2022  Launch is a Savvas side-by-side comparison \u2014 visual, no standard-form factoring.",
    "\u2022  Practice is structured per-item (zeros + mult + behavior on three lines).",
    "\u2022  Choice in Practice: A + B required, C/D/E pick-one.  Reduces overwhelm.",
    "\u2022  Exit ticket structure mirrors Do Now structure.",
]

ELL_SUPPORTS = [
    "\u2022  Sentence frame printed on Launch T-chart: \u201cThe multiplicity is ___, "
    "so the graph ___ at x = ___.\u201d",
    "\u2022  \u201cTouches / kisses / turns / bounces\u201d all accepted for even multiplicity.",
    "\u2022  \u201cCrosses / goes through / cuts through\u201d all accepted for odd multiplicity.",
    "\u2022  ONE new academic word today: MULTIPLICITY.  No other new vocab.",
    "\u2022  Predict-before-verify routine: students commit in writing before speaking.",
]


def build_teacher(path):
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.6)
        sec.bottom_margin = Inches(0.6)
        sec.left_margin = Inches(0.7)
        sec.right_margin = Inches(0.7)

    header_line(doc, "TEACHER EDITION", size=12)
    header_line(doc, "ALGEBRA 2  |  LESSON 3-5", size=14)
    ps.day_banner(doc, "2-3", "Zeros + Multiplicity (Savvas-anchored)",
                  "Teacher pacing + DOK framework crosswalk + answer "
                  "keys + Questions to ask / Adult role per phase.")

    add_two_col(doc, OBJECTIVES + [("CCSS", "F-IF.C.7c, A-APR.B.3, MP.3, MP.7")])
    add_two_col(doc, FRAMEWORK_HEADER)

    add_callout(doc, "\U0001F4CB  DESIGN \u2014  SAVVAS-ONLY PRACTICE DAY (no DOK 3)", [
        "Do Now \u2192 Launch (name multiplicity) \u2192 Practice (apply) \u2192 Share/Summary \u2192 Exit.",
        "[DOK 1] Blooket rule recall; Do Now Q4 (graph-read); Try It 2a/2b.",
        "[DOK 2] Launch investigation; Practice #14/#15/#16; Share/Summary; Exit Q5.",
        "[DOK 3] NOT on this day.  Savvas's editorial choice: DOK-3 in this "
        "lesson is modeling-only (Practice #25 firework, #27 storage box, "
        "#30 Venetta).  The DOK-3 capstone lands on Combined Day 4-5 via "
        "Practice #27.",
        "This design honors the \u201call work from Savvas\u201d rule: every work "
        "item on the student packet traces to a bank ID.  No fabricated tasks.",
    ])

    add_callout(doc, "\u2705  CRITERIA FOR SUCCESS  /  FORMATIVE ASSESSMENT", CRITERIA_FOR_SUCCESS)

    add_callout(doc, "\u23f1\ufe0f  REALISTIC PACING", [
        "Total: 55 min.  Fits 55-min Tue A on the nose; 65-min F has 10 min slack.",
        "  Do Now A (solo paper, LQ Q4) .... 5 min",
        "  Do Now B (Blooket login) ....... 2 min",
        "  Do Now C (Blooket game) ........ 7 min",
        "  Launch (Savvas Example 2) ..... 12 min",
        "  Practice (A, B + 1 of C/D/E) .. 20 min",
        "  Share/Summary ................... 4 min",
        "  Exit (LQ Q5) .................... 5 min",
        "RELEASE VALVES (ordered):",
        "  1. Cut Practice to A + B only (save 8 min for stuck pairs).",
        "  2. Cut Launch from 12 \u2192 10 min (skip the extended Desmos compare).",
        "  3. Cut Share/Summary to 3 min.",
        "  NEVER cut Exit.  Only artifact that documents learning.",
        "65-min F uses slack for: all five Practice items, deeper Launch "
        "compare with (x + 2)\u2074 (x \u2212 1), extended Share/Summary self-rating.",
    ])

    add_callout(doc, "[Do Now A]  [DOK 1] Savvas Lesson Quiz Q4 \u2014 Zeros + Multiplicities  (5 min)", [
        "Students receive the Do Now sheet with the Savvas LQ Q4 prompt + "
        "graph on entry. Silent, 5 min, pencil only.",
    ])
    add_callout(doc, "\u2705  DO NOW / ANSWER KEY", _do_now_key_lines())

    add_callout(doc, "[Do Now B+C]  [DOK 1] Blooket \u2014 Rule Recall ONLY", BLOOKET_SCOPE)

    add_callout(doc, "[Launch]  [DOK 2] Savvas Example 2 \u2014 Name Multiplicity  (12 min)", [
        "Savvas Example 2 (pg. 151): compare y = (x + 2)\u00b2 (x \u2212 1) vs y = (x + 2)\u00b3 (x \u2212 1).",
        "Script:",
        "1.  \u201cPull out your Do Now.\u201d  Cold-call: \u201cWhat did you see "
        "at the repeated-factor zero?\u201d (15s + 60s)",
        "2.  Partners graph both in Desmos, record behavior at x = \u22122. (5 min)",
        "3.  Class share \u2192 name MULTIPLICITY.  Write definition + example on board. (3 min)",
        "4.  Fill T-chart together (ODD vs EVEN). (3 min)",
    ])
    add_callout(doc, "\u2705  LAUNCH / ANSWER KEY", LAUNCH_KEY)

    add_callout(doc, "[Practice]  [DOK 2] Savvas Try Its + Practice  (20 min)", [
        "Five Savvas-anchored items (bank IDs: " + ", ".join(PRACTICE_IDS) + ").",
        "Students complete A + B required, plus ONE of C/D/E (choice).",
        "Teacher circulates with sentence-frame prompts, not corrections.",
        "Fast finishers: complete all five, or try the  \u201cbuild a polynomial "
        "with these behaviors\u201d board challenge.",
    ])
    add_callout(doc, "\u270F\uFE0F  PRACTICE / ANSWER KEY", _practice_key_lines())

    add_callout(doc, "[Share/Summary]  [DOK 2] Synthesis + Self-Rating  (4 min)", [
        "Teacher script (4 min flat):",
        "1.  Essential Question callback (45s): \u201cHow does factored form "
        "tell you everything you need to sketch?\u201d",
        "2.  Language Objective check (30s): \u201cWho used \u2018the multiplicity "
        "is ___, so the graph ___\u2019?\u201d",
        "3.  Self-rating circle (60s).  Teacher scans.",
        "4.  Preview Day 4-5 (30s): \u201cTomorrow \u2014 complex zeros + "
        "modeling.  Savvas storage-box volume problem.\u201d",
        "5.  Transition (30s): \u201cExit ticket.  LQ Q5.  5 minutes.\u201d",
        "Questions to ask: \u201cWhich Criterion for Success did you rate "
        "\u2018partly\u2019?  What\u2019s the blocker?\u201d",
        "Adult role: teacher leads; aide scans self-ratings as packets tilt up.",
    ])
    add_callout(doc,
        "\U0001F501  SHARE / SUMMARY (student-facing)",
        SHARE_SUMMARY_STUDENT)

    add_callout(doc, "[Exit Ticket]  [DOK 2] Savvas Lesson Quiz Q5  (5 min)", [
        "Savvas LQ Q5: Find the zeros of f(x) = \u2212x\u00b3 \u2212 2x\u00b2 + "
        "7x \u2212 4. Then describe the behavior of the graph at each zero.",
        "Full credit = zeros correct AND behavior description using "
        "multiplicity language (\u201ccrosses\u201d / \u201ctouches\u201d / \u201cturns\u201d).",
    ])
    ps.summary_exit_box(doc,
        "\U0001F4E4  EXIT TICKET (student-facing)",
        _exit_lines())
    add_callout(doc, "\u2705  EXIT TICKET / ANSWER KEY", _exit_key_lines())

    add_callout(doc, "\U0001F4F7  WHAT TO COLLECT", [
        "1.  Do Now sheets (LQ Q4).",
        "2.  Practice pages (photograph or collect \u2014 formative evidence).",
        "3.  Exit tickets (LQ Q5, every student).",
        "4.  Share/Summary self-ratings.",
    ])
    add_callout(doc, "\U0001F9E9  MODIFICATIONS / SUPPORT FOR IEP STUDENTS", IEP_MODS)
    add_callout(doc, "\U0001F30D  SUPPORTS FOR ELL STUDENTS", ELL_SUPPORTS)

    doc.save(path)


if __name__ == "__main__":
    build_do_now("Day_23_Do_Now.docx")
    build_student("Day_23_Student_Packet.docx")
    build_teacher("Day_23_Teacher_Packet.docx")
    print("Built Day_23_Do_Now.docx, Day_23_Student_Packet.docx, Day_23_Teacher_Packet.docx")
