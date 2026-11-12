"""All tables from the analysis plan, rebuilt from saved rankings and cached model outputs.

Usage: python analyze.py <data_dir> <repo> [<repo> ...]
Reads  <data_dir>/v2/rank_<repo>.jsonl, <data_dir>/rr/rr_<model>_<repo>.jsonl, <data_dir>/prof_<repo>.junit.xml
Writes <data_dir>/results.json and prints markdown tables.
"""
import gzip
import json
import random
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def jlines(path):
    """Read a .jsonl file, or its gzipped copy if only that exists."""
    path = Path(path)
    if not path.exists() and Path(str(path) + ".gz").exists():
        return [json.loads(l) for l in gzip.open(str(path) + ".gz", "rt")]
    return [json.loads(l) for l in open(path)]


BASE = ["full", "name", "reach", "graphdist", "lexical", "coverage"]
MODELS = {"e2b": "Gemma 4 E2B", "e4b": "Gemma 4 E4B"}
B = 10000


def times(junit):
    t = {}
    for c in ET.parse(junit).getroot().iter("testcase"):
        t[f"{c.get('classname')}::{c.get('name')}"] = float(c.get("time") or 0)
    return t


def first_hit(ranking, failing):
    fs = set(failing)
    for i, t in enumerate(ranking):
        if t in fs:
            return i
    return None


def ttff(ranking, failing, tt):
    """Seconds of test runtime until the first failing test finishes."""
    fs, s = set(failing), 0.0
    for t in ranking:
        s += tt.get(t, 0.0)
        if t in fs:
            return s
    return s


def boot_ci(rows, fn, strata, seed=0):
    """Stratified bootstrap of a statistic over mutants."""
    rng = random.Random(seed)
    groups = {}
    for r, s in zip(rows, strata):
        groups.setdefault(s, []).append(r)
    vals = []
    for _ in range(B):
        sample = [rng.choice(g) for g in groups.values() for _ in g]
        vals.append(fn(sample))
    vals.sort()
    return vals[int(0.025 * B)], vals[int(0.975 * B)]


def main():
    data = Path(sys.argv[1])
    repos = sys.argv[2:]
    rows = []
    for repo in repos:
        tt = times(data / f"prof_{repo}.junit.xml")
        rank = {x["id"]: x for x in jlines(data / "v2" / f"rank_{repo}.jsonl")}
        model_rank = {}
        for tag in MODELS:
            p = data / "rr" / f"rr_{tag}_{repo}.jsonl"
            if p.exists() or Path(str(p) + ".gz").exists():
                model_rank[tag] = {x["id"]: x for x in jlines(p)}
        for mid, r in rank.items():
            if not r["failing"]:
                continue
            row = {"repo": repo, "id": mid, "suite_size": r["suite_size"], "suite_time": r["suite_time"],
                   "static_miss": not (set(r["failing"]) & set(r["dist"])), "hit": {}, "ttff": {}}
            for m in BASE + [x for x in ("pgraph", "pemb") if x in r]:
                row["hit"][m] = first_hit(r[m], r["failing"])
                row["ttff"][m] = ttff(r[m], r["failing"], tt)
            if "pgraph" in r:
                row["provided"] = {"in_pgraph": r["in_pgraph"], "in_pemb": r["in_pemb"], "n_preach": r["n_preach"],
                                   "pstatic_miss": not (set(r["failing"]) & set(r["pdist"]))}
            for tag, mr in model_rank.items():
                if mid in mr:
                    x = mr[mid]
                    row["hit"][tag] = first_hit(x["ranking"], r["failing"])
                    row["ttff"][tag] = ttff(x["ranking"], r["failing"], tt) + x["wall_s"]
                    row.setdefault("model", {})[tag] = {k: x[k] for k in ("wall_s", "extra_used", "unknown", "parse_ok", "prompt_tokens")}
                    # did a test proposed outside the graph's reach fail?
                    extra = [t for t in x["ranking"][: x["n_model_items"]] if t not in r["dist"]]
                    row["model"][tag]["extra_hit"] = bool(set(extra) & set(r["failing"]))
                    row["model"][tag]["extra_tests"] = len(extra)
            rows.append(row)

    methods = BASE + [t for t in MODELS if all(t in r["hit"] for r in rows)]
    strata = [r["repo"] for r in rows]

    def recall(k):
        def f(rs, m):
            return sum(1 for r in rs if r["hit"][m] is not None and r["hit"][m] < (max(1, round(0.1 * r["suite_size"])) if k == "10%" else k)) / len(rs)
        return f

    out = {"n": len(rows), "by_repo": {}, "methods": methods}
    print(f"\n## Recall@k, all repos pooled (n = {len(rows)} bugs), 95% stratified bootstrap\n")
    print("| Method | R@1 | R@5 | R@10 | R@10% of suite |\n|---|---|---|---|---|")
    out["recall"] = {}
    for m in methods:
        cells = []
        for k in (1, 5, 10, "10%"):
            f = recall(k)
            v = f(rows, m)
            lo, hi = boot_ci(rows, lambda s: f(s, m), strata)
            cells.append(f"{v:.2f} [{lo:.2f}, {hi:.2f}]")
            out["recall"].setdefault(m, {})[str(k)] = [v, lo, hi]
        print(f"| {m} | " + " | ".join(cells) + " |")

    print("\n## Recall@10 by repository\n")
    print("| Repo | n | suite tests | suite s | static misses | " + " | ".join(methods) + " |")
    print("|---|---|---|---|---|" + "---|" * len(methods))
    f10 = recall(10)
    for repo in repos:
        rs = [r for r in rows if r["repo"] == repo]
        if not rs:
            continue
        vals = {m: f10(rs, m) for m in methods}
        out["by_repo"][repo] = {"n": len(rs), "suite_size": rs[0]["suite_size"], "suite_time": rs[0]["suite_time"],
                                "static_miss": sum(r["static_miss"] for r in rs), "r10": vals}
        print(f"| {repo} | {len(rs)} | {rs[0]['suite_size']} | {rs[0]['suite_time']:.1f} | {sum(r['static_miss'] for r in rs)} | "
              + " | ".join(f"{vals[m]:.2f}" for m in methods) + " |")

    print("\n## Paired difference in Recall@10: model minus graph distance\n")
    out["paired"] = {}
    for tag in [t for t in MODELS if t in methods]:
        def diff(s, tag=tag):
            return f10(s, tag) - f10(s, "graphdist")
        d = diff(rows)
        lo, hi = boot_ci(rows, diff, strata)
        out["paired"][tag] = [d, lo, hi]
        print(f"- {MODELS[tag]}: {d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    print("\n## Exploratory (not in the plan): model minus lexical similarity, Recall@10\n")
    out["paired_lexical"] = {}
    for tag in [t for t in MODELS if t in methods]:
        def diffl(s, tag=tag):
            return f10(s, tag) - f10(s, "lexical")
        d = diffl(rows)
        lo, hi = boot_ci(rows, diffl, strata)
        out["paired_lexical"][tag] = [d, lo, hi]
        print(f"- {MODELS[tag]}: {d:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    print("\n## Time to first failure (median seconds; model time included for model rows)\n")
    out["ttff"] = {}
    print("| Repo | " + " | ".join(methods) + " |\n|---|" + "---|" * len(methods))
    for repo in repos:
        rs = [r for r in rows if r["repo"] == repo]
        if not rs:
            continue
        meds = {m: statistics.median(r["ttff"][m] for r in rs) for m in methods}
        out["ttff"][repo] = meds
        print(f"| {repo} | " + " | ".join(f"{meds[m]:.2f}" for m in methods) + " |")

    print("\n## Exploratory (not in the plan): break-even suite runtime\n")
    print("Every test's runtime is multiplied by s while model time stays fixed. Break-even is the smallest s at which the "
          "model's MEAN time to first failure is at or below graph distance's; reported as s x measured suite runtime.\n")
    out["breakeven"] = {}
    for tag in [t for t in MODELS if t in methods]:
        for repo in repos + ["pooled"]:
            rs = [r for r in rows if repo == "pooled" or r["repo"] == repo]
            if not rs:
                continue
            mt = sum(r["model"][tag]["wall_s"] for r in rs) / len(rs)
            tm = sum(r["ttff"][tag] - r["model"][tag]["wall_s"] for r in rs) / len(rs)
            tg = sum(r["ttff"]["graphdist"] for r in rs) / len(rs)
            suite = sum(r["suite_time"] for r in rs) / len(rs)
            if tg > tm:
                sstar = mt / (tg - tm)
                be = sstar * suite
                out["breakeven"].setdefault(tag, {})[repo] = {"scale": sstar, "suite_s": be, "mean_model_s": mt,
                                                             "mean_tests_s_model": tm, "mean_tests_s_graphdist": tg}
                print(f"- {MODELS[tag]}, {repo}: test time to first failure {tm:.2f}s (model order) vs {tg:.2f}s (graph distance), "
                      f"model {mt:.1f}s; break-even at x{sstar:.1f}, a suite of about {be:.0f}s")
            else:
                out["breakeven"].setdefault(tag, {})[repo] = None
                print(f"- {MODELS[tag]}, {repo}: model order is not faster in test time ({tm:.2f}s vs {tg:.2f}s); no break-even")

    print("\n## Static misses and the model\n")
    out["misses"] = {}
    miss = [r for r in rows if r["static_miss"]]
    for tag in [t for t in MODELS if t in methods]:
        rec = sum(1 for r in miss if r["model"][tag]["extra_hit"])
        props = [r for r in rows if r["model"][tag]["extra_tests"] > 0]
        false_alarm = sum(1 for r in props if not r["model"][tag]["extra_hit"])
        unknown = sum(r["model"][tag]["unknown"] for r in rows)
        parse_fail = sum(1 for r in rows if not r["model"][tag]["parse_ok"])
        wall = statistics.median(r["model"][tag]["wall_s"] for r in rows)
        out["misses"][tag] = {"static_misses": len(miss), "recovered": rec, "bugs_with_proposals": len(props),
                              "proposals_without_failure": false_alarm, "unknown_names": unknown,
                              "parse_failures": parse_fail, "median_model_s": wall}
        print(f"- {MODELS[tag]}: recovered {rec} of {len(miss)} static misses; proposed outside tests on {len(props)} bugs, "
              f"{false_alarm} of those had no failing proposal; {unknown} unknown names; {parse_fail} unparsable answers; "
              f"median model time {wall:.1f}s")
    prov = [r for r in rows if "provided" in r]
    if prov:
        pm = [m for m in ("graphdist", "pgraph", "lexical", "pemb", "e2b", "e4b", "coverage") if all(m in r["hit"] for r in prov)]
        pstrata = [r["repo"] for r in prov]
        print(f"\n## Competition snapshot: our AST graph vs the provided graph and embeddings (n = {len(prov)})\n")
        print(f"Changed function found in provided graph: {sum(r['provided']['in_pgraph'] for r in prov)}; in provided embeddings: "
              f"{sum(r['provided']['in_pemb'] for r in prov)}; no failing test reachable in provided graph: "
              f"{sum(r['provided']['pstatic_miss'] for r in prov)}; in our graph: {sum(r['static_miss'] for r in prov)}\n")
        print("| Method | R@1 | R@5 | R@10 |\n|---|---|---|---|")
        out["provided"] = {}
        for m in pm:
            cells = []
            for k in (1, 5, 10):
                f = recall(k)
                v = f(prov, m)
                lo, hi = boot_ci(prov, lambda x: f(x, m), pstrata)
                cells.append(f"{v:.2f} [{lo:.2f}, {hi:.2f}]")
                out["provided"].setdefault(m, {})[str(k)] = [v, lo, hi]
            print(f"| {m} | " + " | ".join(cells) + " |")
    (data / "results.json").write_text(json.dumps(out, indent=1))
    (data / "rows.json").write_text(json.dumps(rows))


if __name__ == "__main__":
    main()
