"""Strict schema for one app's research record. Every claim carries evidence."""
from typing import Literal, Optional
from pydantic import BaseModel, Field

Auth = Literal["oauth2", "api_key", "basic", "bearer_token", "jwt", "hmac_signature",
               "session_or_cookie", "none", "other", "unknown"]
Access = Literal["free_self_serve",      # sign up, get creds, no payment
                 "trial_self_serve",     # needs trial / card on file but no human approval
                 "paid_plan_required",   # API only on paid tier
                 "approval_required",    # app review / admin approval / verification
                 "partner_gated",        # partnership, contact sales, enterprise only
                 "no_public_api",        # nothing documented
                 "unknown"]
ApiType = Literal["rest", "graphql", "soap", "sdk_or_cli_only", "websocket", "mixed", "none", "unknown"]
Breadth = Literal["narrow", "medium", "broad", "unknown"]  # <20 / 20-150 / >150 operations
McpStatus = Literal["official", "community", "none_found", "unknown"]
Verdict = Literal["ready", "ready_with_caveats", "blocked", "not_an_api_product"]
Blocker = Literal["none", "paid_plan", "app_review", "partner_program", "enterprise_only",
                  "no_public_api", "per_tenant_credentials", "complex_auth", "sparse_docs",
                  "cli_not_api", "other"]


class Evidence(BaseModel):
    field: str = Field(description="Which field this supports, e.g. auth, access, api, mcp, verdict")
    url: str
    snippet: str = Field(description="Short verbatim excerpt (<25 words) that supports the claim")


class AppRecord(BaseModel):
    app: str
    category: str
    one_liner: str
    auth_methods: list[Auth]
    access: Access
    access_notes: str = Field(description="What exactly gates credentials, in one sentence")
    api_type: ApiType
    api_breadth: Breadth
    openapi_spec_url: Optional[str] = None
    webhooks: Optional[bool] = None
    sandbox_or_test_env: Optional[bool] = None
    mcp_status: McpStatus
    mcp_url: Optional[str] = None
    verdict: Verdict
    main_blocker: Blocker
    verdict_reason: str
    docs_url: str
    evidence: list[Evidence]
    confidence: float = Field(ge=0, le=1)
    needs_human: bool = Field(description="True if docs were missing/contradictory and a human should look")
    agent_notes: str = ""
