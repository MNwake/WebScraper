import asyncio
import base64
import os
import uuid
from io import BytesIO

import pytesseract
from PIL import Image
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, BrowserContext

from Play.base_scraper import BaseScraper
from Play.models.amazon import AmazonItem
from Play.proxies import ProxyManager
from Utility.utils import Websites, google_search


class AmazonScraper(BaseScraper):

    def __init__(self, proxy_manager: ProxyManager, status_callback=None, product_callback=None):
        super().__init__(proxy_manager, Websites.AMAZON, status_callback, product_callback)
        self.context: BrowserContext = None
        self.browser = None
        self.page = None

    async def take_screenshot(self, page, folder_path='screenshots', unique_id=None, attempts=3):
        # Create the folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)

        # Generate a unique ID if not provided
        if unique_id is None:
            unique_id = str(uuid.uuid4())

        file_path = os.path.join(folder_path, f'screenshot_{unique_id}.png')

        for attempt in range(attempts):
            try:
                screenshot_buffer = await page.screenshot(full_page=True, timeout=30000)

                # Save the screenshot buffer to a file
                with open(file_path, 'wb') as f:
                    f.write(screenshot_buffer)

                base64_image = base64.b64encode(screenshot_buffer).decode('utf-8')
                return base64_image, file_path
            except Exception as e:
                if attempt < attempts - 1:
                    print(f"Screenshot failed, retrying... Attempt {attempt + 1} of {attempts}")
                    await asyncio.sleep(5)
                else:
                    print(f"Failed to take screenshot after {attempts} attempts.")
                    raise e

    async def run(self, search_query):
        self.is_running = True
        first_item_link = google_search(search_query)
        if not first_item_link:
            return None, None

        ua = UserAgent()
        proxy = self.proxy_manager.get_random_proxy(self.site)  # Get proxy from ProxyManager

        try:
            async with async_playwright() as p:
                # Launch browser with or without proxy
                if proxy:
                    print(f"Using proxy: {proxy.ip}:{proxy.port}")
                    self.browser = await p.chromium.launch(
                        proxy={'server': f'http://{proxy.ip}:{proxy.port}'},
                        headless=True
                    )
                else:
                    print("No proxy available, running without proxy.")
                    self.browser = await p.chromium.launch(headless=True)

                # Set up browser context with user agent
                self.context = await self.browser.new_context(user_agent=ua.chrome)

                # Create a new page and navigate to the first item link
                self.page = await self.context.new_page()
                await self.page.goto(first_item_link, wait_until='domcontentloaded')

                # Attempt to extract the price
                price = None
                try:
                    price_str = await self.extract_price()
                    if price_str:
                        price = float(price_str.replace(',', ''))  # Convert price string to float
                except Exception as e:
                    print(f"Failed to extract price: {e}")

                # If price extraction fails, take a screenshot
                image = None
                if price is None:
                    await self.slow_scroll()
                    await self.random_sleep()
                    image = await self.take_screenshot(self.page)

                # Return the extracted information
                item = AmazonItem(url=first_item_link, price=price)
                return image, item

        except Exception as e:
            print(f"An error occurred during setup or navigation: {e}")
            return None, None
        finally:
            # Clean up resources
            await self.cleanup()

    async def extract_price(self):
        # List of selectors to try for extracting the price
        price_selectors = [
            '#corePriceDisplay_mobile_feature_div .a-price .a-price-whole',
            '#corePriceDisplay_desktop_feature_div .a-price .a-price-whole',
            '#corePrice_feature_div .a-price .a-price-whole'
        ]
        price = None
        for selector in price_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=3000)
                price_whole = await self.page.locator(selector).first.text_content()
                if price_whole:
                    price_fraction = await self.page.locator(f'{selector} ~ .a-price-fraction').first.text_content()
                    price = f"{price_whole}{price_fraction}"
                    break
            except Exception as e:
                print(f"Failed to extract price using selector {selector}: {e}")
        return price

    async def submit_captcha(self):
        try:
            captcha_image = await self.page.locator("form img").screenshot()
            captcha_text = self.solve_captcha(captcha_image)
            await self.random_sleep()

            await self.page.get_by_placeholder("Type characters").click()
            await self.random_sleep()
            await self.page.get_by_placeholder("Type characters").fill(captcha_text)
            await self.random_sleep()
            await self.page.get_by_role("button", name="Continue shopping").click()
            await self.random_sleep()
        except Exception as e:
            print(f"Error submitting captcha: {e}")

    def solve_captcha(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(BytesIO(image_bytes))
            captcha_text = pytesseract.image_to_string(image)
            return captcha_text.strip()
        except Exception as e:
            print(f"Error solving captcha: {e}")
            return ""

    async def cleanup(self):
        if self.browser:
            await self.browser.close()
            print("Browser closed.")


if __name__ == "__main__":
    async def main():
        proxy_manager = ProxyManager()
        amazon_scraper = AmazonScraper(proxy_manager)
        search_query = "vevor fire pit grate 24 in. dia heavy-duty iron round firewood grate with 7 detachable round legs for backyard, black"
        missing_query = 'Chimney Cap 13"x18" Stainless Steel Fireplace Chimney Cover for Outside Existing Clay Flue Tile'
        await amazon_scraper.run(missing_query)
        await amazon_scraper.cleanup()


    asyncio.run(main())
