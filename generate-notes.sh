#!/bin/bash

set -e

# Get the first heading from CHANGELOG.md
first_heading=$(head -n 1 CHANGELOG.md | cut -d" " -f2)

# Check if the first heading is [Unreleased]
if [[ "$first_heading" == "[Unreleased]" ]]; then
    echo "CHANGELOG.md contains [Unreleased] section - this is not a release commit."
    echo "Skipping release notes generation."
    exit 0
fi

echo -e "## Changelog" > NOTES.md

version_changelog="$first_heading"
version_pyproject=$(grep -E "^version" pyproject.toml | grep -E --only-matching "[0-9]+.[0-9]+.[0-9]+")
if [[ "$version_changelog" != "$version_pyproject" ]]; then
    echo "Error generating NOTES.md: Version mismatch!"
    echo " ├── In CHANGELOG file: $version_changelog"
    echo " └── In pyproject.toml: $version_pyproject"
    exit 1
fi

version="$version_changelog"

while IFS= read -r line; do
    if [[ $line == "## $version" ]]; then
        continue
    fi
    if [[ $line == \#\#* ]]; then
        previous_version=$(echo "$line" | grep -E --only-matching "[0-9]+.[0-9]+.[0-9]+") 
        break
    fi
    echo "$line" >> NOTES.md
done < CHANGELOG.md

echo "**Full Changelog**: https://github.com/ivanbratovic/laebelmaker/compare/$previous_version...$version" >> NOTES.md
echo "**Release on PyPI**: https://pypi.org/project/laebelmaker/$version/" >> NOTES.md

echo "Generated NOTES.md for Release v$version."
