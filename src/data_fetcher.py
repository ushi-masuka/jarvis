import os
import sys
from typing import List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.logger import setup_logger
from src.fetchers.pubmed_fetcher import fetch_pubmed
from src.fetchers.web_search_fetcher import fetch_websearch
from src.fetchers.blog_fetcher import BlogFetcher
from src.fetchers.semantic_scholar_fetcher import fetch_semantic_scholar
# from src.fetchers.arxiv_fetcher import fetch_arxiv  # Uncomment if you want to include arxiv
from src.utils.deduplicator import deduplicate_metadata

logger = setup_logger()
logger.info("Data fetcher orchestrator initialized")

FETCHER_MAP = {
    "pubmed": fetch_pubmed,
    "websearch": fetch_websearch,
    "blog": lambda query, project: BlogFetcher().fetch_articles(query, project),
    "semanticscholar": fetch_semantic_scholar,
    # "arxiv": fetch_arxiv,  # Uncomment if you want to include arxiv
}

def fetch_all(
    query: str,
    project_name: str,
    sources: Optional[List[str]] = None,
    deduplicate: bool = True
) -> List[dict]:
    """
    Orchestrate fetching from all or selected sources, aggregate and optionally deduplicate results.

    Args:
        query (str): The search query.
        project_name (str): The project namespace.
        sources (List[str], optional): List of sources to use. If None, use all.
        deduplicate (bool): Whether to deduplicate results.

    Returns:
        List[dict]: List of metadata dicts (possibly deduplicated).
    """
    logger.info(f"Starting data fetch for query: '{query}' in project: '{project_name}'")
    results = []
    used_sources = sources or list(FETCHER_MAP.keys())

    for source in used_sources:
        fetcher = FETCHER_MAP.get(source)
        if not fetcher:
            logger.warning(f"Unknown source '{source}', skipping.")
            continue
        try:
            logger.info(f"Fetching from {source} ...")
            fetched = fetcher(query, project_name)
            if fetched:
                results.extend(fetched)
                logger.info(f"Fetched {len(fetched)} results from {source}")
            else:
                logger.info(f"No results from {source}")
        except Exception as e:
            logger.error(f"Error fetching from {source}: {e}")

    if deduplicate:
        logger.info("Running deduplication on aggregated results ...")
        deduped = deduplicate_metadata(project_name)
        logger.info(f"Deduplication complete. {len(deduped)} unique entries found.")
        return deduped
    else:
        logger.info(f"Returning {len(results)} raw (non-deduplicated) results.")
        return results

if __name__ == "__main__":
    # Example usage
    test_query = "machine learning in psychology"
    test_project = "test_project"
    all_results = fetch_all(test_query, test_project, deduplicate=True)
    print(f"Fetched and deduplicated {len(all_results)} results.")