import { createContext, useContext, useReducer } from 'react';

const initialState = {
  sessionId: null,
  jobId: null,
  applicationType: 'scholarship',
  uploadedFiles: [],        // [{ id, file, name, type, status, error }]
  analysisResult: null,     // AnalysisResult from backend
  isRecheck: false,
  demoMode: true,
};

function reducer(state, action) {
  switch (action.type) {
    case 'SET_APPLICATION_TYPE':
      return { ...state, applicationType: action.payload };
    case 'SET_SESSION':
      return { ...state, sessionId: action.payload.sessionId };
    case 'SET_JOB':
      return { ...state, jobId: action.payload.jobId };
    case 'SET_FILES':
      return { ...state, uploadedFiles: action.payload };
    case 'ADD_FILE':
      return { ...state, uploadedFiles: [...state.uploadedFiles, action.payload] };
    case 'REMOVE_FILE':
      return { ...state, uploadedFiles: state.uploadedFiles.filter((f) => f.id !== action.payload) };
    case 'UPDATE_FILE':
      return {
        ...state,
        uploadedFiles: state.uploadedFiles.map((f) =>
          f.id === action.payload.id ? { ...f, ...action.payload.updates } : f
        ),
      };
    case 'SET_RESULT':
      return { ...state, analysisResult: action.payload };
    case 'SET_IS_RECHECK':
      return { ...state, isRecheck: action.payload };
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
}

const PreFlightContext = createContext(null);

export function PreFlightProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <PreFlightContext.Provider value={{ state, dispatch }}>
      {children}
    </PreFlightContext.Provider>
  );
}

export function usePreFlight() {
  const ctx = useContext(PreFlightContext);
  if (!ctx) throw new Error('usePreFlight must be used within PreFlightProvider');
  return ctx;
}
