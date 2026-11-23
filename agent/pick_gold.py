"""Stratified gold sample: 3 apps per category (seeded). Prints ids and writes data/gold_template.csv to fill by hand."""
import csv, random
random.seed(11)
rows = list(csv.DictReader(open("data/apps.csv")))
by = {}
for r in rows: by.setdefault(r["category_given"], []).append(r)
pick = [x for c in by.values() for x in random.sample(c, 3)]
with open("data/gold_template.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id","app","auth_methods","access","api_type","mcp_status","verdict","main_blocker","notes"])
    for r in sorted(pick, key=lambda r: int(r["id"])): w.writerow([r["id"], r["app"], "", "", "", "", "", "", ""])
print(",".join(str(r["id"]) for r in sorted(pick, key=lambda r: int(r["id"]))))
