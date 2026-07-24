import React, { useState, useEffect } from 'react';
import DiffInput from './components/DiffInput';
import SummaryPanel from './components/SummaryPanel';
import BlastGraph from './components/BlastGraph';
import { analyzeDiff, fetchGraph } from './api';
import './index.css';

function App() {
  const [fullGraph, setFullGraph] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGraph()
      .then(data => setFullGraph(data))
      .catch(err => console.error("Could not fetch initial graph:", err));
  }, []);

  const handleAnalyze = async (diffText) => {
    if (!diffText.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeDiff(diffText);
      setAnalysisResult(result);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to analyze diff");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>Blast Radius</h1>
        <span className="tagline">AI-Powered Code Impact Analysis</span>
      </header>
      
      <main className="main-content">
        <div className="left-sidebar">
          <DiffInput onAnalyze={handleAnalyze} isLoading={isLoading} />
          {error && <div className="error-message glass-panel">{error}</div>}
          <SummaryPanel result={analysisResult} />
        </div>
        
        <div className="right-panel">
          <BlastGraph fullGraph={fullGraph} analysisResult={analysisResult} />
        </div>
      </main>
    </div>
  );
}

export default App;
