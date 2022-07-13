pyho# Laebelmaker

Tool for generating Traefik labels

## Usage

Laebelmaker can be used to automatically generate Traefik labels
from various sources, such as `docker-compose.yml` files, running
Docker containers and user-given options.

You can always consult the help menu for all features with short
(and hopefully clear) explanations:

```
$ laebelmaker -h
usage: laebelmaker [-h] [-i] [-d FILE] [-c NAME] [-f FORMAT]

Generate Traefik labels

options:
  -h, --help            show this help message and exit
  -i, --interactive     use interactive mode
  -d FILE, --docker-compose FILE
                        generate labels from a given Compose file
  -c NAME, --container NAME
                        generate labels for a given container on the system
  -f FORMAT, --format FORMAT
                        set output format, one of: [none, docker, compose]
```

## Examples

Invoking laebelmaker on a Docker Compose YAML file, the program will
prompt the user for different options, with the defaults given in
parentheses. This example also modifies the output format with
`-f compose`, which means the labels are immediately ready to be used
in a YAML file.

```
$ laebelmaker -d examples/docker-compose-testapp.yml -f compose
Found multiple services.
 1. testapp
 2. testapp-db
Select service (1): 1
Change hostname ('testapp'): testapp-newname
Change HTTPS redirection ('no'): yes
TLS resolver to use: default
-- START GENERATED LABELS --
  - traefik.enable=true
  - traefik.http.routers.testapp.rule=Host(`testapp-newname`)
  - traefik.http.routers.testapp.entrypoints=web
  - traefik.http.routers.testapp-https.rule=Host(`testapp-newname`)
  - traefik.http.routers.testapp-https.entrypoints=websecure
  - traefik.http.routers.testapp.middlewares=testapp-redir
  - traefik.http.middlewares.testapp-redir.redirectscheme.scheme=https
  - traefik.http.routers.testapp-https.tls=true
  - traefik.http.routers.testapp-https.tls.certresolver=default
  - traefik.http.services.testapp.loadbalancer.server.port=80
-- END GENERATED LABELS   --
```

## To-do/Guidelines for self

* [ ] Generate Traefik labels using an interactive CLI
* [ ] Generate Traefik labels using command-line options
* [ ] Generate labels from existing service definitions (e.g. Docker Compose YAML files)
* [ ] Ease of use must be a priority
* [ ] Learn how to and publish this project to PyPi

## For developers

Install all requirements before contributing. This is required for `pre-commit`.

Before commiting, install pre-commit hooks for Git by running:
```
pre-commit install
```

This will run Black, MyPy and PyLint before commiting.
