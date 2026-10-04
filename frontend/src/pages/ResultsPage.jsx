import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2, AlertTriangle, ChevronDown, ChevronUp,
  Download, RefreshCw, Eye
} from 'lucide-react';
import Button from '../components/Button';
import StatusBadge from '../components/StatusBadge';
import { usePreFlight } from '../context/PreFlightContext';
import { downloadReport, confirmField } from '../api/apiService';

// ---------------------------------------------------------------------------
// Readiness gauge
// ---------------------------------------------------------------------------
function ReadinessGauge({ score }) {
  const radius = 52;
  const circ = 2 * Math.PI * radius;
  const strokeDash = (score / 100) * circ;
  const color = score >= 80 ? '#34d399' : score >= 50 ? '#fb923c' : '#f87171';

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="130" height="130" className="-rotate-90" aria-hidden="true">
        <circle cx="65" cy="65" r={radius} fill="none" stroke="var(--border-medium)" strokeWidth="10" />
        <circle
          cx="65" cy="65" r={radius} fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={`${strokeDash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.8s ease', filter: `drop-shadow(0 0 6px ${color}80)` }}
        />
      </svg>
      <div className="absolute text-center">
        <span className="text-3xl font-extrabold" style={{ color: 'var(--text-primary)' }}>{score}%</span>
        <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Readiness</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Issue card
// ---------------------------------------------------------------------------
function IssueCard({ check, onViewEvidence }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`glass rounded-2xl overflow-hidden transition-all
      ${check.status === 'CRITICAL' ? 'border-red-500/25' : check.status === 'WARNING' ? 'border-amber-500/25' : 'border-emerald-500/15'}`}>
      <button
        id={`issue-${check.id}`}
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-start gap-4 p-5 text-left cursor-pointer hover:bg-white/5 transition-colors"
        aria-expanded={expanded}
        aria-controls={`issue-body-${check.id}`}
      >
        <StatusBadge status={check.status} showLabel={false} size="md" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{check.category}</span>
          </div>
          <p className="font-semibold mt-0.5" style={{ color: 'var(--text-primary)' }}>{check.name}</p>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>{check.description}</p>
        </div>
        <StatusBadge status={check.status} size="sm" />
        {expanded ? <ChevronUp size={16} className="flex-shrink-0 mt-1" style={{ color: 'var(--text-muted)' }} aria-hidden /> : <ChevronDown size={16} className="flex-shrink-0 mt-1" style={{ color: 'var(--text-muted)' }} aria-hidden />}
      </button>

      {expanded && (
        <div id={`issue-body-${check.id}`} className="px-5 pb-5 border-t border-subtle pt-4 space-y-4">
          {/* Values */}
          {Object.keys(check.values).length > 0 && (
            <div>
              <p className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>Extracted Values</p>
              <div className="flex flex-wrap gap-3">
                {Object.entries(check.values).map(([doc, val]) => (
                  <div key={doc} className="glass rounded-lg px-3 py-2">
                    <p className="text-[11px] font-semibold" style={{ color: 'var(--text-muted)' }}>{doc}</p>
                    <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{val}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Documents */}
          {check.documents_involved.length > 0 && (
            <div>
              <p className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>Documents Involved</p>
              <div className="flex flex-wrap gap-2">
                {check.documents_involved.map((doc) => (
                  <span key={doc} className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-medium">
                    {doc}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Why it matters */}
          {check.why_it_matters && (
            <div className="bg-amber-500/5 border border-amber-500/15 rounded-xl px-4 py-3">
              <p className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-1">Why it matters</p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{check.why_it_matters}</p>
            </div>
          )}

          {/* Recommendation */}
          {check.recommendation && (
            <div className="bg-indigo-500/5 border border-indigo-500/15 rounded-xl px-4 py-3">
              <p className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">Recommended Action</p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{check.recommendation}</p>
            </div>
          )}

          {/* Evidence button */}
          {check.evidence_ids.length > 0 && (
            <Button
              id={`view-evidence-${check.id}`}
              variant="secondary"
              size="sm"
              onClick={() => onViewEvidence(check)}
            >
              <Eye size={14} aria-hidden /> View Evidence
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Confirmation card (low-confidence field)
// ---------------------------------------------------------------------------
function ConfirmationCard({ field, sessionId }) {
  const [status, setStatus] = useState('pending'); // 'pending'|'confirmed'|'editing'|'done'
  const [editValue, setEditValue] = useState(field.extracted_value);

  async function handleConfirm() {
    setStatus('confirmed');
    await confirmField(sessionId, field.id, field.extracted_value, 'confirm');
    setStatus('done');
  }

  async function handleSaveEdit() {
    await confirmField(sessionId, field.id, editValue, 'edit');
    setStatus('done');
  }

  const confidencePct = Math.round(field.confidence * 100);

  return (
    <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>{field.document} · Page {field.page} · {field.field}</p>
          {status === 'editing' ? (
            <input
              id={`edit-field-${field.id}`}
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              className="mt-1 glass rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-indigo-500 w-64"
              style={{ color: 'var(--text-primary)' }}
              aria-label={`Edit extracted value for ${field.field}`}
            />
          ) : (
            <p className="text-lg font-bold mt-1" style={{ color: 'var(--text-primary)' }}>{field.extracted_value}</p>
          )}
          <p className="text-xs mt-1">
            <span className={`font-bold ${confidencePct < 70 ? 'text-amber-400' : 'text-emerald-400'}`}>
              Confidence: {confidencePct}%
            </span>
          </p>
        </div>
        {status === 'done' ? (
          <span className="text-emerald-400 text-sm font-semibold flex items-center gap-1">
            <CheckCircle2 size={14} aria-hidden /> Confirmed
          </span>
        ) : status === 'editing' ? (
          <div className="flex gap-2">
            <Button id={`save-edit-${field.id}`} variant="primary" size="sm" onClick={handleSaveEdit}>Save</Button>
            <Button id={`cancel-edit-${field.id}`} variant="ghost" size="sm" onClick={() => setStatus('pending')}>Cancel</Button>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button id={`confirm-field-${field.id}`} variant="primary" size="sm" onClick={handleConfirm}>Confirm</Button>
            <Button id={`edit-field-btn-${field.id}`} variant="secondary" size="sm" onClick={() => setStatus('editing')}>Edit</Button>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main results page
// ---------------------------------------------------------------------------
export default function ResultsPage() {
  const navigate = useNavigate();
  const { state, dispatch } = usePreFlight();
  const result = state.analysisResult;

  const [downloading, setDownloading] = useState(false);

  if (!result) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p style={{ color: 'var(--text-muted)' }}>No results yet. <button className="text-indigo-400 underline cursor-pointer" onClick={() => navigate('/')}>Start over</button></p>
      </div>
    );
  }

  const isReady = result.overall_status === 'READY';
  const issues = result.checks.filter(c => c.status !== 'PASS');
  const passed = result.checks.filter(c => c.status === 'PASS');

  function handleViewEvidence(check) {
    const evidenceItems = result.evidence.filter(e => check.evidence_ids.includes(e.id));
    navigate('/evidence', { state: { check, evidenceItems } });
  }

  function handleRecheck() {
    dispatch({ type: 'SET_IS_RECHECK', payload: true });
    navigate('/analyzing');
  }

  async function handleDownload() {
    setDownloading(true);
    try {
      await downloadReport(state.sessionId);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12">

      {/* ── Status banner ── */}
      <div className={`glass rounded-3xl p-8 mb-8 text-center relative overflow-hidden
        ${isReady ? 'border-emerald-500/25 glow-success' : 'border-red-500/25 glow-danger'}`}>
        <div className={`absolute inset-0 opacity-5 pointer-events-none ${isReady ? 'bg-emerald-400' : 'bg-red-400'}`} />

        {state.isRecheck && (
          <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-3">
            ✓ Recheck Complete
          </p>
        )}

        <div className="text-5xl mb-3" aria-hidden>{isReady ? '🟢' : '🔴'}</div>
        <h1 className={`text-4xl font-extrabold mb-1 ${isReady ? 'gradient-success-text' : 'gradient-danger-text'}`}
            style={{ fontFamily: "'Outfit', sans-serif" }}>
          {isReady ? 'READY TO SUBMIT' : 'FIX REQUIRED'}
        </h1>
        <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>
          {isReady
            ? 'Ready to submit based on the checks performed. This does not guarantee approval.'
            : 'Your application has issues that need to be resolved before submission.'}
        </p>

        {/* Metrics row */}
        <div className="flex flex-wrap items-center justify-center gap-8">
          <ReadinessGauge score={result.readiness_score} />
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="glass rounded-xl p-4">
              <p className="text-2xl font-extrabold text-emerald-400">{result.summary.passed}</p>
              <p className="text-xs font-semibold mt-0.5" style={{ color: 'var(--text-muted)' }}>Passed</p>
            </div>
            <div className="glass rounded-xl p-4">
              <p className="text-2xl font-extrabold text-amber-400">{result.summary.warnings}</p>
              <p className="text-xs font-semibold mt-0.5" style={{ color: 'var(--text-muted)' }}>Warning</p>
            </div>
            <div className="glass rounded-xl p-4">
              <p className="text-2xl font-extrabold text-red-400">{result.summary.critical}</p>
              <p className="text-xs font-semibold mt-0.5" style={{ color: 'var(--text-muted)' }}>Critical</p>
            </div>
          </div>
          <div className="glass rounded-xl p-4 text-center">
            <p className={`text-xl font-extrabold ${result.risk_level === 'LOW' ? 'text-emerald-400' : result.risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-red-400'}`}>
              {result.risk_level}
            </p>
            <p className="text-xs font-semibold mt-0.5" style={{ color: 'var(--text-muted)' }}>Risk</p>
          </div>
        </div>
      </div>

      {/* ── Human confirmation section ── */}
      {result.low_confidence_fields?.length > 0 && (
        <div className="glass rounded-2xl p-6 mb-8 border-amber-500/25">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={18} className="text-amber-400" aria-hidden />
            <h2 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>Please verify these fields</h2>
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
            The AI extracted the following with low confidence. Please confirm or correct them.
          </p>
          <div className="space-y-3">
            {result.low_confidence_fields.map((field) => (
              <ConfirmationCard key={field.id} field={field} sessionId={state.sessionId} />
            ))}
          </div>
        </div>
      )}

      {/* ── Fix plan ── */}
      {result.fix_plan.length > 0 && (
        <section className="mb-8" aria-labelledby="fix-plan-heading">
          <h2 id="fix-plan-heading" className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <span aria-hidden>🛠️</span> Your Fix Plan
          </h2>
          <div className="space-y-3">
            {result.fix_plan.map((item) => {
              const emoji = item.severity === 'CRITICAL' ? '🔴' : item.severity === 'WARNING' ? '🟠' : '🟡';
              return (
                <div key={item.id} id={`fix-${item.id}`} className="glass glass-hover rounded-2xl p-5 flex items-start gap-4">
                  <span className="text-xl flex-shrink-0 mt-0.5" aria-hidden>{emoji}</span>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>Priority {item.priority}</span>
                      <StatusBadge status={item.severity} size="sm" />
                    </div>
                    <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{item.title}</p>
                    <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{item.action}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* ── Issues ── */}
      {issues.length > 0 && (
        <section className="mb-8" aria-labelledby="issues-heading">
          <h2 id="issues-heading" className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
            Issues ({issues.length})
          </h2>
          <div className="space-y-3">
            {issues.map((check) => (
              <IssueCard key={check.id} check={check} onViewEvidence={handleViewEvidence} />
            ))}
          </div>
        </section>
      )}

      {/* ── Passed checks ── */}
      {passed.length > 0 && (
        <section className="mb-8" aria-labelledby="passed-heading">
          <h2 id="passed-heading" className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <CheckCircle2 size={20} className="text-emerald-400" aria-hidden /> Passed Checks ({passed.length})
          </h2>
          <div className="space-y-2">
            {passed.map((check) => (
              <div key={check.id} className="glass rounded-xl px-4 py-3 flex items-center gap-3">
                <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" aria-hidden />
                <div>
                  <span className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>{check.category} · </span>
                  <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>{check.name}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Actions ── */}
      <div className="flex flex-wrap gap-3 pt-4 border-t border-subtle">
        {!isReady && (
          <Button id="recheck-btn" variant="primary" size="lg" onClick={handleRecheck}>
            <RefreshCw size={16} aria-hidden /> Run PreFlight Again
          </Button>
        )}
        <Button id="download-report-btn" variant="secondary" size="lg" loading={downloading} onClick={handleDownload}>
          <Download size={16} aria-hidden /> Download Report
        </Button>
        <Button id="start-over-btn" variant="ghost" size="lg" onClick={() => { dispatch({ type: 'RESET' }); navigate('/'); }}>
          Start Over
        </Button>
      </div>
    </div>
  );
}
