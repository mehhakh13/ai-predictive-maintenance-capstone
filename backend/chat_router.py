"""
NDA-safe chat router — POST /api/chat
Assembles context from derived Parquet files (never raw CSV) and streams
a plain-English response via the Anthropic Claude API.

NDA guardrails:
 - Parquets loaded at startup; raw CSV is never read here.
 - Only SAFE_*_FIELDS may appear in the Claude payload.
 - building_id inputs validated against BLD_[A-F0-9]{8} before any query.
 - No real building names, work-order text, or original dataset fields
   ever reach the Claude API.
"""

import json
import os
import re
from pathlib import Path
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

router = APIRouter()

# ─── Paths ───────────────────────────────────────────────────────────────────
DERIVED = Path(__file__).parent.parent / "derived"

# ─── In-memory DataFrames (loaded at startup via lifespan hook in main.py) ──
_risk: Optional[pd.DataFrame]   = None
_cost: Optional[pd.DataFrame]   = None
_themes: Optional[pd.DataFrame] = None

# ─── NDA field whitelists ────────────────────────────────────────────────────
SAFE_RISK_FIELDS   = {"anon_id", "subsystem", "system", "year", "month",
                       "upm_count", "ppm_count", "total_wo", "upm_rate", "risk_tier"}
SAFE_COST_FIELDS   = {"anon_id", "subsystem", "system", "year", "month",
                       "planned_cost", "unplanned_cost", "total_cost", "upm_cost_pct"}
SAFE_THEME_FIELDS  = {"subsystem", "system", "theme", "count", "avg_cost"}

# ─── Validation ──────────────────────────────────────────────────────────────
_BLD_RE = re.compile(r"^BLD_[A-F0-9]{8}$")


def _validate_bld(bld: Optional[str]) -> Optional[str]:
    if bld is None or bld.strip() == "" or bld.lower() == "all":
        return None
    if not _BLD_RE.match(bld.strip()):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid building_id format. Expected BLD_[A-F0-9]{{8}}, got: {bld!r}",
        )
    return bld.strip()


# ─── System prompt ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a facility-maintenance advisor for university campus operations.
Your role is to translate quantitative maintenance data into clear, actionable guidance
for non-technical facility managers.

Rules you must always follow:
- Write in plain English. Never say XGBoost, SHAP, BERTopic, Parquet, DataFrame, or any
  machine-learning term. Say "our analysis shows…" or "the data indicates…" instead.
- Translate numeric risk scores: 0.00–0.33 → "low risk", 0.34–0.66 → "moderate risk",
  0.67–1.00 → "high risk".
- Refer to buildings by their anonymized code (e.g., "Building BLD_3A2F1B44").
- Keep responses to 160 words or fewer unless the user explicitly asks for more detail.
- Always end with exactly one concrete next action the facility manager should take.
- Never invent data. If the context does not contain enough information to answer, say so.
"""

# ─── Intent classification ───────────────────────────────────────────────────
_RISK_KW    = {"risk", "fail", "failure", "dangerous", "probability", "predict",
               "likely", "chance", "unsafe", "breakdown"}
_COST_KW    = {"cost", "spend", "budget", "expensive", "money", "planned", "unplanned",
               "ppm", "upm", "price", "dollar"}
_DEFECT_KW  = {"defect", "issue", "problem", "recurring", "common", "theme",
               "pattern", "hvac", "plumbing", "electrical", "leak", "failure mode"}
_RECO_KW    = {"recommend", "inspect", "should", "prioritize", "winter", "summer",
               "before", "prepare", "action", "next", "focus"}


def _classify_intent(message: str) -> str:
    lower = message.lower()
    words = set(re.findall(r"\w+", lower))
    scores = {
        "risk_query":      len(words & _RISK_KW),
        "cost_query":      len(words & _COST_KW),
        "defect_query":    len(words & _DEFECT_KW),
        "recommendation":  len(words & _RECO_KW),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def _extract_month(message: str) -> Optional[int]:
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }
    lower = message.lower()
    for name, num in months.items():
        if name in lower:
            return num
    m = re.search(r"\b(1[0-2]|[1-9])[/-](20\d{2})\b", message)
    if m:
        return int(m.group(1))
    return None


def _extract_bld(message: str) -> Optional[str]:
    m = re.search(r"BLD_[A-F0-9]{8}", message, re.IGNORECASE)
    return m.group(0).upper() if m else None


# ─── Context assembler ───────────────────────────────────────────────────────

def _assert_safe(records: list[dict], allowed: set) -> list[dict]:
    """Strip any key not in the whitelist before it reaches the Claude payload."""
    return [{k: v for k, v in row.items() if k in allowed} for row in records]


def assemble_context(intent: str, bld: Optional[str], month: Optional[int]) -> dict:
    ctx: dict = {"intent": intent, "filters": {}}
    if bld:
        ctx["filters"]["building"] = bld
    if month:
        ctx["filters"]["month"] = month

    if intent in ("risk_query", "recommendation", "general") and _risk is not None:
        df = _risk.copy()
        if bld:
            df = df[df["anon_id"] == bld]
        if month:
            df = df[df["month"] == month]
        top = (
            df.sort_values("upm_rate", ascending=False)
            .head(8)
        )
        ctx["risk_data"] = _assert_safe(
            top.to_dict(orient="records"), SAFE_RISK_FIELDS
        )

    if intent in ("cost_query", "recommendation") and _cost is not None:
        df = _cost.copy()
        if bld:
            df = df[df["anon_id"] == bld]
        if month:
            df = df[df["month"] == month]
        top = (
            df.sort_values("unplanned_cost", ascending=False)
            .head(8)
        )
        ctx["cost_data"] = _assert_safe(
            top.to_dict(orient="records"), SAFE_COST_FIELDS
        )

    if intent in ("defect_query", "recommendation") and _themes is not None:
        df = _themes.copy()
        # optionally filter by subsystem keyword from message (no building filter — themes are global)
        top = df.head(8)
        ctx["defect_data"] = _assert_safe(
            top.to_dict(orient="records"), SAFE_THEME_FIELDS
        )

    return ctx


# ─── Claude streaming ────────────────────────────────────────────────────────

async def _stream_claude(user_message: str, ctx: dict) -> AsyncGenerator[str, None]:
    if not _ANTHROPIC_AVAILABLE:
        yield "data: [ERROR: anthropic SDK not installed — run: pip install anthropic]\n\n"
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        yield "data: [ERROR: ANTHROPIC_API_KEY environment variable not set]\n\n"
        return

    client = anthropic.Anthropic(api_key=api_key)

    # Build user turn: message + injected anonymized context
    context_block = json.dumps(ctx, default=str, indent=2)
    user_turn = (
        f"{user_message}\n\n"
        f"<context>\n{context_block}\n</context>"
    )

    try:
        with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_turn}],
        ) as stream:
            for text_chunk in stream.text_stream:
                safe = text_chunk.replace("\n", "\\n")
                yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"
    except anthropic.APIError as exc:
        yield f"data: [ERROR: {exc}]\n\n"


# ─── Request/response models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    building_id: Optional[str] = None
    month: Optional[int] = None


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest):
    """Stream a plain-English answer. Only derived, anonymized data reaches Claude."""
    bld   = _validate_bld(req.building_id)
    month = req.month

    # Entity extraction from natural-language message if not provided explicitly
    if bld is None:
        bld = _extract_bld(req.message)
    if month is None:
        month = _extract_month(req.message)

    intent = _classify_intent(req.message)
    ctx    = assemble_context(intent, bld, month)

    headers = {"X-Intent": intent}
    return StreamingResponse(
        _stream_claude(req.message, ctx),
        media_type="text/event-stream",
        headers=headers,
    )


@router.get("/chat/buildings")
async def list_buildings():
    """Return all anonymized building IDs available in the derived data."""
    if _risk is None:
        return {"buildings": []}
    ids = sorted(_risk["anon_id"].dropna().unique().tolist())
    return {"buildings": ids}


@router.get("/chat/months")
async def list_months():
    """Return all year-month strings available in the derived data."""
    if _risk is None:
        return {"months": []}
    df = _risk[["year", "month"]].drop_duplicates().sort_values(["year", "month"])
    months = [f"{int(r.year)}-{int(r.month):02d}" for _, r in df.iterrows()]
    return {"months": months}


# ─── Startup loader (called from main.py) ────────────────────────────────────

def load_derived_data():
    global _risk, _cost, _themes

    risk_path   = DERIVED / "risk_scores.parquet"
    cost_path   = DERIVED / "cost_summary.parquet"
    theme_path  = DERIVED / "defect_themes.parquet"

    if risk_path.exists():
        _risk = pd.read_parquet(risk_path)
        print(f"✓ Chat: risk_scores loaded ({len(_risk):,} rows)")
    else:
        print("⚠ Chat: derived/risk_scores.parquet not found — run preprocess.py first")

    if cost_path.exists():
        _cost = pd.read_parquet(cost_path)
        print(f"✓ Chat: cost_summary loaded ({len(_cost):,} rows)")
    else:
        print("⚠ Chat: derived/cost_summary.parquet not found — run preprocess.py first")

    if theme_path.exists():
        _themes = pd.read_parquet(theme_path)
        print(f"✓ Chat: defect_themes loaded ({len(_themes):,} rows)")
    else:
        print("⚠ Chat: derived/defect_themes.parquet not found — run preprocess.py first")
