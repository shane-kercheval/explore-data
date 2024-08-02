.PHONY: create_environment install_requirements run_app

####
# DOCKER
####
docker_build:
	docker compose -f docker-compose.yml build

docker_run: docker_build
	docker compose -f docker-compose.yml up

docker_app:
	docker compose -f docker-compose.yml up --build app

client:
	open 'http://127.0.0.1:8050'

####
# Virtual Environment
####
# conda remove --name explore_data --all
create_environment:
	conda env create -f environment.yaml

# activate contda environment via `conda activate explore_data`
# install_requirements:
# 	pip install -r requirements.txt
# 	pip install -r https://raw.githubusercontent.com/snowflakedb/snowflake-connector-python/v3.0.4/tested_requirements/requirements_311.reqs
# 	pip install snowflake-connector-python==v3.0.4
# 	pip install "snowflake-connector-python[pandas]"

# activate conda environment via `conda activate explore_data`
app:
	python app.py

####
# Project
####
linting:
	ruff check app.py
	ruff check source/library
	ruff check tests

unittests:
	rm -f tests/test_files/log.log
	coverage run -m pytest --durations=0 tests
	coverage html

doctests:
	python -m doctest source/library/utilities.py

tests: linting unittests doctests

open_coverage:
	open 'htmlcov/index.html'

# explore:
# 	jupyter nbconvert --execute --to html source/notebooks/datasets.ipynb
# 	mv source/notebooks/datasets.html output/data/datasets.html
# 	jupyter nbconvert --execute --to html source/notebooks/data-profile.ipynb
# 	mv source/notebooks/data-profile.html output/data/data-profile.html
