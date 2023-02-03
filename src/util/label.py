"""
Module for Label representations and easy handling.
"""

"""
Label:
Represents a string made up of tokens separated by
a delimiter with an assignment operator.

e.g. 'traefik.http.routers.my_router.rule=Host(`www.hr`)'

"""

from typing import *
from dataclasses import dataclass, asdict
from util.loader import Loader
from util.input import input_item, query_selection, query_change
from util.errors import NoInformationException, UnknownRuleTypeException
import yaml

try:
    import docker
except ModuleNotFoundError:
    print("Install the docker module for advanced Docker support")
    docker = None

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2022, Ivan Bratović"
__license__ = "MIT"


ROUTER_PREFIX = "traefik.http.routers"
SERVICE_PREFIX = "traefik.http.services"
if docker:
    DOCKER_CLIENT = docker.from_env()


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
        return full_rule


@dataclass
class ServiceConfig:
    """
    Contains all data neccessary to generate required labels
    """

    deploy_name: str
    rule: Rule
    port: int = -1
    https_redirection: bool = False
    web_entrypoint: str = "web"
    websecure_entrypoint: str = "websecure"
    tls_resolver: str = ""


def traefik_enable() -> str:
    return "traefik.enable=true"


def gen_simple_label_set_for_service(
    config: ServiceConfig, enable: bool = True
) -> Tuple[str, List[str]]:
    label_set: List[str] = []
    if enable:
        label_set.append(traefik_enable())
    service_name: str = config.deploy_name
    # Traefik router
    rule: Rule = config.rule
    label_set.append(f"{ROUTER_PREFIX}.{service_name}.rule={rule}")
    if config.https_redirection:
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
    return config.deploy_name, label_set


def gen_label_set_from_limited_info(config: ServiceConfig) -> Tuple[str, List[str]]:
    for key, value in asdict(config).items():
        if key in ("deploy_name", "rule"):
            continue

        if (
            key in ("tls_resolver", "web_entrypoint", "websecure_entrypoint")
            and not config.https_redirection
        ):
            continue

        if key == "port" and config.port:
            continue

        typ = type(config.__getattribute__(key))

        if not value:
            new_value: Optional[Any] = None
            while True:
                new_value = input_item(key, typ)
                if new_value == "":
                    print(f"Input of {key!r} is mandatory.")
                else:
                    break
            config.__setattr__(key, new_value)
        else:
            config.__setattr__(key, typ(query_change(value, key)))
    return gen_simple_label_set_for_service(config)


def gen_label_set_from_user(name: str = "") -> Tuple[str, List[str]]:
    if not name:
        name = input_item("deploy_name", str)
    # Create appropriate Rule object
    url: str = query_change(name, "hostname and context path")
    url_parts: List[str] = url.split("/")
    if len(url_parts) == 1:  # Domain OR Context-Path
        rule = Rule("Host", url)
    elif len(url_parts) == 2:  # Domain & Context-Path
        [domain, path] = url_parts
        domain_rule: Rule = Rule("Host", domain)
        context_rule: Rule = Rule("Path", f"/{path}")
        if domain and path:
            rule = CombinedRule(domain_rule, "&&", context_rule)
        elif domain:
            rule = domain_rule
        elif path:
            rule = context_rule
        else:
            raise NoInformationException("Invalid hostname and context path definition")

    config: ServiceConfig = ServiceConfig(name, rule)
    return gen_label_set_from_limited_info(config)


def get_tcp_ports_from_attrs(attrs: Dict[str, Any]) -> List[int]:
    try:
        exposed_ports: List[str] = attrs["Config"]["ExposedPorts"].keys()
    except KeyError:
        print("Could not get ports from docker attributes.")
        return []
    # Get only TCP exposed ports
    filtered_ports: List[str] = list(filter(lambda port: "tcp" in port, exposed_ports))
    # Strip the suffix '/tcp' and convert to int
    tcp_ports: List[int] = list(map(int, map(lambda port: port[:-4], filtered_ports)))
    return tcp_ports


def gen_label_set_from_docker_attrs(
    attrs: Dict[str, Any], name: str
) -> Tuple[str, List[str]]:
    # Get port
    ports = get_tcp_ports_from_attrs(attrs)
    if not ports:
        ports = [int(input("Please manually input the port number: "))]
    port = query_selection(ports, "port")
    # Get hostname
    hostname = query_change(name, "hostname")
    # Generate config
    config = ServiceConfig(name, rule=Rule("Host", hostname), port=port)

    return gen_label_set_from_limited_info(config)


def gen_label_set_from_container(container_name: str) -> Tuple[str, List[str]]:
    if not docker:
        return ("", [])

    try:
        container = DOCKER_CLIENT.containers.get(container_name)
    except docker.errors.NotFound:
        raise NoInformationException(f"Invalid container: {container_name!r}")

    return gen_label_set_from_docker_attrs(container.attrs, container_name)


def gen_label_set_from_image(
    image_name: str, override_name: str = ""
) -> Tuple[str, List[str]]:
    if not docker:
        return ("", [])

    try:
        DOCKER_CLIENT.images.get(image_name)
    except docker.errors.ImageNotFound:
        # TODO: Consider using the Docker Registry HTTP API for getting image data
        print("Pulling image:")
        with Loader(
            f"{image_name} Pulling", f"{image_name} Pulled", f"{image_name} Failed"
        ):
            DOCKER_CLIENT.images.pull(image_name)
    image = DOCKER_CLIENT.images.get(image_name)
    base_image_name = image_name.split(":")[0].split("/")[-1]
    name: str = base_image_name
    if override_name:
        name = override_name
    return gen_label_set_from_docker_attrs(image.attrs, name)


def gen_label_set_from_compose(path: str) -> Tuple[str, List[str]]:
    with open(path, "r") as docker_compose:
        data = yaml.safe_load(docker_compose)
    if not data or not isinstance(data, dict):
        raise NoInformationException(f"File {path!r} does not contain valid YAML.")
    # Get service name
    try:
        possible_services = [str(service) for service in data["services"]]
    except KeyError:
        raise NoInformationException(f"No services defined in {path!r}.")
    service_name: str = query_selection(possible_services, "service")
    # Get entrypoint names
    try:
        service_dict: Dict[str, Any] = data["services"][service_name]
        image_name: str = service_dict["image"]
        try:
            title, label_set = gen_label_set_from_image(image_name, service_name)
            if label_set:
                return title, label_set
        except docker.errors.ImageNotFound:
            raise NoInformationException(
                f"Invalid docker image: {image_name!r} in {path!r}."
            )
        except docker.errors.NotFound:
            raise NoInformationException(
                f"Invalid image tag: {image_name!r} in {path!r}."
            )
        print(
            "The docker module is not installed. We'll have to query some information from you..."
        )
        return gen_label_set_from_user(service_name)
    except KeyError:
        try:
            build_file = service_dict["build"]
        except KeyError:
            raise NoInformationException(
                f"No image or build information found in service definition in {path!r}."
            )
        raise NotImplementedError("Parsing Dockerfile is not implemented yet")
    except TypeError:
        raise NoInformationException(f"Invalid service: {service_name!r} in {path!r}")
