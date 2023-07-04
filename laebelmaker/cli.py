#!/usr/bin/env python

"""
Generates Traefik labels for use in e.g. Docker containers.
"""

__author__ = "Ivan Bratović"
__copyright__ = "Copyright 2023, Ivan Bratović"
__license__ = "MIT"
__version__ = "0.4.0"

import argparse
from typing import List, Tuple, Callable
from laebelmaker.label import (
    gen_label_set_from_user,
    gen_label_set_from_compose,
    gen_label_set_from_container,
)
from laebelmaker.errors import NoInformationException
from laebelmaker.utils.formatter import (  # pylint: disable=unused-import
    formatter_docker,
    formatter_none,
    formatter_yaml,
)

# List of available/imported formatters.
# Each format is a global variable whose name starts with "format_"
# and ends with a suffix indicating the format type. See available format
# types in the import statement above.
FORMATS: List[str] = [
    symbol.split("_")[-1] for symbol in globals() if symbol.startswith("formatter_")
]


def has_yaml_extension(path: str) -> bool:
    """Checks if a given path has a YAML extension."""
    basename = path.strip().split("/")[-1]
    return basename.lower().endswith(".yaml") or basename.lower().endswith(".yml")


def print_labels(
    labels: List[Tuple[str, List[str]]], formatter: Callable[[List[str]], str]
) -> None:
    """Prints labels with a given formatter."""
    for title, label_list in labels:
        if not label_list:
            continue
        print(f"--START GENERATED LABELS FOR {title!r}--")
        print(formatter(label_list), end="")
        print(f"--END GENERATED LABELS FOR {title!r}--")


def labels_from_user() -> List[Tuple[str, List[str]]]:
    """Wrapper for gen_label_set_from_user with exception handling."""
    labels: List[Tuple[str, List[str]]] = []
    try:
        labels = [gen_label_set_from_user("")]
    except NoInformationException as exception:
        print(exception)
    return labels


def labels_from_container(container: str) -> List[Tuple[str, List[str]]]:
    """Wrapper for gen_label_set_from_container with exception handling."""
    labels: List[Tuple[str, List[str]]] = []
    try:
        labels = [gen_label_set_from_container(container)]
    except NoInformationException:
        print(f"Invalid container identifier given: {container!r}.")
    except ModuleNotFoundError:
        print("Please install the docker module to use this feature.")
    return labels


def labels_from_compose_files(files: List[str]) -> List[Tuple[str, List[str]]]:
    """Iterates over given file list and calls gen_label_set_from_compose,
    with exception handling.
    """
    labels: List[Tuple[str, List[str]]] = []
    for filepath in files:
        try:
            labels.append(gen_label_set_from_compose(filepath))
        except FileNotFoundError:
            print(f"Unknown file path: {filepath!r}")
        except NoInformationException as exception:
            print(exception)
    return labels


def main() -> None:
    """Main CLI function."""
    args: argparse.Namespace
    parser: argparse.ArgumentParser
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        prog="laebelmaker",
        description="Generate Traefik labels",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="print version and exit",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="use interactive mode",
    )
    parser.add_argument(
        "-c",
        "--container",
        metavar="NAME",
        help="generate labels for a given container on the system",
    )
    parser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        help=f"set output format, one of: [{', '.join(FORMATS)}]",
        choices=FORMATS,
        default="none",
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="*",
        help="Compose file to generate labels for",
    )

    args, _ = parser.parse_known_args()

    labels: List[Tuple[str, List[str]]] = []

    if args.version:
        print(f"Laebelmaker v{__version__}, ")
        return

    if args.interactive:
        labels = labels_from_user()
    elif container := args.container:
        labels = labels_from_container(container)
    elif files := args.files:
        labels = labels_from_compose_files(files)
    else:
        parser.print_help()
        return

    if labels:
        # Get imported formatter object from globals, by its name
        formatter: Callable[[List[str]], str] = globals()[f"formatter_{args.format}"]
        print_labels(labels, formatter)
    else:
        print("Failed to produce output.")
        print("You can use 'laebelmaker -i' to generate labels manually")

    return


if __name__ == "__main__":
    main()
