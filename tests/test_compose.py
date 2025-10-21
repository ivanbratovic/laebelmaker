"""Tests gen_label_set_from_compose function"""

from unittest import mock
import builtins
import pytest
from laebelmaker.errors import NoInformationException
from laebelmaker.label import gen_label_set_from_compose


def docker_available() -> bool:
    try:
        import docker

        docker.from_env()
        return True
    except Exception:
        return False


def test_compose_http() -> None:
    """Tests loading a Compose YAML file and basic HTTP labels"""
    if docker_available():
        inputs = iter(["1", "testapp", "no"])
        with mock.patch.object(builtins, "input", lambda _: next(inputs)):
            gen_label_set_from_compose("examples/docker-compose-testapp.yml")
    else:
        with pytest.raises(NoInformationException):
            with mock.patch.object(builtins, "input", lambda _: "1"):
                gen_label_set_from_compose("examples/docker-compose-testapp.yml")


def test_compose_https() -> None:
    """Tests loading a Compose YAML file and HTTPS labels"""
    if docker_available():
        inputs = iter(["1", "testapp", "yes", "yes", "http", "https", "letsencrypt"])
        with mock.patch.object(builtins, "input", lambda _: next(inputs)):
            gen_label_set_from_compose("examples/docker-compose-testapp.yml")
    else:
        with pytest.raises(NoInformationException):
            with mock.patch.object(builtins, "input", lambda _: "1"):
                gen_label_set_from_compose("examples/docker-compose-testapp.yml")


def test_compose_build() -> None:
    """Tests loading a Compose YAML file with a build context"""
    inputs = iter(["1"])
    with pytest.raises(NotImplementedError):
        with mock.patch.object(builtins, "input", lambda _: next(inputs)):
            gen_label_set_from_compose("examples/docker-compose-with-build.yaml")


def test_load_empty_yaml() -> None:
    """Tests loading empty YAML file"""
    with pytest.raises(NoInformationException):
        gen_label_set_from_compose("examples/empty.yaml")


def test_load_empty_services() -> None:
    """Tests loading Compose YAML file with empty services map"""
    with pytest.raises(NoInformationException):
        gen_label_set_from_compose("examples/empty-services.yaml")


def test_load_not_yaml() -> None:
    """Tests loading a file that is not in YAML format"""
    with pytest.raises(NoInformationException):
        gen_label_set_from_compose("examples/not-a-yaml.yml")


def test_load_invalid_image() -> None:
    """Tests loading a Compose YAML file with an invalid image"""
    with pytest.raises(NoInformationException):
        gen_label_set_from_compose("examples/invalid-image.yml")


def test_load_invalid_image_tag() -> None:
    """Tests loading a Compose YAML file with an invalid image tag"""
    with pytest.raises(NoInformationException):
        gen_label_set_from_compose("examples/invalid-image-tag.yml")


def test_load_invalid_services() -> None:
    """Tests loading a Compose YAML file with invalid services"""
    with pytest.raises(NoInformationException):
        gen_label_set_from_compose("examples/invalid-services.yaml")
