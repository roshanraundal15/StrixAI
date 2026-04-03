import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './AuthPage.css';

export default function LoginPage() {
  const nav = useNavigate();
  const { login } = useAuth();

  const [form, setForm]     = useState({ email: '', password: '' });
  const [error, setError]   = useState('');
  const [loading, setLoad]  = useState(false);

  const handle = e => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async e => {
    e.preventDefault();
    setError(''); setLoad(true);
    try {
      const { data } = await axios.post('http://localhost:5000/api/login', form);
      login(data.user);
      nav('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Try again.');
    } finally { setLoad(false); }
  };

  return (
    <div className="auth-wrap">
      <div className="orb orb1" /><div className="orb orb2" />

      <div className="auth-card glass-card fade-up">
        {/* logo */}
        <div className="auth-logo">
          <span className="logo-icon">◈</span>
          <span className="logo-text">NovaPay</span>
        </div>

        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-sub">Sign in to your account</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={submit} className="auth-form">
          <div className="field-group">
            <label className="field-label">Email address</label>
            <input
              className="input-field"
              type="email" name="email"
              placeholder="you@example.com"
              value={form.email} onChange={handle} required
            />
          </div>

          <div className="field-group">
            <label className="field-label">Password</label>
            <input
              className="input-field"
              type="password" name="password"
              placeholder="••••••••"
              value={form.password} onChange={handle} required
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