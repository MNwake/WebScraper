import json
import os
import random
from typing import List, Optional, Callable

from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from pydantic import BaseModel
from uszipcode import SearchEngine

from Utility.utils import Websites


class Proxy(BaseModel):
    ip: str
    port: int
    sites: Optional[dict]
    alert: bool = False
    alert_callback: Optional[Callable[[], None]] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.sites:
            self.sites = {site.site_name: None for site in Websites}

    async def async_init(self):
        await self.check_all_sites()

    async def check_all_sites(self):
        for site in Websites:
            await self.check_proxy(site)

    async def check_proxy(self, site: Websites):
        ua = UserAgent()
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(proxy={'server': f'http://{self.ip}:{self.port}'}, headless=True)
                context = await browser.new_context(user_agent=ua.chrome)
                page = await context.new_page()
                success = await self.load_page(page, site.base_url)
                self.sites[site.site_name] = success
            except Exception as e:
                self.sites[site.site_name] = False
                self.trigger_alert()
            finally:
                await browser.close()

    async def load_page(self, page, url: str):
        try:
            response = await page.goto(url)
            if response.status == 200:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error loading {url}: {e}")
            return False

    def trigger_alert(self):
        self.alert = True
        if self.alert_callback:
            self.alert_callback()


class ProxyManager:

    def __init__(self, alert_callback: Optional[Callable[[], None]] = None,
                 metrics_callback: Optional[Callable[[dict], None]] = None, **kwargs):
        super().__init__(**kwargs)
        self.proxies: List[Proxy] = []
        self.proxies_available: bool = False  # Variable to track proxy availability
        self.alert_callback = alert_callback
        self.metrics_callback = metrics_callback
        # self.load_from_json()

    async def refresh_proxy_list(self):
        with open("Play/proxies.txt", 'r') as f:
            proxy_lines = f.readlines()

        # Check if proxies.txt is empty
        if not proxy_lines:
            print("No proxies found. Running without proxies.")
            self.proxies_available = False
            return

        created_proxies = []
        for line in proxy_lines:
            ip_port = line.strip()
            if ':' in ip_port:
                ip, port = ip_port.split(':')
                proxy = Proxy(
                    ip=ip,
                    port=int(port),
                    sites={site.site_name: None for site in Websites},
                    alert=False,
                    alert_callback=self.alert_callback
                )
                await proxy.async_init()
                created_proxies.append(proxy)

        self.proxies = created_proxies  # Update proxies list
        self.proxies_available = bool(self.proxies)  # Update availability flag
        self.save_proxies()

    def save_proxies(self, filename="Play/proxies_status.json"):
        with open(filename, 'w') as f:
            json.dump([proxy.dict() for proxy in self.proxies], f, indent=4)
        self.get_proxy_metrics()

    def load_from_json(self,
                       filename: str = "/Users/theokoester/dev/projects/python/webscrapers/App/Play/proxies_status.json"):
        if not os.path.exists(filename):
            print(f"File {filename} not found. Skipping load.")
            return
        try:
            with open(filename, 'r') as f:
                proxies = json.load(f)
                proxy_models = [Proxy(**proxy) for proxy in proxies]
                self.proxies = proxy_models
                self.proxies_available = bool(self.proxies)  # Update availability flag
                self.get_proxy_metrics()
        except Exception as e:
            print(f"Error loading proxies from {filename}: {e}")

    def get_random_proxy(self, site: Websites) -> Optional[Proxy]:
        # Skip proxy logic if proxies are unavailable
        if not self.proxies_available:
            return None

        while True:
            proxy = random.choice(self.proxies)
            site_status = proxy.sites.get(site.site_name)
            if site_status is not False:
                return proxy

    async def set_geolocation_from_zip(self, context, zip_code: str):
        search = SearchEngine()
        zipcode = search.by_zipcode(zip_code)
        latitude, longitude = zipcode.lat, zipcode.lng

        # Print latitude and longitude for debugging
        await context.set_geolocation({"latitude": latitude, "longitude": longitude})
        await context.add_init_script(f"""
            navigator.geolocation.getCurrentPosition = function(success) {{
                success({{coords: {{latitude: {latitude}, longitude: {longitude}}}}});
            }}
        """)

    def get_proxy_metrics(self):
        total_proxies = len(self.proxies)
        site_metrics = {site.site_name: {'working': 0, 'total': total_proxies} for site in Websites}

        for proxy in self.proxies:
            for site_name, status in proxy.sites.items():
                if status is True:
                    site_metrics[site_name]['working'] += 1

        if self.metrics_callback:
            self.metrics_callback({'total_proxies': total_proxies, 'site_metrics': site_metrics})

        return {'total_proxies': total_proxies, 'site_metrics': site_metrics}
