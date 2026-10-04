import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PreFlightIcon from '../components/PreFlightIcon';
import { usePreFlight } from '../context/PreFlightContext';
import { startAnalysis, getAnalysisResult } from '../api/apiService';

const STEPS = [
  { label: 'Reading documents', duration: 1800 },
  { label: 'Extracting information', duration: 2200 },
  { label: 'Comparing documents', duration: 1600 },
  { label: 'Checking official requirements', duration: 1900 },
  { label: 'Calculating risk', duration: 1400 },
  { label: 'Preparing recommendations', duration: 1200 },
];

const TOTAL_DURATION = STEPS.reduce((s, step) => s + step.duration, 0);

function buildTimeline() {
  let elapsed = 0;
  return STEPS.map((step) => {
    const start = elapsed;
    elapsed += step.duration;
    return { ...step, start, end: elapsed };
  });
}

const TIMELINE = buildTimeline();

export default function AnalyzingPage() {
  const navigate = useNavigate();
  const { state, dispatch } = usePreFlight();
  const [progress, setProgress] = useState(0);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [done, setDone] = useState(false);
  const startTime = useRef(Date.now());
  const raf = useRef(null);

  useEffect(() => {
    async function kickOff() {
      try {
        const { job_id } = await startAnalysis(state.sessionId, state.applicationType);
        dispatch({ type: 'SET_JOB', payload: { jobId: job_id } });
      } catch {
        // In demo mode we still proceed
      }
    }
    kickOff();
  }, []);

  useEffect(() => {
    function tick() {
      const elapsed = Date.now() - startTime.current;
      const pct = Math.min(100, (elapsed / TOTAL_DURATION) * 100);
      setProgress(pct);

      const stepIdx = TIMELINE.findIndex(
        (s) => elapsed >= s.start && elapsed < s.end
      );
      if (stepIdx !== -1) setCurrentStepIdx(stepIdx);

      if (elapsed >= TOTAL_DURATION) {
        setProgress(100);
        setCurrentStepIdx(STEPS.length - 1);
        setDone(true);
        return;
      }
      raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, []);

  useEffect(() => {
    if (!done) return;
    async function fetchResult() {
      const result = await getAnalysisResult(state.jobId, state.isRecheck);
      dispatch({ type: 'SET_RESULT', payload: result });
      // Short pause so "100%" is visible
      await new Promise(r => setTimeout(r, 600));
      navigate('/results');
    }
    fetchResult();
  }, [done]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        {/* Animated icon */}
        <div className="relative mx-auto mb-10 w-24 h-24 flex items-center justify-center">
          <div className="absolute inset-0 rounded-2xl gradient-brand animate-pulse opacity-25" />
          <div className="relative flex items-center justify-center glow-brand rounded-2xl">
            <PreFlightIcon size={64} />
          </div>
        </div>

        <h1 className="text-2xl font-extrabold mb-2" style={{ fontFamily: "'Outfit', sans-serif", color: 'var(--text-primary)' }}>
          Running PreFlight…
        </h1>
        <p className="mb-10" style={{ color: 'var(--text-secondary)' }}>Analysing your documents. Please wait.</p>

        {/* Progress bar */}
        <div className="relative h-2.5 rounded-full overflow-hidden mb-4 border border-subtle" style={{ background: 'var(--bg-raised)' }}>
          <div
            role="progressbar"
            aria-valuenow={Math.round(progress)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Analysis progress"
            className="h-full gradient-brand rounded-full transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>

        <p className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>{Math.round(progress)}%</p>

        {/* Steps list */}
        <div className="mt-8 space-y-3 text-left">
          {STEPS.map((step, i) => {
            const isActive = i === currentStepIdx && !done;
            const isPast = i < currentStepIdx || done;
            return (
              <div key={step.label} className={`flex items-center gap-3 transition-all duration-300 ${isPast ? 'opacity-100' : isActive ? 'opacity-100' : 'opacity-40'}`}>
                <div className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold
                  ${isPast ? 'bg-emerald-500/20 text-emerald-400' : isActive ? 'gradient-brand text-white' : 'glass text-muted'}`}>
                  {isPast ? '✓' : i + 1}
                </div>
                <span
                  className="text-sm font-medium"
                  style={{
                    color: isActive ? 'var(--text-primary)' : isPast ? 'var(--text-secondary)' : 'var(--text-muted)'
                  }}
                >
                  {step.label}
                  {isActive && <span className="ml-2 animate-pulse text-indigo-400">…</span>}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
