.PHONY: create_environment install_requirements run_app

####
# DOCKER
####
# docker_build:
# 	docker compose -f docker-compose.yml build

# docker_run: docker_build
# 	docker compose -f docker-compose.yml up

# docker_app:
# 	docker compose -f docker-compose.yml up --build app

# client:
# 	open 'http://127.0.0.1:8050'

run:
	uv run python app.py

####
# Project
####
linting:
	uv run ruff check app.py
	uv run ruff check source/library
	uv run ruff check tests

unittests:
	rm -f tests/test_files/log.log
	uv run coverage run -m pytest --durations=0 tests
	uv run coverage html

doctests:
	uv run python -m doctest source/library/utilities.py

tests: linting unittests doctests

open_coverage:
	open 'htmlcov/index.html'

# explore:
# 	jupyter nbconvert --execute --to html source/notebooks/datasets.ipynb
# 	mv source/notebooks/datasets.html output/data/datasets.html
# 	jupyter nbconvert --execute --to html source/notebooks/data-profile.ipynb
# 	mv source/notebooks/data-profile.html output/data/data-profile.html
