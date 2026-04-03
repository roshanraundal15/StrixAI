import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import './AuthPage.css';

export default function RegisterPage() {
  const nav = useNavigate();
  const [form, setForm]   = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [ok, setOk]       = useState('');
  const [loading, setLoad]= useState(false);

  const handle = e => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async e => {
    e.preventDefault();
    setError(''); setOk(''); setLoad(true);
    try {
      await axios.post('http://localhost:5000/api/register', form);
      setOk('Account created! Redirecting…');
      setTimeout(() => nav('/login'), 1500);
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed.');
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

        <h2 className="auth-title">Create account</h2>
        <p className="auth-sub">Join millions of happy users</p>

        {error && <div className="auth-error">{error}</div>}
        {ok    && <div className="auth-success">{ok}</div>}

        <form onSubmit={submit} className="auth-form">
          <div className="field-group">
            <label className="field-label">Full Name</label>
            <input className="input-field" type="text" name="name"
              placeholder="Rahul Sharma"
              value={form.name} onChange={handle} required />
          </div>

          <div className="field-group">
            <label className="field-label">Email address</label>
            <input className="input-field" type="email" name="email"
              placeholder="you@example.com"
              value={form.email} onChange={handle} required />
          </div>

          <div className="field-group">
            <label className="field-label">Password</label>
            <input className="input-field" type="password" name="password"
              placeholder="Min. 8 characters"
              value={form.password} onChange={handle} required minLength={6} />
          </div>

          <button className="btn-primary auth-btn" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Create Account →'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{' '}
          <Link to="/login" className="auth-link">Sign in</Link>
        </p>
      </div>
    </div>
  );
}