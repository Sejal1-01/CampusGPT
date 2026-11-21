import { useState, type FormEvent } from "react";
import { api, errorMessage } from "../api/client";
import { Button, Card, ErrorBanner, Input, Spinner } from "../components/ui";
import { DEMO_PASSWORD } from "../config";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../hooks/useAuth";
import { formatRole } from "../lib/format";

function DemoAccounts({ onPick }: { onPick: (username: string) => void }) {
  const accounts = useApi("demo-accounts", api.demoAccounts);
  if (accounts.error) {
    return <ErrorBanner message={errorMessage(accounts.error)} onRetry={accounts.reload} />;
  }
  if (!accounts.data) return <Spinner size="small" label="Loading demo accounts" />;
  if (accounts.data.length === 0) return <p className="muted small">No demo accounts.</p>;
  return (
    <div className="demo-accounts">
      <p className="demo-accounts-title">
        Demo accounts <span className="muted">(password {DEMO_PASSWORD})</span>
      </p>
      <ul>
        {accounts.data.map((account) => (
          <li key={account.username}>
            <button type="button" className="demo-account" onClick={() => onPick(account.username)}>
              <span className="demo-account-name">{account.username}</span>
              <span className="demo-account-role">{formatRole(account.role)}</span>
              {account.note && <span className="demo-account-note">{account.note}</span>}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(username.trim(), password);
    } catch (loginError) {
      setError(errorMessage(loginError));
      setIsSubmitting(false);
    }
  };

  const pickAccount = (demoUsername: string) => {
    setUsername(demoUsername);
    setPassword(DEMO_PASSWORD);
    setError(null);
  };

  return (
    <main className="login-page">
      <Card className="login-card">
        <div className="login-brand">
          <img src="/iiitbh-logo.png" alt="IIIT Bhagalpur logo" className="login-logo" />
          <h1 className="login-institute">Indian Institute of Information Technology Bhagalpur</h1>
          <p className="login-motto" lang="sa">
            चारित्र्यं मम जीवनम्
          </p>
          <p className="login-product">CampusGPT</p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          {error && <ErrorBanner message={error} />}
          <Input
            label="Username"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
            autoFocus
          />
          <Input
            label="Password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          <Button type="submit" isLoading={isSubmitting} disabled={!username.trim() || !password}>
            Log in
          </Button>
        </form>
        <DemoAccounts onPick={pickAccount} />
      </Card>
    </main>
  );
}
