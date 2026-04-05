import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, getErrorMessage } from "../../lib/api";
import { setStoredAuth } from "../../lib/auth";
import { styles } from "../../lib/theme";
import AuthLayout from "./AuthLayout";

export default function DoctorLogin() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "doctor@meditrack.ai", password: "demo123" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loginDemo() {
    setLoading(true);
    setError("");
    try {
      await api.get("/patients");
      setStoredAuth({ role: "doctor", id: 1, name: "Dr. Aisha Kapoor" });
      navigate("/doctor/dashboard");
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not connect to backend."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Doctor Login" subtitle="Access your dashboard, AI consultations, and patient histories.">
      <input style={styles.input} placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <input
        style={styles.input}
        type="password"
        placeholder="Password"
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
      />
      {error ? <div style={{ color: "var(--red)" }}>{error}</div> : null}
      <button type="button" style={styles.primaryButton} onClick={loginDemo} disabled={loading}>
        {loading ? "Checking backend..." : "Login"}
      </button>
      <button type="button" style={styles.secondaryButton} onClick={loginDemo} disabled={loading}>
        Quick Demo Login
      </button>
      <div>
        <Link to="/doctor/signup">Don't have account? Sign up</Link>
      </div>
    </AuthLayout>
  );
}
