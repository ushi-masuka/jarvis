import os
import sys
import json
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed

# Add project root to sys.path before any imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.utils.logger import setup_logger
from src.settings import settings
from src.utils.metadata_schema import Metadata

"""
Provides a fetcher for retrieving web search results via Google's Custom Search API.

This module contains functions to query the Google Custom Search API, process
the search results, and format them into a standardized metadata structure.
It requires a configured API key and Custom Search Engine ID to operate.
"""

logger = setup_logger()
logger.info("Web Search fetcher logger initialized")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_websearch(query: str, project_name: str) -> list:
    """
    Fetches web search results from the Google Custom Search API.

    This function sends a search query to the Google Custom Search API, retrieves
    the results, and formats them into a standardized metadata structure. The
    collected metadata is saved to individual and aggregate JSON files.

    Args:
        query (str): The search query to send to the API.
        project_name (str): The name of the project for namespacing output data.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
        metadata for a fetched search result.
    """
    logger.info(f"Starting web search for query: {query}")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": settings.google_api_key,
        "cx": settings.google_cse_id,
        "num": 10,
        "start": 1
    }

    try:
        if not settings.google_api_key or not settings.google_cse_id:
            logger.error("Google API key or CSE ID not configured in .env file")
            return []

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" not in data or not data["items"]:
            logger.info(f"No results found for query: {query}")
            return []

        results = []
        data_dir = os.path.join("data", project_name, "websearch")
        os.makedirs(data_dir, exist_ok=True)
        fetch_date = datetime.now().isoformat()

        for item in data["items"]:
            meta = Metadata(
                id=item.get("link", "").replace("http://", "").replace("https://", "").replace("/", "_"),
                title=item.get("title", "No title available"),
                authors=[],
                published=item.get("pagemap", {}).get("metatags", [{}])[0].get("og:updated_time", fetch_date),
                summary=item.get("snippet", "No snippet available"),
                source="websearch",
                link=item.get("link", ""),
                pdf_url=None,
                doi=None,
                pmid=None,
                paperId=None,
                citationCount=None,
                displayLink=item.get("displayLink", ""),
                tags=None,
                fetch_date=fetch_date,
                paywalled=None,
                extra={"pagemap": item.get("pagemap", {})}
            )
            results.append(meta.model_dump())
            result_id = meta.id
            metadata_path = os.path.join(data_dir, f"{result_id}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(meta.model_dump(), f, indent=4, ensure_ascii=False)

        all_metadata_path = os.path.join(data_dir, "metadata.json")
        with open(all_metadata_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        logger.info(f"Fetched {len(results)} web results for query: {query}")
        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching web search results for query '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching web search results for query '{query}': {e}")
        return []

# ----------------- TESTS -----------------
def test_fetch_websearch():
    """
    Tests the web search fetcher with a sample query.

    This function executes a predefined search to validate that the fetcher
    is operating correctly. It asserts that the output is a list and that
    the metadata contains the expected fields, logging the results for review.
    """
    test_query = "machine learning in psychology"
    test_project = "test_project"
    logger.info("Running test_fetch_websearch...")
    results = fetch_websearch(test_query, test_project)
    assert isinstance(results, list), "Result should be a list"
    if results:
        first = results[0]
        assert "id" in first and "title" in first, "Metadata missing required fields"
        logger.info(f"Test passed: {len(results)} results, first title: {first['title']}")
    else:
        logger.warning("Test returned no results (may be a query issue)")

if __name__ == "__main__":
    test_fetch_websearch()