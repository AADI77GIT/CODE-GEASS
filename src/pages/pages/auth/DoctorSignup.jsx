import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { styles } from "../../lib/theme";
import AuthLayout from "./AuthLayout";

const specialties = ["General Physician", "Cardiologist", "Diabetologist", "Pulmonologist", "Other"];

export default function DoctorSignup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    specialization: specialties[0],
    phone: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");

  function submit() {
    if (!form.name || !form.email || !form.phone || !form.password) {
      setError("Please complete all fields.");
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    navigate("/doctor/login");
  }

  return (
    <AuthLayout title="Doctor Signup" subtitle="Create a demo-ready doctor account for the hackathon flow.">
      <input style={styles.input} placeholder="Full Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <input style={styles.input} placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <select style={styles.input} value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })}>
        {specialties.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <input style={styles.input} placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
      <input
        style={styles.input}
        type="password"
        placeholder="Password"
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
      />
      <input
        style={styles.input}
        type="password"
        placeholder="Confirm Password"
        value={form.confirmPassword}
        onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
      />
      {error ? <div style={{ color: "var(--red)" }}>{error}</div> : null}
      <button type="button" style={styles.primaryButton} onClick={submit}>
        Create Account
      </button>
      <div>
        <Link to="/doctor/login">← Back to login</Link>
      </div>
    </AuthLayout>
  );
}
