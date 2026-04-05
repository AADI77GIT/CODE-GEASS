import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { api, formatDate, getErrorMessage, parseConsultation } from "../lib/api";
import { getStoredAuth } from "../lib/auth";
import { styles, theme, pillStyle } from "../lib/theme";

function uniqueMedications(consultations) {
  const map = new Map();
  consultations.forEach((consultation) => {
    consultation.parsedSummary.medications_prescribed.forEach((medication) => {
      const key = `${medication.name}-${medication.dosage}-${medication.duration}`;
      if (!map.has(key)) {
        map.set(key, { ...medication, prescribedOn: consultation.date });
      }
    });
  });
  return [...map.values()];
}

export default function PatientPortal() {
  const navigate = useNavigate();
  const auth = getStoredAuth();
  const [activeKey, setActiveKey] = useState("health");
  const [patient, setPatient] = useState(null);
  const [consultations, setConsultations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    async function loadPortal() {
      setLoading(true);
      setError("");
      try {
        const patientId = auth?.id || 1;
        const [patientResponse, consultationsResponse, summaryResponse] = await Promise.all([
          api.get(`/patients/${patientId}`),
          api.get(`/consultations/${patientId}`),
          api.get(`/ai-summary/${patientId}`),
        ]);
        const parsed = consultationsResponse.data.map(parseConsultation);
        setPatient(patientResponse.data);
        setConsultations(parsed);
        setSummary(summaryResponse.data);
        setExpandedId(parsed[0]?.id || null);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Could not load patient portal."));
      } finally {
        setLoading(false);
      }
    }

    loadPortal();
  }, [auth?.id]);

  const activeMeds = useMemo(() => uniqueMedications(consultations), [consultations]);

  async function downloadReport() {
    try {
      setDownloading(true);
      const patientId = auth?.id || 1;
      const response = await api.get(`/report/${patientId}`, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `meditrack_${patientId}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Report will include all visits + AI summaries once backend PDF is ready."));
    } finally {
      setDownloading(false);
    }
  }

  function handleSidebar(action) {
    setActiveKey(action);
    if (action === "report") {
      downloadReport();
      return;
    }
    if (action === "symptom-checker") {
      navigate("/symptom-checker");
    }
  }

  if (loading) {
    return <div style={{ ...styles.page, display: "grid", placeItems: "center" }}>Loading patient portal...</div>;
  }

  return (
    <div style={styles.shell}>
      <Sidebar role="patient" activeKey={activeKey} onSelect={handleSidebar} />
      <main style={styles.main}>
        <div style={{ maxWidth: 1180, margin: "0 auto", display: "grid", gap: 24 }}>
          <section style={styles.card}>
            <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 36 }}>{patient?.name}</div>
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", color: theme.muted, marginTop: 10 }}>
              <span>{patient?.age} years</span>
              <span>{patient?.gender}</span>
              <span>{patient?.blood_group || "Blood group N/A"}</span>
              <span>{patient?.phone}</span>
            </div>
          </section>

          {error ? <div style={{ color: theme.red }}>{error}</div> : null}

          <section style={{ ...styles.card, borderLeft: `6px solid ${theme.accent}` }}>
            <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 26 }}>My Medical History</div>
            <div style={{ color: theme.muted, lineHeight: 1.8, marginTop: 16 }}>
              {summary?.cumulative_patient_summary || "No cumulative history available."}
            </div>
            {summary?.flags?.length ? (
              <div style={{ marginTop: 16, color: theme.amber }}>
                {summary.flags.map((item) => (
                  <div key={item} style={{ marginTop: 8 }}>
                    ⚠ {item}
                  </div>
                ))}
              </div>
            ) : null}
          </section>

          <section style={styles.card}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 26 }}>My Visits</div>
              <button type="button" style={styles.primaryButton} onClick={downloadReport} disabled={downloading}>
                {downloading ? "⏳ Generating PDF..." : "📄 Download My Report"}
              </button>
            </div>
            <div style={{ display: "grid", gap: 16, marginTop: 18 }}>
              {consultations.map((consultation, index) => {
                const open = expandedId === consultation.id;
                const visitSummary = consultation.parsedSummary;
                return (
                  <div key={consultation.id} style={styles.subtleCard}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                      <div>
                        <div style={{ fontSize: 20, fontWeight: 700 }}>
                          Visit {consultations.length - index} | {formatDate(consultation.date)}
                        </div>
                        <div style={{ marginTop: 8, fontWeight: 700 }}>{visitSummary.diagnosis_impression || "None detected"}</div>
                      </div>
                      <button type="button" style={styles.secondaryButton} onClick={() => setExpandedId(open ? null : consultation.id)}>
                        {open ? "Hide AI Analysis" : "View AI Analysis"}
                      </button>
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
                      {visitSummary.symptoms.map((item) => <span key={`${consultation.id}-s-${item}`} style={pillStyle(theme.red)}>{item}</span>)}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
                      {visitSummary.medications_prescribed.map((item) => (
                        <span key={`${consultation.id}-m-${item.name}`} style={pillStyle(theme.green)}>
                          {item.name} {item.dosage} {item.duration}
                        </span>
                      ))}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
                      {visitSummary.tests_ordered.map((item) => <span key={`${consultation.id}-t-${item}`} style={pillStyle(theme.accent2)}>{item}</span>)}
                    </div>
                    {open ? (
                      <div style={{ marginTop: 16, color: theme.muted, lineHeight: 1.8 }}>
                        {visitSummary.visit_summary || "No AI visit summary available."}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </section>

          <section style={styles.card}>
            <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 26 }}>Active Medications</div>
            <div style={{ display: "grid", gap: 14, marginTop: 18 }}>
              {activeMeds.length ? activeMeds.map((item) => (
                <div key={`${item.name}-${item.dosage}`} style={styles.subtleCard}>
                  {item.name} — {item.dosage} — {item.duration} — Prescribed: {formatDate(item.prescribedOn)}
                </div>
              )) : <div style={{ color: theme.muted }}>None detected</div>}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
