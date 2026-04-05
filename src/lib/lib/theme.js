export const theme = {
  bg: "var(--bg)",
  surface: "var(--surface)",
  surface2: "var(--surface2)",
  border: "var(--border)",
  accent: "var(--accent)",
  accent2: "var(--accent2)",
  green: "var(--green)",
  amber: "var(--amber)",
  red: "var(--red)",
  text: "var(--text)",
  muted: "var(--muted)",
  card: "var(--card)",
};

export const styles = {
  page: {
    minHeight: "100vh",
    background: theme.bg,
    color: theme.text,
  },
  shell: {
    display: "grid",
    gridTemplateColumns: "260px 1fr",
    minHeight: "100vh",
  },
  main: {
    padding: "24px",
  },
  card: {
    background: theme.card,
    border: `1px solid ${theme.border}`,
    borderRadius: 24,
    padding: 24,
  },
  subtleCard: {
    background: theme.surface,
    border: `1px solid ${theme.border}`,
    borderRadius: 20,
    padding: 18,
  },
  input: {
    width: "100%",
    padding: "14px 16px",
    borderRadius: 14,
    border: `1px solid ${theme.border}`,
    background: theme.surface2,
    color: theme.text,
    outline: "none",
  },
  textarea: {
    width: "100%",
    minHeight: 130,
    padding: "14px 16px",
    borderRadius: 14,
    border: `1px solid ${theme.border}`,
    background: theme.surface2,
    color: theme.text,
    outline: "none",
    resize: "vertical",
  },
  button: {
    border: "none",
    borderRadius: 14,
    padding: "13px 18px",
    cursor: "pointer",
    fontWeight: 700,
  },
  primaryButton: {
    border: "none",
    borderRadius: 14,
    padding: "13px 18px",
    cursor: "pointer",
    fontWeight: 700,
    color: "#fff",
    background: "linear-gradient(135deg, var(--accent), var(--accent2))",
  },
  secondaryButton: {
    border: `1px solid ${theme.border}`,
    borderRadius: 14,
    padding: "13px 18px",
    cursor: "pointer",
    fontWeight: 700,
    color: theme.text,
    background: theme.surface2,
  },
};

export function pillStyle(color, bgAlpha = "18") {
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "6px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 600,
    border: `1px solid ${color}55`,
    color,
    background: `${color}${bgAlpha}`,
  };
}

export function badgeStyle(level) {
  if (level === "high") return pillStyle(theme.red);
  if (level === "moderate") return pillStyle(theme.amber);
  return pillStyle(theme.green);
}
