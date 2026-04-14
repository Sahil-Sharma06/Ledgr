import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../lib/api";

type TransactionType = "income" | "expense";

interface Transaction {
  id: number;
  amount: number;
  type: TransactionType;
  category: string;
  note: string | null;
  date: string;
}

interface Balance {
  income: number;
  expense: number;
  balance: number;
}

const CATEGORIES = ["Food", "Transport", "Shopping", "Housing", "Health", "Entertainment", "Salary", "Freelance", "Other"];
const PAGE_SIZE = 10;

export default function DashboardPage() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [balance, setBalance] = useState<Balance>({ income: 0, expense: 0, balance: 0 });
  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);

  // ── Filter & Pagination state ─────────────────────────────────────────────
  // These drive the query params sent to GET /transactions/
  const [typeFilter, setTypeFilter] = useState<TransactionType | "">("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [page, setPage] = useState(0); // page 0 → skip=0, page 1 → skip=10, etc.
  const [hasMore, setHasMore] = useState(true); // whether there are more pages

  // Form state
  const [form, setForm] = useState({ amount: "", type: "income" as TransactionType, category: "Other", note: "" });

  // useCallback memoizes fetchTransactions so it can safely be in useEffect deps
  const fetchTransactions = useCallback(async (currentPage: number) => {
    setLoading(true);

    // Build query string params object — only include non-empty values
    const params: Record<string, string | number> = {
      skip: currentPage * PAGE_SIZE,
      limit: PAGE_SIZE,
    };
    if (typeFilter)     params.type     = typeFilter;
    if (categoryFilter) params.category = categoryFilter;

    // axios serialises the params object into ?skip=0&limit=10&type=income etc.
    const res = await api.get("/transactions/", { params });
    setTransactions(res.data);
    // If we got fewer than PAGE_SIZE results, there's no next page
    setHasMore(res.data.length === PAGE_SIZE);
    setLoading(false);
  }, [typeFilter, categoryFilter]);

  // Fetch balance once (balance always covers ALL transactions, not filtered view)
  async function fetchBalance() {
    const res = await api.get("/transactions/balance");
    setBalance(res.data);
  }

  // Re-fetch transactions whenever filters or page changes
  useEffect(() => {
    fetchTransactions(page);
  }, [fetchTransactions, page]);

  // Fetch balance once on mount
  useEffect(() => {
    fetchBalance();
  }, []);

  // When filters change, reset to page 0 before fetching
  function applyFilters() {
    setPage(0);
    // fetchTransactions will run via the useEffect above since page just changed
  }

  function clearFilters() {
    setTypeFilter("");
    setCategoryFilter("");
    setPage(0);
  }

  function logout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  function openAdd() {
    setEditTarget(null);
    setForm({ amount: "", type: "income", category: "Other", note: "" });
    setShowModal(true);
  }

  function openEdit(tx: Transaction) {
    setEditTarget(tx);
    setForm({ amount: String(tx.amount), type: tx.type, category: tx.category, note: tx.note ?? "" });
    setShowModal(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload = { amount: parseFloat(form.amount), type: form.type, category: form.category, note: form.note || null };
    if (editTarget) {
      await api.put(`/transactions/${editTarget.id}`, payload);
    } else {
      await api.post("/transactions/", payload);
    }
    setShowModal(false);
    fetchTransactions(page);
    fetchBalance();
  }

  async function handleDelete(id: number) {
    await api.delete(`/transactions/${id}`);
    fetchTransactions(page);
    fetchBalance();
  }

  const fmt = (n: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

  const isFiltered = typeFilter || categoryFilter;

  return (
    <div className="dash-root">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="auth-logo" style={{ fontSize: "1.4rem", width: 40, height: 40 }}>₹</div>
          <span className="auth-logo-text">Ledgr</span>
        </div>
        <nav className="sidebar-nav">
          <button className="sidebar-nav-item active" id="nav-dashboard">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
            Dashboard
          </button>
        </nav>
        <button className="sidebar-logout" id="logout-btn" onClick={logout}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          Logout
        </button>
      </aside>

      {/* Main */}
      <main className="dash-main">
        <header className="dash-header">
          <div>
            <h1 className="dash-heading">Overview</h1>
            <p className="dash-subheading">Your financial snapshot</p>
          </div>
          <button id="add-transaction-btn" className="add-btn" onClick={openAdd}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Add Transaction
          </button>
        </header>

        {/* Balance Cards */}
        <div className="stats-grid">
          <div className="stat-card stat-balance">
            <p className="stat-label">Net Balance</p>
            <p className="stat-value">{fmt(balance.balance)}</p>
            <div className="stat-glow balance-glow" />
          </div>
          <div className="stat-card stat-income">
            <p className="stat-label">Total Income</p>
            <p className="stat-value income-value">{fmt(balance.income)}</p>
            <div className="stat-glow income-glow" />
          </div>
          <div className="stat-card stat-expense">
            <p className="stat-label">Total Expenses</p>
            <p className="stat-value expense-value">{fmt(balance.expense)}</p>
            <div className="stat-glow expense-glow" />
          </div>
        </div>

        {/* Transactions Section */}
        <div className="tx-section">
          <div className="tx-section-header">
            <h2 className="tx-heading">Transactions</h2>

            {/* ── Filter Bar ─────────────────────────────────────────────── */}
            <div className="filter-bar">
              <select
                id="filter-type"
                className="filter-select"
                value={typeFilter}
                onChange={(e) => { setTypeFilter(e.target.value as TransactionType | ""); setPage(0); }}
              >
                <option value="">All types</option>
                <option value="income">Income</option>
                <option value="expense">Expense</option>
              </select>

              <select
                id="filter-category"
                className="filter-select"
                value={categoryFilter}
                onChange={(e) => { setCategoryFilter(e.target.value); setPage(0); }}
              >
                <option value="">All categories</option>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>

              {isFiltered && (
                <button className="filter-clear-btn" id="clear-filters-btn" onClick={clearFilters} title="Clear filters">
                  ✕ Clear
                </button>
              )}
            </div>
          </div>

          {loading ? (
            // ── Skeleton loading state ──────────────────────────────────────
            <div className="tx-list">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="tx-row skeleton-row">
                  <div className="skeleton-dot" />
                  <div className="skeleton-meta">
                    <div className="skeleton-line w-24" />
                    <div className="skeleton-line w-40" />
                  </div>
                  <div className="skeleton-amount" />
                </div>
              ))}
            </div>
          ) : transactions.length === 0 ? (
            <div className="tx-empty">
              {isFiltered ? (
                <>
                  <p>No transactions match the current filters.</p>
                  <button className="filter-clear-btn" onClick={clearFilters} style={{ marginTop: "1rem" }}>Clear filters</button>
                </>
              ) : (
                <>
                  <p>No transactions yet.</p>
                  <button className="add-btn" onClick={openAdd} style={{ marginTop: "1rem" }}>Add your first one</button>
                </>
              )}
            </div>
          ) : (
            <>
              <div className="tx-list">
                {transactions.map((tx) => (
                  <div key={tx.id} className="tx-row">
                    <div className={`tx-type-dot ${tx.type}`} />
                    <div className="tx-meta">
                      <span className="tx-category">{tx.category}</span>
                      {tx.note && <span className="tx-note">{tx.note}</span>}
                    </div>
                    <div className="tx-info">
                      <span className="tx-date">{new Date(tx.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>
                      <span className={`tx-amount ${tx.type}`}>
                        {tx.type === "income" ? "+" : "-"}{fmt(tx.amount)}
                      </span>
                    </div>
                    <div className="tx-actions">
                      <button className="tx-action-btn" id={`edit-${tx.id}`} onClick={() => openEdit(tx)} title="Edit">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button className="tx-action-btn danger" id={`delete-${tx.id}`} onClick={() => handleDelete(tx.id)} title="Delete">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* ── Pagination Controls ───────────────────────────────────── */}
              <div className="pagination">
                <button
                  id="prev-page-btn"
                  className="page-btn"
                  onClick={() => setPage((p) => p - 1)}
                  disabled={page === 0}
                >
                  ← Prev
                </button>
                <span className="page-info">Page {page + 1}</span>
                <button
                  id="next-page-btn"
                  className="page-btn"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasMore}
                >
                  Next →
                </button>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{editTarget ? "Edit Transaction" : "New Transaction"}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="type-toggle">
                <button type="button" id="type-income" className={`type-btn ${form.type === "income" ? "active-income" : ""}`} onClick={() => setForm({ ...form, type: "income" })}>Income</button>
                <button type="button" id="type-expense" className={`type-btn ${form.type === "expense" ? "active-expense" : ""}`} onClick={() => setForm({ ...form, type: "expense" })}>Expense</button>
              </div>

              <div className="field-group">
                <label className="field-label">Amount (₹)</label>
                <input className="field-input" type="number" min="0.01" step="0.01" placeholder="0.00" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
              </div>

              <div className="field-group">
                <label className="field-label">Category</label>
                <select className="field-input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>

              <div className="field-group">
                <label className="field-label">Note (optional)</label>
                <input className="field-input" type="text" placeholder="Add a note..." value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
              </div>

              <button id="submit-transaction-btn" type="submit" className="auth-btn">
                {editTarget ? "Save Changes" : "Add Transaction"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
