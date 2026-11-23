"""Deterministic checks: no LLM involved. Each returns a list of issue strings."""
import re, requests

UA = {"User-Agent": "Mozilla/5.0 (research-verifier)"}


def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=UA, timeout=timeout, allow_redirects=True)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def check_evidence(rec: dict) -> list[str]:
    """Dead links + snippet really appears on the cited page (fuzzy: 60% of words present in order-free match)."""
    issues = []
    seen = {}
    for ev in rec.get("evidence", []):
        u = ev["url"]
        if u not in seen:
            seen[u] = fetch(u)
        code, body = seen[u]
        if code == 0 or code >= 400:
            # 403/429 are usually bot walls, flag softly
            issues.append(f"evidence_link_{'blocked' if code in (403, 429) else 'dead'}:{u}:{code}")
            continue
        words = [w for w in re.findall(r"[a-z0-9]+", norm(ev["snippet"])) if len(w) > 3]
        if words:
            page = norm(body)
            hit = sum(w in page for w in words) / len(words)
            if hit < 0.6:
                issues.append(f"snippet_not_on_page:{ev['field']}:{u}:{hit:.2f}")
    return issues


def check_openapi(rec: dict) -> list[str]:
    u = rec.get("openapi_spec_url")
    if not u:
        return []
    code, body = fetch(u)
    ok = code == 200 and re.search(r'"?(openapi|swagger)"?\s*[:=]', body[:2000])
    return [] if ok else [f"openapi_url_not_a_spec:{u}:{code}"]


def check_consistency(rec: dict) -> list[str]:
    """Internal contradictions the model tends to make."""
    i = []
    v, b, acc = rec["verdict"], rec["main_blocker"], rec["access"]
    if v == "ready" and b != "none": i.append("ready_but_has_blocker")
    if v == "blocked" and b == "none": i.append("blocked_without_blocker")
    if acc in ("partner_gated", "no_public_api") and v == "ready": i.append("gated_but_ready")
    if rec["api_type"] in ("none", "sdk_or_cli_only") and v == "ready": i.append("no_api_but_ready")
    if rec["mcp_status"] != "none_found" and rec["mcp_status"] != "unknown" and not rec.get("mcp_url"):
        i.append("mcp_claimed_without_url")
    if not rec["auth_methods"]: i.append("no_auth_listed")
    if rec["confidence"] < 0.6: i.append("low_confidence")
    if rec["needs_human"]: i.append("agent_asked_for_human")
    return i


def check_mcp(rec: dict) -> list[str]:
    u = rec.get("mcp_url")
    if not u:
        return []
    code, _ = fetch(u)
    return [] if 0 < code < 400 or code in (403, 429) else [f"mcp_url_dead:{u}:{code}"]


def _is_vendor_url(u: str, token: str) -> bool:
    """Vendor-owned if the DOMAIN contains the vendor name; for github.com, the org/repo path counts."""
    from urllib.parse import urlparse
    p = urlparse(u)
    host = re.sub(r"[^a-z0-9.]", "", p.netloc.lower())
    if "github.com" in host:
        return token in re.sub(r"[^a-z0-9]", "", p.path.lower())
    return token in host


def check_official_sources(rec: dict) -> list[str]:
    """Key claims must cite at least one URL that belongs to the vendor (name appears in the URL)."""
    token = re.sub(r"[^a-z0-9]", "", rec["app"].lower().split()[0])
    issues = []
    for prefix in ("auth", "access", "mcp"):
        urls = [e["url"].lower() for e in rec.get("evidence", []) if e["field"].lower().startswith(prefix)]
        if not urls:
            issues.append(f"no_evidence_for:{prefix}")
        elif not any(_is_vendor_url(u, token) for u in urls):
            issues.append(f"no_official_source:{prefix}")
    return issues


def run_all(rec: dict) -> list[str]:
    return check_consistency(rec) + check_official_sources(rec) + check_evidence(rec) + check_openapi(rec) + check_mcp(rec)
