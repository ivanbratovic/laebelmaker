# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
# Install development dependencies
python3 -m pip --require-virtualenv install -r requirements-dev.txt
# Install pre-commit hooks
pre-commit install
# Install project in development mode
python3 -m pip install -e .
```

### Code Quality and Testing
```bash
# Run all pre-commit checks (formatting, linting, type checking, tests)
pre-commit run --all-files

# Individual tools (as configured in .pre-commit-config.yaml):
black --diff --check .          # Code formatting check
pylint --disable=all --enable=unused-import laebelmaker/  # Import linting
mypy --strict --namespace-packages --ignore-missing-imports laebelmaker/  # Type checking (excludes tests/)
pytest                          # Run all tests

# Format code
black .
```

### Building and Publishing
```bash
# Build package
python3 -m build

# Run the tool locally
laebelmaker --help
laebelmaker -i                  # Interactive mode
```

## Project Architecture

### Core Components
- **`laebelmaker/cli.py`**: Main CLI interface and argument parsing. Entry point for the `laebelmaker` command.
- **`laebelmaker/label.py`**: Core label generation logic with functions:
  - `gen_label_set_from_user()` - Interactive user input
  - `gen_label_set_from_compose()` - Docker Compose file parsing
  - `gen_label_set_from_container()` - Running container inspection
- **`laebelmaker/datatypes.py`**: Data models including `ServiceConfig`, `Rule`, and `CombinedRule` classes
- **`laebelmaker/errors.py`**: Custom exception classes
- **`laebelmaker/utils/`**: Utility modules for formatting, input handling, and data loading

### Data Flow
1. CLI parses arguments and determines input source (interactive, compose file, or container)
2. Appropriate generation function creates `ServiceConfig` objects
3. Label generation functions in `label.py` convert configs to Traefik label strings
4. Output formatters in `utils/formatter.py` format labels for different use cases (docker, yaml, plain)

### Key Features
- Generates Traefik v2 HTTP router and service labels
- Supports multiple input sources: interactive CLI, Docker Compose files, running containers
- Configurable output formats: docker labels, YAML array, plain text
- Rule types: Host, Path, PathPrefix, Headers, with support for combined rules
- HTTPS redirection and TLS certificate resolver configuration

### Dependencies
- **Core**: `pyyaml` for YAML parsing
- **Optional**: `docker` for container inspection (install with `pip install laebelmaker[docker]`)
- **Development**: Black, PyLint, MyPy, PyTest, pre-commit

### Testing
- Tests located in `tests/` directory
- Uses PyTest framework
- Tests include Docker availability checks for container-related functionality
- Run with `pytest` or as part of pre-commit hooks