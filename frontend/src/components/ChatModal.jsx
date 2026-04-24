import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, Minimize2, Maximize2, Loader } from 'lucide-react';
import { useChat } from '../hooks/useChat';
import ReactMarkdown from 'react-markdown';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import '../styles/chatModal.css';

const ChatModal = ({ isOpen, onClose }) => {
  const { messages, loading, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (!isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isMinimized]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      sendMessage(input);
      setInput('');
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (!loading) {
      sendMessage(suggestion);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      {!isMinimized && (
        <div className="chat-modal-backdrop" onClick={onClose} />
      )}

      {/* Chat Modal */}
      <div className={`chat-modal ${isMinimized ? 'minimized' : ''}`}>
        {/* Header */}
        <div className="chat-modal-header">
          <div className="chat-modal-header-content">
            <MessageCircle size={20} className="chat-modal-icon" />
            <div>
              <h2 className="chat-modal-title">AI Assistant</h2>
              <p className="chat-modal-subtitle">Ask about maintenance data</p>
            </div>
          </div>
          <div className="chat-modal-actions">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="chat-modal-btn"
              title={isMinimized ? 'Maximize' : 'Minimize'}
            >
              {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
            </button>
            <button onClick={onClose} className="chat-modal-btn" title="Close">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        {!isMinimized && (
          <>
            <div className="chat-modal-messages">
              {messages.map((message, index) => (
                <div key={index} className={`chat-modal-message ${message.role}`}>
                  <div className="message-header">
                    <span className="message-role">
                      {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
                    </span>
                    {message.timestamp && (
                      <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                    )}
                  </div>

                  <div className="message-content">
                    <ReactMarkdown>{message.content}</ReactMarkdown>

                    {/* Chart rendering */}
                    {message.data && message.chart_type === 'cost_bar' && (
                      <div className="message-chart">
                        <ResponsiveContainer width="100%" height={250}>
                          <BarChart data={message.data.chart_data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                            <YAxis />
                            <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                            <Legend />
                            <Bar dataKey="total_cost" fill="#667eea" name="Total Cost" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {/* Suggestions */}
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="message-suggestions">
                        <div className="suggestions-label">💡 Try asking:</div>
                        <div className="suggestions-grid">
                          {message.suggestions.map((suggestion, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSuggestionClick(suggestion)}
                              className="suggestion-chip"
                              disabled={loading}
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="chat-modal-message assistant loading">
                  <div className="message-header">
                    <span className="message-role">🤖 Assistant</span>
                  </div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <Loader className="spinner" size={16} />
                      <span>Analyzing data...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="chat-modal-input-container">
              <form onSubmit={handleSubmit} className="chat-modal-input-form">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about costs, risks, defects..."
                  className="chat-modal-input"
                  disabled={loading}
                />
                <button
                  type="submit"
                  className="chat-modal-send-btn"
                  disabled={loading || !input.trim()}
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default ChatModal;
