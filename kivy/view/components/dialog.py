from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, NumericProperty
import asyncio
from kivy.clock import Clock

class Dialog(MDFloatLayout):
    condition = asyncio.Condition()
    is_canceled = BooleanProperty(False)
    title = StringProperty("Ajustes")
    wgts = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Clock.schedule_once(self.create_all, 0.2)

    
    def close_setting(self):
        async def close():
            async with self.condition:
                self.condition.notify()
        asyncio.create_task(close())

    def create_all(self, *args):
        for w in self.wgts:
            self.ids.container.add_widget(w)
        self.wgts.clear()


    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MDCard):
            return super().add_widget(widget)
        else:
            self.wgts.append(widget)


class DialogSetting(Dialog):
    pass


class DialogSettingTanque(Dialog):
    level_stop = NumericProperty(100)
