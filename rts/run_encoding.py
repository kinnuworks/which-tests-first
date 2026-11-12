"""Graph-encoding ablation runs (addendum_encoding): arms none and path with Gemma 4 E2B."""
import glob, json, os, subprocess
from pathlib import Path
W = Path(__file__).resolve().parent.parent
PY = str(W / ".venv/bin/python")
M = "gemma4:e2b-it-qat"
def rr(repo, rank, mut, out, arm, prof_glob):
    env = dict(os.environ, PROF_GLOB=prof_glob)
    subprocess.run([PY, str(W / "infra/rerank3.py"), str(repo), str(rank), str(mut), M, str(out), str(W / "data/rr/cache"), arm], env=env)
for repo, prof in (("cachetools", "prof_cachetools"), ("toolz", "prof_toolz"), ("python-sortedcontainers", "prof_python-sortedcontainers")):
    for arm in ("none", "path"):
        rr(W / repo, W / f"data/v2/rank_{repo}.jsonl", W / f"data/v2/mut_{repo}.jsonl", W / f"data/rr/enc_{arm}_e2b_{repo}.jsonl", arm, str(W / f"data/{prof}.junit.xml"))
        print(repo, arm, "done", flush=True)
REPO, OUT = W / "rich", W / "data/real_rich"
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(W / "comp/tasks.jsonl")}
for mp in sorted(glob.glob(str(OUT / "mut_*.jsonl"))):
    tid = Path(mp).stem[4:]
    t = tasks[tid]
    subprocess.run(["git", "checkout", "-qf", t["base_commit"]], cwd=REPO); subprocess.run(["git", "clean", "-fdq"], cwd=REPO)
    for k in ("patch", "test_patch"):
        p = OUT / f"_{k}.diff"; p.write_text(t[k].rstrip("\n") + "\n"); subprocess.run(["git", "apply", str(p)], cwd=REPO)
    for arm in ("none", "path"):
        rr(REPO, OUT / f"rank_{tid}.jsonl", mp, OUT / f"enc_{arm}_e2b_{tid}.jsonl", arm, str(OUT / f"prof_{tid}.junit.xml"))
    print(tid, "done", flush=True)
subprocess.run(["git", "checkout", "-qf", "3a109ccdffe5b2d0e30684a304fbd388e99ce57b"], cwd=REPO); subprocess.run(["git", "clean", "-fdq"], cwd=REPO)
print("ENCODING_DONE", flush=True)
