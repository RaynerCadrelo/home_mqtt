import asyncio
import aiomqtt
import json
import logging
import datetime
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO,
                    filename="py_log.log",
                    filemode="a",
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S')

HOST = "192.168.1.94"
#HOST = "localhost"
NIVEL_TANQUE = "casa_rayner/tanque_elevado"
TURBINA = "casa_rayner/turbina"
TURBINA_ACTION = "casa_rayner/turbina/action"
ARDUINO = "casa_rayner/arduino"
ARDUINO_ACTION = "casa_rayner/arduino/action"

TIME_PUBLISH = 3

ANALOGIC_PORT = "A0"  # Pin del conversor analógico digital del tanque
DIGITAL_PORT = "D4"  # Pin conectado a la turbina
DIGITAL_PORT_SENSOR_MAX = "D3"

FITTING_ADC_MIN = 215  # valor mínimo del conversor cuando el nivel está al 0%
FITTING_ADC_MAX = 610  # valor máximo del conversor cuando el nivel está al 100%
ML_PER_ADC = 1739  # mililitros por valor adc (conversor analógico digital)
TIME_DELTA_RATE = 90  # tiempo de espera para cálculo del flujo (en segundos)
ADC_DELTA_RATE = 8  # unidades del conversor a esperar para el cálculo del flujo 
PERCENT_DELTA_STABILIZE = 0.8  # parámetro para estabilizar el porciento, evitar el ruido.

TIME_MAX_POWER_ON = 2400  # Tiempo máximo que puede estar encendido la turbina (en segundos).

TIMER_TURBINA = [
    {
        "time_start": datetime.time.fromisoformat("07:00"),
        "time_end": datetime.time.fromisoformat("19:59"),
        "min_level": 30,
        "stop_level": 100,
        "active": True
    },
    {
        "time_start": datetime.time.fromisoformat("20:00"),
        "time_end": datetime.time.fromisoformat("23:59"),
        "min_level": 5,
        "stop_level": 40,
        "active": True
    },
    {
        "time_start": datetime.time.fromisoformat("00:00"),
        "time_end": datetime.time.fromisoformat("06:59"),
        "min_level": 1,
        "stop_level": 5,
        "active": True
    }
]

class Turbina(BaseModel):
    running: int = 0  # 0: apagado, 1: encendido
    datetime_start: datetime.datetime = datetime.datetime.now()
    seconds_left: int = -1  # tiempo restante en segundos
    level_percent: int = -1  # porciento del nivel del tanque
    level_adc: int = -1  # valor del adc en arduino del nivel del tanque de 0 - 1023
    sensor_max: int = 0  # Sensor de seguridad de nivel máximo en el tanque
    rate: int = 0  # flujo del agua en mL/min
    force_power_off: int = 0  # forzar apagar la turbina

turbina = Turbina()

async def publish(topic: str, value: str):
    async with aiomqtt.Client(HOST) as client:
        await client.publish(topic=topic, payload=value)

async def subscribe_turbina_action(topic: str):
    while True:
        try:
            async with aiomqtt.Client(HOST) as client:
                await client.subscribe(topic=topic)
                async for message in client.messages:
                    msg_json = json.loads(message.payload.decode())
                    if not msg_json.get("power", None) is None:
                        if not msg_json.get("stop_level", None) is None:
                            stop_level = msg_json.get("stop_level", None)
                        else:
                            stop_level = 100
                        if msg_json.get("power", None) == 1:
                            asyncio.create_task(turbina_power_on(stop_level=stop_level))
                        if msg_json.get("power", None) == 0:
                            asyncio.create_task(turbina_power_off())
        except Exception as e:
            logging.error(e)
        await asyncio.sleep(5)

async def subscribe_turbina(topic: str):
    while True:
        try:
            async with aiomqtt.Client(HOST) as client:
                await client.subscribe(topic=topic)
                async for message in client.messages:
                    msg_json = json.loads(message.payload.decode())
                    if not msg_json.get(ANALOGIC_PORT, None) is None:
                        if msg_json[ANALOGIC_PORT] == -1:  # el conversor aún no está activado
                            continue
                        percent = stablize_percent(
                            percent=adc_to_percent(msg_json[ANALOGIC_PORT]),
                            last_percent=turbina.level_percent)
                        percent = 0 if percent < 0 else percent
                        percent = 100 if percent > 100 else percent
                        turbina.level_adc = msg_json[ANALOGIC_PORT]
                        turbina.level_percent = percent
                        if not msg_json.get(DIGITAL_PORT, None) is None:
                            turbina.running = msg_json[DIGITAL_PORT]
                        if not msg_json.get(DIGITAL_PORT_SENSOR_MAX, None) is None:
                            turbina.sensor_max = msg_json[DIGITAL_PORT_SENSOR_MAX]
        except Exception as e:
            logging.error(e)
        await asyncio.sleep(5)

async def rate():
    while True:
        if turbina.level_adc == -1:
            await asyncio.sleep(5)
            continue
        level_adc_start = turbina.level_adc
        await asyncio.sleep(TIME_DELTA_RATE)
        level_adc_end = turbina.level_adc
        level_delta = level_adc_end - level_adc_start
        if abs(level_delta) > 1:
            turbina.rate = int((ML_PER_ADC * (level_delta)) / (TIME_DELTA_RATE/60))
        else:
            turbina.rate = 0

async def rate_2():
    while True:
        if turbina.level_adc == -1:
            await asyncio.sleep(5)
            continue
        datetime_start = datetime.datetime.now()
        level_adc_start = turbina.level_adc
        level_adc_end_plus = level_adc_start + ADC_DELTA_RATE
        level_adc_end_minus = level_adc_start - ADC_DELTA_RATE
        while turbina.level_adc < level_adc_end_plus and turbina.level_adc > level_adc_end_minus:
            datetime_end = datetime.datetime.now()
            time_delta: datetime.timedelta = datetime_end - datetime_start
            if time_delta.seconds >= (6*60):
                turbina.rate = 0
            await asyncio.sleep(1)
        datetime_end = datetime.datetime.now()
        time_delta: datetime.timedelta = datetime_end - datetime_start
        mlitter = ML_PER_ADC * ADC_DELTA_RATE
        rate = int((mlitter) / (time_delta.seconds/60))
        if turbina.level_adc < level_adc_start:  # poner el flujo negativo si el tanque está bajando el nivel
            rate *= -1
        turbina.rate = rate

async def turbina_power_off():
    if turbina.running:
        turbina.force_power_off = 1

async def refresh_time_left():
    level_percent_start = turbina.level_percent
    await asyncio.sleep(6)  # Esperar que arranque la turbina
    while (turbina.level_percent == level_percent_start):  # Esperar que comience a subir el nivel del tanque
        await asyncio.sleep(0.5)
        if not turbina.running:
            return
    level_adc_start = turbina.level_adc
    datetime_start = datetime.datetime.now()
    while turbina.running:
        await asyncio.sleep(4)
        level_adc = turbina.level_adc
        delta_level_adc = level_adc - level_adc_start
        if delta_level_adc < 5:
            continue
        level_adc_left = FITTING_ADC_MAX - level_adc
        datetime_now = datetime.datetime.now()
        delta_datetime = datetime_now - datetime_start
        delta_seconds = delta_datetime.seconds
        seconds_per_adc = delta_seconds / delta_level_adc
        seconds_left = seconds_per_adc * level_adc_left
        turbina.seconds_left = int(seconds_left)
    turbina.seconds_left = -1

async def turbina_power_on(stop_level: int):
    logging.info("Encender turbina.")
    i = 5
    datetime_start: datetime.datetime = datetime.datetime.now()
    asyncio.create_task(refresh_time_left())
    while True:
        await asyncio.sleep(0.7)
        # llegado al máximo nivel
        if turbina.level_percent >= stop_level:
            logging.info("Apagado por alcanzar el nivel máximo programado")
            break
        # tiempo de llenado excedido Fallo!!
        timedelta = datetime.datetime.now() - datetime_start
        if timedelta.seconds >= TIME_MAX_POWER_ON:
            logging.warning("Apagado por exceso de tiempo de encendido")
            break
        # comprobar si el nivel del agua está subiendo
        if timedelta.seconds >= (TIME_DELTA_RATE*3):
            if turbina.rate <= 0:
                logging.warning("Apagado por no detectar cambio positivo en nivel del tanque")
                break
        # sensor de seguridad de máximo nivel activado
        if turbina.sensor_max:
            logging.warning("Apagado por sensor de nivel máximo")
            break
        # forzar el apagado de la turbina
        if turbina.force_power_off:
            turbina.force_power_off = 0
            logging.info("Apagado forzado")
            break
        if i == 5:
            await publish(topic=ARDUINO_ACTION, value='{"D4": 3}')
            i = 0
        i += 1
    await publish(topic=ARDUINO_ACTION, value='{"D4": 0}')  # apagar turbina
    logging.info("Apagado de turbina")

async def auto_power_on():
    while True:
        try:
            await asyncio.sleep(10)
            datetime_start = datetime.datetime.now()
            timer_turbina = list(filter(lambda x: (x['time_start'] <= datetime_start.time() < x['time_end']), TIMER_TURBINA))
            if timer_turbina:
                min_level = timer_turbina[0]['min_level']
                stop_level = timer_turbina[0]['stop_level']
                if turbina.level_percent <= min_level:
                    logging.info("Encendido automático de la turbina")
                    await turbina_power_on(stop_level=stop_level)
                    await asyncio.sleep(60*30)  # esperar 30 minutos.
        except Exception as e:
            logging.error(e)

def adc_to_percent(adc: int) -> float:
    percent = 100/(FITTING_ADC_MAX-FITTING_ADC_MIN)*adc + (100 - 100/(FITTING_ADC_MAX-FITTING_ADC_MIN)*FITTING_ADC_MAX)
    return percent

def stablize_percent(percent: float, last_percent) -> int:
    if percent <= (last_percent - PERCENT_DELTA_STABILIZE) or percent >= (last_percent + PERCENT_DELTA_STABILIZE):
        last_percent = int(round(percent, 0))
    return last_percent

async def publish_turbina():
    while True:
        last_turbina_json = turbina.model_dump_json()
        for i in range(10):
            await asyncio.sleep(0.3)
            turbina_json = turbina.model_dump_json()
            if last_turbina_json != turbina_json:
                break
        try:
            await publish(topic=TURBINA, value=turbina_json)
        except Exception as e:
            logging.error(e)

async def main():
    task = asyncio.create_task(subscribe_turbina(topic=ARDUINO))
    task2 = asyncio.create_task(publish_turbina())
    task3 = asyncio.create_task(rate_2())
    task4 = asyncio.create_task(auto_power_on())
    task5 = asyncio.create_task(subscribe_turbina_action(topic=TURBINA_ACTION))
    try:
        await asyncio.shield(task)
    except TimeoutError:
	    logging.error('The task was cancelled due to a timeout')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
