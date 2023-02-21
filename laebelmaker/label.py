"""
Module for Label representations and easy handling.

Label:
Represents a string made up of tokens separated by
a delimiter with an assignment operator.

e.g. 'traefik.http.routers.my_router.rule=Host(`www.hr`)'

"""

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2023, Ivan Bratović"
__license__ = "MIT"

from typing import Any, Optional, List, Tuple, Dict
from dataclasses import asdict
import yaml
from laebelmaker.datatypes import ServiceConfig, Rule, CombinedRule
from laebelmaker.errors import NoInformationException
from laebelmaker.utils.loader import Loader
from laebelmaker.utils.input import input_item, query_selection, query_change


ROUTER_PREFIX = "traefik.http.routers"
SERVICE_PREFIX = "traefik.http.services"


def traefik_enable() -> str:
    """Returns a static string with a label that enables Traefik explicitly."""
    return "traefik.enable=true"


def gen_simple_label_set_for_service(
    config: ServiceConfig, enable: bool = True
) -> Tuple[str, List[str]]:
    """Generates a label set for a HTTP service from a given config."""
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


def fill_missing_info(config: ServiceConfig, attr_name: str, value: Any) -> None:
    """Fills a single missing value from a ServiceConfig object"""
    https_related_attrs: List[str] = [
        "tls_resolver",
        "web_entrypoint",
        "websecure_entrypoint",
    ]
    attrs_with_default_value_name: List[str] = ["url"]

    if attr_name in ("deploy_name", "rule"):
        return

    if attr_name in https_related_attrs and not config.https_redirection:
        return

    if attr_name == "port" and config.port:
        return

    default_value: Optional[str] = None
    if attr_name in attrs_with_default_value_name:
        default_value = config.deploy_name

    typ = type(getattr(config, attr_name))

    if not value:
        new_value: Any

        while True:
            new_value = input_item(attr_name, typ, default_value)
            if new_value == "":
                print(f"Input of {attr_name!r} is mandatory.")
            else:
                break
        setattr(config, attr_name, new_value)
    else:
        setattr(config, attr_name, query_change(value, attr_name))

    if attr_name == "url":
        config.rule = CombinedRule.from_string(config.url)


def gen_label_set_from_limited_info(config: ServiceConfig) -> Tuple[str, List[str]]:
    """Generates a label set with from an incomplete config object"""
    for key, value in asdict(config).items():
        fill_missing_info(config, key, value)

    return gen_simple_label_set_for_service(config)


def gen_label_set_from_user(name: str = "") -> Tuple[str, List[str]]:
    """Generates a label set from scratch, without any prior info."""
    if not name:
        name = input_item("deploy_name", str)
    # Get URL
    config: ServiceConfig = ServiceConfig(name)
    return gen_label_set_from_limited_info(config)


def get_tcp_ports_from_attrs(attrs: Dict[str, Any]) -> List[int]:
    """Gets possible ports from a given Docker attributes dictionary."""
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
    """Generates a label set from a given Docker attributes dictionary."""
    # Get port
    ports = get_tcp_ports_from_attrs(attrs)
    if not ports:
        ports = [int(input("Please manually input the port number: "))]
    port = query_selection(ports, "port")
    # Generate config
    config = ServiceConfig(name, port=port)

    return gen_label_set_from_limited_info(config)


def gen_label_set_from_container(container_name: str) -> Tuple[str, List[str]]:
    """Generates a label set from attributes of an existing container."""
    import docker

    docker_client = docker.from_env()
    try:
        container = docker_client.containers.get(container_name)
    except docker.errors.NotFound as exc:
        raise NoInformationException(f"Invalid container: {container_name!r}") from exc

    return gen_label_set_from_docker_attrs(container.attrs, container_name)


def gen_label_set_from_image(
    image_name: str, override_name: str = ""
) -> Tuple[str, List[str]]:
    """Generates a label set from a given Docker image."""
    import docker

    docker_client = docker.from_env()

    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound:
        # TODO: Consider using the Docker Registry HTTP API for getting image data
        print("Pulling image:")
        with Loader(
            f"{image_name} Pulling", f"{image_name} Pulled", f"{image_name} Failed"
        ):
            docker_client.images.pull(image_name)
    image = docker_client.images.get(image_name)
    base_image_name = image_name.split(":")[0].split("/")[-1]
    name: str = base_image_name
    if override_name:
        name = override_name
    return gen_label_set_from_docker_attrs(image.attrs, name)


def gen_label_set_from_compose(path: str) -> Tuple[str, List[str]]:
    """Generates a label set from a given Compose YAML file."""
    with open(path, "r", encoding="utf-8") as docker_compose:
        data = yaml.safe_load(docker_compose)
    if not data or not isinstance(data, dict):
        raise NoInformationException(f"File {path!r} does not contain valid YAML.")
    # Get service name
    try:
        services_dict: Dict[str, Any] = data["services"]
    except KeyError as exc:
        raise NoInformationException(f"No 'services' key in {path!r}.") from exc
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
        except KeyError as exc:
            raise NoInformationException(
                f"No image or build information found in service definition in {path!r}."
            ) from exc
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
        except docker.errors.ImageNotFound as exc:
            raise NoInformationException(
                f"Invalid docker image: {image_name!r} in {path!r}."
            ) from exc
        except docker.errors.NotFound as exc:
            raise NoInformationException(
                f"Invalid image tag: {image_name!r} in {path!r}."
            ) from exc
    except TypeError as exc:
        raise NoInformationException(
            f"Invalid service: {service_name!r} in {path!r}"
        ) from exc
