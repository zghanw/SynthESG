"""Logo fetching utility — migrated from shared/logo_utils.py."""

import logging
import requests

logger = logging.getLogger(__name__)
_TIMEOUT = 5


def get_company_logo(company_name: str) -> str:
    """Try multiple free logo APIs, fall back to SVG initial."""
    domain = _guess_domain(company_name)
    if domain:
        for url in [
            f"https://logo.clearbit.com/{domain}",
            f"https://www.google.com/s2/favicons?domain={domain}&sz=128",
        ]:
            try:
                r = requests.head(url, timeout=_TIMEOUT, allow_redirects=True)
                if r.status_code == 200:
                    return url
            except Exception:
                continue
    return _fallback_svg(company_name)


def _guess_domain(name: str) -> str:
    mapping = {
        "apple": "apple.com", "microsoft": "microsoft.com", "google": "google.com",
        "tesla": "tesla.com", "amazon": "amazon.com", "meta": "meta.com",
        "nvidia": "nvidia.com", "samsung": "samsung.com", "maybank": "maybank.com",
        "netflix": "netflix.com", "toyota": "toyota.com",
    }
    return mapping.get(name.lower().split()[0], f"{name.lower().replace(' ', '')}.com")


def _fallback_svg(name: str) -> str:
    initial = (name or "?")[0].upper()
    svg = (
        f'<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="64" height="64" fill="#1a251f" rx="8"/>'
        f'<text x="32" y="32" font-family="Inter,Arial" font-size="22" '
        f'font-weight="600" fill="#4ade80" text-anchor="middle" dy=".35em">'
        f'{initial}</text></svg>'
    )
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
