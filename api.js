// ALL backend calls live here. Replace the endpoints to match your app.py.
const API_BASE_URL = "http://127.0.0.1:8000";          // Updated to connect to FastAPI
const USE_MOCK = false;            // Set to false to use the real model

// Expected response: { label: "fake" | "real", confidence: number|null }  (confidence 0-100 or 0-1, optional)
async function callApi(path, payload) {
  const res = await fetch(API_BASE_URL + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = "Server error (" + res.status + ").";
    try { const e = await res.json(); if (e.detail || e.error) msg = e.detail || e.error; } catch (_) {}
    const err = new Error(msg); err.status = res.status; throw err;
  }
  return res.json();
}

// MOCK - replace with real endpoint. Demo only, not a real prediction.
function mockResponse() {
  return new Promise((resolve) =>
    setTimeout(() => resolve({ label: Math.random() > 0.5 ? "fake" : "real", confidence: null, mock: true }), 1200)
  );
}

async function analyzeText(text, language) {
  if (USE_MOCK) return mockResponse();
  return callApi("/api/analyze-text", { text, language });
}

async function analyzeUrl(url, language) {
  if (USE_MOCK) return mockResponse();
  return callApi("/api/analyze-url", { url, language });
}