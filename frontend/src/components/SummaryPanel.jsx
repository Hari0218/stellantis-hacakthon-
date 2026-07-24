import React from 'react';
import { AlertTriangle, CheckCircle, ShieldAlert, Users, FlaskConical, Target, Zap, Info } from 'lucide-react';
import './SummaryPanel.css';

function ChangeBadge({ scale }) {
  const configs = {
    minor:    { label: 'Minor Change',    color: '#22c55e', bg: 'rgba(34,197,94,0.1)',   desc: 'Small isolated change — low blast radius.' },
    moderate: { label: 'Moderate Change', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', desc: 'Multiple components affected — review recommended.' },
    major:    { label: 'Major Change',    color: '#ef4444', bg: 'rgba(239,68,68,0.1)',   desc: 'Critical structural change — full regression testing required.' },
    minimal:  { label: 'No Impact',       color: '#6b7280', bg: 'rgba(107,114,128,0.1)', desc: 'No actionable changes detected.' },
  };
  const cfg = configs[scale] || configs.minimal;
  return (
    <div className="change-badge" style={{ background: cfg.bg, borderColor: cfg.color }}>
      <span className="change-badge-label" style={{ color: cfg.color }}>{cfg.label}</span>
      <span className="change-badge-desc">{cfg.desc}</span>
    </div>
  );
}

export default function SummaryPanel({ result }) {
  if (!result) {
    return (
      <div className="summary-panel glass-panel empty-state">
        <Target size={48} className="empty-icon" />
        <h3>Awaiting Analysis</h3>
        <p>Paste a git diff and run impact analysis to see the blast radius and risk scoring.</p>
      </div>
    );
  }

  const { risk_score, explanation, affected_services, affected_teams,
          recommended_tests, change_scale, change_types, affected_nodes } = result;

  // Derive risk band purely from the numeric score
  const effectiveBand =
    risk_score >= 66 ? 'HIGH' :
    risk_score >= 31 ? 'MEDIUM' :
    risk_score >  0  ? 'LOW' : 'NONE';

  const bandConfig = {
    LOW:    { icon: CheckCircle,  color: 'var(--success-color, #22c55e)' },
    MEDIUM: { icon: AlertTriangle, color: 'var(--warning-color, #f59e0b)' },
    HIGH:   { icon: ShieldAlert,  color: 'var(--danger-color, #ef4444)' },
    NONE:   { icon: Info,         color: 'var(--text-muted, #6b7280)' },
  };

  const BandIcon = bandConfig[effectiveBand]?.icon || CheckCircle;
  const bandColor = bandConfig[effectiveBand]?.color;


  return (
    <div className="summary-panel glass-panel fade-in-up">
      {/* Change Scale Banner */}
      <ChangeBadge scale={change_scale} />

      {/* Risk Score */}
      <div className="risk-header">
        <div className="risk-score-circle" style={{ borderColor: bandColor }}>
          <span className="score-value">{risk_score}</span>
          <span className="score-label">RISK</span>
        </div>
        <div className="risk-title">
          <h2 style={{ color: bandColor }}>
            <BandIcon size={24} className="risk-icon" />
            {effectiveBand} RISK
          </h2>
          <p className="explanation-text">{explanation}</p>
        </div>
      </div>

      {/* Change Types */}
      {change_types && change_types.length > 0 && (
        <div className="change-types-row">
          <span className="change-types-label">Change Types:</span>
          {change_types.map(ct => (
            <span key={ct} className={`change-type-pill ct-${ct.toLowerCase().replace('_', '-')}`}>{ct.replace('_', ' ')}</span>
          ))}
        </div>
      )}

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper"><Zap size={18} /></div>
          <div className="stat-content">
            <span className="stat-label">Blast Nodes</span>
            <span className="stat-value">{(affected_nodes || []).length}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper"><Target size={18} /></div>
          <div className="stat-content">
            <span className="stat-label">Services</span>
            <span className="stat-value">{affected_services.length}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper"><Users size={18} /></div>
          <div className="stat-content">
            <span className="stat-label">Teams</span>
            <span className="stat-value">{affected_teams.length}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-wrapper"><FlaskConical size={18} /></div>
          <div className="stat-content">
            <span className="stat-label">Tests</span>
            <span className="stat-value">{recommended_tests.length}</span>
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="details-section">
        <div className="detail-column">
          <h4>Affected Services</h4>
          {affected_services.length > 0 ? (
            <ul className="pill-list">
              {affected_services.map(s => <li key={s} className="pill pill-service">{s}</li>)}
            </ul>
          ) : <p className="no-data">None</p>}
        </div>

        <div className="detail-column">
          <h4>Affected Teams</h4>
          {affected_teams.length > 0 ? (
            <ul className="pill-list">
              {affected_teams.map(t => <li key={t} className="pill pill-team">{t}</li>)}
            </ul>
          ) : <p className="no-data">None</p>}
        </div>
      </div>

      <div className="detail-column full-width">
        <h4>Tests to Run</h4>
        {recommended_tests.length > 0 ? (
          <ul className="code-list">
            {recommended_tests.map(t => <li key={t}><code>pytest {t}</code></li>)}
          </ul>
        ) : <p className="no-data">No specific tests identified.</p>}
      </div>
    </div>
  );
}
