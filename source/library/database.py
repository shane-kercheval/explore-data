"""BigQuery connector, implementing the helpsk.database.Database interface."""
import pandas as pd
from helpsk.database import Database, ConnectionObject


class BigQuery(Database):
    """
    Wraps logic for connecting to BigQuery and querying.

    Example:
        with BigQuery(project='my-gcp-project') as bigquery:
            bigquery.query("SELECT * FROM `dataset.table` LIMIT 100")

    Uses Application Default Credentials (ADC) for authentication. Run
    `gcloud auth application-default login` before using.
    """

    def _open_connection_object(self) -> ConnectionObject:
        """Wraps logic for connecting to BigQuery."""
        from google.cloud import bigquery
        return bigquery.Client(project=self._kwargs.get('project'))

    def _close_connection_object(self) -> None:
        """Wraps logic for closing the connection to BigQuery."""
        self.connection_object.close()

    def _query(self, sql: str) -> pd.DataFrame:
        """
        Wraps logic for querying BigQuery.

        Args:
            sql:
                SQL to execute e.g. "SELECT * FROM `dataset.table` LIMIT 100"

        Returns:
            a pandas DataFrame with the results from the query
        """
        dataframe = self.connection_object.query(sql).to_dataframe()
        # `to_dataframe()` returns pandas nullable dtypes (e.g. `Int64`, `Float64`) for
        # numeric columns, which use `pd.NA` instead of `np.nan`. Aggregations like `.std()`
        # on mostly-null columns then return `pd.NA`, which breaks downstream code (e.g.
        # helpsk.pandas.numeric_summary calling `round()`) that assumes numpy NaN semantics.
        # Cast to plain float64 so behavior matches the other data sources in this app.
        nullable_numeric_dtypes = {
            'Int8', 'Int16', 'Int32', 'Int64',
            'UInt8', 'UInt16', 'UInt32', 'UInt64',
            'Float32', 'Float64',
        }
        for column in dataframe.columns:
            if str(dataframe[column].dtype) in nullable_numeric_dtypes:
                dataframe[column] = dataframe[column].astype('float64')
        return dataframe

    def execute_statement(self, statement: str) -> None:
        """Executes a statement without any data returned."""
        return self.connection_object.query(statement).result()

    def insert_records(
            self,
            dataframe: pd.DataFrame,
            table: str,
            create_table: bool = False,
            overwrite: bool = False,
            schema: str | None = None,
            database: str | None = None) -> None:
        """Not implemented; this app only needs read access to BigQuery."""
        raise NotImplementedError("insert_records is not supported for BigQuery in this project.")
