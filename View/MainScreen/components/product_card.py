import webbrowser

from kivy.properties import StringProperty
from kivymd.uix.card import MDCard


class ProductCard(MDCard):
    brand_name = StringProperty()
    product_name = StringProperty()
    product_price = StringProperty()
    original_price = StringProperty()
    dollar_off = StringProperty()
    percentage_off = StringProperty()
    amazon_price = StringProperty()
    amazon_match = StringProperty()
    image_url = StringProperty()
    url = StringProperty()
    amazon_url = StringProperty()

    def on_image_url(self, instance, value):
        if '<SIZE>' in value:
            self.image_url = value.replace('<SIZE>', '300')
        else:
            self.image_url = value

    def on_press(self):
        if self.url:
            webbrowser.open(self.url)
        if self.amazon_url:
            webbrowser.open(self.amazon_url)
