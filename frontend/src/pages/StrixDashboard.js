import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './StrixDashboard.css';

const API = 'http://localhost:5000';

const ACTION_COLOR = { block: '#ef4444', captcha: '#f59e0b', allow: '#10b981' };
const ACTION_ICON  = { block: '🚫', captcha: '⚠️', allow: '✅' };

function StatCard({ label, value, sub, color, icon }) {
  return (
    <div className="strix-stat-card">
      <div className="strix-stat-icon" style={{ background: color + '22', color }}>{icon}</div>
      <div>
        <div className="strix-stat-val" style={{ color }}>{value}</div>
        <div className="strix-stat-label">{label}</div>
        {sub && <div className="strix-stat-sub">{sub}</div>}
      </div>
    </div>
  );
}

function ScoreBar({ score }) {
  const pct   = Math.round(score * 100);
  const color = score >= 0.7 ? '#ef4444' : score >= 0.4 ? '#f59e0b' : '#10b981';
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-bar-label" style={{ color }}>{pct}</span>
    </div>
  );
}

export default function StrixDashboard() {
  const [stats,        setStats]        = useState(null);
  const [decisions,    setDecisions]    = useState([]);
  const [fingerprints, setFingerprints] = useState([]);
  const [activeTab,    setActiveTab]    = useState('live');
  const [lastUpdate,   setLastUpdate]   = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [s, d, f] = await Promise.all([
        axios.get(`${API}/api/strix/stats`),
        axios.get(`${API}/api/strix/decisions`),
        axios.get(`${API}/api/strix/fingerprints`),
      ]);
      setStats(s.data);
      setDecisions(d.data);
      setFingerprints(f.data);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (e) {
      console.error('Dashboard fetch error:', e);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 3000);  // refresh every 3 seconds
    return () => clearInterval(interval);
  }, [fetchAll]);

  if (!stats) return (
    <div className="strix-loading">
      <div className="strix-logo">◈ Strix AI</div>
      <div className="strix-spinner" />
      <p>Connecting to detection engine…</p>
    </div>
  );

  return (
    <div className="strix-wrap">
      <div className="strix-orb strix-orb1" />
      <div className="strix-orb strix-orb2" />

      {/* ── Header ── */}
      <header className="strix-header">
        <div className="strix-header-left">
          <div className="strix-logo-row">
            <span className="strix-logo-icon">◈</span>
            <span className="strix-logo-text">Strix AI</span>
            <span className="strix-live-badge">● LIVE</span>
          </div>
          <p className="strix-sub">Real-Time Attack Detection Dashboard</p>
        </div>
        <div className="strix-header-right">
          <span className="strix-update">Last update: {lastUpdate}</span>
          <button className="strix-refresh-btn" onClick={fetchAll}>↻ Refresh</button>
        </div>
      </header>

      {/* ── Stat Cards ── */}
      <div className="strix-stats-row">
        <StatCard label="Active Threats"    value={stats.active_threats}  color="#ef4444" icon="🔴" sub="last 5 min" />
        <StatCard label="Suspicious IPs"    value={stats.suspicious_ips}  color="#f59e0b" icon="🌐" />
        <StatCard label="Total Blocked"     value={stats.blocked}         color="#ef4444" icon="🚫" />
        <StatCard label="CAPTCHA Triggered" value={stats.captcha}         color="#f59e0b" icon="⚠️" />
        <StatCard label="Allowed"           value={stats.allowed}         color="#10b981" icon="✅" />
        <StatCard label="Bot Traffic"       value={`${stats.bot_traffic_pct}%`} color="#8b5cf6" icon="🤖" sub="of all requests" />
      </div>

      {/* ── Tabs ── */}
      <div className="strix-tabs">
        {['live', 'fingerprints'].map(t => (
          <button
            key={t}
            className={`strix-tab ${activeTab === t ? 'active' : ''}`}
            onClick={() => setActiveTab(t)}
          >
            {t === 'live' ? '⚡ Live Decisions' : '🔍 Attack Fingerprints'}
          </button>
        ))}
      </div>

      {/* ── Live Decisions Table ── */}
      {activeTab === 'live' && (
        <div className="strix-table-wrap">
          <table className="strix-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>IP Address</th>
                <th>User</th>
                <th>Action</th>
                <th>Risk Score</th>
                <th>Attack Type</th>
                <th>Fingerprint</th>
                <th>Known?</th>
              </tr>
            </thead>
            <tbody>
              {decisions.length === 0 && (
                <tr><td colSpan={8} style={{ textAlign:'center', color:'#64748b', padding:'40px' }}>
                  No decisions yet — run the bot attack or try logging in
                </td></tr>
              )}
              {decisions.map((d, i) => (
                <tr key={i} className={`strix-row strix-row-${d.action}`}>
                  <td className="td-time">{new Date(d.timestamp).toLocaleTimeString('en-US', { timeZone: 'Asia/Kolkata' })}</td>
                  <td className="td-ip">{d.ip}</td>
                  <td className="td-user">{d.user_id?.slice(0, 22)}</td>
                  <td>
                    <span className="action-badge" style={{
                      background: ACTION_COLOR[d.action] + '22',
                      color:      ACTION_COLOR[d.action],
                      borderColor: ACTION_COLOR[d.action] + '55'
                    }}>
                      {ACTION_ICON[d.action]} {d.action.toUpperCase()}
                    </span>
                  </td>
                  <td><ScoreBar score={d.final_score} /></td>
                  <td className="td-type">{d.attack_type || '—'}</td>
                  <td className="td-fp">{d.fp_id || '—'}</td>
                  <td>
                    {d.is_known_fp
                      ? <span className="known-badge">⚡ Known</span>
                      : <span className="new-badge">New</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Fingerprints Table ── */}
      {activeTab === 'fingerprints' && (
        <div className="strix-table-wrap">
          <table className="strix-table">
            <thead>
              <tr>
                <th>Fingerprint ID</th>
                <th>Attack Type</th>
                <th>Speed</th>
                <th>Rate</th>
                <th>User Spread</th>
                <th>Proxy</th>
                <th>Times Seen</th>
                <th>Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {fingerprints.length === 0 && (
                <tr><td colSpan={8} style={{ textAlign:'center', color:'#64748b', padding:'40px' }}>
                  No fingerprints yet — run the bot attack to generate them
                </td></tr>
              )}
              {fingerprints.map((f, i) => (
                <tr key={i} className="strix-row">
                  <td><code className="fp-code">{f.fp_id}</code></td>
                  <td className="td-type">{f.attack_type}</td>
                  <td>{f.signature?.speed}</td>
                  <td>{f.signature?.rate}</td>
                  <td>{f.signature?.user_spread}</td>
                  <td>{f.signature?.is_proxy ? '⚠ Yes' : '✓ No'}</td>
                  <td>
                    <span className="seen-count">{f.seen_count}×</span>
                  </td>
                  <td className="td-time">{new Date(f.last_seen).toLocaleTimeString('en-US', { timeZone: 'Asia/Kolkata' })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}