# project-template

The data explorer is a plotly dash app that makes exploring datasets easy.

![Loading GIF](https://github.com/shane-kercheval/explore-data/blob/main/explore-data.gif)

# Running the project

- install docker (or create a virtual environment)
- navigate to the project directory and run `make docker_run`
- when the docker container is running, open a web browser and go to http://localhost:8050

## Known Issues

- The user needs to refresh the app before loading a different dataset.
- This app is only tested with a single user running a local server; it is not tested/supported for multi-user non-local servers.
- Selecting `Bin Months` (which bins the datetime column into months) doesn't play nice with some date `Date Floor` selections like `Week`. The solution is to only display/use `Bin Months` for valid selections of `Date Floor`. Fix TBD.
- Doing a count distinct with a datetime variable (date as x and non-numeric as y) without first selecting `Date Floor` of `Day` or higher freezes up the app if the granularity of the datetime variable is something like seconds.
- The `file_system_backend` directory will grow indefinitely
    - https://www.dash-extensions.com/transforms/serverside_output_transform
