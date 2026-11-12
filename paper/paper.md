# Which tests should run first? Code graphs and a small local model for regression test selection

*On a laptop, Gemma 4 and a code graph pick the tests most likely to catch a bug, and we measure when the model is worth its latency.*

*Dhiraj Kavuri*

## Abstract

A coding agent on a laptop checks its own edits by running tests, and on a large suite that check is slow. We study regression test selection (RTS) for this setting: after a change, order the tests so a failing one comes early. We plant 375 single-operator bugs in five Python repositories, from libraries whose suites finish in seconds to the competition's FastAPI snapshot, whose 3,207 tests take 31 seconds on one core. Each bug is kept only if the repository's own tests catch it, so the ground truth is the full bug-by-test kill matrix. We compare name matching, static call-graph reachability, graph-distance ranking, lexical similarity, per-test coverage (an upper bound) and Gemma 4 E2B and E4B re-ranking the graph's nearest tests while free to propose tests the graph cannot reach. Pooled over all bugs, graph distance puts a failing test in the first 10 for 56% of bugs; Gemma 4 E2B raises this to 61% and E4B to 66% (paired gains of 5.6 and 10.4 points, both with 95% intervals above zero), mostly by finding tests the graph cannot reach, such as tests that call dunder methods through Python syntax. On the competition's FastAPI snapshot the provided graph reaches fewer failing tests than a plain AST graph, and neither model helps there. The model costs 2.5 to 14 seconds per change, so on the suites we measured it never saves wall-clock time; scaling test runtimes suggests it pays off once a single-core suite runs for about a quarter of an hour. The analysis plan was hashed before any method ran, and a public notebook rebuilds every number from cached model outputs.

## 1. Introduction

Coding agents fix bugs in a loop: read, edit, run tests, repeat. This competition asks how far that loop can go with Gemma 4 on one accelerator under a time budget, and every full test run spends budget. Developers have the same problem on their own machines.

Regression test selection answers a narrow question: given a change, which tests should run first? Classic tools answer it with static dependency analysis or recorded coverage. Recent agent scaffolds answer it by asking a large hosted model. We ask whether a small model that runs locally, given a code graph of the kind the competition provides to its agents, helps, and when its latency is worth paying. On one of the competition's own snapshots we also test the provided graph and embeddings directly.

Two properties make this a good fit for a small model. The task is a ranking over a few dozen candidates, which needs far less reasoning than writing a patch. And the static graph has known blind spots (inheritance, decorators, attribute calls) where reading code helps. We report the model's results against strong cheap baselines, including the case where it loses.

Contributions:
1. A benchmark of 375 planted bugs in five repositories with full kill matrices and per-test runtimes, released with the code that rebuilds it.
2. A comparison of six non-model methods and two Gemma 4 sizes on the same bugs, with paired bootstrap intervals and an analysis plan fixed in advance.
3. A measured answer to when the model pays off: on our laptop, only for suites that take roughly a quarter of an hour or more on one core.

## 2. Task and data

**Repositories.** Four small pure-Python libraries (cachetools, toolz, humanize, sortedcontainers) and FastAPI at the competition's snapshot for task `fastapi_15800` (commit `f1d750f`), so that the competition's provided code graph and node embeddings match the code exactly. Measured on one core, the suites take from 2 to 31 seconds. Commits are pinned in the notebook.

**Bugs.** For each repository we parse every source module, list the sites where one operator can be swapped (comparisons, arithmetic, `and`/`or`, boolean and 0/1 constants), sample sites uniformly with a fixed seed, apply one swap, and run the full suite. A mutant is kept only if at least one test that passes on the original code now fails. We stop at 80 kept mutants per small library and 60 for FastAPI. Five mutants whose failing tests were missing from the clean profiling run are dropped, leaving 375. Planted bugs are a common stand-in for real faults when ground truth must be exact (Just et al., 2014); Section 6 discusses what this costs.

**Ground truth and cost.** For every kept bug we store the ids of all failing tests. One extra clean run records each test's runtime and, with coverage.py's per-test contexts, which lines each test executed.

## 3. Methods

Every method returns a full ordering of the suite. A method that ranks only some tests is completed with the remaining tests in the suite's default order.

- **Full suite**: the default order pytest uses.
- **Name match**: tests whose name contains the changed function's name, or whose file contains the changed module's name, go first.
- **Reachability**: tests from which the changed function is reachable in the static call graph go first, in default order.
- **Graph distance**: the reachable tests, ordered by shortest-path length to the changed function.
- **Lexical similarity**: tests ordered by TF-IDF cosine between the changed function's source and each test's source.
- **Coverage**: tests that executed the changed line on the original code go first. This needs a recorded coverage run per test, so we treat it as an upper bound for a cheap method, not a competitor.
- **Provided graph and embeddings** (FastAPI only): graph distance over the competition's call graph, and cosine similarity of the competition's 256-dimensional node embeddings between the changed function and each test.
- **Gemma re-rank**: Gemma 4 E2B or E4B (4-bit QAT, run locally with Ollama, temperature 0) sees the diff, the changed function's source, its callers and callees from the graph, the 30 nearest tests by graph distance (numbered), and the names of the other tests (at most 600, in alphabetical order, which truncates the list for FastAPI). It returns up to 15 entries, each a candidate number or the exact name of another test (at most five). Unknown names are dropped and counted. Its list goes first, followed by the graph-distance order.

**Code graph.** We build a symbol graph from Python ASTs with `contains`, `calls` and `imports` edges, the same node and edge types as the graphs the competition gives its agents. Calls are resolved by name; a name that matches more than eight definitions is skipped. Like any static graph it misses calls made through inheritance, decorators and dynamic attributes.

**Metrics** (fixed in the analysis plan before any method ran). Primary: Recall@k, the share of bugs with at least one failing test in the first k tests, for k = 1, 5, 10 and 10% of the suite. Secondary: time to first failure (sum of per-test runtimes up to the first failing test, plus model wall time for Gemma rows), recovered static misses, and the break-even suite runtime. Intervals are 95% bootstrap intervals over bugs, stratified by repository, with 10,000 resamples.

## 4. Results

### 4.1 Which tests come first

Table 1 pools all 375 bugs. The default order finds a failing test within the first 10 tests for 12% of bugs, graph distance for 56%, lexical similarity for 58%, Gemma 4 E2B for 61% and E4B for 66%. Coverage, which needs a recorded run of every test, reaches 83%.

**Table 1.** Share of bugs with a failing test among the first k tests, all five repositories (n = 375). 95% bootstrap intervals, stratified by repository.

| Method | k = 1 | k = 5 | k = 10 | 10% of suite |
|---|---|---|---|---|
| Full suite order | 0.07 [0.04, 0.09] | 0.09 [0.07, 0.12] | 0.12 [0.09, 0.15] | 0.32 [0.28, 0.37] |
| Name match | 0.08 [0.05, 0.10] | 0.23 [0.19, 0.27] | 0.30 [0.26, 0.35] | 0.53 [0.48, 0.58] |
| Reachability | 0.26 [0.22, 0.30] | 0.36 [0.31, 0.41] | 0.45 [0.40, 0.49] | 0.69 [0.64, 0.73] |
| Graph distance | 0.34 [0.29, 0.39] | 0.48 [0.43, 0.53] | 0.56 [0.51, 0.61] | 0.72 [0.68, 0.76] |
| Lexical similarity | 0.24 [0.20, 0.28] | 0.46 [0.41, 0.51] | 0.58 [0.53, 0.62] | 0.82 [0.78, 0.86] |
| Gemma 4 E2B re-rank | 0.40 [0.35, 0.45] | 0.55 [0.51, 0.61] | 0.61 [0.57, 0.66] | 0.75 [0.70, 0.79] |
| Gemma 4 E4B re-rank | 0.35 [0.31, 0.40] | 0.59 [0.54, 0.63] | 0.66 [0.62, 0.71] | 0.80 [0.77, 0.84] |
| Coverage (upper bound) | 0.61 [0.56, 0.65] | 0.79 [0.75, 0.83] | 0.83 [0.79, 0.87] | 0.93 [0.91, 0.95] |

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

Across the 117 bugs where the static graph reaches no failing test, E4B proposed a failing test from outside the graph's reach for 40 and E2B for 18. Typical cases: a bug in `TTLCache.__iter__`, where graph distance puts the first failing test at position 412 and E4B puts `test_ttl_iter_expired` second; a bug in `TLRUCache.__contains__` (position 347 vs 5); and `typedmethodkey`, reached by name in a test the graph did not link (position 253 vs 2). Proposals cost precision. E4B proposed outside tests for 181 bugs, and for 135 of those none of its proposals failed. It also named 174 tests that do not exist, and 28 of its answers (of 375) were not valid JSON. E2B proposed less often and was right less often.

### 4.3 The provided code graph and embeddings

On the FastAPI snapshot we also ranked tests with the competition's own graph and node embeddings. The changed function was present in both for 55 of 60 bugs. The provided graph reached a failing test less often than our AST graph (Recall@10 0.22 [0.12, 0.32] vs 0.35 [0.23, 0.47]). It has 2,752 call edges for 4,401 nodes, and only 285 of them run from tests into FastAPI code, so most tests are not linked to the code they exercise. The provided embeddings did about as well as lexical similarity (0.32 vs 0.30). Neither model improved on graph distance here (both 0.37), while coverage reached 0.57. A likely reason, which we did not test: most FastAPI tests go through the `TestClient`, so the path from a test to the changed function runs through the framework's own request handling, which a name-resolved graph does not capture, and the model's 30-test shortlist comes from that graph.

### 4.4 When is the model worth its latency?

Median model time per change was 2.5 s for E2B and 13.9 s for E4B on our laptop. On the suites we measured, that is slower than graph distance needs to reach a failing test (Figure 2): graph distance usually reaches one within a fraction of a second, so the model loses on time for every repository in our data.

![Figure 2](paper/figs/fig2_time_to_failure.png)

**Figure 2.** Median seconds until the first failing test, model time included for Gemma rows (log scale).

To ask when it would pay off, we scaled every test's runtime by a factor s while keeping model time fixed, and found the smallest s at which the model's mean time to first failure drops below graph distance's. Pooled, E2B breaks even at a suite of about 16 minutes on one core and E4B at about 15 minutes. Per repository it ranges from about 2 minutes (cachetools) and 4 minutes (sortedcontainers) to 24 to 64 minutes (humanize) and many hours (FastAPI), where the model's order saves almost no test time. This analysis was not in the plan and assumes tests slow down uniformly; we report it as a guide, not a measurement.

### 4.5 Two pipeline problems we found and fixed

First, FastAPI prompts (up to 22,551 tokens) overflowed the 16k context and the runtime kept only the last half, so the model never saw its candidate list; we raised the context to 32k and reran FastAPI. Second, the model often named parametrised tests without their `[parameter]` suffix, which first counted as unknown; scoring now expands a base name to all its variants, re-scored from cached answers. Together these moved FastAPI Recall@10 for both models from 0.35 to 0.37 and pooled E4B Recall@1 from 0.40 to 0.35. First-run answers are in the repository.

## 5. Related work

**Static and dynamic RTS.** Ekstazi (Gligoric et al., 2015) selects tests from recorded file dependencies; STARTS (Legunsen et al., 2017) does it statically from class-level dependencies. Google's pre-submit system (Regression Test Selection at Scale) ranks tests over a hybrid call graph at very large scale. Our graph-distance and coverage baselines are small versions of these two families.

**LLMs for test selection in agents.** Agentless (Xia et al., 2024) asks a hosted model which existing tests relate to an edit and drops patches that break them. TestPrune (2025) uses a model to predict suspicious methods from an issue and then minimises the regression suite through coverage. Both use large hosted models and judge selection only through issue resolution; we score it directly, with laptop-sized models.

**Mutants as faults.** Just et al. (2014) found that mutant detection correlates with real-fault detection for test suites, which supports using planted bugs to compare selection methods, though not to estimate absolute miss rates on real regressions.

## 6. Limitations

- **Planted bugs, not real regressions.** Single-operator mutants are local and usually caught by tests near the changed code. Real regressions can be wider. Absolute recall numbers should not be read as field estimates; the comparison between methods on the same bugs is the result.
- **Python only, five repositories.** The static graph's blind spots are Python's (inheritance, decorators, dynamic attributes). Languages with explicit types would give a denser graph and likely a smaller gap for the model.
- **One prompt, two small models.** We did not tune the prompt after seeing results. A better prompt or a larger model may do better; our numbers are a floor for this design.
- **Latency is hardware-specific.** Model times come from one Apple M5 laptop with 16 GB of memory. The break-even point moves with hardware and with how many tests can run in parallel.
- **Memorisation.** These popular projects may be in Gemma's training data; the bugs are new, the test names are not.

## 7. Reproducibility

The analysis plan (`analysis_plan.md`) was committed with SHA-256 `941004144a033e7b4edb5a011ad0ff34ab65da29c7ca4eaecf6deab4b74ca9fd` before any selection method ran. The public notebook (Kaggle, linked from the writeup) and the GitHub repository contain the planted bugs, kill matrices, per-test runtimes and coverage, every model prompt and answer (cached by prompt hash), and the scripts. Running it on CPU rebuilds every table and figure without calling a model. Re-running the models needs Ollama with `gemma4:e2b-it-qat` and `gemma4:e4b-it-qat`.

## References

- Gligoric, M., Eloussi, L., and Marinov, D. (2015). Practical regression test selection with dynamic file dependencies. ISSTA.
- Legunsen, O., Shi, A., and Marinov, D. (2017). STARTS: STAtic regression test selection. ASE (tool demo).
- Just, R., Jalali, D., Inozemtseva, L., Ernst, M. D., Holmes, R., and Fraser, G. (2014). Are mutants a valid substitute for real faults in software testing? FSE.
- Xia, C. S., Deng, Y., Dunn, S., and Zhang, L. (2024). Agentless: Demystifying LLM-based software engineering agents. arXiv:2407.01489.
- When Old Meets New: Evaluating the impact of regression tests on SWE issue resolution (TestPrune) (2025). arXiv:2510.18270.
- Regression Test Selection at Scale. Google Research. https://research.google/pubs/regression-test-selection-at-scale-2/
- Markowitz, E., et al. (2026). Google - The Gemma 4 Developer Agent Competition. Kaggle.
