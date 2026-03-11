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
        <p>Manage application settings, branding, and configuration.</p>
      </div>

      <div className="settings-tabs">
        {[['branding', '🖼️ Branding'], ['global-email', '✉️ Global Template'], ['client-emails', '🌟 Personalized Templates']].map(([key, label]) => (
          <button key={key} className={`tab-btn ${tab === key ? 'active' : ''}`} onClick={() => setTab(key)}>{label}</button>
        ))}
      </div>

      {tab === 'branding' && <BrandingTab showToast={showToast} />}
      {tab === 'global-email' && <GlobalEmailTab showToast={showToast} />}
      {tab === 'client-emails' && <ClientEmailsTab showToast={showToast} />}
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

        {/* Predefined logos */}
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

        {/* Upload */}
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

/* ── Global Email Tab ──────────────────────────────────── */
function GlobalEmailTab({ showToast }) {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [mode, setMode] = useState('html');
  const [saving, setSaving] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [testOpen, setTestOpen] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [sendingTest, setSendingTest] = useState(false);
  const bodyRef = useRef(null);
  const subjectRef = useRef(null);
  const activeRef = useRef(null);

  useEffect(() => { loadTemplate(); }, []);

  async function loadTemplate() {
    try {
      const data = await apiJson('/api/settings/email-template');
      setSubject(data.subject || '');
      setBody(data.body || '');
      setMode(data.mode || 'html');
    } catch { showToast('Could not load email template.', 'error'); }
  }

  function insertChip(token) {
    const el = activeRef.current === 'subject' ? subjectRef.current : bodyRef.current;
    if (!el) return;
    const start = el.selectionStart || el.value.length;
    const end = el.selectionEnd || el.value.length;
    const setter = activeRef.current === 'subject' ? setSubject : setBody;
    setter(v => v.slice(0, start) + token + v.slice(end));
    setTimeout(() => { el.focus(); el.setSelectionRange(start + token.length, start + token.length); }, 0);
  }

  function wrapTag(tag) {
    const el = bodyRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selected = el.value.substring(start, end);
    let wrapped;
    if (tag === 'a') {
      const url = prompt('Enter URL:', 'https://');
      if (!url) return;
      wrapped = `<a href="${url}">${selected || 'Link Text'}</a>`;
    } else {
      wrapped = `<${tag}>${selected}</${tag}>`;
    }
    setBody(v => v.slice(0, start) + wrapped + v.slice(end));
  }

  async function saveTemplate() {
    if (!subject.trim()) { showToast('Subject cannot be empty.', 'error'); return; }
    setSaving(true);
    try {
      await apiJson('/api/settings/email-template', { method: 'POST', body: JSON.stringify({ subject, body, mode }) });
      showToast('✅ Global email template saved!', 'success');
    } catch (err) { showToast('Error: ' + err.message, 'error'); }
    finally { setSaving(false); }
  }

  async function sendTestEmail() {
    if (!testEmail.trim()) { showToast('Please enter a recipient email.', 'error'); return; }
    setSendingTest(true);
    try {
      await apiJson('/api/settings/email-template/test', {
        method: 'POST', body: JSON.stringify({ to_email: testEmail, subject: subject || null, body: body || null }),
      });
      showToast(`✅ Test email sent to ${testEmail}!`, 'success');
      setTestOpen(false);
    } catch (err) { showToast('Error: ' + err.message, 'error'); }
    finally { setSendingTest(false); }
  }

  const SAMPLE = { client_name: 'John Doe', proposal_number: 'PROP-20240305-120000', project_name: 'My Test Project', logo_block: '' };
  function applyPlaceholders(text) { let out = text; for (const [k, v] of Object.entries(SAMPLE)) out = out.replaceAll(`{{${k}}}`, v); return out; }

  return (
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon">✉️</div>
        <div><h2>Global Email Template</h2><p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Sent to all clients by default.</p></div>
      </div>
      <div className="section-card-body">
        <div style={{ fontSize: '0.78rem', fontWeight: 600, marginBottom: 8, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Insert Placeholder</div>
        <div className="chip-bar">
          {[['{{client_name}}', '👤 Client Name'], ['{{proposal_number}}', '🔢 Proposal No.'], ['{{project_name}}', '📁 Project Name'], ['{{logo_block}}', '🖼️ Company Logo']].map(([token, label]) => (
            <span key={token} className="chip" onClick={() => insertChip(token)}>{label}</span>
          ))}
        </div>

        <div className="form-group" style={{ marginTop: 14 }}>
          <label>Email Subject</label>
          <input type="text" className="form-control" ref={subjectRef} value={subject}
            onChange={e => setSubject(e.target.value)} onFocus={() => activeRef.current = 'subject'}
            placeholder="Proposal {{proposal_number}} — {{project_name}}" />
        </div>

        <div className="form-group" style={{ marginTop: 18 }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', marginBottom: 8, justifyContent: 'space-between' }}>
            <label style={{ marginBottom: 0 }}>Email Body</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.8rem' }}>
              <span style={{ color: mode === 'html' ? 'var(--accent)' : 'var(--text-muted)' }}>HTML Editor</span>
              <label className="switch"><input type="checkbox" checked={mode === 'plain'} onChange={() => setMode(m => m === 'html' ? 'plain' : 'html')} /><span className="slider" /></label>
              <span style={{ color: mode === 'plain' ? 'var(--accent)' : 'var(--text-muted)' }}>Plain Text</span>
            </div>
          </div>
          {mode === 'html' && (
            <div className="editor-toolbar">
              <button type="button" className="tool-btn" onClick={() => wrapTag('b')}><strong>B</strong></button>
              <button type="button" className="tool-btn" onClick={() => wrapTag('i')}><em>I</em></button>
              <div className="tool-divider" />
              <button type="button" className="tool-btn" onClick={() => wrapTag('a')}>🔗</button>
            </div>
          )}
          <textarea className="form-control" ref={bodyRef} value={body}
            onChange={e => setBody(e.target.value)} onFocus={() => activeRef.current = 'body'}
            rows="10" placeholder={mode === 'html' ? 'Enter HTML email body…' : 'Type your message here… no HTML needed.'} />
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 20, flexWrap: 'wrap' }}>
          <button className="btn btn-primary" disabled={saving} onClick={saveTemplate}>{saving ? 'Saving…' : '💾 Save Template'}</button>
          <button className="btn btn-ghost" onClick={() => setPreviewOpen(true)}>👁 Preview</button>
          <button className="btn btn-ghost" onClick={() => setTestOpen(true)}>🧪 Send Test Email</button>
          <button className="btn btn-ghost" style={{ marginLeft: 'auto' }} onClick={loadTemplate}>↺ Reset Default</button>
        </div>
      </div>

      {/* Preview Modal */}
      {previewOpen && (
        <div className="modal-backdrop open" onClick={e => e.target === e.currentTarget && setPreviewOpen(false)}>
          <div className="modal modal-lg">
            <div className="modal-header">
              <span className="modal-title">📧 Email Preview</span>
              <button className="modal-close" onClick={() => setPreviewOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="email-mockup">
                <div className="email-mockup-bar"><span className="email-mockup-dots"><span className="em-red" /><span className="em-amber" /><span className="em-green" /></span><span>Email Preview — sample data</span></div>
                <div className="email-mockup-subject"><strong>{applyPlaceholders(subject || 'No subject')}</strong><br /><span>To: <strong>john.doe@example.com</strong></span></div>
                <div style={{ padding: 20, fontSize: '0.9rem', lineHeight: 1.7 }} dangerouslySetInnerHTML={{ __html: mode === 'plain' ? applyPlaceholders(body).replace(/\n/g, '<br>') : applyPlaceholders(body) }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Test Email Modal */}
      {testOpen && (
        <div className="modal-backdrop open" onClick={e => e.target === e.currentTarget && setTestOpen(false)}>
          <div className="modal modal-sm">
            <div className="modal-header">
              <span className="modal-title">🧪 Send Test Email</span>
              <button className="modal-close" onClick={() => setTestOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: 16 }}>A test email will be sent using sample data<br />(<em>John Doe / PROP-20240305-120000 / My Test Project</em>).</p>
              <div className="form-group">
                <label>Recipient Email</label>
                <input type="email" className="form-control" value={testEmail} onChange={e => setTestEmail(e.target.value)} placeholder="you@example.com" />
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-primary" disabled={sendingTest} onClick={sendTestEmail}>{sendingTest ? 'Sending…' : '🚀 Send Test Email'}</button>
                <button className="btn btn-ghost" onClick={() => setTestOpen(false)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Client Templates Tab ────────────────────────────── */
function ClientEmailsTab({ showToast }) {
  const [templates, setTemplates] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmail, setEditingEmail] = useState('');
  const [editingSubject, setEditingSubject] = useState('');
  const [editingBody, setEditingBody] = useState('');
  const [isEdit, setIsEdit] = useState(false);

  useEffect(() => { loadClientTemplates(); }, []);

  async function loadClientTemplates() {
    try {
      const data = await apiJson('/api/settings/client-templates');
      setTemplates(data.templates || []);
    } catch (err) { console.error(err); }
  }

  function openAdd() {
    setEditingEmail(''); setEditingSubject(''); setEditingBody('');
    setIsEdit(false);
    setModalOpen(true);
  }

  function openEdit(t) {
    setEditingEmail(t.client_email); setEditingSubject(t.subject); setEditingBody(t.body);
    setIsEdit(true);
    setModalOpen(true);
  }

  async function saveOverride() {
    if (!editingEmail || !editingSubject || !editingBody) { showToast('All fields required', 'error'); return; }
    try {
      await apiJson('/api/settings/client-templates', {
        method: 'POST', body: JSON.stringify({ client_email: editingEmail, subject: editingSubject, body: editingBody }),
      });
      showToast('✅ Saved!', 'success');
      setModalOpen(false);
      loadClientTemplates();
    } catch (err) { showToast(err.message, 'error'); }
  }

  async function deleteOverride(email) {
    if (!confirm(`Delete override for ${email}?`)) return;
    try {
      await apiFetch(`/api/settings/client-templates/${email}`, { method: 'DELETE' });
      showToast(`Deleted ${email}`, 'success');
      loadClientTemplates();
    } catch { showToast('Delete failed', 'error'); }
  }

  return (
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon">🌟</div>
        <div style={{ flex: 1 }}>
          <h2>Personalized Templates</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Specific templates for particular client email addresses. These will override the Global Template.</p>
        </div>
        <button className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.8rem', whiteSpace: 'nowrap' }} onClick={openAdd}>➕ Create Custom Template</button>
      </div>
      <div className="section-card-body">
        {templates.length === 0 ? (
          <p style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>No client-specific templates found.</p>
        ) : (
          <div className="client-card-list">
            {templates.map((t, i) => (
              <div key={i} className="client-card">
                <div><h4 style={{ fontSize: '0.95rem', marginBottom: 2 }}>{t.client_email}</h4><p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t.subject.substring(0, 50)}{t.subject.length > 50 ? '…' : ''}</p></div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => openEdit(t)}>✏️ Edit</button>
                  <button className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: '0.8rem', color: 'var(--red)' }} onClick={() => deleteOverride(t.client_email)}>🗑️ Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {modalOpen && (
        <div className="modal-backdrop open" onClick={e => e.target === e.currentTarget && setModalOpen(false)}>
          <div className="modal modal-lg">
            <div className="modal-header">
              <span className="modal-title">{isEdit ? 'Edit Personalized Template' : '➕ Add Personalized Template'}</span>
              <button className="modal-close" onClick={() => setModalOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Client Email</label>
                <input type="email" className="form-control" value={editingEmail} readOnly={isEdit} onChange={e => setEditingEmail(e.target.value)} placeholder="client@example.com" />
              </div>
              <div className="form-group">
                <label>Override Subject</label>
                <input type="text" className="form-control" value={editingSubject} onChange={e => setEditingSubject(e.target.value)} placeholder="Subject line for this client..." />
              </div>
              <div className="form-group">
                <label>Override Body (HTML)</label>
                <textarea className="form-control" style={{ minHeight: 200 }} value={editingBody} onChange={e => setEditingBody(e.target.value)} placeholder="Custom HTML..." />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setModalOpen(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={saveOverride}>💾 Save Override</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
