from playwright.async_api import async_playwright

from Play.base_scraper import BaseScraper
from Play.proxies import ProxyManager
from Utility.utils import Websites


class SamsClubScraper(BaseScraper):
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    ]

    async def run(self, **kwargs):
        async with async_playwright() as p:
            proxy = self.proxy_manager.get_random_proxy(self.site)
            self.browser = await p.chromium.launch(
                headless=False)

            self.context = await self.browser.new_context(user_agent=self.USER_AGENTS[0])

            self.page = await self.context.new_page()

            await self.page.goto('https://www.samsclub.com')

            # Example of some interaction, you can add more as needed
            await self.page.wait_for_selector('i.sc-menu-icon-list-item-icon')
            await self.page.click('i.sc-menu-icon-list-item-icon')
            await self.random_sleep(min_seconds=10, max_seconds=20)

            # Cleanup
            await self.cleanup()

    async def cleanup(self):
        await self.page.close()
        await self.context.close()
        await self.browser.close()


# Example usage:
proxy_manager = ProxyManager()  # You would need to implement or provide this
site = Websites.SAMS_CLUB  # Replace with your actual site enumeration or identifier
scraper = SamsClubScraper(proxy_manager, site)
scraper.start()
