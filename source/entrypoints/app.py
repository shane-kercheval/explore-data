"""Dash app entry point."""
import base64
import io
import json
from dash import Dash, html, dash_table, dcc, Output, Input, State, callback_context
import plotly.express as px
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

# prints the current working directory
import os
print(os.getcwd())

external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    'custom.css',
]
app = Dash(__name__, external_stylesheets=external_stylesheets)
# external_stylesheets = None
# external_stylesheets = [dbc.themes.BOOTSTRAP]#, 'custom.css']
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Tabs([
        dbc.Tab(label="Load Data", children=[
            html.Br(),
            dbc.Row([
                dbc.Col(width=3, children=[
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
                    html.Br(),html.Br(),
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
                dbc.Col(width=9, children=[
                    dash_table.DataTable(id='table_uploaded_data', page_size=20),
                ]),
            ]),
        ]),
        dbc.Tab(label="Visualize", children=[
            dbc.Row([
                dbc.Col(width=3, children=[
                    html.Br(),
                    html.Div(className="options-panel", children=[
                        html.Label("Select x variable:"),
                        dcc.Dropdown(
                            id='x_column_dropdown',
                            multi=False,
                            value=None,
                            placeholder="Select a variable",
                        ),
                        html.Br(),
                        html.Label("Select y variable:"),
                        dcc.Dropdown(
                            id='y_column_dropdown',
                            multi=False,
                            value=None,
                            placeholder="Select a variable",
                        ),
                        html.Br(),
                        html.Label("Graph options:"),
                        dcc.Slider(
                            10, 100, 20,
                            value=40,
                            id='n_bins',
                        ),
                    ]),
                ]),
                dbc.Col(width=9, children=[
                    dcc.Store(id='data_store'),
                    # dcc.Graph(id='primary-graph'),
                    dcc.Graph(
                        id='primary-graph',
                        config={'staticPlot': False, 'displayModeBar': True},
                        style={'width': '100%', 'height': '41.9vw'},  # 100% / 1.6 = 62.5%; (1-.33)/1.6 = .41875
                    ),
                    dash_table.DataTable(id='table_visualize', page_size=20),
                ]),
            ]),
        ]),
    ]),
], className="app-container", fluid=True, style={"max-width": "99%"})


@app.callback(
    Output('x_column_dropdown', 'options'),
    Output('x_column_dropdown', 'value'),
    Output('y_column_dropdown', 'options'),
    Output('y_column_dropdown', 'value'),
    Output('data_store', 'data'),
    Output('table_visualize', 'data'),
    Output('table_uploaded_data', 'data'),
    Input('load_from_url_button', 'n_clicks'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('load_from_url', 'value'),
    prevent_initial_call=True,
)
def load_data(load_from_url_button: int, upload_data_contents: str, upload_data_filename: str, load_from_url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    print("load_data()", flush=True)
    if not callback_context.triggered:
        print("not triggered")
        print(f"callback_context.triggered: `{callback_context.triggered}`", flush=True)
        return [], None, [], None, None, None, None

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

    options = [{'label': col, 'value': col} for col in data.columns]
    data = data.to_dict('records')
    return options, None, options, None, data, data, data


@app.callback(
    Output('primary-graph', 'figure'),
    Input('x_column_dropdown', 'value'),
    Input('y_column_dropdown', 'value'),
    Input('n_bins', 'value'),
    State('data_store', 'data'),
    prevent_initial_call=True,
)
def update_graph(
            x_column: list,
            y_column: list,
            n_bins: int,
            data: dict,
        ) -> dict:
    """Triggered when the user selects columns from the dropdown."""
    print("update_graph", flush=True)
    print("x_column", x_column, flush=True)
    print("y_column", y_column, flush=True)
    fig = {}
    if x_column and data:
        fig = px.histogram(
            data,
            x=x_column,
            y=y_column,
            nbins=n_bins,
        )
    return fig


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)

# https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv
