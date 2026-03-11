import { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { apiJson, apiFetch } from '../api';
import { useToast } from '../components/Toast';

export default function NewProposal() {
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit') ? parseInt(searchParams.get('edit'), 10) : null;
  const showToast = useToast();

  const [form, setForm] = useState({
    clientName: '', clientEmail: '', projectName: '',
    databaseSize: '', numberOfRuns: '', deploymentType: '',
    resourceLocation: '', sourceDialect: '', targetDialect: '',
    hasWhereClauses: false, hasBirtReports: false, hasMaximoUpgrade: false,
    maximoHasAddon: false, addonDb2Installation: false,
    addonBirtInstallation: false, addonMaximoInstallation: false,
    sqlContent: '',
  });
  const [comp, setComp] = useState([0, 0, 0, 0, 0, 0]);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [editBanner, setEditBanner] = useState('');
  const fileRef = useRef(null);

  const totalReports = comp.reduce((s, v) => s + v, 0);

  useEffect(() => {
    if (editId) loadEditData(editId);
  }, [editId]);

  async function loadEditData(proposalId) {
    setEditBanner('Loading proposal data…');
    try {
      const p = await apiJson(`/api/proposals/${proposalId}`);
      setEditBanner(`Editing: ${p.proposal_number || '#' + proposalId} — ${p.client_name}`);
      setForm({
        clientName: p.client_name || '',
        clientEmail: p.client_email || '',
        projectName: p.project_name || '',
        databaseSize: p.database_size_gb != null ? p.database_size_gb : '',
        numberOfRuns: p.number_of_runs != null ? p.number_of_runs : '',
        deploymentType: p.deployment_type || '',
        resourceLocation: (p.resource_location === 'usa_based' ? 'US_based' : p.resource_location) || 'standard',
        sourceDialect: p.source_dialect || '',
        targetDialect: p.target_dialect || '',
        hasWhereClauses: !!p.has_where_clauses,
        hasBirtReports: !!p.has_birt_reports,
        hasMaximoUpgrade: !!p.has_maximo_upgrade,
        maximoHasAddon: !!p.maximo_has_addon,
        addonDb2Installation: !!p.addon_db2_installation,
        addonBirtInstallation: !!p.addon_birt_installation,
        addonMaximoInstallation: !!p.addon_maximo_installation,
        sqlContent: p.sql_content || '',
      });
      if (p.birt_complexity_distribution) {
        const c = [0, 0, 0, 0, 0, 0];
        for (let i = 0; i <= 5; i++) c[i] = p.birt_complexity_distribution[i] || 0;
        setComp(c);
      }
      setResult(null);
    } catch (err) {
      setEditBanner(`⚠️ Failed to load data: ${err.message}`);
    }
  }

  function updateField(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function updateComp(i, val) {
    setComp((c) => { const n = [...c]; n[i] = parseInt(val) || 0; return n; });
  }

  async function handleFileImport(event) {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await apiFetch('/api/proposals/import-complexity', { method: 'POST', body: formData });
      if (!res.ok) {
        const ct = res.headers.get('content-type');
        const err = ct?.includes('application/json') ? (await res.json()).detail : (await res.text()).substring(0, 200);
        throw new Error(err || 'Failed to import');
      }
      const data = await res.json();
      const c = [0, 0, 0, 0, 0, 0];
      if (data.complexity_distribution) {
        for (const [score, count] of Object.entries(data.complexity_distribution)) {
          if (parseInt(score) >= 0 && parseInt(score) <= 5) c[parseInt(score)] = count;
        }
      }
      setComp(c);
      showToast('File imported! Total reports: ' + data.total_reports, 'success');
      event.target.value = '';
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
      event.target.value = '';
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);

    let complexityDistribution = null;
    if (form.hasBirtReports) {
      complexityDistribution = {};
      for (let i = 0; i <= 5; i++) {
        if (comp[i] > 0) complexityDistribution[i] = comp[i];
      }
      if (!Object.keys(complexityDistribution).length) complexityDistribution = null;
    }

    const data = {
      client_name: form.clientName,
      client_email: form.clientEmail,
      project_name: form.projectName,
      database_size_gb: parseFloat(form.databaseSize),
      number_of_runs: parseInt(form.numberOfRuns),
      deployment_type: form.deploymentType,
      resource_location: form.resourceLocation || 'standard',
      has_where_clauses: form.hasWhereClauses,
      has_birt_reports: form.hasBirtReports,
      num_birt_reports: totalReports || 1,
      birt_complexity_distribution: complexityDistribution,
      has_maximo_upgrade: form.hasMaximoUpgrade,
      maximo_has_addon: form.maximoHasAddon,
      addon_db2_installation: form.addonDb2Installation,
      addon_birt_installation: form.addonBirtInstallation,
      addon_maximo_installation: form.addonMaximoInstallation,
      source_dialect: form.sourceDialect || null,
      target_dialect: form.targetDialect || null,
      sql_content: form.sqlContent || null,
    };

    const endpoint = editId ? `/api/proposals/${editId}/recalculate` : '/api/proposals/create';
    const method = editId ? 'PUT' : 'POST';

    try {
      const res = await apiJson(endpoint, { method, body: JSON.stringify(data) });
      if (editId) {
        window.location.href = '/proposals?updated=1';
      } else {
        setResult(res);
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  }

  async function sendEmailFromHome(id) {
    try {
      showToast('✉️ Sending email to client…', 'info');
      await apiJson(`/api/proposals/${id}/send-email`, { method: 'POST' });
      showToast('✅ Email sent successfully!', 'success');
    } catch (err) {
      showToast('❌ Failed: ' + err.message, 'error');
    }
  }

  const dialects = ['SQL Server', 'Oracle', 'DB2', 'MySQL', 'PostgreSQL'];

  return (
    <div className="page">
      {editId && (
        <div className="edit-banner">
          <div className="edit-banner-left">
            <span style={{ fontSize: '1.4rem' }}>✏️</span>
            <div>
              <strong>Edit Mode</strong>
              <div className="edit-banner-sub">{editBanner || 'Loading proposal data…'}</div>
            </div>
          </div>
          <Link to="/proposals" className="edit-banner-back">← Back to Proposals</Link>
        </div>
      )}

      <div className="page-header">
        <h1>{editId ? 'Edit Proposal' : 'New Proposal'}</h1>
        <p>Fill in the details below to generate a pricing proposal for your client.</p>
      </div>

      <div className="card">
        <div className="card-title">Client Information</div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Client Name *</label>
            <input type="text" className="form-control" placeholder="e.g. Acme Corporation" required
              value={form.clientName} onChange={(e) => updateField('clientName', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Client Email</label>
            <input type="email" className="form-control" placeholder="client@example.com"
              value={form.clientEmail} onChange={(e) => updateField('clientEmail', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Project Name *</label>
            <input type="text" className="form-control" placeholder="e.g. Database Migration 2026" required
              value={form.projectName} onChange={(e) => updateField('projectName', e.target.value)} />
          </div>
          <div className="two-column">
            <div className="form-group">
              <label>Database Size (GB) *</label>
              <input type="number" className="form-control" step="0.01" min="0.01" placeholder="e.g. 50" required
                value={form.databaseSize} onChange={(e) => updateField('databaseSize', e.target.value)} />
            </div>
            <div className="form-group">
              <label>Number of Runs *</label>
              <input type="number" className="form-control" min="1" placeholder="e.g. 3" required
                value={form.numberOfRuns} onChange={(e) => updateField('numberOfRuns', e.target.value)} />
            </div>
          </div>
          <div className="form-group">
            <label>Deployment Type *</label>
            <select className="form-control" required value={form.deploymentType}
              onChange={(e) => updateField('deploymentType', e.target.value)}>
              <option value="">Select deployment type…</option>
              <option value="inhouse_vm">In-house VM</option>
              <option value="client_premises">Client Premises</option>
            </select>
          </div>
          <div className="form-group">
            <label>Resource Location *</label>
            <select className="form-control" required value={form.resourceLocation}
              onChange={(e) => updateField('resourceLocation', e.target.value)}>
              <option value="" disabled>Select resource location…</option>
              <option value="standard">Other (standard pricing)</option>
              <option value="US_based">US-based resources</option>
            </select>
          </div>
          <div className="form-group">
            <label>Source Database Dialect</label>
            <select className="form-control" value={form.sourceDialect} onChange={(e) => updateField('sourceDialect', e.target.value)}>
              <option value="">Select…</option>
              {dialects.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Target Database Dialect</label>
            <select className="form-control" value={form.targetDialect} onChange={(e) => updateField('targetDialect', e.target.value)}>
              <option value="">Select…</option>
              {dialects.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>

          {/* Features & Add-ons */}
          <div className="card-title" style={{ marginTop: 8 }}>Features & Add-ons</div>
          <div className="form-group">
            <label className="checkbox-row" style={{ display: 'flex', textTransform: 'none', letterSpacing: 0, fontWeight: 'inherit', color: 'inherit', marginBottom: 0 }}>
              <input type="checkbox" checked={form.hasWhereClauses} onChange={(e) => updateField('hasWhereClauses', e.target.checked)} />
              <span>Migration contains WHERE clauses</span>
            </label>
          </div>
          <div className="form-group">
            <label className="checkbox-row" style={{ display: 'flex', textTransform: 'none', letterSpacing: 0, fontWeight: 'inherit', color: 'inherit', marginBottom: 0 }}>
              <input type="checkbox" checked={form.hasBirtReports} onChange={(e) => updateField('hasBirtReports', e.target.checked)} />
              <span>BIRT Reports conversion required</span>
            </label>
          </div>

          {form.hasBirtReports && (
            <div>
              <div className="card-title" style={{ marginTop: 12 }}>BIRT Reports Complexity</div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 12 }}>Enter number of reports for each complexity level.</p>
              <div className="complexity-grid">
                {['Level 0 — No Conversion', 'Level 1 — Minimal', 'Level 2 — Simple', 'Level 3 — Moderate', 'Level 4 — Complex', 'Level 5 — Very Complex'].map((label, i) => (
                  <div key={i} className="complexity-box">
                    <label>{label}</label>
                    <input type="number" min="0" value={comp[i]} onChange={(e) => updateComp(i, e.target.value)} />
                  </div>
                ))}
              </div>
              <div className="total-badge">Total Reports: <span>{totalReports}</span></div>
              <div className="import-box">
                <label>Import from CSV / Excel</label>
                <p>Upload a file with column: ComplexityScore or Complexity_Score</p>
                <input type="file" ref={fileRef} accept=".csv,.xlsx,.xls" style={{ display: 'none' }} onChange={handleFileImport} />
                <button type="button" className="btn-import" onClick={() => fileRef.current?.click()}>📁 Import CSV / Excel</button>
              </div>
            </div>
          )}

          <div className="form-group" style={{ marginTop: 8 }}>
            <label className="checkbox-row" style={{ display: 'flex', textTransform: 'none', letterSpacing: 0, fontWeight: 'inherit', color: 'inherit', marginBottom: 0 }}>
              <input type="checkbox" checked={form.hasMaximoUpgrade} onChange={(e) => { updateField('hasMaximoUpgrade', e.target.checked); if (!e.target.checked) updateField('maximoHasAddon', false); }} />
              <span>Maximo Upgrade Feature</span>
            </label>
          </div>

          {form.hasMaximoUpgrade && (
            <div className="form-group" style={{ marginLeft: 28 }}>
              <label className="checkbox-row" style={{ display: 'flex', textTransform: 'none', letterSpacing: 0, fontWeight: 'inherit', color: 'inherit', marginBottom: 0 }}>
                <input type="checkbox" checked={form.maximoHasAddon} onChange={(e) => updateField('maximoHasAddon', e.target.checked)} />
                <span>Add-on Present (additional fee applies)</span>
              </label>
            </div>
          )}

          <div className="card-title" style={{ marginTop: 16, fontSize: '0.9rem' }}>Add-On Installation Services</div>
          {[['addonDb2Installation', 'Db2 Installation'], ['addonBirtInstallation', 'Birt Installation'], ['addonMaximoInstallation', 'Maximo Installation']].map(([key, label]) => (
            <div key={key} className="form-group">
              <label className="checkbox-row" style={{ display: 'flex', textTransform: 'none', letterSpacing: 0, fontWeight: 'inherit', color: 'inherit', marginBottom: 0 }}>
                <input type="checkbox" checked={form[key]} onChange={(e) => updateField(key, e.target.checked)} />
                <span>{label}</span>
              </label>
            </div>
          ))}

          <div className="form-group" style={{ marginTop: 20 }}>
            <label>SQL Content (optional — for AI complexity analysis)</label>
            <textarea className="form-control" rows="4" placeholder="Paste SQL content here for AI complexity analysis…"
              value={form.sqlContent} onChange={(e) => updateField('sqlContent', e.target.value)} />
          </div>

          {editId && (
            <div style={{ marginTop: 4 }}>
              <Link to="/proposals" className="cancel-link" style={{ display: 'block', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem', textDecoration: 'none' }}>
                ✕ Cancel and return to proposals
              </Link>
            </div>
          )}

          <button type="submit" className="btn-submit" disabled={submitting}
            style={editId ? { background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' } : {}}>
            {submitting
              ? (editId ? 'Saving…' : 'Generating…')
              : (editId ? '💾 Save Changes' : '🚀 Generate Proposal')}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && <ResultsCard result={result} onSendEmail={sendEmailFromHome} />}
    </div>
  );
}

function ResultsCard({ result, onSendEmail }) {
  const pricing = result.pricing_breakdown;
  const money = (v) => `$${parseFloat(v || 0).toFixed(2)}`;

  const rows = [
    ['Database Size', pricing.database_size_price],
    ['Number of Runs', pricing.runs_price],
    ['Deployment Type', pricing.deployment_price],
  ];
  if (pricing.where_clauses_price > 0) rows.push(['WHERE Clauses', pricing.where_clauses_price]);
  if (pricing.birt_reports_price > 0) rows.push(['BIRT Reports', pricing.birt_reports_price]);
  if (pricing.maximo_upgrade_price > 0) rows.push(['Maximo Upgrade', pricing.maximo_upgrade_price]);
  if (pricing.addon_db2_installation_price > 0) rows.push(['Db2 Installation', pricing.addon_db2_installation_price]);
  if (pricing.addon_birt_installation_price > 0) rows.push(['Birt Installation', pricing.addon_birt_installation_price]);
  if (pricing.addon_maximo_installation_price > 0) rows.push(['Maximo Installation', pricing.addon_maximo_installation_price]);

  return (
    <div className="results-card">
      <h2>✅ Proposal Generated!</h2>
      <div className="proposal-info">
        <div className="info-chip">
          <label>Proposal Number</label>
          <div className="val">{result.proposal_number}</div>
        </div>
        <div className="info-chip">
          <label>Proposal ID</label>
          <div className="val">#{result.proposal_id}</div>
        </div>
      </div>

      <div className="download-row">
        <a href={`/api/export/proposal/${result.proposal_id}/pdf`} target="_blank" rel="noreferrer" className="btn-dl-lg pdf">📄 Download PDF</a>
        <a href={`/api/export/proposal/${result.proposal_id}/excel`} target="_blank" rel="noreferrer" className="btn-dl-lg excel">📊 Download Excel</a>
        <button onClick={() => onSendEmail(result.proposal_id)} className="btn-dl-lg email">✉️ Send Email</button>
      </div>

      <div className="card-title" style={{ marginBottom: 14 }}>Price Breakdown</div>
      <table className="price-breakdown-table">
        <tbody>
          {rows.map(([label, val]) => (
            <tr key={label}><td>{label}</td><td>{money(val)}</td></tr>
          ))}
          {pricing.us_resources_surcharge > 0 && (
            <tr style={{ color: 'var(--accent)' }}>
              <td>USA-Based Resources (+35%)</td>
              <td style={{ color: '#b45309', fontWeight: 700 }}>+{money(pricing.us_resources_surcharge)}</td>
            </tr>
          )}
          <tr><td><strong>Subtotal</strong></td><td><strong>{money(pricing.subtotal)}</strong></td></tr>
        </tbody>
      </table>

      {pricing.birt_complexity_breakdown && (
        <div>
          <h3 style={{ marginTop: 20, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text)', marginBottom: 10 }}>BIRT Reports Breakdown</h3>
          <table className="complexity-breakdown-table">
            <thead><tr><th>Level</th><th>Reports</th><th>Price / Report</th><th>Total</th></tr></thead>
            <tbody>
              {Object.entries(pricing.birt_complexity_breakdown).sort((a, b) => parseInt(a[0]) - parseInt(b[0])).map(([score, bd]) => (
                <tr key={score}><td>Level {score}</td><td>{bd.num_reports}</td><td>{money(bd.price_per_report)}</td><td>{money(bd.total_price)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="price-total-row">
        <span className="label">Total Price</span>
        <span className="amount">{money(pricing.total_price)}</span>
      </div>
    </div>
  );
}
