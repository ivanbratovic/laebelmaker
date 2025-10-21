"""Unit tests for formatter module"""

from laebelmaker.utils.formatter import (
    LabelFormatter,
    formatter_none,
    formatter_docker,
    formatter_yaml,
)


class TestLabelFormatter:
    """Test cases for LabelFormatter class"""

    def test_default_formatter(self) -> None:
        """Test formatter with default parameters"""
        formatter = LabelFormatter()
        labels = ["label1=value1", "label2=value2"]
        result = formatter.format(labels)
        assert result == "label1=value1 label2=value2\n"

    def test_custom_separator(self) -> None:
        """Test formatter with custom separator"""
        formatter = LabelFormatter(sep=", ")
        labels = ["label1", "label2", "label3"]
        result = formatter.format(labels)
        assert result == "label1, label2, label3\n"

    def test_custom_end(self) -> None:
        """Test formatter with custom end string"""
        formatter = LabelFormatter(end="")
        labels = ["label1"]
        result = formatter.format(labels)
        assert result == "label1"

    def test_custom_formatter_function(self) -> None:
        """Test formatter with custom transformation function"""
        formatter = LabelFormatter(formatter=lambda x: f"[{x}]", sep=" ")
        labels = ["a", "b", "c"]
        result = formatter.format(labels)
        assert result == "[a] [b] [c]\n"

    def test_empty_labels(self) -> None:
        """Test formatter with empty label list"""
        formatter = LabelFormatter()
        result = formatter.format([])
        assert result == "\n"

    def test_single_label(self) -> None:
        """Test formatter with single label"""
        formatter = LabelFormatter()
        result = formatter.format(["single=label"])
        assert result == "single=label\n"

    def test_complex_formatter(self) -> None:
        """Test formatter with multiple custom parameters"""
        formatter = LabelFormatter(
            formatter=lambda x: x.upper(), sep=" | ", end=" END\n"
        )
        labels = ["hello", "world"]
        result = formatter.format(labels)
        assert result == "HELLO | WORLD END\n"


class TestFormatterNone:
    """Test cases for formatter_none function"""

    def test_basic_labels(self) -> None:
        """Test basic label formatting with newlines"""
        labels = [
            "traefik.enable=true",
            "traefik.http.routers.myapp.rule=Host(`example.com`)",
        ]
        result = formatter_none(labels)
        expected = (
            "traefik.enable=true\ntraefik.http.routers.myapp.rule=Host(`example.com`)\n"
        )
        assert result == expected

    def test_empty_labels(self) -> None:
        """Test formatting empty label list"""
        result = formatter_none([])
        assert result == "\n"

    def test_single_label(self) -> None:
        """Test formatting single label"""
        result = formatter_none(["traefik.enable=true"])
        assert result == "traefik.enable=true\n"

    def test_multiple_labels(self) -> None:
        """Test formatting multiple labels"""
        labels = ["label1", "label2", "label3", "label4"]
        result = formatter_none(labels)
        assert result == "label1\nlabel2\nlabel3\nlabel4\n"


class TestFormatterDocker:
    """Test cases for formatter_docker function"""

    def test_basic_labels(self) -> None:
        """Test Docker run format with --label flags"""
        labels = [
            "traefik.enable=true",
            "traefik.http.routers.myapp.rule=Host(`example.com`)",
        ]
        result = formatter_docker(labels)
        expected = "--label 'traefik.enable=true' --label 'traefik.http.routers.myapp.rule=Host(`example.com`)'\n"
        assert result == expected

    def test_empty_labels(self) -> None:
        """Test Docker formatter with empty list"""
        result = formatter_docker([])
        assert result == "\n"

    def test_single_label(self) -> None:
        """Test Docker formatter with single label"""
        result = formatter_docker(["test=value"])
        assert result == "--label 'test=value'\n"

    def test_special_characters(self) -> None:
        """Test Docker formatter with special characters in labels"""
        labels = ["label.with.dots=value", "label-with-dashes=val"]
        result = formatter_docker(labels)
        expected = "--label 'label.with.dots=value' --label 'label-with-dashes=val'\n"
        assert result == expected

    def test_multiple_labels_spacing(self) -> None:
        """Test that labels are separated by single space"""
        labels = ["a=1", "b=2", "c=3"]
        result = formatter_docker(labels)
        assert result.count(" --label ") == 2  # Two spaces between three labels
        assert result.startswith("--label ")


class TestFormatterYaml:
    """Test cases for formatter_yaml function"""

    def test_basic_labels(self) -> None:
        """Test YAML list format"""
        labels = [
            "traefik.enable=true",
            "traefik.http.routers.myapp.rule=Host(`example.com`)",
        ]
        result = formatter_yaml(labels)
        expected = "  - traefik.enable=true\n  - traefik.http.routers.myapp.rule=Host(`example.com`)\n"
        assert result == expected

    def test_empty_labels(self) -> None:
        """Test YAML formatter with empty list"""
        result = formatter_yaml([])
        assert result == "\n"

    def test_single_label(self) -> None:
        """Test YAML formatter with single label"""
        result = formatter_yaml(["test=value"])
        assert result == "  - test=value\n"

    def test_indentation(self) -> None:
        """Test that YAML format has correct indentation"""
        labels = ["label1", "label2"]
        result = formatter_yaml(labels)
        # Don't strip - check raw output
        assert result == "  - label1\n  - label2\n"

    def test_multiple_labels(self) -> None:
        """Test YAML formatter with multiple labels"""
        labels = ["a=1", "b=2", "c=3", "d=4"]
        result = formatter_yaml(labels)
        assert result == "  - a=1\n  - b=2\n  - c=3\n  - d=4\n"

    def test_yaml_format_valid_syntax(self) -> None:
        """Test that output looks like valid YAML list syntax"""
        labels = ["key1=value1", "key2=value2"]
        result = formatter_yaml(labels)
        # Each line should be indented list item (check raw output before final \n)
        lines = result.rstrip("\n").split("\n")
        for line in lines:
            assert line.startswith("  - ")
            assert "=" in line
