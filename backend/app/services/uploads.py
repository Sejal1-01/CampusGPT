import csv
import io
import re
import secrets
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Any

from app.config import (
    MAX_CSV_BYTES,
    MAX_CSV_COLUMNS,
    MAX_CSV_ROWS,
    MAX_RESULT_ROWS,
    SQLITE_MAX_STEPS,
)
from app.errors import AppError
from app.schemas import DatasetUploadResponse, StoredResult
from app.services.portal_data import _model_payload, reserved_names
from app.sessions import Session
from app.sql.guard import GuardError, check_query

PROGRESS_INTERVAL = 1000


@dataclass
class UploadStore:
    connection: sqlite3.Connection
    lock: threading.Lock = field(default_factory=threading.Lock)
    tables: dict[str, list[str]] = field(default_factory=dict)
    steps: int = 0

    def count_steps(self) -> int:
        self.steps += PROGRESS_INTERVAL
        return 1 if self.steps > SQLITE_MAX_STEPS else 0


def _store(session: Session) -> UploadStore:
    if session.uploads is None:
        store = UploadStore(connection=sqlite3.connect(":memory:", check_same_thread=False))
        store.connection.set_progress_handler(store.count_steps, PROGRESS_INTERVAL)
        session.uploads = store
    return session.uploads


def clean_name(raw: str, taken: set[str], fallback: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_") or fallback
    if name[0].isdigit():
        name = f"c_{name}"
    base, suffix = name, 2
    while name in taken:
        name, suffix = f"{base}_{suffix}", suffix + 1
    return name


def _number(value: str) -> float | None:
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _typed_columns(rows: list[list[str]], width: int) -> list[bool]:
    numeric = []
    for index in range(width):
        values = [row[index] for row in rows if index < len(row) and row[index].strip()]
        numeric.append(bool(values) and all(_number(value) is not None for value in values))
    return numeric


def parse_csv(data: bytes) -> tuple[list[str], list[list[str]]]:
    if len(data) > MAX_CSV_BYTES:
        raise AppError("csv_too_large", "The CSV is larger than 5 MB.", 400)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise AppError("csv_encoding", "Save the CSV as UTF-8 and upload it again.", 400) from error
    rows = [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]
    if len(rows) < 2:
        raise AppError("csv_empty", "The CSV needs a header row and at least one data row.", 400)
    if len(rows[0]) > MAX_CSV_COLUMNS or len(rows) - 1 > MAX_CSV_ROWS:
        raise AppError(
            "csv_too_big", f"At most {MAX_CSV_COLUMNS} columns and {MAX_CSV_ROWS} rows.", 400
        )
    return rows[0], rows[1:]


def store_csv(session: Session, filename: str, data: bytes) -> DatasetUploadResponse:
    header, rows = parse_csv(data)
    store = _store(session)
    columns = _unique(
        [clean_name(name, set(), f"column_{index + 1}") for index, name in enumerate(header)]
    )
    table = clean_name(
        "upload_" + filename.rsplit(".", 1)[0], set(store.tables) | reserved_names(), "upload"
    )
    numeric = _typed_columns(rows, len(columns))
    definition = ", ".join(
        f'"{name}" {"REAL" if is_number else "TEXT"}'
        for name, is_number in zip(columns, numeric, strict=True)
    )
    values = [[_cell(row, index, numeric[index]) for index in range(len(columns))] for row in rows]
    with store.lock:
        store.connection.execute(f'CREATE TABLE "{table}" ({definition})')
        store.connection.executemany(
            f'INSERT INTO "{table}" VALUES ({", ".join("?" * len(columns))})', values
        )
    store.tables[table] = columns
    return DatasetUploadResponse(
        dataset_id=table, table_name=table, columns=columns, rows=len(values)
    )


def _unique(columns: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for name in columns:
        result.append(clean_name(name, seen, name))
        seen.add(result[-1])
    return result


def _cell(row: list[str], index: int, is_number: bool) -> Any:
    value = row[index].strip() if index < len(row) else ""
    if not value:
        return None
    return _number(value) if is_number else value


def describe_uploads(session: Session) -> str:
    if session.uploads is None or not session.uploads.tables:
        return "No CSV uploaded in this chat."
    return "\n".join(
        f"- {table}: columns {', '.join(columns)}"
        for table, columns in session.uploads.tables.items()
    )


def query_uploads(session: Session, sql: str, explanation: str) -> dict[str, Any]:
    if session.uploads is None or not session.uploads.tables:
        return {"error": "No CSV uploaded in this chat. Ask the user to upload one."}
    store = session.uploads
    try:
        guarded = check_query(sql, frozenset(store.tables), reserved_names())
        final_sql = guarded.statement.sql(dialect="sqlite")
        with store.lock:
            store.steps = 0
            cursor = store.connection.execute(final_sql)
            columns = [item[0] for item in cursor.description or []]
            rows = [list(row) for row in cursor.fetchmany(MAX_RESULT_ROWS)]
    except GuardError as error:
        return {"error": str(error), "hint": "Fix the query and retry once."}
    except sqlite3.Error as error:
        return {"error": f"Query failed: {error}", "hint": "Fix the query and retry once."}
    stored = StoredResult(
        result_id=f"r_{secrets.token_hex(4)}",
        columns=columns,
        rows=rows,
        total_rows=len(rows),
        truncated=False,
        sql=sql.strip(),
        explanation=explanation.strip(),
    )
    session.store_result(stored)
    return _model_payload(stored)
