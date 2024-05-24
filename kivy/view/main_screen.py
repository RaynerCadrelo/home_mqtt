from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty
import libs.mqtt_tanque as mqtt_tanque
from libs.exceptions import TimeOutPowerOnTurbinaException
import asyncio
import logging
from aiomqtt.exceptions import MqttError
from kivymd.app import MDApp
from view.components.dialog import DialogSetting
import config


class MainScreen(MDScreen):
    manager_screens = ObjectProperty()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = MDApp.get_running_app()
        self.setting: config.Setting = self.app.setting
        asyncio.create_task(self.start_tasks())
        self.running_turbina = 0
        self.cont_seg_connection = 0

    async def refresh_is_connect(self):
        while True:
            await asyncio.sleep(1)
            if self.cont_seg_connection == 0:
                self.ids["icon_connection_tanque"].icon_color="grey"
            else:
                self.ids["icon_connection_tanque"].icon_color="green"
                self.cont_seg_connection -= 1

    async def refresh_info_tanque(self):
        try:
            infos = mqtt_tanque.info_turbina(host=self.setting.host, topic=self.setting.topic_turbina)
            async for info in infos:
                self.cont_seg_connection = self.setting.time_is_connected
                self.ids["tanque"].level = info.get("level_percent", -1000000000)
                self.ids["tanque"].rate = info.get("rate", -1000000000)
                self.ids["cisterna"].level = info.get("level_percent_cisterna", -1000000000)
                seconds_left = info.get("seconds_left", -1)
                if seconds_left >= 0:
                    minutes_left = int(round(seconds_left/60))
                    if minutes_left:
                        self.ids['lb_time_left'].text = f"Restante: {minutes_left} min"
                    else:
                        self.ids['lb_time_left'].text = f"Restante: pocos segundos"
                else:
                    self.ids['lb_time_left'].text = f" "
                if info.get("running", -1) == 0 and self.running_turbina:
                    self.ids["circular_progress"].active = 0
                    self.ids["bt_power_on_off"].disabled = False
                    self.ids["bt_power_on_off_label"].text = "LLENAR TANQUE"   
                    self.ids["bt_power_on_off"].md_bg_color = "blue"
                    self.running_turbina = 0
                elif info.get("running", -1) == 1 and self.running_turbina==0:
                    self.ids["bt_power_on_off"].disabled = False
                    self.ids["bt_power_on_off_label"].text = "DETENER"
                    self.ids["circular_progress"].active = False            
                    self.ids["bt_power_on_off"].md_bg_color = "red"
                    self.running_turbina = 1
        except Exception as e:
            logging.error(e)

    async def on_resumen_app(self):
        while True:
            async with self.app.on_resume_condition:
                await self.app.on_resume_condition.wait()
            self.cont_seg_connection = 0

    def style_button_tubina_wait(self):
        self.ids["circular_progress"].active = True
        self.ids["bt_power_on_off"].disabled = True
        self.ids["bt_power_on_off"].md_bg_color = "grey"

    def style_button_tubina_wait_off(self):
        self.style_button_tubina_wait()
        self.ids["bt_power_on_off_label"].text = "APAGANDO ..."

    def style_button_tubina_wait_on(self):
        self.style_button_tubina_wait()
        self.ids["bt_power_on_off_label"].text = "ENCENDIENDO ..."

    def style_button_tubina_off(self):
        self.ids["circular_progress"].active = 0
        self.ids["bt_power_on_off"].disabled = False
        self.ids["bt_power_on_off_label"].text = "LLENAR TANQUE"
        self.ids["bt_power_on_off"].md_bg_color = "blue"

    def style_button_tubina_on(self):
        self.ids["bt_power_on_off"].disabled = False
        self.ids["bt_power_on_off_label"].text = "DETENER"
        self.ids["circular_progress"].active = False            
        self.ids["bt_power_on_off"].md_bg_color = "red"

    def power_on(self):
        async def power_on():
            if self.running_turbina:
                self.style_button_tubina_wait_off()
                try:
                    await asyncio.wait_for(mqtt_tanque.turbina_power_off(
                        host=self.setting.host,
                        topic=self.setting.topic_turbina_action,
                        topic_info=self.setting.topic_turbina),
                            timeout=10)
                except TimeoutError as e:
                    self.style_button_tubina_on()
                    logging.error(e)
                    return
                except MqttError as e:
                    self.style_button_tubina_on()
                    logging.error("Error de conexión")
                    return
                self.style_button_tubina_off()
                self.running_turbina = 0
            else:
                self.style_button_tubina_wait_on()
                try:
                    await asyncio.wait_for(mqtt_tanque.turbina_power_on(
                        host=self.setting.host,
                        topic=self.setting.topic_turbina_action,
                        topic_info=self.setting.topic_turbina),
                            timeout=10)
                except TimeoutError as e:
                    self.style_button_tubina_off()
                    logging.error(e)
                    return
                except MqttError as e:
                    self.style_button_tubina_off()
                    logging.error("Error de conexión")
                    return
                self.style_button_tubina_on()
                self.running_turbina = 1
        asyncio.create_task(power_on())
    
    async def reset_tasks(self):
        await self.cancel_tasks()
        await self.start_tasks()

    async def cancel_tasks(self):
        self.task_refresh_info_tanque.cancel()
        self.task_refresh_is_connect.cancel()
        self.task_refresh_on_resume.cancel()

    async def start_tasks(self):
        self.task_refresh_info_tanque = asyncio.create_task(self.refresh_info_tanque())
        self.task_refresh_is_connect = asyncio.create_task(self.refresh_is_connect())
        self.task_refresh_on_resume = asyncio.create_task(self.on_resumen_app())

    def open_setting(self):
        async def open():
            dialog_setting = DialogSetting()
            dialog_setting.ids.broker.text = self.setting.host
            dialog_setting.ids.topic.text = self.setting.topic_turbina
            dialog_setting.ids.topic_action.text = self.setting.topic_turbina_action
            self.add_widget(dialog_setting)
            async with dialog_setting.condition:
                await dialog_setting.condition.wait()
            if not dialog_setting.is_canceled:
                self.setting.host = dialog_setting.ids.broker.text
                self.setting.topic_turbina = dialog_setting.ids.topic.text
                self.setting.topic_turbina_action = dialog_setting.ids.topic_action.text
                await self.app.save_configuration()
                await self.reset_tasks()
            self.remove_widget(dialog_setting)
        asyncio.create_task(open())
