import os
import sys
import json
from typing import List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.logger import setup_logger
from src.fetchers.pubmed_fetcher import fetch_pubmed
from src.fetchers.web_search_fetcher import fetch_websearch
from src.fetchers.blog_fetcher import BlogFetcher
from src.fetchers.semantic_scholar_fetcher import fetch_semantic_scholar
from src.fetchers.arxiv_fetcher import fetch_arxiv
from src.utils.deduplicator import deduplicate_metadata
from src.utils.query_processor import process_query, llm_rewrite_query_langchain
from src.settings import settings
from src.full_text_fetcher import fetch_full_text_for_all
from src.utils.metadata_filter import filter_metadata_semantic

"""
Orchestrates the entire data fetching and processing pipeline.

This module provides the main `fetch_all` function that coordinates multiple
data sources (fetchers), processes queries, aggregates results, and runs
subsequent steps like deduplication, semantic filtering, and full-text extraction.
"""

logger = setup_logger()
logger.info("Data fetcher orchestrator initialized")

FETCHER_MAP = {
    "pubmed": fetch_pubmed,
    "websearch": fetch_websearch,
    "blog": lambda query, project: BlogFetcher().fetch_articles(query, project),
    "semanticscholar": fetch_semantic_scholar,
    "arxiv": fetch_arxiv
}

def fetch_all(
    query: str,
    project_name: str,
    sources: Optional[List[str]] = None,
    deduplicate: bool = True,
    query_mode: str = "classic",  # "classic" or "llm"
    llm_model: str = "gpt-3.5-turbo",
    llm_api_key: Optional[str] = None,
    filter_metadata: bool = True,
    min_year: Optional[int] = None,
    min_similarity: float = 0.5,
    filter_model_name: str = 'all-MiniLM-L6-v2',
    fetch_fulltext: bool = True,
) -> List[dict]:
    """
    Orchestrates the end-to-end data fetching and processing pipeline.

    This function manages the entire workflow, including:
    1.  Processing the user query (either classic or LLM-based rewriting).
    2.  Fetching metadata from specified sources (e.g., PubMed, ArXiv).
    3.  Optionally deduplicating the aggregated results based on identifiers.
    4.  Optionally filtering the results semantically against the original query.
    5.  Optionally fetching the full text for the final set of entries.

    Args:
        query (str): The primary search query.
        project_name (str): A unique name for the project to namespace data files.
        sources (Optional[List[str]]): A list of source names to query. If None, all available sources are used.
        deduplicate (bool): If True, performs deduplication on the fetched metadata.
        query_mode (str): The query processing mode. Can be "classic" for simple normalization
            or "llm" for rewriting the query using a language model.
        llm_model (str): The identifier for the language model to use for query rewriting.
        llm_api_key (Optional[str]): The API key for the language model service.
        filter_metadata (bool): If True, applies semantic filtering to the deduplicated results.
        min_year (Optional[int]): The minimum publication year for an entry to be included after filtering.
        min_similarity (float): The minimum cosine similarity score (0.0 to 1.0) required for an entry
            to be considered relevant to the query during semantic filtering.
        filter_model_name (str): The sentence-transformer model to use for semantic filtering.
        fetch_fulltext (bool): If True, attempts to fetch the full text for the final filtered entries.

    Returns:
        List[dict]: A list of dictionaries, where each dictionary is a processed metadata entry.
        The level of processing depends on the arguments provided.
    """
    logger.info(f"Starting data fetch for query: '{query}' in project: '{project_name}'")
    results = []
    used_sources = sources or list(FETCHER_MAP.keys())
    fetch_stats = {}

    for source in used_sources:
        fetcher = FETCHER_MAP.get(source)
        if not fetcher:
            logger.warning(f"Unknown source '{source}', skipping.")
            fetch_stats[source] = {"status": "skipped", "count": 0, "error": "Unknown source"}
            continue

        # --- Query Processing ---
        if query_mode == "llm":
            try:
                processed_query = llm_rewrite_query_langchain(
                    query, fetcher=source, model=llm_model, api_key=llm_api_key
                )
                logger.info(f"LLM-rewritten query for {source}: {processed_query}")
            except Exception as e:
                logger.error(f"LLM query rewriting failed for {source}: {e}")
                processed_query = process_query(query, fetcher=source, use_classic=True)
                logger.info(f"Falling back to classic query for {source}: {processed_query}")
        else:
            processed_query = process_query(query, fetcher=source, use_classic=True)
            logger.info(f"Classic processed query for {source}: {processed_query}")

        try:
            logger.info(f"Fetching from {source} ...")
            fetched = fetcher(processed_query, project_name)
            count = len(fetched) if fetched else 0
            if fetched:
                results.extend(fetched)
            logger.info(f"Fetched {count} results from {source}")
            fetch_stats[source] = {"status": "success", "count": count}
        except Exception as e:
            logger.error(f"Error fetching from {source}: {e}")
            fetch_stats[source] = {"status": "failed", "count": 0, "error": str(e)}

    # --- Reporting ---
    logger.info("--- Fetching Summary Report ---")
    total_fetched = 0
    for source, stats in fetch_stats.items():
        if stats['status'] == 'success':
            logger.info(f"- {source}: Success, {stats['count']} articles fetched.")
            total_fetched += stats['count']
        elif stats['status'] == 'failed':
            logger.error(f"- {source}: Failed. Error: {stats['error']}")
        else:
            logger.warning(f"- {source}: Skipped. Reason: {stats.get('error', 'N/A')}")
    logger.info(f"Total articles fetched across all sources: {total_fetched}")
    logger.info("-----------------------------")

    if deduplicate:
        logger.info("Running deduplication on aggregated results ...")
        deduped = deduplicate_metadata(project_name)
        logger.info(f"Deduplication complete. {len(deduped)} unique entries found.")
        filtered = deduped
        if filter_metadata:
            logger.info(f"Filtering deduplicated metadata using semantic similarity (min_year={min_year}, min_similarity={min_similarity}) ...")
            filtered = filter_metadata_semantic(
                deduped,
                query=query,
                min_year=min_year,
                min_similarity=min_similarity,
                model_name=filter_model_name
            )
            filtered_count = len(filtered)
            logger.info(f"Filtering complete. {filtered_count} entries remain after filtering.")

            # Save the filtered metadata for traceability
            filtered_output_path = os.path.join("data", project_name, "deduplicated", "metadata_filtered.json")
            try:
                with open(filtered_output_path, "w", encoding="utf-8") as f:
                    json.dump(filtered, f, indent=4)
                logger.info(f"Saved filtered metadata to {filtered_output_path}")
            except IOError as e:
                logger.error(f"Failed to save filtered metadata: {e}")
        else:
            filtered_count = len(deduped) # If no filtering, the count is the same as after deduplication

        if fetch_fulltext:
            logger.info("Fetching full text for filtered entries ...")
            filtered_with_fulltext = fetch_full_text_for_all(filtered, project_name)
            logger.info("Full text fetching complete.")
            return filtered_with_fulltext
        return filtered
    else:
        logger.info(f"Returning {len(results)} raw (non-deduplicated) results.")
        return results

if __name__ == "__main__":
    # Example usage
    test_query = "machine learning and parallel computing"
    test_project = "test_project"
    all_results = fetch_all(
        test_query,
        test_project,
        deduplicate=True,
        query_mode="classic",  # Temporarily set to classic for validation
        llm_model="gpt-3.5-turbo",  # Or "soromini", etc.
        llm_api_key=settings.openai_api_key, # Or set your API key here
        filter_metadata=True,
        min_year=2020,
        min_similarity=0.5,
        filter_model_name='all-MiniLM-L6-v2',
        fetch_fulltext=True
    )
    print(f"Fetched, deduplicated, filtered, and full-text processed {len(all_results)} results.")