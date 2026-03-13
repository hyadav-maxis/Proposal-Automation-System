import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiJson, downloadFile } from '../api';
import { useToast } from '../components/Toast';
import './Proposals.css';

export default function Proposals() {
  const showToast = useToast();
  const [searchParams] = useSearchParams();
  const [proposals, setProposals] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState('');
  const [locationFilter, setLocationFilter] = useState('all');
  const [minDbSize, setMinDbSize] = useState('all');
  const [maxDbSize, setMaxDbSize] = useState('all');
  const [sortKey, setSortKey] = useState('created_at');
  const [sortDir, setSortDir] = useState(-1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // modals
  const [viewModal, setViewModal] = useState(null);
  const [deleteModal, setDeleteModal] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (searchParams.has('updated')) {
      setTimeout(() => showToast('✅ Proposal updated & pricing recalculated!', 'success'), 600);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadProposals(locationFilter, search, minDbSize, maxDbSize);
    }, 300);
    return () => clearTimeout(timer);
  }, [locationFilter, search, minDbSize, maxDbSize]);

  async function loadProposals(loc = 'all', q = '', minSz = 'all', maxSz = 'all') {
    setLoading(true);
    setError(null);
    try {
      let url = '/api/proposals';
      const params = new URLSearchParams();
      if (loc && loc !== 'all') params.append('location', loc);
      if (minSz && minSz !== 'all') {
        const val = minSz.endsWith('tb') ? parseFloat(minSz) * 1000 : minSz;
        params.append('min_db_size', val);
      }
      if (maxSz && maxSz !== 'all') {
        const val = maxSz.endsWith('tb') ? parseFloat(maxSz) * 1000 : maxSz;
        params.append('max_db_size', val);
      }
      if (q) params.append('q', q);
      if (params.toString()) url += `?${params.toString()}`;
      
      const data = await apiJson(url);
      setProposals(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // filtering + sorting
  useEffect(() => {
    let f = proposals;
    if (search) {
      const q = search.toLowerCase();
      f = proposals.filter(p =>
        (p.proposal_number || '').toLowerCase().includes(q) ||
        (p.client_name || '').toLowerCase().includes(q) ||
        (p.project_name || '').toLowerCase().includes(q) ||
        (p.client_email || '').toLowerCase().includes(q)
      );
    }
    f = [...f].sort((a, b) => {
      let av = a[sortKey], bv = b[sortKey];
      if (sortKey === 'total_price') { av = parseFloat(av || 0); bv = parseFloat(bv || 0); }
      else if (sortKey === 'created_at') { av = new Date(av); bv = new Date(bv); }
      else { av = (av || '').toString().toLowerCase(); bv = (bv || '').toString().toLowerCase(); }
      if (av < bv) return -1 * sortDir;
      if (av > bv) return 1 * sortDir;
      return 0;
    });
    setFiltered(f);
  }, [proposals, search, sortKey, sortDir]);

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => d * -1);
    else { setSortKey(key); setSortDir(key === 'created_at' ? -1 : 1); }
  }

  // stats
  const total = proposals.length;
  const totalVal = proposals.reduce((s, p) => s + parseFloat(p.total_price || 0), 0);
  const avg = total > 0 ? totalVal / total : 0;
  const latest = total > 0
    ? new Date(proposals[0]?.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
    : '—';

  const money = v => `$${parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const moneyShort = v => `$${parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

  async function openView(id) {
    try {
      const p = await apiJson(`/api/proposals/${id}`);
      setViewModal(p);
    } catch (err) {
      showToast('Failed to load: ' + err.message, 'error');
    }
  }

  async function handleDelete() {
    if (!deleteModal) return;
    setDeleting(true);
    try {
      await apiJson(`/api/proposals/${deleteModal.id}`, { method: 'DELETE' });
      setDeleteModal(null);
      showToast('Proposal deleted successfully.', 'success');
      await loadProposals();
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      setDeleting(false);
    }
  }

  async function sendEmail(id) {
    try {
      showToast('✉️ Sending email to client…', 'info');
      await apiJson(`/api/proposals/${id}/send-email`, { method: 'POST' });
      showToast('✅ Email sent successfully!', 'success');
      loadProposals();
    } catch (err) {
      showToast('❌ Failed to send email: ' + err.message, 'error');
    }
  }

  async function handleDownload(url, filename) {
    try {
      showToast('⏳ Preparing download…', 'info');
      await downloadFile(url, filename);
      showToast('✅ Download started!', 'success');
    } catch (err) {
      showToast('❌ Download failed: ' + err.message, 'error');
    }
  }

  return (
    <div className="page wide">
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h1>All Proposals</h1>
          <p>View, manage, edit and download every generated proposal</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button 
            className="export-btn-pdf"
            onClick={() => {
              const minVal = minDbSize === 'all' ? '' : (minDbSize.endsWith('tb') ? parseFloat(minDbSize) * 1000 : minDbSize);
              const maxVal = maxDbSize === 'all' ? '' : (maxDbSize.endsWith('tb') ? parseFloat(maxDbSize) * 1000 : maxDbSize);
              let url = `/api/export/proposals/all/pdf?location=${locationFilter}&q=${encodeURIComponent(search)}`;
              if (minVal) url += `&min_db_size=${minVal}`;
              if (maxVal) url += `&max_db_size=${maxVal}`;
              handleDownload(url, 'all_proposals.pdf');
            }} 
          >
            📄 Export in PDF
          </button>
          <button 
            className="export-btn-excel"
            onClick={() => {
              const minVal = minDbSize === 'all' ? '' : (minDbSize.endsWith('tb') ? parseFloat(minDbSize) * 1000 : minDbSize);
              const maxVal = maxDbSize === 'all' ? '' : (maxDbSize.endsWith('tb') ? parseFloat(maxDbSize) * 1000 : maxDbSize);
              let url = `/api/export/proposals/all/excel?location=${locationFilter}&q=${encodeURIComponent(search)}`;
              if (minVal) url += `&min_db_size=${minVal}`;
              if (maxVal) url += `&max_db_size=${maxVal}`;
              handleDownload(url, 'all_proposals.xlsx');
            }} 
          >
            📊 Export in Excel
          </button>
          <Link to="/" className="create-proposal-btn">
            ＋ Create New Proposal
          </Link>
        </div>

      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
        {[['Total Proposals', total, false], ['Total Value', moneyShort(totalVal), true], ['Latest', latest, false], ['Avg. Proposal Size', total > 0 ? moneyShort(avg) : '—', true]].map(([label, value, isMoney]) => (
          <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '20px 24px', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'var(--accent)' }} />
            <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)', marginBottom: 8 }}>{label}</div>
            <div style={{ fontSize: '1.9rem', fontWeight: 800, color: isMoney ? 'var(--green)' : 'var(--text)' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Table Card */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden', boxShadow: 'var(--shadow)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 24px', borderBottom: '1px solid var(--border)', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 30, padding: '8px 16px', flex: 1, maxWidth: 340 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg>
            <input type="text" placeholder="Search by proposal #, client, project…" value={search} onChange={e => setSearch(e.target.value)}
              style={{ border: 'none', outline: 'none', background: 'transparent', color: 'var(--text)', fontSize: '0.875rem', fontFamily: "'Inter', sans-serif", width: '100%' }} />
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Database Size:</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <select 
                  value={minDbSize} 
                  onChange={e => setMinDbSize(e.target.value)}
                  style={{ 
                    background: 'var(--surface2)', 
                    border: '1px solid var(--border)', 
                    borderRadius: 30, 
                    padding: '8px 32px 8px 16px', 
                    fontSize: '0.875rem', 
                    color: 'var(--text)', 
                    outline: 'none', 
                    cursor: 'pointer',
                    appearance: 'none',
                    backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 12px center',
                    backgroundSize: '14px',
                    minWidth: '105px'
                  }}
                >
                  <option value="all">Min Size</option>
                  <option value="1">1 GB</option>
                  <option value="10">10 GB</option>
                  <option value="50">50 GB</option>
                  <option value="100">100 GB</option>
                  <option value="500">500 GB</option>
                  <option value="1tb">1 TB</option>
                </select>
                
                <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>-</span>

                <select 
                  value={maxDbSize} 
                  onChange={e => setMaxDbSize(e.target.value)}
                  style={{ 
                    background: 'var(--surface2)', 
                    border: '1px solid var(--border)', 
                    borderRadius: 30, 
                    padding: '8px 32px 8px 16px', 
                    fontSize: '0.875rem', 
                    color: 'var(--text)', 
                    outline: 'none', 
                    cursor: 'pointer',
                    appearance: 'none',
                    backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 12px center',
                    backgroundSize: '14px',
                    minWidth: '105px'
                  }}
                >
                  <option value="all">Max Size</option>
                  <option value="50">50 GB</option>
                  <option value="100">100 GB</option>
                  <option value="500">500 GB</option>
                  <option value="1tb">1 TB</option>
                  <option value="5tb">5 TB</option>
                  <option value="10tb">10 TB+</option>
                </select>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginLeft: 2 }}>GB/TB</span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Location:</span>
              <select 
                value={locationFilter} 
                onChange={e => setLocationFilter(e.target.value)}
                style={{ 
                  background: 'var(--surface2)', 
                  border: '1px solid var(--border)', 
                  borderRadius: 30, 
                  padding: '8px 32px 8px 16px', 
                  fontSize: '0.875rem', 
                  color: 'var(--text)', 
                  outline: 'none', 
                  cursor: 'pointer',
                  appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 12px center',
                  backgroundSize: '14px'
                }}
              >
                <option value="all">All Locations</option>
                <option value="standard">Standard</option>
                <option value="US_based">US Based</option>
              </select>
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', fontWeight: 500 }}>
              <strong style={{ color: 'var(--text-muted)' }}>{filtered.length}</strong> proposal{filtered.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'var(--surface2)', borderBottom: '1px solid var(--border)' }}>
                {[['proposal_number', '# Proposal No.'], ['client_name', 'Client', 'hide-sm'], ['project_name', 'Project', 'hide-sm'], ['resource_location', 'Location', 'hide-sm'], ['created_at', 'Created'], ['total_price', 'Amount'], ['status', 'Status', 'hide-sm']].map(([key, label, cls]) => (
                  <th key={key} onClick={() => handleSort(key)} className={cls || ''}
                    style={{ padding: '14px 18px', textAlign: 'left', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.7px', color: sortKey === key ? 'var(--accent)' : 'var(--text-muted)', whiteSpace: 'nowrap', cursor: 'pointer', userSelect: 'none' }}>
                    {label} <span style={{ marginLeft: 5 }}>↕</span>
                  </th>
                ))}
                <th style={{ padding: '14px 18px', width: 200 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7" style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div className="spinner" /><p>Loading proposals…</p>
                </td></tr>
              ) : error ? (
                <tr><td colSpan="7" style={{ padding: 80, textAlign: 'center' }}>
                  <div style={{ fontSize: '4rem', marginBottom: 16, opacity: 0.4 }}>⚠️</div>
                  <h3 style={{ color: 'var(--text-muted)', fontWeight: 600, marginBottom: 8 }}>Failed to load proposals</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.87rem' }}>{error}</p>
                  <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={loadProposals}>↺ Retry</button>
                </td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan="7" style={{ padding: 80, textAlign: 'center' }}>
                  <div style={{ fontSize: '4rem', marginBottom: 16, opacity: 0.4 }}>📋</div>
                  <h3 style={{ color: 'var(--text-muted)', fontWeight: 600, marginBottom: 8 }}>No proposals found</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.87rem' }}>Try adjusting your search or <Link to="/" style={{ color: 'var(--accent)' }}>create a new proposal</Link></p>
                </td></tr>
              ) : filtered.map(p => {
                const date = new Date(p.created_at).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' });
                const time = new Date(p.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
                const status = (p.status || 'draft').toLowerCase();
                return (
                  <tr key={p.id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.15s' }}>
                    <td style={{ padding: '14px 18px' }}><span style={{ fontWeight: 600, color: 'var(--accent)', letterSpacing: '0.3px', fontFamily: "'Courier New', monospace", fontSize: '0.8rem' }}>{p.proposal_number}</span></td>
                    <td className="hide-sm" style={{ padding: '14px 18px', maxWidth: 220 }}>
                      <div style={{ fontWeight: 600, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.client_name || '—'}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.client_email || ''}</div>
                    </td>
                    <td className="hide-sm" style={{ padding: '14px 18px', color: 'var(--text-muted)', fontSize: '0.83rem', maxWidth: 180, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.project_name || '—'}</td>
                    <td className="hide-sm" style={{ padding: '14px 18px' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', background: 'var(--surface2)', padding: '4px 10px', borderRadius: 20, border: '1px solid var(--border)' }}>
                        {(p.resource_location || 'standard').replace('US_based', 'US Based').replace('standard', 'Standard')}
                      </span>
                    </td>
                    <td style={{ padding: '14px 18px', color: 'var(--text-muted)', fontSize: '0.83rem' }}>
                      <div>{date}</div><div style={{ fontSize: '0.75rem' }}>{time}</div>
                    </td>
                    <td style={{ padding: '14px 18px' }}><span style={{ fontWeight: 600, color: 'var(--green)', fontVariantNumeric: 'tabular-nums' }}>{money(p.total_price)}</span></td>
                    <td className="hide-sm" style={{ padding: '14px 18px' }}><span className={`badge badge-${status}`}>{status}</span></td>
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <ActionBtn tip="View Details" cls="view" onClick={() => openView(p.id)}>👁</ActionBtn>
                        <ActionBtn tip="Edit" cls="edit" onClick={() => window.location.href = `/?edit=${p.id}`}>✏️</ActionBtn>
                        <ActionBtn tip="Send Email" cls="email" onClick={() => sendEmail(p.id)}>✉️</ActionBtn>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <DlBtn cls="pdf" onClick={() => handleDownload(`/api/export/proposal/${p.id}/pdf`, `proposal_${p.proposal_number}.pdf`)}>📄 PDF</DlBtn>
                          <DlBtn cls="xlsx" onClick={() => handleDownload(`/api/export/proposal/${p.id}/excel`, `proposal_${p.proposal_number}.xlsx`)}>📊 XLSX</DlBtn>
                        </div>
                        <ActionBtn tip="Delete" cls="delete" onClick={() => setDeleteModal(p)}>🗑</ActionBtn>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* View Modal */}
      {viewModal && <ViewModal proposal={viewModal} onClose={() => setViewModal(null)} onSendEmail={() => sendEmail(viewModal.id)} />}

      {/* Delete Modal */}
      {deleteModal && (
        <div className="modal-backdrop open" onClick={e => e.target === e.currentTarget && setDeleteModal(null)}>
          <div className="modal modal-sm">
            <div className="modal-header">
              <span className="modal-title">🗑️ Delete Proposal</span>
              <button className="modal-close" onClick={() => setDeleteModal(null)}>✕</button>
            </div>
            <div className="modal-body" style={{ textAlign: 'center' }}>
              <div style={{ width: 56, height: 56, background: '#fee2e2', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', margin: '0 auto 16px', border: '1.5px solid rgba(220, 38, 38, 0.2)' }}>🗑️</div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.7 }}>Are you sure you want to permanently delete proposal</p>
              <p style={{ marginTop: 8 }}><strong>{deleteModal.proposal_number}</strong>?</p>
              <p style={{ marginTop: 12, color: 'var(--red)' }}>This action <strong style={{ color: 'var(--red)' }}>cannot be undone</strong>. All pricing data and complexity breakdowns will be removed.</p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setDeleteModal(null)}>Cancel</button>
              <button className="btn btn-danger" disabled={deleting} onClick={handleDelete}>
                {deleting ? 'Deleting…' : '🗑️ Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ActionBtn({ tip, cls, onClick, children }) {
  return (
    <button onClick={onClick} data-tip={tip} title={tip}
      style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 34, height: 34, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-muted)', cursor: 'pointer', transition: 'all 0.18s', fontSize: '0.9rem', textDecoration: 'none', position: 'relative' }}>
      {children}
    </button>
  );
}

function DlBtn({ cls, onClick, children }) {
  return (
    <button onClick={onClick}
      style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '5px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 500, cursor: 'pointer', textDecoration: 'none', transition: 'all 0.2s' }}>
      {children}
    </button>
  );
}

function ViewModal({ proposal: p, onClose, onSendEmail }) {
  const money = v => `$${parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const pb = p.pricing_breakdown || {};
  const comps = p.pricing_components || [];
  const status = (p.status || 'draft').toLowerCase();

  return (
    <div className="modal-backdrop open" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-lg">
        <div className="modal-header">
          <span className="modal-title">Proposal — {p.proposal_number || p.id}</span>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
            {[['Proposal Number', p.proposal_number, 'mono'], ['Status', null, 'badge'], ['Client Name', p.client_name || '—'], ['Client Email', p.client_email || '—'], ['Project Name', p.project_name || '—'], ['Resource Location', (p.resource_location || 'standard').replace('US_based', 'US Based').replace('standard', 'Standard')], ['Total Amount', money(p.total_price), 'money'], ['Created At', new Date(p.created_at).toLocaleString()], ['Proposal ID', '#' + p.id]].map(([label, val, cls]) => (
              <div key={label}>
                <div style={{ fontSize: '0.73rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.7px', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
                {cls === 'badge'
                  ? <span className={`badge badge-${status}`}>{status}</span>
                  : <div style={{ fontWeight: cls === 'money' ? 700 : 500, color: cls === 'money' ? 'var(--green)' : cls === 'mono' ? 'var(--accent)' : 'var(--text)', fontSize: cls === 'money' ? '1.05rem' : '0.92rem', fontFamily: cls === 'mono' ? "'Courier New', monospace" : 'inherit' }}>{val}</div>
                }
              </div>
            ))}
          </div>

          <div style={{ margin: '20px 0 16px', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 10 }}>
            Pricing Breakdown <span style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.865rem' }}>
            <thead><tr style={{ background: 'var(--surface2)' }}>
              {['Component', 'Qty', 'Unit Price', 'Total'].map(h => <th key={h} style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px', borderBottom: '1px solid var(--border)' }}>{h}</th>)}
            </tr></thead>
            <tbody>
              {comps.length > 0 ? comps.map((c, i) => (
                <tr key={i}><td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)' }}>{c.component_name || c.component_type}</td>
                  <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)' }}>{parseFloat(c.quantity || 1).toLocaleString()}</td>
                  <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', color: 'var(--green)', fontWeight: 600 }}>{money(c.unit_price)}</td>
                  <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', color: 'var(--green)', fontWeight: 600 }}>{money(c.total_price)}</td></tr>
              )) : (
                <tr><td colSpan="4" style={{ padding: '10px 14px', color: 'var(--text-muted)', textAlign: 'center' }}>No components found</td></tr>
              )}
            </tbody>
            <tfoot>
              <tr style={{ background: 'var(--accent-glow)', fontWeight: 700 }}>
                <td colSpan="3" style={{ padding: '10px 14px', borderTop: '1px solid var(--accent)', color: 'var(--accent)' }}><strong>Grand Total</strong></td>
                <td style={{ padding: '10px 14px', borderTop: '1px solid var(--accent)', color: 'var(--green)', fontWeight: 600 }}>{money(p.total_price)}</td>
              </tr>
            </tfoot>
          </table>

          {pb.birt_complexity_breakdown && (
            <>
              <div style={{ margin: '20px 0 16px', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 10 }}>
                BIRT Complexity Breakdown <span style={{ flex: 1, height: 1, background: 'var(--border)' }} />
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.865rem' }}>
                <thead><tr style={{ background: 'var(--surface2)' }}>
                  {['Complexity', 'Reports', 'Price/Report', 'Total'].map(h => <th key={h} style={{ padding: '10px 14px', textAlign: 'left', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase' }}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {Object.entries(pb.birt_complexity_breakdown).sort((a, b) => parseInt(a[0]) - parseInt(b[0])).map(([sc, bd]) => (
                    <tr key={sc}><td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)' }}>Level {sc}</td>
                      <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)' }}>{bd.num_reports}</td>
                      <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', color: 'var(--green)', fontWeight: 600 }}>{money(bd.price_per_report)}</td>
                      <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', color: 'var(--green)', fontWeight: 600 }}>{money(bd.total_price)}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
          <button className="btn" style={{ background: 'var(--accent)', color: '#fff' }} onClick={onSendEmail}>✉️ Send Email</button>
          <a href={`/api/export/proposal/${p.id}/pdf`} target="_blank" rel="noreferrer" className="btn-danger-text">📄 PDF</a>
          <a href={`/api/export/proposal/${p.id}/excel`} target="_blank" rel="noreferrer" className="btn" style={{ background: 'linear-gradient(135deg,#22c55e,#16a34a)', color: '#fff' }}>📊 Excel</a>
        </div>
      </div>
    </div>
  );
}
