import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, BookOpen } from 'lucide-react';
import Button from '../components/Button';

function EvidenceCard({ item }) {
  const confidencePct = item.confidence != null ? Math.round(item.confidence * 100) : null;

  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/15 flex items-center justify-center flex-shrink-0">
          <FileText size={20} className="text-indigo-400" aria-hidden />
        </div>
        <div className="flex-1">
          <p className="font-semibold text-slate-200">{item.document}</p>
          <p className="text-xs text-slate-500 mt-0.5">Page {item.page}</p>
          <div className="mt-3 bg-white/3 border border-white/8 rounded-xl px-4 py-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">{item.field}</p>
            <p className="text-xl font-extrabold text-white">{item.value}</p>
          </div>
          {confidencePct != null && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Confidence</span>
              <div className="flex-1 h-1.5 bg-white/8 rounded-full overflow-hidden max-w-32">
                <div
                  className={`h-full rounded-full ${confidencePct >= 90 ? 'bg-emerald-400' : confidencePct >= 70 ? 'bg-amber-400' : 'bg-red-400'}`}
                  style={{ width: `${confidencePct}%` }}
                  aria-hidden
                />
              </div>
              <span className={`text-xs font-bold ${confidencePct >= 90 ? 'text-emerald-400' : confidencePct >= 70 ? 'text-amber-400' : 'text-red-400'}`}>
                {confidencePct}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function EvidencePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { check, evidenceItems } = location.state || {};

  if (!check || !evidenceItems) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-slate-500 mb-4">No evidence to display.</p>
          <Button variant="secondary" onClick={() => navigate(-1)}>Go Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      {/* Back */}
      <Button id="back-from-evidence" variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-6">
        <ArrowLeft size={16} aria-hidden /> Back to Results
      </Button>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen size={20} className="text-indigo-400" aria-hidden />
          <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Evidence View</p>
        </div>
        <h1 className="text-3xl font-extrabold text-white" style={{ fontFamily: "'Outfit', sans-serif" }}>
          {check.name}
        </h1>
        <p className="text-slate-400 mt-2">{check.description}</p>
      </div>

      {/* Evidence cards */}
      {evidenceItems.length === 0 ? (
        <div className="glass rounded-2xl p-8 text-center text-slate-500">
          No evidence records available for this check.
        </div>
      ) : (
        <div className="space-y-4" role="list" aria-label="Evidence items">
          <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
            {evidenceItems.length} evidence record{evidenceItems.length !== 1 ? 's' : ''}
          </p>
          {evidenceItems.map((item) => (
            <div key={item.id} role="listitem">
              <EvidenceCard item={item} />
            </div>
          ))}
        </div>
      )}

      {/* Warning about demo */}
      <div className="mt-8 px-4 py-3 rounded-xl bg-white/3 border border-white/8 text-xs text-slate-500">
        Evidence is extracted by the AI backend. Only values the backend has extracted with confidence are shown here.
      </div>
    </div>
  );
}
