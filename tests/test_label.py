"""Unit tests for label generation functions"""

import pytest
from laebelmaker.datatypes import ServiceConfig, Rule, CombinedRule, TraefikConfig
from laebelmaker.label import (
    traefik_enable,
    gen_simple_label_set_for_service,
    get_tcp_ports_from_attrs,
    fill_missing_info,
)


class TestTraefikEnable:
    """Test cases for traefik_enable function"""

    def test_returns_enable_label(self) -> None:
        """Test that traefik_enable returns correct static string"""
        result = traefik_enable()
        assert result == "traefik.enable=true"


class TestGenSimpleLabelSetForService:
    """Test cases for gen_simple_label_set_for_service function"""

    def test_http_only_basic(self) -> None:
        """Test generating labels for HTTP-only service"""
        rule = Rule("Host", "example.com")
        config = ServiceConfig(
            deploy_name="myapp",
            rule=rule,
            port=8080,
            https_enabled=False,
        )

        name, labels = gen_simple_label_set_for_service(config)

        assert name == "myapp"
        assert "traefik.enable=true" in labels
        assert "traefik.http.routers.myapp.entrypoints=web" in labels
        assert "traefik.http.routers.myapp.rule=Host(`example.com`)" in labels
        assert "traefik.http.services.myapp.loadbalancer.server.port=8080" in labels
        # Should not have HTTPS labels
        assert not any("-https" in label for label in labels)
        assert not any("tls" in label for label in labels)

    def test_http_only_no_port(self) -> None:
        """Test HTTP service without port specified"""
        rule = Rule("Host", "example.com")
        config = ServiceConfig(deploy_name="myapp", rule=rule, port=0)

        name, labels = gen_simple_label_set_for_service(config)

        assert name == "myapp"
        # Should not have port label when port is 0
        assert not any("loadbalancer.server.port" in label for label in labels)

    def test_https_only(self) -> None:
        """Test generating labels for HTTPS-only service (no redirect)"""
        rule = Rule("Host", "secure.example.com")
        config = ServiceConfig(
            deploy_name="secureapp",
            rule=rule,
            port=443,
            https_enabled=True,
            https_redirection=False,
            tls_resolver="letsencrypt",
        )

        name, labels = gen_simple_label_set_for_service(config)

        assert name == "secureapp"
        assert "traefik.enable=true" in labels
        # Should have HTTPS router
        assert "traefik.http.routers.secureapp-https.entrypoints=websecure" in labels
        assert (
            "traefik.http.routers.secureapp-https.rule=Host(`secure.example.com`)"
            in labels
        )
        assert (
            "traefik.http.services.secureapp-https.loadbalancer.server.port=443"
            in labels
        )
        assert "traefik.http.routers.secureapp-https.tls=true" in labels
        assert (
            "traefik.http.routers.secureapp-https.tls.certresolver=letsencrypt"
            in labels
        )
        # Should NOT have HTTP router or redirect middleware
        assert not any(
            label.startswith("traefik.http.routers.secureapp.") for label in labels
        )
        assert not any("redirectscheme" in label for label in labels)

    def test_https_with_redirect(self) -> None:
        """Test generating labels for HTTPS with HTTP redirect"""
        rule = Rule("Host", "example.com")
        config = ServiceConfig(
            deploy_name="webapp",
            rule=rule,
            port=3000,
            https_enabled=True,
            https_redirection=True,
            tls_resolver="myresolver",
        )

        name, labels = gen_simple_label_set_for_service(config)

        assert name == "webapp"
        # Should have both HTTP and HTTPS routers
        assert "traefik.http.routers.webapp-https.entrypoints=websecure" in labels
        assert "traefik.http.routers.webapp-https.tls=true" in labels
        assert "traefik.http.routers.webapp-https.tls.certresolver=myresolver" in labels
        assert "traefik.http.routers.webapp.entrypoints=web" in labels
        # Should have redirect middleware
        assert "traefik.http.routers.webapp.middlewares=webapp-redir" in labels
        assert (
            "traefik.http.middlewares.webapp-redir.redirectscheme.scheme=https"
            in labels
        )

    def test_custom_entrypoints(self) -> None:
        """Test service with custom entrypoint names"""
        rule = Rule("Host", "custom.example.com")
        config = ServiceConfig(
            deploy_name="customapp",
            rule=rule,
            port=8080,
            https_enabled=True,
            https_redirection=True,
            web_entrypoint="http-custom",
            websecure_entrypoint="https-custom",
            tls_resolver="resolver",
        )

        name, labels = gen_simple_label_set_for_service(config)

        assert "traefik.http.routers.customapp.entrypoints=http-custom" in labels
        assert "traefik.http.routers.customapp-https.entrypoints=https-custom" in labels

    def test_combined_rule(self) -> None:
        """Test service with combined rule"""
        host_rule = Rule("Host", "example.com")
        path_rule = Rule("PathPrefix", "/api")
        combined = CombinedRule(host_rule, "&&", path_rule)
        config = ServiceConfig(
            deploy_name="apiservice",
            rule=combined,
            port=5000,
        )

        name, labels = gen_simple_label_set_for_service(config)

        expected_rule = "(Host(`example.com`) && PathPrefix(`/api`))"
        assert f"traefik.http.routers.apiservice.rule={expected_rule}" in labels

    def test_disable_traefik_enable(self) -> None:
        """Test generating labels without traefik.enable=true"""
        rule = Rule("Host", "example.com")
        config = ServiceConfig(deploy_name="app", rule=rule, port=80)

        name, labels = gen_simple_label_set_for_service(config, enable=False)

        assert "traefik.enable=true" not in labels
        # But other labels should still be there
        assert len(labels) > 0

    def test_missing_rule_raises_error(self) -> None:
        """Test that missing rule raises ValueError"""
        config = ServiceConfig(deploy_name="app", rule=None, port=80)

        with pytest.raises(ValueError, match="cannot be None"):
            gen_simple_label_set_for_service(config)

    def test_https_without_tls_resolver_raises_error(self) -> None:
        """Test that HTTPS without TLS resolver raises ValueError"""
        rule = Rule("Host", "example.com")
        config = ServiceConfig(
            deploy_name="app",
            rule=rule,
            port=80,
            https_enabled=True,
            tls_resolver="",  # Empty resolver
        )

        with pytest.raises(ValueError, match="TLS resolver"):
            gen_simple_label_set_for_service(config)


class TestGetTcpPortsFromAttrs:
    """Test cases for get_tcp_ports_from_attrs function"""

    def test_extract_single_tcp_port(self) -> None:
        """Test extracting a single TCP port"""
        attrs = {
            "Config": {
                "ExposedPorts": {
                    "8080/tcp": {},
                }
            }
        }
        ports = get_tcp_ports_from_attrs(attrs)
        assert ports == [8080]

    def test_extract_multiple_tcp_ports(self) -> None:
        """Test extracting multiple TCP ports"""
        attrs = {
            "Config": {
                "ExposedPorts": {
                    "80/tcp": {},
                    "443/tcp": {},
                    "8080/tcp": {},
                }
            }
        }
        ports = get_tcp_ports_from_attrs(attrs)
        assert set(ports) == {80, 443, 8080}
        assert len(ports) == 3

    def test_filter_out_udp_ports(self) -> None:
        """Test that UDP ports are filtered out"""
        attrs = {
            "Config": {
                "ExposedPorts": {
                    "80/tcp": {},
                    "53/udp": {},
                    "443/tcp": {},
                }
            }
        }
        ports = get_tcp_ports_from_attrs(attrs)
        assert set(ports) == {80, 443}
        assert 53 not in ports

    def test_no_exposed_ports(self) -> None:
        """Test when no ExposedPorts key exists"""
        attrs = {"Config": {}}
        ports = get_tcp_ports_from_attrs(attrs)
        assert ports == []

    def test_empty_exposed_ports(self) -> None:
        """Test when ExposedPorts is empty"""
        attrs = {"Config": {"ExposedPorts": {}}}
        ports = get_tcp_ports_from_attrs(attrs)
        assert ports == []

    def test_missing_config_key(self) -> None:
        """Test when Config key is missing"""
        attrs = {}
        ports = get_tcp_ports_from_attrs(attrs)
        assert ports == []

    def test_only_udp_ports(self) -> None:
        """Test when only UDP ports are exposed"""
        attrs = {
            "Config": {
                "ExposedPorts": {
                    "53/udp": {},
                    "123/udp": {},
                }
            }
        }
        ports = get_tcp_ports_from_attrs(attrs)
        assert ports == []

    def test_common_ports(self) -> None:
        """Test extraction of common web service ports"""
        attrs = {
            "Config": {
                "ExposedPorts": {
                    "3000/tcp": {},
                    "5000/tcp": {},
                    "8000/tcp": {},
                    "8080/tcp": {},
                }
            }
        }
        ports = get_tcp_ports_from_attrs(attrs)
        assert set(ports) == {3000, 5000, 8000, 8080}


class TestFillMissingInfoWithTraefikConfig:
    """Test cases for fill_missing_info with TraefikConfig auto-filling"""

    def test_auto_fill_web_entrypoint_from_traefik_config(self) -> None:
        """Test that web_entrypoint is auto-filled from TraefikConfig"""
        traefik_config = TraefikConfig(
            entrypoints=["web", "websecure"],
            tls_resolvers=["letsencrypt"],
            default_web_entrypoint="web",
            default_websecure_entrypoint="websecure",
            default_tls_resolver="letsencrypt",
        )
        config = ServiceConfig(
            deploy_name="test",
            traefik_config=traefik_config,
        )

        # web_entrypoint should be auto-filled without prompting
        fill_missing_info(config, "web_entrypoint", "")

        assert config.web_entrypoint == "web"

    def test_auto_fill_websecure_entrypoint_from_traefik_config(self) -> None:
        """Test that websecure_entrypoint is auto-filled from TraefikConfig"""
        traefik_config = TraefikConfig(
            entrypoints=["web", "websecure"],
            tls_resolvers=["letsencrypt"],
            default_web_entrypoint="web",
            default_websecure_entrypoint="websecure",
            default_tls_resolver="letsencrypt",
        )
        config = ServiceConfig(
            deploy_name="test",
            https_enabled=True,
            traefik_config=traefik_config,
        )

        # websecure_entrypoint should be auto-filled without prompting
        fill_missing_info(config, "websecure_entrypoint", "")

        assert config.websecure_entrypoint == "websecure"

    def test_auto_fill_tls_resolver_from_traefik_config(self) -> None:
        """Test that tls_resolver is auto-filled from TraefikConfig"""
        traefik_config = TraefikConfig(
            entrypoints=["web", "websecure"],
            tls_resolvers=["letsencrypt"],
            default_web_entrypoint="web",
            default_websecure_entrypoint="websecure",
            default_tls_resolver="letsencrypt",
        )
        config = ServiceConfig(
            deploy_name="test",
            https_enabled=True,
            traefik_config=traefik_config,
        )

        # tls_resolver should be auto-filled without prompting
        fill_missing_info(config, "tls_resolver", "")

        assert config.tls_resolver == "letsencrypt"

    def test_auto_fill_with_custom_entrypoint_names(self) -> None:
        """Test auto-fill with custom entrypoint names from TraefikConfig"""
        traefik_config = TraefikConfig(
            entrypoints=["public", "secure"],
            tls_resolvers=["myresolver"],
            default_web_entrypoint="public",
            default_websecure_entrypoint="secure",
            default_tls_resolver="myresolver",
        )
        config = ServiceConfig(
            deploy_name="test",
            https_enabled=True,
            traefik_config=traefik_config,
        )

        fill_missing_info(config, "web_entrypoint", "")
        fill_missing_info(config, "websecure_entrypoint", "")
        fill_missing_info(config, "tls_resolver", "")

        assert config.web_entrypoint == "public"
        assert config.websecure_entrypoint == "secure"
        assert config.tls_resolver == "myresolver"

    def test_no_auto_fill_without_traefik_config(self) -> None:
        """Test that defaults are used when TraefikConfig is not provided"""
        config = ServiceConfig(
            deploy_name="test",
            traefik_config=None,
        )

        # Without TraefikConfig, should use ServiceConfig defaults
        # (This would normally prompt user, but we're just checking the value exists)
        assert config.web_entrypoint == "web"  # Default from ServiceConfig
        assert config.websecure_entrypoint == "websecure"  # Default from ServiceConfig
