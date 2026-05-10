# SynthESG: AI-Powered ESG Intelligence Platform

> Real-time Environmental, Social & Governance intelligence powered by AI web research.
> Enter any company name and SynthESG crawls the live web, benchmarks findings against sector averages, and returns a structured ESG scorecard with source evidence.

---

## Tech Stack

![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![AWS](https://img.shields.io/badge/AWS_CDK-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)
![S3](https://img.shields.io/badge/AWS_S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white)
![CloudFront](https://img.shields.io/badge/CloudFront-8C4FFF?style=for-the-badge&logo=amazonaws&logoColor=white)
![Tavily](https://img.shields.io/badge/Tavily_API-00B4D8?style=for-the-badge&logo=search&logoColor=white)
![jsPDF](https://img.shields.io/badge/jsPDF-FF0000?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)

---

## How It Works

```
User enters a company name
         ↓
POST /api/v1/analyze
         ↓
Tavily Query 1: Company profile → detect sector & HQ country
Tavily Query 2: ESG & environmental impact
Tavily Query 3: Social responsibility & workforce
Tavily Query 4: Governance & ethics
         ↓
Sector-benchmarked scoring algorithm
         ↓
Structured ESG scorecard + source evidence + PDF export
```

---

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI entry point + CORS
│   ├── config.py             # Pydantic Settings — loads from .env
│   ├── api/
│   │   ├── router.py         # Route aggregation
│   │   └── analysis.py       # POST /analyze — core endpoint
│   └── services/
│       ├── research.py       # Tavily web crawling + sector/country detection
│       ├── scoring.py        # Sector-benchmarked ESG scoring algorithm
│       └── logo.py           # Company logo resolution
├── infrastructure/
│   └── esg_stack.py          # CDK stack: S3 + CloudFront
├── frontend/
│   ├── index.html            # Main UI
│   ├── styles.css            # Dark-mode design system
│   └── script.js             # API client, score rendering, PDF export
├── .env.example              # Configuration template
└── requirements.txt
```

---

## Features

- 🔍 **Real-time AI research**: 4 targeted Tavily queries per analysis (ESG, environmental, social, governance)
- 🏭 **Sector detection**: automatically classifies companies across 14 sectors using a dedicated profile query
- 🌍 **HQ country detection**: identifies headquarters across 18 countries from research text
- 📊 **Sector-benchmarked scoring**: scores are calibrated against sector-specific baselines, not generic averages
- 📄 **PDF export**: generates a clean, formatted A4 ESG report with branding, score summary, insights, and sources
- 🖥️ **Dark-mode SaaS UI**: animated score ring, pillar bars, source evidence cards

---

## Getting Started

### Prerequisites

- Python 3.12+
- A [Tavily API key](https://tavily.com) — free tier, 1,000 credits/month

### Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/zghanw/SynthESG.git
cd SynthESG

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Open .env and set your TAVILY_API_KEY

# 5. Start the API server
uvicorn app.main:app --reload --port 8000
```

Then open `frontend/index.html` in your browser, or visit **http://localhost:8000/docs** for the interactive Swagger UI.

### Deploy to AWS

```bash
npm install -g aws-cdk
cdk bootstrap --region ap-southeast-5
cdk deploy SynthESGStack
```

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/analyze` | Analyze a company's ESG performance |

### Example

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Microsoft"}'
```

**Response:**

```json
{
  "company_name": "Microsoft",
  "company_logo": "https://logo.clearbit.com/microsoft.com",
  "sector": "Technology",
  "country": "United States",
  "esg_score": 84,
  "rating": "Excellent",
  "environmental": 22,
  "social": 21,
  "governance": 22,
  "innovation": 19,
  "research_insights": [...],
  "news_evidence": [...],
  "research_meta": {
    "queries_used": 4,
    "researched_at": "2025-01-01T00:00:00Z"
  }
}
```

---

## Scoring Methodology

Each company is evaluated across four pillars, each scored out of 25:

| Pillar | What It Measures |
|--------|----------------|
| **Environmental** | Carbon emissions, renewable energy adoption, climate initiatives |
| **Social** | Workforce diversity, employee wellbeing, community engagement |
| **Governance** | Board independence, executive accountability, ethics & compliance |
| **Innovation** | ESG-driven R&D, green technology investment, sustainability roadmap |

Scores are seeded by **sector-specific benchmarks** (14 sectors) and adjusted up or down based on real-time research findings. Maximum total score: **100**.

---

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `TAVILY_API_KEY` | ✅ | Your Tavily API key — get one free at [tavily.com](https://tavily.com) |
| `AWS_REGION` | Production only | AWS region for CDK deployment |
| `S3_REPORTS_BUCKET` | Production only | S3 bucket name for exported reports |

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Originally built for the [Great Malaysia AI Hackathon 2025](https://greataihackathon.com/) as a Year 1 Diploma in ICT(Software Engineering) student with my friends (Team Hello World!). It has since evolved into a personal full-stack portfolio project.*