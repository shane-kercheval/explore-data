"""Tests for dash_utilities.py."""
import pandas as pd
import numpy as np
import pytest
from source.library.dash_utilities import (
    log,
    log_function,
    log_variable,
    log_error,
    values_to_dropdown_options,
    filter_data_from_ui_control,
    get_variable_type,
)
import helpsk.pandas as hp


def test_log(capsys):  # noqa
    """Test log function."""
    log("test")
    captured = capsys.readouterr()
    assert captured.out == "test\n"

def test_log_function(capsys):  # noqa
    """Test log_function function."""
    log_function("test")
    captured = capsys.readouterr()
    assert captured.out == "\nFUNCTION: `test`\n"

def test_log_variable(capsys):  # noqa
    """Test log_variable function."""
    log_variable("var", "value")
    captured = capsys.readouterr()
    assert captured.out == "VARIABLE: `var` = `value`\n"

def test_log_error(capsys):  # noqa
    """Test log_error function."""
    log_error("test")
    captured = capsys.readouterr()
    assert captured.out == ">>>>>>>>>ERROR: `test`\n"

def test_values_to_dropdown_options():  # noqa
    """Test values_to_dropdown_options function."""
    assert values_to_dropdown_options([]) == []
    assert values_to_dropdown_options(["a", "b"]) == [
        {"label": "a", "value": "a"},
        {"label": "b", "value": "b"},
    ]

def test_filter_data_from_ui_control__no_selected_columns(capsys, mock_data2):  # noqa
    filtered_data, _, _ = filter_data_from_ui_control(
        filters={},
        data=mock_data2,
    )
    assert filtered_data is not mock_data2
    assert filtered_data.equals(mock_data2)

    filtered_data, _, _ = filter_data_from_ui_control(
        filters=None,
        data=mock_data2,
    )
    assert filtered_data is not mock_data2
    assert filtered_data.equals(mock_data2)

def test_filter_data_from_ui_control__integers_booleans(capsys, mock_data2):  # noqa
    filters = {
        'integers': [1, 3],
        'booleans_with_missing2': ['True', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        data=mock_data2,
    )
    assert filtered_data.shape == (2, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'integers' in markdown_text
    assert 'booleans_with_missing2' in markdown_text
    assert 'integers' in code
    assert 'booleans_with_missing2' in code
    assert filtered_data['integers'].tolist() == [1, 3]
    assert filtered_data['booleans_with_missing'].tolist() == [True, np.nan]
    assert filtered_data['booleans_with_missing2'].tolist() == [None, np.nan]

def test_filter_data_from_ui_control__integers_with_missing_booleans(capsys, mock_data2):  # noqa
    filters = {
        'integers_with_missing': [1, 3],
        'booleans_with_missing2': ['True', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        data=mock_data2,
    )
    assert filtered_data.shape == (1, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'integers_with_missing' in markdown_text
    assert 'booleans_with_missing2' in markdown_text
    assert 'integers_with_missing' in code
    assert 'booleans_with_missing2' in code
    assert filtered_data['integers_with_missing'].tolist() == [1]
    assert filtered_data['booleans_with_missing'].tolist() == [True]
    assert filtered_data['booleans_with_missing2'].tolist() == [None]

def test_filter_data_from_ui_control__strings_with_missing(capsys, mock_data2):  # noqa
    filters = {
        'floats': [1, 3.5],
        'strings_with_missing2': ['b', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        data=mock_data2,
    )
    assert filtered_data.shape == (3, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'floats' in markdown_text
    assert 'strings_with_missing2' in markdown_text
    assert 'floats' in code
    assert 'strings_with_missing2' in code
    assert filtered_data['floats'].tolist() == [1.1, 2.2, 3.3]
    assert filtered_data['strings_with_missing2'].tolist() == [None, 'b', np.nan]
    assert filtered_data['strings'].tolist() == ['a', 'b', 'c']

def test_filter_data_from_ui_control__categorical_with_missing(capsys, mock_data2):  # noqa
    filters = {
        'floats': [1, 3.5],
        'categories_with_missing2': ['b', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        data=mock_data2,
    )
    assert filtered_data.shape == (3, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'floats' in markdown_text
    assert 'categories_with_missing2' in markdown_text
    assert 'floats' in code
    assert 'categories_with_missing2' in code
    assert filtered_data['floats'].tolist() == [1.1, 2.2, 3.3]
    # with categories None gets converted to np.nan
    assert filtered_data['categories_with_missing2'].tolist() == [np.nan, 'b', np.nan]
    assert filtered_data['strings'].tolist() == ['a', 'b', 'c']

def test_filter_data_from_ui_control__dates_with_missing(capsys, mock_data2):  # noqa
    filters = {
        'dates_with_missing2': ['2023-01-01', '2023-01-04'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        data=mock_data2,
    )
    assert filtered_data.shape == (2, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'dates_with_missing2' in markdown_text
    assert 'dates_with_missing2' in code
    assert filtered_data['dates_with_missing2'].tolist() == pd.to_datetime(['2023-01-02', '2023-01-04']).tolist()  # noqa
    assert filtered_data['floats'].tolist() == [2.2, 4.4]
    assert filtered_data['strings'].tolist() == ['b', 'a']

def test_filter_data_from_ui_control__datetimes_with_missing(capsys, mock_data2):  # noqa
    filters = {
        'datetimes_with_missing2': ['2023-01-01', '2023-01-04'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        data=mock_data2,
    )
    assert filtered_data.shape == (2, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'datetimes_with_missing2' in markdown_text
    assert 'datetimes_with_missing2' in code
    assert filtered_data['datetimes_with_missing2'].tolist() == pd.to_datetime(['2023-01-02 02:02:02', '2023-01-04 04:04:04']).tolist()  # noqa
    assert filtered_data['floats'].tolist() == [2.2, 4.4]
    assert filtered_data['strings'].tolist() == ['b', 'a']

def test_xxx(mock_data2):  # noqa
    all_columns = mock_data2.columns.tolist()
    numeric_columns = hp.get_numeric_columns(mock_data2)
    date_columns = hp.get_date_columns(mock_data2)
    categorical_columns = hp.get_categorical_columns(mock_data2)
    string_columns = hp.get_string_columns(mock_data2)
    boolean_columns = [x for x in all_columns if hp.is_series_bool(mock_data2[x])]

    options = {
        'numeric': numeric_columns,
        'date': date_columns,
        'categorical': categorical_columns,
        'string': string_columns,
        'boolean': boolean_columns,
    }

    assert get_variable_type(None, options=options) is None
    with pytest.raises(ValueError):  # noqa: PT011
        get_variable_type('xxx', options=options)

    assert get_variable_type('integers', options=options) == 'numeric'
    assert get_variable_type('integers_with_missing', options=options) == 'numeric'
    assert get_variable_type('integers_with_missing2', options=options) == 'numeric'
    assert get_variable_type('floats', options=options) == 'numeric'
    assert get_variable_type('floats_with_missing', options=options) == 'numeric'
    assert get_variable_type('floats_with_missing2', options=options) == 'numeric'
    assert get_variable_type('booleans', options=options) == 'boolean'
    assert get_variable_type('booleans_with_missing', options=options) == 'boolean'
    assert get_variable_type('booleans_with_missing2', options=options) == 'boolean'
    assert get_variable_type('strings', options=options) == 'string'
    assert get_variable_type('strings_with_missing', options=options) == 'string'
    assert get_variable_type('strings_with_missing2', options=options) == 'string'
    assert get_variable_type('categories', options=options) == 'categorical'
    assert get_variable_type('categories_with_missing', options=options) == 'categorical'
    assert get_variable_type('categories_with_missing2', options=options) == 'categorical'
    assert get_variable_type('dates', options=options) == 'date'
    assert get_variable_type('dates_with_missing', options=options) == 'date'
    assert get_variable_type('dates_with_missing2', options=options) == 'date'
    assert get_variable_type('datetimes', options=options) == 'date'
    assert get_variable_type('datetimes_with_missing', options=options) == 'date'
    assert get_variable_type('datetimes_with_missing2', options=options) == 'date'
