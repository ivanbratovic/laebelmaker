"""Unit tests for traefik_config module"""

import tempfile
import os
from laebelmaker.utils.traefik_config import (
    load_traefik_config,
    load_traefik_config_from_yaml,
    load_traefik_config_from_toml,
)
from laebelmaker.datatypes import TraefikConfig
from laebelmaker.errors import NoInformationException
import pytest


class TestLoadTraefikConfigFromYAML:
    """Test cases for loading Traefik configuration from YAML"""

    def test_load_yaml_basic_config(self) -> None:
        """Test loading basic Traefik YAML config"""
        yaml_content = """
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: test@example.com
      storage: acme.json
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            config = load_traefik_config_from_yaml(tmp_path)
            assert isinstance(config, TraefikConfig)
            assert "web" in config.entrypoints
            assert "websecure" in config.entrypoints
            assert "letsencrypt" in config.tls_resolvers
            assert config.default_web_entrypoint == "web"
            assert config.default_websecure_entrypoint == "websecure"
            assert config.default_tls_resolver == "letsencrypt"
        finally:
            os.unlink(tmp_path)

    def test_load_yaml_lowercase_keys(self) -> None:
        """Test loading YAML with lowercase keys"""
        yaml_content = """
entrypoints:
  http:
    address: ":80"
  https:
    address: ":443"

certificatesresolvers:
  myresolver:
    acme:
      email: test@example.com
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            config = load_traefik_config_from_yaml(tmp_path)
            assert "http" in config.entrypoints
            assert "https" in config.entrypoints
            assert "myresolver" in config.tls_resolvers
            assert config.default_web_entrypoint == "http"
            assert config.default_websecure_entrypoint == "https"
        finally:
            os.unlink(tmp_path)

    def test_load_yaml_empty_config(self) -> None:
        """Test loading empty YAML config"""
        yaml_content = "{}"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            config = load_traefik_config_from_yaml(tmp_path)
            assert config.entrypoints == []
            assert config.tls_resolvers == []
        finally:
            os.unlink(tmp_path)

    def test_load_yaml_file_not_found(self) -> None:
        """Test error when YAML file not found"""
        with pytest.raises(NoInformationException, match="not found"):
            load_traefik_config_from_yaml("/nonexistent/path.yml")

    def test_load_yaml_invalid_yaml(self) -> None:
        """Test error with invalid YAML"""
        yaml_content = "invalid: yaml: content:"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            with pytest.raises(NoInformationException, match="Invalid YAML"):
                load_traefik_config_from_yaml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_yaml_real_world_example_file(self) -> None:
        """Test loading real-world traefik.yml from examples directory"""
        import os.path

        # Path to example traefik.yml in the repository
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "examples", "traefik.yml"
        )

        # Skip test if example file doesn't exist
        if not os.path.exists(example_path):
            pytest.skip("Example traefik.yml not found")

        config = load_traefik_config_from_yaml(example_path)

        # Verify correct entrypoints are detected
        assert len(config.entrypoints) == 2
        assert "web" in config.entrypoints
        assert "websecure" in config.entrypoints

        # Verify correct defaults are set
        assert config.default_web_entrypoint == "web"
        assert config.default_websecure_entrypoint == "websecure"

        # Verify TLS resolver is detected
        assert len(config.tls_resolvers) == 1
        assert "letsencrypt" in config.tls_resolvers
        assert config.default_tls_resolver == "letsencrypt"

    def test_load_yaml_with_multiple_entrypoints(self) -> None:
        """Test config with more than 2 entrypoints to verify correct defaults"""
        yaml_content = """
entryPoints:
  web:
    address: :80
  websecure:
    address: :443
  metrics:
    address: :8082
  traefik:
    address: :8080

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: acme.json
  staging:
    acme:
      email: admin@example.com
      storage: acme-staging.json
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            config = load_traefik_config_from_yaml(tmp_path)
            # Verify all entrypoints are detected
            assert len(config.entrypoints) == 4
            assert "web" in config.entrypoints
            assert "websecure" in config.entrypoints
            assert "metrics" in config.entrypoints
            assert "traefik" in config.entrypoints
            # Verify correct defaults when "web" and "websecure" are present
            assert config.default_web_entrypoint == "web"
            assert config.default_websecure_entrypoint == "websecure"
            # Verify multiple TLS resolvers with first as default
            assert len(config.tls_resolvers) == 2
            assert "letsencrypt" in config.tls_resolvers
            assert "staging" in config.tls_resolvers
            assert config.default_tls_resolver == "letsencrypt"
        finally:
            os.unlink(tmp_path)

    def test_load_yaml_with_custom_names_port_detection(self) -> None:
        """Test that entrypoints with custom names are detected by port"""
        yaml_content = """
entryPoints:
  public:
    address: :80
  secure:
    address: :443
  admin:
    address: :8080

certificatesResolvers:
  myresolver:
    acme:
      email: admin@example.com
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            config = load_traefik_config_from_yaml(tmp_path)
            # Verify port-based detection works even with non-standard names
            assert config.default_web_entrypoint == "public"  # Port 80
            assert config.default_websecure_entrypoint == "secure"  # Port 443
            assert "admin" in config.entrypoints
        finally:
            os.unlink(tmp_path)


class TestLoadTraefikConfigFromTOML:
    """Test cases for loading Traefik configuration from TOML"""

    def test_load_toml_basic_config(self) -> None:
        """Test loading basic Traefik TOML config"""
        toml_content = """
[entryPoints]
  [entryPoints.web]
    address = ":80"
  [entryPoints.websecure]
    address = ":443"

[certificatesResolvers]
  [certificatesResolvers.letsencrypt]
    [certificatesResolvers.letsencrypt.acme]
      email = "test@example.com"
      storage = "acme.json"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
            tmp.write(toml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            config = load_traefik_config_from_toml(tmp_path)
            assert isinstance(config, TraefikConfig)
            assert "web" in config.entrypoints
            assert "websecure" in config.entrypoints
            assert "letsencrypt" in config.tls_resolvers
            assert config.default_web_entrypoint == "web"
            assert config.default_websecure_entrypoint == "websecure"
            assert config.default_tls_resolver == "letsencrypt"
        finally:
            os.unlink(tmp_path)

    def test_load_toml_file_not_found(self) -> None:
        """Test error when TOML file not found"""
        with pytest.raises(NoInformationException, match="not found"):
            load_traefik_config_from_toml("/nonexistent/path.toml")

    def test_load_toml_real_world_example_file(self) -> None:
        """Test loading real-world traefik.toml from examples directory"""
        import os.path

        # Path to example traefik.toml in the repository
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "examples", "traefik.toml"
        )

        # Skip test if example file doesn't exist
        if not os.path.exists(example_path):
            pytest.skip("Example traefik.toml not found")

        config = load_traefik_config_from_toml(example_path)

        # Verify correct entrypoints are detected
        assert len(config.entrypoints) == 2
        assert "web" in config.entrypoints
        assert "websecure" in config.entrypoints

        # Verify correct defaults are set
        assert config.default_web_entrypoint == "web"
        assert config.default_websecure_entrypoint == "websecure"

        # Verify TLS resolver is detected
        assert len(config.tls_resolvers) == 1
        assert "letsencrypt" in config.tls_resolvers
        assert config.default_tls_resolver == "letsencrypt"


class TestLoadTraefikConfig:
    """Test cases for auto-detecting config format"""

    def test_load_yaml_by_extension(self) -> None:
        """Test loading YAML file by extension"""
        yaml_content = """
entryPoints:
  web:
    address: ":80"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()
            tmp_path = tmp.name

        try:
            config = load_traefik_config(tmp_path)
            assert isinstance(config, TraefikConfig)
            assert "web" in config.entrypoints
        finally:
            os.unlink(tmp_path)

    def test_load_unsupported_format(self) -> None:
        """Test error with unsupported file format"""
        with pytest.raises(NoInformationException, match="Unsupported config file"):
            load_traefik_config("/path/to/config.json")


class TestTraefikConfigDataclass:
    """Test cases for TraefikConfig dataclass"""

    def test_create_traefik_config(self) -> None:
        """Test creating TraefikConfig instance"""
        config = TraefikConfig(
            entrypoints=["web", "websecure"],
            tls_resolvers=["letsencrypt"],
            default_web_entrypoint="web",
            default_websecure_entrypoint="websecure",
            default_tls_resolver="letsencrypt",
        )
        assert config.entrypoints == ["web", "websecure"]
        assert config.tls_resolvers == ["letsencrypt"]
        assert config.default_web_entrypoint == "web"
        assert config.default_websecure_entrypoint == "websecure"
        assert config.default_tls_resolver == "letsencrypt"

    def test_create_traefik_config_minimal(self) -> None:
        """Test creating TraefikConfig with minimal configuration"""
        config = TraefikConfig(
            entrypoints=[],
            tls_resolvers=[],
            default_web_entrypoint="web",
            default_websecure_entrypoint="websecure",
            default_tls_resolver="",
        )
        assert config.entrypoints == []
        assert config.tls_resolvers == []
        assert config.default_web_entrypoint == "web"
        assert config.default_websecure_entrypoint == "websecure"
        assert config.default_tls_resolver == ""
