import json
import os
import random
from enum import Enum
from pprint import pprint
from typing import List, Dict
from urllib.parse import urljoin

from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from pydantic import ValidationError

from model.home_depot import HomeDepotItem
from model.item import Product
from scraping.base_scraper import BaseScraper
from scraping.proxies.proxies import Websites, ProxyManager


class SortByOption(Enum):
    MOST_POPULAR = ("Most Popular", "?sortorder=asc&sortby=mostpopular")
    PRICE_LOW_TO_HIGH = ("Price Low to High", "?sortorder=asc&sortby=price")
    PRICE_HIGH_TO_LOW = ("Price High to Low", "?sortorder=desc&sortby=price")
    TOP_RATED_PRODUCTS = ("Top Rated Products", "?sortorder=asc&sortby=toprated")
    WORST_SELLERS = ("Worst Sellers", "?sortorder=desc&sortby=topsellers")
    LOWEST_RATED_PRODUCTS = ("Lowest Rated Products", "?sortorder=desc&sortby=toprated")

    def __new__(cls, display_text, sort_url):
        member = object.__new__(cls)
        member._value_ = sort_url
        member.display_text = display_text
        member.sort_url = sort_url
        return member


class HomeDepotScraper(BaseScraper):
    products_scraped: int = 0
    required_discount_percentage: float = 0.35
    zip_code: str = '33823'
    zip_code_changed: bool = False
    is_running: bool = True
    departments: List[Dict[str, str]] = []

    zip_codes = ['33859', '33805', '33813', '34758', '34741', '34769', '32837', '33511', '33545']
    scrape_page_url = "https://www.homedepot.com/b/{department}/{specials}/N-{reference}"

    specials = [
        "Special-Buys",
        # "New-Lower-Prices/Special-Values",
        # "Clearance/Special-Values",
        # "Temporary-Price-Reduction/Special-Values"
    ]

    def __init__(self, proxy_manager: ProxyManager, status_callback=None, product_callback=None,
                 departments_file: str = 'departments.json'):
        super().__init__(proxy_manager, Websites.HOME_DEPOT, status_callback, product_callback)
        self.departments = self.load_departments_from_json(departments_file)
        if not self.departments:
            print("No departments loaded from JSON file. Please ensure the file is correct and try again.")

    def load_departments_from_json(self, file_path: str) -> List[Dict[str, str]]:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    departments = json.load(file)
                print(f"Departments loaded from {file_path}")
                return departments
            else:
                print(f"File {file_path} not found.")
                return []
        except Exception as e:
            print(f"Error loading departments from JSON: {e}")
            return []

    async def run(self):
        self.is_running = True
        if not self.departments:
            await self.get_departments()
        random.shuffle(self.departments)

        while self.is_running:
            for zip_code in self.zip_codes:
                print(f"Processing zip code: {zip_code}")
                for department in self.departments:
                    department_name = department['name'].replace(" ", "-")
                    print(f"Processing department: {department_name} in zip code: {zip_code}")
                    for special in self.specials:
                        proxy = self.proxy_manager.get_random_proxy(self.site)
                        ua = UserAgent()

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

                                # Set up browser context and page
                                screen_width, screen_height = 1920, 1080
                                self.context = await self.browser.new_context(
                                    user_agent=ua.chrome,
                                    viewport={"width": screen_width, "height": screen_height}
                                )
                                self.page = await self.context.new_page()

                                # Navigate to home site and handle scraping logic
                                if proxy:
                                    await self.go_to_home_site(proxy)
                                else:
                                    await self.page.goto(self.site.base_url)

                                self.page.on("response", self.handle_response)
                                await self.random_sleep()

                                if zip_code:
                                    await self.change_zip_code(zip_code)
                                    self.zip_code_changed = False
                                    await self.random_sleep()

                                # Navigate to the department URL
                                await self.navigate_to_category(department['href'])
                                await self.random_sleep()

                                # Extract the "/N-..." part of the URL
                                current_url = self.page.url
                                reference = current_url.split('/N-')[1]

                                # Construct the URL for the discount category
                                discount_url = self.scrape_page_url.format(
                                    department=department_name,
                                    specials=special,
                                    reference=reference
                                )
                                await self.navigate_to_category(discount_url)
                                await self.random_sleep()

                                # Scrape products and check if all products are loaded
                                await self.scrape_products()
                                await self.random_sleep()

                                # Close resources
                                await self.close_page_and_browser()

                        except Exception as e:
                            print(f"An error occurred: {e}")
                            await self.close_page_and_browser()

                    print(f"Finished processing department: {department_name} for zip code: {zip_code}")
                print(f"Finished processing zip code: {zip_code}")

    async def get_departments(self):
        max_retries = 3
        retries = 0
        while retries < max_retries:
            proxy = self.proxy_manager.get_random_proxy(Websites.HOME_DEPOT)
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(proxy={'server': f'http://{proxy.ip}:{proxy.port}'},
                                                      headless=True)
                    context = await browser.new_context()
                    page = await context.new_page()
                    await page.goto("https://www.homedepot.com/")

                    await page.wait_for_selector("[data-testid='header-button-Shop All']", state='visible',
                                                 timeout=10000)
                    await page.get_by_test_id("header-button-Shop All").click()

                    await page.wait_for_selector("[data-testid='menu-item-id-7dXOWs1aPY2W48fWUYKp0n']", state='visible',
                                                 timeout=10000)
                    await page.get_by_test_id("menu-item-id-7dXOWs1aPY2W48fWUYKp0n").click()

                    await page.wait_for_selector("[data-testid='menu-item-id-20jIcDk4HKzFw8Nvl6SZTw']", state='visible',
                                                 timeout=10000)
                    await page.get_by_test_id("menu-item-id-20jIcDk4HKzFw8Nvl6SZTw").click()

                    await page.wait_for_selector("ul.-sui-pt-2[role='menu']", state='visible', timeout=10000)
                    menu_items = await page.query_selector_all("ul.-sui-pt-2[role='menu'] > a")

                    departments = []
                    for item in menu_items:
                        department_name = await item.inner_text()
                        department_href = await item.get_attribute("href")
                        if department_name and department_href:
                            departments.append({
                                'name': department_name,
                                'href': department_href
                            })

                    random.shuffle(departments)
                    self.departments = departments

                    # Save departments to a JSON file
                    self.save_departments_to_json(departments)
                    break  # Exit the loop once departments are successfully fetched
            except Exception as e:
                print(f"Error getting departments: {e}")
                retries += 1
                if retries >= max_retries:
                    print("Max retries reached. Failed to get departments.")
                    break  # Exit the loop if max retries are reached
                await self.close_page_and_browser()

    def save_departments_to_json(self, departments: List[Dict[str, str]], file_path: str = 'departments.json'):
        try:
            with open(file_path, 'w') as file:
                json.dump(departments, file, indent=4)
            print(f"Departments saved to {file_path}")
        except Exception as e:
            print(f"Error saving departments to JSON: {e}")

    async def navigate_to_category(self, category_url):
        try:
            if not category_url.startswith("http"):
                category_url = Websites.HOME_DEPOT.base_url + category_url
            await self.page.goto(category_url)
            await self.page.wait_for_load_state('load')
        except Exception as e:
            print(f"Error navigating to category: {e}")

    async def scrape_products(self) -> None:
        try:
            # Check if all products are loaded
            await self.paginate_randomly()
            for sort_option in SortByOption:
                print('Now sorting:', sort_option)
                await self.sort_by(sort_option)
                await self.random_sleep()
                await self.paginate_randomly()
                await self.random_sleep()

        except Exception as e:
            print(f"An error occurred during scraping: {e}")

    async def check_all_products_loaded(self) -> bool:
        try:
            element = await self.page.query_selector("div.results-pagination__counts")
            if element:
                text_content = await element.inner_text()
                if "of" in text_content:
                    total_products = int(text_content.split("of")[1].strip().split(" ")[0])
                    current_range = text_content.split("of")[0].strip().split(" ")[-1]
                    start, end = map(int, current_range.split("-"))
                    if end == total_products:
                        return True
            else:
                # If the element is not found, assume it's the last page
                return True
            return False
        except Exception as e:
            print(f"Error checking if all products are loaded: {e}")
            return True  # Assume it's the last page if an error occurs

    async def paginate_randomly(self):
        pages_to_scrape = random.randint(5, 10)
        current_page = 0
        while current_page < pages_to_scrape:
            try:
                await self.page.wait_for_selector('a.hd-pagination__link[aria-label="Next"]', timeout=2000)
                next_button = await self.page.query_selector('a.hd-pagination__link[aria-label="Next"]')

                if next_button:
                    await self.scroll_random_amount()
                    await next_button.click()
                    await self.page.wait_for_load_state('load')
                    current_page += 1

                    # Check if all products are loaded after pagination
                    all_products_loaded = await self.check_all_products_loaded()
                    if all_products_loaded:
                        break

                    await self.random_sleep()
                else:
                    print("Next button not found. Exiting loop.")
                    break
            except Exception as e:
                print(f"Error navigating to the next page: {e}")
                break

    async def change_zip_code(self, zip_code):
        try:
            await self.page.get_by_role("button", name="Open drawer to view my store").click()
            await self.random_sleep(max_seconds=3, min_seconds=1)
            await self.page.get_by_placeholder("ZIP Code, City, State, or").click()
            await self.random_sleep(max_seconds=3, min_seconds=1)
            await self.page.get_by_placeholder("ZIP Code, City, State, or").fill(zip_code)
            await self.random_sleep(max_seconds=3, min_seconds=1)
            await self.page.get_by_test_id("store-search-text-field").get_by_role("button").click()
            await self.random_sleep(max_seconds=3, min_seconds=1)
            await self.page.get_by_test_id("store-pod-localize__button").first.click()
            await self.random_sleep(max_seconds=3, min_seconds=1)
            print(f"Now scraping {zip_code}")
        except Exception as e:
            print(f"Error changing ZIP code: {e}")

    def set_zip_code(self, new_zip_code):
        self.zip_code = new_zip_code
        self.zip_code_changed = True

    async def sort_by(self, sort_option: SortByOption):
        try:
            current_url = self.page.url
            base_url = current_url.split('?')[0]
            sort_url = base_url + sort_option.sort_url
            await self.page.goto(sort_url)
        except Exception as e:
            print(f"Error in sort_by with option '{sort_option.display_text}': {e}")

    async def handle_response(self, response, retries=3):
        url = response.url
        if "searchModel" in url:
            for attempt in range(retries):
                try:
                    status = response.status
                    if status != 200:
                        print(f"Error: Received status code {status} for {url}")
                        return

                    body = await response.text()
                    data = json.loads(body)

                    products_data = data.get('data', {}).get('searchModel', {}).get('products', [])
                    self.parse_data(products_data)
                    break  # Exit loop if successful
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON response from {url}: {e}")
                except Exception as e:
                    print(f"Error processing response from {url}: {e}")
                    if attempt < retries - 1:
                        print(f"Retrying... Attempt {attempt + 1} of {retries}")
                        await self.random_sleep()  # Wait before retrying
                    else:
                        print(f"Failed after {retries} attempts.")

    def parse_data(self, data):
        if data:
            for item_data in data:
                try:
                    hd_product = HomeDepotItem(**item_data)
                    current_price = hd_product.pricing.value if hd_product.pricing else None
                    original_price = hd_product.pricing.original if hd_product.pricing else None

                    if current_price is None or original_price is None:
                        print("Either current_price or original_price is None. Raw JSON data:")
                        pprint(item_data)
                        continue

                    if current_price <= original_price * self.required_discount_percentage:
                        product = Product(
                            id=hd_product.identifiers.itemId,
                            website=self.site,
                            brand=hd_product.identifiers.brandName,
                            name=hd_product.identifiers.productLabel,
                            dollar_off=hd_product.pricing.promotion.dollarOff if hd_product.pricing and hd_product.pricing.promotion else 0,
                            percentage_off=hd_product.pricing.promotion.percentageOff if hd_product.pricing and hd_product.pricing.promotion else 0,
                            original_price=original_price,
                            current_price=current_price,
                            department=hd_product.info.categoryHierarchy[
                                0] if hd_product.info.categoryHierarchy else None,
                            url=urljoin(hd_product.website.base_url, hd_product.identifiers.canonicalUrl),
                            image_url=urljoin(hd_product.website.base_url,
                                              hd_product.media.images[0].url) if hd_product.media.images else ''
                        )
                        if self.product_callback:
                            self.product_callback(product)

                except ValidationError as e:
                    print(f"Error parsing Home Depot product data: {e}")
                except Exception as e:
                    print(f"Unexpected error parsing product data: {e}, item: {item_data}")

    async def close_page_and_browser(self):
        try:
            if self.page and not self.page.is_closed():
                random_website = random.choice(self.exit_sites)
                await self.page.goto(random_website)
                await self.random_sleep()

            if self.browser and not self.browser.is_closed():
                await self.browser.close()
        except Exception as e:
            print(f"Error during closing page and browser: {e}")
