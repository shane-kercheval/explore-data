"""Helper functions for creating dash components."""
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
from dash import html, dcc
import dash_daq as daq


from source.library.utilities import convert_to_date


CLASS__GRAPH_PANEL_SECTION = 'graph_panel_section'

def log(value: str) -> None:
    """Log value."""
    print(value, flush=True)


def log_function(name: str) -> None:
    """Log function calls."""
    log(f"\nFUNCTION: `{name}`")


def log_variable(var: str, value: str) -> None:
    """Log variable value."""
    log(f"VARIABLE: `{var}` = `{value}`")


def log_error(message: str) -> None:
    """Log variable value."""
    log(f">>>>>>>>>ERROR: `{message}`")


def values_to_dropdown_options(values: list[str]) -> list[dict]:
    """Convert a list of columns to a list of options for a dropdown."""
    # needs to be converted to str for dcc.Dropdown other wise it will fail
    return [{'label': str(value), 'value': str(value)} for value in values]


def create_control(
        label: str,
        id: str,  # noqa: A002
        component: html.Div,
        hidden: bool = False) -> html.Div:
    """Create a generic control with a given component (e.g. dropdown)."""
    style = {'display': 'none'} if hidden else {}
    return html.Div(
        id=f'{id}_div',
        className=CLASS__GRAPH_PANEL_SECTION,
        style=style,
        children=[
            html.Label(
                f"{label}:",
                className=CLASS__GRAPH_PANEL_SECTION + '_label',
            ),
            component,
    ])


def create_dropdown_control(
        label: str,
        id: str,  # noqa: A002
        hidden: bool = False,
        multi: bool = False,
        options: list[dict] | None = None,
        value: str | None = None,
        placeholder: str | None = None,
        component_id: dict | None = None,
        ) -> html.Div:
    """Create a dropdown control."""
    if options is None:
        options = []
    if component_id is None:
        component_id = f'{id}_dropdown'
    else:
        assert isinstance(component_id, dict)

    return create_control(
        label=label,
        id=id,
        hidden=hidden,
        component=dcc.Dropdown(
            id=component_id,
            multi=multi,
            options=options,
            value=value,
            placeholder=placeholder,
        ),
    )


def create_slider_control(
        label: str,
        id: str,  # noqa: A002
        min: int | float,  # noqa: A002
        max: int | float,  # noqa: A002
        value: int | float | list[int] | list[float],
        step: int | float | None = None,
        hidden: bool = False,
        component_id: dict | None = None,
        ) -> html.Div:
    """Create a dropdown control."""
    if component_id is None:
        component_id = f'{id}_slider'
    else:
        assert isinstance(component_id, dict)

    if step is None:
        # step should create 5 steps
        step = (max - min) / 5

    slider_type = dcc.RangeSlider if isinstance(value, list) else dcc.Slider

    return create_control(
        label=label,
        id=id,
        hidden=hidden,
        component=slider_type(
            id=component_id,
            min=min,
            max=max,
            step=step,
            # marks={i: str(i) for i in np.arange(min, max + step, step)},
            value=value,
        ),
    )


def create_min_max_control(
        label: str,
        id: str,  # noqa: A002
        min_value: int | float,
        max_value: int | float,
        hidden: bool = False,
        component_id: dict | None = None,
        ) -> html.Div:
    """Create a min/max control."""
    if component_id is None:
        component_id_min = f'{id}_min_max__min'
        component_id_max = f'{id}_min_max__max'
    else:
        assert isinstance(component_id, dict)
        assert 'type' in component_id
        component_id_min = component_id.copy()
        component_id_min['type'] = component_id['type'] + "__min"
        component_id_max = component_id.copy()
        component_id_max['type'] = component_id['type'] + "__max"
        log_variable('component_id_min', component_id_min)
        log_variable('component_id_max', component_id_max)

    style = {'display': 'none'} if hidden else {}
    return html.Div(
        id=f'{id}_div',
        className=CLASS__GRAPH_PANEL_SECTION,
        style=style,
        children=[
            html.Label(
                f"{label}:",
                className=CLASS__GRAPH_PANEL_SECTION + '_label',
            ),
            html.Div(className='min_max_div', children=[
                html.Label("Min:"),
                daq.NumericInput(
                    id=component_id_min,
                    min=min_value,
                    max=max_value,
                    value=min_value,
                ),
                html.Label("Max:"),
                daq.NumericInput(
                    id=component_id_max,
                    min=min_value,
                    max=max_value,
                    value=max_value,
                ),
            ]),
        ],
    )


def create_date_range_control(
        label: str,
        id: str,  # noqa: A002
        min_value: str | date | datetime,
        max_value: str | date | datetime,
        hidden: bool = False,
        component_id: dict | None = None,
        ) -> html.Div:
    """Create a dropdown control."""
    if component_id is None:
        component_id = f'{id}_dropdown'
    else:
        assert isinstance(component_id, dict)

    min_value = convert_to_date(min_value)
    max_value = convert_to_date(max_value)

    return create_control(
        label=label,
        id=id,
        hidden=hidden,
        component=dcc.DatePickerRange(
            id=component_id,
            min_date_allowed=min_value,
            max_date_allowed=max_value,
            start_date=min_value,
            end_date=max_value,
            style={'width': '100%'},
        ),
    )


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

    # Introduce sporadic missing values
    if sporadic_missing:
        num_missing = int(num_rows * 0.1)  # 10% missing values

        # missing_indices = np.random.choice(num_rows, num_missing, replace=False)
        # integers[missing_indices] = np.nan
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        floats[missing_indices] = np.nan
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        dates = [None if i in missing_indices else date for i, date in enumerate(dates)]
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        date_times = [None if i in missing_indices else date_time for i, date_time in enumerate(date_times)]  # noqa
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        date_strings = [None if i in missing_indices else date_string for i, date_string in enumerate(date_strings)]  # noqa
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        date_home_strings = [None if i in missing_indices else date_home_string for i, date_home_string in enumerate(date_home_strings)]  # noqa
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        categories = [None if i in missing_indices else category for i, category in enumerate(categories)]  # noqa
        categories2 = [np.nan if i in missing_indices else category for i, category in enumerate(categories)]  # noqa
        missing_indices = np.random.choice(num_rows, num_missing, replace=False)  # noqa
        booleans[missing_indices] = np.nan

    # Create the DataFrame
    return pd.DataFrame({
        'Integers': integers,
        'Floats': floats,
        'Dates': dates,
        'DateTimes': date_times,
        'DateStrings': date_strings,
        'DateHomeStrings': date_home_strings,
        'Categories': categories,
        'Categories2': categories2,
        'Booleans': booleans,
    })
