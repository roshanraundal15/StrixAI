import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

const TRANSACTIONS = [
  { id:1, name:'Swiggy',        type:'debit',  amt: 342,   date:'Today, 1:20 PM',   icon:'🍔' },
  { id:2, name:'Salary Credit', type:'credit', amt: 85000, date:'Today, 10:00 AM',  icon:'💼' },
  { id:3, name:'Airtel Recharge',type:'debit', amt: 299,   date:'Yesterday',        icon:'📱' },
  { id:4, name:'Amazon Pay',    type:'debit',  amt: 1299,  date:'Dec 30',           icon:'📦' },
  { id:5, name:'Roshan R.',     type:'credit', amt: 500,   date:'Dec 29',           icon:'👤' },
];

const CARDS = [
  { last4:'4521', bank:'HDFC Bank',  color:'linear-gradient(135deg,#1e3a5f,#2563eb)' },
  { last4:'9834', bank:'ICICI Bank', color:'linear-gradient(135deg,#1a1a2e,#e11d48)' },
];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [activeCard, setActiveCard] = useState(0);
  const [showBal, setShowBal] = useState(true);

  const doLogout = () => { logout(); nav('/'); };

  const fmt = n => '₹' + n.toLocaleString('en-IN', { minimumFractionDigits: 2 });

  return (
    <div className="dash-wrap">
      <div className="orb orb1" /><div className="orb orb2" />

      {/* ── sidebar ── */}
      <aside className="sidebar glass-card fade-up">
        <div className="side-logo">
          <span className="logo-icon">◈</span>
          <span className="logo-text">NovaPay</span>
        </div>

        <nav className="side-nav">
          {[
            { icon:'◉', label:'Dashboard',   active: true  },
            { icon:'↕', label:'Transfers',   active: false },
            { icon:'◷', label:'History',     active: false },
            { icon:'◑', label:'Analytics',   active: false },
            { icon:'◻', label:'Cards',       active: false },
            { icon:'◎', label:'Settings',    active: false },
          ].map(item => (
            <div key={item.label} className={`side-item ${item.active ? 'active' : ''}`}>
              <span className="side-icon">{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </nav>

        <div className="side-user" onClick={doLogout} title="Click to logout">
          <div className="user-avatar">{user?.name?.[0]?.toUpperCase()}</div>
          <div>
            <div className="user-name">{user?.name}</div>
            <div className="user-role">Personal Account</div>
          </div>
          <span className="logout-icon">⏻</span>
        </div>
      </aside>

      {/* ── main ── */}
      <main className="dash-main">

        {/* header */}
        <header className="dash-header fade-up">
          <div>
            <h1 className="dash-greeting">Good afternoon, {user?.name?.split(' ')[0]} 👋</h1>
            <p className="dash-date">{new Date().toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long' })}</p>
          </div>
          <div className="header-actions">
            <div className="notif-btn glass-card">🔔</div>
          </div>
        </header>

        {/* ── top row ── */}
        <div className="top-row">

          {/* balance card */}
          <div className="balance-card glass-card fade-up-2">
            <div className="bal-top">
              <span className="bal-label">Total Balance</span>
              <button className="eye-btn" onClick={() => setShowBal(!showBal)}>
                {showBal ? '👁' : '🙈'}
              </button>
            </div>
            <div className="bal-amount">
              {showBal ? fmt(user?.balance ?? 50000) : '₹ ••••••'}
            </div>
            <div className="bal-change positive">▲ 12.4% this month</div>
            <div className="bal-actions">
              <button className="bal-btn">↑ Send</button>
              <button className="bal-btn">↓ Receive</button>
              <button className="bal-btn">+ Add</button>
            </div>
          </div>

          {/* card carousel */}
          <div className="card-section fade-up-2">
            <div className="section-head">
              <span className="section-title">My Cards</span>
              <span className="section-link">+ Add Card</span>
            </div>
            <div className="card-carousel">
              {CARDS.map((c, i) => (
                <div
                  key={c.last4}
                  className={`debit-card ${i === activeCard ? 'active-card' : ''}`}
                  style={{ background: c.color }}
                  onClick={() => setActiveCard(i)}
                >
                  <div className="card-top">
                    <span className="card-bank">{c.bank}</span>
                    <span className="card-chip">▣</span>
                  </div>
                  <div className="card-num">•••• •••• •••• {c.last4}</div>
                  <div className="card-bot">
                    <span>{user?.name}</span>
                    <span className="card-visa">VISA</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── quick stats ── */}
        <div className="stats-grid fade-up-3">
          {[
            { label:'Money Sent',     val:'₹24,500', change:'+8%',  color:'#3b82f6' },
            { label:'Money Received', val:'₹85,500', change:'+23%', color:'#10b981' },
            { label:'Active Goals',   val:'3',        change:'On track', color:'#f59e0b' },
            { label:'Cashback Earned',val:'₹1,240',  change:'+₹340',color:'#8b5cf6' },
          ].map(s => (
            <div className="stat-card glass-card" key={s.label}>
              <div className="stat-dot" style={{ background: s.color }} />
              <div className="stat-body">
                <div className="stat-card-label">{s.label}</div>
                <div className="stat-card-val">{s.val}</div>
                <div className="stat-card-change" style={{ color: s.color }}>{s.change}</div>
              </div>
            </div>
          ))}
        </div>

        {/* ── transactions ── */}
        <div className="txn-section glass-card fade-up-4">
          <div className="section-head" style={{ marginBottom: 20 }}>
            <span className="section-title">Recent Transactions</span>
            <span className="section-link">View All</span>
          </div>
          {TRANSACTIONS.map(t => (
            <div className="txn-row" key={t.id}>
              <div className="txn-icon">{t.icon}</div>
              <div className="txn-info">
                <div className="txn-name">{t.name}</div>
                <div className="txn-date">{t.date}</div>
              </div>
              <div className={`txn-amt ${t.type}`}>
                {t.type === 'debit' ? '−' : '+'}{fmt(t.amt)}
              </div>
            </div>
          ))}
        </div>

      </main>
    </div>
  );
}