"""
backend/services/groq_client.py
────────────────────────────────
Single module that owns ALL Groq API interactions.
No other file should import the openai SDK directly.

Design decisions
────────────────
• Uses the official `openai` SDK pointed at Groq's OpenAI-compatible base URL.
• Reads remaining-quota headers on every response and logs them so that
  developers can monitor free-tier consumption during dev and demo runs.
• Wraps ALL network calls in try/except covering:
    – 429 RateLimitError  → exponential back-off, up to GROQ_MAX_RETRIES
    – APITimeoutError     → immediate user-facing error (no retry — timeout
                            implies server-side pressure; retrying makes it worse)
    – Malformed tool-call → logs and returns None so orchestrator can fallback
    – Any other APIError  → logs sanitised message (no raw user text in logs)
• Tool-call argument validation is performed BEFORE executing local tools.
• DEMO_MODE (env flag) returns canned responses without touching the API —
  designed as a deliberate resilience safeguard for demo days.
"""

import json
import logging
import os
import time
from typing import Any

import openai
from openai import APIStatusError, APITimeoutError

from backend.config import (
    DEMO_MODE,
    GROQ_BACKOFF_BASE,
    GROQ_BACKOFF_MAX,
    GROQ_BASE_URL,
    GROQ_MAX_RETRIES,
    GROQ_MAX_TOKENS,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_TIMEOUT_SECONDS,
)

# ── Logger (structured, no plaintext user content) ────────────────────────────
logger = logging.getLogger("groq-client")

# ── Tool definitions (OpenAI function-calling schema) ─────────────────────────
VENUE_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_route",
            "description": (
                "Return step-by-step navigation instructions between two points "
                "inside or around the stadium, including a step-free/wheelchair "
                "accessible alternative path."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Starting location, e.g. 'Gate A', 'Section 112'.",
                    },
                    "end": {
                        "type": "string",
                        "description": "Destination, e.g. 'Gate C', 'Section 215'.",
                    },
                },
                "required": ["start", "end"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_gate_status",
            "description": (
                "Retrieve the current open/closed status and estimated queue wait "
                "time for a named stadium gate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "gate_name": {
                        "type": "string",
                        "description": "Gate name exactly as stored, e.g. 'Gate A'.",
                    }
                },
                "required": ["gate_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_facility",
            "description": (
                "Find the nearest stadium facility of a given type. Supported types: "
                "toilet, concession, elevator, medical, prayer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "facility_type": {
                        "type": "string",
                        "enum": ["toilet", "concession", "elevator", "medical", "prayer"],
                        "description": "Type of facility to locate.",
                    },
                    "near_section": {
                        "type": "integer",
                        "description": "Section number the fan is currently near (optional).",
                    },
                },
                "required": ["facility_type"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "faq_lookup",
            "description": (
                "Search the venue FAQ knowledge base for policies on bags, ticketing, "
                "prohibited items, or emergency procedures."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The policy or topic to look up.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]

# ── Allowed values for argument validation ────────────────────────────────────
_VALID_FACILITY_TYPES = {"toilet", "concession", "elevator", "medical", "prayer"}
_VALID_GATE_PREFIX = "gate"            # gate names must start with "gate"
_MAX_GATE_NAME_LENGTH = 20
_MAX_ROUTE_NODE_LENGTH = 60
_MAX_FAQ_QUERY_LENGTH = 200

# ── Canned responses for DEMO_MODE ───────────────────────────────────────────
_DEMO_RESPONSES: dict[str, str] = {
    "default": (
        "I am running in offline demo mode. "
        "I can help you find step-free routes (e.g. Gate A → Section 215), "
        "check gate wait times (e.g. Gate B), or locate nearby facilities."
    ),
    "route": (
        "[DEMO] Step-free route from Gate A → Section 215: "
        "Enter Gate A, proceed to the East Elevator Hub near Section 110, "
        "take Elevator East to Level 2, then follow the wide level concourse to Section 215. "
        "Distance: ~250 m."
    ),
    "gate": (
        "[DEMO] Gate B is currently Open. Estimated wait: 25 minutes. "
        "East entrance near Section 110 / general parking Lot B."
    ),
    "toilet": (
        "[DEMO] Nearest accessible restroom to Section 112: "
        "Restroom 112 (Accessible) on Concourse 1 — status: Open. "
        "Wheelchair-friendly."
    ),
    "bag": (
        "[DEMO] Bag policy: only bags ≤ 35 cm × 25 cm × 10 cm are permitted. "
        "Clear bags are strongly recommended. No hard-sided bags."
    ),
}


def _get_demo_response(user_message: str) -> str:
    """Return a canned response keyed by keyword presence."""
    msg = user_message.lower()
    if any(w in msg for w in ("route", "direction", "how do i get", "navigate")):
        return _DEMO_RESPONSES["route"]
    if any(w in msg for w in ("gate", "puerta", "porte", "queue", "wait")):
        return _DEMO_RESPONSES["gate"]
    if any(w in msg for w in ("toilet", "restroom", "bathroom", "wc", "baño")):
        return _DEMO_RESPONSES["toilet"]
    if any(w in msg for w in ("bag", "baggage", "bolsa", "sac")):
        return _DEMO_RESPONSES["bag"]
    return _DEMO_RESPONSES["default"]


# ── Quota header parsing ──────────────────────────────────────────────────────

def _log_quota_headers(response: Any) -> None:
    """
    Extract and log Groq rate-limit headers from the raw HTTP response.
    Headers present: x-ratelimit-remaining-requests, x-ratelimit-remaining-tokens,
                     x-ratelimit-reset-requests, x-ratelimit-reset-tokens.
    """
    try:
        headers = getattr(response, "headers", None) or {}
        remaining_req = headers.get("x-ratelimit-remaining-requests", "?")
        remaining_tok = headers.get("x-ratelimit-remaining-tokens", "?")
        reset_req = headers.get("x-ratelimit-reset-requests", "?")
        reset_tok = headers.get("x-ratelimit-reset-tokens", "?")
        logger.info(
            "Groq quota — remaining requests: %s (resets %s) | "
            "remaining tokens: %s (resets %s)",
            remaining_req, reset_req, remaining_tok, reset_tok,
        )
    except Exception:
        pass  # Never crash on telemetry


# ── Tool-call argument validation ─────────────────────────────────────────────

def _validate_route_args(args: dict) -> tuple[bool, str]:
    """Validates routing arguments."""
    start = args.get("start", "")
    end = args.get("end", "")
    if not isinstance(start, str) or not start.strip():
        return False, "get_route: 'start' must be a non-empty string"
    if not isinstance(end, str) or not end.strip():
        return False, "get_route: 'end' must be a non-empty string"
    if len(start) > _MAX_ROUTE_NODE_LENGTH or len(end) > _MAX_ROUTE_NODE_LENGTH:
        return False, "get_route: node name exceeds maximum allowed length"
    return True, ""


def _validate_gate_args(args: dict) -> tuple[bool, str]:
    """Validates gate status lookup arguments."""
    gate = args.get("gate_name", "")
    if not isinstance(gate, str) or not gate.strip():
        return False, "get_gate_status: 'gate_name' must be a non-empty string"
    if len(gate) > _MAX_GATE_NAME_LENGTH:
        return False, "get_gate_status: gate name too long"
    if not gate.strip().lower().startswith(_VALID_GATE_PREFIX):
        return False, f"get_gate_status: gate name must start with '{_VALID_GATE_PREFIX}'"
    return True, ""


def _validate_facility_args(args: dict) -> tuple[bool, str]:
    """Validates nearest facility lookup arguments."""
    ftype = args.get("facility_type", "")
    if ftype not in _VALID_FACILITY_TYPES:
        return False, f"get_facility: unknown facility_type '{ftype}'"
    near_section = args.get("near_section")
    if near_section is not None:
        if not isinstance(near_section, int) or not (100 <= near_section <= 999):
            return False, "get_facility: near_section must be an integer 100–999"
    return True, ""


def _validate_faq_args(args: dict) -> tuple[bool, str]:
    """Validates FAQ lookup arguments."""
    query = args.get("query", "")
    if not isinstance(query, str) or not query.strip():
        return False, "faq_lookup: 'query' must be a non-empty string"
    if len(query) > _MAX_FAQ_QUERY_LENGTH:
        return False, "faq_lookup: query exceeds maximum allowed length"
    return True, ""


def _validate_tool_args(tool_name: str, args: dict) -> tuple[bool, str]:
    """Validate model-returned tool arguments against known-safe schemas.

    Args:
        tool_name: The name of the tool being called.
        args: Dictionary of arguments supplied to the tool.

    Returns:
        A tuple (is_valid, error_reason) indicating validation success/failure.
    """
    if tool_name == "get_route":
        return _validate_route_args(args)
    if tool_name == "get_gate_status":
        return _validate_gate_args(args)
    if tool_name == "get_facility":
        return _validate_facility_args(args)
    if tool_name == "faq_lookup":
        return _validate_faq_args(args)
    return True, ""


# ── Groq client singleton ─────────────────────────────────────────────────────

def _build_client() -> openai.OpenAI | None:
    """Construct the openai SDK client pointed at Groq's base URL."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        logger.warning("GROQ_API_KEY not set — Groq client unavailable.")
        return None
    return openai.OpenAI(
        api_key=api_key,
        base_url=GROQ_BASE_URL,
        timeout=GROQ_TIMEOUT_SECONDS,
        max_retries=0,   # We handle retries manually for fine-grained control
    )


_client: openai.OpenAI | None = _build_client()


# ── Public API ────────────────────────────────────────────────────────────────

class GroqRateLimitError(RuntimeError):
    """Raised when all retries are exhausted on a 429."""


class GroqUnavailableError(RuntimeError):
    """Raised when the API is unreachable or timed out."""


def groq_chat_completion(
    messages: list[dict],
    use_tools: bool = True,
) -> openai.types.chat.ChatCompletion:
    """
    Send a chat completion request to Groq with optional tool-calling.

    Retry policy
    ─────────────
    On HTTP 429 the function reads the Retry-After header (or falls back to
    exponential back-off capped at GROQ_BACKOFF_MAX seconds) and retries up
    to GROQ_MAX_RETRIES times. RPM, TPM, and RPD 429s are all handled
    identically — the client cannot distinguish which limit was hit from the
    status code alone, so the same back-off strategy protects all three.

    Raises
    ──────
    GroqRateLimitError   – all retries exhausted
    GroqUnavailableError – timeout or non-429 API error
    """
    global _client
    if _client is None:
        _client = _build_client()
    if _client is None:
        raise GroqUnavailableError("GROQ_API_KEY is not configured.")

    kwargs: dict[str, Any] = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": GROQ_MAX_TOKENS,
        "temperature": GROQ_TEMPERATURE,
    }
    if use_tools:
        kwargs["tools"] = VENUE_TOOLS
        kwargs["tool_choice"] = "auto"

    last_exc: Exception | None = None
    for attempt in range(GROQ_MAX_RETRIES + 1):
        try:
            response = _client.chat.completions.create(**kwargs)
            _log_quota_headers(response)
            return response

        except APIStatusError as exc:
            if exc.status_code == 429:
                last_exc = exc
                if attempt >= GROQ_MAX_RETRIES:
                    break
                # Respect Retry-After if present, otherwise exponential back-off
                retry_after_str = (exc.response.headers or {}).get("retry-after")
                if retry_after_str and retry_after_str.isdigit():
                    delay = float(retry_after_str)
                else:
                    delay = min(GROQ_BACKOFF_BASE ** (attempt + 1), GROQ_BACKOFF_MAX)
                logger.warning(
                    "Groq 429 rate limit (attempt %d/%d). Backing off %.1fs.",
                    attempt + 1, GROQ_MAX_RETRIES + 1, delay,
                )
                time.sleep(delay)
                continue
            else:
                # 4xx/5xx that isn't a rate limit — log sanitised message only
                logger.error(
                    "Groq API error status=%d type=%s",
                    exc.status_code,
                    type(exc).__name__,
                )
                raise GroqUnavailableError(
                    f"Groq API returned an error (status {exc.status_code})."
                ) from exc

        except APITimeoutError as exc:
            logger.error("Groq request timed out after %.1fs.", GROQ_TIMEOUT_SECONDS)
            raise GroqUnavailableError(
                "The request to Groq timed out. Please try again in a moment."
            ) from exc

    raise GroqRateLimitError(
        "The assistant is temporarily unavailable due to high demand. "
        "Please wait a moment and try again, or use a quick-action chip."
    ) from last_exc


def parse_tool_calls(
    response: openai.types.chat.ChatCompletion,
) -> list[dict] | None:
    """
    Extract and validate tool calls from a Groq completion response.

    Returns a list of validated dicts:
        [{"name": str, "id": str, "args": dict}, ...]

    Returns None if the model chose not to call any tools.

    Malformed tool-call payloads are logged and skipped rather than crashing
    the request — the orchestrator can decide how to handle partial results.
    """
    choice = response.choices[0]
    if choice.finish_reason != "tool_calls":
        return None

    tool_calls = getattr(choice.message, "tool_calls", None) or []
    validated: list[dict] = []

    for tc in tool_calls:
        name = getattr(tc.function, "name", None)
        raw_args = getattr(tc.function, "arguments", "{}")
        call_id = getattr(tc, "id", "")

        # Parse JSON arguments
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            logger.warning(
                "Malformed tool-call arguments for tool '%s' — skipping. (call_id=%s)",
                name, call_id,
            )
            continue

        if not isinstance(args, dict):
            logger.warning(
                "Tool '%s' arguments are not a dict — skipping. (call_id=%s)",
                name, call_id,
            )
            continue

        # Validate arguments against expected schema
        is_valid, reason = _validate_tool_args(name or "", args)
        if not is_valid:
            logger.warning(
                "Tool argument validation failed for '%s': %s (call_id=%s)",
                name, reason, call_id,
            )
            continue

        validated.append({"name": name, "id": call_id, "args": args})

    return validated if validated else None


def run_groq_turn(
    user_message: str,
    history: list[dict],
    system_prompt: str,
    tool_executor,  # Callable[[str, dict], dict]
) -> str:
    """
    Execute one full chat turn against Groq, including a tool-calling round-trip.

    Parameters
    ──────────
    user_message  : Already-sanitised user text (≤ MAX_USER_INPUT_LENGTH chars).
    history       : Running conversation history (mutated in-place).
    system_prompt : The trusted system prompt string.
    tool_executor : Callable(name, args) → dict — executes a named local tool.

    Returns
    ───────
    The assistant's final reply as a string, or a user-facing error message.
    Logs are emitted at WARNING/ERROR level; user text is never logged verbatim.
    """
    # ── Demo mode fast-path ───────────────────────────────────────────────────
    if DEMO_MODE:
        reply = _get_demo_response(user_message)
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        logger.info("DEMO_MODE active — returning canned response.")
        return reply

    # ── Build message list ────────────────────────────────────────────────────
    history.append({"role": "user", "content": user_message})
    messages: list[dict] = [{"role": "system", "content": system_prompt}] + history

    try:
        # ── First call — may trigger tool use ─────────────────────────────────
        response = groq_chat_completion(messages, use_tools=True)
        tool_calls = parse_tool_calls(response)

        if tool_calls:
            # Append the model's assistant message (containing tool_calls) verbatim
            messages.append(response.choices[0].message)

            # Execute each validated tool and append results
            tool_results: list[dict] = []
            for tc in tool_calls:
                result = tool_executor(tc["name"], tc["args"])
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result),
                })
            messages.extend(tool_results)

            # ── Second call — model synthesises tool results into a reply ─────
            final_response = groq_chat_completion(messages, use_tools=False)
            reply = final_response.choices[0].message.content or ""
        else:
            reply = response.choices[0].message.content or ""

    except GroqRateLimitError as exc:
        logger.warning("Rate limit exhausted after retries.")
        reply = str(exc)

    except GroqUnavailableError as exc:
        logger.error("Groq unavailable: %s", type(exc).__name__)
        reply = str(exc)

    except Exception as exc:
        # Catch-all: log type only — do NOT include user content
        logger.error("Unexpected error in run_groq_turn: %s", type(exc).__name__)
        reply = (
            "Something went wrong while processing your request. "
            "Please try again or use the quick-action chips below."
        )

    history.append({"role": "assistant", "content": reply})
    return reply
