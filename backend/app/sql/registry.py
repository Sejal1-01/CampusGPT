from dataclasses import dataclass, field

DOMAINS = ("academics", "fees", "hostel", "mess", "teaching_feedback", "complaints")
SCOPES = ("self", "own_classes", "advisees", "department", "college")
SCOPE_PARAMETERS = {
    "self": ("student_id",),
    "own_classes": ("faculty_id", "dept_id"),
    "advisees": ("faculty_id", "dept_id"),
    "department": ("dept_id",),
    "college": (),
}
JOIN_KEYS = (
    "student_id",
    "offering_id",
    "feedback_id",
    "complaint_id",
    "fee_due_id",
    "faculty_id",
    "mess_id",
    "hostel_id",
    "dept_code",
)

Grant = tuple[str, str]


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    meaning: str
    allowed_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class Example:
    question: str
    sql: str


@dataclass(frozen=True)
class LogicalView:
    name: str
    description: str
    grants: tuple[Grant, ...]
    template: str
    columns: tuple[Column, ...]
    examples: tuple[Example, ...] = ()
    parameters: tuple[str, ...] = field(default=())

    @property
    def join_keys(self) -> tuple[str, ...]:
        names = {column.name for column in self.columns}
        return tuple(key for key in JOIN_KEYS if key in names)


def col(name: str, type_: str, meaning: str, *allowed_values: str) -> Column:
    return Column(name, type_, meaning, tuple(allowed_values))


def view(
    name: str,
    description: str,
    grants: list[Grant],
    template: str,
    columns: list[Column],
    examples: list[tuple[str, str]] | None = None,
) -> LogicalView:
    parameters = tuple(
        parameter
        for parameter in ("student_id", "faculty_id", "dept_id")
        if "{" + parameter + "}" in template
    )
    return LogicalView(
        name=name,
        description=description,
        grants=tuple(grants),
        template=template.strip(),
        columns=tuple(columns),
        examples=tuple(Example(question, sql) for question, sql in (examples or [])),
        parameters=parameters,
    )
