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

- Gemma 4 E2B re-rank minus Graph distance, Recall@10: +0.000 [+0.000, +0.000]
- Gemma 4 E2B re-rank minus Lexical similarity, Recall@10: -0.025 [-0.125, +0.075]
- Gemma 4 E4B re-rank minus Graph distance, Recall@10: +0.000 [+0.000, +0.000]
- Gemma 4 E4B re-rank minus Lexical similarity, Recall@10: -0.025 [-0.125, +0.075]
