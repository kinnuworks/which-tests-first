"""Summarise the memorisation probe against the re-ranker's Recall@10.

Usage: python analyze_memorisation.py <data_dir>
"""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
rows = {}
for tag in ("e2b", "e4b"):
    p = d / f"mem_{tag}.jsonl"
    if p.exists():
        rows[tag] = [json.loads(l) for l in open(p)]
print("## Memorisation probe: blind recall without code or candidates\n")
print("| Model | Set | n | named test exists | named test fails (blind hit) |\n|---|---|---|---|---|")
out = {}
for tag, rs in rows.items():
    for kind in ("planted", "real"):
        k = [r for r in rs if r["kind"] == kind]
        if not k:
            continue
        ex = sum(r["exists"] for r in k) / len(k)
        hit = sum(r["blind_hit"] for r in k) / len(k)
        out[f"{tag}:{kind}"] = {"n": len(k), "exists": ex, "blind_hit": hit}
        print(f"| {tag.upper()} | {kind} | {len(k)} | {ex:.2f} | {hit:.2f} |")
(d / "results_memorisation.json").write_text(json.dumps(out, indent=1))
