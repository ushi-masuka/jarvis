import os
import sys
# Ensure the project root is in sys.path before imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
from Bio import Entrez
from datetime import datetime
from src.utils.logger import setup_logger
from tenacity import retry, stop_after_attempt, wait_fixed
from src.settings import settings

logger = setup_logger()
logger.info("PubMed fetcher logger initialized")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_pubmed(query: str, project_name: str) -> list:
    """
    Fetch abstracts from PubMed based on the query and save them to the project directory.

    Args:
        query (str): The search query.
        project_name (str): The name of the project to save the abstracts under.

    Returns:
        list: A list of dictionaries containing metadata of the fetched abstracts.
    """

    # Log the start of the fetch
    logger.info(f"Starting fetch for query: {query}")

    try:
        # Use Entrez to search PubMed for the query
        Entrez.email = settings.pubmed_email
        if not Entrez.email:
            # Log an error if the email is not set in the .env file
            logger.error("PubMed email not configured in .env file")
            return []

        # Search PubMed for the query
        handle = Entrez.esearch(db="pubmed", term=query, retmax=20, sort="pub date", retmode="xml")
        # Read the search results
        record = Entrez.read(handle)
        # Close the Entrez handle
        handle.close()

        # If there are no results, log a message and return an empty list
        if not record["IdList"]:
            logger.info(f"No results found for query: {query}")
            return []

        # Get a list of IDs for the search results
        id_list = record["IdList"]
        # Fetch the abstracts for the search results
        fetch_handle = Entrez.efetch(db="pubmed", id=",".join(id_list), retmode="xml")
        # Read the abstracts
        records = Entrez.read(fetch_handle)
        # Close the Entrez handle
        fetch_handle.close()

        # Initialize an empty list to store the paper metadata
        papers = []
        # Make sure the data directory exists
        data_dir = os.path.join("data", project_name, "pubmed")
        os.makedirs(data_dir, exist_ok=True)

        # Loop through each abstract
        for pubmed_article in records["PubmedArticle"]:
            # Get the article and the ID
            article = pubmed_article["MedlineCitation"]["Article"]
            pmid = pubmed_article["MedlineCitation"]["PMID"]

            # Get the title, authors, and abstract
            title = article.get("ArticleTitle", "No title available")
            authors = [
                f"{author.get('LastName', '')} {author.get('Initials', '')}".strip()
                for author in article.get("AuthorList", [])
                if author.get("LastName", "")
            ] or ["Unknown Author"]
            pub_date = article.get("ArticleDate") or pubmed_article["MedlineCitation"].get("DateCompleted", {})
            abstract = article.get("Abstract", {}).get("AbstractText", ["No abstract available"])[0]

            # Format the publication date
            published = (
                pub_date[0].isoformat() if isinstance(pub_date, list) and hasattr(pub_date[0], "isoformat")
                else str(pub_date) if isinstance(pub_date, dict) else str(datetime.now().isoformat())
            )

            # Create a dictionary to store the metadata
            paper_info = {
                "title": title,
                "authors": authors,
                "published": published,
                "summary": abstract,
                "pmid": pmid
            }
            # Add the metadata to the list of papers
            papers.append(paper_info)

            # Save the metadata to a JSON file
            metadata_path = os.path.join(data_dir, f"{pmid}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(paper_info, f, indent=4, ensure_ascii=False)

        # Save all the metadata to a single JSON file
        all_metadata_path = os.path.join(data_dir, "metadata.json")
        with open(all_metadata_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=4, ensure_ascii=False)

        # Log the number of abstracts fetched
        logger.info(f"Fetched {len(papers)} abstracts from PubMed for query: {query}")
        return papers

    except Exception as e:
        # Log any errors that occur
        logger.error(f"Error fetching from PubMed for query '{query}': {e}")
        return []

if __name__ == "__main__":
    test_query = "machine learning in psychology"
    test_project = "test_project"
    fetch_pubmed(test_query, test_project)