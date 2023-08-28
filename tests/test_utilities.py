"""Test utilities.py."""
import pytest
import pandas as pd
from datetime import date, datetime
from source.library.utilities import dataframe_columns_to_datetime, filter_dataframe, to_date


def test_convert_columns_to_datetime(mock_data1):  # noqa
    data_copy = mock_data1.copy()
    data_converted, converted_columns = dataframe_columns_to_datetime(data_copy)

    assert isinstance(data_converted, pd.DataFrame)
    assert isinstance(converted_columns, list)
    assert data_converted is data_copy
    assert data_converted is not mock_data1
    assert data_converted.shape == mock_data1.shape

    # Check that the correct columns were marked as converted
    expected_converted = {
        'date_string', 'date_string_with_missing', 'datetime_string',
        'datetime_string_with_missing', 'datetimes', 'datetimes_with_missing',
        'dates', 'dates_with_missing',
    }
    assert set(converted_columns) == expected_converted

    # Check if date columns were converted correctly
    assert pd.api.types.is_datetime64_any_dtype(data_converted['date_string'])
    assert pd.api.types.is_datetime64_any_dtype(data_converted['date_string_with_missing'])
    assert pd.api.types.is_datetime64_any_dtype(data_converted['datetime_string'])
    assert pd.api.types.is_datetime64_any_dtype(data_converted['datetime_string_with_missing'])
    assert pd.api.types.is_datetime64_any_dtype(data_converted['datetimes'])
    assert pd.api.types.is_datetime64_any_dtype(data_converted['datetimes_with_missing'])
    assert pd.api.types.is_datetime64_any_dtype(data_converted['dates'])
    assert pd.api.types.is_datetime64_any_dtype(data_converted['dates_with_missing'])

    # Check that data meant to be converted has expected values
    assert data_converted['date_string'].equals(pd.to_datetime(mock_data1['date_string']))
    assert data_converted['date_string_with_missing'].equals(pd.to_datetime(mock_data1['date_string_with_missing']))  # noqa
    assert data_converted['datetime_string'].equals(pd.to_datetime(mock_data1['datetime_string']))
    assert data_converted['datetime_string_with_missing'].equals(pd.to_datetime(mock_data1['datetime_string_with_missing']))  # noqa
    assert data_converted['datetimes'].equals(mock_data1['datetimes'])  # already datetime64
    assert data_converted['datetimes_with_missing'].equals(pd.to_datetime(mock_data1['datetimes_with_missing']))  # noqa
    assert data_converted['dates'].equals(pd.to_datetime(mock_data1['dates']))
    assert data_converted['dates_with_missing'].equals(pd.to_datetime(mock_data1['dates_with_missing']))  # noqa

    # Check that non-date columns remain unchanged
    assert pd.api.types.is_object_dtype(data_converted['random_strings'])
    assert pd.api.types.is_integer_dtype(data_converted['integers'])
    assert pd.api.types.is_float_dtype(data_converted['integers_with_missing'])
    assert pd.api.types.is_float_dtype(data_converted['floats'])
    assert pd.api.types.is_float_dtype(data_converted['floats_with_missing'])
    assert pd.api.types.is_bool_dtype(data_converted['booleans'])
    # ideally this would be is_bool_dtype but if anything it's a bug in pandas
    assert pd.api.types.is_object_dtype(data_converted['booleans_with_missing'])

    # Check that data not meant to be converted remains unchanged
    assert data_converted['random_strings'].equals(mock_data1['random_strings'])
    assert data_converted['integers'].equals(mock_data1['integers'])
    assert data_converted['integers_with_missing'].equals(mock_data1['integers_with_missing'])
    assert data_converted['floats'].equals(mock_data1['floats'])
    assert data_converted['floats_with_missing'].equals(mock_data1['floats_with_missing'])
    assert data_converted['booleans'].equals(mock_data1['booleans'])
    assert data_converted['booleans_with_missing'].equals(mock_data1['booleans_with_missing'])

# Test cases
to_date_test_data = [
    ("2023-08-22", date(2023, 8, 22)),
    ("2023-08-22 15:30:45", date(2023, 8, 22)),
    (date(2023, 8, 22), date(2023, 8, 22)),
    (datetime(2023, 8, 22, 15, 30, 45), date(2023, 8, 22)),
]

to_date_invalid_data = [
    "invalid-date-format",
    "2023-13-01",
    "2023-08-22 25:00:00",
]

@pytest.mark.parametrize("value, expected", to_date_test_data)  # noqa
def test_convert_to_date_valid(value, expected):  # noqa
    assert to_date(value) == expected

@pytest.mark.parametrize("value", to_date_invalid_data)
def test_convert_to_date_invalid(value):  # noqa
    with pytest.raises(ValueError):  # noqa
        to_date(value)

# Test cases
to_date_string_test_data = [
    ("2023-08-22", "2023-08-22"),
    ("2023-08-22 15:30:45", "2023-08-22"),
    (date(2023, 8, 22), "2023-08-22"),
    (datetime(2023, 8, 22, 15, 30, 45), "2023-08-22"),
]
@pytest.mark.parametrize("value, expected", to_date_test_data)  # noqa
def test_convert_to_date_string(value, expected):  # noqa
    assert to_date(value) == expected

def test_convert_to_date_none():  # noqa
    assert pd.isna(to_date(None))

def test_convert_to_date_empty_string():  # noqa
    assert pd.isna(to_date(None))

def test_convert_to_date_datetime_with_microseconds():  # noqa
    input_datetime = datetime(2023, 8, 22, 15, 30, 45, 123456)
    expected_date = date(2023, 8, 22)
    assert to_date(input_datetime) == expected_date

def test_filter_dataframe_dates_no_missing(mock_data2):  # noqa
    """Test filter_dataframe function."""
    # testing dates
    filters = {
        'dates': (pd.to_datetime('2023-01-02'), pd.to_datetime('2023-01-04')),
    }
    filtered_df, code = filter_dataframe(mock_data2, filters)
    assert mock_data2 is not filtered_df
    assert mock_data2.shape[1] == filtered_df.shape[1]
    assert len(filtered_df) == 3
    assert code
    assert filtered_df['integers'].tolist() == [2, 3, 4]
    assert filtered_df['dates'].tolist() == mock_data2['dates'].tolist()[1:4]

    # testing datetimes
    filters = {
        'dates': (pd.to_datetime('2023-01-02 12:00:00'), pd.to_datetime('2023-01-04 12:00:00')),
    }
    filtered_df, code = filter_dataframe(mock_data2, filters)
    assert mock_data2 is not filtered_df
    assert mock_data2.shape[1] == filtered_df.shape[1]
    assert len(filtered_df) == 3
    assert code
    assert filtered_df['integers'].tolist() == [2, 3, 4]
    assert filtered_df['dates'].tolist() == mock_data2['dates'].tolist()[1:4]

    # testing date strings
    filters = {
        'dates': ('2023-01-02', '2023-01-04'),
    }
    filtered_df, code = filter_dataframe(mock_data2, filters)
    assert mock_data2 is not filtered_df
    assert mock_data2.shape[1] == filtered_df.shape[1]
    assert len(filtered_df) == 3
    assert code
    assert filtered_df['integers'].tolist() == [2, 3, 4]
    assert filtered_df['dates'].tolist() == mock_data2['dates'].tolist()[1:4]

    # testing datetime strings
    filters = {
        'dates': ('2023-01-02 12:00:00', '2023-01-04 12:00:00'),
    }
    filtered_df, code = filter_dataframe(mock_data2, filters)
    assert mock_data2 is not filtered_df
    assert mock_data2.shape[1] == filtered_df.shape[1]
    assert len(filtered_df) == 3
    assert code
    assert filtered_df['integers'].tolist() == [2, 3, 4]
    assert filtered_df['dates'].tolist() == mock_data2['dates'].tolist()[1:4]
