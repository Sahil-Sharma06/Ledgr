import { useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";

export default function SignupPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/signup", { email, password });
      // After signup, auto-login
      const res = await api.post("/auth/login", { email, password });
      localStorage.setItem("token", res.data.access_token);
      navigate("/dashboard");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail ?? "Could not create account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="grid-bg" aria-hidden="true" />

      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-logo">₹</div>
          <span className="auth-logo-text">Ledgr</span>
        </div>

        <h1 className="auth-title">Create account</h1>
        <p className="auth-subtitle">Start tracking your finances</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field-group">
            <label htmlFor="signup-email" className="field-label">Email</label>
            <input
              id="signup-email"
              type="email"
              className="field-input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="field-group">
            <label htmlFor="signup-password" className="field-label">Password</label>
            <input
              id="signup-password"
              type="password"
              className="field-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button id="signup-btn" type="submit" className="auth-btn" disabled={loading}>
            {loading ? <span className="btn-spinner" /> : "Create account"}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login" className="auth-link">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
