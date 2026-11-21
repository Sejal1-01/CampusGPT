import { useState } from "react";
import { Button, Select } from "../components/ui";

interface MemberEditorProps {
  members: string[];
  usernames: string[];
  onAdd: (username: string) => Promise<boolean>;
  onRemove: (username: string) => Promise<boolean>;
}

export function MemberEditor({ members, usernames, onAdd, onRemove }: MemberEditorProps) {
  const [selected, setSelected] = useState("");
  const candidates = usernames.filter((username) => !members.includes(username));

  const add = async () => {
    if (await onAdd(selected)) setSelected("");
  };

  return (
    <div className="member-editor">
      <h4 className="subheading">Members ({members.length})</h4>
      {members.length === 0 ? (
        <p className="muted small">No members.</p>
      ) : (
        <ul className="chip-list">
          {members.map((member) => (
            <li key={member} className="chip chip--static">
              {member}
              <button
                type="button"
                className="chip-remove"
                aria-label={`Remove ${member}`}
                onClick={() => void onRemove(member)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="inline-form">
        <Select
          label="User"
          hideLabel
          options={candidates}
          placeholder="Choose user"
          value={selected}
          onChange={(event) => setSelected(event.target.value)}
        />
        <Button size="small" variant="secondary" disabled={!selected} onClick={() => void add()}>
          Add member
        </Button>
      </div>
    </div>
  );
}
