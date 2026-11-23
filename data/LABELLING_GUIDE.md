# Hand-labelling guide

You are the answer key. For each of the 30 apps below, open the real developer docs and fill one row in
`data/gold_template.csv`. Save the finished file as `data/gold.csv`.

**Label blind:** do not open anything in `out/` until all 30 rows are done. Use the vendor's own pages
(its docs, site or GitHub), not blog posts. If the docs do not say, write `unknown` and put a note. Never guess.

Spend about 3 to 4 minutes per app. If one takes longer than 8, write `unknown`, add a note, and move on.

## The 6 columns and their allowed values (copy exactly, lowercase)

### auth_methods  (one or more, separated by `;`, for example `oauth2;api_key`)
| value | use when the docs say |
|---|---|
| oauth2 | OAuth 2.0 / authorize + token URLs |
| api_key | "API key" (a key you copy from a dashboard) |
| bearer_token | "Bearer token", "access token", "personal access token" sent in an Authorization header |
| basic | HTTP Basic auth (username + password, or key as username) |
| jwt | you sign a JWT yourself to authenticate |
| hmac_signature | you sign each request with a secret (HMAC) |
| session_or_cookie | login session or cookie |
| none | no authentication needed |
| other | something else, explain in notes |
| unknown | the docs do not say |

List every method the docs offer for the public API. If a product offers OAuth for apps and also personal tokens, list both.

### access  (pick one: what a developer must do to get working credentials today, alone, without paying or talking to sales)
| value | meaning |
|---|---|
| free_self_serve | sign up free, get credentials yourself |
| trial_self_serve | needs a free trial or a card on file, but no human approval |
| paid_plan_required | the API is only on a paid plan, no free route |
| approval_required | app review, verification or admin approval before it works |
| partner_gated | partnership, "contact sales" or enterprise-only |
| no_public_api | there is no public API |
| unknown | docs do not say |

### api_type  (pick one)
rest, graphql, soap, websocket, mixed (several of these), sdk_or_cli_only (only a library or command line), none, unknown

### mcp_status  (pick one)
| value | meaning |
|---|---|
| official | the vendor itself publishes an MCP server (its own docs or its own GitHub org says so) |
| community | only a third party built one |
| none_found | you searched the vendor docs and its GitHub and found none |
| unknown | you could not tell |

Search "<app> MCP server" and check the vendor's docs. Directory sites (for example mcp listings) do not count as official.

### verdict  (pick one: could this become an agent toolkit today?)
| value | meaning |
|---|---|
| ready | self-serve credentials and a documented API |
| ready_with_caveats | works, but with a real gate (paid tier, app review, per-customer credentials) |
| blocked | needs a partnership, enterprise deal or approval a solo developer cannot get |
| not_an_api_product | no API at all (for example a command-line tool or consumer app) |

### main_blocker  (pick one; use `none` if verdict is ready)
none, paid_plan, app_review, partner_program, enterprise_only, no_public_api, per_tenant_credentials, complex_auth, sparse_docs, cli_not_api, other

## Columns in the file
`id, app, auth_methods, access, api_type, mcp_status, verdict, main_blocker, notes`

In `notes`, paste the URL of the page you used. One URL is enough. Add a few words if something was unclear.

## Your 30 apps
| id | app | where to start |
|---|---|---|
| 8 | Close | close.com |
| 9 | Copper | copper.com |
| 10 | DealCloud | api.docs.dealcloud.com |
| 14 | Front | front.com |
| 18 | Help Scout | helpscout.com |
| 19 | Gorgias | gorgias.com |
| 23 | Zoho Cliq | zoho.com/cliq |
| 28 | WhatsApp Business | developers.facebook.com/docs/whatsapp |
| 29 | Aircall | aircall.io |
| 32 | Meta Ads | developers.facebook.com/docs/marketing-apis |
| 33 | LinkedIn Ads | learn.microsoft.com/linkedin/marketing |
| 40 | SendGrid | sendgrid.com |
| 43 | BigCommerce | developer.bigcommerce.com |
| 45 | Magento (Adobe Commerce) | developer.adobe.com/commerce |
| 48 | Gumroad | gumroad.com/api |
| 51 | DataForSEO | docs.dataforseo.com |
| 52 | SE Ranking | seranking.com/api |
| 59 | Waterfall.io | waterfall.io (contact/company intel) |
| 67 | Snowflake | docs.snowflake.com |
| 68 | MongoDB Atlas | mongodb.com/docs/atlas/api |
| 70 | Sentry | docs.sentry.io/api |
| 71 | Notion | developers.notion.com |
| 73 | Linear | developers.linear.app |
| 80 | Harvest | harvestapp.com (help.getharvest.com/api-v2) |
| 81 | Stripe | stripe.com/docs/api |
| 82 | Plaid | plaid.com/docs |
| 89 | Ramp | docs.ramp.com |
| 91 | NotebookLM | cloud.google.com/gemini (Enterprise API) |
| 94 | Consensus | consensus.app (OAuth requested) |
| 99 | YouTube Transcript | transcriptapi.com |
