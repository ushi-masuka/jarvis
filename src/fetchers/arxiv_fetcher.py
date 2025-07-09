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
logger.info("ArXiv fetcher logger initialized")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_arxiv(query: str, project_name: str) -> list:
    """
    Fetch papers from ArXiv based on the query and save them to the project directory.
    """
    import arxiv  # Local import to avoid issues if not installed elsewhere

    logger.info(f"Starting fetch for query: {query}")
    client = arxiv.Client()

    search = arxiv.Search(
        query=query,
        max_results=10,
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
    data_dir = os.path.join("data", project_name, "arxiv")
    os.makedirs(data_dir, exist_ok=True)
    fetch_date = datetime.now().isoformat()

    for result in results:
        arxiv_id = result.entry_id.split('/')[-1]
        canonical_link = f"https://arxiv.org/abs/{arxiv_id}"

        try:
            paper_meta = Metadata(
                id=arxiv_id,
                title=result.title,
                authors=[author.name for author in result.authors],
                published=result.published.isoformat() if hasattr(result.published, "isoformat") else str(result.published),
                summary=result.summary,
                source="arxiv",
                link=canonical_link,
                pdf_url=result.pdf_url,
                doi=None,
                pmid=None,
                paperId=None,
                citationCount=None,
                displayLink=None,
                tags=None,
                fetch_date=fetch_date,
                paywalled=None,
                extra=None
            )
            papers.append(paper_meta.model_dump())
            logger.info(f"Added paper: {result.title}")
        except Exception as e:
            logger.error(f"Error creating metadata for {arxiv_id}: {e}")
            continue

        try:
            result.download_pdf(dirpath=data_dir, filename=f"{arxiv_id}.pdf")
            logger.info(f"Downloaded PDF for {arxiv_id}")
        except Exception as e:
            logger.warning(f"Failed to download PDF for {arxiv_id}: {e}")

    metadata_path = os.path.join(data_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=4, ensure_ascii=False)
    logger.info(f"Fetched and saved {len(papers)} papers from ArXiv for query: {query}")

    return papers

# ----------------- TESTS -----------------
def test_fetch_arxiv():
    """
    Test the ArXiv fetcher with a sample query and project.
    """
    test_query = "protein protein network analysis"
    test_project = "test_project"
    logger.info("Running test_fetch_arxiv...")
    results = fetch_arxiv(test_query, test_project)
    assert isinstance(results, list), "Result should be a list"
    if results:
        first = results[0]
        assert "id" in first and "title" in first, "Metadata missing required fields"
        logger.info(f"Test passed: {len(results)} results, first title: {first['title']}")
    else:
        logger.warning("Test returned no results (may be a query issue)")

if __name__ == "__main__":
    test_fetch_arxiv()