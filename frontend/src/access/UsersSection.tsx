import { useState } from "react";
import type { AccessOverview } from "../api/types";
import { Button, Card, Table } from "../components/ui";
import { CreateUserForm } from "./CreateUserForm";
import { EffectiveAccessPanel } from "./EffectiveAccessPanel";
import type { ActionRunner } from "./useAccessAction";

export function UsersSection({ overview, run }: { overview: AccessOverview; run: ActionRunner }) {
  const [selected, setSelected] = useState<string | null>(null);
  const rows = overview.users.map((user) => [
    user.username,
    user.display_name,
    user.is_platform_admin ? "Yes" : "No",
    <Button key="view" variant="secondary" size="small" onClick={() => setSelected(user.username)}>
      View access
    </Button>,
  ]);

  return (
    <div className="access-stack">
      {selected && (
        <EffectiveAccessPanel
          key={selected}
          username={selected}
          overview={overview}
          run={run}
          onClose={() => setSelected(null)}
        />
      )}
      <Card title={`Users (${overview.users.length})`}>
        <Table columns={["Username", "Name", "Admin", ""]} rows={rows} />
      </Card>
      <CreateUserForm run={run} />
    </div>
  );
}
