"""Rank a repository's tests for each planted bug with the non-model methods.

Usage: python select_tests.py <repo_dir> <mutants.jsonl> <profile_prefix> <out.jsonl>

Writes one line per mutant with the ranked test ids of every method, so the
metrics script (and the model re-ranker) can read them without recomputing.
Test ids are "<junit classname>::<test name>", the same ids the kill matrix uses.
"""
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import networkx as nx
from coverage import CoverageData
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, str(Path(__file__).parent))
from codegraph import build  # noqa: E402


def load_catalog(junit_path):
    """Test id -> {file, name, cls, time}, in the suite's default run order."""
    cat = {}
    for case in ET.parse(junit_path).getroot().iter("testcase"):
        if case.find("skipped") is not None:
            continue
        cls = case.get("classname") or ""
        name = case.get("name")
        tid = f"{cls}::{name}"
        cat[tid] = {
            "file": case.get("file") or "",
            "name": name,
            "base": re.sub(r"\[.*\]$", "", name),
            "cls": cls.rsplit(".", 1)[-1],
            "time": float(case.get("time") or 0.0),
        }
    return cat


def nodeid_to_tid(ctx):
    """'tests/test_a.py::Cls::test_x[1]|run' -> 'tests.test_a.Cls::test_x[1]'."""
    ctx = ctx.split("|")[0]
    parts = ctx.split("::")
    if len(parts) < 2:
        return None
    mod = parts[0][:-3].replace("/", ".") if parts[0].endswith(".py") else parts[0]
    cls = ".".join([mod] + parts[1:-1])
    return f"{cls}::{parts[-1]}"


def coverage_map(cov_path, repo):
    """(relative file, line) -> set of test ids that executed it."""
    data = CoverageData(basename=str(cov_path))
    data.read()
    out = {}
    for fname in data.measured_files():
        rel = str(Path(fname).resolve().relative_to(Path(repo).resolve())) if fname.startswith(str(Path(repo).resolve())) else fname
        for line, ctxs in (data.contexts_by_lineno(fname) or {}).items():
            tids = {nodeid_to_tid(c) for c in ctxs if c}
            tids.discard(None)
            if tids:
                out[(rel, line)] = tids
    return out


def test_node_index(g, cat):
    """Test id -> graph node of the function that defines the test."""
    by_file_name = defaultdict(list)
    for n, d in g.nodes(data=True):
        if d.get("kind") == "function":
            by_file_name[(d["path"], d["name"])].append(n)
    idx = {}
    for tid, t in cat.items():
        cands = by_file_name.get((t["file"], t["base"]), [])
        if not cands:
            # inherited tests are defined in another file; match on name anywhere in tests
            cands = [n for (p, nm), ns in by_file_name.items() if nm == t["base"] and "test" in p for n in ns]
        pick = [n for n in cands if f".{t['cls']}." in n or n.endswith(f"::{t['cls']}.{t['base']}")] or cands
        if pick:
            idx[tid] = pick[0]
    return idx


def main():
    repo, mut_path, prof, out = sys.argv[1:5]
    repo = Path(repo).resolve()
    cat = load_catalog(f"{prof}.junit.xml")
    order = list(cat)  # default run order
    covmap = coverage_map(f"{prof}.coverage", repo)

    g = build(repo)
    calls = nx.DiGraph()
    calls.add_nodes_from(g.nodes)
    calls.add_edges_from((u, v) for u, v, d in g.edges(data=True) if d["type"] == "calls")
    rev = calls.reverse(copy=False)
    tnode = test_node_index(g, cat)

    # lexical similarity between a changed function's source and each test's source
    src_cache = {}

    def node_src(n):
        if n not in src_cache:
            d = g.nodes[n]
            try:
                lines = (repo / d["path"]).read_text().splitlines()
                src_cache[n] = "\n".join(lines[d["start"] - 1:d["end"]])
            except Exception:
                src_cache[n] = d.get("name", "")
        return src_cache[n]

    tids_with_node = [t for t in order if t in tnode]
    vec = TfidfVectorizer(token_pattern=r"[A-Za-z_][A-Za-z0-9_]+").fit(
        [node_src(tnode[t]) for t in tids_with_node] + [node_src(n) for n, d in g.nodes(data=True) if d.get("kind") == "function"])
    test_mat = vec.transform([node_src(tnode[t]) for t in tids_with_node])

    def rest(first):
        seen = set(first)
        return list(first) + [t for t in order if t not in seen]

    with open(mut_path) as f, open(out, "w") as w:
        for line in f:
            m = json.loads(line)
            changed = f"{m['file']}::{m['function']}"
            failing = [t for t in m["failing_tests"] if t in cat]
            rec = {"id": m["id"], "changed": changed, "failing": failing,
                   "in_graph": changed in g, "suite_size": len(order),
                   "suite_time": sum(c["time"] for c in cat.values())}
            short = m["function"].rsplit(".", 1)[-1].lower()
            modname = Path(m["file"]).stem.lower()

            rec["full"] = order
            rec["name"] = rest([t for t in order if short in t.lower() or (modname not in ("__init__",) and modname in cat[t]["file"].lower())])

            dist = {}
            if changed in g:
                dist = nx.single_source_shortest_path_length(rev, changed)
            reach = [t for t in order if t in tnode and tnode[t] in dist]
            rec["reach"] = rest(reach)
            rec["graphdist"] = rest(sorted(reach, key=lambda t: (dist[tnode[t]], order.index(t))))
            rec["n_reachable"] = len(reach)
            rec["dist"] = {t: dist[tnode[t]] for t in reach}

            if changed in g:
                q = vec.transform([node_src(changed)])
                sims = (test_mat @ q.T).toarray().ravel()
                ranked = [tids_with_node[i] for i in sorted(range(len(sims)), key=lambda i: -sims[i])]
                rec["lexical"] = rest(ranked)
            else:
                rec["lexical"] = order

            covered = covmap.get((m["file"], m["line"]), set())
            if m.get("kind") == "real" and changed in g:
                # real fixes often start in a signature line that only runs at import;
                # use every line of the changed function's body instead
                d = g.nodes[changed]
                covered = set()
                for ln in range(d["start"] + 1, d["end"] + 1):
                    covered |= covmap.get((m["file"], ln), set())
            rec["coverage"] = rest([t for t in order if t in covered])
            rec["n_covered"] = len(covered)
            w.write(json.dumps(rec) + "\n")


if __name__ == "__main__":
    main()
