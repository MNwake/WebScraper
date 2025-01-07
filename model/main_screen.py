from typing import List

from Model.base_model import BaseScreenModel

from model.item import Product


class MainScreenModel(BaseScreenModel):
    """
    Implements the logic of the :class:`~View.main_screen.MainScreen.MainScreenView` class.
    This class manages the running state which can control or reflect the state of a process,
    such as web scraping in the background.
    """

    def __init__(self):
        super().__init__()
        self._is_running = False
        self._products: List[Product] = []
        self._archived_products: List[Product] = []
        self._zip_code: str = ''
        self._is_refreshing: bool = False
        self._proxy_metrics: dict = {}

    @property
    def proxy_metrics(self):
        return self._proxy_metrics

    @proxy_metrics.setter
    def proxy_metrics(self, value):
        self._proxy_metrics = value
        self.notify_observers('main screen')

    @property
    def is_refreshing(self):
        """
        Property to get the running state of the model.
        """
        return self._is_refreshing

    @is_refreshing.setter
    def is_refreshing(self, value):
        self._is_refreshing = value
        self.notify_observers('main screen')

    @property
    def is_running(self):
        """
        Property to get the running state of the model.
        """
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        self._is_running = value
        self.notify_observers('main screen')

    @property
    def products(self) -> List[Product]:
        """
        Property to get the list of products.
        """
        return self._products

    @property
    def archived_products(self) -> List[Product]:
        """
        Property to get the list of archived products.
        """
        return self._archived_products

    def add_product(self, new_product: Product):
        """
        Add a new product to the list of products, ensuring no duplicates.
        If the product already exists, update the pricing and fulfillment info.
        """
        self._products.append(new_product)
        self.notify_observers('main screen')
        print('successfully added item')

    def archive_product(self, product_to_archive: Product):
        """
        Move a product to the archived products list.
        """
        if product_to_archive in self._products:
            self._products.remove(product_to_archive)
            self._archived_products.append(product_to_archive)
            self.notify_observers('main screen')

    @property
    def zip_code(self) -> str:
        """
        Property to get the ZIP code.
        """
        return self._zip_code

    @zip_code.setter
    def zip_code(self, value: str):
        self._zip_code = value
        self.notify_observers('main screen')
