import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

const API = 'http://localhost:5000';

const fmt = (n) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', minimumFractionDigits: 2,
  }).format(n ?? 0);

const timeAgo = (iso) => {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

// ── Add Money Modal ───────────────────────────────────────────────────────────
function AddMoneyModal({ user, onClose, onSuccess }) {
  const [amount, setAmount]   = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const QUICK = [500, 1000, 2000, 5000];

  const handleAdd = async () => {
    if (!amount || isNaN(amount) || Number(amount) <= 0) {
      setError('Enter a valid amount'); return;
    }
    setLoading(true); setError('');
    try {
      const res  = await fetch(`${API}/api/wallet/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, amount: Number(amount) }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Failed'); return; }
      onSuccess(data.new_balance, data.txn_id);
    } catch { setError('Network error'); }
    finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-icon-wrap add">＋</div>
            <h2>Add Money</h2>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <p className="modal-sub">Current balance: <strong>{fmt(user.balance)}</strong></p>
          <div className="quick-amounts">
            {QUICK.map(q => (
              <button
                key={q}
                className={`quick-btn ${Number(amount) === q ? 'active' : ''}`}
                onClick={() => setAmount(String(q))}
              >₹{q.toLocaleString('en-IN')}</button>
            ))}
          </div>
          <div className="input-group">
            <span className="input-prefix">₹</span>
            <input
              type="number" placeholder="Enter amount" value={amount}
              onChange={e => setAmount(e.target.value)}
              className="modal-input" autoFocus
            />
          </div>
          {error && <p className="modal-error">{error}</p>}
          <button className="modal-btn primary" onClick={handleAdd} disabled={loading}>
            {loading ? <span className="btn-spinner" /> : 'Add Money'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Send Money Modal ──────────────────────────────────────────────────────────
function SendMoneyModal({ user, onClose, onSuccess }) {
  const [email,     setEmail]     = useState('');
  const [amount,    setAmount]    = useState('');
  const [note,      setNote]      = useState('');
  const [results,   setResults]   = useState([]);
  const [selected,  setSelected]  = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [searching, setSearching] = useState(false);
  const [error,     setError]     = useState('');

  useEffect(() => {
    if (email.length < 3) { setResults([]); return; }
    const t = setTimeout(async () => {
      setSearching(true);
      try {
        const res  = await fetch(`${API}/api/users/search?email=${encodeURIComponent(email)}`);
        const data = await res.json();
        setResults(data.filter(u => u.id !== user.id));
      } catch {} finally { setSearching(false); }
    }, 350);
    return () => clearTimeout(t);
  }, [email, user.id]);

  const handleSend = async () => {
    if (!selected)                                        { setError('Select a recipient'); return; }
    if (!amount || isNaN(amount) || Number(amount) <= 0)  { setError('Enter a valid amount'); return; }
    if (Number(amount) > user.balance)                    { setError('Insufficient balance'); return; }
    setLoading(true); setError('');
    try {
      const res  = await fetch(`${API}/api/wallet/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender_id: user.id, to_email: selected.email,
          amount: Number(amount), note,
        }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Failed'); return; }
      onSuccess(data.new_balance, data.txn_id, selected.name);
    } catch { setError('Network error'); }
    finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-icon-wrap send">→</div>
            <h2>Send Money</h2>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <p className="modal-sub">Available: <strong>{fmt(user.balance)}</strong></p>
          {!selected ? (
            <>
              <div className="input-group">
                <span className="input-prefix">@</span>
                <input
                  type="email" placeholder="Search by email…" value={email}
                  onChange={e => { setEmail(e.target.value); setSelected(null); }}
                  className="modal-input" autoFocus
                />
              </div>
              {searching && <p className="modal-searching">Searching…</p>}
              {results.length > 0 && (
                <div className="search-results">
                  {results.map(u => (
                    <div key={u.id} className="search-result-item"
                      onClick={() => { setSelected(u); setEmail(u.email); setResults([]); }}>
                      <div className="result-avatar">{u.name[0]}</div>
                      <div>
                        <div className="result-name">{u.name}</div>
                        <div className="result-email">{u.email}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="selected-recipient">
              <div className="recipient-avatar">{selected.name[0]}</div>
              <div className="recipient-info">
                <div className="recipient-name">{selected.name}</div>
                <div className="recipient-email">{selected.email}</div>
              </div>
              <button className="change-btn"
                onClick={() => { setSelected(null); setEmail(''); }}>Change</button>
            </div>
          )}
          {selected && (
            <>
              <div className="input-group">
                <span className="input-prefix">₹</span>
                <input
                  type="number" placeholder="Amount" value={amount}
                  onChange={e => setAmount(e.target.value)}
                  className="modal-input" autoFocus
                />
              </div>
              <input
                type="text" placeholder="Add a note (optional)" value={note}
                onChange={e => setNote(e.target.value)}
                className="modal-input standalone"
              />
            </>
          )}
          {error && <p className="modal-error">{error}</p>}
          {selected && (
            <button className="modal-btn primary" onClick={handleSend} disabled={loading}>
              {loading ? <span className="btn-spinner" />
                : `Send ${amount ? fmt(Number(amount)) : 'Money'}`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function Toast({ msg, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return <div className="toast">{msg}</div>;
}

// ── Transaction Item ──────────────────────────────────────────────────────────
function TxnItem({ t, idx }) {
  const isCredit = t.type === 'credit';
  return (
    <div className="txn-item" style={{ animationDelay: `${idx * 45}ms` }}>
      <div className={`txn-icon ${t.type}`}>{isCredit ? '↓' : '↑'}</div>
      <div className="txn-info">
        <div className="txn-title">{isCredit ? t.from_name : t.to_name}</div>
        <div className="txn-meta">
          <span className="txn-id">{t.txn_id}</span>
          <span className="txn-sep">·</span>
          <span className="txn-time">{timeAgo(t.timestamp)}</span>
        </div>
        {t.note && <div className="txn-note">{t.note}</div>}
      </div>
      <div className={`txn-amount ${t.type}`}>
        {isCredit ? '+' : '−'}{fmt(t.amount)}
      </div>
    </div>
  );
}

function TxnList({ txns, loading }) {
  if (loading) return (
    <div className="txn-skeleton-list">
      {[1,2,3,4].map(i => <div key={i} className="txn-skeleton" />)}
    </div>
  );
  if (!txns.length) return (
    <div className="txn-empty">
      <div className="empty-icon">↕</div>
      <p>No transactions yet</p>
      <span>Add money or send to someone to get started</span>
    </div>
  );
  return (
    <div className="txn-list">
      {txns.map((t, i) => <TxnItem key={t._id || i} t={t} idx={i} />)}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════
export default function Dashboard() {
  const { user: authUser, logout } = useAuth();
  const navigate = useNavigate();

  const [user,       setUser]       = useState(authUser);
  const [txns,       setTxns]       = useState([]);
  const [txnLoading, setTxnLoading] = useState(true);
  const [balLoading, setBalLoading] = useState(true);
  const [modal,      setModal]      = useState(null);
  const [toast,      setToast]      = useState('');
  const [activeTab,  setActiveTab]  = useState('home');

  // ── Fetch fresh balance from DB — fixes stale balance bug ─────────────────
  useEffect(() => {
    if (!authUser?.id) return;
    setBalLoading(true);
    fetch(`${API}/api/user/${authUser.id}`)
      .then(r => r.json())
      .then(data => { if (data.id) setUser(data); })
      .catch(() => {})
      .finally(() => setBalLoading(false));
  }, [authUser?.id]);

  const loadTxns = useCallback(async () => {
    if (!authUser?.id) return;
    setTxnLoading(true);
    try {
      const res  = await fetch(`${API}/api/transactions/${authUser.id}`);
      const data = await res.json();
      setTxns(data.transactions || []);
    } catch {}
    finally { setTxnLoading(false); }
  }, [authUser?.id]);

  useEffect(() => { loadTxns(); }, [loadTxns]);

  const onAddSuccess = (bal, txnId) => {
    setUser(u => ({ ...u, balance: bal }));
    setModal(null);
    setToast(`✓ Money added! ${txnId}`);
    loadTxns();
  };

  const onSendSuccess = (bal, txnId, name) => {
    setUser(u => ({ ...u, balance: bal }));
    setModal(null);
    setToast(`✓ Sent to ${name}! ${txnId}`);
    loadTxns();
  };

  const totalIn  = txns.filter(t => t.type === 'credit').reduce((s, t) => s + t.amount, 0);
  const totalOut = txns.filter(t => t.type === 'debit') .reduce((s, t) => s + t.amount, 0);
  const initials = (user?.name || 'U').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  const hour     = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="dash-root">

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">N</div>
          <span className="brand-name">NovaPay</span>
        </div>

        <nav className="sidebar-nav">
          {[
            { id: 'home', icon: '⬡', label: 'Overview'    },
            { id: 'txns', icon: '↕', label: 'Transactions' },
          ].map(item => (
            <button
              key={item.id}
              className={`nav-btn ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-profile">
            <div className="profile-avatar">{initials}</div>
            <div className="profile-info">
              <div className="profile-name">{user?.name}</div>
              <div className="profile-email">{user?.email}</div>
            </div>
          </div>
          <button className="signout-btn" onClick={() => { logout(); navigate('/'); }}>
            ← Sign out
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="dash-main">

        {activeTab === 'home' && (
          <div className="tab-content">

            {/* Greeting */}
            <div className="greeting-row">
              <div>
                <h1 className="greeting-text">
                  {greeting}, <span className="greeting-name">{user?.name?.split(' ')[0]}</span>
                </h1>
                <p className="greeting-sub">Here's your financial summary</p>
              </div>
              <div className="header-actions">
                <button className="hdr-action-btn add-btn" onClick={() => setModal('add')}>
                  ＋ Add Money
                </button>
                <button className="hdr-action-btn send-btn" onClick={() => setModal('send')}>
                  → Send
                </button>
              </div>
            </div>

            {/* Stats Row */}
            <div className="stats-row">
              {/* Balance Card */}
              <div className="balance-card">
                <div className="balance-glow" />
                <div className="balance-grid-lines" />
                <div className="balance-top">
                  <div className="balance-label-row">
                    <span className="balance-label">Total Balance</span>
                    <span className="status-dot-wrap">
                      <span className="status-dot" />
                      Active
                    </span>
                  </div>
                  <div className="acct-no-badge">{user?.account_no || '——'}</div>
                </div>
                <div className="balance-figure">
                  {balLoading
                    ? <div className="bal-skeleton" />
                    : fmt(user?.balance ?? 0)
                  }
                </div>
                <div className="balance-flows">
                  <div className="flow-item">
                    <div className="flow-arrow credit">↓</div>
                    <div>
                      <div className="flow-label">Money In</div>
                      <div className="flow-amount credit">{fmt(totalIn)}</div>
                    </div>
                  </div>
                  <div className="flow-sep" />
                  <div className="flow-item">
                    <div className="flow-arrow debit">↑</div>
                    <div>
                      <div className="flow-label">Money Out</div>
                      <div className="flow-amount debit">{fmt(totalOut)}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Action Tiles */}
              <div className="quick-tiles">
                <button className="quick-tile" onClick={() => setModal('add')}>
                  <div className="tile-ico add-ico">＋</div>
                  <div className="tile-text">
                    <div className="tile-name">Add Money</div>
                    <div className="tile-hint">Top up your wallet</div>
                  </div>
                  <div className="tile-arrow">›</div>
                </button>
                <button className="quick-tile" onClick={() => setModal('send')}>
                  <div className="tile-ico send-ico">→</div>
                  <div className="tile-text">
                    <div className="tile-name">Send Money</div>
                    <div className="tile-hint">Transfer instantly</div>
                  </div>
                  <div className="tile-arrow">›</div>
                </button>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="section">
              <div className="section-hdr">
                <h2 className="section-title">Recent Activity</h2>
                <button className="view-all-btn" onClick={() => setActiveTab('txns')}>
                  View all →
                </button>
              </div>
              <TxnList txns={txns.slice(0, 6)} loading={txnLoading} />
            </div>
          </div>
        )}

        {activeTab === 'txns' && (
          <div className="tab-content">
            <div className="greeting-row">
              <div>
                <h1 className="greeting-text">Transactions</h1>
                <p className="greeting-sub">{txns.length} records total</p>
              </div>
            </div>
            <div className="section">
              <TxnList txns={txns} loading={txnLoading} />
            </div>
          </div>
        )}
      </main>

      {modal === 'add'  && <AddMoneyModal  user={user} onClose={() => setModal(null)} onSuccess={onAddSuccess}  />}
      {modal === 'send' && <SendMoneyModal user={user} onClose={() => setModal(null)} onSuccess={onSendSuccess} />}
      {toast && <Toast msg={toast} onDone={() => setToast('')} />}
    </div>
  );
}