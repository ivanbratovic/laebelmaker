
- run `black` to format the code
- run `pylint` to lint the code and warn about the number of issues
- run `mypy` to test typing
- run `pytest` to run tests

- update version in @pyproject.toml using [Semantic Versioning 2.0.0](https://semver.org/) specification
- check argument 1: "$1" for instruction on which part of semver to increment otherwise increment patch part
- update changelog using [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) specification
  - merge multiple `## [Unreleased]` subsections like `### Added` and others into one `### Added`,
    sometimes we will have two or more `### Added` subsections because of git merges
  - turn `## [Unreleased]` section into released section with version and date, example: `## [1.1.1] - 2023-03-05`
- write commit message using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification

- git commit changes
- git push changes
- git create tag that is version number
- git push tag
