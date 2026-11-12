## Real regressions: competition Rich tasks with the fix undone (n = 36 tasks)

Median failing tests per task: 1

| Method | R@1 | R@5 | R@10 |
|---|---|---|---|
| Full suite order | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| Name match | 0.06 [0.00, 0.14] | 0.19 [0.08, 0.33] | 0.25 [0.11, 0.39] |
| Reachability | 0.00 [0.00, 0.00] | 0.06 [0.00, 0.14] | 0.08 [0.00, 0.17] |
| Graph distance | 0.06 [0.00, 0.14] | 0.14 [0.03, 0.25] | 0.17 [0.06, 0.31] |
| Lexical similarity | 0.06 [0.00, 0.14] | 0.19 [0.08, 0.33] | 0.25 [0.11, 0.39] |
| Provided graph | 0.03 [0.00, 0.08] | 0.03 [0.00, 0.08] | 0.03 [0.00, 0.08] |
| Provided embeddings | 0.00 [0.00, 0.00] | 0.06 [0.00, 0.14] | 0.06 [0.00, 0.14] |
| Coverage (upper bound) | 0.06 [0.00, 0.14] | 0.22 [0.08, 0.36] | 0.31 [0.17, 0.47] |
| Gemma 4 E2B re-rank | 0.11 [0.03, 0.22] | 0.22 [0.08, 0.36] | 0.25 [0.11, 0.39] |
| Gemma 4 E4B re-rank | 0.14 [0.03, 0.25] | 0.33 [0.19, 0.50] | 0.36 [0.19, 0.53] |
| Gemma 4 E2B, prompt v2 | 0.17 [0.06, 0.31] | 0.42 [0.25, 0.58] | 0.42 [0.25, 0.58] |
| Gemma 4 E4B, prompt v2 | 0.08 [0.00, 0.19] | 0.22 [0.08, 0.36] | 0.31 [0.17, 0.47] |

| Method | R@10% of suite | median rank of first failing test |
|---|---|---|
| Full suite order | 0.08 [0.00, 0.19] | 418 |
| Name match | 0.83 [0.69, 0.94] | 25 |
| Reachability | 0.11 [0.03, 0.22] | 404 |
| Graph distance | 0.31 [0.17, 0.47] | 346 |
| Lexical similarity | 0.67 [0.50, 0.81] | 34 |
| Provided graph | 0.08 [0.00, 0.19] | 833 |
| Provided embeddings | 0.08 [0.00, 0.19] | 832 |
| Coverage (upper bound) | 0.72 [0.58, 0.86] | 21 |
| Gemma 4 E2B re-rank | 0.33 [0.19, 0.50] | 313 |
| Gemma 4 E4B re-rank | 0.47 [0.31, 0.64] | 189 |
| Gemma 4 E2B, prompt v2 | 0.53 [0.36, 0.69] | 27 |
| Gemma 4 E4B, prompt v2 | 0.75 [0.61, 0.89] | 21 |

- Gemma 4 E2B re-rank minus Graph distance, Recall@10: +0.083 [+0.000, +0.194]
- Gemma 4 E2B re-rank minus Lexical similarity, Recall@10: +0.000 [-0.167, +0.167]
- Gemma 4 E4B re-rank minus Graph distance, Recall@10: +0.194 [+0.083, +0.333]
- Gemma 4 E4B re-rank minus Lexical similarity, Recall@10: +0.111 [-0.111, +0.333]
- Gemma 4 E2B, prompt v2 minus Graph distance, Recall@10: +0.250 [+0.111, +0.389]
- Gemma 4 E2B, prompt v2 minus Lexical similarity, Recall@10: +0.167 [+0.028, +0.306]
- Gemma 4 E4B, prompt v2 minus Graph distance, Recall@10: +0.139 [+0.000, +0.278]
- Gemma 4 E4B, prompt v2 minus Lexical similarity, Recall@10: +0.056 [-0.167, +0.278]
