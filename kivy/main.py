
__version__ = "0.1.0"

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
import os
import asyncio

from kivy.core.window import Window
from kivy.utils import platform

if platform == "linux":
    Window.size = (400, 700)

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivy.uix.image import Image
import aiofiles
from view.main_screen import MainScreen

from kivy import kivy_home_dir
os.environ["DATA_DIR"] = kivy_home_dir
os.environ["CACHE_DIR"] = os.path.join(os.environ["DATA_DIR"], "casa")
if not os.path.exists(os.environ["CACHE_DIR"]):
    os.makedirs(os.environ["CACHE_DIR"], exist_ok=True)

import config

class Casa(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # This is the screen manager that will contain all the screens of your
        # application.
        self.tasks: list[asyncio.tasks.Task] = []
        self.manager_screens = MDScreenManager()
        Window.bind(on_keyboard=self._key_handler)
        self.back_functions: list = []
        self.version = __version__
        self.intention_close = None
        self.setting: config.Setting = config.Setting()
        self.on_resume_condition = asyncio.Condition()
    
    async def load_configuration(self):
        file_path = os.path.join(os.environ["CACHE_DIR"], "config.json")
        if not os.path.exists(file_path):
            return
        async with aiofiles.open(file_path, mode='r') as file:
            contents = await file.read()
            self.setting = config.Setting.parse_raw(contents)

    async def save_configuration(self):
        async with aiofiles.open(os.path.join(os.environ["CACHE_DIR"], "config.json"), mode='w') as file:
            contents = self.setting.json()
            await file.write(contents)

    def build(self) -> MDScreenManager:
        self.theme_cls.theme_style = "Light"  # "Dark"
        self.theme_cls.primary_palette = "Orange"
        screen = MDScreen()
        screen.add_widget(
            Image(
                source="assets/images/splash_normal.png",
                allow_stretch=True,
                size_hint_x=0.7,
                pos_hint={'center_x': 0.5,'center_y': 0.5}
                ))
        self.manager_screens.add_widget(screen)
        return self.manager_screens

    def generate_application_screens(self) -> None:
        """
        Creating and adding screens to the screen manager.
        You should not change this cycle unnecessarily. He is self-sufficient.

        If you need to add any screen, open the `View.screens.py` module and
        see how new screens are added according to the given application
        architecture.
        """
        view = MainScreen()
        view.manager_screens = self.manager_screens
        view.name = "main_screen"
        self.manager_screens.add_widget(view)
    
    def app_func(self):
        '''This will run both methods asynchronously and then block until they
        are finished
        '''
        # self.other_task = asyncio.ensure_future(self.waste_time_freely())        

        async def run_wrapper():
            # we don't actually need to set asyncio as the lib because it is
            # the default, but it doesn't hurt to be explicit
            # Correr la aplicación
            self.tasks.append(asyncio.create_task(
                self.initial()
            ))
            await self.async_run(async_lib='asyncio')
            for task in self.tasks:
                task.cancel()
        return asyncio.gather(run_wrapper())
    
    async def initial(self):
        await asyncio.sleep(0)
        await self.load_configuration()
        self.load_all_kv_files(self.directory)
        self.generate_application_screens()
        self.manager_screens.current = "main_screen"

    def _key_handler(self, instance, key, *args):
        '''Función que manejará los botones.
        '''
        if key == 27:
            if not self.back_functions:
                self.tasks.append(asyncio.create_task(
                    self.intention_close()
                ))
            for function in self.back_functions[:]:
                function()
            return True

    def add_key_back(self, function):
        '''Añadir una función que se llamará cuando se presiona el botón atrás o esc.
        '''
        self.back_functions.append(function)
    
    def remove_key_back(self, function):
        '''Quitar la función de la lista que se llamará cuando se presiona el botón atrás o esc.
        '''
        if function in self.back_functions:
            self.back_functions.remove(function)

    def on_resume(self):
        async def on_resume():
            async with self.on_resume_condition:
                self.on_resume_condition.notify()
        asyncio.create_task(on_resume())



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Casa().app_func())
    loop.close()
