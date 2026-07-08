# 📚 SynthESG: Comprehensive Reading Guide & Technical Walkthrough

Welcome to the **SynthESG** reading guide! This document is designed as a top-down educational roadmap for software engineering students and developers who want to understand the architecture, tech stack, and logic flow of the SynthESG platform. 

This project is an excellent example of a **modern, stateless AI micro-application** built with Python (FastAPI) and vanilla JavaScript, deployed using Infrastructure as Code (AWS CDK).

---

## 🏗️ 1. High-Level Architecture (The "Bird's-Eye View")

Before diving into the code, you must understand how data flows through the application. SynthESG is entirely **stateless**—it does not use a database. Instead, it relies on real-time web crawling (via the Tavily API) to synthesize data on the fly.

**The End-to-End Flow:**
1. **Frontend (Client):** User enters a company name in the UI and clicks "Analyze".
2. **API (Backend):** FastAPI receives the request and validates it.
3. **Research Service:** The backend makes 4 parallel API calls to Tavily to crawl the web for the company's profile, environmental, social, and governance (ESG) data.
4. **Analysis & Scoring:** 
   - The system detects the company's industry sector and headquarters country by analyzing the text corpus returned by Tavily.
   - It calculates a sector-benchmarked ESG score and adjusts it based on positive/negative findings in the research.
5. **Response:** The structured data (scores, insights, news evidence) is sent back to the frontend.
6. **UI Rendering & PDF:** The frontend dynamically renders rings, charts, and cards, and allows the user to download a formatted PDF report (via `jsPDF`).

---

## 🛠️ 2. The Tech Stack & Key Concepts to Learn

### **Backend: FastAPI + Pydantic (Python)**
- **Why this stack?** FastAPI is asynchronous, blazing fast, and automatically generates API documentation (Swagger/OpenAPI).
- **Key Concept:** **Pydantic Validation.** Notice how requests are strongly typed. If a user sends a bad request, Pydantic catches it before it ever hits the business logic.

### **Frontend: Vanilla HTML/CSS/JS**
- **Why this stack?** To keep the project lightweight and dependency-free. No React/Vue overhead.
- **Key Concept:** **DOM Manipulation & State Management.** The `script.js` file manually updates the UI based on the API response, demonstrating core JavaScript skills.
- **Key Concept:** **Client-Side PDF Generation.** `jsPDF` is used to generate a highly formatted, branded report entirely in the browser, saving server compute costs.

### **Infrastructure: AWS CDK (Python)**
- **Why this stack?** Infrastructure as Code (IaC). You define your cloud resources in Python, and CDK provisions them via CloudFormation.
- **Key Concept:** **Static Site Hosting.** The frontend is pushed to an S3 bucket and served globally via CloudFront (a Content Delivery Network).

---

## 🗺️ 3. Step-by-Step Codebase Walkthrough

Follow this path to read the codebase logically from top to bottom.

### Step 1: The Entry Point (`app/main.py`)
Start here. This is where the FastAPI server is initialized.
- **What to notice:**
  - The `lifespan` context manager handles startup/shutdown logs securely.
  - The `CORSMiddleware` handles Cross-Origin Resource Sharing, allowing the frontend to talk to the backend.
  - `app.include_router(api_router, prefix="/api/v1")` mounts the API routes. 

### Step 2: Request Routing & Validation (`app/api/router.py` & `app/api/analysis.py`)
Next, look at how the `POST /api/v1/analyze` endpoint is constructed.
- **What to notice:** 
  - `class AnalyzeRequest(BaseModel):` strictly enforces that the input is a valid string.
  - The `analyze_company()` function reads almost like plain English. It delegates heavy lifting to specific "Services":
    1. `research_company()`
    2. `calculate_esg_scores()`
    3. `get_company_logo()`

### Step 3: The AI Research Engine (`app/services/research.py`)
This is the "Brain" of the application. It talks to the Tavily AI search API.
- **What to notice:**
  - `_RESEARCH_QUERIES`: Notice how the prompts are explicitly engineered for the Tavily API to fetch profile, E, S, and G data separately.
  - **Text Classification Algorithms:** Look at `_detect_sector_from_text()` and `_detect_country_from_text()`. Instead of using a slow, expensive LLM, the code uses **heuristic phrase-based lookup**. It parses the text returned by Tavily and looks for specific phrases mapping to arrays in `_SECTOR_MAP` and `_COUNTRY_MAP`.

### Step 4: The Scoring Engine (`app/services/scoring.py`)
This file dictates how a company's final score out of 100 is computed.
- **What to notice:**
  - `_SECTOR_PROFILES`: Scoring isn't flat. A "Technology" company has a different baseline environmental score than an "Energy" company. 
  - `_apply_research()`: The script loops through the live research insights. If it finds "high risk factors", it penalizes the score. If it finds extensive news evidence, it boosts the score.

### Step 5: Frontend UI & Client (`frontend/index.html` & `frontend/styles.css`)
Move to the user interface.
- **What to notice in HTML:** Semantic tags are used. The `id` attributes are critical as they are the hooks the JS will use to inject data.
- **What to notice in CSS:** Modern CSS custom properties (variables) are defined at the `:root` level for easy dark-mode theming. Look at the `@keyframes` for smooth animations on the progress rings.

### Step 6: Frontend Logic & PDF Export (`frontend/script.js`)
This script bridges the gap between the user and the API.
- **What to notice:**
  - The `fetch()` API calls the backend endpoints asynchronously (`await`).
  - `renderPillar()` dynamically manipulates SVG stroke-dasharrays to create the animated circular progress bars.
  - `exportPDF()` uses `window.jspdf.jsPDF`. It manually paints text, rectangles, and lines onto a canvas to construct the downloadable report.

### Step 7: Cloud Infrastructure (`infrastructure/esg_stack.py`)
Finally, look at how the app goes live.
- **What to notice:** It provisions three main things using Python objects:
  1. `s3.Bucket`: For the frontend files.
  2. `cloudfront.Distribution`: To cache the site globally at edge locations.
  3. `s3.Bucket` (Private): For potential automated report exports.

---

## 🎓 4. Core Concepts & Takeaways for Your Portfolio

When discussing SynthESG in an interview or project showcase, emphasize these software engineering principles:

1. **Separation of Concerns (SoC):** 
   - The backend API (`app/api/`) does not perform web crawling. It delegates to the Services layer (`app/services/`). The frontend (`frontend/`) has no idea how scoring works; it simply renders JSON.
2. **Stateless Scalability:** 
   - Because there is no database locking or session state, you can spin up 1,000 instances of this FastAPI container simultaneously without them interfering with one another.
3. **Fail-Safe Processing:** 
   - In `research.py`, if one of the 4 Tavily queries times out or fails, the `try/except` block catches it and continues. The app degrades gracefully rather than crashing completely.
4. **Heuristic vs. Generative AI:** 
   - Using phrase-based mapping (Regex/Heuristics) for sector detection instead of sending prompts to OpenAI saves massive amounts of latency and API costs, demonstrating pragmatic engineering.

---

*Take your time exploring each file step-by-step. Reading code is one of the best ways to learn how to write robust, professional-grade software!*
