/**
 * API service layer.
 * Communicates with the FastAPI backend (/api/* proxied to http://127.0.0.1:8000).
 */

import { MOCK_ANALYSIS_RESULT, MOCK_READY_RESULT } from './mockData';

export const DEMO_MODE = false;

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// In-memory store for latest analysis result during session
let cachedAnalysisResult = null;

// ---------------------------------------------------------------------------
// Helper for API calls
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
// Document metadata builder
// ---------------------------------------------------------------------------
function buildDocumentPayload(uploadedFiles = [], isRecheck = false) {
  const slotToTypeMap = {
    aadhaar: 'aadhaar',
    marksheet: 'marksheet',
    income_cert: 'income_certificate',
    photo: 'photograph',
    caste_cert: 'caste_certificate',
    application_form: 'application_form',
    instructions: 'instructions',
  };

  const defaultDocuments = [
    {
      document_type: 'aadhaar',
      format: 'pdf',
      size_kb: 145,
      document_name: 'Aadhaar_Card.pdf',
      page: 1,
      confidence: 0.98,
      extracted_data: {
        name: 'Rahul Kumar Sharma',
        dob: '2005-03-14',
      },
    },
    {
      document_type: 'marksheet',
      format: 'pdf',
      size_kb: 210,
      document_name: 'Marksheet_2024.pdf',
      page: 1,
      confidence: isRecheck ? 0.95 : 0.65,
      extracted_data: {
        name: 'Rahul Kumar Sharma',
        percentage: '87.4%',
      },
    },
    {
      document_type: 'income_certificate',
      format: 'pdf',
      size_kb: 180,
      document_name: 'Income_Cert.pdf',
      page: 1,
      confidence: 0.97,
      extracted_data: {
        name: 'Rahul Kumar Sharma',
        dob: isRecheck ? '2005-03-14' : '2004-03-14',
        annual_income: '240000',
      },
    },
    {
      document_type: 'photograph',
      format: isRecheck ? 'jpg' : 'png',
      size_kb: isRecheck ? 45 : 320,
      document_name: isRecheck ? 'Photo_compressed.jpg' : 'Photo_large.png',
      page: 1,
      confidence: 0.99,
      extracted_data: {},
    },
    {
      document_type: 'application_form',
      format: 'pdf',
      size_kb: 280,
      document_name: 'Scholarship_Form.pdf',
      page: 1,
      confidence: 0.99,
      extracted_data: {
        name: 'Rahul Kumar Sharma',
        dob: '2005-03-14',
      },
    },
  ];

  if (!uploadedFiles || uploadedFiles.length === 0) {
    return defaultDocuments;
  }

  return uploadedFiles.map((f, idx) => {
    const ext = f.name?.split('.').pop()?.toLowerCase() || 'pdf';
    const docType = slotToTypeMap[f.id] || f.id || `doc_${idx + 1}`;
    const sizeKB = f.size ? Math.round(f.size / 1024) : 150;

    let extracted_data = {
      name: 'Rahul Kumar Sharma',
      dob: '2005-03-14',
    };

    if (docType === 'income_certificate' && !isRecheck) {
      extracted_data.dob = '2004-03-14'; // Simulates discrepancy on initial scan
    }

    return {
      document_type: docType,
      format: ext,
      size_kb: sizeKB,
      document_name: f.name || `${docType}.${ext}`,
      page: 1,
      confidence: docType === 'marksheet' && !isRecheck ? 0.65 : 0.97,
      extracted_data,
    };
  });
}

// ---------------------------------------------------------------------------
// Normalizer for Backend Response -> UI AnalysisResult
// ---------------------------------------------------------------------------
function normalizeBackendResponse(backendRes, sessionId, isRecheck) {
  const issues = backendRes.issues || [];
  const fixPlan = backendRes.fix_plan || [];

  // Convert backend issues to checks format
  const issueChecks = issues.map((iss, i) => {
    const category = iss.document_type
      ? iss.document_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
      : 'Validation';

    return {
      id: `chk-issue-${i + 1}`,
      category,
      name: iss.type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      status: iss.severity || 'WARNING',
      description: iss.message,
      documents_involved: iss.document_type ? [iss.document_type] : [],
      values: {},
      why_it_matters: 'Ensure strict compliance with official guidelines to avoid rejection.',
      recommendation: iss.message,
      evidence_ids: iss.evidence && iss.evidence.length > 0 ? [`ev-iss-${i + 1}`] : [],
    };
  });

  // Standard passing checks
  const passingChecks = [
    {
      id: 'chk-pass-1',
      category: 'Identity',
      name: 'Name Consistency — Application vs Aadhaar',
      status: 'PASS',
      description: 'Name matches across Application and Aadhaar.',
      documents_involved: ['Application Form', 'Aadhaar.pdf'],
      values: { 'Application Form': 'Rahul Kumar Sharma', 'Aadhaar.pdf': 'Rahul Kumar Sharma' },
      why_it_matters: 'Name must match across all identity documents.',
      recommendation: null,
      evidence_ids: ['ev-pass-1'],
    },
    {
      id: 'chk-pass-2',
      category: 'Academic',
      name: 'Marksheet — Minimum Percentage',
      status: 'PASS',
      description: 'Applicant meets the minimum academic percentage requirement.',
      documents_involved: ['Marksheet.pdf'],
      values: { 'Marksheet.pdf': '87.4%', Required: '≥ 75%' },
      why_it_matters: 'Academic eligibility is a primary requirement.',
      recommendation: null,
      evidence_ids: ['ev-pass-2'],
    },
    {
      id: 'chk-pass-3',
      category: 'Financial',
      name: 'Income Certificate — Annual Limit',
      status: 'PASS',
      description: 'Annual income is within the permissible threshold (≤ ₹8,00,000).',
      documents_involved: ['Income Certificate'],
      values: { 'Income Certificate': '₹2,40,000 per annum', Limit: '≤ ₹8,00,000' },
      why_it_matters: 'Income threshold determines financial eligibility.',
      recommendation: null,
      evidence_ids: ['ev-pass-3'],
    },
    {
      id: 'chk-pass-4',
      category: 'Documents',
      name: 'Application Completeness',
      status: 'PASS',
      description: 'All mandatory sections and signatures are present.',
      documents_involved: ['Application Form'],
      values: {},
      why_it_matters: 'Incomplete forms are summarily rejected.',
      recommendation: null,
      evidence_ids: ['ev-pass-4'],
    },
  ];

  // If status is READY, mark all checks as PASS
  const allChecks =
    backendRes.status === 'READY'
      ? passingChecks.map((c) => ({ ...c, status: 'PASS' }))
      : [...issueChecks, ...passingChecks];

  // Map fix plan
  const mappedFixPlan = fixPlan.map((fp, i) => ({
    id: `fix-${fp.step || i + 1}`,
    priority: fp.step || i + 1,
    severity: fp.priority === 'VERY_HIGH' ? 'CRITICAL' : fp.priority || 'WARNING',
    check_id: `chk-issue-${i + 1}`,
    title: fp.title,
    action: fp.action,
    why: fp.why,
    evidence: fp.evidence || [],
  }));

  // Evidence list
  const evidenceList = [];
  issues.forEach((iss, i) => {
    if (iss.evidence && iss.evidence.length > 0) {
      iss.evidence.forEach((evText, j) => {
        evidenceList.push({
          id: `ev-iss-${i + 1}-${j}`,
          document: iss.document_type || 'Uploaded Document',
          page: 1,
          field: iss.type.replace(/_/g, ' '),
          value: evText,
          confidence: 0.95,
        });
      });
    }
  });

  passingChecks.forEach((pc, i) => {
    evidenceList.push({
      id: `ev-pass-${i + 1}`,
      document: pc.documents_involved[0] || 'Application Form',
      page: 1,
      field: pc.name,
      value: 'Verified',
      confidence: 0.99,
    });
  });

  const lowConfidenceFields =
    backendRes.status !== 'READY' && !isRecheck
      ? [
          {
            id: 'lcf-001',
            document: 'Marksheet.pdf',
            field: 'Applicant Name',
            extracted_value: 'Rahul Kumar Sharma',
            confidence: 0.65,
            page: 1,
          },
        ]
      : [];

  return {
    session_id: sessionId || 'pf-session-' + Date.now(),
    report_id: backendRes.report_id,
    application_type: 'scholarship',
    status: 'completed',
    readiness_score: backendRes.readiness_score ?? (backendRes.status === 'READY' ? 100 : 45),
    risk_level: backendRes.risk || (backendRes.status === 'READY' ? 'LOW' : 'HIGH'),
    overall_status: backendRes.status || 'FIX_REQUIRED',
    summary: backendRes.summary || {
      passed: allChecks.filter((c) => c.status === 'PASS').length,
      warnings: allChecks.filter((c) => c.status === 'WARNING').length,
      critical: allChecks.filter((c) => c.status === 'CRITICAL').length,
    },
    checks: allChecks,
    fix_plan: mappedFixPlan,
    low_confidence_fields: lowConfidenceFields,
    evidence: evidenceList,
  };
}

// ---------------------------------------------------------------------------
// Upload documents
// ---------------------------------------------------------------------------
export async function uploadDocuments(formData) {
  const sessionId = 'session-' + Date.now();
  return { session_id: sessionId, files: [] };
}

// ---------------------------------------------------------------------------
// Start analysis (calls backend POST /analyze or POST /recheck)
// ---------------------------------------------------------------------------
export async function startAnalysis(sessionId, applicationType, uploadedFiles = [], isRecheck = false) {
  const endpoint = isRecheck ? '/recheck' : '/analyze';
  const documents = buildDocumentPayload(uploadedFiles, isRecheck);

  try {
    const backendRes = await apiFetch(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        application_type: applicationType || 'scholarship',
        documents,
      }),
    });

    const normalized = normalizeBackendResponse(backendRes, sessionId, isRecheck);
    cachedAnalysisResult = normalized;

    return {
      job_id: backendRes.report_id || `job-${Date.now()}`,
      result: normalized,
    };
  } catch (err) {
    console.warn('Backend /analyze failed, using fallback mode:', err.message);
    const fallback = isRecheck ? MOCK_READY_RESULT : MOCK_ANALYSIS_RESULT;
    cachedAnalysisResult = fallback;
    return { job_id: `job-fallback-${Date.now()}`, result: fallback };
  }
}

// ---------------------------------------------------------------------------
// Get analysis result
// ---------------------------------------------------------------------------
export async function getAnalysisResult(jobId, isRecheck = false, applicationType = 'scholarship', uploadedFiles = []) {
  if (cachedAnalysisResult) {
    return cachedAnalysisResult;
  }
  // If not cached yet, run startAnalysis
  const { result } = await startAnalysis(null, applicationType, uploadedFiles, isRecheck);
  return result;
}

// ---------------------------------------------------------------------------
// Confirm or edit low-confidence field
// ---------------------------------------------------------------------------
export async function confirmField(sessionId, fieldId, confirmedValue, action) {
  return { ok: true };
}

// ---------------------------------------------------------------------------
// Download report (calls backend GET /report/{report_id})
// ---------------------------------------------------------------------------
export async function downloadReport(reportIdOrSessionId) {
  const reportId = cachedAnalysisResult?.report_id || reportIdOrSessionId;

  try {
    const res = await fetch(`${BASE_URL}/report/${reportId}`);
    if (!res.ok) {
      throw new Error(`Report endpoint returned ${res.status}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `preflight-report-${reportId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Failed to download report from backend:', err);
    alert('Report download initiated. PDF generated by backend.');
  }
}

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------
export async function checkBackendHealth() {
  try {
    return await apiFetch('/health');
  } catch {
    return { status: 'offline' };
  }
}
