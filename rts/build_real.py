"""Real regressions from the competition's FastAPI tasks.

For each task: check out base_commit, apply the fix (patch) and its tests (test_patch),
then undo the fix while keeping the tests. Tests that pass with the fix and fail without
it are the ground truth: undoing the fix is a real regression of real code. Only tasks
whose fix edits existing functions under fastapi/ are used (a new feature has no
"before" behaviour to regress).

Each kept task gets a one-record mutant file, a profile of the fixed state, rankings
from every method, and Gemma re-rankings, all written under data/real/.

Usage: python build_real.py <tasks.jsonl> <max_tasks>
"""
import ast
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

W = Path(__file__).resolve().parent.parent
REPO = W / os.environ.get("RT_REPO", "fastapi")
PKG = os.environ.get("RT_PKG", "fastapi")
OUT = W / "data" / os.environ.get("RT_OUT", "real")
PYF = str(W / os.environ.get("RT_VENV", ".venv-fastapi") / "bin" / "python")
REPONAME = os.environ.get("RT_REPONAME", "fastapi/fastapi")
FINAL = os.environ.get("RT_FINAL", "f1d750fddad90e2faad6c3cc5c85c7687b787e89")
V2 = os.environ.get("RT_V2") == "1"
PY = str(W / ".venv" / "bin" / "python")


def sh(cmd, **kw):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, **kw)


fixed_ids = set()


def run_suite(tag):
    xml = OUT / f"_{tag}.xml"
    env = dict(os.environ, PYTEST_ADDOPTS="-n 4", PYTHONPATH=str(REPO))
    try:
        subprocess.run([PYF, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", "-o", "junit_family=xunit1"],
                       cwd=REPO, capture_output=True, env=env, timeout=300)
    except subprocess.TimeoutExpired:
        subprocess.run(["pkill", "-f", "junitxml=" + str(xml)])
        if xml.exists():
            xml.unlink()
        return None
    failed = set()
    if xml.exists():
        if tag == "fixed":
            fixed_ids.clear()
            fixed_ids.update(f"{c.get('classname')}::{c.get('name')}" for c in ET.parse(xml).getroot().iter("testcase"))
        for c in ET.parse(xml).getroot().iter("testcase"):
            if c.find("failure") is not None or c.find("error") is not None:
                failed.add(f"{c.get('classname')}::{c.get('name')}")
        xml.unlink()
    return failed


def changed_functions(patch):
    """(file, function qualname, first changed line in the fixed file, n lines) for fastapi/ hunks."""
    out, cur, newline = [], None, 0
    touched = {}
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
        elif line.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
            newline = int(m.group(1))
        elif cur and line.startswith("+") and not line.startswith("+++"):
            touched.setdefault(cur, []).append(newline)
            newline += 1
        elif cur and line.startswith("-") and not line.startswith("---"):
            touched.setdefault(cur, []).append(newline)
        elif cur:
            newline += 1
    for f, lines in touched.items():
        if not f.startswith(PKG + "/") or not f.endswith(".py"):
            continue
        src = (REPO / f).read_text()
        spans = []

        def walk(node, prefix):
            for ch in ast.iter_child_nodes(node):
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    q = f"{prefix}.{ch.name}" if prefix else ch.name
                    if not isinstance(ch, ast.ClassDef):
                        spans.append((ch.lineno, ch.end_lineno, q))
                    walk(ch, q)

        walk(ast.parse(src), "")
        per = {}
        for ln in lines:
            best = None
            for a, b, q in spans:
                if a <= ln <= b and (best is None or a >= best[0]):
                    best = (a, b, q)
            if best:
                per.setdefault(best[2], []).append(ln)
        for q, ls in per.items():
            out.append((f, q, min(ls), len(ls)))
    return out


def main():
    tasks = [json.loads(l) for l in open(sys.argv[1])]
    max_tasks = int(sys.argv[2])
    OUT.mkdir(parents=True, exist_ok=True)
    fa = sorted([t for t in tasks if t["repo"] == REPONAME], key=lambda t: t["created_at"], reverse=True)
    log = open(OUT / "build.log", "a")
    kept = len(list(OUT.glob("mut_*.jsonl")))
    for t in fa:
        if kept >= max_tasks:
            break
        tid = t["instance_id"]
        if (OUT / f"mut_{tid}.jsonl").exists() or (OUT / f"skip_{tid}").exists():
            continue
        files = re.findall(r"^\+\+\+ b/(\S+)", t["patch"], re.M)
        code_files = [f for f in files if f.startswith(PKG + "/")]
        new_files = re.findall(r"^--- /dev/null|^@@ -0,0 ", t["patch"], re.M)
        if not code_files or new_files:
            (OUT / f"skip_{tid}").write_text("no fastapi/ edit or adds files")
            continue
        sh(["git", "checkout", "-qf", t["base_commit"]])
        sh(["git", "clean", "-fdq"])
        (OUT / "_p.diff").write_text(t["patch"].rstrip("\n") + "\n")
        (OUT / "_t.diff").write_text(t["test_patch"].rstrip("\n") + "\n")
        a = sh(["git", "apply", str(OUT / "_p.diff")])
        b = sh(["git", "apply", str(OUT / "_t.diff")])
        if a.returncode or b.returncode:
            (OUT / f"skip_{tid}").write_text("patch did not apply")
            continue
        # install this commit's own pinned dependencies so the suite runs as it did upstream
        env_sync = dict(os.environ, UV_PROJECT_ENVIRONMENT=str(W / ".venv-fastapi"))
        if REPONAME == "fastapi/fastapi" and (REPO / "uv.lock").exists():
            subprocess.run(["uv", "sync", "-q", "--group", "tests", "--extra", "all"], cwd=REPO, env=env_sync, capture_output=True)
        elif (REPO / "requirements-tests.txt").exists():
            subprocess.run(["uv", "pip", "install", "-q", "-p", PYF, "-e", ".[all]", "-r", "requirements-tests.txt"], cwd=REPO, capture_output=True)
        subprocess.run(["uv", "pip", "install", "-q", "-p", PYF, "-e", ".", "pytest-xdist", "pytest-cov", "networkx", "scikit-learn"], cwd=REPO, capture_output=True)
        funcs = changed_functions(t["patch"])
        # keep only functions that already exist at base_commit (a regression needs prior behaviour)
        def base_quals(path):
            src = subprocess.run(["git", "show", f"{t['base_commit']}:{path}"], cwd=REPO, capture_output=True, text=True).stdout
            qs = set()
            def walk(node, prefix):
                for ch in ast.iter_child_nodes(node):
                    if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        q = f"{prefix}.{ch.name}" if prefix else ch.name
                        qs.add(q)
                        walk(ch, q)
            try:
                walk(ast.parse(src), "")
            except SyntaxError:
                pass
            return qs
        funcs = [x for x in funcs if x[1] in base_quals(x[0])]
        if not funcs:
            (OUT / f"skip_{tid}").write_text("no changed function")
            continue
        fixed_fail = run_suite("fixed")
        sh(["git", "apply", "-R", str(OUT / "_p.diff")])
        bug_fail = run_suite("bug") if fixed_fail is not None else None
        if fixed_fail is None or bug_fail is None:
            (OUT / f"skip_{tid}").write_text("test suite timed out")
            print(f"{tid}: skipped, suite timed out", file=log, flush=True)
            continue
        caught = sorted(bug_fail - fixed_fail)
        # a module that fails to import shows up as '::tests.test_x'; expand it to the module's tests
        expanded = []
        for c in caught:
            if c.startswith("::"):
                mod = c[2:]
                expanded += sorted(x for x in fixed_ids if x.split("::")[0] == mod or x.split("::")[0].startswith(mod + "."))
            else:
                expanded.append(c)
        caught = sorted(set(expanded))
        if len(fixed_fail) > 20:
            (OUT / f"skip_{tid}").write_text(f"environment: {len(fixed_fail)} tests fail with the fix applied")
            print(f"{tid}: skipped, {len(fixed_fail)} failures in fixed state", file=log, flush=True)
            sh(["git", "checkout", "-qf", "."])
            continue
        sh(["git", "apply", str(OUT / "_p.diff")])  # back to the fixed state for profiling and graphs
        if not caught:
            (OUT / f"skip_{tid}").write_text("no test fails without the fix")
            print(f"{tid}: skipped, no failing test", file=log, flush=True)
            continue
        f, q, line, n = max(funcs, key=lambda x: x[3])
        diff_rev = "".join(
            ("-" + l[1:] if l.startswith("+") and not l.startswith("+++") else "+" + l[1:] if l.startswith("-") and not l.startswith("---") else l) + "\n"
            for l in t["patch"].splitlines())
        rec = {"id": tid, "file": f, "line": line, "function": q, "kind": "real", "diff": diff_rev,
               "failing_tests": caught, "all_changed": [list(x) for x in funcs], "base_commit": t["base_commit"]}
        mp = OUT / f"mut_{tid}.jsonl"
        mp.write_text(json.dumps(rec) + "\n")
        prof = OUT / f"prof_{tid}"
        env = dict(os.environ, COVERAGE_CORE="ctrace", PYTHONPATH=str(REPO),
                   PYTEST_ADDOPTS="-W ignore::pytest_cov.CentralCovContextWarning -W ignore::coverage.exceptions.CoverageWarning")
        subprocess.run(["bash", str(W / "infra" / "profile_tests.sh"), str(REPO), PKG, str(prof)],
                       capture_output=True, env=dict(env, PATH=str(Path(PYF).parent) + ":" + os.environ["PATH"]))
        if Path(str(prof) + ".coverage").exists() is False and (REPO / ".coverage").exists():
            (REPO / ".coverage").rename(str(prof) + ".coverage")
        cov = REPO / "coverage" / ".coverage"
        if cov.exists():
            cov.rename(str(prof) + ".coverage")
        rk = OUT / f"rank_{tid}.jsonl"
        subprocess.run([PYF, str(W / "infra" / "select_tests.py"), str(REPO), str(mp), str(prof), str(rk)], capture_output=True)
        C = f"{PKG}_{t['base_commit']}"
        gj, ez = W / "comp" / "graphs" / f"{C}.json", W / "comp" / "embeddings" / f"{C}.npz"
        for p in (gj, ez):
            if not p.exists():
                subprocess.run([str(W / ".venv" / "bin" / "kaggle"), "competitions", "download", "gemma-4-developer-agent",
                                "-f", str(p.relative_to(W / "comp")), "-p", str(W / "comp")], capture_output=True)
        if gj.exists() and ez.exists() and rk.exists():
            subprocess.run([PY, str(W / "infra" / "select_provided.py"), str(rk), str(mp), str(gj), str(ez)], capture_output=True)
        for model in ("gemma4:e2b-it-qat", "gemma4:e4b-it-qat"):
            tag = model.split(":")[1].split("-")[0]
            subprocess.run([PY, str(W / "infra" / "rerank.py"), str(REPO), str(rk), str(mp), model,
                            str(OUT / f"rr_{tag}_{tid}.jsonl"), str(W / "data" / "rr" / "cache")], capture_output=True)
        if V2:
            for model in ("gemma4:e2b-it-qat", "gemma4:e4b-it-qat"):
                tag = model.split(":")[1].split("-")[0]
                subprocess.run([PY, str(W / "infra" / "rerank2.py"), str(REPO), str(rk), str(mp), model,
                                str(OUT / f"rr2_{tag}_{tid}.jsonl"), str(W / "data" / "rr" / "cache")], capture_output=True)
        kept += 1
        print(f"{tid}: kept ({q} in {f}, {len(caught)} failing tests, fixed-state failures {len(fixed_fail)})", file=log, flush=True)
    sh(["git", "checkout", "-qf", FINAL])
    sh(["git", "clean", "-fdq"])
    if REPONAME == "fastapi/fastapi":
        subprocess.run(["uv", "sync", "-q", "--group", "tests", "--extra", "all"], cwd=REPO,
                       env=dict(os.environ, UV_PROJECT_ENVIRONMENT=str(W / ".venv-fastapi")), capture_output=True)
    subprocess.run(["uv", "pip", "install", "-q", "-p", PYF, "pytest-xdist", "pytest-cov", "networkx", "scikit-learn"], cwd=REPO, capture_output=True)
    print("REAL_DONE", file=log, flush=True)


if __name__ == "__main__":
    main()
