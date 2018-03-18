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

import sen
from sen import set_logging
from sen.exceptions import TerminateApplication
from sen.tui.init import Application
from sen.util import get_log_file_path, log_last_traceback

logger = logging.getLogger("sen")


def main():
    parser = argparse.ArgumentParser(
        description="Terminal User Interface for Docker Engine"
    )
    parser.add_argument(
        "--yolo", "--skip-prompt-for-irreversible-action",
        action="store_true",
        default=False,
        help="Don't prompt when performing irreversible actions, a.k.a. YOLO!"
    )
    exclusive_group = parser.add_mutually_exclusive_group()
    exclusive_group.add_argument(
            "--debug", action="store_true", default=None,
            help="Set logging level to debug"
            )

    args = parser.parse_args()

    # !IMPORTANT! make sure that sen does NOT log via `logging.info` b/c it sets up root logger
    # and adds StreamHandler which causes to display logs on stdout which is definitely what we
    # don't want in a terminal app (thanks to Slavek Kabrda for explanation)
    if args.debug:
        set_logging(level=logging.DEBUG, path=get_log_file_path())
        logger.debug("sen loaded from %s", sen.__file__)
    else:
        set_logging(level=logging.INFO, path=get_log_file_path())

    logger.info("application started")

    try:
        app = Application(yolo=args.yolo)
    except TerminateApplication as ex:
        print("Error: {0}".format(str(ex)), file=sys.stderr)
        return 1

    try:
        app.run()
    except KeyboardInterrupt:
        print("Quitting on user request.")
        return 1
    except Exception as ex:  # pylint: disable=broad-except
        log_last_traceback()
        if args.debug:
            raise
        else:
            # TODO: improve this message to be more thorough
            print("There was an error during program execution, see logs for more info.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
