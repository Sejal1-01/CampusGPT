import { useState } from "react";
import { accessApi } from "../api/client";
import type { GrantKind, GrantRow } from "../api/types";
import { Button, Select } from "../components/ui";
import type { ActionRunner } from "./useAccessAction";

interface GrantEditorProps {
  kind: GrantKind;
  target: string;
  grants: GrantRow[];
  domains: string[];
  scopes: string[];
  run: ActionRunner;
}

export function GrantEditor({ kind, target, grants, domains, scopes, run }: GrantEditorProps) {
  const [domain, setDomain] = useState("");
  const [scope, setScope] = useState("");

  const add = async () => {
    const added = await run(
      () => accessApi.addGrant({ kind, target, domain, scope }),
      `Granted ${domain} · ${scope} to ${target}.`,
    );
    if (added) {
      setDomain("");
      setScope("");
    }
  };

  const revoke = (grant: GrantRow) =>
    run(
      () => accessApi.revokeGrant({ kind, target, domain: grant.domain, scope: grant.scope }),
      `Revoked ${grant.domain} · ${grant.scope} from ${target}.`,
    );

  return (
    <div className="grant-editor">
      <h4 className="subheading">Grants</h4>
      {grants.length === 0 ? (
        <p className="muted small">No grants.</p>
      ) : (
        <ul className="chip-list">
          {grants.map((grant) => (
            <li key={`${grant.domain}-${grant.scope}`} className="chip chip--static">
              {grant.domain} · {grant.scope}
              <button
                type="button"
                className="chip-remove"
                aria-label={`Revoke ${grant.domain} ${grant.scope}`}
                onClick={() => void revoke(grant)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="inline-form">
        <Select
          label="Domain"
          hideLabel
          options={domains}
          placeholder="Domain"
          value={domain}
          onChange={(event) => setDomain(event.target.value)}
        />
        <Select
          label="Scope"
          hideLabel
          options={scopes}
          placeholder="Scope"
          value={scope}
          onChange={(event) => setScope(event.target.value)}
        />
        <Button
          size="small"
          variant="secondary"
          disabled={!domain || !scope}
          onClick={() => void add()}
        >
          Add grant
        </Button>
      </div>
    </div>
  );
}
