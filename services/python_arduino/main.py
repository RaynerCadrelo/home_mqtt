import asyncio
import serial_asyncio
import aiomqtt
import json
import logging
import time

'''
Commands

  string -> "ABC"
  A: D -> digital
     A -> analógico
     T -> período de refrescado (delay loop)
          A     D     T
  B: A -> A0    D0    10ms
     B -> A1    D1    50ms
     C -> A2    D2    100ms
     D -> A3    D3    200ms
     E -> A4    D4    300ms
     F -> A5    D5    400ms
     G -> A6    D6    500ms
     H -> A7    D7    600ms
     I -> A8    D8    700ms
     J -> A9    D9    800ms
     K -> A10   D10   900ms
     L -> A11   D11   1000ms
     M -> A12   D12   1200ms
     N -> A13   D13   1500ms
     O -> ---   ---   1700ms
     P -> ---   ---   2000ms
     Q -> ---   ---   3000ms
     R -> ---   ---   4000ms
     S -> ---   ---   5000ms
     T -> ---   ---   7000ms
     U -> ---   ---   10000ms
     V -> ---   ---   15000ms
     W -> ---   ---   20000ms
     X -> ---   ---   30000ms
     Y -> ---   ---   60000ms
     Z -> ---   ---   120000ms

     Digital:
  C: 0 -> poner en bajo
     1 -> poner en alto
     3 -> configurar como entrada
     4 -> configurar como salida
     5 -> poner en estado bajo con confirmación
     6 -> poner en estado alto con confirmación
     Analógico:
     0 -> desactivar lectura del analógico
     1 -> activar lectura del analógico
'''

logging.basicConfig(level=logging.INFO,
                    filename="py_log.log",
                    filemode="a",
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S')

HOST = "192.168.1.94"
#HOST = "localhost"
ARDUINO = "casa_rayner/arduino"
ARDUINO_ACTION = "casa_rayner/arduino/action"


async def publish(topic: str, value: str):
    async with aiomqtt.Client(HOST) as client:
        await client.publish(topic=topic, payload=value)


class OutputProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.buf: str = ''
        self.transport = transport
        print('port opened', transport)
        transport.serial.rts = False  # You can manipulate Serial object via transport
        #transport.write(b'Hello, World!\n')  # Write serial data via transport
        #self.transport.write(b'AA5\n')
        self.is_configured = False
        asyncio.create_task(self.subscribe(ARDUINO_ACTION))

    def configure_arduino(self):
        time.sleep(0.5)
        self.transport.write(b'\n')     # Limpiar
        self.transport.write(b'AA1\n')  # Activar el analógico 0
        self.transport.write(b'DD3\n')  # Poner como entrada el pin D3
        self.transport.write(b'DF3\n')  # Poner como entrada el pin D5
        self.transport.write(b'DE4\n')  # Poner como salida el pin D4
        self.transport.write(b'TI0\n')  # Configurar el período del loop en I->700 ms

    def data_received(self, data):
        if not self.is_configured:
            self.configure_arduino()
            self.is_configured = True
        data_str = data.decode()
        self.buf += data_str.replace("\r", "")
        if '\n' in self.buf:
            lines = self.buf.split('\n')
            self.buf = lines[-1]  # whatever was left over
            for line in lines[:-1]:
                line_json = json.loads(line)
                asyncio.create_task(publish(topic=ARDUINO, value=json.dumps(line_json)))

    async def subscribe(self, topic: str):
        while True:
            try:
                async with aiomqtt.Client(HOST) as client:
                    await client.subscribe(topic=topic)
                    async for message in client.messages:
                        msg = message.payload.decode()
                        msg_json = json.loads(msg)
                        digital_pins = ["D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13"]
                        digital_pins_arduino = {"D2" : "C", "D3": "D", "D4": "E", "D5": "F", "D6": "G", "D7": "H",
                                                "D8": "I", "D9": "J", "D10": "K", "D11": "L", "D12": "M", "D13": "N"}
                        analogic_pins = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"]
                        for dig in digital_pins:
                            if not msg_json.get(dig, None) is None:
                                if msg_json.get(dig, None) == 0:    # poner en bajo
                                    self.transport.write(f'D{digital_pins_arduino[dig]}0\n'.encode())
                                elif msg_json.get(dig, None) == 1:  # poner en alto
                                    self.transport.write(f'D{digital_pins_arduino[dig]}1\n'.encode())
                                elif msg_json.get(dig, None) == 2:  # poner en bajo con confirmación
                                    self.transport.write(f'D{digital_pins_arduino[dig]}5\n'.encode())
                                elif msg_json.get(dig, None) == 3:  # poner en alto con confirmación
                                    self.transport.write(f'D{digital_pins_arduino[dig]}6\n'.encode())
            except Exception as e:
                logging.error(e)
            await asyncio.sleep(5)



    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())
        print('resume writing')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    while True:
        while True:
            try:
                coro = serial_asyncio.create_serial_connection(loop, OutputProtocol, '/dev/ttyUSB0', baudrate=9600)
                loop.run_until_complete(coro)
                break
            except serial_asyncio.serial.SerialException as e:
                logging.warning(e)
            time.sleep(3)
        
        loop.run_forever()
        time.sleep(3)
    loop.close()
