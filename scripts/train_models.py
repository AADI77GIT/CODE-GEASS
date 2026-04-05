from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "app" / "ml_artifacts"
HEALTHCARE_CSV = Path(r"C:\Users\AADI\OneDrive\Desktop\1ST YEAR BOOKS\Healthcare.csv")
SYNTHETIC_CSV = Path(r"C:\Users\AADI\OneDrive\Desktop\1ST YEAR BOOKS\synthetic_medical_symptoms_dataset.csv")


def ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def train_disease_model() -> dict:
    df = pd.read_csv(HEALTHCARE_CSV).dropna()
    features = df[["Age", "Gender", "Symptoms", "Symptom_Count"]].copy()
    target = df["Disease"].copy()

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("symptoms", TfidfVectorizer(ngram_range=(1, 2), min_df=2), "Symptoms"),
            ("gender", OneHotEncoder(handle_unknown="ignore"), ["Gender"]),
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), ["Age", "Symptom_Count"]),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2500,
                    solver="lbfgs",
                ),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    result = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "macro_f1": float(f1_score(y_test, predictions, average="macro")),
        "report": classification_report(y_test, predictions, output_dict=True),
    }

    joblib.dump(
        {"pipeline": pipeline, "classes": list(pipeline.named_steps["classifier"].classes_)},
        ARTIFACTS_DIR / "disease_model.joblib",
    )
    return result


def train_acute_model() -> dict:
    df = pd.read_csv(SYNTHETIC_CSV).dropna()
    target = df["diagnosis"].copy()
    features = df.drop(columns=["diagnosis"]).copy()

    categorical_columns = ["gender"]
    numeric_columns = [column for column in features.columns if column not in categorical_columns]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("gender", OneHotEncoder(handle_unknown="ignore"), categorical_columns),
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_columns),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2500,
                    solver="lbfgs",
                ),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    result = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "macro_f1": float(f1_score(y_test, predictions, average="macro")),
        "report": classification_report(y_test, predictions, output_dict=True),
    }

    joblib.dump(
        {"pipeline": pipeline, "classes": list(pipeline.named_steps["classifier"].classes_)},
        ARTIFACTS_DIR / "acute_model.joblib",
    )
    return result


def main() -> None:
    ensure_artifacts_dir()
    disease_result = train_disease_model()
    acute_result = train_acute_model()
    report = {
        "datasets": {
            "healthcare_csv": str(HEALTHCARE_CSV),
            "synthetic_csv": str(SYNTHETIC_CSV),
        },
        "disease_model": disease_result,
        "acute_model": acute_result,
    }
    (ARTIFACTS_DIR / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"disease_model": disease_result, "acute_model": acute_result}, indent=2))


if __name__ == "__main__":
    main()
