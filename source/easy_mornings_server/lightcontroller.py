import logging

log = logging.getLogger(__name__)


class LightController:

    __slots__ = ['percentage']

    def __init__(self):
        self.percentage = 0

    def is_on(self):
        return self.percentage == 0

    def set_level(self, percentage):
        log.warning("light level is {}%".format(round(percentage * 100)))
