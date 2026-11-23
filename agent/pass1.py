"""Pass 1: baseline single-shot research for all apps (or a subset). Saves raw output untouched.
Usage: python -m agent.pass1 [--only 1,5,9] [--workers 8]
"""
import argparse, csv, json, pathlib, concurrent.futures as cf
from dotenv import load_dotenv
load_dotenv()
from .llm import research

OUT = pathlib.Path("out/pass1"); OUT.mkdir(parents=True, exist_ok=True)


def run_one(row):
    p = OUT / f"{int(row['id']):03d}.json"
    if p.exists():
        return row["app"], "cached"
    try:
        rec = research(row["app"], row["category_given"], row["hint"])
        p.write_text(rec.model_dump_json(indent=2), encoding="utf-8")
        return row["app"], "ok"
    except Exception as e:
        p.with_suffix(".err").write_text(str(e), encoding="utf-8")
        return row["app"], f"ERR {e}"[:120]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    rows = list(csv.DictReader(open("data/apps.csv")))
    if a.only:
        keep = {int(x) for x in a.only.split(",")}
        rows = [r for r in rows if int(r["id"]) in keep]
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for app, status in ex.map(run_one, rows):
            print(f"{app:30s} {status}")
