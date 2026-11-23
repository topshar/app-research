"""Phase 1 sanity check. Run: python -m agent.probe
Checks Gemini, then Composio Tavily (Instant account) search + extract, printing real errors.
"""
import os, traceback
from dotenv import load_dotenv
load_dotenv()


def gemini():
    print("== Gemini ==")
    from google import genai
    c = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    r = c.models.generate_content(model=model, contents="Reply with the single word: ok")
    print(f"  {model} says:", r.text.strip())


def composio():
    print("== Composio (Tavily via Instant) ==")
    from . import tools
    print("  slugs:", tools.SEARCH_SLUG, "|", tools.FETCH_SLUG, "| account:", tools.ACCOUNT)
    try:
        out = tools._run(tools.SEARCH_SLUG, {"query": "Slack API authentication OAuth", "max_results": 3})
        res = tools._results(out)
        print("  SEARCH OK, results:", len(res))
        for r in res[:3]:
            print("   -", r.get("url"))
        if not res:
            print("  raw:", str(out)[:300])
    except Exception as e:
        print("  SEARCH FAILED:", type(e).__name__, str(e)[:500])
    try:
        out = tools._run(tools.FETCH_SLUG, {"urls": ["https://api.slack.com/authentication"]})
        res = tools._results(out)
        n = len(str((res[0] if res else out).get("raw_content", "") if res else out))
        print("  EXTRACT OK, chars:", n)
    except Exception as e:
        print("  EXTRACT FAILED:", type(e).__name__, str(e)[:500])
    print("  via helper:", tools.web_search("Pylon support API authentication")["via"], tools.stats)


if __name__ == "__main__":
    for fn in (gemini, composio):
        try:
            fn()
        except Exception:
            print("  FAILED:"); traceback.print_exc(limit=2)
