# Addendum to the analysis plan: prompt v2 (frozen before any held-out run)

Written after the FastAPI real-regression results, and before prompt v2 has been run on any Rich task or any planted bug.

## Why a second prompt
On 40 real FastAPI regressions the first prompt added nothing over graph distance. Only 4 of 40 tasks had a failing test among the 30 graph candidates the model saw, and the list of other test names was cut at 600 of about 3,200. Prompt v2 (`rts/rerank2.py`) changes only the inputs: 15 candidates from graph distance plus 15 from lexical similarity, and the full list of test files (the model may name up to 3 files; all their tests run). Everything else (models, temperature 0, output format, scoring) is unchanged.

## Status of the FastAPI result
Prompt v2 was designed after seeing the 40 FastAPI tasks, so its FastAPI result is reported as post hoc (exploratory).

## Held-out confirmation
- Data: real regressions built the same way from the competition's Rich (Textualize/rich) tasks: base commit with its own dependencies, fix and its tests applied, fix undone; tests that pass with the fix and fail without it are the ground truth.
- Primary outcome: paired difference in Recall@10, prompt v2 (E4B) minus graph distance, 95% bootstrap interval over tasks. A claim needs the interval to exclude zero. E2B and the comparison with lexical similarity are secondary.
- Also reported: prompt v2 on the 375 planted bugs, against prompt v1, whatever the direction.
