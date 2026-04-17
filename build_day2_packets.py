"""Generate Day 2 Student + Teacher packets for Algebra 2 Unit 3 Lesson 5.

Day 2 = Graphing from Factored Form (post-spring-break Monday, 60-min usable).
Savvas-grounded sequence. Materials-light: laptops + blank paper + pencils.
No chart paper.

Phases (total 60 min):
  0\u20137   Blooket recall                                       [DOK 1]
  7\u201315  Sign Flip Warm-Up (f vs -f)                         [DOK 2]
  15\u201320 Savvas Practice #12 fluency pre-check               [DOK 2]
  20\u201337 Savvas Practice #13 discovery (repeated root)       [DOK 2-3]
  37\u201355 Reverse engineering from zeros + y-intercept         [DOK 3]
  55\u201360 CER Exit Ticket (Savvas Practice #6)                 [DOK 2]

Format mirrors Day 1 packet conventions exactly: plain-paragraph headers,
bordered tables for every section, 2-col label|content for titled blocks,
1-col callout for activity panels. Teacher edition adds DOK labels,
justifications, teacher moves, answer keys, look-fors, ELL supports.
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
# Content blocks
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

EXIT_STUDENT = [
    "\ud83d\udce4  EXIT TICKET \u2014 CER  [DOK 2]",
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

# Convert emoji surrogate-pair literals via explicit codepoints where needed
EXIT_STUDENT[0] = "\U0001F4E4  EXIT TICKET \u2014 CER  [DOK 2]"


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

    add_callout(doc, "\U0001F501  WELCOME BACK \u2014 RECALL", [
        "Before break you built sign charts and sketches for three "
        "polynomials and finished with The Leap. Today we push further:",
        "\u2022  What does a negative leading coefficient do to the graph?",
        "\u2022  What happens when a zero appears twice?",
        "\u2022  Can you write an equation from scratch if you know the zeros?",
        "Materials today: laptop (Desmos), blank paper, pencil.",
    ])

    add_callout(doc, "\U0001F3AE  Blooket Warm-Up  (7 min)", [
        "Join the game! Your teacher will display the code.",
        "Topics: finding zeros from factors, counting intervals, difference of "
        "squares, GCF + quadratic factoring, and a new sign-flip primer.",
    ])

    add_two_col(doc, [("\U0001F504  Sign Flip Warm-Up  (8 min)", SIGN_FLIP_STUDENT)])
    add_two_col(doc, [("\u270f\ufe0f  Fluency Pre-Check  (5 min)", P12_STUDENT)])
    add_two_col(doc, [("\U0001F50D  Discovery: something new at a zero  (17 min)", P13_STUDENT)])
    add_two_col(doc, [("\U0001F527  Build the Equation  (18 min)", REVERSE_ENG_STUDENT)])

    add_callout(doc, EXIT_STUDENT[0], EXIT_STUDENT[1:])

    doc.save(path)


# ------------------------------------------------------------------
# Teacher edition
# ------------------------------------------------------------------

P12_KEY = [
    "f(x) = 3x\u00b3 \u2212 9x\u00b2 \u2212 12x",
    "\u2705 GCF: 3x(x\u00b2 \u2212 3x \u2212 4)",
    "\u2705 Factored: 3x(x \u2212 4)(x + 1)",
    "\u2705 Zeros: x = 0,  x = 4,  x = \u22121",
    "\u2705 Number line: plot \u22121, 0, 4 \u2192 four intervals: "
    "(\u2212\u221e, \u22121), (\u22121, 0), (0, 4), (4, \u221e)",
    "Note: this is a deliberate repeat of the GCF-cubic pattern from Day 1's "
    "Try It 1a. Students should do this quickly. Cap at 5 minutes \u2014 "
    "anyone still stuck goes to partner support; don't reteach class-wide.",
]

P13_KEY = [
    "g(x) = x\u00b3 \u2212 8x\u00b2 + 16x",
    "\u2705 GCF: x(x\u00b2 \u2212 8x + 16)",
    "\u2705 Factored: x(x \u2212 4)\u00b2  \u2190  REPEATED FACTOR",
    "\u2705 Zeros: x = 0 and x = 4 (only two distinct \u2014 x = 4 appears twice)",
    "\u2705 What happens at x = 4 in Desmos: the graph TOUCHES the x-axis and "
    "turns around (does not cross)",
    "\u2705 End behavior: x\u00b3 \u2192 down left, up right (odd degree, positive leading coeff)",
    "TEACHER MOVE \u2014 the discovery:",
    "Students will see the graph touch at x = 4 and ask \u201cwhy doesn\u2019t "
    "it cross?\u201d DO NOT name multiplicity today. Say: \u201cInteresting. "
    "Describe what you see in your own words.\u201d Log the observation on the "
    "board as a class-curiosity. Tomorrow is Day 3: Multiplicity. Let the "
    "mystery sit overnight.",
    "Accept student language: \u201ctouches\u201d / \u201cbounces\u201d / "
    "\u201cturns\u201d / \u201ckisses the axis.\u201d All fine for today.",
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
    "\u2705 Desmos check: graph should pass through (0, \u22128) with zeros at "
    "\u22122, 1, 4, and (because a is negative) go UP on the left, DOWN on the right.",
    "WHY THIS IS DOK 3:",
    "Students must (1) translate zeros \u2192 factors (Zero Product Property in "
    "reverse), (2) recognize that any leading coefficient a scales the function, "
    "(3) use a known point to solve for a. Three representations used together: "
    "algebraic zeros, factored form, point on graph.",
]

EXIT_KEY = [
    "Savvas Practice #6: \u201cIf you use zeros to sketch the graph of a "
    "polynomial function, how can you verify that your graph is correct?\u201d",
    "Sample answer:",
    "CLAIM: The graph can be verified by checking zeros, end behavior, and "
    "sign intervals.",
    "EVIDENCE: Substitute each x-value at a zero \u2014 the function should "
    "equal 0. Pick a test point in each interval \u2014 the sign of f(test) "
    "should match whether the graph is above or below the x-axis there. "
    "Compare to a Desmos graph.",
    "REASONING: Zeros are where the graph crosses or touches the x-axis by "
    "definition, so if my sketched zeros match the factors, the x-intercepts "
    "are right. Test points confirm the shape in between. Desmos is a visual "
    "cross-check.",
    "Why DOK 2: applying known verification strategies (substitute, test "
    "points, tech check) to a general question. Not constructing a novel "
    "argument \u2014 that was the reverse engineering task earlier in class.",
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

    add_callout(doc, "\U0001F4CB  DOK GUIDE FOR EVALUATORS", [
        "This lesson sequences DOK 1\u21922\u21923 across a 60-minute post-"
        "spring-break Monday. Savvas-grounded, materials-light "
        "(laptops + blank paper, no chart paper). Each section is "
        "explicitly labeled and justified.",
        "[DOK 1] Recall & Reproduction \u2014 retrieve a procedure, one right answer.",
        "  \u2192  Blooket warm-up.",
        "[DOK 2] Skills & Concepts \u2014 apply a procedure to a new problem, "
        "multi-step decisions.",
        "  \u2192  Sign flip prediction; Practice #12 fluency; Practice #13 "
        "discovery; CER exit ticket (applying verification strategies).",
        "[DOK 3] Strategic Thinking \u2014 reason across representations, construct "
        "an argument, generalize.",
        "  \u2192  Reverse engineering: zeros + y-intercept \u2192 equation. "
        "Students coordinate zero-product reasoning, factor form, and a point "
        "constraint to determine the leading coefficient.",
        "Exit ticket is intentionally DOK 2, not DOK 3. DOK 3 for the day is "
        "reverse engineering, where students have teacher + partner support. "
        "A walk-out-the-door task at DOK 3 under time pressure produces "
        "unreliable formative evidence.",
    ])

    add_callout(doc, "\u26a0\ufe0f  PACING NOTE \u2014 POST-SPRING-BREAK MONDAY", [
        "Hard budget: 60 minutes usable (last 5 of the block reserved for "
        "students to pack up). Every minute counts.",
        "Expect activation friction. Students have been off a week; skill "
        "decay is real. The Blooket is diagnostic \u2014 watch for which skills "
        "are cold. If Blooket reveals >40% miss on one skill, pause 60 "
        "seconds before the warm-up to reset it. Do not spend longer than "
        "that \u2014 kids who need more will get it during the fluency "
        "pre-check anyway.",
        "RELEASE VALVE: if #13 discovery or reverse engineering runs long, "
        "the reverse engineering task compresses to \u201cverbal partner "
        "work only, written justification is homework.\u201d Do NOT compress "
        "the discovery moment at x = 4 in #13 \u2014 that\u2019s the bridge "
        "to Day 3.",
        "Chart paper intentionally skipped today. Traveling-teacher setup "
        "cost is high and no walkthroughs are scheduled; kids get a "
        "blank-paper break after four days of chart-paper work.",
    ])

    # DOK 1
    add_callout(doc, "[DOK 1] Recall & Reproduction", [
        "Students retrieve memorized procedures: identifying zeros from "
        "factors, counting intervals, difference of squares, GCF factoring. "
        "Includes one new primer-level question on sign flip (\u201cif a "
        "factor flips sign, what happens?\u201d) to set up the warm-up.",
    ])

    add_callout(doc, "\U0001F3AE  Blooket Warm-Up  [DOK 1]   (7 min)", [
        "20 questions. Mix of Day 1 skills (zeros, intervals, factoring) "
        "plus 2\u20133 sign-flip primer questions:",
        "  \u2022  \u201cIf f(x) = x(x \u2212 4), what are the zeros of \u2212f(x)?\u201d (same zeros)",
        "  \u2022  \u201cIf the leading coefficient is negative, which way does an odd-degree graph point on the right?\u201d (down)",
        "Watch the dashboard. Hard stop at 7 minutes.",
    ])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Blooket", [
        "Diagnostic: Which skills have decayed most over break? Note the two "
        "lowest-percent questions.",
        "If a Day 1 skill is cold: 60-second board reset, then move on \u2014 "
        "it will get reps during the activities.",
        "Do NOT reteach sign flip at the board. Let students discover it in "
        "the warm-up in 2 minutes.",
    ])

    # DOK 2 - Sign Flip
    add_callout(doc, "[DOK 2] Skills & Concepts \u2014 Sign Flip", [
        "Students apply Day 1\u2019s sign-chart and end-behavior reasoning to "
        "a NEW comparison: f vs. \u2212f. Requires predicting before verifying "
        "and articulating what changes vs. what stays. Multi-step reasoning "
        "across algebraic and graphical representations.",
    ])

    add_two_col(doc, [("\U0001F504  Sign Flip Warm-Up  [DOK 2]   (8 min)", [
        "f(x) = x(x \u2212 4)(x + 3)   vs.   g(x) = \u2212x(x \u2212 4)(x + 3)",
        "Think silently (2 min) \u2192 Turn and Talk (2 min) \u2192 Desmos "
        "verify + class synthesis (4 min).",
        "KEY POINTS (do NOT front-load \u2014 draw from students):",
        "\u2022  Zeros are identical (\u22123, 0, 4). The factor x flipping sign "
        "does not change where it equals 0.",
        "\u2022  Sign chart flips every row. Product has one more negative.",
        "\u2022  End behavior flips: positive cubic goes down-left/up-right; "
        "negative cubic goes up-left/down-right.",
        "\u2022  The graph is a reflection over the x-axis.",
    ])])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Sign Flip", [
        "Common misconception: \u201cThe zeros change.\u201d Prompt: \u201cPlug "
        "in x = 0. Does \u22120 equal 0?\u201d",
        "Push for precision: \u201cHow do you know BEFORE you graph that the "
        "zeros are the same?\u201d (Zero Product Property: 0 times anything is 0, "
        "regardless of a leading negative sign.)",
        "End-behavior language: use \u201cpoints\u201d (up/down) not \u201copens.\u201d "
        "Reserves \u201copens\u201d for parabolas.",
    ])

    # Practice #12
    add_callout(doc, "[DOK 2] Skills & Concepts \u2014 Fluency Pre-Check", [
        "Savvas Practice #12. Students factor and identify zeros only \u2014 "
        "no sketch. Deliberate repeat of the Day 1 Try It 1a pattern (GCF "
        "cubic) to confirm the skill survived break. 5 minutes; anyone "
        "still factoring at 5-minute mark partners up with a nearby student "
        "who finished.",
    ])

    add_two_col(doc, [("\u270f\ufe0f  Practice #12 / ANSWER KEY", P12_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 #12", [
        "No circulating teaching. Circulate watching only. This is a "
        "diagnostic: who factored fluently, who didn\u2019t.",
        "If a student gets stuck factoring x\u00b2 \u2212 3x \u2212 4, prompt: "
        "\u201cTwo numbers \u00d7 to \u22124, + to \u22123.\u201d Give the "
        "prompt once; if still stuck, pair with a finisher and MOVE ON.",
        "Hard stop at 5 minutes even if not all finished. #13 is the "
        "instructional priority.",
    ])

    # Practice #13 - the discovery
    add_callout(doc, "[DOK 2\u20133] Skills & Concepts \u2192 Strategic Thinking", [
        "Savvas Practice #13. Students factor x\u00b3 \u2212 8x\u00b2 + 16x \u2192 "
        "x(x \u2212 4)\u00b2, then graph in Desmos and observe the graph "
        "TOUCHING the x-axis at x = 4 (not crossing). This is a phenomenon "
        "they have not seen before. They describe what they see in their "
        "own words \u2014 the teacher does NOT name multiplicity today. This "
        "is the planted seed for Day 3.",
    ])

    add_two_col(doc, [("\U0001F50D  Practice #13 / ANSWER KEY", P13_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 #13 DISCOVERY", [
        "Common stall: Factor x(x\u00b2 \u2212 8x + 16) and stop. Prompt: "
        "\u201cLook at the quadratic. Is it a perfect square?\u201d",
        "Common error: Write two factors (x \u2212 4)(x \u2212 4) but list "
        "x = 4 only once and say there are 3 zeros. Prompt: \u201cCount your "
        "factors. Count your distinct zero values. What\u2019s different?\u201d",
        "The moment that matters: Students graph in Desmos and say \u201cit "
        "touches but doesn\u2019t cross.\u201d Capture this on the board. "
        "DO NOT explain. Ask one follow-up: \u201cWhich factor made that "
        "happen, do you think?\u201d Hear their guesses. Say \u201cwe\u2019ll "
        "name it tomorrow.\u201d Leave it open.",
        "ELL support: \u201ctouches\u201d / \u201cbounces\u201d / "
        "\u201ckisses the axis\u201d are all valid descriptions today. "
        "Precision is tomorrow\u2019s job.",
    ])

    # Reverse engineering
    add_callout(doc, "[DOK 3] Strategic Thinking \u2014 Reverse Engineering", [
        "Students reverse the Day 1 process: given zeros and a point on the "
        "graph, construct the polynomial equation. This is DOK 3 because "
        "students must (1) translate zeros into factors (inverse of the Zero "
        "Product Property), (2) recognize that the factored form "
        "f(x) = a(x \u2212 r\u2081)(x \u2212 r\u2082)(x \u2212 r\u2083) has a "
        "hidden parameter a, (3) use a given point as a constraint to solve "
        "for a. Three representations coordinated: zeros \u2192 factors, "
        "factored form \u2192 point substitution, solved equation \u2192 "
        "final equation. No memorized procedure gets them there in one "
        "step.",
    ])

    add_two_col(doc, [("\U0001F527  Reverse Engineering / ANSWER KEY", REVERSE_KEY)])

    add_callout(doc, "\U0001F3AF  TEACHER MOVES \u2014 Reverse Engineering", [
        "Common stall: Students write f(x) = (x + 2)(x \u2212 1)(x \u2212 4) "
        "and don\u2019t include the leading coefficient a. Prompt: \u201cPlug "
        "in x = 0. What do you get? Is that \u22128?\u201d",
        "Common error: Sign flip on a zero. \u201cx = \u22122 is a zero\u201d "
        "becomes (x \u2212 2) instead of (x + 2). Prompt: \u201cSet your factor "
        "equal to zero. Does it give you x = \u22122?\u201d",
        "If time runs short: partners verbally justify their answer to each "
        "other \u2014 written CER can move to homework. Do NOT skip the "
        "justification conversation; that\u2019s where DOK 3 lives.",
        "Extension for fast finishers: \u201cWhat if the point had been "
        "(0, 8) instead of (0, \u22128)?\u201d (a = 1, so f(x) = (x + 2)(x \u2212 1)(x \u2212 4).)",
    ])

    # Exit ticket
    add_callout(doc, "[DOK 2] Verification \u2014 Exit Ticket", [
        "Savvas Practice #6. Students apply known verification strategies "
        "(substitute, test points, Desmos cross-check) to a general question "
        "about sketch correctness. DOK 2, not DOK 3: students are applying "
        "strategies they have, not constructing a novel argument. "
        "Appropriate for a 5-minute walk-out task.",
    ])

    add_callout(doc, "\U0001F4E4  EXIT TICKET \u2014 CER  [DOK 2]   (5 min)", [
        "\u201cIf you use zeros to sketch the graph of a polynomial function, "
        "how can you verify that your graph is correct?\u201d",
        "Students write Claim / Evidence / Reasoning on the student packet.",
    ])

    add_callout(doc, "\u2705  EXIT TICKET / ANSWER KEY", EXIT_KEY)

    # Closing
    add_callout(doc, "\U0001F4F7  WHAT TO COLLECT", [
        "1.  Exit ticket from each student (DOK 2 formative evidence).",
        "2.  Reverse engineering pages \u2014 scan or photo the page with the "
        "equation and justification (DOK 3 formative evidence).",
        "3.  Note which students showed the \u201cit touches!\u201d discovery "
        "in #13 \u2014 they are primed for Day 3 and can be asked to narrate "
        "their observation at the start of next class.",
    ])

    add_callout(doc, "\U0001F440  LOOK-FORS DURING WALKTHROUGH", [
        "[DOK 1] Blooket: Teacher monitoring dashboard? Using data "
        "diagnostically rather than just playing?",
        "[DOK 2] Sign flip & fluency: Students predicting BEFORE graphing? "
        "Teacher circulating with questions, not answers?",
        "[DOK 2\u20133] #13 discovery: Students articulating what they see in "
        "their own language? Teacher resisting the urge to name multiplicity?",
        "[DOK 3] Reverse engineering: Partners justifying their leading "
        "coefficient? Students referencing the point constraint by name?",
    ])

    add_callout(doc, "\U0001F30D  ELL SUPPORTS BUILT INTO THIS LESSON", [
        "\u2022  Sentence frame: \u201cThe zeros stay the same because ___. "
        "The graph changes because ___.\u201d",
        "\u2022  Predict-before-verify routine reduces reliance on spoken "
        "English \u2014 students commit in writing first.",
        "\u2022  \u201cTouches\u201d / \u201cbounces\u201d / \u201cturns\u201d "
        "accepted for #13 discovery. Academic term (multiplicity) deferred to Day 3.",
        "\u2022  No new vocabulary introduced today \u2014 deliberate "
        "language-load reduction after a week off.",
        "\u2022  Materials-light: no chart paper setup, no manipulatives, "
        "reduces logistical language for group transitions.",
        "\u2022  Think-Pair-Share before any public share; writing before speaking.",
    ])

    doc.save(path)


if __name__ == "__main__":
    build_student("Day_2_Student_Packet.docx")
    build_teacher("Day_2_Teacher_Packet.docx")
    print("Built Day_2_Student_Packet.docx and Day_2_Teacher_Packet.docx")
