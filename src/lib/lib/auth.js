const AUTH_KEY = "meditrack_auth";

export function getStoredAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.log("Auth parse failed", error);
    return null;
  }
}

export function setStoredAuth(value) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(value));
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_KEY);
}
