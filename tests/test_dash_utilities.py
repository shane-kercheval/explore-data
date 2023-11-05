"""Tests for dash_utilities.py."""
import pandas as pd
import numpy as np
import pytest
from tests.conftest import generate_combinations
import source.library.types as t
from source.library.dash_utilities import (
    InvalidConfigurationError,
    convert_to_graph_data,
    filter_data_from_ui_control,
    generate_graph,
    get_category_orders,
    get_graph_config,
    log,
    log_function,
    log_variable,
    log_error,
    values_to_dropdown_options,
)
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
    column_types = t.get_column_types(mock_data2)
    filtered_data, _, _ = filter_data_from_ui_control(
        filters={},
        column_types=column_types,
        data=mock_data2,
    )
    # assert filtered_data is not mock_data2
    assert filtered_data.equals(mock_data2)

    filtered_data, _, _ = filter_data_from_ui_control(
        filters=None,
        column_types=column_types,
        data=mock_data2,
    )
    # assert filtered_data is not mock_data2
    assert filtered_data.equals(mock_data2)

def test_filter_data_from_ui_control__integers_booleans(capsys, mock_data2):  # noqa
    column_types = t.get_column_types(mock_data2)
    filters = {
        'integers': [1, 3],
        'booleans_with_missing2': ['True', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        column_types=column_types,
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
    column_types = t.get_column_types(mock_data2)
    filters = {
        'integers_with_missing': [1, 3],
        'booleans_with_missing2': ['True', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        column_types=column_types,
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
    column_types = t.get_column_types(mock_data2)
    filters = {
        'floats': [1, 3.5],
        'strings_with_missing2': ['b', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        column_types=column_types,
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
    column_types = t.get_column_types(mock_data2)
    filters = {
        'floats': [1, 3.5],
        'categories_with_missing2': ['b', '<Missing>'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        column_types=column_types,
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
    column_types = t.get_column_types(mock_data2)
    filters = {
        'dates_with_missing2': ['2023-01-01', '2023-01-04'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        column_types=column_types,
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
    column_types = t.get_column_types(mock_data2)
    filters = {
        'datetimes_with_missing2': ['2023-01-01', '2023-01-04'],
    }
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filters,
        column_types=column_types,
        data=mock_data2,
    )
    assert filtered_data.shape == (2, 21)
    assert 'filters applied' in markdown_text.lower()
    assert 'datetimes_with_missing2' in markdown_text
    assert 'datetimes_with_missing2' in code
    assert filtered_data['datetimes_with_missing2'].tolist() == pd.to_datetime(['2023-01-02 02:02:02', '2023-01-04 04:04:04']).tolist()  # noqa
    assert filtered_data['floats'].tolist() == [2.2, 4.4]
    assert filtered_data['strings'].tolist() == ['b', 'a']

def test_get_graph_config__not_found_raises_value_error(graphing_configurations):  # noqa
    with pytest.raises(InvalidConfigurationError):
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

def test_get_graph_config__numeric_numeric_numeric(graphing_configurations):  # noqa
    config = get_graph_config(
        configurations=graphing_configurations,
        x_variable='numeric',
        y_variable='numeric',
        z_variable='numeric',
    )
    assert isinstance(config, dict)
    assert 'numeric' in config['selected_variables']['x_variable']
    assert 'numeric' in config['selected_variables']['y_variable']

    assert isinstance(config['graph_types'], list)
    assert len(config['graph_types']) > 0
    assert isinstance(config['graph_types'][0], dict)
    assert 'name' in config['graph_types'][0]
    assert config['graph_types'][0]['name'] == 'scatter-3d'
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

@pytest.mark.parametrize('x_variable', ['boolean', 'string', 'categorical'])
@pytest.mark.parametrize('y_variable', ['boolean', 'string', 'categorical'])
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

def test_convert_to_graph_data(capsys, mock_data2):  # noqa
    data_copy = mock_data2.copy()
    column_types = t.get_column_types(data_copy)
    selected_variables = ['integers', 'strings', 'categories', 'booleans']
    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=10,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
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
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=3,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
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
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=None,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
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
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
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
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
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
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
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
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=1,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
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

def test_convert_to_graph_data__missing_categories(capsys, mock_data2):  # noqa
    column_types = t.get_column_types(mock_data2)
    data_copy = mock_data2.copy()
    selected_variables = [
        'strings', 'strings_with_missing', 'strings_with_missing2',
        'categories', 'categories_with_missing', 'categories_with_missing2',
        'booleans', 'booleans_with_missing', 'booleans_with_missing2',
        'dates',
    ]

    assert mock_data2['categories'].dtype.name == 'category'
    assert mock_data2['categories_with_missing'].dtype.name == 'category'
    assert mock_data2['categories_with_missing2'].dtype.name == 'category'

    new_data, markdown, code = convert_to_graph_data(
        data=data_copy,
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=10,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
    )

    assert new_data.columns.tolist() == selected_variables

    assert new_data['strings'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['strings_with_missing'].tolist() == ['a', 'b', '<Missing>', 'a', 'b']
    assert new_data['strings_with_missing2'].tolist() == ['<Missing>', 'b', '<Missing>', 'a', 'b']

    assert new_data['categories'].tolist() == ['a', 'b', 'c', 'a', 'b']
    assert new_data['categories_with_missing'].tolist() == ['a', 'b', '<Missing>', 'a', 'b']
    assert new_data['categories_with_missing2'].tolist() == ['<Missing>', 'b', '<Missing>', 'a', 'b']  # noqa
    assert new_data['categories'].dtype.name == 'category'
    assert new_data['categories_with_missing'].dtype.name == 'category'
    assert new_data['categories_with_missing2'].dtype.name == 'category'
    assert new_data['categories'].cat.categories.tolist() == mock_data2['categories'].cat.categories.tolist()  # noqa
    assert new_data['categories_with_missing'].cat.categories.tolist() == mock_data2['categories_with_missing'].cat.categories.tolist() + ['<Missing>']  # noqa
    assert new_data['categories_with_missing2'].cat.categories.tolist() == mock_data2['categories_with_missing2'].cat.categories.tolist() + ['<Missing>']  # noqa

    assert new_data['booleans'].tolist() == [True, False, True, False, True]
    assert new_data['booleans_with_missing'].tolist() == [True, False, '<Missing>', False, True]
    assert new_data['booleans_with_missing2'].tolist() == ['<Missing>', False, '<Missing>', False, True]  # noqa

    assert new_data['dates'].tolist() == [
        pd.Timestamp('2023-01-01 00:00:00'),
        pd.Timestamp('2023-01-02 00:00:00'),
        pd.Timestamp('2023-01-03 00:00:00'),
        pd.Timestamp('2023-01-04 00:00:00'),
        pd.Timestamp('2023-01-05 00:00:00'),
    ]

def test_convert_to_graph_data__date_columns(capsys):  # noqa
    dates_df = pd.DataFrame({
        'dates': [
            pd.Timestamp('2023-02-15 00:00:01'),
            pd.Timestamp('2023-03-31 10:31:00'),
            pd.Timestamp('2023-07-02 09:13:00'),
            pd.Timestamp('2023-09-04 01:01:01'),
            pd.Timestamp('2024-12-31 11:59:59'),
        ],
        'dates_with_missing': [
            pd.Timestamp('2023-02-15 00:00:01'),
            pd.Timestamp('2023-03-31 10:31:00'),
            pd.NaT,
            pd.Timestamp('2023-09-04 01:01:01'),
            pd.Timestamp('2024-12-31 11:59:59'),
        ],
    })
    column_types = t.get_column_types(dates_df)

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor=None,
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert 'dates_with_missing' in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        pd.Timestamp('2023-02-15 00:00:01'),
        pd.Timestamp('2023-03-31 10:31:00'),
        pd.Timestamp('2023-09-04 01:01:01'),
        pd.Timestamp('2024-12-31 11:59:59'),
    ]
    assert new_data['dates_with_missing'].tolist() == [
        pd.Timestamp('2023-02-15 00:00:01'),
        pd.Timestamp('2023-03-31 10:31:00'),
        pd.Timestamp('2023-09-04 01:01:01'),
        pd.Timestamp('2024-12-31 11:59:59'),
    ]

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor='second',
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert "'dates'" in code
    assert "'dates_with_missing'" in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        '2023-02-15 00:00:01',
        '2023-03-31 10:31:00',
        '2023-09-04 01:01:01',
        '2024-12-31 11:59:59',
    ]
    assert new_data['dates_with_missing'].tolist() == [
        '2023-02-15 00:00:01',
        '2023-03-31 10:31:00',
        '2023-09-04 01:01:01',
        '2024-12-31 11:59:59',
    ]

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor='minute',
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert "'dates'" in code
    assert "'dates_with_missing'" in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        '2023-02-15 00:00:00',
        '2023-03-31 10:31:00',
        '2023-09-04 01:01:00',
        '2024-12-31 11:59:00',
    ]
    assert new_data['dates_with_missing'].tolist() == [
        '2023-02-15 00:00:00',
        '2023-03-31 10:31:00',
        '2023-09-04 01:01:00',
        '2024-12-31 11:59:00',
    ]

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor='hour',
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert "'dates'" in code
    assert "'dates_with_missing'" in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        '2023-02-15 00:00:00',
        '2023-03-31 10:00:00',
        '2023-09-04 01:00:00',
        '2024-12-31 11:00:00',
    ]
    assert new_data['dates_with_missing'].tolist() == [
        '2023-02-15 00:00:00',
        '2023-03-31 10:00:00',
        '2023-09-04 01:00:00',
        '2024-12-31 11:00:00',
    ]

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor='day',
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert "'dates'" in code
    assert "'dates_with_missing'" in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        '2023-02-15',
        '2023-03-31',
        '2023-09-04',
        '2024-12-31',
    ]
    assert new_data['dates_with_missing'].tolist() == [
        '2023-02-15',
        '2023-03-31',
        '2023-09-04',
        '2024-12-31',
    ]

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor='week',
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert "'dates'" in code
    assert "'dates_with_missing'" in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        '2023-02-13',
        '2023-03-27',
        '2023-09-04',
        '2024-12-30',
    ]
    assert new_data['dates_with_missing'].tolist() == [
        '2023-02-13',
        '2023-03-27',
        '2023-09-04',
        '2024-12-30',
    ]

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor='quarter',
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert "'dates'" in code
    assert "'dates_with_missing'" in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        '2023-01-01',
        '2023-01-01',
        '2023-07-01',
        '2024-10-01',
    ]
    assert new_data['dates_with_missing'].tolist() == [
        '2023-01-01',
        '2023-01-01',
        '2023-07-01',
        '2024-10-01',
    ]

    new_data, markdown, code = convert_to_graph_data(
        data=dates_df,
        column_types=column_types,
        selected_variables=['dates', 'dates_with_missing'],
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=None,
        date_floor='year',
    )
    assert new_data.columns.tolist() == ['dates', 'dates_with_missing']
    assert dates_df is not new_data
    assert "'dates'" in code
    assert "'dates_with_missing'" in code
    assert 'dates_with_missing' in markdown
    assert '`1` missing' in markdown
    assert new_data['dates'].tolist() == [
        '2023-01-01',
        '2023-01-01',
        '2023-01-01',
        '2024-01-01',
    ]
    assert new_data['dates_with_missing'].tolist() == [
        '2023-01-01',
        '2023-01-01',
        '2023-01-01',
        '2024-01-01',
    ]

def test_convert_to_graph_data__create_cohorts_from(capsys, mock_data2):  # noqa
    column_types = t.get_column_types(mock_data2)
    selected_variables = [
        'integers', 'strings', 'dates', 'datetimes_with_missing', 'datetimes_with_missing2',
    ]
    new_data, markdown, code = convert_to_graph_data(
        data=mock_data2,
        column_types=column_types,
        selected_variables=selected_variables,
        top_n_categories=2,
        exclude_from_top_n_transformation=None,
        create_cohorts_from=('datetimes_with_missing', 'datetimes_with_missing2'),
        date_floor='week',
    )
    assert new_data.columns.tolist() == [*selected_variables, "datetimes_with_missing (Cohorts)"]
    assert mock_data2 is not new_data
    assert new_data['integers'].tolist() == [1, 2, 4, 5]
    assert new_data['strings'].tolist() == ['a', 'b', 'a', 'b']
    assert new_data['dates'].tolist() == ['2022-12-26', '2023-01-02', '2023-01-02', '2023-01-02']
    # still auto-filtering out missing values for datetimes_with_missing
    # since it is being used as the cohort
    assert 'datetimes_with_missing' in code
    assert 'datetimes_with_missing' in markdown
    # this variable should be ignored when using as cohort
    assert 'datetimes_with_missing2' not in code
    assert 'datetimes_with_missing2' not in markdown
    assert '`1` missing' in markdown  # should only be missing value 1 from datetimes_with_missing
    # should not have modified either dates so that we can accurately calculate the
    # time to conversion
    assert new_data['datetimes_with_missing'].tolist() == [
        pd.Timestamp('2023-01-01 01:01:01'),
        pd.Timestamp('2023-01-02 02:02:02'),
        pd.Timestamp('2023-01-04 04:04:04'),
        pd.Timestamp('2023-01-05 05:05:05'),
    ]
    assert new_data['datetimes_with_missing2'].tolist() == [
        pd.NaT,
        pd.Timestamp('2023-01-02 02:02:02'),
        pd.Timestamp('2023-01-04 04:04:04'),
        pd.Timestamp('2023-01-05 05:05:05'),
    ]
    assert new_data['datetimes_with_missing (Cohorts)'].tolist() == [
        '2022-12-26', '2023-01-02', '2023-01-02', '2023-01-02',
    ]

def test_convert_to_graph_data__exclude_from_top_n_transformation():  # noqa
    data = pd.DataFrame({
        'strings': ['a', 'b', 'c', 'a', 'b', 'd', 'e', 'f'],
        'strings2': ['a', 'b', 'c', 'a', 'b', 'd', 'e', 'f'],
        'categories': pd.Categorical(['a', 'b', 'c', 'a', 'b', 'd', 'e', 'f']),
        'categories2': pd.Categorical(['a', 'b', 'c', 'a', 'b', 'd', 'e', 'f']),
    })
    column_types = t.get_column_types(data)
    new_data, markdown, code = convert_to_graph_data(
        data=data,
        column_types=column_types,
        selected_variables=['strings', 'categories', 'categories2'],
        top_n_categories=2,
        exclude_from_top_n_transformation=['strings', 'categories'],
        create_cohorts_from=None,
        date_floor=None,
    )
    assert new_data.columns.tolist() == ['strings', 'categories', 'categories2']
    # assert data is not new_data
    assert markdown == ''
    assert new_data['strings'].tolist() == data['strings'].tolist()
    assert new_data['categories'].tolist() == data['categories'].tolist()
    assert new_data['categories2'].tolist() == [
        'a', 'b', '<Other>', 'a', 'b', '<Other>', '<Other>', '<Other>',
    ]

def test_get_combinations():  # noqa
    assert generate_combinations([[None], ['a', 'b'], [None]]) == [(None, 'a', None), (None, 'b', None)]  # noqa
    assert generate_combinations([[None], ['a', 'b']]) == [(None, 'a'), (None, 'b')]
    assert generate_combinations([[1], ['a', 'b']]) == [(1, 'a'), (1, 'b')]
    assert generate_combinations([[1, 2], ['a', 'b']]) == [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
    assert generate_combinations([[1, 2], ['a', 'b'], [True, False]]) == [
        (1, 'a', True), (1, 'a', False), (1, 'b', True), (1, 'b', False),
        (2, 'a', True), (2, 'a', False), (2, 'b', True), (2, 'b', False),
    ]

def test_generate_graph__all_configurations(  # noqa
        capsys,  # noqa
        mock_data2: list[str],
        graphing_configurations: dict,
        ):
    # this function tests all combinations found in graphing_configurations.yml
    # it tests all selected-variable, grpah-type, and optional-variable combinations
    column_types = t.get_column_types(mock_data2)
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
        selected_category_order=None,
        hist_func_agg=None,
        bar_mode=None,
        date_floor=None,
        cohort_conversion_rate_snapshots=None,
        cohort_conversion_rate_units=None,
        opacity=None,
        n_bins=None,
        min_retention_events=None,
        num_retention_periods=None,
        log_x_axis=None,
        log_y_axis=None,
        free_x_axis=None,
        free_y_axis=None,
        show_axes_histogram=None,
        title=None,
        graph_labels=None,
        column_types=column_types,
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
                if graph_type['name'] == 'cohorted conversion rates':
                    mock_data2 = mock_data2.copy()
                    # this happens in `convert_to_graph_data``
                    mock_data2[f'{type_to_column_lookup[x_var]} (Cohorts)'] = (
                        pd.to_datetime(mock_data2[type_to_column_lookup[x_var]])
                        .dt.to_period('M').dt.start_time
                        .dt.strftime('%Y-%m-%d')
                    )
                print(graph_type['name'], x_var, y_var, z_var)
                # x_var, y_var, z_var = variable_combinations[0]
                # test with no parameters
                if graph_type['name'] == 'bar - count distinct' and y_var == x_var:
                    with pytest.raises(InvalidConfigurationError):
                        fig, code = generate_graph(
                            data=mock_data2.copy(),
                            graph_type=graph_type['name'],
                            x_variable=type_to_column_lookup[x_var] if x_var else None,
                            y_variable=type_to_column_lookup[y_var] if y_var else None,
                            z_variable=type_to_column_lookup[z_var] if z_var else None,
                            color_variable=None,
                            size_variable=None,
                            facet_variable=None,
                            num_facet_columns=4,
                            selected_category_order='category ascending',
                            hist_func_agg='max',
                            bar_mode='relative',
                            date_floor='week',
                            cohort_conversion_rate_snapshots=[1, 2, 3],
                            cohort_conversion_rate_units='days',
                            opacity=0.6,
                            n_bins=30,
                            min_retention_events=2,
                            num_retention_periods=10,
                            log_x_axis=None,
                            log_y_axis=None,
                            free_x_axis=None,
                            free_y_axis=None,
                            show_axes_histogram=None,
                            title=None,
                            graph_labels=None,
                            column_types=column_types,
                        )
                else:
                    fig, code = generate_graph(
                        data=mock_data2.copy(),
                        graph_type=graph_type['name'],
                        x_variable=type_to_column_lookup[x_var] if x_var else None,
                        y_variable=type_to_column_lookup[y_var] if y_var else None,
                        z_variable=type_to_column_lookup[z_var] if z_var else None,
                        color_variable=None,
                        size_variable=None,
                        facet_variable=None,
                        num_facet_columns=4,
                        selected_category_order='category ascending',
                        hist_func_agg='max',
                        bar_mode='relative',
                        date_floor='week',
                        cohort_conversion_rate_snapshots=[1, 2, 3],
                        cohort_conversion_rate_units='days',
                        opacity=0.6,
                        n_bins=30,
                        min_retention_events=2,
                        num_retention_periods=10,
                        log_x_axis=None,
                        log_y_axis=None,
                        free_x_axis=None,
                        free_y_axis=None,
                        show_axes_histogram=None,
                        title=None,
                        graph_labels=None,
                        column_types=column_types,
                    )
                    assert isinstance(fig, go.Figure)
                    assert code is not None
                    if graph_type['name'] == 'scatter-3d':
                        assert 'px.scatter_3d' in code
                    elif graph_type['name'] == 'retention':
                        assert 'plot_retention' in code
                    elif graph_type['name'] == 'heatmap - count distinct':
                        assert 'px.density_heatmap' in code
                    elif graph_type['name'] == 'P(Y | X)':
                        assert 'px.bar' in code or 'px.line' in code
                    elif graph_type['name'] == 'bar - count distinct':
                        assert 'px.bar' in code
                    elif graph_type['name'] == 'cohorted conversion rates':
                        assert 'plot_cohorted_conversion_rates' in code
                    else:
                        assert graph_type['name'] in code

                # test with optional parameters
                if 'optional_variables' in graph_type:
                    optional_variables = graph_type['optional_variables'] or {}
                else:
                    optional_variables = {}

                color_variable = optional_variables['color_variable']['types'] if 'color_variable' in optional_variables else None  # noqa
                size_variable = optional_variables['size_variable']['types'] if 'size_variable' in optional_variables else None  # noqa
                facet_variable = optional_variables['facet_variable']['types'] if 'facet_variable' in optional_variables else None  # noqa

                optional_combinations = generate_combinations([
                    color_variable or [None],
                    size_variable or [None],
                    facet_variable or [None],
                ])
                if graph_type['name'] == 'P(Y | X)':
                    continue
                for color_var, size_var, facet_var in optional_combinations:
                    if (graph_type['name'] == 'bar - count distinct'
                            and y_var in [x_var, color_var, size_var, facet_var]
                        ):
                        # ensure y variable (which is what we are counting distinct on) is not the
                        # same as x, color, or facet variable
                        with pytest.raises(InvalidConfigurationError):
                            fig, code = generate_graph(
                                data=mock_data2.copy(),
                                graph_type=graph_type['name'],
                                x_variable=type_to_column_lookup[x_var] if x_var else None,
                                y_variable=type_to_column_lookup[y_var] if y_var else None,
                                z_variable=type_to_column_lookup[z_var] if z_var else None,
                                color_variable=type_to_column_lookup[color_var] if color_var else None,  # noqa
                                size_variable=type_to_column_lookup[size_var] if size_var else None,  # noqa
                                facet_variable=type_to_column_lookup[facet_var] if facet_var else None,  # noqa
                                num_facet_columns=None,
                                selected_category_order=None,
                                hist_func_agg=None,
                                bar_mode=None,
                                date_floor=None,
                                cohort_conversion_rate_snapshots=None,
                                cohort_conversion_rate_units=None,
                                opacity=None,
                                n_bins=None,
                                min_retention_events=None,
                                num_retention_periods=None,
                                log_x_axis=True,
                                log_y_axis=False,
                                free_x_axis=True,
                                free_y_axis=False,
                                show_axes_histogram=True,
                                title="Title",
                                graph_labels={"x": "X", "y": "Y", "color": "Color", "size": "Size"},  # noqa
                                column_types=column_types,
                            )
                    else:
                        print(graph_type['name'], x_var, y_var, z_var, color_var, size_var, facet_var)  # noqa  
                        fig, code = generate_graph(
                            data=mock_data2.copy(),
                            graph_type=graph_type['name'],
                            x_variable=type_to_column_lookup[x_var] if x_var else None,
                            y_variable=type_to_column_lookup[y_var] if y_var else None,
                            z_variable=type_to_column_lookup[z_var] if z_var else None,
                            color_variable=type_to_column_lookup[color_var] if color_var else None,
                            size_variable=type_to_column_lookup[size_var] if size_var else None,
                            facet_variable=type_to_column_lookup[facet_var] if facet_var else None,
                            num_facet_columns=None,
                            selected_category_order=None,
                            hist_func_agg=None,
                            bar_mode=None,
                            date_floor='week',
                            cohort_conversion_rate_snapshots=[1, 2, 3],
                            cohort_conversion_rate_units='days',
                            opacity=None,
                            n_bins=None,
                            min_retention_events=2,
                            num_retention_periods=10,
                            log_x_axis=True,
                            log_y_axis=False,
                            free_x_axis=True,
                            free_y_axis=False,
                            show_axes_histogram=True,
                            title="Title",
                            graph_labels={"x": "X", "y": "Y", "color": "Color", "size": "Size"},
                            column_types=column_types,
                        )
                        assert isinstance(fig, go.Figure)
                        assert code is not None
                        if graph_type['name'] == 'scatter-3d':
                            assert 'px.scatter_3d' in code
                        elif graph_type['name'] == 'retention':
                            assert 'plot_retention' in code
                        elif graph_type['name'] == 'heatmap - count distinct':
                            assert 'px.density_heatmap' in code
                        elif graph_type['name'] == 'P(Y | X)':
                            assert 'px.bar' in code or 'px.line' in code
                        elif graph_type['name'] == 'bar - count distinct':
                            assert 'px.bar' in code
                        elif graph_type['name'] == 'cohorted conversion rates':
                            assert 'plot_cohorted_conversion_rates' in code
                        else:
                            assert graph_type['name'] in code

def test_generate_graph__error(  # noqa
        capsys,  # noqa
        mock_data2: list[str],
        ):
    # plotly express complains if you try to use a categorical series where the categories are
    # not in the data.
    # In graph_data we removed unused categories, so to test this, we'll filter the data
    # to only include a subset of the categories and then try to plot using the column
    # as color or facet variable (for some reason plotly express doesn't complain about
    # using a categorical column as x or y variable)
    data = mock_data2.copy()
    column_types = t.get_column_types(mock_data2)
    data = data[data['categories'].isin(['a', 'b'])]
    fig, code = generate_graph(
        data=data,
        graph_type='box',
        x_variable='integers',
        y_variable=None,
        z_variable=None,
        color_variable=None,
        size_variable=None,
        facet_variable='categories',
        num_facet_columns=4,
        selected_category_order=None,
        hist_func_agg=None,
        bar_mode=None,
        date_floor=None,
        cohort_conversion_rate_snapshots=None,
        cohort_conversion_rate_units=None,
        opacity=None,
        n_bins=None,
        min_retention_events=None,
        num_retention_periods=None,
        log_x_axis=None,
        log_y_axis=None,
        free_x_axis=None,
        free_y_axis=None,
        show_axes_histogram=None,
        title=None,
        graph_labels=None,
        column_types=column_types,
    )
    assert isinstance(fig, go.Figure)
    assert code is not None
    assert 'px.box' in code

    fig, code = generate_graph(
        data=data,
        graph_type='histogram',
        x_variable='categories',
        y_variable=None,
        z_variable=None,
        color_variable='categories',
        size_variable=None,
        facet_variable=None,
        num_facet_columns=4,
        selected_category_order=None,
        hist_func_agg=None,
        bar_mode=None,
        date_floor=None,
        cohort_conversion_rate_snapshots=None,
        cohort_conversion_rate_units=None,
        opacity=None,
        n_bins=None,
        min_retention_events=None,
        num_retention_periods=None,
        log_x_axis=None,
        log_y_axis=None,
        free_x_axis=None,
        free_y_axis=None,
        show_axes_histogram=None,
        title=None,
        graph_labels=None,
        column_types=column_types,
    )
    assert isinstance(fig, go.Figure)
    assert code is not None
    assert 'px.histogram' in code

@pytest.mark.parametrize('order_type,expected_output', [  # noqa
    ('category ascending', {'category_1': ['x', 'y', 'z'], 'category_2': ['x', 'y', 'z']}),
    ('category descending', {'category_1': ['z', 'y', 'x'], 'category_2': ['z', 'y', 'x']}),
    ('total ascending',  {'category_1': ['z', 'x', 'y'], 'category_2': ['z', 'x', 'y']}),
    ('total descending',   {'category_1': ['y', 'x', 'z'], 'category_2': ['y', 'x', 'z']}),
])
def test_category_orders__strings_categories(order_type, expected_output):  # noqa
    category_order_data = pd.DataFrame({
        'numeric': [1, 2, 3, 4, 5, 6],
        'category_1': ['x', 'y', 'y', 'x', 'z', 'y'],
        'category_2': pd.Categorical(['x', 'y', 'y', 'x', 'z', 'y'], categories=['x', 'y', 'z']),
    })
    column_types = t.get_column_types(category_order_data)
    result = get_category_orders(
        data=category_order_data,
        selected_variables=['numeric', 'category_1', 'category_2'],
        selected_category_order=order_type,
        column_types=column_types,
    )
    assert result == expected_output

@pytest.mark.parametrize('order_type', [
    'category ascending',
    'category descending',
    'total ascending',
    'total descending',
])
def test_category_orders__dates(order_type):  # noqa
    category_order_data = pd.DataFrame({
        'numeric': [1, 2, 3, 4, 5, 6],
        'date': pd.to_datetime([
            '2021-01-01', '2021-01-02', '2021-01-02', '2021-01-01', '2021-01-03', '2021-01-02',
        ]),
    })
    column_types = t.get_column_types(category_order_data)
    result = get_category_orders(
        data=category_order_data,
        selected_variables=['numeric', 'date'],
        selected_category_order=order_type,
        column_types=column_types,
    )
    assert result == {}

@pytest.mark.parametrize('order_type,expected_output', [  # noqa
    ('category ascending', {'boolean': [False, True]}),
    ('category descending', {'boolean': [True, False]}),
    ('total ascending',  {'boolean': [True, False]}),
    ('total descending',   {'boolean': [False, True]}),
])
def test_category_orders__boolean(order_type, expected_output):  # noqa
    category_order_data = pd.DataFrame({
        'numeric': [1, 2, 3, 4, 5],
        'boolean': [True, False, False, True, False],
    })
    column_types = t.get_column_types(category_order_data)
    result = get_category_orders(
        data=category_order_data,
        selected_variables=['numeric', 'boolean'],
        selected_category_order=order_type,
        column_types=column_types,
    )
    assert result == expected_output

def test_no_selected_order():  # noqa
    category_order_data = pd.DataFrame({
        'numeric': [1, 2, 3, 4, 5, 6],
        'category_1': ['x', 'y', 'y', 'x', 'z', 'y'],
        'category_2': pd.Categorical(['x', 'y', 'y', 'x', 'z', 'y'], categories=['x', 'y', 'z']),
    })
    column_types = t.get_column_types(category_order_data)
    result = get_category_orders(
        data=category_order_data,
        selected_variables=['category_1', 'category_2'],
        selected_category_order=None,
        column_types=column_types,
    )
    assert result == {}

def test_unknown_order_type_raises_exception():  # noqa
    category_order_data = pd.DataFrame({
        'numeric': [1, 2, 3, 4, 5, 6],
        'category_1': ['x', 'y', 'y', 'x', 'z', 'y'],
        'category_2': pd.Categorical(['x', 'y', 'y', 'x', 'z', 'y'], categories=['x', 'y', 'z']),
    })
    column_types = t.get_column_types(category_order_data)
    with pytest.raises(ValueError, match=r"Unknown selected_category_order"):
        get_category_orders(
            data=category_order_data,
            selected_variables=['category_1', 'category_2'],
            selected_category_order='unknown_order_type',
            column_types=column_types,
        )

@pytest.mark.parametrize('order_type', [
    'category ascending',
    'category descending',
    'total ascending',
    'total descending',
])
def test_get_category_orders_with_more_than_50_values(order_type):  # noqa
    data = pd.DataFrame({
        'valid': ['a', 'b'] * 50,
        'invalid': [f'category_{i}' for i in range(100)],
    })
    column_types = t.get_column_types(data)
    result = get_category_orders(
        data=data,
        selected_variables=['valid', 'invalid'],
        selected_category_order=order_type,
        column_types=column_types,
    )
    result['valid'] = ['a', 'b']
    assert 'invalid' not in result

def test_duplicates_in_selected_variables():  # noqa
    category_order_data = pd.DataFrame({
        'numeric': [1, 2, 3, 4, 5, 6],
        'category_1': ['x', 'y', 'y', 'x', 'z', 'y'],
        'category_2': pd.Categorical(['x', 'y', 'y', 'x', 'z', 'y'], categories=['x', 'y', 'z']),
    })
    column_types = t.get_column_types(category_order_data)
    with pytest.raises(AssertionError):
        get_category_orders(
            data=category_order_data,
            selected_variables=['category_1', 'category_1'],
            selected_category_order='unknown_order_type',
            column_types=column_types,
        )
