"""
SynthESG — FastAPI application entry point.

AI-powered ESG intelligence platform. Accepts a company name,
crawls the web via Tavily, and returns sector-benchmarked ESG
scores with source evidence.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SynthESG API starting...")
    yield
    logger.info("SynthESG API shutting down.")


app = FastAPI(
    title="SynthESG",
    description=(
        "AI-powered ESG intelligence platform. "
        "Enter a company name to get real-time Environmental, Social, "
        "and Governance scores backed by live web research."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    return {
        "app": "SynthESG",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "analyze": "POST /api/v1/analyze",
    }
