import asyncio
import random
from random import uniform

from playwright.async_api import Browser, BrowserContext, Page

from scraping.exceptions import UserStoppedScraper
from scraping.proxies.proxies import Websites, ProxyManager
from utility.utils import ProxyError


#
# class ScraperManager:
#     def __init__(self, max_workers=10):
#         self.executor = ThreadPoolExecutor(max_workers=max_workers)
#         self.loop = asyncio.new_event_loop()
#         threading.Thread(target=self._start_loop, daemon=True).start()
#
#     def _start_loop(self):
#         asyncio.set_event_loop(self.loop)
#         self.loop.run_forever()
#
#     async def start_scraper(self, scraper):
#         await scraper.run()
#
#     def run_task(self, coro):
#         asyncio.run_coroutine_threadsafe(coro, self.loop)
#
#     def stop(self):
#         self.executor.shutdown(wait=False)


class BaseScraper:
    def __init__(self, proxy_manager: ProxyManager, site: Websites, status_callback=None, product_callback=None):
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None

        self.proxy_manager = proxy_manager
        self.site = site

        self.thread = None
        self.loop = None
        self.is_running = False

        self.status_callback = status_callback
        self.product_callback = product_callback

        self.exit_sites = [
            "https://www.google.com",
            "https://www.facebook.com",
            "https://www.youtube.com",
            "https://www.amazon.com",
            "https://www.wikipedia.org",
            "https://www.twitter.com",
            "https://www.instagram.com",
            "https://www.linkedin.com",
            "https://www.netflix.com",
            "https://www.reddit.com"
        ]

    def start(self):
        self.is_running = True
        if self.status_callback:
            self.status_callback(self.is_running)
        self.run_async()

    def run_async(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.run())
        except UserStoppedScraper:
            print("User manually stopped the scraper.")
        except ProxyError as e:
            print(f"Proxy error occurred: {e}")
            self.stop()
            raise e
        except Exception as e:
            print(f"An error occurred: {e}")
            self.stop()
            raise e
        finally:
            print("Running cleanup.")
            self.loop.run_until_complete(self.cleanup())
            self.loop.close()
            self.is_running = False
            if self.status_callback:
                self.status_callback(self.is_running)

    async def run(self, **kwargs):
        print("Base run method. Should be overridden by subclass.")
        raise NotImplementedError

    async def click_element_by_testid(self, testid: str, hover: bool = False):
        try:
            await self.page.wait_for_selector(f"[data-testid='{testid}']", state='visible', timeout=5000)
            await self.random_sleep()
            element = await self.page.query_selector(f"[data-testid='{testid}']")
            if hover:
                await element.hover()
            await element.click()
        except Exception as e:
            print(f"Error clicking element with data-testid '{testid}': {e}")

    def stop(self):
        print("Stopping scraper.")
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join()
        self.is_running = False
        if self.status_callback:
            self.status_callback(self.is_running)

    async def random_sleep(self, min_seconds: float = 1.0, max_seconds: float = 3.0, steps: int = 3):
        # Wait for the page to finish loading
        await self.page.wait_for_load_state('load')
        sleep_duration = uniform(min_seconds, max_seconds)

        action = random.choice(["mouse_move", "random_mouse_move", "nothing"])

        interval = sleep_duration / steps
        for _ in range(steps):
            if action == "mouse_move":
                start_x = random.uniform(0, self.page.viewport_size['width'])
                start_y = random.uniform(0, self.page.viewport_size['height'])
                end_x = random.uniform(0, self.page.viewport_size['width'])
                end_y = random.uniform(0, self.page.viewport_size['height'])
                await self.human_like_mouse_move(start_x, start_y, end_x, end_y)
            elif action == "random_mouse_move":
                await self.move_mouse_randomly(duration=interval)

            await asyncio.sleep(interval)

    async def cleanup(self):
        if self.browser:
            await self.browser.close()

    async def human_like_mouse_move(self, start_x, start_y, end_x, end_y, steps=100):
        x_diff = end_x - start_x
        y_diff = end_y - start_y

        for i in range(steps):
            x = start_x + (x_diff * i / steps) + random.uniform(-1, 1)
            y = start_y + (y_diff * i / steps) + random.uniform(-1, 1)
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))  # Small delay to simulate human movement

    async def human_like_typing(self, selector, text, delay=0.1):
        for char in text:
            await self.page.fill(selector,
                                 await self.page.evaluate(f'document.querySelector("{selector}").value + "{char}"'))
            await asyncio.sleep(delay + random.uniform(-delay / 2, delay / 2))

    async def move_mouse_randomly(self, duration: float, steps: int = 1):
        for _ in range(steps):
            x = random.randint(0, await self.page.evaluate("() => window.innerWidth"))
            y = random.randint(0, await self.page.evaluate("() => window.innerHeight"))
            await self.page.mouse.move(x, y)
            await asyncio.sleep(duration / steps)

    async def scroll_random_amount(self, direction="down"):
        scroll_amount = random.randint(50, 150)  # Adjust the range as needed
        if direction == "down":
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount});")
        elif direction == "up":
            await self.page.evaluate(f"window.scrollBy(0, -{scroll_amount});")

    async def scroll_up_down(self):
        for _ in range(2):  # Scroll up and down twice
            scroll_amount = random.randint(50, 150)  # Adjust the range as needed
            # Scroll down
            await self.scroll_random_amount("down")
            await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay to simulate human behavior
            # Scroll up
            await self.scroll_random_amount("up")
            await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay to simulate human behavior

    async def slow_scroll(self):
        for _ in range(10):
            await self.page.mouse.wheel(0, 500)
            await asyncio.sleep(.25)
        await self.page.evaluate('window.scrollTo(0, 0);')

    async def go_to_home_site(self, proxy):
        try:
            await self.page.goto(self.site.base_url)
        except Exception as e:
            print(f"Error navigating to Home Depot base URL: {e}")
            proxy.alert = True
            self.proxy_manager.save_proxies()
            raise ProxyError("Bad proxy detected.")
