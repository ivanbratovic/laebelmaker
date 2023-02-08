"""Module containing Laebelmaker errors"""

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2022, Ivan Bratović"
__license__ = "MIT"


class UnknownRuleTypeException(Exception):
    """A Traefik rule tried to be created with an unkown type"""


class NoInformationException(Exception):
    """Laebelmaker cannot continue running due to lack of information"""
