"""Test fixtures for the project."""
import os
from itertools import product
from dotenv import load_dotenv
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import helpsk.pandas as hp

import yaml

load_dotenv()


def generate_combinations(lists: list[list[str]]) -> list[tuple]:
    """Get all combinations of the items in the lists. There can be any number of lists."""
    if not lists:
        return []
    return list(product(*lists))


@pytest.fixture()
def mock_data1() -> pd.DataFrame:
    """Create a dataframe with various data types."""
    return pd.DataFrame({
        'date_string': ['2023-08-01', '2023-08-15', '2023-09-01'],
        'date_string_with_missing': ['2023-08-01', '2023-08-15', np.nan],
        'datetime_string': ['2023-08-01 12:00:00', '2023-08-15 15:30:00', '2023-09-01 18:45:00'],
        'datetime_string_with_missing': [np.nan, '2023-08-01 12:00:00', '2023-08-15 15:30:00'],
        'random_strings': ['abc', 'def', 'ghi'],
        'integers': [10, 20, 30],
        'integers_with_missing': [np.nan, 20, 30],
        'floats': [1.5, 2.7, 3.0],
        'floats_with_missing': [1.5, 2.7, np.nan],
        'booleans': [True, False, True],
        'booleans_with_missing': [np.nan, True, False],
        'datetimes': [datetime(2023, 8, 1), datetime(2023, 8, 15), datetime(2023, 9, 1)],
        'datetimes_with_missing': [datetime(2023, 8, 1), pd.NaT, datetime(2023, 9, 1)],
        'dates': [datetime(2023, 8, 1).date(), datetime(2023, 8, 15).date(), datetime(2023, 9, 1).date()],  # noqa
        'dates_with_missing': [pd.NaT, datetime(2023, 8, 15).date(), datetime(2023, 9, 1).date()],
    })

@pytest.fixture()
def mock_data2() -> pd.DataFrame:
    """Create a dataframe with various data types."""
    return pd.DataFrame({
        'integers': [1, 2, 3, 4, 5],
        'integers_with_missing': [1, 2, np.nan, 4, 5],
        'integers_with_missing2': [None, 2, np.nan, 4, 5],
        'floats': [1.1, 2.2, 3.3, 4.4, 5.5],
        'floats_with_missing': [1.1, 2.2, np.nan, 4.4, 5.5],
        'floats_with_missing2': [None, 2.2, np.nan, 4.4, 5.5],
        'booleans': [True, False, True, False, True],
        'booleans_with_missing': [True, False, np.nan, False, True],
        'booleans_with_missing2': [None, False, np.nan, False, True],
        'strings': ['a', 'b', 'c', 'a', 'b'],
        'strings_with_missing': ['a', 'b', np.nan, 'a', 'b'],
        'strings_with_missing2': [None, 'b', np.nan, 'a', 'b'],
        'categories': pd.Categorical(['a', 'b', 'c', 'a', 'b']),
        'categories_with_missing': pd.Categorical(['a', 'b', np.nan, 'a', 'b']),
        'categories_with_missing2': pd.Categorical([None, 'b', np.nan, 'a', 'b']),
        'dates': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),  # noqa
        'dates_with_missing': pd.to_datetime(['2023-01-01', '2023-01-02', np.nan, '2023-01-04', '2023-01-05']),  # noqa
        'dates_with_missing2': pd.to_datetime([None, '2023-01-02', np.nan, '2023-01-04', '2023-01-05']),  # noqa
        'datetimes': pd.to_datetime(['2023-01-01 01:01:01', '2023-01-02 02:02:02', '2023-01-03 03:03:03', '2023-01-04 04:04:04', '2023-01-05 05:05:05']),  # noqa
        'datetimes_with_missing': pd.to_datetime(['2023-01-01 01:01:01', '2023-01-02 02:02:02', np.nan, '2023-01-04 04:04:04', '2023-01-05 05:05:05']),  # noqa
        'datetimes_with_missing2': pd.to_datetime([None, '2023-01-02 02:02:02', np.nan, '2023-01-04 04:04:04', '2023-01-05 05:05:05']),  # noqa
    })

@pytest.fixture()
def graphing_configurations() -> dict:
    """Load graphing configurations from yaml file."""
    with open(os.path.join(os.getenv('PROJECT_PATH'), 'source/config/graphing_configurations.yml')) as f:  # noqa
        return yaml.safe_load(f)['configurations']


@pytest.fixture()
def credit_data() -> pd.DataFrame:
    """Load credit dataset."""
    return pd.read_csv(os.path.join(os.getenv('PROJECT_PATH'), 'data/credit.csv'))


@pytest.fixture()
def conversions_data() -> pd.DataFrame:
    """Load conversion dataset."""
    return pd.read_csv(os.path.join(os.getenv('PROJECT_PATH'), 'data/conversions.csv'))


@pytest.fixture()
def mock_data2_all_columns(mock_data2: pd.DataFrame) -> list[str]:
    """Returns all_columns for mock_data2."""
    return mock_data2.columns.tolist()


@pytest.fixture()
def mock_data2_numeric_columns(mock_data2: pd.DataFrame) -> list[str]:
    """Returns numeric_columns for mock_data2."""
    return hp.get_numeric_columns(mock_data2)


@pytest.fixture()
def mock_data2_date_columns(mock_data2: pd.DataFrame) -> list[str]:
    """Returns date_columns for mock_data2."""
    return hp.get_date_columns(mock_data2)


@pytest.fixture()
def mock_data2_string_columns(mock_data2: pd.DataFrame) -> list[str]:
    """Returns string_columns for mock_data2."""
    return hp.get_string_columns(mock_data2)


@pytest.fixture()
def mock_data2_categorical_columns(mock_data2: pd.DataFrame) -> list[str]:
    """Returns categorical_columns for mock_data2."""
    return hp.get_categorical_columns(mock_data2)


@pytest.fixture()
def mock_data2_boolean_columns(mock_data2: pd.DataFrame, mock_data2_all_columns: str) -> list[str]:
    """Returns boolean_columns for mock_data2."""
    return [x for x in mock_data2_all_columns if hp.is_series_bool(mock_data2[x])]
