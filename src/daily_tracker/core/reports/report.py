import pathlib

import duckdb

from daily_tracker.utils import DB

HERE = pathlib.Path(__file__).parent
QUERIES = HERE / "queries"


def _query(sql: str) -> duckdb.DuckDBPyRelation:
    duckdb.sql(f"attach {str(DB)!r} as tracker (read_only true)")
    return duckdb.sql(sql)


def report(report_name: str) -> None:
    result = _query((QUERIES / report_name).with_suffix(".sql").read_text())
    result.show(max_rows=len(result), null_value="")
