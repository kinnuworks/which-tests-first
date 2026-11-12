"""Memorisation probe (analysis_plan_addendum_memorisation.md): blind recall of failing tests.

The model gets only the repository name and the changed function's name and file,
no code and no candidates, and names up to 10 tests that would fail. We record
whether any named test exists in the suite and whether any is a failing test.

Usage: python memorisation_probe.py <data_dir> <model> <out.jsonl>
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rerank import call  # noqa: E402

REPO_NAME = {"cachetools": "cachetools", "toolz": "toolz", "humanize": "humanize",
             "python-sortedcontainers": "sortedcontainers", "fastapi": "FastAPI", "real": "FastAPI",
             "real_rich": "Rich (Textualize/rich)", "real_requests": "requests (psf/requests)"}
PROMPT = """Repository: {repo} (Python, open source).
A developer changed the function `{func}` in `{file}`. You cannot see the code or the change.
From your knowledge of this repository's test suite, list up to 10 test function names (for example test_something) that would most likely fail if this function were broken.
Return JSON: {{"tests": ["test_name", ...]}}"""


def base(t):
    return re.sub(r"\[.*\]$", "", t.split("::")[-1])


def records(d):
    for repo in ("cachetools", "toolz", "humanize", "python-sortedcontainers", "fastapi"):
        muts = {json.loads(l)["id"]: json.loads(l) for l in open(d / "v2" / f"mut_{repo}.jsonl")}
        for l in open(d / "v2" / f"rank_{repo}.jsonl"):
            r = json.loads(l)
            if r["failing"]:
                yield "planted", repo, muts[r["id"]], r
    for sub in ("real", "real_rich", "real_requests"):
        for mp in sorted((d / sub).glob("mut_*.jsonl")):
            tid = mp.stem[4:]
            rp = d / sub / f"rank_{tid}.jsonl"
            if not rp.exists():
                continue
            r = json.loads(rp.read_text().splitlines()[0])
            if r["failing"]:
                yield "real", sub, json.loads(mp.read_text().splitlines()[0]), r


def main():
    d, model, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    cache = d / "rr" / "cache"
    done = set()
    if Path(out).exists():
        done = {json.loads(l)["id"] for l in open(out)}
    w = open(out, "a")
    for kind, repo, m, r in records(d):
        if r["id"] in done:
            continue
        prompt = PROMPT.format(repo=REPO_NAME[repo], func=m["function"], file=m["file"])
        res = call(model, prompt, str(cache))
        try:
            names = [str(x) for x in json.loads(res["content"]).get("tests", [])][:10]
        except Exception:
            names = []
        names = [base(n) for n in names]
        suite = {base(t) for t in r["full"]}
        failing = {base(t) for t in r["failing"]}
        w.write(json.dumps({"id": r["id"], "kind": kind, "repo": repo, "named": names,
                            "exists": any(n in suite for n in names), "blind_hit": any(n in failing for n in names)}) + "\n")
        w.flush()
    print("PROBE_DONE", model, flush=True)


if __name__ == "__main__":
    main()
