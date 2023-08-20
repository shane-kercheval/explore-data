from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

default_csv_url = 'https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv'

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children='Title of Dash App', style={'textAlign':'center'}),
    dcc.Input(id='csv-url', type='text', value=default_csv_url),
    html.Button('Load', id='load-button', n_clicks=0),
    dcc.Dropdown(id='dropdown-selection'),
    dcc.Graph(id='graph-content'),
    html.Label('Filter Year Range:'),
    dcc.RangeSlider(id='year-range', marks={}, step=None),
])

@callback(
    [Output('dropdown-selection', 'options'),
     Output('dropdown-selection', 'value')],
    [Input('csv-url', 'value'),
     Input('load-button', 'n_clicks')]
)
def update_dropdown(csv_url, n_clicks):
    df = pd.read_csv(csv_url)
    country_options = [{'label': country, 'value': country} for country in df.country.unique()]
    default_country = df.country.unique()[0]
    year_marks = {str(year): str(year) for year in df.year.unique()}
    return country_options, default_country

@callback(
    [Output('graph-content', 'figure'),
     Output('year-range', 'marks'),
     Output('year-range', 'min'),
     Output('year-range', 'max'),
     Output('year-range', 'value')],
    [Input('dropdown-selection', 'value'),
     Input('load-button', 'n_clicks')]
)
def update_graph(value, n_clicks):
    df = pd.read_csv(default_csv_url)  # Read the CSV again using the default URL
    dff = df[df.country==value]
    year_marks = {str(year): str(year) for year in dff.year.unique()}
    min_year = min(dff.year)
    max_year = max(dff.year)
    selected_year_range = [min_year, max_year]
    return (
        px.line(dff, x='year', y='pop'),
        year_marks,
        min_year,
        max_year,
        selected_year_range
    )


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)
