import config
from scrapers.base_scraper import BaseScraper


class QuotesScraper(BaseScraper):
    source_name = config.QUOTES_SOURCE
    default_url = config.QUOTES_URL
    record_selector = "div.quote"

    def parse_record(self, element, page_url):
        text = element.select_one("span.text")
        author = element.select_one("small.author")
        tags = [tag.get_text() for tag in element.select("a.tag")]

        return {
            "source": self.source_name,
            "source_url": page_url,
            "name": text.get_text() if text else None,
            "price": None,
            "rating": None,
            "category": None,
            "description": None,
            "author": author.get_text() if author else None,
            "tags": tags,
        }
