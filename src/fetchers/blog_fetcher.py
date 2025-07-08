import os
import sys
import json
import time
import feedparser
from newspaper import Article, Config
from trafilatura import fetch_url, extract
# Add the project root to sys.path to find the src module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.logger import setup_logger

logger = setup_logger()

class BlogFetcher:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.config = Config()
        self.config.request_timeout = timeout
        self.config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        # Comprehensive RSS feeds across diverse topics
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
        self.general_feed = "https://medium.com/feed"  # Broad catch-all

    def fetch_from_rss(self, query):
        """Fetch blog URLs from RSS feeds based on a query."""
        urls = []
        keywords = query.lower().split()
        
        # Select feeds based on matching keywords to categories
        selected_feeds = set()
        for kw in keywords:
            for category, feeds in self.feeds.items():
                if kw in category:
                    selected_feeds.update(feeds)
        
        if not selected_feeds:
            logger.warning(f"No specific feeds found for query '{query}'. Using general feed.")
            selected_feeds.add(self.general_feed)
        else:
            selected_feeds.add(self.general_feed)  # Always include general feed as fallback
        
        for feed_url in selected_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    if any(kw in entry.get("title", "").lower() or kw in entry.get("summary", "").lower() for kw in keywords):
                        urls.append(entry.link)
            except Exception as e:
                logger.warning(f"Error parsing RSS feed {feed_url}: {str(e)}")
        
        return list(dict.fromkeys(urls))  # Remove duplicates while preserving order

    def extract_with_newspaper(self, url):
        """Extract article metadata using newspaper3k."""
        entry = {"link": url, "source": "newspaper3k", "title": "No Title", "published": "Unknown", "summary": "No Summary"}
        try:
            article = Article(url, config=self.config)
            article.download()
            if article.download_state == 2:  # Successfully downloaded
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
        """Extract article metadata using trafilatura."""
        entry = {"link": url, "source": "trafilatura", "title": "No Title", "published": "Unknown", "summary": "No Summary"}
        try:
            downloaded = fetch_url(url)
            if downloaded:
                result = extract(downloaded)
                if result:
                    entry.update({
                        "title": result.get("title", "No Title"),
                        "published": result.get("date", "Unknown"),
                        "summary": result.get("description", "No Summary")[:200]  # Limit summary length
                    })
                    logger.info(f"Extracted with trafilatura: {entry['title']}")
        except Exception as e:
            logger.warning(f"trafilatura failed for {url}: {str(e)}")
        return entry

    def fetch_articles(self, query, project_name, max_articles=None):
        """Fetch blog article metadata based on a query and project name."""
        articles = []
        output_dir = os.path.join("data", project_name, "blog")
        os.makedirs(output_dir, exist_ok=True)

        # Get URLs from RSS feeds
        urls = self.fetch_from_rss(query)
        if not urls:
            logger.warning(f"No URLs found in RSS feeds for query '{query}'")
            return articles

        # Limit URLs if max_articles is provided
        if max_articles and max_articles < len(urls) * 2:  # *2 for two entries per URL
            urls = urls[:max_articles // 2]

        try:
            for idx, url in enumerate(urls):
                logger.info(f"Fetching article {idx + 1} from {url}")
                # Extract with newspaper3k
                newspaper_entry = self.extract_with_newspaper(url)
                articles.append(newspaper_entry)
                # Extract with trafilatura
                trafilatura_entry = self.extract_with_trafilatura(url)
                articles.append(trafilatura_entry)
                time.sleep(1)  # Rate limit to 1 request/second

            output_file = os.path.join(output_dir, f"blog_{query.replace(' ', '_')}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=4)
            logger.info(f"Saved {len(articles)} articles to {output_file}")

        except Exception as e:
            logger.error(f"Error in Blog fetcher: {str(e)}")

        return articles

if __name__ == "__main__":
    # Example usage with dummy query and project name (to be replaced by query processor)
    fetcher = BlogFetcher()
    fetcher.fetch_articles("machine learning in actuary", "test_project", max_articles=100)