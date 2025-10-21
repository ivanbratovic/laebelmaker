## [Unreleased]

### Added
- Added support for loading Traefik configuration files (traefik.yml or traefik.toml)
- Added new CLI option `-t/--traefik-config` to specify Traefik config file
- Added intelligent port-based entrypoint detection (detects port 80 and 443)
- Added automatic detection of default entrypoints (web/http, websecure/https)
- Added automatic detection of TLS certificate resolvers from Traefik config
- Added auto-fill feature: when TraefikConfig is loaded, entrypoints and TLS resolvers are filled automatically without prompting user
- Added new `TraefikConfig` dataclass to store configuration data
- Added example traefik.toml file in examples/ directory
- Added comprehensive test suite for Traefik config parsing and auto-fill (20 new tests)

### Changed
- Updated all development dependencies to latest versions
- Updated PyYAML from 6.0.2 to 6.0.3 (security fix)
- Updated black from 24.8.0 to 25.9.0
- Updated pylint from 3.3.1 to 4.0.2
- Updated mypy from 1.11.2 to 1.18.2
- Updated pytest from 8.3.3 to 8.4.2
- Updated pre-commit from 3.8.0 to 4.3.0
- Updated requests from 2.32.3 to 2.32.5 (security fix)
- Updated certifi from 2024.8.30 to 2025.10.5 (security fix)
- Updated 23+ other dependencies to latest versions
- Added Python 3.12 to supported versions in project metadata
- Modified `ServiceConfig` to automatically apply TraefikConfig defaults via `__post_init__`
- Updated all label generation functions to accept optional TraefikConfig parameter
- Refactored Traefik config parsing to use shared helper function (DRY principle)
- Extracted magic strings "web" and "websecure" to constants `DEFAULT_WEB_ENTRYPOINT` and `DEFAULT_WEBSECURE_ENTRYPOINT`
- Made TraefikConfig fields required (no defaults) - values are always determined from actual config file

### Fixed
- Removed unused imports from test files
- Applied Black formatting to all source files
- Fixed validation logic to properly handle empty Traefik configuration files

## 0.4.1

- Bug fixes

## 0.4.0

- Add parsing of Docker build context from Compose YAML
- Reorganize project structure
- Update output format to include label group name
- Update PyPI classifiers
- Various bugfixes and code cleanup

## 0.3.0

- Add parsing of Path Traefik rule

## 0.2.1

- Improve error handling
- Improve output quality
- Refactor code to be more readable

## 0.2.0

- Added interactive mode (as -i option)
- Prompts are now prefilled when possible
- Import of docker module is not mandatory anymore

## 0.1.0

- Initial version