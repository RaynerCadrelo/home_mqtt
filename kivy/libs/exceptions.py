
class TimeOutPowerOnTurbinaException(Exception):
    def __init__(self, message='Timeout to power on turbina'):
        self.message = message