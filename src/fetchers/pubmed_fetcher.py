import os
import sys
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
    logger.info(f"Starting fetch for query: {query}")
    try:
        Entrez.email = settings.pubmed_email
        if not Entrez.email:
            logger.error("PubMed email not configured in .env file")
            return []

        handle = Entrez.esearch(db="pubmed", term=query, retmax=20, sort="pub date", retmode="xml")
        record = Entrez.read(handle)
        handle.close()

        if not record["IdList"]:
            logger.info(f"No results found for query: {query}")
            return []

        id_list = record["IdList"]
        fetch_handle = Entrez.efetch(db="pubmed", id=",".join(id_list), retmode="xml")
        records = Entrez.read(fetch_handle)
        fetch_handle.close()

        papers = []
        data_dir = os.path.join("data", project_name, "pubmed")
        os.makedirs(data_dir, exist_ok=True)

        for pubmed_article in records["PubmedArticle"]:
            article = pubmed_article["MedlineCitation"]["Article"]
            pmid = pubmed_article["MedlineCitation"]["PMID"]

            title = article.get("ArticleTitle", "No title available")
            authors = [
                f"{author.get('LastName', '')} {author.get('Initials', '')}".strip()
                for author in article.get("AuthorList", [])
                if author.get("LastName", "")
            ] or ["Unknown Author"]
            pub_date = article.get("ArticleDate") or pubmed_article["MedlineCitation"].get("DateCompleted", {})
            abstract = article.get("Abstract", {}).get("AbstractText", ["No abstract available"])[0]

            published = (
                pub_date[0].isoformat() if isinstance(pub_date, list) and hasattr(pub_date[0], "isoformat")
                else str(pub_date) if isinstance(pub_date, dict) else str(datetime.now().isoformat())
            )

            paper_info = {
                "title": title,
                "authors": authors,
                "published": published,
                "summary": abstract,
                "pmid": pmid
            }
            papers.append(paper_info)

            metadata_path = os.path.join(data_dir, f"{pmid}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(paper_info, f, indent=4, ensure_ascii=False)

        all_metadata_path = os.path.join(data_dir, "metadata.json")
        with open(all_metadata_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=4, ensure_ascii=False)

        logger.info(f"Fetched {len(papers)} abstracts from PubMed for query: {query}")
        return papers

    except Exception as e:
        logger.error(f"Error fetching from PubMed for query '{query}': {e}")
        return []

if __name__ == "__main__":
    test_query = "machine learning in psychology"
    test_project = "test_project"
    fetch_pubmed(test_query, test_project)