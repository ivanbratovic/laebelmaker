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
from dataclasses import dataclass, asdict
from util.loader import Loader
from util.formatter import *
import yaml
import readline

try:
    import docker
except ModuleNotFoundError:
    print("Install the docker module for advanced Docker support")
    docker = False

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2021, Ivan Bratović"
__license__ = "MIT"


ROUTER_PREFIX = "traefik.http.routers"
SERVICE_PREFIX = "traefik.http.services"
if docker:
    DOCKER_CLIENT = docker.from_env()


class UnknownRuleTypeException(Exception):
    """A Traefik rule tried to be created with an unkown type"""


class NoInformationException(Exception):
    """Laebelmaker cannot continue running due to lack of information"""


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


class CombinedRule:
    """
    Represents a combined Traefik HTTP Router rule by wrapping multiple
    simple rules.
    """

    def __init__(self, *args: Rule | str) -> None:
        self.operators: List[str] = []
        self.rules: List[Rule] = []

        for arg in args:
            if type(arg) is str:
                self.operators.append(arg)
            if type(arg) is Rule:
                self.rules.append(arg)

    def __str__(self) -> str:
        full_rule: str = str(self.rules[0])
        for rule, operator in zip(self.rules[1:], self.operators):
            full_rule += f" {operator} "
            full_rule += str(rule)
        return full_rule


@dataclass
class ServiceConfig:
    """
    Contains all data neccessary to generate required labels
    """

    name: str
    rule: Rule
    port: int = -1
    https_redir: bool = False
    web_entrypoint: str = "web"
    websecure_entrypoint: str = "websecure"
    tls_resolver: str = ""


def traefik_enable() -> str:
    return "traefik.enable=true"


def gen_simple_label_set_for_service(
    config: ServiceConfig, enable: bool = True
) -> List[str]:
    label_set = []
    if enable:
        label_set.append(traefik_enable())
    service_name: str = config.name
    # Traefik router
    rule: Rule = config.rule
    label_set.append(f"{ROUTER_PREFIX}.{service_name}.rule={rule}")
    if config.https_redir:
        # HTTPS router
        label_set.append(
            f"{ROUTER_PREFIX}.{service_name}.entrypoints={config.web_entrypoint}"
        )
        label_set.append(f"{ROUTER_PREFIX}.{service_name}-https.rule={rule}")
        label_set.append(
            f"{ROUTER_PREFIX}.{service_name}-https.entrypoints={config.websecure_entrypoint}"
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


def input_prefilled(prompt: str, text: str) -> str:
    def hook() -> None:
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def input_item(name: str, type: type) -> Any:
    if type == int:
        hint_text = " (integer)"
    elif type == bool:
        hint_text = " (yes/no)"
    else:
        hint_text = ""
    new_value = input(f"Enter value for '{name}'{hint_text}: ")
    if type == bool and new_value.lower() in ("false", "no", "0"):
        new_value = ""
    return type(new_value)


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
    answer = input_prefilled(f"Enter new value for '{item_name}': ", item)
    if len(answer) != 0:
        item = answer
    return typ(item)


def get_children_keys(d: Dict[str, Any]) -> List[str]:
    return [str(key) for key in d]


def gen_label_set_from_limited_info(config: ServiceConfig) -> List[str]:
    for key, value in asdict(config).items():
        if key in ("name", "rule"):
            continue

        if (
            key in ("tls_resolver", "web_entrypoint", "websecure_entrypoint")
            and not config.https_redir
        ):
            continue

        if key == "port" and config.port != -1:
            continue

        typ = type(config.__getattribute__(key))

        if not value:
            new_value = input_item(key, typ)
            config.__setattr__(key, new_value)
        else:
            config.__setattr__(key, typ(query_change(value, key)))
    return gen_simple_label_set_for_service(config)


def gen_label_set_from_user(name: str = "") -> List[str]:
    if not name:
        name = input_item("name", str)
    # Get hostname
    hostname = query_change(name, "hostname")
    rule = Rule("Host", hostname)
    config = ServiceConfig(name, rule)
    return gen_label_set_from_limited_info(config)


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
    config = ServiceConfig(name=name, rule=Rule("Host", hostname), port=port)

    return gen_label_set_from_limited_info(config)


def gen_label_set_from_container(container_name: str) -> List[str] | NoReturn:
    if not docker:
        return []

    try:
        container = DOCKER_CLIENT.containers.get(container_name)
    except docker.errors.NotFound:
        raise NoInformationException("Could not find the info of the given container")

    return gen_label_set_from_docker_attrs(container.attrs, container_name)


def gen_label_set_from_image(image_name: str, override_name: str = "") -> List[str]:
    if not docker:
        return []
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
    # Get entrypoint names
    try:
        image_name = service["image"]
        if label_set := gen_label_set_from_image(image_name, service_name):
            return label_set
        print(
            "The docker module is not installed. We'll have to query some information from you..."
        )
        return gen_label_set_from_user(service_name)
    except KeyError:
        try:
            build_file = service["build"]
        except KeyError:
            raise NoInformationException(
                "No image or build information found in service definition"
            )
        assert False, "Parsing Dockerfile is not implemented yet"
