import requests

from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

BOOKS_PAGE_1 = """
<html><body>
<article class="product_pod">
  <p class="star-rating Three"></p>
  <h3><a href="catalogue/book-one_1/index.html" title="Book One Full Title">Book One F...</a></h3>
  <p class="price_color">\u00c2\u00a351.77</p>
</article>
<article class="product_pod">
  <h3><a href="catalogue/book-two_2/index.html" title="Book Two">Book Two</a></h3>
</article>
<ul class="pager"><li class="next"><a href="catalogue/page-2.html">next</a></li></ul>
</body></html>
"""

BOOKS_PAGE_2 = """
<html><body>
<article class="product_pod">
  <p class="star-rating Five"></p>
  <h3><a href="book-three_3/index.html" title="Book Three">Book Three</a></h3>
  <p class="price_color">\u00a310.00</p>
</article>
</body></html>
"""

QUOTES_PAGE = """
<html><body>
<div class="quote">
  <span class="text">\u201cA quote.\u201d</span>
  <span>by <small class="author">Someone</small></span>
  <div class="tags"><a class="tag">life</a><a class="tag">love</a></div>
</div>
<div class="quote">
  <small class="author">No Text Author</small>
</div>
</body></html>
"""


class FakeResponse:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status
        self.encoding = None

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, pages):
        self.pages = pages
        self.requested = []

    def get(self, url, timeout=None):
        self.requested.append(url)
        if url not in self.pages:
            raise requests.ConnectionError("no such page")
        return self.pages[url]


def test_books_pagination_follows_next_link():
    pages = {
        "https://books.toscrape.com/": FakeResponse(BOOKS_PAGE_1),
        "https://books.toscrape.com/catalogue/page-2.html": FakeResponse(BOOKS_PAGE_2),
    }
    session = FakeSession(pages)
    scraper = BooksScraper(session=session, delay=0)
    records = scraper.scrape()

    assert len(session.requested) == 2
    assert len(records) == 3
    assert records[0]["name"] == "Book One Full Title"
    assert records[0]["source_url"] == "https://books.toscrape.com/catalogue/book-one_1/index.html"
    assert records[2]["source_url"] == "https://books.toscrape.com/catalogue/book-three_3/index.html"


def test_missing_elements_do_not_crash():
    pages = {"https://books.toscrape.com/": FakeResponse(BOOKS_PAGE_1)}
    records = BooksScraper(session=FakeSession(pages), delay=0, max_pages=1).scrape()
    assert records[1]["price"] is None
    assert records[1]["rating"] is None


def test_failed_page_stops_source_but_keeps_earlier_records():
    pages = {"https://books.toscrape.com/": FakeResponse(BOOKS_PAGE_1)}
    records = BooksScraper(session=FakeSession(pages), delay=0).scrape()
    assert len(records) == 2


def test_http_error_returns_no_records():
    pages = {"https://quotes.toscrape.com/": FakeResponse("", status=500)}
    records = QuotesScraper(session=FakeSession(pages), delay=0).scrape()
    assert records == []


def test_quotes_parsing():
    pages = {"https://quotes.toscrape.com/": FakeResponse(QUOTES_PAGE)}
    records = QuotesScraper(session=FakeSession(pages), delay=0).scrape()
    assert len(records) == 2
    assert records[0]["author"] == "Someone"
    assert records[0]["tags"] == ["life", "love"]
    assert records[0]["source_url"] == "https://quotes.toscrape.com/"
    assert records[1]["name"] is None
