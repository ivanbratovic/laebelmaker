## [Unreleased]

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

### Fixed
- Removed unused imports from test files
- Applied Black formatting to all source files

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