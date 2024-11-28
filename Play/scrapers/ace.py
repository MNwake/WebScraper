from pprint import pprint
from typing import List

from playwright.async_api import async_playwright

from Play.base_scraper import BaseScraper
from Play.models.item import Product
from Play.proxies import ProxyManager
from Utility.utils import Websites


class AceScraper(BaseScraper):
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    ]

    async def run(self, **kwargs):
        async with async_playwright() as p:
            # Get proxy from ProxyManager
            proxy = self.proxy_manager.get_random_proxy(self.site)
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

                # Create browser context and page
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()

                # Navigate to the target URL
                await self.page.goto('https://www.acehardware.com/best-sales-and-specials/')

                # Continuously click "Load More Products" button until all products are loaded
                while True:
                    try:
                        load_more_button = await self.page.query_selector("#loadMoreBtn")
                        if load_more_button:
                            print("Clicking 'Load More Products' button...")
                            await load_more_button.click()
                            await self.random_sleep()  # Wait for the products to load
                        else:
                            print("No 'Load More Products' button found.")
                            break
                    except Exception as e:
                        print(f"Error clicking 'Load More Products' button: {e}")
                        break

                # Extract product information from the page
                product_info = await self.extract_product_info()
                print("Extracted Product Info:")
                pprint(product_info)
                print(f"Total products extracted: {len(product_info)}")

            except Exception as e:
                print(f"Error during scraping: {e}")
            finally:
                # Clean up resources
                await self.cleanup()

    async def extract_product_info(self) -> List[Product]:
        product_info = []
        products = await self.page.query_selector_all("li[data-mz-product]")
        for product in products:
            id = await product.get_attribute("data-mz-product")
            name = await product.get_attribute("data-item-name")
            original_price_element = await product.query_selector(".span-crossedout")
            discounted_price_element = await product.query_selector(".sales-price")
            product_url_element = await product.query_selector("a.mz-productlisting-title")
            image_url_element = await product.query_selector(".prim-img")
            department = await product.get_attribute("data-category-id")
            brand = name.split()[0] if name else None

            original_price = await original_price_element.inner_text() if original_price_element else None
            current_price = await discounted_price_element.inner_text() if discounted_price_element else None
            product_url = await product_url_element.get_attribute('href') if product_url_element else None
            image_url = await image_url_element.get_attribute('src') if image_url_element else None

            original_price = float(original_price.replace('$', '')) if original_price else None
            current_price = float(current_price.replace('$', '')) if current_price else None
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
                department=department,
                image_url=image_url,
                url=product_url
            ))
        return product_info


# Example usage:
proxy_manager = ProxyManager()  # You would need to implement or provide this
site = Websites.ACE  # Assuming you have an enumeration or similar for websites
scraper = AceScraper(proxy_manager, site)
scraper.start()
