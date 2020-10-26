import logging

log = logging.getLogger(__name__)


class LightManager:

    __slots__ = ['percentage']

    def __init__(self):
        self.percentage = 0

    def is_on(self):
        return self.percentage == 0

    def set_level(self, percentage):
        if self.percentage != percentage:
            self.percentage = percentage
            log.warning("light level is {}%".format(round(percentage * 100)))
