"""Run the v2 re-ranker on the real FastAPI regressions (fixed state checked out per task)."""
import glob
import json
import subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
REPO = W / "fastapi"
OUT = W / "data" / "real"
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(W / "comp" / "tasks.jsonl")}
for mp in sorted(glob.glob(str(OUT / "mut_*.jsonl"))):
    tid = Path(mp).stem[4:]
    t = tasks[tid]
    if all((OUT / f"rr2_{tag}_{tid}.jsonl").exists() for tag in ("e2b", "e4b")):
        continue
    subprocess.run(["git", "checkout", "-qf", t["base_commit"]], cwd=REPO)
    subprocess.run(["git", "clean", "-fdq"], cwd=REPO)
    for k in ("patch", "test_patch"):
        p = OUT / f"_{k}.diff"
        p.write_text(t[k].rstrip("\n") + "\n")
        subprocess.run(["git", "apply", str(p)], cwd=REPO)
    for model in ("gemma4:e2b-it-qat", "gemma4:e4b-it-qat"):
        tag = model.split(":")[1].split("-")[0]
        subprocess.run([str(W / ".venv" / "bin" / "python"), str(W / "infra" / "rerank2.py"), str(REPO), str(OUT / f"rank_{tid}.jsonl"),
                        mp, model, str(OUT / f"rr2_{tag}_{tid}.jsonl"), str(W / "data" / "rr" / "cache")])
    print(tid, "done", flush=True)
subprocess.run(["git", "checkout", "-qf", "f1d750fddad90e2faad6c3cc5c85c7687b787e89"], cwd=REPO)
subprocess.run(["git", "clean", "-fdq"], cwd=REPO)
print("REAL_V2_DONE", flush=True)
