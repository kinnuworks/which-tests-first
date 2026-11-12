# Addendum: memorisation probe (frozen before any run)

Question: are the model's gains explained by memorised knowledge of these public repositories' test suites?

Probe ("blind recall"): Gemma 4 E2B and E4B, temperature 0, get only the repository name, the changed function's qualified name and file path. No code, no diff, no candidate tests. They return up to 10 test function names that would most likely fail.

Measures, per bug:
- Exists: at least one named test exists in the suite (base name match).
- Blind hit: at least one named test is among the tests that fail for this bug.

Data: the 375 planted bugs and the 84 real regressions.

Reading: compare the blind-hit rate with the re-ranker's Recall@10 on the same bugs. If blind hits are far below the re-ranker's gain over graph distance, memorised test names cannot explain that gain. Exploratory; reported whatever the result.
