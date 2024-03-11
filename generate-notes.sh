#!/bin/bash

set -e

echo -e "## Changelog" > NOTES.md

version_changelog=$(head -n 1 CHANGELOG.md | cut -d" " -f2)
version_pyproject=$(grep -E "^version" pyproject.toml | grep -E --only-matching "[0-9]+.[0-9]+.[0-9]+")
if [[ "$version_changelog" != "$version_pyproject" ]]; then
    echo "Error generating NOTES.md: Version mismatch!"
    echo "  Latest in CHANGELOG.md: $version_changelog"
    echo "  Version in pyproject.toml: $version_pyproject"
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
