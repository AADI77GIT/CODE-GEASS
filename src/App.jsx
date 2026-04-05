import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import DoctorDashboard from "./pages/DoctorDashboard";
import LandingPage from "./pages/LandingPage";
import NewConsultation from "./pages/NewConsultation";
import PatientPortal from "./pages/PatientPortal";
import SymptomChecker from "./pages/SymptomChecker";
import DoctorLogin from "./pages/auth/DoctorLogin";
import DoctorSignup from "./pages/auth/DoctorSignup";
import PatientLogin from "./pages/auth/PatientLogin";
import PatientSignup from "./pages/auth/PatientSignup";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/doctor/login" element={<DoctorLogin />} />
      <Route path="/doctor/signup" element={<DoctorSignup />} />
      <Route
        path="/doctor/dashboard"
        element={
          <ProtectedRoute role="doctor">
            <DoctorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/consult/:patientId"
        element={
          <ProtectedRoute role="doctor">
            <NewConsultation />
          </ProtectedRoute>
        }
      />
      <Route path="/patient/login" element={<PatientLogin />} />
      <Route path="/patient/signup" element={<PatientSignup />} />
      <Route
        path="/patient/portal"
        element={
          <ProtectedRoute role="patient">
            <PatientPortal />
          </ProtectedRoute>
        }
      />
      <Route path="/symptom-checker" element={<SymptomChecker />} />
      <Route path="/patient" element={<Navigate to="/patient/portal" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
