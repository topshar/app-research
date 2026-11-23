"""Score a pass against the human gold set.
Gold file: data/gold.csv with columns id,auth_methods(;-sep),access,api_type,mcp_status,verdict,main_blocker,notes
Usage: python -m agent.evaluate pass1 pass2 pass3   -> per-field accuracy table (JSON in out/accuracy.json)
"""
import csv, json, sys, pathlib

FIELDS = ["auth_methods", "access", "api_type", "mcp_status", "verdict", "main_blocker"]


def val(rec, f):
    v = rec.get(f)
    return frozenset(v) if f == "auth_methods" else v


def score(passname, gold):
    per = {f: [0, 0] for f in FIELDS}; misses = []
    for g in gold:
        p = pathlib.Path(f"out/{passname}/{int(g['id']):03d}.json")
        if not p.exists():
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        for f in FIELDS:
            if not g[f].strip():
                continue  # not labelled
            want = frozenset(x for x in g[f].split(";") if x) if f == "auth_methods" else g[f]
            ok = val(rec, f) == want
            per[f][0] += ok; per[f][1] += 1
            if not ok:
                misses.append({"id": g["id"], "app": rec["app"], "field": f,
                               "agent": sorted(val(rec, f)) if f == "auth_methods" else val(rec, f),
                               "human": g[f], "note": g.get("notes", "")})
    acc = {f: round(a / n, 3) if n else None for f, (a, n) in per.items()}
    tot_a = sum(a for a, _ in per.values()); tot_n = sum(n for _, n in per.values())
    acc["overall"] = round(tot_a / tot_n, 3) if tot_n else None
    return acc, misses


if __name__ == "__main__":
    gold = list(csv.DictReader(open("data/gold.csv", encoding="utf-8")))
    res = {}
    for name in sys.argv[1:]:
        acc, misses = score(name, gold); res[name] = {"accuracy": acc, "misses": misses}
        print(name, acc)
    pathlib.Path("out/accuracy.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
