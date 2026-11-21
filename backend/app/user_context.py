from dataclasses import dataclass, field

from app.sql.registry import Grant, LogicalView
from app.sql.rewrite import ScopeParameters


@dataclass(frozen=True)
class UserContext:
    user_id: int
    username: str
    display_name: str
    roles: tuple[str, ...]
    department: str | None
    is_platform_admin: bool
    scope: ScopeParameters
    grants: frozenset[Grant] = field(default_factory=frozenset)
    views: dict[str, LogicalView] = field(default_factory=dict)

    @property
    def allowed_view_names(self) -> frozenset[str]:
        return frozenset(self.views)

    @property
    def allowed_areas(self) -> list[str]:
        return sorted({domain for domain, _scope in self.grants})
