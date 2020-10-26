import yaml
import logging
import time
from os import path
from datetime import date, datetime
from typing import List, Any
from easy_mornings_server.lightmanager import LightManager

log = logging.getLogger(__name__)


class SchedulerError(Exception):
    pass


CONSTANT_MODE = 'CONSTANT'
INCREASING_MODE = 'INCREASING'
DECREASING_MODE = 'DECREASING'
MODES = [CONSTANT_MODE, INCREASING_MODE, DECREASING_MODE]

MS_IN_DAY = 24 * 60 * 60 * 1000


class ScheduledItem:
    __slots__ = ['name', 'mode', 'start_time', 'end_time', 'repeat', 'days_of_week', 'active', 'dismissed']

    def __init__(self, name: str, mode: str, start_time: int = None, end_time: int = None, repeat: bool = False, days_of_week: List[str] = None):
        self.name = name
        if mode not in MODES:
            raise SchedulerError('mode must be one of {}. Not: {}'.format(','.join(MODES), mode))
        self.mode = mode
        if mode != CONSTANT_MODE and (start_time is None or end_time is None):
            raise SchedulerError('can only pick {} when start or end times are undefined'.format(','.join(MODES), mode))
        if (start_time is not None and not 0 <= start_time <= MS_IN_DAY) or (end_time is not None and not 0 <= end_time <= MS_IN_DAY):
            raise SchedulerError('start and end time must be within {} and {}'.format(0, MS_IN_DAY))
        self.start_time = start_time
        self.end_time = end_time
        self.repeat = repeat
        self.days_of_week = days_of_week
        if self.repeat and self.days_of_week is not None and len(self.days_of_week) == 0:
            raise SchedulerError("select at least one day which repeat is enabled")
        self.active = False
        self.dismissed = False

    @classmethod
    def from_dict(cls, config):
        try:
            name = config['name']
            mode = config['mode']
            start_time = config.get('start_time', None)
            end_time = config.get('end_time', None)
            repeat = config.get('repeat', False)
            days_of_week = config.get('days_of_week', None)
            if days_of_week is not None:
                days_of_week = days_of_week.split(',')
            return ScheduledItem(name, mode, start_time, end_time, repeat, days_of_week)
        except Exception as e:
            log.exception(e)
            return None

    def to_dict(self):
        ret = {
            'name': self.name,
            'mode': self.mode,
            'repeat': bool(self.repeat),
        }
        if self.start_time is not None:
            ret['start_time'] = self.start_time
        if self.end_time is not None:
            ret['end_time'] = self.end_time
        if self.days_of_week is not None:
            ret['days_of_week'] = ','.join(self.days_of_week)
        return ret

    def is_active(self, now, day_of_week: str = None):
        if day_of_week is not None and self.days_of_week is not None and day_of_week not in self.days_of_week:
            return False
        elif self.start_time is None or self.end_time is None:
            return True
        else:
            return self.start_time < now < self.end_time or self.end_time < self.start_time < now or now < self.end_time < self.start_time

    def __repr__(self):
        if self.start_time is None or self.end_time is None:
            when = 'forever'
        else:
            when = 'from {} to {}'.format(self.start_time, self.end_time)
        if self.repeat:
            count = 'repeating'
        else:
            count = 'once'
        if self.days_of_week is None:
            days = 'any day'
        else:
            days = 'on {}'.format(','.join(self.days_of_week))
        return 'name: {}, light on {} {} at a {} level {}'.format(self.name, count, days, self.mode.lower(), when)


class Scheduler:
    __slots__ = ['light_manager', 'schedule', 'active', 'manual_override', 'save_file']

    def __init__(self, light_manager: LightManager, schedule: List[ScheduledItem] = None, schedule_file: str = None):
        self.light_manager = light_manager
        self.schedule = schedule or []
        self.active = None
        self.manual_override = None
        self.save_file = schedule_file
        if schedule_file is not None and path.exists(schedule_file):
            self.load_schedule_file(schedule_file)
        log.debug("Scheduler started with {} items".format(len(self.schedule)))

    def load_schedule_file(self, filename: str):
        try:
            with open(filename, 'r') as f:
                config = f.read()
            config = yaml.safe_load(config)
            self.load_schedule(config)
        except Exception as e:
            log.exception(e)

    def load_schedule(self, config: yaml):
        try:
            schedule = []
            for item in config:
                item = ScheduledItem.from_dict(item)
                if item:
                    assert_no_conflict(schedule, item)
                    schedule.append(item)
            self.schedule = schedule
        except Exception as e:
            log.exception(e)

    def save_schedule(self):
        if self.save_file is not None:
            config = yaml.safe_dump(self.get_schedule_dicts())
            with open(self.save_file, 'w') as f:
                f.write(config)

    def get_schedule_dicts(self):
        return [item.to_dict() for item in self.get_schedule()]

    def get_schedule(self):
        return self.schedule

    def add_item(self, item):
        assert_no_conflict(self.schedule, item)
        self.schedule.append(item)
        self.save_schedule()

    def remove_item(self, name):
        schedule = []
        found = False
        for item in self.schedule:
            if item.name == name:
                found = True
            else:
                schedule.append(item)
        if found:
            self.schedule = schedule
            self.save_schedule()
        if self.active is not None and self.active.name == name:
            self.end_active_item()
        return found

    def set_manual_override(self, item: ScheduledItem):
        self.manual_override = item

    def clear_manual_override(self):
        self.manual_override = None
        self.light_manager.set_level(0)

    def dismiss_active(self):
        self.active.dismissed = True
        self.end_active_item()

    def run(self):
        log.debug("Scheduler is running")
        sleep_time = 0.1
        while True:
            time.sleep(sleep_time)
            if self.run_timestep():
                sleep_time = 0.1
            else:
                sleep_time = min(sleep_time*2, 2)

    def run_timestep(self):
        now = milli(datetime.now().time())
        day_of_week = date.today().strftime('%A')
        for item in self.schedule:
            if not item.active:
                if item.dismissed and not item.is_active(now, day_of_week):
                    item.dismissed = False
                elif not item.dismissed and item.is_active(now, day_of_week):
                    self.switch_active_item(item)
                    return True

        active = self.manual_override or self.active

        if active is not None:
            if active.is_active(now):
                if active.mode == CONSTANT_MODE:
                    level = 1
                elif active.mode == INCREASING_MODE:
                    level = (now - active.start_time) / (active.end_time - active.start_time)
                elif active.mode == DECREASING_MODE:
                    level = 1 - ((now - active.start_time) / (active.end_time - active.start_time))
                else:
                    raise RuntimeError("Mode is {}".format(active.mode))
                self.light_manager.set_level(level)
            elif self.manual_override:
                self.clear_manual_override()
            else:
                self.end_active_item()
            return True

        return False

    def switch_active_item(self, item: ScheduledItem):
        self.end_active_item()
        self.active = item
        self.active.active = True

    def end_active_item(self):
        if self.active:
            item = self.active
            self.active = None
            self.light_manager.set_level(0)
            if item.repeat:
                item.active = False
            else:
                self.remove_item(item.name)


def assert_no_conflict(items: List[ScheduledItem], item: ScheduledItem):
    if item.name in (a.name for a in items):
        raise SchedulerError("Two alarms with the same name: {}".format(item.name))
    for other in items:
        if other.days_of_week is None or any((day in other.days_of_week for day in item.days_of_week)):
            if other.start_time <= item.start_time < other.end_time or item.start_time <= other.start_time < item.end_time:
                raise SchedulerError("Two items {} and {} overlap".format(item.name, other.name))


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
