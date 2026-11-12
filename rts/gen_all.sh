#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
source .venv/bin/activate
for spec in "cachetools src/cachetools" "toolz toolz" "humanize src/humanize" "python-sortedcontainers src/sortedcontainers"; do
  set -- $spec
  python infra/mutate.py "$1" "$2" "data/v2/mut_$1.jsonl" 80 7 > "data/v2/log_$1.txt" 2>&1
  echo "$1 $(wc -l < data/v2/mut_$1.jsonl)"
done
./infra/profile_tests.sh python-sortedcontainers sortedcontainers "$PWD/data/prof_sortedcontainers"
echo ALLDONE
