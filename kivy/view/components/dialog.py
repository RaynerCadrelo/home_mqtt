from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.properties import ObjectProperty, BooleanProperty
import asyncio

class DialogSetting(MDFloatLayout):
    condition = asyncio.Condition()
    is_canceled = BooleanProperty(False)
    
    def close_setting(self):
        async def close():
            async with self.condition:
                self.condition.notify()
        asyncio.create_task(close())
