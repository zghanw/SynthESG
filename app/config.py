"""
SynthESG — Application configuration.

All settings are loaded from environment variables (or a .env file).
Only TAVILY_API_KEY is required to run the full application locally.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Tavily (required for AI research) ---
    # Get a free key at https://tavily.com — 1,000 credits/month
    TAVILY_API_KEY: str = ""

    # --- AWS (only needed for production CDK deployment) ---
    AWS_REGION: str = "ap-southeast-5"
    S3_REPORTS_BUCKET: str = ""


settings = Settings()
