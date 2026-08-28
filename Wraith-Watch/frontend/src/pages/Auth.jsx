
import { useState } from "react";
import { API } from "../utils/constants";

function AuthShell({ children, footer }) {
  return (
    <div style={{
      minHeight: "100vh", width: "100%", display: "flex", alignItems: "center", justifyContent: "center",
      background: "var(--ww-surface)", padding: 20,
    }}>
      <div style={{ width: "100%", maxWidth: 380 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 28 }}>
          <i className="ti ti-eye" style={{ fontSize: 26, color: "#378ADD" }} aria-hidden="true" />
          <span style={{ fontSize: 20, fontWeight: 500, color: "var(--ww-text)" }}>WraithWatch</span>
        </div>
        <div style={{ background: "var(--ww-card)", border: "0.5px solid var(--ww-border)", borderRadius: 14, padding: "28px 26px" }}>
          {children}
        </div>
        {footer && <div style={{ textAlign: "center", marginTop: 18 }}>{footer}</div>}
      </div>
    </div>
  );
}

function FormField({ label, type = "text", value, onChange, placeholder, error, autoFocus, rightSlot }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 6 }}>{label}</label>
      <div style={{ position: "relative" }}>
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoFocus={autoFocus}
          style={{
            width: "100%", fontSize: 13, padding: "9px 12px",
            paddingRight: rightSlot ? 38 : 12,
            borderRadius: 8, border: `0.5px solid ${error ? "#D85A30" : "var(--ww-border)"}`,
            background: "var(--ww-surface)", color: "var(--ww-text)",
          }}
        />
        {rightSlot}
      </div>
      {error && <div style={{ fontSize: 11, color: "#D85A30", marginTop: 5 }}>{error}</div>}
    </div>
  );
}

function PasswordField({ label, value, onChange, placeholder, error, autoFocus }) {
  const [show, setShow] = useState(false);
  return (
    <FormField
      label={label}
      type={show ? "text" : "password"}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      error={error}
      autoFocus={autoFocus}
      rightSlot={
        <button
          type="button"
          onClick={() => setShow(s => !s)}
          aria-label={show ? "Hide password" : "Show password"}
          style={{
            position: "absolute", right: 4, top: "50%", transform: "translateY(-50%)",
            background: "none", border: "none", cursor: "pointer", padding: 6,
            color: "var(--ww-muted)", display: "flex", alignItems: "center",
          }}
        >
          <i className={`ti ti-${show ? "eye-off" : "eye"}`} style={{ fontSize: 15 }} aria-hidden="true" />
        </button>
      }
    />
  );
}

function Login({ onAuth, goSignup }) {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!identifier.trim() || !password) {
      setError("Enter your username/email and password.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: identifier.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Login failed.");
      } else {
        onAuth(data.token, data.user);
      }
    } catch {
      setError("Could not reach the backend. Is Flask running on port 5000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell footer={
      <span style={{ fontSize: 13, color: "var(--ww-muted)" }}>
        Don't have an account?{" "}
        <button onClick={goSignup} style={{ background: "none", border: "none", color: "#378ADD", fontWeight: 500, cursor: "pointer", fontSize: 13, padding: 0 }}>Sign up</button>
      </span>
    }>
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 17, fontWeight: 500, color: "var(--ww-text)", marginBottom: 4 }}>Log in</div>
        <div style={{ fontSize: 12, color: "var(--ww-muted)" }}>Welcome back. Enter your details to access the dashboard.</div>
      </div>

      <form onSubmit={submit}>
        <FormField label="Username or email" value={identifier} onChange={e => setIdentifier(e.target.value)} placeholder="analyst" autoFocus />
        <PasswordField label="Password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />

        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "9px 12px", borderRadius: 8, background: "#FAECE7", marginBottom: 14 }}>
            <i className="ti ti-alert-circle" style={{ fontSize: 14, color: "#712B13" }} aria-hidden="true" />
            <span style={{ fontSize: 12, color: "#712B13" }}>{error}</span>
          </div>
        )}

        <button type="submit" disabled={loading} style={{
          width: "100%", fontSize: 13, fontWeight: 500, padding: "10px 0", borderRadius: 8,
          border: "none", background: loading ? "#85B7EB" : "#378ADD", color: "#fff",
          cursor: loading ? "default" : "pointer", marginTop: 4,
        }}>
          {loading ? "Logging in…" : "Log in"}
        </button>
      </form>

      <div style={{ marginTop: 18, padding: "10px 12px", borderRadius: 8, background: "var(--ww-surface)", fontSize: 11, color: "var(--ww-muted)", lineHeight: 1.6 }}>
        <strong style={{ color: "var(--ww-text)" }}>Demo account</strong> — username <code>analyst</code>, password <code>Password123!</code>
      </div>
    </AuthShell>
  );
}

function Signup({ onAuth, goLogin }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const rules = [
    { label: "At least 8 characters", pass: password.length >= 8 },
    { label: "One uppercase letter", pass: /[A-Z]/.test(password) },
    { label: "One number", pass: /[0-9]/.test(password) },
  ];

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !email.trim() || !password) {
      setError("All fields are required.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (!rules.every(r => r.pass)) {
      setError("Password does not meet the requirements below.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), email: email.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Signup failed.");
      } else {
        onAuth(data.token, data.user);
      }
    } catch {
      setError("Could not reach the backend. Is Flask running on port 5000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell footer={
      <span style={{ fontSize: 13, color: "var(--ww-muted)" }}>
        Already have an account?{" "}
        <button onClick={goLogin} style={{ background: "none", border: "none", color: "#378ADD", fontWeight: 500, cursor: "pointer", fontSize: 13, padding: 0 }}>Log in</button>
      </span>
    }>
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 17, fontWeight: 500, color: "var(--ww-text)", marginBottom: 4 }}>Create an account</div>
        <div style={{ fontSize: 12, color: "var(--ww-muted)" }}>Set up analyst access to the WraithWatch dashboard.</div>
      </div>

      <form onSubmit={submit}>
        <FormField label="Username" value={username} onChange={e => setUsername(e.target.value)} placeholder="jane_analyst" autoFocus />
        <FormField label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="jane@soc.local" />
        <PasswordField label="Password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />

        <div style={{ marginBottom: 16, marginTop: -6 }}>
          {rules.map(r => (
            <div key={r.label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: r.pass ? "#1D9E75" : "var(--ww-muted)", marginBottom: 2 }}>
              <i className={`ti ti-${r.pass ? "circle-check-filled" : "circle"}`} style={{ fontSize: 12 }} aria-hidden="true" />
              {r.label}
            </div>
          ))}
        </div>

        <PasswordField label="Confirm password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="••••••••" />

        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "9px 12px", borderRadius: 8, background: "#FAECE7", marginBottom: 14 }}>
            <i className="ti ti-alert-circle" style={{ fontSize: 14, color: "#712B13" }} aria-hidden="true" />
            <span style={{ fontSize: 12, color: "#712B13" }}>{error}</span>
          </div>
        )}

        <button type="submit" disabled={loading} style={{
          width: "100%", fontSize: 13, fontWeight: 500, padding: "10px 0", borderRadius: 8,
          border: "none", background: loading ? "#85B7EB" : "#378ADD", color: "#fff",
          cursor: loading ? "default" : "pointer", marginTop: 4,
        }}>
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}
export { Login, Signup };
