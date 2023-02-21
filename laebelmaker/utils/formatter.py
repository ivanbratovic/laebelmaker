"""
Module for converting Label representations to many customizable formats.



Implemented formatters are at the end of the file.
"""

from typing import List, Callable

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2023, Ivan Bratović"
__license__ = "MIT"


class LabelFormatter:
    """A simple class with a main task of transforming
    a list of labels into a single, formatted string.

    Attributes:
        _formatter: a callable object performing a string transformation
            on a single label
        _sep: a string with which the transformed labels are separated with
        _end: a string with which is appended to the end of the formatted
            labels
    """

    def __init__(
        self,
        formatter: Callable[[str], str] = lambda x: x,
        sep: str = " ",
        end: str = "\n",
    ):
        self._formatter: Callable[[str], str] = formatter
        self._sep: str = sep
        self._end: str = end

    def format(self, labels: List[str]) -> str:
        """Joins a list of formatted labels with a
        defined separator and an end string."""
        pre_format: List[str] = list(map(self._formatter, labels))
        return self._sep.join(pre_format) + self._end


# What follows are specific formatter definitions


def formatter_none(labels: List[str]) -> str:
    """Simply puts each label in its own line"""
    return LabelFormatter(sep="\n").format(labels)


def formatter_docker(labels: List[str]) -> str:
    """Creates a string of `docker run` label options"""
    return LabelFormatter(
        formatter=lambda x: "--label '" + x + "'",
        sep=" ",
    ).format(labels)


def formatter_yaml(labels: List[str]) -> str:
    """Creates a YAML list of Docker Compose labels"""
    return LabelFormatter(
        formatter=lambda x: "  - " + x,
        sep="\n",
    ).format(labels)
