import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import config

logger = logging.getLogger(__name__)


def create_session():
    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    retries = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class BaseScraper:
    source_name = ""
    default_url = ""
    record_selector = ""

    def __init__(self, start_url=None, session=None, delay=config.REQUEST_DELAY, max_pages=None):
        self.start_url = start_url or self.default_url
        self.session = session or create_session()
        self.delay = delay
        self.max_pages = max_pages

    def fetch(self, url):
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            response.encoding = "utf-8"
        except requests.RequestException as error:
            logger.error("Failed to fetch %s: %s", url, error)
            return None
        return BeautifulSoup(response.text, "lxml")

    def parse_record(self, element, page_url):
        raise NotImplementedError

    def find_next_url(self, soup, page_url):
        next_link = soup.select_one("li.next > a")
        if next_link is None or not next_link.get("href"):
            return None
        return urljoin(page_url, next_link["href"])

    def scrape(self):
        records = []
        url = self.start_url
        page = 1

        while url:
            if self.max_pages and page > self.max_pages:
                logger.info("%s: reached page limit of %d", self.source_name, self.max_pages)
                break

            logger.info("%s | page %d | %s", self.source_name, page, url)
            soup = self.fetch(url)
            if soup is None:
                logger.error("%s: stopping at page %d because it could not be loaded", self.source_name, page)
                break

            for element in soup.select(self.record_selector):
                try:
                    record = self.parse_record(element, url)
                except Exception:
                    logger.exception("%s: could not parse a record on %s", self.source_name, url)
                    continue
                if record:
                    records.append(record)

            url = self.find_next_url(soup, url)
            page += 1
            time.sleep(self.delay)

        logger.info("%s: collected %d raw records", self.source_name, len(records))
        return records
