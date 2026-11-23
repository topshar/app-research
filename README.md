# App research agent

Researches SaaS apps for "can an agent build an integration on this?": login methods, self-serve vs gated access, API type, MCP server status, a buildability verdict with the blocker, and the URLs behind each claim.

Live page: see the GitHub Pages link in the repo description. Data for agents: `docs/apps.json`, `docs/apps.csv`.

## How it works
1. `agent/tools.py` searches and reads pages through **Composio** (Tavily tools, called with the Composio Python SDK; your own free Tavily key is stored as a Composio connected account).
2. `agent/llm.py` sends only that gathered text to Gemini (free tier) and gets back strict JSON, validated against `agent/schema.py`.
3. `agent/checks.py` runs plain-code checks: self-consistency, vendor-domain source check, snippet-is-on-the-page, dead links, MCP/OpenAPI reachability.
4. `agent/pass2.py` re-researches flagged records (plus a random 15%) with fresh vendor pages.
5. `agent/evaluate.py` scores each pass against `data/gold.csv`. The answer key is mostly AI-labelled from vendor docs, with a few rows confirmed by a person (see the page).

## Run it
```
pip install -r requirements.txt
cp .env.example .env     # fill GEMINI_API_KEY, COMPOSIO_API_KEY, TAVILY_API_KEY
python -m agent.connect_tavily        # one time: connect Tavily to Composio
python -m agent.pass1                 # one JSON per app in out/pass1 (safe to stop and rerun)
python -m agent.pass2                 # checks + verifier, out/pass2
python -m agent.evaluate pass1 pass2  # accuracy vs data/gold.csv
python build_site.py                  # rebuild docs/index.html
```
Set `LLM_MAX_TRIES=1` to fail fast when Gemini is overloaded; rerunning resumes where it stopped.

## Things worth knowing
- Composio's own Search toolkit was retired (calls returned 410/404), so search goes through the Tavily toolkit instead.
- Composio Instant bills the org balance, so it was not enabled; a self-created Tavily connection is used.
- This run covered 65 of 100 apps. The rest failed on Gemini "high demand" errors from the free tier.
