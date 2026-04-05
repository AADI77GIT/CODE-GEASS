from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.schemas import MLPredictRequest, MLPredictionResponse

ML_DIR = Path(__file__).resolve().parents[1] / "ml"
MODEL_VITALS_PATH = ML_DIR / "model_vitals.pkl"
MODEL_SYMPTOMS_PATH = ML_DIR / "model_symptoms.pkl"
FEATURES_PATH = ML_DIR / "features.json"
KNOWLEDGE_BASE_PATH = ML_DIR / "knowledge_base.json"

MODEL_VITALS = None
MODEL_SYMPTOMS = None
FEATURES: dict[str, Any] = {}
KNOWLEDGE_BASE: dict[str, Any] = {}


def load_primary_model() -> None:
    global MODEL_VITALS, MODEL_SYMPTOMS, FEATURES, KNOWLEDGE_BASE
    try:
        MODEL_VITALS = joblib.load(MODEL_VITALS_PATH)
        MODEL_SYMPTOMS = joblib.load(MODEL_SYMPTOMS_PATH)
        FEATURES = json.loads(FEATURES_PATH.read_text(encoding="utf-8"))
        KNOWLEDGE_BASE = json.loads(KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8"))
        print("Both ML models loaded successfully")
    except Exception as exc:
        MODEL_VITALS = None
        MODEL_SYMPTOMS = None
        FEATURES = {}
        KNOWLEDGE_BASE = {}
        print(f"ML models not loaded: {exc}")


def model_status() -> str:
    return "trained" if MODEL_VITALS is not None or MODEL_SYMPTOMS is not None else "untrained"


def _list_to_symptom_flags(symptoms: list[str]) -> dict[str, float]:
    symptom_flags: dict[str, float] = {}
    normalized = {item.strip().lower().replace(" ", "_") for item in symptoms if item.strip()}
    for item in normalized:
        symptom_flags[item] = 1.0
        if item == "high_fever":
            symptom_flags["fever"] = 1.0
        if item == "skin_rash":
            symptom_flags["itching"] = max(symptom_flags.get("itching", 0.0), 1.0)
    return symptom_flags


def _legacy_payload(symptoms: list[str], vitals: dict[str, float | None] | None) -> MLPredictRequest:
    vitals = vitals or {}
    symptom_flags = _list_to_symptom_flags(symptoms)
    normalized = {item.strip().lower().replace(" ", "_") for item in symptoms if item.strip()}
    return MLPredictRequest(
        symptoms=symptoms,
        vitals=vitals,
        systolic_bp=vitals.get("bp_systolic"),
        diastolic_bp=vitals.get("bp_diastolic"),
        heart_rate=vitals.get("heart_rate"),
        temperature_c=vitals.get("temperature"),
        oxygen_saturation=vitals.get("oxygen_sat"),
        glucose_level=vitals.get("glucose"),
        fever=2 if "fever" in normalized or "high_fever" in normalized else 0,
        cough=1 if "cough" in normalized else 0,
        fatigue=1 if "fatigue" in normalized else 0,
        headache=1 if "headache" in normalized else 0,
        muscle_pain=1 if "muscle_pain" in normalized or "muscle pain" in normalized else 0,
        nausea=1 if "nausea" in normalized else 0,
        vomiting=1 if "vomiting" in normalized else 0,
        diarrhea=1 if "diarrhea" in normalized or "diarrhoea" in normalized else 0,
        skin_rash=1 if "skin_rash" in normalized else 0,
        loss_smell=1 if "loss_smell" in normalized else 0,
        loss_taste=1 if "loss_taste" in normalized else 0,
        symptom_flags=symptom_flags,
    )


def _knowledge_for(disease: str) -> dict[str, str]:
    top_disease = disease.lower()
    for key, value in KNOWLEDGE_BASE.items():
        if key in top_disease or top_disease in key:
            return value
    return {}


def _top_predictions(classes: list[str], probabilities: np.ndarray, min_threshold: float = 0.05) -> list[dict[str, Any]]:
    top_indices = np.argsort(probabilities)[-3:][::-1]
    predictions = []
    for index in top_indices:
        if float(probabilities[index]) > min_threshold:
            predictions.append(
                {
                    "disease": classes[index],
                    "confidence": round(float(probabilities[index]) * 100, 1),
                }
            )
    return predictions


def _apply_clinical_adjustments(predictions: list[dict[str, Any]], data: MLPredictRequest) -> list[dict[str, Any]]:
    adjusted: list[dict[str, Any]] = []
    symptom_flags = data.symptom_flags or {}
    for prediction in predictions:
        next_prediction = dict(prediction)
        disease = next_prediction["disease"].lower()
        score = float(next_prediction["confidence"])
        if data.oxygen_saturation is not None and data.oxygen_saturation < 94 and (data.cough or symptom_flags.get("cough")):
            if "pneumonia" in disease or "covid" in disease:
                score += 26
            elif "asthma" in disease:
                score += 10
        if data.temperature_c is not None and data.temperature_c >= 38.5 and (data.fever or symptom_flags.get("high_fever")):
            if "influenza" in disease or "covid" in disease or "dengue" in disease:
                score += 8
        if data.glucose_level is not None and data.glucose_level >= 180 and (symptom_flags.get("polyuria") or data.fatigue):
            if "diabetes" in disease:
                score += 22
        if (data.skin_rash or symptom_flags.get("skin_rash")) and symptom_flags.get("itching"):
            if "fungal" in disease or "allergy" in disease or "drug reaction" in disease:
                score += 20
        next_prediction["confidence"] = round(min(score, 99.0), 1)
        adjusted.append(next_prediction)
    return adjusted


def predict_condition(
    data_or_symptoms: MLPredictRequest | list[str] | None = None,
    vitals: dict[str, float | None] | None = None,
) -> MLPredictionResponse:
    data = data_or_symptoms if isinstance(data_or_symptoms, MLPredictRequest) else _legacy_payload(data_or_symptoms or [], vitals)
    if isinstance(data_or_symptoms, MLPredictRequest) and data.vitals:
        data = data.model_copy(
            update={
                "systolic_bp": data.systolic_bp if data.systolic_bp is not None else data.vitals.get("bp_systolic"),
                "diastolic_bp": data.diastolic_bp if data.diastolic_bp is not None else data.vitals.get("bp_diastolic"),
                "heart_rate": data.heart_rate if data.heart_rate is not None else data.vitals.get("heart_rate"),
                "temperature_c": data.temperature_c if data.temperature_c is not None else data.vitals.get("temperature"),
                "oxygen_saturation": data.oxygen_saturation if data.oxygen_saturation is not None else data.vitals.get("oxygen_sat"),
                "glucose_level": data.glucose_level if data.glucose_level is not None else data.vitals.get("glucose"),
            }
        )
    if not data.symptom_flags and data.symptoms:
        data = data.model_copy(update={"symptom_flags": _list_to_symptom_flags(data.symptoms)})
    if data.symptoms:
        normalized = {item.strip().lower().replace(" ", "_") for item in data.symptoms if item.strip()}
        data = data.model_copy(
            update={
                "fever": data.fever or (2 if "fever" in normalized or "high_fever" in normalized else 0),
                "cough": data.cough or (1 if "cough" in normalized else 0),
                "fatigue": data.fatigue or (1 if "fatigue" in normalized else 0),
                "headache": data.headache or (1 if "headache" in normalized else 0),
                "muscle_pain": data.muscle_pain or (1 if "muscle_pain" in normalized else 0),
                "nausea": data.nausea or (1 if "nausea" in normalized else 0),
                "vomiting": data.vomiting or (1 if "vomiting" in normalized else 0),
                "diarrhea": data.diarrhea or (1 if "diarrhea" in normalized or "diarrhoea" in normalized else 0),
                "skin_rash": data.skin_rash or (1 if "skin_rash" in normalized or "rash" in normalized else 0),
                "loss_smell": data.loss_smell or (1 if "loss_smell" in normalized else 0),
                "loss_taste": data.loss_taste or (1 if "loss_taste" in normalized else 0),
            }
        )
    results: dict[str, Any] = {"model_used": False, "predictions": [], "knowledge": {}, "model_type": None}

    if MODEL_VITALS and FEATURES and (data.systolic_bp or data.heart_rate or data.temperature_c):
        try:
            vitals_defaults = {
                "age": data.age,
                "fever": data.fever,
                "cough": data.cough,
                "fatigue": data.fatigue,
                "headache": data.headache,
                "muscle_pain": data.muscle_pain,
                "nausea": data.nausea,
                "vomiting": data.vomiting,
                "diarrhea": data.diarrhea,
                "skin_rash": data.skin_rash,
                "loss_smell": data.loss_smell,
                "loss_taste": data.loss_taste,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 75,
                "temperature_c": 37.0,
                "oxygen_saturation": 98.0,
                "wbc_count": 7.0,
                "hemoglobin": 13.5,
                "platelet_count": 250.0,
                "crp_level": 5.0,
                "glucose_level": 100.0,
            }
            row = []
            for feature in FEATURES.get("model_A_features", []):
                if feature == "gender_enc":
                    row.append(1 if data.gender.lower() == "male" else 0)
                elif getattr(data, feature, None) is not None:
                    row.append(float(getattr(data, feature)))
                else:
                    row.append(vitals_defaults.get(feature, 0))
            probabilities = MODEL_VITALS.predict_proba(pd.DataFrame([row], columns=FEATURES.get("model_A_features", [])))[0]
            classes = FEATURES.get("model_A_classes", [])
            results["predictions"].extend(_top_predictions(classes, probabilities))
            results["model_used"] = True
            results["model_type"] = "vitals_based"
        except Exception as exc:
            print(f"Model A error: {exc}")

    if MODEL_SYMPTOMS and FEATURES and data.symptom_flags:
        try:
            feature_cols = FEATURES.get("model_B_features", [])
            row = [float(data.symptom_flags.get(feature, 0)) for feature in feature_cols]
            probabilities = MODEL_SYMPTOMS.predict_proba(pd.DataFrame([row], columns=feature_cols))[0]
            classes = FEATURES.get("model_B_classes", [])
            symptom_predictions = _top_predictions(classes, probabilities)
            existing = {item["disease"] for item in results["predictions"]}
            for item in symptom_predictions:
                item["source"] = "symptom_model"
                if item["disease"] not in existing:
                    results["predictions"].append(item)
            results["model_used"] = True
            if results["model_type"] is None:
                results["model_type"] = "symptom_based"
        except Exception as exc:
            print(f"Model B error: {exc}")

    if results["predictions"]:
        results["predictions"] = _apply_clinical_adjustments(results["predictions"], data)
        results["predictions"] = sorted(results["predictions"], key=lambda item: item["confidence"], reverse=True)
        results["knowledge"] = _knowledge_for(results["predictions"][0]["disease"])
        top_prediction = results["predictions"][0]
        return MLPredictionResponse(
            prediction=top_prediction["disease"],
            confidence=round(float(top_prediction["confidence"]) / 100, 4),
            model_used=True,
            predictions=results["predictions"],
            knowledge=results["knowledge"],
            model_type="hybrid" if any("source" in item for item in results["predictions"]) and results["model_type"] else results["model_type"],
            source=top_prediction.get("source", results["model_type"]),
        )

    return MLPredictionResponse(
        prediction="ML model not available",
        confidence=None,
        model_used=False,
        predictions=[],
        knowledge={},
        model_type=None,
        source=None,
    )
