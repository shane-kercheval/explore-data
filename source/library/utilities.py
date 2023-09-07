"""Misc utilities."""
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
import helpsk.pandas as hp

def is_series_datetime(series: pd.Series) -> bool:
    """Check if a series can be converted to a datetime."""
    if pd.api.types.is_numeric_dtype(series):
        return False
    try:
        _ = pd.to_datetime(series)
        return True
    except Exception:
        return False


def series_to_datetime(series: pd.Series) -> tuple[pd.Series, bool]:
    """
    Convert a series to a datetime if possible.

    Returns the converted series and a boolean indicating whether the series was converted.
    """
    try:
        if not pd.api.types.is_numeric_dtype(series):
            return pd.to_datetime(series), True
    except Exception:
        pass

    return series, False


def dataframe_columns_to_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check if each column in the DataFrame can be converted to a date/datetime. If so, convert it.

    This function modifies the DataFrame in place and returns the data frame and a list of the
    columns that were converted. Create a copy of the DataFrame if you want to preserve the
    original.

    Args:
        df: DataFrame to convert

    """
    converted_columns = []
    for column in df.columns:
        df[column], converted = series_to_datetime(df[column])
        if converted:
            converted_columns.append(column)
    return df, converted_columns


def to_date(value: str | datetime | date) -> date:
    """Convert a string or datetime to a date."""
    return pd.to_datetime(value or '').date()
    # if isinstance(value, datetime):
    #     return value.date()

    # if isinstance(value, date):
    #     return value

    # datetime_formats = [
    #     "%Y-%m-%d",
    #     "%Y-%m-%d %H:%M:%S",
    #     "%Y-%m-%dT%H:%M:%S",
    #     "%Y-%m-%dT%H:%M:%S.%f",
    # ]

    # for format in datetime_formats:
    #     try:
    #         parsed_date = datetime.strptime(value, format)
    #         return parsed_date.date()
    #     except ValueError:
    #         pass

    # raise ValueError("Invalid input format. Expected 'yyyy-mm-dd' or 'yyyy-mm-dd hh:mm:ss'.")


def to_date_string(value: str | datetime | date, str_format: str = '%Y-%m-%d') -> str:
    """Convert a string/datetime/date to a string in the format of str_format."""
    return to_date(value).strftime(str_format)


def create_random_dataframe(num_rows: int, sporadic_missing: bool = False) -> pd.DataFrame:
    """Generate random data for the columns."""
    integers = np.random.randint(1, 100, size=num_rows)  # noqa
    floats = np.random.rand(num_rows) * 100  # noqa
    dates = [datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365)) for _ in range(num_rows)]  # noqa
    date_times = [datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365), hours=np.random.randint(0, 24)) for _ in range(num_rows)]  # noqa
    date_strings = [date.strftime('%Y-%m-%d') for date in dates]
    date_home_strings = [date.strftime('%d/%m/%Y') for date in dates]
    categories = np.random.choice(['Category A', 'Category B', 'Category C'], num_rows)  # noqa
    booleans = np.random.choice([True, False], num_rows)  # noqa

    fake_df = pd.DataFrame({
        'Integers': integers,
        'Floats': floats,
        'Dates': dates,
        'DateTimes': date_times,
        'DateStrings': date_strings,
        'DateHomeStrings': date_home_strings,
        'Categories': pd.Categorical(categories, categories=['Category A', 'Category B', 'Category C']),  # noqa
        'Categories2': categories.copy(),
        'Booleans': booleans,
        'Booleans1': booleans.copy(),
        'Booleans2': booleans.copy(),
    })
    # Introduce sporadic missing values
    if sporadic_missing:
        num_missing = int(num_rows * 0.1)  # 10% missing values

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'Integers'] = np.nan

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'Floats'] = np.nan

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'Dates'] = np.nan

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'DateTimes'] = np.nan

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'DateStrings'] = np.nan

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'DateHomeStrings'] = np.nan

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'Categories'] = np.nan
        fake_df['Categories'] = pd.Categorical(fake_df['Categories'], categories=['Category A', 'Category B', 'Category C'])  # noqa
        fake_df.loc[missing_indices, 'Categories2'] = None
        fake_df['Categories2'] = pd.Categorical(fake_df['Categories2'], categories=['Category A', 'Category B', 'Category C'])  # noqa

        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'Booleans1'] = np.nan
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        fake_df.loc[missing_indices, 'Booleans2'] = None

    return fake_df


def filter_dataframe(data: pd.DataFrame, filters: dict | None) -> tuple[pd.DataFrame, str]:
    """
    Filter a dataframe based on a dictionary. Each key is a column name and the value is the
    value(s) (e.g. value or list) to filter on.

    Returns the filtered dataframe, and the code used to recreate the filters (in string format).

    For integers/floats, the value must be a tuple of (min, max) values, and the data will return
    values between these numbers. Missing values are automatically excluded.

    For dates, the value must be a tuple of (start, max) values, and the data will return values
    between these dates. Missing values are automatically excluded. NOTE: datetime values are not
    supported. Any datetime value will be converted to a date.

    For booleans, the value must be a list with `True` or `False` values, and the data will return
    values that match the boolean. `np.nan` values can be included in the list to return missing
    values.

    For strings, the value must be a list of strings, and the data will return values in the list.
    `np.nan` values can be included in the list to return missing values.

    For categories, the value must be a list of strings, and the data will return values in the
    list. `np.nan` values can be included in the list to return missing values.
    """
    if not filters:
        return data.copy(), ''

    # graph_data = data.copy()
    code = 'def filter_data(data: pd.DataFrame) -> pd.DataFrame:\n'
    code += '    graph_data = data.copy()\n'

    for column, values in filters.items():
        assert column in data.columns, f"Column `{column}` not found in `data`"
        code += f"    # Filter on `{column}`\n"
        # convert the series to a datetime if possible
        series, converted_to_datetime = series_to_datetime(data[column].copy())
        if converted_to_datetime:
            assert isinstance(values, tuple)
            code += f"    series = pd.to_datetime(graph_data['{column}']).dt.date\n"
            code += f"    start_date = pd.to_datetime('{values[0]}').date()\n"
            code += f"    end_date = pd.to_datetime('{values[1]}').date() + pd.Timedelta(days=1)\n"
            code += "    graph_data = graph_data[(series >= start_date) & (series < end_date)]\n"
        elif (
            hp.is_series_bool(series)
            or series.dtype == 'object'
            or series.dtype.name == 'category'
            ):
            assert isinstance(values, list), f"Values for column `{column}` must be a list not `{type(values)}`"  # noqa
            # np.nan values are converted to 'nan' strings, but we need 'np.nan' string for the
            # code to work
            values = str(values).replace('nan', 'np.nan')  # noqa
            code += f"    graph_data = graph_data[graph_data['{column}'].isin({values})]\n"
        elif pd.api.types.is_numeric_dtype(series):
            assert isinstance(values, tuple)
            code += f"    graph_data = graph_data[graph_data['{column}'].between({values[0]}, {values[1]})]\n"  # noqa
        else:
            raise ValueError(f"Unknown dtype for column `{column}`: {data[column].dtype}")

    code += '    return graph_data\n\n'
    code += "graph_data = filter_data(data)"

    local_vars = locals()
    exec(code, globals(), local_vars)
    return local_vars['graph_data'], code
