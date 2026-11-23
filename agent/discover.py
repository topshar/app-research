"""Find Composio search/fetch toolkits we can actually use for free.
Run: python -m agent.discover
Prints, per candidate toolkit: whether it needs no auth, whether Composio manages the auth, auth modes, and tool slugs.
"""
from dotenv import load_dotenv
load_dotenv()
from composio import Composio

CANDIDATES = ["tavily", "tavily_mcp", "exa", "firecrawl", "brave_search", "serpapi", "anakin_io", "beatapi",
              "agenty", "apify", "crawl4ai", "openweb_ninja", "jina_ai", "browserless", "scrapingbee",
              "hackernews", "duckduckgo", "perplexityai", "serper", "linkup", "parallel", "you_com"]


def main():
    c = Composio()
    for slug in CANDIDATES:
        try:
            tk = c.toolkits.get(slug)
            d = tk.model_dump() if hasattr(tk, "model_dump") else dict(tk)
        except Exception as e:
            print(f"{slug:16s} not available ({type(e).__name__})")
            continue
        modes = [a.get("mode") for a in (d.get("auth_config_details") or [])]
        managed = d.get("composio_managed_auth_schemes")
        print(f"{slug:16s} no_auth={d.get('no_auth')} managed={managed} modes={modes}")
        try:
            raw = c.tools.get_raw_composio_tools(toolkits=[slug], limit=8)
            print("   tools:", [getattr(t, "slug", str(t)) for t in raw])
        except Exception as e:
            print("   tools list failed:", str(e)[:100])


if __name__ == "__main__":
    main()
