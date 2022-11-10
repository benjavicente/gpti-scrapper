import uuid
from abc import ABC, abstractmethod

from playwright.async_api import Page
from playwright.async_api import Request as PlaywrightRequest
from scrapy import Spider
from scrapy.http import Request as ScrapyRequest


def abort_conditions(req: PlaywrightRequest):
    yield req.resource_type == "image"
    yield req.url.startswith("https://www.google.com/pagead")
    yield req.url.startswith("https://sb.scorecardresearch.com")
    yield req.url.startswith("https://analytics.google.com/g/collect")
    yield req.url.startswith("https://analytics.tiktok.com")
    yield "fls.doubleclick.net/" in req.url
    yield req.url.startswith("https://www.facebook.com/tr/")
    yield req.url.startswith("https://www.youtube.com/embed/")
    yield req.url.startswith("https://bam.nr-data.net")
    yield req.url.startswith("https://webchat.keepcon.com")
    yield req.url.startswith("https://firebaselogging-pa.googleapis.com/v1")
    yield req.url.startswith("https://sp.vtex.com/event-api")


def should_abort_request(req: PlaywrightRequest):
    "Función que detecta si una petición debe ser abortada"
    return any(abort_conditions(req))


def yield_requests(urls: list[str]):
    "Función que inicializa las requests"


class SpiderWithPlayRight(ABC, Spider):
    "Clase básica para crear spiders con playwright"
    start_urls: list[str] = []

    def __init_subclass__(cls) -> None:
        cls.name = cls.__name__.lower()

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"Starting with {url}")
            yield ScrapyRequest(url, **self.make_request_kwargs())

    def make_request_kwargs(self, callback=None):
        return dict(
            callback=callback or self.parse,
            errback=self._error_callback,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_init_callback": self.init_page,
            },
        )

    async def init_page(self, page: Page, request: ScrapyRequest):
        pass

    async def _error_callback(self, failure):
        page: Page = failure.request.meta["playwright_page"]
        await page.close()
