import logging
import time
from urllib.parse import urljoin

import config
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BooksScraper(BaseScraper):
    source_name = config.BOOKS_SOURCE
    default_url = config.BOOKS_URL
    record_selector = "article.product_pod"

    def __init__(self, fetch_details=False, **kwargs):
        super().__init__(**kwargs)
        self.fetch_details = fetch_details

    def parse_record(self, element, page_url):
        link = element.select_one("h3 > a")
        price = element.select_one("p.price_color")
        rating = element.select_one("p.star-rating")

        book_url = None
        title = None
        if link is not None:
            if link.get("href"):
                book_url = urljoin(page_url, link["href"])
            title = link.get("title") or link.get_text()

        record = {
            "source": self.source_name,
            "source_url": book_url,
            "name": title,
            "price": price.get_text() if price else None,
            "rating": " ".join(rating.get("class", [])) if rating else None,
            "category": None,
            "description": None,
            "author": None,
            "tags": None,
        }

        if self.fetch_details and book_url:
            record.update(self.get_details(book_url))
        return record

    def get_details(self, book_url):
        soup = self.fetch(book_url)
        time.sleep(self.delay)
        if soup is None:
            return {}

        crumbs = soup.select("ul.breadcrumb li a")
        category = crumbs[2].get_text() if len(crumbs) > 2 else None

        heading = soup.select_one("#product_description")
        paragraph = heading.find_next_sibling("p") if heading else None
        description = paragraph.get_text() if paragraph else None

        return {"category": category, "description": description}
