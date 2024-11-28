from kivy.properties import StringProperty, DictProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.navigationdrawer import MDNavigationDrawerItem, MDNavigationDrawer


class DrawerLabel(MDBoxLayout):
    icon = StringProperty()
    text = StringProperty()
    trailing_text = StringProperty()


class DrawerItem(MDNavigationDrawerItem):
    icon = StringProperty()
    text = StringProperty()
    trailing_text = StringProperty()


class NavigationDrawer(MDNavigationDrawer):
    metrics = DictProperty()
    update_zip_code = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_metrics(self, instance, value):
        site_metrics = value.get('site_metrics', {})
        self.ids.metrics.clear_widgets()

        for site, info in site_metrics.items():
            label_text = f"{site}"
            trailing_text = f"{info['working']}/{info['total']}"
            self.ids.metrics.add_widget(DrawerLabel(text=label_text, icon='store', trailing_text=trailing_text))
