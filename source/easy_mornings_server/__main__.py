import argparse
from threading import Thread
import logging
from sys import stdout
from .scheduler import Scheduler
from .lightmanager import LightManager
from .webserver import WebServer

log = logging.getLogger("easy_mornings_server")


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--config', '-c')
    arg_parser.add_argument('--verbose', '-v', action='store_true')
    args = arg_parser.parse_args()
    run(args.confi, args.verbose)


def run(config=None, verbose=None):

    log.addHandler(logging.StreamHandler(stdout))
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARNING)

    light_manager = LightManager()
    scheduler = Scheduler(light_manager, schedule_file=config)

    scheduler_thread = Thread(target=scheduler.run)
    scheduler_thread.start()

    WebServer(scheduler)


if __name__ == '__main__':
    main()
