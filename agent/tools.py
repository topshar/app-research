"""Search + fetch layer, run through Composio's Tavily toolkit using the free "Instant" account
(no Tavily key needed). Plain HTTP is only a backup for page fetching.

Env overrides (optional): TOOL_SEARCH_SLUG, TOOL_FETCH_SLUG, TOOL_CONNECTED_ACCOUNT ('instant_account' by default;
set to an 'ca_...' id to use your own Tavily connection instead).
"""
import json, os, re, html
import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; api-research-agent)"}
SEARCH_SLUG = os.getenv("TOOL_SEARCH_SLUG", "TAVILY_SEARCH")
FETCH_SLUG = os.getenv("TOOL_FETCH_SLUG", "TAVILY_EXTRACT")
ACCOUNT = os.getenv("TOOL_CONNECTED_ACCOUNT", "")  # empty = Composio picks the account connected for USER_ID
USER_ID = os.getenv("COMPOSIO_USER_ID", "research-agent")

_composio = None
stats = {"composio_ok": 0, "composio_fail": 0, "fallback_used": 0, "last_error": ""}


def _client():
    global _composio
    if _composio is None and os.getenv("COMPOSIO_API_KEY"):
        from composio import Composio
        _composio = Composio()
    return _composio


def _run(slug, arguments):
    c = _client()
    if not c:
        raise RuntimeError("no COMPOSIO_API_KEY")
    kw = {"connected_account_id": ACCOUNT} if ACCOUNT else {}
    r = c.tools.execute(slug=slug, arguments=arguments, user_id=USER_ID,
                        dangerously_skip_version_check=True, **kw)
    if isinstance(r, dict) and r.get("successful") is False:
        raise RuntimeError(str(r.get("error"))[:300])
    return r.get("data", r) if isinstance(r, dict) else r


def urls_in(obj) -> list[str]:
    seen, out = set(), []
    for u in re.findall(r"https?://[^\s\"'<>\\)\]]+", json.dumps(obj, default=str)):
        u = u.rstrip(".,;")
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def _results(data):
    """Find the list of result dicts wherever Composio nests it."""
    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            return data["results"]
        for v in data.values():
            r = _results(v)
            if r:
                return r
    return []


def web_search(query: str) -> dict:
    """Returns {'text': str, 'urls': [..], 'via': 'composio'|'fallback'}."""
    try:
        data = _run(SEARCH_SLUG, {"query": query, "max_results": 6, "search_depth": "basic"})
        stats["composio_ok"] += 1
        res = _results(data)
        if res:
            text = "\n".join(f"- {r.get('title','')} | {r.get('url','')}\n  {str(r.get('content',''))[:500]}" for r in res)
            urls = [r.get("url") for r in res if r.get("url")]
        else:
            text, urls = json.dumps(data, default=str)[:5000], urls_in(data)
        return {"text": text, "urls": urls, "via": "composio"}
    except Exception as e:
        stats["composio_fail"] += 1; stats["fallback_used"] += 1; stats["last_error"] = str(e)[:300]
        return {"text": "", "urls": [], "via": "failed"}


def fetch_page(url: str, limit: int = 12000) -> str:
    try:
        data = _run(FETCH_SLUG, {"urls": [url]})
        stats["composio_ok"] += 1
        res = _results(data)
        txt = "\n".join(str(r.get("raw_content") or r.get("content") or "") for r in res) if res \
            else (data if isinstance(data, str) else json.dumps(data, default=str))
        if len(txt) > 200:
            return txt[:limit]
    except Exception as e:
        stats["composio_fail"] += 1; stats["last_error"] = str(e)[:300]
    stats["fallback_used"] += 1
    try:
        r = requests.get(url, headers=UA, timeout=20)
        t = re.sub(r"(?s)<(script|style).*?</\1>", " ", r.text)
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        return re.sub(r"\s+", " ", t)[:limit]
    except Exception:
        return ""
