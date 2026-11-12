
## Recall@k, all repos pooled (n = 375 bugs), 95% stratified bootstrap

| Method | R@1 | R@5 | R@10 | R@10% of suite |
|---|---|---|---|---|
| full | 0.07 [0.04, 0.09] | 0.09 [0.07, 0.12] | 0.12 [0.09, 0.15] | 0.32 [0.28, 0.37] |
| name | 0.08 [0.05, 0.10] | 0.23 [0.19, 0.27] | 0.30 [0.26, 0.35] | 0.53 [0.48, 0.58] |
| reach | 0.26 [0.22, 0.30] | 0.36 [0.31, 0.41] | 0.45 [0.40, 0.49] | 0.69 [0.64, 0.73] |
| graphdist | 0.34 [0.29, 0.39] | 0.48 [0.43, 0.53] | 0.56 [0.51, 0.61] | 0.72 [0.68, 0.76] |
| lexical | 0.24 [0.20, 0.28] | 0.46 [0.41, 0.51] | 0.58 [0.53, 0.62] | 0.82 [0.78, 0.86] |
| coverage | 0.61 [0.56, 0.65] | 0.79 [0.75, 0.83] | 0.83 [0.79, 0.87] | 0.93 [0.91, 0.95] |
| e2b | 0.40 [0.35, 0.45] | 0.55 [0.51, 0.61] | 0.61 [0.57, 0.66] | 0.75 [0.70, 0.79] |
| e4b | 0.35 [0.31, 0.40] | 0.59 [0.54, 0.63] | 0.66 [0.62, 0.71] | 0.80 [0.77, 0.84] |

## Recall@10 by repository

| Repo | n | suite tests | suite s | static misses | full | name | reach | graphdist | lexical | coverage | e2b | e4b |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cachetools | 79 | 416 | 1.9 | 48 | 0.16 | 0.52 | 0.32 | 0.42 | 0.54 | 0.78 | 0.53 | 0.62 |
| toolz | 78 | 192 | 2.0 | 24 | 0.14 | 0.50 | 0.65 | 0.67 | 0.76 | 0.96 | 0.74 | 0.81 |
| humanize | 80 | 746 | 1.9 | 0 | 0.00 | 0.25 | 0.68 | 0.69 | 0.39 | 0.88 | 0.71 | 0.68 |
| python-sortedcontainers | 78 | 366 | 23.5 | 16 | 0.26 | 0.05 | 0.38 | 0.62 | 0.83 | 0.91 | 0.65 | 0.77 |
| fastapi | 60 | 3207 | 31.3 | 29 | 0.00 | 0.17 | 0.12 | 0.35 | 0.30 | 0.57 | 0.37 | 0.37 |

## Paired difference in Recall@10: model minus graph distance

- Gemma 4 E2B: +0.056 [+0.032, +0.083]
- Gemma 4 E4B: +0.104 [+0.067, +0.141]

## Exploratory (not in the plan): model minus lexical similarity, Recall@10

- Gemma 4 E2B: +0.037 [-0.019, +0.091]
- Gemma 4 E4B: +0.085 [+0.029, +0.139]

## Time to first failure (median seconds; model time included for model rows)

| Repo | full | name | reach | graphdist | lexical | coverage | e2b | e4b |
|---|---|---|---|---|---|---|---|---|
| cachetools | 0.40 | 0.08 | 0.15 | 0.15 | 0.02 | 0.02 | 3.32 | 9.68 |
| toolz | 1.64 | 0.04 | 0.06 | 0.01 | 0.01 | 0.01 | 1.37 | 13.11 |
| humanize | 0.70 | 0.14 | 0.01 | 0.01 | 0.02 | 0.00 | 9.53 | 25.32 |
| python-sortedcontainers | 2.25 | 0.45 | 0.12 | 0.04 | 5.03 | 0.01 | 1.98 | 6.69 |
| fastapi | 5.02 | 0.35 | 1.53 | 1.47 | 0.17 | 0.01 | 10.04 | 29.52 |

## Exploratory (not in the plan): break-even suite runtime

Every test's runtime is multiplied by s while model time stays fixed. Break-even is the smallest s at which the model's MEAN time to first failure is at or below graph distance's; reported as s x measured suite runtime.

- Gemma 4 E2B, cachetools: test time to first failure 0.44s (model order) vs 0.49s (graph distance), model 2.9s; break-even at x52.6, a suite of about 98s
- Gemma 4 E2B, toolz: test time to first failure 0.42s (model order) vs 0.43s (graph distance), model 1.3s; break-even at x123.7, a suite of about 251s
- Gemma 4 E2B, humanize: test time to first failure 0.02s (model order) vs 0.03s (graph distance), model 9.5s; break-even at x756.9, a suite of about 1438s
- Gemma 4 E2B, python-sortedcontainers: test time to first failure 2.18s (model order) vs 2.35s (graph distance), model 1.8s; break-even at x10.9, a suite of about 257s
- Gemma 4 E2B, fastapi: test time to first failure 5.00s (model order) vs 5.01s (graph distance), model 8.9s; break-even at x1037.7, a suite of about 32478s
- Gemma 4 E2B, pooled: test time to first failure 1.44s (model order) vs 1.49s (graph distance), model 4.7s; break-even at x88.9, a suite of about 989s
- Gemma 4 E4B, cachetools: test time to first failure 0.32s (model order) vs 0.49s (graph distance), model 10.7s; break-even at x61.0, a suite of about 114s
- Gemma 4 E4B, toolz: test time to first failure 0.34s (model order) vs 0.43s (graph distance), model 12.8s; break-even at x143.2, a suite of about 290s
- Gemma 4 E4B, humanize: test time to first failure 0.02s (model order) vs 0.03s (graph distance), model 27.9s; break-even at x2019.4, a suite of about 3837s
- Gemma 4 E4B, python-sortedcontainers: test time to first failure 1.65s (model order) vs 2.35s (graph distance), model 6.9s; break-even at x9.8, a suite of about 232s
- Gemma 4 E4B, fastapi: test time to first failure 5.00s (model order) vs 5.01s (graph distance), model 28.2s; break-even at x3729.1, a suite of about 116712s
- Gemma 4 E4B, pooled: test time to first failure 1.28s (model order) vs 1.49s (graph distance), model 16.8s; break-even at x81.7, a suite of about 909s

## Static misses and the model

- Gemma 4 E2B: recovered 18 of 117 static misses; proposed outside tests on 59 bugs, 41 of those had no failing proposal; 408 unknown names; 0 unparsable answers; median model time 2.5s
- Gemma 4 E4B: recovered 40 of 117 static misses; proposed outside tests on 181 bugs, 135 of those had no failing proposal; 174 unknown names; 28 unparsable answers; median model time 13.9s

## Competition snapshot: our AST graph vs the provided graph and embeddings (n = 60)

Changed function found in provided graph: 55; in provided embeddings: 55; no failing test reachable in provided graph: 31; in our graph: 29

| Method | R@1 | R@5 | R@10 |
|---|---|---|---|
| graphdist | 0.25 [0.15, 0.37] | 0.33 [0.22, 0.45] | 0.35 [0.23, 0.47] |
| pgraph | 0.07 [0.02, 0.13] | 0.15 [0.07, 0.25] | 0.22 [0.12, 0.32] |
| lexical | 0.17 [0.08, 0.27] | 0.27 [0.17, 0.38] | 0.30 [0.18, 0.42] |
| pemb | 0.17 [0.08, 0.27] | 0.20 [0.10, 0.30] | 0.32 [0.20, 0.43] |
| e2b | 0.32 [0.20, 0.43] | 0.37 [0.25, 0.48] | 0.37 [0.25, 0.48] |
| e4b | 0.23 [0.13, 0.35] | 0.32 [0.20, 0.43] | 0.37 [0.25, 0.48] |
| coverage | 0.32 [0.20, 0.43] | 0.52 [0.38, 0.65] | 0.57 [0.45, 0.68] |
