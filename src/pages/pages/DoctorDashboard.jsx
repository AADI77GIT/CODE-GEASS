import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { api, formatDate, getErrorMessage, parseConsultation } from "../lib/api";
import { styles, theme, badgeStyle, pillStyle } from "../lib/theme";

function frequencyMap(consultations) {
  const map = {};
  consultations.forEach((consultation) => {
    consultation.parsedSummary.symptoms.forEach((symptom) => {
      map[symptom] = (map[symptom] || 0) + 1;
    });
  });
  return Object.entries(map)
    .map(([label, count]) => ({ label, count }))
    .sort((left, right) => right.count - left.count);
}

function riskLevelFromFlags(flags) {
  if (flags >= 3) return "high";
  if (flags >= 1) return "moderate";
  return "low";
}

function EmptyText({ text = "None detected" }) {
  return <div style={{ color: theme.muted }}>{text}</div>;
}

export default function DoctorDashboard() {
  const navigate = useNavigate();
  const [activeKey, setActiveKey] = useState("dashboard");
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [patient, setPatient] = useState(null);
  const [consultations, setConsultations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedVisitId, setSelectedVisitId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadPatients() {
      try {
        const response = await api.get("/patients");
        setPatients(response.data);
        if (response.data.length) {
          setSelectedPatientId(String(response.data[0].id));
        }
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Could not load patients."));
      }
    }

    loadPatients();
  }, []);

  useEffect(() => {
    if (!selectedPatientId) return;

    async function loadBundle() {
      setLoading(true);
      setError("");
      try {
        const [patientResponse, consultationsResponse, summaryResponse] = await Promise.all([
          api.get(`/patients/${selectedPatientId}`),
          api.get(`/consultations/${selectedPatientId}`),
          api.get(`/ai-summary/${selectedPatientId}`),
        ]);
        const parsed = consultationsResponse.data.map(parseConsultation);
        setPatient(patientResponse.data);
        setConsultations(parsed);
        setSummary(summaryResponse.data);
        setSelectedVisitId(parsed[0]?.id || null);
        console.log("Dashboard patient loaded", patientResponse.data.name);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Could not load patient dashboard."));
      } finally {
        setLoading(false);
      }
    }

    loadBundle();
  }, [selectedPatientId]);

  const selectedVisit = useMemo(
    () => consultations.find((item) => item.id === selectedVisitId) || consultations[0] || null,
    [consultations, selectedVisitId],
  );
  const trends = useMemo(() => frequencyMap(consultations), [consultations]);
  const latestSummary = selectedVisit?.parsedSummary || summary;
  const latestFlagsCount = summary?.flags?.length || consultations[0]?.parsedSummary?.flags?.length || 0;
  const riskLevel = riskLevelFromFlags(latestFlagsCount);
  const aiActive = Boolean(
    summary?.cumulative_patient_summary ||
      summary?.visit_summary ||
      summary?.symptoms?.length ||
      summary?.medications_prescribed?.length ||
      summary?.tests_ordered?.length,
  );

  function handleSidebar(action) {
    setActiveKey(action);
    if (action === "consult" && patient) {
      navigate(`/consult/${patient.id}`);
      return;
    }
    if (action === "symptom-checker") {
      navigate("/symptom-checker");
    }
  }

  if (loading) {
    return <div style={{ ...styles.page, display: "grid", placeItems: "center" }}>Loading doctor dashboard...</div>;
  }

  return (
    <div style={styles.shell}>
      <Sidebar role="doctor" activeKey={activeKey} onSelect={handleSidebar} />
      <main style={styles.main}>
        <div style={{ maxWidth: 1280, margin: "0 auto", display: "grid", gap: 24 }}>
          <section style={styles.card}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
              <div>
                <div style={{ color: theme.muted, textTransform: "uppercase", letterSpacing: 1.5, fontSize: 12 }}>Patient Overview</div>
                <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 38, marginTop: 10 }}>{patient?.name}</div>
                <div style={{ color: theme.muted, marginTop: 8 }}>
                  {patient?.age} years | {patient?.gender} | {patient?.blood_group || "Blood group N/A"} | {patient?.phone}
                </div>
              </div>
              <div style={{ display: "flex", gap: 10, alignItems: "flex-start", flexWrap: "wrap" }}>
                <span style={badgeStyle(riskLevel)}>{riskLevel[0].toUpperCase() + riskLevel.slice(1)} Risk</span>
                <span style={aiActive ? badgeStyle("low") : badgeStyle("moderate")}>
                  {aiActive ? "AI Active" : "AI Data Pending"}
                </span>
              </div>
            </div>

            <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", marginTop: 22 }}>
              <div style={styles.subtleCard}>
                <div style={{ color: theme.muted, fontSize: 13 }}>Total Visits</div>
                <div style={{ fontSize: 30, fontWeight: 700, marginTop: 8 }}>{consultations.length}</div>
              </div>
              <div style={styles.subtleCard}>
                <div style={{ color: theme.muted, fontSize: 13 }}>Active Medications</div>
                <div style={{ fontSize: 30, fontWeight: 700, marginTop: 8 }}>{summary?.medications_prescribed?.length || 0}</div>
              </div>
              <div style={styles.subtleCard}>
                <div style={{ color: theme.muted, fontSize: 13 }}>Recurring Flags</div>
                <div style={{ fontSize: 30, fontWeight: 700, marginTop: 8 }}>{latestFlagsCount}</div>
              </div>
              <div style={styles.subtleCard}>
                <div style={{ color: theme.muted, fontSize: 13 }}>Patient Selector</div>
                <select
                  style={{ ...styles.input, marginTop: 8 }}
                  value={selectedPatientId}
                  onChange={(event) => setSelectedPatientId(event.target.value)}
                >
                  {patients.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {error ? <div style={{ marginTop: 18, color: theme.red }}>{error}</div> : null}
          </section>

          <section style={{ display: "grid", gap: 24, gridTemplateColumns: "minmax(0, 1.1fr) minmax(0, 0.9fr)" }}>
            <div style={styles.card}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 28 }}>Visit Timeline</div>
                  <div style={{ color: theme.muted, marginTop: 8 }}>Click a visit to inspect all AI output.</div>
                </div>
                <button type="button" style={styles.primaryButton} onClick={() => navigate(`/consult/${selectedPatientId}`)}>
                  + New Consultation
                </button>
              </div>

              <div style={{ display: "grid", gap: 16, marginTop: 20 }}>
                {consultations.map((consultation, index) => (
                  <button
                    key={consultation.id}
                    type="button"
                    onClick={() => setSelectedVisitId(consultation.id)}
                    style={{
                      ...styles.subtleCard,
                      textAlign: "left",
                      background: selectedVisitId === consultation.id ? theme.surface2 : theme.surface,
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                      <div style={{ fontSize: 20, fontWeight: 700 }}>
                        Visit {consultations.length - index} | {formatDate(consultation.date)}
                      </div>
                      <div style={{ color: theme.muted }}>{consultation.parsedSummary.diagnosis_impression || "No diagnosis impression"}</div>
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
                      {consultation.parsedSummary.symptoms.length ? consultation.parsedSummary.symptoms.map((item) => (
                        <span key={`${consultation.id}-${item}`} style={pillStyle(theme.red)}>
                          {item}
                        </span>
                      )) : <EmptyText />}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
                      {consultation.parsedSummary.medications_prescribed.map((item) => (
                        <span key={`${consultation.id}-${item.name}`} style={pillStyle(theme.green)}>
                          {item.name}
                        </span>
                      ))}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
                      {consultation.parsedSummary.tests_ordered.map((item) => (
                        <span key={`${consultation.id}-${item}`} style={pillStyle(theme.accent2)}>
                          {item}
                        </span>
                      ))}
                    </div>
                    {consultation.parsedSummary.flags[0] ? (
                      <div
                        style={{
                          marginTop: 14,
                          padding: "10px 12px",
                          borderRadius: 12,
                          background: "rgba(251,191,36,0.08)",
                          color: theme.amber,
                        }}
                      >
                        ⚠ Pattern: {consultation.parsedSummary.flags[0]}
                      </div>
                    ) : null}
                  </button>
                ))}
              </div>
            </div>

            <div style={styles.card}>
              <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 28 }}>AI Clinical Panel</div>
              <div style={{ display: "grid", gap: 16, marginTop: 20 }}>
                <div style={styles.subtleCard}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>AI Cumulative Summary</div>
                  <div style={{ color: theme.muted, lineHeight: 1.7 }}>
                    {latestSummary?.cumulative_patient_summary || "None detected"}
                  </div>
                </div>
                <div style={styles.subtleCard}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>This Visit — AI Summary</div>
                  <div style={{ color: theme.muted, lineHeight: 1.7 }}>{latestSummary?.visit_summary || "None detected"}</div>
                </div>
                <div style={styles.subtleCard}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Extracted Entities</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {latestSummary?.symptoms?.map((item) => (
                      <span key={`sym-${item}`} style={pillStyle(theme.red)}>
                        {item}
                      </span>
                    ))}
                    {latestSummary?.medications_prescribed?.map((item) => (
                      <span key={`med-${item.name}`} style={pillStyle(theme.green)}>
                        {item.name}
                      </span>
                    ))}
                    {latestSummary?.tests_ordered?.map((item) => (
                      <span key={`test-${item}`} style={pillStyle(theme.accent2)}>
                        {item}
                      </span>
                    ))}
                    {!latestSummary?.symptoms?.length &&
                    !latestSummary?.medications_prescribed?.length &&
                    !latestSummary?.tests_ordered?.length ? (
                      <EmptyText />
                    ) : null}
                  </div>
                </div>
                <div style={{ ...styles.subtleCard, background: "rgba(251,191,36,0.08)" }}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Recurring Flags</div>
                  {latestSummary?.flags?.length ? latestSummary.flags.map((item) => <div key={item} style={{ marginTop: 8 }}>⚠ {item}</div>) : <EmptyText />}
                </div>
                <div style={{ ...styles.subtleCard, background: "rgba(38,185,200,0.08)" }}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>AI Suggestions</div>
                  {latestSummary?.context_suggestions?.length ? latestSummary.context_suggestions.map((item) => <div key={item} style={{ marginTop: 8 }}>→ {item}</div>) : <EmptyText />}
                </div>
                <div style={styles.subtleCard}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Symptom Frequency</div>
                  {trends.length ? trends.map((item) => (
                    <div key={item.label} style={{ marginTop: 10 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", color: theme.muted, marginBottom: 6 }}>
                        <span>{item.label}</span>
                        <span>{item.count}x</span>
                      </div>
                      <div style={{ height: 8, background: theme.surface2, borderRadius: 999 }}>
                        <div style={{ height: 8, width: `${Math.min(100, item.count * 22)}%`, background: theme.accent, borderRadius: 999 }} />
                      </div>
                    </div>
                  )) : <EmptyText />}
                </div>
                <div style={styles.subtleCard}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>ML Condition Prediction</div>
                  {latestSummary?.ml_prediction ? (
                    <div style={{ color: theme.muted }}>
                      <div style={{ color: theme.text, fontWeight: 700 }}>{latestSummary.ml_prediction.prediction}</div>
                      <div style={{ marginTop: 6 }}>
                        Confidence: {latestSummary.ml_prediction.confidence != null ? `${Math.round(latestSummary.ml_prediction.confidence * 100)}%` : "N/A"}
                      </div>
                    </div>
                  ) : (
                    <EmptyText />
                  )}
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
