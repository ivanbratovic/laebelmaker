"""
Module for Label representations and easy handling.
"""

"""
Label:
Represents a string made up of tokens separated by
a delimiter with an assignment operator.

e.g. '{traefik.http.routers}.my_router.rule=Host(`www.hr`)'

"""

from typing import *
from dataclasses import dataclass

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2021, Ivan Bratović"
__license__ = "MIT"


ROUTER_PREFIX = "traefik.http.routers"
SERVICE_PREFIX = "traefik.http.services"


class UnknownRuleTypeException(Exception):
    pass


class Rule:
    """
    Represents a simple Traefik HTTP rule
    """

    ALLOWED_RULES = ("Host", "Path", "Headers")

    def __init__(self, t: str, content: List[str]):
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


@dataclass
class ServiceConfig:
    """
    Contains all data neccessary to generate required labels
    """

    name: str
    rule: Rule
    port: int = -1
    https_redir: bool = False
    web: str = "web"
    websecure: str = "websecure"
    tls_resolver: str = ""


def traefik_enable() -> str:
    return "traefik.enable=true"


def gen_simple_label_set_for_service(
    config: ServiceConfig, enable: bool = True
) -> List[str]:
    label_set = []
    if enable:
        label_set.append(traefik_enable())
    service_name = config.name
    # Traefik router
    rule = config.rule
    label_set.append(f"{ROUTER_PREFIX}.{service_name}.rule={rule}")
    if config.https_redir:
        # HTTPS router
        label_set.append(f"{ROUTER_PREFIX}.{service_name}.entrypoints={config.web}")
        label_set.append(f"{ROUTER_PREFIX}.{service_name}-https.rule={rule}")
        label_set.append(
            f"{ROUTER_PREFIX}.{service_name}-https.entrypoints={config.websecure}"
        )
        # Middleware for redirect
        middleware_name = f"{service_name}-redir"
        label_set.append(
            f"{ROUTER_PREFIX}.{service_name}.middlewares={middleware_name}"
        )
        label_set.append(
            f"traefik.http.middlewares.{middleware_name}.redirectscheme.scheme=https"
        )
        # Cert resolver
        resolver = config.tls_resolver
        assert (
            len(resolver) > 0
        ), "ServiceConfig must contain a TLS resolver when using HTTPS redirection"
        label_set.append(f"{ROUTER_PREFIX}.{service_name}-https.tls=true")
        label_set.append(
            f"{ROUTER_PREFIX}.{service_name}-https.tls.certresolver={resolver}"
        )
    port = config.port
    if port > 0:
        # Traefik service
        label_set.append(
            f"{SERVICE_PREFIX}.{service_name}.server.loadbalancer.port={port}"
        )
    return label_set
