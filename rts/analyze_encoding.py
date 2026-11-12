"""Graph-encoding ablation (analysis_plan_addendum_encoding.md): Recall@10 per arm, paired differences.

Usage: python analyze_encoding.py <data_dir>
"""
import gzip
import json
import random
import sys
from pathlib import Path


def lines(p):
    p = Path(p)
    if not p.exists() and Path(str(p) + ".gz").exists():
        return [json.loads(l) for l in gzip.open(str(p) + ".gz", "rt") if l.strip()]
    return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []


def fh(rk, f):
    fs = set(f)
    for i, t in enumerate(rk):
        if t in fs:
            return i
    return None


d = Path(sys.argv[1])
sets = {}
for repo in ("cachetools", "toolz", "python-sortedcontainers"):
    rk = {x["id"]: x for x in lines(d / "v2" / f"rank_{repo}.jsonl")}
    arms = {"list": {x["id"]: x for x in lines(d / "rr" / f"rr_e2b_{repo}.jsonl")}}
    for arm in ("none", "path"):
        arms[arm] = {x["id"]: x for x in lines(d / "rr" / f"enc_{arm}_e2b_{repo}.jsonl")}
    for mid, r in rk.items():
        if r["failing"] and all(mid in a for a in arms.values()):
            sets.setdefault("planted", []).append({a: fh(arms[a][mid]["ranking"], r["failing"]) for a in arms} | {"graphdist": fh(r["graphdist"], r["failing"])})
rd = d / "real_rich"
for mp in sorted(rd.glob("mut_*.jsonl")):
    tid = mp.stem[4:]
    rr = lines(rd / f"rank_{tid}.jsonl")
    if not rr or not rr[0]["failing"]:
        continue
    r = rr[0]
    arms = {"list": lines(rd / f"rr_e2b_{tid}.jsonl"), "none": lines(rd / f"enc_none_e2b_{tid}.jsonl"), "path": lines(rd / f"enc_path_e2b_{tid}.jsonl")}
    if all(arms.values()):
        sets.setdefault("Rich real", []).append({a: fh(v[0]["ranking"], r["failing"]) for a, v in arms.items()} | {"graphdist": fh(r["graphdist"], r["failing"])})


def r10(rows, a):
    return sum(1 for x in rows if x[a] is not None and x[a] < 10) / len(rows)


rng = random.Random(0)
out = {}
print("## Graph-encoding ablation, Gemma 4 E2B, Recall@10\n")
print("| Set | n | graph distance (no model) | none | list (prompt v1) | path |\n|---|---|---|---|---|---|")
for name, rows in sets.items():
    print(f"| {name} | {len(rows)} | {r10(rows, 'graphdist'):.2f} | {r10(rows, 'none'):.2f} | {r10(rows, 'list'):.2f} | {r10(rows, 'path'):.2f} |")
print()
for name, rows in sets.items():
    for a, b in (("path", "list"), ("none", "list")):
        dif = r10(rows, a) - r10(rows, b)
        bs = sorted(r10(s, a) - r10(s, b) for s in ([rng.choice(rows) for _ in rows] for _ in range(10000)))
        out[f"{name}:{a}-{b}"] = [dif, bs[250], bs[9750]]
        print(f"- {name}: {a} minus {b}: {dif:+.3f} [{bs[250]:+.3f}, {bs[9750]:+.3f}]")
(d / "results_encoding.json").write_text(json.dumps(out, indent=1))
