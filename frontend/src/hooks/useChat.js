import { useState, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8000';

export const useChat = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hello! I'm your Maintenance Intelligence Assistant. Ask me about costs, risks, defects, or building insights!",
      timestamp: new Date().toISOString(),
      suggestions: [
        "What are the most expensive defects?",
        "Show me high-risk systems",
        "Which buildings have most issues?",
        "What defects are trending?"
      ]
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const sendMessage = useCallback(async (userMessage, filters = {}) => {
    if (!userMessage.trim()) return;

    console.log('Sending message:', userMessage);

    // Add user message
    const userMsg = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      console.log('Making API request to:', `${API_BASE_URL}/api/chat`);

      // Build conversation history from messages (exclude initial greeting and current message)
      const conversationHistory = messages
        .slice(1) // Skip initial greeting
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 300 second timeout (Ollama needs time for 2 API calls with tool execution)

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: conversationHistory,
          session_id: sessionId,
          filters
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Response data:', data);

      // Update session ID from backend
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      // Add assistant response
      const assistantMsg = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        suggestions: data.suggestions || [],
        data: data.data || null,
        chart_type: data.chart_type || null
      };

      setMessages(prev => [...prev, assistantMsg]);
      setLoading(false);

    } catch (err) {
      console.error('Chat error:', err);

      let errorMessage = err.message;
      if (err.name === 'AbortError') {
        errorMessage = 'Request timeout - the server took too long to respond. Please try again.';
      }

      setError(errorMessage);

      // Add error message
      const errorMsg = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date().toISOString(),
        suggestions: [
          "What are the most expensive defects?",
          "Show me high-risk systems"
        ]
      };

      setMessages(prev => [...prev, errorMsg]);
      setLoading(false);
    }
  }, [messages, sessionId]);

  const clearChat = useCallback(() => {
    setMessages([
      {
        role: 'assistant',
        content: "👋 Hello! I'm your Maintenance Intelligence Assistant. Ask me about costs, risks, defects, or building insights!",
        timestamp: new Date().toISOString(),
        suggestions: [
          "What are the most expensive defects?",
          "Show me high-risk systems",
          "Which buildings have most issues?",
          "What defects are trending?"
        ]
      }
    ]);
    setError(null);
    setSessionId(null); // Reset session on clear
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearChat
  };
};
