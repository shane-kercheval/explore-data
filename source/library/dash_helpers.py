"""Helper functions for creating dash components."""
from dash import html, dcc


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
            min=min,
            max=max,
            step=step,
            # marks={i: str(i) for i in np.arange(min, max + step, step)},
            value=value,
            id=component_id,
        ),
    )

