from pydantic import BaseSettings
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Keys
    unpaywall_key: str = os.getenv("UNPAYWALL_KEY", "")
    semantics_key: str = os.getenv("SEMANTICS_KEY", "")
    # Add other API keys as needed

    # Proxy Settings
    proxy: str = os.getenv("PROXY", "https://")

    # PubMed Settings
    pubmed_email: str = os.getenv("PUBMED_EMAIL", "")

    # Other Settings
    # Add any other configuration settings here

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate the settings object
settings = Settings()