#!/usr/bin/env bash
# FastAPI snapshot arm + remaining model runs, in order.
set -u
cd "$(dirname "$0")/.."
W=$PWD
MUT_TIMEOUT=900 PYTEST_ADDOPTS="-n 4" .venv-fastapi/bin/python infra/mutate.py fastapi fastapi data/v2/mut_fastapi.jsonl 60 7 > data/v2/log_fastapi.txt 2>&1
echo "fastapi mutants $(wc -l < data/v2/mut_fastapi.jsonl)"
git -C fastapi status --short | grep -v '^??' && echo "WARNING fastapi tree dirty"
(source .venv-fastapi/bin/activate && COVERAGE_CORE=ctrace ./infra/profile_tests.sh fastapi fastapi "$W/data/prof_fastapi")
echo "fastapi profiled"
.venv-fastapi/bin/python infra/select_tests.py fastapi data/v2/mut_fastapi.jsonl data/prof_fastapi data/v2/rank_fastapi.jsonl
echo "fastapi ranked"
.venv-fastapi/bin/python infra/select_provided.py data/v2/rank_fastapi.jsonl data/v2/mut_fastapi.jsonl comp/graphs/fastapi_f1d750fddad90e2faad6c3cc5c85c7687b787e89.json comp/embeddings/fastapi_f1d750fddad90e2faad6c3cc5c85c7687b787e89.npz && echo "fastapi provided-graph methods added"
until grep -q MODELS_DONE data/rr/run.log 2>/dev/null; do sleep 30; done
for model in gemma4:e2b-it-qat gemma4:e4b-it-qat; do
  tag=${model#gemma4:}; tag=${tag%%-*}
  for r in fastapi; do
    .venv-fastapi/bin/python infra/rerank.py $r data/v2/rank_$r.jsonl data/v2/mut_$r.jsonl $model data/rr/rr_${tag}_$r.jsonl data/rr/cache
    echo "$model $r $(wc -l < data/rr/rr_${tag}_$r.jsonl)"
  done
done
echo TAIL_DONE
