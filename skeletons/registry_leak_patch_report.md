# Registry answer-macro repair

All 11 patches were run through `qb_patch_row.py --from <patch.json> --dry-run` before this report was written and before applying any changes. Prompt excerpts below show the first 200 and last 120 characters (overlap is intentional for short prompts). Notes are shown in full. JSON string escaping preserves whitespace and LaTeX exactly.

Scope: removal of answer/TE macro blocks; worked-example prose outside those blocks is preserved.

## 1-1-savvas-example-1-lesson-1-1

Before:

```json
{
  "prompt_first_200": "Understand Domain and Range\n\nA. What are the domain and range of the function defined by (y=x^2-3)?\n\nThe set of all possible inputs for a relation is called the domain.\n\nThe domain of this function is",
  "prompt_last_120": "y\\mid y≥-3\\}); [-3,∞). B. (f(x)=400x); domain: (\\{x\\mid0≤ x≤20\\}), [0,20]; range: (\\{y\\mid0≤ y≤8{,}000\\}), [0,8{,}000].}",
  "notes": "IMAGE PLACEHOLDER [photo]: Airtanker dropping water over a forest fire, with labels ``Rate: 400 gals per second'' and ``8,000 gals. in the tank.''"
}
```

After:

```json
{
  "prompt_first_200": "Understand Domain and Range\n\nA. What are the domain and range of the function defined by (y=x^2-3)?\n\nThe set of all possible inputs for a relation is called the domain.\n\nThe domain of this function is",
  "prompt_last_120": "egative number of gallons, and its maximum capacity is 8,000 gal.\n\nThe range is (\\{y\\mid0≤ y≤8{,}000\\}), or [0,8{,}000].",
  "notes": "Answer key (from source): A. Domain: (\\{x\\mid x is a real number\\}); (-∞,∞). Range: (\\{y\\mid y≥-3\\}); [-3,∞). B. (f(x)=400x); domain: (\\{x\\mid0≤ x≤20\\}), [0,20]; range: (\\{y\\mid0≤ y≤8{,}000\\}), [0,8{,}000]. · IMAGE PLACEHOLDER [photo]: Airtanker dropping water over a forest fire, with labels ``Rate: 400 gals per second'' and ``8,000 gals. in the tank.''"
}
```

## 4-3-ex-1

Before:

```json
{
  "prompt_first_200": "Write Equivalent Rational Expressions\n\nWrite an expression that is equivalent to (x+3)/(x+9). For what domain are the expressions equivalent?\n\nYou can multiply by factors of 1 in any form 1 to write e",
  "prompt_last_120": "real numbers where x\\ne 0,6, or -9\\}.\n\n\\answer{(x^3-3x^2-18x)/(x^3+3x^2-54x) over the domain \\{x \\mid x\\ne 0,6, or -9\\}}",
  "notes": "T1 pool: 'Write Equivalent Rational Expressions  Write an expression that is equivalent to' → [factor-polynomial, domain-restriction-rational, rewrite-rational-expression]"
}
```

After:

```json
{
  "prompt_first_200": "Write Equivalent Rational Expressions\n\nWrite an expression that is equivalent to (x+3)/(x+9). For what domain are the expressions equivalent?\n\nYou can multiply by factors of 1 in any form 1 to write e",
  "prompt_last_120": "/(x+9) is equivalent to (x^3-3x^2-18x)/(x^3+3x^2-54x) over the domain \\{x \\mid all real numbers where x\\ne 0,6, or -9\\}.",
  "notes": "Answer key (from source): (x^3-3x^2-18x)/(x^3+3x^2-54x) over the domain \\{x \\mid x\\ne 0,6, or -9\\} · T1 pool: 'Write Equivalent Rational Expressions  Write an expression that is equivalent to' → [factor-polynomial, domain-restriction-rational, rewrite-rational-expression]"
}
```

## 4-3-savvas-q11

Before:

```json
{
  "prompt_first_200": "Reason Explain why (4x^2-7)/(4x^2-7)=1 is a valid identity under the domain of all real numbers except ±\\frac{√(7)}{2}.\n\\answer{Using the difference of two squares formula, (4x^2-7)/(4x^2-7)=\\frac{(2x",
  "prompt_last_120": " divide to 1, so (4x^2-7)/(4x^2-7)=1 over all elements of the domain, which is all real numbers except ±\\frac{√(7)}{2}.}",
  "notes": "T1 pool: 'Reason Explain why (4x^2-7)/(4x^2-7)=1 is a valid identity under the domain of a' → [factor-polynomial, distractor-analysis]"
}
```

After:

```json
{
  "prompt_first_200": "Reason Explain why (4x^2-7)/(4x^2-7)=1 is a valid identity under the domain of all real numbers except ±\\frac{√(7)}{2}.",
  "prompt_last_120": "Reason Explain why (4x^2-7)/(4x^2-7)=1 is a valid identity under the domain of all real numbers except ±\\frac{√(7)}{2}.",
  "notes": "Answer key (from source): Using the difference of two squares formula, (4x^2-7)/(4x^2-7)=\\frac{(2x+√(7))(2x-√(7))}{(2x+√(7))(2x-√(7))}. Both factors on the numerator and denominator divide to 1, so (4x^2-7)/(4x^2-7)=1 over all elements of the domain, which is all real numbers except ±\\frac{√(7)}{2}. · T1 pool: 'Reason Explain why (4x^2-7)/(4x^2-7)=1 is a valid identity under the domain of a' → [factor-polynomial, distractor-analysis]"
}
```

## 5-4-savvas-teacher-edition-elicitevidence-le-5

Before:

```json
{
  "prompt_first_200": "Q: How can this inequality be written according to these new conditions?\n\\answer{(\\sqrt{\\frac{H·75}{3{,}600}}<1.8)}",
  "prompt_last_120": "Q: How can this inequality be written according to these new conditions?\n\\answer{(\\sqrt{\\frac{H·75}{3{,}600}}<1.8)}",
  "notes": "T1 pool: 'Q: How can this inequality be written according to these new conditions? \\\\answer' → [solve-radical-equation, interpret-answer-in-context]"
}
```

After:

```json
{
  "prompt_first_200": "Q: How can this inequality be written according to these new conditions?",
  "prompt_last_120": "Q: How can this inequality be written according to these new conditions?",
  "notes": "Answer key (from source): (\\sqrt{\\frac{H·75}{3{,}600}}<1.8) · T1 pool: 'Q: How can this inequality be written according to these new conditions? \\\\answer' → [solve-radical-equation, interpret-answer-in-context]"
}
```

## 6-4-savvas-q7

Before:

```json
{
  "prompt_first_200": "The function y=5\\ln(x+1) gives y, the number of downloads, in hundreds, x minutes after the release of a song. Find the equation of the inverse and interpret its meaning.\n\n[IMAGE: Download bar labeled",
  "prompt_last_120": "unction gives x, the number of minutes after the release of a song, in terms of the number of downloads in hundreds, y.}",
  "notes": "IMAGE PLACEHOLDER [illustration]: Download bar labeled \"Downloading...\", green bar labeled \"y downloads\", blue bar labeled \"x minutes\"."
}
```

After:

```json
{
  "prompt_first_200": "The function y=5\\ln(x+1) gives y, the number of downloads, in hundreds, x minutes after the release of a song. Find the equation of the inverse and interpret its meaning.\n\n[IMAGE: Download bar labeled",
  "prompt_last_120": "meaning.\n\n[IMAGE: Download bar labeled \"Downloading...\", green bar labeled \"y downloads\", blue bar labeled \"x minutes\".]",
  "notes": "Answer key (from source): x=e^{(y)/(5)}-1; This function gives x, the number of minutes after the release of a song, in terms of the number of downloads in hundreds, y. · IMAGE PLACEHOLDER [illustration]: Download bar labeled \"Downloading...\", green bar labeled \"y downloads\", blue bar labeled \"x minutes\"."
}
```

## 6-4-savvas-q8

Before:

```json
{
  "prompt_first_200": "Sketch the functions represented by the tables. Identify which graph is the logarithmic function. Are the two functions inverses?\n\nA.\n\\begin{center}\nTABLE:\n →prule\nx | 10^{-10} | 0.01 | 1 | 2 | 10 \n\\m",
  "prompt_last_120": "tomrule\nEND_TABLE\n\\end{center}\n\n\\answer{g(x) is the logarithmic function. Yes they are inverses.\n\n[GRAPH / TIKZ figure]}",
  "notes": "T1 pool: 'Sketch the functions represented by the tables. Identify which graph is the loga' → [sketch-polynomial-graph, evaluate-log, graph-log-function]"
}
```

After:

```json
{
  "prompt_first_200": "Sketch the functions represented by the tables. Identify which graph is the logarithmic function. Are the two functions inverses?\n\nA.\n\\begin{center}\nTABLE:\n →prule\nx | 10^{-10} | 0.01 | 1 | 2 | 10\n\\mi",
  "prompt_last_120": "\n →prule\nx | -1 | 0 | 1 | 2 | 3 | 4\n\\midrule\nh(x) | 0.001 | 0.01 | 0.1 | 1 | 10 | 100\n\\bottomrule\nEND_TABLE\n\\end{center}",
  "notes": "Answer key (from source): g(x) is the logarithmic function. Yes they are inverses.\n\n[GRAPH / TIKZ figure] · T1 pool: 'Sketch the functions represented by the tables. Identify which graph is the loga' → [sketch-polynomial-graph, evaluate-log, graph-log-function]"
}
```

## 6-4-savvas-q26

Before:

```json
{
  "prompt_first_200": "Find the equation of the inverse of each function. f(x)=4\\log_2(x-3)+2.\n\\answer{f^{-1}(x)=2^{(x-2)/(4)}+3}",
  "prompt_last_120": "Find the equation of the inverse of each function. f(x)=4\\log_2(x-3)+2.\n\\answer{f^{-1}(x)=2^{(x-2)/(4)}+3}",
  "notes": "T1 pool: 'Find the equation of the inverse of each function. f(x)=4\\\\log_2(x-3)+2. \\\\answer{' → [find-inverse-function, evaluate-log]"
}
```

After:

```json
{
  "prompt_first_200": "Find the equation of the inverse of each function. f(x)=4\\log_2(x-3)+2.",
  "prompt_last_120": "Find the equation of the inverse of each function. f(x)=4\\log_2(x-3)+2.",
  "notes": "Answer key (from source): f^{-1}(x)=2^{(x-2)/(4)}+3 · T1 pool: 'Find the equation of the inverse of each function. f(x)=4\\\\log_2(x-3)+2. \\\\answer{' → [find-inverse-function, evaluate-log]"
}
```

## 6-4-savvas-q27

Before:

```json
{
  "prompt_first_200": "The altitude y, in feet, of a plane t minutes after takeoff is approximated by the function y=5{,}000\\ln(.05t)+8{,}000. Solve for t in terms of y. What is a situation in which it would be easier to us",
  "prompt_last_120": "{y-8{,}000}{5{,}000}}; Use this new equation when the altitude of the plane is known but the time since takeoff is not.}",
  "notes": "T1 pool: 'The altitude y, in feet, of a plane t minutes after takeoff is approximated by t' → [solve-for-variable, log-vocabulary, extract-time-from-model]"
}
```

After:

```json
{
  "prompt_first_200": "The altitude y, in feet, of a plane t minutes after takeoff is approximated by the function y=5{,}000\\ln(.05t)+8{,}000. Solve for t in terms of y. What is a situation in which it would be easier to us",
  "prompt_last_120": " for t in terms of y. What is a situation in which it would be easier to use your new equation rather than the original?",
  "notes": "Answer key (from source): t=20e^{\\frac{y-8{,}000}{5{,}000}}; Use this new equation when the altitude of the plane is known but the time since takeoff is not. · T1 pool: 'The altitude y, in feet, of a plane t minutes after takeoff is approximated by t' → [solve-for-variable, log-vocabulary, extract-time-from-model]"
}
```

## 6-4-savvas-q28

Before:

```json
{
  "prompt_first_200": "A company uses this function to relate sales revenue, R, and advertising costs, a. What is the equation of the inverse of the equation? Which equation would be easier to use to find a value of a for a",
  "prompt_last_120": "er{The inverse of the formula is a=10^{(R-25)/(12)}-1. It would be easier to use the inverse to find a when R is known.}",
  "notes": "IMAGE PLACEHOLDER [illustration]: Sales revenue represented by stacks of coins labeled \"Sales Revenue, R\" and advertising costs represented by a web ad and phone labeled \"Advertising Costs, a\" with formula $R=12\\log(a+1)+25$."
}
```

After:

```json
{
  "prompt_first_200": "A company uses this function to relate sales revenue, R, and advertising costs, a. What is the equation of the inverse of the equation? Which equation would be easier to use to find a value of a for a",
  "prompt_last_120": "\" and advertising costs represented by a web ad and phone labeled \"Advertising Costs, a\" with formula R=12\\log(a+1)+25.]",
  "notes": "Answer key (from source): The inverse of the formula is a=10^{(R-25)/(12)}-1. It would be easier to use the inverse to find a when R is known. · IMAGE PLACEHOLDER [illustration]: Sales revenue represented by stacks of coins labeled \"Sales Revenue, R\" and advertising costs represented by a web ad and phone labeled \"Advertising Costs, a\" with formula $R=12\\log(a+1)+25$."
}
```

## 6-4-savvas-q29

Before:

```json
{
  "prompt_first_200": "Model with Mathematics The equation r=90-25\\log(t+1) is to model a student's retention r after taking a physics course where r represents a student's test score (as a percent), and t represents the nu",
  "prompt_last_120": " figure]\n\nB. t=10^{(r-90)/(-25)}-1; the number of months since taking the course at which a student has a retention, r.}",
  "notes": "T1 pool: \"Model with Mathematics The equation r=90-25\\\\log(t+1) is to model a student's ret\" → [sketch-polynomial-graph, evaluate-log, graph-log-function]"
}
```

After:

```json
{
  "prompt_first_200": "Model with Mathematics The equation r=90-25\\log(t+1) is to model a student's retention r after taking a physics course where r represents a student's test score (as a percent), and t represents the nu",
  "prompt_last_120": "u may use a graphing calculator to check.)\n\nB. Find the equation of the inverse. Interpret the meaning of this function.",
  "notes": "Answer key (from source): A. Check students' work.\n\nTABLE:\n →prule\nt | r \n\\midrule\n9 | 65 \n99 | 40 \n200 | 32.5 \n300 | 28 \n400 | 24.9 \n\\bottomrule\nEND_TABLE\n\n[GRAPH / TIKZ figure]\n\nB. t=10^{(r-90)/(-25)}-1; the number of months since taking the course at which a student has a retention, r. · T1 pool: \"Model with Mathematics The equation r=90-25\\\\log(t+1) is to model a student's ret\" → [sketch-polynomial-graph, evaluate-log, graph-log-function]"
}
```

## 4-4-savvas-concept-summary-lesson-4-4-2

Before:

```json
{
  "prompt_first_200": "CONCEPT SUMMARY Find Sums and Differences of Rational Expressions\n\nWords: To add or subtract rational expressions with common denominators, add the numerators and keep the denominator the same.\n[\n(1)/",
  "prompt_last_120": "3y^2-2y-8)+(7)/(3y^2+y-4))\n \n\n11. Find the perimeter of the quadrilateral in simplest form.\n [\n [GRAPH / TIKZ figure]\n ]",
  "notes": ""
}
```

After:

```json
{
  "prompt_first_200": "CONCEPT SUMMARY Find Sums and Differences of Rational Expressions\n\nWords: To add or subtract rational expressions with common denominators, add the numerators and keep the denominator the same.\n[\n(1)/",
  "prompt_last_120": "/(3y^2-2y-8)+(7)/(3y^2+y-4))\n\n11. Find the perimeter of the quadrilateral in simplest form.\n [\n [GRAPH / TIKZ figure]\n ]",
  "notes": "Answer key (from source): A compound fraction is a fraction that has one or more fractions in the numerator and/or denominator. Example: (((1)/(2x))/(x+y))."
}
```

## Applied verification

- Dry runs: 11 passed; registry bytes unchanged.
- Applied patches: 11 passed.
- Remaining prompt macro IDs: `[]`.
- Total rows: 990 before / 990 after.
- Exactly the 11 requested rows changed, only prompt and notes; all unrelated lines preserved byte-for-byte.

| Lesson | Before | After |
| --- | ---: | ---: |
| 1-1 | 71 | 71 |
| 4-3 | 74 | 74 |
| 4-4 | 91 | 91 |
| 5-4 | 132 | 132 |
| 6-4 | 69 | 69 |
