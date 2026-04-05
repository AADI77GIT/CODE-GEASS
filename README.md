# MediTrack AI

MediTrack AI is a telemedicine prototype with:

- a FastAPI backend in `app/`
- a Vite + React frontend in `src/`
- Gemini-powered longitudinal summaries
- local ML models in `ml/`

## Before You Run

You need both runtimes installed and available in your terminal:

- Node.js 20+
- Python 3.11+

Also create a real `.env` file by copying `.env.example`.

## Training the ML Model

1. Place CSV files in `data/`:
   - `Testing.csv`
   - `Diseases_Symptoms.csv`
   - `synthetic_medical_symptoms_dataset.csv`

2. Install dependencies:
   `pip install scikit-learn pandas numpy joblib reportlab google-generativeai`

3. Train the model from the project root:
   `python ml/train_model.py`

4. Expected output:
   - `Model A (Vitals) - CV Accuracy: ~0.92 ± 0.03`
   - `Model B (Symptoms) - LOO Accuracy: ~0.95`
   - `Knowledge base saved: 400 diseases`
   - `All models saved to ml/ folder`

5. Set environment variable:
   `GEMINI_API_KEY=your_key_from_aistudio.google.com`

6. Start backend:
   `uvicorn app.main:app --reload --port 8000`

## Local Run Without Docker

Backend:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python ml\train_model.py
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Frontend:

```powershell
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

Open:

- frontend: `http://127.0.0.1:3000`
- backend docs: `http://127.0.0.1:8000/docs`

## Local Run With Docker

Create `.env` first, then run:

```powershell
docker compose up --build
```

## Key Endpoints

- `POST /ml-predict`
- `GET /report/{patient_id}`
- `GET /patients/{patient_id}`
- `GET /consultations/{patient_id}`
- `POST /consultations`
- `GET /ai-summary/{patient_id}`
