#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
C=fastapi_f1d750fddad90e2faad6c3cc5c85c7687b787e89
.venv-fastapi/bin/python infra/select_tests.py fastapi data/v2/mut_fastapi.jsonl data/prof_fastapi data/v2/rank_fastapi.jsonl && echo ranked
.venv/bin/python infra/select_provided.py data/v2/rank_fastapi.jsonl data/v2/mut_fastapi.jsonl comp/graphs/$C.json comp/embeddings/$C.npz
for model in gemma4:e2b-it-qat gemma4:e4b-it-qat; do
  tag=${model#gemma4:}; tag=${tag%%-*}
  .venv/bin/python infra/rerank.py fastapi data/v2/rank_fastapi.jsonl data/v2/mut_fastapi.jsonl $model data/rr/rr_${tag}_fastapi.jsonl data/rr/cache
  echo "$model fastapi $(wc -l < data/rr/rr_${tag}_fastapi.jsonl)"
done
echo FASTAPI_DONE
