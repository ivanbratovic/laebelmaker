"""
Module for displaying a loading animation in a separate thread.

Source: https://stackoverflow.com/questions/22029562/
"""

__author__ = "https://stackoverflow.com/users/3867406/ted"

from typing import Optional, Type
from types import TracebackType

from itertools import cycle
from shutil import get_terminal_size
from threading import Thread
from time import sleep


class Loader:
    """
    A loader-like context manager

    Args:
        desc (str, optional): The loader's description. Defaults to "Loading...".
        end (str, optional): Final print after loading. Defaults to "Done!".
        errend (str, optional): Final print in case of error. Defaults to "Failed!".
        timeout (float, optional): Sleep time between prints. Defaults to 0.1.
    """

    def __init__(
        self,
        desc: str = "Loading...",
        end: str = "Done!",
        errend: str = "Failed!",
        timeout: float = 0.125,
    ) -> None:
        self.desc = desc
        self.end = end
        self.errend = errend
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)
        self.steps = ["⠻", "⠽", "⠾", "⠷", "⠯", "⠟"]
        self.done = False

    def start(self) -> None:
        """Starts the loader thread"""
        self._thread.start()

    def _animate(self) -> None:
        """Draw the animation loop"""
        for c in cycle(self.steps):
            if self.done:
                break
            print(f"\r {c} {self.desc}", flush=True, end="")
            sleep(self.timeout)

    def __enter__(self) -> None:
        self.start()

    def stop(self, *, error: bool = False) -> None:
        """Draw the end of the animation"""
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        end: str = self.end
        if error:
            end = self.errend
        print(f"\r ⠿ {end}", flush=True)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_inst: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        # handle exceptions with those variables ^
        if exc_type:
            self.stop(error=True)
        else:
            self.stop()
