"""Research one app: Composio gathers evidence (search + fetch), Gemini (free tier) only READS it
and fills the strict schema. Gemini never searches (free tier has no search grounding for Gemini 3+).
"""
import json, os, re, threading, time
from google import genai
from google.genai import types
from .schema import AppRecord
from . import tools
from .checks import check_official_sources, check_consistency

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
MIN_GAP = float(os.getenv("MIN_SECONDS_BETWEEN_CALLS", "5"))  # 12 per minute, under the 15 RPM free limit
_client = None
_lock, _last = threading.Lock(), [0.0]

SYSTEM = """You fill in a research record about one app's developer platform for a team that builds AI-agent toolkits.
You are given EVIDENCE: search results and page text. Rules:
- Use ONLY the evidence given. Never use memory for facts. If the evidence does not say it, answer 'unknown' and set needs_human=true.
- For auth, access and MCP claims, cite the vendor's OWN pages (its docs, site or GitHub org) whenever the evidence contains one. Third-party blogs may only support a claim with confidence 0.6 or lower, and then needs_human must be true.
- Never leave auth_methods empty: use ['none'] if no authentication is needed, or ['unknown'] if the evidence does not say.
- Do not list a feature (webhooks, sandbox, OAuth) unless an evidence item supports it; otherwise use null or leave it out.
- Every evidence item must use a URL that appears in the evidence and a snippet (under 25 words) copied word-for-word from it.
- 'access' = what a developer must do to get working credentials today without paying or talking to sales.
- verdict: ready = self-serve creds + documented API; ready_with_caveats = works but has a real gate (paid tier, app review, per-tenant creds);
  blocked = needs partnership, enterprise deal or approval a solo developer cannot get; not_an_api_product = no API (CLI, consumer app).
- mcp_status: official = published by the vendor; community = third party; none_found only if the evidence shows none.
Return ONE JSON object matching the schema. No prose."""


def _gemini():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _throttle():
    with _lock:
        wait = _last[0] + MIN_GAP - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()


FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite")
MAX_TRIES = int(os.getenv("LLM_MAX_TRIES", "7"))


def _call(prompt: str) -> str:
    model = MODEL
    for attempt in range(MAX_TRIES):
        _throttle()
        try:
            r = _gemini().models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.1,
                                                   response_mime_type="application/json"))
            return r.text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                if "PerDay" in msg or "per day" in msg.lower():
                    raise RuntimeError("DAILY_QUOTA_HIT: stop and resume tomorrow (results are cached)")
                time.sleep(20 * (attempt + 1)); continue
            if any(c in msg for c in ("503", "500", "UNAVAILABLE", "overloaded", "high demand", "DEADLINE")):
                if attempt == 2 and model != FALLBACK_MODEL:
                    model = FALLBACK_MODEL  # main model stays busy: use the other free lite model
                time.sleep(min(15 * (attempt + 1), 60)); continue
            if attempt >= 3:
                raise
            time.sleep(3)
    raise RuntimeError("Gemini still unavailable after 7 tries; rerun the command later")


def gather(app: str, hint: str) -> str:
    """Collect evidence text. Search 3 angles, fetch hint page + best doc URLs."""
    queries = [f"{app} official API documentation authentication OAuth API key",
               f"{app} official developer docs get API credentials pricing plan requirements",
               f"{app} official MCP server"]
    parts, urls = [], []
    for q in queries:
        s = tools.web_search(q)
        parts.append(f"## SEARCH: {q} (via {s['via']})\n{s['text']}")
        urls += s["urls"]
    first = hint.split()[0]
    cand = ([first if first.startswith("http") else "https://" + first] if "." in first else [])
    seen = set()
    for u in cand + urls:
        if u in seen or len(seen) >= 4:
            continue
        if any(b in u for b in ("youtube.com", "reddit.com", "linkedin.com/pulse")):
            continue
        seen.add(u)
        txt = tools.fetch_page(u)
        if len(txt) > 300:
            parts.append(f"## PAGE: {u}\n{txt}")
    return "\n\n".join(parts)[:60000]


def gather_cached(app: str, hint: str) -> str:
    import pathlib, re as _re
    d = pathlib.Path("out/evidence"); d.mkdir(parents=True, exist_ok=True)
    p = d / (_re.sub(r"[^a-z0-9]+", "-", app.lower()).strip("-") + ".txt")
    if p.exists():
        return p.read_text(encoding="utf-8")
    ev = gather(app, hint)
    if len(ev) > 500:
        p.write_text(ev, encoding="utf-8")
    return ev


def gather_verify(rec: dict) -> str:
    """Pass-2 evidence: NEW pages. Opens the vendor URLs the first pass cited (and its docs/MCP/OpenAPI links)
    plus two differently worded searches, so the verifier does not just re-read the same cache."""
    import pathlib, re as _re
    app = rec["app"]
    d = pathlib.Path("out/evidence2"); d.mkdir(parents=True, exist_ok=True)
    p = d / (_re.sub(r"[^a-z0-9]+", "-", app.lower()).strip("-") + ".txt")
    if p.exists():
        return p.read_text(encoding="utf-8")
    parts, urls = [], []
    cited = [e["url"] for e in rec.get("evidence", []) if e.get("url")]
    for k in ("docs_url", "openapi_spec_url", "mcp_url"):
        if rec.get(k):
            cited.append(rec[k])
    for q in (f"{app} developer documentation authentication get started API keys access",
              f"{app} API requirements plan pricing approval partner program MCP server"):
        s = tools.web_search(q)
        parts.append(f"## SEARCH: {q}\n{s['text']}")
        urls += s["urls"]
    seen = set()
    for u in cited + urls:
        if u in seen or len(seen) >= 6:
            continue
        if any(b in u for b in ("youtube.com", "reddit.com", "linkedin.com/pulse")):
            continue
        seen.add(u)
        txt = tools.fetch_page(u)
        if len(txt) > 300:
            parts.append(f"## PAGE: {u}\n{txt}")
    ev = "\n\n".join(parts)[:60000]
    if len(ev) > 500:
        p.write_text(ev, encoding="utf-8")
    return ev


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model output")
    return json.loads(m.group(0))


def research(app: str, category: str, hint: str, extra: str = "", verify_rec=None) -> AppRecord:
    evidence = gather_verify(verify_rec) if verify_rec else gather_cached(app, hint)
    schema = json.dumps(AppRecord.model_json_schema())
    prompt = (f"APP: {app}\nGIVEN CATEGORY: {category}\nHINT: {hint}\n{extra}\n\n"
              f"SCHEMA:\n{schema}\n\nEVIDENCE:\n{evidence}")
    last_err = None
    for _ in range(2):  # one retry if the JSON fails validation
        raw = _call(prompt if last_err is None else prompt + f"\n\nYour previous answer failed validation: {last_err}. Fix it.")
        try:
            rec = AppRecord.model_validate(_extract_json(raw))
            flags = check_official_sources(rec.model_dump()) + [f for f in check_consistency(rec.model_dump())
                                                                 if f not in ("low_confidence", "agent_asked_for_human")]
            if flags:  # enforce what the prompt asks for but the small model does not always do
                rec.needs_human = True
                rec.confidence = min(rec.confidence, 0.6)
                rec.agent_notes = (rec.agent_notes + " [auto-flagged: " + ", ".join(flags) + "]").strip()
            return rec
        except Exception as e:
            last_err = str(e)[:400]
    raise ValueError(f"validation failed twice: {last_err}")
