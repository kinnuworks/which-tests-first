"""Recall@k and paired differences on the real FastAPI regressions (data/real).

Usage: python analyze_real.py <real_dir>
"""
import gzip
import json
import random
import sys
from pathlib import Path

METHODS = ["full", "name", "reach", "graphdist", "lexical", "pgraph", "pemb", "coverage", "e2b", "e4b"]
LABEL = {"full": "Full suite order", "name": "Name match", "reach": "Reachability", "graphdist": "Graph distance",
         "lexical": "Lexical similarity", "pgraph": "Provided graph", "pemb": "Provided embeddings",
         "coverage": "Coverage (upper bound)", "e2b": "Gemma 4 E2B re-rank", "e4b": "Gemma 4 E4B re-rank"}


def first_line(path):
    """First JSON record of a .jsonl file or its .gz copy; None if neither exists or it is empty."""
    for p, op in ((path, open), (Path(str(path) + ".gz"), gzip.open)):
        if p.exists():
            with op(p, "rt") as f:
                line = f.readline().strip()
            return json.loads(line) if line else None
    return None


def first_hit(ranking, failing):
    fs = set(failing)
    for i, t in enumerate(ranking):
        if t in fs:
            return i
    return None


def boot(rows, fn, n=10000, seed=0):
    rng = random.Random(seed)
    vals = sorted(fn([rng.choice(rows) for _ in rows]) for _ in range(n))
    return vals[int(0.025 * n)], vals[int(0.975 * n)]


def main():
    d = Path(sys.argv[1])
    rows = []
    for mp in sorted(d.glob("mut_*.jsonl")):
        tid = mp.stem[4:]
        r = first_line(d / f"rank_{tid}.jsonl")
        if r is None:
            continue
        if not r["failing"]:
            continue
        row = {"id": tid, "hit": {}, "n_failing": len(r["failing"]), "suite": r["suite_size"]}
        for m in METHODS[:8]:
            if m in r:
                row["hit"][m] = first_hit(r[m], r["failing"])
        for tag in ("e2b", "e4b"):
            x = first_line(d / f"rr_{tag}_{tid}.jsonl")
            if x is not None:
                row["hit"][tag] = first_hit(x["ranking"], r["failing"])
        rows.append(row)
    ms = [m for m in METHODS if all(m in r["hit"] for r in rows)]
    print(f"## Real regressions: competition FastAPI tasks with the fix undone (n = {len(rows)} tasks)\n")
    print(f"Median failing tests per task: {sorted(r['n_failing'] for r in rows)[len(rows)//2]}\n")
    print("| Method | R@1 | R@5 | R@10 |\n|---|---|---|---|")
    out = {"n": len(rows), "recall": {}}

    def rec(k, m):
        return lambda rs: sum(1 for r in rs if r["hit"][m] is not None and r["hit"][m] < k) / len(rs)
    for m in ms:
        cells = []
        for k in (1, 5, 10):
            v = rec(k, m)(rows)
            lo, hi = boot(rows, rec(k, m))
            out["recall"].setdefault(m, {})[k] = [v, lo, hi]
            cells.append(f"{v:.2f} [{lo:.2f}, {hi:.2f}]")
        print(f"| {LABEL[m]} | " + " | ".join(cells) + " |")
    print("\n| Method | R@10% of suite | median rank of first failing test |\n|---|---|---|")
    for m in ms:
        f = lambda rs, m=m: sum(1 for r in rs if r["hit"][m] is not None and r["hit"][m] < max(1, round(0.1 * r["suite"]))) / len(rs)
        lo, hi = boot(rows, f)
        ranks = sorted((r["hit"][m] + 1) if r["hit"][m] is not None else r["suite"] for r in rows)
        med = ranks[len(ranks) // 2]
        out.setdefault("r10pct", {})[m] = [f(rows), lo, hi]
        out.setdefault("median_rank", {})[m] = med
        print(f"| {LABEL[m]} | {f(rows):.2f} [{lo:.2f}, {hi:.2f}] | {med} |")
    print()
    for tag in ("e2b", "e4b"):
        if tag in ms:
            for base in ("graphdist", "lexical"):
                f = lambda rs, tag=tag, base=base: rec(10, tag)(rs) - rec(10, base)(rs)
                lo, hi = boot(rows, f)
                print(f"- {LABEL[tag]} minus {LABEL[base]}, Recall@10: {f(rows):+.3f} [{lo:+.3f}, {hi:+.3f}]")
                out.setdefault("paired", {})[f"{tag}-{base}"] = [f(rows), lo, hi]
    (d / "results_real.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
