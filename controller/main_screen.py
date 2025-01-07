import asyncio
import threading
from collections import deque

from uszipcode import SearchEngine

from controller.chatgpt_controller import ChatGPTController
from model.item import Product
from model.main_screen import MainScreenModel
from scraping.proxies.proxies import ProxyManager
from scraping.scrapers.amazon import AmazonScraper
from scraping.scrapers.home_depot import HomeDepotScraper
from view.main_screen.main_screen import MainScreenView


class MainScreenController:
    def __init__(self, model):
        self.model: MainScreenModel = model  # Assuming model.main_screen.MainScreenModel
        self.view = MainScreenView(controller=self, model=self.model)
        self.search_engine = SearchEngine()
        self.chatgpt = ChatGPTController()
        self.proxy_manager = ProxyManager(metrics_callback=self.update_proxy_metrics)
        # self.scraper_manager = ScraperManager()
        self.product_queue = deque()  # Queue to manage products to be scraped
        self.scraping = False  # Flag to indicate if scraping is in progress

        self.hd_scraper = HomeDepotScraper(proxy_manager=self.proxy_manager,
                                           status_callback=self.update_running_status,
                                           product_callback=self.new_product_found)
        self.amazon_scraper = AmazonScraper(proxy_manager=self.proxy_manager,
                                            status_callback=self.update_running_status)

        self.amazon_thread = None  # Keep track of the Amazon scraper thread

    def get_view(self) -> MainScreenView:
        return self.view

    def start_scrapers(self):
        hd_thread = threading.Thread(target=self.run_hd_scraper)
        hd_thread.start()
        self.model.is_running = True

    def run_hd_scraper(self):
        print('Running Scrapers')
        asyncio.run(self.hd_scraper.start())

    async def process_amazon_scraper(self, product: Product):
        print(f'Processing: {product.search_query}')
        image, item = await self.amazon_scraper.run(product.search_query)
        if not image or not item:
            print("Error: Amazon scraper did not return valid image or item.")
            product.amazon = item
            self.model.add_product(product)
            return

        if image:
            match = await self.chatgpt.get_product_info(product.search_query, image)

            if match:
                try:
                    price = match.get("price", "N/A")
                    if price != "N/A" and price.replace("$", "").replace(".", "").isdigit():
                        item.price = float(price.replace("$", ""))
                    else:
                        item.price = None  # Set a default or error value
                    item.match = match.get("match", "0%")
                    product.amazon = item
                except ValueError as e:
                    print(f"Error converting price to float: {e}")
                    item.price = None  # Set a default or error value
            else:
                print("No match found from ChatGPT.")
                item.price = None  # Set a default or error value

            product.amazon = item
            self.model.add_product(product)

        await self.amazon_scraper.cleanup()

    async def run_amazon_scraper(self):
        while True:
            if self.product_queue and not self.scraping:
                self.scraping = True
                product = self.product_queue.popleft()
                await self.process_amazon_scraper(product)
                self.scraping = False
                print(f'Completed Item, {len(self.product_queue)} remaining')
            else:
                await asyncio.sleep(1)  # Await asyncio.sleep to avoid busy-waiting

            if not self.product_queue:
                print("Queue is empty, stopping Amazon scraper.")
                self.amazon_scraper.is_running = False
                break

    def manage_amazon_scraper(self):
        if self.product_queue and not self.amazon_scraper.is_running:
            self.amazon_scraper.is_running = True
            self.amazon_thread = threading.Thread(target=self.run_amazon_scraper_loop)
            self.amazon_thread.start()
        elif not self.product_queue and self.amazon_scraper.is_running:
            self.amazon_scraper.is_running = False
            if self.amazon_thread:
                self.amazon_thread.join()  # Ensure the thread has finished

    def run_amazon_scraper_loop(self):
        asyncio.run(self.run_amazon_scraper())

    def new_product_found(self, product: Product):
        if not self.is_product_in_model(product):
            self.product_queue.append(product)
            print(f'New product added to queue: {len(self.product_queue)}')
            self.manage_amazon_scraper()

    def is_product_in_model(self, product: Product) -> bool:
        # Check if the product is already in the archived products list
        for archived_product in self.model.archived_products:
            if archived_product.id == product.id:
                return True

        # Check if the product is already in the current products list
        for existing_product in self.model.products:
            if existing_product.id == product.id:
                return True

        return False

    def stop_scraper(self):
        print('Stopping scrapers.')
        self.hd_scraper.stop()
        # self.scraper_manager.stop()
        self.amazon_scraper.is_running = False
        self.hd_scraper.is_running = False
        self.model.is_running = False

    def update_running_status(self, is_running):
        self.model.running = is_running

    def update_zip_code(self, instance, text):
        # Remove non-numerical characters
        cleaned_text = ''.join(filter(str.isdigit, text))
        instance.text = cleaned_text

        if len(cleaned_text) > 5:
            cleaned_text = cleaned_text[:5]
            instance.text = cleaned_text
            return
        # Limit to 5 characters

        # If the text length is less than 5, just update the text field and return
        if len(cleaned_text) < 5:
            instance.text = cleaned_text
            return

        # Verify the ZIP code using uszipcode if it is exactly 5 characters

        zipcode = self.search_engine.by_zipcode(cleaned_text)

        if zipcode and zipcode.zipcode:
            self.model.zip_code = cleaned_text
            self.hd_scraper.set_zip_code(cleaned_text)
            instance.error = False  # Clear any existing error
        else:
            print("Invalid ZIP code")
            self.model.zip_code = ''
            instance.error = True  # Set error state for the text field

    def refresh_proxy_list(self):
        async def run_refresh():
            self.model.is_refreshing = True
            await self.proxy_manager.refresh_proxy_list()
            self.model.is_refreshing = False

        def thread_refresh():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_refresh())
            loop.close()

        refresh_thread = threading.Thread(target=thread_refresh)
        refresh_thread.start()

    def update_proxy_metrics(self, metrics):
        self.model.proxy_metrics = metrics

    def alert_user(self):
        pass
