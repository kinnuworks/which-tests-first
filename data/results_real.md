## Real regressions: competition FastAPI tasks with the fix undone (n = 40 tasks)

Median failing tests per task: 2

| Method | R@1 | R@5 | R@10 |
|---|---|---|---|
| Full suite order | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| Name match | 0.03 [0.00, 0.07] | 0.07 [0.00, 0.17] | 0.07 [0.00, 0.17] |
| Reachability | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.07] |
| Graph distance | 0.05 [0.00, 0.12] | 0.07 [0.00, 0.17] | 0.10 [0.03, 0.20] |
| Lexical similarity | 0.05 [0.00, 0.12] | 0.10 [0.03, 0.20] | 0.12 [0.03, 0.23] |
| Provided graph | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| Provided embeddings | 0.03 [0.00, 0.07] | 0.03 [0.00, 0.07] | 0.03 [0.00, 0.07] |
| Coverage (upper bound) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.07] |
| Gemma 4 E2B re-rank | 0.05 [0.00, 0.12] | 0.07 [0.00, 0.17] | 0.10 [0.03, 0.20] |
| Gemma 4 E4B re-rank | 0.05 [0.00, 0.12] | 0.10 [0.03, 0.20] | 0.10 [0.03, 0.20] |
| Gemma 4 E2B, prompt v2 | 0.10 [0.03, 0.20] | 0.17 [0.07, 0.30] | 0.25 [0.12, 0.40] |
| Gemma 4 E4B, prompt v2 | 0.17 [0.07, 0.30] | 0.23 [0.10, 0.38] | 0.28 [0.15, 0.42] |

| Method | R@10% of suite | median rank of first failing test |
|---|---|---|
| Full suite order | 0.23 [0.10, 0.35] | 732 |
| Name match | 0.25 [0.12, 0.40] | 663 |
| Reachability | 0.33 [0.17, 0.47] | 631 |
| Graph distance | 0.45 [0.30, 0.60] | 422 |
| Lexical similarity | 0.60 [0.45, 0.75] | 217 |
| Provided graph | 0.20 [0.07, 0.33] | 736 |
| Provided embeddings | 0.12 [0.03, 0.23] | 2574 |
| Coverage (upper bound) | 0.28 [0.15, 0.42] | 566 |
| Gemma 4 E2B re-rank | 0.42 [0.28, 0.57] | 422 |
| Gemma 4 E4B re-rank | 0.42 [0.28, 0.57] | 422 |
| Gemma 4 E2B, prompt v2 | 0.57 [0.42, 0.72] | 189 |
| Gemma 4 E4B, prompt v2 | 0.57 [0.42, 0.72] | 199 |

| Method | median test-seconds to first failure | mean |
|---|---|---|
| Full suite order | 3.41 | 3.83 |
| Name match | 3.04 | 3.65 |
| Reachability | 2.39 | 3.23 |
| Graph distance | 1.60 | 2.62 |
| Lexical similarity | 0.63 | 2.61 |
| Provided graph | 3.28 | 3.80 |
| Provided embeddings | 11.61 | 11.32 |
| Coverage (upper bound) | 3.04 | 3.45 |
| Gemma 4 E2B re-rank | 1.60 | 2.63 |
| Gemma 4 E4B re-rank | 1.62 | 2.62 |
| Gemma 4 E2B, prompt v2 | 0.84 | 2.25 |
| Gemma 4 E4B, prompt v2 | 0.63 | 2.12 |

Full-suite test time per task: median 14.2 s

- Gemma 4 E2B re-rank minus Graph distance, Recall@10: +0.000 [+0.000, +0.000]
- Gemma 4 E2B re-rank minus Lexical similarity, Recall@10: -0.025 [-0.125, +0.075]
- Gemma 4 E4B re-rank minus Graph distance, Recall@10: +0.000 [+0.000, +0.000]
- Gemma 4 E4B re-rank minus Lexical similarity, Recall@10: -0.025 [-0.125, +0.075]
- Gemma 4 E2B, prompt v2 minus Graph distance, Recall@10: +0.150 [+0.050, +0.275]
- Gemma 4 E2B, prompt v2 minus Lexical similarity, Recall@10: +0.125 [+0.000, +0.250]
- Gemma 4 E4B, prompt v2 minus Graph distance, Recall@10: +0.175 [+0.075, +0.300]
- Gemma 4 E4B, prompt v2 minus Lexical similarity, Recall@10: +0.150 [+0.000, +0.300]
