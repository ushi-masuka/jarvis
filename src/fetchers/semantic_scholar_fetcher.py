import os
import sys
import json
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.logger import setup_logger

logger = setup_logger()
logger.info("Semantic Scholar fetcher logger initialized")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_semantic_scholar(query: str, project_name: str) -> list:
    """
    Fetch papers from Semantic Scholar based on the query and save them to the project directory.

    Args:
        query (str): The search query.
        project_name (str): The name of the project to save the papers under.

    Returns:
        list: A list of dictionaries containing metadata of the fetched papers.
    """
    logger.info(f"Starting fetch for query: {query}")

    # Construct the API request URL and parameters.
    url = "http://api.semanticscholar.org/graph/v1/paper/search/bulk"
    params = {
        # The search query to use.
        "query": query,
        # The number of results to request.
        "limit": 20,
        # The fields to include in the response.
        "fields": "title,authors,abstract,year,citationCount,paperId"
    }

    try:
        # Make the request and get the response.
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # If there are no results, log a message and return an empty list.
        if not data.get("data") or not data["data"]:
            logger.info(f"No results found for query: {query}")
            return []

        # Create a list to store the metadata for the fetched papers.
        papers = []

        # Create the directory for storing the metadata files if it doesn't exist.
        data_dir = os.path.join("data", project_name, "semanticscholar")
        os.makedirs(data_dir, exist_ok=True)

        # Iterate over the results and extract the metadata.
        for paper in data["data"]:
            # Extract the title, authors, abstract, year, citation count, and paper ID.
            paper_info = {
                # The title of the paper, or "No title available" if not present.
                "title": paper.get("title", "No title available"),
                # The authors of the paper, or a list containing "Unknown Author" if not present.
                "authors": [author.get("name", "Unknown Author") for author in paper.get("authors", [])] or ["Unknown Author"],
                # The year the paper was published, or the current year if not present.
                "published": str(paper.get("year", datetime.now().year)),
                # The abstract of the paper, or "No abstract available" if not present.
                "summary": paper.get("abstract", "No abstract available"),
                # The paper ID, or an empty string if not present.
                "paperId": paper.get("paperId", ""),
                # The citation count of the paper, or 0 if not present.
                "citationCount": paper.get("citationCount", 0)
            }

            # Add the paper's metadata to the list.
            papers.append(paper_info)

            # Save the metadata to a JSON file per paper.
            metadata_path = os.path.join(data_dir, f"{paper_info['paperId']}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(paper_info, f, indent=4, ensure_ascii=False)

        # Save all metadata to a single file.
        all_metadata_path = os.path.join(data_dir, "metadata.json")
        with open(all_metadata_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=4, ensure_ascii=False)

        # Log a message indicating how many papers were fetched.
        logger.info(f"Fetched {len(papers)} papers from Semantic Scholar for query: {query}")
        return papers

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from Semantic Scholar for query '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching from Semantic Scholar for query '{query}': {e}")
        return []

if __name__ == "__main__":
    test_query = "machine learning in psychology"
    test_project = "test_project"
    fetch_semantic_scholar(test_query, test_project)