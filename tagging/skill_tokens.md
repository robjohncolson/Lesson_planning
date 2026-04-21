# Skill tokens — glossary

Atomic moves. One token = one thing a student either can or cannot do, independent of topic/lesson wrapper. Kebab-case. Append as new ones emerge during the dry-run; never rename silently (breaks the DAG).

## Seeded from Lesson 5-1 pilot

| Token | Definition |
|---|---|
| `evaluate-nth-root` | Given a numeric radicand and integer index, produce the real root(s). |
| `count-real-nth-roots` | State how many real nth roots a given number has (rule by parity of index + sign of radicand). |
| `convert-radical-to-rational-exp` | Rewrite √[n]{x^m} as x^(m/n). |
| `convert-rational-exp-to-radical` | Rewrite x^(m/n) as √[n]{x^m}. |
| `evaluate-rational-exponent` | Compute a^(m/n) for numeric a, using either order. |
| `simplify-nth-root-with-variables` | Pull perfect-nth-power factors out of √[n]{...} when variables are present. |
| `invert-square-function` | Reverse y = x² to find x given y. Precursor to nth-root-as-inverse. |
| `recognize-nth-root-as-inverse` | See √[n]{} as the undo of x^n. |
| `recognize-equivalent-expressions` | Decide whether two notations name the same value. |
| `distractor-analysis` | Explain why a specific wrong answer is tempting. |
| `build-equation-from-constraint` | Translate a verbal geometric/physical constraint into an equation. |
| `extract-dimension-from-volume` | Solve V = f(dim) for the dimension — typically requires nth-root or rational exponent. |
| `rationalize-denominator` | Clear a radical from a denominator. |
| `interpret-answer-in-context` | Report the numeric answer with units and constraint check. |

## Added from Lesson 6-5 pilot

| Token | Definition |
|---|---|
| `product-property-log` | Apply log(AB) = log A + log B (either direction). |
| `quotient-property-log` | Apply log(A/B) = log A − log B (either direction). |
| `power-property-log` | Apply log(A^n) = n·log A (either direction). |
| `expand-log-expression` | Rewrite a single log of a product/quotient/power as a sum/difference/scalar-multiple of logs. |
| `condense-log-expression` | Reverse: combine a sum/difference/scalar-multiple of logs into a single log. |
| `change-of-base` | Rewrite log_b(x) as ln x / ln b (or log_k x / log_k b). |
| `solve-exponential-equation` | Solve a^x = c by taking log of both sides (and change-of-base if needed). |
| `prove-via-exponent-laws` | Establish a log property by invoking the defining exponent relationship + exponent arithmetic. Algebraic-proof flavor of DOK-3. |
| `generalize-numerical-result` | Given a specific numeric instance, produce the symbolic general form. |
| `interpret-log-in-context` | Apply a log-scale physical formula (Richter, pH, decibel) and report the contextual meaning. |
| `numeric-simplification-in-log` | Recognize that a log of a perfect power simplifies (e.g., log_3 27 = 3). |
| `error-analysis-log` | Identify and correct a misapplication of a log property. |

## Added from batch pass (3-5, 4-1, 4-3, 4-4, 4-5, 5-4, 5-5, 6-3, 6-4)

### Polynomials / zeros (Unit 3)
| Token | Definition |
|---|---|
| `identify-zeros` | Given a polynomial, list its zeros. |
| `factor-polynomial` | Factor a polynomial expression. |
| `factor-by-grouping` | Group and factor 4-term polynomials. |
| `factor-quadratic-in-form` | Recognize and factor u-substitution quadratics (e.g. quartic as quadratic in x²). |
| `describe-multiplicity-behavior` | State tangent vs cross at each zero by multiplicity parity. |
| `identify-complex-zeros` | Find non-real zeros (typically via factoring a quadratic factor). |
| `conjugate-pairs` | Apply the theorem: complex zeros of real-coefficient polynomials come in conjugate pairs. |
| `synthetic-or-long-division` | Divide a polynomial by a linear factor to reduce degree. |
| `sketch-polynomial-graph` | Draw a polynomial's graph from its factored form. |
| `solve-polynomial-equation` | Solve p(x) = q(x) by equating and factoring. |
| `graph-intersection` | Find where two graphs meet (algebraically or visually). |

### Rational functions & expressions (Unit 4)
| Token | Definition |
|---|---|
| `recognize-inverse-variation` | Decide whether a table/graph fits y = k/x. |
| `test-constant-product` | Compute xy for each row of a table to test inverse variation. |
| `solve-for-k` | Find the constant of variation from a single data point. |
| `evaluate-inverse-variation` | Given k and one variable, find the other. |
| `recognize-inverse-square-variation` | Decide whether y = k/x² is the model. |
| `model-inverse-variation-context` | Translate a physical scenario into an inverse-variation equation. |
| `domain-restriction-rational` | State forbidden inputs (zeros of the denominator). |
| `state-domain-restriction` | Alias for the above when attached to an expression, not a function. |
| `graph-reciprocal-function` | Draw y = 1/x or a translation of it. |
| `identify-asymptotes` | State vertical and horizontal asymptotes of a rational function. |
| `state-domain-range` | Give domain and range of a function. |
| `translate-parent-function` | Apply horizontal/vertical shifts to a parent function. |
| `find-intercepts` | Find x- and y-intercepts. |
| `write-equation-from-graph` | Given a transformed parent-function graph, write its equation. |
| `rewrite-rational-expression` | Produce an equivalent rational expression with stated domain. |
| `simplify-rational-expression` | Cancel common factors of numerator and denominator. |
| `multiply-rational-expressions` | Multiply two or more rational expressions, then simplify. |
| `divide-rational-expressions` | Multiply by reciprocal, then simplify. |
| `reciprocal-then-multiply` | The micro-move: flip the divisor. |
| `add-rational-expressions` | Find LCD, rewrite, add numerators. |
| `subtract-rational-expressions` | Same as add, watching signs. |
| `find-lcd` | Compute least common denominator of rational expressions. |
| `simplify-complex-fraction` | Resolve a fraction-of-fractions. |
| `clear-denominators` | Multiply both sides of an equation by the LCD. |
| `solve-rational-equation` | Solve an equation with rational expressions. |
| `identify-extraneous-solution` | After solving, check for solutions that violate domain. |
| `error-analysis-rational` | Identify a mistake in a rational-expression manipulation. |
| `ratio-modeling` | Express a physical ratio (SA/V, resistance, etc.) as a rational expression. |
| `area-modeling` | Use rational expressions to model area given dimensions. |
| `closure-argument` | Justify that a set of objects is closed under an operation. |
| `model-rate-context` | Translate a rate problem (work, travel) into rational equations. |
| `model-mixture-context` | Translate a mixture/concentration problem. |
| `analogize-to-numeric-fractions` | Connect rational-expression ops to fraction arithmetic. |

### Radicals & rational exponents (Unit 5)
| Token | Definition |
|---|---|
| `solve-radical-equation` | Isolate radical, raise to inverse power. |
| `isolate-radical` | Move everything off the radical side. |
| `isolate-before-inverting` | Generalize: isolate the expression before applying the inverse op. |
| `raise-to-reciprocal-power` | Undo a rational exponent. |
| `solve-rational-exponent-equation` | Solve (stuff)^(m/n) = c. |
| `error-analysis-radical` | Identify a radical-manipulation mistake. |
| `rewrite-formula` | Solve a physical-formula for a different variable. |
| `solve-for-variable` | Generic algebraic-rearrangement move. |

### Functions (Unit 5 continued)
| Token | Definition |
|---|---|
| `add-subtract-functions` | Compute f+g, f−g as expressions. |
| `compose-functions` | Compute f∘g as an expression. |
| `evaluate-composition` | Compute f(g(a)) for numeric a. |
| `combine-like-terms` | The low-level move. |
| `find-inverse-function` | Produce f⁻¹ algebraically. |
| `recognize-inverse-pair` | Given two functions/graphs, decide inverse relationship. |
| `compare-graphs-y-equals-x-reflection` | Use the y=x reflection test for inverses. |
| `decide-application-order` | In compositions/modeling, choose the order that matches the context. |
| `model-discount-context` | Translate sequential-discount scenarios to composed functions. |

### Exponents, logs, inverses (Unit 6)
| Token | Definition |
|---|---|
| `evaluate-log` | Compute log_b c for standard bases. |
| `reason-about-log-sign` | Decide when log_b x < 0 etc., from monotonicity. |
| `log-vocabulary` | Distinguish common (base 10), natural (base e), general log. |
| `distinguish-common-natural` | Specifically: ln vs log. |
| `recognize-log-as-inverse-exponential` | Treat y=log_b x and y=b^x as inverses. |
| `graph-log-function` | Draw y=log_b x or transformation. |
| `describe-end-behavior` | State behavior as x→∞ and x→0⁺ (log) or x→−∞ and x→∞ (exp). |
| `describe-translation` | Name the shift of a parent graph. |
| `estimate-log-from-graph` | Read log value from an exponential graph. |
| `model-continuous-compound` | Use A = Pe^(rt). |
| `compare-investments` | Contrast two continuous-compound accounts. |
| `model-decay` | Use y = C(r)^(t/h) for half-life. |
| `extract-time-from-model` | Solve a model-equation for t. |
| `model-physical-context` | General: translate a physics scenario to an equation. |
| `read-given-formula` | Apply a formula supplied in the problem. |
| `read-graph-values` | Pull numeric values off a provided graph. |

### Generic / cross-cutting
| Token | Definition |
|---|---|
| `construct-argument` | Produce a written justification. |
| `recognize-equivalent-expressions` | Decide whether two notations name the same value. |
| `interpret-root-in-context` | Report what a solution means for the scenario. |
| `interpret-answer-in-context` | General version of the above. |
| `model-physical-constant` | Recognize formulas that set a physical constant by constraint. |
| `reason-about-operation-order` | Notice commutativity/associativity violations in applied settings. |

## Rules

- **Don't create a token for "do the whole DOK-3 item."** Tokens are atomic; DOK-3 items are compositions of tokens.
- **Prefer verb-object form** (`extract-dimension-from-volume`, not `volume-dimension`).
- **If two tokens feel equivalent, merge them** — register the merge here with the chosen name + the abandoned synonym.
