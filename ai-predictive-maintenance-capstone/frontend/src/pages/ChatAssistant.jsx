import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Trash2, TrendingUp, Loader } from 'lucide-react';
import { useChat } from '../hooks/useChat';
import ReactMarkdown from 'react-markdown';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import '../styles/chat.css';

const ChatAssistant = () => {
  const { messages, loading, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

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

  return (
    <div className="chat-page">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-content">
          <MessageCircle size={28} className="chat-icon" />
          <div>
            <h1 className="chat-title">Maintenance Assistant</h1>
            <p className="chat-subtitle">Ask questions about your maintenance data</p>
          </div>
        </div>
        <button onClick={clearChat} className="clear-chat-btn" title="Clear conversation">
          <Trash2 size={18} />
          Clear Chat
        </button>
      </div>

      {/* Messages Container */}
      <div className="chat-messages-container">
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`chat-message ${message.role}`}>
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

                {/* Chart rendering if data is provided */}
                {message.data && message.chart_type === 'cost_bar' && (
                  <div className="message-chart">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={message.data.chart_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="category" angle={-45} textAnchor="end" height={100} />
                        <YAxis />
                        <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                        <Legend />
                        <Bar dataKey="total_cost" fill="#8884d8" name="Total Cost" />
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
            <div className="chat-message assistant loading">
              <div className="message-header">
                <span className="message-role">🤖 Assistant</span>
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <Loader className="spinner" size={16} />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about costs, risks, defects, or buildings..."
            className="chat-input"
            disabled={loading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={loading || !input.trim()}
          >
            <Send size={20} />
          </button>
        </form>

        <div className="chat-footer-info">
          <TrendingUp size={14} />
          <span>Powered by your maintenance data • Phase 1: Keyword Intelligence</span>
        </div>
      </div>
    </div>
  );
};

export default ChatAssistant;
