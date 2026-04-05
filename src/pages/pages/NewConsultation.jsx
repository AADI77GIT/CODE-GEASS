import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { api, formatDate, getErrorMessage } from "../lib/api";
import { pillStyle, styles, theme } from "../lib/theme";

function shouldShowRetry(aiSummary) {
  if (!aiSummary) return false;
  const steps = aiSummary.pipeline_steps || [];
  const stepText = steps.map((step) => `${step.name || ""} ${step.message || ""}`.toLowerCase()).join(" ");
  return (
    !steps.length ||
    stepText.includes("api error") ||
    stepText.includes("json parse failed") ||
    stepText.includes("failed insufficient input") ||
    String(aiSummary.diagnosis_impression || "").toLowerCase().includes("ai unavailable") ||
    String(aiSummary.cumulative_patient_summary || "").toLowerCase().includes("pending")
  );
}

export default function NewConsultation() {
  const navigate = useNavigate();
  const { patientId } = useParams();
  const [activeKey, setActiveKey] = useState("consult");
  const [patient, setPatient] = useState(null);
  const [notes, setNotes] = useState("");
  const [metrics, setMetrics] = useState({
    systolic_bp: "",
    diastolic_bp: "",
    heart_rate: "",
    temperature_c: "",
    oxygen_saturation: "",
    glucose_level: "",
  });
  const [result, setResult] = useState(null);
  const [savedConsultationId, setSavedConsultationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [error, setError] = useState("");
  const [recording, setRecording] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    async function loadPatient() {
      try {
        const response = await api.get(`/patients/${patientId}`);
        setPatient(response.data);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Could not load patient."));
      }
    }

    loadPatient();
  }, [patientId]);

  const pipelineSteps = useMemo(() => result?.ai_summary?.pipeline_steps || [], [result]);

  function handleSidebar(action) {
    setActiveKey(action);
    if (action === "dashboard" || action === "patients" || action === "insights") {
      navigate("/doctor/dashboard");
      return;
    }
    if (action === "symptom-checker") {
      navigate("/symptom-checker");
    }
  }

  function speechSupported() {
    return typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  function toggleRecording() {
    if (!speechSupported()) return;

    if (recording && recognitionRef.current) {
      recognitionRef.current.stop();
      setRecording(false);
      return;
    }

    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Recognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-IN";
    recognition.onresult = (event) => {
      let transcript = "";
      for (let index = 0; index < event.results.length; index += 1) {
        transcript += event.results[index][0].transcript;
      }
      setNotes(transcript);
    };
    recognition.onend = () => setRecording(false);
    recognition.start();
    recognitionRef.current = recognition;
    setRecording(true);
  }

  async function submit() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await api.post("/consultations", {
        patient_id: Number(patientId),
        notes,
        clinical_metrics: {
          systolic_bp: metrics.systolic_bp ? Number(metrics.systolic_bp) : null,
          diastolic_bp: metrics.diastolic_bp ? Number(metrics.diastolic_bp) : null,
          heart_rate: metrics.heart_rate ? Number(metrics.heart_rate) : null,
          temperature_c: metrics.temperature_c ? Number(metrics.temperature_c) : null,
          oxygen_saturation: metrics.oxygen_saturation ? Number(metrics.oxygen_saturation) : null,
          glucose_level: metrics.glucose_level ? Number(metrics.glucose_level) : null,
        },
      });
      setSavedConsultationId(response.data.consultation_id);
      setResult(response.data);
      console.log("Consultation created", response.data.consultation_id);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not save consultation."));
    } finally {
      setLoading(false);
    }
  }

  async function retryAiAnalysis() {
    if (!savedConsultationId) return;
    setRetrying(true);
    setError("");
    try {
      const response = await api.post(`/retry-ai/${savedConsultationId}`);
      const { id, ...aiSummary } = response.data;
      setResult((previous) => ({
        ...(previous || {}),
        consultation_id: id || savedConsultationId,
        patient_id: Number(patientId),
        date: previous?.date || new Date().toISOString(),
        ai_summary: aiSummary,
      }));
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not retry AI analysis."));
    } finally {
      setRetrying(false);
    }
  }

  return (
    <div style={styles.shell}>
      <Sidebar role="doctor" activeKey={activeKey} onSelect={handleSidebar} />
      <main style={styles.main}>
        <div style={{ maxWidth: 1240, margin: "0 auto", display: "grid", gap: 24 }}>
          <section style={styles.card}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 34 }}>New Consultation</div>
                <div style={{ color: theme.muted, marginTop: 8 }}>
                  {patient ? `${patient.name} | ${patient.age} years | ${patient.gender}` : "Loading patient..."}
                </div>
              </div>
              <button type="button" style={styles.secondaryButton} onClick={() => navigate("/doctor/dashboard")}>
                Back to Dashboard
              </button>
            </div>
          </section>

          <section style={{ ...styles.card, display: "grid", gap: 18 }}>
            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
              {[
                ["systolic_bp", "Systolic BP"],
                ["diastolic_bp", "Diastolic BP"],
                ["heart_rate", "Heart Rate"],
                ["temperature_c", "Temperature"],
                ["oxygen_saturation", "Oxygen Sat"],
                ["glucose_level", "Glucose"],
              ].map(([key, label]) => (
                <input
                  key={key}
                  style={styles.input}
                  placeholder={label}
                  value={metrics[key]}
                  onChange={(event) => setMetrics({ ...metrics, [key]: event.target.value })}
                />
              ))}
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 8 }}>
                <div style={{ fontWeight: 700 }}>Doctor Notes</div>
                {speechSupported() ? (
                  <button
                    type="button"
                    onClick={toggleRecording}
                    style={{
                      ...styles.secondaryButton,
                      color: recording ? theme.red : theme.text,
                      boxShadow: recording ? "0 0 0 8px rgba(248,113,113,0.12)" : "none",
                    }}
                  >
                    {recording ? "Recording..." : "Mic Input"}
                  </button>
                ) : null}
              </div>
              <textarea
                style={{ ...styles.textarea, minHeight: 200 }}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Enter full consultation notes here — include symptoms, vitals, medications, tests ordered..."
              />
            </div>

            {error ? <div style={{ color: theme.red }}>{error}</div> : null}

            <button
              type="button"
              style={{ ...styles.primaryButton, width: "100%", fontSize: 14 }}
              onClick={submit}
              disabled={loading}
            >
              {loading ? "Running AI Analysis & Saving..." : "Run AI Analysis & Save"}
            </button>
          </section>

          {result ? (
            <section style={{ display: "grid", gap: 24 }}>
              <div
                style={{
                  ...styles.subtleCard,
                  borderColor: `${theme.green}66`,
                  background: "rgba(52,211,153,0.08)",
                  color: theme.green,
                  fontWeight: 700,
                }}
              >
                Analysis complete - consultation saved
              </div>

              <div style={{ display: "grid", gap: 24, gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)" }}>
                <div style={styles.card}>
                  <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 26 }}>AI Extracted Data</div>
                  <div style={{ display: "grid", gap: 16, marginTop: 18 }}>
                    <div style={styles.subtleCard}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>Symptoms detected</div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        {result.ai_summary.symptoms?.length ? (
                          result.ai_summary.symptoms.map((item) => (
                            <span key={item} style={pillStyle(theme.red)}>
                              {item}
                            </span>
                          ))
                        ) : (
                          <div style={{ color: theme.muted }}>No symptoms detected</div>
                        )}
                      </div>
                    </div>

                    <div style={styles.subtleCard}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>Medications prescribed</div>
                      {result.ai_summary.medications_prescribed?.length ? (
                        <div style={{ display: "grid", gap: 8 }}>
                          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: 10, color: theme.muted, fontSize: 12 }}>
                            <div>Medication</div>
                            <div>Dosage</div>
                            <div>Duration</div>
                          </div>
                          {result.ai_summary.medications_prescribed.map((item) => (
                            <div key={`${item.name}-${item.dosage}`} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: 10 }}>
                              <div>{item.name}</div>
                              <div>{item.dosage}</div>
                              <div>{item.duration}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ color: theme.muted }}>None prescribed this visit</div>
                      )}
                    </div>

                    <div style={styles.subtleCard}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>Tests ordered</div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        {result.ai_summary.tests_ordered?.length ? (
                          result.ai_summary.tests_ordered.map((item) => (
                            <span key={item} style={pillStyle(theme.accent2)}>
                              {item}
                            </span>
                          ))
                        ) : (
                          <div style={{ color: theme.muted }}>No tests ordered</div>
                        )}
                      </div>
                    </div>

                    <div style={styles.subtleCard}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>ML Model Prediction</div>
                      {result.ai_summary.ml_prediction?.predictions?.length ? (
                        <div style={{ display: "grid", gap: 10 }}>
                          {result.ai_summary.ml_prediction.predictions.slice(0, 3).map((item) => (
                            <div key={`${item.disease}-${item.source || "ml"}`} style={{ color: theme.muted }}>
                              <span style={{ color: theme.text, fontWeight: 700 }}>{item.disease}</span> — {item.confidence}% {item.source ? `(${item.source})` : ""}
                            </div>
                          ))}
                        </div>
                      ) : result.ai_summary.ml_prediction?.prediction ? (
                        <div style={{ color: theme.muted }}>
                          <div style={{ color: theme.text, fontWeight: 700 }}>{result.ai_summary.ml_prediction.prediction}</div>
                          <div style={{ marginTop: 6 }}>
                            Confidence: {result.ai_summary.ml_prediction.confidence != null ? `${Math.round(result.ai_summary.ml_prediction.confidence * 100)}%` : "N/A"}
                          </div>
                        </div>
                      ) : (
                        <div style={{ color: theme.muted }}>ML model not available</div>
                      )}
                    </div>
                  </div>
                </div>

                <div style={styles.card}>
                  <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 26 }}>AI Generated Summary</div>
                  <div style={{ display: "grid", gap: 16, marginTop: 18 }}>
                    <div style={styles.subtleCard}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>Visit summary</div>
                      <div style={{ color: theme.muted, lineHeight: 1.7 }}>{result.ai_summary.visit_summary || "Consultation recorded."}</div>
                    </div>

                    <div style={{ ...styles.subtleCard, background: "rgba(251,191,36,0.08)" }}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>Recurring patterns found</div>
                      {result.ai_summary.flags?.length ? (
                        result.ai_summary.flags.map((item) => (
                          <div key={item} style={{ marginTop: 8 }}>
                            ⚠ {item}
                          </div>
                        ))
                      ) : (
                        <div style={{ color: theme.muted }}>None detected</div>
                      )}
                    </div>

                    <div style={{ ...styles.subtleCard, background: "rgba(38,185,200,0.08)" }}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>AI Suggestions based on history</div>
                      {result.ai_summary.context_suggestions?.length ? (
                        result.ai_summary.context_suggestions.map((item) => (
                          <div key={item} style={{ marginTop: 8 }}>
                            → {item}
                          </div>
                        ))
                      ) : (
                        <div style={{ color: theme.muted }}>No history-based suggestions yet</div>
                      )}
                    </div>

                    <div style={styles.subtleCard}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>AI memory across all visits</div>
                      <div style={{ color: theme.muted, lineHeight: 1.7 }}>
                        {result.ai_summary.cumulative_patient_summary || "No cumulative summary available yet."}
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", color: theme.green }}>
                      {pipelineSteps.length ? (
                        pipelineSteps.map((step, index) => (
                          <div key={`${step.name || "step"}-${index}`}>Done: {step.name}: {step.message}</div>
                        ))
                      ) : (
                        <div style={{ color: theme.muted }}>No pipeline status available</div>
                      )}
                    </div>

                    {shouldShowRetry(result.ai_summary) && savedConsultationId ? (
                      <button type="button" style={styles.secondaryButton} onClick={retryAiAnalysis} disabled={retrying}>
                        {retrying ? "Retrying AI..." : "Retry AI Analysis"}
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            </section>
          ) : null}

          <section style={{ ...styles.subtleCard, maxWidth: 1240, margin: "0 auto" }}>
            <div style={{ color: theme.muted }}>Patient: {patient?.name || "Loading"} | Last updated: {formatDate(new Date())}</div>
          </section>
        </div>
      </main>
    </div>
  );
}
