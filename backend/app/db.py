import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any

from mysql.connector import pooling
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

from app.config import MySqlAccount, get_settings

logger = logging.getLogger(__name__)

Connection = PooledMySQLConnection | MySQLConnectionAbstract


class Account(Enum):
    READONLY = "readonly"
    APP = "app"
    AUTH_RW = "auth_rw"


_pools: dict[Account, pooling.MySQLConnectionPool] = {}


def _account_credentials(account: Account) -> tuple[MySqlAccount, str]:
    settings = get_settings()
    if account is Account.READONLY:
        return settings.readonly_account, settings.mysql_db
    if account is Account.APP:
        return settings.app_account, settings.mysql_db
    return settings.auth_rw_account, settings.mysql_auth_db


def _pool(account: Account) -> pooling.MySQLConnectionPool:
    if account not in _pools:
        settings = get_settings()
        credentials, database = _account_credentials(account)
        _pools[account] = pooling.MySQLConnectionPool(
            pool_name=f"campusgpt_{account.value}",
            pool_size=8,
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=credentials.user,
            password=credentials.password,
            database=database,
            charset="utf8mb4",
            autocommit=True,
        )
    return _pools[account]


@contextmanager
def connection(account: Account) -> Iterator[Connection]:
    conn = _pool(account).get_connection()
    try:
        yield conn
    finally:
        conn.close()


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]


def fetch_all(account: Account, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    with connection(account) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
    return [dict(row) for row in rows]


def fetch_one(account: Account, sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
    rows = fetch_all(account, sql, params)
    return rows[0] if rows else None


def execute(account: Account, sql: str, params: Sequence[Any] = ()) -> int:
    with connection(account) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        last_id = cursor.lastrowid or 0
        cursor.close()
    return last_id


def run_bounded_query(sql: str, max_rows: int, timeout_ms: int) -> QueryResult:
    with connection(Account.READONLY) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={int(timeout_ms)}")
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description or []]
        rows = [list(row) for row in cursor.fetchmany(max_rows)]
        cursor.fetchall()
        cursor.close()
    return QueryResult(columns=columns, rows=rows)


def ping() -> bool:
    try:
        fetch_one(Account.APP, "SELECT 1 AS ok")
    except Exception:
        logger.exception("database ping failed")
        return False
    return True
