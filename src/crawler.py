import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.logger import setup_logger

"""
Provides a recursive web crawler for discovering hyperlinks from a seed URL.

This module defines the `Crawler` class, which systematically browses a website
to a specified depth. It includes features for domain-scoping and implements
a request delay to ensure respectful server interaction.
"""

logger = setup_logger()

class Crawler:
    """
    A recursive web crawler for discovering hyperlinks on a website.

    This class initiates a crawl from a seed URL, recursively following links
    up to a specified `max_depth`. It can be configured to stay within the
    origin domain and avoids re-visiting URLs.

    Attributes:
        seed_url (str): The starting URL for the crawl.
        max_depth (int): The maximum depth to crawl from the seed URL.
        stay_in_domain (bool): If True, restricts crawling to the seed domain.
        domain (str): The network location (domain) of the seed URL.
        visited_urls (set): A set of URLs that have already been fetched.
        headers (dict): HTTP headers for requests.
    """
    def __init__(self, seed_url: str, max_depth: int = 1, stay_in_domain: bool = True):
        self.seed_url = seed_url
        self.max_depth = max_depth
        self.stay_in_domain = stay_in_domain
        self.domain = urlparse(seed_url).netloc
        self.visited_urls = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_page(self, url: str) -> str | None:
        """
        Fetches the HTML content for a given URL.

        Args:
            url (str): The URL of the page to fetch.

        Returns:
            Optional[str]: The HTML content as a string, or None if the URL has
            already been visited or if the request fails.
        """
        if url in self.visited_urls:
            return None
        logger.info(f"Fetching: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            self.visited_urls.add(url)
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Could not fetch {url}: {e}")
            return None

    def parse_links(self, html_content: str, base_url: str) -> list[str]:
        """
        Parses HTML content to extract all valid, absolute hyperlinks.

        This method filters out page fragments and can restrict links to the
        origin domain based on the `stay_in_domain` attribute.

        Args:
            html_content (str): The HTML content of the page.
            base_url (str): The base URL used for resolving relative links.

        Returns:
            List[str]: A list of unique, absolute URLs found on the page.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_link = urljoin(base_url, href)
            parsed_link = urlparse(absolute_link)
            if parsed_link.scheme in ['http', 'https'] and not parsed_link.fragment:
                if self.stay_in_domain and parsed_link.netloc != self.domain:
                    continue
                links.append(absolute_link)
        return list(set(links))

    def crawl(self) -> list[str]:
        """
        Initiates the crawling process starting from the seed URL.

        Returns:
            List[str]: A list of all unique URLs discovered during the crawl.
        """
        logger.info(f"Starting crawl at {self.seed_url} on domain {self.domain} with max depth {self.max_depth}")
        all_links = set()
        self._crawl_recursive(self.seed_url, 0, all_links)
        logger.info(f"Crawl complete. Found {len(all_links)} unique links.")
        return list(all_links)

    def _crawl_recursive(self, url: str, current_depth: int, all_links: set):
        """
        Performs the recursive step of the crawling process.

        This method fetches a page, parses its links, adds them to the collection,
        and recursively calls itself for each newly discovered link until the
        maximum depth is reached.

        Args:
            url (str): The URL to crawl in the current step.
            current_depth (int): The current depth relative to the seed URL.
            all_links (set): A set for accumulating all discovered links.
        """
        if current_depth > self.max_depth or url in self.visited_urls:
            return

        html = self.fetch_page(url)
        if not html:
            return

        found_links = self.parse_links(html, url)
        new_links_count = len(set(found_links) - all_links)
        logger.info(f"Depth {current_depth}: Found {new_links_count} new links on {url}")
        all_links.update(found_links)

        # Recursively crawl the new links
        for link in found_links:
            self._crawl_recursive(link, current_depth + 1, all_links)
            time.sleep(0.1) # Be polite to the server

# Example Usage
if __name__ == "__main__":
    # Test with a blog that has a clear list of articles
    seed = "https://blog.langchain.dev/"
    # Crawl 1 level deep
    crawler = Crawler(seed_url=seed, max_depth=1)
    discovered_links = crawler.crawl()

    print(f"\n--- Discovered Links from {seed} (depth=1) ---")
    if discovered_links:
        # Print a sample of the links
        for i, link in enumerate(discovered_links[:20]):
            print(f"{i+1}. {link}")
    else:
        print("No links were discovered.")
