from kivy.clock import Clock
from kivy.properties import BooleanProperty, DictProperty, ListProperty

from view.base_screen import BaseScreenView
from view.main_screen.components.navdrawer import DrawerItem, DrawerLabel  # NOQA
from view.main_screen.components.product_card import ProductCard  # NOQA


class MainScreenView(BaseScreenView):
    is_running = BooleanProperty(False)
    scraper_running = BooleanProperty(False)
    proxy_metrics = DictProperty({})
    products = ListProperty([])
    refreshing = BooleanProperty(defaultvalue=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        self.controller.proxy_manager.get_proxy_metrics()

    def model_is_changed(self):
        """
        Called whenever any change has occurred in the data model.
        The view in this method tracks these changes and updates the UI
        according to these changes.
        """
        self.on_is_running()
        self.update_product_list()

        # Safely update zip_code_input
        if 'zip_code_input' in self.ids:
            self.ids.zip_code_input.text = self.model.zip_code
        self.refreshing = self.model.is_refreshing
        self.update_refresh_button()

        if 'nav_drawer' in self.ids:
            Clock.schedule_once(lambda dt: self.update_nav_drawer_metrics())

    def on_is_running(self):
        if self.model.is_running:
            self.ids.start_stop_button.icon = 'stop-circle'
        else:
            self.ids.start_stop_button.icon = 'play-circle-outline'

    def toggle_scraper(self):
        if self.model.is_running:
            self.controller.stop_scraper()
        else:
            self.controller.start_scrapers()

    def refresh_proxies(self):
        self.controller.refresh_proxy_list()

    def open_settings(self):
        self.ids.nav_drawer.set_state("open")

    def update_product_list(self):
        def format_fulfillment_options(fulfillment):
            fulfillment_details = []
            if fulfillment and fulfillment.fulfillmentOptions:
                for option in fulfillment.fulfillmentOptions:
                    for service in option.services:
                        for location in service.locations:
                            details = (
                                f"Type: {option.type}, "
                                f"Quantity: {location.inventory.quantity}, "
                                f"LocationID: {location.locationId}, "
                                f"State: {location.state}, "
                                f"DeliveryTimeline: {service.deliveryTimeline}"
                            )
                            fulfillment_details.append(details)
            return "\n".join(fulfillment_details)

        self.ids.product_list.data = [{
            'brand_name': product.brand,
            'product_name': product.name,
            'product_price': f"Price: {product.current_price}",
            'original_price': f"Original: {product.original_price}",
            'dollar_off': f"Dollar Off: {product.dollar_off}",
            'percentage_off': f"Percentage Off: {product.percentage_off}",
            'image_url': product.image_url,
            'url': product.url,
            'amazon_price': f"Amazon Price: {product.amazon.price if product.amazon else 'N/A'}",
            'amazon_match': f"Amazon Match: {product.amazon.match if product.amazon else 'N/A'}",
            'amazon_url': product.amazon.url if product.amazon else ''
        } for product in self.model.products]

    def update_refresh_button(self):
        if self.refreshing:
            self.ids.refresh_button.disabled = True
            # self.ids.refresh_text.text = "Refreshing..."
        else:
            self.ids.refresh_button.disabled = False
            # self.ids.refresh_text.text = "Refresh"

    def update_nav_drawer_metrics(self):
        self.ids.nav_drawer.metrics = self.model.proxy_metrics
