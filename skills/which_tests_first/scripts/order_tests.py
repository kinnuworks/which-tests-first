"""Order a repository's tests for the current uncommitted change. Standard library only.

Usage: python order_tests.py [repo_dir] [max_tests]
Prints pytest node ids, best first: half by call-graph distance from the changed
functions to test functions, half by identifier overlap with the changed source.
"""
import ast
import os
import re
import subprocess
import sys
from collections import defaultdict, deque

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 30
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "docs", "node_modules", "__pycache__"}
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def changed_lines():
    out = subprocess.run(["git", "diff", "-U0", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout
    lines, cur = defaultdict(set), None
    for l in out.splitlines():
        if l.startswith("+++ b/"):
            cur = l[6:]
        elif l.startswith("@@") and cur and cur.endswith(".py"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))?", l)
            start, n = int(m.group(1)), int(m.group(2) or 1)
            lines[cur].update(range(start, start + max(n, 1)))
    return lines


def is_test_path(p):
    parts = p.split(os.sep)
    return any(x in ("tests", "test", "testing") for x in parts) or os.path.basename(p).startswith("test_")


def main():
    defs, calls, src = {}, defaultdict(set), {}   # node -> (path, start, end), caller -> names, node -> source
    by_name = defaultdict(list)
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.relpath(os.path.join(dirpath, f), ROOT)
            try:
                text = open(os.path.join(ROOT, path), encoding="utf-8").read()
                tree = ast.parse(text)
            except Exception:
                continue
            lines = text.splitlines()

            def walk(node, prefix, cls):
                for ch in ast.iter_child_nodes(node):
                    if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        q = f"{prefix}.{ch.name}" if prefix else ch.name
                        key = f"{path}::{q}"
                        if not isinstance(ch, ast.ClassDef):
                            defs[key] = (path, ch.lineno, ch.end_lineno, ch.name, cls)
                            src[key] = "\n".join(lines[ch.lineno - 1:ch.end_lineno])
                            by_name[ch.name].append(key)
                            for sub in ast.walk(ch):
                                if isinstance(sub, ast.Call):
                                    fn = sub.func
                                    calls[key].add(fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else "")
                                elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                                    calls[key].add(sub.id)
                        walk(ch, q, ch.name if isinstance(ch, ast.ClassDef) else cls)
            walk(tree, "", None)

    # reverse call graph: callee -> callers (names resolved when they match at most 8 definitions)
    rev = defaultdict(set)
    for caller, names in calls.items():
        for n in names:
            targets = by_name.get(n, [])
            if 0 < len(targets) <= 8:
                for t in targets:
                    if t != caller:
                        rev[t].add(caller)

    changed = []
    for path, ls in changed_lines().items():
        for key, (p, a, b, name, cls) in defs.items():
            if p == path and any(a <= x <= b for x in ls):
                changed.append(key)
    # keep the innermost function for each changed line
    changed = [k for k in changed if not any(o != k and o.startswith(k + ".") for o in changed)]
    if not changed:
        print("No changed Python function found in `git diff HEAD`. Run the full suite.")
        return

    tests = [k for k, v in defs.items() if is_test_path(v[0]) and v[3].startswith("test")]

    # graph distance: BFS over callers from every changed function
    dist = {}
    q = deque((c, 0) for c in changed)
    seen = set(changed)
    while q:
        n, d = q.popleft()
        if n in tests and n not in dist:
            dist[n] = d
        for c in rev.get(n, ()):
            if c not in seen:
                seen.add(c)
                q.append((c, d + 1))
    by_graph = sorted(dist, key=lambda t: (dist[t], t))

    # identifier overlap between changed source and each test's source
    want = set()
    for c in changed:
        want |= set(WORD.findall(src.get(c, "")))
    def overlap(t):
        have = set(WORD.findall(src.get(t, "")))
        return len(want & have) / (len(have) ** 0.5 + 1)
    by_words = sorted(tests, key=lambda t: -overlap(t))

    half = LIMIT // 2
    picked = by_graph[:half]
    for t in by_words:
        if len(picked) >= LIMIT:
            break
        if t not in picked:
            picked.append(t)

    def node_id(key):
        path, a, b, name, cls = defs[key]
        return f"{path}::{cls}::{name}" if cls else f"{path}::{name}"

    print("Changed functions: " + ", ".join(c.split("::")[1] for c in changed))
    print("\nTests to run first (best first):")
    for t in picked:
        why = f"graph distance {dist[t]}" if t in dist and t in by_graph[:half] else "shares identifiers"
        print(f"{node_id(t)}    # {why}")
    files = []
    for t in picked:
        if defs[t][0] not in files:
            files.append(defs[t][0])
    print("\nTest files to run next: " + " ".join(files))


if __name__ == "__main__":
    main()
