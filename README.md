The data explorer is a plotly dash app that makes exploring datasets easy.

![Loading GIF](https://github.com/shane-kercheval/explore-data/blob/main/explore-data.gif)

# AI Generated Graphs

![Loading GIF](https://github.com/shane-kercheval/explore-data/blob/main/ai-generated.gif)

This app uses OpenAI Functions to transform a description of a plot to the correct variable selections within the app. In order to enable this functionality, you must update the `.env` file with your OpenAI API token with the entry: `OPENAI_API_KEY=<YOUR TOKEN>`.

# Running the project

## `.env`

Create a `.env` file in the project directory with the following contents.

```
HOST='0.0.0.0'
DEBUG=True
PORT=8050
PROJECT_PATH=.
```

If you want to query Snowflake, add this information to the `.env` file:

```
SNOWFLAKE_USER=my.email@address.com
SNOWFLAKE_ACCOUNT=account.id
SNOWFLAKE_AUTHENTICATOR=externalbrowser
SNOWFLAKE_WAREHOUSE=WAREHOUSE_NAME
SNOWFLAKE_DATABASE=DATABASE_NAME
```

Note: if `SNOWFLAKE_AUTHENTICATOR` is set to `externalbrowser` you will probably not be able to run the app in a docker container.

If you want to use the AI feature that allows you to describe the graph in plain text and have AI select the appropriate values, add this information to the `.env` file:

```
OPENAI_API_KEY=sk-<your key>
```

## Launching

Run the following commands to start the program.

```
pip install uv
make run-app
```

# Querying Snowflake

## Default Queries

You can create a `queries.txt` file to the project directory (same directory as `app.py`) and the content of the file (e.g. default query or queries) will be populated in the text-box used to query Snowflake.

## Known Issues

- The user needs to refresh the app before loading a different dataset.
- This app is only tested with a single user running a local server; it is not tested/supported for multi-user non-local servers.
- Doing a count distinct with a datetime variable (date as x and non-numeric as y) without first selecting `Date Floor` of `Day` or higher freezes up the app if the granularity of the datetime variable is something like seconds.
- The `file_system_backend` directory will grow indefinitely
    - https://www.dash-extensions.com/transforms/serverside_output_transform
