#!/usr/bin/env python

from typing import *
from util.label import *


def main() -> None:
    print("\n # Simple service with an explicit port\n")
    cfg = ServiceConfig(
        name="test_service", rule=Rule("Host", ["example.com"]), port=25565
    )
    labels = gen_simple_label_set_for_service(cfg)
    print("labels:", *labels, sep="\n  - ")

    print("\n # Simple service with HTTPS redirect\n")
    cfg = ServiceConfig(
        name="test_service",
        rule=Rule("Host", ["example.com"]),
        https_redir=True,
        tls_resolver="letsencrypt",
    )
    labels = gen_simple_label_set_for_service(cfg)
    print("labels:", *labels, sep="\n  - ")

    print("\n # Read from docker-compose.yml\n")
    labels = gen_label_set_from_compose("docker-compose-testapp.yml")
    print("labels:", *labels, sep="\n  - ")


if __name__ == "__main__":
    main()
