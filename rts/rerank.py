"""Gemma re-ranking of tests for each planted bug, as fixed in the analysis plan.

The model sees the diff, the changed function's source, its callers and callees
from the code graph, the 30 tests closest in the graph (numbered), and the names
of the other tests. It returns one ranked list that may mix those numbers with up
to 5 other test names. Unknown names are dropped and counted. Every call is cached
by a hash of its prompt, so a rerun reads the cache instead of calling the model.

Usage: python rerank.py <repo_dir> <ranked.jsonl> <mutants.jsonl> <model> <out.jsonl> [cache_dir]
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).parent))
from codegraph import build  # noqa: E402

TOP = 30
PARAM_RE = r'\\[.*\\]$'
MAX_EXTRA = 5
OLLAMA = "http://localhost:11434/api/chat"

SYSTEM = (
    "You pick which tests to run first after a code change, so that a bug in the change is caught as early as possible. "
    "Answer with JSON only."
)

TEMPLATE = """A developer changed one function. Rank the tests so that a test which fails because of this change comes as early as possible.

Changed function: {func} in {file}

Diff:
{diff}

Function source before the change:
{src}

Callers of this function (from the code graph): {callers}
Functions it calls (from the code graph): {callees}

Candidate tests, closest in the code graph first (number. test, graph distance):
{cands}

Other tests in the suite (not reachable in the code graph), as file::name:
{others}

Return JSON: {{"ranked": [...]}} with at most 15 entries. Each entry is either a candidate number or an exact name from the other tests (at most {max_extra} of those). Put the tests most likely to fail first."""


def call(model, prompt, cache_dir):
    key = hashlib.sha256((model + "\n" + prompt).encode()).hexdigest()
    path = Path(cache_dir) / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    body = json.dumps({
        "model": model, "stream": False, "think": False, "format": "json",
        "options": {"temperature": 0, "seed": 0, "num_ctx": 32768, "num_predict": 400},
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
    }).encode()
    t0 = time.time()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.loads(r.read())
    out = {
        "model": model, "content": resp["message"]["content"], "wall_s": time.time() - t0,
        "prompt_tokens": resp.get("prompt_eval_count"), "output_tokens": resp.get("eval_count"),
        "prompt_s": (resp.get("prompt_eval_duration") or 0) / 1e9, "gen_s": (resp.get("eval_duration") or 0) / 1e9,
    }
    path.write_text(json.dumps(out))
    return out


def main():
    repo, ranked_path, mut_path, model, out_path = sys.argv[1:6]
    cache_dir = sys.argv[6] if len(sys.argv) > 6 else str(Path(out_path).parent / "cache")
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    repo = Path(repo).resolve()
    g = build(repo)
    calls = nx.DiGraph((u, v) for u, v, d in g.edges(data=True) if d["type"] == "calls")
    muts = {json.loads(l)["id"]: json.loads(l) for l in open(mut_path)}

    done = set()
    if Path(out_path).exists():
        done = {json.loads(l)["id"] for l in open(out_path)}
    w = open(out_path, "a")
    for line in open(ranked_path):
        r = json.loads(line)
        if r["id"] in done or not r["failing"]:
            continue
        m = muts[r["id"]]
        changed = r["changed"]
        order = r["full"]
        cands = r["graphdist"][:TOP] if r["dist"] else []
        cands = [t for t in cands if t in r["dist"]]

        # other tests, deduplicated to file::name (parametrised and inherited copies collapse)
        def short(t):
            cls, name = t.split("::", 1)
            # kept byte-identical to the regex used for the cached runs (it does not strip parameters)
            base = re.sub(PARAM_RE, '', name)
            return f"{cls.rsplit('.', 1)[0] if '.' in cls else cls}::{base}"
        cand_set = set(cands)
        others = sorted({short(t) for t in order if t not in cand_set})
        by_short = defaultdict(list)
        by_base = defaultdict(list)  # same name with any [parameter] suffix removed
        for t in order:
            by_short[short(t)].append(t)
            by_base[re.sub(r"\[.*\]$", "", short(t))].append(t)

        d = g.nodes[changed] if changed in g else {}
        try:
            lines = (repo / m["file"]).read_text().splitlines()
            src = "\n".join(lines[d["start"] - 1:d["end"]]) if d else ""
        except Exception:
            src = ""
        src = "\n".join(src.splitlines()[:60])
        callers = sorted({u.split("::")[-1] for u in calls.predecessors(changed)})[:15] if changed in calls else []
        callees = sorted({v.split("::")[-1] for v in calls.successors(changed)})[:15] if changed in calls else []
        prompt = TEMPLATE.format(
            func=m["function"], file=m["file"], diff=m["diff"][:1500], src=src or "(not found)",
            callers=", ".join(callers) or "none found", callees=", ".join(callees) or "none found",
            cands="\n".join(f"{i+1}. {short(t)} [{t.split('::')[0].rsplit('.', 1)[-1]}], {r['dist'][t]}" for i, t in enumerate(cands)) or "(none: the code graph reaches no test)",
            others="\n".join(others[:600]), max_extra=MAX_EXTRA,
        )
        res = call(model, prompt, cache_dir)

        ranked, extra_used, unknown, parse_ok = [], 0, 0, True
        try:
            items = json.loads(res["content"]).get("ranked", [])
        except Exception:
            items, parse_ok = [], False
        for it in items:
            if isinstance(it, int) or (isinstance(it, str) and it.strip().isdigit()):
                i = int(it) - 1
                if 0 <= i < len(cands):
                    ranked.append(cands[i])
            elif isinstance(it, str) and extra_used < MAX_EXTRA:
                key = it.strip()
                base_key = re.sub(r"\[.*\]$", "", key)
                if key in by_short:
                    ranked.extend(by_short[key])
                    extra_used += 1
                elif base_key in by_base:
                    ranked.extend(by_base[base_key])
                    extra_used += 1
                else:
                    unknown += 1
        seen, final = set(), []
        for t in ranked + r["graphdist"]:
            if t not in seen:
                seen.add(t)
                final.append(t)
        w.write(json.dumps({
            "id": r["id"], "model": model, "ranking": final, "n_model_items": len(ranked),
            "extra_used": extra_used, "unknown": unknown, "parse_ok": parse_ok,
            "wall_s": res["wall_s"], "prompt_tokens": res["prompt_tokens"], "output_tokens": res["output_tokens"],
        }) + "\n")
        w.flush()


if __name__ == "__main__":
    main()
