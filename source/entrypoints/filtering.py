# Import necessary libraries
import dash
from dash import dcc, html, Input, Output, State
from dash.dependencies import ALL
import pandas as pd

# Initialize the Dash app
app = dash.Dash(__name__)

# Read data from CSV URL
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

# App layout
app.layout = html.Div([
    dcc.Dropdown(
        id='column-dropdown',
        options=[{'label': col, 'value': col} for col in df.columns],
        multi=True,
        value=[]
    ),
    html.Div(id='dynamic-controls'),
    html.Button('Apply Filter', id='apply-button'),
    html.Div(id='filtered-data-display')
])

@app.callback(
    Output('dynamic-controls', 'children'),
    Input('column-dropdown', 'value'),
)
def update_controls(selected_columns):
    components = []
    for col in selected_columns:
        if df[col].dtype == 'O':  # Object or string data type
            components.append(html.Label(col))
            components.append(dcc.Dropdown(
                id={"type": "filter-control-dropdown", "index": col},
                options=[{'label': val, 'value': val} for val in df[col].unique()],
                multi=True,
            ))
        elif df[col].dtype in ['int64', 'float64']:  # Numeric data type
            components.append(html.Label(col))
            components.append(dcc.RangeSlider(
                id={"type": "filter-control-slider", "index": col},
                min=df[col].min(),
                max=df[col].max(),
                value=[df[col].min(), df[col].max()],
                marks={int(val): str(val) for val in df[col].unique()}
            ))
        # TODO: Handle other data types like date
    return components

@app.callback(
    Output('filtered-data-display', 'children'),
    [Input('apply-button', 'n_clicks')],
    [State('column-dropdown', 'value'),
     State({'type': 'filter-control-dropdown', 'index': ALL}, 'value'),
     State({'type': 'filter-control-dropdown', 'index': ALL}, 'id'),
     State({'type': 'filter-control-slider', 'index': ALL}, 'value'),
     State({'type': 'filter-control-slider', 'index': ALL}, 'id'),
     ]
)
def filter_data(n_clicks, selected_columns, dropdown_values, dropdown_ids, slider_values, slider_ids):
    print('filter_data', flush=True)
    if not n_clicks:
        return None

    filtered_df = df.copy()

    print(f"selected_columns: {selected_columns}", flush=True)
    print(f"dropdown_values: {dropdown_values}", flush=True)
    print(f"dropdown_ids: {dropdown_ids}", flush=True)
    print(f"slider_values: {slider_values}", flush=True)
    print(f"slider_ids: {slider_ids}", flush=True)
    for column in selected_columns:
        print(f"column: {column}", flush=True)
        if df[column].dtype == 'O':
            for value, id in zip(dropdown_values, dropdown_ids):
                print(f"value: {value}", flush=True)
                print(f"id: {id}", flush=True)
                if id['index'] == column:
                    if value:
                        print(f"filtering on {column} with {value}", flush=True)
                        print(len(filtered_df), flush=True)
                        filtered_df = filtered_df[filtered_df[column].isin(value)]
                        print(len(filtered_df), flush=True)
        elif df[column].dtype in ['int64', 'float64']:
            for value, id in zip(slider_values, slider_ids):
                print(f"value: {value}", flush=True)
                print(f"id: {id}", flush=True)
                if id['index'] == column:
                    print(f"filtering on {column} with {value}", flush=True)
                    print(len(filtered_df), flush=True)
                    filtered_df = filtered_df[(filtered_df[column] >= value[0]) & (filtered_df[column] <= value[1])]
                    print(len(filtered_df), flush=True)

    # for col, d_val, s_val in zip(selected_columns, dropdown_values, slider_values):
    #     print("adsf" + col, d_val, s_val, flush=True)
    #     if df[col].dtype == 'O':
    #         if d_val:
    #             filtered_df = filtered_df[filtered_df[col].isin(d_val)]
    #     elif df[col].dtype in ['int64', 'float64']:
    #         filtered_df = filtered_df[(filtered_df[col] >= s_val[0]) & (filtered_df[col] <= s_val[1])]
        # TODO: Handle other data types like date

    # Here, we just display the first 10 rows of the filtered data for simplicity.
    # You can modify this part to display data in a more suitable way.
    return html.Table(
        [html.Tr([html.Th(col) for col in filtered_df.columns])] + [html.Tr([html.Td(filtered_df.iloc[i][col]) for col in filtered_df.columns]) for i in range(min(40, len(filtered_df)))],
        style={'border': '1px solid black', 'border-collapse': 'collapse'}
    )

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)