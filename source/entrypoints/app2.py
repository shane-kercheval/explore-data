# Import necessary libraries
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# Dummy data
df = {
    'x': [1, 2, 3, 4, 5],
    'y': [5, 4, 3, 2, 1]
}

# Initialize the Dash app with bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    # Tabs at the top
    dbc.Tabs([
        dbc.Tab(label="Tab 1", children=[
            html.Div([
                html.H1("Content of Tab 1"),
            ]),
        ]),
        dbc.Tab(label="Tab 2", children=[
            # Sidebar
            dbc.Row([
                dbc.Col(
                    [
                        html.H2("Graph Options"),
                        html.Hr(),
                        html.Label("Select X-axis data:"),
                        dcc.Dropdown(
                            id="x-axis-dropdown",
                            options=[
                                {"label": "X Data", "value": "x"},
                            ],
                            value="x",
                        ),
                        html.Label("Select Y-axis data:"),
                        dcc.Dropdown(
                            id="y-axis-dropdown",
                            options=[
                                {"label": "Y Data", "value": "y"},
                            ],
                            value="y",
                        ),
                        html.Button("Plot", id="plot-button"),
                    ],
                    width=3,
                ),
                # Main content for Tab 2
                dbc.Col(
                    [
                        dcc.Graph(id="main-graph"),
                    ],
                ),
            ]),
        ]),
    ]),
])

@app.callback(
    Output("main-graph", "figure"),
    [Input("plot-button", "n_clicks")],
    [Input("x-axis-dropdown", "value"),
     Input("y-axis-dropdown", "value")]
)
def update_graph(n_clicks, x_value, y_value):
    if n_clicks:
        return {
            "data": [
                go.Scatter(
                    x=df[x_value],
                    y=df[y_value],
                    mode="lines+markers"
                )
            ],
            "layout": go.Layout(title="Generated Graph")
        }
    else:
        return go.Figure()


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
