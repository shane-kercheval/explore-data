"""Helper functions for creating dash components."""
from dash import html, dcc
import dash_daq as daq


def log(value: str) -> None:
    """Log value."""
    print(value, flush=True)

def log_function(name: str) -> None:
    """Log function calls."""
    log(f"\nFUNCTION: `{name}`")

def log_variable(var: str, value: str) -> None:
    """Log variable value."""
    log(f"VARIABLE: `{var}` = `{value}`")

def values_to_dropdown_options(values: list[str]) -> list[dict]:
    """Convert a list of columns to a list of options for a dropdown."""
    return [{'label': value, 'value': value} for value in values]


def create_control(
        label: str,
        id: str,  # noqa: A002
        component: html.Div,
        hidden: bool = False) -> html.Div:
    """Create a generic control with a given component (e.g. dropdown)."""
    style = {'display': 'none'} if hidden else {}
    return html.Div(
        id=f'{id}_div',
        className='graph_options',
        style=style,
        children=[
            html.Label(
                f"{label}:",
                className='graph_options_label',
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
        value: tuple[int] | tuple[float],
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
        className='graph_options',
        style=style,
        children=[
            html.Label(
                f"{label}:",
                className='graph_options_label',
            ),
            html.Div(className='min_max_div', children=[
                html.Label("Min:"),
                daq.NumericInput(
                    id=component_id_min,
                    min=value[0],
                    max=value[1],
                    value=value[0],
                ),
                html.Label("Max:"),
                daq.NumericInput(
                    id=component_id_max,
                    min=value[0],
                    max=value[1],
                    value=value[1],
                ),
            ]),
        ],
    )
