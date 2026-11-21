from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.tokens import TokenType

from app.config import MAX_RESULT_ROWS

DENIED_FUNCTIONS = frozenset(
    {
        "LOAD_FILE",
        "SLEEP",
        "BENCHMARK",
        "GET_LOCK",
        "RELEASE_LOCK",
        "USER",
        "CURRENT_USER",
        "SESSION_USER",
        "SYSTEM_USER",
        "DATABASE",
        "SCHEMA",
        "VERSION",
        "CONNECTION_ID",
        "CURRENT_VERSION",
        "CURRENT_SCHEMA",
    }
)
RESERVED_SCHEMAS = frozenset({"information_schema", "mysql", "performance_schema", "sys"})
FORBIDDEN_COMMENT_MARKERS = ("/*!", "/*+")


class GuardError(Exception):
    pass


@dataclass(frozen=True)
class GuardedQuery:
    statement: exp.Query
    views: frozenset[str]
    has_explicit_limit: bool


def check_query(
    sql: str, allowed_views: frozenset[str], reserved_names: frozenset[str]
) -> GuardedQuery:
    _reject_forbidden_text(sql)
    statement = _parse_single(sql)
    _require_select(statement)
    cte_names = _cte_names(statement, reserved_names)
    views = _check_tables(statement, allowed_views, cte_names)
    _check_functions(statement)
    has_limit = _apply_limit(statement)
    return GuardedQuery(statement=statement, views=frozenset(views), has_explicit_limit=has_limit)


def _reject_forbidden_text(sql: str) -> None:
    if any(marker in sql for marker in FORBIDDEN_COMMENT_MARKERS):
        raise GuardError("Executable comments and optimizer hints are not allowed.")
    try:
        tokens = sqlglot.tokenize(sql, read="mysql")
    except SqlglotError as error:
        raise GuardError("The SQL could not be parsed.") from error
    for token in tokens:
        if token.token_type in (TokenType.PARAMETER, TokenType.SESSION_PARAMETER):
            raise GuardError("User variables and @@ system variables are not allowed.")


def _parse_single(sql: str) -> exp.Expression:
    try:
        statements = [item for item in sqlglot.parse(sql, read="mysql") if item is not None]
    except SqlglotError as error:
        raise GuardError("The SQL could not be parsed as a single MySQL SELECT.") from error
    if len(statements) != 1:
        raise GuardError("Exactly one SQL statement is allowed.")
    return statements[0]


def _require_select(statement: exp.Expression) -> None:
    if not isinstance(statement, exp.Select | exp.SetOperation):
        raise GuardError("Only SELECT queries are allowed.")
    for node in statement.walk():
        if isinstance(node, exp.Into):
            raise GuardError("SELECT ... INTO is not allowed.")
        if isinstance(node, exp.Lock):
            raise GuardError("Locking clauses are not allowed.")
        is_write = isinstance(node, exp.Insert | exp.Update | exp.Delete | exp.Create | exp.Drop)
        if is_write or isinstance(node, exp.Command):
            raise GuardError("Only SELECT queries are allowed.")


def _cte_names(statement: exp.Expression, reserved_names: frozenset[str]) -> set[str]:
    names: set[str] = set()
    for cte in statement.find_all(exp.CTE):
        name = cte.alias_or_name.lower()
        if name in reserved_names:
            raise GuardError(f"The CTE name '{name}' is reserved; choose another name.")
        names.add(name)
    return names


def _check_tables(
    statement: exp.Expression, allowed_views: frozenset[str], cte_names: set[str]
) -> set[str]:
    views: set[str] = set()
    for table in statement.find_all(exp.Table):
        if table.args.get("db") or table.args.get("catalog"):
            raise GuardError("Schema-qualified names are not allowed. Use only the listed views.")
        name = table.name.lower()
        if not name:
            raise GuardError("Table functions are not allowed.")
        if name in RESERVED_SCHEMAS:
            raise GuardError(f"'{name}' is not available.")
        if name in cte_names:
            continue
        if name not in allowed_views:
            raise GuardError(f"'{name}' is not one of your allowed views.")
        views.add(name)
    return views


def _function_name(node: exp.Func) -> str:
    if isinstance(node, exp.Anonymous):
        return str(node.name).upper()
    return node.sql_name().upper()


def _check_functions(statement: exp.Expression) -> None:
    for node in statement.find_all(exp.Func):
        name = _function_name(node)
        if name in DENIED_FUNCTIONS:
            raise GuardError(f"The function {name} is not allowed.")


def _apply_limit(statement: exp.Query) -> bool:
    limit = statement.args.get("limit")
    if limit is None:
        statement.set("limit", exp.Limit(expression=exp.Literal.number(MAX_RESULT_ROWS)))
        return False
    value = limit.expression
    if isinstance(value, exp.Literal) and value.is_int and int(value.this) <= MAX_RESULT_ROWS:
        return True
    limit.set("expression", exp.Literal.number(MAX_RESULT_ROWS))
    return True
