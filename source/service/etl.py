"""Contains the logic for extracting and transforming the project data."""

import warnings
import logging

import numpy as np
import pandas as pd

from helpsk.logging import log_function_call, log_timer
from sklearn.datasets import fetch_openml


@log_function_call
@log_timer
def extract() -> pd.DataFrame:
    """Downloads and returns the credit data from openml.org."""
    logging.info("Downloading credit data from https://www.openml.org/d/31")
    credit_g = fetch_openml('credit-g', version=1)
    credit_data = credit_g['data']
    credit_data['target'] = credit_g['target']
    return credit_data


@log_function_call
@log_timer
def transform(credit__raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the credit data.

    Args:
        credit__raw: the raw data to transform
    """
    credit = credit__raw.copy()
    # Create Missing Values
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        credit['duration'].iloc[0:46] = np.nan
        credit['checking_status'].iloc[25:75] = np.nan
        credit['credit_amount'].iloc[10:54] = 0
    return credit
