"""Misc utilities."""
from datetime import datetime, date
import pandas as pd


def convert_to_datetime(series: pd.Series) -> pd.Series:
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



def convert_columns_to_datetime(df: pd.DataFrame) -> pd.DataFrame:
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
        df[column], converted = convert_to_datetime(df[column])
        if converted:
            converted_columns.append(column)
    return df, converted_columns


def convert_to_date(value: str | datetime | date) -> date:
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
