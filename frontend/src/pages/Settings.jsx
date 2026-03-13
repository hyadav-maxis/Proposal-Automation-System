import { useState, useEffect, useRef } from 'react';
import { apiJson, apiFetch } from '../api';
import { useToast } from '../components/Toast';
import './Settings.css';

export default function Settings() {
  const showToast = useToast();
  const [tab, setTab] = useState('branding');

  return (
    <div className="page settings-page">
      <div className="page-header">
        <h1>⚙️ Settings</h1>
        <p>Manage application settings, branding, and email templates.</p>
      </div>

      <div className="settings-tabs">
        {[['branding', '🖼️ Branding'], ['email-templates', '✉️ Email Templates']].map(([key, label]) => (
          <button key={key} className={`tab-btn ${tab === key ? 'active' : ''}`} onClick={() => setTab(key)}>{label}</button>
        ))}
      </div>

      {tab === 'branding' && <BrandingTab showToast={showToast} />}
      {tab === 'email-templates' && <EmailTemplatesTab showToast={showToast} />}
    </div>
  );
}

/* ── Branding Tab ─────────────────────────────────────── */
function BrandingTab({ showToast }) {
  const [logoUrl, setLogoUrl] = useState(null);
  const [predefined, setPredefined] = useState([]);
  const [selectedLogoId, setSelectedLogoId] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [selectedName, setSelectedName] = useState('');
  const [selectedThumb, setSelectedThumb] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [applying, setApplying] = useState(false);
  const fileRef = useRef(null);

  useEffect(() => { loadLogoStatus(); loadPredefinedLogos(); }, []);

  async function loadLogoStatus() {
    try {
      const data = await apiJson('/api/settings/logo');
      setLogoUrl(data.has_logo ? data.url : null);
    } catch { }
  }

  async function loadPredefinedLogos() {
    try {
      const data = await apiJson('/api/settings/predefined-logos');
      setPredefined(data.logos || []);
    } catch { }
  }

  async function applyPredefined() {
    if (!selectedLogoId) return;
    setApplying(true);
    try {
      const data = await apiJson('/api/settings/logo/select', {
        method: 'POST', body: JSON.stringify({ logo_id: selectedLogoId }),
      });
      showToast(`${data.name} is now the active company logo!`, 'success');
      setLogoUrl(data.url);
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally { setApplying(false); }
  }

  async function uploadLogo() {
    if (!file) return;
    if (!file.type.match(/^image\/(png|jpeg|jpg)$/)) { showToast('Please choose a PNG or JPEG image.', 'error'); return; }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiFetch('/api/settings/logo', { method: 'POST', body: formData });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Upload failed'); }
      showToast('Logo uploaded and set as active!', 'success');
      setFile(null);
      setSelectedLogoId(null);
      setSelectedName('');
      setSelectedThumb('');
      await loadLogoStatus();
    } catch (err) {
      showToast('Upload failed: ' + err.message, 'error');
    } finally { setUploading(false); }
  }

  return (
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon">🖼️</div>
        <div><h2>Company Logo</h2><p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Appears at the top of proposal PDFs and exports.</p></div>
      </div>
      <div className="section-card-body">
        <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 8 }}>Current Active Logo</div>
        <div className="logo-preview-card">
          {logoUrl ? <img src={logoUrl} alt="Active company logo" style={{ maxHeight: 80, maxWidth: 220, objectFit: 'contain' }} /> : (
            <><div style={{ fontSize: '3rem', opacity: 0.3 }}>🖼️</div><p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No logo set. Choose or upload one below.</p></>
          )}
        </div>

        <div className="divider"><span>Option 1 — Choose a Predefined Logo</span></div>
        <div style={{ position: 'relative' }}>
          <div className={`logo-dropdown-trigger ${dropdownOpen ? 'open' : ''}`} onClick={() => setDropdownOpen(!dropdownOpen)}>
            {selectedThumb && <img src={selectedThumb} alt="" style={{ height: 28, width: 28, objectFit: 'contain', borderRadius: 4, marginRight: 8 }} />}
            <span>{selectedName || '— Select a logo —'}</span>
            <svg style={{ marginLeft: 'auto' }} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9" /></svg>
          </div>
          {dropdownOpen && (
            <div className="logo-dropdown-menu open">
              {predefined.length === 0 ? (
                <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: '0.85rem' }}>No predefined logos found.</div>
              ) : predefined.map(logo => (
                <div key={logo.id} className={`logo-dropdown-item ${selectedLogoId === logo.id ? 'selected' : ''}`}
                  onClick={() => { setSelectedLogoId(logo.id); setSelectedName(logo.name); setSelectedThumb(logo.url); setDropdownOpen(false); }}>
                  <img src={logo.url} alt={logo.name} style={{ height: 32, width: 32, objectFit: 'contain' }} loading="lazy" />
                  <div style={{ flex: 1 }}><div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{logo.name}</div><div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{logo.file || ''}</div></div>
                  {selectedLogoId === logo.id && <span style={{ color: 'var(--accent)' }}>✓</span>}
                </div>
              ))}
            </div>
          )}
        </div>
        <button className="btn btn-primary" style={{ marginTop: 12 }} disabled={!selectedLogoId || applying} onClick={applyPredefined}>
          {applying ? 'Applying…' : '✅ Use This Logo'}
        </button>

        <div className="divider"><span>Option 2 — Upload a Custom Logo</span></div>
        <div className="file-drop-zone" onClick={() => fileRef.current?.click()}>
          <input type="file" ref={fileRef} accept="image/png,image/jpeg,image/jpg" style={{ display: 'none' }}
            onChange={e => { if (e.target.files?.[0]) setFile(e.target.files[0]); }} />
          <div style={{ fontSize: '2rem', opacity: 0.3 }}>📁</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}><strong>Click to browse</strong> or drag & drop</div>
        </div>
        {file && <div style={{ marginTop: 8, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>📎 {file.name}</div>}
        <button className="btn btn-primary" style={{ marginTop: 12 }} disabled={!file || uploading} onClick={uploadLogo}>
          {uploading ? 'Uploading…' : '⬆️ Upload Logo'}
        </button>
      </div>
    </div>
  );
}

/* ── Email Template Utilities ─────────────────────────── */
const PREMIUM_HTML_FRAME = (content, logoUrl = '', subtitle = '') => `
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f8f9fc;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <div style="padding: 20px 0; text-align: center;">
      ${logoUrl ? `<img src="${logoUrl}" alt="Company Logo" style="max-height:80px; max-width:240px; object-fit:contain;" />` : ''}
    </div>
    <div style="max-width:600px;margin:0 auto 40px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,0.05);border:1px solid #eef0f5;">
      <div style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:40px;text-align:left;">
        <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:700;letter-spacing:-0.5px;">Proposal Ready</h1>
        ${subtitle ? `<p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;font-weight:500;">${subtitle}</p>` : ''}
      </div>
      <div style="padding:40px;font-size:16px;color:#334155;line-height:1.7;">
        ${content.replace(/\n/g, '<br>')}
      </div>
      <div style="background:#f1f5f9;padding:24px 40px;text-align:center;font-size:12px;color:#64748b;border-top:1px solid #e2e8f0;">
        <p style="margin:0;">This is an automated message from the <strong>Proposal Automation System</strong>.</p>
        <p style="margin:4px 0 0;">© ${new Date().getFullYear()} All Rights Reserved.</p>
      </div>
    </div>
  </body>
</html>
`;

/* ── Email Templates Tab ──────────────────────────────── */
function EmailTemplatesTab({ showToast }) {
  const [templates, setTemplates] = useState([]);
  const [activeTemplateId, setActiveTemplateId] = useState(null);
  const [placeholders, setPlaceholders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [logoUrl, setLogoUrl] = useState('');

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editId, setEditId] = useState(null);
  const [editName, setEditName] = useState('');
  const [editSubject, setEditSubject] = useState('');
  const [editBody, setEditBody] = useState('');
  const [editType, setEditType] = useState('CUSTOM');
  const [saving, setSaving] = useState(false);

  // Preview & Test
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState(null);
  const [testOpen, setTestOpen] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [sendingTest, setSendingTest] = useState(false);
  const [testTemplateId, setTestTemplateId] = useState(null);

  // Editor refs
  const bodyRef = useRef(null);
  const subjectRef = useRef(null);
  const activeRef = useRef(null);

  useEffect(() => { loadTemplates(); loadLogo(); }, []);

  async function loadLogo() {
    try {
      const data = await apiJson('/api/settings/logo');
      if (data.has_logo) setLogoUrl(data.url);
    } catch { }
  }

  async function loadTemplates() {
    setLoading(true);
    try {
      const data = await apiJson('/api/settings/email-templates');
      setTemplates(data.templates || []);
      setActiveTemplateId(data.active_template_id);
      setPlaceholders(data.placeholders || []);
    } catch (err) {
      showToast('Could not load templates: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  function openCreateModal() {
    setIsEditing(false);
    setEditId(null);
    setEditName('');
    setEditSubject('Proposal {{proposal_number}} — {{project_name}}');
    setEditBody('Dear {{client_name}},\n\nPlease find attached the proposal for the project "{{project_name}}".\n\nBest regards,\nYour Team');
    setEditType('CUSTOM');
    setModalOpen(true);
  }

  function openEditModal(tpl) {
    setIsEditing(true);
    setEditId(tpl.id);
    setEditName(tpl.template_name);
    setEditSubject(tpl.subject || '');
    setEditBody(tpl.body || '');
    setEditType(tpl.template_type);
    setModalOpen(true);
  }

  async function saveTemplate() {
    if (!editName.trim()) { showToast('Template name is required.', 'error'); return; }
    if (!editSubject.trim()) { showToast('Subject is required.', 'error'); return; }
    setSaving(true);
    try {
      if (isEditing) {
        await apiJson(`/api/settings/email-templates/${editId}`, {
          method: 'PUT',
          body: JSON.stringify({
            template_name: editName,
            subject: editSubject,
            body: editBody,
          }),
        });
        showToast('✅ Template updated!', 'success');
      } else {
        await apiJson('/api/settings/email-templates', {
          method: 'POST',
          body: JSON.stringify({
            template_name: editName,
            subject: editSubject,
            body: editBody,
            template_type: 'CUSTOM',
          }),
        });
        showToast('✅ Template created!', 'success');
      }
      setModalOpen(false);
      loadTemplates();
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      setSaving(false);
    }
  }

  async function deleteTemplate(id, name) {
    if (!confirm(`Delete template "${name}"? This cannot be undone.`)) return;
    try {
      await apiJson(`/api/settings/email-templates/${id}`, { method: 'DELETE' });
      showToast(`🗑️ Template "${name}" deleted`, 'success');
      loadTemplates();
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

  async function setActiveTemplate(id) {
    try {
      const data = await apiJson('/api/settings/email-templates/set-active', {
        method: 'POST',
        body: JSON.stringify({ template_id: id }),
      });
      showToast(`✅ ${data.message}`, 'success');
      setActiveTemplateId(id);
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

  function openPreview(tpl) {
    setPreviewTemplate(tpl);
    setPreviewOpen(true);
  }

  function openTestModal(tpl) {
    setTestTemplateId(tpl.id);
    setTestEmail('');
    setTestOpen(true);
  }

  async function sendTestEmail() {
    if (!testEmail.trim()) { showToast('Please enter a recipient email.', 'error'); return; }
    setSendingTest(true);
    try {
      await apiJson('/api/settings/email-templates/test', {
        method: 'POST',
        body: JSON.stringify({ to_email: testEmail, template_id: testTemplateId }),
      });
      showToast(`✅ Test email sent to ${testEmail}!`, 'success');
      setTestOpen(false);
    } catch (err) { showToast('Error: ' + err.message, 'error'); }
    finally { setSendingTest(false); }
  }

  function insertChip(token) {
    const el = activeRef.current === 'subject' ? subjectRef.current : bodyRef.current;
    if (!el) return;
    const start = el.selectionStart || el.value.length;
    const end = el.selectionEnd || el.value.length;
    const setter = activeRef.current === 'subject' ? setEditSubject : setEditBody;
    setter(v => v.slice(0, start) + token + v.slice(end));
    setTimeout(() => { el.focus(); el.setSelectionRange(start + token.length, start + token.length); }, 0);
  }

  const SAMPLE = { 
    client_name: 'John Doe', 
    proposal_number: 'PROP-20240311-120000', 
    project_name: 'Migration to Cloud Alpha', 
    total_price: '$12,500.00',
    logo_block: '' 
  };
  function applyPlaceholders(text, wrap = false) {
    if (!text) return '';
    let out = text;
    for (const [k, v] of Object.entries(SAMPLE)) {
      // Support {{key}}, {{ key }}, {{key }}, {{ key}}
      const tokens = [`{{${k}}}`, `{{ ${k} }}`, `{{${k} }}`, `{{ ${k}}}`];
      tokens.forEach(t => {
        out = out.replaceAll(t, v);
      });
    }
    if (wrap && !out.includes('<html')) {
      return PREMIUM_HTML_FRAME(out, logoUrl, SAMPLE.proposal_number);
    }
    return out;
  }

  const isHtml = (text) => /<[a-z][\s\S]*>/i.test(text || '');

  return (
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
        </div>
        <div style={{ flex: 1 }}>
          <h2>Email Templates</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            The active template is used for all outgoing proposal emails.
          </p>
        </div>
        <button className="btn btn-primary" style={{ padding: '8px 18px', fontSize: '0.82rem', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={openCreateModal}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Create Template
        </button>
      </div>
      <div className="section-card-body">
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Loading templates…</div>
        ) : templates.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '2.5rem', opacity: 0.3, marginBottom: 8 }}>✉️</div>
            <p>No templates found. The system default will be created automatically.</p>
          </div>
        ) : (
          <div className="template-card-list">
            {templates.map(tpl => {
              const isActive = tpl.id === activeTemplateId;
              const isSystem = tpl.template_type === 'SYSTEM';
              return (
                <div key={tpl.id} className={`template-card ${isActive ? 'template-card-active' : ''}`}>
                  <div className="template-card-top">
                    <div className="template-card-left">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <h4 className="template-card-name">{tpl.template_name}</h4>
                        <span className={`template-type-badge ${isSystem ? 'badge-system' : 'badge-custom'}`}>
                          {isSystem ? (<><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg> SYSTEM</>) : (<><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg> CUSTOM</>)}
                        </span>
                        {isActive && (
                          <span className="template-active-badge">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                            ACTIVE
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="template-card-actions">
                      {!isActive && (
                        <button className="btn btn-primary btn-sm" onClick={() => setActiveTemplate(tpl.id)} title="Set as global template">
                          Set Active
                        </button>
                      )}
                      <button className="btn btn-ghost btn-sm btn-icon" onClick={() => openPreview(tpl)} title="Preview">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        Preview
                      </button>
                      {!isSystem && (
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={() => openEditModal(tpl)} title="Edit">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                          Edit
                        </button>
                      )}
                      <button className="btn btn-ghost btn-sm btn-icon" onClick={() => openTestModal(tpl)} title="Send test email">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                        Test
                      </button>
                      {!isSystem && (
                        <button className="btn btn-ghost btn-sm btn-icon btn-danger-ghost" onClick={() => deleteTemplate(tpl.id, tpl.template_name)} title="Delete">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="template-card-preview">
                    <p className="template-card-subject">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, verticalAlign: 'text-bottom', marginRight: 4, opacity: 0.5 }}><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                      {(tpl.subject || '').substring(0, 60)}{(tpl.subject || '').length > 60 ? '…' : ''}
                    </p>
                    <p className="template-card-body-preview">
                      {(tpl.body || '').substring(0, 100).replace(/<[^>]+>/g, '')}{(tpl.body || '').length > 100 ? '…' : ''}
                    </p>
                  </div>
                  {tpl.updated_at && (
                    <p className="template-card-meta">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'text-bottom', marginRight: 3, opacity: 0.6 }}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                      Last updated: {new Date(tpl.updated_at).toLocaleString()}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Create / Edit Modal ────────────────────────── */}
      {modalOpen && (
        <div className="modal-backdrop open" onClick={e => e.target === e.currentTarget && setModalOpen(false)}>
          <div className="modal modal-lg">
            <div className="modal-header">
              <span className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {isEditing ? (
                  <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg> Edit Template</>
                ) : (
                  <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Create New Template</>
                )}
              </span>
              <button className="modal-close" onClick={() => setModalOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              {/* Placeholder chips */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 600, marginBottom: 6, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Quick Insert Placeholder
                </div>
                <div className="chip-bar">
                  {[
                    ['{{client_name}}', '👤 Name'], 
                    ['{{proposal_number}}', '🔢 Prop #'], 
                    ['{{project_name}}', '📁 Project'],
                    ['{{total_price}}', '💰 Price']
                  ].map(([token, label]) => (
                    <span key={token} className="chip" onClick={() => insertChip(token)} title={`Insert ${token}`}>{label}</span>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Template Name <span style={{ color: 'var(--red)', fontWeight: 700 }}>*</span></label>
                <input
                  type="text"
                  className="form-control"
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                  placeholder="e.g. Welcome Email, Follow-Up Template…"
                />
              </div>

              <div className="form-group">
                <label>Email Subject <span style={{ color: 'var(--red)', fontWeight: 700 }}>*</span></label>
                <input
                  type="text"
                  className="form-control"
                  ref={subjectRef}
                  value={editSubject}
                  onChange={e => setEditSubject(e.target.value)}
                  onFocus={() => activeRef.current = 'subject'}
                  placeholder="Proposal {{proposal_number}} — {{project_name}}"
                />
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <label style={{ marginBottom: 0 }}>Email Body</label>
                  <span style={{ fontSize: '0.75rem', color: isHtml(editBody) ? 'var(--accent)' : 'var(--text-muted)' }}>
                    {isHtml(editBody) ? '✨ HTML Detected' : '📝 Plain Text (auto-wrapped in professional layout)'}
                  </span>
                </div>
                <textarea
                  className="form-control"
                  ref={bodyRef}
                  value={editBody}
                  onChange={e => setEditBody(e.target.value)}
                  onFocus={() => activeRef.current = 'body'}
                  rows="12"
                  placeholder="Dear {{client_name}},&#10;&#10;Type your email message here…"
                  style={{ fontFamily: isHtml(editBody) ? "'Courier New', monospace" : "'Inter', sans-serif" }}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost btn-icon" onClick={() => {
                setPreviewTemplate({ template_name: editName, subject: editSubject, body: editBody });
                setPreviewOpen(true);
              }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                Preview
              </button>
              <div style={{ flex: 1 }} />
              <button className="btn btn-ghost" onClick={() => setModalOpen(false)}>Cancel</button>
              <button className="btn btn-primary btn-icon" disabled={saving} onClick={saveTemplate}>
                {saving ? 'Saving…' : (
                  <><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg> Save Template</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Preview Modal ──────────────────────────────── */}
      {previewOpen && previewTemplate && (
        <div className="modal-backdrop open" style={{ zIndex: 1100 }} onClick={e => e.target === e.currentTarget && setPreviewOpen(false)}>
          <div className="modal modal-lg">
            <div className="modal-header">
              <span className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                Preview — {previewTemplate.template_name}
              </span>
              <button className="modal-close" onClick={() => setPreviewOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="email-mockup">
                <div className="email-mockup-bar">
                  <span className="email-mockup-dots"><span className="em-red" /><span className="em-amber" /><span className="em-green" /></span>
                  <span>Email Preview — sample data</span>
                </div>
                <div className="email-mockup-subject">
                  <strong>{applyPlaceholders(previewTemplate.subject || 'No subject', false)}</strong><br />
                  <span>To: <strong>john.doe@example.com</strong></span>
                </div>
                <div style={{ padding: 0 }} dangerouslySetInnerHTML={{ __html: applyPlaceholders(previewTemplate.body || '', true) }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Test Email Modal ──────────────────────────── */}
      {testOpen && (
        <div className="modal-backdrop open" style={{ zIndex: 1100 }} onClick={e => e.target === e.currentTarget && setTestOpen(false)}>
          <div className="modal modal-sm">
            <div className="modal-header">
              <span className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                Send Test Email
              </span>
              <button className="modal-close" onClick={() => setTestOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: 16 }}>
                A test email will be sent using sample data<br />
                (<em>John Doe / PROP-20240305-120000 / My Test Project</em>).
              </p>
              <div className="form-group">
                <label>Recipient Email</label>
                <input type="email" className="form-control" value={testEmail} onChange={e => setTestEmail(e.target.value)} placeholder="you@example.com" />
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-primary btn-icon" disabled={sendingTest} onClick={sendTestEmail}>
                  {sendingTest ? 'Sending…' : (
                    <><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Send Test Email</>
                  )}
                </button>
                <button className="btn btn-ghost" onClick={() => setTestOpen(false)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
