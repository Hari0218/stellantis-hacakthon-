import React, { useState } from 'react';
import { Play } from 'lucide-react';
import './DiffInput.css';

const sampleDiff = `--- a/order_service/main.py
+++ b/order_service/main.py
@@ -10,1 +10,1 @@
-def create_order(db: Session, order_data: OrderCreate) -> Order:
+def create_order(db: Session, order_data: OrderCreate, expedited: bool = False) -> Order:
`;

export default function DiffInput({ onAnalyze, isLoading }) {
  const [diff, setDiff] = useState(sampleDiff);

  return (
    <div className="diff-input-panel glass-panel">
      <div className="panel-header">
        <h3>Change Ingestion</h3>
        <p>Paste a git diff or pull request content</p>
      </div>
      
      <textarea 
        className="diff-textarea"
        value={diff}
        onChange={(e) => setDiff(e.target.value)}
        placeholder="Paste unified diff here..."
        spellCheck="false"
      />
      
      <div className="panel-footer">
        <button 
          className="analyze-btn"
          onClick={() => onAnalyze(diff)}
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="spinner"></span>
          ) : (
            <Play size={18} />
          )}
          {isLoading ? 'Analyzing...' : 'Analyze Impact'}
        </button>
      </div>
    </div>
  );
}
