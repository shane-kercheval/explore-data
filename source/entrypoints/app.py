"""Dash app entry point."""
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
                    dcc.Slider(
                        10, 100, 20,
                        value=40,
                        id='n_bins',
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
    Output('column-dropdown', 'options'),
    Output('column-dropdown', 'value'),
    Output('data-store', 'data'),
    Output('table', 'data'),
    Output('table3', 'data'),
    Input('load-button', 'n_clicks'),
    State('url-input', 'value'),
)
def load_data(n_clicks: int, url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    print("load_data", flush=True)
    if n_clicks > 0 and url:
        data = pd.read_csv(url)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        options = [{'label': col, 'value': col} for col in numeric_cols]
        data = data.to_dict('records')
        return options, [], data, data, data
    return [], [], None, None, None

@app.callback(
    Output('primary-graph', 'figure'),
    Input('column-dropdown', 'value'),
    Input('n_bins', 'value'),
    State('data-store', 'data'),
)
def update_graph(
            selected_columns: list,
            n_bins: int,
            data: dict,
        ) -> dict:
    """Triggered when the user selects columns from the dropdown."""
    print("update_graph", flush=True)
    fig = {}
    if selected_columns and data:
        fig = px.histogram(data, x=selected_columns[0], y=selected_columns[0], nbins=n_bins)
        # print("graph", flush=True)
        # print(f"selected_columns[0]: {selected_columns[0]}", flush=True)
        # graphs = []
        # for col in selected_columns:
        #     for graph_type in graph_options:
        #         if graph_type == 'histogram':
        #             graphs.append({'x': data[col], 'type': 'histogram', 'name': f'{col} (histogram)'})
        #         elif graph_type == 'scatter':
        #             graphs.append({'x': data.index, 'y': data[col], 'mode': 'markers', 'name': f'{col} (scatter)'})
        # return {'data': graphs, 'layout': {'title': 'Graphs'}}
    return fig


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)

# https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv


# First, install the necessary packages if you haven't already:
# pip install dash dash-core-components dash-html-components plotly

# import dash
# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output
# import plotly.express as px
# import numpy as np

# # Sample data
# x = np.linspace(0, 10, 100)
# y = np.sin(x)

# # Create the Dash app
# app = dash.Dash(__name__)

# app.layout = html.Div([
#     # Left side panel
#     html.Div([
#         html.Label("Choose a Graph Type:"),
#         dcc.Dropdown(
#             id='graph-type-dropdown',
#             options=[
#                 {'label': 'Bar Graph', 'value': 'bar'},
#                 {'label': 'Line Graph', 'value': 'line'}
#             ],
#             value='bar'
#         ),
#     ], style={'width': '20%', 'float': 'left', 'borderRight': 'thin lightgrey solid', 'padding': '20px'}),

#     # Right side for graph display
#     html.Div([
#         dcc.Graph(id='displayed-graph')
#     ], style={'width': '75%', 'float': 'right', 'padding': '20px'}),
# ])

# @app.callback(
#     Output('displayed-graph', 'figure'),
#     [Input('graph-type-dropdown', 'value')]
# )
# def update_graph(graph_type):
#     if graph_type == 'bar':
#         fig = px.bar(x=x, y=y, labels={'x': 'X values', 'y': 'Y values'}, title="Bar Graph")
#     elif graph_type == 'line':
#         fig = px.line(x=x, y=y, labels={'x': 'X values', 'y': 'Y values'}, title="Line Graph")
#     else:
#         fig = {}
#     return fig


# if __name__ == '__main__':
#     app.run_server(host='0.0.0.0', debug=True, port=8050)
