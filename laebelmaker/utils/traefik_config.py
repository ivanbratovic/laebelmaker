"""Module for parsing Traefik configuration files"""

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2023, Ivan Bratović"
__license__ = "MIT"

from typing import Dict, Any, List
import yaml
from laebelmaker.datatypes import TraefikConfig
from laebelmaker.errors import NoInformationException


def _build_traefik_config_from_dict(data: Dict[str, Any]) -> TraefikConfig:
    """
    Build TraefikConfig from parsed configuration dictionary.

    Extracts entrypoints and TLS resolvers, and determines smart defaults.
    Works with both YAML and TOML parsed data.
    """
    # Extract entrypoints (handle both camelCase and lowercase)
    entrypoints_dict: Dict[str, Any] = {}
    if "entryPoints" in data:
        entrypoints_dict = data["entryPoints"]
    elif "entrypoints" in data:
        entrypoints_dict = data["entrypoints"]

    entrypoints: List[str] = list(entrypoints_dict.keys())

    # Extract TLS resolvers (handle both camelCase and lowercase)
    tls_resolvers: List[str] = []
    if "certificatesResolvers" in data:
        tls_resolvers = list(data["certificatesResolvers"].keys())
    elif "certificatesresolvers" in data:
        tls_resolvers = list(data["certificatesresolvers"].keys())

    # Determine smart defaults for entrypoints
    default_web = "web"
    default_websecure = "websecure"
    default_tls_resolver = ""

    if entrypoints:
        # First, try to find entrypoints by port number in address field
        port_80_entrypoint = None
        port_443_entrypoint = None

        for ep_name, ep_config in entrypoints_dict.items():
            if isinstance(ep_config, dict) and "address" in ep_config:
                address = str(ep_config["address"])
                # Check if address is exactly :80 or contains :80 (with proper boundary)
                # Handle formats like ":80", "0.0.0.0:80", ":80/tcp", etc.
                if address == ":80" or ":80/" in address or address.endswith(":80"):
                    port_80_entrypoint = ep_name
                elif (
                    address == ":443" or ":443/" in address or address.endswith(":443")
                ):
                    port_443_entrypoint = ep_name

        # Use port-based detection first if available
        if port_80_entrypoint:
            default_web = port_80_entrypoint
        elif "web" in entrypoints:
            default_web = "web"
        elif "http" in entrypoints:
            default_web = "http"
        elif len(entrypoints) > 0:
            # Fallback to first entrypoint
            default_web = entrypoints[0]

        if port_443_entrypoint:
            default_websecure = port_443_entrypoint
        elif "websecure" in entrypoints:
            default_websecure = "websecure"
        elif "https" in entrypoints:
            default_websecure = "https"
        elif len(entrypoints) > 1:
            # Fallback to second entrypoint
            default_websecure = entrypoints[1]

    # Use first TLS resolver as default
    if tls_resolvers:
        default_tls_resolver = tls_resolvers[0]

    return TraefikConfig(
        entrypoints=entrypoints,
        tls_resolvers=tls_resolvers,
        default_web_entrypoint=default_web,
        default_websecure_entrypoint=default_websecure,
        default_tls_resolver=default_tls_resolver,
    )


def load_traefik_config_from_yaml(path: str) -> TraefikConfig:
    """
    Load Traefik configuration from YAML file (traefik.yml).

    Extracts entrypoints and TLS certificate resolvers configuration.
    """
    try:
        with open(path, "r", encoding="utf-8") as config_file:
            data: Dict[str, Any] = yaml.safe_load(config_file)
    except FileNotFoundError as exc:
        raise NoInformationException(
            f"Traefik config file not found: {path!r}"
        ) from exc
    except yaml.YAMLError as exc:
        raise NoInformationException(
            f"Invalid YAML in Traefik config file {path!r}: {exc}"
        ) from exc

    if data is None or not isinstance(data, dict):
        raise NoInformationException(
            f"File {path!r} does not contain valid Traefik configuration."
        )

    return _build_traefik_config_from_dict(data)


def load_traefik_config_from_toml(path: str) -> TraefikConfig:
    """
    Load Traefik configuration from TOML file (traefik.toml).

    Note: TOML support requires the 'toml' or 'tomli' package.
    """
    try:
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # type: ignore

        with open(path, "rb") as config_file:
            data: Dict[str, Any] = tomllib.load(config_file)
    except FileNotFoundError as exc:
        raise NoInformationException(
            f"Traefik config file not found: {path!r}"
        ) from exc
    except ModuleNotFoundError as exc:
        raise NoInformationException(
            "TOML support requires 'tomli' package. Install with: pip install tomli"
        ) from exc
    except Exception as exc:
        raise NoInformationException(
            f"Error reading TOML file {path!r}: {exc}"
        ) from exc

    if data is None or not isinstance(data, dict):
        raise NoInformationException(
            f"File {path!r} does not contain valid Traefik configuration."
        )

    return _build_traefik_config_from_dict(data)


def load_traefik_config(path: str) -> TraefikConfig:
    """
    Load Traefik configuration from file (auto-detect YAML or TOML format).
    """
    if path.lower().endswith((".yml", ".yaml")):
        return load_traefik_config_from_yaml(path)
    elif path.lower().endswith(".toml"):
        return load_traefik_config_from_toml(path)
    else:
        raise NoInformationException(
            f"Unsupported config file format: {path!r}. "
            "Supported formats: .yml, .yaml, .toml"
        )
