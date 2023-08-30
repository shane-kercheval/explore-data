"""Tests for dash_utilities.py."""
import pytest
import pandas as pd
import numpy as np
from source.library.dash_utilities import (
    log,
    log_function,
    log_variable,
    log_error,
    values_to_dropdown_options,
    filter_data_from_ui_control,
)


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
    selected_columns = []
    cache = {
        'integers': [1, 3],
        'booleans_with_missing2': ['True', '<Missing>'],
    }
    filtered_data, _, _ = filter_data_from_ui_control(
        selected_columns=selected_columns,
        cache=cache,
        data=mock_data2,
    )
    assert filtered_data is not mock_data2
    assert filtered_data.equals(mock_data2)


def test_filter_data_from_ui_control_selected_column_in_cache(capsys, mock_data2):  # noqa
    with pytest.raises(AssertionError):
        filter_data_from_ui_control(
            selected_columns=['booleans', 'not_column'],
            cache={'booleans': ['True']},
            data=mock_data2,
        )


def test_filter_data_from_ui_control__integers_booleans(capsys, mock_data2):  # noqa
    selected_columns = ['integers', 'booleans_with_missing2']
    cache = {
        'integers': [1, 3],
        'booleans_with_missing2': ['True', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        selected_columns=selected_columns,
        cache=cache,
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


def test_filter_data_from_ui_control__strings_with_missing(capsys, mock_data2):  # noqa
    selected_columns = ['floats', 'strings_with_missing2']
    cache = {
        'floats': [1, 3.5],
        'strings_with_missing2': ['b', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        selected_columns=selected_columns,
        cache=cache,
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
    selected_columns = ['floats', 'categories_with_missing2']
    cache = {
        'floats': [1, 3.5],
        'categories_with_missing2': ['b', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        selected_columns=selected_columns,
        cache=cache,
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
    selected_columns = ['dates_with_missing2']
    cache = {
        'dates_with_missing2': ['2023-01-01', '2023-01-04'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        selected_columns=selected_columns,
        cache=cache,
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
    selected_columns = ['datetimes_with_missing2']
    cache = {
        'datetimes_with_missing2': ['2023-01-01', '2023-01-04'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        selected_columns=selected_columns,
        cache=cache,
        data=mock_data2,
    )
    assert filtered_data.shape == (2, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'datetimes_with_missing2' in markdown_text
    assert 'datetimes_with_missing2' in code
    assert filtered_data['datetimes_with_missing2'].tolist() == pd.to_datetime(['2023-01-02 02:02:02', '2023-01-04 04:04:04']).tolist()  # noqa
    assert filtered_data['floats'].tolist() == [2.2, 4.4]
    assert filtered_data['strings'].tolist() == ['b', 'a']
