import time
from datetime import datetime
import logging
from easy_mornings_server.lightcontroller import LightController

log = logging.getLogger(__name__)

LIGHT_STATE_ON_INDEFINITELY = 'LIGHT_STATE_ON_INDEFINITELY'
LIGHT_STATE_OFF_INDEFINITELY = 'LIGHT_STATE_OFF_INDEFINITELY'
LIGHT_STATE_ON_TIMED = 'LIGHT_STATE_ON_TIMED'
LIGHT_STATE_FADING_ON = 'LIGHT_STATE_FADING_ON'
LIGHT_STATE_FADING_OFF = 'LIGHT_STATE_FADING_OFF'


class LightState:
    __slots__ = ['state', 'start', 'end']

    def __init__(self, state, start=None, end=None):
        self.state = state
        self.start = start
        self.end = end

    @classmethod
    def off(cls):
        return cls(LIGHT_STATE_OFF_INDEFINITELY)

    @classmethod
    def on(cls):
        return cls(LIGHT_STATE_ON_INDEFINITELY)

    @classmethod
    def timed_on(cls, start, end):
        return cls(LIGHT_STATE_ON_TIMED, start, end)

    @classmethod
    def fading_on(cls, start, end):
        return cls(LIGHT_STATE_FADING_ON, start, end)

    @classmethod
    def fading_off(cls, start, end):
        return cls(LIGHT_STATE_FADING_OFF, start, end)


class LightManager:
    __slots__ = ['light_controller', 'state']

    def __init__(self, light_controller: LightController):
        self.light_controller = light_controller
        self.state = LightState.off()

    def on(self, level: float):
        level = level or 1
        self.state = LightState.on()
        self.light_controller.set_level(level)

    def off(self):
        self.state = LightState.off()
        self.light_controller.set_level(0)

    def on_timed(self, period: int):
        now = milli(datetime.now().time())
        self.state = LightState.timed_on(now, now + period * 1000)
        self.light_controller.set_level(1)

    def fade_on(self, period: int):
        now = milli(datetime.now().time())
        self.state = LightState.fading_on(now, now + period*1000)

    def fade_off(self, period: int):
        now = milli(datetime.now().time())
        self.state = LightState.fading_off(now, now + period * 1000)

    def run(self):
        log.debug("Light Manager is running")
        sleep_time = 0.1
        while True:
            time.sleep(sleep_time)
            if self.run_timestep():
                sleep_time = 0.01
            else:
                sleep_time = min(sleep_time * 2, 2)

    def run_timestep(self):
        now = milli(datetime.now().time())
        if self.state.state == LIGHT_STATE_ON_TIMED:
            if now > self.state.end:
                self.light_controller.set_level(0)
                self.state = LightState.off()
        elif self.state.state == LIGHT_STATE_FADING_ON:
            if now > self.state.end:
                self.light_controller.set_level(1)
                self.state = LightState.on()
            else:
                level = (now - self.state.start) / (self.state.end - self.state.start)
                self.light_controller.set_level(level)
                return True
        elif self.state.state == LIGHT_STATE_FADING_OFF:
            if now > self.state.end:
                self.light_controller.set_level(0)
                self.state = LightState.off()
            else:
                level = (self.state.end - now) / (self.state.end - self.state.start)
                self.light_controller.set_level(level)
                return True


def milli(timestamp: datetime.time):
    millis = 0
    millis += timestamp.hour
    millis *= 60
    millis += timestamp.minute
    millis *= 60
    millis += timestamp.second
    millis *= 1000
    millis += timestamp.microsecond // 1000
    return float(millis)
