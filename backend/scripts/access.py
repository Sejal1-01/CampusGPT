import argparse
import json
import logging
import sys

from app.access import repository, service
from app.access.model import AccessError
from app.access.resolver import allowed_views, effective_access

logger = logging.getLogger("access")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage CampusGPT access (platform admin only).")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="Show roles, groups and their grants and members")
    for name in ("create-group", "delete-group"):
        command = commands.add_parser(name)
        command.add_argument("group")
        if name == "create-group":
            command.add_argument("--description", default="")
    for name in ("add-member", "remove-member"):
        command = commands.add_parser(name)
        command.add_argument("group")
        command.add_argument("username")
    for name in ("grant", "revoke"):
        command = commands.add_parser(name)
        command.add_argument("kind", choices=["role", "group", "user"])
        command.add_argument("target")
        command.add_argument("domain")
        command.add_argument("scope")
    for name in ("assign-role", "unassign-role"):
        command = commands.add_parser(name)
        command.add_argument("username")
        command.add_argument("role")
    command = commands.add_parser("create-role")
    command.add_argument("role")
    command.add_argument("--description", default="")
    command = commands.add_parser("effective", help="Show a user's effective access")
    command.add_argument("username")
    return parser


def _effective(username: str) -> dict:
    row = repository.find_user_by_username(username)
    if row is None:
        raise AccessError(f"No user named '{username}'.")
    access = effective_access(int(row["id"]))
    available = {key for key in ("student_id", "faculty_id", "dept_id") if row[key] is not None}
    return {
        "roles": list(access.roles),
        "grants": [vars(source) for source in access.sources],
        "views": sorted(allowed_views(access.grants, available)),
    }


def run(args: argparse.Namespace) -> object:
    actions = {
        "list": lambda: {"roles": service.list_roles(), "groups": service.list_groups()},
        "create-group": lambda: service.create_group(args.group, args.description),
        "delete-group": lambda: service.delete_group(args.group),
        "add-member": lambda: service.add_member(args.group, args.username),
        "remove-member": lambda: service.remove_member(args.group, args.username),
        "grant": lambda: service.grant(args.kind, args.target, args.domain, args.scope),
        "revoke": lambda: service.revoke(args.kind, args.target, args.domain, args.scope),
        "assign-role": lambda: service.assign_role(args.username, args.role),
        "unassign-role": lambda: service.unassign_role(args.username, args.role),
        "create-role": lambda: service.create_role(args.role, args.description),
        "effective": lambda: _effective(args.username),
    }
    return actions[args.command]()


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parser().parse_args(argv)
    try:
        output = run(args)
    except AccessError as error:
        logger.error("Rejected: %s", error)
        return 1
    if output is not None:
        sys.stdout.write(json.dumps(output, indent=2, default=str) + "\n")
    logger.info("Done. Changes apply at each user's next login.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
