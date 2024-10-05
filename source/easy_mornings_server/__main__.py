import argparse
import time
from threading import Thread
import logging
from sys import stdout

DEBUG = False
if not DEBUG:
    import pigpio

from .lightmanager import LightManager
from .lightcontroller import LightController
from .webserver import WebServer

log = logging.getLogger("easy_mornings_server")



def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--verbose', '-v', action='store_true')
    args = arg_parser.parse_args()
    gpio = None if DEBUG else pigpio.pi()
    run(gpio, args.verbose)


def run(gpio, verbose=None):

    log.addHandler(logging.StreamHandler(stdout))
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARNING)

    light_controller = LightController(gpio)
    light_manager = LightManager(light_controller)

    def start_light_manager():
        thread = Thread(target=light_manager.run)
        thread.daemon = True
        thread.start()
        return thread

    def start_web_server():
        thread = Thread(target=WebServer, args=(light_manager,))
        thread.daemon = True
        thread.start()
        return thread

    light_manager_thread = start_light_manager()
    web_server_thread = start_web_server()

    while True:
        if not light_manager_thread.is_alive():
            light_manager_thread = start_light_manager()
        if not web_server_thread.is_alive():
            web_server_thread = start_web_server()
        time.sleep(10)


if __name__ == '__main__':
    main()
