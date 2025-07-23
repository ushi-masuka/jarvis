import os
import sys
import json
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed

# Add project root to sys.path for CLI execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.utils.logger import setup_logger
from src.utils.metadata_schema import Metadata

logger = setup_logger()
logger.info("Semantic Scholar fetcher logger initialized")

"""
Provides a fetcher for retrieving academic papers from Semantic Scholar.

This module contains functions to query the Semantic Scholar Graph API,
fetch paper metadata, and save the results. It handles API requests,
error management, and data formatting.
"""

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_semantic_scholar(query: str, project_name: str) -> list:
    """
    Fetches paper metadata from the Semantic Scholar API based on a search query.

    This function sends a request to the Semantic Scholar Graph API, retrieves
    paper details, and formats the data into a standardized metadata structure.
    The collected metadata is then saved to a JSON file.

    Args:
        query (str): The search query.
        project_name (str): The name of the project to save the papers under.

    Returns:
        list: A list of dictionaries, where each dictionary represents the
        metadata for a fetched paper.
    """
    import requests

    logger.info(f"Starting fetch for query: {query}")

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": 10,
        "fields": "title,authors,abstract,year,citationCount,paperId,externalIds,url,isOpenAccess"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from Semantic Scholar for query '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching from Semantic Scholar for query '{query}': {e}")
        return []

    if not data.get("data"):
        logger.info(f"No results found for query: {query}")
        return []

    papers = []
    data_dir = os.path.join("data", project_name, "semanticscholar")
    os.makedirs(data_dir, exist_ok=True)
    fetch_date = datetime.now().isoformat()

    for paper in data["data"]:
        # Prefer DOI, then paperId, then url hash for id
        doi = paper.get("externalIds", {}).get("DOI")
        paper_id = paper.get("paperId")
        url_val = paper.get("url")
        id_val = doi or paper_id or (url_val.replace("https://", "").replace("http://", "").replace("/", "_") if url_val else "")

        # Paywall detection (isOpenAccess is True if not paywalled)
        is_open_access = paper.get("isOpenAccess", None)
        paywalled = None if is_open_access is None else not is_open_access

        try:
            paper_meta = Metadata(
                id=id_val,
                title=paper.get("title", "No title available"),
                authors=[author.get("name", "Unknown Author") for author in paper.get("authors", [])] or ["Unknown Author"],
                published=str(paper.get("year", "")),
                summary=paper.get("abstract", "No abstract available"),
                source="semanticscholar",
                link=url_val or "",
                pdf_url=None,  # Semantic Scholar API does not provide direct PDF links
                doi=doi,
                pmid=paper.get("externalIds", {}).get("PMID"),
                paperId=paper_id,
                citationCount=paper.get("citationCount"),
                displayLink=None,
                tags=None,
                fetch_date=fetch_date,
                paywalled=paywalled,
                extra={"externalIds": paper.get("externalIds", {})}
            )
            papers.append(paper_meta.model_dump())
            logger.info(f"Added paper: {paper_meta.title}")
        except Exception as e:
            logger.error(f"Error creating metadata for {id_val}: {e}")
            continue

    # Save all metadata to a single file
    all_metadata_path = os.path.join(data_dir, "metadata.json")
    with open(all_metadata_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=4, ensure_ascii=False)
    logger.info(f"Fetched and saved {len(papers)} papers from Semantic Scholar for query: {query}")

    return papers

# ----------------- TESTS -----------------
def test_fetch_semantic_scholar():
    """
    Tests the Semantic Scholar fetcher with a sample query.

    This function executes a predefined search to validate that the fetcher
    is operating correctly. It asserts that the output is a list and that
    the metadata contains the expected fields, logging the results.
    """
    test_query = "science"
    test_project = "test_project"
    logger.info("Running test_fetch_semantic_scholar...")
    results = fetch_semantic_scholar(test_query, test_project)
    assert isinstance(results, list), "Result should be a list"
    if results:
        first = results[0]
        assert "id" in first and "title" in first, "Metadata missing required fields"
        logger.info(f"Test passed: {len(results)} results, first title: {first['title']}")
    else:
        logger.warning("Test returned no results (may be a query issue)")

if __name__ == "__main__":
    test_fetch_semantic_scholar()
