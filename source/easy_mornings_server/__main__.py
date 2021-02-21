import argparse
from threading import Thread
import logging
from sys import stdout

import pigpio

from .lightmanager import LightManager
from .lightcontroller import LightController
from .webserver import WebServer

log = logging.getLogger("easy_mornings_server")


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--verbose', '-v', action='store_true')
    args = arg_parser.parse_args()
    run(args.verbose)


def run(verbose=None):

    log.addHandler(logging.StreamHandler(stdout))
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARNING)

    gpio = pigpio.pi()
    light_controller = LightController(gpio)
    light_manager = LightManager(light_controller)

    light_manager_thread = Thread(target=light_manager.run)
    light_manager_thread.start()

    WebServer(light_manager)


if __name__ == '__main__':
    main()
