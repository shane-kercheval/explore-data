"""Dash app entry point."""
from dash import Dash, html, dash_table, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np

app = Dash(__name__)

app.layout = html.Div([
    html.H1("CSV Data Visualization"),
    dcc.Input(
        id='url-input',
        type='text',
        placeholder='Enter CSV URL',
        value='https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv',
    ),
    html.Button('Load', id='load-button', n_clicks=0),
    html.Br(),html.Br(),
    html.Label("Select numeric columns:"),
    dcc.Dropdown(id='column-dropdown', multi=True),
    dcc.Store(id='data-store'),  # Store component to hold the loaded data
    dcc.Graph(id='primary-graph'),
    dash_table.DataTable(id='table', page_size=20),
])

@app.callback(
    [
        Output('column-dropdown', 'options'),
        Output('column-dropdown', 'value'),
        Output('data-store', 'data'),  # Update the data in the store
        Output('table', 'data'),
    ],
    [
        Input('load-button', 'n_clicks'),
    ],
    [
        State('url-input', 'value'),
    ],
)
def load_data(n_clicks: int, url: str) -> tuple:
    """Triggered when the user clicks on the Load button."""
    if n_clicks > 0 and url:
        loaded_data = pd.read_csv(url)
        numeric_columns = loaded_data.select_dtypes(include=[np.number]).columns
        dropdown_options = [{'label': col, 'value': col} for col in numeric_columns]
        loaded_data = loaded_data.to_dict('records')
        return dropdown_options, [], loaded_data, loaded_data  # Store data in the store
    return [], [], None, None

@app.callback(
    [
        Output('primary-graph', 'figure'),
    ],
    [
        Input('column-dropdown', 'value'),
    ],
    [
        State('data-store', 'data'),
    ],  # Access the data from the store
)
def update_histogram(selected_columns: str, data_store: dict) -> dict:
    """Triggered when the user selects a column from the dropdown."""
    if data_store and selected_columns:
        loaded_data = pd.DataFrame.from_records(data_store)  # Convert stored data to DataFrame
        data = []
        for col in selected_columns:
            data.append({'x': loaded_data[col], 'type': 'histogram', 'name': col})
        return {'data': data, 'layout': {'title': 'Histogram'}}
    return {'data': [], 'layout': {'title': 'Histogram'}}


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)

# https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv
