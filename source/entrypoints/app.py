"""Dash app entry point."""
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
                            html.A('Select Files', style={'color': 'blue'})
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
                    dash_table.DataTable(id='table3', page_size=20),
                ]),
            ]),
        ]),
        dbc.Tab(label="Visualize", children=[
            dbc.Row([
                dbc.Col(width=3, children=[
                    html.Div(className="split-view", children=[
                        html.Div(className="options-panel", children=[
                            html.Label("Select x variable:"),
                            dcc.Dropdown(
                                id='x_column_dropdown',
                                multi=False,
                                value=None,
                                placeholder="Select a variable",
                            ),
                            html.Label("Select y variable:"),
                            dcc.Dropdown(
                                id='y_column_dropdown',
                                multi=False,
                                value=None,
                                placeholder="Select a variable",
                            ),
                            html.Label("Graph options:"),
                            dcc.Slider(
                                10, 100, 20,
                                value=40,
                                id='n_bins',
                            ),
                        ]),
                    ]),
                ]),
                dbc.Col(width=9, children=[
                    html.Div(className="visualization-panel", children=[
                        dcc.Store(id='data_store'),
                        # dcc.Graph(id='primary-graph'),
                        dcc.Graph(
                            id='primary-graph',
                            config={'staticPlot': False, 'displayModeBar': True},
                            style={'width': '100%', 'height': '41.9vw'},  # 100% / 1.6 = 62.5%; (1-.33)/1.6 = .41875
                        ),
                        dash_table.DataTable(id='table', page_size=20),
                    ]),
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
    Output('table', 'data'),
    Output('table3', 'data'),
    Input('load_from_url_button', 'n_clicks'),
    State('load_from_url', 'value'),
)
def load_data(load_from_url_button: int, load_from_url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    print("load_data()", flush=True)
    triggered = callback_context.triggered[0]['prop_id']
    print(f"triggered: {triggered}", flush=True)
    # ctx = callback_context
    # ctx_msg = json.dumps({
    #     'states': ctx.states,
    #     'triggered': ctx.triggered,
    #     'inputs': ctx.inputs,
    # }, indent=2)
    # print(ctx_msg, flush=True)
    if triggered == 'load_from_url_button.n_clicks' and load_from_url:
        print("Loading from CSV URL", flush=True)
        data = pd.read_csv(load_from_url)
        # numeric_cols = data.select_dtypes(include=[np.number]).columns
        options = [{'label': col, 'value': col} for col in data.columns]
        data = data.to_dict('records')
        return options, None, options, None, data, data, data
    return [], None, [], None, None, None, None


@app.callback(
    Output('primary-graph', 'figure'),
    Input('x_column_dropdown', 'value'),
    Input('y_column_dropdown', 'value'),
    Input('n_bins', 'value'),
    State('data_store', 'data'),
)
def update_graph(
            x_column: list,
            y_column: list,
            n_bins: int,
            data: dict,
        ) -> dict:
    """Triggered when the user selects columns from the dropdown."""
    print("update_graph", flush=True)
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
