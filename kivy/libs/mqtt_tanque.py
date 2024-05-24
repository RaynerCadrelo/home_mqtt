import aiomqtt
import asyncio
import json
import logging
from aiomqtt.exceptions import MqttError


async def publish(host:str, topic: str, value: str):
    async with aiomqtt.Client(host) as client:
        await client.publish(topic=topic, payload=value)

async def turbina_power_on(host:str, topic: str, topic_info: str):
    '''Espera que el tanque se llene'''
    await publish(host=host, topic=topic, value='{"power": 1}')
    infos = info_turbina(host=host, topic=topic_info)
    async for info in infos:
        if info.get("running", -1) == 1:
            break
    return True

async def turbina_power_off(host:str, topic: str, topic_info: str):
    '''Espera que el tanque se llene'''
    await publish(host=host, topic=topic, value='{"power": 0}')
    async for info in info_turbina(host=host, topic=topic_info):
        if info.get("running", -1) == 0:
            break

async def info_turbina(host: str, topic: str):
    while True:
        try:
            async with aiomqtt.Client(host) as client:
                await client.subscribe(topic=topic)
                async for message in client.messages:
                    msg_json = json.loads(message.payload.decode())
                    yield msg_json
        except Exception as e:
            logging.error(e)
        await asyncio.sleep(5)