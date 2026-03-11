import { useState, useEffect, useRef } from 'react';
import { apiJson, apiFetch } from '../api';
import { useToast } from '../components/Toast';
import './Chat.css';

export default function Chat() {
  const showToast = useToast();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [agentStatus, setAgentStatus] = useState('checking');
  const logRef = useRef(null);

  useEffect(() => { checkAgentStatus(); }, []);
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [messages]);

  async function checkAgentStatus() {
    try {
      const res = await apiFetch('/api/chat/status');
      if (res.ok) {
        const data = await res.json();
        const isOnline = data.available || data.status === 'ready' || data.status === 'ok';
        setAgentStatus(isOnline ? 'online' : 'offline');
      } else {
        setAgentStatus('offline');
      }
    } catch {
      setAgentStatus('offline');
    }
  }

  async function sendMessage(e) {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const userMsg = { role: 'user', content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setSending(true);

    try {
      const data = await apiJson('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ messages: newMessages.map(m => ({ role: m.role, content: m.content })) }),
      });

      const assistantMsg = { role: 'assistant', content: data.reply || data.content || 'No response.' };
      setMessages(prev => [...prev, assistantMsg]);

      if (data.proposal_data) {
        try {
          const proposalRes = await apiJson('/api/proposals/create', {
            method: 'POST',
            body: JSON.stringify(data.proposal_data),
          });
          const sysMsg = {
            role: 'system',
            proposalId: proposalRes.proposal_id,
            content: `✅ Proposal Created!\n\nProposal #${proposalRes.proposal_number}\nTotal: $${parseFloat(proposalRes.total_price || proposalRes.pricing_breakdown?.total_price || 0).toFixed(2)}`,
          };
          setMessages(prev => [...prev, sysMsg]);
        } catch (err) {
          showToast('Failed to create proposal: ' + err.message, 'error');
        }
      }
    } catch (err) {
      const errMsg = { role: 'system', content: '❌ Error: ' + err.message };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  }

  async function sendEmail(id) {
    try {
      showToast('✉️ Sending email to client…', 'info');
      await apiJson(`/api/proposals/${id}/send-email`, { method: 'POST' });
      showToast('✅ Email sent successfully!', 'success');
    } catch (err) {
      showToast('❌ Failed to send email: ' + err.message, 'error');
    }
  }

  function clearChat() {
    setMessages([]);
  }

  const statusColors = { online: '#16a34a', offline: '#dc2626', checking: '#d97706' };
  const statusLabels = { online: 'Online', offline: 'Offline', checking: 'Checking…' };

  return (
    <div className="page chat-page">
      <div className="page-header">
        <h1>🤖 AI Assistant</h1>
        <p>Describe a proposal scenario and let the AI generate it for you.</p>
      </div>

      {/* Status Bar */}
      <div className="chat-status-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: statusColors[agentStatus], boxShadow: `0 0 8px ${statusColors[agentStatus]}` }} />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Agent: {statusLabels[agentStatus]}</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" style={{ padding: '6px 14px', fontSize: '0.8rem' }} onClick={checkAgentStatus}>↻ Refresh</button>
          <button className="btn btn-ghost" style={{ padding: '6px 14px', fontSize: '0.8rem' }} onClick={clearChat}>🗑 Clear</button>
        </div>
      </div>

      {/* Chat Log */}
      <div className="chat-log" ref={logRef}>
        {messages.length === 0 && (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">🤖</div>
            <h3>Welcome!</h3>
            <p>Describe a proposal scenario, and I'll generate it for you.</p>
            <div className="prompt-examples">
              {[
                'Create a proposal for a 50GB database migration with 3 runs',
                'Generate a proposal for Acme Corp with BIRT reports',
                'Price a migration with Maximo upgrade and add-ons',
              ].map((ex, i) => (
                <button key={i} className="prompt-example" onClick={() => setInput(ex)}>{ex}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
            <div className="chat-msg-bubble">
              {msg.role === 'system' ? (
                <div>
                  <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\n/g, '<br>').replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: var(--accent)">$1</a>') }} />
                  {msg.proposalId && (
                    <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      <a href={`/api/export/proposal/${msg.proposalId}/pdf`} target="_blank" rel="noreferrer" className="chat-action-btn pdf">
                        📄 PDF
                      </a>
                      <a href={`/api/export/proposal/${msg.proposalId}/excel`} target="_blank" rel="noreferrer" className="chat-action-btn excel">
                        📊 Excel
                      </a>
                      <button onClick={() => sendEmail(msg.proposalId)} className="chat-action-btn email">
                        ✉️ Send Email
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-msg-bubble typing">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form className="chat-input-area" onSubmit={sendMessage}>
        <input type="text" className="chat-input" placeholder="Describe a proposal scenario…" value={input}
          onChange={e => setInput(e.target.value)} disabled={sending} />
        <button type="submit" className="chat-send-btn" disabled={!input.trim() || sending}>
          {sending ? <span className="spinner-sm" /> : '➤'}
        </button>
      </form>
    </div>
  );
}
