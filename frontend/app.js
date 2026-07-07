// Generate a random session ID
const sessionId = 'session_' + Math.random().toString(36).substring(2, 11);

// State management
let speechFeedbackEnabled = true;
let isRecording = false;
let recognition = null;
let synth = window.speechSynthesis;

// DOM Elements
const body = document.body;
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatBox = document.getElementById('chat-box');
const btnMic = document.getElementById('btn-mic');
const btnContrast = document.getElementById('btn-contrast');
const btnTextSize = document.getElementById('btn-text-size');
const btnSpeechFeedback = document.getElementById('btn-speech-feedback');
const announcementLog = document.getElementById('announcement-log');

// Setup speech recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onstart = () => {
        isRecording = true;
        btnMic.classList.add('recording');
        btnMic.setAttribute('aria-pressed', 'true');
        btnMic.setAttribute('aria-label', 'Stop voice typing');
        announceToScreenReader("Voice input activated. Speak now.");
    };

    recognition.onend = () => {
        isRecording = false;
        btnMic.classList.remove('recording');
        btnMic.setAttribute('aria-pressed', 'false');
        btnMic.setAttribute('aria-label', 'Start voice typing');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        announceToScreenReader("Captured: " + transcript);
        submitMessage(transcript);
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        announceToScreenReader("Speech recognition failed. Please try typing.");
        isRecording = false;
        btnMic.classList.remove('recording');
    };
} else {
    btnMic.style.display = 'none';
    console.log("Speech recognition not supported in this browser.");
}

// Helper to announce status to screen readers
function announceToScreenReader(text) {
    announcementLog.textContent = text;
}

// Text-to-speech feedback
function speak(text) {
    if (!speechFeedbackEnabled || !synth) return;
    
    // Stop any ongoing speech
    synth.cancel();
    
    // Clean text of markdown/formatting for cleaner speech
    const cleanText = text.replace(/[*_#`~🚨]/g, '').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Try to auto-detect language based on standard markers
    if (text.includes("puerta") || text.includes("baño") || text.includes("ruta")) {
        utterance.lang = "es-ES";
    } else if (text.includes("porte") || text.includes("toilette") || text.includes("chemin")) {
        utterance.lang = "fr-FR";
    } else {
        utterance.lang = "en-US";
    }
    
    synth.speak(utterance);
}

// Toggle contrast
btnContrast.addEventListener('click', () => {
    const isContrast = body.classList.toggle('high-contrast');
    btnContrast.setAttribute('aria-pressed', isContrast);
    announceToScreenReader(isContrast ? "High contrast mode enabled." : "High contrast mode disabled.");
});

// Toggle text sizing
btnTextSize.addEventListener('click', () => {
    const isLarge = body.classList.toggle('large-text');
    btnTextSize.setAttribute('aria-pressed', isLarge);
    btnTextSize.firstElementChild.textContent = isLarge ? "Size -" : "Size +";
    announceToScreenReader(isLarge ? "Text size set to large." : "Text size set to standard.");
});

// Toggle voice output
btnSpeechFeedback.addEventListener('click', () => {
    speechFeedbackEnabled = !speechFeedbackEnabled;
    btnSpeechFeedback.classList.toggle('toggle-active', speechFeedbackEnabled);
    btnSpeechFeedback.setAttribute('aria-pressed', speechFeedbackEnabled);
    if (!speechFeedbackEnabled && synth) {
        synth.cancel();
    }
    announceToScreenReader(speechFeedbackEnabled ? "Voice response enabled." : "Voice response disabled.");
});

// Handle microphone click
btnMic.addEventListener('click', () => {
    if (!recognition) return;
    if (isRecording) {
        recognition.stop();
    } else {
        // Request user language or auto
        recognition.lang = document.documentElement.lang || 'en-US';
        recognition.start();
    }
});

// Append message to UI
function appendMessage(sender, text, isUser = false) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', isUser ? 'user-msg' : 'assistant-msg');
    
    const label = document.createElement('strong');
    label.textContent = sender + ": ";
    
    const bodyP = document.createElement('p');
    bodyP.textContent = text;
    
    msgDiv.appendChild(label);
    msgDiv.appendChild(bodyP);
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    if (!isUser) {
        speak(text);
        announceToScreenReader("Response received: " + text);
    }
}

// Submit message handler
async function submitMessage(messageText) {
    if (!messageText) return;
    
    appendMessage("You", messageText, true);
    chatInput.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: messageText
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            appendMessage("Assistant", data.reply, false);
        } else {
            appendMessage("System", data.error || "An error occurred.", false);
        }
    } catch (err) {
        console.error(err);
        appendMessage("System", "Could not reach the server. Please check your network.", false);
    }
}

// Chat Form submit
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (text) {
        submitMessage(text);
    }
});

// Keyboard Navigation & Shortcuts
window.addEventListener('keydown', (e) => {
    // Ctrl + Space for toggling microphone
    if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault();
        btnMic.click();
    }
    // Escape to focus input
    if (e.key === 'Escape') {
        chatInput.focus();
    }
});
