from urllib.parse import parse_qs, urlencode, urlparse

from playwright.async_api import Page
from scrapy.http import Response
from scrapy.utils.reactor import install_reactor

from ..utils import SpiderWithPlayRight

install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")


class Jumbo(SpiderWithPlayRight):
    start_urls = ["https://www.jumbo.cl/despensa"]

    async def parse(self, response: Response):
        self.logger.info(f"Parseando {response.url}")
        page: Page = response.meta["playwright_page"]

        # Esperamos que la página esté OK
        try:
            await page.wait_for_selector(".category-list-container", timeout=10_000)
        except Exception as e:
            self.logger.info(f"No se cargó la página {response.url}")
            return

        # Pasamos por todas las categorías
        categories = await page.query_selector_all(".category-list-container a.catalog-aside-nav-link")
        for category in categories:
            await category.scroll_into_view_if_needed()
            link = await category.get_attribute("href")
            yield response.follow(link, **self.make_request_kwargs(self.parse_category))

        await page.close()

    async def parse_category(self, response: Response):
        self.logger.info(f"Parseando {response.url}")
        page: Page = response.meta["playwright_page"]

        category = urlparse(response.url).path.rpartition("/")[-1]

        # Esperamos que la página esté OK
        try:
            await page.wait_for_selector(".shelf-content", timeout=10_000)
        except Exception as e:
            self.logger.info(f"No se cargó la página {response.url}")
            return

        # Obtenemos los productos de la página actual
        products = await page.query_selector_all(".shelf-product-island + :not(.no-stock)")
        for product in products:
            await product.scroll_into_view_if_needed()
            name_link_el = await product.query_selector("a.shelf-product-title")
            price_el = await product.query_selector(".product-sigle-price-wrapper, .price-best")
            brand_el = await product.query_selector(".shelf-product-brand")
            img_el = await product.query_selector("img")
            if name_link_el and price_el and brand_el:
                name = (await name_link_el.inner_text()).strip()
                link = await name_link_el.get_attribute("href")
                price = (await price_el.inner_text()).strip()
                brand = (await brand_el.inner_text()).strip()
                yield {
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "img": await img_el.get_attribute("src") if img_el else None,
                    "link": link,
                    "category": category,
                }

        # Obtenemos las páginas siguientes
        pagination_btn = await page.query_selector_all(".paginator-slider .page-number")
        current_url = urlparse(response.url)
        pagination_query = parse_qs(current_url.query)
        for i in range(len(pagination_btn)):
            pagination_query["page"] = [str(i + 1)]
            pagination_url = current_url._replace(query=urlencode(pagination_query, doseq=True))
            yield response.follow(pagination_url.geturl(), **self.make_request_kwargs(self.parse_category))

        await page.close()
