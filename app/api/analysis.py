"""
AI-powered ESG analysis endpoint.

Flow:
  POST /api/v1/analyze
    → Crawl the web via Tavily (real-time ESG data)
    → Detect sector and HQ country from research text
    → Score via sector-benchmarked algorithm
    → Return structured ESG scorecard + source evidence
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.research import research_company
from app.services.scoring import calculate_esg_scores
from app.services.logo import get_company_logo

router = APIRouter()


class AnalyzeRequest(BaseModel):
    company_name: str = Field(
        ..., min_length=2, max_length=200, examples=["Apple"]
    )


@router.post("/")
def analyze_company(payload: AnalyzeRequest):
    """
    Analyze a company's ESG performance using real-time web research.

    1. Crawls the web via Tavily for ESG-related data
    2. Detects sector and HQ country from research text
    3. Generates sector-benchmarked E, S, G, and Innovation scores
    4. Returns insights, source evidence, and research metadata
    """
    company_name = payload.company_name.strip()

    if not company_name:
        raise HTTPException(status_code=400, detail="Company name cannot be empty")

    # Step 1: Research + metadata extraction
    research = research_company(company_name, max_queries=4)

    # Step 2: Use detected sector for more accurate benchmarking
    detected_sector = research.get("sector", "General")
    detected_country = research.get("country", "Global")

    # Step 3: Score with real sector context
    esg = calculate_esg_scores(
        company_name=company_name,
        sector=detected_sector,
        research=research,
    )

    # Step 4: Fetch company logo
    logo_url = get_company_logo(company_name)

    return {
        "company_name": company_name,
        "company_logo": logo_url,
        "sector": detected_sector,
        "country": detected_country,
        "esg_score": esg["total"],
        "rating": esg["rating"],
        "environmental": esg["environmental"],
        "social": esg["social"],
        "governance": esg["governance"],
        "innovation": esg["innovation"],
        "methodology": esg["methodology"],
        "research_insights": research.get("insights", []),
        "news_evidence": research.get("news_evidence", []),
        "risk_factors": research.get("risk_factors", []),
        "research_meta": {
            "queries_used": research.get("queries_used", 0),
            "data_sources": research.get("data_sources", []),
            "researched_at": research.get("researched_at", ""),
        },
    }
