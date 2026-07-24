import React, { useState, useRef } from 'react';
import { Play, Upload, X, FileArchive } from 'lucide-react';
import './DiffInput.css';

const sampleDiff = `--- a/order_service/main.py
+++ b/order_service/main.py
@@ -10,1 +10,1 @@
-def create_order(db: Session, order_data: OrderCreate) -> Order:
+def create_order(db: Session, order_data: OrderCreate, expedited: bool = False) -> Order:
`;

export default function DiffInput({ onAnalyze, isLoading }) {
  const [diff, setDiff] = useState(sampleDiff);
  const [zipFile, setZipFile] = useState(null);
  const fileRef = useRef(null);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) setZipFile(f);
  };

  const clearZip = () => {
    setZipFile(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  return (
    <div className="diff-input-panel glass-panel">
      <div className="panel-header">
        <h3>Change Ingestion</h3>
        <p>Paste a git diff, optionally upload your full codebase as a .zip</p>
      </div>

      <textarea
        className="diff-textarea"
        value={diff}
        onChange={(e) => setDiff(e.target.value)}
        placeholder="Paste unified diff here..."
        spellCheck="false"
      />

      {/* ZIP Upload Area */}
      <div className="zip-upload-area" onClick={() => !zipFile && fileRef.current?.click()}>
        <input
          ref={fileRef}
          type="file"
          accept=".zip"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        {zipFile ? (
          <div className="zip-file-selected">
            <FileArchive size={16} />
            <span className="zip-name">{zipFile.name}</span>
            <span className="zip-size">({(zipFile.size / 1024).toFixed(0)} KB)</span>
            <button className="clear-zip-btn" onClick={(e) => { e.stopPropagation(); clearZip(); }}>
              <X size={14} />
            </button>
          </div>
        ) : (
          <div className="zip-placeholder">
            <Upload size={16} />
            <span>Upload codebase .zip (optional — for deeper graph analysis)</span>
          </div>
        )}
      </div>

      <div className="panel-footer">
        <button
          className="analyze-btn"
          onClick={() => onAnalyze(diff, zipFile)}
          disabled={isLoading || !diff.trim()}
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
