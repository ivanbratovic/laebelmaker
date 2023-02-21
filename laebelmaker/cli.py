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

FORMATS: List[str] = [
    symbol.split("_")[-1] for symbol in globals() if symbol.startswith("format")
]


def has_yaml_extension(path: str) -> bool:
    basename = path.strip().split("/")[-1]
    return basename.lower().endswith(".yaml") or basename.lower().endswith(".yml")


def main() -> None:
    args: argparse.Namespace
    parser: argparse.ArgumentParser
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate Traefik labels")
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

    formatter: Callable[[List[str]], str] = globals()[f"formatter_{args.format}"]
    labels: List[Tuple[str, List[str]]] = []

    if args.interactive:
        try:
            labels = [gen_label_set_from_user("")]
        except NoInformationException as e:
            print(e)
    elif container := args.container:
        try:
            labels = [gen_label_set_from_container(container)]
        except NoInformationException:
            print(f"Invalid container identifier given: {container!r}.")
        except ModuleNotFoundError:
            print(f"Please install the docker module to use this feature.")

    elif args.files:
        for arg in args.files:
            try:
                labels.append(gen_label_set_from_compose(arg))
            except FileNotFoundError:
                print(f"Unknown file path: {arg!r}")
            except NoInformationException as e:
                print(e)
    else:
        parser.print_help()
        return

    if labels:
        for title, label_list in labels:
            print(f"--START GENERATED LABELS FOR {title!r}--")
            print(formatter(label_list), end="")
            print(f"--END GENERATED LABELS FOR {title!r}--")
    else:
        print("Failed to produce output.")
        print("Try running: laebelmaker --help")

    return


if __name__ == "__main__":
    main()
