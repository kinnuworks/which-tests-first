# Which tests should run first?

After a code change, a small Gemma 4 model running on a laptop reads the code graph and orders the tests so the one that catches a bug runs early.

The code graph alone misses tests that reach the changed code through inheritance, decorators or attribute calls. A small local model can read the code and suggest those tests, but it costs seconds per change, so we also measure the suite runtime at which it pays off.

![Bugs caught within the first k tests](paper/figs/fig1_recall_at_k.png)

**Paper:** [paper/paper.md](paper/paper.md) · **Kaggle notebook:** {{NOTEBOOK_LINK}} · **Analysis plan (frozen before any method ran):** [analysis_plan.md](analysis_plan.md)

## Rebuild every number (about two minutes, CPU only, no model needed)

```bash
git clone https://github.com/kinnuworks/which-tests-first.git
cd which-tests-first
pip install networkx matplotlib
python rts/analyze.py data cachetools toolz humanize python-sortedcontainers fastapi
python rts/figures.py data paper/figs
```

All Gemma 4 prompts and answers are cached in `data/rr/cache`, keyed by the SHA-256 of model name and prompt.

## What is in the repository

- `rts/mutate.py` plants single-operator bugs and records which tests catch each one.
- `rts/codegraph.py` builds the call graph from Python ASTs.
- `rts/select_tests.py` ranks tests with the six non-model methods; `rts/select_provided.py` adds rankings from the competition's provided code graph and embeddings.
- `rts/rerank.py` asks Gemma 4 (via Ollama, temperature 0) to re-rank the tests and caches every answer.
- `rts/analyze.py` and `rts/figures.py` build the tables and figures.
- `data/` holds the planted bugs, kill matrices, per-test runtimes, every method's rankings and the cached model answers.

## Re-running the models

Install [Ollama](https://ollama.com), pull `gemma4:e2b-it-qat` and `gemma4:e4b-it-qat`, then run `rts/rerank.py` per repository (see the top of the file). With the cache in place a rerun reads the stored answers.

## Licence

Apache 2.0.
