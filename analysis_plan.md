# Analysis plan: small local models and code graphs for regression test selection

Written before any selection method was run on any bug. Frozen by its SHA-256, recorded in the git history of this repository.

## Question
After a change, which tests should run first so a regression shows up fast? Does a small local model (Gemma 4 E2B, E4B, 4-bit QAT) add anything over static code-graph methods, and when is its latency worth paying?

## Data
- Bugs: single-operator mutants (comparison, arithmetic, boolean operator, bool/0-1 constant swaps) planted in functions of each repository's source package. A mutant is kept only if at least one test that passes on the original fails on the mutant. Mutant sites are sampled uniformly at random with a fixed seed.
- Repositories: cachetools, toolz, humanize, sortedcontainers (small suites), and the competition's repository snapshots where available (fastapi, httpx, rich, requests).
- Ground truth: for each mutant, the set of tests that fail (the kill matrix), from one full run of the suite.
- Per-test runtime from one clean run of the full suite with durations recorded.

## Methods (each outputs a ranked list of test ids)
1. Full suite in its default order (reference).
2. Name match: tests whose name or file contains the changed function's name or module name first, then the rest in default order.
3. Reachability: tests from which the changed function is reachable in the static call graph, ordered by default order; unreachable tests after.
4. Graph distance: reachable tests ordered by shortest-path length to the changed function; ties in default order.
5. Embedding similarity: tests ordered by cosine similarity between the changed function's node embedding and each test's node embedding.
6. Coverage (oracle-like upper bound): tests that executed the changed line on the original code, by default order.
7. Model re-rank: Gemma re-orders the top 30 tests from method 4, given the diff, the changed function's graph neighbourhood and test names, and may add up to 5 test ids from outside that list. Unknown ids are dropped and counted as hallucinations. Temperature 0, fixed prompt, outputs cached.

## Primary outcome (decided in advance)
Recall@k: share of mutants for which at least one failing test is among the first k tests, for k = 1, 5, 10, and at a budget of 10% of the suite's tests.

## Secondary outcomes
- Time to first failure: sum of per-test runtimes until the first failing test in the ranking, plus model time for method 7.
- Static misses: mutants where no failing test is reachable in the graph; how many of those the model recovers, and its false-alarm (non-failing proposed test) count.
- Break-even suite runtime: the full-suite runtime above which method 7's median time to first failure beats method 4's, from the measured times.

## Analysis
- Paired comparisons on the same mutants. 95% bootstrap intervals (10,000 resamples of mutants, stratified by repository). Claims about method 7 versus method 4 use the paired difference in Recall@10 and its interval; an interval that includes zero is reported as no detectable difference.
- All results are reported whatever their direction. Anything not listed here is labelled exploratory.
