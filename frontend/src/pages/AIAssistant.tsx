import { useState, useRef, useEffect } from 'react';
import { useAIStore } from '../stores/aiStore';
import { formatCost, formatTokens } from '../utils/format';
import { Bot, Send, User, Upload } from 'lucide-react';
import { aiApi } from '../services/api';

export default function AIAssistant() {
  const { history, query, loading } = useAIStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput('');
    await query(text);
  };

  const [ingestText, setIngestText] = useState('');
  const [ingestStatus, setIngestStatus] = useState('');

  const handleIngest = async () => {
    if (!ingestText.trim()) return;
    setIngestStatus('Ingesting...');
    try {
      const docs = ingestText.split('\n').filter(Boolean).map(line => ({
        content: line,
        metadata: { source: 'manual' },
      }));
      await aiApi.ingest(docs);
      setIngestStatus(`Ingested ${docs.length} document(s) successfully`);
      setIngestText('');
    } catch {
      setIngestStatus('Ingest failed');
    }
  };

  return (
    <div className="page ai-page">
      <h1 className="page-title">AI Assistant</h1>

      <details style={{ marginBottom: 16 }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: 14, marginBottom: 8 }}>
          Ingest Documents (teach the AI)
        </summary>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <textarea
            className="form-input"
            placeholder="Paste document content here (one line = one document)..."
            value={ingestText}
            onChange={(e) => setIngestText(e.target.value)}
            rows={4}
            style={{ resize: 'vertical' }}
          />
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn btn-primary btn-sm" onClick={handleIngest}>
            <Upload size={14} /> Ingest
          </button>
          {ingestStatus && <span className="text-muted">{ingestStatus}</span>}
        </div>
      </details>

      <div className="chat-container">
        <div className="chat-messages">
          {history.length === 0 && (
            <div className="chat-empty">
              <Bot size={48} />
              <p>Ask me anything about your system, users, or data!</p>
            </div>
          )}
          {history.map((entry, i) => (
            <div key={i}>
              <div className="chat-bubble user-bubble">
                <div className="bubble-icon">
                  <User size={16} />
                </div>
                <div className="bubble-content">{entry.query}</div>
              </div>
              <div className="chat-bubble ai-bubble">
                <div className="bubble-icon">
                  <Bot size={16} />
                </div>
                <div className="bubble-content">
                  <p>{entry.response}</p>
                  {entry.metadata && (
                    <div className="bubble-meta">
                      <span>
                        Latency:{' '}
                        {(entry.metadata.latency_ms / 1000).toFixed(2)}s
                      </span>
                      <span>
                        Tokens: {formatTokens(entry.metadata.total_tokens)}
                      </span>
                      <span>
                        Cost: {formatCost(entry.metadata.estimated_cost)}
                      </span>
                      <span>
                        Chunks: {entry.metadata.context_chunks}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble ai-bubble">
              <div className="bubble-icon">
                <Bot size={16} />
              </div>
              <div className="bubble-content">
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            className="form-input"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !input.trim()}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
