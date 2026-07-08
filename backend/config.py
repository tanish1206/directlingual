"""
backend/config.py
─────────────────
Central configuration for the Groq client and assistant behaviour.
All tunable constants are defined here so that no magic numbers appear
throughout the codebase.

Model choice — meta-llama/llama-4-scout-17b-16e-instruct
──────────────────────────────────────────────────────────
Selected over other free-tier options for the following reasons:
  • Supports LOCAL + REMOTE tool calling AND parallel tool use (critical for
    multi-step venue queries, e.g. route + gate-status in one turn).
  • Highest TPM of any free-tier tool-calling model: 30 000 TPM vs 12 000 for
    llama-3.3-70b-versatile — TPM is the tighter constraint on free tier.
  • 500K tokens per day (TPD) cap provides comfortable demo headroom.

Free-tier rate limits (as of 2026-07, verify at console.groq.com/docs/rate-limits):
  RPM  : 30
  TPM  : 30 000
  RPD  : 1 000
  TPD  : 500 000
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Model ─────────────────────────────────────────────────────────────────────
GROQ_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"

# ── Inference parameters ──────────────────────────────────────────────────────
# Keep max_tokens deliberate — every output token counts toward TPM.
GROQ_MAX_TOKENS: int = 512
GROQ_TEMPERATURE: float = 0.2          # Low temperature → deterministic venue answers

# ── Network ───────────────────────────────────────────────────────────────────
GROQ_TIMEOUT_SECONDS: float = 20.0    # Wall-clock timeout per API call
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

# ── Retry / back-off (429 handling) ──────────────────────────────────────────
GROQ_MAX_RETRIES: int = 2             # Max retries on 429 before failing gracefully
GROQ_BACKOFF_BASE: float = 2.0        # Base for exponential back-off (seconds)
GROQ_BACKOFF_MAX: float = 16.0        # Cap on back-off delay

# ── Conversation history ──────────────────────────────────────────────────────
MAX_HISTORY_TURNS: int = 8            # Keep last N user+assistant message pairs

# ── Input validation ─────────────────────────────────────────────────────────
MAX_USER_INPUT_LENGTH: int = 400      # Characters — matches input_validation.py

# ── Demo / fallback mode ──────────────────────────────────────────────────────
# When DEMO_MODE=true (env) the Groq API is bypassed entirely — safe for
# presentations where free-tier quota may be exhausted.
DEMO_MODE: bool = os.environ.get("DEMO_MODE", "false").strip().lower() == "true"
