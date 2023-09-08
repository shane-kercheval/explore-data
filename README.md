# project-template

- shit; adding new filters removes existing filters
- Filtering needs to handle missing values
    - missing values shouldn't make it crash
    - should be able to filter on missing values
    - if filtering on numeric/date/etc, filtering values are automatically removed
    - where do i display what is currently being filtered?


- test categorical in filtering and what we display
- test boolean with na (shows up as object)

# Running the project

- .env (shouldn't need to modify unless you're serving the app non-locally)
-


## Known Issues


- The user needs to refresh the app before loading a different dataset.
- This app is only tested with a single user running a local server; it is not tested/supported for multi-user non-local servers.
- Selecting `Bin Months` (which bins the datetime column into months) doesn't play nice with some date `Date Floor` selections like `Week`. The solution is to only display/use `Bin Months` for valid selections of `Date Floor`. Fix TBD.
- Doing a count distinct with a datetime variable (date as x and non-numeric as y) without first selecting `Date Floor` of `Day` or higher freezes up the app if the granularity of the datetime variable is something like seconds.
- The `file_system_backend` directory will grow indefinitely
    - https://www.dash-extensions.com/transforms/serverside_output_transform


## Filtering

- filtering on dates, datetimes, or numeric (int/float) automatically removes missing values



## Combinations

create a spreadsheet (or something) to track the combinations.. and expected types of graphs possible and default

e.g. 

- `x (numeric)`
    - box
    - histogram
    - scatter (y is index)
    - bar (y is index)




# TODO Update


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
