import os
import logging

from typing import Callable, Any
import chardet

LINE_NUM_ANALOGS = [
    "line number",
    "linenumber",
    "line num",
    "linenum",
    "line no",
    "lineno",
    "line#",
    "line #",
]

FORBIDDEN_COLUMN_NAMES = ["company", "companyno"]

VOUCHER_ANALOGS = [
    "vouchernumber",
    "voucherno",
    "vouchernum",
    "voucher number",
    "voucher no",
    "voucher num",
    "voucher",
]

BATCH_ANALOGS = [
    "batchnumber",
    "batchno",
    "batchnum",
    "batchid",
    "batch",
    "batchn umber",
    "batch no",
    "batch num",
    "batch id",
]


def requires_connection(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Any:
        logging.debug("Checking connection...")

        if instance.connection is None or instance.cursor is None:
            logging.error("Not connected to SQL Server.")
            raise Exception("NO_CONN", "Not connected to SQL Server.")
        return func(instance, *args, **kwargs)

    return wrapper


def get_query_from_file(path: str, file_name: str) -> str:
    logging.debug("Getting query from file " + str(file_name))

    query = ""

    file_path = os.path.join(path, file_name)

    # Detect file encoding
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
    encoding = result["encoding"]

    # Read the file with the detected encoding
    with open(file_path, "r", encoding=encoding) as f:
        query = f.read()

        # Remove BOM character if it exists
        if query.startswith("\ufeff"):
            query = query[1:]

    return query


def raise_error(error_msg: str, error_code: str = "GENERIC_ERROR") -> None:
    logging.error("Raising error " + str(error_code) + " " + str(error_msg))
    raise Exception(error_code, error_msg)


def record_transaction(query: str) -> None:
    with open("transactions.txt", "a") as f:
        f.write(query + "\n\n")


def row_to_json(row):
    """Convert a row to a JSON object"""
    return {column[0]: row[i] for i, column in enumerate(row.cursor_description)}


def api_row_to_json(row, column_info):
    """Convert a row to a JSON object"""
    return {column_info[i]["Name"]: row[i] for i, _ in enumerate(row)}


def is_line_number(text: str) -> bool:
    """Returns True if the given text is a line number analog."""
    return text.lower() in LINE_NUM_ANALOGS


def is_forbidden_column_name(text: str) -> bool:
    """Returns True if the given text is a forbidden column name."""
    return text.lower() in FORBIDDEN_COLUMN_NAMES


def is_voucher_analog(text: str) -> bool:
    """Returns True if the given text is a voucher analog."""
    return text.lower() in VOUCHER_ANALOGS


def is_batch_analog(text: str) -> bool:
    """Returns True if the given text is a batch analog."""
    return text.lower() in BATCH_ANALOGS


def is_auto_included(text: str) -> bool:
    """Returns True if the given text should be auto included."""
    text = text.lower()
    return (
        # is_line_number(text)
        is_forbidden_column_name(text)
        or is_voucher_analog(text)
        or is_batch_analog(text)
    )
