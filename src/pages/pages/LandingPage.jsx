import { Link } from "react-router-dom";
import { styles, theme } from "../lib/theme";

function RoleCard({ icon, title, subtitle, buttonLabel, buttonTo, linkLabel, linkTo, accent }) {
  return (
    <div
      style={{
        ...styles.card,
        minWidth: 280,
        maxWidth: 380,
        flex: 1,
        transition: "transform 0.2s ease, border-color 0.2s ease",
        boxShadow: `0 20px 50px ${accent}15`,
      }}
      onMouseEnter={(event) => {
        event.currentTarget.style.transform = "translateY(-4px)";
      }}
      onMouseLeave={(event) => {
        event.currentTarget.style.transform = "translateY(0px)";
      }}
    >
      <div style={{ fontSize: 42 }}>{icon}</div>
      <div style={{ marginTop: 16, fontSize: 28, fontWeight: 700, fontFamily: '"Playfair Display", serif' }}>{title}</div>
      <div style={{ marginTop: 10, color: theme.muted, lineHeight: 1.7 }}>{subtitle}</div>
      <Link to={buttonTo} style={{ display: "block", marginTop: 22 }}>
        <button type="button" style={{ ...styles.primaryButton, width: "100%", background: accent }}>
          {buttonLabel}
        </button>
      </Link>
      <Link to={linkTo} style={{ display: "inline-block", marginTop: 16, color: theme.text }}>
        {linkLabel}
      </Link>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div
      style={{
        ...styles.page,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        backgroundImage:
          "linear-gradient(rgba(42,51,88,0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(42,51,88,0.2) 1px, transparent 1px)",
        backgroundSize: "32px 32px",
      }}
    >
      <div style={{ width: "100%", maxWidth: 1080, textAlign: "center" }}>
        <div style={{ fontFamily: '"Playfair Display", serif', fontSize: "clamp(42px, 6vw, 68px)", fontWeight: 700 }}>
          MediTrack AI
        </div>
        <div style={{ marginTop: 12, color: theme.muted, fontSize: 18 }}>
          AI-powered lifetime medical records via telemedicine
        </div>

        <div
          style={{
            marginTop: 44,
            display: "flex",
            gap: 24,
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          <RoleCard
            icon="🩺"
            title="I am a Doctor"
            subtitle="Manage patients, run AI consultations, view medical histories"
            buttonLabel="Doctor Login"
            buttonTo="/doctor/login"
            linkLabel="New here? Create account"
            linkTo="/doctor/signup"
            accent="linear-gradient(135deg, var(--accent), var(--accent2))"
          />
          <RoleCard
            icon="👤"
            title="I am a Patient"
            subtitle="View your medical history, medications, and AI health summaries"
            buttonLabel="Patient Login"
            buttonTo="/patient/login"
            linkLabel="New here? Create account"
            linkTo="/patient/signup"
            accent="linear-gradient(135deg, #26b9c8, #34d399)"
          />
        </div>

        <div style={{ marginTop: 28, color: theme.muted }}>
          Demo: Riya Sharma (patient) | Dr. Aisha Kapoor (doctor)
        </div>
      </div>
    </div>
  );
}
