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
This will allow Laebelmaker to use metadata of Docker images
to prevent redundant prompts from the user, e.g. when an image
exposes a single port.

## Usage

Laebelmaker can be used to automatically generate Traefik labels
from various sources, such as `docker-compose.yml` files, running
Docker containers and user-given options.

You can always consult the help menu for all features with short
(and hopefully clear) explanations:

```
$ laebelmaker
usage: laebelmaker [-h] [-i] [-c NAME] [-f FORMAT] [FILES ...]

Generate Traefik labels

positional arguments:
  FILES                 list of Compose files to generate labels for

options:
  -h, --help            show this help message and exit
  -i, --interactive     use interactive mode
  -c NAME, --container NAME
                        generate labels for a given container on the system
  -f FORMAT, --format FORMAT
                        set output format, one of: [docker, none, yaml]
```

## Examples

### CLI Interactive Mode

```
$ laebelmaker -i
Enter value for 'deploy name': testapp
Enter new value for 'hostname and context path': test/traefik
Enter new value for 'port': 25565
Enter value for 'https redirection' (yes/No): no
-- START GENERATED LABELS --
traefik.enable=true
traefik.http.routers.testapp.rule=Host(`test`) && Path(`/traefik`)
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
$ laebelmaker -f yaml examples/docker-compose-testapp.yml
Found multiple services.
 1. testapp
 2. testapp-db
Service number to use (default 1): 1
Enter new value for 'hostname': testapp-customname
Enter value for 'https redirection' (yes/No): yes
Enter new value for 'web entrypoint': http
Enter new value for 'websecure entrypoint': https
Enter value for 'tls resolver': letsencrypt
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

If an invalid file is given, Laebelmaker should hopefully print a
sensible error message.
```
$ laebelmaker examples/invalid-image-tag.yml
Pulling image:
 ⠿ ubuntu:latestest Failed
Invalid image tag: 'ubuntu:latestest' in 'examples/invalid-image-tag.yml'.
Failed to produce output.
Try running: laebelmaker --help
```

## To-do

* [x] Generate Traefik labels using an interactive CLI
* [x] Generate Traefik labels using command-line options
* [x] Generate labels from existing service definitions (e.g. Docker Compose YAML files)
* [x] Learn how to and publish this project to PyPi
* [x] Add combined Rule types (with logical operators)
* [ ] Add automated tests
* [ ] Remove pyyaml as a hard dependency
* [ ] Add local Traefik config as data source (e.g. for entrypoint and TLS resolver names)
* [ ] Add Dockerfile as a data source
* [ ] Add K8s YAML as a data source
* [ ] Add more sophisticated Rule parsing (e.g. from a given URL)

Something to think about:

* [ ] Expand out of Traefik into a more general use-case
* [ ] Compatibility for Windows machines

## Guidelines for development

* Ease of use is a priority
* Use sensible defaults without asking, when possible
* When defaults are not possible, offer the user a sensible prefilled value
* The code should be as Pythonic as possible
* Use type hints as much as possible to catch logical errors

## Local development setup

For local development, a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
is highly recommended. The following section will assume you installed a virtual
environment with the [`venv`](https://docs.python.org/3/library/venv.html) module:
```
python3 -m venv venv
```

All requirements for development are given in `requirements-dev.txt`.
Install all of them before contributing. This is required for `pre-commit`.

Before commiting, install pre-commit hooks for Git by running:
```
pre-commit install
```

This will run the following programs to verify a commit:

* [Black](https://pypi.org/project/black) - code formatting
* [MyPy](https://mypy.readthedocs.io/en/stable/) - static type checking
* [PyLint](https://pypi.org/project/pylint/) - code linting

You can install the Laebelmaker project locally in
[Development Mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):
```
python3 -m pip install -e .
```
The project will be installed in the virtual environment but will remain editable.
