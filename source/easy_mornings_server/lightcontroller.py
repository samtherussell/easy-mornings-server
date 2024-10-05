import logging

DEBUG = False
if not DEBUG:
    import pigpio

log = logging.getLogger(__name__)

PIN = 18
PWM_RANGE = 255


class LightController:

    __slots__ = ['level', 'gpio']

    def __init__(self, gpio):
        self.level = 0
        self.gpio = gpio
        if not DEBUG:
            self.gpio.set_mode(PIN, pigpio.OUTPUT)
            self.gpio.set_PWM_range(PIN, PWM_RANGE)

    def is_on(self):
        return self.level == 0

    def set_level(self, percentage):
        self.level = percentage
        log.debug("light level is {}%".format(round(percentage * 100)))
        if percentage == 1:
            if not DEBUG:
                self.gpio.write(PIN, 1)
        elif percentage == 0:
            if not DEBUG:
                self.gpio.write(PIN, 0)
        else:
            value = 2 + round(percentage * percentage * (PWM_RANGE-2))
            if not DEBUG:
                self.gpio.set_PWM_dutycycle(PIN, value)

