#!/usr/bin/env python

"""
Generates Traefik labels for use in e.g. Docker containers.
"""

from typing import *
from util.label import *

import readline


__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2021, Ivan Bratović"
__license__ = "MIT"

__version__ = "1.0.0"


# Initialize readline interface
HISTORY_FILE = ".labelmaker_history"
readline.set_history_length(1000)
try:
    readline.read_history_file(HISTORY_FILE)
    HISTORY_LEN = readline.get_current_history_length()
except FileNotFoundError:
    open(HISTORY_FILE, "wb").close()
    HISTORY_LEN = 0


def main() -> None:
    readline.write_history_file(HISTORY_FILE)


if __name__ == "__main__":
    main()
