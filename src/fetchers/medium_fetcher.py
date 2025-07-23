import os
import sys
import json
import time
from urllib.robotparser import RobotFileParser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.logger import setup_logger
from src.utils.metadata_schema import Metadata

logger = setup_logger()

"""
Provides a fetcher for scraping articles from Medium.com.

This module uses Selenium to perform web scraping of Medium articles, handling
dynamically loaded content. It includes functionality to respect robots.txt
to ensure ethical data collection practices.
"""

class MediumFetcher:
    """
    A web scraper for fetching articles from Medium.com.

    This class encapsulates the logic for searching Medium, scraping article
    content using Selenium, and saving the extracted metadata.

    Attributes:
        base_url (str): The base URL for Medium search.
        headers (dict): HTTP headers to use for requests.
        max_articles (int): The maximum number of articles to fetch.
        ignore_robots (bool): Whether to ignore the robots.txt file.
        chromedriver_path (str): The path to the ChromeDriver executable.
        robot_parser (RobotFileParser): An instance to parse robots.txt.
    """
    def __init__(self, max_articles=10, ignore_robots=False, chromedriver_path=None):
        """
        Initializes the MediumFetcher instance.

        Args:
            max_articles (int): The maximum number of articles to fetch.
            ignore_robots (bool): If True, robots.txt rules will be ignored.
            chromedriver_path (str, optional): The path to the ChromeDriver
                executable. Defaults to None.
        """
        self.base_url = "https://medium.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.max_articles = max_articles
        self.ignore_robots = ignore_robots
        self.chromedriver_path = chromedriver_path or "D:/jarvis/chromedriver.exe"
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url("https://medium.com/robots.txt")
        self.robot_parser.read()

    def is_allowed(self, url):
        """
        Checks if scraping a given URL is permitted by robots.txt.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if scraping is allowed, False otherwise.
        """
        return self.ignore_robots or self.robot_parser.can_fetch(self.headers["User-Agent"], url)

    def fetch_articles(self, query: str, project_name: str):
        """
        Fetches and scrapes articles from Medium based on a search query.

        This method navigates to the Medium search results page, scrolls to load
        articles, and then iterates through the links to scrape content from each
        article page. The extracted metadata is saved to a JSON file.

        Args:
            query (str): The search term to use on Medium.
            project_name (str): The name of the project for namespacing output data.

        Returns:
            list: A list of dictionaries, where each dictionary contains the
            metadata for a scraped article.
        """
        articles = []
        output_dir = os.path.join("data", project_name, "medium")
        os.makedirs(output_dir, exist_ok=True)
        full_url = f"{self.base_url}?q={query.replace(' ', '+')}"
        fetch_date = datetime.now().isoformat()

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            # Use Selenium's service to manage chromedriver automatically
            service = webdriver.chrome.service.Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(full_url)
            logger.info(f"Navigated to {full_url}")

            # Wait for article containers to be present
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-test-id='post-preview']"))
            )

            # Scroll to load more articles if necessary
            for _ in range(3): # Scroll 3 times to load more content
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            article_links = soup.select("article[data-test-id='post-preview'] a[href*='/@']")
            unique_links = list(dict.fromkeys([a['href'] for a in article_links if a.h2]))

            logger.info(f"Found {len(unique_links)} unique article links.")

            for idx, link_href in enumerate(unique_links):
                if idx >= self.max_articles:
                    break
                
                full_link = link_href if link_href.startswith('http') else 'https://medium.com' + link_href
                if not self.is_allowed(full_link):
                    logger.warning(f"Skipping disallowed URL: {full_link}")
                    continue

                try:
                    logger.info(f"Fetching content from: {full_link}")
                    driver.get(full_link)
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                    article_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    title = article_soup.find('h1').get_text(strip=True) if article_soup.find('h1') else 'No Title'
                    
                    # Extract full text content
                    article_body = article_soup.find('article')
                    full_text = ' '.join([p.get_text(strip=True) for p in article_body.find_all('p')]) if article_body else "No Content"
                    summary = full_text[:1000] + '...' if len(full_text) > 1000 else full_text

                    meta = Metadata(
                        id=full_link.split('?')[0].replace("https://", "").replace("/", "_").replace(".", "_"),
                        title=title,
                        authors=[], # Author extraction can be complex, skipping for now
                        published="Unknown", # Date extraction is also brittle
                        summary=summary,
                        source="medium",
                        link=full_link,
                        pdf_url=None, doi=None, pmid=None, paperId=None, citationCount=None,
                        displayLink=None, tags=None, fetch_date=fetch_date, paywalled=None, extra=None
                    )
                    articles.append(meta.model_dump())
                    logger.info(f"Successfully fetched and processed: {title}")
                except Exception as article_error:
                    logger.error(f"Failed to process article {full_link}: {article_error}")
                time.sleep(1) # Be respectful

            driver.quit()

            output_file = os.path.join(output_dir, f"medium_{query.replace(' ', '_')}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=4)
            logger.info(f"Saved {len(articles)} articles to {output_file}")

        except Exception as e:
            logger.error(f"Error in Medium fetcher: {str(e)}")
            if 'driver' in locals():
                driver.quit()

        return articles

if __name__ == "__main__":
    fetcher = MediumFetcher(max_articles=5, ignore_robots=True)
    fetcher.fetch_articles("machine learning", "test_project")