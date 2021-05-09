import time
from datetime import datetime
import logging
from attr import attrs, attrib

from easy_mornings_server.lightcontroller import LightController

log = logging.getLogger(__name__)

LIGHT_STATE_CONSTANT = 'LIGHT_STATE_CONSTANT'
LIGHT_STATE_FADING = 'LIGHT_STATE_FADING'
LIGHT_STATE_TIMER = 'LIGHT_STATE_TIMER'


@attrs
class LightState:
    state = attrib()

    @classmethod
    def constant(cls):
        return cls(LIGHT_STATE_CONSTANT)


@attrs
class FadingLightState(LightState):
    start_time = attrib()
    start_level = attrib()
    end_time = attrib()
    end_level = attrib()

    @classmethod
    def fading(cls, start_time, start_level, end_time, end_level):
        return cls(LIGHT_STATE_FADING, start_time, start_level, end_time, end_level)


@attrs
class TimedLightState(LightState):
    end_time = attrib()
    end_level = attrib()

    @classmethod
    def timed(cls, end_time, end_level):
        return cls(LIGHT_STATE_TIMER, end_time, end_level)


class LightManager:
    __slots__ = ['light_controller', 'state', 'level']

    def __init__(self, light_controller: LightController):
        self.light_controller = light_controller
        self.state = LightState.constant()
        self.level = light_controller.level

    def _set_level(self, level: float):
        self.level = level
        self.light_controller.set_level(level)

    def set_level(self, level: float):
        self.state = LightState.constant()
        self._set_level(level)

    def fade(self, period: int, level: float):
        now_time = milli(datetime.now().time())
        now_level = self.level
        then_time = now_time + period * 1000
        self.state = FadingLightState.fading(now_time, now_level, then_time, level)

    def timer(self, period: int, level: float):
        now_time = milli(datetime.now().time())
        then_time = now_time + period * 1000
        self.state = TimedLightState.timed(then_time, level)

    def run(self):
        log.debug("Light Manager is running")
        sleep_time = 0.1
        while True:
            time.sleep(sleep_time)
            if self.run_timestep():
                sleep_time = 0.1
            else:
                sleep_time = min(sleep_time * 2, 2)

    def run_timestep(self):
        now = milli(datetime.now().time())
        if self.state.state != LIGHT_STATE_CONSTANT:
            if now > self.state.end_time:
                self._set_level(self.state.end_level)
                self.state = LightState.constant()
            elif self.state.state == LIGHT_STATE_FADING:
                progress = (now - self.state.start_time) / (self.state.end_time - self.state.start_time)
                level = self.state.start_level + progress * (self.state.end_level - self.state.start_level)
                self._set_level(level)
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
