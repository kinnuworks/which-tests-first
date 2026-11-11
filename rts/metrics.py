"""Recall@k, recall at a 10% test budget, and time to first failure, with bootstrap intervals.

Usage: python metrics.py <ranked.jsonl>... [--methods a,b,c] [--times profile_prefix:repo ...]
"""
import argparse
import json
import random
import statistics
import xml.etree.ElementTree as ET


def first_hit(ranking, failing):
    fs = set(failing)
    for i, t in enumerate(ranking):
        if t in fs:
            return i
    return None


def boot(values, n=10000, seed=0):
    rng = random.Random(seed)
    k = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--methods", default="full,name,reach,graphdist,lexical,coverage")
    args = ap.parse_args()
    recs = [json.loads(l) for f in args.files for l in open(f)]
    recs = [r for r in recs if r["failing"]]
    methods = args.methods.split(",")
    print(f"mutants with failing tests in catalog: {len(recs)}")
    print(f"{'method':10s} " + " ".join(f"{'R@'+str(k):>16s}" for k in (1, 5, 10)) + f" {'R@10%':>16s}")
    for m in methods:
        cells = []
        for k in (1, 5, 10, "10%"):
            vals = []
            for r in recs:
                kk = max(1, round(0.1 * r["suite_size"])) if k == "10%" else k
                h = first_hit(r[m], r["failing"])
                vals.append(1.0 if h is not None and h < kk else 0.0)
            lo, hi = boot(vals, n=2000)
            cells.append(f"{sum(vals)/len(vals):.2f} [{lo:.2f},{hi:.2f}]")
        print(f"{m:10s} " + " ".join(f"{c:>16s}" for c in cells))
    miss = [r for r in recs if not set(r["failing"]) & set(r["dist"])]
    print(f"static misses (no failing test reachable): {len(miss)} of {len(recs)}")


if __name__ == "__main__":
    main()
