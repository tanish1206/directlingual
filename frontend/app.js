const { useState, useEffect, useRef } = React;

// Simple custom SVG icons to avoid external package loading issues
const Icons = {
    Wheelchair: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14a3 3 0 11-6 0v-4M9 10a1 1 0 100-2 1 1 0 000 2zm3 6H9M9 13H5m6 7a8 8 0 110-16 8 8 0 010 16z" />
        </svg>
    ),
    Walking: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5a1 1 0 100-2 1 1 0 000 2zM9 20l4-9 4 9m-5-9H9m4 0l-1-3" />
        </svg>
    ),
    MapPin: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
    ),
    ArrowRight: () => (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
    ),
    CheckCircle: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    ),
    XCircle: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    ),
    Mic: ({ active }) => (
        <svg className={`w-6 h-6 ${active ? 'animate-pulse text-white' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
    ),
    VolumeUp: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        </svg>
    ),
    VolumeMute: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.707.707l-4.707-4.707M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
        </svg>
    ),
    Refresh: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3-3 3 3m-3-3v12" />
        </svg>
    ),
    Info: () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    )
};

// Render RouteCard Component
function RouteCard({ start, end, standardRoute, stepFreeRoute, distanceMeters, isAccessibilityUser }) {
    return (
        <div className="bg-stadiumDark-900 border border-fifaGreen-800 rounded-xl p-4 shadow-lg w-full max-w-md my-2" role="region" aria-label="Route instructions card">
            <div className="flex justify-between items-center mb-3">
                <span className="text-xs uppercase tracking-wider text-fifaGold-400 font-bold">Directions Map</span>
                <span className="text-xs font-semibold text-gray-400">{distanceMeters}m distance</span>
            </div>
            <div className="flex items-center gap-2 font-heading font-semibold text-sm mb-4">
                <span className="px-2 py-0.5 bg-fifaGreen-900 text-fifaGreen-100 rounded text-xs">{start}</span>
                <Icons.ArrowRight />
                <span className="px-2 py-0.5 bg-fifaGreen-900 text-fifaGreen-100 rounded text-xs">{end}</span>
            </div>
            
            <div className="space-y-3">
                {isAccessibilityUser ? (
                    <div className="flex gap-3 items-start bg-fifaGreen-950/40 p-3 rounded-lg border border-fifaGreen-900/60">
                        <div className="p-2 bg-fifaGreen-900/80 rounded-full text-fifaGold-400 mt-0.5">
                            <Icons.Wheelchair />
                        </div>
                        <div>
                            <h4 className="text-xs font-bold text-fifaGreen-200 uppercase tracking-wide">♿ Step-Free Accessible Route</h4>
                            <p className="text-sm text-gray-200 mt-1 leading-relaxed">{stepFreeRoute}</p>
                        </div>
                    </div>
                ) : (
                    <div className="flex gap-3 items-start bg-stadiumDark-850 p-3 rounded-lg border border-gray-800">
                        <div className="p-2 bg-gray-800 rounded-full text-fifaGreen-400 mt-0.5">
                            <Icons.Walking />
                        </div>
                        <div>
                            <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wide">🏃 Standard Fast Pathway</h4>
                            <p className="text-sm text-gray-300 mt-1 leading-relaxed">{standardRoute}</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// Render GateStatusBadge Component
function GateStatusBadge({ name, status, waitTimeMinutes, locationDescription }) {
    const isOpen = status.toLowerCase() === 'open';
    return (
        <div className="bg-stadiumDark-900 border border-gray-800 rounded-xl p-4 shadow-lg w-full max-w-sm my-2" role="region" aria-label={`Gate status card for ${name}`}>
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="font-heading font-bold text-lg text-white">{name}</h3>
                    <p className="text-xs text-gray-400">Security Gate Entrance</p>
                </div>
                <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                    isOpen ? 'bg-emerald-900/40 text-emerald-400 border border-emerald-800' : 'bg-fifaRed-500/20 text-red-400 border border-red-800'
                }`}>
                    {isOpen ? <Icons.CheckCircle /> : <Icons.XCircle />}
                    <span>{status}</span>
                </div>
            </div>
            
            <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-gray-800">
                <div>
                    <span className="text-[10px] uppercase text-gray-500 block font-bold">Estimated Wait</span>
                    <span className="text-xl font-heading font-extrabold text-fifaGold-400">
                        {isOpen ? `${waitTimeMinutes} min` : 'N/A'}
                    </span>
                </div>
                <div>
                    <span className="text-[10px] uppercase text-gray-500 block font-bold">Status Detail</span>
                    <span className="text-xs font-medium text-gray-300 mt-1 block">
                        {isOpen ? 'Normal queues' : 'Maintenance'}
                    </span>
                </div>
            </div>
            <p className="text-xs text-gray-400 mt-3 bg-stadiumDark-950 p-2.5 rounded border border-gray-800/60 leading-relaxed">
                📍 {locationDescription}
            </p>
        </div>
    );
}

// Render FacilityCard Component
function FacilityCard({ name, type, level, section, isAccessible, status, onRouteMe }) {
    const isAvailable = status.toLowerCase() !== 'closed';
    return (
        <div className="bg-stadiumDark-900 border border-gray-800 rounded-xl p-3.5 shadow-md w-full max-w-sm my-2" role="region" aria-label={`Facility card for ${name}`}>
            <div className="flex justify-between items-start">
                <div className="flex gap-2.5 items-start">
                    <div className="p-2 bg-fifaGreen-950 border border-fifaGreen-800 text-fifaGold-400 rounded-lg text-lg">
                        {type === 'toilet' ? '🚽' : type === 'concession' ? '🍔' : type === 'medical' ? '🏥' : type === 'prayer' ? '🕌' : '🛗'}
                    </div>
                    <div>
                        <h4 className="font-heading font-bold text-sm text-white">{name}</h4>
                        <p className="text-[11px] text-gray-400 mt-0.5">{level} • Nearest Sec {section}</p>
                    </div>
                </div>
                <div className="flex flex-col items-end gap-1.5">
                    {isAccessible && (
                        <span className="px-2 py-0.5 bg-fifaGreen-900/80 text-fifaGreen-200 border border-fifaGreen-700/80 rounded text-[9px] font-extrabold flex items-center gap-0.5">
                            ♿ ACCESSIBLE
                        </span>
                    )}
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        status === 'Open' ? 'bg-emerald-950/60 text-emerald-400' : status === 'Busy' ? 'bg-amber-950/60 text-amber-400' : 'bg-red-950/60 text-red-400'
                    }`}>
                        {status}
                    </span>
                </div>
            </div>
            
            <div className="mt-3.5 pt-2.5 border-t border-gray-800/60 flex justify-between items-center">
                <span className="text-[11px] text-gray-500 font-semibold">Ready to navigate?</span>
                <button 
                    onClick={() => onRouteMe(name)}
                    className="px-3 py-1 bg-fifaGreen-600 hover:bg-fifaGreen-500 text-white rounded text-[11px] font-bold transition-all flex items-center gap-1 focus:ring-2 focus:ring-fifaGold-400 focus:outline-none"
                    aria-label={`Get directions to ${name}`}
                >
                    <span>Route Me</span>
                    <Icons.ArrowRight />
                </button>
            </div>
        </div>
    );
}

// Render A11yControls Component
function A11yControls({ highContrast, setHighContrast, largeText, setLargeText, speechEnabled, setSpeechEnabled, currentLang, setCurrentLang }) {
    return (
        <div className="bg-stadiumDark-900 border-b border-fifaGreen-900/60 p-3 flex flex-wrap gap-2.5 items-center justify-between shadow-md" role="group" aria-label="Accessibility options">
            <div className="flex flex-wrap gap-2">
                <button 
                    onClick={() => {
                        setHighContrast(!highContrast);
                        document.body.classList.toggle('high-contrast', !highContrast);
                        const announcement = !highContrast ? "High contrast mode enabled." : "High contrast mode disabled.";
                        document.getElementById('announcement-log').textContent = announcement;
                    }}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-bold transition-all min-h-[44px] min-w-[70px] ${
                        highContrast 
                            ? 'bg-yellow-400 text-black border-yellow-400 font-extrabold shadow' 
                            : 'bg-stadiumDark-850 border-gray-800 text-gray-300 hover:bg-stadiumDark-800'
                    }`}
                    aria-pressed={highContrast}
                    title="Toggle High Contrast Theme for low-vision support"
                >
                    🌓 Contrast
                </button>

                <button 
                    onClick={() => {
                        setLargeText(!largeText);
                        document.body.classList.toggle('large-text-mode', !largeText);
                        const announcement = !largeText ? "Font sizing set to large." : "Font sizing set to standard.";
                        document.getElementById('announcement-log').textContent = announcement;
                    }}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-bold transition-all min-h-[44px] min-w-[70px] ${
                        largeText 
                            ? 'bg-fifaGreen-600 text-white border-fifaGreen-500 shadow' 
                            : 'bg-stadiumDark-850 border-gray-800 text-gray-300 hover:bg-stadiumDark-800'
                    }`}
                    aria-pressed={largeText}
                    title="Toggle larger font scaling for readability"
                >
                    {largeText ? 'Size -' : 'Size +'}
                </button>

                <button 
                    onClick={() => {
                        setSpeechEnabled(!speechEnabled);
                        if (speechEnabled) {
                            window.speechSynthesis.cancel();
                        }
                        const announcement = !speechEnabled ? "Voice assistant reader activated." : "Voice assistant reader deactivated.";
                        document.getElementById('announcement-log').textContent = announcement;
                    }}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-bold transition-all min-h-[44px] min-w-[70px] flex items-center gap-1.5 ${
                        speechEnabled 
                            ? 'bg-fifaGold-500 text-stadiumDark-950 border-fifaGold-400 font-extrabold shadow' 
                            : 'bg-stadiumDark-850 border-gray-800 text-gray-300 hover:bg-stadiumDark-800'
                    }`}
                    aria-pressed={speechEnabled}
                    title="Toggle Text-to-Speech audio feedback"
                >
                    {speechEnabled ? <Icons.VolumeUp /> : <Icons.VolumeMute />}
                    <span>Voice</span>
                </button>
            </div>

            <div className="flex items-center gap-2">
                <label htmlFor="lang-select" className="text-xs text-gray-400 font-bold uppercase tracking-wider">Lang:</label>
                <select 
                    id="lang-select"
                    value={currentLang} 
                    onChange={(e) => {
                        setCurrentLang(e.target.value);
                        document.documentElement.lang = e.target.value.split('-')[0];
                        const announcement = `Language changed to ${e.target.value === 'en-US' ? 'English' : e.target.value === 'es-ES' ? 'Spanish' : 'French'}.`;
                        document.getElementById('announcement-log').textContent = announcement;
                    }}
                    className="bg-stadiumDark-850 text-white border border-gray-800 rounded-lg px-2.5 py-1.5 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-fifaGold-400 min-h-[44px]"
                >
                    <option value="en-US">🇬🇧 English</option>
                    <option value="es-ES">🇪🇸 Español</option>
                    <option value="fr-FR">🇫🇷 Français</option>
                </select>
            </div>
        </div>
    );
}

// Message bubble representing dialog turn
function MessageBubble({ role, content, meta, onRouteMe }) {
    const isUser = role === 'user';
    const isSystem = role === 'system';
    
    if (isSystem) {
        return (
            <div className="flex justify-center my-2.5" role="status">
                <span className="bg-fifaRed-500/10 border border-fifaRed-500/30 text-red-300 text-xs px-4 py-2.5 rounded-xl text-center max-w-xs md:max-w-md block shadow">
                    🚨 {content}
                </span>
            </div>
        );
    }

    return (
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} my-2.5`}>
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-extrabold mb-1 px-1">
                {isUser ? 'You' : 'FIFA Event Tech'}
            </span>
            <div className={`max-w-[85%] rounded-2xl p-4 shadow-md ${
                isUser 
                    ? 'bg-fifaGreen-600 text-white rounded-tr-none font-medium' 
                    : 'bg-stadiumDark-900 border border-gray-800 text-gray-200 rounded-tl-none'
            }`}>
                <p className="text-sm leading-relaxed whitespace-pre-line">{content}</p>
                
                {/* Render structured metadata if present */}
                {meta && (
                    <div className="mt-3.5 space-y-2 border-t border-gray-800/80 pt-3">
                        {meta.type === 'route' && (
                            <RouteCard 
                                start={meta.start} 
                                end={meta.end} 
                                standardRoute={meta.standardRoute} 
                                stepFreeRoute={meta.stepFreeRoute} 
                                distanceMeters={meta.distanceMeters}
                                isAccessibilityUser={meta.isAccessibilityUser}
                            />
                        )}
                        {meta.type === 'gate' && (
                            <GateStatusBadge 
                                name={meta.name} 
                                status={meta.status} 
                                waitTimeMinutes={meta.waitTimeMinutes} 
                                locationDescription={meta.locationDescription}
                            />
                        )}
                        {meta.type === 'facility' && meta.results && meta.results.map((fac, idx) => (
                            <FacilityCard 
                                key={idx}
                                name={fac.name} 
                                type={fac.type} 
                                level={fac.level} 
                                section={fac.section} 
                                isAccessible={fac.isAccessible} 
                                status={fac.status}
                                onRouteMe={onRouteMe}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

// App container
function App() {
    const [highContrast, setHighContrast] = useState(false);
    const [largeText, setLargeText] = useState(false);
    const [speechEnabled, setSpeechEnabled] = useState(true);
    const [currentLang, setCurrentLang] = useState('en-US');
    
    // Mode toggles
    const [isDemoMode, setIsDemoMode] = useState(true);
    
    const [messages, setMessages] = useState([]);
    const [inputMsg, setInputMsg] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [speechSupported, setSpeechSupported] = useState(true);
    const [isThinking, setIsThinking] = useState(false);

    const chatBoxEndRef = useRef(null);
    const recognitionRef = useRef(null);

    // Initial conversation states for quick demonstration
    const demoScenarios = {
        route: {
            userQuery: "Can I get an accessible route from Gate A to Section 215?",
            reply: "Hello! I have generated an accessible (step-free) route from Gate A to Section 215 for you. This route relies entirely on level concourses and elevator corridors.",
            meta: {
                type: "route",
                start: "Gate A",
                end: "Section 215",
                standardRoute: "Enter Gate A, proceed to central corridor, take the escalator on your left to Level 2 (Concourse 2), and follow signs.",
                stepFreeRoute: "Enter Gate A, proceed to the East Elevator Hub near Section 110, take Elevator East to Level 2, exit and follow the wide level concourse directly to Section 215.",
                distanceMeters: 250,
                isAccessibilityUser: true
            }
        },
        gate: {
            userQuery: "What is the wait time for Gate B?",
            reply: "Checking gate metrics... Here is the live status card for Gate B. The gate is open with moderate queue sizes.",
            meta: {
                type: "gate",
                name: "Gate B",
                status: "Open",
                waitTimeMinutes: 25,
                locationDescription: "East entrance, closest to Section 110. Near general parking Lot B."
            }
        },
        toilet: {
            userQuery: "Where is the nearest restroom to Section 112?",
            reply: "Searching nearby amenities... I found the following restroom facilities near Section 112. Restroom 112 is fully wheelchair accessible.",
            meta: {
                type: "facility",
                results: [
                    {
                        name: "Restroom 112 (Accessible)",
                        type: "toilet",
                        level: "Concourse 1",
                        section: 112,
                        isAccessible: true,
                        status: "Open"
                    },
                    {
                        name: "Restroom 122 (Accessible)",
                        type: "toilet",
                        level: "Concourse 1",
                        section: 122,
                        isAccessible: true,
                        status: "Open"
                    }
                ]
            }
        }
    };

    // Load initial greeting
    useEffect(() => {
        const welcomeMsgs = {
            'en-US': "⚽ Welcome to the FIFA World Cup 2026 Venue Assistant! I can help you find step-free paths, check gate wait times, locate accessible restrooms, and lookup venue policy questions. Tap a quick chip below or ask anything!",
            'es-ES': "⚽ ¡Bienvenido al Asistente del Estadio FIFA 2026! Puedo ayudarte a buscar rutas accesibles, comprobar tiempos de espera, encontrar baños adaptados o resolver dudas sobre políticas de bolsos. ¡Elige un botón o escribe!",
            'fr-FR': "⚽ Bienvenue à l'assistant de stade de la Coupe du Monde FIFA 2026! Je peux vous guider sur des parcours accessibles, vérifier l'attente aux portes, repérer les toilettes adaptées. Écrivez ou parlez!"
        };
        setMessages([
            { role: 'assistant', content: welcomeMsgs[currentLang] || welcomeMsgs['en-US'] }
        ]);
    }, [currentLang]);

    // Auto-scroll chat window
    useEffect(() => {
        chatBoxEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isThinking]);

    // Setup speech synthesis & recognition
    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const rec = new SpeechRecognition();
            rec.continuous = false;
            rec.interimResults = false;
            
            rec.onstart = () => {
                setIsRecording(true);
                announce("Voice input activated. Speak now.");
            };
            
            rec.onend = () => {
                setIsRecording(false);
            };
            
            rec.onresult = (event) => {
                const text = event.results[0][0].transcript;
                setInputMsg(text);
                announce(`Captured: ${text}`);
                handleSendMessage(text);
            };
            
            rec.onerror = (err) => {
                console.error("STT Error:", err);
                announce("Speech recognition failed. Please try typing.");
                setIsRecording(false);
            };
            
            recognitionRef.current = rec;
        } else {
            setSpeechSupported(false);
        }
    }, [currentLang]);

    const announce = (text) => {
        const logger = document.getElementById('announcement-log');
        if (logger) logger.textContent = text;
    };

    const speakText = (text) => {
        if (!speechEnabled || !window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        
        const clean = text.replace(/[*_#`~🚨♿🏃]/g, '').trim();
        const utterance = new SpeechSynthesisUtterance(clean);
        
        if (currentLang === 'es-ES' || text.includes("puerta") || text.includes("baño")) {
            utterance.lang = "es-ES";
        } else if (currentLang === 'fr-FR' || text.includes("porte") || text.includes("toilette")) {
            utterance.lang = "fr-FR";
        } else {
            utterance.lang = "en-US";
        }
        window.speechSynthesis.speak(utterance);
    };

    // Trigger mic recording
    const toggleRecording = () => {
        if (!speechSupported) {
            alert("Voice recognition is not supported in this browser layout.");
            return;
        }
        if (isRecording) {
            recognitionRef.current.stop();
        } else {
            recognitionRef.current.lang = currentLang;
            recognitionRef.current.start();
        }
    };

    // Post to FastAPI or simulate in demo mode
    const handleSendMessage = async (textToSend) => {
        const query = textToSend || inputMsg;
        if (!query.trim()) return;

        // Append user query to chat log
        setMessages(prev => [...prev, { role: 'user', content: query }]);
        setInputMsg('');
        setIsThinking(true);

        // Speech announcement
        announce(`Sending message: ${query}`);

        // Handle Emergency Escalation immediately in client side for instant visual cue
        const emergencyKeywords = ["bomb", "weapon", "shooter", "gun", "knife", "medical emergency", "heart attack", "bleeding", "fire", "smoke", "terrorist", "die", "kill"];
        if (emergencyKeywords.some(kw => query.toLowerCase().includes(kw))) {
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: "EMERGENCY ESCALATION: If you are experiencing an active medical emergency or security threat, contact stadium staff immediately, text 'HELP' to 69050, or find the nearest First Aid Station (North Section 102 / South Section 124)."
                }]);
                setIsThinking(false);
                speakText("Emergency warning triggered. Please consult stadium personnel or security instantly.");
            }, 600);
            return;
        }

        // Simulating or calling endpoint
        if (isDemoMode) {
            setTimeout(() => {
                const normQuery = query.toLowerCase();
                let matchedResponse = null;

                if (normQuery.includes('route') || normQuery.includes('map') || normQuery.includes('cómo ir') || normQuery.includes('chemin')) {
                    matchedResponse = demoScenarios.route;
                } else if (normQuery.includes('gate b') || normQuery.includes('gate') || normQuery.includes('puerta') || normQuery.includes('porte')) {
                    matchedResponse = demoScenarios.gate;
                } else if (normQuery.includes('toilet') || normQuery.includes('bathroom') || normQuery.includes('restroom') || normQuery.includes('baño') || normQuery.includes('toilette')) {
                    matchedResponse = demoScenarios.toilet;
                }

                if (matchedResponse) {
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: matchedResponse.reply,
                        meta: matchedResponse.meta
                    }]);
                    speakText(matchedResponse.reply);
                } else {
                    const fallbackReply = "I have scanned the local stadium databases. Let me know if you would like me to lookup routing directions, gate statuses (e.g. Gate A, Gate B), or toilets near you.";
                    setMessages(prev => [...prev, { role: 'assistant', content: fallbackReply }]);
                    speakText(fallbackReply);
                }
                setIsThinking(false);
            }, 800);
        } else {
            // Send requests to live FastAPI backend
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: "session_react_stadium_assistant",
                        message: query
                    })
                });
                
                const data = await response.json();
                if (response.ok) {
                    // Try parsing structures if returned from fastapi tools
                    let meta = null;
                    const reply = data.reply;
                    
                    // Add mock structured components inside UI even with backend reply for visualization
                    if (reply.toLowerCase().includes('ruta') || reply.toLowerCase().includes('route')) {
                        meta = demoScenarios.route.meta;
                    } else if (reply.toLowerCase().includes('gate') || reply.toLowerCase().includes('puerta') || reply.toLowerCase().includes('porte')) {
                        meta = demoScenarios.gate.meta;
                    } else if (reply.toLowerCase().includes('baño') || reply.toLowerCase().includes('toilet') || reply.toLowerCase().includes('sanitario')) {
                        meta = demoScenarios.toilet.meta;
                    }

                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: reply,
                        meta: meta
                    }]);
                    speakText(reply);
                } else {
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: `⚠️ Error: ${data.error || 'Server error. Please wait.'}`
                    }]);
                }
            } catch (err) {
                console.error("FastAPI Call failed:", err);
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: "⚠️ Connection lost. Unable to reach stadium server. Re-trying using offline tournament guidelines..."
                }]);
            } finally {
                setIsThinking(false);
            }
        }
    };

    // Hotkeys setup
    useEffect(() => {
        const handleKeys = (e) => {
            if (e.ctrlKey && e.code === 'Space') {
                e.preventDefault();
                toggleRecording();
            }
            if (e.key === 'Escape') {
                document.getElementById('chat-text-input')?.focus();
            }
        };
        window.addEventListener('keydown', handleKeys);
        return () => window.removeEventListener('keydown', handleKeys);
    }, [currentLang, isRecording]);

    // Handle Quick Action Chips
    const handleQuickAction = (actionKey) => {
        let text = "";
        if (currentLang === 'es-ES') {
            if (actionKey === 'toilet') text = "Dónde está el baño más cercano a Sección 112?";
            if (actionKey === 'gate') text = "Cuál es el tiempo de espera de la Puerta B?";
            if (actionKey === 'route') text = "Ruta accesible de Puerta A a Sección 215";
            if (actionKey === 'bag') text = "Cuál es la política de bolsos del estadio?";
        } else if (currentLang === 'fr-FR') {
            if (actionKey === 'toilet') text = "Où se trouve la toilette la plus proche de la Section 112?";
            if (actionKey === 'gate') text = "Quel est l'attente pour la Porte B?";
            if (actionKey === 'route') text = "Itinéraire accessible de la Porte A à Section 215";
            if (actionKey === 'bag') text = "Quelle est la politique des sacs?";
        } else {
            if (actionKey === 'toilet') text = "Where is the nearest restroom to Section 112?";
            if (actionKey === 'gate') text = "What is the wait time for Gate B?";
            if (actionKey === 'route') text = "Accessible route from Gate A to Section 215";
            if (actionKey === 'bag') text = "What is the stadium bag policy?";
        }
        handleSendMessage(text);
    };

    return (
        <div className="flex-1 flex flex-col max-w-md mx-auto w-full bg-stadiumDark-950 border-x border-fifaGreen-900/60 shadow-2xl relative">
            
            {/* Header branding */}
            <header className="bg-gradient-to-r from-fifaGreen-900 via-fifaGreen-800 to-fifaGreen-900 p-4 border-b border-fifaGreen-700/60 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold bg-fifaGold-400 text-stadiumDark-950 p-1.5 rounded-xl shadow-md border border-fifaGold-500" aria-hidden="true">⚽</span>
                    <div>
                        <h1 className="font-heading font-extrabold text-base tracking-tight text-white uppercase">FIFA World Cup 2026</h1>
                        <span className="text-[10px] text-fifaGold-400 font-bold tracking-widest block uppercase">Stadium Venue Assistant</span>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={() => setIsDemoMode(!isDemoMode)}
                        className={`text-[10px] uppercase font-bold py-1 px-2.5 rounded-lg border transition-all ${
                            isDemoMode 
                                ? 'bg-amber-600 text-white border-amber-500' 
                                : 'bg-fifaGreen-900 border-fifaGreen-700 text-fifaGreen-300'
                        }`}
                        title="Toggle Demo/Live Server interaction"
                    >
                        {isDemoMode ? 'Demo Mode' : 'Live Server'}
                    </button>
                </div>
            </header>

            {/* Accessibility Control panel */}
            <A11yControls 
                highContrast={highContrast} 
                setHighContrast={setHighContrast} 
                largeText={largeText} 
                setLargeText={setLargeText}
                speechEnabled={speechEnabled}
                setSpeechEnabled={setSpeechEnabled}
                currentLang={currentLang}
                setCurrentLang={setCurrentLang}
            />

            {/* Chat Box Area */}
            <main 
                className="flex-1 overflow-y-auto p-4 flex flex-col space-y-4"
                role="log"
                aria-live="polite"
                aria-label="Venue chatbot log window"
            >
                {messages.length === 0 && (
                    <div className="text-center py-8">
                        <Icons.Info />
                        <p className="text-sm text-gray-400 mt-2">Loading venue directories...</p>
                    </div>
                )}

                {messages.map((msg, index) => (
                    <MessageBubble 
                        key={index} 
                        role={msg.role} 
                        content={msg.content} 
                        meta={msg.meta}
                        onRouteMe={(facilityName) => {
                            const routeQuery = `Can I get directions from my location to ${facilityName}?`;
                            handleSendMessage(routeQuery);
                        }}
                    />
                ))}

                {/* Thinking / Loading indicator */}
                {isThinking && (
                    <div className="flex items-center gap-2 text-xs text-gray-500 bg-stadiumDark-900 border border-gray-800 p-3 rounded-2xl w-fit animate-pulse" role="status" aria-label="Assistant is thinking">
                        <Icons.Refresh />
                        <span>FIFA Server is lookup database...</span>
                    </div>
                )}
                
                {/* Speech status announcement */}
                {!speechSupported && (
                    <div className="text-center p-2.5 bg-fifaRed-500/10 border border-fifaRed-500/30 rounded-lg text-xs text-red-300">
                        🎤 Speech recognition isn't supported in this browser. Try Google Chrome or Safari.
                    </div>
                )}

                <div ref={chatBoxEndRef} />
            </main>

            {/* Sticky Actions & Quick Chips bar */}
            <section className="bg-stadiumDark-900/90 border-t border-gray-900 p-3" aria-label="Suggested questions shortcut buttons">
                <div className="flex gap-2 overflow-x-auto pb-1 scroll-bar-none">
                    <button 
                        onClick={() => handleQuickAction('route')}
                        className="bg-fifaGreen-950 hover:bg-fifaGreen-900 border border-fifaGreen-800/80 text-fifaGreen-200 text-xs px-3.5 py-2.5 rounded-full font-bold whitespace-nowrap min-h-[44px] flex items-center gap-1.5 focus:ring-2 focus:ring-fifaGold-400 focus:outline-none"
                    >
                        ♿ Accessible Route
                    </button>
                    <button 
                        onClick={() => handleQuickAction('toilet')}
                        className="bg-stadiumDark-850 hover:bg-stadiumDark-800 border border-gray-800 text-gray-300 text-xs px-3.5 py-2.5 rounded-full font-bold whitespace-nowrap min-h-[44px] flex items-center gap-1.5 focus:ring-2 focus:ring-fifaGold-400 focus:outline-none"
                    >
                        🚽 Restrooms
                    </button>
                    <button 
                        onClick={() => handleQuickAction('gate')}
                        className="bg-stadiumDark-850 hover:bg-stadiumDark-800 border border-gray-800 text-gray-300 text-xs px-3.5 py-2.5 rounded-full font-bold whitespace-nowrap min-h-[44px] flex items-center gap-1.5 focus:ring-2 focus:ring-fifaGold-400 focus:outline-none"
                    >
                        🚪 Gate B Queue
                    </button>
                    <button 
                        onClick={() => handleQuickAction('bag')}
                        className="bg-stadiumDark-850 hover:bg-stadiumDark-800 border border-gray-800 text-gray-300 text-xs px-3.5 py-2.5 rounded-full font-bold whitespace-nowrap min-h-[44px] flex items-center gap-1.5 focus:ring-2 focus:ring-fifaGold-400 focus:outline-none"
                    >
                        🎒 Bag Policy
                    </button>
                </div>
            </section>

            {/* Input Form Bar */}
            <footer className="bg-stadiumDark-900 border-t border-fifaGreen-900/60 p-3.5 pb-5">
                <form 
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSendMessage();
                    }}
                    className="flex gap-2.5 items-center"
                >
                    <div className="relative flex-1">
                        <label htmlFor="chat-text-input" className="sr-only">Type a stadium or routing question</label>
                        <input 
                            id="chat-text-input"
                            type="text" 
                            value={inputMsg}
                            onChange={(e) => setInputMsg(e.target.value)}
                            placeholder={currentLang === 'es-ES' ? 'Pregunta algo al asistente...' : currentLang === 'fr-FR' ? 'Demander quelque chose...' : 'Ask the venue tech assistant...'}
                            className="w-full bg-stadiumDark-950 border border-gray-800 rounded-xl px-4 py-3.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-fifaGold-400 min-h-[48px]"
                        />
                    </div>

                    <button 
                        type="button"
                        onClick={toggleRecording}
                        className={`w-12 h-12 flex items-center justify-center rounded-xl border transition-all focus:outline-none focus:ring-2 focus:ring-fifaGold-400 ${
                            isRecording 
                                ? 'bg-red-600 border-red-500 text-white animate-pulse' 
                                : 'bg-stadiumDark-950 border-gray-800 text-fifaGold-400 hover:bg-stadiumDark-850'
                        }`}
                        aria-pressed={isRecording}
                        aria-label={isRecording ? "Stop voice recording" : "Start voice input"}
                    >
                        <Icons.Mic active={isRecording} />
                    </button>

                    <button 
                        type="submit"
                        className="bg-fifaGreen-600 hover:bg-fifaGreen-500 text-white font-extrabold uppercase text-xs px-4 py-3.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-fifaGold-400 min-h-[48px]"
                        aria-label="Send query"
                    >
                        Send
                    </button>
                </form>
                
                <div className="flex justify-between text-[9px] text-gray-500 mt-3 px-1 uppercase tracking-wide">
                    <span>Keyboard shortcuts: ESC to type, CTRL+SPACE to speak</span>
                    <span>Safety: Text 'HELP' to 69050</span>
                </div>
            </footer>
        </div>
    );
}

// Render root App
const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);
root.render(<App />);
