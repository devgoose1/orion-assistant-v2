# System Architecture

## Overview

Orion Assistant v2 gebruikt een **hub-and-spoke** architectuur waarbij een centrale backend server communiceert met meerdere device clients via WebSocket verbindingen.

```text
                          ┌─────────────────┐
                          │  Ollama Cloud   │
                          │   (LLM API)     │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │                 │
                          │  Backend Server │◄──── HTTP/REST (future)
                          │   (FastAPI)     │
                          │                 │
                          └─┬──────┬──────┬─┘
                            │      │      │
                   WebSocket│      │      │WebSocket
                            │      │      │
              ┌─────────────▼┐  ┌──▼──────▼──────┐
              │   Client 1   │  │    Client 2     │
              │  (Laptop)    │  │  (Desktop PC)   │
              └──────────────┘  └─────────────────┘
```

---

## Components

### 1. Backend Server (Python/FastAPI)

**Verantwoordelijkheden:**

- WebSocket connection management
- LLM query processing
- Tool call validation & routing
- Device registry & state management
- Permission enforcement
- Event aggregation & prioritization
- Context & memory management

**Key Modules:**

- `main.py` - Server entry point, WebSocket endpoints
- `tools/` - Tool implementations & validators
- `models/` - Database models (devices, sessions, logs)
- `services/` - Business logic (LLM service, device service)
- `utils/` - Helpers (permissions, logging)

---

### 2. Device Clients (Godot/GDScript)

**Verantwoordelijkheden:**

- Persistent WebSocket connection to backend
- Device registration & heartbeat
- Tool execution (file ops, app control)
- Event monitoring & reporting
- Local safety checks

**Key Components:**

- `websocket.gd` - WebSocket communication layer
- `tools/` - Tool executors (create_directory, open_app, etc.)
- `monitors/` - System monitors (disk space, CPU, events)
- `device_info.gd` - Device metadata provider

---

### 3. LLM Layer (Ollama Cloud)

**Model:** `gpt-oss:120b` (cloud inference)

**Role:**

- Natural language understanding
- Tool call generation (structured JSON)
- Response generation
- Context-aware decision making

**API Format:**

```python
messages = [
    {"role": "system", "content": "System prompt..."},
    {"role": "user", "content": "User query..."}
]
response = client.chat(model="gpt-oss:120b", messages=messages)
```

---

## Data Flow

### User Query Flow

```text
1. User → Client UI
   "Maak een folder Test op mijn laptop"

2. Client → Backend (WebSocket)
   {
     "type": "user_query",
     "query": "Maak een folder Test op mijn laptop",
     "device_id": "laptop-123"
   }

3. Backend → LLM (Ollama Cloud)
   messages = [
     {"role": "system", "content": "...tool definitions..."},
     {"role": "user", "content": "Maak een folder Test op mijn laptop"}
   ]

4. LLM → Backend (Tool Call)
   {
     "tool": "create_directory",
     "device": "laptop-123",
     "path": "C:/Users/njsch/Test"
   }

5. Backend validates & routes → Client (WebSocket)
   {
     "type": "tool_execute",
     "tool": "create_directory",
     "path": "C:/Users/njsch/Test"
   }

6. Client executes & responds
   {
     "type": "tool_result",
     "success": true,
     "message": "Directory created"
   }

7. Backend → LLM (Result)
   {"role": "user", "content": "Tool result: Directory created"}

8. LLM → Backend (Final Response)
   "Ik heb de folder Test aangemaakt op je laptop."

9. Backend → Client (Response)
   {
     "type": "assistant_response",
     "response": "Ik heb de folder Test aangemaakt op je laptop."
   }
```

---

## WebSocket Message Protocol

### Message Types

**From Client → Backend:**

- `device_register` - Device identifies itself
- `device_heartbeat` - Keep-alive ping
- `tool_result` - Result of tool execution
- `event` - Device event (low disk space, etc.)
- `user_query` (future) - Direct user input from client

**From Backend → Client:**

- `tool_execute` - Execute a tool
- `assistant_response` - LLM response to display
- `llm_request` - Request for LLM (current implementation)
- `llm_response_chunk` - Streaming LLM response
- `command` - System command (restart, update, etc.)

---

## Security Architecture

### Permission Layers

```text
┌─────────────────────────────────────┐
│  User Request                       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  LLM Tool Call Generation           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Backend Validation Layer           │
│  - Tool whitelist check             │
│  - Permission check                 │
│  - Path validation                  │
│  - Risk assessment                  │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │  ALLOWED?      │
       └───┬────────┬───┘
          YES       NO
           │         │
           │    ┌────▼─────┐
           │    │  REJECT  │
           │    └──────────┘
           │
┌──────────▼──────────────────────────┐
│  Route to Device Client             │
└──────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Client-side Safety Check           │
│  - Path within allowed dirs         │
│  - No dangerous operations          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Execute Tool                       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Audit Log                          │
└─────────────────────────────────────┘
```

### Whitelisting Strategy

**Backend:** Maintains allowed tools per device
**Client:** Double-checks paths and operations
**Logging:** Every action is logged with timestamp, device, user, tool, parameters

---

## Database Schema (Future)

### Tables

#### devices

- id (UUID)
- hostname
- os_type (Windows/Linux/Mac)
- last_seen (timestamp)
- capabilities (JSON)
- permissions (JSON)

#### sessions

- id (UUID)
- device_id (FK)
- started_at
- ended_at
- context (JSON)

#### tool_executions

- id (UUID)
- session_id (FK)
- device_id (FK)
- tool_name
- parameters (JSON)
- result (JSON)
- executed_at

#### events

- id (UUID)
- device_id (FK)
- event_type
- severity
- data (JSON)
- created_at

#### context_memory

- id (UUID)
- key (string)
- value (JSON)
- device_id (nullable FK)
- created_at
- expires_at (nullable)

---

## Scalability Considerations

### Current Design (v2.0)

- **Single backend instance**
- **Multiple clients** (up to ~100 devices)
- **In-memory state** (clients dict)

### Future (v3.0+)

- **Redis** for distributed state
- **PostgreSQL** for persistence
- **Load balancer** for multiple backend instances
- **Message queue** (RabbitMQ/Redis) for async tasks
- **Distributed tracing** (OpenTelemetry)

---

## Error Handling Strategy

### Backend

1. **Catch all exceptions** in WebSocket handlers
2. **Log error** with full context
3. **Return structured error** to client
4. **Keep connection alive** when possible

### Client

1. **Retry logic** for failed tool executions
2. **Reconnect** on WebSocket disconnect
3. **Local error logging**
4. **Graceful degradation** (offline mode future)

---

## Performance Targets

- **WebSocket latency:** < 50ms
- **LLM response time:** 2-10 seconds (depends on Ollama Cloud)
- **Tool execution:** < 1 second (most operations)
- **Client heartbeat:** Every 30 seconds
- **Max concurrent clients:** 100+

---

## Technology Choices - Rationale

| Technology | Why? |
| ---------- | ------ |
| **FastAPI** | Async-native, fast, modern Python, great WebSocket support |
| **Godot** | Cross-platform, game engine = UI flexibility, GDScript is simple |
| **WebSocket** | Real-time, persistent, bidirectional, low latency |
| **Ollama Cloud** | Free tier, good models, simple API |
| **SQLite → PostgreSQL** | Start simple, migrate when needed |

---

## Deployment Architecture (Future)

```text
┌──────────────────────────────────────────┐
│           Cloud / Server                 │
│                                          │
│  ┌────────────┐      ┌──────────────┐   │
│  │  Backend   │◄────►│ PostgreSQL   │   │
│  │  (Docker)  │      │  (Database)  │   │
│  └──────┬─────┘      └──────────────┘   │
│         │                                │
│         │ HTTPS/WSS                      │
└─────────┼────────────────────────────────┘
          │
          │ Internet
          │
    ┌─────┴──────────────┐
    │                    │
┌───▼────┐         ┌─────▼────┐
│Client 1│         │Client 2  │
│(Home)  │         │(Office)  │
└────────┘         └──────────┘
```

**Benefits:**

- Remote access from anywhere
- Centralized management
- Data persistence
- Better security (HTTPS/WSS)
