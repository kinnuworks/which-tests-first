"""Add rankings that use the competition's provided code graph and node embeddings.

Usage: python select_provided.py <ranked.jsonl> <mutants.jsonl> <graph.json> <embeddings.npz>

Adds to each record (in place):
  pgraph  tests reachable from the changed function in the provided call graph, by
          shortest-path length, then the rest in default order
  pemb    tests ordered by cosine similarity of provided node embeddings
  in_pgraph, n_preach  bookkeeping
Provided node ids are dotted paths (fastapi.routing.serialize_response,
tests.test_x.test_y), so ours are converted: file path -> module, plus qualified name.
"""
import json
import re
import sys
from pathlib import Path

import networkx as nx
import numpy as np


def module_of(path):
    parts = list(Path(path).with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def test_pid(tid):
    """'tests.test_a.Cls::test_x[p]' -> 'tests.test_a.Cls.test_x'."""
    cls, name = tid.split("::", 1)
    base = re.sub(r"\[.*\]$", "", name)
    return f"{cls}.{base}"


def main():
    rank_path, mut_path, graph_path, emb_path = sys.argv[1:5]
    g = json.load(open(graph_path))
    G = nx.DiGraph()
    G.add_nodes_from(n["id"] for n in g["nodes"])
    G.add_edges_from((e["source"], e["target"]) for e in g["edges"] if e.get("type", "calls") == "calls")
    rev = G.reverse(copy=False)
    z = np.load(emb_path)
    emb = {k: z[k] for k in z.files}
    muts = {json.loads(l)["id"]: json.loads(l) for l in open(mut_path)}

    recs = [json.loads(l) for l in open(rank_path)]
    for r in recs:
        m = muts[r["id"]]
        changed = f"{module_of(m['file'])}.{m['function']}"
        order = r["full"]
        pid = {t: test_pid(t) for t in order}
        r["in_pgraph"] = changed in G
        dist = nx.single_source_shortest_path_length(rev, changed) if changed in G else {}
        reach = [t for t in order if pid[t] in dist]
        r["n_preach"] = len(reach)
        r["pdist"] = {t: dist[pid[t]] for t in reach}
        first = sorted(reach, key=lambda t: (dist[pid[t]], order.index(t)))
        seen = set(first)
        r["pgraph"] = first + [t for t in order if t not in seen]
        if changed in emb:
            q = emb[changed] / (np.linalg.norm(emb[changed]) + 1e-9)
            scored = []
            for i, t in enumerate(order):
                v = emb.get(pid[t])
                s = float(v @ q / (np.linalg.norm(v) + 1e-9)) if v is not None else -2.0
                scored.append((-s, i, t))
            r["pemb"] = [t for _, _, t in sorted(scored)]
        else:
            r["pemb"] = order
        r["in_pemb"] = changed in emb
    with open(rank_path, "w") as w:
        for r in recs:
            w.write(json.dumps(r) + "\n")
    n = len(recs)
    print(f"{n} records; changed function in provided graph: {sum(r['in_pgraph'] for r in recs)}, "
          f"in embeddings: {sum(r['in_pemb'] for r in recs)}; mean tests reachable: {sum(r['n_preach'] for r in recs)/max(n,1):.1f}")


if __name__ == "__main__":
    main()
