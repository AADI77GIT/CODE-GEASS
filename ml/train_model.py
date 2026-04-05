import json
import os
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import LeaveOneOut, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ML_DIR = ROOT / "ml"


def main() -> None:
    warnings.filterwarnings("ignore", message="The number of unique classes is greater than 50% of the number of samples.*")
    print("Loading datasets...")
    df_synthetic = pd.read_csv(DATA_DIR / "synthetic_medical_symptoms_dataset.csv")
    df_testing = pd.read_csv(DATA_DIR / "Testing.csv")
    df_diseases = pd.read_csv(DATA_DIR / "Diseases_Symptoms.csv")

    feature_cols_a = [
        "age",
        "fever",
        "cough",
        "fatigue",
        "headache",
        "muscle_pain",
        "nausea",
        "vomiting",
        "diarrhea",
        "skin_rash",
        "loss_smell",
        "loss_taste",
        "systolic_bp",
        "diastolic_bp",
        "heart_rate",
        "temperature_c",
        "oxygen_saturation",
        "wbc_count",
        "hemoglobin",
        "platelet_count",
        "crp_level",
        "glucose_level",
    ]
    df_synthetic["gender_enc"] = (df_synthetic["gender"].astype(str).str.lower() == "male").astype(int)
    feature_cols_a.append("gender_enc")
    x_a = df_synthetic[feature_cols_a].copy()
    x_a = x_a.fillna(x_a.median(numeric_only=True))
    y_a = df_synthetic["diagnosis"].astype(str).str.strip()

    model_a = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                GradientBoostingClassifier(
                    n_estimators=200,
                    learning_rate=0.1,
                    subsample=0.8,
                    max_depth=5,
                    random_state=42,
                ),
            ),
        ]
    )
    x_train_a, x_test_a, y_train_a, y_test_a = train_test_split(
        x_a, y_a, test_size=0.2, random_state=42, stratify=y_a
    )
    model_a.fit(x_train_a, y_train_a)
    cv_scores_a = cross_val_score(model_a, x_a, y_a, cv=5, scoring="accuracy")
    print(f"Model A (Vitals) - CV Accuracy: {cv_scores_a.mean():.3f} +/- {cv_scores_a.std():.3f}")
    print(classification_report(y_test_a, model_a.predict(x_test_a)))
    print(f"Model A test accuracy: {accuracy_score(y_test_a, model_a.predict(x_test_a)):.3f}")

    feature_cols_b = list(df_testing.columns[:-1])
    x_b = df_testing[feature_cols_b].fillna(0)
    y_b = df_testing["prognosis"].astype(str).str.strip()
    model_b = Pipeline(
        [
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=None,
                    min_samples_split=2,
                    class_weight="balanced",
                    random_state=42,
                ),
            )
        ]
    )

    loo = LeaveOneOut()
    correct = 0
    for train_idx, test_idx in loo.split(x_b):
        m = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42)
        m.fit(x_b.iloc[train_idx], y_b.iloc[train_idx])
        if m.predict(x_b.iloc[test_idx])[0] == y_b.iloc[test_idx].values[0]:
            correct += 1
    print(f"Model B (Symptoms) - LOO Accuracy: {correct / len(x_b):.3f}")
    model_b.fit(x_b, y_b)

    knowledge_base = {}
    for _, row in df_diseases.iterrows():
        name = str(row["Name"]).strip().lower()
        knowledge_base[name] = {
            "symptoms": str(row.get("Symptoms", "")),
            "treatments": str(row.get("Treatments", "")),
        }

    os.makedirs(ML_DIR, exist_ok=True)
    with open(ML_DIR / "knowledge_base.json", "w", encoding="utf-8") as handle:
        json.dump(knowledge_base, handle, indent=2)
    print(f"Knowledge base saved: {len(knowledge_base)} diseases")

    joblib.dump(model_a, ML_DIR / "model_vitals.pkl")
    joblib.dump(model_b, ML_DIR / "model_symptoms.pkl")

    with open(ML_DIR / "features.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "model_A_features": feature_cols_a,
                "model_B_features": feature_cols_b,
                "model_A_classes": list(model_a.named_steps["clf"].classes_),
                "model_B_classes": list(model_b.named_steps["clf"].classes_),
            },
            handle,
            indent=2,
        )

    with open(ML_DIR / "training_report.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "model_A_cv_accuracy_mean": round(float(cv_scores_a.mean()), 4),
                "model_A_cv_accuracy_std": round(float(cv_scores_a.std()), 4),
                "model_A_test_accuracy": round(float(accuracy_score(y_test_a, model_a.predict(x_test_a))), 4),
                "model_B_loo_accuracy": round(float(correct / len(x_b)), 4),
                "knowledge_base_size": len(knowledge_base),
            },
            handle,
            indent=2,
        )

    print("All models saved to ml/ folder")
    print(f"Model A diseases: {list(model_a.named_steps['clf'].classes_)}")
    print(f"Model B diseases: {list(model_b.named_steps['clf'].classes_)[:10]}...")


if __name__ == "__main__":
    main()
