"""Dash app entry point."""
from dash import Dash, html, dash_table, dcc
from dash.dependencies import Input, Output, State
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

app.layout = html.Div([
    dbc.Tabs([
        dbc.Tab(label="Load Data", children=[
            dcc.Input(
                id='url-input',
                type='text',
                placeholder='Enter CSV URL',
                value='https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv',
            ),
            html.Button('Load', id='load-button', n_clicks=0),
            html.Br(), html.Br(),
            dash_table.DataTable(id='table3', page_size=20),
        ]),
        dbc.Tab(label="Visualize", children=[
            html.Div(className="split-view", children=[
                html.Div(className="options-panel", children=[
                    html.Label("Select numeric columns:"),
                    dcc.Dropdown(id='column-dropdown', multi=True),
                    html.Label("Graph options:"),
                    dcc.Checklist(
                        id='graph-options',
                        options=[
                            {'label': 'Show histogram', 'value': 'histogram'},
                            {'label': 'Show scatter plot', 'value': 'scatter'}
                        ],
                        value=['histogram'],
                    ),
                ]),
                html.Div(className="visualization-panel", children=[
                    dcc.Store(id='data-store'),
                    dcc.Graph(id='primary-graph'),
                    dash_table.DataTable(id='table', page_size=20),
                ]),
            ]),
        ]),
    ]),
], className="app-container")

@app.callback(
    [
        Output('column-dropdown', 'options'),
        Output('column-dropdown', 'value'),
        Output('data-store', 'data'),
        Output('table', 'data'),
        Output('table3', 'data'),
    ],
    [
        Input('load-button', 'n_clicks')
    ],
    [
        State('url-input', 'value')
    ],
)
def load_data(n_clicks: int, url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    if n_clicks > 0 and url:
        data = pd.read_csv(url)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        options = [{'label': col, 'value': col} for col in numeric_cols]
        data = data.to_dict('records')
        return options, [], data, data, data
    return [], [], None, None, None

@app.callback(
    Output('primary-graph', 'figure'),
    [Input('column-dropdown', 'value'), Input('graph-options', 'value')],
    [State('data-store', 'data')]
)
def update_graph(selected_columns: list, graph_options: list, data: dict) -> dict:
    """Triggered when the user selects columns from the dropdown."""
    if selected_columns and data:
        data = pd.DataFrame(data)
        graphs = []
        for col in selected_columns:
            for graph_type in graph_options:
                if graph_type == 'histogram':
                    graphs.append({'x': data[col], 'type': 'histogram', 'name': f'{col} (histogram)'})
                elif graph_type == 'scatter':
                    graphs.append({'x': data.index, 'y': data[col], 'mode': 'markers', 'name': f'{col} (scatter)'})
        return {'data': graphs, 'layout': {'title': 'Graphs'}}
    return {'data': [], 'layout': {}}

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)

# https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv
