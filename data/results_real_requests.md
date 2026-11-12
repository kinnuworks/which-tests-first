## Real regressions: competition requests tasks with the fix undone (n = 8 tasks)

Median failing tests per task: 1

| Method | R@1 | R@5 | R@10 |
|---|---|---|---|
| Full suite order | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] |
| Name match | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] |
| Reachability | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] |
| Graph distance | 0.25 [0.00, 0.62] | 0.50 [0.12, 0.88] | 0.50 [0.12, 0.88] |
| Lexical similarity | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] | 0.38 [0.00, 0.75] |
| Provided graph | 0.00 [0.00, 0.00] | 0.12 [0.00, 0.38] | 0.25 [0.00, 0.62] |
| Provided embeddings | 0.12 [0.00, 0.38] | 0.25 [0.00, 0.62] | 0.25 [0.00, 0.62] |
| Coverage (upper bound) | 0.25 [0.00, 0.62] | 0.38 [0.12, 0.75] | 0.38 [0.12, 0.75] |
| Gemma 4 E2B re-rank | 0.25 [0.00, 0.62] | 0.50 [0.12, 0.88] | 0.50 [0.12, 0.88] |
| Gemma 4 E4B re-rank | 0.25 [0.00, 0.62] | 0.62 [0.25, 0.88] | 0.62 [0.25, 0.88] |
| Gemma 4 E2B, prompt v2 | 0.25 [0.00, 0.62] | 0.62 [0.25, 0.88] | 0.75 [0.38, 1.00] |
| Gemma 4 E4B, prompt v2 | 0.38 [0.12, 0.75] | 0.88 [0.62, 1.00] | 0.88 [0.62, 1.00] |

| Method | R@10% of suite | median rank of first failing test |
|---|---|---|
| Full suite order | 0.38 [0.12, 0.75] | 233 |
| Name match | 0.38 [0.12, 0.75] | 138 |
| Reachability | 0.50 [0.12, 0.88] | 210 |
| Graph distance | 0.75 [0.38, 1.00] | 18 |
| Lexical similarity | 1.00 [1.00, 1.00] | 22 |
| Provided graph | 0.25 [0.00, 0.62] | 413 |
| Provided embeddings | 0.25 [0.00, 0.62] | 442 |
| Coverage (upper bound) | 0.62 [0.25, 1.00] | 33 |
| Gemma 4 E2B re-rank | 0.75 [0.38, 1.00] | 18 |
| Gemma 4 E4B re-rank | 0.75 [0.38, 1.00] | 5 |
| Gemma 4 E2B, prompt v2 | 0.88 [0.62, 1.00] | 5 |
| Gemma 4 E4B, prompt v2 | 1.00 [1.00, 1.00] | 2 |

| Method | median test-seconds to first failure | mean |
|---|---|---|
| Full suite order | 20.44 | 35.50 |
| Name match | 0.10 | 7.65 |
| Reachability | 20.42 | 35.45 |
| Graph distance | 0.02 | 5.89 |
| Lexical similarity | 5.76 | 3.57 |
| Provided graph | 72.30 | 53.85 |
| Provided embeddings | 72.31 | 53.92 |
| Coverage (upper bound) | 15.22 | 21.60 |
| Gemma 4 E2B re-rank | 0.02 | 5.89 |
| Gemma 4 E4B re-rank | 0.01 | 5.89 |
| Gemma 4 E2B, prompt v2 | 0.02 | 0.22 |
| Gemma 4 E4B, prompt v2 | 0.01 | 0.01 |

Full-suite test time per task: median 73.4 s

- Gemma 4 E2B re-rank minus Graph distance, Recall@10: +0.000 [+0.000, +0.000]
- Gemma 4 E2B re-rank minus Lexical similarity, Recall@10: +0.125 [-0.375, +0.625]
- Gemma 4 E4B re-rank minus Graph distance, Recall@10: +0.125 [+0.000, +0.375]
- Gemma 4 E4B re-rank minus Lexical similarity, Recall@10: +0.250 [-0.375, +0.750]
- Gemma 4 E2B, prompt v2 minus Graph distance, Recall@10: +0.250 [+0.000, +0.500]
- Gemma 4 E2B, prompt v2 minus Lexical similarity, Recall@10: +0.375 [+0.000, +0.750]
- Gemma 4 E4B, prompt v2 minus Graph distance, Recall@10: +0.375 [+0.125, +0.750]
- Gemma 4 E4B, prompt v2 minus Lexical similarity, Recall@10: +0.500 [+0.125, +0.875]
