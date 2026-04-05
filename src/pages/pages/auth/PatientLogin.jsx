import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { setStoredAuth } from "../../lib/auth";
import { styles } from "../../lib/theme";
import AuthLayout from "./AuthLayout";

export default function PatientLogin() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ phone: "9876543210", password: "demo123" });

  function loginDemo() {
    setStoredAuth({ role: "patient", id: 1, name: "Riya Sharma" });
    navigate("/patient/portal");
  }

  return (
    <AuthLayout title="Patient Login" subtitle="Open your visits, medications, and AI-generated history safely.">
      <input style={styles.input} placeholder="Phone Number" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
      <input
        style={styles.input}
        type="password"
        placeholder="Password or DOB"
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
      />
      <button type="button" style={styles.primaryButton} onClick={loginDemo}>
        Login
      </button>
      <button type="button" style={styles.secondaryButton} onClick={loginDemo}>
        Quick Demo Login
      </button>
      <div>
        <Link to="/patient/signup">Don't have account? Sign up</Link>
      </div>
    </AuthLayout>
  );
}
