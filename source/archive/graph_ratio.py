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
    dcc.Dropdown(
        id='graph-dropdown',
        options=[
            {'label': 'Iris Scatter Plot', 'value': 'iris_scatter'},
            {'label': 'Tips Histogram', 'value': 'tips_histogram'}
        ],
        value='iris_scatter',
        clearable=False
    ),
    dcc.Graph(
        id='example-graph',
        config={'staticPlot': False, 'displayModeBar': True},
        style={'width': '100%', 'height': '62.5vw'}  # 100% / 1.6 = 62.5%
    )
])

@app.callback(
    Output('example-graph', 'figure'),
    Input('graph-dropdown', 'value')
)
def update_graph(selected_graph):
    if selected_graph == 'iris_scatter':
        df = px.data.iris()
        fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species", size="petal_length")
    elif selected_graph == 'tips_histogram':
        df = px.data.tips()
        fig = px.histogram(df, x="total_bill", color="sex")
    else:
        fig = px.scatter()  # default to an empty scatter plot

    # Adjust margins
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))

    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)
