"""Dash app entry point."""
import base64
import io
from dash import Dash, html, dash_table, dcc, Output, Input, State, callback_context
from dash.dependencies import ALL
import plotly.express as px
import pandas as pd
import helpsk.pandas as hp
import dash_bootstrap_components as dbc
from source.library.dash_helpers import create_dropdown_control, create_slider_control, log, \
    log_function, log_variable, values_to_dropdown_options


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
    dcc.Store(id='filtered_data'),
    dcc.Store(id='filter_variables_cache'),
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
                                    id="x_variable",
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
                                    id="filter_variables",
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
                                create_slider_control(
                                    label="# of Bins",
                                    id="n_bins",
                                    min=20,
                                    max=100,
                                    step=20,
                                    value=40,
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


@app.callback(
    Output('x_variable_dropdown', 'options'),
    Output('y_variable_dropdown', 'options'),
    Output('filter_variables_dropdown', 'options'),
    Output('table_uploaded_data', 'data'),
    Output('numeric_summary', 'data'),
    Output('non_numeric_summary', 'data'),
    Output('original_data', 'data'),
    Output('filtered_data', 'data', allow_duplicate=True),
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
    log_function('load_data')
    x_variable_dropdown = []
    y_variable_dropdown = []
    filter_variables_dropdown = []
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
        # ctx_msg = json.dumps({
        #     'states': callback_context.states,
        #     'triggered': callback_context.triggered,
        #     'triggered2': callback_context.triggered[0]['prop_id'],
        #     'inputs': callback_context.inputs,
        # }, indent=2)
        # log_var('ctx_msg', ctx_msg)

        if triggered == 'upload-data.contents':
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

        options = values_to_dropdown_options(all_columns)
        data = data.to_dict('records')

        x_variable_dropdown = options
        y_variable_dropdown = options
        filter_variables_dropdown = options
        table_uploaded_data = data
        original_data = data
        filtered_data = data.copy()

    return (
        x_variable_dropdown,
        y_variable_dropdown,
        filter_variables_dropdown,
        table_uploaded_data,
        numeric_summary,
        non_numeric_summary,
        original_data,
        filtered_data,
        all_columns,
        numeric_columns,
        non_numeric_columns,
        date_columns,
        categorical_columns,
        string_columns,
    )


@app.callback(
    Output('filtered_data', 'data'),
    Input('filter-apply-button', 'n_clicks'),
    State('filter_variables_dropdown', 'value'),
    State('original_data', 'data'),
    State({'type': 'filter-control-dropdown', 'index': ALL}, 'value'),
    State({'type': 'filter-control-dropdown', 'index': ALL}, 'id'),
    State({'type': 'filter-control-slider', 'index': ALL}, 'value'),
    State({'type': 'filter-control-slider', 'index': ALL}, 'id'),
    prevent_initial_call=True,
)
def filter_data(
        n_clicks: int,  # noqa
        selected_columns: list[str],
        original_data: dict,
        dropdown_values: list[list],
        dropdown_ids: list[dict],
        slider_values: list[list],
        slider_ids: list[dict],
        ) -> dict:
    """Filter the data based on the user's selections."""
    log_function('filtered_data')
    log_variable('selected_columns', selected_columns)
    log_variable('dropdown_values', dropdown_values)
    log_variable('dropdown_ids', dropdown_ids)
    log_variable('slider_values', slider_values)
    log_variable('slider_ids', slider_ids)

    filtered_data = pd.DataFrame(original_data).copy()
    for column in selected_columns:
        log(f"Filtering on `{column}`")
        if column in [item['index'] for item in dropdown_ids]:
            for value, id in zip(dropdown_values, dropdown_ids):  # noqa
                log_variable('value', value)
                log_variable('id', id)
                if id['index'] == column and value:
                    log(f"filtering on {column} with {value}")
                    filtered_data = filtered_data[filtered_data[column].isin(value)]
        if column in [item['index'] for item in slider_ids]:
            for value, id in zip(slider_values, slider_ids):  # noqa
                print(f"value: {value}", flush=True)
                print(f"id: {id}", flush=True)
                if id['index'] == column and value:
                    log(f"filtering on {column} with {value}")
                    filtered_data = filtered_data[filtered_data[column].between(value[0], value[1])]  # noqa

    return filtered_data.to_dict('records')


@app.callback(
    Output('non_numeric_summary_table', 'data'),
    Input('non_numeric_summary', 'data'),
    prevent_initial_call=True,
)
def non_numeric_summary_table(non_numeric_summary: dict) -> dict:
    """Triggered when the user clicks on the Load button."""
    log_function('non_numeric_summary_table')
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
    log_function('numeric_summary_table')
    if numeric_summary:
        numeric_summary = pd.DataFrame(numeric_summary)
        return numeric_summary.to_dict('records')
    return []


@app.callback(
    Output('primary-graph', 'figure'),
    Output('table_visualize', 'data'),
    Input('x_variable_dropdown', 'value'),
    Input('y_variable_dropdown', 'value'),
    Input('facet_variable_dropdown', 'value'),
    Input('n_bins_slider', 'value'),
    Input('title_textbox', 'value'),
    Input('filtered_data', 'data'),
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
    log_function('update_graph')
    log_variable('x_variable', x_variable)
    log_variable('y_variable', y_variable)
    log_variable('facet_variable', facet_variable)
    log_variable('n_bins', n_bins)
    log_variable('type(n_bins)', type(n_bins))
    fig = {}
    if (x_variable or y_variable) and data:
        fig = px.histogram(
            data,
            x=x_variable,
            y=y_variable,
            title=title_textbox,
            nbins=n_bins,
        )
    return fig, data


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
    log_function('facet_variable_div')
    if x_variable_dropdown or y_variable_dropdown:
        log("returning display: block")
        options = [{'label': col, 'value': col} for col in non_numeric_columns]
        return {'display': 'block'}, options
    log("returning display: none")
    return  {'display': 'none'}, []


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
    # Output('filter_variables_cache', 'data'),  # used to cache columns and values being filtered
    Input('filter_variables_dropdown', 'value'),
    State('filter_variables_cache', 'data'),
    State('non_numeric_columns', 'data'),
    State('numeric_columns', 'data'),
    State('original_data', 'data'),

    prevent_initial_call=True,
)
def update_filter_controls(
        selected_columns: list[str],
        filter_variables_cache: dict,
        non_numeric_columns: list[str],
        numeric_columns: list[str],
        data: dict) -> list[html.Div]:
    """
    Triggered when the user selects columns from the filter dropdown.

    If the user selects a column and adds a value, and then selects another column, the value from
    the original column will be removed. This is because all of the controls are recreated. So we
    need to cache the values of the controls in the filter_variables_cache.
    """
    log_function('update_filter_controls')
    log_variable('selected_columns', selected_columns)
    log_variable('filter_variables_cache', filter_variables_cache)
    log_variable('non_numeric_columns', non_numeric_columns)
    log_variable('numeric_columns', numeric_columns)

    components = []
    if selected_columns and data:
        data = pd.DataFrame(data)
        for column in selected_columns:
            log(f"Creating controls for `{column}`")
            value = []
            if filter_variables_cache and column in filter_variables_cache:
                value = filter_variables_cache[column]
                log(f"found `{column}` in filter_variables_cache with value `{value}`")
            if column in non_numeric_columns:
                log("create dropdown")
                components.append(create_dropdown_control(
                    label=column,
                    id=f"filter_control_{column}",
                    value=value,
                    multi=True,
                    options=values_to_dropdown_options(data[column].unique()),
                    component_id={"type": "filter-control-dropdown", "index": column},
                ))
            if column in numeric_columns:
                log("create slider")
                components.append(create_slider_control(
                    label=column,
                    id=f"filter_control_{column}",
                    min=data[column].min(),
                    max=data[column].max(),
                    value=value or [data[column].min(), data[column].max()],
                    component_id={"type": "filter-control-slider", "index": column},
                ))

    log_variable('# of components', len(components))
    return components


@app.callback(
    Output('filter_variables_cache', 'data'),
    Input({'type': 'filter-control-dropdown', 'index': ALL}, 'value'),
    Input({'type': 'filter-control-dropdown', 'index': ALL}, 'id'),
    Input({'type': 'filter-control-slider', 'index': ALL}, 'value'),
    Input({'type': 'filter-control-slider', 'index': ALL}, 'id'),
    State('filter_variables_dropdown', 'value'),
    State('filter_variables_cache', 'data'),
    prevent_initial_call=True,
)
def cache_filter_variables(
        dropdown_values: list[list],
        dropdown_ids: list[dict],
        slider_values: list[list],
        slider_ids: list[dict],
        selected_columns: list[str],
        filter_variables_cache: dict,
        ) -> dict:
    """
    Cache the values from the drop and slider controls. This is used to recreate the controls when
    the user selects a new variable to filter on, which triggers the recreation of all controls.
    This is also used to filter the data.
    """
    log_function('cache_filter_variables')
    log_variable('selected_columns', selected_columns)
    log_variable('filter_variables_cache', filter_variables_cache)
    log_variable('dropdown_values', dropdown_values)
    log_variable('dropdown_ids', dropdown_ids)
    log_variable('slider_values', slider_values)
    log_variable('slider_ids', slider_ids)

    # cache the values from the dropdown and slider controls
    if filter_variables_cache is None:
        filter_variables_cache = {}
    else:
        filter_variables_cache = filter_variables_cache.copy()
        for column in filter_variables_cache:
            if column not in selected_columns:
                log(f"removing {column} from filter_variables_cache")
                # filter_variables_cache.pop(column)

    for column in selected_columns:
        log(f"caching column: `{column}`")
        if column in [item['index'] for item in dropdown_ids]:
            for value, id in zip(dropdown_values, dropdown_ids):  # noqa
                # log(f"value: {value}")
                # log(f"id: {id}")
                if id['index'] == column:
                    log(f"caching `{column}` with `{value}`")
                    filter_variables_cache[column] = value
        if column in [item['index'] for item in slider_ids]:
            for value, id in zip(slider_values, slider_ids):  # noqa
                # log(f"value: {value}")
                # log(f"id: {id}")
                if id['index'] == column:
                    log(f"caching `{column}` with `{value}`")
                    filter_variables_cache[column] = value

    log(f"filter_variables_cache: {filter_variables_cache}")
    return filter_variables_cache


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)

