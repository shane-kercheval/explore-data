"""
Function definitions for the command line interface. The makefile calls the commands defined in
this file.

For help in terminal, navigate to the project directory, run the docker container, and from within
the container run the following examples:
    - `source/scripts/commands.py --help`
    - `source/scripts/commands.py extract --help`
"""
import os.path
import logging.config
import logging
import click

import source.service.etl as etl
from source.service.datasets import DATA
from source.config.settings import settings


logging.config.fileConfig(
    settings.LOGGING_CONFIG_PATH,
    defaults={'logfilename': os.path.join(settings.DIR_OUTPUT, settings.LOGGING_FILE_NAME)},
    disable_existing_loggers=False,
)


@click.group()
def main() -> None:
    """Logic For Extracting and Transforming Datasets."""
    pass


@main.command()
def extract() -> None:
    """Downloads the credit data from openml.org."""
    credit_data = etl.extract()
    logging.info(
        f"Credit data downloaded with {credit_data.shape[0]} "
        f"rows and {credit_data.shape[1]} columns.",
    )
    DATA.raw__credit.save(credit_data)


@main.command()
def transform() -> None:
    """Transforms the credit data."""
    raw__credit = DATA.raw__credit.load()
    logging.info("Transforming credit data.")
    credit = etl.transform(raw__credit)
    DATA.credit.save(credit)


if __name__ == '__main__':
    main()
