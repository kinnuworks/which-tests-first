"""Build a symbol-level code graph for a Python repository from its ASTs.

Nodes are modules, classes and functions (qualified as path::Qual.name). Edges:
  contains  module/class -> member
  calls     function -> function it calls (resolved by name, best effort)
  imports   module -> module it imports
Test functions are ordinary nodes whose path sits under a tests folder.

Name resolution is static and approximate on purpose: it is the same kind of
graph a code-graph tool gives an agent, with the same blind spots (dynamic
dispatch, fixtures, getattr).
"""
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx


def module_name(rel):
    parts = list(Path(rel).with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


class Collector(ast.NodeVisitor):
    def __init__(self, rel, graph):
        self.rel, self.g, self.stack = rel, graph, []
        self.mod = f"{rel}::"
        graph.add_node(self.mod, kind="module", path=rel, name=module_name(rel))
        self.calls = []  # (caller node, called name, is_attribute)
        self.imports = []

    def qual(self, name):
        return f"{self.rel}::" + ".".join([s for s, _ in self.stack] + [name])

    def _def(self, node, kind):
        q = self.qual(node.name)
        parent = self.qual("").rstrip(".") if self.stack else self.mod
        if parent.endswith("::"):
            parent = self.mod
        self.g.add_node(q, kind=kind, path=self.rel, name=node.name,
                        start=node.lineno, end=node.end_lineno)
        self.g.add_edge(parent, q, type="contains")
        self.stack.append((node.name, q))
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node):
        self._def(node, "class")

    def visit_FunctionDef(self, node):
        self._def(node, "function")

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        caller = next((q for _, q in reversed(self.stack)
                       if self.g.nodes[q]["kind"] == "function"), self.mod)
        f = node.func
        if isinstance(f, ast.Name):
            self.calls.append((caller, f.id, False))
        elif isinstance(f, ast.Attribute):
            self.calls.append((caller, f.attr, True))
        self.generic_visit(node)

    def visit_Name(self, node):
        # A bare reference (e.g. passing a function or class) counts as a use.
        if isinstance(node.ctx, ast.Load) and self.stack:
            caller = next((q for _, q in reversed(self.stack)
                           if self.g.nodes[q]["kind"] == "function"), self.mod)
            self.calls.append((caller, node.id, False))

    def visit_Import(self, node):
        self.imports += [a.name for a in node.names]

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
            self.imports += [f"{node.module}.{a.name}" for a in node.names]


def build(repo):
    repo = Path(repo).resolve()
    g = nx.MultiDiGraph()
    collectors = []
    for path in sorted(repo.rglob("*.py")):
        rel = str(path.relative_to(repo))
        if any(p.startswith(".") or p in ("build", "docs", "venv", ".venv") for p in Path(rel).parts):
            continue
        try:
            tree = ast.parse(path.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        c = Collector(rel, g)
        c.visit(tree)
        collectors.append(c)

    by_name = defaultdict(list)
    for n, d in g.nodes(data=True):
        if d["kind"] in ("function", "class"):
            by_name[d["name"]].append(n)
    mods = {d["name"]: n for n, d in g.nodes(data=True) if d["kind"] == "module"}

    for c in collectors:
        for caller, name, attr in c.calls:
            targets = by_name.get(name, [])
            # Skip very common names that would link everything to everything.
            if 0 < len(targets) <= 8:
                for t in targets:
                    if t != caller:
                        g.add_edge(caller, t, type="calls")
        for imp in c.imports:
            for cand in (imp, imp.rsplit(".", 1)[0]):
                if cand in mods:
                    g.add_edge(c.mod, mods[cand], type="imports")
                    break
    return g


def is_test(node, data):
    parts = Path(data.get("path", "")).parts
    in_tests = any(p in ("tests", "test", "testing") for p in parts) or Path(data.get("path", "")).name.startswith("test_")
    return in_tests and data.get("kind") == "function" and data.get("name", "").startswith("test")


if __name__ == "__main__":
    g = build(sys.argv[1])
    types = defaultdict(int)
    for _, _, d in g.edges(data=True):
        types[d["type"]] += 1
    tests = sum(1 for n, d in g.nodes(data=True) if is_test(n, d))
    print(json.dumps({"nodes": g.number_of_nodes(), "edges": dict(types), "test_functions": tests}))
