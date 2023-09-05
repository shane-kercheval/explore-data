"""Utility functions for dash app."""
import textwrap
import numpy as np
import pandas as pd
from source.library.utilities import filter_dataframe, series_to_datetime, to_date
import helpsk.pandas as hp
import plotly.graph_objs as go


def log(value: str) -> None:
    """Log value."""
    print(value, flush=True)


def log_function(name: str) -> None:
    """Log function calls."""
    log(f"\nFUNCTION: `{name}`")


def log_variable(var: str, value: str) -> None:
    """Log variable value."""
    log(f"VARIABLE: `{var}` = `{value}`")


def log_error(message: str) -> None:
    """Log variable value."""
    log(f">>>>>>>>>ERROR: `{message}`")


def values_to_dropdown_options(values: list[str]) -> list[dict]:
    """Convert a list of columns to a list of options for a dropdown."""
    # needs to be converted to str for dcc.Dropdown other wise it will fail
    return [{'label': str(value), 'value': str(value)} for value in values]


def filter_data_from_ui_control(  # noqa: PLR0915
        filters: dict,
        data: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    """
    Filters data based on the selected columns and values. Returns the filtered data, markdown
    text, and code. The code is a string that can be used to reproduce the filtering.

    When I save tuples in the cache, they are converted to lists. This is because tuples are not
    JSON serializable. So when I read the values from the cache, I need to convert them back to
    tuples.

    For dates, the value must be a tuple of (start, max) values. Missing values are automatically
    excluded.

    For booleans, the value must be a list with `True` or `False` values, and the data will return
    values that match the boolean. `np.nan` values can be included in the list to return missing

    The markdown text is used to display the filters that were applied. It is also used to display
    the number of rows that were removed by the filters.

    The code is used to recreate the filters. It is also used to filter the data in the
    `filter_data` function.
    """
    log_function('filtered_data')
    log_variable('filters', filters)

    if not filters:
        log("No filters applied.")
        return data.copy(), "No filters applied.", ""

    converted_filters = {}
    markdown_text = "##### Manual filters applied:  \n"

    # this for loop builds the filters dictionary and the markdown text
    for column, value in filters.items():
        log(f"filtering on `{column}` with `{value}`")

        series, _ = series_to_datetime(data[column])
        log_variable('series.dtype', series.dtype)
        if pd.api.types.is_datetime64_any_dtype(series):
            series = series.dt.date
            assert isinstance(value, list)
            assert len(value) == 2
            start_date = to_date(value[0])
            end_date = to_date(value[1])
            converted_filters[column] = (start_date, end_date)
            markdown_text += f"  - `{column}` between `{start_date}` and `{end_date}`"
            num_missing = series.isna().sum()
            if num_missing > 0:
                markdown_text += f"; `{num_missing:,}` missing values removed"
            markdown_text += "  \n"
        elif hp.is_series_bool(series):
            # e.g. [True, False, '<Missing>']
            assert isinstance(value, list)
            filters_list = [
                x.lower() == 'true'
                for x in value
                if x != '<Missing>' and x is not None
            ]
            if '<Missing>' in value:
                filters_list.extend([np.nan, None])
            log_variable('filters_list', filters_list)
            converted_filters[column] = filters_list
            markdown_text += f"  - `{column}` in `{filters_list}`  \n"
        elif series.dtype in ('object', 'category'):
            assert isinstance(value, list)
            filters_list = [x for x in value if x != '<Missing>' and x is not None]
            if '<Missing>' in value:
                filters_list.extend([np.nan, None])
            log_variable('filters_list', filters_list)
            converted_filters[column] = filters_list
            markdown_text += f"  - `{column}` in `{filters_list}`  \n"
        elif pd.api.types.is_numeric_dtype(series):
            assert isinstance(value, list)
            assert len(value) == 2
            min_value = value[0]
            max_value = value[1]
            converted_filters[column] = (min_value, max_value)
            markdown_text += f"  - `{column}` between `{min_value}` and `{max_value}`"
            num_missing = series.isna().sum()
            if num_missing > 0:
                markdown_text += f"; `{num_missing:,}` missing values removed"
            markdown_text += "  \n"
        else:
            raise ValueError(f"Unknown dtype for column `{column}`: {data[column].dtype}")

    filtered_data, code = filter_dataframe(data=data, filters=converted_filters)
    rows_removed = len(data) - len(filtered_data)
    markdown_text += f"  \n`{len(filtered_data):,}` rows remaining after manual filtering; `{rows_removed:,}` (`{rows_removed / len(data):.1%}`) rows removed  \n"  # noqa
    log(f"{len(data):,} rows before after filtering")
    log(f"{len(filtered_data):,} rows remaining after filtering")

    return filtered_data, markdown_text, code


def get_variable_type(variable: str | None, options: dict) -> str | None:
    """
    Takes a variable name and returns the type of the variable based on the options.
    The type will be one of 'numeric', 'date', 'categorical', 'string', or 'boolean', which will
    be associated with the keys in `options`. The values in option are lists of column types that
    match the key. For example, `options['numeric']` is a list of all numeric columns in the
    dataset.
    If the variable is None, then None is returned. If the variable is not found in the options,
    then an error is raised.
    """
    if variable is None:
        return None

    for key, value in options.items():
        if variable in value:
            return key

    raise ValueError(f"Unknown dtype for column `{variable}`")


# New Error type for invalid configuration selected
class InvalidConfigurationError(Exception):
    """Invalid configuration selected."""


def get_graph_config(
          configurations: list[dict],
          x_variable: str | None,
          y_variable: str | None,
          z_variable: str | None = None,
          ) -> dict:
    """
    Takes a list of configurations and returns the matching configuration based on the selected x,
    y, color, size, and facet variables. If no matching configuration is found, then an error is
    raised. If more than one matching configuration is found, then an error is raised.
    """
    if (x_variable is None and y_variable is None):
        return []

    matching_configs = []

    for config in configurations:
        selected_variables = config['selected_variables']
        if (
            (
                (x_variable is None and selected_variables['x_variable'] is None)
                or (
                    selected_variables['x_variable']
                    and x_variable in selected_variables['x_variable']
                )
            )
            and (
                (y_variable is None and selected_variables['y_variable'] is None)
                or (
                    selected_variables['y_variable']
                    and y_variable in selected_variables['y_variable']
                )
            )
            and (
                (
                    z_variable is None
                    and (
                        'z_variable' not in selected_variables
                        or selected_variables['z_variable'] is None
                    )
                )
                or (
                    'z_variable' in selected_variables
                    and selected_variables['z_variable']
                    and z_variable in selected_variables['z_variable']
                )
            )
        ):
            matching_configs.append(config)

    if len(matching_configs) == 0:
        raise InvalidConfigurationError("No matching configurations found.")
    if len(matching_configs) > 1:
        raise ValueError("More than one matching configuration found.")

    return matching_configs[0]


def get_columns_from_config(
        allowed_types: list[str],
        columns_by_type: dict,
        all_columns: list[str],
    ) -> list[str]:
    """Get the columns that match the variable type allowed by the configuration."""
    allowed_columns = []
    for allowed_type in allowed_types:
        allowed_columns.extend(columns_by_type[allowed_type])
    # return the same order as the all_columns list
    return [c for c in all_columns if c in allowed_columns]


def create_title_and_labels(  # noqa
        title_input: str | None,
        subtitle_input: str | None,
        config_description: str,
        x_variable: str | None,
        y_variable: str | None,
        z_variable: str | None,
        color_variable: str | None,
        size_variable: str | None,
        facet_variable: str | None,
        x_axis_label_input: str | None,
        y_axis_label_input: str | None,
        color_label_input: str | None,
        size_label_input: str | None,
        facet_label_input: str | None,
    ):
    """Create the title and labels for the graph."""
    if title_input or subtitle_input:
        title = title_input or ''
        if subtitle_input:
            title += f"<br><sub>{subtitle_input}</sub>"
    else:
        title = f"<br><sub>{config_description}</sub>"
        if x_variable:
            title = title.replace('{{x_variable}}', f"`{x_variable}`")
        if y_variable:
            title = title.replace('{{y_variable}}', f"`{y_variable}`")
        if z_variable:
            title = title.replace('{{z_variable}}', f"`{z_variable}`")
        if color_variable:
            title = title.replace('{{color_variable}}', f"`{color_variable}`")
        if size_variable:
            title = title.replace('{{size_variable}}', f"`{size_variable}`")
        if facet_variable:
            title = title.replace('{{facet_variable}}', f"`{facet_variable}`")
    graph_labels = {}
    if x_variable and x_axis_label_input:
        graph_labels[x_variable] = x_axis_label_input
    if y_variable and y_axis_label_input:
        graph_labels[y_variable] = y_axis_label_input
    if color_variable and color_label_input:
        graph_labels[color_variable] = color_label_input
    if size_variable and size_label_input:
        graph_labels[size_variable] = size_label_input
    if facet_variable and facet_label_input:
        graph_labels[facet_variable] = facet_label_input

    return title, graph_labels


def convert_to_graph_data(
        data: pd.DataFrame,
        numeric_columns: list[str],
        string_columns: list[str],
        categorical_columns: list[str],
        boolean_columns: list[str],
        selected_variables: list[str],
        top_n_categories: int,
    ) -> tuple[pd.DataFrame, str, str]:
    """
    Numeric columns are filtered by removing missing values.
    Missing values in non_numeric columns are replaced with '<Missing>'.
    The values non-numeric columns are updated to the top n categories. Other values are replaced
    with '<Other>'.
    """
    top_n_categories_code = textwrap.dedent("""
    def top_n_categories(series: pd.Series, n: int):
        top_n_values = series.value_counts().nlargest(n).index
        return series.where(series.isin(top_n_values), '<Other>')

    """)
    assert isinstance(selected_variables, list)
    assert len(selected_variables) == len(set(selected_variables))  # no duplicates
    original_num_rows = len(data)

    code = ""
    data = data[selected_variables].copy()
    # TODO: need to convert code to string and execute string
    if any(x in numeric_columns for x in selected_variables):
        markdown = "##### Automatic filters applied:  \n"
    else:
        markdown = ""

    for variable in selected_variables:
        if variable in string_columns or variable in categorical_columns or variable in boolean_columns:  # noqa
            log(f"filling na for {variable}")
            if data[variable].dtype.name == 'category':
                if data[variable].isna().any():
                    data[variable] = data[variable].cat.add_categories('<Missing>').fillna('<Missing>')  # noqa
                    code += f"graph_data['{variable}'] = graph_data['{variable}'].cat.add_categories('<Missing>').fillna('<Missing>')\n"  # noqa
            else:
                data[variable] = data[variable].fillna('<Missing>')
                code += f"graph_data['{variable}'] = graph_data['{variable}'].fillna('<Missing>')\n"  # noqa

            if top_n_categories:
                if 'top_n_categories' not in code:
                    code += top_n_categories_code
                code += f"graph_data['{variable}'] = top_n_categories(graph_data['{variable}'], n={top_n_categories})\n"  # noqa
                data[variable] = hp.top_n_categories(
                    categorical=data[variable],
                    top_n=top_n_categories,
                    other_category='<Other>',
                )
        if variable in numeric_columns:
            log(f"removing missing values for {variable}")
            num_values_removed = data[variable].isna().sum()
            if num_values_removed > 0:
                markdown += f"- `{num_values_removed:,}` missing values have been removed from `{variable}`  \n"  # noqa
            code += f"graph_data = graph_data[graph_data['{variable}'].notna()].copy()\n"
            data = data[data[variable].notna()]

    if any(x in numeric_columns for x in selected_variables):
        rows_remaining = len(data)
        rows_removed = original_num_rows - rows_remaining
        markdown += f"\n`{rows_remaining:,}` rows remaining after manual/automatic filtering; `{rows_removed:,}` (`{rows_removed / original_num_rows:.1%}`) rows removed from automatic filtering\n"  # noqa
        markdown += "---  \n"

    return data, markdown, code


def get_category_orders(
        data: pd.DataFrame,
        selected_variables: list[str],
        selected_category_order: str | None,
        non_numeric_columns: list[str],
    ) -> dict:
    """
    Returns a dictionary of category orders for each categorical column. The dictionary keys are
    the categorical columns, and the values are lists of categories in the order they should be
    displayed in the graph.
    """
    assert isinstance(selected_variables, list)
    assert len(selected_variables) == len(set(selected_variables))  # no duplicates

    # The order is based on the order_type, which can be one of:
    #     - 'category ascending': Sort the categories in ascending order
    #     - 'category descending': Sort the categories in descending order
    #     - 'total ascending': Sort the categories by the total in ascending order
    #     - 'total descending': Sort the categories by the total in descending order
    category_orders = {}
    if selected_category_order:
        for variable in selected_variables:
            if variable in non_numeric_columns:
                if 'category' in selected_category_order:
                    reverse = 'ascending' not in selected_category_order
                    categories = sorted(
                        data[variable].unique().tolist(),
                        reverse=reverse,
                        key=lambda x: str(x),
                    )
                    category_orders[variable] = categories
                elif 'total' in selected_category_order:
                    category_orders[variable] = data[variable].\
                        value_counts(sort=True, ascending='ascending' in selected_category_order).\
                        index.\
                        tolist()
                else:
                    raise ValueError(f"Unknown selected_category_order: {selected_category_order}")

    return category_orders


def generate_graph(  # noqa: PLR0912
        data: pd.DataFrame,
        graph_type: str,
        x_variable: str | None,
        y_variable: str | None,
        z_variable: str | None,
        color_variable: str | None,
        size_variable: str | None,
        facet_variable: str | None,
        num_facet_columns: int | None,
        selected_category_order: str | None,
        hist_func_agg: str | None,
        bar_mode: str | None,
        opacity: float | None,
        n_bins: int | None,
        log_x_axis: bool | None,
        log_y_axis: bool | None,
        title: str | None,
        graph_labels: dict | None,
        numeric_columns: list[str],
        string_columns: list[str],
        categorical_columns: list[str],
        boolean_columns: list[str],
        date_columns: list[str],
    ) -> tuple[go.Figure, str]:
    """
    Generate a graph based on the selected variables. Returns the graph and the code.
    The code is a string that can be used to recreate the graph.
    """
    log("creating fig")
    fig = None
    graph_data = data
    graph_code = ''

    category_orders = get_category_orders(
        data=data,
        selected_variables = list({x_variable, y_variable, z_variable, color_variable, size_variable, facet_variable}),  # noqa
        selected_category_order=selected_category_order,
        # TODO: dates?
        non_numeric_columns=string_columns + categorical_columns + boolean_columns,
    )

    def remove_unused_categories(variable: str) -> str:
        """Remove unused categories from the categorical columns."""
        values = graph_data[variable].unique().tolist()
        if data[variable].unique().tolist() != data[variable].cat.categories.tolist():
            code = "# plotly complains if the categories are missing\n"
            code += f"unique_values = {values}\n"
            code += "# preserve categories in same order as original categories\n"
            code += "new_categories = [\n"
            code += f"    x for x in graph_data['{variable}'].cat.categories\n"
            code += f"     if x in {values}\n"
            code += "]\n"
            code += f"graph_data['{variable}'] = pd.Categorical(graph_data['{variable}'], categories=new_categories)\n\n"  # noqa
            return code
        return ""

    for variable in list({color_variable, size_variable, facet_variable}):
        # plotly express complains if you try to use a categorical series where the categories are
        # not in the data.
        # In graph_data we removed unused categories for color, size, or facet variable
        # (for some reason plotly express doesn't complain about using a categorical column as x
        # or y variable)
        if variable and data[variable].dtype.name == 'category':
            graph_code += remove_unused_categories(variable)

    if graph_type == 'scatter':
        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.scatter(
            graph_data,
            x={f"'{x_variable}'" if x_variable else None},
            y={f"'{y_variable}'" if y_variable else None},
            color={f"'{color_variable}'" if color_variable else None},
            size={f"'{size_variable}'" if size_variable else None},
            opacity={opacity},
            facet_col={f"'{facet_variable}'" if facet_variable else None},
            facet_col_wrap={num_facet_columns},
            category_orders={category_orders},
            log_x={log_x_axis},
            log_y={log_y_axis},
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        fig
        """)
    elif graph_type == 'scatter-3d':
        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.scatter_3d(
            graph_data,
            x={f"'{x_variable}'" if x_variable else None},
            y={f"'{y_variable}'" if y_variable else None},
            z={f"'{z_variable}'" if z_variable else None},
            color={f"'{color_variable}'" if color_variable else None},
            size={f"'{size_variable}'" if size_variable else None},
            opacity={opacity},
            category_orders={category_orders},
            log_x={log_x_axis},
            log_y={log_y_axis},
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        fig.update_layout(margin={{'l': 0, 'r': 0, 'b': 0, 't': 20}})
        fig
        """)
    elif graph_type == 'box':
        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.box(
            graph_data,
            x={f"'{x_variable}'" if x_variable else None},
            y={f"'{y_variable}'" if y_variable else None},
            color={f"'{color_variable}'" if color_variable else None},
            facet_col={f"'{facet_variable}'" if facet_variable else None},
            facet_col_wrap={num_facet_columns},
            category_orders={category_orders},
            log_x={log_x_axis},
            log_y={log_y_axis},
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        fig
        """)
    elif graph_type == 'line':
        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.line(
            graph_data,
            x={f"'{x_variable}'" if x_variable else None},
            y={f"'{y_variable}'" if y_variable else None},
            color={f"'{color_variable}'" if color_variable else None},
            facet_col={f"'{facet_variable}'" if facet_variable else None},
            facet_col_wrap={num_facet_columns},
            category_orders={category_orders},
            log_x={log_x_axis},
            log_y={log_y_axis},
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        fig
        """)
    elif graph_type == 'histogram':

        if y_variable and y_variable in numeric_columns:
            hist_func_agg = f"'{hist_func_agg}'" if hist_func_agg else None
        else:
            hist_func_agg = None

        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.histogram(
            graph_data,
            x={f"'{x_variable}'" if x_variable else None},
            y={f"'{y_variable}'" if y_variable else None},
            color={f"'{color_variable}'" if color_variable else None},
            opacity={opacity},
            nbins={n_bins},
            histfunc={hist_func_agg},
            barmode={f"'{bar_mode}'" if bar_mode else None},
            facet_col={f"'{facet_variable}'" if facet_variable else None},
            facet_col_wrap={num_facet_columns},
            category_orders={category_orders},
            log_x={log_x_axis},
            log_y={log_y_axis},
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        """)
        if (
            (x_variable in numeric_columns or x_variable in date_columns)
            and bar_mode and bar_mode != 'group'
        ):
            # Adjust the bar group gap
            graph_code += f"fig.update_layout(barmode='{bar_mode}', bargap=0.05)\n"
        graph_code += "fig\n"
    elif graph_type == 'bar':
        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.bar(
            graph_data,
            x={f"'{x_variable}'" if x_variable else None},
            y={f"'{y_variable}'" if y_variable else None},
            color={f"'{color_variable}'" if color_variable else None},
            barmode={f"'{bar_mode}'" if bar_mode else None},
            facet_col={f"'{facet_variable}'" if facet_variable else None},
            facet_col_wrap={num_facet_columns},
            category_orders={category_orders},
            log_x={log_x_axis},
            log_y={log_y_axis},
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        """)
    else:
        raise ValueError(f"Unknown graph type: {graph_type}")


    # TODO: add range slider
    # graph_code += "fig.update_xaxes(rangeslider_visible=True)\n"

    log_variable('graph_code', graph_code)
    if 'Timestamp' in graph_code:
        log("Timestamp found in graph_code")
        raise ValueError(f"Timestamp found in graph_code {graph_code}")
    local_vars = locals()
    global_vars = globals()
    exec(graph_code, global_vars, local_vars)
    fig = local_vars['fig']
    return fig, graph_code

