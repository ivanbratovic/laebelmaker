"""Module containing datatypes used in other modules"""

from dataclasses import dataclass
from typing import List, Optional
from laebelmaker.errors import UnknownRuleTypeException, NoInformationException

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2023, Ivan Bratović"
__license__ = "MIT"


class Rule:  # pylint: disable=too-few-public-methods
    """
    Represents a Traefik HTTP Router rule
    """

    ALLOWED_RULES = ("Host", "Path", "PathPrefix", "Headers")

    def __init__(self, typ: str, *content: str) -> None:
        if typ not in self.ALLOWED_RULES:
            raise UnknownRuleTypeException("Invalid rule or not implemented yet")
        self.content = content
        self.typ = typ
        assert len(self.content) > 0, "A given rule must have content"
        if self.typ == "Headers":
            assert len(self.content) == 2, "Headers rule must have only key and value"

    def __str__(self) -> str:
        content = "`" + "`, `".join(self.content) + "`"
        return f"{self.typ}({content})"


class CombinedRule(Rule):  # pylint: disable=too-few-public-methods
    """
    Represents a combined Traefik HTTP Router rule by wrapping multiple
    simple rules.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self, *args: Rule | str
    ) -> None:
        self.operators: List[str] = []
        self.rules: List[Rule] = []

        for arg in args:
            if isinstance(arg, str):
                self.operators.append(arg)
            elif isinstance(arg, Rule):
                self.rules.append(arg)
            else:
                raise TypeError("CombinedRule args must be either strings or Rules")

    def __str__(self) -> str:
        full_rule: str = str(self.rules[0])
        for rule, operator in zip(self.rules[1:], self.operators):
            full_rule += f" {operator} "
            full_rule += str(rule)
        return f"({full_rule})"

    @classmethod
    def from_string(cls, string: str) -> Rule:
        """Creates a Rule object from a string"""
        url_parts: List[str] = string.split("/")
        rule: Optional[Rule] = None
        if len(url_parts) == 1:  # Domain OR Context-Path
            rule = Rule("Host", string)
        elif len(url_parts) == 2:  # Domain & Context-Path
            [domain, path] = url_parts
            domain_rule: Rule = Rule("Host", domain)
            context_rule: Rule = Rule("PathPrefix", f"/{path}")
            if domain and path:
                rule = CombinedRule(domain_rule, "&&", context_rule)
            elif domain:
                rule = domain_rule
            elif path:
                rule = context_rule
        if not rule:
            raise NoInformationException("Invalid hostname and context path definition")
        return rule


@dataclass
class ServiceConfig:  # pylint: disable=too-many-instance-attributes
    """
    Contains all data neccessary to generate required labels
    """

    deploy_name: str
    rule: Optional[Rule] = None
    url: str = ""
    port: int = 0
    https_enabled: bool = False
    https_redirection: bool = False
    web_entrypoint: str = "web"
    websecure_entrypoint: str = "websecure"
    tls_resolver: str = ""
