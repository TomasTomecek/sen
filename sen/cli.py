#!/usr/bin/python3
"""
yes, this is python 3 ONLY project
"""
import argparse
import logging

from sen.tui.init import UI
from sen import set_logging


logger = logging.getLogger("sen")


def main():
    parser = argparse.ArgumentParser(
        description="Terminal User Interface for Docker Engine"
    )
    exclusive_group = parser.add_mutually_exclusive_group()
    exclusive_group.add_argument("--debug", action="store_true", default=None)

    args = parser.parse_args()

    if args.debug:
        set_logging(level=logging.DEBUG)
    else:
        set_logging(level=logging.INFO)

    logger.info("application started")

    ui = UI()

    try:
        ui.run()
    except KeyboardInterrupt:
        print("Quitting on user request.")
        return -1
    except Exception as ex:  # pylint: disable=broad-except
        if args.debug:
            raise
        else:
            logger.error("Exception caught: %r", ex)
            return -1

if __name__ == "__main__":
    main()
