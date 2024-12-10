The data explorer is a plotly dash app that makes exploring datasets easy.

![Loading GIF](https://github.com/shane-kercheval/explore-data/blob/main/explore-data.gif)

# AI Generated Graphs

![Loading GIF](https://github.com/shane-kercheval/explore-data/blob/main/ai-generated.gif)

This app uses OpenAI Functions to transform a description of a plot to the correct variable selections within the app. In order to enable this functionality, you must update the `.env` file with your OpenAI API token with the entry: `OPENAI_API_KEY=<YOUR TOKEN>`.

# Running the project

- `pip install uv`
- `make run-app`

# Querying Snowflake

## Configuration

- To enable the `Query Snowflake` tab, you must create a configuration file in the format below
- The name and location of the configuration file can be either of the following:
    - `.snowflake.config` located in the project directory (same directory as `app.py`)
    - Any file name/path of your choosing, as long as you set the `SNOWFLAKE_CONFIG_PATH` variable in the `.env` file.

```
[snowflake]
user=my.email@address.com
account=account.id
authenticator=externalbrowser
warehouse=WAREHOUSE_NAME
database=DATABASE_NAME
```

Note: if `authenticator` is set to `externalbrowser` you will probably not be able to run the app in a docker container, and instead can create a virtual/conda environment. Follow the steps in the `Running the project -> Conda` section above.

## Default Queries

You can create a `queries.txt` file to the project directory (same directory as `app.py`) and the content of the file (e.g. default query or queries) will be populated in the text-box used to query Snowflake.

## Known Issues

- The user needs to refresh the app before loading a different dataset.
- This app is only tested with a single user running a local server; it is not tested/supported for multi-user non-local servers.
- Doing a count distinct with a datetime variable (date as x and non-numeric as y) without first selecting `Date Floor` of `Day` or higher freezes up the app if the granularity of the datetime variable is something like seconds.
- The `file_system_backend` directory will grow indefinitely
    - https://www.dash-extensions.com/transforms/serverside_output_transform
