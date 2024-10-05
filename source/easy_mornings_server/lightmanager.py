import time
from datetime import datetime
import logging
from attr import attrs, attrib

from easy_mornings_server.lightcontroller import LightController

log = logging.getLogger(__name__)

LIGHT_STATE_CONSTANT = 'LIGHT_STATE_CONSTANT'
LIGHT_STATE_FADING = 'LIGHT_STATE_FADING'
LIGHT_STATE_TIMER = 'LIGHT_STATE_TIMER'
LIGHT_STATE_RAVE = 'LIGHT_STATE_RAVE'



@attrs
class LightState:
    state = attrib()
    end_time = attrib(default=None)
    end_level = attrib(default=None)
    start_time = attrib(default=None)
    start_level = attrib(default=None)

    @classmethod
    def constant(cls):
        return cls(LIGHT_STATE_CONSTANT)

    @classmethod
    def fading(cls, start_time, start_level, end_time, end_level):
        return cls(LIGHT_STATE_FADING, end_time, end_level, start_time, start_level)

    @classmethod
    def timed(cls, end_time, end_level):
        return cls(LIGHT_STATE_TIMER, end_time, end_level)

    def time_left(self):
        if self.end_time is None:
            return -1
        else:
            now_time = datetime.now().timestamp()
            return int(self.end_time - now_time)

    @classmethod
    def rave(cls):
        return cls(LIGHT_STATE_RAVE)


class ScheduleItem:
    def __init__(self, id, enabled, hour, minute, state, level=None, period=None, repeat=False, days=None):
        self.id = id
        self.enabled = enabled
        self.hour = hour
        self.minute = minute
        self.next = None
        self.state = state
        self.level = level
        self.period = period
        self.repeat = repeat
        if days == None:
            days = [True] * 7
        elif len(days) != 7:
            days = days + ( [False] * (7-len(days)) )
        self.days = days
        self.set_next(datetime.now())

    @classmethod
    def from_dict(cls, item_id, values):
        return cls(
            id=item_id,
            enabled=values.get("enabled", True),
            hour=values["hour"],
            minute=values["minute"],
            state=values["state"],
            level=values.get("level", None),
            period=values.get("period", None),
            repeat=values.get("repeat", False),
            days=values.get("days", None),
        )

    def to_dict(self):
        ret = {
            "id": self.id,
            "enabled": self.enabled,
            "hour": self.hour,
            "minute": self.minute,
            "state": self.state,
            "repeat": self.repeat,
            "days": self.days,
        }
        if self.level is not None:
            ret["level"] = self.level
        if self.period is not None:
            ret["period"] = self.period
        return ret

    def set_next(self, now):
        if not self.enabled:
            self.next = None
            return

        today = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if today < now:
            next = today.replace(day=today.day+1)
        else:
            next = today  

        for i in range(7):
            if self.days[next.weekday()]:
                break
            next = next.replace(day=next.day+1)
        else:
            next = None

        self.next = next

    def triggered(self, now):
        triggered = self.next < now
        if triggered:
            if not self.repeat:
                self.enabled = False
            self.set_next(now)
        return triggered

    
class Schedule:

    def __init__(self):
        self.items = {}
        self.counter = 0

    def add(self, values):
        item_id = str(self.counter)
        self.items[item_id] = ScheduleItem.from_dict(item_id, values)
        self.counter += 1
        return item_id

    def get(self, key):
        return self.items[key].to_dict()

    def getall(self):
        return [i.to_dict() for i in self.items.values()]

    def remove(self, key):
        del self.items[key]    


class LightManager:
    __slots__ = ['light_controller', 'state', 'level', 'schedule']

    def __init__(self, light_controller: LightController):
        self.light_controller = light_controller
        self.state = LightState.constant()
        self.level = light_controller.level
        self.schedule = Schedule()

    def status(self):
        state = self.state.state
        time_left = self.state.time_left()
        level = self.level
        return {
            'state': state,
            'level': level,
            'time_left': time_left,
        }

    def _set_level(self, level: float):
        self.level = level
        self.light_controller.set_level(level)

    def constant(self, level: float):
        self.state = LightState.constant()
        self._set_level(level)

    def fade(self, period: int, level: float):
        now_time = datetime.now().timestamp()
        now_level = self.level           
        then_time = now_time + period
        self.state = LightState.fading(now_time, now_level, then_time, level)

    def timer(self, period: int, level: float):
        now_time = datetime.now().timestamp()
        end_time = now_time + period
        self.state = LightState.timed(end_time, level)

    def rave(self):
        self.state = LightState.rave()

    def run(self):
        log.debug("Light Manager is running")
        sleep_time = 0.1
        previous = None
        while True:
            now = datetime.now()
            self.check_schedule(now)
            sleep_time = self.run_timestep(now)
            time.sleep(sleep_time)

    def check_schedule(self, now):
        for item in self.schedule.items.values():
            if item.triggered(now):
                if item.state == LIGHT_STATE_CONSTANT:
                    self.constant(item.level)
                elif item.state == LIGHT_STATE_FADING:
                    self.fade(item.period, item.level)
                elif item.state == LIGHT_STATE_TIMER:
                    self.timer(item.period, item.level)
                elif item.state == LIGHT_STATE_RAVE:
                    self.rave()

    def run_timestep(self, now):

        now = now.timestamp()

        if self.state.state == LIGHT_STATE_CONSTANT:
            return 2

        if self.state.state == LIGHT_STATE_RAVE:
            self._set_level(int(now * 5) % 2)
            return 0.1

        if self.state.state == LIGHT_STATE_TIMER:
            if now > self.state.end_time:
                self._set_level(self.state.end_level)
                self.state = LightState.constant()
            return 2
        
        if self.state.state == LIGHT_STATE_FADING:
            if now > self.state.end_time:
                self._set_level(self.state.end_level)
                self.state = LightState.constant()
                return 2
            duration = self.state.end_time - self.state.start_time
            progress = (now - self.state.start_time) / duration
            amount = self.state.end_level - self.state.start_level
            if amount == 0:
                return 2
            level = self.state.start_level + progress * amount
            self._set_level(level)
            return 1/100 * duration / abs(amount)

        raise Exception("bad state")
