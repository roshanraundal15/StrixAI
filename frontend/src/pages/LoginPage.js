import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './AuthPage.css';

export default function LoginPage() {
  const nav       = useNavigate();
  const { login } = useAuth();

  const [form, setForm]   = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoad]= useState(false);

  // ── Behavioral tracking ───────────────────────────────────────────────────
  const pageLoadTime     = useRef(Date.now());
  const keystrokeTimings = useRef([]);
  const lastKeystroke    = useRef(null);
  const mouseMoveCount   = useRef(0);
  const fieldFocusCount  = useRef(0);
  const passwordPasted   = useRef(false);

  useEffect(() => {
    const onMove = () => { mouseMoveCount.current += 1; };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  const handleKeyDown = () => {
    const now = Date.now();
    if (lastKeystroke.current !== null) {
      keystrokeTimings.current.push(now - lastKeystroke.current);
    }
    lastKeystroke.current = now;
  };

  const handleFocus = () => { fieldFocusCount.current += 1; };

  const handle = e => setForm({ ...form, [e.target.name]: e.target.value });

  const collectBehavioralData = () => ({
    time_to_submit:      Date.now() - pageLoadTime.current,
    keystroke_intervals: keystrokeTimings.current,
    mouse_move_count:    mouseMoveCount.current,
    password_pasted:     passwordPasted.current,
    field_focus_count:   fieldFocusCount.current,
    js_enabled:          true,
    phone:               '',   // honeypot — always blank for real users
  });

  const submit = async e => {
    e.preventDefault();
    setError(''); setLoad(true);
    const payload = { ...form, ...collectBehavioralData() };

    try {
      const { data } = await axios.post('http://localhost:5000/api/login', payload);

      if (data.captcha_required) {
        const ok = window.confirm(
          '🛡 Security Check\n\nSuspicious activity detected.\nClick OK to confirm you are human.'
        );
        if (!ok) { setLoad(false); return; }
      }
      login(data.user);
      nav('/dashboard');

    } catch (err) {
      const strix = err.response?.data?.strix;
      if (err.response?.status === 403) {
        setError(`🚫 Blocked by Strix AI — bot detected (score: ${strix?.score})`);
      } else {
        setError(err.response?.data?.error || 'Login failed. Try again.');
      }
    } finally { setLoad(false); }
  };

  return (
    <div className="auth-wrap">
      <div className="orb orb1" /><div className="orb orb2" />

      <div className="auth-card glass-card fade-up">
        <div className="auth-logo">
          <span className="logo-icon">◈</span>
          <span className="logo-text">NovaPay</span>
        </div>

        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-sub">Sign in to your account</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={submit} className="auth-form">

          {/* HONEYPOT — invisible to humans, bots will fill this */}
          <input
            type="text" name="phone" tabIndex="-1"
            autoComplete="off" aria-hidden="true"
            style={{ position:'absolute', left:'-9999px', opacity:0, height:0, width:0 }}
          />

          <div className="field-group">
            <label className="field-label">Email address</label>
            <input
              className="input-field" type="email" name="email"
              placeholder="you@example.com"
              value={form.email} onChange={handle}
              onKeyDown={handleKeyDown} onFocus={handleFocus}
              required
            />
          </div>

          <div className="field-group">
            <label className="field-label">Password</label>
            <input
              className="input-field" type="password" name="password"
              placeholder="••••••••"
              value={form.password} onChange={handle}
              onKeyDown={handleKeyDown} onFocus={handleFocus}
              onPaste={() => { passwordPasted.current = true; }}
              required
            />
          </div>

          <button className="btn-primary auth-btn" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Sign In →'}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account?{' '}
          <Link to="/register" className="auth-link">Create one</Link>
        </p>
      </div>
    </div>
  );
}