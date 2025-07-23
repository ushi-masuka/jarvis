import os
import time
import requests
from typing import Dict, Any

# Selenium is the primary, mandatory dependency for URL extraction.
# Ensure it's installed via requirements.txt: selenium, webdriver-manager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.logger import setup_logger

logger = setup_logger()

"""
Provides utilities for extracting text from various document formats.

This module offers functions to retrieve text from local PDF files using PyMuPDF
and from web pages (HTML) using a robust strategy that combines Selenium for
dynamic content rendering with a cascading series of text extraction libraries.
"""

def get_html_with_selenium(url: str) -> str | None:
    """
    Fetches the HTML source of a URL using a headless browser.

    This function uses Selenium to render a web page, which is essential for
    content that is dynamically loaded with JavaScript.

    Args:
        url (str): The URL of the web page to fetch.

    Returns:
        Optional[str]: The page's HTML content, or None if fetching fails.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    try:
        # Suppress verbose output from webdriver-manager
        os.environ['WDM_LOG_LEVEL'] = '0'
        service = Service(ChromeDriverManager().install())
        with webdriver.Chrome(service=service, options=options) as driver:
            driver.get(url)
            time.sleep(5)  # Wait for dynamic content to load
            return driver.page_source
    except Exception as e:
        logger.warning(f"Selenium failed to render URL {url}. It might be a non-critical error. Details: {e}")
        return None

def fetch_url_content_fallback(url: str, retries: int = 3, delay: int = 5) -> str | None:
    """
    Fetches HTML from a URL using a simple `requests` call with retries.

    This serves as a fallback for when Selenium is not needed or has failed.

    Args:
        url (str): The URL of the web page to fetch.
        retries (int): The number of times to retry the request. Defaults to 3.
        delay (int): The delay between retries in seconds. Defaults to 5.

    Returns:
        Optional[str]: The page's HTML content, or None if all retries fail.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            logger.info(f"Successfully fetched {url} using fallback method.")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Fallback attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"All {retries} fallback attempts for {url} failed.")
                return None

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts plain text from a local PDF file.

    This function uses the PyMuPDF (fitz) library to read text from each page
    of a PDF document. It handles common errors such as file not found or
    encryption.

    Args:
        pdf_path (str): The file path to the PDF document.

    Returns:
        str: The extracted text content, or an empty string if extraction fails.
    """
    if not os.path.isfile(pdf_path):
        logger.error(f"PDF file not found at path: {pdf_path}")
        return ""

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        
        if doc.is_encrypted:
            logger.warning(f"PDF file {pdf_path} is encrypted and cannot be processed.")
            return ""

        text = "\n".join(page.get_text() for page in doc)
        
        if not text.strip():
            logger.warning(f"No text could be extracted from {pdf_path}. It may be an image-only PDF.")

        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {pdf_path}: {e}", exc_info=True)
        return ""

def _extract_from_html_content(html_content: str, source_id: str) -> str:
    """
    Extracts text from HTML content using a cascade of extraction libraries.

    This internal helper function attempts to extract text using a prioritized
    list of tools ('trafilatura', 'readability', 'newspaper3k', 'boilerpy3').
    It proceeds to the next tool if the current one fails or returns low-quality content.

    Parameters
    ----------
    html_content : str
        The HTML source code to process.
    source_id : str
        The identifier of the source (URL or file path) for logging.

    Returns
    -------
    str
        The extracted plain text, or an empty string if all methods fail.

    Raises
    ------
    Exception
        If any of the extraction tools fail.

    """
    def _try_trafilatura(html):
        """
        Extracts text from HTML using the 'trafilatura' library.

        Args:
            html (str): The HTML content of a web page.

        Returns:
            Optional[str]: The extracted main text, or None if extraction fails.
        """
        from trafilatura import extract
        return extract(html)

    def _try_readability(html):
        """
        Extracts text from HTML using the 'readability-lxml' library.

        Args:
            html (str): The HTML content of a web page.

        Returns:
            Optional[str]: The extracted main text, or None if extraction fails.
        """
        try:
            from readability import Document
            from bs4 import BeautifulSoup
            doc = Document(html)
            soup = BeautifulSoup(doc.summary(), 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        except Exception:
            return None

    def _try_newspaper(html):
        """
        Extracts text from HTML using the 'newspaper3k' library.

        Args:
            html (str): The HTML content of a web page.

        Returns:
            Optional[str]: The extracted main text, or None if extraction fails.
        """
        from newspaper import Article
        article = Article(url='http://example.com') # Base URL is required but not used for parsing local HTML
        article.set_html(html)
        article.parse()
        return article.text

    def _try_boilerpy(html):
        """
        Extracts text from HTML using the 'boilerpy3' library.

        Args:
            html (str): The HTML content of a web page.

        Returns:
            Optional[str]: The extracted main text, or None if extraction fails.
        """
        from boilerpy3 import extractors
        extractor = extractors.ArticleExtractor()
        return extractor.get_content(html)

    extractors = [
        ("trafilatura", _try_trafilatura),
        ("readability-lxml", _try_readability),
        ("newspaper3k", _try_newspaper),
        ("boilerpy3", _try_boilerpy),
    ]

    for name, extractor_func in extractors:
        try:
            text = extractor_func(html_content)
            if text and len(text.strip()) > 100:
                logger.info(f"Successfully extracted text from {source_id} using {name}.")
                return text.strip()
            else:
                logger.warning(f"{name} produced no or very little text for {source_id}.")
        except Exception as e:
            logger.warning(f"{name} failed to extract text from {source_id}", exc_info=True)

    logger.error(f"All extractors failed for HTML from: {source_id}")
    return ""

def extract_text_from_html(html_path: str) -> str:
    """
    Extracts text from a local HTML file.

    Args:
        html_path (str): The path to the local HTML file.

    Returns:
        str: The extracted text content, or an empty string if the file cannot be read.
    """
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        if not html_content.strip():
            logger.warning(f"HTML file is empty: {html_path}")
            return ""
    except IOError as e:
        logger.error(f"Could not read HTML file at {html_path}: {e}")
        return ""
    return _extract_from_html_content(html_content, source_id=html_path)

def extract_text_from_url(url: str) -> str:
    """
    Fetches and extracts text from a given URL.

    This function orchestrates the fetching and extraction process. It first tries
    to fetch HTML using Selenium to support JavaScript-rendered pages, falling
    back to a standard `requests` call if Selenium fails.

    Args:
        url (str): The URL of the web page to process.

    Returns:
        str: The extracted text, or an empty string if all methods fail.
    """
    logger.info(f"Attempting to extract from {url} using primary method (Selenium)...")
    html_content = get_html_with_selenium(url)

    if not html_content:
        logger.warning(f"Primary method (Selenium) failed for {url}. Attempting fallback (requests)...")
        html_content = fetch_url_content_fallback(url)

    if not html_content:
        logger.error(f"All fetch methods failed for {url}.")
        return ""

    return _extract_from_html_content(html_content, source_id=url)

# Example usage
if __name__ == "__main__":
    # Create a dummy HTML file for testing
    if not os.path.exists("example.html"):
        with open("example.html", "w", encoding="utf-8") as f:
            f.write("""<html><head><title>Test Page</title></head>
                       <body><h1>An Important Headline</h1>
                       <p>This is the first paragraph of the article. It contains over one hundred characters to ensure it passes the quality check we have implemented in our extraction logic.</p>
                       <p>This is a second paragraph, just for good measure.</p>
                       </body></html>""")

    if not os.path.exists("example.pdf"):
        logger.warning("Test PDF 'example.pdf' not found. PDF extraction will not be fully tested.")

    # --- Test Cases ---
    entry_pdf = {"fulltext_path": "example.pdf", "title": "Example PDF"}
    entry_html = {"fulltext_path": "example.html", "title": "Example HTML"}
    # This URL is known to work well with standard requests
    entry_url_simple = {"url": "http://info.cern.ch/hypertext/WWW/TheProject.html", "title": "CERN Page"}
    # A URL that might benefit from or require JS rendering
    entry_url_dynamic = {"url": "https://www.youtube.com", "title": "YouTube"}


    print("--- Testing PDF Extraction ---")
    pdf_text = extract_text_from_pdf(entry_pdf["fulltext_path"])
    if pdf_text:
        print(f"Successfully extracted {len(pdf_text)} characters from PDF.")
    else:
        print("PDF extraction failed or file not found.")

    print("\n--- Testing HTML File Extraction ---")
    html_text = extract_text_from_html(entry_html["fulltext_path"])
    print(f"Extracted {len(html_text)} characters from local HTML file.")

    print("\n--- Testing URL Extraction (Simple URL) ---")
    url_text_simple = extract_text_from_url(entry_url_simple["url"])
    print(f"Extracted {len(url_text_simple)} characters from simple URL.")

    print("\n--- Testing URL Extraction (Dynamic URL) ---")
    url_text_dynamic = extract_text_from_url(entry_url_dynamic["url"])
    print(f"Extracted {len(url_text_dynamic)} characters from dynamic URL.")