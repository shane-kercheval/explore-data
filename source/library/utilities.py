"""Misc utilities."""
from datetime import datetime, date
import pandas as pd


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
        try:
            if not pd.api.types.is_numeric_dtype(df[column]):
                df[column] = pd.to_datetime(df[column])
                converted_columns.append(column)
        except Exception:
            pass
    return df, converted_columns


def convert_to_date(value: str | datetime | date) -> date:
    """Convert a string or datetime to a date."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d")
        return parsed_date.date()
    except ValueError:
        pass

    try:
        parsed_datetime = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return parsed_datetime.date()
    except ValueError:
        pass

    raise ValueError("Invalid input format. Expected 'yyyy-mm-dd' or 'yyyy-mm-dd hh:mm:ss'.")
