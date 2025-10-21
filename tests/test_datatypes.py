"""Unit tests for datatypes module"""

import pytest
from laebelmaker.datatypes import Rule, CombinedRule, ServiceConfig
from laebelmaker.errors import UnknownRuleTypeException, NoInformationException


class TestRule:
    """Test cases for Rule class"""

    def test_create_host_rule(self) -> None:
        """Test creating a Host rule"""
        rule = Rule("Host", "example.com")
        assert rule.typ == "Host"
        assert rule.content == ("example.com",)
        assert str(rule) == "Host(`example.com`)"

    def test_create_path_rule(self) -> None:
        """Test creating a Path rule"""
        rule = Rule("Path", "/api")
        assert rule.typ == "Path"
        assert rule.content == ("/api",)
        assert str(rule) == "Path(`/api`)"

    def test_create_pathprefix_rule(self) -> None:
        """Test creating a PathPrefix rule"""
        rule = Rule("PathPrefix", "/app")
        assert rule.typ == "PathPrefix"
        assert str(rule) == "PathPrefix(`/app`)"

    def test_create_headers_rule(self) -> None:
        """Test creating a Headers rule with key and value"""
        rule = Rule("Headers", "X-Custom-Header", "value123")
        assert rule.typ == "Headers"
        assert rule.content == ("X-Custom-Header", "value123")
        assert str(rule) == "Headers(`X-Custom-Header`, `value123`)"

    def test_invalid_rule_type(self) -> None:
        """Test that invalid rule types raise UnknownRuleTypeException"""
        with pytest.raises(UnknownRuleTypeException):
            Rule("InvalidType", "content")

    def test_rule_without_content(self) -> None:
        """Test that rules without content raise ValueError"""
        with pytest.raises(ValueError, match="must have content"):
            Rule("Host")

    def test_headers_rule_wrong_number_of_args(self) -> None:
        """Test that Headers rule with wrong number of args raises ValueError"""
        with pytest.raises(ValueError, match="only key and value"):
            Rule("Headers", "only-one-arg")

        with pytest.raises(ValueError, match="only key and value"):
            Rule("Headers", "arg1", "arg2", "arg3")

    def test_multiple_content_values(self) -> None:
        """Test rules with multiple content values (non-Headers)"""
        rule = Rule("Host", "example.com", "test.com")
        assert len(rule.content) == 2
        assert str(rule) == "Host(`example.com`, `test.com`)"


class TestCombinedRule:
    """Test cases for CombinedRule class"""

    def test_create_combined_rule_with_and(self) -> None:
        """Test creating a combined rule with AND operator"""
        host_rule = Rule("Host", "example.com")
        path_rule = Rule("PathPrefix", "/api")
        combined = CombinedRule(host_rule, "&&", path_rule)

        assert len(combined.rules) == 2
        assert len(combined.operators) == 1
        assert combined.operators[0] == "&&"
        assert str(combined) == "(Host(`example.com`) && PathPrefix(`/api`))"

    def test_create_combined_rule_with_or(self) -> None:
        """Test creating a combined rule with OR operator"""
        rule1 = Rule("Host", "example.com")
        rule2 = Rule("Host", "test.com")
        combined = CombinedRule(rule1, "||", rule2)

        assert str(combined) == "(Host(`example.com`) || Host(`test.com`))"

    def test_create_complex_combined_rule(self) -> None:
        """Test creating a complex combined rule with multiple operators"""
        rule1 = Rule("Host", "example.com")
        rule2 = Rule("PathPrefix", "/api")
        rule3 = Rule("Headers", "X-Api-Key", "secret")
        combined = CombinedRule(rule1, "&&", rule2, "&&", rule3)

        assert len(combined.rules) == 3
        assert len(combined.operators) == 2
        expected = "(Host(`example.com`) && PathPrefix(`/api`) && Headers(`X-Api-Key`, `secret`))"
        assert str(combined) == expected

    def test_from_string_domain_only(self) -> None:
        """Test creating rule from string with domain only"""
        rule = CombinedRule.from_string("example.com")
        assert isinstance(rule, Rule)
        assert str(rule) == "Host(`example.com`)"

    def test_from_string_domain_and_path(self) -> None:
        """Test creating rule from string with domain and path"""
        rule = CombinedRule.from_string("example.com/api")
        assert isinstance(rule, CombinedRule)
        assert str(rule) == "(Host(`example.com`) && PathPrefix(`/api`))"

    def test_from_string_path_only(self) -> None:
        """Test creating rule from string with path only (empty domain)"""
        rule = CombinedRule.from_string("/api")
        assert isinstance(rule, Rule)
        assert str(rule) == "PathPrefix(`/api`)"

    def test_from_string_domain_with_empty_path(self) -> None:
        """Test creating rule from string with domain and empty path"""
        rule = CombinedRule.from_string("example.com/")
        assert isinstance(rule, Rule)
        assert str(rule) == "Host(`example.com`)"

    def test_combined_rule_invalid_arg_type(self) -> None:
        """Test that invalid argument types raise TypeError"""
        with pytest.raises(TypeError, match="must be either strings or Rules"):
            CombinedRule(Rule("Host", "example.com"), 123)  # type: ignore


class TestServiceConfig:
    """Test cases for ServiceConfig dataclass"""

    def test_create_minimal_config(self) -> None:
        """Test creating a minimal ServiceConfig"""
        config = ServiceConfig(deploy_name="myapp")
        assert config.deploy_name == "myapp"
        assert config.rule is None
        assert config.url == ""
        assert config.port == 0
        assert config.https_enabled is False
        assert config.https_redirection is False
        assert config.web_entrypoint == "web"
        assert config.websecure_entrypoint == "websecure"
        assert config.tls_resolver == ""

    def test_create_full_config(self) -> None:
        """Test creating a fully configured ServiceConfig"""
        rule = Rule("Host", "example.com")
        config = ServiceConfig(
            deploy_name="myapp",
            rule=rule,
            url="example.com",
            port=8080,
            https_enabled=True,
            https_redirection=True,
            web_entrypoint="http",
            websecure_entrypoint="https",
            tls_resolver="letsencrypt",
        )

        assert config.deploy_name == "myapp"
        assert config.rule == rule
        assert config.url == "example.com"
        assert config.port == 8080
        assert config.https_enabled is True
        assert config.https_redirection is True
        assert config.web_entrypoint == "http"
        assert config.websecure_entrypoint == "https"
        assert config.tls_resolver == "letsencrypt"

    def test_config_with_https_only(self) -> None:
        """Test config with HTTPS enabled but no redirection"""
        config = ServiceConfig(
            deploy_name="myapp",
            https_enabled=True,
            https_redirection=False,
            tls_resolver="myresolver",
        )

        assert config.https_enabled is True
        assert config.https_redirection is False

    def test_config_port_validation(self) -> None:
        """Test that port can be set to various values"""
        config1 = ServiceConfig(deploy_name="app1", port=80)
        config2 = ServiceConfig(deploy_name="app2", port=8080)
        config3 = ServiceConfig(deploy_name="app3", port=0)

        assert config1.port == 80
        assert config2.port == 8080
        assert config3.port == 0
