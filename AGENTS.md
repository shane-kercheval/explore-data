# Instructions for AI agents

This file is for AI coding agents (Claude Code, Codex, etc.) working in this repo.

## This app is local-only, not a deployed service

`explore-data` runs on one person's machine via `uv run python app.py`. There is no
staging environment, no production deployment, no CI running this app, and no backup of
its local state anywhere. That changes how you should treat local files compared to a
typical hosted service:

- There is no "redeploy from source" story for local data. If you delete it, it's gone.
- A process listening on the dev port (default 8050, see `.env`) is very likely the
  user's own live session, not a leftover of yours.
- Treat every local, gitignored file/directory below as **real user data**, not a cache
  or build artifact you're free to regenerate.

## Never touch these without being asked

- **`.query_history/`** — the user's actual saved Snowflake/BigQuery queries
  (`snowflake.json`, `bigquery.json`). This is the whole point of the feature; there is
  no other copy of this data. Never `rm`, truncate, or overwrite it, and never run tests
  or ad-hoc verification scripts against the real one at the project root.
- **`.env`** — real credentials (Snowflake, BigQuery, OpenAI). Never print its contents
  into a place that could leak (commit, log, external tool call) and never overwrite it.
- **A running `app.py` process** — check `ps`/`lsof -i :8050` before assuming a dev
  server on the usual port is disposable. Don't `kill` it or restart it to "test your
  change" unless the user asked you to run the app.

## How to actually test changes that touch local storage or run the live app

Do this in an isolated copy, every time — this bit the user once already this session
(an agent's ad-hoc test scripts wiped real query history by running directly against
this project's live `.query_history/` and dev server):

```bash
rsync -a --exclude='.venv' --exclude='.git' --exclude='.query_history' --exclude='__pycache__' \
  /path/to/explore-data/ /tmp/explore-data-test/
cd /tmp/explore-data-test
cat > .env <<'EOF'
HOST='127.0.0.1'
DEBUG=True
PORT=8099          # not 8050 - never share the real dev server's port
PROJECT_PATH=.
EOF
uv sync
uv run python app.py
```

To exercise the "Query Snowflake"/"Query BigQuery" tabs without hitting real cloud
infra (and without needing real credentials), add obviously-fake values to that
isolated `.env` — the tab just needs `ENABLE_SNOWFLAKE`/`ENABLE_BIGQUERY` to be truthy;
the connection attempt failing fast is fine, since query history is recorded before the
query even runs (that's intentional - failed queries still get cached):

```bash
SNOWFLAKE_USER=fake
SNOWFLAKE_ACCOUNT=fake
SNOWFLAKE_AUTHENTICATOR=snowflake
SNOWFLAKE_WAREHOUSE=fake
SNOWFLAKE_DATABASE=fake
```

For pure `source/library/query_history.py` logic (no browser needed), use a pytest
`tmp_path` fixture that monkeypatches `HISTORY_DIR`, the same way
`tests/test_query_history.py` does — see the `history_dir` fixture there. Never call
`record_query`/`update_title`/`delete_query`/`_save_history` against the real
`HISTORY_DIR` in a script or one-off shell command.

When you need to click through the UI, Playwright driving a headless Chromium against
the isolated copy above works well; there's no project-specific run skill checked in,
so improvise per the pattern above rather than reusing the real server.

## Project shape

- `app.py` — the entire Dash app: layout, callbacks, both clientside and server-side.
  It's large; search for the feature area (e.g. `query-history`, `sidebar-resize`)
  rather than reading top to bottom.
- `source/library/` — helpers used by `app.py`: `dash_ui.py` (component builders),
  `dash_utilities.py` / `utilities.py` (data/graph logic), `database.py` (Snowflake/
  BigQuery connectors), `query_history.py` (the local query cache).
- `assets/custom.css` — the whole design system (buttons, tabs, tables, dropdowns,
  the query history list). Most visual changes belong here, not in inline `style=`
  props in `app.py` — check for an existing class before adding a new one.
- `tests/` mirrors `source/library/` one file at a time (`test_query_history.py` for
  `query_history.py`, etc.). `app.py` itself has no test file; it's exercised via the
  library functions it calls plus manual/Playwright verification.

## Running checks

- `uv run ruff check app.py source/library tests` (or `make linting`)
- `uv run python -m pytest tests` (or `make unittests`) — `make tests` runs
  linting + unittests + doctests together.
- **Known pre-existing failure**: `tests/test_dash_utilities.py::test_generate_graph__all_configurations`
  fails due to pandas API drift unrelated to this app's own code (confirmed via
  `git stash` against a clean `main`). It's not something you introduced; don't spend
  time chasing it unless specifically asked to fix it.
- Two of the test-fixture YAML files under `tests/test_files/utilities/` regenerate
  random UUIDs every time the test suite runs (`test_build_tools_from_graph_configs__*.yml`).
  `git checkout` them back after running tests locally so they don't show up as
  unrelated diff noise.

## Other conventions already in place

- BigQuery auth is via `gcloud auth application-default login` (ADC), not a service
  account key file — see the README.
- Dependencies are managed with `uv` (`pyproject.toml` / `uv.lock`), not `pip`/`venv`
  directly.
- Only commit when the user explicitly asks; this session's history involved several
  rounds of iteration before anything was committed.
