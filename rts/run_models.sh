#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
source .venv/bin/activate
for model in gemma4:e2b-it-qat gemma4:e4b-it-qat; do
  tag=${model#gemma4:}; tag=${tag%%-*}
  for r in cachetools toolz humanize; do
    python infra/rerank.py $r data/v2/rank_$r.jsonl data/v2/mut_$r.jsonl $model data/rr/rr_${tag}_$r.jsonl data/rr/cache
    echo "$model $r $(wc -l < data/rr/rr_${tag}_$r.jsonl)"
  done
done
echo MODELS_DONE
