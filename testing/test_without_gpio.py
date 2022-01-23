import unittest

from easy_mornings_server.__main__ import run


class Test(unittest.TestCase):

    def test_run(self):

        class MockGPIO():
            def set_mode(self, pin, val):
                print(f"called set_mode({pin}, {val})")
            def set_PWM_range(self, pin, val):
                print(f"called set_PWM_range({pin}, {val})")
            def write(self, pin, val):
                print(f"called write({pin}, {val})")
            def set_PWM_dutycycle(self, pin, val):
                print(f"called set_PWM_dutycycle({pin}, {val})")

        mock_gpio = MockGPIO()
        run(mock_gpio, verbose=True)