from app.access import repository
from app.access.model import EffectiveAccess, GrantSource
from app.sql.registry import Grant, LogicalView
from app.sql.views import all_views


def effective_access(user_id: int) -> EffectiveAccess:
    sources: list[GrantSource] = []
    for row in repository.role_grants_for_user(user_id):
        sources.append(GrantSource(row["domain"], row["scope"], "role", row["name"]))
    for row in repository.group_grants_for_user(user_id):
        sources.append(GrantSource(row["domain"], row["scope"], "group", row["name"]))
    for row in repository.direct_grants_for_user(user_id):
        sources.append(GrantSource(row["domain"], row["scope"], "user", "direct"))
    grants = frozenset((source.domain, source.scope) for source in sources)
    roles = tuple(repository.user_role_names(user_id))
    return EffectiveAccess(roles=roles, grants=grants, sources=tuple(sources))


def allowed_views(
    grants: frozenset[Grant], available_parameters: set[str]
) -> dict[str, LogicalView]:
    return {
        name: item
        for name, item in all_views().items()
        if set(item.grants) & grants and set(item.parameters) <= available_parameters
    }
