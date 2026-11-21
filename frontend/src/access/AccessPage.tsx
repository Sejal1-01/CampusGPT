import { useState } from "react";
import { accessApi, errorMessage } from "../api/client";
import { ErrorBanner, Spinner } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { AuditSection } from "./AuditSection";
import { GroupsSection } from "./GroupsSection";
import { RolesSection } from "./RolesSection";
import { useAccessAction } from "./useAccessAction";
import { UsersSection } from "./UsersSection";

const TABS = ["Roles", "Groups", "Users", "Audit log"] as const;
type Tab = (typeof TABS)[number];

export default function AccessPage() {
  const [tab, setTab] = useState<Tab>("Roles");
  const overview = useApi("access-overview", accessApi.overview);
  const action = useAccessAction(overview.reload);

  return (
    <main className="access-page">
      <div className="access-header">
        <h1 className="page-title">Access</h1>
        <nav className="tabs" aria-label="Access sections">
          {TABS.map((name) => (
            <button
              key={name}
              type="button"
              className={`tab${name === tab ? " tab--active" : ""}`}
              aria-current={name === tab ? "page" : undefined}
              onClick={() => setTab(name)}
            >
              {name}
            </button>
          ))}
        </nav>
        {action.isBusy && <Spinner size="small" label="Saving" />}
      </div>
      {action.error && <ErrorBanner message={action.error} onDismiss={action.clearError} />}
      {action.notice && (
        <p className="notice" role="status">
          {action.notice}
        </p>
      )}
      {tab === "Audit log" ? (
        <AuditSection />
      ) : overview.error ? (
        <ErrorBanner message={errorMessage(overview.error)} onRetry={overview.reload} />
      ) : !overview.data ? (
        <Spinner label="Loading access" />
      ) : tab === "Roles" ? (
        <RolesSection overview={overview.data} run={action.run} />
      ) : tab === "Groups" ? (
        <GroupsSection overview={overview.data} run={action.run} />
      ) : (
        <UsersSection overview={overview.data} run={action.run} />
      )}
    </main>
  );
}
