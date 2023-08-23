"""Misc utilities."""
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
