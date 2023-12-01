"""Dash app entry point."""
from dotenv import load_dotenv
import uuid
import os
import math
import io
import yaml
import base64
from textwrap import dedent
from dash import ctx, callback_context, dash_table
from dash.dependencies import ALL
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import helpsk.pandas as hp
from helpsk.database import Snowflake
import dash_bootstrap_components as dbc
from source.library.dash_ui import (
    create_cohort_adoption_rate_control,
    create_cohort_conversion_rate_control,
    create_dropdown_control,
    create_checklist_control,
    create_input_control,
    create_slider_control,
    create_min_max_control,
    create_date_range_control,
    CLASS__GRAPH_PANEL_SECTION,
)
from source.library.dash_utilities import (
    MISSING,
    InvalidConfigurationError,
    convert_to_graph_data,
    create_title_and_labels,
    filter_data_from_ui_control,
    generate_graph,
    get_graph_config,
    get_columns_from_config,
    log,
    log_error,
    log_function,
    log_variable,
)
from dash_extensions.enrich import DashProxy, Output, Input, State, Serverside, html, dcc, \
    ServersideOutputTransform
from llm_workflow.agents import Tool, OpenAIFunctions
import source.library.types as t


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
min_retention_events_lookup = {
    1: '1',
    2: '2',
    3: '3',
    4: '4',
    5: '5',
    6: '10',
    7: '25',
    8: '50',
    9: '100',
    10: '500',

}
bar_mode_options = [
    {'label': 'Stacked', 'value': 'relative'},
    {'label': 'Side-by-Side', 'value': 'group'},
    {'label': 'Overlay', 'value': 'overlay'},
]
with open(os.path.join(os.getenv('PROJECT_PATH'), 'source/config/graphing_configurations.yml')) as f:  # noqa
    GRAPH_CONFIGS = yaml.safe_load(f)

SNOWFLAKE_CONFIG_PATH = os.getenv('SNOWFLAKE_CONFIG_PATH')
ENABLE_SNOWFLAKE = os.path.isfile(SNOWFLAKE_CONFIG_PATH)
DEFAULT_QUERIES = ''
if os.path.isfile('queries.txt'):
    with open('queries.txt') as f:
        DEFAULT_QUERIES = f.read()

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
    dcc.Store(id='generated_filter_code'),
    dcc.Store(id='column_types'),
    dcc.Store(id='variables_changed_by_ai'),
    dbc.Tabs([
        dbc.Tab(label="Load Data", children=[
            dcc.Loading(type="default", children=[
            html.Br(),
            dbc.Row([
                dbc.Tabs(active_tab='tab-0' if ENABLE_SNOWFLAKE else 'tab-1', children=[
                    dbc.Tab(label="Query Snowflake", disabled=ENABLE_SNOWFLAKE is False, children=[
                        html.Br(),
                        html.Button(
                            'Query',
                            id='query_snowflake_button',
                            n_clicks=0,
                            style={'width': '200px', 'margin': '0 8px 0 0'},
                        ),
                        html.Br(),html.Br(),
                        dcc.Textarea(
                            id='query_snowflake_text',
                            value=DEFAULT_QUERIES,
                            style={'width': '100%', 'height': 400, 'padding': '10px'},
                        ),
                        dbc.Alert(
                            "Error.",
                            color="danger",
                            id="snowflake_error",
                            dismissable=True,
                            is_open=False,
                            fade=False,
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
                            value='https://raw.githubusercontent.com/shane-kercheval/explore-data/main/data/credit.csv',
                            # value='https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv',
                            # value='https://raw.githubusercontent.com/shane-kercheval/shiny-explore-dataset/master/shiny-explore-dataset/example_datasets/credit.csv',
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
                    dbc.Tab(label="Generate Random Dataframe", children=[
                        html.Br(),
                        html.Button(
                            'Generate',
                            id='load_random_data_button',
                            n_clicks=0,
                            style={'width': '200px', 'margin': '0 8px 0 0'},
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
                dbc.Col(sm=4, md=4, lg=4, xl=3, xxl=2, children=[
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
                                #  dbc.Button(
                                #     "TEMP",
                                #     className='btn-custom',
                                #     id="TEMP-settings-button",
                                # ),
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
                                    label="Z variable",
                                    id="z_variable",
                                    placeholder="Select a variable",
                                    hidden=True,
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
                                create_dropdown_control(
                                    label="Date Floor",
                                    id="date_floor",
                                    hidden=True,
                                    clearable=False,
                                    options=[
                                        {'label': 'Year', 'value': 'year'},
                                        {'label': 'Quarter', 'value': 'quarter'},
                                        {'label': 'Month', 'value': 'month'},
                                        {'label': 'Week', 'value': 'week'},
                                        {'label': 'Day', 'value': 'day'},
                                        {'label': 'Hour', 'value': 'hour'},
                                        {'label': 'Minute', 'value': 'minute'},
                                        {'label': 'Second', 'value': 'second'},
                                    ],
                                    value='month',
                                ),
                                dbc.Button(
                                    "Clear",
                                    className='btn-custom',
                                    id="clear-settings-button",
                                    style={'margin': '10px 20px 0 0'},
                                ),
                                dbc.Button(
                                    "Swap X/Y",
                                    className='btn-custom',
                                    id="swap-x-y-button",
                                    style={'margin': '10px 20px 0 0'},
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
                                    className='btn-custom',
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
                                create_dropdown_control(
                                    label="Aggregation",
                                    id='hist_func_agg',
                                    hidden=False,
                                    multi=False,
                                    clearable=False,
                                    options=[
                                        {'label': 'Sum', 'value': 'sum'},
                                        {'label': 'Average', 'value': 'avg'},
                                        {'label': 'Min', 'value': 'min'},
                                        {'label': 'Max', 'value': 'max'},
                                    ],
                                    value='sum',
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
                                    options=bar_mode_options,
                                    value='relative',
                                ),
                                create_cohort_conversion_rate_control(
                                    label="Conversion Durations",
                                    id='cohort_conversion_rate',
                                    hidden=False,
                                ),
                                create_checklist_control(
                                    id='show_record_count',
                                    hidden=True,
                                    options=['Show Record Count'],
                                    value=[],
                                ),
                                create_cohort_adoption_rate_control(
                                    label="Adoption Range",
                                    id='cohort_adoption_rate',
                                    hidden=False,
                                ),
                                create_slider_control(
                                    label="Last N Cohorts",
                                    id='last_n_cohorts',
                                    hidden=True,
                                    value=15,
                                    step=5,
                                    min=5,
                                    max=30,
                                ),
                                create_checklist_control(
                                    id='show_unfinished_cohorts',
                                    hidden=True,
                                    options=['Show Unfinished Cohorts'],
                                    value=['Show Unfinished Cohorts'],
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
                                    label="Min Events for Retention",
                                    id='min_retention_events',
                                    hidden=True,
                                    value=1,
                                    step=1,
                                    min=1,
                                    max=10,
                                    marks=min_retention_events_lookup,
                                ),
                                create_slider_control(
                                    label="# of Periods",
                                    id='num_retention_periods',
                                    hidden=True,
                                    min=10,
                                    max=60,
                                    step=10,
                                    value=20,
                                ),
                                create_slider_control(
                                    label="# of Bins",
                                    id='n_bins',
                                    hidden=True,
                                    min=0,
                                    max=100,
                                    step=20,
                                    value=0,  # off
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
                                create_checklist_control(
                                    id='free_x_y_axis',
                                    hidden=True,
                                    options=['Free X-Axis', 'Free Y-Axis'],
                                    value=[],
                                ),
                                create_checklist_control(
                                    id='show_axes_histogram',
                                    hidden=True,
                                    options=['Show histogram in axes'],
                                    value=['Show histogram in axes'],
                                ),
                                create_slider_control(
                                    label="# of Facet Columns",
                                    id='num_facet_columns',
                                    hidden=True,
                                    min=1,
                                    max=10,
                                    step=1,
                                    value=3,
                                ),
                            ]),
                        ]),
                    ]),
                    dbc.Card(style={'margin': '10px 0 10px 0'}, children=[
                        dbc.CardHeader(
                            dbc.Button(
                                "AI (Beta)",
                                id="panel-ai-toggle",
                                className="panel_toggle_button",
                            ),
                        ),
                        dbc.Collapse(id="collapse-ai", is_open=False, children=[
                            dbc.CardBody([
                                dcc.Loading(type="default", children=[
                                    dbc.Button(
                                        "Do AI Stuff",
                                        className='btn-custom',
                                        id="ai-apply-button",
                                        style={'margin': '0 20px 20px 0'},
                                    ),
                                    dcc.Textarea(
                                        id='ai_prompt_textarea',
                                        value="plot the probability of default given the duration.",
                                        #value="Plot a 3d scatter the duration of the loan against the amount of the loan and age.",
                                        style={'width': '100%', 'height': 200, 'padding': '10px'},
                                    ),
                                ]),
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
                        dbc.Collapse(id="collapse-other-options", is_open=False, children=[
                            dbc.CardBody([
                                dbc.Button(
                                    "Apply",
                                    className='btn-custom',
                                    id="labels-apply-button",
                                    style={'margin': '0 20px 20px 0'},
                                ),
                                dbc.Button(
                                    "Clear",
                                    className='btn-custom',
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
                                create_input_control(
                                    label="Color Label",
                                    id="color_label",
                                    placeholder="Color label",
                                    hidden=True,
                                ),
                                create_input_control(
                                    label="Size Label",
                                    id="size_label",
                                    placeholder="Size label",
                                    hidden=True,
                                ),
                                create_input_control(
                                    label="Facet Label",
                                    id="facet_label",
                                    placeholder="Facet label",
                                    hidden=True,
                                ),
                            ]),
                        ]),
                    ]),
                ]),
                dbc.Col(sm=8, md=8, lg=8, xl=9, xxl= 10, children=[
                    dbc.Alert(
                        "Unsupported selection.",
                        color="danger",
                        id="invalid_configuration_alert",
                        dismissable=True,
                        fade=False,
                    ),
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
                                dcc.Markdown(id="generated_code", children="Select columns to graph."),  # noqa
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
        dbc.Tab(label="Correlations", children=[
            html.Br(),
            dcc.Graph(
                id='correlations_graph',
                config={'staticPlot': False, 'displayModeBar': False},
                # 3/12 because the sidebar is 3/12 of the width
                # style={'width': '100%', 'height': f'100vw'},
            ),
        ]),
    ]),
])


@app.callback(
    Output('x_variable_dropdown', 'options'),
    Output('y_variable_dropdown', 'options'),
    Output('filter_columns_dropdown', 'options'),
    Output('filter_columns_cache', 'data', allow_duplicate=True),
    Output('visualize_graph', 'figure', allow_duplicate=True),
    Output('visualize_table', 'data', allow_duplicate=True),
    Output('table_uploaded_data', 'children'),
    Output('numeric_summary_table', 'data'),
    Output('non_numeric_summary_table', 'data'),
    Output('original_data', 'data'),
    Output('filtered_data', 'data', allow_duplicate=True),
    Output('column_types', 'data'),
    Output('snowflake_error', 'is_open'),
    Output('snowflake_error', 'children'),
    Input('query_snowflake_button', 'n_clicks'),
    Input('load_random_data_button', 'n_clicks'),
    Input('load_from_url_button', 'n_clicks'),
    Input('upload-data', 'contents'),
    State('query_snowflake_text', 'value'),
    State('upload-data', 'filename'),
    State('load_from_url', 'value'),
    prevent_initial_call=True,
)
def load_data(  # noqa
        query_snowflake_button: int,
        load_random_data_button: int,
        load_from_url_button: int,
        upload_data_contents: str,
        query_snowflake_text: str,
        upload_data_filename: str,
        load_from_url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    log_function('load_data')
    x_variable_dropdown = []
    y_variable_dropdown = []
    filter_columns_dropdown = []
    filter_columns_cache = None
    primary_graph = {}
    visualize_table = None
    table_uploaded_data = None
    numeric_summary = None
    non_numeric_summary = None
    original_data = None
    filtered_data = None
    column_types = None
    snowflake_error_message = None
    log_variable('query_snowflake_button', query_snowflake_button)
    log_variable('load_random_data_button', load_random_data_button)
    log_variable('load_from_url_button', load_from_url_button)

    if callback_context.triggered:
        triggered = callback_context.triggered[0]['prop_id']
        log_variable('triggered', triggered)
        if triggered == 'upload-data.contents':
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
        elif triggered == 'query_snowflake_button.n_clicks':
            log("Querying Snowflake")
            try:
                with Snowflake.from_config(SNOWFLAKE_CONFIG_PATH, config_key='snowflake') as db:
                    data  = db.query(query_snowflake_text)
            except Exception as e:
                data = None
                snowflake_error_message = f"{type(e).__name__}: {e}"
                log_error(snowflake_error_message)

        elif triggered == 'load_from_url_button.n_clicks' and load_from_url:
            log("Loading from CSV URL")
            if 'docs.google.com/spreadsheets' in load_from_url:
                load_from_url = load_from_url.replace('/edit#gid=', '/export?format=csv&gid=')
            data = pd.read_csv(load_from_url)
        elif triggered == 'load_random_data_button.n_clicks':
            log("Loading DataFrame with random data")
            from source.library.utilities import create_random_dataframe
            data = create_random_dataframe(num_rows=10_000, sporadic_missing=True)
            log(f"Loaded data w/ {data.shape[0]:,} rows and {data.shape[1]:,} columns")
        else:
            raise ValueError(f"Unknown trigger: {triggered}")

        if data is not None:
            column_types = t.get_column_types(data)
            log_variable('column_types', column_types)
            log_variable('column_types', column_types)

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

            x_variable_dropdown = data.columns.to_list()
            y_variable_dropdown = x_variable_dropdown
            filter_columns_dropdown = x_variable_dropdown
            table_uploaded_data = [
                dcc.Markdown("#### Sample of Data (first 500 rows):"),
                dash_table.DataTable(
                    id='data_sample_table',
                    data=data.iloc[0:500].to_dict('records'),
                    page_size=20,
                    style_header={
                        'fontWeight': 'bold',
                    },
                ),
            ]
            original_data = data
            filtered_data = data

    return (
        x_variable_dropdown,
        y_variable_dropdown,
        filter_columns_dropdown,
        filter_columns_cache,
        primary_graph,
        visualize_table,
        table_uploaded_data,
        numeric_summary,
        non_numeric_summary,
        Serverside(original_data),
        Serverside(filtered_data),
        column_types,
        snowflake_error_message is not None,
        snowflake_error_message,
    )


@app.callback(
    Output('x_variable_dropdown', 'value', allow_duplicate=True),
    Output('y_variable_dropdown', 'value', allow_duplicate=True),
    Output('z_variable_dropdown', 'value', allow_duplicate=True),
    Output('color_variable_dropdown', 'value', allow_duplicate=True),
    Output('size_variable_dropdown', 'value', allow_duplicate=True),
    Output('facet_variable_dropdown', 'value', allow_duplicate=True),
    Output('graph_type_dropdown', 'value', allow_duplicate=True),
    Output('variables_changed_by_ai', 'data', allow_duplicate=True),
    Output('ai_prompt_textarea', 'value'),  # this is simply to make the progress bar work
    # i.e. (dcc.Loading)
    Input('ai-apply-button', 'n_clicks'),
    State('ai_prompt_textarea', 'value'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def apply_temporary_settings(n_clicks: int, ai_prompt: str, column_types: dict) -> tuple:
    def build_tools_from_graph_configs(configs: dict, column_types: dict) -> list[Tool]:
        # TODO: need to add graph_type in order to support e.g. P( y | x ) chart
        # TODO: i might have to add graph_type as another variable in yaml since it's not always
        # valid. Only certain graphs need to specify the graph_type. Actually i'm not sure that
        # is True.. i think i can just pass graph_type in the same way as x_variable, etc.
        # I just need to add it to the inputs dict or extract it from the tool name. or something
        # BUT there are other variables like `Aggregation:` (sum, avg, etc.) that are not always
        # valid.
        #TODO: would also be nice to specify monthly/weekly/daily etc. for date variables
        tools = []
        for config in configs:
            # config = configs[0]
            variables = {k:v for k, v in config['selected_variables'].items() if v is not None}
            required_variables = list(variables.keys())
            for graph_type in config['graph_types']:
                if 'agent_description' not in graph_type:
                    continue
                # description = graph_type['info']
                agent_description = graph_type['agent_description']
                agent_description = agent_description.strip() if agent_description else ''
                description = f"({graph_type['name']}) {graph_type['description']} {agent_description}"
                for var, types in variables.items():
                    replacement = f" axis variable (which can be a column of type {', '.join(types)})"
                    description = description.replace(
                        f"{{{{{var}}}}}",
                        f"{var.replace('_variable',replacement)}"
                    ).strip()
                # description = f"({graph_type['name']}) "

                # graph_type = config['graph_types'][0]
                if 'optional_variables' in graph_type:
                    optional_variables = graph_type['optional_variables']
                    variables.update({k:v['types'] for k, v in optional_variables.items() if v is not None})
                # print(f"variables: {variables}")
                # print(f"required_variables: {required_variables}")
                valid_graph = True
                inputs = {}
                for k, valid_column_types in variables.items():
                    valid_column_names = [n for n, t in column_types.items() if t in valid_column_types]
                    inputs[k] = {
                        'type': 'string',
                        'description': f"{k.replace('_variable', ' axis')} that supports {', '.join(valid_column_types)} columns",   # noqa
                    }
                    if len(valid_column_names) == 0:
                        if k in required_variables:
                            # if there are no valid columns that support the corresponding types and the
                            # variable is required (e.g. there are no dates columns in the dataset and a
                            # date is required for the graph), then skip this graph/tool altogether
                            valid_graph = False
                            break
                    else:
                        inputs[k]['enum'] = valid_column_names
                if valid_graph:
                    # inputs = {'inputs': inputs}
                    tool = Tool(
                        name=str(uuid.uuid4()),
                        description=description,
                        inputs=inputs,
                        required=required_variables,
                    )
                    tool.graph_name = graph_type['name']
                    tools.append(tool)
        return tools

    x_variable = None
    y_variable = None
    z_variable = None
    color_variable = None
    size_variable = None
    facet_variable = None
    graph_type = None
    variables_changed_by_ai = False

    if ai_prompt:
        tools = build_tools_from_graph_configs(GRAPH_CONFIGS['configurations'], column_types)
        agent = OpenAIFunctions(
            model_name='gpt-3.5-turbo-1106',
            tools=tools,
        )
        formatted_colum_names = '\n'.join([f"{k}: {v}" for k, v in column_types.items()])
        template = dedent(f"""
        The user is asking to create a plot based on the following column names and types. Infer the correct column names and the correct axes from the users question. Choose a tool that uses all of the columns listed by the user. Prioritize the required columns.

        Valid columns and types:

        ```
        {formatted_colum_names}
        ```

        User's question:
        
        {ai_prompt}
        """)  # noqa
        log_variable('OpenAI template', template)
        response = agent(template)

        log(f"Agent Cost:           ${agent.history()[0].cost:.5f}")
        log(f"Agent Tokens:          {agent.history()[0].total_tokens:,}")
        log(f"Agent Prompt Tokens:   {agent.history()[0].input_tokens:,}")
        log(f"Agent Response Tokens: {agent.history()[0].response_tokens:,}")

        if response:
            tool, args = response[0]
            log_variable('OpenAI functions args', args)
            variables_changed_by_ai = True
            if 'x_variable' in args and args['x_variable'] in column_types:
                x_variable = args['x_variable']
            if 'y_variable' in args and args['y_variable'] in column_types:
                y_variable = args['y_variable']
            if 'z_variable' in args and args['z_variable'] in column_types:
                z_variable = args['z_variable']
            if 'color_variable' in args and args['color_variable'] in column_types:
                color_variable = args['color_variable']
            if 'size_variable' in args and args['size_variable'] in column_types:
                size_variable = args['size_variable']
            if 'facet_variable' in args and args['facet_variable'] in column_types:
                facet_variable = args['facet_variable']

            graph_type = tool.graph_name

    log_variable('x_variable', x_variable)
    log_variable('y_variable', y_variable)
    log_variable('z_variable', z_variable)
    log_variable('color_variable', color_variable)
    log_variable('size_variable', size_variable)
    log_variable('facet_variable', facet_variable)
    log_variable('graph_type', graph_type)
    return (
        x_variable,
        y_variable,
        z_variable,
        color_variable,
        size_variable,
        facet_variable,
        graph_type,
        variables_changed_by_ai,
        ai_prompt,
    )

@app.callback(
    Output('filtered_data', 'data'),
    Output('visualize_filter_info', 'children'),
    Output('generated_filter_code', 'data'),
    Input('filter-apply-button', 'n_clicks'),
    State('filter_columns_cache', 'data'),
    State('original_data', 'data'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def filter_data(
        n_clicks: int,  # noqa: ARG001
        filter_columns_cache: dict,
        original_data: pd.DataFrame,
        column_types: dict,
        ) -> dict:
    """Filter the data based on the user's selections."""
    filtered_data, markdown_text, code = filter_data_from_ui_control(
        filters=filter_columns_cache,
        column_types=column_types,
        data=original_data,
    )
    return Serverside(filtered_data), markdown_text, code


@app.callback(
    Output('visualize_graph', 'figure'),
    Output('visualize_table', 'data'),
    Output('visualize_numeric_na_removal_markdown', 'children'),
    Output('generated_code', 'children'),
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
    Output('variables_changed_by_ai', 'data'),
    Output('invalid_configuration_alert', 'is_open'),

    # INPUTS
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('z_variable_dropdown', 'value'),
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

    Input('date_floor_dropdown', 'value'),

    Input('graph_type_dropdown', 'options'),
    Input('graph_type_dropdown', 'value'),
    Input('sort_categories_dropdown', 'value'),
    Input('n_bins_slider', 'value'),
    Input('opacity_slider', 'value'),
    Input('top_n_categories_slider', 'value'),
    Input('min_retention_events_slider', 'value'),
    Input('num_retention_periods_slider', 'value'),
    Input('hist_func_agg_dropdown', 'value'),
    Input('bar_mode_dropdown', 'value'),
    Input('cohort_conversion_rate__input', 'value'),
    Input('cohort_conversion_rate__dropdown', 'value'),
    Input('show_record_count_checklist', 'value'),
    Input('cohort_adoption_rate__input', 'value'),
    Input('cohort_adoption_rate__dropdown', 'value'),
    Input('last_n_cohorts_slider', 'value'),
    Input('show_unfinished_cohorts_checklist', 'value'),
    Input('log_x_y_axis_checklist', 'value'),
    Input('free_x_y_axis_checklist', 'value'),
    Input('show_axes_histogram_checklist', 'value'),
    Input('num_facet_columns_slider', 'value'),
    Input('filtered_data', 'data'),
    Input('labels-apply-button', 'n_clicks'),
    State('generated_filter_code', 'data'),
    State('column_types', 'data'),
    State('title_input', 'value'),
    State('subtitle_input', 'value'),
    State('x_axis_label_input', 'value'),
    State('y_axis_label_input', 'value'),
    State('color_label_input', 'value'),
    State('size_label_input', 'value'),
    State('facet_label_input', 'value'),
    State('variables_changed_by_ai', 'data'),
    prevent_initial_call=True,
)
def update_controls_and_graph(  # noqa
            x_variable: str | None,
            y_variable: str | None,
            z_variable: str | None,
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
            date_floor: str | None,

            graph_types: list[dict],
            graph_type: str,
            sort_categories: str,
            n_bins: int,
            opacity: float,
            top_n_categories: float,
            min_retention_events: float,
            num_retention_periods: float,
            hist_func_agg: str,
            bar_mode: str,
            cohort_conversion_rate_input: str,
            cohort_conversion_rate_dropdown: str,
            show_record_count_checklist: list[str],
            cohort_adoption_rate_input: str,
            cohort_adoption_rate_dropdown: str,
            last_n_cohorts_slider: int,
            show_unfinished_cohorts_checklist: list[str],
            log_x_y_axis: list[str],
            free_x_y_axis: list[str],
            show_axes_histogram: list[str],
            num_facet_columns: int,

            data: pd.DataFrame,
            labels_apply_button: int,  # noqa: ARG001
            generated_filter_code: str,
            column_types: dict,
            title_input: str | None,
            subtitle_input: str | None,
            x_axis_label_input: str | None,
            y_axis_label_input: str | None,
            color_label_input: str | None,
            size_label_input: str | None,
            facet_label_input: str | None,
            variables_changed_by_ai: bool | None,
        ) -> tuple[go.Figure, dict]:
    """
    Triggered when the user selects columns from the dropdown.

    This function should *not* modify the data. It should only return a figure.
    """
    log_function('update_graph')
    log_variable('triggered_id', ctx.triggered_id)
    log_variable('x_variable', x_variable)
    log_variable('y_variable', y_variable)
    log_variable('z_variable', z_variable)
    log_variable('color_variable', color_variable)
    log_variable('size_variable', size_variable)
    log_variable('facet_variable', facet_variable)
    log_variable('n_bins', n_bins)
    log_variable('opacity', opacity)
    log_variable('top_n_categories', top_n_categories)
    log_variable('min_retention_events', min_retention_events)
    log_variable('num_retention_periods', num_retention_periods)
    log_variable('hist_func_agg', hist_func_agg)
    log_variable('bar_mode', bar_mode)
    log_variable('cohort_conversion_rate_input', cohort_conversion_rate_input)
    log_variable('cohort_conversion_rate_dropdown', cohort_conversion_rate_dropdown)
    log_variable('show_record_count_checklist', show_record_count_checklist)
    log_variable('cohort_adoption_rate_input', cohort_adoption_rate_input)
    log_variable('cohort_adoption_rate_dropdown', cohort_adoption_rate_dropdown)
    log_variable('last_n_cohorts_slider', last_n_cohorts_slider)
    log_variable('show_unfinished_cohorts_checklist', show_unfinished_cohorts_checklist)
    log_variable('log_x_y_axis', log_x_y_axis)
    log_variable('free_x_y_axis', free_x_y_axis)
    log_variable('show_axes_histogram', show_axes_histogram)
    log_variable('num_facet_columns', num_facet_columns)
    log_variable('graph_types', graph_types)
    log_variable('graph_type', graph_type)
    log_variable('sort_categories', sort_categories)
    log_variable('date_floor', date_floor)
    log_variable('column_types', column_types)
    log_variable('title_input', title_input)
    log_variable('subtitle_input', subtitle_input)
    log_variable('x_axis_label_input', x_axis_label_input)
    log_variable('y_axis_label_input', y_axis_label_input)
    log_variable('color_label_input', color_label_input)
    log_variable('size_label_input', size_label_input)
    log_variable('facet_label_input', facet_label_input)

    graph_types = [x['value'] for x in graph_types]
    fig = {}
    graph_data = pd.DataFrame()
    selected_graph_config = None
    numeric_na_removal_markdown = ''
    generated_code = generated_filter_code or ''
    invalid_configuration_alert = False

    try:
        if (
            (x_variable or y_variable)
            and data is not None and len(data) > 0
            and (not x_variable or x_variable in data.columns)
            and (not y_variable or y_variable in data.columns)
            and (not color_variable or color_variable in data.columns)
            and (not size_variable or size_variable in data.columns)
            and (not facet_variable or facet_variable in data.columns)
            ):
            if t.is_date(x_variable, column_types):
                assert date_floor

            ####
            # update graph options
            ####
            # get current configuration based on graph_options.yml (selected_variables)
            matching_graph_config = get_graph_config(
                configurations=GRAPH_CONFIGS['configurations'],
                x_variable=t.get_type(x_variable, column_types),
                y_variable=t.get_type(y_variable, column_types),
                z_variable=t.get_type(z_variable, column_types),
            )
            log_variable('matching_graph_config', matching_graph_config)
            possible_graph_types = matching_graph_config['graph_types']
            # update graph options based on graph config
            graph_types = [x['name'] for x in possible_graph_types]
            # update graph_type if it's not valid (not in list) or if a new x/y variable has been
            # selected
            if (
                (
                    graph_type not in graph_types
                    # we want to return it to the default graph if the user changes selections
                    # e.g. if we select numeric and then numeric, we want a scatter not histogram
                    # (and we don't want to manually have to select scatter each time, it should
                    # display the first option in the config)
                    or ctx.triggered_id in ['x_variable_dropdown', 'y_variable_dropdown', 'z_variable_dropdown']  # noqa
                )
                # we don't want to override the value if it was changed by the AI
                and not variables_changed_by_ai
            ):
                graph_type = graph_types[0]

            selected_graph_config = next(
                x for x in possible_graph_types if x['name'] == graph_type
            )

            ####
            # create graph
            ####
            # create labels
            config_description = selected_graph_config['description']
            title, graph_labels = create_title_and_labels(
                title_input=title_input,
                subtitle_input=subtitle_input,
                config_description=config_description,
                x_variable=x_variable,
                y_variable=y_variable,
                z_variable=z_variable,
                color_variable=color_variable,
                size_variable=size_variable,
                facet_variable=facet_variable,
                x_axis_label_input=x_axis_label_input,
                y_axis_label_input=y_axis_label_input,
                color_label_input=color_label_input,
                size_label_input=size_label_input,
                facet_label_input=facet_label_input,
            )

            possible_variables = [
                x_variable,
                y_variable,
                z_variable,
                color_variable,
                size_variable,
                facet_variable,
            ]
            selected_variables = [col for col in possible_variables if col is not None]
            selected_variables = list(set(selected_variables))  # remove duplicates

            log(f"top_n_categories_lookup[{top_n_categories}]: {top_n_categories_lookup[top_n_categories]}")  # noqa
            # TODO: need to convert code to string and execute string
            top_n_categories = top_n_categories_lookup[top_n_categories]
            top_n_categories = None if top_n_categories == 'None' else int(top_n_categories)
            exclude_from_top_n_transformation = []
            if graph_type in ['bar - count distinct', 'retention']:
                exclude_from_top_n_transformation = [y_variable]
            elif graph_type == 'heatmap - count distinct':
                exclude_from_top_n_transformation = [z_variable]

            if t.is_date(x_variable, column_types) and t.is_date(y_variable, column_types):
                # if x and y are both dates then we need to preserve them to calculate the
                # cohorted conversion rates
                # missing values will be removed from the timestamps
                create_cohorts_from = (x_variable, y_variable)
            else:
                create_cohorts_from = []
            graph_data, numeric_na_removal_markdown, code = convert_to_graph_data(
                data=data,
                column_types=column_types,
                selected_variables=selected_variables,
                top_n_categories=top_n_categories,
                create_cohorts_from=create_cohorts_from,
                exclude_from_top_n_transformation=exclude_from_top_n_transformation,
                date_floor=date_floor,
            )
            if code:
                generated_code += "\n"
                generated_code += code

            if cohort_conversion_rate_input:
                cohort_conversion_rate_input = [
                    int(x.strip()) for x in cohort_conversion_rate_input.split(',')
                ]
            min_retention_events = min_retention_events_lookup[min_retention_events]
            fig, graph_code = generate_graph(
                data=graph_data,
                graph_type=graph_type,
                x_variable=x_variable,
                y_variable=y_variable,
                z_variable=z_variable,
                color_variable=color_variable,
                size_variable=size_variable,
                facet_variable=facet_variable,
                num_facet_columns=num_facet_columns,
                selected_category_order=sort_categories,
                hist_func_agg=hist_func_agg,
                bar_mode=bar_mode,
                date_floor=date_floor,
                cohort_conversion_rate_snapshots=cohort_conversion_rate_input,
                cohort_conversion_rate_units=cohort_conversion_rate_dropdown,
                show_record_count='Show Record Count' in show_record_count_checklist,
                cohort_adoption_rate_range=cohort_adoption_rate_input,
                cohort_adoption_rate_units=cohort_adoption_rate_dropdown,
                last_n_cohorts=last_n_cohorts_slider,
                show_unfinished_cohorts='Show Unfinished Cohorts' in show_unfinished_cohorts_checklist,  # noqa
                opacity=opacity,
                n_bins=n_bins,
                min_retention_events=min_retention_events,
                num_retention_periods=num_retention_periods,
                log_x_axis='Log X-Axis' in log_x_y_axis,
                log_y_axis='Log Y-Axis' in log_x_y_axis,
                free_x_axis='Free X-Axis' in free_x_y_axis,
                free_y_axis='Free Y-Axis' in free_x_y_axis,
                show_axes_histogram='Show histogram in axes' in show_axes_histogram,
                title=title,
                graph_labels=graph_labels,
                column_types=column_types,
            )
            generated_code += graph_code

        if selected_graph_config:
            # update color/size/facet variable options based on graph type
            log_variable('graph_config', selected_graph_config)
            if 'optional_variables' in selected_graph_config:
                optional_variables = selected_graph_config['optional_variables'] or {}
            else:
                optional_variables = {}
            log_variable('optional_variables', optional_variables)

            if 'color_variable' in optional_variables:
                color_variable_div = {'display': 'block'}
                color_variable_dropdown = get_columns_from_config(
                    allowed_types=optional_variables['color_variable']['types'],
                    column_types=column_types,
                )
            else:
                color_variable_div = {'display': 'none'}
                color_variable_dropdown = []
                color_variable = None

            if 'size_variable' in optional_variables:
                size_variable_div = {'display': 'block'}
                size_variable_dropdown = get_columns_from_config(
                    allowed_types=optional_variables['size_variable']['types'],
                    column_types=column_types,
                )
            else:
                size_variable_div = {'display': 'none'}
                size_variable_dropdown = []
                size_variable = None

            if 'facet_variable' in optional_variables:
                facet_variable_div = {'display': 'block'}
                facet_variable_dropdown = get_columns_from_config(
                    allowed_types=optional_variables['facet_variable']['types'],
                    column_types=column_types,
                )
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

    except InvalidConfigurationError as e:
            log_error(e)
            invalid_configuration_alert = True

    log("returning fig")
    return (
        fig,
        graph_data.iloc[0:500].to_dict('records'),
        numeric_na_removal_markdown,
        f"""```python\n{generated_code}\n```""",
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
        False,  # reset variables_changed_by_ai
        invalid_configuration_alert,
    )


@app.callback(
    Output('correlations_graph', 'figure'),
    Input('original_data', 'data'),
)
def update_correlations_graph(data: pd.DataFrame) -> go.Figure:
    """Triggered when the user clicks on the Load button."""
    log_function('update_correlations_graph')
    if data is None:
        return {}
    # Calculate the correlation matrix
    correlation_matrix = data.corr(numeric_only=True, min_periods=30).round(2)
    return px.imshow(
        correlation_matrix,
        x=correlation_matrix.columns,
        y=correlation_matrix.index,
        text_auto=True,
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        title='Correlation Heatmap of Numeric Columns',
        width=1_000,
        height=800,
    )


@app.callback(
    Output('x_variable_dropdown', 'value'),
    Output('y_variable_dropdown', 'value'),
    Output('date_floor_dropdown', 'value'),
    Input('clear-settings-button', 'n_clicks'),
    prevent_initial_call=True,
)
def clear_settings(n_clicks: int) -> str:
    """Triggered when the user clicks on the Clear button."""
    log_function('clear_settings')
    log_variable('n_clicks', n_clicks)
    return None, None, 'month'


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
    Output('color_label_input', 'value'),
    Output('size_label_input', 'value'),
    Output('facet_label_input', 'value'),
    Input('labels-clear-button', 'n_clicks'),
    prevent_initial_call=True,
)
def clear_labels(n_clicks: int) -> str:
    """
    Triggered when the user clicks on the Clear button in the "Other Options" section for
    title/subtitle, etc.
    """
    log_function('Clear Labels')
    log_variable('n_clicks', n_clicks)
    return '', '', '', '', '', '', ''


@app.callback(
    Output('date_floor_div', 'style'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('z_variable_dropdown', 'value'),
    Input('color_variable_dropdown', 'value'),
    Input('size_variable_dropdown', 'value'),
    Input('facet_variable_dropdown', 'value'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def show_date_floor_div(
        x_variable: str | None,
        y_variable: str | None,
        z_variable: str | None,
        color_variable: str | None,
        size_variable: str | None,
        facet_variable: str | None,
        column_types: dict,
        ) -> dict:
    """Show the date floor dropdown if any of the variables are dates."""
    log_function('show_date_floor_div')
    # if any variables are in date_columns, show the date_floor dropdown
    variables = [x_variable, y_variable, z_variable, color_variable, size_variable, facet_variable]
    if any(t.is_date(x, column_types) for x in variables):
        return {'display': 'block'}
    return {'display': 'none'}

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
    Output("collapse-ai", "is_open"),
    Input("panel-ai-toggle", "n_clicks"),
    State("collapse-ai", "is_open"),
    prevent_initial_call=True,
)
def toggle_ai_panel(n: int, is_open: bool) -> bool:
    """Toggle the ai panel."""
    log_function('toggle_ai_panel')
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
    State('column_types', 'data'),
    State('original_data', 'data'),

    prevent_initial_call=True,
)
def update_filter_controls(  # noqa: PLR0912
        selected_filter_columns: list[str],
        filter_columns_cache: dict,
        column_types: list[str],
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
    log_variable('non_numeric_columns', column_types)

    components = []
    if selected_filter_columns and data is not None and len(data) > 0:
        for column in selected_filter_columns:
            log(f"Creating controls for `{column}`")
            value = []
            if filter_columns_cache and column in filter_columns_cache:
                value = filter_columns_cache[column]
                log(f"found `{column}` in filter_columns_cache with value `{value}`")

            if t.is_date(column, column_types):
                log("Creating date range control")
                _date_series = pd.to_datetime(data[column])
                components.append(create_date_range_control(
                    label=column,
                    id=f"filter_control_{column}",
                    min_value=value[0] if value else _date_series.min(),
                    max_value=value[1] if value else _date_series.max(),
                    component_id={"type": "filter-control-date-range", "index": column},
                ))
            elif t.is_boolean(column, column_types):
                log("Creating dropdown control")
                options = ['True', 'False']
                if data[column].isna().any():
                    options.append(MISSING)
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
            elif t.get_type(column, column_types) in {t.STRING, t.CATEGORICAL}:
                log("Creating dropdown control")
                options = sorted(data[column].dropna().unique().tolist())
                # most likely is an id value of some sort and will cause issues and slow down the
                # app if there are too many options
                if len(options) > 1000:
                    log(f"skipping {column}; too many unique values.")
                    continue
                log_variable('data[column].unique()', options)
                if data[column].isna().any():
                    options.append(MISSING)
                components.append(create_dropdown_control(
                    label=column,
                    id=f"filter_control_{column}",
                    value=value,
                    multi=True,
                    options=options,
                    # options=values_to_dropdown_options(series.unique()),
                    component_id={"type": "filter-control-dropdown", "index": column},
                ))
            elif t.is_numeric(column, column_types):
                log("Creating min/max control")
                components.append(create_min_max_control(
                    label=column,
                    id=f"filter_control_{column}",
                    min_value=value[0] if value else round(data[column].min()),
                    max_value=value[1] if value else math.ceil(data[column].max()),
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
            # this can happen if the user selects a column that we won't filter on (e.g. the
            # column has too many unique values)
            log_error(f"Unknown column type: {column}")

    log(f"filter_columns_cache: {filter_columns_cache}")
    return filter_columns_cache


@app.callback(
    Output('hist_func_agg_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('z_variable_dropdown', 'value'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def update_hist_func_agg_div_style(
        graph_type: str,
        y_variable: str | None,
        z_variable: str | None,
        column_types: list[str]) -> dict:
    """Toggle the bar mode div."""
    if (
        (t.is_numeric(y_variable, column_types) and graph_type == 'histogram')
        or (t.is_numeric(z_variable, column_types) and graph_type == 'heatmap')
        ):
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('bar_mode_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    Input('color_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_bar_mode_div_style(graph_type: str, color_variable: str | None) -> dict:
    """Toggle the bar mode div."""
    allowed_graphs = ['histogram', 'bar', 'bar - count distinct']
    if (color_variable and graph_type in allowed_graphs) or graph_type == 'cohorted conversion rates':  # noqa
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('z_variable_div', 'style'),
    Output('z_variable_dropdown', 'options'),
    Output('z_variable_dropdown', 'value'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('z_variable_dropdown', 'value'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def update_z_variable_dropdown_style(
        x_variable: str | None,
        y_variable: str | None,
        z_variable: str | None,
        column_types: dict,
    ) -> tuple[dict, list, str]:
    """Toggle the z-variable dropdown."""
    numeric_columns = t.get_numeric_columns(column_types)
    if t.is_numeric(x_variable, column_types) and t.is_numeric(y_variable, column_types):
        return {'display': 'block'}, numeric_columns, z_variable
    if t.is_discrete(x_variable, column_types) and t.is_discrete(y_variable, column_types):
        options = [x for x, y in column_types.items() if y != t.DATE]
        return {'display': 'block'}, options, z_variable
    return {'display': 'none'}, [], z_variable


@app.callback(
    Output('sort_categories_div', 'style'),
    Output('top_n_categories_div', 'style'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('color_variable_dropdown', 'value'),
    Input('size_variable_dropdown', 'value'),
    Input('facet_variable_dropdown', 'value'),
    Input('graph_type_dropdown', 'value'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def update_categorical_controls_div_style(
        x_variable: str | None,
        y_variable: str | None,
        color_variable: str | None,
        size_variable: str | None,
        facet_variable: str | None,
        graph_type: str,
        column_types: list[str],
    ) -> dict:
    """Toggle the sort-categories div."""
    if graph_type == 'retention':
        return {'display': 'none'}, {'display': 'none'}
    if (
        t.is_discrete(x_variable, column_types)
        or t.is_discrete(y_variable, column_types)
        or t.is_discrete(color_variable, column_types)
        or t.is_discrete(size_variable, column_types)
        or t.is_discrete(facet_variable, column_types)
        ):
        return {'display': 'block'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


@app.callback(
    Output('n_bins_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('facet_variable_dropdown', 'value'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def update_n_bins_div_style(
        graph_type: str,
        x_variable: str | None,
        y_variable: str | None,
        facet_variable: str | None,
        column_types: dict,
    ) -> dict:
    """Toggle the n-bins div."""
    turn_on = {'display': 'block'}
    turn_off = {'display': 'none'}
    log_variable('graph_type', graph_type)
    if (
            t.is_numeric(x_variable, column_types)
            and t.is_numeric(y_variable, column_types)
            and graph_type == 'heatmap'
        ):
        return turn_on
    if graph_type == 'histogram' and t.is_numeric(x_variable, column_types):
        return turn_on
    if graph_type == 'P(Y | X)' and t.is_numeric(facet_variable, column_types):
        return turn_on
    return turn_off


@app.callback(
    Output('min_retention_events_div', 'style'),
    Output('num_retention_periods_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_retention_div_style(graph_type: str) -> dict:
    """Toggle the retention div."""
    if graph_type == 'retention':
        return {'display': 'block'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


@app.callback(
    Output('opacity_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_opacity_div_style(graph_type: str) -> dict:
    """Toggle the bar mode div."""
    if graph_type in ['histogram', 'scatter', 'scatter-3d']:
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('log_x_y_axis_div', 'style'),
    Output('log_x_y_axis_checklist', 'value'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('log_x_y_axis_checklist', 'value'),
    State('column_types', 'data'),
    prevent_initial_call=True,
)
def update_log_x_y_axis_div_style(
        x_variable: str | None,
        y_variable: str | None,
        log_x_y_axis: list[str],
        column_types: dict,
    ) -> dict:
    """
    Toggle the 'log x/y axis' div. If we are showing the div, then don't update the values (i.e.
    return the same list of current values that is passed in). If we are hiding the div, then
    return an empty list. This is so that graphs don't attempt to log the x/y axis when the div is
    hidden.

    The original bug was that if the user selected a numeric variable, and then log transformed the
    x or y axis, and then selected, for example, a date variable, the log transformation would
    still be applied to the date variable, both on the x and y axis.
    """
    if t.is_numeric(x_variable, column_types) or t.is_numeric(y_variable, column_types):
        return {'display': 'block'}, log_x_y_axis
    return {'display': 'none'}, []


@app.callback(
    Output('show_axes_histogram_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_show_axes_histogram_div_style(
        graph_type: str,
    ) -> dict:
    """Toggle the 'log x/y axis' div."""
    if graph_type in ['scatter', 'heatmap', 'heatmap - count distinct']:
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('free_x_y_axis_div', 'style'),
    Input('facet_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_free_x_y_axis_div_style(facet_variable: str | None) -> dict:
    """Toggle the 'free x/y axis' div."""
    if facet_variable:
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('num_facet_columns_div', 'style'),
    Input('facet_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_num_facet_columns_div_style(facet_variable: str | None) -> dict:
    """Toggle the 'log x/y axis' div."""
    if facet_variable:
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


@app.callback(
    Output('color_label_div', 'style'),
    Input('color_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_color_label_div_style(color_variable: str | None) -> dict:
    """Toggle the color label div."""
    if color_variable:
        return {'width': '100%', 'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('facet_label_div', 'style'),
    Input('facet_variable_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_facet_label_div_style(facet_variable: str | None) -> dict:
    """Toggle the facet label div."""
    if facet_variable:
        return {'width': '100%', 'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('cohort_conversion_rate_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_cohort_conversion_rate_div_style(graph_type: str) -> dict:
    """Toggle the cohort conversion rate div."""
    if graph_type == 'cohorted conversion rates':
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('show_record_count_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_show_record_count_div_style(graph_type: str) -> dict:
    """Toggle the show record count div."""
    if graph_type == 'cohorted conversion rates':
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('cohort_adoption_rate_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_cohort_adoption_rate_div_style(graph_type: str) -> dict:
    """Toggle the cohort adoption rate div."""
    if graph_type == 'cohorted adoption rates':
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('last_n_cohorts_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_last_n_cohorts_div_style(graph_type: str) -> dict:
    """Toggle the last n cohorts div."""
    if graph_type == 'cohorted adoption rates':
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output('show_unfinished_cohorts_div', 'style'),
    Input('graph_type_dropdown', 'value'),
    prevent_initial_call=True,
)
def update_show_unfinished_cohorts_div_style(graph_type: str) -> dict:
    """Toggle the show unfinished cohorts div."""
    if graph_type == 'cohorted adoption rates':
        return {'display': 'block'}
    return {'display': 'none'}


if __name__ == '__main__':
    app.run_server(host=HOST, debug=DEBUG, port=PORT)
