"""
backend/tests/test_groq_client.py
──────────────────────────────────
Unit tests for backend/services/groq_client.py.

Design principles
─────────────────
• The REAL Groq API is NEVER called from tests — all openai SDK calls are
  intercepted with unittest.mock.  This protects the free-tier RPD budget
  from being consumed by CI runs.
• Each test focuses on one specific behaviour (happy path / 429 / malformed
  tool-call / demo-mode / arg validation) so failures are easy to diagnose.
"""

import json
import os
import time
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ── Make sure GROQ_API_KEY is present for tests that exercise the client path
os.environ.setdefault("GROQ_API_KEY", "gsk_test_key_for_unit_tests_only")
os.environ["DEMO_MODE"] = "false"  # Ensure demo-mode is off unless explicitly set

from backend.services.groq_client import (
    GroqRateLimitError,
    GroqUnavailableError,
    _validate_tool_args,
    groq_chat_completion,
    parse_tool_calls,
    run_groq_turn,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — build realistic mock response objects
# ─────────────────────────────────────────────────────────────────────────────

def _make_text_response(content: str) -> MagicMock:
    """Return a mock ChatCompletion whose first choice is a plain text reply."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = None

    choice = MagicMock()
    choice.message = msg
    choice.finish_reason = "stop"

    response = MagicMock()
    response.choices = [choice]
    response.headers = {}
    return response


def _make_tool_call_response(tool_name: str, tool_args: dict, call_id: str = "call_abc") -> MagicMock:
    """Return a mock ChatCompletion that requests a tool call."""
    tc_function = MagicMock()
    tc_function.name = tool_name
    tc_function.arguments = json.dumps(tool_args)

    tc = MagicMock()
    tc.id = call_id
    tc.function = tc_function

    msg = MagicMock()
    msg.content = None
    msg.tool_calls = [tc]

    choice = MagicMock()
    choice.message = msg
    choice.finish_reason = "tool_calls"

    response = MagicMock()
    response.choices = [choice]
    response.headers = {}
    return response


def _make_429_error() -> MagicMock:
    """Return a mock APIStatusError with status_code=429."""
    import openai
    err_response = MagicMock()
    err_response.headers = {}
    exc = openai.APIStatusError(
        message="Rate limit exceeded",
        response=err_response,
        body={},
    )
    exc.status_code = 429
    return exc


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tool argument validation
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateToolArgs(unittest.TestCase):

    def test_get_route_valid(self):
        ok, _ = _validate_tool_args("get_route", {"start": "Gate A", "end": "Section 215"})
        self.assertTrue(ok)

    def test_get_route_missing_start(self):
        ok, reason = _validate_tool_args("get_route", {"start": "", "end": "Gate C"})
        self.assertFalse(ok)
        self.assertIn("start", reason)

    def test_get_route_too_long(self):
        ok, reason = _validate_tool_args("get_route", {"start": "A" * 100, "end": "Gate A"})
        self.assertFalse(ok)
        self.assertIn("length", reason)

    def test_get_gate_status_valid(self):
        ok, _ = _validate_tool_args("get_gate_status", {"gate_name": "Gate B"})
        self.assertTrue(ok)

    def test_get_gate_status_invalid_prefix(self):
        ok, reason = _validate_tool_args("get_gate_status", {"gate_name": "Section 112"})
        self.assertFalse(ok)
        self.assertIn("gate", reason)

    def test_get_gate_status_empty(self):
        ok, reason = _validate_tool_args("get_gate_status", {"gate_name": ""})
        self.assertFalse(ok)

    def test_get_facility_valid(self):
        ok, _ = _validate_tool_args("get_facility", {"facility_type": "toilet", "near_section": 112})
        self.assertTrue(ok)

    def test_get_facility_invalid_type(self):
        ok, reason = _validate_tool_args("get_facility", {"facility_type": "jacuzzi"})
        self.assertFalse(ok)
        self.assertIn("jacuzzi", reason)

    def test_get_facility_invalid_section(self):
        ok, reason = _validate_tool_args("get_facility", {"facility_type": "toilet", "near_section": 9999})
        self.assertFalse(ok)
        self.assertIn("near_section", reason)

    def test_faq_lookup_valid(self):
        ok, _ = _validate_tool_args("faq_lookup", {"query": "bag policy"})
        self.assertTrue(ok)

    def test_faq_lookup_empty(self):
        ok, _ = _validate_tool_args("faq_lookup", {"query": ""})
        self.assertFalse(ok)

    def test_faq_lookup_too_long(self):
        ok, _ = _validate_tool_args("faq_lookup", {"query": "q" * 300})
        self.assertFalse(ok)


# ─────────────────────────────────────────────────────────────────────────────
# 2. parse_tool_calls — happy path and malformed inputs
# ─────────────────────────────────────────────────────────────────────────────

class TestParseToolCalls(unittest.TestCase):

    def test_no_tool_calls_returns_none(self):
        response = _make_text_response("Gate A is open.")
        result = parse_tool_calls(response)
        self.assertIsNone(result)

    def test_valid_tool_call_parsed(self):
        response = _make_tool_call_response("get_gate_status", {"gate_name": "Gate A"})
        result = parse_tool_calls(response)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "get_gate_status")
        self.assertEqual(result[0]["args"]["gate_name"], "Gate A")

    def test_malformed_json_args_skipped(self):
        """A tool call with invalid JSON arguments must be skipped, not crash."""
        tc_function = MagicMock()
        tc_function.name = "get_gate_status"
        tc_function.arguments = "{NOT VALID JSON"

        tc = MagicMock()
        tc.id = "call_bad"
        tc.function = tc_function

        msg = MagicMock()
        msg.tool_calls = [tc]

        choice = MagicMock()
        choice.message = msg
        choice.finish_reason = "tool_calls"

        response = MagicMock()
        response.choices = [choice]

        result = parse_tool_calls(response)
        # Malformed call skipped → no valid calls → None
        self.assertIsNone(result)

    def test_invalid_args_skipped(self):
        """A tool call whose args fail validation must be silently skipped."""
        response = _make_tool_call_response(
            "get_gate_status",
            {"gate_name": "Section 112"},  # Invalid — doesn't start with "gate"
        )
        result = parse_tool_calls(response)
        self.assertIsNone(result)

    def test_non_dict_args_skipped(self):
        """If the model returns a JSON array instead of an object, skip it."""
        tc_function = MagicMock()
        tc_function.name = "get_gate_status"
        tc_function.arguments = '["Gate A"]'  # array, not object

        tc = MagicMock()
        tc.id = "call_arr"
        tc.function = tc_function

        msg = MagicMock()
        msg.tool_calls = [tc]

        choice = MagicMock()
        choice.message = msg
        choice.finish_reason = "tool_calls"

        response = MagicMock()
        response.choices = [choice]

        result = parse_tool_calls(response)
        self.assertIsNone(result)


# ─────────────────────────────────────────────────────────────────────────────
# 3. groq_chat_completion — 429 back-off and retry
# ─────────────────────────────────────────────────────────────────────────────

class TestGroqChatCompletion(unittest.TestCase):

    @patch("backend.services.groq_client._client")
    def test_happy_path_returns_response(self, mock_client):
        """A successful response is returned immediately."""
        expected = _make_text_response("Gate A is open.")
        mock_client.chat.completions.create.return_value = expected

        result = groq_chat_completion([{"role": "user", "content": "Gate A status?"}])
        self.assertEqual(result, expected)
        mock_client.chat.completions.create.assert_called_once()

    @patch("backend.services.groq_client.time.sleep", return_value=None)
    @patch("backend.services.groq_client._client")
    def test_429_triggers_backoff_and_retry(self, mock_client, mock_sleep):
        """
        A 429 must trigger exponential back-off and retry.
        After GROQ_MAX_RETRIES (2) retries, raise GroqRateLimitError.
        """
        exc_429 = _make_429_error()
        mock_client.chat.completions.create.side_effect = exc_429

        with self.assertRaises(GroqRateLimitError):
            groq_chat_completion([{"role": "user", "content": "Gate A?"}])

        from backend.config import GROQ_MAX_RETRIES
        # sleep should be called GROQ_MAX_RETRIES times (one per failed attempt)
        self.assertEqual(mock_sleep.call_count, GROQ_MAX_RETRIES)

    @patch("backend.services.groq_client.time.sleep", return_value=None)
    @patch("backend.services.groq_client._client")
    def test_429_then_success_returns_response(self, mock_client, mock_sleep):
        """Succeeds on the second attempt after a 429 on the first."""
        ok_response = _make_text_response("OK response after retry.")
        exc_429 = _make_429_error()
        mock_client.chat.completions.create.side_effect = [exc_429, ok_response]

        result = groq_chat_completion([{"role": "user", "content": "Hello"}])
        self.assertEqual(result, ok_response)
        mock_sleep.assert_called_once()

    @patch("backend.services.groq_client._client")
    def test_timeout_raises_unavailable(self, mock_client):
        """APITimeoutError must become a GroqUnavailableError immediately (no retry)."""
        import openai
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
            request=MagicMock()
        )
        with self.assertRaises(GroqUnavailableError):
            groq_chat_completion([{"role": "user", "content": "Hello"}])


# ─────────────────────────────────────────────────────────────────────────────
# 4. run_groq_turn — end-to-end orchestration
# ─────────────────────────────────────────────────────────────────────────────

class TestRunGroqTurn(unittest.TestCase):

    def _tool_executor(self, name: str, args: dict) -> dict:
        """Stub tool executor used across tests."""
        if name == "get_gate_status":
            return {"name": "Gate A", "status": "Open", "wait_time_minutes": 10,
                    "location_description": "North side.", "cached": False}
        return {"error": f"Unknown tool: {name}"}

    @patch("backend.services.groq_client.groq_chat_completion")
    def test_plain_text_reply(self, mock_completion):
        """When the model returns plain text (no tools), that text is returned."""
        mock_completion.return_value = _make_text_response("The gate is open.")
        history: list = []
        result = run_groq_turn("Gate A?", history, "System prompt.", self._tool_executor)
        self.assertEqual(result, "The gate is open.")
        self.assertEqual(history[-1]["content"], "The gate is open.")

    @patch("backend.services.groq_client.groq_chat_completion")
    def test_tool_call_round_trip(self, mock_completion):
        """
        When the first call returns a tool_call and the second returns text,
        the second response text is what run_groq_turn returns.
        """
        first_call = _make_tool_call_response("get_gate_status", {"gate_name": "Gate A"})
        second_call = _make_text_response("Gate A is Open with a 10-minute wait.")

        mock_completion.side_effect = [first_call, second_call]

        history: list = []
        result = run_groq_turn("Status of Gate A?", history, "System.", self._tool_executor)
        self.assertIn("Gate A", result)
        self.assertEqual(mock_completion.call_count, 2)

    @patch("backend.services.groq_client.groq_chat_completion")
    def test_rate_limit_returns_user_friendly_message(self, mock_completion):
        """When GroqRateLimitError is raised, run_groq_turn returns a user-facing string."""
        mock_completion.side_effect = GroqRateLimitError("Rate limit hit.")
        history: list = []
        result = run_groq_turn("Hello", history, "System.", self._tool_executor)
        # Should not raise; should return a friendly string
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("backend.services.groq_client.groq_chat_completion")
    def test_unexpected_exception_returns_safe_message(self, mock_completion):
        """An unexpected exception must not leak a traceback to the caller."""
        mock_completion.side_effect = RuntimeError("Something exploded internally.")
        history: list = []
        result = run_groq_turn("Hello", history, "System.", self._tool_executor)
        self.assertIsInstance(result, str)
        # The raw exception message must NOT appear in the user reply
        self.assertNotIn("exploded", result)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Demo mode
# ─────────────────────────────────────────────────────────────────────────────

class TestDemoMode(unittest.TestCase):

    @patch("backend.services.groq_client.DEMO_MODE", True)
    @patch("backend.services.groq_client.groq_chat_completion")
    def test_demo_mode_never_calls_api(self, mock_completion):
        """With DEMO_MODE=True the openai SDK is never invoked."""
        history: list = []
        result = run_groq_turn(
            "nearest restroom", history, "System.", lambda n, a: {}
        )
        mock_completion.assert_not_called()
        self.assertIsInstance(result, str)
        self.assertIn("[DEMO]", result)

    @patch("backend.services.groq_client.DEMO_MODE", True)
    def test_demo_route_keyword(self):
        result = run_groq_turn("accessible route from Gate A", [], "S.", lambda n, a: {})
        self.assertIn("Gate A", result)

    @patch("backend.services.groq_client.DEMO_MODE", True)
    def test_demo_gate_keyword(self):
        result = run_groq_turn("what is the wait at Gate B", [], "S.", lambda n, a: {})
        self.assertIn("Gate B", result)

    @patch("backend.services.groq_client.DEMO_MODE", True)
    def test_demo_toilet_keyword(self):
        result = run_groq_turn("where is the toilet near section 112", [], "S.", lambda n, a: {})
        self.assertIn("112", result)


if __name__ == "__main__":
    unittest.main()
