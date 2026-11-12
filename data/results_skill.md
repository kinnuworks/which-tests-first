## Recall@10 by setting: graph distance, lexical, skill ordering (no model), Gemma 4 E4B

| Setting | n | Graph distance | Lexical | Skill (no model) | E4B |
|---|---|---|---|---|---|
| planted: cachetools | 79 | 0.42 | 0.54 | 0.53 | 0.62 |
| planted: toolz | 78 | 0.67 | 0.76 | 0.74 | 0.81 |
| planted: humanize | 80 | 0.69 | 0.39 | 0.69 | 0.68 |
| planted: python-sortedcontainers | 78 | 0.62 | 0.83 | 0.65 | 0.77 |
| planted: fastapi | 60 | 0.35 | 0.30 | 0.45 | 0.37 |
| real: FastAPI | 40 | 0.10 | 0.12 | 0.17 | 0.10 |
| real: Rich | 36 | 0.17 | 0.25 | 0.25 | 0.36 |
| real: requests | 8 | 0.50 | 0.38 | 0.50 | 0.62 |

- e4b vs graph distance across 8 settings: better in 6, tied in 1, worse in 1 (one-sided sign test over non-ties, p = 0.062)
- skill vs graph distance across 8 settings: better in 6, tied in 2, worse in 0 (one-sided sign test over non-ties, p = 0.016)
- skill minus graph distance, all 459 bugs pooled: +0.065 [+0.039, +0.094]
- e4b minus graph distance, all 459 bugs pooled: +0.102 [+0.070, +0.135]
