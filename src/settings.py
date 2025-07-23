"""
Manages application-wide settings and configuration.

This module uses Pydantic's BaseSettings to load configuration values from
environment variables and a .env file. It centralizes all API keys, proxy
settings, and other configurable parameters for easy access throughout the
application.
"""

import os
import sys
# Add project root to sys.path before any imports and debug the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print(f"Adding to sys.path: {project_root}")  # Debug output
sys.path.append(project_root)

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from src.utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Load environment variables from .env file
env_path = os.path.join(project_root, ".env")
if not os.path.exists(env_path):
    logger.error(f"No .env file found at {env_path}")
else:
    logger.info(f"Loading .env file from {env_path}")
    load_dotenv(env_path)

class Settings(BaseSettings):
    """
    Defines and loads the application settings from environment variables.

    This class maps environment variables to typed fields, providing validation
    and a centralized point of access for all configuration parameters.

    Attributes:
        unpaywall_key (str): API key for Unpaywall.
        semantics_key (str): API key for Semantics.
        semantic_scholar_key (str): API key for Semantic Scholar.
        google_api_key (str): API key for Google services.
        google_cse_id (str): ID for Google Custom Search Engine.
        openai_api_key (str): API key for OpenAI services.
        google_cse_key_path (str): Path to Google service account key file.
        proxy (str): General proxy URL.
        proxy_http (str): HTTP-specific proxy URL.
        proxy_https (str): HTTPS-specific proxy URL.
        pubmed_email (str): Email address for PubMed API requests.
        ncbi_api_key (str): API key for NCBI services (for PubMed rate limits).
    """
    # API Keys
    unpaywall_key: str = os.getenv("UNPAYWALL_KEY", "")
    semantics_key: str = os.getenv("SEMANTICS_KEY", "")
    semantic_scholar_key: str = os.getenv("SEMANTIC_SCHOLAR_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_cse_id: str = os.getenv("GOOGLE_CSE_ID", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Google Service Account (optional, kept for flexibility)
    google_cse_key_path: str = os.getenv("GOOGLE_CSE_KEY_PATH", "")

    # Proxy Settings
    proxy: str = os.getenv("PROXY", "https://")
    proxy_http: str = os.getenv("PROXY_HTTP", "")
    proxy_https: str = os.getenv("PROXY_HTTPS", "")

    # PubMed Settings
    pubmed_email: str = os.getenv("PUBMED_EMAIL", "")

    # NCBI API Key (optional, for PubMed rate limits)
    ncbi_api_key: str = os.getenv("NCBI_API_KEY", "")

    class Config:
        env_file = env_path  # Use the defined env_path
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"Loaded settings - GOOGLE_API_KEY: {self.google_api_key}, GOOGLE_CSE_ID: {self.google_cse_id}")

# Instantiate the settings object
settings = Settings()