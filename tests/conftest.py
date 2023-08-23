"""Test fixtures for the project."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime


@pytest.fixture()
def data() -> pd.DataFrame:
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
        'dates': [datetime(2023, 8, 1).date(), datetime(2023, 8, 15).date(), datetime(2023, 9, 1).date()],
        'dates_with_missing': [pd.NaT, datetime(2023, 8, 15).date(), datetime(2023, 9, 1).date()],
    })
