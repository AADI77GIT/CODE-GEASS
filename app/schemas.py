from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Medication(BaseModel):
    name: str
    dosage: str
    duration: str


class ConditionPrediction(BaseModel):
    label: str
    confidence: float
    source: str


class PipelineStep(BaseModel):
    name: str
    success: bool
    message: str


class MLPredictionResponse(BaseModel):
    prediction: str
    confidence: float | None = None
    model_used: bool
    predictions: List[dict] = Field(default_factory=list)
    knowledge: dict = Field(default_factory=dict)
    model_type: str | None = None
    source: str | None = None


class MLPredictRequest(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    vitals: dict[str, float | None] = Field(default_factory=dict)
    age: float = 30
    gender: str = "Male"
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    heart_rate: float | None = None
    temperature_c: float | None = None
    oxygen_saturation: float | None = None
    wbc_count: float | None = None
    hemoglobin: float | None = None
    platelet_count: float | None = None
    crp_level: float | None = None
    glucose_level: float | None = None
    fever: float = 0
    cough: float = 0
    fatigue: float = 0
    headache: float = 0
    muscle_pain: float = 0
    nausea: float = 0
    vomiting: float = 0
    diarrhea: float = 0
    skin_rash: float = 0
    loss_smell: float = 0
    loss_taste: float = 0
    symptom_flags: dict[str, float] = Field(default_factory=dict)


class SymptomCheckerRequest(BaseModel):
    symptoms: List[str] = Field(default_factory=list)


class ClinicalMetrics(BaseModel):
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    heart_rate: float | None = None
    temperature_c: float | None = None
    oxygen_saturation: float | None = None
    wbc_count: float | None = None
    hemoglobin: float | None = None
    platelet_count: float | None = None
    crp_level: float | None = None
    glucose_level: float | None = None


class MLInsights(BaseModel):
    model_status: str
    model_summary: str
    condition_predictions: List[ConditionPrediction]
    acute_predictions: List[ConditionPrediction]
    triage_recommendation: str
    evidence: List[str]


class AISummary(BaseModel):
    symptoms: List[str]
    diagnosis_impression: str
    medications_prescribed: List[Medication]
    tests_ordered: List[str]
    visit_summary: str
    flags: List[str]
    cumulative_patient_summary: str
    context_suggestions: List[str] = Field(default_factory=list)
    possible_conditions: List[str] = Field(default_factory=list)
    risk_level: str = "low"
    pipeline_steps: List[PipelineStep] = Field(default_factory=list)
    ml_prediction: MLPredictionResponse | None = None
    ml_insights: MLInsights | None = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: str
    phone: str
    blood_group: str | None = None


class ConsultationCreate(BaseModel):
    patient_id: int
    notes: str = Field(default="", max_length=5000)
    clinical_metrics: ClinicalMetrics | None = None

    @model_validator(mode="after")
    def validate_meaningful_input(self):
        if not self.notes.strip():
            raise ValueError("Provide doctor notes before saving a consultation.")
        return self


class ConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    date: date
    raw_notes: str
    ai_summary: str
    created_at: datetime


class StructuredConsultationResponse(BaseModel):
    consultation_id: int
    patient_id: int
    date: date
    ai_summary: AISummary


class AppStatus(BaseModel):
    message: str
    environment: str
    ai_mode: str
    ml_model_status: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    ai_mode: str
    ml_model_status: str


class PatientListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: str
    blood_group: str | None = None


class PatientReportResponse(BaseModel):
    patient: PatientResponse
    total_visits: int
    active_medications: List[Medication]
    recurring_conditions: List[str]
    cumulative_summary: AISummary
    consultations: List[ConsultationResponse]


class PatientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    age: int = Field(ge=0, le=130)
    gender: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=6, max_length=50)
    blood_group: str | None = Field(default=None, max_length=20)
