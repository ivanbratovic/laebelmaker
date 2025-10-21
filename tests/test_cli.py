"""Integration tests for CLI module"""

from unittest import mock
from laebelmaker.cli import (
    main,
    has_yaml_extension,
    print_labels,
    FORMATS,
)
from laebelmaker.utils.formatter import formatter_none


class TestHasYamlExtension:
    """Test cases for has_yaml_extension function"""

    def test_yaml_extension(self) -> None:
        """Test files with .yaml extension"""
        assert has_yaml_extension("docker-compose.yaml") is True
        assert has_yaml_extension("/path/to/file.yaml") is True

    def test_yml_extension(self) -> None:
        """Test files with .yml extension"""
        assert has_yaml_extension("config.yml") is True
        assert has_yaml_extension("/some/path/config.yml") is True

    def test_case_insensitive(self) -> None:
        """Test that extension check is case insensitive"""
        assert has_yaml_extension("file.YAML") is True
        assert has_yaml_extension("file.YML") is True
        assert has_yaml_extension("file.Yaml") is True
        assert has_yaml_extension("file.Yml") is True

    def test_non_yaml_extensions(self) -> None:
        """Test files with non-YAML extensions"""
        assert has_yaml_extension("file.txt") is False
        assert has_yaml_extension("file.json") is False
        assert has_yaml_extension("file.py") is False
        assert has_yaml_extension("Dockerfile") is False

    def test_no_extension(self) -> None:
        """Test files with no extension"""
        assert has_yaml_extension("file") is False
        assert has_yaml_extension("/path/to/file") is False

    def test_yaml_in_filename_but_wrong_extension(self) -> None:
        """Test that yaml in filename but wrong extension returns False"""
        assert has_yaml_extension("yaml_file.txt") is False
        assert has_yaml_extension("my-yaml.conf") is False

    def test_with_whitespace(self) -> None:
        """Test paths with whitespace (stripped)"""
        assert has_yaml_extension("  file.yaml  ") is True
        assert has_yaml_extension("  file.yml  ") is True


class TestPrintLabels:
    """Test cases for print_labels function"""

    def test_print_single_service(self, capsys) -> None:  # type: ignore
        """Test printing labels for single service"""
        labels = [("myapp", ["label1=value1", "label2=value2"])]
        print_labels(labels, formatter_none)

        captured = capsys.readouterr()
        assert "--START GENERATED LABELS FOR 'myapp'--" in captured.out
        assert "label1=value1" in captured.out
        assert "label2=value2" in captured.out
        assert "--END GENERATED LABELS FOR 'myapp'--" in captured.out

    def test_print_multiple_services(self, capsys) -> None:  # type: ignore
        """Test printing labels for multiple services"""
        labels = [
            ("app1", ["label1=a"]),
            ("app2", ["label2=b"]),
        ]
        print_labels(labels, formatter_none)

        captured = capsys.readouterr()
        assert "--START GENERATED LABELS FOR 'app1'--" in captured.out
        assert "--START GENERATED LABELS FOR 'app2'--" in captured.out
        assert "label1=a" in captured.out
        assert "label2=b" in captured.out

    def test_skip_empty_label_lists(self, capsys) -> None:  # type: ignore
        """Test that services with empty label lists are skipped"""
        labels = [
            ("app1", ["label1=a"]),
            ("app2", []),  # Empty
            ("app3", ["label3=c"]),
        ]
        print_labels(labels, formatter_none)

        captured = capsys.readouterr()
        assert "'app1'" in captured.out
        assert "'app2'" not in captured.out  # Should be skipped
        assert "'app3'" in captured.out

    def test_empty_labels_list(self, capsys) -> None:  # type: ignore
        """Test with empty labels list"""
        labels = []  # type: ignore
        print_labels(labels, formatter_none)

        captured = capsys.readouterr()
        assert captured.out == ""


class TestFormats:
    """Test that FORMATS list is correctly populated"""

    def test_formats_contains_expected_formatters(self) -> None:
        """Test that FORMATS contains the expected format names"""
        assert "none" in FORMATS
        assert "docker" in FORMATS
        assert "yaml" in FORMATS

    def test_formats_count(self) -> None:
        """Test that we have the expected number of formatters"""
        assert len(FORMATS) == 3


class TestMainCLI:
    """Integration tests for main CLI function"""

    def test_version_flag(self, capsys) -> None:  # type: ignore
        """Test --version flag"""
        with mock.patch("sys.argv", ["laebelmaker", "--version"]):
            main()

        captured = capsys.readouterr()
        assert "Laebelmaker v" in captured.out

    def test_help_with_no_args(self, capsys) -> None:  # type: ignore
        """Test that help is shown when no arguments provided"""
        with mock.patch("sys.argv", ["laebelmaker"]):
            main()

        captured = capsys.readouterr()
        assert "usage:" in captured.out or "Generate Traefik labels" in captured.out

    def test_format_choices(self) -> None:
        """Test that format argument accepts valid choices"""
        # This is implicitly tested by the argument parser
        # Just verify that FORMATS list is populated
        assert len(FORMATS) > 0
        assert "none" in FORMATS

    def test_interactive_mode_flag_recognized(self) -> None:
        """Test that -i flag is recognized (without actually running interactive)"""
        # We just test that the argument is accepted without error
        with mock.patch("sys.argv", ["laebelmaker", "-i"]):
            with mock.patch("laebelmaker.cli.labels_from_user") as mock_labels:
                mock_labels.return_value = []
                main()
                mock_labels.assert_called_once()

    def test_container_flag_recognized(self) -> None:
        """Test that -c flag is recognized"""
        with mock.patch("sys.argv", ["laebelmaker", "-c", "mycontainer"]):
            with mock.patch("laebelmaker.cli.labels_from_container") as mock_labels:
                mock_labels.return_value = []
                main()
                mock_labels.assert_called_once_with("mycontainer")

    def test_file_argument_recognized(self) -> None:
        """Test that file arguments are recognized"""
        with mock.patch("sys.argv", ["laebelmaker", "docker-compose.yml"]):
            with mock.patch("laebelmaker.cli.labels_from_compose_files") as mock_labels:
                mock_labels.return_value = []
                main()
                mock_labels.assert_called_once_with(["docker-compose.yml"])

    def test_multiple_files(self) -> None:
        """Test processing multiple compose files"""
        with mock.patch("sys.argv", ["laebelmaker", "file1.yml", "file2.yaml"]):
            with mock.patch("laebelmaker.cli.labels_from_compose_files") as mock_labels:
                mock_labels.return_value = []
                main()
                mock_labels.assert_called_once_with(["file1.yml", "file2.yaml"])

    def test_format_option_docker(self) -> None:
        """Test --format docker option"""
        with mock.patch("sys.argv", ["laebelmaker", "-i", "--format", "docker"]):
            with mock.patch("laebelmaker.cli.labels_from_user") as mock_labels:
                with mock.patch("laebelmaker.cli.print_labels") as mock_print:
                    mock_labels.return_value = [("app", ["label=value"])]
                    main()
                    # Verify formatter_docker was used
                    mock_print.assert_called_once()
                    args = mock_print.call_args[0]
                    formatter = args[1]
                    # Test that it's the docker formatter
                    result = formatter(["test=val"])
                    assert "--label" in result

    def test_format_option_yaml(self) -> None:
        """Test --format yaml option"""
        with mock.patch("sys.argv", ["laebelmaker", "-i", "--format", "yaml"]):
            with mock.patch("laebelmaker.cli.labels_from_user") as mock_labels:
                with mock.patch("laebelmaker.cli.print_labels") as mock_print:
                    mock_labels.return_value = [("app", ["label=value"])]
                    main()
                    # Verify formatter_yaml was used
                    mock_print.assert_called_once()
                    args = mock_print.call_args[0]
                    formatter = args[1]
                    # Test that it's the yaml formatter
                    result = formatter(["test=val"])
                    assert "  - " in result

    def test_no_labels_produced_message(self, capsys) -> None:  # type: ignore
        """Test message when no labels are produced"""
        with mock.patch("sys.argv", ["laebelmaker", "-i"]):
            with mock.patch("laebelmaker.cli.labels_from_user") as mock_labels:
                mock_labels.return_value = []
                main()

        captured = capsys.readouterr()
        assert (
            "Failed to produce output" in captured.out
            or "laebelmaker -i" in captured.out
        )
