## Graph-encoding ablation, Gemma 4 E2B, Recall@10

| Set | n | graph distance (no model) | none | list (prompt v1) | path |
|---|---|---|---|---|---|
| planted | 235 | 0.57 | 0.64 | 0.64 | 0.62 |
| Rich real | 36 | 0.17 | 0.25 | 0.25 | 0.25 |

- planted: path minus list: -0.021 [-0.051, +0.004]
- planted: none minus list: -0.004 [-0.038, +0.030]
- Rich real: path minus list: +0.000 [-0.083, +0.083]
- Rich real: none minus list: +0.000 [-0.083, +0.083]
