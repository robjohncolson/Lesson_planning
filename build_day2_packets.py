"""Generate Day 2 materials: separate Do Now sheet + Student Packet + Teacher Packet.

Day 2 = Graphing from Factored Form (post-spring-break Monday, 60-min usable).

The Do Now is a SEPARATE sheet handed to students as they walk in. Early
arrivers work silently on the Sign Flip prediction while the library-charger
students return. When all are back, Blooket runs (still Do Now). Main packet
(Launch -> Exit) is handed out after Blooket.

Phases (total 60 min, library-trip adjusted):
  0\u20135    Do Now A : Solo paper Sign Flip prediction          [DOK 2]
  5\u20137    Do Now B : Blooket login                             [\u2014]
  7\u201314   Do Now C : Blooket game                              [DOK 1]
  14\u201320  Launch    : Sign Flip synthesis + Desmos verify       [DOK 2]
  20\u201335  Explore   : Practice #13 discovery                    [DOK 2-3]
  35\u201350  Explore   : Reverse engineering                       [DOK 3]
  50\u201355  Share/Sum : Synthesis + self-reflection               [DOK 2]
  55\u201360  Exit      : CER (Savvas Practice #6)                  [DOK 2]

Practice #12 cut (Blooket provides the GCF-cubic diagnostic).
"""
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.table import WD_ALIGN_VERTICAL

TABLE_STYLE = "Table Grid"

OBJECTIVES = [
    ("Math Objective",
     "Identify the zeros of a function using factoring or synthetic division. "
     "Use zeros to graph a polynomial function."),
    ("Language Objective",
     "Students will use the frame \u201cThe zeros stay the same because ___. "
     "The graph changes because ___\u201d to justify their comparison."),
    ("Essential Understanding",
     "The zeros of a polynomial function can be determined using factoring or "
     "synthetic division. The zeros can be used to sketch its graph."),
]

FRAMEWORK_HEADER = [
    ("Topic Goals",
     "Students build fluency moving between a polynomial\u2019s factored form "
     "and its graph. They work forward (zeros \u2192 sign chart \u2192 graph) "
     "and backward (zeros + a point \u2192 equation)."),
    ("Essential Question",
     "How do the zeros of a polynomial \u2014 and a single point on the graph "
     "\u2014 determine its complete equation?"),
    ("Materials",
     "Student laptops with Desmos; blank paper; pencils; Blooket access "
     "(warm-up code on the board). No chart paper, no manipulatives."),
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


# ==================================================================
# DO NOW SHEET (handed out on entry)
# ==================================================================

def build_do_now(path):
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.6)
        sec.bottom_margin = Inches(0.6)
        sec.left_margin = Inches(0.7)
        sec.right_margin = Inches(0.7)

    header_line(doc, "ALGEBRA 2  |  LESSON 3-5", size=14)
    header_line(doc, "Day 2  |  DO NOW   \u2014   Sign Flip Prediction", size=13)

    # Name + date line
    p = doc.add_paragraph()
    r = p.add_run("Name: _____________________________________        Date: _____________")
    r.font.size = Pt(11)
    doc.add_paragraph()

    add_callout(doc, "\u270d\ufe0f  INSTRUCTIONS", [
        "Work SILENTLY. Pencil only. Do NOT open Desmos yet.",
        "When you finish, flip your paper over and wait. We\u2019ll start the "
        "Blooket as soon as everyone is back.",
        "Time: 5 minutes.",
    ])

    add_callout(doc, "\U0001F504  Compare these two functions:", [
        "f(x) = x(x \u2212 4)(x + 3)",
        "g(x) = \u2212x(x \u2212 4)(x + 3)",
        "Before graphing, PREDICT:",
    ])

    add_two_col(doc, [
        ("1.  What will stay the EXACT SAME when you graph these?", [
            "_______________________________________________",
            "_______________________________________________",
            "_______________________________________________",
            "_______________________________________________",
        ]),
        ("2.  What will CHANGE? How do you know BEFORE graphing?", [
            "_______________________________________________",
            "_______________________________________________",
            "_______________________________________________",
            "_______________________________________________",
        ]),
        ("3.  Finish this sentence:", [
            "\u201cThe zeros stay the same because",
            "_______________________________________________,",
            "and the graph changes because",
            "_______________________________________________.\u201d",
        ]),
    ])

    add_callout(doc, "\u2705  HOW YOU WILL KNOW YOU\u2019RE DONE", [
        "\u2022  All three questions answered in writing.",
        "\u2022  Your sentence in #3 is a COMPLETE sentence (has a \u201cbecause\u201d).",
        "\u2022  You haven\u2019t opened Desmos or your packet yet.",
        "\u2022  You are ready to justify your prediction when called on.",
    ])

    doc.save(path)


# ==================================================================
# STUDENT PACKET (main, handed out after Blooket)
# ==================================================================

P13_STUDENT = [
    "g(x) = x\u00b3 \u2212 8x\u00b2 + 16x",
    "Step 1 \u2014 Factor on blank paper",
    "Pull out the GCF:  x(________________)",
    "Factor the quadratic inside:  = x(________)(________)",
    "Something unusual happens \u2014 look carefully.",
    "Step 2 \u2014 Zeros",
    "The zeros are: ________ and ________. Only TWO distinct zeros \u2014 why?",
    "_______________________________________________",
    "Step 3 \u2014 Graph in Desmos. Look at x = 4.",
    "What does the graph DO at x = 4? (Write one sentence in your own words.)",
    "_______________________________________________",
    "Step 4 \u2014 Sketch on blank paper",
    "Sketch g(x). Pay attention to what happens at x = 4 \u2014 you\u2019ll need "
    "this tomorrow.",
]

REVERSE_ENG_STUDENT = [
    "Write the equation of a polynomial with zeros at x = \u22122, x = 1, and "
    "x = 4 that passes through the point (0, \u22128).",
    "Step 1 \u2014 Zeros \u2192 factors",
    "If x = \u22122 is a zero, one factor is (________).",
    "If x = 1 is a zero, one factor is (________).",
    "If x = 4 is a zero, one factor is (________).",
    "So far: f(x) = a(________)(________)(________)",
    "Step 2 \u2014 Use the point (0, \u22128) to find a",
    "Substitute x = 0 and f(x) = \u22128:",
    "\u22128 = a(________)(________)(________)",
    "\u22128 = a \u00b7 ________",
    "a = ________",
    "Step 3 \u2014 Final equation",
    "f(x) = ________________________________________",
    "Step 4 \u2014 Explain to your partner (use CER format \u2014 see reference):",
    "\u2022  How did the zeros give you the factors?",
    "\u2022  How did the point (0, \u22128) give you the leading coefficient?",
]

SHARE_SUMMARY_STUDENT = [
    "Synthesis:",
    "Today the ________ of a polynomial came from its ________, and a "
    "________ on the graph told us the leading coefficient.",
    "Quick self-check \u2014 circle one for each (Criteria for Success):",
    "1.  I can factor a polynomial and find its zeros.            \u2713    partly    not yet",
    "2.  I can predict what changes when f(x) becomes \u2212f(x).      \u2713    partly    not yet",
    "3.  I can build an equation from zeros and a point.          \u2713    partly    not yet",
    "4.  I can describe what the graph does at a repeated zero.   \u2713    partly    not yet",
    "Preview: tomorrow we name the thing we saw at x = 4 in g(x).",
]

EXIT_STUDENT = [
    "Savvas Practice #6:",
    "If you use zeros to sketch the graph of a polynomial function, how can "
    "you verify that your graph is correct?",
    "Use CER format (see reference at top of packet if you need a reminder).",
    "Claim:  ____________________________________________",
    "_______________________________________________",
    "Evidence:  __________________________________________",
    "_______________________________________________",
    "_______________________________________________",
    "Reasoning:  _________________________________________",
    "_______________________________________________",
    "_______________________________________________",
]


def build_student(path):
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.6)
        sec.bottom_margin = Inches(0.6)
        sec.left_margin = Inches(0.7)
        sec.right_margin = Inches(0.7)

    header_line(doc, "ALGEBRA 2  |  LESSON 3-5", size=14)
    header_line(doc, "Day 2  |  Graphing from Factored Form", size=13)

    add_two_col(doc, OBJECTIVES)
    add_two_col(doc, FRAMEWORK_HEADER)

    add_callout(doc, "\U0001F501  WELCOME BACK \u2014 RECALL", [
        "Before break you built sign charts and sketches for three "
        "polynomials and finished with The Leap. Today we push further:",
        "\u2022  What does a negative leading coefficient do to the graph?",
        "\u2022  What happens when a zero appears twice?",
        "\u2022  Can you write an equation from scratch if you know the zeros?",
        "Materials today: laptop (Desmos), blank paper, pencil.",
    ])

    # CER reference - placed near the top so students can refer back
    add_callout(doc, "\U0001F4DD  HOW TO WRITE A CER ANSWER   (reference \u2014 use below)", [
        "CLAIM \u2014 Answer the question in ONE sentence.",
        "   Starter: \u201cYou can verify your graph by ___.\u201d",
        "EVIDENCE \u2014 Name 2\u20133 specific things to check. Use steps, examples, or numbers.",
        "   Starter: \u201cI would check ___, and then ___.\u201d",
        "REASONING \u2014 Explain WHY that evidence proves your claim. Use \u201cbecause\u201d or \u201csince.\u201d",
        "   Starter: \u201cThis works because ___.\u201d",
        "WORKED EXAMPLE (different topic):",
        "Q: How do you know two lines are parallel?",
        "CLAIM: Two lines are parallel if their slopes are equal.",
        "EVIDENCE: Calculate each line\u2019s slope using m = (y\u2082 \u2212 y\u2081) / "
        "(x\u2082 \u2212 x\u2081). If both slopes are the same number, the lines are parallel.",
        "REASONING: Slope measures the steepness of a line. Two lines with "
        "the same steepness go in the same direction, so they never meet.",
    ])

    add_callout(doc, "\U0001F4C4  DO NOW \u2014 DONE ON A SEPARATE SHEET", [
        "You received the Sign Flip Prediction sheet when you walked in.",
        "Hang onto it \u2014 we\u2019ll use your predictions during the Launch "
        "synthesis after the Blooket.",
    ])

    add_callout(doc, "\U0001F3AE  Blooket Warm-Up   [Do Now B+C]  [DOK 1]   (2 + 7 min)", [
        "Teacher displays the code on the screen. Log in (2 min).",
        "Game runs 7 minutes. Topics: finding zeros from factors, counting "
        "intervals, difference of squares, GCF + quadratic factoring, plus "
        "sign-flip primer questions.",
    ])

    add_callout(doc, "\U0001F504  Sign Flip \u2014 Class Synthesis   [Launch]  [DOK 2]   (6 min)", [
        "Pull out your DO NOW sheet.",
        "Share with your partner: what did you predict would stay the same? "
        "What did you predict would change?",
        "Class synthesis + Desmos check together.",
        "Use the frame: \u201cThe zeros stay the same because ___. The graph "
        "changes because ___.\u201d",
    ])

    add_two_col(doc, [(
        "\U0001F50D  Practice #13 \u2014 Something New at a Zero   [Explore]  [DOK 2\u20133]   (15 min)",
        P13_STUDENT,
    )])
    add_two_col(doc, [(
        "\U0001F527  Build the Equation (Reverse)   [Explore]  [DOK 3]   (15 min)",
        REVERSE_ENG_STUDENT,
    )])

    add_callout(doc,
        "\U0001F501  SHARE / SUMMARY   [Share/Summary]  [DOK 2]   (5 min)",
        SHARE_SUMMARY_STUDENT)

    add_callout(doc,
        "\U0001F4E4  EXIT TICKET \u2014 CER   [Exit Ticket]  [DOK 2]   (5 min)",
        EXIT_STUDENT)

    doc.save(path)


# ==================================================================
# TEACHER PACKET
# ==================================================================

CRITERIA_FOR_SUCCESS = [
    "Student-facing, revisited during Share/Summary:",
    "1.  I can factor a polynomial using GCF and quadratic-factoring patterns.",
    "2.  I can identify all zeros of a polynomial from factored form.",
    "3.  I can predict what happens to a graph when f(x) becomes \u2212f(x).",
    "4.  I can build a polynomial equation from given zeros and a point.",
    "5.  I can describe (in my own words) what a graph does at a repeated zero.",
    "Formative assessment evidence:",
    "\u2022  Do Now sheets \u2014 scan for written predictions as they come in.",
    "\u2022  Blooket per-student percentages (Do Now C, DOK 1).",
    "\u2022  Partner conversations during Reverse Engineering (circulating).",
    "\u2022  Reverse engineering page \u2014 collected or photographed (DOK 3).",
    "\u2022  Share/Summary self-rating (student-owned).",
    "\u2022  CER exit ticket (DOK 2, collected).",
]

SELF_REFLECTION = [
    "Completed by students during Share/Summary (5 min phase):",
    "\u2022  Rate each Criterion for Success: \u2713 / partly / not yet.",
    "\u2022  Students rating \u201cnot yet\u201d on #4 (repeated zero) are primed "
    "for Day 3 \u2014 call on them first tomorrow to describe what they saw.",
    "\u2022  Students rating \u201cnot yet\u201d on #3 (reverse engineering) "
    "need a quick conference during the next Do Now.",
]

IEP_MODS = [
    "\u2022  Chunked tasks: one step per clearly numbered step. No dense text blocks.",
    "\u2022  Desmos graphing reduces fine-motor sketch demand.",
    "\u2022  Partner pairing for Reverse Engineering: assign roles "
    "(\u201cfactor-finder\u201d and \u201cequation-checker\u201d) so students "
    "with processing-speed accommodations have a clearly scoped job.",
    "\u2022  Extended-time release valve: written CER portion of Reverse "
    "Engineering \u2192 homework if class time runs short.",
    "\u2022  Blooket answers read aloud if an individual IEP requires audio support.",
    "\u2022  Preferential seating near board for Sign Flip synthesis.",
    "\u2022  Do Now sheet is deliberately short (3 prompts) so students with "
    "slower processing can complete it in 5 minutes.",
]

ELL_SUPPORTS = [
    "\u2022  Sentence frame on Do Now sheet: \u201cThe zeros stay the same "
    "because ___, and the graph changes because ___.\u201d",
    "\u2022  Predict-before-verify routine \u2014 students commit in writing before speaking.",
    "\u2022  \u201cTouches\u201d / \u201cbounces\u201d / \u201cturns\u201d all "
    "accepted for #13 discovery today; academic term (multiplicity) deferred to Day 3.",
    "\u2022  No new vocabulary introduced today \u2014 deliberate language-load "
    "reduction after a week off.",
    "\u2022  Materials-light: no chart paper setup, no manipulatives.",
    "\u2022  Think-Pair-Share before any public share; writing before speaking.",
    "\u2022  CER reference callout at top of packet gives sentence starters + "
    "worked example on a DIFFERENT topic so CER structure is portable.",
    "\u2022  Share/Summary self-rating uses check/partly/not-yet icons \u2014 "
    "keeps cognitive load on the math, not on producing English.",
]

DO_NOW_KEY = [
    "Expected predictions (students will vary \u2014 accept well-reasoned answers):",
    "STAYS THE SAME:",
    "\u2022  Zeros at x = \u22123, x = 0, x = 4 (ZPP still applies: 0 \u00d7 anything = 0)",
    "\u2022  The three x-intercepts",
    "\u2022  Degree (still a cubic)",
    "CHANGES:",
    "\u2022  Every sign in the sign chart flips",
    "\u2022  End behavior flips (was down-left/up-right; now up-left/down-right)",
    "\u2022  The graph is a REFLECTION of f(x) over the x-axis",
    "\u2022  Leading coefficient is \u22121 instead of +1",
    "Sentence-frame examples (strong student response):",
    "\u201cThe zeros stay the same because x \u00b7 \u22121 = 0 whenever x = 0, "
    "and the graph changes because multiplying by \u22121 reflects every "
    "y-value across the x-axis.\u201d",
    "\u201cThe zeros stay the same because the Zero Product Property doesn\u2019t "
    "care about a \u22121 in front, and the graph changes because every "
    "positive becomes negative and vice versa.\u201d",
    "DIAGNOSTIC: scan Do Now sheets as students hand them to you. Students "
    "who predict \u201czeros change\u201d have a conceptual gap \u2014 "
    "address during Launch synthesis at the board with a direct ZPP check.",
]

P13_KEY = [
    "g(x) = x\u00b3 \u2212 8x\u00b2 + 16x",
    "\u2705 GCF: x(x\u00b2 \u2212 8x + 16)",
    "\u2705 Factored: x(x \u2212 4)\u00b2  \u2190  REPEATED FACTOR",
    "\u2705 Zeros: x = 0 and x = 4 (only two distinct \u2014 x = 4 appears twice)",
    "\u2705 At x = 4 in Desmos: the graph TOUCHES the x-axis and turns around.",
    "\u2705 End behavior: x\u00b3 \u2192 down left, up right.",
    "TEACHER MOVE \u2014 the discovery:",
    "Students see the touch at x = 4 and ask \u201cwhy doesn\u2019t it cross?\u201d "
    "DO NOT name multiplicity today. Say: \u201cInteresting. Describe what "
    "you see in your own words.\u201d Log the observation on the board as "
    "class curiosity. Day 3 is Multiplicity \u2014 let the mystery sit overnight.",
    "Accept: \u201ctouches,\u201d \u201cbounces,\u201d \u201cturns,\u201d "
    "\u201ckisses the axis.\u201d All fine for today.",
]

REVERSE_KEY = [
    "Target: zeros at x = \u22122, 1, 4 through (0, \u22128)",
    "\u2705 Step 1 \u2014 Factors: (x + 2), (x \u2212 1), (x \u2212 4)",
    "\u2705 Step 2 \u2014 Plug in (0, \u22128):",
    "   \u22128 = a(0 + 2)(0 \u2212 1)(0 \u2212 4) = a(2)(\u22121)(\u22124) = 8a",
    "   a = \u22121",
    "\u2705 Step 3 \u2014 Final: f(x) = \u2212(x + 2)(x \u2212 1)(x \u2212 4)",
    "\u2705 Desmos check: passes through (0, \u22128); zeros at \u22122, 1, 4; "
    "negative leading coeff flips end behavior.",
    "SAMPLE CER PARTNER JUSTIFICATION (what students should say aloud):",
    "CLAIM: \u201cThe equation is f(x) = \u2212(x + 2)(x \u2212 1)(x \u2212 4).\u201d",
    "EVIDENCE: \u201cThe zeros told me the factors: \u22122 gives (x + 2), 1 "
    "gives (x \u2212 1), 4 gives (x \u2212 4). The point (0, \u22128) told me "
    "a = \u22121 because plugging in x = 0 gave \u22128 = 8a.\u201d",
    "REASONING: \u201cThis works because the Zero Product Property guarantees "
    "the factors produce zeros, and a single point is enough to solve for "
    "the one unknown coefficient a.\u201d",
    "Release valve: if short on time, partners justify aloud in class; "
    "written CER \u2192 homework. Preserve the justification conversation.",
]

SHARE_SUMMARY_KEY = [
    "Sentence completion: The ZEROS came from its FACTORS, and a POINT on "
    "the graph told us the leading coefficient.",
    "Criteria for Success scan targets:",
    "\u2022  #1 factoring: \u2713 or partly for most. \u201cNot yet\u201d = "
    "intervention in next Do Now.",
    "\u2022  #2 sign flip: \u2713 for most (explicit Do Now + Launch content).",
    "\u2022  #3 reverse engineering: \u201cpartly\u201d acceptable today. New skill.",
    "\u2022  #4 repeated zero: expect mostly \u201cpartly\u201d or \u201cnot yet.\u201d "
    "Day 3 exists to name this.",
    "Teacher script (5 min):",
    "1.  Essential Question callback (60s).",
    "2.  Language Objective check (60s): \u201cWho used \u2018the zeros stay "
    "the same because...\u2019? What did you finish with?\u201d",
    "3.  Students circle self-ratings (90s).",
    "4.  Preview Day 3 (30s): \u201cTomorrow we name what happened at x = 4.\u201d",
    "5.  Transition (30s): packets out for CER.",
]

EXIT_KEY = [
    "Savvas Practice #6 sample answer:",
    "CLAIM: The graph can be verified by checking zeros, end behavior, and sign intervals.",
    "EVIDENCE: Substitute each suspected zero \u2014 f(x) should equal 0. "
    "Pick a test point in each interval and calculate f(test) \u2014 the "
    "sign should match above/below the x-axis. Compare to a Desmos graph.",
    "REASONING: Zeros are where the graph meets the x-axis by definition, "
    "so if sketched zeros match the factors, the x-intercepts are right. "
    "Test points confirm the shape between zeros. Desmos is a visual cross-check.",
    "Why DOK 2: applying known verification strategies. Not constructing a "
    "novel argument (that was Reverse Engineering).",
    "ELL look-for: students using \u201cbecause\u201d or \u201csince\u201d in Reasoning \u2014 the CER scaffold worked.",
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
    header_line(doc, "Day 2  |  Graphing from Factored Form", size=13)

    add_two_col(doc, OBJECTIVES + [("CCSS", "F-IF.C.7c, A-APR.B.3, MP.3")])
    add_two_col(doc, FRAMEWORK_HEADER)

    add_callout(doc, "\U0001F4CB  DOK GUIDE FOR EVALUATORS", [
        "Aligned to the school\u2019s lesson-plan framework: Do Now \u2192 "
        "Launch \u2192 Explore \u2192 Share/Summary \u2192 Exit Ticket. Every "
        "phase carries explicit [Framework] and [DOK] tags in packets + pacer + slides.",
        "[DOK 1] Blooket warm-up [Do Now C].",
        "[DOK 2] Solo paper Sign Flip prediction [Do Now A]; Sign Flip "
        "synthesis [Launch]; Share/Summary; CER exit ticket.",
        "[DOK 3] Reverse engineering [Explore]: zeros + y-intercept "
        "\u2192 equation.",
        "Exit Ticket is intentionally DOK 2. DOK 3 happens during Reverse "
        "Engineering with teacher + partner support.",
    ])

    add_callout(doc, "\u2705  CRITERIA FOR SUCCESS  /  FORMATIVE ASSESSMENT", CRITERIA_FOR_SUCCESS)
    add_callout(doc, "\U0001F9ED  SELF-REFLECTION ASSESSMENT", SELF_REFLECTION)

    add_callout(doc, "\u26a0\ufe0f  PACING NOTE \u2014 POST-SPRING-BREAK MONDAY", [
        "Hard budget: 60 minutes usable (last 5 of the block = pack up).",
        "LIBRARY-CHARGER LOGISTICS:",
        "\u2022  Some students go to the library for chargers at the bell. "
        "They take ~5 min to return.",
        "\u2022  Hand the DO NOW sheet to every student as they walk in. "
        "Early arrivers work silently at their desks while library students "
        "return. This prevents the \u201cdead air\u201d problem.",
        "\u2022  When everyone is back, display the Blooket code. Give "
        "2 minutes for login. Then run the 7-minute game.",
        "\u2022  Effective Do Now block: ~14 minutes (5 solo + 2 login + 7 game). "
        "That\u2019s over the framework\u2019s Do Now target (<10 min), but it "
        "carries legitimate DOK 2 solo work, not just recall \u2014 so the "
        "cognitive demand is right.",
        "RELEASE VALVE: if #13 discovery or Reverse Engineering runs long, "
        "the written CER portion of RE moves to homework; the in-class "
        "justification conversation is preserved.",
    ])

    # Do Now A - Solo Paper
    add_callout(doc, "[Do Now A]  [DOK 2] Solo Paper \u2014 Sign Flip Prediction", [
        "Students receive the SEPARATE Do Now sheet on entry. Work silently "
        "for 5 minutes. Pencil only, no Desmos, no packet.",
        "Purpose: productive use of the library-trip window + early commitment "
        "to a prediction before the class synthesis.",
        "This is DOK 2, not DOK 1 \u2014 students apply Zero Product Property "
        "and end-behavior reasoning to a novel comparison. Framework "
        "category is Do Now, but demand is higher than a typical recall warm-up.",
    ])

    add_callout(doc, "\u2705  DO NOW / ANSWER KEY", DO_NOW_KEY)

    # Do Now B+C - Blooket
    add_callout(doc, "[Do Now B+C]  [\u2014 \u2192 DOK 1] Blooket", [
        "B: 2-minute login window. Students get Chromebooks ready, type code.",
        "C: 7-minute game. Mix of Day 1 skills + 2\u20133 sign-flip primers.",
        "Diagnostic: note the two lowest-percent questions on the dashboard. "
        "If a Day 1 skill is cold, 60-second board reset before Launch.",
    ])

    add_callout(doc,
        "\U0001F3AE  Blooket Warm-Up   [Do Now B+C]  [DOK 1]   (2 + 7 min)", [
        "20 questions: zeros from factors, counting intervals, difference of "
        "squares, GCF + quadratic factoring, plus 2\u20133 sign-flip primers:",
        "  \u2022  \u201cIf f(x) = x(x \u2212 4), what are the zeros of \u2212f(x)?\u201d (same)",
        "  \u2022  \u201cIf leading coefficient is negative, which way does an "
        "odd-degree graph point on the right?\u201d (down)",
        "Hard stop at 7 minutes.",
    ])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Blooket", [
        "Use the dashboard DIAGNOSTICALLY, not as entertainment.",
        "Do NOT reteach sign flip at the board \u2014 students already "
        "committed predictions on the Do Now sheet. Surface THEIR thinking "
        "during Launch synthesis.",
    ])

    # Launch - Sign Flip Synthesis
    add_callout(doc, "[Launch]  [DOK 2] Sign Flip \u2014 Class Synthesis", [
        "Framework: Launch, 5\u201315 min. Purpose: unpack objectives, entry "
        "to new content, skill review, academic conversation, check for understanding.",
        "Students have their predictions on the Do Now sheet. This phase "
        "surfaces the predictions, checks with Desmos, and formalizes the "
        "insight. Shorter than typical Launch (6 min) because the prediction "
        "is pre-done.",
    ])

    add_callout(doc, "\U0001F504  Sign Flip Synthesis   [Launch]  [DOK 2]   (6 min)", [
        "Script:",
        "1.  \u201cPull out your Do Now sheet.\u201d (15s)",
        "2.  Turn and Talk: \u201cWhat did you predict would stay the same? "
        "What would change?\u201d (90s)",
        "3.  Cold-call a student whose prediction was WRONG about zeros "
        "(from your scan as they walked in). Ask them to share. (60s)",
        "4.  Prompt: \u201cLet\u2019s check with Desmos.\u201d Graph both. "
        "Confirm zeros identical, graph reflected. (90s)",
        "5.  Class synthesis: \u201cWhy are the zeros the same?\u201d Elicit: "
        "Zero Product Property doesn\u2019t care about \u22121. Record on "
        "board. (90s)",
        "Cold-call, don\u2019t call on volunteers \u2014 post-break, low-hand "
        "students need the re-engagement.",
    ])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Launch Synthesis", [
        "Common misconception surfaced by Do Now scan: \u201czeros change.\u201d "
        "Address directly: \u201cPlug in x = 0 to \u2212x(x \u2212 4)(x + 3). "
        "What\u2019s \u22120(\u22124)(3)? Zero. Zeros don\u2019t care about "
        "a leading negative.\u201d",
        "Language anchor: use \u201cpoints\u201d (up/down) not \u201copens\u201d "
        "for end behavior. Reserve \u201copens\u201d for parabolas.",
    ])

    # Explore - #13
    add_callout(doc, "[Explore]  [DOK 2\u20133] Practice #13 \u2014 Discovery", [
        "Framework: Explore, 35\u201340 min total. Students do the heavy lifting.",
        "Students factor x\u00b3 \u2212 8x\u00b2 + 16x \u2192 x(x \u2212 4)\u00b2, "
        "graph in Desmos, observe the graph TOUCHING at x = 4. Teacher does "
        "NOT name multiplicity. Planted seed for Day 3.",
    ])

    add_two_col(doc, [("\U0001F50D  Practice #13 / ANSWER KEY", P13_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 #13 DISCOVERY", [
        "Common stall: Factor x(x\u00b2 \u2212 8x + 16) and stop. Prompt: "
        "\u201cIs the quadratic a perfect square?\u201d",
        "Common error: Two factors (x \u2212 4)(x \u2212 4) but list x = 4 "
        "once and call it 3 zeros. Prompt: \u201cCount factors. Count "
        "distinct zeros. What\u2019s different?\u201d",
        "Discovery moment: Students say \u201cit touches but doesn\u2019t "
        "cross.\u201d Capture on board. DO NOT explain. \u201cWhich factor "
        "made that happen?\u201d Hear guesses. \u201cWe\u2019ll name it "
        "tomorrow.\u201d",
        "ELL: \u201ctouches,\u201d \u201cbounces,\u201d \u201ckisses the axis\u201d all valid.",
    ])

    # Explore - Reverse Engineering
    add_callout(doc, "[Explore]  [DOK 3] Reverse Engineering", [
        "Students coordinate three moves: zeros \u2192 factors, factored form "
        "with hidden a, point constraint \u2192 solve for a. No memorized "
        "procedure gets them there in one step.",
        "15 min. Release valve: written CER \u2192 homework if pressed; "
        "in-class partner justification preserved.",
    ])

    add_two_col(doc, [("\U0001F527  Reverse Engineering / ANSWER KEY + CER sample", REVERSE_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Reverse Engineering", [
        "Common stall: Forget the leading coefficient a. Prompt: \u201cPlug "
        "in x = 0. Do you get \u22128?\u201d",
        "Common error: Sign flip on a zero. \u201cx = \u22122\u201d becomes "
        "(x \u2212 2). Prompt: \u201cSet your factor = 0. Does it give x = \u22122?\u201d",
        "Partner roles (IEP-friendly): \u201cfactor-finder\u201d and "
        "\u201cequation-checker.\u201d Clear scope for processing-speed accommodations.",
        "CER push: \u201cExplain it to your partner using the CER template "
        "from the top of the packet. Use \u2018because.\u2019\u201d",
        "Extension: \u201cWhat if the point were (0, 8) instead?\u201d "
        "(a = 1, so f(x) = (x + 2)(x \u2212 1)(x \u2212 4).)",
    ])

    # Share / Summary
    add_callout(doc, "[Share/Summary]  [DOK 2] Synthesis + Reflection", [
        "Framework: 5\u201315 min. Synthesis, return to objectives, Criteria "
        "for Success self-rating. NOT optional \u2014 use the RE release "
        "valve before cutting this.",
    ])

    add_callout(doc,
        "\U0001F501  SHARE / SUMMARY   [Share/Summary]  [DOK 2]   (5 min)",
        SHARE_SUMMARY_STUDENT)

    add_callout(doc, "\u2705  SHARE / SUMMARY / ANSWER KEY + DIAGNOSTIC", SHARE_SUMMARY_KEY)

    # Exit Ticket
    add_callout(doc, "[Exit Ticket]  [DOK 2] Verification", [
        "Framework: shows what students learned relative to objective.",
        "Savvas Practice #6 in CER format. DOK 2 deliberately \u2014 walk-out "
        "task under time pressure should not be DOK 3.",
    ])

    add_callout(doc,
        "\U0001F4E4  EXIT TICKET \u2014 CER   [Exit Ticket]  [DOK 2]   (5 min)",
        EXIT_STUDENT)

    add_callout(doc, "\u2705  EXIT TICKET / ANSWER KEY", EXIT_KEY)

    # Closing
    add_callout(doc, "\U0001F4F7  WHAT TO COLLECT", [
        "1.  Do Now sheets \u2014 collected on entry scan or during Launch "
        "synthesis (diagnostic evidence, DOK 2).",
        "2.  Exit ticket (DOK 2, every student).",
        "3.  Reverse engineering pages \u2014 photo or collect (DOK 3 evidence).",
        "4.  Share/Summary self-ratings \u2014 quick scan as packets come in.",
        "5.  Note students who showed the \u201cit touches!\u201d discovery "
        "on #13 \u2014 call on them first in Day 3.",
    ])

    add_callout(doc, "\U0001F440  LOOK-FORS DURING WALKTHROUGH", [
        "[Do Now A] Solo paper: students working silently? Predictions in writing?",
        "[Do Now C] Blooket: Teacher monitoring dashboard diagnostically?",
        "[Launch] Sign Flip: predictions referenced? Cold-calls used to "
        "surface wrong ideas safely?",
        "[Explore] #13: students articulating observations in their own "
        "language? Teacher resisting the urge to name multiplicity?",
        "[Explore] RE: partners justifying with CER structure? "
        "\u201cBecause\u201d/\u201csince\u201d in their reasoning?",
        "[Share/Summary] Self-ratings honest? Teacher calling back Essential "
        "Question + Language Objective?",
        "[Exit Ticket] CER structure visible? All three components present?",
    ])

    add_callout(doc, "\U0001F9E9  MODIFICATIONS / SUPPORT FOR IEP STUDENTS", IEP_MODS)
    add_callout(doc, "\U0001F30D  SUPPORTS FOR ELL STUDENTS", ELL_SUPPORTS)

    doc.save(path)


if __name__ == "__main__":
    build_do_now("Day_2_Do_Now.docx")
    build_student("Day_2_Student_Packet.docx")
    build_teacher("Day_2_Teacher_Packet.docx")
    print("Built Day_2_Do_Now.docx, Day_2_Student_Packet.docx, Day_2_Teacher_Packet.docx")
