import os
import sys
import json
import time
import feedparser
from newspaper import Article, Config
from trafilatura import fetch_url, extract
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.logger import setup_logger
from src.utils.metadata_schema import Metadata

"""
Provides a fetcher for discovering and extracting content from blogs.

This module contains the BlogFetcher class, which uses RSS feeds to discover
relevant article URLs based on a query. It then employs multiple extraction
libraries (newspaper3k, trafilatura) to scrape content and metadata.
"""

logger = setup_logger()

class BlogFetcher:
    """
    Fetches and extracts blog articles using RSS feeds and web scraping.

    This class discovers article URLs by searching through a predefined list of
    RSS feeds based on query keywords. It then uses multiple extraction tools
    to parse and retrieve content from the discovered URLs.

    Attributes:
        timeout (int): Default timeout for HTTP requests.
        config (newspaper.Config): Configuration object for the newspaper library.
        feeds (Dict[str, List[str]]): A dictionary mapping categories to RSS feed URLs.
        general_feed (str): A fallback RSS feed URL to use if no specific feeds match.
    """

    def __init__(self, timeout=10):
        """
        Initializes the BlogFetcher instance.

        Args:
            timeout (int): The request timeout in seconds.
        """
        self.timeout = timeout
        self.config = Config()
        self.config.request_timeout = timeout
        self.config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.feeds = {
            "news": ["https://rss.cnn.com/rss/edition.rss", "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml", "https://www.bbc.com/mundo/index.xml"],
            "technology": ["https://techcrunch.com/feed/", "https://www.theverge.com/rss/index.xml", "https://feeds.feedburner.com/engadget/full"],
            "lifestyle": ["https://www.apartmenttherapy.com/rss/all.xml", "https://www.treehugger.com/rss/all.xml"],
            "education": ["https://www.edutopia.org/blog/feed", "https://www.insidehighered.com/feed"],
            "health": ["https://www.healthline.com/rss/health", "https://www.webmd.com/rss/default.aspx"],
            "sports": ["https://www.espn.com/espn/rss/news", "https://www.skysports.com/rss/feeds/wa.xml"],
            "entertainment": ["https://www.hollywoodreporter.com/feed/", "https://variety.com/feed/"],
            "business": ["https://www.forbes.com/business/feed/", "https://feeds.feedburner.com/entrepreneur/latest"],
            "diversity": ["https://paradigmiq.com/feed", "https://catalyst.org/feed"],
            "science": ["https://www.sciencedaily.com/rss/top.xml", "https://www.nature.com/subjects/physics/rss"]
        }
        self.general_feed = "https://medium.com/feed"

    def fetch_from_rss(self, query):
        """
        Discovers article URLs from RSS feeds based on a query.

        It selects relevant RSS feeds by matching keywords from the query against
        predefined categories. It then parses these feeds to find entries that
        match the query keywords in their title or summary.

        Args:
            query (str): The search query used to find relevant articles.

        Returns:
            List[str]: A list of unique URLs found in the RSS feeds.
        """
        urls = []
        keywords = query.lower().split()
        selected_feeds = set()
        for kw in keywords:
            for category, feeds in self.feeds.items():
                if kw in category:
                    selected_feeds.update(feeds)
        if not selected_feeds:
            logger.warning(f"No specific feeds found for query '{query}'. Using general feed.")
            selected_feeds.add(self.general_feed)
        else:
            selected_feeds.add(self.general_feed)
        for feed_url in selected_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    if any(kw in entry.get("title", "").lower() or kw in entry.get("summary", "").lower() for kw in keywords):
                        urls.append(entry.link)
            except Exception as e:
                logger.warning(f"Error parsing RSS feed {feed_url}: {str(e)}")
        return list(dict.fromkeys(urls))

    def extract_with_newspaper(self, url):
        """
        Extracts article content and metadata using the newspaper3k library.

        Args:
            url (str): The URL of the article to process.

        Returns:
            Dict[str, str]: A dictionary containing the extracted title, publication
            date, summary, and other metadata.
        """
        entry = {"link": url, "source": "newspaper3k", "title": "No Title", "published": "Unknown", "summary": "No Summary"}
        try:
            article = Article(url, config=self.config)
            article.download()
            if article.download_state == 2:
                article.parse()
                entry.update({
                    "title": article.title,
                    "published": article.publish_date.strftime("%Y-%m-%d") if article.publish_date else "Unknown",
                    "summary": article.summary
                })
                logger.info(f"Extracted with newspaper3k: {article.title}")
        except Exception as e:
            logger.warning(f"newspaper3k failed for {url}: {str(e)}")
        return entry

    def extract_with_trafilatura(self, url):
        """
        Extracts the main text content from a URL using the trafilatura library.

        Args:
            url (str): The URL of the article to process.

        Returns:
            Dict[str, str]: A dictionary containing the extracted summary and other
            metadata.
        """
        entry = {"link": url, "source": "trafilatura", "title": "No Title", "published": "Unknown", "summary": "No Summary"}
        try:
            downloaded = fetch_url(url)
            if downloaded:
                text = extract(downloaded, include_comments=False, include_tables=False, deduplicate=True, output_format='python')
                if text:
                    entry.update({
                        "summary": text.strip()[:500]
                    })
                    logger.info(f"Extracted text with trafilatura for {url}")
        except Exception as e:
            logger.warning(f"trafilatura failed for {url}: {str(e)}")
        return entry

    def fetch_articles(self, query, project_name, max_articles=None):
        """
        Orchestrates the fetching and processing of blog articles.

        This method performs the full workflow: discovering URLs via RSS, extracting
        content using multiple methods (newspaper3k, trafilatura), creating standardized
        metadata objects, and saving the results to a JSON file within the project's
        data directory.

        Args:
            query (str): The search query to discover articles.
            project_name (str): The name of the project for namespacing data.
            max_articles (Optional[int]): The maximum number of articles to process.

        Returns:
            List[dict]: A list of dictionaries, where each represents the metadata
            of a fetched article.
        """
        articles = []
        output_dir = os.path.join("data", project_name, "blog")
        os.makedirs(output_dir, exist_ok=True)
        urls = self.fetch_from_rss(query)
        if not urls:
            logger.warning(f"No URLs found in RSS feeds for query '{query}'")
            return articles
        if max_articles and max_articles < len(urls) * 2:
            urls = urls[:max_articles // 2]
        fetch_date = datetime.now().isoformat()
        for idx, url in enumerate(urls):
            logger.info(f"Fetching article {idx + 1} from {url}")
            for entry in [self.extract_with_newspaper(url), self.extract_with_trafilatura(url)]:
                meta = Metadata(
                    id=entry.get("link", "").replace("http://", "").replace("https://", "").replace("/", "_"),
                    title=entry.get("title", "No Title"),
                    authors=[],
                    published=entry.get("published", "Unknown"),
                    summary=entry.get("summary", "No Summary"),
                    source="blog",
                    link=entry.get("link", ""),
                    pdf_url=None,
                    doi=None,
                    pmid=None,
                    paperId=None,
                    citationCount=None,
                    displayLink=None,
                    tags=None,
                    fetch_date=fetch_date,
                    paywalled=None,
                    extra={"source": entry.get("source")}
                )
                articles.append(meta.model_dump())
            time.sleep(1)
        output_file = os.path.join(output_dir, f"blog_{query.replace(' ', '_')}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4)
        logger.info(f"Saved {len(articles)} articles to {output_file}")
        return articles

if __name__ == "__main__":
    fetcher = BlogFetcher()
    fetcher.fetch_articles("machine learning in actuary", "test_project", max_articles=100)