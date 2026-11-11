#!/usr/bin/env bash
# Per-test runtime (junit xml) and per-test line coverage (coverage contexts) for one repo.
# Usage: profile_tests.sh <repo_dir> <package_for_cov> <out_prefix>
set -u
repo=$1; pkg=$2; out=$3
cd "$repo"
python -m pytest -q -p no:cacheprovider --junitxml="$out.junit.xml" -o junit_family=xunit1 \
  --cov="$pkg" --cov-context=test --cov-report= > "$out.pytest.log" 2>&1
mv .coverage "$out.coverage" 2>/dev/null
echo "$repo exit $?"
