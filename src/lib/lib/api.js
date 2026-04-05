import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export function parseConsultation(consultation) {
  try {
    return { ...consultation, parsedSummary: JSON.parse(consultation.ai_summary) };
  } catch (error) {
    return {
      ...consultation,
      parsedSummary: {
        symptoms: [],
        diagnosis_impression: "AI summary unavailable",
        medications_prescribed: [],
        tests_ordered: [],
        visit_summary: consultation.raw_notes || "No notes recorded.",
        flags: [],
        cumulative_patient_summary: "No cumulative history available yet.",
        context_suggestions: [],
        pipeline_steps: [],
        risk_level: "low",
        ml_prediction: null,
      },
    };
  }
}

export function getErrorMessage(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback;
}

export function formatDate(value) {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function splitComma(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
