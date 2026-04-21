# Phase 2: AI-Powered Chat with History Restoration

This document describes the Phase 2 implementation of the chatbot with conversation history management.

## Overview

Phase 2 replaces the keyword-based chat system (Phase 1) with an AI-powered assistant using Claude 3.5 Sonnet with function calling capabilities. The assistant can intelligently query maintenance data and maintain conversation context across multiple messages.

## Key Features

### 1. AI-Powered Responses
- Uses Claude 3.5 Sonnet API for natural language understanding
- Function calling to query real data from FMUCD dataset
- Context-aware responses based on conversation history

### 2. Session Management
- Each conversation is stored in a session
- Sessions persist conversation history
- Multiple concurrent sessions supported
- Automatic session cleanup for old conversations

### 3. Function Calling Tools
The assistant has access to the following tool categories:

**Cost Tools:**
- `get_most_expensive_systems` - Top N most expensive systems
- `get_cheapest_systems` - Least expensive systems
- `get_cost_by_subsystem` - Cost details for specific subsystem

**Risk Tools:**
- `get_highest_risk_systems` - Systems with highest failure probability
- `get_risk_by_subsystem` - Risk details for specific subsystem

**Building Tools:**
- `get_top_buildings` - Buildings ranked by cost, risk, or event count
- `get_building_details` - Detailed stats for a specific building

**Trend Tools:**
- `get_monthly_trends` - Monthly trend data over time
- `get_trend_by_subsystem` - Subsystem-specific trends

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (React/Vue)    │
└────────┬────────┘
         │
         │ HTTP POST /api/chat
         ↓
┌─────────────────────────────┐
│   FastAPI Backend           │
│                             │
│  ┌─────────────────────┐   │
│  │ Session Manager     │   │
│  │ - Store sessions    │   │
│  │ - Track history     │   │
│  └─────────────────────┘   │
│           ↓                 │
│  ┌─────────────────────┐   │
│  │ LLM Service         │   │
│  │ - Claude API        │   │
│  │ - Function calling  │   │
│  └─────────────────────┘   │
│           ↓                 │
│  ┌─────────────────────┐   │
│  │ Tool Functions      │   │
│  │ - Cost tools        │   │
│  │ - Risk tools        │   │
│  │ - Building tools    │   │
│  │ - Trend tools       │   │
│  └─────────────────────┘   │
│           ↓                 │
│  ┌─────────────────────┐   │
│  │ Data Service        │   │
│  │ - Query FMUCD data  │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

## API Endpoints

### Chat Endpoint
```
POST /api/chat
```

**Request:**
```json
{
  "message": "What are the most expensive systems?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "Based on the data, here are the top 5 most expensive systems...",
  "suggestions": [
    "Which buildings have highest costs?",
    "Show me cost trends over time"
  ],
  "session_id": "abc-123-def-456",
  "data": {
    "chart_data": [...]
  },
  "chart_type": "cost_bar",
  "function_calls": ["get_most_expensive_systems"]
}
```

### Session Management Endpoints

**List all sessions:**
```
GET /api/sessions
```

**Get specific session:**
```
GET /api/sessions/{session_id}
```

**Create new session:**
```
POST /api/sessions
```

**Delete session:**
```
DELETE /api/sessions/{session_id}
```

## Setup Instructions

### 1. Environment Variables
Create a `.env` file in the backend directory:

```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
```

Get your API key from: https://console.anthropic.com/

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Backend
```bash
cd backend
python main.py
```

The server will start on `http://localhost:8000`

### 4. Test the API

**Start a conversation:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the most expensive systems?"
  }'
```

**Continue the conversation:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which buildings have these systems?",
    "session_id": "SESSION_ID_FROM_PREVIOUS_RESPONSE"
  }'
```

## Frontend Integration

### Example React Hook

```javascript
import { useState } from 'react';

export function useChat() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);

  const sendMessage = async (text) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: text }]);

    // Send to API
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: sessionId
      })
    });

    const data = await response.json();

    // Update session ID
    setSessionId(data.session_id);

    // Add assistant response
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.response,
      suggestions: data.suggestions,
      chart_data: data.data
    }]);
  };

  return { messages, sendMessage, sessionId };
}
```

## Conversation History

The system automatically maintains conversation context:

1. **User sends first message** → System creates new session
2. **System returns session_id** in response
3. **User sends follow-up** → Include session_id in request
4. **System retrieves history** → Claude sees full context
5. **Intelligent responses** → Assistant understands references like "these systems" or "that building"

### Example Conversation Flow

```
User: "What are the most expensive systems?"
Assistant: [Lists top 5 systems with costs]
Session ID: abc-123

User: "Show me trends for the top one" (includes session_id: abc-123)
Assistant: [Shows trends for HVAC - remembers context!]

User: "Which buildings have this issue?" (includes session_id: abc-123)
Assistant: [Shows buildings with HVAC issues - full context maintained!]
```

## Session Storage

Currently, sessions are stored **in-memory** for simplicity:
- Fast and simple
- No database setup required
- Sessions cleared on server restart

**For production**, consider:
- Redis for session storage
- PostgreSQL for persistence
- MongoDB for flexible schema

## Configuration

Edit `backend/config.py`:

```python
# Claude API settings
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
MAX_CONVERSATION_HISTORY = 10  # Keep last N messages
DEFAULT_TEMPERATURE = 0.1  # Low for factual responses
MAX_TOKENS = 4000

# Session settings (future)
SESSION_TIMEOUT_HOURS = 24
MAX_SESSIONS_PER_USER = 10
```

## Monitoring & Debugging

### View Function Calls
The response includes which tools were called:
```json
{
  "function_calls": ["get_most_expensive_systems", "get_top_buildings"]
}
```

### Debug Endpoint
```
GET /api/debug/chat-data
```
Returns data loading status for all chat tools.

### Server Logs
The backend prints useful debug info:
```
[LLM] Calling tool: get_most_expensive_systems with {'limit': 5}
[Session] Created new session: abc-123-def-456
```

## Migration from Phase 1

Phase 1 (keyword-based) has been replaced. The old implementation is removed but the endpoints remain backward compatible:

**Old behavior:** Pattern matching on keywords
**New behavior:** AI understanding with function calling

No frontend changes needed - same API contract!

## Cost Optimization

Claude API calls cost money. Tips to reduce costs:

1. **Limit context window** - We keep only last 10 messages
2. **Low temperature** - 0.1 for more deterministic responses
3. **Smart caching** - Pre-compute summaries in data_service
4. **Efficient tools** - Return only necessary data

Estimated cost: ~$0.01 per conversation (5-10 messages)

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Add API key to `.env` file or environment variables

**"Session not found"**
- Session may have been cleared or expired
- Frontend should handle and create new session

**"Tool execution failed"**
- Check data files are loaded (predictions_with_metadata.parquet)
- Verify data_service initialized correctly

**No chat history**
- Ensure session_id is passed in subsequent requests
- Check session wasn't deleted or expired

## Next Steps

Possible enhancements:
1. **Persistent sessions** - Store in Redis/PostgreSQL
2. **User authentication** - Associate sessions with users
3. **Conversation export** - Download chat history
4. **Custom tools** - Add more domain-specific functions
5. **Streaming responses** - Server-sent events for real-time responses
6. **Multi-modal** - Support images/charts in chat
