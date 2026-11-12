"""Pooled Recall@10 over all real-regression sets, stratified bootstrap by repository (exploratory).

Usage: python analyze_real_pooled.py <data_dir>
"""
import random
import sys
from pathlib import Path

sys.argv = sys.argv[:2]
exec(open(Path(__file__).with_name("analyze_real.py")).read().split("def main():")[0])
d = Path(sys.argv[1])
rows = []
for sub in ("real", "real_rich", "real_requests"):
    D = d / sub
    for mp in sorted(D.glob("mut_*.jsonl")):
        tid = mp.stem[4:]
        r = first_line(D / f"rank_{tid}.jsonl")
        if r is None or not r["failing"]:
            continue
        h = {m: first_hit(r[m], r["failing"]) for m in ("graphdist", "lexical", "coverage") if m in r}
        for tag in ("e2b", "e4b"):
            x, x2 = first_line(D / f"rr_{tag}_{tid}.jsonl"), first_line(D / f"rr2_{tag}_{tid}.jsonl")
            if x:
                h[tag] = first_hit(x["ranking"], r["failing"])
            if x2:
                h[tag + "_v2"] = first_hit(x2["ranking"], r["failing"])
        rows.append((sub, h))


def r10(m, rs):
    return sum(1 for _, h in rs if h.get(m) is not None and h[m] < 10) / len(rs)


rng = random.Random(0)
g = {}
for x in rows:
    g.setdefault(x[0], []).append(x)
print(f"## Real regressions pooled over {len(g)} repositories (n = {len(rows)}), Recall@10, stratified bootstrap\n")
for m in ("graphdist", "lexical", "coverage", "e2b", "e4b", "e2b_v2", "e4b_v2"):
    bs = sorted(r10(m, [rng.choice(v) for v in g.values() for _ in v]) for _ in range(10000))
    print(f"- {m}: {r10(m, rows):.3f} [{bs[250]:.3f}, {bs[9750]:.3f}]")
for a in ("e4b", "e4b_v2", "e2b_v2"):
    bs = sorted((lambda s: r10(a, s) - r10("graphdist", s))([rng.choice(v) for v in g.values() for _ in v]) for _ in range(10000))
    print(f"- {a} minus graphdist: {r10(a, rows) - r10('graphdist', rows):+.3f} [{bs[250]:+.3f}, {bs[9750]:+.3f}]")
