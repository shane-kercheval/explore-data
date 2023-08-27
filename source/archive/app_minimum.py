"""Dash app entry point."""
import base64
import io
from dash import Dash, html, dash_table, dcc, Output, Input, State, callback_context
from dash.dependencies import ALL
import plotly.express as px
import pandas as pd
import helpsk.pandas as hp
import dash_bootstrap_components as dbc
from source.library.dash_helpers import (
    log,
    log_error,
    log_function,
    log_variable,
    values_to_dropdown_options,
    create_dropdown_control,
    create_slider_control,
    create_min_max_control,
    create_date_range_control,
    CLASS__GRAPH_PANEL_SECTION,
    create_random_dataframe,
)
from source.library.utilities import to_date, series_to_datetime

GOLDEN_RATIO = 1.618


app = Dash(
    __name__,
    title="Data Explorer",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        # 'https://codepen.io/chriddyp/pen/bWLwgP.css',
    ],
)
app.layout = dbc.Container(className="app-container", fluid=True, style={"max-width": "99%"}, children=[  # noqa
    dcc.Store(id='original_data'),

    html.Br(),
    html.Button(
        'Generate',
        id='load_random_data_button',
        n_clicks=0,
        style={'width': '200px', 'margin': '0 8px 0 0'},
    ),
    create_dropdown_control(
        label="X variable",
        id="x_variable",
        options=['Integers', 'Floats', 'Strings', 'Dates'],
        placeholder="Select a variable",
    ),
    create_dropdown_control(
        label="Y variable",
        id="y_variable",
        placeholder="Select a variable",
    ),
    create_dropdown_control(
        label="Facet variable",
        id="facet_variable",
        placeholder="Select a variable",
        hidden=True,
    ),
    dcc.Loading([

    dcc.Graph(
        id='primary-graph',
        config={'staticPlot': False, 'displayModeBar': True},
        # 3/12 because the sidebar is 3/12 of the width
        style={'width': '100%', 'height': f'{(1-(3/12)) / GOLDEN_RATIO * 100: .1f}vw'},  # noqa
    ),
    ]),
])


@app.callback(
    Output('x_variable_dropdown', 'options'),
    Output('y_variable_dropdown', 'options'),
    Output('original_data', 'data'),
    Output('primary-graph', 'figure', allow_duplicate=True),
    Input('load_random_data_button', 'n_clicks'),
    prevent_initial_call=True,
)
def load_data(load_random_data_button: int) -> tuple:
    """Triggered when the user clicks on the Load button."""
    log_function('load_data')
    x_variable_dropdown = []
    y_variable_dropdown = []
    filter_columns_dropdown = []
    filter_columns_cache = None
    dynamic_filter_controls = None
    primary_graph = {}
    table_visualize = None
    table_uploaded_data = None
    numeric_summary = None
    non_numeric_summary = None
    original_data = None
    filtered_data = None
    all_columns = None
    numeric_columns = None
    non_numeric_columns = None
    date_columns = None
    categorical_columns = None
    string_columns = None

    if callback_context.triggered:
        triggered = callback_context.triggered[0]['prop_id']
        log_variable('triggered', triggered)
        if triggered == 'load_random_data_button.n_clicks':
            data = create_random_dataframe(num_rows=100_000, sporadic_missing=False)
            original_data = data
            x_variable_dropdown = values_to_dropdown_options(original_data.columns.tolist())
            y_variable_dropdown = values_to_dropdown_options(original_data.columns.tolist())
            original_data = original_data.to_dict('records')
    log("loaded data")
    return (
        x_variable_dropdown,
        y_variable_dropdown,
        original_data,
        primary_graph,
    )



@app.callback(
    Output('primary-graph', 'figure'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    State('original_data', 'data'),
    prevent_initial_call=True,
)
def update_graph(
            x_variable: str,
            y_variable: str,
            data: dict,
        ) -> dict:
    """Triggered when the user selects columns from the dropdown."""
    log_function('update_graph')
    log_variable('x_variable', x_variable)
    log_variable('y_variable', y_variable)
    fig = {}
    if (
        (x_variable or y_variable)
        and data
        and (not x_variable or x_variable in data[0])
        and (not y_variable or y_variable in data[0])
        ):

        graph_types_lookup = {
            'histogram': px.histogram,
            'scatter': px.scatter,
            'line': px.line,
            'bar': px.bar,
            'box': px.box,
        }

        fig = px.histogram(
            data,
            x=x_variable,
            # y=y_variable,
        )
    return fig




if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)

