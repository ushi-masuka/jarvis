import os
import sys
import json
import requests
import time
from typing import List, Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.logger import setup_logger

logger = setup_logger()
logger.info("Full text fetcher initialized")

UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "")

def download_pdf(url: str, out_path: str, timeout: int = 30) -> bool:
    try:
        logger.info(f"Attempting PDF download: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.ok and "application/pdf" in r.headers.get("content-type", ""):
            with open(out_path, "wb") as f:
                f.write(r.content)
            logger.info(f"PDF saved to {out_path}")
            return True
        else:
            logger.warning(f"PDF download failed or not a PDF: {url}")
            return False
    except Exception as e:
        logger.warning(f"PDF download error for {url}: {e}")
        return False

def fetch_unpaywall_pdf(doi: str, out_path: str) -> Optional[str]:
    if not UNPAYWALL_EMAIL:
        logger.warning("No UNPAYWALL_EMAIL set; skipping Unpaywall PDF fetch.")
        return None
    api_url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    try:
        logger.info(f"Querying Unpaywall for DOI: {doi}")
        r = requests.get(api_url, timeout=15)
        if r.ok:
            data = r.json()
            pdf_url = data.get("best_oa_location", {}).get("url_for_pdf")
            if pdf_url:
                if download_pdf(pdf_url, out_path):
                    return pdf_url
        logger.info(f"No OA PDF found via Unpaywall for DOI: {doi}")
    except Exception as e:
        logger.warning(f"Unpaywall error for DOI {doi}: {e}")
    return None

def fetch_html(url: str, out_path: str, timeout: int = 30) -> bool:
    try:
        logger.info(f"Attempting HTML download: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.ok and "text/html" in r.headers.get("content-type", ""):
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            logger.info(f"HTML saved to {out_path}")
            return True
        else:
            logger.warning(f"HTML download failed or not HTML: {url}")
            return False
    except Exception as e:
        logger.warning(f"HTML download error for {url}: {e}")
        return False

def fetch_full_text_for_entry(entry: Dict[str, Any], project_name: str, fulltext_dir: str) -> Dict[str, Any]:
    entry_id = entry.get("id") or entry.get("link") or str(hash(str(entry)))
    safe_id = str(entry_id).replace("/", "_").replace(":", "_")
    pdf_path = os.path.join(fulltext_dir, f"{safe_id}.pdf")
    html_path = os.path.join(fulltext_dir, f"{safe_id}.html")

    # 1. Try direct PDF link
    if entry.get("pdf_url"):
        if download_pdf(entry["pdf_url"], pdf_path):
            entry["fulltext_path"] = pdf_path
            entry["fulltext_status"] = "success"
            entry["fulltext_type"] = "pdf"
            return entry
        else:
            entry["fulltext_status"] = "pdf_url_failed"

    # 2. Try Unpaywall if DOI
    if entry.get("doi"):
        pdf_url = fetch_unpaywall_pdf(entry["doi"], pdf_path)
        if pdf_url:
            entry["fulltext_path"] = pdf_path
            entry["fulltext_status"] = "success"
            entry["fulltext_type"] = "pdf"
            entry["fulltext_pdf_url"] = pdf_url
            return entry
        else:
            entry["fulltext_status"] = "unpaywall_failed"

    # 3. Try PubMed Central (PMC) if available
    if entry.get("pmid"):
        pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{entry['pmid']}/pdf/"
        if download_pdf(pmc_url, pdf_path):
            entry["fulltext_path"] = pdf_path
            entry["fulltext_status"] = "success"
            entry["fulltext_type"] = "pdf"
            return entry
        else:
            entry["fulltext_status"] = "pmc_failed"

    # 4. Try HTML download for web/blog/news/medium
    if entry.get("link"):
        if fetch_html(entry["link"], html_path):
            entry["fulltext_path"] = html_path
            entry["fulltext_status"] = "success"
            entry["fulltext_type"] = "html"
            return entry
        else:
            entry["fulltext_status"] = "html_failed"

    # 5. Mark as not found
    entry["fulltext_status"] = "not_found"
    return entry

def fetch_full_text_for_all(metadata_list: List[Dict[str, Any]], project_name: str, delay: float = 1.0) -> List[Dict[str, Any]]:
    fulltext_dir = os.path.join("data", project_name, "fulltext")
    os.makedirs(fulltext_dir, exist_ok=True)
    results = []
    for entry in metadata_list:
        result = fetch_full_text_for_entry(entry, project_name, fulltext_dir)
        results.append(result)
        time.sleep(delay)  # Be polite to servers
    # Save updated metadata with fulltext info
    out_path = os.path.join("data", project_name, "deduplicated", "metadata_with_fulltext.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    logger.info(f"Full text fetching complete. Results saved to {out_path}")
    return results

if __name__ == "__main__":
    # Example usage: load deduplicated metadata and fetch full text
    project_name = "test_project"
    dedup_path = os.path.join("data", project_name, "deduplicated", "metadata.json")
    if not os.path.exists(dedup_path):
        logger.error(f"No deduplicated metadata found at {dedup_path}")
        sys.exit(1)
    with open(dedup_path, "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    fetch_full_text_for_all(metadata_list, project_name)
