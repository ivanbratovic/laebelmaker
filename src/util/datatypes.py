"""Module containing datatypes used in other modules"""

from typing import List
from util.errors import UnknownRuleTypeException
from dataclasses import dataclass


class Rule:
    """
    Represents a Traefik HTTP Router rule
    """

    ALLOWED_RULES = ("Host", "Path", "Headers")

    def __init__(self, t: str, *content: str) -> None:
        if t not in self.ALLOWED_RULES:
            raise UnknownRuleTypeException("Invalid rule or not implemented yet")
        self.content = content
        self.typ = t
        assert len(self.content) > 0, "A given rule must have content"
        if self.typ == "Headers":
            assert len(self.content) == 2, "Headers rule must have only key and value"

    def __str__(self) -> str:
        content = "`" + "`, `".join(self.content) + "`"
        return f"{self.typ}({content})"


class CombinedRule(Rule):
    """
    Represents a combined Traefik HTTP Router rule by wrapping multiple
    simple rules.
    """

    def __init__(self, *args: Rule | str) -> None:
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


@dataclass
class ServiceConfig:
    """
    Contains all data neccessary to generate required labels
    """

    deploy_name: str
    rule: Rule
    port: int = 0
    https_redirection: bool = False
    web_entrypoint: str = "web"
    websecure_entrypoint: str = "websecure"
    tls_resolver: str = ""
