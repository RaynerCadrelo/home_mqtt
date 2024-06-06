from pydantic import BaseModel
import datetime


class Turbina(BaseModel):
    running: int = 0  # 0: apagado, 1: encendido
    datetime_start: datetime.datetime = datetime.datetime.now()
    seconds_left: int = -1  # tiempo restante en segundos
    level_percent: int = -1  # porciento del nivel del tanque
    level_adc: int = -1  # valor del adc en arduino del nivel del tanque de 0 - 1023
    level_percent_stop: int = 100  # porciento del nivel del tanque para apagarse
    sensor_max: int = 0  # Sensor de seguridad de nivel máximo en el tanque
    rate: int = 0  # flujo del agua en mL/min
    force_power_off: int = 0  # forzar apagar la turbina
