"""Defines the types of data that can be used in the library."""
import pandas as pd
import helpsk.pandas as hp


NUMERIC = 'numeric'
DATE = 'date'
STRING = 'string'
CATEGORICAL = 'categorical'
BOOLEAN = 'boolean'

DISCRETE_TYPES = {STRING, CATEGORICAL, BOOLEAN}
CONTINUOUS_TYPES = {NUMERIC, DATE}


def is_series_datetime(series: pd.Series) -> bool:
    """Check if a series can be converted to a datetime."""
    if pd.api.types.is_numeric_dtype(series):
        return False
    try:
        parsed = pd.to_datetime(series)
    except Exception:
        return False
    # Empty strings and all-missing columns parse to all NaT without raising.
    return bool(parsed.notna().any())


def get_column_type(series: pd.Series) -> str:
    """
    Return one of 'numeric', 'date', 'string', 'categorical', 'boolean' for the series.

    Object columns from databases often pass more than one check (e.g. '1' is numeric and a
    string, and integers parse as dates), so the checks run in a fixed order and the first match
    wins. Anything that matches no check (e.g. all missing values, dicts) is treated as a string.
    """
    if isinstance(series.dtype, pd.CategoricalDtype):
        return CATEGORICAL
    if hp.is_series_bool(series):
        return BOOLEAN
    if hp.is_series_numeric(series) and not hp.is_series_string(series):
        return NUMERIC
    # Date strings count as dates; callers convert them with `pd.to_datetime` when used.
    if is_series_datetime(series):
        return DATE
    return STRING


def get_column_types(data: pd.DataFrame) -> dict:
    """Map each column name to its type; see `get_column_type`."""
    return {column: get_column_type(data[column]) for column in data.columns}


def get_all_columns(column_types: dict) -> list[str]:
    """Return a list of all columns."""
    return list(column_types.keys())


def get_numeric_columns(column_types: dict) -> list[str]:
    """Return a list of columns that are numeric."""
    return [x for x, y in column_types.items() if y == NUMERIC]


def get_date_columns(column_types: dict) -> list[str]:
    """Return a list of columns that are dates."""
    return [x for x, y in column_types.items() if y == DATE]


def get_string_columns(column_types: dict) -> list[str]:
    """Return a list of columns that are strings."""
    return [x for x, y in column_types.items() if y == STRING]


def get_categorical_columns(column_types: dict) -> list[str]:
    """Return a list of columns that are categorical."""
    return [x for x, y in column_types.items() if y == CATEGORICAL]


def get_boolean_columns(column_types: dict) -> list[str]:
    """Return a list of columns that are booleans."""
    return [x for x, y in column_types.items() if y == BOOLEAN]


def get_discrete_columns(column_types: dict) -> list[str]:
    """Return a list of columns that are discrete."""
    return [x for x, y in column_types.items() if y in DISCRETE_TYPES]


def get_continuous_columns(column_types: dict) -> list[str]:
    """Return a list of columns that are continuous."""
    return [x for x, y in column_types.items() if y in CONTINUOUS_TYPES]


def is_type(column: str | None, column_types: dict, dtype: str) -> bool:
    """Check if a column is a certain type."""
    return column and column_types[column] == dtype


def is_numeric(column: str | None, column_types: dict) -> bool:
    """Check if a column is numeric."""
    return is_type(column=column, column_types=column_types, dtype=NUMERIC)


def is_date(column: str | None, column_types: dict) -> bool:
    """Check if a column is a date."""
    return is_type(column=column, column_types=column_types, dtype=DATE)


def is_string(column: str | None, column_types: dict) -> bool:
    """Check if a column is a string."""
    return is_type(column=column, column_types=column_types, dtype=STRING)


def is_categorical(column: str | None, column_types: dict) -> bool:
    """Check if a column is categorical."""
    return is_type(column=column, column_types=column_types, dtype=CATEGORICAL)


def is_boolean(column: str | None, column_types: dict) -> bool:
    """Check if a column is a boolean."""
    return is_type(column=column, column_types=column_types, dtype=BOOLEAN)


def is_discrete(column: str | None, column_types: dict) -> bool:
    """Check if a column is discrete."""
    return column and column_types[column] in DISCRETE_TYPES


def is_continuous(column: str | None, column_types: dict) -> bool:
    """Check if a column is continuous."""
    return column and column_types[column] in CONTINUOUS_TYPES


def get_type(column: str, column_types: dict) -> str:
    """Get the type of a column."""
    return None if not column else column_types[column]
