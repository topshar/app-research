"""Pass 2: deterministic checks, then an independent verifier agent re-researches ONLY flagged records
(and a random 15% control slice), with the pass-1 claims + the issues as a challenge prompt.
Usage: python -m agent.pass2 [--workers 8]
"""
import argparse, json, os, pathlib, random, concurrent.futures as cf
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault('LLM_MAX_TRIES', '3')  # fail fast: keep pass-1 answer if Gemini is overloaded
from .llm import research
from .checks import run_all
from .schema import AppRecord
import csv

IN, OUT = pathlib.Path("out/pass1"), pathlib.Path("out/pass2"); OUT.mkdir(parents=True, exist_ok=True)
APPS = {int(r["id"]): r for r in csv.DictReader(open("data/apps.csv"))}


def work(path):
    i = int(path.stem)
    if (OUT / f'{i:03d}.json').exists() and '--redo' not in __import__('sys').argv:
        return {'id': i, 'app': json.loads(path.read_text(encoding='utf-8'))['app'], 'pass1_issues': [], 'reresearched': False, 'skipped': 'already done'}
    rec = json.loads(path.read_text(encoding="utf-8"))
    issues = run_all(rec)
    log = {"id": i, "app": rec["app"], "pass1_issues": issues, "reresearched": False}
    final = rec
    hard = [x for x in issues if not x.startswith("evidence_link_blocked")]
    if hard or random.random() < 0.15:
        extra = ("A previous researcher produced this answer:\n" + json.dumps(rec) +
                 "\n\nAutomated checks flagged: " + (", ".join(hard) or "none (random audit)") +
                 "\nIndependently re-verify EVERY field against primary docs. Fix what is wrong, keep what is right. "
                 "Prefer docs pages you actually opened. If a snippet is not on the cited page, replace it.")
        try:
            new = research(rec["app"], APPS[i]["category_given"], APPS[i]["hint"], extra=extra, verify_rec=rec)
            final = json.loads(new.model_dump_json())
            log["reresearched"] = True
            log["fields_changed"] = [k for k in ("auth_methods", "access", "api_type", "api_breadth",
                                                 "mcp_status", "verdict", "main_blocker")
                                     if rec[k] != final[k]]
            log["pass2_issues"] = run_all(final)
        except Exception as e:
            log["error"] = str(e)[:200]
    (OUT / f"{i:03d}.json").write_text(json.dumps(final, indent=2), encoding="utf-8")
    return log


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true"); ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    random.seed(7)
    files = sorted(IN.glob("*.json"))
    logs = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for l in ex.map(work, files):
            logs.append(l); print(l["app"], l["pass1_issues"][:3], "-> changed" if l.get("fields_changed") else "")
    pathlib.Path("out/pass2_log.json").write_text(json.dumps(logs, indent=2), encoding="utf-8")
