from dash import Dash, dcc, html, Input, Output, ALL, Patch, callback

app = Dash(__name__)

app.layout = html.Div(
    [
        html.Button("Add Filter", id="add-filter-btn", n_clicks=0),
        html.Div(id="dropdown-container-div", children=[]),
        html.Div(id="dropdown-container-output-div"),
    ]
)


@callback(
    Output("dropdown-container-div", "children"),
    Input("add-filter-btn", "n_clicks"),
)
def display_dropdowns(n_clicks):
    patched_children = Patch()
    new_dropdown = dcc.Dropdown(
        ["NYC", "MTL", "LA", "TOKYO"],
        multi=True,
        id={"type": "city-filter-dropdown", "index": str(n_clicks) + 's'},
    )
    patched_children.append(new_dropdown)
    return patched_children


@callback(
    Output("dropdown-container-output-div", "children"),
    Input({"type": "city-filter-dropdown", "index": ALL}, "value"),
    Input({"type": "city-filter-dropdown", "index": ALL}, "id"),
)
def display_output(values, indexes):
    print(f"values: {values}", flush=True)
    print(f"indexes: {indexes}", flush=True)
    return html.Div(
        [html.Div(f"Dropdown {i + 1} = {value}") for (i, value) in enumerate(values)]
    )


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=True, port=8050)
