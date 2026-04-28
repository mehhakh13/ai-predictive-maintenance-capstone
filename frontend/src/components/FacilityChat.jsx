import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, Loader, AlertCircle, Lock, ChevronDown } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const SUGGESTIONS = [
  'Which subsystems are highest risk next month?',
  'Summarize recurring HVAC defects this semester',
  'What should we inspect before winter?',
  'Compare planned vs. unplanned maintenance costs',
];

const INTENT_LABELS = {
  risk_query:     { label: 'Risk data', color: '#ef4444' },
  cost_query:     { label: 'Cost data', color: '#10b981' },
  defect_query:   { label: 'Defect themes', color: '#f59e0b' },
  recommendation: { label: 'Risk + Cost + Defects', color: '#8b5cf6' },
  general:        { label: 'General', color: '#64748b' },
};

export default function FacilityChat() {
  const [messages, setMessages]       = useState([]);
  const [input, setInput]             = useState('');
  const [streaming, setStreaming]     = useState(false);
  const [buildings, setBuildings]     = useState([]);
  const [months, setMonths]           = useState([]);
  const [selBuilding, setSelBuilding] = useState('');
  const [selMonth, setSelMonth]       = useState('');
  const [apiError, setApiError]       = useState(null);
  const bottomRef                     = useRef(null);
  const abortRef                      = useRef(null);

  // Load filter options
  useEffect(() => {
    fetch(`${API_BASE}/chat/buildings`)
      .then(r => r.json())
      .then(d => setBuildings(d.buildings || []))
      .catch(() => setApiError('Cannot reach the backend. Start the FastAPI server first.'));

    fetch(`${API_BASE}/chat/months`)
      .then(r => r.json())
      .then(d => setMonths(d.months || []))
      .catch(() => {});
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const appendBot = useCallback((id, text, intent) => {
    setMessages(prev => {
      const idx = prev.findIndex(m => m.id === id);
      if (idx === -1) {
        return [...prev, { id, role: 'bot', text, intent }];
      }
      const updated = [...prev];
      updated[idx] = { ...updated[idx], text, intent };
      return updated;
    });
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || streaming) return;

    const userMsg = { id: Date.now(), role: 'user', text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setStreaming(true);
    setApiError(null);

    const botId = Date.now() + 1;
    appendBot(botId, '', null);

    const body = {
      message: text.trim(),
      building_id: selBuilding || null,
      month: selMonth ? parseInt(selMonth.split('-')[1], 10) : null,
    };

    try {
      abortRef.current = new AbortController();
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        appendBot(botId, `Error: ${err.detail || res.statusText}`, 'general');
        setStreaming(false);
        return;
      }

      const intent = res.headers.get('X-Intent') || 'general';
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const chunk = line.slice(6);
          if (chunk === '[DONE]') break;
          if (chunk.startsWith('[ERROR:')) {
            accumulated += `\n${chunk}`;
          } else {
            accumulated += chunk.replace(/\\n/g, '\n');
          }
          appendBot(botId, accumulated, intent);
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        appendBot(botId, 'Connection lost. Please check the backend server.', 'general');
      }
    } finally {
      setStreaming(false);
    }
  }, [streaming, selBuilding, selMonth, appendBot]);

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <Bot size={24} color="#8b5cf6" />
          <div>
            <h1 style={styles.title}>Facility Advisor</h1>
            <p style={styles.subtitle}>Ask about risk, defects, or maintenance costs</p>
          </div>
        </div>
        <div style={styles.ndaBadge}>
          <Lock size={12} />
          <span>NDA-safe · anonymized data only</span>
        </div>
      </div>

      {/* Filter bar */}
      <div style={styles.filterBar}>
        <div style={styles.filterGroup}>
          <ChevronDown size={14} color="#94a3b8" />
          <select
            style={styles.select}
            value={selBuilding}
            onChange={e => setSelBuilding(e.target.value)}
          >
            <option value="">All buildings</option>
            {buildings.map(b => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>
        <div style={styles.filterGroup}>
          <ChevronDown size={14} color="#94a3b8" />
          <select
            style={styles.select}
            value={selMonth}
            onChange={e => setSelMonth(e.target.value)}
          >
            <option value="">All months</option>
            {months.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      {apiError && (
        <div style={styles.apiError}>
          <AlertCircle size={16} />
          <span>{apiError}</span>
        </div>
      )}

      {/* Message thread */}
      <div style={styles.thread}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <Bot size={48} color="#333" style={{ marginBottom: 16 }} />
            <p style={styles.emptyTitle}>Ask a question about your facilities</p>
            <p style={styles.emptySubtitle}>
              Data is aggregated and anonymized — no raw work orders are shared.
            </p>
            <div style={styles.chips}>
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  style={styles.chip}
                  onClick={() => sendMessage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div
            key={msg.id}
            style={{
              ...styles.messageRow,
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            {msg.role === 'bot' && (
              <div style={styles.avatar}>
                <Bot size={16} color="#8b5cf6" />
              </div>
            )}

            <div style={{ maxWidth: '70%' }}>
              <div
                style={
                  msg.role === 'user' ? styles.bubbleUser : styles.bubbleBot
                }
              >
                {msg.text || (
                  <span style={styles.thinkingDots}>
                    <span>.</span><span>.</span><span>.</span>
                  </span>
                )}
              </div>

              {msg.role === 'bot' && msg.intent && (
                <div style={styles.contextPill}>
                  <span
                    style={{
                      ...styles.pillDot,
                      backgroundColor: INTENT_LABELS[msg.intent]?.color || '#64748b',
                    }}
                  />
                  <span style={styles.pillText}>
                    {INTENT_LABELS[msg.intent]?.label || msg.intent} · anonymized
                  </span>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div style={{ ...styles.avatar, backgroundColor: '#1a1a1a' }}>
                <User size={16} color="#94a3b8" />
              </div>
            )}
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips (after first message, show below thread) */}
      {messages.length > 0 && !streaming && (
        <div style={styles.chipsBottom}>
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              style={styles.chip}
              onClick={() => sendMessage(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <form onSubmit={handleSubmit} style={styles.inputBar}>
        <input
          style={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask about risk, costs, or defect patterns…"
          disabled={streaming}
        />
        <button
          type="submit"
          disabled={!input.trim() || streaming}
          style={{
            ...styles.sendBtn,
            opacity: (!input.trim() || streaming) ? 0.4 : 1,
          }}
        >
          {streaming ? <Loader size={18} style={styles.spin} /> : <Send size={18} />}
        </button>
      </form>
    </div>
  );
}

/* ─── Styles ─────────────────────────────────────────────────────────────── */
const styles = {
  page: {
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 60px)',
    maxWidth: 900,
    margin: '0 auto',
    padding: '0 1rem',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1.25rem 0 0.75rem',
    borderBottom: '1px solid #1a1a1a',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  title: {
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#e2e8f0',
    margin: 0,
  },
  subtitle: {
    fontSize: '0.75rem',
    color: '#64748b',
    margin: 0,
  },
  ndaBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    fontSize: '0.6875rem',
    color: '#10b981',
    background: 'rgba(16,185,129,0.1)',
    border: '1px solid rgba(16,185,129,0.3)',
    borderRadius: '9999px',
    padding: '0.25rem 0.75rem',
  },
  filterBar: {
    display: 'flex',
    gap: '0.75rem',
    padding: '0.75rem 0',
    borderBottom: '1px solid #1a1a1a',
  },
  filterGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    background: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '0.375rem',
    padding: '0.25rem 0.625rem',
  },
  select: {
    background: 'transparent',
    border: 'none',
    color: '#e2e8f0',
    fontSize: '0.8125rem',
    cursor: 'pointer',
    outline: 'none',
  },
  apiError: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#ef4444',
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: '0.5rem',
    padding: '0.75rem 1rem',
    margin: '0.75rem 0',
    fontSize: '0.875rem',
  },
  thread: {
    flex: 1,
    overflowY: 'auto',
    padding: '1rem 0',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    textAlign: 'center',
    padding: '3rem 1rem',
  },
  emptyTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#e2e8f0',
    margin: '0 0 0.5rem',
  },
  emptySubtitle: {
    fontSize: '0.875rem',
    color: '#64748b',
    margin: '0 0 2rem',
  },
  chips: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    justifyContent: 'center',
  },
  chipsBottom: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    padding: '0.5rem 0',
    borderTop: '1px solid #1a1a1a',
  },
  chip: {
    background: '#1a1a1a',
    border: '1px solid #333',
    color: '#94a3b8',
    borderRadius: '9999px',
    padding: '0.375rem 0.875rem',
    fontSize: '0.8125rem',
    cursor: 'pointer',
    transition: 'all 0.15s',
    whiteSpace: 'nowrap',
  },
  messageRow: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '0.5rem',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: '50%',
    background: 'rgba(139,92,246,0.15)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  bubbleUser: {
    background: '#333',
    color: '#e2e8f0',
    borderRadius: '1rem 1rem 0.25rem 1rem',
    padding: '0.75rem 1rem',
    fontSize: '0.9375rem',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  bubbleBot: {
    background: '#1a1a1a',
    color: '#e2e8f0',
    border: '1px solid #2a2a2a',
    borderRadius: '1rem 1rem 1rem 0.25rem',
    padding: '0.75rem 1rem',
    fontSize: '0.9375rem',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    minWidth: 80,
    minHeight: 42,
  },
  contextPill: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    marginTop: '0.375rem',
    paddingLeft: '0.25rem',
  },
  pillDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    flexShrink: 0,
  },
  pillText: {
    fontSize: '0.6875rem',
    color: '#64748b',
  },
  thinkingDots: {
    display: 'inline-flex',
    gap: 3,
    color: '#64748b',
    animation: 'pulse 1.2s ease-in-out infinite',
  },
  inputBar: {
    display: 'flex',
    gap: '0.5rem',
    padding: '0.75rem 0 1rem',
    borderTop: '1px solid #1a1a1a',
  },
  input: {
    flex: 1,
    background: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '0.5rem',
    color: '#e2e8f0',
    padding: '0.625rem 1rem',
    fontSize: '0.9375rem',
    outline: 'none',
  },
  sendBtn: {
    background: '#8b5cf6',
    border: 'none',
    borderRadius: '0.5rem',
    color: '#fff',
    width: 42,
    height: 42,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    flexShrink: 0,
    transition: 'opacity 0.15s',
  },
  spin: {
    animation: 'spin 1s linear infinite',
  },
};
