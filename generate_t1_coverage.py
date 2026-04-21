"""Phase 2: T1 coverage-fill tag pass.

For each lesson in the T1 lesson list, enumerate untagged DOK>=2 items
(no 'role' field, no '-2' suffix) and produce tagging/{lesson}_t1_coverage.jsonl.

All items get role='explore-practice', lesson-inferred standards, empty
prereq_ids/rehearses/echoes, and skill_tokens from keyword matching.

New token proposals are logged to tagging/skill_tokens_new_from_t1.md.

Usage: python generate_t1_coverage.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REGISTRY = Path("questionbank/registry.jsonl")
TAGGING = Path("tagging")
NEW_TOKENS_FILE = TAGGING / "skill_tokens_new_from_t1.md"

LESSONS = ["3-5", "4-1", "4-3", "4-4", "4-5", "5-1", "5-4", "5-5", "6-3", "6-4", "6-5"]

# Standards per lesson — inferred from already-tagged items (see Phase 1 output)
# Using the primary standard(s) that cover practice items in each lesson
LESSON_STANDARDS: dict[str, list[str]] = {
    "3-5": ["A-APR.B.3", "F-IF.C.7c"],
    "4-1": ["A-CED.A.2", "F-IF.C.7d"],
    "4-3": ["A-APR.D.6", "A-APR.D.7"],
    "4-4": ["A-APR.D.7", "A-SSE.A.2"],
    "4-5": ["A-REI.A.2", "A-CED.A.1"],
    "5-1": ["N-RN.A.1", "N-RN.A.2"],
    "5-4": ["A-REI.A.2", "A-CED.A.4"],
    "5-5": ["F-BF.A.1b", "F-BF.A.1c"],
    "6-3": ["F-BF.B.5", "F-LE.A.4"],
    "6-4": ["F-IF.C.7e", "F-BF.B.3"],
    "6-5": ["F-LE.A.4", "F-BF.B.5"],
}

# ---------------------------------------------------------------------------
# Skill-token keyword matching
# Rules: (list_of_regex_patterns, token_name)
# First-pass: run all rules; collect all matches.
# ---------------------------------------------------------------------------

def _re(*patterns: str) -> re.Pattern:
    return re.compile("|".join(patterns), re.IGNORECASE)

# Each rule: (compiled_pattern, token)
TOKEN_RULES: list[tuple[re.Pattern, str]] = [
    # ---- Polynomial / zeros (3-5) -------------------------------------------
    (_re(r"\bzero", r"\broot", r"f\(x\)\s*=\s*0", r"solve.*poly"), "identify-zeros"),
    (_re(r"\bfactor(?:ing|ed|s)?\b", r"factor completely"), "factor-polynomial"),
    (_re(r"\bgroup(?:ing|ed)?\b.*factor", r"factor.*group"), "factor-by-grouping"),
    (_re(r"\bu[-\s]?sub", r"quadratic in form", r"\bx\^4\b.*quadratic", r"quadratic form"), "factor-quadratic-in-form"),
    (_re(r"\bmultiplicity\b", r"tangent.*x-axis", r"touch.*x-axis", r"cross.*x-axis", r"bounce"), "describe-multiplicity-behavior"),
    (_re(r"\bcomplex\s+zero", r"\bimaginary\s+zero", r"\bnon-real\s+zero"), "identify-complex-zeros"),
    (_re(r"\bconjugate\b"), "conjugate-pairs"),
    (_re(r"\bsynthetic\s+division\b", r"\blong\s+division\b", r"divide.*polynomial", r"remainder theorem", r"factor theorem"), "synthetic-or-long-division"),
    (_re(r"sketch.*graph", r"draw.*graph", r"graph.*polynomial"), "sketch-polynomial-graph"),
    (_re(r"\bsolve.*equation\b.*polynomial", r"polynomial.*equation"), "solve-polynomial-equation"),
    (_re(r"intersection", r"where.*meet", r"graphs.*meet"), "graph-intersection"),
    # ---- Inverse variation (4-1) --------------------------------------------
    (_re(r"inverse\s+variation", r"varies?\s+inversely", r"y\s*=\s*k/x"), "recognize-inverse-variation"),
    (_re(r"xy\s*=\s*k", r"constant.*product", r"product.*constant"), "test-constant-product"),
    (_re(r"\bsolve\s+for\s+k\b", r"\bfind\s+k\b", r"\bconstant\s+of\s+variation\b"), "solve-for-k"),
    (_re(r"inverse\s+square\s+variation", r"y\s*=\s*k/x\^2"), "recognize-inverse-square-variation"),
    (_re(r"\bmodel\b.*inverse\s+variation", r"inverse\s+variation.*\bmodel\b", r"physical.*inverse"), "model-inverse-variation-context"),
    (_re(r"evaluate.*inverse\s+variation", r"inverse\s+variation.*evaluate"), "evaluate-inverse-variation"),
    # ---- Rational functions (4-1) -------------------------------------------
    (_re(r"\bdomain\b.*restrict", r"restrict.*domain", r"undefined", r"denominator.*zero", r"excluded value"), "domain-restriction-rational"),
    (_re(r"\bvertical\s+asymptote", r"\bhorizontal\s+asymptote", r"\boblique\s+asymptote", r"\basymptote"), "identify-asymptotes"),
    (_re(r"reciprocal\s+function", r"f\(x\)\s*=\s*1/x", r"parent\s+function.*1/x"), "graph-reciprocal-function"),
    (_re(r"\bdomain\b.*range\b", r"\brange\b.*domain\b"), "state-domain-range"),
    (_re(r"translate|shift|transformation.*parent", r"parent.*transform"), "translate-parent-function"),
    (_re(r"\bintercept", r"x-intercept", r"y-intercept"), "find-intercepts"),
    (_re(r"write.*equation.*graph", r"equation.*from.*graph"), "write-equation-from-graph"),
    # ---- Rational expressions (4-3, 4-4) ------------------------------------
    (_re(r"simplif.*rational\s+expression", r"simplif.*fraction.*variable"), "simplify-rational-expression"),
    (_re(r"equivalent.*rational\s+expression", r"rewrite.*rational\s+expression"), "rewrite-rational-expression"),
    (_re(r"\bmultiply.*rational\s+expression", r"rational.*multiply"), "multiply-rational-expressions"),
    (_re(r"\bdivide.*rational\s+expression", r"rational.*divid"), "divide-rational-expressions"),
    (_re(r"\badd.*rational\s+expression", r"sum.*rational"), "add-rational-expressions"),
    (_re(r"\bsubtract.*rational\s+expression", r"difference.*rational"), "subtract-rational-expressions"),
    (_re(r"\blcd\b", r"least\s+common\s+denom", r"common\s+denom"), "find-lcd"),
    (_re(r"complex\s+fraction", r"fraction.*fraction", r"compound\s+fraction"), "simplify-complex-fraction"),
    (_re(r"closure", r"\bclosed\s+under\b"), "closure-argument"),
    (_re(r"ratio.*surface", r"surface.*area.*volume", r"SA/V", r"ratio.*model"), "ratio-modeling"),
    (_re(r"area.*model", r"model.*area.*rational"), "area-modeling"),
    (_re(r"analogize.*fraction", r"like\s+fraction", r"similar.*numeric\s+fraction"), "analogize-to-numeric-fractions"),
    # ---- Rational equations (4-5) -------------------------------------------
    (_re(r"clear.*denominator", r"multiply.*both.*LCD", r"LCD.*both.*sides"), "clear-denominators"),
    (_re(r"\bsolve.*rational\s+equation", r"rational\s+equation.*solve"), "solve-rational-equation"),
    (_re(r"\bextraneous\b", r"check.*solution", r"verify.*solution"), "identify-extraneous-solution"),
    (_re(r"rate.*problem", r"work.*rate", r"travel.*rate"), "model-rate-context"),
    (_re(r"mixture", r"concentration"), "model-mixture-context"),
    # ---- Radicals / rational exponents (5-1) --------------------------------
    (_re(r"nth\s+root", r"\bindex\b.*radical", r"\bradical.*index\b"), "evaluate-nth-root"),
    (_re(r"how many.*real.*root", r"real.*root.*count", r"number of.*root"), "count-real-nth-roots"),
    (_re(r"rational\s+exponent.*radical", r"radical.*rational\s+exponent", r"convert.*radical.*exponent"), "convert-radical-to-rational-exp"),
    (_re(r"rational\s+exponent.*convert", r"rewrite.*rational\s+exp.*radical"), "convert-rational-exp-to-radical"),
    (_re(r"evaluate.*rational\s+exponent", r"rational\s+exponent.*evaluate", r"a\^\{?[mp]/[nq]\}?"), "evaluate-rational-exponent"),
    (_re(r"simplif.*\bvariable.*radical", r"simplif.*\bradical.*variable", r"simplif.*nth.*root.*var"), "simplify-nth-root-with-variables"),
    (_re(r"inverse.*square\s+function", r"y\s*=\s*x\^2.*inverse"), "invert-square-function"),
    (_re(r"nth\s+root.*inverse", r"inverse.*nth\s+root"), "recognize-nth-root-as-inverse"),
    (_re(r"rationalize.*denom", r"denom.*rationalize"), "rationalize-denominator"),
    (_re(r"volume.*dimension", r"dimension.*from.*volume", r"radius.*volume", r"height.*volume"), "extract-dimension-from-volume"),
    (_re(r"build.*equation.*constraint", r"translate.*constraint.*equation"), "build-equation-from-constraint"),
    (_re(r"interpret.*answer.*context", r"context.*answer", r"units.*check"), "interpret-answer-in-context"),
    # ---- Radical equations (5-4) --------------------------------------------
    (_re(r"radical\s+equation", r"solve.*radical", r"square.*both.*sides", r"\^\{1/[234]\}", r"\^\{2/3\}", r"\^\{3/2\}"), "solve-radical-equation"),
    (_re(r"isolate.*radical", r"radical.*isolate"), "isolate-radical"),
    (_re(r"rational\s+exponent.*equation", r"equation.*rational\s+exponent"), "solve-rational-exponent-equation"),
    (_re(r"rewrite.*formula", r"formula.*rewrite", r"solve.*for.*variable.*formula"), "rewrite-formula"),
    (_re(r"solve.*for\s+\w+", r"isolate\s+\w+"), "solve-for-variable"),
    # ---- Function operations (5-5) ------------------------------------------
    (_re(r"add.*functions?", r"subtract.*functions?", r"f\s*\+\s*g", r"f\s*-\s*g"), "add-subtract-functions"),
    (_re(r"compos.*function", r"f\s*\(\s*g\s*\("), "compose-functions"),
    (_re(r"f\(g\([0-9]", r"evaluate.*compos", r"compos.*evaluat"), "evaluate-composition"),
    (_re(r"inverse\s+function", r"f\^?\{?-1\}?"), "find-inverse-function"),
    (_re(r"inverse\s+pair", r"inverse.*relationship.*function"), "recognize-inverse-pair"),
    (_re(r"y\s*=\s*x.*reflect", r"reflect.*y\s*=\s*x"), "compare-graphs-y-equals-x-reflection"),
    (_re(r"discount.*compos", r"compos.*discount", r"successive.*discount"), "model-discount-context"),
    (_re(r"order.*compos", r"application.*order", r"which.*first"), "decide-application-order"),
    # ---- Logs / exponents (6-3, 6-4, 6-5) ----------------------------------
    (_re(r"\blog_?\s*\w*\s*\(", r"\\\blog\b", r"logarithm"), "evaluate-log"),
    (_re(r"log.*negative", r"when.*log.*<\s*0", r"log.*sign"), "reason-about-log-sign"),
    (_re(r"common\s+log", r"natural\s+log", r"\bln\b", r"base\s+10\s+log", r"base\s+e"), "log-vocabulary"),
    (_re(r"ln\s+vs\s+log", r"distinguish.*ln.*log", r"ln.*common"), "distinguish-common-natural"),
    (_re(r"log.*inverse.*exp", r"exp.*inverse.*log"), "recognize-log-as-inverse-exponential"),
    (_re(r"graph.*log", r"log.*graph"), "graph-log-function"),
    (_re(r"end\s+behavior", r"as.*x.*approach", r"x.*→.*∞", r"x\s*->\s*infty", r"x\s*->\s*0"), "describe-end-behavior"),
    (_re(r"translation.*log", r"shift.*log", r"describe.*translation"), "describe-translation"),
    (_re(r"estimate.*log.*graph", r"log.*estimate.*graph"), "estimate-log-from-graph"),
    (_re(r"product.*prop.*log", r"log.*product.*prop", r"log\s*\(\s*[A-Za-z]+\s*[*·]\s*[A-Za-z]+"), "product-property-log"),
    (_re(r"quotient.*prop.*log", r"log.*quotient.*prop"), "quotient-property-log"),
    (_re(r"power.*prop.*log", r"log.*power.*prop"), "power-property-log"),
    (_re(r"expand.*log", r"log.*expand"), "expand-log-expression"),
    (_re(r"condense.*log", r"log.*condense", r"single\s+log", r"write.*single.*log"), "condense-log-expression"),
    (_re(r"change.of.base", r"change.*base.*formula"), "change-of-base"),
    (_re(r"solve.*exponential\s+equation", r"exponential\s+equation.*solve", r"a\^x\s*=\s*[0-9]", r"[0-9]+\^\{?-?[0-9]+\}?\s*="), "solve-exponential-equation"),
    (_re(r"prove.*log.*property", r"log.*property.*prove", r"exponent.*law.*prove"), "prove-via-exponent-laws"),
    (_re(r"generalize.*numeric", r"general\s+form.*specific", r"symbolic.*general"), "generalize-numerical-result"),
    (_re(r"context.*log", r"Richter", r"\bpH\b", r"\bdecibel\b", r"Seismic"), "interpret-log-in-context"),
    (_re(r"perfect\s+power.*log", r"log.*simplif.*base", r"log_\d+\s+\d+"), "numeric-simplification-in-log"),
    (_re(r"error\s+analysis.*log", r"log.*error\s+analysis"), "error-analysis-log"),
    (_re(r"continuous.*compound", r"A\s*=\s*Pe", r"Pe\^"), "model-continuous-compound"),
    (_re(r"compare.*invest", r"two.*accounts"), "compare-investments"),
    (_re(r"half.life", r"decay\s+model", r"depreciate"), "model-decay"),
    (_re(r"solve.*for\s+t\b", r"extract.*time"), "extract-time-from-model"),
    # ---- Generic -----------------------------------------------------------
    (_re(r"error\s+analysis", r"Error Analysis"), "error-analysis-rational"),  # fallback; lesson-specific ones override
    (_re(r"construct\s+argument", r"justify", r"\bproof\b", r"prove"), "construct-argument"),
    (_re(r"equivalent\s+expression", r"same\s+value.*expression"), "recognize-equivalent-expressions"),
    (_re(r"interpret.*root.*context", r"root.*mean.*context"), "interpret-root-in-context"),
    (_re(r"SAT", r"ACT", r"standardized\s+test"), "distractor-analysis"),
    (_re(r"combine\s+like\s+terms", r"collect\s+like\s+terms"), "combine-like-terms"),
]

# Lesson-specific error-analysis token overrides
LESSON_ERROR_TOKEN: dict[str, str] = {
    "3-5": "error-analysis-rational",
    "4-1": "error-analysis-rational",
    "4-3": "error-analysis-rational",
    "4-4": "error-analysis-rational",
    "4-5": "error-analysis-rational",
    "5-1": "error-analysis-radical",
    "5-4": "error-analysis-radical",
    "5-5": "error-analysis-rational",
    "6-3": "error-analysis-log",
    "6-4": "error-analysis-log",
    "6-5": "error-analysis-log",
}

# All known tokens (to detect when we'd be adding a new one)
KNOWN_TOKENS = {
    "evaluate-nth-root", "count-real-nth-roots", "convert-radical-to-rational-exp",
    "convert-rational-exp-to-radical", "evaluate-rational-exponent", "simplify-nth-root-with-variables",
    "invert-square-function", "recognize-nth-root-as-inverse", "recognize-equivalent-expressions",
    "distractor-analysis", "build-equation-from-constraint", "extract-dimension-from-volume",
    "rationalize-denominator", "interpret-answer-in-context",
    "product-property-log", "quotient-property-log", "power-property-log",
    "expand-log-expression", "condense-log-expression", "change-of-base",
    "solve-exponential-equation", "prove-via-exponent-laws", "generalize-numerical-result",
    "interpret-log-in-context", "numeric-simplification-in-log", "error-analysis-log",
    "identify-zeros", "factor-polynomial", "factor-by-grouping", "factor-quadratic-in-form",
    "describe-multiplicity-behavior", "identify-complex-zeros", "conjugate-pairs",
    "synthetic-or-long-division", "sketch-polynomial-graph", "solve-polynomial-equation",
    "graph-intersection",
    "recognize-inverse-variation", "test-constant-product", "solve-for-k",
    "evaluate-inverse-variation", "recognize-inverse-square-variation",
    "model-inverse-variation-context", "domain-restriction-rational", "state-domain-restriction",
    "graph-reciprocal-function", "identify-asymptotes", "state-domain-range",
    "translate-parent-function", "find-intercepts", "write-equation-from-graph",
    "rewrite-rational-expression", "simplify-rational-expression",
    "multiply-rational-expressions", "divide-rational-expressions", "reciprocal-then-multiply",
    "add-rational-expressions", "subtract-rational-expressions", "find-lcd",
    "simplify-complex-fraction", "clear-denominators", "solve-rational-equation",
    "identify-extraneous-solution", "error-analysis-rational", "ratio-modeling",
    "area-modeling", "closure-argument", "model-rate-context", "model-mixture-context",
    "analogize-to-numeric-fractions",
    "solve-radical-equation", "isolate-radical", "isolate-before-inverting",
    "raise-to-reciprocal-power", "solve-rational-exponent-equation",
    "error-analysis-radical", "rewrite-formula", "solve-for-variable",
    "add-subtract-functions", "compose-functions", "evaluate-composition",
    "combine-like-terms", "find-inverse-function", "recognize-inverse-pair",
    "compare-graphs-y-equals-x-reflection", "decide-application-order",
    "model-discount-context",
    "evaluate-log", "reason-about-log-sign", "log-vocabulary", "distinguish-common-natural",
    "recognize-log-as-inverse-exponential", "graph-log-function", "describe-end-behavior",
    "describe-translation", "estimate-log-from-graph", "model-continuous-compound",
    "compare-investments", "model-decay", "extract-time-from-model", "model-physical-context",
    "read-given-formula", "read-graph-values",
    "construct-argument", "interpret-root-in-context", "model-physical-constant",
    "reason-about-operation-order",
}


def infer_tokens(prompt: str, lesson: str) -> tuple[list[str], list[str]]:
    """Return (matched_tokens, unknown_descriptions)."""
    matched: list[str] = []
    text = prompt or ""

    # Handle error-analysis specially
    if re.search(r"error\s+analysis", text, re.IGNORECASE):
        tok = LESSON_ERROR_TOKEN.get(lesson, "error-analysis-rational")
        if tok not in matched:
            matched.append(tok)
        skip_generic_error = True
    else:
        skip_generic_error = False

    for pattern, token in TOKEN_RULES:
        if skip_generic_error and token == "error-analysis-rational":
            continue
        if pattern.search(text):
            if token not in matched:
                matched.append(token)

    # Lesson-specific fallback rules for items with bare-expression prompts
    if not matched:
        if lesson in ("5-1",):
            # Bare radical: \sqrt[n]{...} or √(...)
            if re.search(r"\\\\?sqrt|√|\\\\[a-z]+\{[^}]+\}", text):
                # If it has variables, it's simplify-nth-root-with-variables
                if re.search(r"[a-wyzA-Z]\^|[a-wyzA-Z]\{", text):
                    matched.append("simplify-nth-root-with-variables")
                else:
                    matched.append("evaluate-nth-root")
            # Bare rational exponent: a^{m/n} or a^(m/n)
            elif re.search(r"\^\{?\(?[0-9]+\)?/\(?[0-9]+", text):
                if re.search(r"[a-wyzA-Z]\^|[a-wyzA-Z]\{", text):
                    matched.append("convert-radical-to-rational-exp")
                else:
                    matched.append("evaluate-rational-exponent")
            elif re.search(r"solve|x\^[234]|= ?[0-9]", text, re.IGNORECASE):
                matched.append("solve-rational-exponent-equation")
            elif re.search(r"volume|cube|cylinder|globe|ball|container|snow", text, re.IGNORECASE):
                matched.append("extract-dimension-from-volume")
                matched.append("interpret-answer-in-context")
            elif re.search(r"triangle|legs|hypotenuse|right.*tri", text, re.IGNORECASE):
                matched.append("evaluate-nth-root")
            elif re.search(r"bank|interest|earn|annually", text, re.IGNORECASE):
                matched.append("solve-rational-exponent-equation")
        if lesson in ("5-4",):
            # Bare radical equation: contains √ or \sqrt and = sign
            if re.search(r"(\\\\?sqrt|√|3√|[0-9]√).*=|=.*(\\\\?sqrt|√)", text):
                matched.append("solve-radical-equation")
            elif re.search(r"solve|equation|\^{[23]/[234]}", text, re.IGNORECASE):
                matched.append("solve-radical-equation")
            elif re.search(r"formula|variable.*formula|rewrite|BSA", text, re.IGNORECASE):
                matched.append("rewrite-formula")
            elif re.search(r"inequalit|dose|medicine|mass|BSA", text, re.IGNORECASE):
                matched.append("solve-radical-equation")
                matched.append("interpret-answer-in-context")
        if lesson in ("4-4",):
            # Bare rational expression with +/- operators = add/subtract
            if re.search(r"x\^2\s*-\s*y\^2|x\^2\s*-\s*2xy|LCM|lcm|5x\^3y|15x\^2", text):
                matched.append("find-lcd")
            elif re.search(r"simplest\s+form|sum|perimeter|numerator|denominator", text, re.IGNORECASE):
                matched.append("add-rational-expressions")
            # Bare fraction subtraction: e.g. (3x)/(4y^2) - (y)/(10x)
            elif re.search(r"\([^)]+\)/\([^)]+\)\s*[-+]", text) or re.search(r"\)\s*[-+]\s*\(", text):
                matched.append("add-rational-expressions")
            if re.search(r"slope|line.*through|points? shown", text, re.IGNORECASE):
                matched.append("ratio-modeling")
            if re.search(r"rate|miles|drive|travel|speed|round.?trip", text, re.IGNORECASE):
                matched.append("model-rate-context")
            if re.search(r"lens|focal|optic", text, re.IGNORECASE):
                matched.append("solve-rational-equation")
                matched.append("ratio-modeling")
        if lesson in ("4-5",):
            if re.search(r"solve|equation|=\s*[0-9]|\([^)]+\)/\([^)]+\)", text, re.IGNORECASE):
                matched.append("solve-rational-equation")
            if re.search(r"shed|together|build|job|work.*rate|rate.*work|pipe|pool|fill|plant|garden|tomato|together", text, re.IGNORECASE):
                matched.append("model-rate-context")
            if re.search(r"beach|jet.?ski|miles|drive|speed", text, re.IGNORECASE):
                matched.append("model-rate-context")
            if re.search(r"baseball|hit|batting|season|proportion", text, re.IGNORECASE):
                matched.append("ratio-modeling")
        if lesson in ("5-5",):
            if re.search(r"f.*g|function|domain|rule|compose", text, re.IGNORECASE):
                matched.append("compose-functions")
        if lesson in ("6-3",):
            if re.search(r"^[0-9a-zA-Z^{}\(\).]+\s*[=≈]\s*[0-9\(]", text):
                # Bare exponential equation like 2^{-6} = 1/64
                matched.append("evaluate-log")
            elif re.search(r"e\^|Pe\^|compounded.*continuous|continuous.*compound", text, re.IGNORECASE):
                matched.append("model-continuous-compound")
            elif re.search(r"log|logarithm|solve|equation", text, re.IGNORECASE):
                matched.append("evaluate-log")
        if lesson in ("6-4",):
            if re.search(r"graph|log|function|key feature|domain|range|altitude|pressure|air", text, re.IGNORECASE):
                matched.append("graph-log-function")
        if lesson in ("3-5",):
            if re.search(r"inequalit|x\^3|x\^2|polynomial|zero|root", text, re.IGNORECASE):
                matched.append("identify-zeros")
        if lesson in ("4-1",):
            if re.search(r"inverse|variation|k|rectangle|sketch|graph", text, re.IGNORECASE):
                matched.append("recognize-inverse-variation")
        if lesson in ("4-3",):
            if re.search(r"rational|simplif|express|equivalent|domain|restrict|x\\s*\\\\ne", text, re.IGNORECASE):
                matched.append("simplify-rational-expression")
            if re.search(r"model|carnival|game|beanbag|design|math", text, re.IGNORECASE):
                matched.append("ratio-modeling")
            if re.search(r"restriction|x\\\\ne|x \\\\ne|domain.*restrict|restrict.*domain|necessary.*restrict", text, re.IGNORECASE):
                matched.append("domain-restriction-rational")

    # Remove duplicates while preserving order
    seen: set[str] = set()
    deduped = []
    for t in matched:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    return deduped, []


def item_notes(row: dict, tokens: list[str]) -> str:
    """Generate a brief notes line."""
    prompt = (row.get("prompt") or "").strip()[:80].replace("\n", " ")
    tok_summary = ", ".join(tokens[:3]) if tokens else "no tokens matched"
    return f"T1 pool: {prompt!r} → [{tok_summary}]"


def load_registry() -> list[dict]:
    return [json.loads(line) for line in REGISTRY.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    registry = load_registry()
    TAGGING.mkdir(exist_ok=True)

    new_token_proposals: list[str] = []
    total_tagged = 0

    for lesson in LESSONS:
        standards = LESSON_STANDARDS[lesson]

        # Candidates: lesson match, dok>=2, no role, no -2 suffix
        candidates = [
            r for r in registry
            if r.get("lesson") == lesson
            and (r.get("dok") or 0) >= 2
            and not r.get("role")
            and not r["id"].endswith("-2")
        ]

        out_path = TAGGING / f"{lesson}_t1_coverage.jsonl"
        rows_out: list[str] = []
        no_token_ids: list[str] = []

        for row in candidates:
            rid = row["id"]
            prompt = row.get("prompt") or ""
            tokens, _ = infer_tokens(prompt, lesson)

            if not tokens:
                no_token_ids.append(rid)
                # Log proposal
                new_token_proposals.append(
                    f"- `{rid}` (lesson {lesson}, dok={row.get('dok')}): {prompt[:120]!r}")

            tag_row = {
                "id": rid,
                "role": "explore-practice",
                "standards": standards,
                "prereq_ids": [],
                "rehearses": [],
                "echoes": [],
                "skill_tokens": tokens,
                "notes": item_notes(row, tokens),
            }
            rows_out.append(json.dumps(tag_row, ensure_ascii=False))

        out_path.write_text("\n".join(rows_out) + "\n" if rows_out else "\n", encoding="utf-8")
        total_tagged += len(candidates)
        no_tok = len(no_token_ids)
        print(f"{lesson}: {len(candidates)} items → {out_path.name}  (no tokens: {no_tok})")

    print(f"\nTotal items written: {total_tagged}")

    # Write new token proposals
    if new_token_proposals:
        lines = ["# New skill-token proposals from T1 pass\n",
                 "Items that matched NO existing token. Review and either find the best existing token",
                 "or add a new token to skill_tokens.md.\n",
                 ""]
        lines.extend(new_token_proposals)
        NEW_TOKENS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n{len(new_token_proposals)} items with no token match → {NEW_TOKENS_FILE}")
    else:
        print("\nNo unmatched items — no new token proposals.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
