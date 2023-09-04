"""Tests for dash_utilities.py."""
import pandas as pd
import numpy as np
import pytest
from tests.conftest import generate_combinations
from source.library.dash_utilities import (
    convert_to_graph_data,
    filter_data_from_ui_control,
    generate_graph,
    get_columns_from_config,
    get_graph_config,
    get_variable_type,
    log,
    log_function,
    log_variable,
    log_error,
    values_to_dropdown_options,
)
import helpsk.pandas as hp
import plotly.graph_objs as go


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

def test_get_variable_type(mock_data2):  # noqa
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

def test_get_graph_config__not_found_raises_value_error(graphing_configurations):  # noqa
    with pytest.raises(ValueError):  # noqa: PT011
        get_graph_config(
            configurations=graphing_configurations,
            x_variable='doesnotexist',
            y_variable=None,
        )

def test_get_graph_config__numeric(graphing_configurations):  # noqa
    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable='numeric',
        y_variable=None,
    )
    assert isinstance(config, dict)
    assert 'numeric' in config['selected_variables']['x_variable']
    assert config['selected_variables']['y_variable'] is None

    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'box'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]

    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable=None,
        y_variable='numeric',
    )
    assert isinstance(config, dict)
    assert 'numeric' in config['selected_variables']['y_variable']
    assert config['selected_variables']['x_variable'] is None

    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'box'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]

def test_get_graph_config__numeric_numeric(graphing_configurations):  # noqa
    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable='numeric',
        y_variable='numeric',
    )
    assert isinstance(config, dict)
    assert 'numeric' in config['selected_variables']['x_variable']
    assert 'numeric' in config['selected_variables']['y_variable']

    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'scatter'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]

@pytest.mark.parametrize('x_variable', ['date', 'boolean', 'string', 'categorical'])
def test_get_graph_config__nonnumeric(x_variable, graphing_configurations):  # noqa
    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable=x_variable,
        y_variable=None,
    )
    # test variables
    assert isinstance(config, dict)
    assert x_variable in config['selected_variables']['x_variable']
    assert config['selected_variables']['y_variable'] is None
    # test graph types
    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'histogram'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]

    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable=None,
        y_variable=x_variable,
    )
    # test variables
    assert isinstance(config, dict)
    assert x_variable in config['selected_variables']['y_variable']
    assert config['selected_variables']['x_variable'] is None
    # test graph types
    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'histogram'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]

@pytest.mark.parametrize('x_variable', ['date', 'boolean', 'string', 'categorical'])
def test_get_graph_config__nonnumeric_numeric(x_variable, graphing_configurations):  # noqa
    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable=x_variable,
        y_variable='numeric',
    )
    # test variables
    assert isinstance(config, dict)
    assert x_variable in config['selected_variables']['x_variable']
    assert 'numeric' in config['selected_variables']['y_variable']
    # test graph types
    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'histogram'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]


@pytest.mark.parametrize('x_variable', ['date', 'boolean', 'string', 'categorical'])
@pytest.mark.parametrize('y_variable', ['date', 'boolean', 'string', 'categorical'])
def test_get_graph_config__nonnumeric_nonnumeric(x_variable, y_variable, graphing_configurations):  # noqa
    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable=x_variable,
        y_variable=y_variable,
    )
    # test variables
    assert isinstance(config, dict)
    assert x_variable in config['selected_variables']['x_variable']
    assert y_variable in config['selected_variables']['y_variable']
    # test graph types
    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'heatmap'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]


def test_get_graph_config__z_variable(graphing_configurations):  # noqa
    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable='numeric',
        y_variable='numeric',
        z_variable='numeric',
    )
    # test variables
    assert isinstance(config, dict)
    assert 'numeric' in config['selected_variables']['x_variable']
    assert 'numeric' in config['selected_variables']['y_variable']
    assert 'numeric' in config['selected_variables']['z_variable']
    # test graph types
    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'scatter-3d'
    assert 'description' in config['graph_types'][0]
    assert 'optional_variables' in config['graph_types'][0]


def test_get_columns_from_config():  # noqa
    all_columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    columns_by_type = {
        'numeric': ['a', 'b'],
        'date': ['c', 'd'],
        'categorical': ['e', 'f'],
        'string': ['g', 'h'],
        'boolean': ['i', 'j'],
    }
    results = get_columns_from_config(
        allowed_types=['numeric', 'date', 'categorical', 'string', 'boolean'],
        columns_by_type=columns_by_type,
        all_columns=all_columns,
    )
    assert results == all_columns

    results = get_columns_from_config(
        allowed_types=['date'],
        columns_by_type=columns_by_type,
        all_columns=all_columns,
    )
    assert results == ['c', 'd']

    results = get_columns_from_config(
        allowed_types=['date', 'boolean'],
        columns_by_type=columns_by_type,
        all_columns=all_columns,
    )
    assert results == ['c', 'd', 'i', 'j']

    results = get_columns_from_config(
        allowed_types=reversed(['numeric', 'date', 'categorical', 'string', 'boolean']),
        columns_by_type=columns_by_type,
        all_columns=all_columns,
    )
    assert results == all_columns

    results = get_columns_from_config(
        allowed_types=reversed(['date', 'boolean']),
        columns_by_type=columns_by_type,
        all_columns=all_columns,
    )
    assert results == ['c', 'd', 'i', 'j']

def test_convert_to_graph_data(capsys, mock_data2):  # noqa
    data_copy = mock_data2.copy()
    numeric_columns = [
        'integers', 'integers_with_missing', 'integers_with_missing2',
        'floats', 'floats_with_missing', 'floats_with_missing2',
    ]
    string_columns = ['strings', 'strings_with_missing', 'strings_with_missing2']
    categorical_columns = ['categories', 'categories_with_missing', 'categories_with_missing2']
    boolean_columns = ['booleans', 'booleans_with_missing', 'booleans_with_missing2']
    selected_variables = ['integers', 'strings', 'categories', 'booleans']
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        numeric_columns=numeric_columns,
        string_columns=string_columns,
        categorical_columns=categorical_columns,
        boolean_columns=boolean_columns,
        selected_variables=selected_variables,
        top_n_categories=10,
    )
    assert new_data.columns.tolist() == selected_variables
    assert mock_data2 is not new_data
    assert code is not None
    assert markdown is not None
    assert '`5` rows remaining' in markdown
    assert '`0` (`0.0%`) rows removed' in markdown
    assert new_data['integers'].tolist() == [1, 2, 3, 4, 5]
    assert new_data['strings'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['categories'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['booleans'].tolist() == [True, False, True, False, True]

    # top_n_categories with 3 shouldn't change anything
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        numeric_columns=numeric_columns,
        string_columns=string_columns,
        categorical_columns=categorical_columns,
        boolean_columns=boolean_columns,
        selected_variables=selected_variables,
        top_n_categories=3,
    )
    assert new_data.columns.tolist() == selected_variables
    assert mock_data2 is not new_data
    assert code is not None
    assert markdown is not None
    assert '`5` rows remaining' in markdown
    assert '`0` (`0.0%`) rows removed' in markdown
    assert new_data['integers'].tolist() == [1, 2, 3, 4, 5]
    assert new_data['strings'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['categories'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['booleans'].tolist() == [True, False, True, False, True]

    # top_n_categories with 3 shouldn't change anything
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        numeric_columns=numeric_columns,
        string_columns=string_columns,
        categorical_columns=categorical_columns,
        boolean_columns=boolean_columns,
        selected_variables=selected_variables,
        top_n_categories=None,
    )
    assert new_data.columns.tolist() == selected_variables
    assert mock_data2 is not new_data
    assert code is not None
    assert markdown is not None
    assert '`5` rows remaining' in markdown
    assert '`0` (`0.0%`) rows removed' in markdown
    assert new_data['integers'].tolist() == [1, 2, 3, 4, 5]
    assert new_data['strings'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['categories'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['booleans'].tolist() == [True, False, True, False, True]


    # top_n_categories with 3 shouldn't change anything
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        numeric_columns=numeric_columns,
        string_columns=string_columns,
        categorical_columns=categorical_columns,
        boolean_columns=boolean_columns,
        selected_variables=selected_variables,
        top_n_categories=2,
    )
    assert new_data.columns.tolist() == selected_variables
    assert mock_data2 is not new_data
    assert code is not None
    assert markdown is not None
    assert '`5` rows remaining' in markdown
    assert '`0` (`0.0%`) rows removed' in markdown
    assert new_data['integers'].tolist() == [1, 2, 3, 4, 5]
    assert new_data['strings'].tolist() == ['a', 'b', '<Other>', 'a', 'b']
    assert new_data['categories'].tolist() == ['a', 'b', '<Other>', 'a', 'b']
    assert new_data['booleans'].tolist() == [True, False, True, False, True]

    selected_variables = [
        'integers_with_missing', 'strings', 'categories_with_missing2', 'booleans_with_missing',
    ]
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        numeric_columns=numeric_columns,
        string_columns=string_columns,
        categorical_columns=categorical_columns,
        boolean_columns=boolean_columns,
        selected_variables=selected_variables,
        top_n_categories=2,
    )
    assert new_data.columns.tolist() == selected_variables
    assert mock_data2 is not new_data
    assert code is not None
    assert markdown is not None
    assert '`4` rows remaining' in markdown
    assert '`1` (`20.0%`) rows removed' in markdown
    assert new_data['integers_with_missing'].tolist() == [1, 2, 4, 5]
    assert new_data['strings'].tolist() == ['a', 'b', 'a', 'b']
    assert new_data['categories_with_missing2'].tolist() == ['<Other>', 'b', 'a', 'b']
    assert new_data['booleans_with_missing'].tolist() == [True, False, False, True]

    selected_variables = [
        'integers_with_missing', 'strings_with_missing2', 'categories', 'booleans_with_missing2',
    ]
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        numeric_columns=numeric_columns,
        string_columns=string_columns,
        categorical_columns=categorical_columns,
        boolean_columns=boolean_columns,
        selected_variables=selected_variables,
        top_n_categories=2,
    )
    assert new_data.columns.tolist() == selected_variables
    assert mock_data2 is not new_data
    assert code is not None
    assert markdown is not None
    assert '`4` rows remaining' in markdown
    assert '`1` (`20.0%`) rows removed' in markdown
    assert new_data['integers_with_missing'].tolist() == [1, 2, 4, 5]
    assert new_data['strings_with_missing2'].tolist() == ['<Missing>', 'b', '<Other>', 'b']
    assert new_data['categories'].tolist() == ['a', 'b', 'a', 'b']
    assert new_data['booleans_with_missing2'].tolist() == ['<Missing>', False, False, '<Other>']

    selected_variables = [
        'integers_with_missing', 'strings_with_missing2', 'categories', 'booleans_with_missing2',
    ]
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        numeric_columns=numeric_columns,
        string_columns=string_columns,
        categorical_columns=categorical_columns,
        boolean_columns=boolean_columns,
        selected_variables=selected_variables,
        top_n_categories=1,
    )
    assert new_data.columns.tolist() == selected_variables
    assert mock_data2 is not new_data
    assert code is not None
    assert markdown is not None
    assert '`4` rows remaining' in markdown
    assert '`1` (`20.0%`) rows removed' in markdown
    assert new_data['integers_with_missing'].tolist() == [1, 2, 4, 5]
    assert new_data['strings_with_missing2'].tolist() == ['<Other>', 'b', '<Other>', 'b']
    assert new_data['categories'].tolist() == ['a', '<Other>', 'a', '<Other>']
    assert new_data['booleans_with_missing2'].tolist() == ['<Other>', False, False, '<Other>']


def test_get_combinations():  # noqa
    assert generate_combinations([[None], ['a', 'b'], [None]]) == [(None, 'a', None), (None, 'b', None)]  # noqa
    assert generate_combinations([[None], ['a', 'b']]) == [(None, 'a'), (None, 'b')]
    assert generate_combinations([[1], ['a', 'b']]) == [(1, 'a'), (1, 'b')]
    assert generate_combinations([[1, 2], ['a', 'b']]) == [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
    assert generate_combinations([[1, 2], ['a', 'b'], [True, False]]) == [
        (1, 'a', True), (1, 'a', False), (1, 'b', True), (1, 'b', False),
        (2, 'a', True), (2, 'a', False), (2, 'b', True), (2, 'b', False),
    ]


def test_generate_graph__scatter(  # noqa
        capsys,  # noqa
        mock_data2: list[str],
        graphing_configurations: dict,
        mock_data2_numeric_columns: list[str],
        mock_data2_string_columns: list[str],
        mock_data2_categorical_columns: list[str],
        mock_data2_boolean_columns: list[str],
        mock_data2_date_columns: list[str],
        ):
    # this function tests all combinations found in graphing_configurations.yml
    # it tests all selected-variable, grpah-type, and optional-variable combinations
    fig, code = generate_graph(
        data=mock_data2,
        graph_type='scatter',
        x_variable='integers',
        y_variable='floats',
        z_variable=None,
        color_variable=None,
        size_variable=None,
        facet_variable=None,
        num_facet_columns=None,
        category_orders=None,
        bar_mode=None,
        opacity=None,
        n_bins=None,
        log_x_axis=None,
        log_y_axis=None,
        title=None,
        graph_labels=None,
        numeric_columns=mock_data2_numeric_columns,
        string_columns=mock_data2_string_columns,
        categorical_columns=mock_data2_categorical_columns,
        boolean_columns=mock_data2_boolean_columns,
        date_columns=mock_data2_date_columns,
    )
    assert isinstance(fig, go.Figure)
    assert code is not None
    assert 'px.scatter' in code

    type_to_column_lookup = {
        'numeric': 'integers',
        'date': 'dates',
        'string': 'strings',
        'categorical': 'categories',
        'boolean': 'booleans',
    }

    for config in graphing_configurations:
        # config = graphing_configurations[6]
        selected_variables = config['selected_variables']
        x_variable = selected_variables['x_variable'] if 'x_variable' in selected_variables else None  # noqa
        y_variable = selected_variables['y_variable'] if 'y_variable' in selected_variables else None  # noqa
        z_variable = selected_variables['z_variable'] if 'z_variable' in selected_variables else None  # noqa
        variable_combinations = generate_combinations([
            x_variable or [None],
            y_variable or [None],
            z_variable or [None],
        ])
        graph_types = config['graph_types']
        for graph_type in graph_types:
            # graph_type = graph_types[0]
            for x_var, y_var, z_var in variable_combinations:
                # x_var, y_var, z_var = variable_combinations[0]
                # test with no parameters
                fig, code = generate_graph(
                    data=mock_data2,
                    graph_type=graph_type['name'],
                    x_variable=type_to_column_lookup[x_var] if x_var else None,
                    y_variable=type_to_column_lookup[y_var] if y_var else None,
                    z_variable=type_to_column_lookup[z_var] if z_var else None,
                    color_variable=None,
                    size_variable=None,
                    facet_variable=None,
                    num_facet_columns=4,
                    category_orders={'var': ['a', 'b', 'c']},
                    bar_mode='relative',
                    opacity=0.6,
                    n_bins=30,
                    log_x_axis=None,
                    log_y_axis=None,
                    title=None,
                    graph_labels=None,
                    numeric_columns=mock_data2_numeric_columns,
                    string_columns=mock_data2_string_columns,
                    categorical_columns=mock_data2_categorical_columns,
                    boolean_columns=mock_data2_boolean_columns,
                    date_columns=mock_data2_date_columns,
                )
                assert isinstance(fig, go.Figure)
                assert code is not None
                if graph_type['name'] == 'scatter-3d':
                    assert 'px.scatter_3d' in code
                else:
                    assert graph_type['name'] in code

                # test with optional parameters
                optional_variables = graph_type['optional_variables']
                color_variable = optional_variables['color_variable']['types'] if 'color_variable' in optional_variables else None  # noqa
                size_variable = optional_variables['size_variable']['types'] if 'size_variable' in optional_variables else None  # noqa
                facet_variable = optional_variables['facet_variable']['types'] if 'facet_variable' in optional_variables else None  # noqa

                optional_combinations = generate_combinations([
                    color_variable or [None],
                    size_variable or [None],
                    facet_variable or [None],
                ])
                for color_var, size_var, facet_var in optional_combinations:
                    fig, code = generate_graph(
                        data=mock_data2,
                        graph_type=graph_type['name'],
                        x_variable=type_to_column_lookup[x_var] if x_var else None,
                        y_variable=type_to_column_lookup[y_var] if y_var else None,
                        z_variable=type_to_column_lookup[z_var] if z_var else None,
                        color_variable=type_to_column_lookup[color_var] if color_var else None,
                        size_variable=type_to_column_lookup[size_var] if size_var else None,
                        facet_variable=type_to_column_lookup[facet_var] if facet_var else None,
                        num_facet_columns=None,
                        category_orders=None,
                        bar_mode=None,
                        opacity=None,
                        n_bins=None,
                        log_x_axis=True,
                        log_y_axis=False,
                        title="Title",
                        graph_labels={"x": "X", "y": "Y", "color": "Color", "size": "Size"},
                        numeric_columns=mock_data2_numeric_columns,
                        string_columns=mock_data2_string_columns,
                        categorical_columns=mock_data2_categorical_columns,
                        boolean_columns=mock_data2_boolean_columns,
                        date_columns=mock_data2_date_columns,
                    )
                    assert isinstance(fig, go.Figure)
                    assert code is not None
                    if graph_type['name'] == 'scatter-3d':
                        assert 'px.scatter_3d' in code
                    else:
                        assert graph_type['name'] in code
