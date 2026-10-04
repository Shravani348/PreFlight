import { useCallback, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload, X, CheckCircle2, AlertCircle, FileText, Image, File, Rocket
} from 'lucide-react';
import Button from '../components/Button';
import { usePreFlight } from '../context/PreFlightContext';
import { uploadDocuments } from '../api/apiService';

const ACCEPTED_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

const REQUIRED_SLOTS = [
  { id: 'application_form', label: 'Application Form', hint: 'PDF', required: true },
  { id: 'aadhaar', label: 'Identity Document (Aadhaar / Passport)', hint: 'PDF or image', required: true },
  { id: 'marksheet', label: 'Marksheet / Academic Certificate', hint: 'PDF', required: true },
  { id: 'income_cert', label: 'Income Certificate', hint: 'PDF', required: false },
  { id: 'caste_cert', label: 'Caste Certificate', hint: 'PDF', required: false },
  { id: 'photo', label: 'Passport Photograph', hint: 'JPEG/PNG, max 50 KB recommended', required: true },
  { id: 'instructions', label: 'Official Instructions / Notification', hint: 'PDF', required: false },
];

function fileIcon(type) {
  if (type?.startsWith('image/')) return Image;
  if (type === 'application/pdf') return FileText;
  return File;
}

function FileRow({ slot, file, onRemove }) {
  const Icon = file ? fileIcon(file.type) : File;
  const sizeKB = file ? (file.size / 1024).toFixed(1) : null;
  const tooLarge = file && file.size > MAX_SIZE_BYTES;

  return (
    <div className={`glass rounded-xl p-4 flex items-center gap-4 transition-all
      ${file ? (tooLarge ? 'border-red-500/30' : 'border-emerald-500/20') : 'border-subtle'}`}>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
        ${file ? (tooLarge ? 'bg-red-500/15' : 'bg-emerald-500/10') : 'bg-white/5'}`}>
        {file
          ? tooLarge
            ? <AlertCircle size={20} className="text-red-400" aria-hidden />
            : <CheckCircle2 size={20} className="text-emerald-400" aria-hidden />
          : <Icon size={20} style={{ color: 'var(--text-muted)' }} aria-hidden />
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{slot.label}</p>
          {slot.required && (
            <span className="text-[10px] font-bold text-red-400 uppercase">Required</span>
          )}
        </div>
        {file ? (
          <p className="text-xs truncate" style={{ color: tooLarge ? '#f87171' : 'var(--text-secondary)' }}>
            {file.name} · {sizeKB} KB
            {tooLarge && ` · Exceeds ${MAX_SIZE_MB} MB limit`}
          </p>
        ) : (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{slot.hint}</p>
        )}
      </div>
      {file ? (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(slot.id); }}
          aria-label={`Remove ${slot.label}`}
          className="hover:text-red-400 transition-colors flex-shrink-0 cursor-pointer p-1"
          style={{ color: 'var(--text-muted)' }}
        >
          <X size={18} aria-hidden />
        </button>
      ) : (
        <span className="text-xs flex-shrink-0" style={{ color: 'var(--text-muted)' }}>— Not uploaded</span>
      )}
    </div>
  );
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { state, dispatch } = usePreFlight();
  const [slotFiles, setSlotFiles] = useState({});  // { slot_id: File }
  const [activeSlot, setActiveSlot] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const requiredFilled = REQUIRED_SLOTS.filter(s => s.required).every(s => slotFiles[s.id]);
  const hasFiles = Object.keys(slotFiles).length > 0;

  function openFilePicker(slotId) {
    setActiveSlot(slotId);
    fileInputRef.current?.click();
  }

  function validateFile(file) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return `Unsupported file type. Please upload PDF, JPEG, or PNG.`;
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Max ${MAX_SIZE_MB} MB.`;
    }
    return null;
  }

  function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file || !activeSlot) return;
    const err = validateFile(file);
    if (err) { setError(err); return; }
    setError('');
    setSlotFiles(prev => ({ ...prev, [activeSlot]: file }));
    e.target.value = '';
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    const slot = activeSlot || REQUIRED_SLOTS.find(s => !slotFiles[s.id])?.id;
    if (!file || !slot) return;
    const err = validateFile(file);
    if (err) { setError(err); return; }
    setError('');
    setSlotFiles(prev => ({ ...prev, [slot]: file }));
  }, [activeSlot, slotFiles]);

  function removeFile(slotId) {
    setSlotFiles(prev => {
      const copy = { ...prev };
      delete copy[slotId];
      return copy;
    });
  }

  async function handleAnalyze() {
    setUploading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('application_type', state.applicationType);
      Object.entries(slotFiles).forEach(([slotId, file]) => {
        formData.append(slotId, file);
      });

      const res = await uploadDocuments(formData);
      dispatch({ type: 'SET_SESSION', payload: { sessionId: res.session_id } });

      // Store file metadata in context
      dispatch({
        type: 'SET_FILES',
        payload: Object.entries(slotFiles).map(([slotId, file]) => ({
          id: slotId,
          name: file.name,
          type: file.type,
          size: file.size,
          status: 'uploaded',
        })),
      });

      navigate('/analyzing');
    } catch (e) {
      setError(e.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="mb-8">
        <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-2">
          Step 1 — Upload Documents
        </p>
        <h1 className="text-3xl font-extrabold mb-2" style={{ fontFamily: "'Outfit', sans-serif", color: 'var(--text-primary)' }}>
          Upload your documents
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Upload the documents for your <span className="text-indigo-400 font-semibold capitalize">{state.applicationType}</span> application.
          Required items are marked.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`glass rounded-2xl border-2 border-dashed p-8 text-center mb-6 transition-all
          ${dragOver ? 'border-indigo-500/60 bg-indigo-500/5' : 'border-subtle'}`}
      >
        <Upload size={36} className="mx-auto mb-3" style={{ color: 'var(--text-muted)' }} aria-hidden />
        <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>Drag & drop files here</p>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>PDF, JPEG, PNG · Max {MAX_SIZE_MB} MB per file</p>
      </div>

      {/* Document slots */}
      <div className="space-y-3 mb-6" role="list" aria-label="Document upload slots">
        {REQUIRED_SLOTS.map((slot) => (
          <button
            key={slot.id}
            id={`slot-${slot.id}`}
            role="listitem"
            onClick={() => openFilePicker(slot.id)}
            className="w-full text-left cursor-pointer"
            aria-label={`Upload ${slot.label}`}
          >
            <FileRow slot={slot} file={slotFiles[slot.id] || null} onRemove={removeFile} />
          </button>
        ))}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={handleFileSelect}
        className="hidden"
        aria-hidden="true"
      />

      {/* Error */}
      {error && (
        <div role="alert" className="mb-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
          <AlertCircle size={16} aria-hidden /> {error}
        </div>
      )}

      {/* Summary */}
      {hasFiles && (
        <div className="mb-6 px-4 py-3 rounded-xl glass text-sm flex flex-wrap gap-4" style={{ color: 'var(--text-secondary)' }}>
          <span>✅ {Object.keys(slotFiles).length} file{Object.keys(slotFiles).length !== 1 ? 's' : ''} selected</span>
          {!requiredFilled && (
            <span className="text-amber-400">
              ⚠️ {REQUIRED_SLOTS.filter(s => s.required && !slotFiles[s.id]).length} required document(s) missing
            </span>
          )}
        </div>
      )}

      {/* CTA */}
      <Button
        id="run-preflight-btn"
        variant="primary"
        size="lg"
        disabled={!requiredFilled}
        loading={uploading}
        onClick={handleAnalyze}
        className="w-full"
      >
        <Rocket size={18} aria-hidden /> Run PreFlight
      </Button>
      {!requiredFilled && (
        <p className="text-xs text-center mt-3" style={{ color: 'var(--text-muted)' }}>
          Please upload all required documents to continue.
        </p>
      )}
    </div>
  );
}
