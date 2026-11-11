"""Plant single-operator bugs in a library and record which tests catch each one.

Usage: python mutate.py <repo_dir> <package_dir_rel> <out.jsonl> [max_mutants] [seed]

For every candidate site (comparison, arithmetic, boolean operator, constant),
we swap one operator, run the library's own test suite, and keep the mutant only
if at least one test fails. Each output line holds the mutant's file, line,
function, the diff, and the ids of the failing tests.
"""
import ast
import difflib
import json
import random
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Is: ast.IsNot, ast.IsNot: ast.Is,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult,
    ast.And: ast.Or, ast.Or: ast.And,
}


def enclosing_functions(tree):
    """Map line number -> qualified name of the innermost enclosing def."""
    spans = []

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}.{child.name}" if prefix else child.name
                if not isinstance(child, ast.ClassDef):
                    spans.append((child.lineno, child.end_lineno, name))
                walk(child, name)
            else:
                walk(child, prefix)

    walk(tree, "")
    return spans


def func_at(spans, line):
    best = None
    for start, end, name in spans:
        if start <= line <= end and (best is None or start >= best[0]):
            best = (start, end, name)
    return best[2] if best else None


def candidate_sites(tree):
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                if type(op) in SWAPS:
                    sites.append(("cmp", node, i))
        elif isinstance(node, ast.BinOp) and type(node.op) in SWAPS:
            sites.append(("bin", node, None))
        elif isinstance(node, ast.BoolOp) and type(node.op) in SWAPS:
            sites.append(("bool", node, None))
        elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
            sites.append(("const", node, None))
        elif isinstance(node, ast.Constant) and type(node.value) is int and node.value in (0, 1):
            sites.append(("int", node, None))
    return sites


def apply(kind, node, i):
    """Mutate the node in place and return an undo function."""
    if kind == "cmp":
        old = node.ops[i]
        node.ops[i] = SWAPS[type(old)]()
        return lambda: node.ops.__setitem__(i, old)
    if kind in ("bin", "bool"):
        old = node.op
        node.op = SWAPS[type(old)]()
        return lambda: setattr(node, "op", old)
    old = node.value
    node.value = (not old) if kind == "const" else (1 - old)
    return lambda: setattr(node, "value", old)


def run_tests(repo, timeout=int(__import__("os").environ.get("MUT_TIMEOUT", "120"))):
    xml = Path(repo) / ".mut_report.xml"
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", "-o", "junit_family=xunit1"],
            cwd=repo, capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None
    if not xml.exists():
        return None
    failed = []
    for case in ET.parse(xml).getroot().iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(f"{case.get('classname')}::{case.get('name')}")
    xml.unlink()
    return failed


def main():
    repo, pkg, out = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    max_mutants = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    rng = random.Random(int(sys.argv[5]) if len(sys.argv) > 5 else 0)

    baseline = run_tests(repo)
    if baseline is None:
        sys.exit("baseline test run failed")
    base_fail = set(baseline)

    pool = []
    for path in sorted((repo / pkg).rglob("*.py")):
        if "test" in path.name:
            continue
        src = path.read_text()
        tree = ast.parse(src)
        spans = enclosing_functions(tree)
        for idx, (kind, node, i) in enumerate(candidate_sites(tree)):
            fn = func_at(spans, node.lineno)
            if fn:
                pool.append((path, idx, fn))
    rng.shuffle(pool)

    kept = 0
    with open(out, "w") as f:
        for path, idx, fn in pool:
            if kept >= max_mutants:
                break
            src = path.read_text()
            tree = ast.parse(src)
            kind, node, i = candidate_sites(tree)[idx]
            line = node.lineno
            undo = apply(kind, node, i)
            try:
                new_src = ast.unparse(tree)
                undo()
                old_norm = ast.unparse(tree)
            except Exception:
                continue
            if new_src == old_norm:
                continue
            path.write_text(new_src)
            try:
                failed = run_tests(repo)
            finally:
                path.write_text(src)
            if not failed:
                continue
            caught = sorted(set(failed) - base_fail)
            if not caught:
                continue
            diff = "".join(difflib.unified_diff(
                old_norm.splitlines(True), new_src.splitlines(True),
                fromfile=str(path.relative_to(repo)), tofile=str(path.relative_to(repo)), n=2))
            f.write(json.dumps({
                "id": f"{repo.name}-{kept:04d}", "file": str(path.relative_to(repo)),
                "line": line, "function": fn, "kind": kind, "diff": diff, "failing_tests": caught,
            }) + "\n")
            f.flush()
            kept += 1
            print(f"kept {kept}: {fn} ({kind}) -> {len(caught)} failing", flush=True)


if __name__ == "__main__":
    main()
