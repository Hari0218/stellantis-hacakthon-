import React from 'react';
import { AlertTriangle, CheckCircle, ShieldAlert, Users, FlaskConical, Target } from 'lucide-react';
import './SummaryPanel.css';

export default function SummaryPanel({ result }) {
  if (!result) {
    return (
      <div className="summary-panel glass-panel empty-state">
        <Target size={48} className="empty-icon" />
        <h3>Awaiting Analysis</h3>
        <p>Run impact analysis on a change to see the blast radius and risk scoring.</p>
      </div>
    );
  }

  const { risk_band, risk_score, explanation, affected_services, affected_teams, recommended_tests } = result;

  const bandConfig = {
    LOW: { icon: CheckCircle, color: 'var(--success-color)' },
    MEDIUM: { icon: AlertTriangle, color: 'var(--warning-color)' },
    HIGH: { icon: ShieldAlert, color: 'var(--danger-color)' },
    NONE: { icon: CheckCircle, color: 'var(--text-muted)' }
  };

  const BandIcon = bandConfig[risk_band]?.icon || CheckCircle;

  return (
    <div className="summary-panel glass-panel fade-in-up">
      <div className="risk-header">
        <div className="risk-score-circle" style={{ borderColor: bandConfig[risk_band]?.color }}>
          <span className="score-value">{risk_score}</span>
          <span className="score-label">RISK</span>
        </div>
        <div className="risk-title">
          <h2 style={{ color: bandConfig[risk_band]?.color }}>
            <BandIcon size={24} className="risk-icon" />
            {risk_band} RISK
          </h2>
          <p className="explanation-text">{explanation}</p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper"><Target size={18} /></div>
          <div className="stat-content">
            <span className="stat-label">Affected Services</span>
            <span className="stat-value">{affected_services.length}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper"><Users size={18} /></div>
          <div className="stat-content">
            <span className="stat-label">Teams Impacted</span>
            <span className="stat-value">{affected_teams.length}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper"><FlaskConical size={18} /></div>
          <div className="stat-content">
            <span className="stat-label">Tests to Run</span>
            <span className="stat-value">{recommended_tests.length}</span>
          </div>
        </div>
      </div>

      <div className="details-section">
        <div className="detail-column">
          <h4>Affected Teams</h4>
          {affected_teams.length > 0 ? (
            <ul className="pill-list">
              {affected_teams.map(t => <li key={t} className="pill pill-team">{t}</li>)}
            </ul>
          ) : (
            <p className="no-data">None</p>
          )}
        </div>
        
        <div className="detail-column">
          <h4>Required Action</h4>
          {recommended_tests.length > 0 ? (
             <ul className="code-list">
               {recommended_tests.map(t => <li key={t}><code>pytest {t}</code></li>)}
             </ul>
          ) : (
             <p className="no-data">No specific tests identified.</p>
          )}
        </div>
      </div>
    </div>
  );
}
