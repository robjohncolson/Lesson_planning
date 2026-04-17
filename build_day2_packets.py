"""Generate Day 2 Student + Teacher packets for Algebra 2 Unit 3 Lesson 5.

Day 2 = Graphing from Factored Form (post-spring-break Monday, 60-min usable).
Savvas-grounded sequence. Materials-light: laptops + blank paper + pencils.
No chart paper.

Aligned to the school's lesson-plan framework (Do Now / Launch / Explore /
Share-Summary / Exit Ticket) with explicit framework tags on every phase and
DOK tags for evaluator clarity.

Phases (total 60 min):
  0\u20137   Do Now        : Blooket recall                       [DOK 1]
  7\u201315  Launch        : Sign Flip Warm-Up (f vs -f)          [DOK 2]
  15\u201320 Explore       : Savvas Practice #12 fluency           [DOK 2]
  20\u201335 Explore       : Savvas Practice #13 discovery         [DOK 2-3]
  35\u201350 Explore       : Reverse engineering                   [DOK 3]
  50\u201355 Share/Summary : Synthesis + self-reflection           [DOK 2]
  55\u201360 Exit Ticket   : CER (Savvas Practice #6)              [DOK 2]
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


# ------------------------------------------------------------------
# Student content
# ------------------------------------------------------------------

SIGN_FLIP_STUDENT = [
    "f(x) = x(x \u2212 4)(x + 3)   vs.   g(x) = \u2212x(x \u2212 4)(x + 3)",
    "Before you graph, predict:",
    "\u2022  What will stay the EXACT SAME when you graph these?",
    "   _______________________________________________",
    "\u2022  What will CHANGE? How do you know before graphing?",
    "   _______________________________________________",
    "Think silently (2 min) \u2192 Turn and Talk with your partner (2 min) "
    "\u2192 Desmos check.",
    "Frame: \u201cThe zeros stay the same because ___. The graph changes because ___.\u201d",
]

P12_STUDENT = [
    "f(x) = 3x\u00b3 \u2212 9x\u00b2 \u2212 12x",
    "Fluency check \u2014 blank paper, no full sketch. You have 5 minutes.",
    "Step 1 \u2014 Factor",
    "Pull out the GCF:  3x(________________)",
    "Factor the quadratic inside:  = 3x(________)(________)",
    "Step 2 \u2014 Zeros",
    "The zeros are: ________,  ________,  ________",
    "Step 3 \u2014 Plot them on a number line below. (No sketch today.)",
    "\u27a1\ufe0f  How many intervals does this divide the number line into? ____",
]

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
    "Step 4 \u2014 Explain to your partner:",
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
    "Claim:  ____________________________________________",
    "_______________________________________________",
    "Evidence:  __________________________________________",
    "_______________________________________________",
    "Reasoning:  _________________________________________",
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

    add_callout(doc, "\U0001F3AE  Blooket Warm-Up   [Do Now]  [DOK 1]   (7 min)", [
        "Join the game! Your teacher will display the code.",
        "Topics: finding zeros from factors, counting intervals, difference of "
        "squares, GCF + quadratic factoring, and a new sign-flip primer.",
    ])

    add_two_col(doc, [(
        "\U0001F504  Sign Flip Warm-Up   [Launch]  [DOK 2]   (8 min)",
        SIGN_FLIP_STUDENT,
    )])
    add_two_col(doc, [(
        "\u270f\ufe0f  Practice #12 \u2014 Fluency Pre-Check   [Explore]  [DOK 2]   (5 min)",
        P12_STUDENT,
    )])
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


# ------------------------------------------------------------------
# Teacher edition
# ------------------------------------------------------------------

CRITERIA_FOR_SUCCESS = [
    "Student-facing, revisited during Share/Summary:",
    "1.  I can factor a polynomial using GCF and quadratic-factoring patterns.",
    "2.  I can identify all zeros of a polynomial from factored form.",
    "3.  I can predict what happens to a graph when f(x) becomes \u2212f(x).",
    "4.  I can build a polynomial equation from given zeros and a point.",
    "5.  I can describe (in my own words) what a graph does at a repeated zero.",
    "Formative assessment evidence:",
    "\u2022  Blooket per-student percentages (Do Now, DOK 1).",
    "\u2022  Partner conversations during Sign Flip and Reverse Engineering (circulating).",
    "\u2022  Reverse engineering page \u2014 collected or photographed (DOK 3).",
    "\u2022  Share/Summary self-rating (student-owned).",
    "\u2022  CER exit ticket (DOK 2, collected).",
]

SELF_REFLECTION = [
    "Completed by students during Share/Summary (5 min phase):",
    "\u2022  Rate each Criterion for Success: \u2713 / partly / not yet.",
    "\u2022  One-sentence reflection is NOT required today. Post-break, the "
    "written CER exit ticket is the language-load. Self-rating only.",
    "Teacher use:",
    "\u2022  Scan ratings as packets are turned in. Students self-rating "
    "\u201cnot yet\u201d on #4 (repeated zero) are primed for Day 3 \u2014 "
    "call on them first tomorrow to describe what they saw.",
    "\u2022  Students rating \u201cnot yet\u201d on #3 (reverse engineering) "
    "need a quick conference during the next Do Now.",
]

IEP_MODS = [
    "\u2022  Chunked tasks on blank paper: one step per clearly numbered step. "
    "No dense text blocks.",
    "\u2022  Desmos graphing reduces fine-motor sketch demand \u2014 sketches "
    "on blank paper are supported, not required to be precise.",
    "\u2022  Partner pairing for Reverse Engineering: assign roles "
    "(\u201cfactor-finder\u201d and \u201cequation-checker\u201d) so students "
    "with processing-speed accommodations have a clearly scoped job.",
    "\u2022  Extended-time release valve is built-in: the written CER portion "
    "of Reverse Engineering can move to homework if class time runs short. "
    "No student is penalized for not finishing written work in class.",
    "\u2022  Blooket answers read aloud to the class if an individual IEP "
    "requires it (audio support).",
    "\u2022  Preferential seating for students with attention accommodations "
    "\u2014 close to board for Sign Flip synthesis.",
]

ELL_SUPPORTS = [
    "\u2022  Sentence frame: \u201cThe zeros stay the same because ___. "
    "The graph changes because ___.\u201d",
    "\u2022  Predict-before-verify routine \u2014 students commit in writing "
    "before speaking.",
    "\u2022  \u201cTouches\u201d / \u201cbounces\u201d / \u201cturns\u201d all "
    "accepted for #13 discovery today; academic term (multiplicity) deferred "
    "to Day 3.",
    "\u2022  No new vocabulary introduced today \u2014 deliberate language-load "
    "reduction after a week off.",
    "\u2022  Materials-light: no chart paper setup, no manipulatives. Reduces "
    "logistical language for group transitions.",
    "\u2022  Think-Pair-Share before any public share; writing before speaking.",
    "\u2022  Share/Summary self-rating uses check/partly/not-yet icons, not "
    "sentence-level reflection \u2014 keeps the cognitive load on the math, "
    "not on producing English.",
]

P12_KEY = [
    "f(x) = 3x\u00b3 \u2212 9x\u00b2 \u2212 12x",
    "\u2705 GCF: 3x(x\u00b2 \u2212 3x \u2212 4)",
    "\u2705 Factored: 3x(x \u2212 4)(x + 1)",
    "\u2705 Zeros: x = 0,  x = 4,  x = \u22121",
    "\u2705 Number line: plot \u22121, 0, 4 \u2192 four intervals: "
    "(\u2212\u221e, \u22121), (\u22121, 0), (0, 4), (4, \u221e)",
    "Note: deliberate repeat of the GCF-cubic pattern from Day 1 Try It 1a. "
    "Students should do this quickly. Cap at 5 min \u2014 still-stuck "
    "students pair with finishers; don't reteach class-wide.",
]

P13_KEY = [
    "g(x) = x\u00b3 \u2212 8x\u00b2 + 16x",
    "\u2705 GCF: x(x\u00b2 \u2212 8x + 16)",
    "\u2705 Factored: x(x \u2212 4)\u00b2  \u2190  REPEATED FACTOR",
    "\u2705 Zeros: x = 0 and x = 4 (only two distinct \u2014 x = 4 appears twice)",
    "\u2705 At x = 4 in Desmos: the graph TOUCHES the x-axis and turns around "
    "(does not cross).",
    "\u2705 End behavior: x\u00b3 \u2192 down left, up right (odd degree, "
    "positive leading coeff).",
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
    "   \u22128 = a(0 + 2)(0 \u2212 1)(0 \u2212 4)",
    "   \u22128 = a(2)(\u22121)(\u22124)",
    "   \u22128 = 8a",
    "   a = \u22121",
    "\u2705 Step 3 \u2014 Final: f(x) = \u2212(x + 2)(x \u2212 1)(x \u2212 4)",
    "\u2705 Desmos check: passes through (0, \u22128), zeros at \u22122, 1, 4, "
    "leading negative flips end behavior to up-left/down-right.",
    "WHY THIS IS DOK 3:",
    "Students coordinate three moves: (1) zeros \u2192 factors (inverse Zero "
    "Product Property), (2) factored form with hidden parameter a, "
    "(3) point constraint \u2192 solve for a. No memorized procedure gets them "
    "there in one step.",
    "Compressed window (15 min, down from 18): if partner conversations "
    "take too long, written CER component of Reverse Engineering moves to "
    "homework. Preserve the DOK 3 partner discussion \u2014 that\u2019s where "
    "the reasoning lives.",
]

SHARE_SUMMARY_KEY = [
    "Sentence completion: The ZEROS of a polynomial came from its FACTORS, "
    "and a POINT on the graph told us the leading coefficient.",
    "Criteria for Success \u2014 what to scan when packets come in:",
    "\u2022  #1 (factoring): should be \u2713 or \u201cpartly\u201d for most. "
    "\u201cNot yet\u201d = intervention in next Do Now.",
    "\u2022  #2 (sign flip): should be \u2713 for most \u2014 it was explicit "
    "Launch content.",
    "\u2022  #3 (reverse engineering): \u201cpartly\u201d is acceptable for "
    "most today. This was the new DOK 3 skill. Not-yet is diagnostic \u2014 "
    "cluster these students for partner-pair support in Day 3\u2019s Explore.",
    "\u2022  #4 (repeated zero): expect mostly \u201cpartly\u201d or "
    "\u201cnot yet\u201d \u2014 we deliberately did NOT name it today. Day 3 "
    "exists precisely to name this.",
    "Teacher action during Share/Summary (5 min):",
    "1.  Call back the Essential Question: \u201cHow do zeros + a point "
    "determine the equation?\u201d Invite one student to answer in their "
    "own words.",
    "2.  Revisit the Language Objective: \u201cWho used \u2018the zeros stay "
    "the same because...\u2019 today? What did you finish the sentence with?\u201d "
    "Hear 2\u20133 voices.",
    "3.  Students circle their self-ratings (90 seconds).",
    "4.  Tease Day 3: \u201cTomorrow we name the thing that happened at x = 4 "
    "in g(x).\u201d Do not name it now.",
]

EXIT_KEY = [
    "Savvas Practice #6: \u201cIf you use zeros to sketch the graph of a "
    "polynomial function, how can you verify that your graph is correct?\u201d",
    "Sample answer:",
    "CLAIM: The graph can be verified by checking zeros, end behavior, and "
    "sign intervals.",
    "EVIDENCE: Substitute each x-value at a zero \u2014 f(x) should equal 0. "
    "Pick a test point in each interval \u2014 the sign of f(test) should "
    "match whether the graph is above or below the x-axis there. Compare "
    "to a Desmos graph.",
    "REASONING: Zeros are where the graph meets the x-axis by definition, "
    "so if sketched zeros match the factors, x-intercepts are right. Test "
    "points confirm the shape between. Desmos is a visual cross-check.",
    "Why DOK 2: applying known verification strategies. Not constructing a "
    "novel argument \u2014 that was Reverse Engineering.",
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
        "Aligned to the school\u2019s lesson-plan framework: "
        "Do Now \u2192 Launch \u2192 Explore \u2192 Share/Summary "
        "\u2192 Exit Ticket. Every phase carries an explicit [Framework] and "
        "[DOK] tag in this packet and in the classroom pacer HTML.",
        "[DOK 1] Recall & Reproduction \u2014 retrieve a procedure, one right answer.",
        "  \u2192  Blooket warm-up [Do Now].",
        "[DOK 2] Skills & Concepts \u2014 apply a procedure to a new problem, "
        "multi-step decisions.",
        "  \u2192  Sign Flip Warm-Up [Launch]; #12 fluency [Explore]; #13 "
        "discovery [Explore]; Share/Summary synthesis; CER exit ticket.",
        "[DOK 3] Strategic Thinking \u2014 reason across representations, "
        "construct an argument, generalize.",
        "  \u2192  Reverse Engineering [Explore]: zeros + y-intercept "
        "\u2192 equation.",
        "Note: the Exit Ticket is intentionally DOK 2, not DOK 3. Students "
        "get their DOK 3 work done during Reverse Engineering with teacher "
        "+ partner support. A walk-out-the-door task at DOK 3 under time "
        "pressure produces unreliable formative evidence.",
    ])

    add_callout(doc,
        "\u2705  CRITERIA FOR SUCCESS  /  FORMATIVE ASSESSMENT",
        CRITERIA_FOR_SUCCESS)

    add_callout(doc,
        "\U0001F9ED  SELF-REFLECTION ASSESSMENT",
        SELF_REFLECTION)

    add_callout(doc, "\u26a0\ufe0f  PACING NOTE \u2014 POST-SPRING-BREAK MONDAY", [
        "Hard budget: 60 minutes usable (last 5 of the block reserved for "
        "students to pack up). Every minute counts.",
        "Expect activation friction. Students have been off a week; skill "
        "decay is real. The Blooket is diagnostic \u2014 watch for which "
        "skills are cold. If Blooket reveals >40% miss on one skill, pause "
        "60 seconds before Launch to reset it. Do not exceed 60 seconds.",
        "RELEASE VALVE: if #13 discovery or Reverse Engineering runs long, "
        "the WRITTEN portion of Reverse Engineering compresses to homework; "
        "the in-class partner JUSTIFICATION conversation is preserved. Do "
        "NOT compress the discovery moment at x = 4 in #13 \u2014 that\u2019s "
        "the bridge to Day 3.",
        "Chart paper intentionally skipped today. Traveling-teacher setup "
        "cost is high and no walkthroughs are scheduled; students get a "
        "materials-light day after four days of chart-paper work.",
    ])

    # Do Now
    add_callout(doc, "[Do Now]  [DOK 1] Recall & Reproduction", [
        "Framework: Do Now, <10 min. Purpose: engage, hook, diagnostic.",
        "Students retrieve Day 1 procedures (zeros from factors, counting "
        "intervals, difference of squares, GCF factoring) and get a primer "
        "on sign flip via 2\u20133 new items.",
    ])

    add_callout(doc,
        "\U0001F3AE  Blooket Warm-Up   [Do Now]  [DOK 1]   (7 min)", [
        "20 questions. Day 1 skill mix plus 2\u20133 sign-flip primers:",
        "  \u2022  \u201cIf f(x) = x(x \u2212 4), what are the zeros of \u2212f(x)?\u201d (same)",
        "  \u2022  \u201cIf the leading coefficient is negative, which way does "
        "an odd-degree graph point on the right?\u201d (down)",
        "Watch the dashboard. Hard stop at 7 minutes.",
    ])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Blooket", [
        "Diagnostic: note the two lowest-percent questions.",
        "If a Day 1 skill is cold: 60-second board reset, then move on. It "
        "will get reps during Explore.",
        "Do NOT reteach sign flip at the board. Let students discover it in "
        "Launch in 2 minutes.",
    ])

    # Launch
    add_callout(doc, "[Launch]  [DOK 2] Skills & Concepts \u2014 Sign Flip", [
        "Framework: Launch, 5\u201315 min. Purpose: unpack objectives, entry "
        "point to new content, review skill, academic conversation, check "
        "for understanding.",
        "Students apply Day 1\u2019s sign-chart and end-behavior reasoning to "
        "a NEW comparison: f vs. \u2212f. Predict BEFORE verifying. Articulate "
        "what changes vs. stays. Multi-step reasoning across algebraic and "
        "graphical representations.",
    ])

    add_two_col(doc, [("\U0001F504  Sign Flip Warm-Up   [Launch]  [DOK 2]   (8 min)", [
        "f(x) = x(x \u2212 4)(x + 3)   vs.   g(x) = \u2212x(x \u2212 4)(x + 3)",
        "Think silently (2 min) \u2192 Turn and Talk (2 min) \u2192 Desmos "
        "verify + class synthesis (4 min).",
        "KEY POINTS (do NOT front-load \u2014 draw from students):",
        "\u2022  Zeros are identical (\u22123, 0, 4). The factor x flipping "
        "sign does not change where it equals 0.",
        "\u2022  Sign chart flips every row.",
        "\u2022  End behavior flips: positive cubic goes down-left/up-right; "
        "negative cubic goes up-left/down-right.",
        "\u2022  The graph is a reflection over the x-axis.",
    ])])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Sign Flip", [
        "Common misconception: \u201cThe zeros change.\u201d Prompt: \u201cPlug "
        "in x = 0. Does \u22120 equal 0?\u201d",
        "Push for precision: \u201cHow do you know BEFORE you graph that the "
        "zeros are the same?\u201d (Zero Product Property: 0 times anything "
        "is 0, regardless of a leading negative.)",
        "End-behavior language: use \u201cpoints\u201d (up/down), not "
        "\u201copens.\u201d Reserve \u201copens\u201d for parabolas.",
    ])

    # Explore - #12
    add_callout(doc, "[Explore 1]  [DOK 2] \u2014 Fluency Pre-Check", [
        "Framework: Explore, 35\u201340 min total (across three activities). "
        "Purpose: cognitively demanding task, academic conversation, content-"
        "based writing, students doing heavy lifting.",
        "Savvas Practice #12. Factor and identify zeros only \u2014 no sketch. "
        "Deliberate repeat of Day 1 Try It 1a (GCF cubic) to confirm the "
        "skill survived break. 5 minutes; still-stuck students partner up.",
    ])

    add_two_col(doc, [("\u270f\ufe0f  Practice #12 / ANSWER KEY", P12_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 #12", [
        "No circulating teaching. Circulate watching only \u2014 diagnostic: "
        "who factored fluently, who didn\u2019t.",
        "Stuck on x\u00b2 \u2212 3x \u2212 4? Prompt: \u201cTwo numbers \u00d7 "
        "to \u22124, + to \u22123.\u201d Give once; pair with a finisher; MOVE ON.",
        "Hard stop at 5 min even if not all finished. #13 is the "
        "instructional priority.",
    ])

    # Explore - #13
    add_callout(doc,
        "[Explore 2]  [DOK 2\u20133] Skills & Concepts \u2192 Strategic Thinking", [
        "Savvas Practice #13. Factor x\u00b3 \u2212 8x\u00b2 + 16x \u2192 "
        "x(x \u2212 4)\u00b2, graph in Desmos, observe the graph TOUCHING the "
        "x-axis at x = 4 (not crossing). Phenomenon not seen before. Students "
        "describe in their own words; teacher does NOT name multiplicity "
        "today. Planted seed for Day 3.",
        "Compressed to 15 min (was 17) to make room for Share/Summary. The "
        "discovery moment itself is NOT cut \u2014 Desmos observation and "
        "student articulation are preserved.",
    ])

    add_two_col(doc, [("\U0001F50D  Practice #13 / ANSWER KEY", P13_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 #13 DISCOVERY", [
        "Common stall: Factor x(x\u00b2 \u2212 8x + 16) and stop. Prompt: "
        "\u201cLook at the quadratic. Is it a perfect square?\u201d",
        "Common error: Write (x \u2212 4)(x \u2212 4) but list x = 4 only "
        "once and call it 3 zeros. Prompt: \u201cCount factors. Count distinct "
        "zero values. What\u2019s different?\u201d",
        "The moment that matters: Students graph in Desmos and say \u201cit "
        "touches but doesn\u2019t cross.\u201d Capture on the board. DO NOT "
        "explain. Ask one follow-up: \u201cWhich factor made that happen, do "
        "you think?\u201d Hear guesses. Say \u201cwe\u2019ll name it tomorrow.\u201d "
        "Leave it open.",
        "ELL support: \u201ctouches\u201d / \u201cbounces\u201d / \u201ckisses "
        "the axis\u201d all valid today. Precision is tomorrow\u2019s job.",
    ])

    # Explore - Reverse Engineering
    add_callout(doc, "[Explore 3]  [DOK 3] Strategic Thinking \u2014 Reverse Engineering", [
        "Students reverse the Day 1 process: given zeros and a point on the "
        "graph, construct the polynomial equation. DOK 3 because students "
        "coordinate three representations: (1) zeros \u2192 factors (inverse "
        "Zero Product Property), (2) factored form with hidden parameter a, "
        "(3) point constraint \u2192 solve for a.",
        "Compressed to 15 min (was 18) to make room for Share/Summary. "
        "Release valve: written CER portion moves to homework if time "
        "runs short; in-class partner justification is preserved. This is "
        "where the DOK 3 reasoning lives.",
    ])

    add_two_col(doc, [("\U0001F527  Reverse Engineering / ANSWER KEY", REVERSE_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Reverse Engineering", [
        "Common stall: Students write f(x) = (x + 2)(x \u2212 1)(x \u2212 4) "
        "without the leading coefficient a. Prompt: \u201cPlug in x = 0. What "
        "do you get? Is that \u22128?\u201d",
        "Common error: Sign flip on a zero. \u201cx = \u22122\u201d becomes "
        "(x \u2212 2). Prompt: \u201cSet your factor = 0. Does it give x = \u22122?\u201d",
        "Partner roles (IEP-friendly): one student is \u201cfactor-finder,\u201d "
        "one is \u201cequation-checker.\u201d Clear scope for processing-speed "
        "accommodations.",
        "If short on time: verbal partner justification in class; written CER "
        "as homework. Do NOT skip the justification conversation.",
        "Extension: \u201cWhat if the point were (0, 8) instead?\u201d "
        "(a = 1, so f(x) = (x + 2)(x \u2212 1)(x \u2212 4).)",
    ])

    # Share / Summary
    add_callout(doc, "[Share/Summary]  [DOK 2] Synthesis + Reflection", [
        "Framework: Share/Summary, 5\u201315 min. Purpose: synthesis of "
        "learning, return to content and language objectives, reflection on "
        "criteria for success, academic conversation.",
        "This phase was explicitly added for framework alignment. Do NOT "
        "skip it even if Explore runs long \u2014 use the Reverse Engineering "
        "release valve instead.",
    ])

    add_callout(doc,
        "\U0001F501  SHARE / SUMMARY   [Share/Summary]  [DOK 2]   (5 min)", [
        "Teacher script:",
        "1.  Essential Question callback (60 sec): \u201cHow do the zeros "
        "and a point on the graph determine the polynomial\u2019s equation?\u201d "
        "Hear one student; paraphrase with precision.",
        "2.  Language Objective check (60 sec): \u201cWho used \u2018the "
        "zeros stay the same because...\u2019 today? What did you finish it "
        "with?\u201d Hear 2\u20133 voices.",
        "3.  Students complete sentence completion + self-ratings on packet "
        "(90 sec). Teacher circulates and scans ratings.",
        "4.  Preview Day 3 (30 sec): \u201cTomorrow we name what happened "
        "at x = 4.\u201d Do NOT name it.",
        "5.  Collect packets (30 sec) as students transition to CER.",
    ])

    add_callout(doc,
        "\u2705  SHARE / SUMMARY / ANSWER KEY + DIAGNOSTIC",
        SHARE_SUMMARY_KEY)

    # Exit Ticket
    add_callout(doc, "[Exit Ticket]  [DOK 2] Verification", [
        "Framework: Exit Ticket / Assessment. Purpose: show what students "
        "have learned based on the objective.",
        "Savvas Practice #6. Students apply known verification strategies "
        "(substitute, test points, Desmos cross-check) to a general question "
        "about sketch correctness. DOK 2 deliberately \u2014 walk-out task "
        "under time pressure should not be DOK 3.",
    ])

    add_callout(doc,
        "\U0001F4E4  EXIT TICKET \u2014 CER   [Exit Ticket]  [DOK 2]   (5 min)", [
        "\u201cIf you use zeros to sketch the graph of a polynomial function, "
        "how can you verify that your graph is correct?\u201d",
        "Students write Claim / Evidence / Reasoning on the student packet.",
    ])

    add_callout(doc, "\u2705  EXIT TICKET / ANSWER KEY", EXIT_KEY)

    # Closing
    add_callout(doc, "\U0001F4F7  WHAT TO COLLECT", [
        "1.  Exit ticket from each student (DOK 2 formative evidence).",
        "2.  Reverse engineering pages \u2014 scan or photo the equation and "
        "justification (DOK 3 formative evidence).",
        "3.  Share/Summary self-ratings \u2014 quick visual scan as packets "
        "come in.",
        "4.  Note which students showed the \u201cit touches!\u201d discovery "
        "on #13 \u2014 call on them first in Day 3.",
    ])

    add_callout(doc, "\U0001F440  LOOK-FORS DURING WALKTHROUGH", [
        "[Do Now] Blooket: Teacher monitoring dashboard diagnostically?",
        "[Launch] Sign Flip: Students predicting BEFORE graphing? Teacher "
        "circulating with questions, not answers?",
        "[Explore] #13 discovery: Students articulating observations in "
        "their own language? Teacher resisting the urge to name multiplicity?",
        "[Explore] Reverse Engineering: Partners justifying leading "
        "coefficient? Students referencing the point constraint by name?",
        "[Share/Summary] Students self-rating honestly? Teacher calling "
        "back to Essential Question + Language Objective?",
        "[Exit Ticket] CER structure visible? All three components present?",
    ])

    add_callout(doc,
        "\U0001F9E9  MODIFICATIONS / SUPPORT FOR IEP STUDENTS",
        IEP_MODS)

    add_callout(doc,
        "\U0001F30D  SUPPORTS FOR ELL STUDENTS",
        ELL_SUPPORTS)

    doc.save(path)


if __name__ == "__main__":
    build_student("Day_2_Student_Packet.docx")
    build_teacher("Day_2_Teacher_Packet.docx")
    print("Built Day_2_Student_Packet.docx and Day_2_Teacher_Packet.docx")
