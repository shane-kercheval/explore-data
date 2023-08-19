"""Dash app for exploring data."""
from dash import Dash, html

app = Dash(__name__)
#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/hello-world-stock.csv')

print('hello2')

app.layout = html.Div([
    html.Div(children='Hello World'),
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)
