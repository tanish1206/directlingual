import pytest
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
    # Since key is not present in tests, this will run through the mock provider
    history = []
    reply = run_chat_turn("test_session", "How do I get to Gate C?", history)
    assert "Gate C" in reply
    assert len(history) == 2  # user + assistant
