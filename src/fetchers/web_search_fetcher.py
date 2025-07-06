import os
import sys
import json
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
# Add project root to sys.path before any imports and debug the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
print(f"Adding to sys.path: {project_root}")  # Debug output
sys.path.append(project_root)

from src.utils.logger import setup_logger
from src.settings import settings

logger = setup_logger()
logger.info("Web Search fetcher logger initialized")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_websearch(query: str, project_name: str) -> list:
    """
    Fetch web search results from Google Custom Search API and save them to the project directory.

    Args:
        query (str): The search query.
        project_name (str): The name of the project to save the results under.

    Returns:
        list: A list of dictionaries containing metadata of the fetched web results.
    """

    # Log some info about the query
    logger.info(f"Starting web search for query: {query}")

    # Construct the URL for the Google Custom Search API
    url = "https://www.googleapis.com/customsearch/v1"

    # Set up the query parameters
    params = {
        "q": query,
        "key": settings.google_api_key,  # Use the API key from .env
        "cx": settings.google_cse_id,    # Use the CSE ID from .env
        "num": 10,  # Number of results to return (max 10 per request)
        "start": 1  # Starting index
    }

    try:
        # Check if the Google API key and CSE ID are configured
        if not settings.google_api_key or not settings.google_cse_id:
            logger.error("Google API key or CSE ID not configured in .env file")
            return []

        # Make the API request
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check if there are any results
        if "items" not in data or not data["items"]:
            logger.info(f"No results found for query: {query}")
            return []

        # Process the results
        results = []
        data_dir = os.path.join("data", project_name, "websearch")
        os.makedirs(data_dir, exist_ok=True)

        # Process each result
        for item in data["items"]:
            # Extract the information we need from the result
            result_info = {
                "title": item.get("title", "No title available"),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "No snippet available"),
                "displayLink": item.get("displayLink", ""),
                "published": item.get("pagemap", {}).get("metatags", [{}])[0].get("og:updated_time", str(datetime.now().isoformat()))
            }

            # Add the result to the list of results
            results.append(result_info)

            # Save the metadata to a JSON file per result
            result_id = item.get("link", "").replace("http://", "").replace("https://", "").replace("/", "_")
            metadata_path = os.path.join(data_dir, f"{result_id}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(result_info, f, indent=4, ensure_ascii=False)

        # Save all the metadata to a single file
        all_metadata_path = os.path.join(data_dir, "metadata.json")
        with open(all_metadata_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        # Log some info about the results
        logger.info(f"Fetched {len(results)} web results for query: {query}")
        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching web search results for query '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching web search results for query '{query}': {e}")
        return []

if __name__ == "__main__":
    test_query = "machine learning in psychology"
    test_project = "test_project2"
    fetch_websearch(test_query, test_project)