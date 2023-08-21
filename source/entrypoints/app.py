"""Dash app entry point."""
import base64
import io
from dash import Dash, html, dash_table, dcc, Output, Input, State, callback_context
import plotly.express as px
import pandas as pd
import helpsk.pandas as hp
import dash_bootstrap_components as dbc


GOLDEN_RATIO = 1.618


external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    # 'https://codepen.io/chriddyp/pen/bWLwgP.css',
]
app = Dash(__name__, title="Data Explorer", external_stylesheets=external_stylesheets)


def create_dropdown_control(
        label: str,
        name: str,
        multi: bool = False,
        options: list[dict] | None = None,
        value: str | None = None,
        placeholder: str | None = None,
        ) -> html.Div:
    """Create a dropdown control."""
    if options is None:
        options = []
    return create_control(
        label=label,
        name=name,
        component=dcc.Dropdown(
            id=f'{name}_dropdown',
            multi=multi,
            options=options,
            value=value,
            placeholder=placeholder,
        ),
    )

def create_control(label: str, name: str, component: html.Div) -> html.Div:
    """Create a generic control with a given component (e.g. dropdown)."""
    return html.Div(
        id=f'{name}_div',
        className='graph_options',
        children=[
            html.Label(
                f"{label}:",
                className='graph_options_label',
            ),
            component,
    ])


app.layout = dbc.Container(className="app-container", fluid=True, style={"max-width": "99%"}, children=[  # noqa
    dcc.Store(id='data_store'),
    dcc.Store(id='numeric_summary'),
    dcc.Store(id='non_numeric_summary'),
    dcc.Store(id='all_columns'),
    dcc.Store(id='numeric_columns'),
    dcc.Store(id='non_numeric_columns'),
    dcc.Store(id='date_columns'),
    dcc.Store(id='categorical_columns'),
    dcc.Store(id='string_columns'),
    dbc.Tabs([
        dbc.Tab(label="Load Data", children=[
            dcc.Loading(type="default", children=[
            html.Br(),
            dbc.Row([
                dbc.Col(width=3, children=[
                    html.H4("Load .csv or .pkl from file"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
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
                dbc.Col(width=1, children=[]),
                dbc.Col(width=7, children=[
                    html.H4("Load .csv from URL"),
                    html.Button(
                        'Load',
                        id='load_from_url_button',
                        n_clicks=0,
                        style={'width': '20%', 'padding': '0px'},
                    ),
                    dcc.Input(
                        id='load_from_url',
                        type='text',
                        placeholder='Enter CSV URL',
                        # value='https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv',
                        value='https://raw.githubusercontent.com/fivethirtyeight/data/master/bechdel/movies.csv',
                        style={
                            'width': '80%',
                        },
                    ),
                ]),
            ]),
            html.Br(),
            dbc.Row(children=[
                html.Hr(),
                dash_table.DataTable(
                    id='table_uploaded_data',
                    page_size=20,
                    style_header={
                        'fontWeight': 'bold',
                    },
                ),
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
                                    name="x_variable",
                                    placeholder="Select a variable",
                                ),
                                create_dropdown_control(
                                    label="Y variable",
                                    name="y_variable",
                                    placeholder="Select a variable",
                                ),
                                create_dropdown_control(
                                    label="Facet variable",
                                    name="facet_variable",
                                    placeholder="Select a variable",
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
                                dbc.Button(
                                    "Clear",
                                    id="filter-clear-button",
                                    style={'margin': '0 20px 20px 0'},
                                ),
                                create_dropdown_control(
                                    label="Variables",
                                    name="filter_variables",
                                    multi=True,
                                ),
                                html.Div(
                                    id='dynamic-filter-controls',
                                    style={'margin': '15px 0 10px 0'},
                                    className='graph_options',
                                ),
                            ]),
                        ]),
                    ]),
                    dbc.Card(style={'margin': '10px 0 10px 0'}, children=[
                        dbc.CardHeader(
                            dbc.Button(
                                "Graph Options",
                                id="panel-graph-options-toggle",
                                className="panel_toggle_button",
                            ),
                        ),
                        dbc.Collapse(id="collapse-graph-options", is_open=True, children=[
                            dbc.CardBody([
                                html.Div(
                                    id='n_bins_div',
                                    className='graph_options',
                                    # style={'display': 'none'},
                                    children=[
                                        html.Label(
                                            "# of Bins:",
                                            className='graph_options_label',
                                        ),
                                        dcc.Slider(
                                            10, 100, 20,
                                            value=40,
                                            id='n_bins',
                                        ),
                                        html.Br(),
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
                        dbc.Collapse(id="collapse-other-options", is_open=True, children=[
                            dbc.CardBody([
                                html.Div(
                                    id='title_div',
                                    className='graph_options',
                                    # style={'display': 'none'},
                                    children=[
                                        html.Label(
                                            "Title:",
                                            className='graph_options_label',
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
                    dcc.Graph(
                        id='primary-graph',
                        config={'staticPlot': False, 'displayModeBar': True},
                        # 3/12 because the sidebar is 3/12 of the width
                        style={'width': '100%', 'height': f'{(1-(3/12)) / GOLDEN_RATIO * 100: .1f}vw'},  # noqa
                    ),
                    html.Hr(),
                    dash_table.DataTable(
                        id='table_visualize',
                        page_size=20,
                        style_header={
                            'fontWeight': 'bold',
                        },
                    ),
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


def columns_to_options(columns: list[str]) -> list[dict]:
    """Convert a list of columns to a list of options for a dropdown."""
    return [{'label': col, 'value': col} for col in columns]


@app.callback(
    Output('dynamic-filter-controls', 'children'),
    Input('filter-apply-button', 'n_clicks'),
    State('filter_variables_dropdown', 'value'),
    State('non_numeric_columns', 'data'),
    State('numeric_columns', 'data'),
    State('data_store', 'data'),
    prevent_initial_call=True,
)
def update_filter_controls(
        filter_apply_button: int,
        selected_columns: list[str],
        non_numeric_columns: list[str],
        numeric_columns: list[str],
        data: dict) -> list[html.Div]:
    """Triggered when the user selects columns from the filter dropdown."""
    print("update_filter_controls", flush=True)
    print("selected_columns", selected_columns, flush=True)
    components = []
    if selected_columns and data:
        data = pd.DataFrame(data)
        for column in selected_columns:
            print(f"Creating controls for `{column}`", flush=True)
            if column in non_numeric_columns:
                print('create dropdown', flush=True)
            if column in numeric_columns:
                print('create slider', flush=True)
    return components



@app.callback(
    Output("collapse-variables", "is_open"),
    Input("panel-variables-toggle", "n_clicks"),
    State("collapse-variables", "is_open"),
    prevent_initial_call=True,
)
def toggle_variables_panel(n: int, is_open: bool) -> bool:
    """Toggle the variables panel."""
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
    if n:
        return not is_open
    return is_open


@app.callback(
    Output('non_numeric_summary_table', 'data'),
    Input('non_numeric_summary', 'data'),
    prevent_initial_call=True,
)
def non_numeric_summary_table(non_numeric_summary: dict) -> dict:
    """Triggered when the user clicks on the Load button."""
    if non_numeric_summary:
        non_numeric_summary = pd.DataFrame(non_numeric_summary)
        return non_numeric_summary.to_dict('records')
    return []


@app.callback(
    Output('numeric_summary_table', 'data'),
    Input('numeric_summary', 'data'),
    prevent_initial_call=True,
)
def numeric_summary_table(numeric_summary: dict) -> dict:
    """Triggered when the user clicks on the Load button."""
    if numeric_summary:
        numeric_summary = pd.DataFrame(numeric_summary)
        return numeric_summary.to_dict('records')
    return []


@app.callback(
    Output('x_variable_dropdown', 'options'),
    Output('y_variable_dropdown', 'options'),
    Output('filter_variables_dropdown', 'options'),
    Output('table_visualize', 'data'),
    Output('table_uploaded_data', 'data'),
    Output('numeric_summary', 'data'),
    Output('non_numeric_summary', 'data'),
    Output('data_store', 'data'),
    Output('all_columns', 'data'),
    Output('numeric_columns', 'data'),
    Output('non_numeric_columns', 'data'),
    Output('date_columns', 'data'),
    Output('categorical_columns', 'data'),
    Output('string_columns', 'data'),
    Input('load_from_url_button', 'n_clicks'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('load_from_url', 'value'),
    prevent_initial_call=True,
)
def load_data(  # noqa
        load_from_url_button: int,
        upload_data_contents: str,
        upload_data_filename: str,
        load_from_url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    print("load_data()", flush=True)
    x_variable_dropdown = []
    y_variable_dropdown = []
    filter_variables_dropdown = []
    table_visualize = None
    table_uploaded_data = None
    numeric_summary = None
    non_numeric_summary = None
    data_store = None
    all_columns = None
    numeric_columns = None
    non_numeric_columns = None
    date_columns = None
    categorical_columns = None
    string_columns = None

    if callback_context.triggered:
        triggered = callback_context.triggered[0]['prop_id']
        print(f"triggered: {triggered}", flush=True)
        # ctx_msg = json.dumps({
        #     'states': callback_context.states,
        #     'triggered': callback_context.triggered,
        #     'triggered2': callback_context.triggered[0]['prop_id'],
        #     'inputs': callback_context.inputs,
        # }, indent=2)
        # print(ctx_msg, flush=True)

        if triggered == 'upload-data.contents':
            print(f"load_from_url_button: {load_from_url_button}", flush=True)
            print(f"upload_data_filename: {upload_data_filename}", flush=True)
            _, content_string = upload_data_contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                if '.pkl' in upload_data_filename:
                    print("loading from .pkl", flush=True)
                    data = pd.read_pickle(io.BytesIO( base64.b64decode(content_string)))
                if '.csv' in upload_data_filename:
                    print("loading from .csv", flush=True)
                    # Assume that the user uploaded a CSV file
                    data = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                elif 'xls' in upload_data_filename:
                    print("loading from .xls", flush=True)
                    # Assume that the user uploaded an excel file
                    data = pd.read_excel(io.BytesIO(decoded))
            except Exception as e:
                print(e)
                # print(e.with_traceback())
                return html.Div([
                    'There was an error processing this file.',
                ])
        elif triggered == 'load_from_url_button.n_clicks' and load_from_url:
            print("Loading from CSV URL", flush=True)
            data = pd.read_csv(load_from_url)
        else:
            raise ValueError(f"Unknown trigger: {triggered}")

        all_columns = data.columns.tolist()
        numeric_columns = hp.get_numeric_columns(data)
        non_numeric_columns = hp.get_non_numeric_columns(data)
        date_columns = hp.get_date_columns(data)
        categorical_columns = hp.get_categorical_columns(data)
        string_columns = hp.get_string_columns(data)

        numeric_summary = hp.numeric_summary(data, return_style=False)
        if numeric_summary is not None and len(numeric_summary) > 0:
            numeric_summary = numeric_summary.\
                reset_index().\
                rename(columns={'index': 'Column Name'}).\
                to_dict('records')
        else:
            numeric_summary = None

        non_numeric_summary = hp.non_numeric_summary(data, return_style=False)
        if non_numeric_summary is not None and len(non_numeric_summary) > 0:
            non_numeric_summary = non_numeric_summary.\
                reset_index().\
                rename(columns={'index': 'Column Name'}).\
                to_dict('records')
        else:
            non_numeric_summary = None

        options = columns_to_options(all_columns)
        data = data.to_dict('records')

        x_variable_dropdown = options
        y_variable_dropdown = options
        filter_variables_dropdown = options
        table_visualize = data
        table_uploaded_data = data
        data_store = data

    return (
        x_variable_dropdown,
        y_variable_dropdown,
        filter_variables_dropdown,
        table_visualize,
        table_uploaded_data,
        numeric_summary,
        non_numeric_summary,
        data_store,
        all_columns,
        numeric_columns,
        non_numeric_columns,
        date_columns,
        categorical_columns,
        string_columns,
    )


@app.callback(
    Output('primary-graph', 'figure'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('facet_variable_dropdown', 'value'),
    Input('n_bins', 'value'),
    Input('title_textbox', 'value'),
    State('data_store', 'data'),
    prevent_initial_call=True,
)
def update_graph(
            x_variable: str,
            y_variable: str,
            facet_variable: str,
            n_bins: int,
            title_textbox: str,
            data: dict,
        ) -> dict:
    """Triggered when the user selects columns from the dropdown."""
    print("update_graph", flush=True)
    print("x_variable", x_variable, flush=True)
    print("y_variable", y_variable, flush=True)
    fig = {}
    if x_variable and data:
        fig = px.histogram(
            data,
            x=x_variable,
            y=y_variable,
            title=title_textbox,
            nbins=n_bins,
        )
    return fig


@app.callback(
    Output('facet_variable_div', 'style'),
    Output('facet_variable_dropdown', 'options'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    State('non_numeric_columns', 'data'),
    prevent_initial_call=True,
)
def facet_variable_div(
        x_variable_dropdown: str,
        y_variable_dropdown: str,
        non_numeric_columns: dict) -> dict:
    """Triggered when the user selects columns from the dropdown."""
    print("facet_variable_div", flush=True)
    if x_variable_dropdown or y_variable_dropdown:
        print("returning display: block", flush=True)
        options = [{'label': col, 'value': col} for col in non_numeric_columns]
        return {'display': 'block'}, options
    print('returning display: none', flush=True)
    return  {'display': 'none'}, []


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)

# https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv
