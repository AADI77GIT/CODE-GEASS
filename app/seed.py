import json
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Consultation, Patient


def seed_demo_data(db: Session) -> None:
    demo_payloads = [
        {
            "patient": {
                "name": "Riya Sharma",
                "age": 34,
                "gender": "Female",
                "phone": "9876543210",
                "blood_group": "B+",
            },
            "consultations": [
                {
                    "days_ago": 120,
                    "notes": "Patient reports intermittent dry cough and mild wheeze for one week. No fever. Advised steam inhalation and rescue inhaler use.",
                    "ai_summary": {
                        "symptoms": ["dry cough", "mild wheeze"],
                        "diagnosis_impression": "Doctor noted a possible mild reactive airway episode.",
                        "medications_prescribed": [{"name": "Salbutamol inhaler", "dosage": "2 puffs as needed", "duration": "7 days"}],
                        "tests_ordered": [],
                        "visit_summary": "Patient reported a mild respiratory flare with dry cough and wheeze. Conservative management with inhaler support was advised.",
                        "flags": ["Respiratory symptoms recurring intermittently"],
                        "cumulative_patient_summary": "The patient has had mild respiratory complaints over multiple telemedicine visits. Symptoms have generally responded to conservative treatment and have not shown severe red flags so far.",
                        "context_suggestions": ["Compare future cough episodes with this baseline respiratory visit."],
                        "risk_level": "low",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
                {
                    "days_ago": 75,
                    "notes": "Follow-up for cough. Improved overall but still reports night-time cough twice this week. No shortness of breath. Discussed allergen avoidance.",
                    "ai_summary": {
                        "symptoms": ["night-time cough"],
                        "diagnosis_impression": "Doctor noted improving cough with a possible allergy-triggered pattern.",
                        "medications_prescribed": [{"name": "Cetirizine", "dosage": "10 mg once daily", "duration": "10 days"}],
                        "tests_ordered": [],
                        "visit_summary": "Respiratory symptoms improved since the previous visit, though occasional night-time cough persists. Allergy control strategies were added.",
                        "flags": ["Cough persists from prior visit"],
                        "cumulative_patient_summary": "The patient shows a recurring pattern of mild respiratory and likely allergy-related symptoms across visits. Symptom burden has improved with conservative treatment, though cough continues intermittently.",
                        "context_suggestions": ["Patient had similar cough in the earlier respiratory visit; compare trigger exposure."],
                        "risk_level": "moderate",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
                {
                    "days_ago": 30,
                    "notes": "Reports fatigue, poor sleep, and headache for 5 days during a stressful work period. Hydration low. No visual symptoms or vomiting.",
                    "ai_summary": {
                        "symptoms": ["fatigue", "poor sleep", "headache"],
                        "diagnosis_impression": "Doctor noted a possible tension headache and fatigue pattern related to stress and sleep disruption.",
                        "medications_prescribed": [{"name": "Paracetamol", "dosage": "500 mg as needed", "duration": "3 days"}],
                        "tests_ordered": ["Basic blood work if fatigue persists"],
                        "visit_summary": "This visit focused on fatigue and headache likely linked to stress and inadequate rest. No acute neurological red flags were described.",
                        "flags": ["New non-respiratory symptom cluster", "Review if fatigue continues"],
                        "cumulative_patient_summary": "Across visits, the patient has had recurrent respiratory complaints and a later stress-related episode of fatigue and headache. Symptoms have remained low acuity overall.",
                        "context_suggestions": ["Track whether fatigue persists independently of respiratory follow-ups."],
                        "risk_level": "moderate",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
                {
                    "days_ago": 14,
                    "notes": "Follow-up for persistent fatigue and cough. Patient reports fatigue improving slightly but still present. Night cough persists. Prescribed Montelukast 10mg for possible allergic component. Referred for spirometry.",
                    "ai_summary": {
                        "symptoms": ["fatigue", "night cough"],
                        "diagnosis_impression": "Doctor noted persistent cough with a possible allergic component and slowly improving fatigue.",
                        "medications_prescribed": [{"name": "Montelukast", "dosage": "10 mg once daily", "duration": "14 days"}],
                        "tests_ordered": ["Spirometry"],
                        "visit_summary": "Patient followed up for persistent fatigue and cough, with fatigue improving slightly but night cough still present. Montelukast was prescribed and spirometry referral was planned.",
                        "flags": ["Cough recurring across multiple visits", "Fatigue persisted across follow-up visits"],
                        "cumulative_patient_summary": "Riya Sharma has had a longitudinal pattern of respiratory complaints with intermittent cough and wheeze, later followed by fatigue and headache during a stress-related period. The latest visit suggests persistent night cough with a possible allergic component. Overall acuity remains moderate because symptoms are recurring rather than rapidly worsening.",
                        "context_suggestions": [
                            "Patient had similar cough in earlier visits; compare this visit with the allergy-oriented follow-up.",
                            "If fatigue persists after respiratory symptoms settle, review sleep and blood work trends."
                        ],
                        "risk_level": "moderate",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
            ],
        },
        {
            "patient": {
                "name": "Arjun Mehta",
                "age": 45,
                "gender": "Male",
                "phone": "9123456789",
                "blood_group": "O+",
            },
            "consultations": [
                {
                    "days_ago": 90,
                    "notes": "Hypertension diagnosis. BP 155/95. Started Amlodipine 5mg.",
                    "ai_summary": {
                        "symptoms": ["elevated blood pressure"],
                        "diagnosis_impression": "Doctor noted hypertension based on reported blood pressure readings.",
                        "medications_prescribed": [{"name": "Amlodipine", "dosage": "5 mg once daily", "duration": "Ongoing"}],
                        "tests_ordered": [],
                        "visit_summary": "Initial visit documented elevated blood pressure and a new hypertension diagnosis. Amlodipine 5 mg was started.",
                        "flags": ["High blood pressure requires longitudinal tracking"],
                        "cumulative_patient_summary": "Arjun Mehta's recorded history begins with hypertension management and medication initiation. Blood pressure monitoring is the main longitudinal theme in his early visits.",
                        "context_suggestions": ["Track blood pressure response after starting Amlodipine."],
                        "risk_level": "moderate",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
                {
                    "days_ago": 60,
                    "notes": "Diabetes screening visit. Blood sugar 185. Started Metformin.",
                    "ai_summary": {
                        "symptoms": ["elevated blood sugar"],
                        "diagnosis_impression": "Doctor noted elevated blood sugar and started diabetes management.",
                        "medications_prescribed": [{"name": "Metformin", "dosage": "500 mg twice daily", "duration": "Ongoing"}],
                        "tests_ordered": ["Fasting blood sugar"],
                        "visit_summary": "Screening visit identified elevated blood sugar and diabetes treatment was started with Metformin.",
                        "flags": ["Metabolic risk factors now span blood pressure and blood sugar"],
                        "cumulative_patient_summary": "The patient's longitudinal record now includes both hypertension and elevated blood sugar requiring medication-based management. Cardiometabolic follow-up became the main focus after the second visit.",
                        "context_suggestions": ["Coordinate blood pressure and glucose follow-up rather than tracking them separately."],
                        "risk_level": "moderate",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
                {
                    "days_ago": 30,
                    "notes": "BP controlled 135/85. Fatigue reported. HbA1c 7.8%.",
                    "ai_summary": {
                        "symptoms": ["fatigue"],
                        "diagnosis_impression": "Doctor noted improved blood pressure control with ongoing diabetes follow-up and reported fatigue.",
                        "medications_prescribed": [
                            {"name": "Amlodipine", "dosage": "5 mg once daily", "duration": "Continue"},
                            {"name": "Metformin", "dosage": "500 mg twice daily", "duration": "Continue"}
                        ],
                        "tests_ordered": ["HbA1c"],
                        "visit_summary": "Blood pressure appeared more controlled at this follow-up, but fatigue was reported and HbA1c remained elevated at 7.8%.",
                        "flags": ["Cardiometabolic monitoring remains active", "Fatigue should be reviewed if persistent"],
                        "cumulative_patient_summary": "Arjun Mehta's record shows parallel management of hypertension and diabetes risk. Blood pressure control improved, though glycemic control and fatigue still require ongoing review.",
                        "context_suggestions": ["Compare fatigue with diabetes control and medication adherence trends."],
                        "risk_level": "moderate",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
                {
                    "days_ago": 14,
                    "notes": "Chest tightness reported. ECG ordered. Referred to cardiologist.",
                    "ai_summary": {
                        "symptoms": ["chest tightness"],
                        "diagnosis_impression": "Doctor noted chest tightness requiring cardiac evaluation rather than definitive diagnosis.",
                        "medications_prescribed": [
                            {"name": "Amlodipine", "dosage": "5 mg once daily", "duration": "Continue"},
                            {"name": "Metformin", "dosage": "500 mg twice daily", "duration": "Continue"}
                        ],
                        "tests_ordered": ["ECG"],
                        "visit_summary": "The latest visit focused on chest tightness in a patient with cardiometabolic risk factors. ECG was ordered and cardiology referral was advised.",
                        "flags": ["Chest symptoms are new and higher priority", "Hypertension and diabetes history elevate context risk"],
                        "cumulative_patient_summary": "Arjun Mehta has a longitudinal record of hypertension and diabetes follow-up, with improving blood pressure control but persistent metabolic monitoring needs. The most recent visit introduced chest tightness, which raises the urgency of cardiac review in the context of existing cardiometabolic risk factors.",
                        "context_suggestions": [
                            "Because of prior hypertension and diabetes-related visits, chest tightness should be compared against broader cardiovascular risk.",
                            "Review ECG results alongside blood pressure and HbA1c follow-up."
                        ],
                        "risk_level": "high",
                        "pipeline_steps": [
                            {"name": "Step 1: Entities extracted", "success": True, "message": "Seeded data"},
                            {"name": "Step 2: Visit summarized", "success": True, "message": "Seeded data"},
                            {"name": "Step 3: History updated", "success": True, "message": "Seeded data"},
                        ],
                    },
                },
            ],
        },
    ]

    for payload in demo_payloads:
        patient_data = payload["patient"]
        patient = db.query(Patient).filter(Patient.name == patient_data["name"]).first()
        if not patient:
            patient = Patient(**patient_data)
            db.add(patient)
            db.flush()
        else:
            patient.age = patient_data["age"]
            patient.gender = patient_data["gender"]
            patient.phone = patient_data["phone"]
            patient.blood_group = patient_data["blood_group"]

        for consultation_payload in payload["consultations"]:
            consult_date = date.today() - timedelta(days=consultation_payload["days_ago"])
            existing = (
                db.query(Consultation)
                .filter(Consultation.patient_id == patient.id, Consultation.date == consult_date)
                .first()
            )
            if existing:
                existing.raw_notes = consultation_payload["notes"]
                existing.ai_summary = json.dumps(consultation_payload["ai_summary"])
                continue

            db.add(
                Consultation(
                    patient_id=patient.id,
                    date=consult_date,
                    raw_notes=consultation_payload["notes"],
                    ai_summary=json.dumps(consultation_payload["ai_summary"]),
                )
            )

    db.commit()
