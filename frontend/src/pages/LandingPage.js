import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../index.css';
import './LandingPage.css';

export default function LandingPage() {
  const nav = useNavigate();

  return (
    <div className="landing">
      {/* ── glow orbs ── */}
      <div className="orb orb1" />
      <div className="orb orb2" />

      {/* ── navbar ── */}
      <nav className="land-nav fade-up">
        <div className="land-logo">
          <span className="logo-icon">◈</span>
          <span className="logo-text">NovaPay</span>
        </div>
        <div className="nav-links">
          <button className="btn-ghost" onClick={() => nav('/login')}>Sign In</button>
          <button className="btn-primary" onClick={() => nav('/register')}>Get Started</button>
        </div>
      </nav>

      {/* ── hero ── */}
      <main className="hero">
        <div className="hero-badge fade-up">
          <span className="badge-dot" />
          Trusted by 2M+ users across India
        </div>

        <h1 className="hero-title fade-up-2">
          Banking that<br />
          <span className="gradient-text">moves with you</span>
        </h1>

        <p className="hero-sub fade-up-3">
          Send money, pay bills, and manage your finances —<br />
          all in one beautifully simple app.
        </p>

        <div className="hero-actions fade-up-4">
          <button className="btn-primary" onClick={() => nav('/register')}>
            Open Free Account →
          </button>
          <button className="btn-ghost" onClick={() => nav('/login')}>
            I already have an account
          </button>
        </div>

        {/* ── floating stats ── */}
        <div className="stats-row fade-up-4">
          {[
            { val: '₹2.4B+', label: 'Processed Daily' },
            { val: '99.9%', label: 'Uptime SLA' },
            { val: '< 1s',  label: 'Transfer Speed' },
            { val: '256-bit', label: 'Encryption' },
          ].map(s => (
            <div className="stat-pill glass-card" key={s.val}>
              <span className="stat-val">{s.val}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}