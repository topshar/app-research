"""Turn the final pass into patterns. Usage: python -m agent.analyze pass2 -> out/patterns.json + out/final.csv"""
import json, sys, pathlib, pandas as pd

name = sys.argv[1] if len(sys.argv) > 1 else "pass2"
rows = []
for p in sorted(pathlib.Path(f"out/{name}").glob("*.json")):
    r = json.loads(p.read_text(encoding="utf-8")); r["id"] = int(p.stem); rows.append(r)
df = pd.DataFrame(rows)
cats = pd.read_csv("data/apps.csv").set_index("id")["category_given"]
df["category"] = df["id"].map(cats)

ex = df.explode("auth_methods")
pat = {
    "n": len(df),
    "auth_share": ex["auth_methods"].value_counts(normalize=True).round(3).to_dict(),
    "auth_apps_with": ex.groupby("auth_methods")["id"].nunique().sort_values(ascending=False).to_dict(),
    "access_counts": df["access"].value_counts().to_dict(),
    "verdict_counts": df["verdict"].value_counts().to_dict(),
    "blocker_counts": df[df.main_blocker != "none"]["main_blocker"].value_counts().to_dict(),
    "mcp_counts": df["mcp_status"].value_counts().to_dict(),
    "verdict_by_category": pd.crosstab(df["category"], df["verdict"]).to_dict("index"),
    "gated_rate_by_category": df.assign(g=df.access.isin(["paid_plan_required", "approval_required", "partner_gated", "no_public_api"]))
                               .groupby("category")["g"].mean().round(2).to_dict(),
    "oauth_and_apikey_both": int(df.auth_methods.apply(lambda a: "oauth2" in a and "api_key" in a).sum()),
    "easy_wins": df[df.verdict == "ready"]["app"].tolist(),
    "needs_outreach": df[df.verdict == "blocked"]["app"].tolist(),
    "needs_human": df[df.needs_human]["app"].tolist(),
}
pathlib.Path("out/patterns.json").write_text(json.dumps(pat, indent=2), encoding="utf-8")
df.drop(columns=["evidence"]).assign(auth_methods=df.auth_methods.apply(";".join)).to_csv("out/final.csv", index=False, encoding="utf-8")
print(json.dumps({k: pat[k] for k in ("auth_share", "access_counts", "verdict_counts", "blocker_counts", "mcp_counts")}, indent=2))
