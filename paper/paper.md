# Which tests should run first? Code graphs and a small local model for regression test selection

*Subtitle: On a laptop, Gemma 4 and a code graph pick the tests most likely to catch a bug, and we measure when the model is worth its latency.*

## Abstract

A coding agent on a laptop checks its own edits by running tests, and on a large suite that check is slow. We study regression test selection (RTS) for this setting: after a change, order the tests so a failing one comes early. We plant {{N_BUGS}} single-operator bugs in five Python repositories, from libraries whose suites finish in seconds to FastAPI, whose 4,811 tests take {{FASTAPI_SUITE_S}} seconds on one core. Each bug is kept only if the repository's own tests catch it, so the ground truth is the full bug-by-test kill matrix. We compare name matching, static call-graph reachability, graph-distance ranking, lexical similarity, per-test coverage (an upper bound) and Gemma 4 E2B and E4B re-ranking the graph's nearest tests while free to propose tests the graph cannot reach. {{HEADLINE_RESULT}} The analysis plan was hashed before any method ran, and a public notebook rebuilds every number from cached model outputs.

## 1. Introduction

Coding agents fix bugs in a loop: read, edit, run tests, repeat. The competition this paper belongs to asks how far that loop can go with Gemma 4 on one accelerator, under a fixed time budget. Every turn of the loop that runs a whole test suite spends budget, and on a big repository a full run takes minutes. Developers have the same problem on their own machines.

Regression test selection answers a narrow question: given a change, which tests should run first? Classic tools answer it with static dependency analysis or recorded coverage. Recent agent scaffolds answer it by asking a large hosted model. We ask whether a small model that runs locally, given the code graph the competition already provides to agents, helps, and when its latency is worth paying.

Two properties make this a good fit for a small model. The task is a ranking over a few dozen candidates, which needs far less reasoning than writing a patch. And the static graph has known blind spots (inheritance, decorators, attribute calls) where reading code helps. We report the model's results against strong cheap baselines, including the case where it loses.

Contributions:
1. A benchmark of {{N_BUGS}} planted bugs in five repositories with full kill matrices and per-test runtimes, released with the code that rebuilds it.
2. A comparison of six non-model methods and two Gemma 4 sizes on the same bugs, with paired bootstrap intervals and an analysis plan fixed in advance.
3. A measured answer to when the model pays off: {{BREAKEVEN_SENTENCE}}

## 2. Task and data

**Repositories.** Four small pure-Python libraries (cachetools, toolz, humanize, sortedcontainers) and FastAPI, one of the four repositories in the competition's task set. Suites range from {{MIN_SUITE}} to {{FASTAPI_SUITE_S}} seconds on one core. Commits are pinned in the notebook.

**Bugs.** For each repository we parse every source module, list the sites where one operator can be swapped (comparisons, arithmetic, `and`/`or`, boolean and 0/1 constants), sample sites uniformly with a fixed seed, apply one swap, and run the full suite. A mutant is kept only if at least one test that passes on the original code now fails. We stop at 80 kept mutants per small library and 60 for FastAPI. Planted bugs are a common stand-in for real faults when ground truth must be exact (Just et al., 2014); Section 6 discusses what this costs.

**Ground truth and cost.** For every kept bug we store the ids of all failing tests. One extra clean run records each test's runtime and, with coverage.py's per-test contexts, which lines each test executed.

## 3. Methods

Every method returns a full ordering of the suite. A method that ranks only some tests is completed with the remaining tests in the suite's default order.

- **Full suite**: the default order pytest uses.
- **Name match**: tests whose name contains the changed function's name, or whose file contains the changed module's name, go first.
- **Reachability**: tests from which the changed function is reachable in the static call graph go first, in default order.
- **Graph distance**: the reachable tests, ordered by shortest-path length to the changed function.
- **Lexical similarity**: tests ordered by TF-IDF cosine between the changed function's source and each test's source.
- **Coverage**: tests that executed the changed line on the original code go first. This needs a recorded coverage run per test, so we treat it as an upper bound for a cheap method, not a competitor.
- **Gemma re-rank**: Gemma 4 E2B or E4B (4-bit QAT, run locally with Ollama, temperature 0) sees the diff, the changed function's source, its callers and callees from the graph, the 30 nearest tests by graph distance (numbered), and the names of all other tests. It returns up to 15 entries, each a candidate number or the exact name of another test (at most five). Unknown names are dropped and counted. Its list goes first, followed by the graph-distance order.

**Code graph.** We build a symbol graph from Python ASTs with `contains`, `calls` and `imports` edges, the same node and edge types as the graphs the competition gives its agents. Calls are resolved by name; a name that matches more than eight definitions is skipped. Like any static graph it misses calls made through inheritance, decorators and dynamic attributes.

**Metrics** (fixed in the analysis plan before any method ran). Primary: Recall@k, the share of bugs with at least one failing test in the first k tests, for k = 1, 5, 10 and 10% of the suite. Secondary: time to first failure (sum of per-test runtimes up to the first failing test, plus model wall time for Gemma rows), recovered static misses, and the break-even suite runtime. Intervals are 95% bootstrap intervals over bugs, stratified by repository, with 10,000 resamples.

## 4. Results

{{RESULTS}}

## 5. Related work

**Static and dynamic RTS.** Ekstazi (Gligoric et al., 2015) selects tests from recorded file dependencies; STARTS (Legunsen et al., 2017) does it statically from class-level dependencies. Google's pre-submit system ranks tests over a hybrid call graph at very large scale. Our graph-distance and coverage baselines are small versions of these two families.

**LLMs for test selection in agents.** Agentless (Xia et al., 2024) asks a hosted model which existing tests relate to an edit and drops patches that break them. TestPrune (2025) uses a model to predict suspicious methods from an issue and then minimises the regression suite through coverage. Both use large hosted models and judge success by downstream issue resolution. We isolate the selection step, use models small enough for a laptop, and score selection directly against a kill matrix.

**Mutants as faults.** Just et al. (2014) found that mutant detection correlates with real-fault detection for test suites, which supports using planted bugs to compare selection methods, though not to estimate absolute miss rates on real regressions.

## 6. Limitations

- **Planted bugs, not real regressions.** Single-operator mutants are local and usually caught by tests near the changed code. Real regressions can be wider. Absolute recall numbers should not be read as field estimates; the comparison between methods on the same bugs is the result.
- **Python only, five repositories.** The static graph's blind spots are Python's (inheritance, decorators, dynamic attributes). Languages with explicit types would give a denser graph and likely a smaller gap for the model.
- **One prompt, two small models.** We did not tune the prompt after seeing results. A better prompt or a larger model may do better; our numbers are a floor for this design.
- **Latency is hardware-specific.** Model times come from one Apple M5 laptop with 16 GB of memory. The break-even point moves with hardware and with how many tests can run in parallel.
- **Memorisation.** These are popular open-source projects that may be in Gemma's training data. The bugs themselves are new, but test names are not.

## 7. Reproducibility

The analysis plan (`analysis_plan.md`) was committed with SHA-256 `941004144a033e7b4edb5a011ad0ff34ab65da29c7ca4eaecf6deab4b74ca9fd` before any selection method ran. The public notebook {{NOTEBOOK_LINK}} contains the planted bugs, kill matrices, per-test runtimes and coverage, every model prompt and answer (cached by prompt hash), and the scripts. Running it on CPU rebuilds every table and figure without calling a model. Re-running the models needs Ollama with `gemma4:e2b-it-qat` and `gemma4:e4b-it-qat`.

## References

- Gligoric, M., Eloussi, L., and Marinov, D. (2015). Practical regression test selection with dynamic file dependencies. ISSTA.
- Legunsen, O., Shi, A., and Marinov, D. (2017). STARTS: STAtic regression test selection. ASE (tool demo).
- Just, R., Jalali, D., Inozemtseva, L., Ernst, M. D., Holmes, R., and Fraser, G. (2014). Are mutants a valid substitute for real faults in software testing? FSE.
- Xia, C. S., Deng, Y., Dunn, S., and Zhang, L. (2024). Agentless: Demystifying LLM-based software engineering agents. arXiv:2407.01489.
- When Old Meets New: Evaluating the impact of regression tests on SWE issue resolution (TestPrune) (2025). arXiv:2510.18270.
- Regression Test Selection at Scale. Google Research. https://research.google/pubs/regression-test-selection-at-scale-2/
- Jimenez, C. E., et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? ICLR.
- Markowitz, E., et al. (2026). Google - The Gemma 4 Developer Agent Competition. Kaggle.
