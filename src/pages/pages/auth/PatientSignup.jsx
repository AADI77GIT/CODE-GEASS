import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, getErrorMessage } from "../../lib/api";
import { styles } from "../../lib/theme";
import AuthLayout from "./AuthLayout";

const bloodGroups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"];

export default function PatientSignup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    age: "",
    gender: "Female",
    phone: "",
    blood_group: "B+",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setLoading(true);
    setError("");
    try {
      await api.post("/patients", {
        name: form.name,
        age: Number(form.age),
        gender: form.gender,
        phone: form.phone,
        blood_group: form.blood_group,
      });
      navigate("/patient/login");
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not create patient."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Patient Signup" subtitle="Create a patient profile for the portal experience.">
      <input style={styles.input} placeholder="Full Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <input style={styles.input} placeholder="Age" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} />
      <div style={{ display: "flex", gap: 12 }}>
        {["Male", "Female", "Other"].map((gender) => (
          <label key={gender} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input type="radio" checked={form.gender === gender} onChange={() => setForm({ ...form, gender })} />
            {gender}
          </label>
        ))}
      </div>
      <input style={styles.input} placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
      <select style={styles.input} value={form.blood_group} onChange={(e) => setForm({ ...form, blood_group: e.target.value })}>
        {bloodGroups.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <input
        style={styles.input}
        type="password"
        placeholder="Password"
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
      />
      {error ? <div style={{ color: "var(--red)" }}>{error}</div> : null}
      <button type="button" style={styles.primaryButton} disabled={loading} onClick={submit}>
        {loading ? "Creating..." : "Create Account"}
      </button>
      <div>
        <Link to="/patient/login">← Back to login</Link>
      </div>
    </AuthLayout>
  );
}
