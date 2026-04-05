import { Link } from "react-router-dom";
import { styles, theme } from "../../lib/theme";

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div style={{ ...styles.page, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        <Link to="/" style={{ color: theme.muted }}>
          ← Choose role
        </Link>
        <div style={{ ...styles.card, marginTop: 18 }}>
          <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 36, fontWeight: 700 }}>MediTrack AI</div>
          <div style={{ marginTop: 8, fontSize: 28, fontWeight: 700 }}>{title}</div>
          <div style={{ marginTop: 8, color: theme.muted, lineHeight: 1.6 }}>{subtitle}</div>
          <div style={{ display: "grid", gap: 14, marginTop: 24 }}>{children}</div>
          {footer ? <div style={{ marginTop: 18, color: theme.muted }}>{footer}</div> : null}
        </div>
      </div>
    </div>
  );
}
