"""Re-profile and re-rank Rich tasks whose profiling stopped on an unrelated collection error."""
import glob, json, os, subprocess
from pathlib import Path
W = Path(__file__).resolve().parent.parent
REPO, OUT = W / "rich", W / "data" / "real_rich"
PYF, PY = str(W / ".venv-rich/bin/python"), str(W / ".venv/bin/python")
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(W / "comp/tasks.jsonl")}
for mp in sorted(glob.glob(str(OUT / "mut_*.jsonl"))):
    tid = Path(mp).stem[4:]
    if (OUT / f"rank_{tid}.jsonl").exists():
        continue
    t = tasks[tid]
    subprocess.run(["git", "checkout", "-qf", t["base_commit"]], cwd=REPO); subprocess.run(["git", "clean", "-fdq"], cwd=REPO)
    for k in ("patch", "test_patch"):
        p = OUT / f"_{k}.diff"; p.write_text(t[k].rstrip("\n") + "\n"); subprocess.run(["git", "apply", str(p)], cwd=REPO)
    subprocess.run(["uv", "pip", "install", "-q", "-p", PYF, "-e", "."], cwd=REPO, capture_output=True)
    prof = OUT / f"prof_{tid}"
    env = dict(os.environ, COVERAGE_CORE="ctrace", PYTHONPATH=str(REPO), PATH=str(Path(PYF).parent) + ":" + os.environ["PATH"],
               PYTEST_ADDOPTS="--continue-on-collection-errors")
    subprocess.run(["bash", str(W / "infra/profile_tests.sh"), str(REPO), "rich", str(prof)], capture_output=True, env=env)
    rk = OUT / f"rank_{tid}.jsonl"
    subprocess.run([PYF, str(W / "infra/select_tests.py"), str(REPO), mp, str(prof), str(rk)], capture_output=True)
    C = f"rich_{t['base_commit']}"
    gj, ez = W / "comp/graphs" / f"{C}.json", W / "comp/embeddings" / f"{C}.npz"
    if gj.exists() and ez.exists() and rk.exists():
        subprocess.run([PY, str(W / "infra/select_provided.py"), str(rk), mp, str(gj), str(ez)], capture_output=True)
    for script, pre in (("rerank.py", "rr"), ("rerank2.py", "rr2")):
        for model in ("gemma4:e2b-it-qat", "gemma4:e4b-it-qat"):
            tag = model.split(":")[1].split("-")[0]
            outp = OUT / f"{pre}_{tag}_{tid}.jsonl"
            if outp.exists():
                outp.unlink()
            subprocess.run([PY, str(W / "infra" / script), str(REPO), str(rk), mp, model, str(outp), str(W / "data/rr/cache")], capture_output=True)
    print(tid, "rank" if rk.exists() else "NO RANK", flush=True)
subprocess.run(["git", "checkout", "-qf", "3a109ccdffe5b2d0e30684a304fbd388e99ce57b"], cwd=REPO); subprocess.run(["git", "clean", "-fdq"], cwd=REPO)
print("FIX7_DONE", flush=True)
