#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
    echo "You must activate this project's virtual environment before proceeding."
    exit 1
fi

if ! which "pip-compile"; then
    echo "The 'pip-compile' binary was not found. You're in the wrong venv."
    exit 2
fi

pip-compile pyproject.toml -o requirements.txt --upgrade
pip-compile --extra=dev pyproject.toml -o requirements-dev.txt --upgrade
