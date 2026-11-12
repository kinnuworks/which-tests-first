#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
until grep -q MODELS_DONE data/rr/run.log 2>/dev/null; do sleep 30; done
for model in gemma4:e2b-it-qat gemma4:e4b-it-qat; do
  tag=${model#gemma4:}; tag=${tag%%-*}
  .venv/bin/python infra/rerank.py python-sortedcontainers data/v2/rank_python-sortedcontainers.jsonl data/v2/mut_python-sortedcontainers.jsonl $model data/rr/rr_${tag}_python-sortedcontainers.jsonl data/rr/cache
  echo "$model sorted $(wc -l < data/rr/rr_${tag}_python-sortedcontainers.jsonl)"
done
echo SORTED_DONE
