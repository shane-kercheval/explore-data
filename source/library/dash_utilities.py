"""Utility functions for dash app."""
import textwrap
import numpy as np
import pandas as pd
from source.library.utilities import filter_dataframe, to_date
import source.library.types as t
import helpsk.pandas as hp
import plotly.graph_objs as go


MISSING = '<Missing>'
OTHER = '<Other>'


# New Error type for invalid configuration selected
class InvalidConfigurationError(Exception):
    """Invalid configuration selected."""


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
        column_types: dict,
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
        return data, "No filters applied.", ""

    converted_filters = {}
    markdown_text = "##### Manual filters applied:  \n"

    # this for loop builds the filters dictionary and the markdown text
    for column, value in filters.items():
        log(f"filtering on `{column}` ({t.get_type(column, column_types)}) with `{value}`")
        if t.is_date(column, column_types):
            series = pd.to_datetime(data[column]).dt.date
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
        elif t.is_boolean(column, column_types):
            # e.g. [True, False, MISSING]
            assert isinstance(value, list)
            filters_list = [
                x.lower() == 'true'
                for x in value
                if x != MISSING and x is not None
            ]
            if MISSING in value:
                filters_list.extend([np.nan, None])
            log_variable('filters_list', filters_list)
            converted_filters[column] = filters_list
            markdown_text += f"  - `{column}` in `{filters_list}`  \n"
        elif t.get_type(column, column_types) in {t.STRING, t.CATEGORICAL}:
            assert isinstance(value, list)
            filters_list = [x for x in value if x != MISSING and x is not None]
            if MISSING in value:
                filters_list.extend([np.nan, None])
            log_variable('filters_list', filters_list)
            converted_filters[column] = filters_list
            markdown_text += f"  - `{column}` in `{filters_list}`  \n"
        elif t.is_numeric(column, column_types):
            assert isinstance(value, list)
            assert len(value) == 2
            min_value = value[0]
            max_value = value[1]
            converted_filters[column] = (min_value, max_value)
            markdown_text += f"  - `{column}` between `{min_value}` and `{max_value}`"
            num_missing = data[column].isna().sum()
            if num_missing > 0:
                markdown_text += f"; `{num_missing:,}` missing values removed"
            markdown_text += "  \n"
        else:
            raise ValueError(f"Unknown dtype for column `{column}` ({t.get_type(column, column_types)}): {data[column].dtype}")  # noqa

    filtered_data, code = filter_dataframe(
        data=data,
        filters=converted_filters,
        column_types=column_types,
    )
    rows_removed = len(data) - len(filtered_data)
    markdown_text += f"  \n`{len(filtered_data):,}` rows remaining after manual filtering; `{rows_removed:,}` (`{rows_removed / len(data):.1%}`) rows removed  \n"  # noqa
    log(f"{len(data):,} rows before after filtering")
    log(f"{len(filtered_data):,} rows remaining after filtering")

    return filtered_data, markdown_text, code


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
        column_types: dict,
    ) -> list[str]:
    """Get the columns that match the variable type allowed by the configuration."""
    return [c for c, t in column_types.items() if t in allowed_types]


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


def convert_to_graph_data(  # noqa: PLR0912, PLR0915
        data: pd.DataFrame,
        column_types: dict,
        selected_variables: list[str],
        top_n_categories: int,
        exclude_from_top_n_transformation: list[str],
        create_cohorts_from: tuple[str, str] | None,
        date_floor: str | None,
    ) -> tuple[pd.DataFrame, str, str]:
    """
    Numeric columns are filtered by removing missing values.
    Missing values in non_numeric columns are replaced with MISSING.
    The values non-numeric columns are updated to the top n categories. Other values are replaced
    with '<Other>'.

    For `create_cohorts_from`, the first value is the x-variable, which we will create a cohorted
    column from, and the second value is the y-variable, which we will not filter on because we
    expect missing values.
    """
    top_n_categories_code = textwrap.dedent(f"""
    def top_n_categories(series: pd.Series, n: int):
        top_n_values = series.value_counts().nlargest(n).index
        return series.where(series.isin(top_n_values), '{OTHER}')

    """)
    assert isinstance(selected_variables, list)
    assert len(selected_variables) == len(set(selected_variables))  # no duplicates
    original_num_rows = len(data)

    code = ""
    data = data[selected_variables].copy()
    # TODO: need to convert code to string and execute string
    if any(t.is_numeric(x, column_types) for x in selected_variables):
        markdown = "##### Automatic filters applied:  \n"
    else:
        markdown = ""

    for variable in selected_variables:
        # fill missing values for string, categorical, and boolean columns with MISSING
        if t.is_discrete(variable, column_types):
            log(f"filling na for {variable}")
            if data[variable].dtype.name == 'category':
                if data[variable].isna().any():
                    data[variable] = data[variable].cat.add_categories(MISSING).fillna(MISSING)  # noqa
                    code += f"graph_data['{variable}'] = graph_data['{variable}'].cat.add_categories('{MISSING}').fillna(MISSING)\n"  # noqa
            else:
                data[variable] = data[variable].fillna(MISSING)
                code += f"graph_data['{variable}'] = graph_data['{variable}'].fillna('{MISSING}')\n"  # noqa

            exclude_from_top_n_transformation = exclude_from_top_n_transformation or []
            if top_n_categories and variable not in exclude_from_top_n_transformation:
                if 'top_n_categories' not in code:
                    code += top_n_categories_code
                code += f"graph_data['{variable}'] = top_n_categories(graph_data['{variable}'], n={top_n_categories})\n"  # noqa
                data[variable] = hp.top_n_categories(
                    categorical=data[variable],
                    top_n=top_n_categories,
                    other_category=OTHER,
                )

        if date_floor and t.is_date(variable, column_types):
            # convert the date to the specified date_floor
            if create_cohorts_from and variable == create_cohorts_from[1]:
                # we don't want to floor or remove anything from y-variable
                # since we need to use that to calculate the conversion rates
                continue

            series = pd.to_datetime(data[variable], errors='coerce')
            code += f"series = pd.to_datetime(graph_data['{variable}'], errors='coerce')\n"

            temp_variable = None
            if create_cohorts_from and variable == create_cohorts_from[0]:
                temp_variable = variable
                variable = f"{variable} (Cohorts)"  # noqa: PLW2901

            if date_floor == 'year':
                data[variable] = series.dt.to_period('Y').dt.start_time.dt.strftime('%Y-%m-%d')
                code += f"graph_data['{variable}'] = series.dt.to_period('Y').dt.start_time.dt.strftime('%Y-%m-%d')\n"  # noqa            
            elif date_floor == 'quarter':
                data[variable] = series.dt.to_period('Q').dt.start_time.dt.strftime('%Y-%m-%d')
                code += f"graph_data['{variable}'] = series.dt.to_period('Q').dt.start_time.dt.strftime('%Y-%m-%d')\n"  # noqa
            elif date_floor == 'month':
                data[variable] = series.dt.to_period('M').dt.start_time.dt.strftime('%Y-%m-%d')
                code += f"graph_data['{variable}'] = series.dt.to_period('M').dt.start_time.dt.strftime('%Y-%m-%d')\n"  # noqa
            elif date_floor == 'week':
                data[variable] = series.dt.to_period('W').dt.start_time.dt.strftime('%Y-%m-%d')
                code += f"graph_data['{variable}'] = series.dt.to_period('W').dt.start_time.dt.strftime('%Y-%m-%d')\n"  # noqa
            elif date_floor == 'day':
                data[variable] = series.dt.strftime('%Y-%m-%d')
                code += f"graph_data['{variable}'] = series.dt.strftime('%Y-%m-%d')\n"
            elif date_floor == 'hour':
                data[variable] = series.dt.strftime('%Y-%m-%d %H:00:00')
                code += f"graph_data['{variable}'] = series.dt.strftime('%Y-%m-%d %H:00:00')\n"
            elif date_floor == 'minute':
                data[variable] = series.dt.strftime('%Y-%m-%d %H:%M:00')
                code += f"graph_data['{variable}'] = series.dt.strftime('%Y-%m-%d %H:%M:00')\n"
            elif date_floor == 'second':
                data[variable] = series.dt.strftime('%Y-%m-%d %H:%M:%S')
                code += f"graph_data['{variable}'] = series.dt.strftime('%Y-%m-%d %H:%M:%S')\n"
            else:
                raise ValueError(f"Unknown date_floor: {date_floor}")

            if temp_variable:
                variable = temp_variable  # noqa

        if t.is_continuous(variable, column_types):
            log(f"removing missing values for - {variable}")
            num_values_removed = data[variable].isna().sum()
            if num_values_removed > 0:
                markdown += f"- `{num_values_removed:,}` missing values have been removed from `{variable}`  \n"  # noqa
                code += f"graph_data = graph_data[graph_data['{variable}'].notna()]\n"
                data = data[data[variable].notna()]

    if any(t.is_numeric(x, column_types) for x in selected_variables):
        rows_remaining = len(data)
        rows_removed = original_num_rows - rows_remaining
        markdown += f"\n`{rows_remaining:,}` rows remaining after manual/automatic filtering; `{rows_removed:,}` (`{rows_removed / original_num_rows:.1%}`) rows removed from automatic filtering\n"  # noqa
        markdown += "---  \n"

    return data, markdown, code


def get_category_orders(
        data: pd.DataFrame,
        selected_variables: list[str],
        selected_category_order: str | None,
        column_types: dict,
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
            if t.is_discrete(variable, column_types) and data[variable].nunique() < 50:
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


def plot_retention(
        graph_data: pd.DataFrame,
        x_variable:str,
        y_variable: str,
        intervals: str,
        min_events: int,
        max_periods_to_display: int) -> go.Figure:
    """Plot retention heatmap."""
    if intervals not in ['day', 'week', 'month']:
        raise InvalidConfigurationError(f"Invalid interval selected for retention heatmap ({intervals}).")  # noqa

    from helpsk.conversions import retention_matrix
    import pandas as pd
    import plotly.express as px

    graph_data[x_variable] = pd.to_datetime(graph_data[x_variable])
    retention = retention_matrix(
        df=graph_data,
        timestamp=x_variable,
        unique_id=y_variable,
        intervals=intervals,
        min_events=min_events,
    )
    columns = [str(x) for x in range(1, max_periods_to_display) if str(x) in retention.columns]
    retention_data = retention[columns]
    return px.imshow(
        retention_data,
        color_continuous_scale='Greens',
        text_auto='.1%',
        labels={'x': intervals.capitalize(), 'y': "Cohort", 'color': "% Retained"},
        y=retention['cohort'].astype(str).tolist(),
        template='simple_white',
        zmin=0,
        zmax=retention_data.max().max(),
    )


def generate_graph(  # noqa: PLR0912, PLR0915
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
        date_floor: str | None,
        cohort_conversion_rate_snapshots: list[int] | None,
        cohort_conversion_rate_units: str | None,
        opacity: float | None,
        n_bins_month: int | None,
        n_bins: int | None,
        min_retention_events: int | None,
        num_retention_periods: int | None,
        log_x_axis: bool | None,
        log_y_axis: bool | None,
        free_x_axis: bool | None,
        free_y_axis: bool | None,
        show_axes_histogram: bool | None,
        title: str | None,
        graph_labels: dict | None,
        column_types: dict,
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
        column_types=column_types,
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
            marginal_x={"'histogram'" if show_axes_histogram else None},
            marginal_y={"'histogram'" if show_axes_histogram else None},
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
        if not color_variable:
            bar_mode = 'relative'

        if t.is_numeric(y_variable, column_types):
            hist_func_agg = f"'{hist_func_agg}'" if hist_func_agg else None
        else:
            hist_func_agg = None

        if t.is_date(x_variable, column_types):
            if n_bins_month:
                n_bins = None
                n_bins_month = f"'M{n_bins_month}'"
            else:
                n_bins_month = None
        else:
            n_bins_month = None

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
            t.is_continuous(x_variable, column_types)
            and bar_mode
            and bar_mode != 'group'
            ):
            # Adjust the bar group gap
            graph_code += f"fig.update_layout(barmode='{bar_mode}', bargap=0.05)\n"

        if n_bins_month:
            graph_code += f"fig.update_traces(xbins_size={n_bins_month})\n"
            graph_code += f"fig.update_xaxes(showgrid=True, ticklabelmode='period', dtick={n_bins_month}, tickformat='%b\\n%Y')\n"  # noqa

        graph_code += "fig\n"
    elif graph_type in ['bar', 'bar - count distinct']:
        if not color_variable:
            bar_mode = None

        if graph_type == 'bar - count distinct':
            if y_variable in [x_variable, color_variable, facet_variable]:
                raise InvalidConfigurationError("Cannot use the same variable for y and x, color, or facet")  # noqa
            selected_variables = [
                x for x in [x_variable, color_variable, facet_variable]
                if x is not None and x != y_variable
            ]
            selected_variables = list(set(selected_variables))
            graph_code += textwrap.dedent(f"""
            graph_data = (
                graph_data
                .groupby({selected_variables})
                .agg({{'{y_variable}': 'nunique'}})
                .reset_index()
            )
            """)
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
            opacity=0.6,
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        """)
    elif graph_type == 'heatmap':

        if t.is_numeric(z_variable, column_types):
            hist_func_agg = f"'{hist_func_agg}'" if hist_func_agg else None
        else:
            hist_func_agg = None

        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.density_heatmap(
            graph_data,
            x={f"'{x_variable}'" if x_variable else None},
            y={f"'{y_variable}'" if y_variable else None},
            z={f"'{z_variable}'" if z_variable else None},
            facet_col={f"'{facet_variable}'" if facet_variable else None},
            facet_col_wrap={num_facet_columns},
            category_orders={category_orders},
            histfunc={hist_func_agg},
            nbinsx={n_bins},
            nbinsy={n_bins},
            log_x={log_x_axis},
            log_y={log_y_axis},
            # color_continuous_scale=['white', 'red'],
            marginal_x={"'histogram'" if show_axes_histogram else None},
            marginal_y={"'histogram'" if show_axes_histogram else None},
            title={f'"{title}"' if title else None},
            labels={graph_labels},
        )
        """)
    elif graph_type == 'retention':
        graph_code += textwrap.dedent(f"""
        from helpsk.conversions import retention_matrix
        import pandas as pd
        graph_data['{x_variable}'] = pd.to_datetime(graph_data['{x_variable}'])
        fig = plot_retention(
            graph_data,
            x_variable='{x_variable}',
            y_variable='{y_variable}',
            intervals='{date_floor}',
            min_events={min_retention_events},
            max_periods_to_display={num_retention_periods},
        )
        """)

    elif graph_type == 'heatmap - count distinct':
        selected_variables = [
            x for x in [x_variable, y_variable, z_variable, facet_variable]
            if x is not None
        ]
        selected_variables = list(set(selected_variables))
        graph_code += f"graph_data = graph_data[{selected_variables}].drop_duplicates()\n"
        graph_code += textwrap.dedent(f"""
        import plotly.express as px
        fig = px.density_heatmap(
            graph_data,
            x={f"'{x_variable}'"},
            y={f"'{y_variable}'"},
            z={f"'{z_variable}'"},
            histfunc='count',
            facet_col={f"'{facet_variable}'" if facet_variable else None},
            facet_col_wrap={num_facet_columns},
            category_orders={category_orders},
            title={f'"{title}"' if title else None},
            marginal_x={"'histogram'" if show_axes_histogram else None},
            marginal_y={"'histogram'" if show_axes_histogram else None},
            labels={graph_labels},
        )
        """)
    elif graph_type == 'cohorted conversion rates':
        log_variable('columns', graph_data.columns.tolist())
        log(x_variable in graph_data.columns)
        log(y_variable in graph_data.columns)
        log(f"{x_variable} (Cohorts)" in graph_data.columns)
        intervals = [
            (x, cohort_conversion_rate_units)
            for x in cohort_conversion_rate_snapshots if x > 0
        ]
        cohorted_graph_type = 'line' if bar_mode == 'relative' else 'bar'
        graph_code += textwrap.dedent(f"""
        from helpsk.conversions import plot_cohorted_conversion_rates
        graph_data['{x_variable}'] = pd.to_datetime(graph_data['{x_variable}'])
        graph_data['{y_variable}'] = pd.to_datetime(graph_data['{y_variable}'])
        fig = plot_cohorted_conversion_rates(
            df=graph_data,
            base_timestamp='{x_variable}',
            conversion_timestamp='{y_variable}',
            cohort={f"'{x_variable} (Cohorts)'"},
            intervals={intervals},
            groups={f"'{facet_variable}'" if facet_variable else None},
            category_orders={category_orders},
            current_datetime=None,
            graph_type='{cohorted_graph_type}',
            title={f'"{title}"' if title else None},
            facet_col_wrap={num_facet_columns},
            bar_mode={f"'{bar_mode}'" if bar_mode else None},
            opacity={opacity},
            height=None,
            width=None,
        )
        fig.update_yaxes(tickformat=',.1%')
        """)
    else:
        raise ValueError(f"Unknown graph type: {graph_type}")

    if free_x_axis:
        graph_code += "fig.update_xaxes(matches=None)\n"
        graph_code += "fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))\n"

    if free_y_axis:
        graph_code += "fig.update_yaxes(matches=None)\n"
        graph_code += "fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))\n"

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
