import React, { useState, useEffect } from 'react';
import DiffInput from './components/DiffInput';
import SummaryPanel from './components/SummaryPanel';
import BlastGraph from './components/BlastGraph';
import { analyzeDiff, analyzeZip, fetchGraph } from './api';
import './index.css';

function App() {
  const [baseGraph, setBaseGraph] = useState(null);   // seed graph (always loaded)
  const [activeGraph, setActiveGraph] = useState(null); // graph from analysis (zip or seed)
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load seed graph on mount for initial display
  useEffect(() => {
    fetchGraph()
      .then(data => { setBaseGraph(data); setActiveGraph(data); })
      .catch(err => console.error('Could not load base graph:', err));
  }, []);

  const handleAnalyze = async (diffText, zipFile) => {
    if (!diffText.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      let result;
      if (zipFile) {
        result = await analyzeZip(diffText, zipFile);
      } else {
        result = await analyzeDiff(diffText);
      }
      setAnalysisResult(result);
      // Use graph embedded in response (from zip) or fall back to base
      if (result.graph) {
        setActiveGraph(result.graph);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <div className="header-brand">
          <span className="header-icon">💥</span>
          <div>
            <h1>Blast Radius</h1>
            <div className="tagline">AI-Powered Code Impact Analysis · CodeHunters Hackathon</div>
          </div>
        </div>
      </header>

      <main className="main-content">
        {/* ── LEFT: sticky control + results panel ── */}
        <div className="left-sidebar">
          <DiffInput onAnalyze={handleAnalyze} isLoading={isLoading} />
          {error && <div className="error-message glass-panel">⚠️ {error}</div>}
          <SummaryPanel result={analysisResult} />
        </div>

        {/* ── RIGHT: big graph on top, dependencies scroll below ── */}
        <div className="right-panel">
          <BlastGraph
            fullGraph={activeGraph}
            analysisResult={analysisResult}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
