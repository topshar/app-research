"""One-time: store your Tavily API key inside Composio so the agent can call Tavily through Composio.
Needs in .env:  COMPOSIO_API_KEY, TAVILY_API_KEY, COMPOSIO_TAVILY_AUTH_CONFIG_ID (ac_...)
Run: python -m agent.connect_tavily
"""
import os
from dotenv import load_dotenv
load_dotenv()
from composio import Composio
from composio.types import auth_scheme
from . import tools


def main():
    c = Composio()
    auth_config_id = os.environ["COMPOSIO_TAVILY_AUTH_CONFIG_ID"]
    key = os.environ["TAVILY_API_KEY"]

    # find the exact field name Composio expects for the key (varies per toolkit)
    names = []
    try:
        d = c.toolkits.get("tavily").model_dump()
        for a in d.get("auth_config_details") or []:
            if a.get("mode") == "API_KEY":
                req = ((a.get("fields") or {}).get("connected_account_initiation") or {}).get("required") or []
                names = [f.get("name") for f in req]
    except Exception as e:
        print("could not read field names:", str(e)[:150])
    field = names[0] if names else "api_key"
    print("using field name:", field, "| user id:", tools.USER_ID)

    conn = c.connected_accounts.initiate(
        user_id=tools.USER_ID,
        auth_config_id=auth_config_id,
        config=auth_scheme.api_key({field: key}),
    )
    print("connected account id:", conn.id)
    try:
        print("status:", getattr(conn, "status", "unknown"))
    except Exception:
        pass


if __name__ == "__main__":
    main()
