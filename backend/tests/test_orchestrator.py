import os
from unittest.mock import patch
from backend.orchestrator import check_emergency, run_chat_turn, STATIC_EMERGENCY_RESPONSE

def test_emergency_escalation_detection():
    # Active medical emergency or security threat
    assert check_emergency("There is a shooter at Gate A!") is True
    assert check_emergency("Someone is having a heart attack!") is True
    assert check_emergency("Where is the gate?") is False

def test_run_chat_turn_emergency():
    history = []
    reply = run_chat_turn("test_session", "Help, someone is bleeding!", history)
    assert reply == STATIC_EMERGENCY_RESPONSE
    # Emergency should not pollute conversation history
    assert len(history) == 0

def test_run_chat_turn_normal_mock():
    """
    With no GROQ_API_KEY the orchestrator must fall back to the deterministic
    mock engine and return a recognisable response — no real API call is made.
    """
    # Ensure the mock path is taken by removing any key set by other test modules
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
        history = []
        reply = run_chat_turn("test_session", "How do I get to Gate C?", history)
        assert "Gate C" in reply
        assert len(history) == 2  # user + assistant
