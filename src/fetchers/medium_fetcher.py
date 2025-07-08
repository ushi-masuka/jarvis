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
# Add the project root to sys.path to find the src module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.logger import setup_logger

logger = setup_logger()

class MediumFetcher:
    def __init__(self, max_articles=10, ignore_robots=False, chromedriver_path=None):
        self.base_url = "https://medium.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.max_articles = max_articles
        self.ignore_robots = ignore_robots
        self.chromedriver_path = chromedriver_path or "D:/jarvis/chromedriver.exe"  # Default path
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url("https://medium.com/robots.txt")
        self.robot_parser.read()

    def is_allowed(self, url):
        """Check if the URL is allowed by robots.txt."""
        return self.robot_parser.can_fetch(self.headers["User-Agent"], url)

    def fetch_articles(self, query):
        """Fetch article metadata from Medium based on a search query."""
        articles = []
        params = {"q": query}
        output_dir = os.path.join("data", "test_project", "medium")
        os.makedirs(output_dir, exist_ok=True)
        full_url = f"{self.base_url}?q={query.replace(' ', '+')}"

        try:
            # Set up Selenium with headless Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")  # For Windows compatibility
            logger.debug(f"Using ChromeDriver at: {self.chromedriver_path}")
            driver = webdriver.Chrome(executable_path=self.chromedriver_path, options=chrome_options)

            driver.get(full_url)
            logger.debug(f"Page title: {driver.title}")

            # Wait for articles to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )

            # Get the page source after JavaScript rendering
            soup = BeautifulSoup(driver.page_source, "html.parser")
            logger.debug(f"Found {len(soup.find_all('div'))} div tags in response")
            article_blocks = soup.find_all("article")  # Try article tag as a starting point

            if not article_blocks:
                logger.warning("No article blocks found with tag 'article'. Trying 'div' as fallback.")
                article_blocks = soup.find_all("div", class_=lambda x: x and "post" in x.lower())

            for idx, block in enumerate(article_blocks):
                if idx >= self.max_articles:
                    break

                title_elem = block.find("h3")
                link_elem = block.find("a", href=True)
                date_elem = block.find("time")
                summary_elem = block.find("p", class_=lambda x: x and "graf" in x.lower())

                title = title_elem.text.strip() if title_elem else "No Title"
                link = link_elem["href"] if link_elem else ""
                published = date_elem["datetime"] if date_elem else "Unknown"
                summary = summary_elem.text.strip() if summary_elem else "No Summary"

                if link and not link.startswith("http"):
                    link = "https://medium.com" + link

                entry = {
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": summary
                }
                articles.append(entry)
                logger.info(f"Fetched article: {title}")
                time.sleep(1)  # Rate limit to 1 request/second

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
    fetcher.fetch_articles("machine learning")