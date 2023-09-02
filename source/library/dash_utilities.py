"""Utility functions for dash app."""
import numpy as np
import pandas as pd
from source.library.utilities import filter_dataframe, series_to_datetime, to_date
import helpsk.pandas as hp

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
        return data.copy(), "No filters applied.", "No filters applied."

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

    return filtered_data, markdown_text, f"""```\n{code}\n```"""


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



def get_graph_config(
          configurations: list[dict],
          x_variable: str | None,
          y_variable: str | None,
          color_variable: str | None,
          size_variable: str | None,
          facet_variable: str | None) -> dict:
    """
    Takes a list of configurations and returns the matching configuration based on the selected x,
    y, color, size, and facet variables. If no matching configuration is found, then an error is
    raised. If more than one matching configuration is found, then an error is raised.
    """
    if (
        x_variable is None
        and y_variable is None
        and color_variable is None
        and size_variable is None
        and facet_variable is None
        ):
        return []

    matching_configs = []

    for config in configurations:
        selected_variables = config['selected_variables']
        if (
            (
                (x_variable is None and selected_variables['x_variable'] is None)
                or (x_variable in selected_variables['x_variable'])
            )
            and (
                (y_variable is None and selected_variables['y_variable'] is None)
                or (y_variable in selected_variables['y_variable'])
            )
            and (
                (color_variable is None and selected_variables['color_variable'] is None)
                or (color_variable in selected_variables['color_variable'])
            )
            and (
                (size_variable is None and selected_variables['size_variable'] is None)
                or (size_variable in selected_variables['size_variable'])
            )
            and (
                (facet_variable is None and selected_variables['facet_variable'] is None)
                or (facet_variable in selected_variables['facet_variable'])
            )
        ):
            matching_configs.append(config)

    if len(matching_configs) == 0:
        raise ValueError("No matching configurations found.")
    if len(matching_configs) > 1:
        raise ValueError("More than one matching configuration found.")

    return matching_configs[0]
