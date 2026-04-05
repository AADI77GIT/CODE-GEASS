import json
import os
from datetime import date
from typing import Iterable

import google.generativeai as genai

from app.models import Consultation
from app.schemas import AISummary, Medication, PipelineStep

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
gemini = genai.GenerativeModel("gemini-1.5-flash")


def consultation_date() -> date:
    return date.today()


def ai_mode() -> str:
    return "gemini" if os.getenv("GEMINI_API_KEY") else "mock"


def _serialize_previous_visits(previous_consultations: Iterable[Consultation]) -> list[dict]:
    visits: list[dict] = []
    for consultation in previous_consultations:
        try:
            parsed = json.loads(str(consultation.ai_summary))
        except json.JSONDecodeError:
            parsed = {"visit_summary": str(consultation.ai_summary)}
        visits.append(
            {
                "date": consultation.date.isoformat(),
                "visit_summary": parsed.get("visit_summary", str(consultation.raw_notes)[:240]),
            }
        )
    return visits


def _build_manual_summary(
    notes: str,
    symptoms: list[str] | None = None,
    diagnosis_impression: str | None = None,
    medications: list[Medication] | None = None,
    tests: list[str] | None = None,
) -> AISummary:
    return AISummary(
        symptoms=symptoms or [],
        diagnosis_impression=diagnosis_impression or "Manual consultation saved without AI analysis.",
        medications_prescribed=medications or [],
        tests_ordered=tests or [],
        visit_summary=notes[:300] if notes else "Consultation saved without AI analysis.",
        flags=[],
        context_suggestions=[],
        possible_conditions=[],
        cumulative_patient_summary="Consultation saved without AI analysis. AI memory can be generated later.",
        pipeline_steps=[],
        risk_level="low",
    )


def extract_symptoms_fallback(notes: str) -> list[str]:
    symptom_keywords = [
        "fever",
        "cough",
        "cold",
        "headache",
        "vomiting",
        "nausea",
        "fatigue",
        "weakness",
        "pain",
        "ache",
        "rash",
        "itching",
        "breathlessness",
        "dizziness",
        "swelling",
        "bleeding",
        "diarrhoea",
        "diarrhea",
        "constipation",
        "chills",
        "shivering",
        "jaundice",
        "burning",
        "discharge",
        "sore throat",
        "runny nose",
        "chest pain",
        "back pain",
        "joint pain",
        "muscle pain",
        "abdominal pain",
        "loss of appetite",
        "weight loss",
        "sweating",
        "anxiety",
        "depression",
        "frequent urination",
        "blurred vision",
        "tingling",
        "numbness",
        "seizures",
    ]
    notes_lower = notes.lower()
    found = [symptom for symptom in symptom_keywords if symptom in notes_lower]
    return found if found else ["see consultation notes"]


def extract_meds_fallback(notes: str) -> list[dict]:
    common_meds = [
        "paracetamol",
        "ibuprofen",
        "amoxicillin",
        "azithromycin",
        "metformin",
        "amlodipine",
        "atorvastatin",
        "cetirizine",
        "pantoprazole",
        "omeprazole",
        "metronidazole",
        "ciprofloxacin",
        "doxycycline",
        "prednisolone",
        "betamethasone",
        "salbutamol",
        "montelukast",
        "losartan",
        "telmisartan",
        "atenolol",
        "fluconazole",
        "clotrimazole",
        "terbinafine",
        "glimepiride",
        "insulin",
        "hydrochlorothiazide",
        "furosemide",
        "spironolactone",
        "warfarin",
        "aspirin",
        "clopidogrel",
        "enalapril",
        "ramipril",
        "levothyroxine",
        "vitamin d",
        "calcium",
        "iron",
        "folic acid",
        "b12",
        "zinc",
        "oseltamivir",
        "tamiflu",
        "artemether",
        "hydroxychloroquine",
        "favipiravir",
    ]
    notes_lower = notes.lower()
    found: list[dict] = []
    for medication in common_meds:
        if medication in notes_lower:
            found.append(
                {
                    "name": medication.title(),
                    "dosage": "as prescribed",
                    "duration": "as advised",
                }
            )
    return found


def run_ai_pipeline(notes: str, prev: list[dict]) -> dict:
    if not notes or len(notes.strip()) < 10:
        return {
            "symptoms": ["insufficient notes provided"],
            "diagnosis_impression": "Please provide detailed consultation notes",
            "medications_prescribed": [],
            "tests_ordered": [],
            "visit_summary": "Notes too brief for AI analysis.",
            "flags": [],
            "context_suggestions": [],
            "cumulative_patient_summary": "Add more notes for AI summary.",
            "possible_conditions": [],
            "pipeline_steps": ["failed_insufficient_input"],
            "risk_level": "low",
        }

    prev_text = ""
    if prev:
        for visit in prev[-3:]:
            prev_text += f"- {visit.get('date', '')}: {visit.get('visit_summary', '')}\n"

    prompt = f"""You are a doctor's assistant. Read these consultation notes and extract information.

CONSULTATION NOTES:
{notes}

PREVIOUS VISITS:
{prev_text if prev_text else "First visit"}

Return a JSON object. Use EXACTLY this format with NO extra text before or after:

{{
  "symptoms": ["symptom1", "symptom2", "symptom3"],
  "diagnosis_impression": "Write 1-2 sentences about what condition this likely is",
  "medications_prescribed": [
    {{"name": "MedName", "dosage": "dose", "duration": "days"}}
  ],
  "tests_ordered": ["test1", "test2"],
  "visit_summary": "Write 2-3 sentences summarizing this visit specifically",
  "flags": ["Any symptom appearing in multiple visits"],
  "context_suggestions": ["Suggestion based on history"],
  "cumulative_patient_summary": "Write 3-4 sentences covering all visits and trends",
  "possible_conditions": ["condition1", "condition2"]
}}

RULES:
- symptoms: extract EVERY symptom mentioned in the notes above
- diagnosis_impression: must mention the actual condition from notes
- medications_prescribed: extract EVERY medicine mentioned with dosage
- tests_ordered: extract EVERY test mentioned
- visit_summary: must be specific to THIS visit
- Return ONLY the JSON object, nothing else"""

    try:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("Missing GEMINI_API_KEY")
        print(f"Calling Gemini with {len(notes)} chars of notes...")
        response = gemini.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 1500,
            },
        )
        raw = response.text.strip()
        print(f"Gemini raw response (first 200 chars): {raw[:200]}")

        if "```json" in raw:
            raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in raw:
            raw = raw.split("```", 1)[1].split("```", 1)[0].strip()

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        result = json.loads(raw)
        if not result.get("symptoms"):
            result["symptoms"] = ["see notes above"]
        if not result.get("visit_summary"):
            result["visit_summary"] = "Consultation recorded."
        if not result.get("diagnosis_impression"):
            result["diagnosis_impression"] = "See consultation notes for details."
        if not result.get("cumulative_patient_summary"):
            result["cumulative_patient_summary"] = result.get("visit_summary", "")
        result.setdefault("medications_prescribed", extract_meds_fallback(notes))
        result.setdefault("tests_ordered", [])
        result.setdefault("flags", [])
        result.setdefault("context_suggestions", [])
        result.setdefault("possible_conditions", [])
        result["pipeline_steps"] = ["gemini_success"]
        result.setdefault("risk_level", "low")
        print("Gemini pipeline SUCCESS")
        return result
    except json.JSONDecodeError as exc:
        print(f"JSON parse error: {exc}")
        print(f"Raw response was: {raw[:500]}")
        return {
            "symptoms": extract_symptoms_fallback(notes),
            "diagnosis_impression": "AI response format error — manual review needed",
            "medications_prescribed": extract_meds_fallback(notes),
            "tests_ordered": [],
            "visit_summary": f"Consultation recorded. Notes: {notes[:200]}",
            "flags": [],
            "context_suggestions": [],
            "possible_conditions": [],
            "cumulative_patient_summary": f"Patient history recorded across {len(prev) + 1} visits.",
            "pipeline_steps": ["json_parse_failed"],
            "risk_level": "low",
        }
    except Exception as exc:
        print(f"Gemini API error: {type(exc).__name__}: {exc}")
        return {
            "symptoms": extract_symptoms_fallback(notes),
            "diagnosis_impression": f"AI unavailable ({type(exc).__name__}) — notes saved",
            "medications_prescribed": extract_meds_fallback(notes),
            "tests_ordered": [],
            "visit_summary": f"Consultation notes saved. {notes[:150]}",
            "flags": [],
            "context_suggestions": [],
            "possible_conditions": [],
            "cumulative_patient_summary": "AI summary pending — retry analysis.",
            "pipeline_steps": ["api_error"],
            "risk_level": "low",
        }


def generate_ai_summary(
    previous_consultations: list[Consultation],
    current_notes: str,
) -> AISummary:
    payload = run_ai_pipeline(current_notes, _serialize_previous_visits(previous_consultations))
    steps = [
        PipelineStep(
            name=f"Step {index + 1}",
            success=True,
            message=value.replace("_", " ").capitalize(),
        )
        for index, value in enumerate(payload.get("pipeline_steps", []))
    ]
    try:
        return AISummary.model_validate(
            {
                **payload,
                "pipeline_steps": steps,
            }
        )
    except Exception:
        return _build_manual_summary(
            current_notes,
            symptoms=payload.get("symptoms", []),
            diagnosis_impression=payload.get("diagnosis_impression"),
            medications=[Medication.model_validate(item) for item in payload.get("medications_prescribed", [])],
            tests=payload.get("tests_ordered", []),
        )


def build_manual_summary(
    notes: str,
    symptoms: list[str],
    diagnosis_impression: str,
    medications: list[Medication],
    tests: list[str],
) -> AISummary:
    return _build_manual_summary(notes, symptoms, diagnosis_impression, medications, tests)
