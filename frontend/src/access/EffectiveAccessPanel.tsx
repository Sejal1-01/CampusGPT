import { useState, type FormEvent } from "react";
import { accessApi, errorMessage } from "../api/client";
import type { AccessOverview, GrantRow } from "../api/types";
import { Button, Card, ErrorBanner, Input, Spinner, Table } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { formatRole } from "../lib/format";
import { GrantEditor } from "./GrantEditor";
import type { ActionRunner } from "./useAccessAction";

interface PanelProps {
  username: string;
  overview: AccessOverview;
  run: ActionRunner;
  onClose: () => void;
}

function ResetPasswordForm({ username, run }: { username: string; run: ActionRunner }) {
  const [password, setPassword] = useState("");
  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (
      await run(
        () => accessApi.resetPassword(username, password),
        `Password reset for ${username}.`,
      )
    ) {
      setPassword("");
    }
  };
  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <Input
        label="New password"
        type="password"
        minLength={6}
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        autoComplete="new-password"
      />
      <Button type="submit" variant="secondary" disabled={password.length === 0}>
        Reset password
      </Button>
    </form>
  );
}

export function EffectiveAccessPanel({ username, overview, run, onClose }: PanelProps) {
  const effective = useApi(`effective:${username}`, () => accessApi.effective(username));
  const runAndRefresh: ActionRunner = async (action, success) => {
    const ok = await run(action, success);
    if (ok) effective.reload();
    return ok;
  };

  const actions = (
    <Button variant="ghost" size="small" onClick={onClose}>
      Close
    </Button>
  );

  if (effective.error) {
    return (
      <Card title={`Access: ${username}`} actions={actions}>
        <ErrorBanner message={errorMessage(effective.error)} onRetry={effective.reload} />
      </Card>
    );
  }
  if (!effective.data) {
    return (
      <Card title={`Access: ${username}`} actions={actions}>
        <Spinner label="Loading access" />
      </Card>
    );
  }

  const { roles, grants, views } = effective.data;
  const userGrants: GrantRow[] = grants.filter((grant) => grant.source === "user");

  return (
    <Card title={`Access: ${username}`} actions={actions}>
      <p>
        <strong>Roles:</strong> {roles.length ? roles.map(formatRole).join(", ") : "None"}
      </p>
      <h4 className="subheading">Effective grants</h4>
      <Table
        columns={["Domain", "Scope", "From", "Name"]}
        rows={grants.map((grant) => [
          grant.domain,
          grant.scope,
          formatRole(grant.source),
          grant.name,
        ])}
      />
      <h4 className="subheading">Views ({views.length})</h4>
      <p className="muted small">{views.length ? views.join(", ") : "No views."}</p>
      <GrantEditor
        kind="user"
        target={username}
        grants={userGrants}
        domains={overview.domains}
        scopes={overview.scopes}
        run={runAndRefresh}
      />
      <ResetPasswordForm username={username} run={run} />
    </Card>
  );
}
