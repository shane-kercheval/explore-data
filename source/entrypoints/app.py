"""Dash app entry point."""
import math
import os
from dotenv import load_dotenv
import base64
import io
from dash import dash_table, callback_context
from dash.dependencies import ALL
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import helpsk.pandas as hp
import dash_bootstrap_components as dbc
from source.library.dash_ui import (
    create_dropdown_control,
    create_slider_control,
    create_min_max_control,
    create_date_range_control,
    CLASS__GRAPH_PANEL_SECTION,
)
from source.library.dash_utilities import (
    log,
    log_error,
    log_function,
    log_variable,
    filter_data_from_ui_control,
)
from source.library.utilities import (
    series_to_datetime,
    create_random_dataframe,
)

from dash_extensions.enrich import DashProxy, Output, Input, State, Serverside, html, dcc, \
    ServersideOutputTransform



load_dotenv()
HOST = os.getenv('HOST')
DEBUG = os.getenv('DEBUG').lower() == 'true'
PORT = os.getenv('PORT')
GOLDEN_RATIO = 1.618

app = DashProxy(
    __name__,
    title="Data Explorer",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        # 'https://codepen.io/chriddyp/pen/bWLwgP.css',
    ],
    transforms=[ServersideOutputTransform()],
)

app.layout = dbc.Container(className="app-container", fluid=True, style={"max-width": "99%"}, children=[  # noqa
    dcc.Store(id='original_data'),
    dcc.Store(id='filtered_data'),
    dcc.Store(id='filter_columns_cache'),
    dcc.Store(id='all_columns'),
    dcc.Store(id='numeric_columns'),
    dcc.Store(id='non_numeric_columns'),
    dcc.Store(id='date_columns'),
    dcc.Store(id='categorical_columns'),
    dcc.Store(id='string_columns'),
    dcc.Store(id='boolean_columns'),
    dbc.Tabs([
        dbc.Tab(label="Load Data", children=[
            dcc.Loading(type="default", children=[
            html.Br(),
            dbc.Row([
                dbc.Tabs([
                    dbc.Tab(label="Generate Random Dataframe", children=[
                        html.Br(),
                        html.Button(
                            'Generate',
                            id='load_random_data_button',
                            n_clicks=0,
                            style={'width': '200px', 'margin': '0 8px 0 0'},
                        ),
                    ]),
                    dbc.Tab(label="Load .csv from URL", children=[
                        html.Br(),
                        html.Button(
                            'Load csv from URL',
                            id='load_from_url_button',
                            n_clicks=0,
                            style={'width': '200px', 'margin': '0 8px 0 0'},
                        ),
                        dcc.Input(
                            id='load_from_url',
                            type='text',
                            placeholder='Enter CSV URL',
                            # value='https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv',
                            value='https://raw.githubusercontent.com/fivethirtyeight/data/master/bechdel/movies.csv',
                            style={
                                'width': '600px',
                            },
                        ),
                    ]),
                    dbc.Tab(label="Load .csv or .pkl from file", children=[
                        html.Br(),
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop .csv or .pkl or ',
                                html.A('Select Files', style={'color': 'blue'}),
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'align-items': 'center',
                                # 'margin': '0px',
                            },
                            multiple=False,
                        ),
                    ]),
                ]),
            ]),
            html.Br(),
            dbc.Row(children=[
                html.Hr(),
                html.Div(id='table_uploaded_data'),
            ]),
            ]),
        ]),
        dbc.Tab(label="Visualize", children=[
            dbc.Row([
                dbc.Col(width=3, children=[
                    dbc.Card(style={'margin': '10px 0 10px 0'}, children=[
                        dbc.CardHeader(
                            dbc.Button(
                                "Variables",
                                id="panel-variables-toggle",
                                className="panel_toggle_button",
                            ),
                        ),
                        dbc.Collapse(id="collapse-variables", is_open=True, children=[
                            dbc.CardBody([
                                create_dropdown_control(
                                    label="X variable",
                                    id="x_variable",
                                    placeholder="Select a variable",
                                ),
                                create_dropdown_control(
                                    label="Y variable",
                                    id="y_variable",
                                    placeholder="Select a variable",
                                ),
                                create_dropdown_control(
                                    label="Color variable",
                                    id="color_variable",
                                    placeholder="Select a variable",
                                    hidden=True,
                                ),
                                create_dropdown_control(
                                    label="Size variable",
                                    id="size_variable",
                                    placeholder="Select a variable",
                                    hidden=True,
                                ),
                                create_dropdown_control(
                                    label="Facet variable",
                                    id="facet_variable",
                                    placeholder="Select a variable",
                                    hidden=True,
                                ),
                                dbc.Button(
                                    "Clear",
                                    id="clear-settings-button",
                                    style={'margin': '0 20px 20px 0'},
                                ),
                            ]),
                        ]),
                    ]),
                    dbc.Card(style={'margin': '10px 0 10px 0'}, children=[
                        dbc.CardHeader(
                            dbc.Button(
                                "Filter",
                                id="panel-filter-toggle",
                                className="panel_toggle_button",
                            ),
                        ),
                        dbc.Collapse(id="collapse-filter", is_open=False, children=[
                            dbc.CardBody([
                                dbc.Button(
                                    "Apply",
                                    id="filter-apply-button",
                                    style={'margin': '0 20px 20px 0'},
                                ),
                                create_dropdown_control(
                                    label="Variables",
                                    id="filter_columns",
                                    multi=True,
                                ),
                                html.Div(
                                    id='dynamic-filter-controls',
                                    style={'margin': '15px 0 10px 0'},
                                    className=CLASS__GRAPH_PANEL_SECTION,
                                ),
                            ]),
                        ]),
                    ]),
                    dbc.Card(style={'margin': '10px 0 10px 0'}, children=[
                        dbc.CardHeader(
                            dbc.Button(
                                "Graph Options",
                                id='panel-graph-options-toggle',
                                className='panel_toggle_button',
                            ),
                        ),
                        dbc.Collapse(id="collapse-graph-options", is_open=True, children=[
                            dbc.CardBody([
                                create_dropdown_control(
                                    label="Graph Type",
                                    id='graph_type',
                                    hidden=False,
                                    multi=False,
                                    clearable=False,
                                    options=[
                                        {'label': 'Scatter', 'value': 'scatter'},
                                        {'label': 'Histogram', 'value': 'histogram'},
                                        {'label': 'Box', 'value': 'box'},
                                        {'label': 'Line', 'value': 'line'},
                                        {'label': 'Bar', 'value': 'bar'},
                                    ],
                                    value='scatter',
                                ),
                                create_slider_control(
                                    label="# of Bins",
                                    id="n_bins",
                                    min=20,
                                    max=100,
                                    step=20,
                                    value=40,
                                ),
                                create_slider_control(
                                    label="Top N Categories",
                                    id="top_n_categories",
                                    value=6,
                                    step=1,
                                    min=0,
                                    max=10,
                                    marks={
                                        0: 'None',
                                        1: '1',
                                        2: '2',
                                        3: '3',
                                        4: '4',
                                        5: '5',
                                        6: '10',
                                        7: '15',
                                        8: '20',
                                        9: '40',
                                        10: '50',
                                    },
                                ),
                                create_slider_control(
                                    label="Opacity",
                                    id="opacity",
                                    min=0,
                                    max=1,
                                    step=0.1,
                                    value=0.5,
                                ),
                            ]),
                        ]),
                    ]),
                    dbc.Card(style={'margin': '10px 0 10px 0'}, children=[
                        dbc.CardHeader(
                            dbc.Button(
                                "Other Options",
                                id="panel-other-options-toggle",
                                className="panel_toggle_button",
                            ),
                        ),
                        dbc.Collapse(id="collapse-other-options", is_open=True, children=[
                            dbc.CardBody([
                                html.Div(
                                    id='title_div',
                                    className=CLASS__GRAPH_PANEL_SECTION,
                                    # style={'display': 'none'},
                                    children=[
                                        html.Label(
                                            "Title:",
                                            className=CLASS__GRAPH_PANEL_SECTION + '_label',
                                        ),
                                        dcc.Input(
                                            id='title_textbox',
                                            # multi=False,
                                            value=None,
                                            placeholder="Title",
                                            style={'width': '100%'},
                                        ),
                                        html.Br(),
                                ]),
                            ]),
                        ]),
                    ]),
                ]),
                dbc.Col(width=9, children=[
                    dcc.Loading(type="default", children=[
                        dcc.Graph(
                            id='visualize_graph',
                            config={'staticPlot': False, 'displayModeBar': True},
                            # 3/12 because the sidebar is 3/12 of the width
                            style={'width': '100%', 'height': f'{(1-(3/12)) / GOLDEN_RATIO * 100: .1f}vw'},  # noqa
                        ),
                        html.Hr(),
                        dbc.Tabs([
                            dbc.Tab(label="Filters", children=[
                                html.Br(),
                                dcc.Markdown(id="visualize_filter_info", children="No filters applied."),  # noqa
                            ]),
                            dbc.Tab(label="Code", children=[
                                html.Br(),
                                dcc.Markdown(id="visualize_filter_code", children="No filters applied."),  # noqa
                            ]),
                            dbc.Tab(label="Data", children=[
                                dcc.Markdown("#### Sample of Uploaded Data (first 500 rows):"),
                                dcc.Loading(type="default", children=[
                                    dash_table.DataTable(
                                        id='visualize_table',
                                        page_size=20,
                                        style_header={
                                            'fontWeight': 'bold',
                                        },
                                    ),
                                ]),
                            ]),
                        ]),
                    ]),
                ]),
            ]),
        ]),
        dbc.Tab(label="Numeric Summary", children=[
            html.Br(),
            dash_table.DataTable(
                id='numeric_summary_table',
                page_size=30,
                style_header={
                    'fontWeight': 'bold',
                },
                style_data_conditional=[
                    {
                       'if': {'column_id': 'Column Name'},
                        'fontWeight': 'bold',
                    },
                    {
                        'if': {
                            'filter_query': '{# of Nulls} > 0',
                            'column_id': '# of Nulls',
                        },
                        'backgroundColor': 'tomato',
                        'color': 'white',
                    },
                    {
                        'if': {
                            'filter_query': '{% Nulls} > 0',
                            'column_id': '% Nulls',
                        },
                        'backgroundColor': 'tomato',
                        'color': 'white',
                    },
                    {
                        'if': {
                            'filter_query': '{# of Zeros} > 0',
                            'column_id': '# of Zeros',
                        },
                        'backgroundColor': 'orange',
                        'color': 'white',
                    },
                    {
                        'if': {
                            'filter_query': '{% Zeros} > 0',
                            'column_id': '% Zeros',
                        },
                        'backgroundColor': 'orange',
                        'color': 'white',
                    },
                ],
            ),
        ]),
        dbc.Tab(label="Non-Numeric Summary", children=[
            html.Br(),
            dash_table.DataTable(
                id='non_numeric_summary_table',
                page_size=30,
                style_header={
                    'fontWeight': 'bold',
                },
                style_data_conditional=[
                    {
                       'if': {'column_id': 'Column Name'},
                        'fontWeight': 'bold',
                    },
                    {
                        'if': {
                            'filter_query': '{# of Nulls} > 0',
                            'column_id': '# of Nulls',
                        },
                        'backgroundColor': 'tomato',
                        'color': 'white',
                    },
                    {
                        'if': {
                            'filter_query': '{% Nulls} > 0',
                            'column_id': '% Nulls',
                        },
                        'backgroundColor': 'tomato',
                        'color': 'white',
                    },
                ],
            ),
        ]),
    ]),
])


@app.callback(
    Output('x_variable_dropdown', 'options'),
    Output('y_variable_dropdown', 'options'),
    Output('filter_columns_dropdown', 'options'),
    Output('filter_columns_cache', 'data', allow_duplicate=True),
    Output('dynamic-filter-controls', 'children', allow_duplicate=True),
    Output('visualize_graph', 'figure', allow_duplicate=True),
    Output('visualize_table', 'data', allow_duplicate=True),
    Output('table_uploaded_data', 'children'),
    Output('numeric_summary_table', 'data'),
    Output('non_numeric_summary_table', 'data'),
    Output('original_data', 'data'),
    Output('filtered_data', 'data', allow_duplicate=True),
    Output('all_columns', 'data'),
    Output('numeric_columns', 'data'),
    Output('non_numeric_columns', 'data'),
    Output('date_columns', 'data'),
    Output('categorical_columns', 'data'),
    Output('string_columns', 'data'),
    Output('boolean_columns', 'data'),
    Input('load_random_data_button', 'n_clicks'),
    Input('load_from_url_button', 'n_clicks'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('load_from_url', 'value'),
    prevent_initial_call=True,
)
def load_data(  # noqa
        load_random_data_button: int,
        load_from_url_button: int,
        upload_data_contents: str,
        upload_data_filename: str,
        load_from_url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    log_function('load_data')
    x_variable_dropdown = []
    y_variable_dropdown = []
    filter_columns_dropdown = []
    filter_columns_cache = None
    dynamic_filter_controls = None
    primary_graph = {}
    visualize_table = None
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
    boolean_columns = None

    if callback_context.triggered:
        triggered = callback_context.triggered[0]['prop_id']
        log_variable('triggered', triggered)
        # ctx_msg = json.dumps({
        #     'states': callback_context.states,
        #     'triggered': callback_context.triggered,
        #     'triggered2': callback_context.triggered[0]['prop_id'],
        #     'inputs': callback_context.inputs,
        # }, indent=2)
        # log_var('ctx_msg', ctx_msg)

        if triggered == 'upload-data.contents':
            log_variable('load_random_data_button', load_random_data_button)
            log_variable('load_from_url_button', load_from_url_button)
            log_variable('upload_data_filename', upload_data_filename)
            _, content_string = upload_data_contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                if '.pkl' in upload_data_filename:
                    log("loading from .pkl")
                    data = pd.read_pickle(io.BytesIO( base64.b64decode(content_string)))
                if '.csv' in upload_data_filename:
                    log("loading from .csv")
                    # Assume that the user uploaded a CSV file
                    data = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                elif 'xls' in upload_data_filename:
                    log("loading from .xls")
                    # Assume that the user uploaded an excel file
                    data = pd.read_excel(io.BytesIO(decoded))
            except Exception as e:
                log(e)
                return html.Div([
                    'There was an error processing this file.',
                ])
        elif triggered == 'load_from_url_button.n_clicks' and load_from_url:
            log("Loading from CSV URL")
            data = pd.read_csv(load_from_url)
        elif triggered == 'load_random_data_button.n_clicks':
            log("Loading DataFrame with random data")
            data = create_random_dataframe(num_rows=10_000, sporadic_missing=True)
            log(f"Loaded data w/ {data.shape[0]:,} rows and {data.shape[1]:,} columns")
        else:
            raise ValueError(f"Unknown trigger: {triggered}")

        # i can't convert columns to datetime here because the dataframe gets converted to a dict
        # and loses the converted datetime dtypes
        # data, converted_columns = convert_columns_to_datetime(data)
        # log_variable('converted_columns', converted_columns)
        all_columns = data.columns.tolist()
        numeric_columns = hp.get_numeric_columns(data)
        non_numeric_columns = hp.get_non_numeric_columns(data)
        date_columns = hp.get_date_columns(data)
        categorical_columns = hp.get_categorical_columns(data)
        string_columns = hp.get_string_columns(data)
        boolean_columns = [x for x in all_columns if hp.is_series_bool(data[x])]
        log_variable('all_columns', all_columns)
        log_variable('numeric_columns', numeric_columns)
        log_variable('non_numeric_columns', non_numeric_columns)
        log_variable('date_columns', date_columns)
        log_variable('categorical_columns', categorical_columns)
        log_variable('string_columns', string_columns)
        log_variable('boolean_columns', boolean_columns)

        log('creating numeric summary')
        numeric_summary = hp.numeric_summary(data, return_style=False)
        if numeric_summary is not None and len(numeric_summary) > 0:
            numeric_summary = numeric_summary.\
                reset_index().\
                rename(columns={'index': 'Column Name'}).\
                to_dict('records')
        else:
            numeric_summary = None

        log('creating non-numeric summary')
        non_numeric_summary = hp.non_numeric_summary(data, return_style=False)
        if non_numeric_summary is not None and len(non_numeric_summary) > 0:
            non_numeric_summary = non_numeric_summary.\
                reset_index().\
                rename(columns={'index': 'Column Name'}).\
                to_dict('records')
        else:
            non_numeric_summary = None

        options = all_columns
        x_variable_dropdown = options
        y_variable_dropdown = options
        filter_columns_dropdown = options
        table_uploaded_data = [
            dcc.Markdown("#### Sample of Uploaded Data (first 500 rows):"),
            dash_table.DataTable(
                id='adsf',
                data=data.iloc[0:500].to_dict('records'),
                page_size=20,
                style_header={
                    'fontWeight': 'bold',
                },
            ),
        ]
        original_data = data
        filtered_data = data.copy()

    return (
        x_variable_dropdown,
        y_variable_dropdown,
        filter_columns_dropdown,
        filter_columns_cache,
        dynamic_filter_controls,
        primary_graph,
        visualize_table,
        table_uploaded_data,
        numeric_summary,
        non_numeric_summary,
        Serverside(original_data),
        Serverside(filtered_data),
        all_columns,
        numeric_columns,
        non_numeric_columns,
        date_columns,
        categorical_columns,
        string_columns,
        boolean_columns,
    )


@app.callback(
    Output('filtered_data', 'data'),
    Output('visualize_filter_info', 'children'),
    Output('visualize_filter_code', 'children'),
    Input('filter-apply-button', 'n_clicks'),
    State('filter_columns_dropdown', 'value'),
    State('filter_columns_cache', 'data'),
    State('original_data', 'data'),
    prevent_initial_call=True,
)
def filter_data(
        n_clicks: int,  # noqa: ARG001
        selected_filter_columns: list[str],
        filter_columns_cache: dict,
        original_data: pd.DataFrame,
        ) -> dict:
    """Filter the data based on the user's selections."""
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        selected_columns=selected_filter_columns,
        cache=filter_columns_cache,
        data=original_data,
    )
    return Serverside(filtered_data), markdown_text, code


@app.callback(
    Output('visualize_graph', 'figure'),
    Output('visualize_table', 'data'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('color_variable_dropdown', 'value'),
    Input('size_variable_dropdown', 'value'),
    Input('facet_variable_dropdown', 'value'),
    Input('graph_type_dropdown', 'value'),
    Input('n_bins_slider', 'value'),
    Input('opacity_slider', 'value'),
    Input('title_textbox', 'value'),
    Input('filtered_data', 'data'),
    State('numeric_columns', 'data'),
    State('non_numeric_columns', 'data'),
    State('date_columns', 'data'),
    State('categorical_columns', 'data'),
    State('string_columns', 'data'),
    State('boolean_columns', 'data'),
    prevent_initial_call=True,
)
def update_graph(
            x_variable: str,
            y_variable: str,
            color_variable: str,
            size_variable: str,
            facet_variable: str,
            graph_type: str,
            n_bins: int,
            opacity: float,
            title_textbox: str,
            data: pd.DataFrame,
            numeric_columns: list[str],
            non_numeric_columns: list[str],
            date_columns: list[str],
            categorical_columns: list[str],
            string_columns: list[str],
            boolean_columns: list[str],
        ) -> tuple[go.Figure, dict]:
    """
    Triggered when the user selects columns from the dropdown.

    This function should *not* modify the data. It should only return a figure.
    """
    log_function('update_graph')
    log_variable('x_variable', x_variable)
    log_variable('y_variable', y_variable)
    log_variable('color_variable', color_variable)
    log_variable('size_variable', size_variable)
    log_variable('facet_variable', facet_variable)
    log_variable('n_bins', n_bins)
    log_variable('opacity', opacity)
    log_variable('graph_type', graph_type)
    log_variable('type(n_bins)', type(n_bins))
    # log_variable('type(data)', type(data))
    # log_variable('data', data)
    fig = {}
    graph_data = pd.DataFrame()
    if (
        (x_variable or y_variable)
        and data is not None and len(data) > 0
        and graph_type
        and (not x_variable or x_variable in data.columns)
        and (not y_variable or y_variable in data.columns)
        and (not color_variable or color_variable in data.columns)
        and (not size_variable or size_variable in data.columns)
        and (not facet_variable or facet_variable in data.columns)
        ):
        columns = [x_variable, y_variable, color_variable, size_variable, facet_variable]
        columns = [col for col in columns if col is not None]
        columns = list(set(columns))
        graph_data = data[columns].copy()

        for column in columns:
            if column in string_columns or column in categorical_columns or column in boolean_columns:  # noqa
                log(f"filling na for {column}")
                graph_data[column] = hp.fill_na(
                    series=graph_data[column],
                    missing_value_replacement='<Missing>',
                )

        log("creating fig")
        if graph_type == 'scatter':
            fig = px.scatter(
                graph_data,
                x=x_variable,
                y=y_variable,
                color=color_variable,
                size=size_variable,
                opacity=opacity,
                facet_col=facet_variable,
                facet_col_wrap=4,
                title=title_textbox,
            )
        elif graph_type == 'histogram':
            fig = px.histogram(
                graph_data,
                x=x_variable,
                y=y_variable,
                color=color_variable,
                opacity=opacity,
                facet_col=facet_variable,
                facet_col_wrap=4,
                title=title_textbox,
                nbins=n_bins,
            )
        elif graph_type == 'box':
            fig = px.box(
                graph_data,
                x=x_variable,
                y=y_variable,
                color=color_variable,
                # opacity=opacity,
                facet_col=facet_variable,
                facet_col_wrap=4,
                title=title_textbox,
            )
        elif graph_type == 'bar':
            fig = px.bar(
                graph_data,
                x=x_variable,
                y=y_variable,
                color=color_variable,
                # opacity=opacity,
                facet_col=facet_variable,
                facet_col_wrap=4,
                title=title_textbox,
            )
        elif graph_type == 'line':
            fig = px.line(
                graph_data,
                x=x_variable,
                y=y_variable,
                color=color_variable,
                # opacity=opacity,
                facet_col=facet_variable,
                facet_col_wrap=4,
                title=title_textbox,
            )
        else:
            raise ValueError(f"Unknown graph type: {graph_type}")
    log("returning fig")
    return fig, graph_data.iloc[0:500].to_dict('records')


@app.callback(
    Output('facet_variable_div', 'style'),
    Output('facet_variable_dropdown', 'options'),
    Output('facet_variable_dropdown', 'value'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    State('facet_variable_dropdown', 'value'),
    State('non_numeric_columns', 'data'),
    prevent_initial_call=True,
)
def facet_variable_div(
        x_variable_dropdown: str,
        y_variable_dropdown: str,
        current_value: str,
        non_numeric_columns: dict) -> dict:
    """
    Triggered when the user selects columns (specified in Input fields in callback) from the
    dropdown.
    This function is used to show/hide the facet variable dropdown and to populate it with options.
    """
    log_function('facet_variable_div')
    if x_variable_dropdown or y_variable_dropdown:
        log("returning {display: block}")
        options = non_numeric_columns
        return {'display': 'block'}, options, current_value
    log("returning {display: none}")
    return  {'display': 'none'}, [], None


@app.callback(
    Output('color_variable_div', 'style'),
    Output('color_variable_dropdown', 'options'),
    Output('color_variable_dropdown', 'value'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    State('color_variable_dropdown', 'value'),
    State('all_columns', 'data'),
    prevent_initial_call=True,
)
def color_variable_div(
        x_variable_dropdown: str,
        y_variable_dropdown: str,
        current_value: str,
        all_columns: dict) -> dict:
    """
    Triggered when the user selects columns (specified in Input fields in callback) from the
    dropdown.
    This function is used to show/hide the color variable dropdown and to populate it with options.
    """
    log_function('color_variable_div')
    if x_variable_dropdown or y_variable_dropdown:
        log("returning {display: block}")
        options = all_columns
        return {'display': 'block'}, options, current_value
    log("returning {display: none}")
    return  {'display': 'none'}, [], None


@app.callback(
    Output('size_variable_div', 'style'),
    Output('size_variable_dropdown', 'options'),
    Output('size_variable_dropdown', 'value'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    State('size_variable_dropdown', 'value'),
    State('all_columns', 'data'),
    prevent_initial_call=True,
)
def size_variable_div(
        x_variable_dropdown: str,
        y_variable_dropdown: str,
        current_value: str,
        all_columns: dict) -> dict:
    """
    Triggered when the user selects columns (specified in Input fields in callback) from the
    dropdown.
    This function is used to show/hide the size variable dropdown and to populate it with options.
    """
    log_function('size_variable_div')
    if x_variable_dropdown or y_variable_dropdown:
        log("returning {display: block}")
        options = all_columns
        return {'display': 'block'}, options, current_value
    log("returning {display: none}")
    return  {'display': 'none'}, [], None


@app.callback(
    Output('x_variable_dropdown', 'value'),
    Output('y_variable_dropdown', 'value'),
    Input('clear-settings-button', 'n_clicks'),
    State('all_columns', 'data'),
    prevent_initial_call=True,
)
def clear_settings(n_clicks: int, all_columns: list[str]) -> str:
    """Triggered when the user clicks on the Clear button."""
    log_function('clear_settings')
    log_variable('n_clicks', n_clicks)
    log_variable('all_columns', all_columns)
    return None, None

@app.callback(
    Output("collapse-variables", "is_open"),
    Input("panel-variables-toggle", "n_clicks"),
    State("collapse-variables", "is_open"),
    prevent_initial_call=True,
)
def toggle_variables_panel(n: int, is_open: bool) -> bool:
    """Toggle the variables panel."""
    log_function('toggle_variables_panel')
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("collapse-filter", "is_open"),
    Input("panel-filter-toggle", "n_clicks"),
    State("collapse-filter", "is_open"),
    prevent_initial_call=True,
)
def toggle_filter_panel(n: int, is_open: bool) -> bool:
    """Toggle the filter panel."""
    log_function('toggle_filter_panel')
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("collapse-graph-options", "is_open"),
    Input("panel-graph-options-toggle", "n_clicks"),
    State("collapse-graph-options", "is_open"),
    prevent_initial_call=True,
)
def toggle_graph_options_panel(n: int, is_open: bool) -> bool:
    """Toggle the graph-options panel."""
    log_function('toggle_graph_options_panel')
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("collapse-other-options", "is_open"),
    Input("panel-other-options-toggle", "n_clicks"),
    State("collapse-other-options", "is_open"),
    prevent_initial_call=True,
)
def toggle_other_options_panel(n: int, is_open: bool) -> bool:
    """Toggle the other-options panel."""
    log_function('toggle_other_options_panel')
    if n:
        return not is_open
    return is_open


@app.callback(
    Output('dynamic-filter-controls', 'children'),
    Input('filter_columns_dropdown', 'value'),
    State('filter_columns_cache', 'data'),
    State('non_numeric_columns', 'data'),
    State('numeric_columns', 'data'),
    State('original_data', 'data'),

    prevent_initial_call=True,
)
def update_filter_controls(
        selected_filter_columns: list[str],
        filter_columns_cache: dict,
        non_numeric_columns: list[str],
        numeric_columns: list[str],
        data: dict) -> list[html.Div]:
    """
    Triggered when the user selects columns from the filter dropdown.

    If the user selects a column and adds a value, and then selects another column, the value from
    the original column will be removed. This is because all of the controls are recreated. So we
    need to cache the values of the controls in the filter_columns_cache.
    """
    log_function('update_filter_controls')
    log_variable('selected_filter_columns', selected_filter_columns)
    log_variable('filter_columns_cache', filter_columns_cache)
    log_variable('non_numeric_columns', non_numeric_columns)
    log_variable('numeric_columns', numeric_columns)

    components = []
    if selected_filter_columns and data is not None and len(data) > 0:
        # data = pd.DataFrame(data)
        for column in selected_filter_columns:
            series, _ = series_to_datetime(data[column])

            log(f"Creating controls for `{column}`")
            value = []
            if filter_columns_cache and column in filter_columns_cache:
                value = filter_columns_cache[column]
                log(f"found `{column}` in filter_columns_cache with value `{value}`")

            # check if column is datetime
            # if data[column].dtype == 'datetime64[ns]':
            log_variable('series.dtype', series.dtype)
            if pd.api.types.is_datetime64_any_dtype(series):
                log("Creating date range control")
                components.append(create_date_range_control(
                    label=column,
                    id=f"filter_control_{column}",
                    min_value=value[0] if value else series.min(),
                    max_value=value[1] if value else series.max(),
                    component_id={"type": "filter-control-date-range", "index": column},
                ))
            elif hp.is_series_bool(series):
                log("Creating dropdown control")
                options = ['True', 'False']
                if series.isna().any():
                    options.append('<Missing>')
                    multi = True
                else:
                    multi = False
                    if value:
                        value = value[0]

                components.append(create_dropdown_control(
                    label=column,
                    id=f"filter_control_{column}",
                    value=value or 'True',
                    multi=multi,
                    options=options,
                    component_id={"type": "filter-control-dropdown", "index": column},
                ))
            elif column in non_numeric_columns:
                log("Creating dropdown control")
                log_variable('series.unique()', series.unique())
                options = sorted(series.dropna().unique().tolist())
                if series.isna().any():
                    options.append('<Missing>')
                components.append(create_dropdown_control(
                    label=column,
                    id=f"filter_control_{column}",
                    value=value,
                    multi=True,
                    options=options,
                    # options=values_to_dropdown_options(series.unique()),
                    component_id={"type": "filter-control-dropdown", "index": column},
                ))
            elif column in numeric_columns:
                log("Creating min/max control")
                components.append(create_min_max_control(
                    label=column,
                    id=f"filter_control_{column}",
                    min_value=value[0] if value else round(series.min()),
                    max_value=value[1] if value else math.ceil(series.max()),
                    component_id={"type": "filter-control-min-max", "index": column},
                ))
            else:
                log_error(f"Unknown column type: {column}")
                raise ValueError(f"Unknown column type: {column}")

    log_variable('# of components', len(components))
    return components


@app.callback(
    Output('filter_columns_cache', 'data'),
    Input({'type': 'filter-control-date-range', 'index': ALL}, 'id'),
    Input({'type': 'filter-control-date-range', 'index': ALL}, 'start_date'),
    Input({'type': 'filter-control-date-range', 'index': ALL}, 'end_date'),
    Input({'type': 'filter-control-dropdown', 'index': ALL}, 'id'),
    Input({'type': 'filter-control-dropdown', 'index': ALL}, 'value'),
    Input({'type': 'filter-control-min-max__min', 'index': ALL}, 'id'),
    Input({'type': 'filter-control-min-max__min', 'index': ALL}, 'value'),
    Input({'type': 'filter-control-min-max__max', 'index': ALL}, 'id'),
    Input({'type': 'filter-control-min-max__max', 'index': ALL}, 'value'),
    State('filter_columns_dropdown', 'value'),
    State('filter_columns_cache', 'data'),
    prevent_initial_call=True,
)
def cache_filter_columns(  # noqa: PLR0912
        date_range_ids: list[dict],
        date_range_start_date: list[list],
        date_range_end_date: list[list],
        dropdown_ids: list[dict],
        dropdown_values: list[list],
        minmax_min_ids: list[dict],
        minmax_min_values: list[list],
        minmax_max_ids: list[dict],
        minmax_max_values: list[list],
        selected_filter_columns: list[str],
        filter_columns_cache: dict,
        ) -> dict:
    """
    Cache the values from the drop and slider controls. This is used to recreate the controls when
    the user selects a new variable to filter on, which triggers the recreation of all controls.
    This is also used to filter the data.
    """
    log_function('cache_filter_columns')
    log_variable('selected_filter_columns', selected_filter_columns)
    log_variable('filter_columns_cache', filter_columns_cache)
    log_variable('date_range_start_date', date_range_start_date)
    log_variable('date_range_end_date', date_range_end_date)
    log_variable('date_range_ids', date_range_ids)
    log_variable('dropdown_values', dropdown_values)
    log_variable('dropdown_ids', dropdown_ids)
    log_variable('minmax_min_values', minmax_min_values)
    log_variable('minmax_min_ids', minmax_min_ids)
    log_variable('minmax_max_values', minmax_max_values)
    log_variable('minmax_max_ids', minmax_max_ids)

    # cache the values from the dropdown and slider controls
    if filter_columns_cache is None:
        filter_columns_cache = {}
    # NOTE: I can't seem to remove values from the cache. I get an error complaining that the value
    # has been modified
    # else:
    #     filter_columns_cache = filter_columns_cache.copy()
    #     for column in filter_columns_cache:
    #         if column not in selected_filter_columns:
    #             log(f"removing {column} from filter_columns_cache")
    #             filter_columns_cache.pop(column)

    for column in selected_filter_columns:
        log(f"caching column: `{column}`")
        if column in [item['index'] for item in date_range_ids]:
            log(f"found `{column}` in date_range_ids")
            for id, start_date, end_date in zip(date_range_ids, date_range_start_date, date_range_end_date):  # noqa
                if id['index'] == column:
                    values = (start_date, end_date)
                    log(f"caching `{column}` with `{values}`")
                    filter_columns_cache[column] = values
                    break
        elif column in [item['index'] for item in dropdown_ids]:
            log(f"found `{column}` in dropdown_ids")
            for id, value in zip(dropdown_ids, dropdown_values):  # noqa
                if id['index'] == column:
                    if not isinstance(value, list):
                        value = [value]  # noqa
                    log(f"caching `{column}` with `{value}`")
                    filter_columns_cache[column] = value
                    break
        elif column in [item['index'] for item in minmax_min_ids]:
            log(f"found `{column}` in minmax_min_ids")
            for id, min_value, max_value in zip(minmax_min_ids, minmax_min_values, minmax_max_values):  # noqa
                if id['index'] == column:
                    values = (min_value, max_value)
                    log(f"caching `{column}` with `{values}`")
                    filter_columns_cache[column] = values
                    break
        else:
            log_error(f"Unknown column type: {column}")
            raise ValueError(f"Unknown column type: {column}")

    log(f"filter_columns_cache: {filter_columns_cache}")
    return filter_columns_cache


if __name__ == '__main__':
    app.run_server(host=HOST, debug=DEBUG, port=PORT)

