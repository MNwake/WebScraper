import time
from enum import Enum
from typing import Tuple

import requests
from dotenv import load_dotenv
from uszipcode import SearchEngine

from config.config import Config

load_dotenv()


class ProxyError(Exception):
    pass


def get_lat_long_from_zip(zip_code: str) -> Tuple[float, float]:
    search = SearchEngine(simple_zipcode=True)
    zipcode = search.by_zipcode(zip_code)
    return zipcode.lat, zipcode.lng


class Websites(Enum):
    HOME_DEPOT = ("home_depot", "https://www.homedepot.com")
    LOWES = ("lowes", "https://www.lowes.com")
    AMAZON = ("amazon", "https://www.amazon.com")
    GOOGLE = ('google', "https://www.google.com")
    ACE = ('ace', "https://www.acehardware.com")
    NORTHERN_TOOL = ('northern_tool', "https://www.northerntool.com")
    SAMS_CLUB = ('sams_club', 'https://www.samsclub.com')

    def __init__(self, site_name, base_url):
        self.site_name = site_name
        self.base_url = base_url

    def __str__(self):
        return self.site_name


def google_search(search_query, retries=5, backoff_factor=1, num_results=1):
    search_engine = Config.SEARCH_ENGINE
    google_api_key = Config.GOOGLE_API_KEY

    if not search_engine or not google_api_key:
        print("Environment variables for search engine or API key are not set.")
        return None

    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': search_query,
        'key': google_api_key,
        'cx': search_engine,
        'num': num_results
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            response_json = response.json()

            # Extract the link of the first Amazon item, if available
            items = response_json.get('items', [])
            if items:
                first_item_link = items[0]['link']
                return first_item_link
            else:
                print("No items found.")
                return None
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:  # Too Many Requests
                sleep_time = backoff_factor * (2 ** attempt)
                print(f"HTTP 429 error: Too Many Requests. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"HTTP error occurred: {http_err}")
                return None
        except Exception as err:
            print(f"An error occurred: {err}")
            return None

    print("Max retries exceeded.")
    return None


if __name__ == "__main__":
    search_query = "utilitech cord storage reel and stand"
    amazon_link = google_search(search_query)
    print("Resulting Amazon Link:", amazon_link)
