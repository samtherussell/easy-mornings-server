import logging
import pigpio

log = logging.getLogger(__name__)

PIN = 18
PWM_RANGE = 256

class LightController:

    __slots__ = ['percentage', 'gpio']

    def __init__(self):
        self.percentage = 0
        self.gpio = pigpio.pi()
        self.gpio.set_mode(PIN, pigpio.OUTPUT)
        self.gpio.set_PWM_range(PIN, PWM_RANGE)
        print("setup pigpio")

    def is_on(self):
        return self.percentage == 0

    def set_level(self, percentage):
        self.percentage = percentage
        log.warning("light level is {}%".format(round(percentage * 100)))
        if percentage == 1:
            self.gpio.write(PIN, 1)
        elif percentage == 0:
            self.gpio.write(PIN, 0)
        else:
            value = round(percentage * percentage * PWM_RANGE)
            self.gpio.set_PWM_dutycycle(PIN, value)
