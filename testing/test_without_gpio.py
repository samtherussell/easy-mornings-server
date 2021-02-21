import unittest
from threading import Thread

from easy_mornings_server.lightcontroller import LightController
from easy_mornings_server.lightmanager import LightManager
from easy_mornings_server.webserver import WebServer


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
        light_controller = LightController(mock_gpio)
        light_manager = LightManager(light_controller)

        light_manager_thread = Thread(target=light_manager.run)
        light_manager_thread.start()

        WebServer(light_manager)