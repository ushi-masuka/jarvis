import os
import sys
import json
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed

# Add project root to sys.path for CLI execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.utils.logger import setup_logger
from src.utils.metadata_schema import Metadata
from src.settings import settings

logger = setup_logger()
logger.info("PubMed fetcher logger initialized")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_pubmed(query: str, project_name: str) -> list:
    """
    Fetch papers from PubMed based on the query and save them to the project directory.
    """
    from Bio import Entrez

    logger.info(f"Starting fetch for query: {query}")

    Entrez.email = settings.pubmed_email
    if not Entrez.email:
        logger.error("PubMed email not configured in .env file")
        return []

    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=10, sort="pub date", retmode="xml")
        record = Entrez.read(handle)
        handle.close()
    except Exception as e:
        logger.error(f"Error searching PubMed for query '{query}': {e}")
        return []

    if not record.get("IdList"):
        logger.info(f"No results found for query: {query}")
        return []

    id_list = record["IdList"]

    try:
        fetch_handle = Entrez.efetch(db="pubmed", id=",".join(id_list), retmode="xml")
        records = Entrez.read(fetch_handle)
        fetch_handle.close()
    except Exception as e:
        logger.error(f"Error fetching PubMed records: {e}")
        return []

    papers = []
    data_dir = os.path.join("data", project_name, "pubmed")
    os.makedirs(data_dir, exist_ok=True)
    fetch_date = datetime.now().isoformat()

    for pubmed_article in records.get("PubmedArticle", []):
        try:
            citation = pubmed_article["MedlineCitation"]
            article = citation["Article"]
            pmid = citation.get("PMID", "")
            title = article.get("ArticleTitle", "No title available")
            authors = [
                f"{author.get('LastName', '')} {author.get('Initials', '')}".strip()
                for author in article.get("AuthorList", [])
                if isinstance(author, dict) and author.get("LastName", "")
            ] or ["Unknown Author"]
            # Try to get publication date
            pub_date = ""
            if "ArticleDate" in article and article["ArticleDate"]:
                d = article["ArticleDate"][0]
                pub_date = f"{d.get('Year', '')}-{d.get('Month', '01')}-{d.get('Day', '01')}"
            elif "Journal" in article and "JournalIssue" in article["Journal"]:
                journal_issue = article["Journal"]["JournalIssue"]
                year = journal_issue.get("PubDate", {}).get("Year", "")
                pub_date = year
            else:
                pub_date = ""
            # Abstract
            abstract = ""
            if "Abstract" in article and "AbstractText" in article["Abstract"]:
                abs_text = article["Abstract"]["AbstractText"]
                if isinstance(abs_text, list):
                    abstract = " ".join(str(x) for x in abs_text)
                else:
                    abstract = str(abs_text)
            else:
                abstract = "No abstract available"
            # DOI
            doi = None
            if "ELocationID" in article:
                for eloc in article["ELocationID"]:
                    if eloc.attributes.get("EIdType") == "doi":
                        doi = str(eloc)
                        break
            # Build metadata
            paper_meta = Metadata(
                id=str(pmid),
                title=title,
                authors=authors,
                published=pub_date,
                summary=abstract,
                source="pubmed",
                link=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                pdf_url=None,
                doi=doi,
                pmid=str(pmid),
                paperId=None,
                citationCount=None,
                displayLink=None,
                tags=None,
                fetch_date=fetch_date,
                paywalled=None,
                extra=None
            )
            papers.append(paper_meta.model_dump())
            logger.info(f"Added paper: {title}")
        except Exception as e:
            logger.error(f"Error creating metadata for PubMed article: {e}")
            continue

    metadata_path = os.path.join(data_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=4, ensure_ascii=False)
    logger.info(f"Fetched and saved {len(papers)} papers from PubMed for query: {query}")

    return papers

# ----------------- TESTS -----------------
def test_fetch_pubmed():
    """
    Test the PubMed fetcher with a sample query and project.
    """
    test_query = "protein protein network analysis"
    test_project = "test_project"
    logger.info("Running test_fetch_pubmed...")
    results = fetch_pubmed(test_query, test_project)
    assert isinstance(results, list), "Result should be a list"
    if results:
        first = results[0]
        assert "id" in first and "title" in first, "Metadata missing required fields"
        logger.info(f"Test passed: {len(results)} results, first title: {first['title']}")
    else:
        logger.warning("Test returned no results (may be a query issue)")

if __name__ == "__main__":
    test_fetch_pubmed()