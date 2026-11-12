# Which tests should run first? Code graphs and a small local model for regression test selection

*On a laptop, Gemma 4 and a code graph pick the tests most likely to catch a bug, and we measure when the model is worth its latency.*

*Dhiraj Kavuri*

## Abstract

A coding agent on a laptop checks its edits by running tests, and full runs are slow. We study regression test selection for this setting: after a change, order the tests so a failing one comes early. On 375 single-operator bugs planted in five Python repositories, including the competition's FastAPI snapshot, graph distance in a static call graph puts a failing test in the first 10 for 56% of bugs; Gemma 4 E2B and E4B re-ranking raise this to 61% and 66% (paired gains of 5.6 and 10.4 points, intervals above zero), mostly by finding tests the graph cannot reach. The competition's provided graph reaches fewer failing tests than a plain AST graph. We then replay 76 real regressions by undoing real fixes from the competition's FastAPI and Rich tasks. Every method does far worse; the pre-registered prompt adds nothing on FastAPI but E4B gains 19 points on held-out Rich, and a second prompt designed on FastAPI did not pass its pre-registered held-out test. Started in parallel with graph-distance tests, the model never slows the loop. Analysis plans were hashed before the runs they cover; a public notebook rebuilds every number from cached model answers.

## 1. Introduction

Coding agents fix bugs in a loop: read, edit, run tests, repeat. This competition asks how far that loop can go with Gemma 4 on one accelerator under a time budget, and every full test run spends budget. Developers have the same problem on their own machines.

Regression test selection asks which tests to run first after a change. Classic tools use static dependencies or recorded coverage; agent scaffolds ask a large hosted model. We ask whether a small local model, given a code graph like the one the competition gives its agents, helps, and when its latency is worth paying. The task suits a small model: it ranks a few dozen candidates, and the static graph has blind spots (inheritance, decorators, syntax-driven calls) where reading code helps.

Contributions:
1. 375 planted bugs in five repositories and 76 real regressions replayed from the competition's FastAPI and Rich tasks, with full kill matrices (which tests fail for each bug), released with the code that rebuilds them.
2. Six non-model methods, the competition's graph and embeddings, and two Gemma 4 sizes compared on the same bugs, with an analysis plan fixed in advance.
3. Evidence that planted bugs overstate test selection, and a schedule under which the model's latency costs nothing.

## 2. Task and data

**Repositories.** Four small pure-Python libraries (cachetools, toolz, humanize, sortedcontainers) and FastAPI at the competition's snapshot for task `fastapi_15800` (commit `f1d750f`), so that the competition's provided code graph and node embeddings match the code exactly. Measured on one core, the suites take from 2 to 31 seconds. Commits are pinned in the notebook.

**Bugs.** For each repository we parse every source module, list the sites where one operator can be swapped (comparisons, arithmetic, `and`/`or`, boolean and 0/1 constants), sample sites uniformly with a fixed seed, apply one swap, and run the full suite. A mutant is kept only if at least one test that passes on the original code now fails. We stop at 80 kept mutants per small library and 60 for FastAPI. Five mutants whose failing tests were missing from the clean profiling run are dropped, leaving 375. Planted bugs are a common stand-in for real faults when ground truth must be exact (Just et al., 2014); Section 4.5 adds real regressions.

**Ground truth and cost.** For every kept bug we store the ids of all failing tests. One extra clean run records each test's runtime and, with coverage.py's per-test contexts, which lines each test executed.

## 3. Methods

Every method returns a full ordering of the suite; a partial ranking is completed in the suite's default order.

- **Full suite**: pytest's default order.
- **Name match**: tests whose name contains the changed function's name, or whose file contains the module's name, first.
- **Reachability**: tests from which the changed function is reachable in the static call graph first.
- **Graph distance**: reachable tests by shortest-path length to the changed function.
- **Lexical similarity**: TF-IDF cosine between the changed function's source and each test's source.
- **Coverage**: tests that executed the changed line first. It needs a recorded run of every test, so it is an upper bound, not a competitor.
- **Provided graph and embeddings** (FastAPI): graph distance over the competition's call graph, and cosine of its 256-dimensional node embeddings.
- **Gemma re-rank**: Gemma 4 E2B or E4B (4-bit QAT, Ollama, temperature 0) sees the diff, the function's source, its callers and callees, the 30 nearest tests by graph distance, and the names of other tests (at most 600, alphabetical). It returns up to 15 entries, candidate numbers or other test names (at most five); unknown names are dropped and counted. Its list goes first, then the graph-distance order.

**Code graph.** A symbol graph from Python ASTs with `contains`, `calls` and `imports` edges, the node and edge types of the competition's graphs. Calls are resolved by name; names matching more than eight definitions are skipped.

**Metrics** (fixed in the plan). Primary: Recall@k, the share of bugs with a failing test in the first k, for k = 1, 5, 10 and 10% of the suite. Secondary: time to first failure (test runtimes up to the first failing test, plus model wall time), recovered static misses, and break-even suite runtime. 95% bootstrap intervals over bugs, stratified by repository, 10,000 resamples.

## 4. Results

### 4.1 Which tests come first

Table 1 pools all 375 bugs. The default order finds a failing test within the first 10 tests for 12% of bugs, graph distance for 56%, lexical similarity for 58%, Gemma 4 E2B for 61% and E4B for 66%. Coverage, which needs a recorded run of every test, reaches 83%.

**Table 1.** Share of bugs with a failing test among the first k tests (n = 375), 95% bootstrap intervals.

| Method | k = 1 | k = 10 | 10% of suite |
|---|---|---|---|
| Full suite order | 0.07 [0.04, 0.09] | 0.12 [0.09, 0.15] | 0.32 [0.28, 0.37] |
| Name match | 0.08 [0.05, 0.10] | 0.30 [0.26, 0.35] | 0.53 [0.48, 0.58] |
| Reachability | 0.26 [0.22, 0.30] | 0.45 [0.40, 0.49] | 0.69 [0.64, 0.73] |
| Graph distance | 0.34 [0.29, 0.39] | 0.56 [0.51, 0.61] | 0.72 [0.68, 0.76] |
| Lexical similarity | 0.24 [0.20, 0.28] | 0.58 [0.53, 0.62] | 0.82 [0.78, 0.86] |
| Gemma 4 E2B re-rank | 0.40 [0.35, 0.45] | 0.61 [0.57, 0.66] | 0.75 [0.70, 0.79] |
| Gemma 4 E4B re-rank | 0.35 [0.31, 0.40] | 0.66 [0.62, 0.71] | 0.80 [0.77, 0.84] |
| Coverage (upper bound) | 0.61 [0.56, 0.65] | 0.83 [0.79, 0.87] | 0.93 [0.91, 0.95] |

![Figure 1](paper/figs/fig1_recall_at_k.png)

**Figure 1.** Share of bugs caught within the first k tests, pooled over 375 bugs.

The pre-registered comparison is the paired difference in Recall@10 against graph distance. E2B adds 5.6 points [+3.2, +8.3] and E4B adds 10.4 points [+6.7, +14.1]. Against lexical similarity, a comparison we added after seeing that it was strong, E4B adds 8.5 points [+2.9, +13.9], while the E2B difference (+3.7 [−1.9, +9.1]) is not distinguishable from zero.

The gain is uneven across repositories (Table 2). It is largest where the static graph is blind. In cachetools, 48 of 79 bugs had no failing test reachable in the graph, largely because much of the behaviour sits in dunder methods (`__contains__`, `__iter__`, `__setitem__`) that tests call through Python syntax, not by name. There E4B lifts Recall@10 from 0.42 to 0.62. On humanize, where every bug was reachable, the models match graph distance. On sortedcontainers, lexical similarity beats both models.

**Table 2.** Recall@10 by repository. "Misses" counts bugs for which no failing test is reachable in our static graph.

| Repository | Bugs | Tests | Suite (s) | Misses | Graph dist. | Lexical | E2B | E4B | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| cachetools | 79 | 416 | 1.9 | 48 | 0.42 | 0.54 | 0.53 | 0.62 | 0.78 |
| toolz | 78 | 192 | 2.0 | 24 | 0.67 | 0.76 | 0.74 | 0.81 | 0.96 |
| humanize | 80 | 746 | 1.9 | 0 | 0.69 | 0.39 | 0.71 | 0.68 | 0.88 |
| sortedcontainers | 78 | 366 | 23.5 | 16 | 0.62 | 0.83 | 0.65 | 0.77 | 0.91 |
| FastAPI (snapshot) | 60 | 3,207 | 31.3 | 29 | 0.35 | 0.30 | 0.37 | 0.37 | 0.57 |

### 4.2 What the model adds: tests the graph cannot reach

For the 117 planted bugs where the static graph reaches no failing test, E4B proposed a failing test from outside its reach for 40 and E2B for 18. For a bug in `TTLCache.__iter__`, graph distance puts the first failing test at position 412 and E4B puts `test_ttl_iter_expired` second; for `TLRUCache.__contains__` it is 347 against 5. Proposals cost precision: E4B proposed outside tests for 181 bugs and none failed in 135 of them, named 174 tests that do not exist, and returned invalid JSON 28 times in 375.

### 4.3 The provided code graph and embeddings

On the FastAPI snapshot we also ranked tests with the competition's own graph and embeddings. The provided graph reached a failing test less often than our AST graph (Recall@10 0.22 [0.12, 0.32] against 0.35 [0.23, 0.47]): only 285 of its 2,752 call edges run from tests into FastAPI code. The provided embeddings did about as well as lexical similarity (0.32 against 0.30). Neither model beat graph distance here (both 0.37), while coverage reached 0.57, plausibly because most FastAPI tests reach the changed code through the `TestClient` and the framework's request handling, which a name-resolved graph does not see.

### 4.4 When is the model worth its latency?

Median model time per change was 2.5 s for E2B and 13.9 s for E4B. On our suites graph distance usually reaches a failing test within a fraction of a second, so run first, the model loses on time everywhere (Figure 2).

![Figure 2](paper/figs/fig2_time_to_failure.png)

**Figure 2.** Median seconds until the first failing test, model time included for Gemma rows (log scale).

Scaling every test's runtime by s while model time stays fixed, the model's mean time to first failure drops below graph distance's at a pooled suite of about 15 minutes (E4B) to 16 minutes (E2B) on one core.

The latency need not be paid in sequence. In a **hybrid schedule** tests start at once in graph-distance order while the model thinks, then switch to the model's order, skipping tests already run. On our suites the hybrid is never slower on average (pooled 1.47 s vs 1.49 s), because fast suites find the bug before the model answers. With runtimes scaled by 10, 100 and 300, the E4B hybrid reaches the first failure 9%, 11% and 14% sooner than graph distance. Both analyses were not in the plan and assume uniform slow-down; they are guides, not measurements.

### 4.5 Real regressions

To test real bugs we replayed the competition's tasks for two repositories. For each task whose fix edits an existing function, we checked out the base commit with its dependencies, applied the fix and its tests, then undid the fix; tests that pass with the fix and fail without it are the ground truth. 40 FastAPI and 36 Rich tasks qualified (median 1 to 2 failing tests); tasks adding new code, timing out or failing with the fix were dropped. Coverage here spans the whole changed function.

**Table 3.** Real regressions (fix undone): Recall@10 with 95% bootstrap intervals over tasks, and median rank of the first failing test.

| Method | FastAPI (40) | rank | Rich (36) | rank |
|---|---|---|---|---|
| Graph distance | 0.10 [0.03, 0.20] | 422 | 0.17 [0.06, 0.31] | 346 |
| Lexical similarity | 0.12 [0.03, 0.23] | 217 | 0.25 [0.11, 0.39] | 34 |
| Coverage | 0.03 [0.00, 0.07] | 566 | 0.31 [0.17, 0.47] | 21 |
| E2B, prompt v1 | 0.10 [0.03, 0.20] | 422 | 0.25 [0.11, 0.39] | 313 |
| E4B, prompt v1 | 0.10 [0.03, 0.20] | 422 | 0.36 [0.19, 0.53] | 189 |
| E2B, prompt v2 | 0.25 [0.12, 0.40] | 189 | 0.42 [0.25, 0.58] | 27 |
| E4B, prompt v2 | 0.28 [0.15, 0.42] | 199 | 0.31 [0.17, 0.47] | 21 |

Every method does far worse than on planted bugs. The failing tests are usually the ones written with the fix, and the changed functions are run by hundreds of other tests, so coverage ranks them late on FastAPI. With the pre-registered prompt (v1), the models add nothing on FastAPI, where only 4 of 40 tasks had a failing test among the 30 graph candidates and the list of other names was cut at 600 of about 3,200. On Rich, which we built afterwards and did not tune on, E4B with prompt v1 beats graph distance by 19.4 points [+8.3, +33.3].

From the FastAPI diagnosis we wrote prompt v2: 15 candidates from graph distance and 15 from lexical similarity, and the full list of test files. We froze an addendum before running it anywhere else. On FastAPI (post hoc) it lifts E4B to 0.28. On held-out Rich, the pre-registered test, E4B v2 minus graph distance, gave +13.9 points with an interval of [0.0, +27.8], so it is not confirmed; E2B v2 gained +25.0 [+11.1, +38.9]. On the planted bugs v2 helps E2B (0.61 to 0.66) and hurts E4B (0.66 to 0.60). No prompt wins everywhere, lexical similarity is a strong cheap baseline on real regressions, and planted-bug benchmarks overstate how well any method selects tests.

## 5. Related work

**Static and dynamic RTS.** Ekstazi (Gligoric et al., 2015) selects tests from recorded file dependencies; STARTS (Legunsen et al., 2017) does it statically from class-level dependencies. Google's pre-submit system (Regression Test Selection at Scale) ranks tests over a hybrid call graph at very large scale. Our graph-distance and coverage baselines are small versions of these two families.

**LLMs for test selection in agents.** Agentless (Xia et al., 2024) asks a hosted model which tests relate to an edit; TestPrune (2025) predicts suspicious methods from an issue and minimises the suite through coverage. Both use large hosted models and judge selection only through issue resolution; we score it directly, with laptop-sized models.

**Mutants as faults.** Mutant detection correlates with real-fault detection for test suites (Just et al., 2014); Section 4.5 shows the gap can still be large for selection.

## 6. Limitations

- **Small real sets.** 76 real regressions from two repositories give wide intervals, and the second prompt was designed after seeing the FastAPI half.
- **Python only, five repositories.** The static graph's blind spots are Python's (inheritance, decorators, dynamic attributes). Languages with explicit types would give a denser graph and likely a smaller gap for the model.
- **Two prompts, two small models.** Prompt v1 was fixed in advance; v2 was written after the FastAPI real results and is labelled so. Larger models may do better.
- **Latency is hardware-specific.** Model times come from one Apple M5 laptop with 16 GB of memory.
- **Memorisation.** These popular projects may be in Gemma's training data; the bugs are new, the test names are not.

## 7. Reproducibility

The analysis plan (`analysis_plan.md`, SHA-256 `9410...a9fd`) was committed before any selection method ran, and an addendum for prompt v2 (`analysis_plan_addendum_v2.md`, SHA-256 `c55d...7d09`) before v2 ran on Rich or the planted bugs. The public notebook (Kaggle, linked from the writeup) and the GitHub repository contain the planted bugs, kill matrices, per-test runtimes and coverage, every model prompt and answer (cached by prompt hash), and the scripts. Running it on CPU rebuilds every table and figure without calling a model. Two pipeline faults were found and fixed during the study, and both runs are kept: FastAPI prompts first overflowed a 16k context (raised to 32k and rerun), and test names given without their `[parameter]` suffix were first counted as unknown (now expanded to all variants and re-scored from cache). Re-running the models needs Ollama with `gemma4:e2b-it-qat` and `gemma4:e4b-it-qat`.

## References

- Gligoric, M., Eloussi, L., and Marinov, D. (2015). Practical regression test selection with dynamic file dependencies. ISSTA.
- Legunsen, O., Shi, A., and Marinov, D. (2017). STARTS: STAtic regression test selection. ASE (tool demo).
- Just, R., Jalali, D., Inozemtseva, L., Ernst, M. D., Holmes, R., and Fraser, G. (2014). Are mutants a valid substitute for real faults in software testing? FSE.
- Xia, C. S., Deng, Y., Dunn, S., and Zhang, L. (2024). Agentless: Demystifying LLM-based software engineering agents. arXiv:2407.01489.
- When Old Meets New: Evaluating the impact of regression tests on SWE issue resolution (TestPrune) (2025). arXiv:2510.18270.
- Regression Test Selection at Scale. Google Research. https://research.google/pubs/regression-test-selection-at-scale-2/
- Markowitz, E., et al. (2026). Google - The Gemma 4 Developer Agent Competition. Kaggle.
