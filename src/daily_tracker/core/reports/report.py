from __future__ import annotations

import dataclasses
import pathlib
import re

import duckdb

from daily_tracker.utils import DB

HERE = pathlib.Path(__file__).parent
QUERIES = HERE / "queries"
PARAMS_PATTERN = re.compile(r"{([\w-]+)}")


@dataclasses.dataclass
class Report:
    path: pathlib.Path
    params: list[str]

    @classmethod
    def from_path(cls, filepath: pathlib.Path) -> Report:
        return cls(
            path=filepath,
            params=sorted(
                PARAMS_PATTERN.findall(filepath.read_text(encoding="utf-8"))
            ),
        )


def get_reports() -> list[Report]:
    return sorted(
        [
            Report.from_path(p)
            for p in QUERIES.iterdir()
            if p.is_file() and p.suffix == ".sql"
        ],
        key=lambda r: r.path.name,
    )


def _query(sql: str) -> duckdb.DuckDBPyRelation:
    duckdb.sql(f"attach {str(DB)!r} as tracker (read_only true)")
    return duckdb.sql(sql)


def report(report_name: str, params: dict[str, str | int]) -> None:
    query = (QUERIES / report_name).with_suffix(".sql").read_text()
    result = _query(query.format(**params))
    result.show(max_rows=len(result), null_value="")
