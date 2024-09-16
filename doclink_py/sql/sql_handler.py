import pyodbc
import json
import logging

from typing import Any, Callable

from ..utilities import record_transaction


def requires_connection(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to check if the SQL connection is valid."""

    def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Any:
        logging.debug("Checking connection...")

        if instance.connection is None or instance.cursor is None:
            logging.error("Not connected to SQL Server.")
            raise Exception("NO_CONN", "Not connected to SQL Server.")
        return func(instance, *args, **kwargs)

    return wrapper


class SQLHandler:
    """Low level class to handle SQL connections."""

    def __init__(self) -> None:
        self.connection: pyodbc.Connection = None
        self.cursor: pyodbc.Cursor = None

    def connect(self, server_name, database_name, username, password) -> None:
        # Connect to SQL Server
        logging.info("Connecting to SQL Server...")
        self.connection = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=" + server_name + ";"
            "DATABASE=" + database_name + ";"
            "UID=" + username + ";"
            "PWD=" + password + ";"
        )
        logging.debug("Connected to SQL Server.")

        self.cursor = self.connection.cursor()

    def disconnect(self) -> None:
        # Disconnect from SQL Server
        logging.info("Disconnecting from SQL Server...")
        if self.connection:
            self.connection.close()
        logging.debug("Disconnected from SQL Server.")

    @requires_connection
    def get_identity(self) -> int:
        self.cursor.execute("SELECT SCOPE_IDENTITY()")
        result = self.cursor.fetchone()
        record_transaction("SELECT SCOPE_IDENTITY()")
        record_transaction(f"Result: {result[0]}")
        return result[0]

    @requires_connection
    def query_and_commit(self, query: str) -> None:
        record_transaction(query)
        self.cursor.execute(query)
        self.connection.commit()

    @requires_connection
    def query_and_fetch_all(self, query: str) -> list[pyodbc.Row]:
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        record_transaction(query)
        record_transaction(f"Results:\n{json.dumps(data, default=str, indent=2)}")
        return data

    @requires_connection
    def query_and_fetch_one(self, query: str) -> pyodbc.Row:
        self.cursor.execute(query)
        data = self.cursor.fetchone()
        record_transaction(query)
        record_transaction(f"Results:\n{json.dumps(data, default=str, indent=2)}")
        return data

    @requires_connection
    def columns_for_table(self, table: str) -> dict[str, int]:
        self.cursor.execute(f"SELECT TOP(1) * FROM {table}")

        # Create a dictionary mapping column names to indices
        columns: dict = {
            description[0]: index
            for index, description in enumerate(self.cursor.description)
        }

        return columns

    @requires_connection
    def query_and_execute(self, query: str) -> None:
        record_transaction(query)
        self.cursor.execute(query)
