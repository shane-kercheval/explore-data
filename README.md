# project-template

This repo contains a minimal project template.

The structure and documents were heavily influenced from:

- https://github.com/drivendata/cookiecutter-data-science
- https://github.com/Azure/Azure-TDSP-ProjectTemplate

---

This project contains

- dockerfile
- linting
- unit tests
- makefile and command line program (via click)

# Running the Project

All commmands for running the project can be found in the `Makefile` and ran in the command-line with the command `make [command]`.

## Starting Docker

Build and run docker-compose:

```commandline
make docker_run
```

```commandline
make docker_open
```

Running the entire project (tests, ETL, EDA, etc.) from command-line (outside of docker container):

```commandline
make docker_all
```

Running the entire project (tests, ETL, EDA, etc.) from command-line (inside docker container):

```commandline
make all
```

## Running the Code

The `Makefile` runs all components of the project. You can think of it as containing the implicit DAG, or recipe, of the project.

**Run make commands from terminal connected to container via `make docker_run` or `make zsh`**.

If you want to run the entire project from start to finish, including unit tests and linting, run:

```
make all
```

Common commands available from the Makefile are:

- `make all`: The entire project can be built/ran with the simple command `make all` from the project directory, which runs all components (build virtual environments, run tests, run scripts, generate output, etc.)
- `make clean`: Removes all virtual environments, python/R generated/hidden folders, and interim/processed data.
- `make data`: Runs ETL scripts
- `make explore`: Runs exploration notebooks and generate html/md documents.

See `Makefile` for additional commands and implicit project DAG.

---
