# app.py
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.express as px

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    dcc.Graph(
        id='example-graph',
        config={'staticPlot': False, 'displayModeBar': True},
        style={'width': '100%', 'height': '62.5vw'},  # 100% / 1.6 = 62.5%
    )
])

@app.callback(
    Output('example-graph', 'figure'),
    Input('example-graph', 'relayoutData'),
)
def update_graph(relayoutData):
    # A simple scatter plot using plotly_express
    df = px.data.iris()
    fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species", size="petal_length", title="Resize and Watch the Ratio!")
    # Adjust margins
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))

    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)
