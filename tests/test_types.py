"""Tests for types.py."""
import numpy as np
import pandas as pd
import source.library.types as t


def test_is_series_datetime(mock_data1):  # noqa
    assert t.is_series_datetime(mock_data1['date_string'])
    assert t.is_series_datetime(mock_data1['date_string_with_missing'])
    assert t.is_series_datetime(mock_data1['datetime_string'])
    assert t.is_series_datetime(mock_data1['datetime_string_with_missing'])
    assert t.is_series_datetime(mock_data1['datetimes'])
    assert t.is_series_datetime(mock_data1['datetimes_with_missing'])
    assert t.is_series_datetime(mock_data1['dates'])
    assert t.is_series_datetime(mock_data1['dates_with_missing'])
    assert not t.is_series_datetime(mock_data1['random_strings'])
    assert not t.is_series_datetime(mock_data1['integers'])
    assert not t.is_series_datetime(mock_data1['integers_with_missing'])
    assert not t.is_series_datetime(mock_data1['floats'])
    assert not t.is_series_datetime(mock_data1['floats_with_missing'])
    assert not t.is_series_datetime(mock_data1['booleans'])
    assert not t.is_series_datetime(mock_data1['booleans_with_missing'])


def test_create_type_dict(mock_data1):  # noqa
    mock_data1 = mock_data1.copy()
    mock_data1['categorical'] = pd.Categorical(['a', 'b', 'c'])
    mock_data1['categorical_with_missing'] = pd.Categorical(['a', 'b', np.nan])
    column_types = t.get_column_types(mock_data1)
    assert column_types == {
        'date_string': 'date',
        'date_string_with_missing': 'date',
        'datetime_string': 'date',
        'datetime_string_with_missing': 'date',
        'random_strings': 'string',
        'integers': 'numeric',
        'integers_with_missing': 'numeric',
        'floats': 'numeric',
        'floats_with_missing': 'numeric',
        'booleans': 'boolean',
        'booleans_with_missing': 'boolean',
        'datetimes': 'date',
        'datetimes_with_missing': 'date',
        'dates': 'date',
        'dates_with_missing': 'date',
        'categorical': 'categorical',
        'categorical_with_missing': 'categorical',
    }
    assert t.get_type(column='date_string', column_types=column_types) == 'date'
    assert t.get_type(column='date_string_with_missing', column_types=column_types) == 'date'
    assert t.get_type(column='datetime_string', column_types=column_types) == 'date'
    assert t.get_type(column='datetime_string_with_missing', column_types=column_types) == 'date'
    assert t.get_type(column='random_strings', column_types=column_types) == 'string'
    assert t.get_type(column='integers', column_types=column_types) == 'numeric'
    assert t.get_type(column='integers_with_missing', column_types=column_types) == 'numeric'
    assert t.get_type(column='floats', column_types=column_types) == 'numeric'
    assert t.get_type(column='floats_with_missing', column_types=column_types) == 'numeric'
    assert t.get_type(column='booleans', column_types=column_types) == 'boolean'
    assert t.get_type(column='booleans_with_missing', column_types=column_types) == 'boolean'
    assert t.get_type(column='datetimes', column_types=column_types) == 'date'
    assert t.get_type(column='datetimes_with_missing', column_types=column_types) == 'date'
    assert t.get_type(column='dates', column_types=column_types) == 'date'
    assert t.get_type(column='dates_with_missing', column_types=column_types) == 'date'
    assert t.get_type(column='categorical', column_types=column_types) == 'categorical'
    assert t.get_type(column='categorical_with_missing', column_types=column_types) == 'categorical'  # noqa
    assert t.get_type(column=None, column_types=column_types) is None

    assert t.is_numeric(column=None, column_types=column_types) is None
    assert t.is_date(column=None, column_types=column_types) is None
    assert t.is_string(column=None, column_types=column_types) is None
    assert t.is_categorical(column=None, column_types=column_types) is None
    assert t.is_boolean(column=None, column_types=column_types) is None
    assert t.is_discrete(column=None, column_types=column_types) is None
    assert t.is_continuous(column=None, column_types=column_types) is None

    assert t.get_all_columns(column_types) == mock_data1.columns.tolist()
    assert t.get_numeric_columns(column_types) == ['integers', 'integers_with_missing', 'floats', 'floats_with_missing']  # noqa
    assert t.get_date_columns(column_types) == ['date_string', 'date_string_with_missing', 'datetime_string', 'datetime_string_with_missing', 'datetimes', 'datetimes_with_missing', 'dates', 'dates_with_missing']  # noqa
    assert t.get_string_columns(column_types) == ['random_strings']
    assert t.get_categorical_columns(column_types) == ['categorical', 'categorical_with_missing']
    assert t.get_boolean_columns(column_types) == ['booleans', 'booleans_with_missing']
    assert t.get_discrete_columns(column_types) == ['random_strings', 'booleans', 'booleans_with_missing', 'categorical', 'categorical_with_missing']  # noqa
    assert t.get_continuous_columns(column_types) == ['date_string', 'date_string_with_missing', 'datetime_string', 'datetime_string_with_missing', 'integers', 'integers_with_missing', 'floats', 'floats_with_missing', 'datetimes', 'datetimes_with_missing', 'dates', 'dates_with_missing']  # noqa

    assert t.is_type(column='integers', column_types=column_types, dtype='numeric')
    assert not t.is_type(column='integers', column_types=column_types, dtype='date')
    assert t.is_numeric(column='integers', column_types=column_types)
    assert not t.is_date(column='integers', column_types=column_types)
    assert not t.is_string(column='integers', column_types=column_types)
    assert not t.is_categorical(column='integers', column_types=column_types)
    assert not t.is_boolean(column='integers', column_types=column_types)
    assert not t.is_discrete(column='integers', column_types=column_types)
    assert t.is_continuous(column='integers', column_types=column_types)

    assert t.is_type(column='integers_with_missing', column_types=column_types, dtype='numeric')
    assert not t.is_type(column='integers_with_missing', column_types=column_types, dtype='date')
    assert t.is_numeric(column='integers_with_missing', column_types=column_types)
    assert not t.is_date(column='integers_with_missing', column_types=column_types)
    assert not t.is_string(column='integers_with_missing', column_types=column_types)
    assert not t.is_categorical(column='integers_with_missing', column_types=column_types)
    assert not t.is_boolean(column='integers_with_missing', column_types=column_types)
    assert not t.is_discrete(column='integers_with_missing', column_types=column_types)
    assert t.is_continuous(column='integers_with_missing', column_types=column_types)

    assert t.is_type(column='date_string', column_types=column_types, dtype='date')
    assert not t.is_type(column='date_string', column_types=column_types, dtype='numeric')
    assert not t.is_numeric(column='date_string', column_types=column_types)
    assert t.is_date(column='date_string', column_types=column_types)
    assert not t.is_string(column='date_string', column_types=column_types)
    assert not t.is_categorical(column='date_string', column_types=column_types)
    assert not t.is_boolean(column='date_string', column_types=column_types)
    assert not t.is_discrete(column='date_string', column_types=column_types)
    assert t.is_continuous(column='date_string', column_types=column_types)

    assert t.is_type(column='date_string_with_missing', column_types=column_types, dtype='date')
    assert not t.is_type(column='date_string_with_missing', column_types=column_types, dtype='numeric')  # noqa
    assert not t.is_numeric(column='date_string_with_missing', column_types=column_types)
    assert t.is_date(column='date_string_with_missing', column_types=column_types)
    assert not t.is_string(column='date_string_with_missing', column_types=column_types)
    assert not t.is_categorical(column='date_string_with_missing', column_types=column_types)
    assert not t.is_boolean(column='date_string_with_missing', column_types=column_types)
    assert not t.is_discrete(column='date_string_with_missing', column_types=column_types)
    assert t.is_continuous(column='date_string_with_missing', column_types=column_types)

    assert t.is_type(column='random_strings', column_types=column_types, dtype='string')
    assert not t.is_type(column='random_strings', column_types=column_types, dtype='numeric')
    assert not t.is_numeric(column='random_strings', column_types=column_types)
    assert not t.is_date(column='random_strings', column_types=column_types)
    assert t.is_string(column='random_strings', column_types=column_types)
    assert not t.is_categorical(column='random_strings', column_types=column_types)
    assert not t.is_boolean(column='random_strings', column_types=column_types)
    assert t.is_discrete(column='random_strings', column_types=column_types)
    assert not t.is_continuous(column='random_strings', column_types=column_types)

    assert t.is_type(column='booleans', column_types=column_types, dtype='boolean')
    assert not t.is_type(column='booleans', column_types=column_types, dtype='numeric')
    assert not t.is_numeric(column='booleans', column_types=column_types)
    assert not t.is_date(column='booleans', column_types=column_types)
    assert not t.is_string(column='booleans', column_types=column_types)
    assert not t.is_categorical(column='booleans', column_types=column_types)
    assert t.is_boolean(column='booleans', column_types=column_types)
    assert t.is_discrete(column='booleans', column_types=column_types)
    assert not t.is_continuous(column='booleans', column_types=column_types)

    assert t.is_type(column='booleans_with_missing', column_types=column_types, dtype='boolean')
    assert not t.is_type(column='booleans_with_missing', column_types=column_types, dtype='numeric')  # noqa
    assert not t.is_numeric(column='booleans_with_missing', column_types=column_types)
    assert not t.is_date(column='booleans_with_missing', column_types=column_types)
    assert not t.is_string(column='booleans_with_missing', column_types=column_types)
    assert not t.is_categorical(column='booleans_with_missing', column_types=column_types)
    assert t.is_boolean(column='booleans_with_missing', column_types=column_types)
    assert t.is_discrete(column='booleans_with_missing', column_types=column_types)
    assert not t.is_continuous(column='booleans_with_missing', column_types=column_types)

    assert t.is_type(column='floats', column_types=column_types, dtype='numeric')
    assert not t.is_type(column='floats', column_types=column_types, dtype='date')
    assert t.is_numeric(column='floats', column_types=column_types)
    assert not t.is_date(column='floats', column_types=column_types)
    assert not t.is_string(column='floats', column_types=column_types)
    assert not t.is_categorical(column='floats', column_types=column_types)
    assert not t.is_boolean(column='floats', column_types=column_types)
    assert not t.is_discrete(column='floats', column_types=column_types)
    assert t.is_continuous(column='floats', column_types=column_types)

    assert t.is_type(column='floats_with_missing', column_types=column_types, dtype='numeric')
    assert not t.is_type(column='floats_with_missing', column_types=column_types, dtype='date')
    assert t.is_numeric(column='floats_with_missing', column_types=column_types)
    assert not t.is_date(column='floats_with_missing', column_types=column_types)
    assert not t.is_string(column='floats_with_missing', column_types=column_types)
    assert not t.is_categorical(column='floats_with_missing', column_types=column_types)
    assert not t.is_boolean(column='floats_with_missing', column_types=column_types)
    assert not t.is_discrete(column='floats_with_missing', column_types=column_types)
    assert t.is_continuous(column='floats_with_missing', column_types=column_types)

    assert t.is_type(column='datetime_string', column_types=column_types, dtype='date')
    assert not t.is_type(column='datetime_string', column_types=column_types, dtype='numeric')
    assert not t.is_numeric(column='datetime_string', column_types=column_types)
    assert t.is_date(column='datetime_string', column_types=column_types)
    assert not t.is_string(column='datetime_string', column_types=column_types)
    assert not t.is_categorical(column='datetime_string', column_types=column_types)
    assert not t.is_boolean(column='datetime_string', column_types=column_types)
    assert not t.is_discrete(column='datetime_string', column_types=column_types)
    assert t.is_continuous(column='datetime_string', column_types=column_types)

    assert t.is_type(column='datetime_string_with_missing', column_types=column_types, dtype='date')  # noqa
    assert not t.is_type(column='datetime_string_with_missing', column_types=column_types, dtype='numeric')  # noqa
    assert not t.is_numeric(column='datetime_string_with_missing', column_types=column_types)
    assert t.is_date(column='datetime_string_with_missing', column_types=column_types)
    assert not t.is_string(column='datetime_string_with_missing', column_types=column_types)
    assert not t.is_categorical(column='datetime_string_with_missing', column_types=column_types)
    assert not t.is_boolean(column='datetime_string_with_missing', column_types=column_types)
    assert not t.is_discrete(column='datetime_string_with_missing', column_types=column_types)
    assert t.is_continuous(column='datetime_string_with_missing', column_types=column_types)

    assert t.is_type(column='datetimes', column_types=column_types, dtype='date')
    assert not t.is_type(column='datetimes', column_types=column_types, dtype='numeric')
    assert not t.is_numeric(column='datetimes', column_types=column_types)
    assert t.is_date(column='datetimes', column_types=column_types)
    assert not t.is_string(column='datetimes', column_types=column_types)
    assert not t.is_categorical(column='datetimes', column_types=column_types)
    assert not t.is_boolean(column='datetimes', column_types=column_types)
    assert not t.is_discrete(column='datetimes', column_types=column_types)
    assert t.is_continuous(column='datetimes', column_types=column_types)

    assert t.is_type(column='datetimes_with_missing', column_types=column_types, dtype='date')
    assert not t.is_type(column='datetimes_with_missing', column_types=column_types, dtype='numeric')  # noqa
    assert not t.is_numeric(column='datetimes_with_missing', column_types=column_types)
    assert t.is_date(column='datetimes_with_missing', column_types=column_types)
    assert not t.is_string(column='datetimes_with_missing', column_types=column_types)
    assert not t.is_categorical(column='datetimes_with_missing', column_types=column_types)
    assert not t.is_boolean(column='datetimes_with_missing', column_types=column_types)
    assert not t.is_discrete(column='datetimes_with_missing', column_types=column_types)
    assert t.is_continuous(column='datetimes_with_missing', column_types=column_types)

    assert t.is_type(column='dates', column_types=column_types, dtype='date')
    assert not t.is_type(column='dates', column_types=column_types, dtype='numeric')
    assert not t.is_numeric(column='dates', column_types=column_types)
    assert t.is_date(column='dates', column_types=column_types)
    assert not t.is_string(column='dates', column_types=column_types)
    assert not t.is_categorical(column='dates', column_types=column_types)
    assert not t.is_boolean(column='dates', column_types=column_types)
    assert not t.is_discrete(column='dates', column_types=column_types)
    assert t.is_continuous(column='dates', column_types=column_types)

    assert t.is_type(column='dates_with_missing', column_types=column_types, dtype='date')
    assert not t.is_type(column='dates_with_missing', column_types=column_types, dtype='numeric')
    assert not t.is_numeric(column='dates_with_missing', column_types=column_types)
    assert t.is_date(column='dates_with_missing', column_types=column_types)
    assert not t.is_string(column='dates_with_missing', column_types=column_types)
    assert not t.is_categorical(column='dates_with_missing', column_types=column_types)
    assert not t.is_boolean(column='dates_with_missing', column_types=column_types)
    assert not t.is_discrete(column='dates_with_missing', column_types=column_types)
    assert t.is_continuous(column='dates_with_missing', column_types=column_types)
