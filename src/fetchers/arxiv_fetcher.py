import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import arxiv
import json
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from src.utils.logger import setup_logger

logger = setup_logger()
logger.info("ArXiv fetcher logger initialized")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_arxiv(query: str, project_name: str) -> list:
    """
    Fetch papers from ArXiv based on the query and save them to the project directory.

    Args:
        query (str): The search query.
        project_name (str): The name of the project to save the papers under.

    Returns:
        list: A list of dictionaries containing metadata of the fetched papers.
    """
    logger.info(f"Starting fetch for query: {query}")
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=20,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    try:
        results = list(client.results(search))
    except arxiv.UnexpectedEmptyPageError as e:
        logger.error(f"Unexpected empty page error for query '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching results for query '{query}': {e}")
        return []

    if not results:
        logger.info(f"No results found for query: {query}")
        return []

    papers = []
    data_dir = os.path.join("data", project_name)
    os.makedirs(data_dir, exist_ok=True)

    for result in results:
        paper_info = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "published": result.published.isoformat(),
            "summary": result.summary,
            "pdf_url": result.pdf_url
        }
        papers.append(paper_info)
        try:
            result.download_pdf(dirpath=data_dir, filename=f"{result.entry_id.split('/')[-1]}.pdf")
        except Exception as e:
            logger.error(f"Failed to download PDF for {result.entry_id}: {e}")
            continue

    metadata_path = os.path.join(data_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(papers, f, indent=4)

    logger.info(f"Fetched {len(papers)} papers from ArXiv for query: {query}")
    return papers

if __name__ == "__main__":
    test_query = "machine learning in psychology and social sciences"
    test_project = "test_project"
    fetch_arxiv(test_query, test_project)