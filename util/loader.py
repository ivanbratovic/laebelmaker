from typing import *
from types import TracebackType

from itertools import cycle
from shutil import get_terminal_size
from threading import Thread
from time import sleep

"""
Module for displaying a loading animation in a separate thread.
"""

__author__ = "https://stackoverflow.com/users/3867406/ted"


class Loader:
    def __init__(
        self, desc: str = "Loading...", end: str = "Done!", timeout: float = 0.125
    ) -> None:
        """
        A loader-like context manager

        Args:
            desc (str, optional): The loader's description. Defaults to "Loading...".
            end (str, optional): Final print. Defaults to "Done!".
            timeout (float, optional): Sleep time between prints. Defaults to 0.1.
        """
        self.desc = desc
        self.end = end
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)
        self.steps = ["⠻", "⠽", "⠾", "⠷", "⠯", "⠟"]
        self.done = False

    def start(self) -> None:
        self._thread.start()

    def _animate(self) -> None:
        for c in cycle(self.steps):
            if self.done:
                break
            print(f"\r {c} {self.desc}", flush=True, end="")
            sleep(self.timeout)

    def __enter__(self) -> None:
        self.start()

    def stop(self) -> None:
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r ⠿ {self.end}", flush=True)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_inst: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        # handle exceptions with those variables ^
        self.stop()
