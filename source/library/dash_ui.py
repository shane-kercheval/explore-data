"""Helper functions for creating dash components."""
from datetime import date, datetime
from dash import html, dcc
import dash_daq as daq
from source.library.dash_utilities import log_variable
from source.library.utilities import to_date


CLASS__GRAPH_PANEL_SECTION = 'graph_panel_section'


def create_control(
        label: str,
        id: str,  # noqa: A002
        component: html.Div,
        hidden: bool = False) -> html.Div:
    """Create a generic control with a given component (e.g. dropdown)."""
    style = {'display': 'none'} if hidden else {}
    if label:
        children = [
            html.Label(
                f"{label}:",
                className=CLASS__GRAPH_PANEL_SECTION + '_label',
            ),
            component,
        ]
    else:
        children = [component]
    return html.Div(
        id=f'{id}_div',
        className=CLASS__GRAPH_PANEL_SECTION,
        style=style,
        children=children,
    )


def create_dropdown_control(
        label: str,
        id: str,  # noqa: A002
        hidden: bool = False,
        multi: bool = False,
        options: list[dict] | None = None,
        value: str | None = None,
        placeholder: str | None = None,
        clearable: bool = True,
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
            clearable=clearable,
        ),
    )


def create_checklist_control(
        id: str,  # noqa: A002
        hidden: bool = False,
        options: list[str] | None = None,
        value: list[str] | None = None,
        component_id: dict | None = None,
        ) -> html.Div:
    """Create a dropdown control."""
    if options is None:
        options = []
    if component_id is None:
        component_id = f'{id}_checklist'
    else:
        assert isinstance(component_id, dict)

    return create_control(
        label=None,
        id=id,
        hidden=hidden,
        component=dcc.Checklist(
            id=component_id,
            className='checkbox-label',
            options=options or [],
            value=value or [],
            inline=True,
        ),
    )


def create_slider_control(
        label: str,
        id: str,  # noqa: A002
        value: int | float | list[int] | list[float],
        min: int | float | None = None,  # noqa: A002
        max: int | float | None = None,  # noqa: A002
        step: int | float | None = None,
        marks: dict = {},
        hidden: bool = False,
        component_id: dict | None = None,
        ) -> html.Div:
    """Create a dropdown control."""
    if component_id is None:
        component_id = f'{id}_slider'
    else:
        assert isinstance(component_id, dict)

    # if step is None:
    #     # step should create 5 steps
    #     step = (max - min) / 5

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
            marks=marks,
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


def create_cohort_conversion_rate_control(
        label: str,
        id: str,  # noqa: A002
        input_value: str = '1, 7, 14, 30',
        dropdown_options: list[dict] | None = None,
        dropdown_value: str = 'days',
        hidden: bool = False,
        ) -> html.Div:
    """Create a min/max control."""
    if dropdown_options is None:
        dropdown_options = [
            {'label': 'Days', 'value': 'days'},
            {'label': 'Hours', 'value': 'hours'},
            {'label': 'Seconds', 'value': 'seconds'},
            {'label': 'Minutes', 'value': 'minutes'},

        ]

    component_id_input = f'{id}__input'
    component_id_dropdown = f'{id}__dropdown'

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
            html.Div(className='cohort_snapshots_div', children=[
                dcc.Input(
                    id=component_id_input,
                    value=input_value,
                ),
                dcc.Dropdown(
                    id=component_id_dropdown,
                    options=dropdown_options,
                    value=dropdown_value,
                    clearable=False,
                ),
            ]),
        ],
    )

def create_cohort_adoption_rate_control(
        label: str,
        id: str,  # noqa: A002
        input_value: int = 30,
        dropdown_options: list[dict] | None = None,
        dropdown_value: str = 'days',
        hidden: bool = False,
        ) -> html.Div:
    """Create cohorted adoption rate control."""
    if dropdown_options is None:
        dropdown_options = [
            {'label': 'Weeks', 'value': 'weeks'},
            {'label': 'Days', 'value': 'days'},
            {'label': 'Hours', 'value': 'hours'},
            {'label': 'Minutes', 'value': 'minutes'},
            {'label': 'Seconds', 'value': 'seconds'},
        ]

    component_id_input = f'{id}__input'
    component_id_dropdown = f'{id}__dropdown'

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
            html.Div(className='cohort_adoption_div', children=[
                daq.NumericInput(
                    id=component_id_input,
                    min=0,
                    max=1000,
                    value=input_value,
                ),
                dcc.Dropdown(
                    id=component_id_dropdown,
                    options=dropdown_options,
                    value=dropdown_value,
                    clearable=False,
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
    """Create a date-range control."""
    if component_id is None:
        component_id = f'{id}_date_range'
    else:
        assert isinstance(component_id, dict)

    min_value = to_date(min_value)
    max_value = to_date(max_value)

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


def create_input_control(
        label: str,
        id: str,  # noqa: A002
        hidden: bool = False,
        value: str | None = None,
        placeholder: str | None = None,
        component_id: dict | None = None,
        ) -> html.Div:
    """Create a dropdown control."""
    if component_id is None:
        component_id = f'{id}_input'
    else:
        assert isinstance(component_id, dict)

    return create_control(
        label=label,
        id=id,
        hidden=hidden,
        component=dcc.Input(
            id=component_id,
            value=value,
            placeholder=placeholder,
            style={'width': '100%'},
        ),
    )
