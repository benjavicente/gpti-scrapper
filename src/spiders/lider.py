from urllib.parse import parse_qs, urlencode, urlparse

from playwright.async_api import Page
from scrapy.http import Response
from scrapy.utils.reactor import install_reactor

from ..utils import SpiderWithPlayRight

install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")


class Lider(SpiderWithPlayRight):
    start_urls = ["https://www.lider.cl/supermercado/category/Despensa/Pastas_y_Salsas?page=1&hitsPerPage=100"]

    async def parse(self, response: Response):
        self.logger.info(f"Parseando {response.url}")
        page: Page = response.meta["playwright_page"]
        category = urlparse(response.url).path.rpartition("/")[-1]

        # Esperamos que la página esté OK
        try:
            await page.wait_for_selector(".ais-Hits-list", timeout=10_000)
        except Exception as e:
            self.logger.info(f"No se cargó la página {response.url}")
            # self.logger.info(e)
            # with open(f"dump/{category}.html", "w") as f:
            #     f.write(await page.content())
            # await page.screenshot(path=f"img/{category}.png", full_page=True)
            return

        # Obtenemos los productos de la página actual
        products = await page.query_selector_all(".ais-Hits-item")

        for product in products:
            await product.scroll_into_view_if_needed()
            price_el = await product.query_selector("div.product-card__sale-price")
            brand_el, name_el = await product.query_selector_all("div.product-card_description-wrapper span")
            img_el = await product.query_selector("img")
            link_el = await product.query_selector("a")
            yield {
                "name": (await name_el.inner_text()).strip(),
                "brand": (await brand_el.inner_text()).strip(),
                "price": (await price_el.inner_text()).strip() if price_el else None,
                "img": await img_el.get_attribute("src") if img_el else None,
                "link": await link_el.get_attribute("href") if link_el else None,
                "category": category,
            }

        # Obtenemos que páginas hay disponibles para la categoría actual
        pagination_btns = await page.query_selector_all(".ais-Pagination-list .ais-Pagination-item--page")
        current_url = urlparse(response.url)
        pagination_query = parse_qs(current_url.query)
        for i in range(1, len(pagination_btns)):
            pagination_query["page"] = [str(i + 1)]
            url = current_url._replace(query=urlencode(pagination_query, doseq=True))
            yield response.follow(url.geturl(), **self.make_request_kwargs())

        # Vemos si nos falta una categoría
        categories = await page.query_selector_all("a.sister-categories")
        for category in categories:
            href = await category.get_attribute("href")
            new_url = urlparse(href)._replace(query=urlencode(pagination_query, doseq=True))
            yield response.follow(new_url.geturl(), **self.make_request_kwargs())

        await page.close()
