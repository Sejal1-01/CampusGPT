import { useState, type FormEvent } from "react";
import { accessApi } from "../api/client";
import type { AccessOverview, GroupSummary } from "../api/types";
import { Button, Card, EmptyState, Input } from "../components/ui";
import { GrantEditor } from "./GrantEditor";
import { MemberEditor } from "./MemberEditor";
import type { ActionRunner } from "./useAccessAction";

interface SectionProps {
  overview: AccessOverview;
  run: ActionRunner;
}

function CreateGroupForm({ run }: { run: ActionRunner }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const created = await run(
      () => accessApi.createGroup({ name: name.trim(), description: description.trim() }),
      `Created group ${name.trim()}.`,
    );
    if (created) {
      setName("");
      setDescription("");
    }
  };

  return (
    <Card title="New group">
      <form className="inline-form" onSubmit={handleSubmit}>
        <Input
          label="Name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
        />
        <Input
          label="Description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <Button type="submit" disabled={!name.trim()}>
          Create
        </Button>
      </form>
    </Card>
  );
}

function GroupCard({ group, overview, run }: SectionProps & { group: GroupSummary }) {
  const remove = () => {
    if (window.confirm(`Delete group ${group.name}?`)) {
      void run(() => accessApi.deleteGroup(group.name), `Deleted group ${group.name}.`);
    }
  };
  return (
    <Card
      title={group.name}
      actions={
        <Button variant="danger" size="small" onClick={remove}>
          Delete
        </Button>
      }
    >
      {group.description && <p className="muted">{group.description}</p>}
      <GrantEditor
        kind="group"
        target={group.name}
        grants={group.grants}
        domains={overview.domains}
        scopes={overview.scopes}
        run={run}
      />
      <MemberEditor
        members={group.members}
        usernames={overview.users.map((user) => user.username)}
        onAdd={(username) =>
          run(
            () => accessApi.addGroupMember(group.name, username),
            `Added ${username} to ${group.name}.`,
          )
        }
        onRemove={(username) =>
          run(
            () => accessApi.removeGroupMember(group.name, username),
            `Removed ${username} from ${group.name}.`,
          )
        }
      />
    </Card>
  );
}

export function GroupsSection({ overview, run }: SectionProps) {
  return (
    <div className="access-stack">
      <CreateGroupForm run={run} />
      {overview.groups.length === 0 ? (
        <EmptyState title="No groups yet" />
      ) : (
        <div className="access-grid">
          {overview.groups.map((group) => (
            <GroupCard key={group.name} group={group} overview={overview} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
