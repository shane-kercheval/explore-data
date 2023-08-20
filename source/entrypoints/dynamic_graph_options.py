import base64
import io
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import os

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        dcc.Input(id='url-input', placeholder='Enter a URL...', type='text'),
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
            },
            multiple=False,
        ),
        html.Button('Load Data', id='load-button'),
    ]),
    html.Div(id='storage', style={'display': 'none'}),
    html.Div(id='column-select-div'),
    html.Div(id='graph-options-div'),
    html.Div(id='display-graph')
])

@app.callback(
    Output('storage', 'children'),
    Input('load-button', 'n_clicks'),
    State('url-input', 'value'),
    State('upload-data', 'contents'),
    prevent_initial_call=True
)
def load_data(n, url, contents):
    if url:
        df = pd.read_csv(url)
    elif contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        except:
            df = pd.read_pickle(io.BytesIO(decoded))
    df.to_pickle('temp.pkl')
    return 'Data Loaded'

@app.callback(
    Output('column-select-div', 'children'),
    Input('storage', 'children'),
    prevent_initial_call=True
)
def select_columns(storage_content):
    if storage_content == 'Data Loaded':
        df = pd.read_pickle('temp.pkl')
        options = [{'label': col, 'value': col} for col in df.columns]
        return [
            dcc.Checklist(options=options, id='column-checklist'),
            html.Button('Select Columns', id='select-columns-button')
        ]
    return []

@app.callback(
    Output('graph-options-div', 'children'),
    Input('select-columns-button', 'n_clicks'),
    State('column-checklist', 'value'),
    prevent_initial_call=True
)
def graph_options(n, columns):
    if not columns:
        return []
    df = pd.read_pickle('temp.pkl')
    column_types = df[columns].dtypes
    if 'object' in column_types.values:
        return [dcc.Dropdown(options=[{'label': 'Bar Chart', 'value': 'bar'}, {'label': 'Pie Chart', 'value': 'pie'}], id='graph-dropdown')]
    else:
        return [dcc.Dropdown(options=[{'label': 'Line Chart', 'value': 'line'}, {'label': 'Scatter Plot', 'value': 'scatter'}], id='graph-dropdown')]

@app.callback(
    Output('display-graph', 'children'),
    Input('graph-dropdown', 'value'),
    State('column-checklist', 'value'),
    prevent_initial_call=True
)
def display_graph(graph_type, columns):
    df = pd.read_pickle('temp.pkl')
    if not columns:
        return []
    if graph_type == 'bar':
        fig = px.bar(df, x=columns[0], y=columns[1:])
    elif graph_type == 'pie':
        fig = px.pie(df, names=columns[0], values=columns[1])
    elif graph_type == 'line':
        fig = px.line(df, x=columns[0], y=columns[1:])
    elif graph_type == 'scatter':
        fig = px.scatter(df, x=columns[0], y=columns[1])
    else:
        return []
    return dcc.Graph(figure=fig)

if __name__ == '__main__':
    app.run_server(debug=True)
