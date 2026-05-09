"""
ESG Scoring Engine — sector benchmarks + research adjustments.

Migrated from shared/scoring.py with identical logic.
"""

import hashlib
import logging

logger = logging.getLogger(__name__)

_SECTOR_PROFILES: dict[str, dict[str, int]] = {
    "Technology": {"environmental": 21, "social": 22, "governance": 20, "innovation": 24},
    "Automotive": {"environmental": 23, "social": 19, "governance": 18, "innovation": 22},
    "E-commerce": {"environmental": 19, "social": 21, "governance": 21, "innovation": 23},
    "Financial Services": {"environmental": 18, "social": 21, "governance": 24, "innovation": 19},
    "Consumer Goods": {"environmental": 20, "social": 23, "governance": 19, "innovation": 18},
    "Utilities": {"environmental": 22, "social": 18, "governance": 21, "innovation": 17},
    "General": {"environmental": 19, "social": 20, "governance": 20, "innovation": 19},
}
_DEFAULT = {"environmental": 19, "social": 20, "governance": 20, "innovation": 19}
MAX_PILLAR = 25


def _adjust(name: str, pillar: str, base: int) -> int:
    seed = hashlib.sha256(f"{name}:{pillar}".encode()).hexdigest()
    adj = (int(seed[:4], 16) % 5) - 2
    return max(10, min(MAX_PILLAR, base + adj))


def _apply_research(scores: dict, research: dict) -> dict:
    adj = dict(scores)
    for insight in research.get("insights", []):
        cat = insight.get("category", "").lower()
        for pillar in ("environmental", "social", "governance", "innovation"):
            if pillar in cat or "esg" in cat:
                adj[pillar] = min(MAX_PILLAR, adj[pillar] + 1)
    for risk in research.get("risk_factors", []):
        penalty = {"High": 3, "Medium": 2, "Low": 1}.get(risk.get("severity", "Low"), 1)
        adj["governance"] = max(10, adj["governance"] - penalty)
    if len(research.get("news_evidence", [])) >= 6:
        for p in adj:
            adj[p] = min(MAX_PILLAR, adj[p] + 1)
    return adj


def calculate_esg_scores(company_name: str, sector: str, research: dict | None = None) -> dict:
    profile = _SECTOR_PROFILES.get(sector, _DEFAULT)
    scores = {p: _adjust(company_name, p, b) for p, b in profile.items()}

    research_applied = False
    if research and research.get("research_depth", 0) > 0:
        scores = _apply_research(scores, research)
        research_applied = True

    total = sum(scores.values())
    if total >= 90: rating = "Outstanding"
    elif total >= 80: rating = "Excellent"
    elif total >= 70: rating = "Good"
    elif total >= 60: rating = "Fair"
    else: rating = "Needs Improvement"

    return {
        **scores, "total": total, "rating": rating,
        "methodology": {
            "framework": "Sector-Weighted ESG Scoring v2.0",
            "scoring_basis": "Sector benchmarks with real-time research adjustments",
            "research_applied": research_applied,
            "max_pillar_score": MAX_PILLAR,
            "max_total_score": MAX_PILLAR * 4,
        },
    }
