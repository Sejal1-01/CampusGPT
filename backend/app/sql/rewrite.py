from dataclasses import dataclass
from datetime import date

import sqlglot
from sqlglot import exp

from app.config import CURRENT_ACADEMIC_YEAR
from app.sql.registry import LogicalView


@dataclass(frozen=True)
class ScopeParameters:
    student_id: int | None
    faculty_id: int | None
    dept_id: int | None
    today: date

    def available(self) -> set[str]:
        values = {
            "student_id": self.student_id,
            "faculty_id": self.faculty_id,
            "dept_id": self.dept_id,
        }
        return {name for name, value in values.items() if value is not None}


class RewriteError(Exception):
    pass


def bind_template(view: LogicalView, scope: ScopeParameters) -> str:
    missing = set(view.parameters) - scope.available()
    if missing:
        raise RewriteError(
            f"View {view.name} needs {sorted(missing)} which this user does not have."
        )
    return view.template.format(
        student_id=int(scope.student_id or 0),
        faculty_id=int(scope.faculty_id or 0),
        dept_id=int(scope.dept_id or 0),
        year=f"'{CURRENT_ACADEMIC_YEAR}'",
        today=f"'{scope.today.isoformat()}'",
    )


def rewrite(
    statement: exp.Query,
    views: dict[str, LogicalView],
    scope: ScopeParameters,
    cte_names: frozenset[str] = frozenset(),
) -> str:
    rewritten = statement.copy()
    for table in list(rewritten.find_all(exp.Table)):
        name = table.name.lower()
        if name in cte_names or name not in views:
            continue
        derived = sqlglot.parse_one(bind_template(views[name], scope), read="mysql")
        alias = table.alias or name
        table.replace(
            exp.Subquery(this=derived, alias=exp.TableAlias(this=exp.to_identifier(alias)))
        )
    return rewritten.sql(dialect="mysql", comments=False)


def cte_names_of(statement: exp.Expression) -> frozenset[str]:
    return frozenset(cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE))
