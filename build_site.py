"""Builds docs/index.html (single self-contained page) + docs/apps.json + docs/apps.csv from out/pass2 and out/accuracy.json."""
import json, glob, csv, collections as C, pathlib, html
apps = {int(r["id"]): r for r in csv.DictReader(open("data/apps.csv", encoding="utf-8"))}
R = {int(p[-8:-5]): json.load(open(p, encoding="utf-8")) for p in glob.glob("out/pass2/*.json")}
L = {l["id"]: l for l in json.load(open("out/pass2_log.json"))}
ACC = json.load(open("out/accuracy.json"))
gold = list(csv.DictReader(open("data/gold.csv", encoding="utf-8")))
FIELDS = ["auth_methods", "access", "api_type", "mcp_status", "verdict", "main_blocker"]

rows = []
for i in sorted(R):
    r = R[i]; hard = [x for x in L[i]["pass1_issues"] if not x.startswith("evidence_link_blocked")]
    rows.append({"id": i, "app": r["app"], "category": apps[i]["category_given"], "one_liner": r["one_liner"],
                 "auth": r["auth_methods"], "access": r["access"], "access_notes": r["access_notes"],
                 "api_type": r["api_type"], "breadth": r["api_breadth"], "mcp": r["mcp_status"], "mcp_url": r.get("mcp_url"),
                 "verdict": r["verdict"], "blocker": r["main_blocker"], "reason": r["verdict_reason"],
                 "docs": r.get("docs_url"), "evidence": [{"f": e["field"], "u": e["url"]} for e in r["evidence"]],
                 "conf": r["confidence"], "human": r["needs_human"], "flags": hard,
                 "verifier": "re-checked" if L[i].get("reresearched") else ("verifier failed (overload)" if L[i].get("error") else "not targeted")})
missing = [{"id": i, "app": apps[i]["app"], "category": apps[i]["category_given"]} for i in sorted(apps) if i not in R]

N = len(rows)
cnt = lambda k, v: sum(1 for r in rows if r[k] == v)
ready = cnt("verdict", "ready"); caveat = cnt("verdict", "ready_with_caveats")
paid = cnt("blocker", "paid_plan"); gated = cnt("blocker", "app_review") + cnt("blocker", "partner_program") + cnt("blocker", "enterprise_only")
official = cnt("mcp", "official"); oauth = sum(1 for r in rows if "oauth2" in r["auth"])
multi = sum(1 for r in rows if len(r["auth"]) >= 2)
flagged = sum(1 for r in rows if r["flags"])
targeted = sum(1 for l in L.values() if l.get("reresearched") or l.get("error"))
rechecked = sum(1 for l in L.values() if l.get("reresearched"))
failedv = sum(1 for l in L.values() if l.get("error"))
changed = sum(1 for l in L.values() if l.get("fields_changed"))
mcpdead = sum(1 for l in L.values() if any(x.startswith('mcp_url_dead') for x in l['pass1_issues']))
selfserve = cnt("access", "free_self_serve") + cnt("access", "trial_self_serve")

# gold scoring denominators
n = C.Counter(); 
for g in gold:
    if int(g["id"]) in R:
        for f in FIELDS:
            if g[f].strip(): n[f] += 1
gold_labelled = sum(1 for g in gold if any(g[f].strip() for f in FIELDS))
gold_scored = len({int(g["id"]) for g in gold if int(g["id"]) in R and any(g[f].strip() for f in FIELDS)})
human_conf = [g["app"] for g in gold if "HUMAN-CONFIRMED" in g["notes"]]
a1, a2 = ACC["pass1"]["accuracy"], ACC["pass2"]["accuracy"]
misses = ACC["pass2"]["misses"]

pct = lambda x: f"{round(100*x/N)}%"
def accrow(f, label):
    x, y = a1[f], a2[f]
    if x is None: return ""
    return f"<tr><td>{label}</td><td>{n[f]}</td><td>{round(x*100)}%</td><td>{round(y*100)}%</td></tr>"
acc_rows = "".join(accrow(f, l) for f, l in [("auth_methods", "Auth methods"), ("api_type", "API type"), ("access", "Access (self-serve vs gated)"),
                   ("mcp_status", "MCP status"), ("main_blocker", "Main blocker"), ("verdict", "Buildability verdict")])
miss_rows = "".join(f"<tr><td>{html.escape(m['app'])}</td><td>{m['field']}</td><td>{html.escape(', '.join(m['agent']) if isinstance(m['agent'], list) else str(m['agent']))}</td><td>{html.escape(m['human'].replace(';', ', '))}</td></tr>" for m in misses)
miss_rows_missing = "".join(f"<li><b>{html.escape(m['app'])}</b> <span class=muted>({html.escape(m['category'])})</span></li>" for m in missing)

DATA = json.dumps({"rows": rows, "missing": missing}, ensure_ascii=False).replace("</", "<\\/")

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Can an agent build on these 100 apps? Research on {N} of them</title>
<style>
:root{{--ink:#1d1b18;--mut:#6b655c;--bg:#faf8f4;--card:#fff;--line:#e5dfd4;--acc:#b4451f;--ok:#2f6b3f;--warn:#9a6a00;--bad:#a02a2a}}
*{{box-sizing:border-box}}body{{margin:0;font:16px/1.6 Georgia,'Times New Roman',serif;color:var(--ink);background:var(--bg)}}
.wrap{{max-width:1080px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:2rem;line-height:1.2;margin:.2em 0 .3em}}h2{{font-size:1.35rem;margin:2.2em 0 .5em;border-top:1px solid var(--line);padding-top:1em}}
h3{{font-size:1.05rem;margin:1.2em 0 .3em}}p{{margin:.5em 0}}.muted{{color:var(--mut)}}
.sans,table,button,select,input,.chip{{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}}
.lede{{font-size:1.1rem;color:#3a362f}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:16px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.big{{font:700 2.1rem/1 -apple-system,Segoe UI,Arial,sans-serif;color:var(--acc)}}
.note{{background:#fff6e5;border:1px solid #ecd9a8;border-radius:10px;padding:12px 16px;margin:16px 0}}
table{{border-collapse:collapse;width:100%;font-size:.88rem;background:var(--card)}}th,td{{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#f1ece1;position:sticky;top:0;cursor:pointer;white-space:nowrap}}tr.row{{cursor:pointer}}tr.row:hover{{background:#fbf7ee}}
.chip{{display:inline-block;padding:1px 8px;border-radius:99px;font-size:.78rem;border:1px solid var(--line);background:#f4f0e6;margin:1px 2px 1px 0;white-space:nowrap}}
.v-ready{{background:#e3f1e6;border-color:#bcd9c3;color:var(--ok)}}.v-ready_with_caveats{{background:#fff1d1;border-color:#ecd9a8;color:var(--warn)}}
.v-blocked,.v-not_an_api_product{{background:#f7dede;border-color:#e6bcbc;color:var(--bad)}}
.tools{{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}}select,input,button{{padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:.9rem}}
button{{cursor:pointer}}.scroll{{max-height:640px;overflow:auto;border:1px solid var(--line);border-radius:10px}}
.detail td{{background:#fcfaf5;font-size:.86rem}}code,pre{{font-family:Consolas,Menlo,monospace;font-size:.85rem}}pre{{background:#1f1d1a;color:#f1ece1;padding:12px 14px;border-radius:8px;overflow:auto}}
.cols{{columns:2;column-gap:30px}}.cols li{{break-inside:avoid}}@media(max-width:700px){{.cols{{columns:1}}h1{{font-size:1.6rem}}}}
a{{color:var(--acc)}}
</style></head><body><div class="wrap">

<p class="sans muted" style="margin:0">App research for Composio's AI Product Ops take-home</p>
<h1>Almost every app can be built on. The real blocker is a paid plan, not permission.</h1>
<p class="lede">This covers {N} of the 100 apps ({len(missing)} are listed under Coverage) across 10 categories: how you log in, whether a developer can get access on their own, what kind of API it has, whether an MCP server exists, and whether an integration can realistically be built. Everything below comes from one agent run plus a checking pass.</p>

<h2 style="border:0;margin-top:1.2em">What the data says</h2>
<div class="grid sans">
<div class="card"><div class="big">{ready+caveat} of {N}</div><b>can be built on</b><p class="muted">{ready} are ready as-is, {caveat} are ready with a caveat. Only {cnt('verdict','blocked')} was rated blocked and {cnt('verdict','not_an_api_product')} is not an API product at all (a command-line tool).</p></div>
<div class="card"><div class="big">{paid} vs {gated}</div><b>paid plan vs approval gate</b><p class="muted">When something stands in the way it is usually money: {paid} apps need a paid plan to get API access, while only {gated} sit behind an app review, partner program or enterprise deal.</p></div>
<div class="card"><div class="big">{pct(oauth)}</div><b>offer OAuth 2.0</b><p class="muted">{oauth} of {N}. {multi} apps list two or more login methods, so an integration layer has to handle several per app, not one.</p></div>
<div class="card"><div class="big">{official} of {N}</div><b>say they have an official MCP server</b><p class="muted">That is the agent's reading, and it is the field I trust least: {mcpdead} MCP links were flagged as unreachable and only 3 apps in my answer key had an MCP label to check against.</p></div>
</div>
<p><b>What that means for a tool-integration platform:</b> the hard part of covering these apps is not finding an API. It is the commercial gate in front of it. About {pct(paid)} of apps would need a customer to be on a paid plan, and {selfserve} of {N} let a developer start self-serve (free or trial). Planning the catalog around who can try it for free tells you more than planning around who has an API.</p>

<p class="muted sans"><b>Coverage:</b> {N} of 100 apps were researched in this run. The other {len(missing)} are listed under Coverage below.</p>

<h2>The matrix</h2>
<p class="muted">Click a row for the reasoning, the pages it relied on and the automatic check flags. Download the data for use by an agent: <a href="#" id="dl-json">JSON</a> or <a href="#" id="dl-csv">CSV</a> (also in the repo as <code>docs/apps.json</code> and <code>docs/apps.csv</code>).</p>
<div class="tools">
<input id="q" placeholder="Search app or text" size="22">
<select id="fc"><option value="">All categories</option></select>
<select id="fv"><option value="">Any verdict</option><option>ready</option><option>ready_with_caveats</option><option>blocked</option><option>not_an_api_product</option></select>
<select id="fa"><option value="">Any access</option></select>
<select id="fm"><option value="">Any MCP status</option><option>official</option><option>community</option><option>none_found</option></select>
<span class="muted sans" id="count"></span></div>
<div class="scroll"><table id="t"><thead><tr><th data-k="app">App</th><th data-k="category">Category</th><th>Auth</th><th data-k="access">Access</th><th data-k="api_type">API</th><th data-k="mcp">MCP</th><th data-k="verdict">Verdict</th><th data-k="blocker">Blocker</th><th data-k="conf">Confidence</th></tr></thead><tbody></tbody></table></div>

<h2>How the research agent works</h2>
<ol>
<li><b>Search and read.</b> For each app the agent runs three web searches (API auth docs, how to get credentials and plan limits, official MCP) and opens the best vendor pages. Search and page reading go through <b>Composio</b> (its Tavily tools, called from the Composio Python SDK with my own free Tavily key as a connected account).</li>
<li><b>Fill a fixed form.</b> Gemini (free tier) reads only that gathered text and fills a strict schema: auth methods, access, API type, MCP status, verdict, blocker, plus the URL and snippet behind each claim. It is told never to guess and to lower its confidence when evidence is thin.</li>
<li><b>Check the work with plain code.</b> Rules check that the answer agrees with itself, that cited links are alive, that quoted snippets really appear on the page, that an official-sounding claim comes from the vendor's own domain, and that MCP and OpenAPI links respond. {flagged} of {N} records tripped at least one check; "no vendor source for this field" was the most common ({sum(1 for r in rows for f in r['flags'] if f.startswith('no_official_source'))} times).</li>
<li><b>Second look.</b> Flagged records (plus a random 15%) go to a verifier pass that re-reads fresh vendor pages and the pass-one answer. This is the step that mostly failed to run, see below.</li>
</ol>
<h3>Where a human was needed</h3>
<ul>
<li>Getting a working search tool: Composio's own search toolkit was retired (calls returned 410/404), and Composio Instant would have billed the organisation's balance, so a person had to create a free Tavily account and connect its key.</li>
<li>Reading some vendor pages the tools cannot render (JavaScript-only docs for Ramp, Gumroad and others).</li>
<li>Building the answer key and spot-checking it (next section).</li>
<li>Deciding when to stop: the free model was overloaded for hours, so a person called time on retries.</li>
</ul>

<h2>How accurate is it? First pass vs final pass</h2>
<div class="note sans"><b>How the answer key was made.</b> The key is mostly AI-labelled from vendor docs, with a person confirming a subset. We picked {len(gold)} apps spread across the categories. An independent AI check labelled them from vendor documentation (without looking at the agent's answers); {gold_labelled} apps ended up with at least one label and {len(gold)-gold_labelled} could not be read. A person then reviewed {len(human_conf)} rows against the vendor pages and corrected or confirmed them ({', '.join(human_conf)}). The other rows are unreviewed by a human. {gold_scored} of those labelled apps were also researched by the agent, so they are what the scores below use.</div>
<table class="sans"><thead><tr><th>Field</th><th>Apps scored</th><th>First pass</th><th>After checking</th></tr></thead><tbody>{acc_rows}
<tr><td><b>All fields together</b></td><td></td><td><b>{round(a1['overall']*100)}%</b></td><td><b>{round(a2['overall']*100)}%</b></td></tr></tbody></table>
<p><b>Hits.</b> The agent is reliable on what kind of API an app has ({round(a2['api_type']*100)}% across {n['api_type']} apps) and no verdict disagreed with the key, but only one verdict had a label, so that says little.</p>
<p><b>Misses.</b> Login methods are where it goes wrong: only {round(a2['auth_methods']*100)}% of the {n['auth_methods']} scored apps matched exactly. Most misses are the agent listing an extra method (for example both API key and OAuth where the docs describe one). It also got access and blocker wrong for Copper, Aircall and LinkedIn Ads, where the vendor docs are vague and the key had to rely on a person's judgement.</p>
<p><b>First pass vs final pass.</b> The score moved from {round(a1['overall']*100)}% to {round(a2['overall']*100)}%. That gap comes from one changed record (Notion's login methods), so it is not a measured improvement: the verifier completed {rechecked} of its {targeted} planned re-checks, and the other {failedv} kept their first-pass answers after the free model returned overload errors. Access, MCP, blocker and verdict were scored on 3, 3, 3 and 1 apps, which is too few to read anything into.</p>
<details><summary class="sans">All {len(misses)} remaining misses after checking</summary>
<table class="sans"><thead><tr><th>App</th><th>Field</th><th>Agent said</th><th>Answer key says</th></tr></thead><tbody>{miss_rows}</tbody></table></details>

<h2>Coverage: apps not yet researched ({len(missing)})</h2>
<p>These did not complete in this run because the free Gemini model returned overload errors. They are unrated, not blocked.</p>
<ul class="cols">{miss_rows_missing}</ul>

<h2>Run it yourself</h2>
<pre>git clone &lt;repo-url&gt; &amp;&amp; cd app-research
pip install -r requirements.txt
# put GEMINI_API_KEY, COMPOSIO_API_KEY (and your Tavily connection) in .env
python -m agent.pass1          # research every app in data/apps.csv, one JSON per app in out/pass1
python -m agent.pass2          # checks + verifier on flagged records, out/pass2
python -m agent.evaluate pass1 pass2   # score against data/gold.csv
python build_site.py           # rebuild this page</pre>
<p class="muted">Rerunning pass1 only retries apps that failed, so it is safe to stop and resume.</p>

<h2>Scope and next steps</h2>
<ul>
<li>This run covers {N} of 100 apps; the rest are a rerun away (the pipeline resumes and only retries what is missing).</li>
<li>The answer key is small and mostly AI-labelled; {len(human_conf)} rows were confirmed by a person. Growing the human-checked share is the next accuracy step.</li>
<li>The MCP field is the agent's reading and was checked on very few apps.</li>
<li>The verifier needs a rerun on the {failedv} records it could not reach. A paid model or an off-peak run would remove the overload problem.</li>
</ul>
</div>
<script>
const D={DATA};
const rows=D.rows;
const $=s=>document.querySelector(s);
const cats=[...new Set(rows.map(r=>r.category))].sort();
cats.forEach(c=>$("#fc").insertAdjacentHTML("beforeend",`<option>${{c}}</option>`));
[...new Set(rows.map(r=>r.access))].sort().forEach(c=>$("#fa").insertAdjacentHTML("beforeend",`<option>${{c}}</option>`));
let sk="app",sd=1;
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
function draw(){{
 const q=$("#q").value.toLowerCase(),fc=$("#fc").value,fv=$("#fv").value,fa=$("#fa").value,fm=$("#fm").value;
 let rs=rows.filter(r=>(!fc||r.category==fc)&&(!fv||r.verdict==fv)&&(!fa||r.access==fa)&&(!fm||r.mcp==fm)&&(!q||(r.app+r.one_liner+r.reason+r.access_notes).toLowerCase().includes(q)));
 rs.sort((a,b)=>(a[sk]>b[sk]?1:a[sk]<b[sk]?-1:0)*sd);
 $("#count").textContent=rs.length+" of "+rows.length+" apps";
 $("#t tbody").innerHTML=rs.map(r=>`<tr class="row" data-id="${{r.id}}"><td><b>${{esc(r.app)}}</b></td><td>${{esc(r.category)}}</td><td>${{r.auth.map(a=>`<span class=chip>${{esc(a)}}</span>`).join("")}}</td><td>${{esc(r.access)}}</td><td>${{esc(r.api_type)}}</td><td>${{esc(r.mcp)}}</td><td><span class="chip v-${{r.verdict}}">${{esc(r.verdict)}}</span></td><td>${{esc(r.blocker)}}</td><td>${{Math.round(r.conf*100)}}%${{r.human?" &#9873;":""}}</td></tr>`).join("");
}}
document.querySelector("#t tbody").addEventListener("click",e=>{{
 const tr=e.target.closest("tr.row");if(!tr)return;
 const nx=tr.nextElementSibling;if(nx&&nx.classList.contains("detail")){{nx.remove();return;}}
 const r=rows.find(x=>x.id==tr.dataset.id);
 const ev=r.evidence.map(x=>`<li><span class=chip>${{esc(x.f)}}</span> <a href="${{esc(x.u)}}" target="_blank" rel="noopener">${{esc(x.u)}}</a></li>`).join("");
 tr.insertAdjacentHTML("afterend",`<tr class="detail"><td colspan="9"><p><b>${{esc(r.one_liner)}}</b></p><p><b>Verdict reason:</b> ${{esc(r.reason)}}</p><p><b>Access:</b> ${{esc(r.access_notes)}}</p><p><b>Docs:</b> ${{r.docs?`<a href="${{esc(r.docs)}}" target="_blank" rel="noopener">${{esc(r.docs)}}</a>`:"none found"}} &nbsp; <b>MCP:</b> ${{r.mcp_url?`<a href="${{esc(r.mcp_url)}}" target="_blank" rel="noopener">${{esc(r.mcp_url)}}</a>`:"no link"}}</p><p><b>Check flags:</b> ${{r.flags.length?esc(r.flags.join(", ")):"none"}} &nbsp; <b>Verifier:</b> ${{esc(r.verifier)}}</p><ul>${{ev}}</ul></td></tr>`);
}});
document.querySelectorAll("th[data-k]").forEach(th=>th.addEventListener("click",()=>{{const k=th.dataset.k;sd=(sk==k)?-sd:1;sk=k;draw();}}));
["#q","#fc","#fv","#fa","#fm"].forEach(s=>$(s).addEventListener("input",draw));
function dl(name,text,type){{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([text],{{type}}));a.download=name;a.click();}}
$("#dl-json").onclick=e=>{{e.preventDefault();dl("apps.json",JSON.stringify(rows,null,1),"application/json");}};
$("#dl-csv").onclick=e=>{{e.preventDefault();const h=["app","category","auth","access","api_type","mcp","verdict","blocker","confidence","docs","mcp_url","reason"];
 const q=v=>'"'+String(v??"").replace(/"/g,'""')+'"';
 dl("apps.csv",[h.join(",")].concat(rows.map(r=>[r.app,r.category,r.auth.join(";"),r.access,r.api_type,r.mcp,r.verdict,r.blocker,r.conf,r.docs,r.mcp_url,r.reason].map(q).join(","))).join("\\n"),"text/csv");}};
draw();
</script></body></html>"""
page = page.replace("\u2014", "-")
pathlib.Path("docs/index.html").write_text(page, encoding="utf-8")
rows = json.loads(json.dumps(rows, ensure_ascii=False).replace("\u2014", "-"))
json.dump(rows, open("docs/apps.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
with open("docs/apps.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["app", "category", "auth", "access", "api_type", "mcp", "verdict", "blocker", "confidence", "docs", "mcp_url", "reason"])
    for r in rows: w.writerow([r["app"], r["category"], ";".join(r["auth"]), r["access"], r["api_type"], r["mcp"], r["verdict"], r["blocker"], r["conf"], r["docs"], r["mcp_url"], r["reason"]])
print("ok", N, len(missing), len(misses))
