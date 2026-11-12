## Prompt v2 on planted bugs (n = 375), Recall@10

| Repo | graphdist | lexical | e2b_v1 | e4b_v1 | e2b_v2 | e4b_v2 |
|---|---|---|---|---|---|---|
| cachetools | 0.42 | 0.54 | 0.53 | 0.62 | 0.57 | 0.66 |
| toolz | 0.67 | 0.76 | 0.74 | 0.81 | 0.79 | 0.69 |
| humanize | 0.69 | 0.39 | 0.71 | 0.68 | 0.71 | 0.75 |
| python-sortedcontainers | 0.62 | 0.83 | 0.65 | 0.77 | 0.71 | 0.44 |
| fastapi | 0.35 | 0.30 | 0.37 | 0.37 | 0.45 | 0.42 |
| pooled | 0.56 | 0.58 | 0.61 | 0.66 | 0.66 | 0.60 |

- e4b_v2 minus graphdist: +0.043 [+0.000, +0.085]
- e2b_v2 minus graphdist: +0.099 [+0.059, +0.139]
- e4b_v2 minus e4b_v1: -0.061 [-0.104, -0.019]
- e2b_v2 minus e2b_v1: +0.043 [+0.000, +0.085]
