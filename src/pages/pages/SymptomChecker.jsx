import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { api, getErrorMessage } from "../lib/api";
import { getStoredAuth } from "../lib/auth";
import { badgeStyle, pillStyle, styles, theme } from "../lib/theme";

const CATEGORY_MAP = {
  General: ["fever", "fatigue", "weakness", "weight loss", "loss of appetite"],
  Respiratory: ["cough", "breathlessness", "chest pain", "wheezing", "sore throat", "runny nose"],
  Digestive: ["nausea", "vomiting", "diarrhea", "abdominal pain", "acidity", "bloating"],
  Skin: ["itching", "rash", "blisters", "jaundice", "pale skin", "yellow"],
  Pain: ["headache", "bodyache", "joint pain", "muscle pain", "back pain"],
  Other: ["dizziness", "blurred vision", "frequent urination", "chills", "sweating"],
};

function confidenceColor(value) {
  if (value > 70) return theme.red;
  if (value >= 40) return theme.amber;
  return theme.green;
}

function groupSymptoms(symptoms, search) {
  const filtered = symptoms.filter((symptom) => symptom.includes(search.toLowerCase()));
  const grouped = {};
  Object.entries(CATEGORY_MAP).forEach(([label, keywords]) => {
    grouped[label] = filtered.filter((symptom) => keywords.some((keyword) => symptom.includes(keyword)));
  });
  grouped.Other = [...new Set([...(grouped.Other || []), ...filtered.filter((symptom) => !Object.values(CATEGORY_MAP).some((keywords) => keywords.some((keyword) => symptom.includes(keyword))))])];
  return grouped;
}

export default function SymptomChecker() {
  const navigate = useNavigate();
  const auth = getStoredAuth();
  const role = auth?.role === "doctor" ? "doctor" : "patient";
  const [activeKey, setActiveKey] = useState("symptom-checker");
  const [symptoms, setSymptoms] = useState([]);
  const [selected, setSelected] = useState([]);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState([]);
  const [disclaimer, setDisclaimer] = useState("");
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSymptoms() {
      try {
        const response = await api.get("/all-symptoms");
        setSymptoms(response.data.symptoms || []);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Could not load symptom list."));
      } finally {
        setLoading(false);
      }
    }

    loadSymptoms();
  }, []);

  const groupedSymptoms = useMemo(() => groupSymptoms(symptoms, search), [search, symptoms]);

  function handleSidebar(action) {
    setActiveKey(action);
    if (action === "dashboard") navigate("/doctor/dashboard");
    if (action === "consult" && auth?.role === "doctor") navigate("/doctor/dashboard");
    if (action === "health" || action === "visits" || action === "medications") navigate("/patient/portal");
    if (action === "report") navigate("/patient/portal");
    if (action === "symptom-checker") navigate("/symptom-checker");
  }

  function toggleSymptom(symptom) {
    setSelected((current) => (current.includes(symptom) ? current.filter((item) => item !== symptom) : [...current, symptom]));
  }

  async function checkSymptoms() {
    setChecking(true);
    setError("");
    try {
      const response = await api.post("/symptom-checker", { symptoms: selected });
      setResults(response.data.results || []);
      setDisclaimer(response.data.disclaimer || "");
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not run symptom checker."));
    } finally {
      setChecking(false);
    }
  }

  function resetChecker() {
    setSelected([]);
    setResults([]);
    setDisclaimer("");
    setSearch("");
  }

  return (
    <div style={styles.shell}>
      <Sidebar role={role} activeKey={activeKey} onSelect={handleSidebar} />
      <main style={styles.main}>
        <div style={{ maxWidth: 1240, margin: "0 auto", display: "grid", gap: 24 }}>
          <section style={styles.card}>
            <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 36 }}>Symptom Checker</div>
            <div style={{ color: theme.muted, marginTop: 10 }}>Select your symptoms to find possible conditions</div>
            <div style={{ ...styles.subtleCard, marginTop: 18, background: "rgba(251,191,36,0.08)", color: theme.amber }}>
              This tool is for information only. Not a substitute for professional medical advice.
            </div>
          </section>

          <section style={styles.card}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <div style={{ fontWeight: 700 }}>{selected.length} symptoms selected</div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <input
                  style={{ ...styles.input, minWidth: 280 }}
                  placeholder="Search symptoms..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
                <button type="button" style={styles.secondaryButton} onClick={() => setSelected([])}>
                  Clear all
                </button>
              </div>
            </div>

            {loading ? (
              <div style={{ color: theme.muted, marginTop: 18 }}>Loading symptoms...</div>
            ) : (
              <div style={{ display: "grid", gap: 18, marginTop: 22 }}>
                {Object.entries(groupedSymptoms).map(([category, items]) => (
                  <div key={category} style={styles.subtleCard}>
                    <div style={{ fontWeight: 700, marginBottom: 12 }}>{category}</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                      {items.length ? (
                        items.map((symptom) => (
                          <button
                            key={symptom}
                            type="button"
                            onClick={() => toggleSymptom(symptom)}
                            style={{
                              ...pillStyle(selected.includes(symptom) ? theme.accent : theme.muted),
                              background: selected.includes(symptom) ? "rgba(79,142,247,0.18)" : theme.surface2,
                              color: selected.includes(symptom) ? theme.accent : theme.text,
                              cursor: "pointer",
                            }}
                          >
                            {symptom}
                          </button>
                        ))
                      ) : (
                        <div style={{ color: theme.muted }}>No symptoms in this category for the current search.</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {error ? <div style={{ color: theme.red, marginTop: 16 }}>{error}</div> : null}

            <div style={{ display: "flex", gap: 12, marginTop: 20, flexWrap: "wrap" }}>
              <button type="button" style={styles.primaryButton} onClick={checkSymptoms} disabled={checking || !selected.length}>
                {checking ? "Checking Symptoms..." : "Check Symptoms"}
              </button>
              <button type="button" style={styles.secondaryButton} onClick={resetChecker}>
                Check again
              </button>
            </div>
          </section>

          {results.length ? (
            <section style={styles.card}>
              <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 28 }}>Possible Matches</div>
              <div style={{ display: "grid", gap: 16, marginTop: 20 }}>
                {results.map((item) => {
                  const color = confidenceColor(item.confidence);
                  return (
                    <div key={item.disease} style={styles.subtleCard}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                        <div style={{ fontSize: 24, fontWeight: 700 }}>{item.disease}</div>
                        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                          <span style={badgeStyle(item.urgency === "high" ? "high" : item.urgency === "medium" ? "moderate" : "low")}>
                            {item.urgency.toUpperCase()}
                          </span>
                          <span style={{ color, fontWeight: 700 }}>{item.confidence}% match</span>
                        </div>
                      </div>

                      <div style={{ height: 10, background: theme.surface2, borderRadius: 999, marginTop: 14 }}>
                        <div style={{ height: 10, width: `${item.confidence}%`, background: color, borderRadius: 999 }} />
                      </div>

                      {item.urgency === "high" ? (
                        <div style={{ ...styles.subtleCard, marginTop: 14, background: "rgba(248,113,113,0.08)", color: theme.red }}>
                          See a doctor immediately
                        </div>
                      ) : null}

                      <div style={{ marginTop: 16 }}>
                        <div style={{ fontWeight: 700, marginBottom: 8 }}>Matched symptoms</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                          {item.matched_symptoms.map((symptom) => (
                            <span key={`${item.disease}-${symptom}`} style={pillStyle(theme.accent)}>
                              {symptom}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div style={{ marginTop: 16 }}>
                        <div style={{ fontWeight: 700, marginBottom: 8 }}>Possible medications</div>
                        <div style={{ color: theme.muted, lineHeight: 1.7 }}>
                          {item.medications.map((medication) => (
                            <div key={`${item.disease}-${medication}`}>{medication}</div>
                          ))}
                        </div>
                        <div style={{ color: theme.amber, marginTop: 8 }}>Consult doctor before taking any medicine.</div>
                      </div>

                      <div style={{ marginTop: 16 }}>
                        <div style={{ fontWeight: 700, marginBottom: 8 }}>What to do</div>
                        <div style={{ color: theme.muted, lineHeight: 1.7 }}>{item.advice}</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{ ...styles.subtleCard, marginTop: 20, borderColor: `${theme.amber}66`, background: "rgba(251,191,36,0.08)", color: theme.amber }}>
                {disclaimer || "IMPORTANT: This symptom checker uses pattern matching only. It cannot replace clinical examination or laboratory tests. Always visit a qualified doctor for proper diagnosis and treatment."}
              </div>
            </section>
          ) : null}
        </div>
      </main>
    </div>
  );
}
