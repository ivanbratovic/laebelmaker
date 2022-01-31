#!/usr/bin/env python

"""
Generates Traefik labels for use in e.g. Docker containers.
"""

from typing import *
from util.label import *

import readline
import argparse

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2021, Ivan Bratović"
__license__ = "MIT"

__version__ = "1.0.0"


def main() -> None:
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate Traefik labels")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="use interactive mode",
    )
    parser.add_argument(
        "-c",
        "--docker-compose",
        metavar="FILE",
        help="generate labels from a given Compose file",
    )

    args = parser.parse_args()

    if args.interactive:
        # Initialize readline interface
        HISTORY_FILE = ".labelmaker_history"
        readline.set_history_length(1000)
        try:
            readline.read_history_file(HISTORY_FILE)
            HISTORY_LEN = readline.get_current_history_length()
        except FileNotFoundError:
            open(HISTORY_FILE, "wb").close()
            HISTORY_LEN = 0
        assert False, "Interactive mode is not implemented yet"
        readline.write_history_file(HISTORY_FILE)
    if args.docker_compose:
        try:
            labels = gen_label_set_from_compose(args.docker_compose)
            print()
            print(*labels, sep="\n")
        except NoInformationException:
            print("Invalid docker-compose file given.")


if __name__ == "__main__":
    main()
