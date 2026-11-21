import { useCallback, useState } from "react";
import { errorMessage } from "../api/client";

export type ActionRunner = (action: () => Promise<unknown>, success: string) => Promise<boolean>;

export function useAccessAction(onDone: () => void) {
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  const run = useCallback<ActionRunner>(
    async (action, success) => {
      setIsBusy(true);
      setError(null);
      setNotice(null);
      try {
        await action();
        setNotice(success);
        onDone();
        return true;
      } catch (actionError) {
        setError(errorMessage(actionError));
        return false;
      } finally {
        setIsBusy(false);
      }
    },
    [onDone],
  );

  return { run, error, notice, isBusy, clearError: () => setError(null) };
}
