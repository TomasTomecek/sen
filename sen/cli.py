#!/usr/bin/env python3
"""
yes, this is python 3 ONLY project
"""

from __future__ import print_function

import sys

# let's be so gentle and print the error message even on python 2

if sys.version_info.major <= 2:
    error_message = """\
It looks like you are running sen with python 2. I'm sorry but sen is a python 3 only project.
Please see installation steps at official project page:

https://github.com/TomasTomecek/sen"""
    print(error_message, file=sys.stderr)
    sys.exit(2)

import argparse
import logging

from sen import set_logging
from sen.exceptions import TerminateApplication
from sen.tui.init import Application
from sen.util import get_log_file_path, log_vars_from_tback, setup_dirs


logger = logging.getLogger("sen")


def main():
    parser = argparse.ArgumentParser(
        description="Terminal User Interface for Docker Engine"
    )
    exclusive_group = parser.add_mutually_exclusive_group()
    exclusive_group.add_argument("--debug", action="store_true", default=None)

    args = parser.parse_args()

    if args.debug:
        set_logging(level=logging.DEBUG, path=get_log_file_path())
    else:
        set_logging(level=logging.INFO, path=get_log_file_path())

    logger.info("application started")

    try:
        ui = Application()
    except TerminateApplication as ex:
        print("Error: {0}".format(str(ex)), file=sys.stderr)
        return 1

    try:
        ui.run()
    except KeyboardInterrupt:
        print("Quitting on user request.")
        return 1
    # except AssertionError as ex:
        # if ex.args[0] == "rows, render mismatch":
        #     logger.error("race condition happened")
        #     # restart the ui
        #     # # continue
    #    return 2
    except Exception as ex:  # pylint: disable=broad-except
        log_vars_from_tback(process_frames=3 if args.debug else 0)  # show complete stack trace
        if args.debug:
            raise
        else:
            # TODO: improve this message to be more thorough
            print("There was an error during program execution, see logs for more info.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
