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
        _ = pd.to_datetime(series)
        return True
    except Exception:
        return False


def get_column_types(data: pd.DataFrame) -> dict:
    """
    Create a dictionary with column names as keys and values of either 'numeric', 'date', 'string',
    'categorical', 'boolean'.
    """
    # i can't convert columns to datetime here because the dataframe gets converted to a dict
    # and loses the converted datetime dtypes
    # but i need to still get the columns that should be treated as dates
    date_columns = [x for x in data.columns.tolist() if is_series_datetime(data[x])]
    all_columns = data.columns.tolist()
    numeric_columns = hp.get_numeric_columns(data)
    categorical_columns = hp.get_categorical_columns(data)
    string_columns = [x for x in hp.get_string_columns(data) if x not in date_columns]
    boolean_columns = [x for x in all_columns if hp.is_series_bool(data[x])]
    # ensure all columns lists are mutually exclusive
    sets = [set(lst) for lst in [numeric_columns, date_columns, categorical_columns, string_columns, boolean_columns]]  # noqa
    assert sum(len(s) for s in sets) == len(set.union(*sets))

    def _get_type(var: str) -> str:
        if var in numeric_columns:
            return 'numeric'
        if var in date_columns:
            return 'date'
        if var in string_columns:
            return 'string'
        if var in categorical_columns:
            return 'categorical'
        if var in boolean_columns:
            return 'boolean'
        raise ValueError(f"Unknown type for {var}")

    # for each column create a dictionary with column name as key and
    # values of either 'numeric', 'date', 'string', 'categorical', 'boolean'
    # this is used to determine which controls to show for each column
    return {x:_get_type(x) for x in all_columns}


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
