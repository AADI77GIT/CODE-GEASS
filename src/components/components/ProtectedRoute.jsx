import { Navigate } from "react-router-dom";
import { getStoredAuth } from "../lib/auth";

export default function ProtectedRoute({ children, role }) {
  const auth = getStoredAuth();

  if (!auth) {
    return <Navigate to="/" replace />;
  }

  if (role && auth.role !== role) {
    return <Navigate to="/" replace />;
  }

  return children;
}
