"""Prompt v2 against prompt v1 and graph distance on the planted bugs (addendum, secondary outcome).

Usage: python analyze_v2_planted.py <data_dir>
"""
import gzip
import json
import random
import sys
from pathlib import Path

REPOS = ["cachetools", "toolz", "humanize", "python-sortedcontainers", "fastapi"]


def jl(p):
    p = Path(p)
    if not p.exists() and Path(str(p) + ".gz").exists():
        return [json.loads(l) for l in gzip.open(str(p) + ".gz", "rt")]
    return [json.loads(l) for l in open(p)]


def fh(rk, f):
    fs = set(f)
    for i, t in enumerate(rk):
        if t in fs:
            return i
    return None


d = Path(sys.argv[1])
rows = []
for repo in REPOS:
    rk = {x["id"]: x for x in jl(d / "v2" / f"rank_{repo}.jsonl")}
    runs = {(pre, tag): {x["id"]: x for x in jl(d / "rr" / f"{pre}_{tag}_{repo}.jsonl")} for pre in ("rr", "rr2") for tag in ("e2b", "e4b")}
    for mid, r in rk.items():
        if not r["failing"]:
            continue
        h = {"graphdist": fh(r["graphdist"], r["failing"]), "lexical": fh(r["lexical"], r["failing"])}
        for (pre, tag), dd in runs.items():
            if mid in dd:
                h[f"{tag}_{'v2' if pre == 'rr2' else 'v1'}"] = fh(dd[mid]["ranking"], r["failing"])
        rows.append((repo, h))


def r10(m, rs):
    return sum(1 for _, h in rs if h.get(m) is not None and h[m] < 10) / len(rs)


ms = ["graphdist", "lexical", "e2b_v1", "e4b_v1", "e2b_v2", "e4b_v2"]
print(f"## Prompt v2 on planted bugs (n = {len(rows)}), Recall@10\n")
print("| Repo | " + " | ".join(ms) + " |\n|---|" + "---|" * len(ms))
for repo in REPOS + ["pooled"]:
    rs = [x for x in rows if repo == "pooled" or x[0] == repo]
    print(f"| {repo} | " + " | ".join(f"{r10(m, rs):.2f}" for m in ms) + " |")
rng = random.Random(0)
groups = {}
for x in rows:
    groups.setdefault(x[0], []).append(x)
print()
for a, b in [("e4b_v2", "graphdist"), ("e2b_v2", "graphdist"), ("e4b_v2", "e4b_v1"), ("e2b_v2", "e2b_v1")]:
    dif = r10(a, rows) - r10(b, rows)
    bs = sorted(r10(a, s) - r10(b, s) for s in ([rng.choice(g) for g in groups.values() for _ in g] for _ in range(10000)))
    print(f"- {a} minus {b}: {dif:+.3f} [{bs[250]:+.3f}, {bs[9750]:+.3f}]")
