## Abstract

Planted bugs are the usual way to score test selection, because their ground truth is free, but they overstate how well every method works. RegressionReplay turns SWE-style task sets into real regressions with exact ground truth by undoing real fixes and recording which tests then fail. From this competition's own tasks it provides 84 real regressions (40 FastAPI, 36 Rich, 8 requests), 375 planted bugs with full kill matrices, per-test runtimes and coverage, rankings and cached Gemma 4 answers for ten test-ordering methods, a builder that extends it to any task set, and a drop-in ADK skill for the competition's agent harness. Everything rebuilds from public files in a public notebook.

## 1. Introduction

**RegressionReplay** turns SWE-style task sets into real regressions with exact ground truth, so test selection and agent self-checking can be measured on real bugs instead of planted ones. It ships three things:

1. **A builder** (`rts/build_real.py`) that replays any task with a base commit, a fix and its tests: check out the base commit with its own dependencies, apply the fix and its tests, then undo the fix. Tests that pass with the fix and fail without it are the ground truth. Tasks that add new code, time out, or fail with the fix applied are dropped automatically.
2. **The replayed data** from this competition's own tasks: 40 FastAPI, 36 Rich and 8 requests regressions, each with the changed function, every failing test id, per-test runtimes and per-test coverage of the fixed state, plus 375 planted single-operator bugs in five repositories with full kill matrices (which tests fail for each bug).
3. **Rankings and model answers for ten test-ordering methods**, including the competition's provided code graph and embeddings and Gemma 4 E2B and E4B, so new methods can be compared on the same tasks, and a drop-in ADK skill (`skills/which_tests_first`) in the competition's submission format.

## 2. Why it is needed

Planted bugs are the usual way to score test selection because their ground truth is free. Our companion paper shows how much they flatter every method: the best methods put a failing test in the first 10 tests for 56% to 66% of planted bugs but only 17% to 37% of the 84 real regressions, and coverage, an upper bound on planted bugs, ranks near the bottom on real FastAPI regressions because the failing tests are new tests written with the fix. Any team building an agent that checks its own patches, as in this competition, faces exactly that real case.

## 3. Construction (methods)

- **Source tasks:** the competition's `tasks.jsonl` (FastAPI, Rich and requests tasks). Only derived records are published: task id, changed file and function, failing test ids, runtimes and rankings. Patches and problem statements are not redistributed; the builder regenerates everything from the competition data.
- **Environments:** each task's base commit is installed with its own pinned dependencies (FastAPI through its `uv.lock`); a task is kept only if at most 20 tests fail with the fix applied.
- **Checks:** the published data rebuilds every table in the paper with one command, and the public Kaggle notebook reruns it on CPU in about 2.5 minutes.

**Table 1.** Contents.

| Set | Tasks | Distinct changed functions | Failing tests (total) |
|---|---|---|---|
| FastAPI real regressions | 40 | 27 | 449 |
| Rich real regressions | 36 | 33 | 71 |
| requests real regressions | 8 | 6 | 340 |
| Planted bugs, five repositories | 375 | | full kill matrices |

## 4. Experiments: baselines on the resource

**Table 2.** Recall@10 (share of tasks with a failing test among the first 10 tests run) on the real regressions, 95% bootstrap intervals over tasks.

| Method | FastAPI (40) | Rich (36) | requests (8) | All 84, pooled |
|---|---|---|---|---|
| Graph distance | 0.10 [0.03, 0.20] | 0.17 [0.06, 0.31] | 0.50 [0.12, 0.88] | 0.17 [0.10, 0.25] |
| Lexical similarity | 0.12 [0.03, 0.23] | 0.25 [0.11, 0.39] | 0.38 [0.00, 0.75] | 0.20 [0.12, 0.29] |
| Gemma 4 E4B re-rank | 0.10 [0.03, 0.20] | 0.36 [0.19, 0.53] | 0.62 [0.25, 0.88] | 0.26 [0.18, 0.36] |
| Gemma 4 E2B re-rank, prompt v2 | 0.25 [0.12, 0.40] | 0.42 [0.25, 0.58] | 0.75 [0.38, 1.00] | 0.37 [0.27, 0.46] |

The same methods reach 0.56 to 0.66 on the planted bugs. The released skill's model-free ordering (graph distance interleaved with shared identifiers) was never worse than graph distance in any of the 8 settings (5 planted repositories, 3 real) and added 6.5 points pooled over all 459 bugs and regressions. Full results, including the provided graph and embeddings, are in the companion paper and the notebook.

## 5. How to use it

- **Evaluate a test-selection method:** rank the tests for each record, then run `rts/analyze_real.py` for Recall@k, median rank of the first failing test and test-seconds to first failure, with bootstrap intervals.
- **Extend it:** point the builder at any task set with base commits, fixes and test patches (`RT_REPO`, `RT_PKG`, `RT_REPONAME` environment variables).
- **Use it in an agent:** add `skills/which_tests_first` to `agent.yaml`; after each edit the agent gets its tests ordered by call-graph distance and shared identifiers, with no model call.

## 6. Related work

Defects4J (Just, Jalali and Ernst, 2014) and BugsInPy (Widyasari et al., 2020) collect real bugs with failing tests for Java and Python; SWE-bench (Jimenez et al., 2024) pairs real issues with fixes and tests for agents. RegressionReplay reuses such task sets for a different question, which tests to run first after a change, and adds what that question needs: per-test runtimes, coverage and kill matrices for every test in the suite, and baselines from classic regression test selection (Gligoric et al., 2015; Legunsen et al., 2017) to small local models. Mutant studies (Just et al., 2014) motivate planted bugs; our real sets measure the gap.

## 7. Limits

Python only; three repositories (only 8 tasks from requests); real sets are small (tens of tasks each) and some candidate tasks are dropped by the filters above. Runtimes come from one laptop.

## References

- Just, R., Jalali, D., and Ernst, M. D. (2014). Defects4J: A database of existing faults to enable controlled testing studies for Java programs. ISSTA.
- Widyasari, R., et al. (2020). BugsInPy: A database of existing bugs in Python programs to enable controlled testing and debugging studies. ESEC/FSE (demo).
- Jimenez, C. E., et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? ICLR.
- Gligoric, M., Eloussi, L., and Marinov, D. (2015). Practical regression test selection with dynamic file dependencies. ISSTA.
- Legunsen, O., Shi, A., and Marinov, D. (2017). STARTS: STAtic regression test selection. ASE.
- Just, R., Jalali, D., Inozemtseva, L., Ernst, M. D., Holmes, R., and Fraser, G. (2014). Are mutants a valid substitute for real faults in software testing? FSE.
- Markowitz, E., et al. (2026). Google - The Gemma 4 Developer Agent Competition. Kaggle.

## Links

- Code, data, cached model answers and the ADK skill: https://github.com/kinnuworks/which-tests-first
- Notebook that rebuilds every number: https://www.kaggle.com/code/dhirajkavuri/which-tests-should-run-first-rebuild-every-number
