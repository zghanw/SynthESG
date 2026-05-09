"""
Tavily Research Service — real-time ESG data collection.

Uses the Tavily Search API to gather current ESG information
about companies from the web. Also detects sector and HQ country
from a dedicated company profile query for accuracy.
"""

import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from app.config import settings

logger = logging.getLogger(__name__)

_TAVILY_URL = "https://api.tavily.com/search"
_REQUEST_TIMEOUT = 15
_RATE_LIMIT_DELAY = 1.0

# Query 0 is a dedicated profile query — used ONLY for sector/country detection.
# Queries 1–3 are ESG-focused — used for scoring and insights.
_RESEARCH_QUERIES = [
    "{company} company industry sector business type headquarters country founded",
    "{company} ESG sustainability environmental impact climate 2024 2025",
    "{company} social responsibility diversity workforce community",
    "{company} corporate governance board transparency ethics compliance",
]

_CATEGORY_LABELS = ["company_profile", "environmental", "social", "governance"]


# ---------------------------------------------------------------------------
# Sector classification
# ---------------------------------------------------------------------------

# Each entry: (Sector label, [high-specificity phrases/terms])
# Rules:
#   • Use PHRASES not single words wherever possible to avoid false matches.
#   • More specific sectors come first — first match wins after regex pass.
#   • Single words only where they are truly sector-unique.
_SECTOR_MAP = [
    ("Food & Beverage",      ["restaurant", "food and beverage", "food company", "food manufacturer",
                               "grocery", "supermarket", "beverage company", "fast food", "dining",
                               "food retail", "confectionery", "packaged food", "dairy", "bakery",
                               "snack", "qsr", "food processing", "food production"]),
    ("Retail & Malls",       ["shopping mall", "shopping centre", "shopping center", "retail mall",
                               "department store", "retail chain", "retail store", "fashion retail",
                               "luxury retail", "specialty retail", "retail group", "retailer"]),
    ("Technology",           ["software company", "technology company", "tech company", "saas",
                               "semiconductor", "cloud computing", "artificial intelligence company",
                               "cybersecurity", "data center", "it services", "semiconductor company",
                               "hardware company", "fabless", "internet company", "platform company",
                               "machine learning", "enterprise software"]),
    ("Automotive",           ["automotive", "automobile", "automaker", "car manufacturer",
                               "electric vehicle company", "ev company", "auto parts", "motor company",
                               "vehicle manufacturer", "autonomous vehicle", "self-driving"]),
    ("Financial Services",   ["bank", "banking", "financial services", "insurance company",
                               "asset management", "investment firm", "fintech", "brokerage",
                               "wealth management", "payment company", "credit card", "lender",
                               "private equity", "venture capital"]),
    ("Healthcare",           ["healthcare company", "pharmaceutical", "pharma company", "biotech",
                               "medical device", "hospital", "health system", "diagnostics company",
                               "life sciences", "drug company", "therapeutics", "genomics",
                               "medical technology", "healthtech"]),
    ("Real Estate",          ["real estate", "property developer", "reit", "property company",
                               "real estate investment trust", "commercial real estate",
                               "residential developer", "construction company", "proptech",
                               "property management"]),
    ("Telecommunications",   ["telecom company", "telecommunications", "wireless carrier",
                               "mobile operator", "internet service provider", "broadband provider",
                               "5g", "fiber network", "satellite communications", "mobile network"]),
    ("Energy",               ["oil company", "gas company", "petroleum", "fossil fuel",
                               "oil and gas", "energy company", "refinery", "upstream", "downstream",
                               "natural gas", "coal", "oil exploration", "offshore energy"]),
    ("Utilities",            ["utility company", "electric utility", "water utility",
                               "gas utility", "power utility", "electricity provider",
                               "energy provider", "power generation", "transmission network",
                               "distribution network"]),
    ("Consumer Goods",       ["consumer goods", "consumer products", "fmcg", "household products",
                               "personal care", "cosmetics company", "apparel company",
                               "fashion brand", "luxury brand", "sportswear"]),
    ("Media & Entertainment",["streaming company", "gaming company", "media company",
                               "entertainment company", "broadcasting", "film studio",
                               "music company", "television network", "social media company",
                               "esports", "content platform"]),
    ("Industrials",          ["manufacturing company", "industrial company", "logistics company",
                               "freight company", "aerospace company", "defense company",
                               "engineering company", "machinery", "heavy equipment",
                               "airline", "aviation company", "railroad"]),
    ("Materials & Mining",   ["mining company", "chemicals company", "steel company",
                               "materials company", "packaging company", "mining and minerals",
                               "precious metals", "rare earth", "aluminum", "copper mining",
                               "lithium mining"]),
    ("E-commerce",           ["e-commerce company", "ecommerce", "online marketplace",
                               "online retail", "digital commerce", "online shopping platform",
                               "direct-to-consumer"]),
]


# ---------------------------------------------------------------------------
# Country classification
# ---------------------------------------------------------------------------

# Each entry: (Country, [specific phrases/terms])
_COUNTRY_MAP = [
    ("United States",  ["united states", "u.s.-based", "american company", "cupertino",
                        "seattle", "silicon valley", "wall street", "nasdaq-listed",
                        "nyse-listed", "s&p 500", "new york", "california", "delaware"]),
    ("Malaysia",       ["malaysia", "malaysian company", "kuala lumpur", "bursa malaysia",
                        "klse", "klci", "penang", "selangor", "klang valley",
                        "petronas", "maybank", "cimb", "securities commission malaysia"]),
    ("China",          ["china", "chinese company", "beijing", "shanghai", "shenzhen",
                        "hong kong", "hkex", "guangzhou", "hang seng", "csi 300"]),
    ("Japan",          ["japan", "japanese company", "tokyo", "osaka", "nikkei", "tse",
                        "kyoto", "softbank", "honda", "toyota", "sony"]),
    ("South Korea",    ["south korea", "south korean company", "seoul", "kospi", "kosdaq",
                        "samsung", "hyundai", "lg group", "sk hynix", "chaebol"]),
    ("United Kingdom", ["united kingdom", "uk company", "british company", "london",
                        "ftse 100", "lse-listed", "cambridge", "oxford", "england"]),
    ("Singapore",      ["singapore", "sgx-listed", "singapore company", "mas-regulated",
                        "temasek", "grab", "sea limited", "changi"]),
    ("India",          ["india", "indian company", "mumbai", "bangalore", "new delhi",
                        "nse-listed", "bse-listed", "sensex", "nifty", "tata group",
                        "reliance industries", "hyderabad", "infosys"]),
    ("Germany",        ["germany", "german company", "berlin", "munich", "frankfurt",
                        "dax", "sap", "volkswagen", "siemens", "bmw"]),
    ("France",         ["france", "french company", "paris", "cac 40", "lvmh",
                        "totalenergies", "euronext paris"]),
    ("Taiwan",         ["taiwan", "taiwanese company", "taipei", "tsmc", "foxconn",
                        "hsinchu", "mediatek", "twse"]),
    ("Canada",         ["canada", "canadian company", "toronto", "tsx-listed", "shopify",
                        "vancouver", "montreal"]),
    ("Australia",      ["australia", "australian company", "sydney", "melbourne",
                        "asx-listed", "bhp", "perth"]),
    ("Netherlands",    ["netherlands", "dutch company", "amsterdam", "asml", "unilever"]),
    ("Sweden",         ["sweden", "swedish company", "stockholm", "spotify", "ericsson"]),
    ("Switzerland",    ["switzerland", "swiss company", "zurich", "geneva",
                        "nestle", "roche", "novartis", "ubs"]),
    ("Brazil",         ["brazil", "brazilian company", "sao paulo", "b3",
                        "petrobras", "vale"]),
]


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

# Regex patterns that explicitly state a company's sector
_SECTOR_REGEX = re.compile(
    r"(?:is|operates as|classified as|one of the world'?s? (?:largest|leading))\s+"
    r"(?:a|an|the)?\s*(?:\w+\s+){0,3}(?:company|corporation|group|firm|provider|retailer|"
    r"manufacturer|operator|conglomerate|bank|insurer)",
    re.IGNORECASE,
)


def _detect_sector_from_text(text: str) -> str:
    """
    Match sector using phrase-based lookup against a corpus string.
    Returns the first sector whose phrases appear in the text.
    Falls back to 'General' if nothing matches.
    """
    lower = text.lower()
    scores: dict[str, int] = {label: 0 for label, _ in _SECTOR_MAP}

    for label, phrases in _SECTOR_MAP:
        for phrase in phrases:
            if phrase in lower:
                scores[label] += 1

    best_label = max(scores, key=scores.get)
    return best_label if scores[best_label] > 0 else "General"


def _detect_country_from_text(text: str) -> str:
    """
    Match country using phrase-based lookup against a corpus string.
    Returns 'Global' if nothing matches.
    """
    lower = text.lower()
    scores: dict[str, int] = {country: 0 for country, _ in _COUNTRY_MAP}

    for country, phrases in _COUNTRY_MAP:
        for phrase in phrases:
            if phrase in lower:
                scores[country] += 1

    best_country = max(scores, key=scores.get)
    return best_country if scores[best_country] > 0 else "Global"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def research_company(company_name: str, max_queries: int = 4) -> dict:
    """Perform multi-dimensional ESG research on a company using Tavily."""
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        logger.warning("TAVILY_API_KEY not set — returning empty research")
        return _empty_research(company_name, reason="API key not configured")

    results_by_category = {}
    queries_used = min(max_queries, len(_RESEARCH_QUERIES))

    for i in range(queries_used):
        query = _RESEARCH_QUERIES[i].format(company=company_name)
        category = _CATEGORY_LABELS[i]

        try:
            data = _execute_search(api_key, query)
            if data:
                results_by_category[category] = {
                    "answer": data.get("answer", ""),
                    "sources": data.get("results", [])[:3],
                    "query": query,
                }
            if i < queries_used - 1:
                time.sleep(_RATE_LIMIT_DELAY)
        except Exception as exc:
            logger.warning("Research query failed [%s]: %s", category, exc)
            continue

    return _synthesize(company_name, results_by_category)


def _execute_search(api_key: str, query: str) -> dict | None:
    """Execute a single Tavily search query."""
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": 3,
        "include_answer": True,
        "include_raw_content": False,
    }
    response = requests.post(
        _TAVILY_URL, json=payload,
        headers={"Content-Type": "application/json"},
        timeout=_REQUEST_TIMEOUT,
    )
    if response.status_code == 200:
        return response.json()
    logger.warning("Tavily returned %d: %s", response.status_code, response.text[:200])
    return None


def _synthesize(company_name: str, results: dict) -> dict:
    """Synthesize raw research results into structured ESG intelligence."""
    insights = []
    news_evidence = []

    # ── Sector & country detection ──────────────────────────────────────────
    # Use ONLY the company_profile query answer — it's a direct description
    # of what the company does, making keyword matching far more accurate.
    profile_data = results.get("company_profile", {})
    profile_corpus = " ".join([
        profile_data.get("answer", ""),
        *[s.get("title", "") + " " + s.get("content", "")[:150]
          for s in profile_data.get("sources", [])],
    ])

    # Fall back to full corpus only if profile query produced nothing
    if not profile_corpus.strip():
        profile_corpus = " ".join(
            data.get("answer", "") for data in results.values()
        )

    sector = _detect_sector_from_text(profile_corpus)
    country = _detect_country_from_text(profile_corpus)

    logger.info("Detected sector=%s country=%s for '%s'", sector, country, company_name)

    # ── ESG insights (skip company_profile — it's metadata, not ESG) ────────
    for category, data in results.items():
        if category == "company_profile":
            continue

        answer = data.get("answer", "")
        if answer:
            insights.append({
                "category": category.replace("_", " ").title(),
                "finding": answer[:400],
                "source_count": len(data.get("sources", [])),
            })

        for source in data.get("sources", []):
            url = source.get("url", "")
            try:
                domain = urlparse(url).netloc.replace("www.", "").split(".")[0].title()
            except Exception:
                domain = "Source"

            news_evidence.append({
                "title": source.get("title", "")[:120],
                "snippet": (source.get("content", "")[:250] + "...") if source.get("content") else "",
                "url": url,
                "source": domain,
                "category": category.replace("_", " ").title(),
                "relevance_score": max(1, min(10, int(source.get("score", 0.5) * 10))),
            })

    # Deduplicate by URL
    seen: set[str] = set()
    unique = []
    for item in news_evidence:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)
    unique.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {
        "insights": insights,
        "news_evidence": unique[:10],
        "risk_factors": [],
        "sector": sector,
        "country": country,
        "research_depth": len(results),
        "queries_used": len(results),
        "data_sources": list(results.keys()),
        "researched_at": datetime.now(timezone.utc).isoformat(),
    }


def _empty_research(company_name: str, reason: str = "") -> dict:
    return {
        "insights": [], "news_evidence": [], "risk_factors": [],
        "sector": "General", "country": "Global",
        "research_depth": 0, "queries_used": 0, "data_sources": [],
        "researched_at": datetime.now(timezone.utc).isoformat(),
        "note": reason,
    }
