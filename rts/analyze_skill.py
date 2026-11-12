"""Score the no-model skill ordering, and count where the model beats graph distance.

Skill ordering (as in skills/which_tests_first): the 15 nearest reachable tests by graph
distance, then tests by lexical similarity until 30, then the rest in default order.

Usage: python analyze_skill.py <data_dir>
"""
import gzip
import json
import math
import random
import sys
from pathlib import Path


def lines(p):
    p = Path(p)
    if p.exists():
        return [json.loads(l) for l in open(p) if l.strip()]
    if Path(str(p) + ".gz").exists():
        return [json.loads(l) for l in gzip.open(str(p) + ".gz", "rt") if l.strip()]
    return []


def fh(rk, f):
    fs = set(f)
    for i, t in enumerate(rk):
        if t in fs:
            return i
    return None


def skill_order(r):
    g = [t for t in r["graphdist"] if t in r["dist"]][:15]
    out = list(g)
    for t in r["lexical"]:
        if len(out) >= len(g) + 15:
            break
        if t not in out:
            out.append(t)
    seen = set(out)
    return out + [t for t in r["full"] if t not in seen]


d = Path(sys.argv[1])
settings = []
for repo in ("cachetools", "toolz", "humanize", "python-sortedcontainers", "fastapi"):
    rk = lines(d / "v2" / f"rank_{repo}.jsonl")
    e4b = {x["id"]: x for x in lines(d / "rr" / f"rr_e4b_{repo}.jsonl")}
    rows = [{"graphdist": fh(r["graphdist"], r["failing"]), "lexical": fh(r["lexical"], r["failing"]),
             "skill": fh(skill_order(r), r["failing"]), "e4b": fh(e4b[r["id"]]["ranking"], r["failing"]) if r["id"] in e4b else None}
            for r in rk if r["failing"]]
    settings.append((f"planted: {repo}", rows))
for sub, name in (("real", "FastAPI"), ("real_rich", "Rich"), ("real_requests", "requests")):
    rows = []
    for mp in sorted((d / sub).glob("mut_*.jsonl")):
        tid = mp.stem[4:]
        rr = lines(d / sub / f"rank_{tid}.jsonl")
        if not rr or not rr[0]["failing"]:
            continue
        r = rr[0]
        x = lines(d / sub / f"rr_e4b_{tid}.jsonl")
        rows.append({"graphdist": fh(r["graphdist"], r["failing"]), "lexical": fh(r["lexical"], r["failing"]),
                     "skill": fh(skill_order(r), r["failing"]), "e4b": fh(x[0]["ranking"], r["failing"]) if x else None})
    settings.append((f"real: {name}", rows))


def r10(rows, m):
    return sum(1 for x in rows if x[m] is not None and x[m] < 10) / len(rows)


print("## Recall@10 by setting: graph distance, lexical, skill ordering (no model), Gemma 4 E4B\n")
print("| Setting | n | Graph distance | Lexical | Skill (no model) | E4B |\n|---|---|---|---|---|---|")
wins = {"e4b": [0, 0, 0], "skill": [0, 0, 0]}
out = {}
for name, rows in settings:
    v = {m: r10(rows, m) for m in ("graphdist", "lexical", "skill", "e4b")}
    out[name] = {"n": len(rows), **v}
    print(f"| {name} | {len(rows)} | {v['graphdist']:.2f} | {v['lexical']:.2f} | {v['skill']:.2f} | {v['e4b']:.2f} |")
    for m in ("e4b", "skill"):
        wins[m][0 if v[m] > v["graphdist"] + 1e-9 else 2 if v[m] < v["graphdist"] - 1e-9 else 1] += 1
print()
for m, (w, t, l) in wins.items():
    n = w + l
    p = sum(math.comb(n, k) for k in range(w, n + 1)) / 2 ** n if n else 1.0
    print(f"- {m} vs graph distance across {len(settings)} settings: better in {w}, tied in {t}, worse in {l} (one-sided sign test over non-ties, p = {p:.3f})")
    out[f"wins_{m}"] = [w, t, l, p]
allrows = [x for _, rows in settings for x in rows]
rng = random.Random(0)
g = {name: rows for name, rows in settings}
for m in ("skill", "e4b"):
    dif = r10(allrows, m) - r10(allrows, "graphdist")
    bs = sorted((lambda s: r10(s, m) - r10(s, "graphdist"))([rng.choice(v) for v in g.values() for _ in v]) for _ in range(10000))
    print(f"- {m} minus graph distance, all {len(allrows)} bugs pooled: {dif:+.3f} [{bs[250]:+.3f}, {bs[9750]:+.3f}]")
    out[f"pooled_{m}"] = [dif, bs[250], bs[9750]]
(d / "results_skill.json").write_text(json.dumps(out, indent=1))
