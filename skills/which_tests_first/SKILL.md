---
name: which_tests_first
description: After you edit code, list the tests most likely to catch a mistake in your edit, so you can run those first instead of the whole suite.
---

# Which tests should run first?

Use this after every edit, before running tests.

1. Run the script `order_tests.py` (no arguments needed; it reads `git diff HEAD` in the current repository).
2. It prints up to 30 test ids, best first, and the test files they come from. Half are tests close to your changed functions in the call graph; half are tests whose source shares the most identifiers with your changed functions.
3. Read the list and your diff. Put first the tests that exercise the behaviour you changed, including tests that reach your code through syntax (`in` calls `__contains__`, a `for` loop calls `__iter__`) or through a framework (for example a web test client).
4. Run those tests first, for example `python -m pytest -x -q <ids>`. If they all pass, run the test files listed at the end, then the full suite.

The ordering costs no model calls and takes a few seconds on a large repository. In our measurements on real regressions replayed from this competition's tasks, ordering of this kind reached the first failing test after a median of under one second of test time, against about three seconds for the default order.
