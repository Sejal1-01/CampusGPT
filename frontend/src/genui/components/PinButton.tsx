import { useState } from "react";
import { Button } from "../../components/ui";
import { useCurrentUser } from "../../hooks/useAuth";
import { findPin, pinTile, unpinTile, type TileSpec } from "../../lib/pinnedTiles";

export function PinButton({ spec }: { spec: TileSpec }) {
  const user = useCurrentUser();
  const username = user && !user.is_platform_admin ? user.username : null;
  const [pinnedId, setPinnedId] = useState<string | null>(() =>
    username ? (findPin(username, spec)?.id ?? null) : null,
  );
  const [hasFailed, setHasFailed] = useState(false);
  if (!username) return null;

  const toggle = () => {
    if (pinnedId) {
      const removed = unpinTile(username, pinnedId);
      setHasFailed(!removed);
      if (removed) setPinnedId(null);
      return;
    }
    const tile = pinTile(username, spec);
    setHasFailed(tile === null);
    setPinnedId(tile?.id ?? null);
  };

  return (
    <span className="pin-control">
      <Button variant="secondary" size="small" onClick={toggle} aria-pressed={pinnedId !== null}>
        {pinnedId ? "Unpin" : "Pin"}
      </Button>
      {hasFailed && (
        <span className="pin-error" role="alert">
          Can't save pins in this browser.
        </span>
      )}
    </span>
  );
}
