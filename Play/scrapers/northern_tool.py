from typing import List

from fake_useragent import UserAgent
from playwright.async_api import async_playwright

from Play.base_scraper import BaseScraper
from Play.proxies.proxies import ProxyManager
from Utility.utils import Websites
from model.item import Product


class NorthernToolScraper(BaseScraper):
    async def run(self, **kwargs):
        async with async_playwright() as p:
            proxy = self.proxy_manager.get_random_proxy(self.site)  # Get proxy from ProxyManager
            ua = UserAgent()

            try:
                # Launch browser with or without proxy
                if proxy:
                    print(f"Using proxy: {proxy.ip}:{proxy.port}")
                    self.browser = await p.chromium.launch(
                        proxy={'server': f'http://{proxy.ip}:{proxy.port}'},
                        headless=False
                    )
                else:
                    print("No proxy available, running without proxy.")
                    self.browser = await p.chromium.launch(headless=False)

                # Set up browser context and page
                screen_width, screen_height = 1920, 1080
                self.context = await self.browser.new_context(
                    user_agent=ua.chrome,
                    viewport={"width": screen_width, "height": screen_height}
                )
                self.page = await self.context.new_page()

                # Navigate to the target website
                await self.page.goto("https://www.northerntool.com/")

                # Intercept the network request if needed (uncomment and implement `handle_route` if applicable)
                # await self.page.route("**/search/resources/store/6970/productview/byCategory/3351*", self.handle_route)

                # Wait for some time to ensure all data is captured
                await self.random_sleep(min_seconds=10, max_seconds=20)

            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                # Clean up resources
                await self.cleanup()

    async def handle_route(self, route, request):
        response = await route.continue_()
        if "search/resources/store/6970/productview/byCategory/3351" in request.url:
            data = await response.json()
            products = data.get("catalogEntryView", [])
            product_info = self.extract_product_info(products)
            for product in product_info:
                print(product)

    def extract_product_info(self, products) -> List[Product]:
        product_info = []
        for product in products:
            try:
                id = product.get("uniqueID")
                name = product.get("name")
                brand = product.get("manufacturer")
                original_price = None
                current_price = None

                # Extracting prices
                for price in product.get("price", []):
                    if price.get("usage") == "Display":
                        original_price = float(price.get("value"))
                    elif price.get("usage") == "Offer":
                        current_price = float(price.get("value"))

                dollar_off = original_price - current_price if original_price and current_price else 0.0
                percentage_off = (dollar_off / original_price * 100) if original_price and dollar_off else 0.0

                product_info.append(Product(
                    id=id,
                    website=self.site,
                    brand=brand,
                    name=name,
                    original_price=original_price,
                    current_price=current_price,
                    dollar_off=dollar_off,
                    percentage_off=percentage_off,
                    department="Deals",
                    image_url=product.get("fullImage"),
                    url=f"https://www.northerntool.com{product.get('seo', {}).get('href')}"
                ))
            except Exception as e:
                print(f"Error extracting product information: {e}")
        return product_info


# Example usage:
proxy_manager = ProxyManager()  # You would need to implement or provide this
site = Websites.NORTHERN_TOOL  # Assuming you have an enumeration or similar for websites
scraper = NorthernToolScraper(proxy_manager, site)
scraper.start()
