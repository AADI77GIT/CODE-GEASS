
# MediTrack AI

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Node](https://img.shields.io/badge/Node.js-20+-green)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React-61DAFB)
![License](https://img.shields.io/badge/License-MIT-yellow)

**MediTrack AI** is a full-stack telemedicine prototype that leverages **Machine Learning + Generative AI** to provide intelligent patient monitoring, diagnosis assistance, and longitudinal health summaries.
##  Features

**ML-based Disease Prediction**

  * Symptoms-based classification
  * Vitals-based risk analysis

**AI-Powered Summaries**

  * Longitudinal patient insights using Gemini API

**Patient Management**

  * Track history, reports, and consultations

  **Full Stack Architecture**

  * FastAPI backend
  * React + Vite frontend
  * 
Project Structure

MediTrack-AI/
│
├── app/                # FastAPI backend
├── src/                # React frontend
├── ml/                 # ML models & training scripts
├── data/               # Dataset files
├── .env.example
├── .env
├── requirements.txt
├── docker-compose.yml
└── README.md


##  Prerequisites

Make sure you have:

* **Node.js 20+**
* **Python 3.11+**

---

## 🔐 Environment Setup

Create your `.env` file:

```bash
cp .env.example .env
```

Add your Gemini API key:

```env
GEMINI_API_KEY=your_key_from_aistudio.google.com
```

---

## 🧠 Machine Learning Setup

### 1. Add Dataset Files

Place these files in the `data/` folder:

* `Testing.csv`
* `Diseases_Symptoms.csv`
* `synthetic_medical_symptoms_dataset.csv`

---

### 2. Install Dependencies

```bash
pip install scikit-learn pandas numpy joblib reportlab google-generativeai
```

---

### 3. Train Models

```bash
python ml/train_model.py
```

### ✅ Expected Output

* Model A (Vitals): **~0.92 ± 0.03 accuracy**
* Model B (Symptoms): **~0.95 accuracy**
* Knowledge base: **400 diseases**
* Models saved in `ml/`

---

## ▶️ Running Locally (Without Docker)

### Backend

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python ml\train_model.py
uvicorn app.main:app --reload --reload-dir app --port 8000
```

---

### Frontend

```powershell
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

---

### 🌍 Access URLs

* Frontend: [http://127.0.0.1:3000](http://127.0.0.1:3000)
* API Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🐳 Running with Docker

```powershell
docker compose up --build
```

---

## 🔗 API Endpoints

### 📊 Machine Learning

* `POST /ml-predict`

### 👤 Patient

* `GET /patients/{patient_id}`
* `GET /report/{patient_id}`

### 🩺 Consultations

* `GET /consultations/{patient_id}`
* `POST /consultations`

### 🤖 AI

* `GET /ai-summary/{patient_id}`

---

## 📸 Demo (Optional)

> Add screenshots or demo GIFs here for better presentation

```
![App Screenshot](./assets/demo.png)
```

---

## 🧩 Tech Stack

* **Backend:** FastAPI
* **Frontend:** React + Vite
* **ML:** Scikit-learn
* **AI:** Google Gemini API
* **Deployment:** Docker
