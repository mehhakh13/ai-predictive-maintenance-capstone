# AI Advisor — NDA-Safe Claude Chat Assistant

A plain-English chat interface for the PredicX facility maintenance dashboard, powered by the Anthropic Claude API.

---

## What It Does

Facility managers can ask questions about maintenance data without needing to understand machine learning:

- *"Which subsystems are highest risk next month?"*
- *"Summarize recurring HVAC defects this semester"*
- *"What should we inspect before winter?"*
- *"Compare planned vs. unplanned maintenance costs"*

Responses stream in real time and always end with one concrete next action.

---

## Architecture

```
Raw CSV (1.4 GB, NDA-protected)
         ↓ preprocess.py — run ONCE
    derived/
    ├── risk_scores.parquet    ~5 MB
    ├── cost_summary.parquet   ~5 MB
    └── defect_themes.parquet  ~0.1 MB
         ↓ loaded at server startup
    FastAPI /api/chat
    ├── Intent classifier
    ├── Context assembler (top 8 anonymized rows)
    └── Claude API → streamed response
         ↓
    React FacilityChat.jsx
```

---

## NDA Compliance

The raw FMUCD dataset is covered by a signed NDA prohibiting disclosure to third parties. Claude (Anthropic) is a third party.

**Firewall rules — enforced in `backend/chat_router.py`:**

| What is blocked | How |
|---|---|
| Raw work order text | Never stored in derived files |
| Real building names | SHA-256 hashed → `BLD_XXXXXXXX` in `preprocess.py` |
| Original dataset fields | Server-side field whitelist (`SAFE_*_FIELDS`) |
| Invalid building IDs | Regex validation — rejects anything not matching `BLD_[A-F0-9]{8}` |
| Derived files in git | `derived/` is in `.gitignore` |

---

## Setup

### 1. Install dependencies
```bash
pip3 install anthropic pandas pyarrow python-dotenv fastapi uvicorn --break-system-packages
```

### 2. Add your API key
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```
Get a key at [console.anthropic.com](https://console.anthropic.com) → API Keys.

### 3. Run preprocessing (one time only, ~3–5 min)
```bash
python3 preprocess.py
```
Reads the raw CSV once and writes three anonymized Parquets to `derived/`.

### 4. Start the app
```bash
cd frontend && npm run dev
```
Both the FastAPI backend and Vite frontend start together. Open the browser and click **AI Advisor** in the navbar.

---

## File Structure

```
project/
├── preprocess.py              reads raw CSV once → writes derived/
├── derived/                   gitignored — NDA-safe aggregated outputs
│   ├── risk_scores.parquet
│   ├── cost_summary.parquet
│   └── defect_themes.parquet
├── backend/
│   ├── main.py                mounts chat router at startup
│   └── chat_router.py         /api/chat, /api/chat/buildings, /api/chat/months
└── frontend/src/
    ├── components/
    │   └── FacilityChat.jsx   streaming chat UI
    └── pages/
        └── ChatPage.jsx       route wrapper
```

---

## How a Request Works

1. User types a question in the chat UI
2. Frontend sends `POST /api/chat` with `{ message, building_id?, month? }`
3. Backend classifies intent: `risk_query | cost_query | defect_query | recommendation`
4. Context assembler queries the in-memory Parquets and returns the top 8 rows
5. Only whitelisted fields (anonymized IDs, aggregated stats) are injected into the Claude prompt
6. Claude streams a plain-English response (~160 words, ends with a next action)
7. Response renders token-by-token in the browser

---

## Troubleshooting

**"Cannot reach the backend"** — run `cd frontend && npm run dev` from the project root, not the `frontend/` folder directly.

**Chat returns empty data** — `derived/` files are missing. Run `python3 preprocess.py` first.

**API key error** — confirm `.env` exists in the project root (not inside `data/`) and contains `ANTHROPIC_API_KEY=sk-ant-...`.

**Preprocessing is slow** — normal. The CSV is 1.4 GB and is only read this one time.
