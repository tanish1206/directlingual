# FIFA World Cup 2026 Stadium Navigation & Info Assistant

An accessibility-aware, multilingual, and secure venue assistant designed for fans attending the FIFA World Cup 2026. The app supports step-free wheelchair routing, multi-language speech-to-text (STT) and text-to-speech (TTS), structured venue tool calls, policy lookup, and strict safety boundaries.

## Architecture

```
stadium-assistant/
├── backend/
│   ├── main.py                 # FastAPI app, routing, rate limiting
│   ├── orchestrator.py         # Prompt engineering, Claude tool calling, mock LLM fallback
│   ├── tools/
│   │   ├── routing.py          # get_route() (returns standard vs. step-free paths)
│   │   ├── gate_status.py      # get_gate_status() (gate status & wait times, with 30s cache)
│   │   ├── facilities.py       # get_facility() (finds nearest restroom, concession, etc.)
│   │   └── faq.py              # faq_lookup() (fuzzy search over markdown docs)
│   ├── data/
│   │   ├── init_db.py          # DB schema definition & seed data
│   │   ├── venue.db            # SQLite database
│   │   └── faq_kb/             # Markdown KB files for bag policy, ticketing, prohibited items
│   ├── security/
│   │   ├── input_validation.py # HTML sanitization, script block stripping, and length limits
│   │   └── rate_limiter.py     # Thread-safe sliding window rate-limiter
│   └── tests/
│       ├── test_tools.py       # Unit tests for database queries and cache
│       ├── test_orchestrator.py# Integration tests for LLM orchestration and emergency escalation
│       └── test_adversarial.py # 10 documented prompt injection, HTML injection, and security tests
├── frontend/
│   ├── index.html              # Fully semantic ARIA HTML layout with toggles
│   ├── style.css               # Glassmorphism design and high contrast/large text stylesheets
│   └── app.js                  # SpeechRecognition (STT), SpeechSynthesis (TTS), AJAX, and keyboard hotkeys
├── run.py                      # Server entry point
└── requirements.txt            # Python dependencies
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Installation
Install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database
Seed the SQLite database with the stadium layout, facilities, and routes:
```bash
python backend/data/init_db.py
```

### 4. Running the Server
Start the FastAPI server:
```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000) in your web browser.

---

## Running the Test Suite

Execute the 22 unit, integration, and adversarial tests:
```bash
python -m pytest backend/tests/
```

---

## Key Features & Security Enhancements

1. **Accessibility-Aware Routing**: Evaluates if the user requests an accessible pathway (e.g. wheelchair, stroller, "can't walk") and returns step-free instructions using elevator hubs and ramps instead of stairs.
2. **Web Speech API**: Uses native browser speech synthesis (TTS) and speech recognition (STT) for keyboard-free queries. Supports auto-language detection for speech feedback.
3. **Emergency Escalation (Safety Boundary)**: Instantly intercepts messages containing security threats or active medical emergencies to display a static escalation prompt, bypassing LLM processing.
4. **Prompt Injection & Adversarial Protections**: System instructions treat user text as untrusted data. Input validation strips dangerous tags and caps length at 400 characters.
5. **Rate Limiting**: Employs a sliding window rate-limiter to prevent API spam and abuse.
