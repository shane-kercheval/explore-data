"""Dash app entry point."""
import math
import os
from dotenv import load_dotenv
import base64
import io
import yaml
from dash import ctx, callback_context, dash_table
from dash.dependencies import ALL
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import helpsk.pandas as hp
import dash_bootstrap_components as dbc
from source.library.dash_ui import (
    create_dropdown_control,
    create_checklist_control,
    create_input_control,
    create_slider_control,
    create_min_max_control,
    create_date_range_control,
    CLASS__GRAPH_PANEL_SECTION,
)
from source.library.dash_utilities import (
    filter_data_from_ui_control,
    get_variable_type,
    get_graph_config,
    log,
    log_error,
    log_function,
    log_variable,
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
top_n_categories_lookup = {
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
}
with open(os.path.join(os.getenv('PROJECT_PATH'), 'source/config/graphing_configurations.yml')) as f:  # noqa
    GRAPH_CONFIGS = yaml.safe_load(f)


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
    dcc.Store(id='category_orders_cache', data={}),
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
                            value='https://raw.githubusercontent.com/shane-kercheval/shiny-explore-dataset/master/shiny-explore-dataset/example_datasets/credit.csv',
                            # value='https://raw.githubusercontent.com/fivethirtyeight/data/master/bechdel/movies.csv',
                            # value='https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv',
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
                                dbc.Button(
                                    "Swap X & Y",
                                    id="swap-x-y-button",
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
                        dbc.Collapse(id='collapse-graph-options', is_open=True, children=[
                            dbc.CardBody([
                                create_dropdown_control(
                                    label="Graph Type",
                                    id='graph_type',
                                    hidden=False,
                                    multi=False,
                                    clearable=False,
                                    placeholder="Select a variable above.",
                                ),
                                # One of 'group', 'overlay' or 'relative'
                                # In 'relative' mode, bars are stacked above zero for positive
                                # values and below zero for negative values.
                                # In 'overlay' mode, bars are drawn on top of one another.
                                # In 'group' mode, bars are placed beside each other.
                                create_dropdown_control(
                                    label="Bar Mode",
                                    id='bar_mode',
                                    hidden=True,
                                    multi=False,
                                    clearable=False,
                                    options=[
                                        {'label': 'Stacked', 'value': 'relative'},
                                        {'label': 'Side-by-Side', 'value': 'group'},
                                        {'label': 'Overlay', 'value': 'overlay'},
                                    ],
                                    value='relative',
                                ),
                                create_dropdown_control(
                                    label="Sort Categories By",
                                    id='sort_categories',
                                    hidden=True,
                                    multi=False,
                                    clearable=False,
                                    options=[
                                        {'label': 'Ascending  - Label', 'value': 'category ascending'},  # noqa
                                        {'label': 'Descending - Label', 'value': 'category descending'},  # noqa
                                        {'label': 'Ascending  - # of Records', 'value': 'total ascending'},  # noqa
                                        {'label': 'Descending - # of Records', 'value': 'total descending'},  # noqa
                                    ],
                                    value='category ascending',
                                ),
                                create_slider_control(
                                    label="Top N Categories",
                                    id='top_n_categories',
                                    hidden=True,
                                    value=6,
                                    step=1,
                                    min=0,
                                    max=10,
                                    marks=top_n_categories_lookup,
                                ),
                                create_slider_control(
                                    label="# of Bins",
                                    id='n_bins',
                                    hidden=True,
                                    min=20,
                                    max=100,
                                    step=20,
                                    value=40,
                                ),
                                create_slider_control(
                                    label="Opacity",
                                    id='opacity',
                                    hidden=True,
                                    min=0,
                                    max=1,
                                    step=0.1,
                                    value=0.6,
                                ),
                                create_checklist_control(
                                    id='log_x_y_axis',
                                    hidden=True,
                                    options=['Log X-Axis', 'Log Y-Axis'],
                                    value=[],
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
                                dbc.Button(
                                    "Apply",
                                    id="labels-apply-button",
                                    style={'margin': '0 20px 20px 0'},
                                ),
                                dbc.Button(
                                    "Clear",
                                    id="labels-clear-button",
                                    style={'margin': '0 20px 20px 0'},
                                ),
                                create_input_control(
                                    label="Title",
                                    id="title",
                                    placeholder="Title",
                                    hidden=False,
                                ),
                                create_input_control(
                                    label="Subtitle",
                                    id="subtitle",
                                    placeholder="Subtitle",
                                    hidden=False,
                                ),
                                create_input_control(
                                    label="X-Axis Label",
                                    id="x_axis_label",
                                    placeholder="X-axis label",
                                    hidden=True,
                                ),
                                create_input_control(
                                    label="Y-Axis Label",
                                    id="y_axis_label",
                                    placeholder="Y-axis label",
                                    hidden=True,
                                ),
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
                                dcc.Markdown(id="visualize_numeric_na_removal_markdown", children=""),  # noqa
                                dcc.Markdown(id="visualize_filter_info", children="No manual filters applied."),  # noqa
                                dcc.Markdown(children="\n\n---\nManual filters are applied first. Automatic filters are subsequently applied when visualizing numeric data."),  # noqa
                            ]),
                            dbc.Tab(label="Code", children=[
                                html.Br(),
                                dcc.Markdown(id="visualize_filter_code", children="Select columns to graph."),  # noqa
                            ]),
                            dbc.Tab(label="Data", children=[
                                html.Br(),
                                dcc.Markdown("##### Sample of Uploaded Data (first 500 rows):"),
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


def cache_category_order(cache: dict,
        variable: str,
        order_type: str,
        top_n_categories: int,
        data: pd.DataFrame,
    ) -> dict:
    """
    Updates and returns the cache containing the category order for a variable.

    The cache is dependant on top_n_categories because the order is different if the user selects
    1 category vs 10 categories and the <Other> category may or may not be included.

    The order is based on the order_type, which can be one of:
        - 'category ascending': Sort the categories in ascending order
        - 'category descending': Sort the categories in descending order
        - 'total ascending': Sort the categories by the total in ascending order
        - 'total descending': Sort the categories by the total in descending order
    """
    # TODO: test
    # can't use a tuple as the key because tuples aren't json serializable so dash complains
    key = f"{variable}__{order_type}__{top_n_categories}"
    if key in cache:
        return cache

    if 'category' in order_type:
        reverse = 'ascending' not in order_type
        categories = sorted(
            data[variable].unique().tolist(),
            reverse=reverse,
            key=lambda x: str(x),
        )
        cache[key] = categories
    elif 'total' in order_type:
        cache[key] = data[variable].\
            value_counts(sort=True, ascending='ascending' in order_type).\
            index.\
            tolist()
    else:
        raise ValueError(f"Unknown order_type: {order_type}")

    return cache


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
    State('filter_columns_cache', 'data'),
    State('original_data', 'data'),
    prevent_initial_call=True,
)
def filter_data(
        n_clicks: int,  # noqa: ARG001
        filter_columns_cache: dict,
        original_data: pd.DataFrame,
        ) -> dict:
    """Filter the data based on the user's selections."""
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filter_columns_cache,
        data=original_data,
    )
    return Serverside(filtered_data), markdown_text, code


@app.callback(
    Output('visualize_graph', 'figure'),
    Output('visualize_table', 'data'),
    Output('visualize_numeric_na_removal_markdown', 'children'),
    Output('category_orders_cache', 'data'),
    # color variable
    Output('color_variable_div', 'style'),
    Output('color_variable_dropdown', 'options'),
    Output('color_variable_dropdown', 'value'),
    # size variable
    Output('size_variable_div', 'style'),
    Output('size_variable_dropdown', 'options'),
    Output('size_variable_dropdown', 'value'),
    # facet variable
    Output('facet_variable_div', 'style'),
    Output('facet_variable_dropdown', 'options'),
    Output('facet_variable_dropdown', 'value'),
    Output('graph_type_dropdown', 'options'),
    Output('graph_type_dropdown', 'value'),

    # INPUTS
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    # color variable
    Input('color_variable_div', 'style'),
    Input('color_variable_dropdown', 'options'),
    Input('color_variable_dropdown', 'value'),
    # size variable
    Input('size_variable_div', 'style'),
    Input('size_variable_dropdown', 'options'),
    Input('size_variable_dropdown', 'value'),
    # facet variable
    Input('facet_variable_div', 'style'),
    Input('facet_variable_dropdown', 'options'),
    Input('facet_variable_dropdown', 'value'),

    Input('graph_type_dropdown', 'options'),
    Input('graph_type_dropdown', 'value'),
    Input('sort_categories_dropdown', 'value'),
    Input('n_bins_slider', 'value'),
    Input('opacity_slider', 'value'),
    Input('top_n_categories_slider', 'value'),
    Input('bar_mode_dropdown', 'value'),
    Input('log_x_y_axis_checklist', 'value'),
    Input('filtered_data', 'data'),
    Input('labels-apply-button', 'n_clicks'),
    State('all_columns', 'data'),
    State('numeric_columns', 'data'),
    State('non_numeric_columns', 'data'),
    State('date_columns', 'data'),
    State('categorical_columns', 'data'),
    State('string_columns', 'data'),
    State('boolean_columns', 'data'),
    State('category_orders_cache', 'data'),
    State('title_input', 'value'),
    State('subtitle_input', 'value'),
    State('x_axis_label_input', 'value'),
    State('y_axis_label_input', 'value'),
    prevent_initial_call=True,
)
def update_controls_and_graph(  # noqa
            x_variable: str | None,
            y_variable: str | None,
            # color variable
            color_variable_div: dict,
            color_variable_dropdown: list[str],
            color_variable: str | None,
            # size variable
            size_variable_div: dict,
            size_variable_dropdown: list[str],
            size_variable: str | None,
            # facet variable
            facet_variable_div: dict,
            facet_variable_dropdown: list[str],
            facet_variable: str | None,

            graph_types: list[dict],
            graph_type: str,
            sort_categories: str,
            n_bins: int,
            opacity: float,
            top_n_categories: float,
            bar_mode: str,
            log_x_y_axis: list[str],

            data: pd.DataFrame,
            labels_apply_button: int,  # noqa: ARG001
            all_columns: list[str],  # noqa: ARG001
            numeric_columns: list[str],
            non_numeric_columns: list[str],
            date_columns: list[str],
            categorical_columns: list[str],
            string_columns: list[str],
            boolean_columns: list[str],
            category_orders_cache: dict,
            title_input: str | None,
            subtitle_input: str | None,
            x_axis_label_input: str | None,
            y_axis_label_input: str | None,
        ) -> tuple[go.Figure, dict]:
    """
    Triggered when the user selects columns from the dropdown.

    This function should *not* modify the data. It should only return a figure.
    """
    # TODO: refactor and unit test

    log_function('update_graph')
    log_variable('triggered_id', ctx.triggered_id)
    log_variable('x_variable', x_variable)
    log_variable('y_variable', y_variable)
    log_variable('color_variable', color_variable)
    log_variable('size_variable', size_variable)
    log_variable('facet_variable', facet_variable)
    log_variable('n_bins', n_bins)
    log_variable('opacity', opacity)
    log_variable('top_n_categories', top_n_categories)
    log_variable('bar_mode', bar_mode)
    log_variable('log_x_y_axis', log_x_y_axis)
    log_variable('graph_types', graph_types)
    log_variable('graph_type', graph_type)
    log_variable('sort_categories', sort_categories)
    log_variable('title_input', title_input)
    log_variable('subtitle_input', subtitle_input)
    log_variable('x_axis_label_input', x_axis_label_input)
    log_variable('y_axis_label_input', y_axis_label_input)
    log_variable('category_orders_cache', category_orders_cache)
    # log_variable('type(data)', type(data))
    # log_variable('data', data)

    graph_types = [x['value'] for x in graph_types]

    ####
    # update variables
    ####

    fig = {}
    graph_data = pd.DataFrame()
    graph_config = None
    numeric_na_removal_markdown = ''
    if (
        (x_variable or y_variable)
        and data is not None and len(data) > 0
        and (not x_variable or x_variable in data.columns)
        and (not y_variable or y_variable in data.columns)
        and (not color_variable or color_variable in data.columns)
        and (not size_variable or size_variable in data.columns)
        and (not facet_variable or facet_variable in data.columns)
        ):
        ####
        # update graph options
        ####
        # get current configuration based on graph_options.yml (selected_variables)
        columns_by_type = {
            'numeric': numeric_columns,
            'date': date_columns,
            'string': string_columns,
            'categorical': categorical_columns,
            'boolean': boolean_columns,
        }
        graph_config = get_graph_config(
            configurations=GRAPH_CONFIGS['configurations'],
            x_variable=get_variable_type(variable=x_variable, options=columns_by_type),
            y_variable=get_variable_type(variable=y_variable, options=columns_by_type),
        )
        log_variable('graph_config', graph_config)
        graph_type_configs = graph_config['graph_types']
        # update graph options based on graph config
        graph_types = [x['name'] for x in graph_type_configs]

         # update graph_type if it's not valid (not in list) or if a new x/y variable has been
         # selected
        if (
            graph_type not in graph_types
            or ctx.triggered_id in ['x_variable_dropdown', 'y_variable_dropdown']
        ):
            graph_type = graph_types[0]

        # we have to decide if we are setting graph types or using something that was already
        # selected

        # selected graph config
        graph_config = next(x for x in graph_type_configs if x['name'] == graph_type)

        ####
        # create graph
        ####
        # create labels
        if title_input or subtitle_input:
            title = title_input or ''
            if subtitle_input:
                title += f"<br><sub>{subtitle_input}</sub>"
        else:
            title = f"<br><sub>{graph_config['description']}</sub>"
            if x_variable:
                title = title.replace('{{x_variable}}', f"`{x_variable}`")
            if y_variable:
                title = title.replace('{{y_variable}}', f"`{y_variable}`")
            if color_variable:
                title = title.replace('{{color_variable}}', f"`{color_variable}`")
            if size_variable:
                title = title.replace('{{size_variable}}', f"`{size_variable}`")
            if facet_variable:
                title = title.replace('{{facet_variable}}', f"`{facet_variable}`")
        graph_labels = {}
        if x_variable and x_axis_label_input:
            graph_labels[x_variable] = x_axis_label_input
        if y_variable and y_axis_label_input:
            graph_labels[y_variable] = y_axis_label_input


        columns = [x_variable, y_variable, color_variable, size_variable, facet_variable]
        columns = [col for col in columns if col is not None]
        columns = list(set(columns))
        graph_data = data[columns].copy()

        # TODO: need to convert code to string and execute string
        if any(x in numeric_columns for x in columns):
            numeric_na_removal_markdown = "##### Automatic filters applied:  \n"

        for column in columns:
            if column in string_columns or column in categorical_columns or column in boolean_columns:  # noqa
                log(f"filling na for {column}")
                graph_data[column] = hp.fill_na(
                    series=graph_data[column],
                    missing_value_replacement='<Missing>',
                )
                if top_n_categories:
                    log(f"top_n_categories_lookup[{top_n_categories}]: {top_n_categories_lookup[top_n_categories]}")  # noqa
                    graph_data[column] = hp.top_n_categories(
                        categorical=graph_data[column],
                        top_n=int(top_n_categories_lookup[top_n_categories]),
                        other_category='<Other>',
                    )
            if column in numeric_columns:
                log(f"removing missing values for {column}")
                num_values_removed = graph_data[column].isna().sum()
                if num_values_removed > 0:
                    numeric_na_removal_markdown += f"- `{num_values_removed:,}` missing values have been removed from `{column}`  \n"  # noqa
                graph_data = graph_data[graph_data[column].notna()]

        if any(x in numeric_columns for x in columns):
            rows_remaining = len(graph_data)
            rows_removed = len(data) - rows_remaining
            numeric_na_removal_markdown += f"\n`{rows_remaining:,}` rows remaining after manual/automatic filtering; `{rows_removed:,}` (`{rows_removed / len(data):.1%}`) rows removed from automatic filtering\n"  # noqa
            numeric_na_removal_markdown += "---  \n"

        selected_variables = [
            x_variable,
            y_variable,
            color_variable,
            size_variable,
            facet_variable,
        ]
        # determine category orders
        for variable in selected_variables:
            if variable is not None and variable in non_numeric_columns:
                category_orders_cache = cache_category_order(
                    cache=category_orders_cache,
                    variable=variable,
                    order_type=sort_categories,
                    top_n_categories=top_n_categories,
                    data=graph_data,
                )
        log_variable('category_orders_cache', category_orders_cache)
        category_orders = {
            k.split('__')[0]:v for k, v in category_orders_cache.items()
            if k in [f"{x}__{sort_categories}__{top_n_categories}" for x in selected_variables]
        }
        log_variable('category_orders', category_orders)

        # TODO: need to convert code to string and execute string
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
                category_orders=category_orders,
                log_x='Log X-Axis' in log_x_y_axis,
                log_y='Log Y-Axis' in log_x_y_axis,
                title=title,
                labels=graph_labels,
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
                category_orders=category_orders,
                log_x='Log X-Axis' in log_x_y_axis,
                log_y='Log Y-Axis' in log_x_y_axis,
                title=title,
                labels=graph_labels,
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
                log_x='Log X-Axis' in log_x_y_axis,
                log_y='Log Y-Axis' in log_x_y_axis,
                title=title,
                labels=graph_labels,
            )
        elif graph_type == 'histogram':
            fig = px.histogram(
                graph_data,
                x=x_variable,
                y=y_variable,
                color=color_variable,
                opacity=opacity,
                barmode=bar_mode,
                # bargap=0.1,
                # histnorm='percent',
                # log_x bool
                # log_y bool
                facet_col=facet_variable,
                facet_col_wrap=4,
                category_orders=category_orders,
                log_x='Log X-Axis' in log_x_y_axis,
                log_y='Log Y-Axis' in log_x_y_axis,
                title=title,
                labels=graph_labels,
                nbins=n_bins,
            )
            if x_variable in numeric_columns and bar_mode != 'group':# and color_variable is None:
                # Adjust the bar group gap
                fig.update_layout(barmode=bar_mode, bargap=0.05)

        elif graph_type == 'bar':
            fig = px.bar(
                graph_data,
                x=x_variable,
                y=y_variable,
                color=color_variable,
                # opacity=opacity,
                barmode=bar_mode,
                facet_col=facet_variable,
                facet_col_wrap=4,
                log_x='Log X-Axis' in log_x_y_axis,
                log_y='Log Y-Axis' in log_x_y_axis,
                title=title,
                labels=graph_labels,
            )
        else:
            raise ValueError(f"Unknown graph type: {graph_type}")

    if graph_config:
        # update color/size/facet variable options based on graph type
        log_variable('graph_config', graph_config)
        optional_variables = graph_config['optional_variables']
        log_variable('optional_variables', optional_variables)


        def get_columns_from_config(variable: str | None) -> list[str]:
            allowed_types = optional_variables[variable]['types']
            types = []
            for allowed_type in allowed_types:
                types.extend(columns_by_type[allowed_type])
            return types

        if 'color_variable' in optional_variables:
            color_variable_div = {'display': 'block'}
            color_variable_dropdown = get_columns_from_config('color_variable')
        else:
            color_variable_div = {'display': 'none'}
            color_variable_dropdown = []
            color_variable = None

        if 'size_variable' in optional_variables:
            size_variable_div = {'display': 'block'}
            size_variable_dropdown = get_columns_from_config('size_variable')
        else:
            size_variable_div = {'display': 'none'}
            size_variable_dropdown = []
            size_variable = None

        if 'facet_variable' in optional_variables:
            facet_variable_div = {'display': 'block'}
            facet_variable_dropdown = get_columns_from_config('facet_variable')
        else:
            facet_variable_div = {'display': 'none'}
            facet_variable_dropdown = []
            facet_variable = None
    else:
        color_variable_div = {'display': 'none'}
        color_variable_dropdown = []
        color_variable = None

        size_variable_div = {'display': 'none'}
        size_variable_dropdown = []
        size_variable = None

        facet_variable_div = {'display': 'none'}
        facet_variable_dropdown = []
        facet_variable = None

    log("returning fig")
    return (
        fig,
        graph_data.iloc[0:500].to_dict('records'),
        numeric_na_removal_markdown,
        category_orders_cache,
        # color variable
        color_variable_div,
        color_variable_dropdown,
        color_variable,
        # size variable
        size_variable_div,
        size_variable_dropdown,
        size_variable,
        # facet variable
        facet_variable_div,
        facet_variable_dropdown,
        facet_variable,
        # graphing options
        [{'label': x.capitalize(), 'value': x} for x in graph_types],
        graph_type,
    )


@app.callback(
    Output('x_variable_dropdown', 'value'),
    Output('y_variable_dropdown', 'value'),
    Input('clear-settings-button', 'n_clicks'),
    prevent_initial_call=True,
)
def clear_settings(n_clicks: int) -> str:
    """Triggered when the user clicks on the Clear button."""
    log_function('clear_settings')
    log_variable('n_clicks', n_clicks)
    return None, None


@app.callback(
    Output('x_variable_dropdown', 'value', allow_duplicate=True),
    Output('y_variable_dropdown', 'value', allow_duplicate=True),
    Input('swap-x-y-button', 'n_clicks'),
    State('x_variable_dropdown', 'value'),
    State('y_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def swap_x_y_variables(n_clicks: int, x_variable: str | None, y_variable: str | None) -> str:
    """Triggered when the user clicks on the Clear button."""
    log_function('Swap X/Y Variables')
    log_variable('n_clicks', n_clicks)
    return y_variable, x_variable

@app.callback(
    Output('title_input', 'value'),
    Output('subtitle_input', 'value'),
    Output('x_axis_label_input', 'value'),
    Output('y_axis_label_input', 'value'),
    Input('labels-clear-button', 'n_clicks'),
    prevent_initial_call=True,
)
def clear_labels(n_clicks: int) -> str:
    """Triggered when the user clicks on the Clear button."""
    log_function('Clear Labels')
    log_variable('n_clicks', n_clicks)
    return '', '', '', ''



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
    else:
        # remove any columns that are no longer selected
        for column in filter_columns_cache.copy():
            if column not in selected_filter_columns:
                log(f"removing {column} from filter_columns_cache")
                filter_columns_cache.pop(column)

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


@app.callback(
    Output('bar_mode_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_bar_mode_div_style(graph_type: str) -> dict:
    """Toggle the bar mode div."""
    if graph_type in ['histogram', 'bar']:
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('sort_categories_div', 'style'),
    Output('top_n_categories_div', 'style'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('color_variable_dropdown', 'value'),
    Input('size_variable_dropdown', 'value'),
    Input('facet_variable_dropdown', 'value'),
    State('non_numeric_columns', 'data'),
    prevent_initial_call=True,
)
def update_categorical_controls_div_style(
        x_variable: str | None,
        y_variable: str | None,
        color_variable: str | None,
        size_variable: str | None,
        facet_variable: str | None,
        non_numeric_columns: list[str],
    ) -> dict:
    """Toggle the sort-categories div."""
    if (
        x_variable in non_numeric_columns
        or y_variable in non_numeric_columns
        or color_variable in non_numeric_columns
        or size_variable in non_numeric_columns
        or facet_variable in non_numeric_columns
        ):
        return {'display': 'block'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


@app.callback(
    Output('n_bins_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_n_bins_div_style(graph_type: str) -> dict:
    """Toggle the n-bins div."""
    if graph_type == 'histogram':
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('opacity_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_opacity_div_style(graph_type: str) -> dict:
    """Toggle the bar mode div."""
    if graph_type in ['histogram', 'scatter']:
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('log_x_y_axis_div', 'style'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    State('numeric_columns', 'data'),
    prevent_initial_call=True,
)
def update_log_x_y_axis_div_style(
        x_variable: str | None,
        y_variable: str | None,
        numeric_columns: list[str],
    ) -> dict:
    """Toggle the 'log x/y axis' div."""
    if (x_variable in numeric_columns or y_variable in numeric_columns):
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('x_axis_label_div', 'style'),
    Input('x_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_x_axis_label_div_style(x_variable: str | None) -> dict:
    """Toggle the 'log x/y axis' div."""
    if x_variable:
        return {'width': '100%', 'display': 'block'}
    return {'display': 'none'}

@app.callback(
    Output('y_axis_label_div', 'style'),
    Input('y_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_y_axis_label_div_style(y_variable: str | None) -> dict:
    """Toggle the 'log x/y axis' div."""
    if y_variable:
        return {'width': '100%', 'display': 'block'}
    return {'display': 'none'}


if __name__ == '__main__':
    app.run_server(host=HOST, debug=DEBUG, port=PORT)

