import pytest
import os
import sqlite3

from backend.tools.routing import get_route
from backend.tools.gate_status import get_gate_status
from backend.tools.facilities import get_facility
from backend.tools.faq import faq_lookup

def test_routing_success():
    # Test standard & step-free routing from seeded DB
    res = get_route("Gate A", "Gate C")
    assert "error" not in res
    assert res["start"] == "Gate A"
    assert res["end"] == "Gate C"
    assert "concourse" in res["standard_route"]
    assert "step-free" in res["step_free_route"]
    assert res["distance_meters"] == 400

def test_routing_failure():
    res = get_route("Gate X", "Gate Z")
    assert "error" in res
    assert "No route found" in res["error"]

def test_gate_status_and_caching():
    # Test first fetch
    res1 = get_gate_status("Gate A")
    assert "error" not in res1
    assert res1["name"] == "Gate A"
    assert res1["status"] == "Open"
    assert res1["cached"] is False
    
    # Test cached fetch (should hit within 30s)
    res2 = get_gate_status("Gate A")
    assert res2["cached"] is True

def test_facilities_nearest():
    # Find nearest toilet to Section 112
    res = get_facility("toilet", near_section=112)
    assert "error" not in res
    # First result should be Section 112 Restroom
    results = res["results"]
    assert len(results) > 0
    assert results[0]["section"] == 112
    assert results[0]["is_accessible"] is True

def test_faq_lookup_match():
    # Test searching bag rules
    res = faq_lookup("Can I bring a large backpack?")
    assert "error" not in res
    assert "Bag Policy" in res["topic"]
    assert "backpacks" in res["content"].lower()

def test_faq_lookup_no_match():
    res = faq_lookup("xyzabc")
    assert "error" in res
