/**
 * API service layer.
 * All backend communication goes through this file.
 * Toggle DEMO_MODE to switch between mock data and real API calls.
 *
 * DO NOT store API secrets here. Use environment variables via import.meta.env.
 */

import { MOCK_ANALYSIS_RESULT, MOCK_READY_RESULT } from './mockData';

/** Set to true to use mock data. Set to false when backend is ready. */
export const DEMO_MODE = true;

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------
async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Upload documents
// POST /api/upload
// Body: FormData with files
// Returns: { session_id, files: [{ name, type, size, status }] }
// ---------------------------------------------------------------------------
export async function uploadDocuments(formData) {
  if (DEMO_MODE) {
    await delay(1200);
    return { session_id: 'demo-session-001', files: [] };
  }
  const res = await fetch(`${BASE_URL}/upload`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Start analysis
// POST /api/analyze
// Body: { session_id, application_type }
// Returns: { job_id }
// ---------------------------------------------------------------------------
export async function startAnalysis(sessionId, applicationType) {
  if (DEMO_MODE) {
    await delay(600);
    return { job_id: 'demo-job-001' };
  }
  return apiFetch('/analyze', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, application_type: applicationType }),
  });
}

// ---------------------------------------------------------------------------
// Poll analysis status
// GET /api/analyze/{job_id}/status
// Returns: { status: "pending"|"running"|"completed"|"failed", progress: 0-100, step: string }
// ---------------------------------------------------------------------------
export async function getAnalysisStatus(jobId) {
  if (DEMO_MODE) {
    // Simulated — caller controls timing
    return { status: 'completed', progress: 100, step: 'Done' };
  }
  return apiFetch(`/analyze/${jobId}/status`);
}

// ---------------------------------------------------------------------------
// Get analysis result
// GET /api/analyze/{job_id}/result
// Returns: AnalysisResult (see mockData.js for full shape)
// ---------------------------------------------------------------------------
export async function getAnalysisResult(jobId, isRecheck = false) {
  if (DEMO_MODE) {
    await delay(400);
    return isRecheck ? MOCK_READY_RESULT : MOCK_ANALYSIS_RESULT;
  }
  return apiFetch(`/analyze/${jobId}/result`);
}

// ---------------------------------------------------------------------------
// Confirm or correct a low-confidence field
// POST /api/confirm-field
// Body: { session_id, field_id, confirmed_value, action: "confirm"|"edit" }
// Returns: { ok: true }
// ---------------------------------------------------------------------------
export async function confirmField(sessionId, fieldId, confirmedValue, action) {
  if (DEMO_MODE) {
    await delay(400);
    return { ok: true };
  }
  return apiFetch('/confirm-field', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, field_id: fieldId, confirmed_value: confirmedValue, action }),
  });
}

// ---------------------------------------------------------------------------
// Recheck
// POST /api/recheck
// Body: { session_id }
// Returns: { job_id }
// ---------------------------------------------------------------------------
export async function requestRecheck(sessionId) {
  if (DEMO_MODE) {
    await delay(600);
    return { job_id: 'demo-recheck-001' };
  }
  return apiFetch('/recheck', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

// ---------------------------------------------------------------------------
// Download report
// GET /api/report/{session_id}
// Returns: PDF blob
// ---------------------------------------------------------------------------
export async function downloadReport(sessionId) {
  if (DEMO_MODE) {
    alert('[Demo Mode] PDF download would be triggered here from the backend.');
    return;
  }
  const res = await fetch(`${BASE_URL}/report/${sessionId}`);
  if (!res.ok) throw new Error(`Report download failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `preflight-report-${sessionId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
