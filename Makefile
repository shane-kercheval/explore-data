####
# DOCKER
####
docker_build:
	docker compose -f docker-compose.yml build

docker_run: docker_build
	docker compose -f docker-compose.yml up

app:
	docker compose -f docker-compose.yml up --build app

app_client:
	open 'http://127.0.0.1:8050'

zsh:
	docker exec -it data-science-template-bash-1 /bin/zsh

####
# Project
####
linting:
	ruff check source/config
	ruff check source/entrypoints
	ruff check source/library
	ruff check source/notebooks
	ruff check source/service
	ruff check tests

unittests:
	rm -f tests/test_files/log.log
	# pytest tests
	coverage run -m pytest --durations=0 tests
	coverage html

doctests:
	python -m doctest source/library/utilities.py

tests: linting unittests doctests

open_coverage:
	open 'htmlcov/index.html'

data_extract:
	python source/entrypoints/cli.py extract

data_transform:
	python source/entrypoints/cli.py transform

data: data_extract data_transform

explore:
	jupyter nbconvert --execute --to html source/notebooks/datasets.ipynb
	mv source/notebooks/datasets.html output/data/datasets.html
	jupyter nbconvert --execute --to html source/notebooks/data-profile.ipynb
	mv source/notebooks/data-profile.html output/data/data-profile.html

remove_logs:
	rm -f output/log.log

## Run entire workflow.
all: tests remove_logs data explore

## Delete all generated files (e.g. virtual)
clean:
	rm -f data/raw/*.pkl
	rm -f data/raw/*.csv
	rm -f data/processed/*
