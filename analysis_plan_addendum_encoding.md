# Addendum: graph-encoding ablation (frozen before any run)

Question: does the way the code graph is written into the prompt change how well Gemma 4 orders tests? This follows work showing that graph-to-text encodings change LLM accuracy on graph tasks (Fatemi, Halcrow and Perozzi, ICLR 2024; Markowitz et al., 2025).

Arms (prompt v1 otherwise unchanged, Gemma 4 E2B, temperature 0):
- none: candidates (the 30 nearest tests by graph distance) without distances, callers or callees.
- list: prompt v1 as run (callers and callees by name, graph distance per candidate). Reused from the cache.
- path: as list, plus for each candidate its shortest call path from the test to the changed function, written as "test -> f -> g -> changed".

Data: planted bugs in cachetools, toolz and python-sortedcontainers (the libraries whose suites the static graph reaches), and the 36 Rich real regressions.

Outcome: Recall@10 per arm; paired differences path minus list and none minus list, 95% bootstrap intervals. This is exploratory and reported whatever the direction.
