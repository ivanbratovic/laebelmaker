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
from util.loader import Loader
from util.formatter import *
import yaml
import docker


__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2021, Ivan Bratović"
__license__ = "MIT"


ROUTER_PREFIX = "traefik.http.routers"
SERVICE_PREFIX = "traefik.http.services"
DOCKER_CLIENT = docker.from_env()


class UnknownRuleTypeException(Exception):
    """A Traefik rule tried to be created with an unkown type"""


class NoInformationException(Exception):
    """Laebelmaker cannot continue running due to lack of information"""


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
            f"{SERVICE_PREFIX}.{service_name}.loadbalancer.server.port={port}"
        )
    return label_set


def query_selection(options: list[Any], item_name: str, default_index: int = 0) -> Any:
    if len(options) < 1:
        raise NoInformationException(f"No {item_name} choices given.")
    if len(options) > 1:
        print(f"Found multiple {item_name}s.")
        for i, service in enumerate(options):
            print(f" {i+1}. {service}")
        answer = input(f"Select {item_name} ({default_index + 1}): ")
        if len(answer) == 0:
            selection = default_index
        else:
            selection = int(answer) - 1
        assert selection in range(0, len(options)), "Selected index out of range"
        selected = options[selection]
    else:
        selected = options[0]
    return selected


def query_change(item: Any, item_name: str) -> Any:
    typ = type(item)
    answer = input(f"Change {item_name} ('{item}'): ")
    if len(answer) != 0:
        item = answer
    return typ(item)


def get_children_keys(d: Dict[str, Any]) -> List[str]:
    return [str(key) for key in d]


def get_tcp_ports_from_attrs(attrs: Dict[str, Any]) -> List[int]:
    # Get only TCP exposed ports
    exposed_ports = attrs["Config"]["ExposedPorts"].keys()
    filtered_ports: List[str] = list(filter(lambda port: "tcp" in port, exposed_ports))
    # Strip the suffix '/tcp' and convert to int
    tcp_ports: List[int] = list(map(int, map(lambda port: port[:-4], filtered_ports)))
    return tcp_ports


def gen_label_set_from_docker_attrs(attrs: Dict[str, Any], name: str) -> List[str]:
    # Get port
    try:
        ports = get_tcp_ports_from_attrs(attrs)
    except KeyError:
        print("Could not get ports from docker attributes.")
        ports = [int(input("Please manually input the port number: "))]
    port = query_selection(ports, "port")
    # Get hostname
    hostname = query_change(name, "hostname")
    # Generate config
    config = ServiceConfig(name=name, rule=Rule("Host", [hostname]), port=port)
    # Get HTTPS redirect
    https_redir = query_change("no", "HTTPS redirection")
    if https_redir.lower() in ("y", "yes"):
        config.https_redir = True
        tls_resolver = input("TLS resolver to use: ")
        config.tls_resolver = tls_resolver
    return gen_simple_label_set_for_service(config)


def gen_label_set_from_container(container_name: str) -> List[str]:
    try:
        container = DOCKER_CLIENT.containers.get(container_name)
    except docker.errors.NotFound:
        raise NoInformationException("Could not find the info of the given container")

    return gen_label_set_from_docker_attrs(container.attrs, container_name)


def gen_label_set_from_image(image_name: str, override_name: str = "") -> List[str]:
    try:
        DOCKER_CLIENT.images.get(image_name)
    except docker.errors.ImageNotFound:
        # TODO: Consider using the Docker Registry HTTP API for getting image data
        print("Pulling image:")
        with Loader(f"{image_name} Pulling", f"{image_name} Pulled"):
            DOCKER_CLIENT.images.pull(image_name)
    finally:
        image = DOCKER_CLIENT.images.get(image_name)
    base_image_name = image_name.split(":")[0].split("/")[-1]
    if override_name:
        name = override_name
    else:
        name = base_image_name
    return gen_label_set_from_docker_attrs(image.attrs, name)


def gen_label_set_from_compose(path: str) -> List[str]:
    try:
        with open(path, "r") as docker_compose:
            data = yaml.safe_load(docker_compose)
    except FileNotFoundError:
        print(f"Cannot open file {path} for reading.")
        raise
    # Get service name
    possible_services = get_children_keys(data["services"])
    service_name = query_selection(possible_services, "service")
    service = data["services"][service_name]
    # Get image data
    try:
        image_name = service["image"]
        return gen_label_set_from_image(image_name, service_name)
    except KeyError:
        try:
            build_file = service["build"]
        except KeyError:
            raise NoInformationException(
                "No image or build information found in service definition"
            )
        assert False, "Parsing Dockerfile is not implemented yet"
