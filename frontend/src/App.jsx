import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { PreFlightProvider } from './context/PreFlightContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import AnalyzingPage from './pages/AnalyzingPage';
import ResultsPage from './pages/ResultsPage';
import EvidencePage from './pages/EvidencePage';

export default function App() {
  return (
    <ThemeProvider>
      <PreFlightProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/analyzing" element={<AnalyzingPage />} />
                <Route path="/results" element={<ResultsPage />} />
                <Route path="/evidence" element={<EvidencePage />} />
                {/* Catch-all */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <footer className="border-t py-6 text-center text-xs text-muted"
                    style={{ borderColor: 'var(--border-subtle)' }}>
              PreFlight · Application Readiness Checker
            </footer>
          </div>
        </BrowserRouter>
      </PreFlightProvider>
    </ThemeProvider>
  );
}
