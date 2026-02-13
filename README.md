# Orion Assistant v2

## Multi-device AI Assistant met Ollama Cloud Integration

Orion Assistant v2 is een intelligente, multi-device assistent die natuurlijke taal gebruikt om devices te besturen, bestanden te beheren, homelab services te monitoren en creatieve tools te ondersteunen.

## 🎯 Project Overview

### Architectuur

- **Backend**: FastAPI (Python) - Central coordinator & LLM interface
- **Clients**: Godot 4.x (GDScript) - Device agents op elk apparaat
- **LLM**: Ollama Cloud (gratis tier) - `gpt-oss:120b`
- **Communication**: WebSocket (persistent real-time verbindingen)

### Core Concept

De assistent bestaat uit:

1. **Backend Server** - Centraal brein, LLM coordinator, tool validator
2. **Device Clients** - Agenten op elk apparaat (Godot apps)
3. **LLM Layer** - Ollama Cloud voor natuurlijke taal processing
4. **Tool System** - Veilige, gestructureerde actie uitvoering

---

## 📂 Project Structure

```text
orion-assistant-v2/
├── backend/                    # Python FastAPI server
│   ├── main.py                # WebSocket server & LLM integration
│   ├── .env                   # API keys & configuratie
│   ├── requirements.txt       # Python dependencies
│   └── (toekomstig)
│       ├── tools/             # Tool implementations
│       ├── models/            # Database models
│       ├── services/          # Business logic
│       └── utils/             # Helpers
│
├── client/                     # Godot device clients
│   ├── websocket.gd           # WebSocket client
│   ├── test_scene.gd          # Test scene
│   ├── project.godot          # Godot project
│   └── (toekomstig)
│       ├── tools/             # Client-side tool executors
│       ├── monitors/          # Event monitors
│       └── ui/                # User interface
│
└── docs/                       # Documentatie (deze folder)
    ├── ARCHITECTURE.md         # Systeem architectuur
    ├── API.md                  # API specificaties
    ├── TOOLS.md                # Tool calling system
    └── SECURITY.md             # Security & permissions
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Conda environment (orion-assistant-v2)
- Godot 4.6+
- Ollama Cloud account + API key

### Setup Backend

```bash
cd backend
conda activate orion-assistant-v2
pip install -r requirements.txt

# Configureer .env bestand
# OLLAMA_API_URL=https://ollama.com
# OLLAMA_API_KEY=your_key_here
# OLLAMA_MODEL=gpt-oss:120b

python main.py
```

### Setup Client (Godot)

1. Open `client/project.godot` in Godot
2. Maak een test scene met WebSocketNode
3. Attach `websocket.gd` aan de node
4. Run de scene

---

## 🧠 Features (Roadmap)

### ✅ Phase 0: Foundation (COMPLETED)

- [x] WebSocket communication layer
- [x] Ollama Cloud LLM integration
- [x] Streaming responses
- [x] Basic client-server connection

### 🔧 Phase 1: Core System (COMPLETED)

- [x] Tool/Function calling system
- [x] Device registration & identification
- [x] Permission & safety layer
- [x] Basic file operations
- [x] Application control

### 📋 Phase 2: LLM Tool Calling Integration (COMPLETED)

- [x] Tool schema in system prompt
- [x] Tool call parsing and validation
- [x] Tool execution loop with result handling
- [x] Streaming + tool calling support
- [x] Conversation context management

### 🧭 Phase 3: Multi-Device Control (NEXT)

- [ ] File search across devices
- [ ] Device event monitoring
- [ ] Cross-device coordination

### 🏠 Phase 3: Homelab Integration

- [ ] Service awareness (Docker, APIs)
- [ ] Health monitoring
- [ ] Service control
- [ ] Web scraping tool

### 🎨 Phase 4: Advanced Features

- [ ] Voice interface (STT/TTS)
- [ ] Code generation assistant
- [ ] CAD integration (OpenSCAD/FreeCAD)
- [ ] Arduino/Pi circuit builder
- [ ] Model switching & fallbacks

---

## 🔐 Security Principles

1. **Tool Whitelisting** - Alleen gevalideerde tools mogen uitgevoerd worden
2. **Path Restrictions** - File operations binnen toegestane directories
3. **Permission Layer** - Per device configureerbare rechten
4. **Audit Logging** - Alle acties worden gelogd
5. **No Direct Shell Access** - Geen directe OS command execution

---

## 📚 Documentation

Zie de `docs/` folder voor gedetailleerde documentatie:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Systeem architectuur en data flow
- **[API.md](docs/API.md)** - WebSocket API & message formats
- **[TOOLS.md](docs/TOOLS.md)** - Tool calling system & implementatie
- **[SECURITY.md](docs/SECURITY.md)** - Security model & best practices
- **[DATABASE.md](docs/DATABASE.md)** - Database schema & context management

---

## 🛠️ Tech Stack

### Backend

- **FastAPI** - Async web framework
- **Uvicorn** - ASGI server
- **Ollama SDK** - LLM client library
- **WebSockets** - Real-time communication
- **SQLAlchemy** - ORM
- **Python-dotenv** - Environment configuration

### Client

- **Godot 4.6** - Game engine / app framework
- **GDScript** - Client scripting
- **WebSocketPeer** - WebSocket client

### Infrastructure

- **Ollama Cloud** - LLM inference (gratis tier)
- **Docker** (optioneel) - Container deployment
- **SQLite** - Database (current)
- **PostgreSQL** (toekomstig) - Production database

---

## 🤝 Contributing

Dit is een persoonlijk project, maar suggesties zijn welkom via issues!

---

## 📄 License

MIT License (of andere naar keuze)

---

## 🔗 Links

- [Ollama Cloud Docs](https://docs.ollama.com/cloud)
- [Godot Engine](https://godotengine.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
