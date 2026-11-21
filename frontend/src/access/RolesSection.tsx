import { accessApi } from "../api/client";
import type { AccessOverview } from "../api/types";
import { Card, EmptyState } from "../components/ui";
import { formatRole } from "../lib/format";
import { GrantEditor } from "./GrantEditor";
import { MemberEditor } from "./MemberEditor";
import type { ActionRunner } from "./useAccessAction";

export function RolesSection({ overview, run }: { overview: AccessOverview; run: ActionRunner }) {
  if (overview.roles.length === 0) return <EmptyState title="No roles" />;
  const usernames = overview.users.map((user) => user.username);
  return (
    <div className="access-grid">
      {overview.roles.map((role) => (
        <Card key={role.name} title={formatRole(role.name)}>
          {role.description && <p className="muted">{role.description}</p>}
          <GrantEditor
            kind="role"
            target={role.name}
            grants={role.grants}
            domains={overview.domains}
            scopes={overview.scopes}
            run={run}
          />
          <MemberEditor
            members={role.members}
            usernames={usernames}
            onAdd={(username) =>
              run(
                () => accessApi.assignRole(username, role.name),
                `Assigned ${role.name} to ${username}.`,
              )
            }
            onRemove={(username) =>
              run(
                () => accessApi.removeRole(username, role.name),
                `Removed ${role.name} from ${username}.`,
              )
            }
          />
        </Card>
      ))}
    </div>
  );
}
