"""
Module for Label representations and easy handling.
"""

"""
Label:
Represents a string made up of tokens separated by
a delimiter with an assignment operator.

e.g. 'traefik.http.routers.my_router.rule=Host(`www.hr`)'

"""

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2023, Ivan Bratović"
__license__ = "MIT"

import yaml
from typing import Any, Optional, List, Tuple, Dict
from dataclasses import asdict
from laebelmaker.datatypes import ServiceConfig, Rule, CombinedRule
from laebelmaker.errors import NoInformationException
from laebelmaker.utils.loader import Loader
from laebelmaker.utils.input import input_item, query_selection, query_change


ROUTER_PREFIX = "traefik.http.routers"
SERVICE_PREFIX = "traefik.http.services"


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
    rule: Optional[Rule] = config.rule
    assert rule, "config.rule should not be None"
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
    https_related_keys: List[str] = [
        "tls_resolver",
        "web_entrypoint",
        "websecure_entrypoint",
    ]
    keys_with_default_value_name: List[str] = ["url"]
    for key, value in asdict(config).items():
        if key in ("deploy_name", "rule"):
            continue

        if key in https_related_keys and not config.https_redirection:
            continue

        if key == "port" and config.port:
            continue

        default_value: Optional[str] = None
        if key in keys_with_default_value_name:
            default_value = config.deploy_name

        typ = type(config.__getattribute__(key))

        if not value:
            new_value: Any

            while True:
                new_value = input_item(key, typ, default_value)
                if new_value == "":
                    print(f"Input of {key!r} is mandatory.")
                else:
                    break
            config.__setattr__(key, new_value)
        else:
            config.__setattr__(key, query_change(value, key))

        if key == "url":
            url_parts: List[str] = config.url.split("/")
            rule: Optional[Rule] = None
            if len(url_parts) == 1:  # Domain OR Context-Path
                rule = Rule("Host", config.url)
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
                raise NoInformationException(
                    "Invalid hostname and context path definition"
                )
            config.rule = rule

    return gen_simple_label_set_for_service(config)


def gen_label_set_from_user(name: str = "") -> Tuple[str, List[str]]:
    if not name:
        name = input_item("deploy_name", str)
    # Get URL
    config: ServiceConfig = ServiceConfig(name)
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
    # Generate config
    config = ServiceConfig(name, port=port)

    return gen_label_set_from_limited_info(config)


def gen_label_set_from_container(container_name: str) -> Tuple[str, List[str]]:
    import docker

    DOCKER_CLIENT = docker.from_env()
    try:
        container = DOCKER_CLIENT.containers.get(container_name)
    except docker.errors.NotFound:
        raise NoInformationException(f"Invalid container: {container_name!r}")

    return gen_label_set_from_docker_attrs(container.attrs, container_name)


def gen_label_set_from_image(
    image_name: str, override_name: str = ""
) -> Tuple[str, List[str]]:
    import docker

    DOCKER_CLIENT = docker.from_env()

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
        services_dict: Dict[str, Any] = data["services"]
    except KeyError:
        raise NoInformationException(f"No 'services' key in {path!r}.")
    if not services_dict:
        raise NoInformationException(f"No services defined in {path!r}.")
    possible_services = [str(service) for service in services_dict]
    service_name: str = query_selection(possible_services, "service")
    service_dict = services_dict[service_name]
    # Get entrypoint names
    try:
        build_def: str | Dict[str, Any] = service_dict["build"]
        base_dir_compose: str = "/".join(path.split("/")[:-1])
        build_dir: str
        if isinstance(build_def, str):
            build_dir = f"{base_dir_compose}/{build_def}/"
        elif isinstance(build_def, dict):
            build_dir = f"{base_dir_compose}/{build_def['context']}/"
        build_dir = build_dir.replace("/./", "/")
        raise NotImplementedError(
            f"Parsing Dockerfile in {build_dir!r} is not implemented yet"
        )
    except KeyError:
        try:
            image_name: str = service_dict["image"]
        except KeyError:
            raise NoInformationException(
                f"No image or build information found in service definition in {path!r}."
            )
        try:
            import docker
        except ModuleNotFoundError:
            print(
                "The docker module is not installed. Laebelmaker will have to query some extra information..."
            )
            return gen_label_set_from_user(service_name)
        try:
            title, label_set = gen_label_set_from_image(image_name, service_name)
            if label_set:
                return title, label_set
            else:
                return gen_label_set_from_user(service_name)
        except docker.errors.ImageNotFound:
            raise NoInformationException(
                f"Invalid docker image: {image_name!r} in {path!r}."
            )
        except docker.errors.NotFound:
            raise NoInformationException(
                f"Invalid image tag: {image_name!r} in {path!r}."
            )
    except TypeError:
        raise NoInformationException(f"Invalid service: {service_name!r} in {path!r}")
