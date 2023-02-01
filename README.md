# Laebelmaker

<a target="_blank" href="https://pypi.org/project/laebelmaker/"><img src="https://img.shields.io/pypi/v/laebelmaker.svg?maxAge=86400&style=flat-square"/></a>
<a target="_blank" href="https://choosealicense.com/licenses/mit/"><img src="https://img.shields.io/pypi/l/laebelmaker.svg?maxAge=86400&style=flat-square"/></a>
<a target="_blank" href="https://pypi.org/project/laebelmaker/"><img src="https://img.shields.io/pypi/dm/laebelmaker?style=flat-square"/></a>
<a target="_blank" href="https://pypi.org/project/laebelmaker/"><img src="https://img.shields.io/pypi/pyversions/laebelmaker.svg?maxAge=86400&style=flat-square"/></a>
<a target="_blank" href="https://github.com/ivanbratovic/laebelmaker"><img src="https://img.shields.io/github/last-commit/ivanbratovic/laebelmaker?style=flat-square" /></a>

Tool for generating Traefik labels. Written in Python.

## Installation

Laebelmaker is published on PyPI. You can use pip to install it:
```
python3 -m pip install --user laebelmaker
```

It is recommended that you also install the `docker` module. You
can install both Laebelmaker and docker as its dependency with:
```
python3 -m pip install --user laebelmaker[docker]
```

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
                        set output format, one of: [none, docker, yaml]
```

## Examples

### GUI Interactive Mode

```
$ laebelmaker -i
Enter value for 'name': testapp
Enter new value for 'hostname': test
Enter new value for 'port': 25565
Enter value for 'https_redir' (yes/no): no
-- START GENERATED LABELS --
traefik.enable=true
traefik.http.routers.testapp.rule=Host(`test`)
traefik.http.services.testapp.loadbalancer.server.port=25565
-- END GENERATED LABELS   --
```


### With Compose YAML file

Invoking laebelmaker on a Docker Compose YAML file, the program will
prompt the user for different options, with the defaults given in
parentheses. This example also modifies the output format with
`-f yaml`, which means the labels are immediately ready to be used
in a YAML file.

```
$ laebelmaker -d examples/docker-compose-testapp.yml -f yaml
Found multiple services.
 1. testapp
 2. testapp-db
Select service (1): 1
Enter new value for 'hostname': testapp-customname
Enter value for 'https_redir' (yes/no): yes
Enter new value for 'web_entrypoint': http
Enter new value for 'websecure_entrypoint': https
Enter value for 'tls_resolver': letsencrypt
-- START GENERATED LABELS --
  - traefik.enable=true
  - traefik.http.routers.testapp.rule=Host(`testapp-customname`)
  - traefik.http.routers.testapp.entrypoints=http
  - traefik.http.routers.testapp-https.rule=Host(`testapp-customname`)
  - traefik.http.routers.testapp-https.entrypoints=https
  - traefik.http.routers.testapp.middlewares=testapp-redir
  - traefik.http.middlewares.testapp-redir.redirectscheme.scheme=https
  - traefik.http.routers.testapp-https.tls=true
  - traefik.http.routers.testapp-https.tls.certresolver=letsencrypt
  - traefik.http.services.testapp.loadbalancer.server.port=80
-- END GENERATED LABELS   --
```

## To-do

* [x] Generate Traefik labels using an interactive CLI
* [x] Generate Traefik labels using command-line options
* [x] Generate labels from existing service definitions (e.g. Docker Compose YAML files)
* [x] Learn how to and publish this project to PyPi
* [ ] Add more data sources
* [ ] Add more Rule types
* [ ] Add combined Rule types (with logical operators)
* [ ] Compatibility for Windows machines

## Guidelines for development

* Ease of use is a priority
* More guidelines must be added

## For developers

For local development, a virtual environment is highly recommended. The following
section will assume you installed a virtual environment with the venv module:
```
python3 -m venv venv
```

Install all requirements before contributing. This is required for `pre-commit`.
All requirements for development are given in `requirements.txt`.

Before commiting, install pre-commit hooks for Git by running:
```
pre-commit install
```

This will run Black, MyPy and PyLint before commiting.

You can install the Laebelmaker project locally in
[Development Mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):
```
python3 -m pip install -e .
```
The project will be installed but will remain editable.
