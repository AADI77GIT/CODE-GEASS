import { useNavigate } from "react-router-dom";
import { clearStoredAuth, getStoredAuth } from "../lib/auth";
import { styles, theme } from "../lib/theme";

export default function Sidebar({ role, activeKey, onSelect }) {
  const navigate = useNavigate();
  const auth = getStoredAuth();

  const doctorItems = [
    { key: "dashboard", label: "Dashboard" },
    { key: "patients", label: "Patients" },
    { key: "consult", label: "New Consultation" },
    { key: "insights", label: "AI Insights" },
    { key: "symptom-checker", label: "Symptom Checker" },
  ];

  const patientItems = [
    { key: "health", label: "My Health" },
    { key: "visits", label: "My Visits" },
    { key: "medications", label: "My Medications" },
    { key: "symptom-checker", label: "Symptom Checker" },
    { key: "report", label: "Download Report" },
  ];

  const items = role === "doctor" ? doctorItems : patientItems;

  return (
    <aside
      style={{
        background: theme.surface,
        borderRight: `1px solid ${theme.border}`,
        padding: 24,
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        position: "sticky",
        top: 0,
      }}
    >
      <div>
        <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 34, fontWeight: 700 }}>MediTrack AI</div>
        <div style={{ color: theme.muted, marginTop: 8, lineHeight: 1.6 }}>
          {role === "doctor" ? "Doctor workspace" : "Patient portal"}
        </div>
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 28 }}>
        {items.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => onSelect(item.key)}
            style={{
              ...styles.secondaryButton,
              textAlign: "left",
              background: activeKey === item.key ? theme.accent : theme.surface2,
              borderColor: activeKey === item.key ? theme.accent : theme.border,
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={() => {
          clearStoredAuth();
          navigate("/");
        }}
        style={{ ...styles.secondaryButton, marginTop: 16 }}
      >
        Logout
      </button>

      <div style={{ marginTop: "auto", ...styles.subtleCard }}>
        <div style={{ color: theme.muted, fontSize: 12, textTransform: "uppercase", letterSpacing: 1.5 }}>
          Logged In
        </div>
        <div style={{ marginTop: 10, fontWeight: 700 }}>{auth?.name || "Guest"}</div>
      </div>
    </aside>
  );
}
