# pip install google-generativeai reportlab
import io
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.ai_service import ai_mode, consultation_date, generate_ai_summary, gemini, run_ai_pipeline
from app.config import settings
from app.database import Base, SessionLocal, engine, get_db, run_startup_migrations
from app.ml_service import load_primary_model, model_status, predict_condition
from app.models import Consultation, Patient
from app.schemas import (
    AISummary,
    AppStatus,
    ConsultationCreate,
    ConsultationResponse,
    HealthResponse,
    MLPredictRequest,
    MLPredictionResponse,
    PatientCreate,
    PatientListItem,
    PatientReportResponse,
    PatientResponse,
    StructuredConsultationResponse,
    SymptomCheckerRequest,
)
from app.seed import seed_demo_data


DISEASE_SYMPTOM_MAP = {
    "Common Cold": {
        "symptoms": ["runny nose", "sneezing", "sore throat", "mild fever", "cough", "congestion", "headache", "fatigue", "watery eyes"],
        "medications": ["Paracetamol 500mg TDS", "Cetirizine 10mg OD", "Vitamin C 500mg"],
        "advice": "Rest, drink warm fluids, steam inhalation. Usually resolves in 7 days.",
        "urgency": "low",
    },
    "Influenza": {
        "symptoms": ["high fever", "severe bodyache", "muscle pain", "headache", "cough", "sore throat", "fatigue", "chills", "loss of appetite"],
        "medications": ["Paracetamol 650mg TDS", "Oseltamivir 75mg BD x5 days"],
        "advice": "Rest, isolation for 5 days, fluids. See doctor if breathing difficulty.",
        "urgency": "medium",
    },
    "Dengue Fever": {
        "symptoms": ["high fever", "severe headache", "pain behind eyes", "joint pain", "muscle pain", "skin rash", "nausea", "fatigue", "vomiting", "low platelet"],
        "medications": ["Paracetamol only (NO ibuprofen/aspirin)", "ORS", "IV fluids if severe"],
        "advice": "URGENT — see doctor immediately. Monitor platelet count daily.",
        "urgency": "high",
    },
    "Malaria": {
        "symptoms": ["cyclical fever", "chills", "rigors", "sweating", "headache", "nausea", "vomiting", "fatigue", "jaundice", "body ache"],
        "medications": ["Artemether-Lumefantrine", "Chloroquine (if P.vivax)"],
        "advice": "Requires blood test confirmation. See doctor IMMEDIATELY.",
        "urgency": "high",
    },
    "Typhoid": {
        "symptoms": ["prolonged fever", "headache", "weakness", "abdominal pain", "constipation", "loss of appetite", "rose spots", "fatigue"],
        "medications": ["Azithromycin 500mg OD x7 days", "Cefixime 200mg BD"],
        "advice": "Blood culture needed for confirmation. Doctor visit required.",
        "urgency": "high",
    },
    "COVID-19": {
        "symptoms": ["fever", "dry cough", "fatigue", "loss of smell", "loss of taste", "breathlessness", "body ache", "sore throat", "headache"],
        "medications": ["Paracetamol 650mg TDS", "Vitamin C", "Zinc", "Monitor O2 sat"],
        "advice": "Isolate immediately. Monitor oxygen. Hospital if O2 < 94%.",
        "urgency": "high",
    },
    "Pneumonia": {
        "symptoms": ["high fever", "productive cough", "chest pain", "breathlessness", "chills", "fatigue", "yellow sputum", "rapid breathing"],
        "medications": ["Amoxicillin-Clavulanate 625mg BD", "Azithromycin 500mg OD"],
        "advice": "Needs chest X-ray and doctor assessment urgently.",
        "urgency": "high",
    },
    "Tuberculosis": {
        "symptoms": ["prolonged cough", "blood in sputum", "night sweats", "weight loss", "low grade fever", "fatigue", "loss of appetite", "chest pain"],
        "medications": ["DOTS therapy — must be prescribed by doctor"],
        "advice": "See doctor for sputum test and chest X-ray. Do NOT self-medicate.",
        "urgency": "high",
    },
    "Diabetes (Type 2)": {
        "symptoms": ["frequent urination", "excessive thirst", "fatigue", "blurred vision", "slow healing wounds", "weight loss", "tingling feet", "hunger"],
        "medications": ["Metformin 500mg BD (doctor prescribed)", "Lifestyle changes"],
        "advice": "Get fasting blood sugar test. Requires doctor diagnosis.",
        "urgency": "medium",
    },
    "Hypertension": {
        "symptoms": ["headache", "dizziness", "blurred vision", "chest pain", "shortness of breath", "nosebleed", "palpitations", "fatigue"],
        "medications": ["Amlodipine 5mg OD", "Telmisartan 40mg OD (doctor prescribed)"],
        "advice": "Monitor BP daily. Doctor visit required for medication.",
        "urgency": "medium",
    },
    "Gastroenteritis": {
        "symptoms": ["diarrhea", "vomiting", "nausea", "abdominal pain", "fever", "cramps", "loss of appetite", "dehydration", "weakness"],
        "medications": ["ORS sachets", "Metronidazole 400mg TDS", "Probiotics"],
        "advice": "Drink ORS, avoid solid food for 24hrs. Doctor if blood in stool.",
        "urgency": "medium",
    },
    "Acid Reflux / GERD": {
        "symptoms": ["heartburn", "acidity", "chest burning", "nausea", "bloating", "belching", "sour taste", "difficulty swallowing", "indigestion"],
        "medications": ["Pantoprazole 40mg OD before meals", "Antacid syrup"],
        "advice": "Avoid spicy/fatty food, eat small meals, elevate head while sleeping.",
        "urgency": "low",
    },
    "Urinary Tract Infection": {
        "symptoms": ["burning urination", "frequent urination", "cloudy urine", "lower abdominal pain", "foul smell urine", "mild fever"],
        "medications": ["Nitrofurantoin 100mg BD x5 days", "Ciprofloxacin 500mg BD"],
        "advice": "Drink plenty of water. Urine culture needed. Doctor visit.",
        "urgency": "medium",
    },
    "Fungal Skin Infection": {
        "symptoms": ["itching", "ring shaped rash", "scaly skin", "redness", "skin rash", "burning skin", "cracked skin", "white patches"],
        "medications": ["Clotrimazole cream BD", "Fluconazole 150mg weekly x4"],
        "advice": "Keep skin dry, avoid sharing towels, wear cotton clothes.",
        "urgency": "low",
    },
    "Allergic Rhinitis": {
        "symptoms": ["sneezing", "runny nose", "itchy eyes", "nasal congestion", "watery eyes", "itchy nose", "postnasal drip", "mild headache"],
        "medications": ["Cetirizine 10mg OD", "Montelukast 10mg", "Nasal spray"],
        "advice": "Avoid allergen triggers. Works better with antihistamines long term.",
        "urgency": "low",
    },
    "Migraine": {
        "symptoms": ["severe headache", "one sided headache", "sensitivity to light", "nausea", "vomiting", "visual aura", "throbbing pain", "fatigue"],
        "medications": ["Sumatriptan 50mg (acute)", "Paracetamol 1g", "Dark quiet room"],
        "advice": "Track triggers (stress, sleep, food). Doctor for preventive therapy.",
        "urgency": "medium",
    },
    "Chickenpox": {
        "symptoms": ["itchy blisters", "skin rash", "fever", "fatigue", "loss of appetite", "headache", "fluid filled blisters"],
        "medications": ["Calamine lotion", "Paracetamol", "Acyclovir (if severe)"],
        "advice": "Isolate for 7 days. Do NOT scratch blisters. Doctor if breathless.",
        "urgency": "medium",
    },
    "Asthma": {
        "symptoms": ["wheezing", "breathlessness", "chest tightness", "cough", "shortness of breath", "nighttime cough", "exercise intolerance"],
        "medications": ["Salbutamol inhaler (rescue)", "Budesonide inhaler (controller)"],
        "advice": "Identify and avoid triggers. Carry rescue inhaler always.",
        "urgency": "medium",
    },
    "Anaemia": {
        "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness", "cold hands", "rapid heartbeat", "headache", "brittle nails"],
        "medications": ["Iron tablets 150mg OD", "Folic acid 5mg OD", "Vitamin B12"],
        "advice": "Blood test needed. Eat iron-rich foods. Doctor for cause.",
        "urgency": "medium",
    },
    "Jaundice / Hepatitis": {
        "symptoms": ["yellow eyes", "yellow skin", "dark urine", "pale stools", "fatigue", "nausea", "abdominal pain", "loss of appetite", "itching"],
        "medications": ["No self-medication — doctor required immediately"],
        "advice": "URGENT doctor visit. Blood tests (LFT, Hepatitis panel) needed.",
        "urgency": "high",
    },
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_startup_migrations()
    load_primary_model()
    if settings.seed_demo_data:
        db = SessionLocal()
        try:
            seed_demo_data(db)
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test-gemini")
def test_gemini():
    try:
        response = gemini.generate_content("Say hello in one word")
        return {"status": "working", "response": response.text}
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "api_key_set": bool(os.getenv("GEMINI_API_KEY", "")),
        }


def _get_patient_or_404(patient_id: int, db: Session) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()  # type: ignore[arg-type]
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def _patient_consultations(patient_id: int, db: Session) -> list[Consultation]:
    return (
        db.query(Consultation)
        .filter(Consultation.patient_id == patient_id)  # type: ignore[arg-type]
        .order_by(Consultation.date.desc(), Consultation.created_at.desc())  # type: ignore[attr-defined]
        .all()
    )


def _build_consultation_notes(payload: ConsultationCreate) -> str:
    sections: list[str] = []
    if payload.notes.strip():
        sections.append(payload.notes.strip())
    if payload.clinical_metrics:
        metrics = payload.clinical_metrics.model_dump(exclude_none=True)
        if metrics:
            sections.append(f"Clinical metrics: {json.dumps(metrics)}")
    return "\n".join(sections) or "Consultation recorded."


def _load_summary(consultation: Consultation) -> AISummary | None:
    try:
        return AISummary.model_validate_json(str(consultation.ai_summary))
    except Exception:
        return None


def _latest_summary(patient_id: int, db: Session) -> AISummary:
    consultations = _patient_consultations(patient_id, db)
    if not consultations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No consultations found for patient")
    summary = _load_summary(consultations[0])
    if summary:
        return summary
    recalculated = generate_ai_summary(consultations[1:], str(consultations[0].raw_notes))
    consultations[0].ai_summary = recalculated.model_dump_json()  # type: ignore[assignment]
    db.commit()
    return recalculated


def _active_medications(consultations: list[Consultation]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    medications: list[dict] = []
    for consultation in consultations:
        summary = _load_summary(consultation)
        if not summary:
            continue
        for medication in summary.medications_prescribed:
            key = (medication.name, medication.dosage, medication.duration)
            if key not in seen:
                seen.add(key)
                medications.append(medication.model_dump())
    return medications


def _recurring_conditions(consultations: list[Consultation]) -> list[str]:
    counts: dict[str, int] = {}
    for consultation in consultations:
        summary = _load_summary(consultation)
        if not summary:
            continue
        for symptom in summary.symptoms:
            counts[symptom] = counts.get(symptom, 0) + 1
    return [symptom for symptom, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])) if count >= 2]


def _build_pdf(patient: Patient, consultations: list[Consultation], summary: AISummary) -> bytes:
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)
    sub_style = ParagraphStyle("sub", fontSize=8, fontName="Helvetica", alignment=TA_CENTER, textColor=colors.grey, spaceAfter=6)
    section_style = ParagraphStyle("section", fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#1a3a6b"), spaceBefore=4, spaceAfter=2)
    body_style = ParagraphStyle("body", fontSize=7.5, fontName="Helvetica", leading=10, spaceAfter=2)
    table_text_style = ParagraphStyle("td", fontSize=7, leading=9)
    flag_style = ParagraphStyle(
        "flag",
        fontSize=7,
        fontName="Helvetica",
        backColor=colors.HexColor("#fff8e1"),
        borderColor=colors.HexColor("#fbbf24"),
        borderWidth=0.5,
        borderPadding=4,
        textColor=colors.HexColor("#7a4f00"),
        spaceAfter=4,
    )
    footer_style = ParagraphStyle("footer", fontSize=6.5, fontName="Helvetica", textColor=colors.grey, alignment=TA_CENTER)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    story = []
    story.append(Paragraph("MediTrack AI - Patient Medical Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y')} | Confidential", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4f8ef7"), spaceAfter=6))

    info_table = Table(
        [[
            "Patient",
            patient.name,
            "Age",
            str(patient.age),
            "Gender",
            patient.gender,
            "Blood Group",
            patient.blood_group or "N/A",
            "Phone",
            patient.phone,
        ]],
        colWidths=[1.5 * cm, 3 * cm, 1 * cm, 1.2 * cm, 1.5 * cm, 1.5 * cm, 2 * cm, 1.5 * cm, 1.2 * cm, 2.5 * cm],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0fe")),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
                ("FONTNAME", (4, 0), (4, 0), "Helvetica-Bold"),
                ("FONTNAME", (6, 0), (6, 0), "Helvetica-Bold"),
                ("FONTNAME", (8, 0), (8, 0), "Helvetica-Bold"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#4f8ef7")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("AI Cumulative Health Summary", section_style))
    story.append(Paragraph(summary.cumulative_patient_summary or "No cumulative summary available.", body_style))
    if summary.flags:
        story.append(Paragraph("  ".join([f"&#9888; {flag}" for flag in summary.flags]), flag_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Consultation History", section_style))
    visit_data = [["#", "Date", "Diagnosis", "Symptoms", "Medications", "Tests"]]
    for index, consultation in enumerate(sorted(consultations, key=lambda item: item.date), start=1):
        visit_summary = _load_summary(consultation) or summary
        symptoms = ", ".join(visit_summary.symptoms)[:40] or "-"
        medications = ", ".join(f"{med.name} {med.dosage}".strip() for med in visit_summary.medications_prescribed)[:45] or "-"
        tests = ", ".join(visit_summary.tests_ordered)[:35] or "-"
        diagnosis = (visit_summary.diagnosis_impression or "-")[:45]
        visit_data.append(
            [
                str(index),
                consultation.date.strftime("%d %b %Y"),
                Paragraph(diagnosis, table_text_style),
                Paragraph(symptoms, table_text_style),
                Paragraph(medications, table_text_style),
                Paragraph(tests, table_text_style),
            ]
        )

    visit_table = Table(visit_data, colWidths=[0.6 * cm, 2 * cm, 4 * cm, 3.5 * cm, 4 * cm, 3 * cm], repeatRows=1)
    visit_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a6b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7ff")]),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#2a3358")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(visit_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Current Medications", section_style))
    active_medications = []
    seen_meds = set()
    for consultation in sorted(consultations, key=lambda item: item.date, reverse=True):
        visit_summary = _load_summary(consultation)
        if not visit_summary:
            continue
        for medication in visit_summary.medications_prescribed:
            if medication.name not in seen_meds:
                seen_meds.add(medication.name)
                active_medications.append(
                    [medication.name, medication.dosage or "-", medication.duration or "-", consultation.date.strftime("%d %b %Y")]
                )
    if active_medications:
        medication_table = Table([["Medication", "Dosage", "Duration", "Prescribed"], *active_medications], colWidths=[5 * cm, 3 * cm, 3 * cm, 3 * cm], repeatRows=1)
        medication_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f6e56")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e1f5ee")]),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0f6e56")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(medication_table)
    else:
        story.append(Paragraph("No medications on record.", body_style))

    if summary.possible_conditions:
        story.append(Spacer(1, 6))
        story.append(Paragraph("AI Condition Insights", section_style))
        story.append(Paragraph(f"Possible conditions considered: {', '.join(summary.possible_conditions)}", body_style))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4))
    story.append(
        Paragraph(
            "Generated by MediTrack AI | For medical use only | AI outputs are assistive and not a substitute for clinical diagnosis",
            footer_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", environment=settings.environment, ai_mode=ai_mode(), ml_model_status=model_status())


@app.get("/patients", response_model=list[PatientListItem])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).order_by(Patient.name.asc()).all()


@app.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@app.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return _get_patient_or_404(patient_id, db)


@app.get("/consultations/{patient_id}", response_model=list[ConsultationResponse])
def get_consultations(patient_id: int, db: Session = Depends(get_db)):
    _get_patient_or_404(patient_id, db)
    return _patient_consultations(patient_id, db)


@app.post("/ml-predict", response_model=MLPredictionResponse)
def ml_predict(payload: MLPredictRequest):
    return predict_condition(payload)


@app.post("/consultations", response_model=StructuredConsultationResponse, status_code=status.HTTP_201_CREATED)
def create_consultation(payload: ConsultationCreate, db: Session = Depends(get_db)):
    _get_patient_or_404(payload.patient_id, db)
    compiled_notes = _build_consultation_notes(payload)
    ml_prediction = predict_condition(
        MLPredictRequest(
            symptoms=[],
            vitals={
                "bp_systolic": payload.clinical_metrics.systolic_bp if payload.clinical_metrics else None,
                "bp_diastolic": payload.clinical_metrics.diastolic_bp if payload.clinical_metrics else None,
                "heart_rate": payload.clinical_metrics.heart_rate if payload.clinical_metrics else None,
                "temperature": payload.clinical_metrics.temperature_c if payload.clinical_metrics else None,
                "oxygen_sat": payload.clinical_metrics.oxygen_saturation if payload.clinical_metrics else None,
                "glucose": payload.clinical_metrics.glucose_level if payload.clinical_metrics else None,
            },
            systolic_bp=payload.clinical_metrics.systolic_bp if payload.clinical_metrics else None,
            diastolic_bp=payload.clinical_metrics.diastolic_bp if payload.clinical_metrics else None,
            heart_rate=payload.clinical_metrics.heart_rate if payload.clinical_metrics else None,
            temperature_c=payload.clinical_metrics.temperature_c if payload.clinical_metrics else None,
            oxygen_saturation=payload.clinical_metrics.oxygen_saturation if payload.clinical_metrics else None,
            glucose_level=payload.clinical_metrics.glucose_level if payload.clinical_metrics else None,
        )
    )
    previous_consultations = _patient_consultations(payload.patient_id, db)
    ai_summary = generate_ai_summary(previous_consultations, compiled_notes)
    ai_summary.symptoms = ai_summary.symptoms or []
    ai_summary.diagnosis_impression = ai_summary.diagnosis_impression or ""
    ai_summary.medications_prescribed = ai_summary.medications_prescribed or []
    ai_summary.tests_ordered = ai_summary.tests_ordered or []
    ai_summary.visit_summary = ai_summary.visit_summary or "Consultation recorded."
    ai_summary.flags = ai_summary.flags or []
    ai_summary.context_suggestions = ai_summary.context_suggestions or []
    ai_summary.cumulative_patient_summary = ai_summary.cumulative_patient_summary or ""
    ai_summary.possible_conditions = ai_summary.possible_conditions or []
    ai_summary.ml_prediction = ml_prediction

    consultation = Consultation(
        patient_id=payload.patient_id,
        date=consultation_date(),
        raw_notes=compiled_notes,
        ai_summary=ai_summary.model_dump_json(),
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return StructuredConsultationResponse(
        consultation_id=consultation.id,  # type: ignore[arg-type]
        patient_id=payload.patient_id,
        date=consultation.date,  # type: ignore[arg-type]
        ai_summary=ai_summary,
    )


@app.post("/consultations/{consultation_id}/reanalyze", response_model=StructuredConsultationResponse)
def reanalyze_consultation(consultation_id: int, db: Session = Depends(get_db)):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    previous = [item for item in _patient_consultations(consultation.patient_id, db) if item.id != consultation.id]
    ai_summary = generate_ai_summary(previous, str(consultation.raw_notes))
    existing = _load_summary(consultation)
    if existing and existing.ml_prediction:
        ai_summary.ml_prediction = existing.ml_prediction
    consultation.ai_summary = ai_summary.model_dump_json()  # type: ignore[assignment]
    db.commit()
    db.refresh(consultation)
    return StructuredConsultationResponse(
        consultation_id=consultation.id,  # type: ignore[arg-type]
        patient_id=consultation.patient_id,  # type: ignore[arg-type]
        date=consultation.date,  # type: ignore[arg-type]
        ai_summary=ai_summary,
    )


@app.post("/retry-ai/{consultation_id}")
def retry_ai(consultation_id: int, db: Session = Depends(get_db)):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")

    previous_rows = (
        db.query(Consultation)
        .filter(Consultation.patient_id == consultation.patient_id, Consultation.id != consultation_id)
        .order_by(Consultation.date.asc(), Consultation.created_at.asc())
        .all()
    )
    result = generate_ai_summary(previous_rows, str(consultation.raw_notes))
    existing = _load_summary(consultation)
    if existing and existing.ml_prediction:
        result.ml_prediction = existing.ml_prediction
    consultation.ai_summary = result.model_dump_json()  # type: ignore[assignment]
    db.commit()
    return {"id": consultation_id, **result.model_dump()}


@app.post("/symptom-checker")
def symptom_checker(data: SymptomCheckerRequest):
    if not data.symptoms:
        return {"results": [], "message": "Please select at least one symptom"}

    user_symptoms = [item.lower().strip() for item in data.symptoms if str(item).strip()]
    results: list[dict] = []
    for disease, info in DISEASE_SYMPTOM_MAP.items():
        disease_symptoms = [item.lower() for item in info["symptoms"]]
        matches: list[str] = []
        for user_symptom in user_symptoms:
            for disease_symptom in disease_symptoms:
                if user_symptom in disease_symptom or disease_symptom in user_symptom or (len(user_symptom) > 4 and user_symptom in disease_symptom):
                    matches.append(user_symptom)
                    break
        if matches:
            match_ratio = len(matches) / len(disease_symptoms)
            coverage_ratio = len(matches) / len(user_symptoms)
            confidence = round((match_ratio * 0.6 + coverage_ratio * 0.4) * 100)
            confidence = min(confidence, 95)
            results.append(
                {
                    "disease": disease,
                    "confidence": confidence,
                    "matched_symptoms": matches,
                    "total_disease_symptoms": len(disease_symptoms),
                    "medications": info["medications"],
                    "advice": info["advice"],
                    "urgency": info["urgency"],
                }
            )

    results.sort(key=lambda item: -item["confidence"])
    return {
        "results": results[:5],
        "symptoms_checked": user_symptoms,
        "disclaimer": "This is NOT a diagnosis. Always consult a qualified doctor.",
        "total_diseases_checked": len(DISEASE_SYMPTOM_MAP),
    }


@app.get("/all-symptoms")
def get_all_symptoms():
    all_symptoms: set[str] = set()
    for info in DISEASE_SYMPTOM_MAP.values():
        for symptom in info["symptoms"]:
            all_symptoms.add(symptom.lower())
    return {"symptoms": sorted(all_symptoms)}


@app.get("/ai-summary/{patient_id}", response_model=AISummary)
def get_cumulative_ai_summary(patient_id: int, db: Session = Depends(get_db)):
    _get_patient_or_404(patient_id, db)
    return _latest_summary(patient_id, db)


@app.get("/reports/{patient_id}", response_model=PatientReportResponse)
def get_patient_report(patient_id: int, db: Session = Depends(get_db)):
    patient = _get_patient_or_404(patient_id, db)
    consultations = _patient_consultations(patient_id, db)
    summary = _latest_summary(patient_id, db)
    return PatientReportResponse(
        patient=patient,
        total_visits=len(consultations),
        active_medications=_active_medications(consultations),  # type: ignore[arg-type]
        recurring_conditions=_recurring_conditions(consultations),
        cumulative_summary=summary,
        consultations=consultations,  # type: ignore[arg-type]
    )


@app.get("/report/{patient_id}")
def report_pdf(patient_id: int, db: Session = Depends(get_db)):
    patient = _get_patient_or_404(patient_id, db)
    consultations = _patient_consultations(patient_id, db)
    summary = _latest_summary(patient_id, db)
    pdf = _build_pdf(patient, consultations, summary)
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="meditrack_report_{patient.name.replace(" ", "_")}.pdf"'},
    )


@app.get("/", response_model=AppStatus)
def root():
    return AppStatus(
        message=f"{settings.app_name} is running",
        environment=settings.environment,
        ai_mode=ai_mode(),
        ml_model_status=model_status(),
    )
