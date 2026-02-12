# WebSocket API Specification

## Connection

**Endpoint:** `ws://localhost:8765/ws`  
**Protocol:** WebSocket (JSON messages)

---

## Message Format

All messages are JSON objects with a `type` field:

```json
{
  "type": "message_type",
  "field1": "value1",
  "field2": "value2"
}
```

---

## Client → Backend Messages

### 1. Device Registration

Eerste bericht dat een client stuurt na verbinding.

```json
{
  "type": "device_register",
  "device_id": "laptop-123",
  "hostname": "NJSCH-LAPTOP",
  "os": "Windows",
  "os_version": "11",
  "capabilities": {
    "file_operations": true,
    "app_control": true,
    "voice": false,
    "homelab": false
  },
  "metadata": {
    "cpu": "AMD Ryzen 7",
    "ram_gb": 16,
    "disk_gb": 512
  }
}
```

**Response:**

```json
{
  "type": "device_registered",
  "device_id": "laptop-123",
  "permissions": {
    "allowed_tools": ["create_directory", "delete_directory", "open_app"],
    "allowed_paths": ["C:/Users/njsch", "D:/Projects"],
    "allowed_apps": ["code", "chrome", "explorer"]
  }
}
```

---

### 2. Device Heartbeat

Keep-alive ping elke 30 seconden.

```json
{
  "type": "device_heartbeat",
  "device_id": "laptop-123",
  "timestamp": "2026-02-12T10:30:00Z"
}
```

**Response:**

```json
{
  "type": "heartbeat_ack",
  "timestamp": "2026-02-12T10:30:01Z"
}
```

---

### 3. Tool Result

Resultaat van een uitgevoerde tool.

```json
{
  "type": "tool_result",
  "device_id": "laptop-123",
  "tool_call_id": "call-abc123",
  "success": true,
  "result": {
    "created_path": "C:/Users/njsch/Test",
    "message": "Directory created successfully"
  },
  "executed_at": "2026-02-12T10:30:05Z"
}
```

**Error Example:**

```json
{
  "type": "tool_result",
  "device_id": "laptop-123",
  "tool_call_id": "call-abc123",
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Access to C:/Windows is not allowed"
  },
  "executed_at": "2026-02-12T10:30:05Z"
}
```

---

### 4. Device Event

Proactieve events van device.

```json
{
  "type": "event",
  "device_id": "laptop-123",
  "event_type": "low_disk_space",
  "severity": "warning",
  "data": {
    "drive": "C:",
    "free_gb": 5.2,
    "total_gb": 512,
    "percentage_free": 1.0
  },
  "timestamp": "2026-02-12T10:45:00Z"
}
```

**Event Types:**

- `low_disk_space` - Disk space < 10%
- `high_cpu_usage` - CPU > 90% for 5 min
- `new_file_detected` - File watcher detected change
- `service_down` - Homelab service offline
- `error_occurred` - General error

---

### 5. User Query (Future)

Direct user input vanaf client UI.

```json
{
  "type": "user_query",
  "device_id": "laptop-123",
  "query": "Maak een folder Test op mijn laptop",
  "timestamp": "2026-02-12T10:50:00Z"
}
```

---

## Backend → Client Messages

### 1. Tool Execute

Instructie om een tool uit te voeren.

```json
{
  "type": "tool_execute",
  "tool_call_id": "call-abc123",
  "tool": "create_directory",
  "parameters": {
    "path": "C:/Users/njsch/Test"
  },
  "timeout_sec": 30
}
```

**Tool Examples:**

**Create Directory:**

```json
{
  "type": "tool_execute",
  "tool_call_id": "call-001",
  "tool": "create_directory",
  "parameters": {
    "path": "C:/Projects/NewProject"
  }
}
```

**Delete Directory:**

```json
{
  "type": "tool_execute",
  "tool_call_id": "call-002",
  "tool": "delete_directory",
  "parameters": {
    "path": "C:/Temp/OldFolder",
    "recursive": true
  }
}
```

**Open Application:**

```json
{
  "type": "tool_execute",
  "tool_call_id": "call-003",
  "tool": "open_app",
  "parameters": {
    "app": "chrome",
    "args": ["https://google.com"]
  }
}
```

**Search Files:**

```json
{
  "type": "tool_execute",
  "tool_call_id": "call-004",
  "tool": "search_files",
  "parameters": {
    "query": "project_alpha.zip",
    "path": "C:/Users/njsch",
    "recursive": true
  }
}
```

---

### 2. Assistant Response

LLM antwoord voor gebruiker.

```json
{
  "type": "assistant_response",
  "response": "Ik heb de folder Test aangemaakt op je laptop in C:/Users/njsch/Test",
  "timestamp": "2026-02-12T10:30:10Z"
}
```

---

### 3. LLM Request (Current Implementation)

Request naar LLM via client.

```json
{
  "type": "llm_request",
  "prompt": "Hallo! Wat kun je doen?",
  "model": "gpt-oss:120b",
  "stream": true
}
```

---

### 4. LLM Response Chunk (Streaming)

Streaming response van LLM.

```json
{
  "type": "llm_response_chunk",
  "chunk": "Ik ben een AI assistent ",
  "complete": false
}
```

**Final Chunk:**

```json
{
  "type": "llm_response_chunk",
  "chunk": "",
  "complete": true
}
```

---

### 5. System Command

Systeem commando's.

```json
{
  "type": "system_command",
  "command": "restart_client",
  "reason": "Update available"
}
```

**Commands:**

- `restart_client` - Herstart de client
- `update_permissions` - Nieuwe permissions laden
- `shutdown` - Graceful shutdown

---

## Error Responses

### General Error

```json
{
  "type": "error",
  "error_code": "TOOL_EXECUTION_FAILED",
  "message": "Tool execution failed: Permission denied",
  "details": {
    "tool": "create_directory",
    "path": "C:/Windows/System32/Test"
  },
  "timestamp": "2026-02-12T10:30:15Z"
}
```

**Error Codes:**

- `INVALID_MESSAGE` - Malformed JSON
- `UNKNOWN_DEVICE` - Device not registered
- `PERMISSION_DENIED` - Action not allowed
- `TOOL_NOT_FOUND` - Unknown tool
- `TOOL_EXECUTION_FAILED` - Tool crashed
- `TIMEOUT` - Operation timed out
- `INVALID_PARAMETERS` - Bad parameters

---

## Connection Lifecycle

```text
1. Client connects
   → WebSocket handshake

2. Client sends device_register
   → Backend validates & stores device
   → Backend responds with permissions

3. Normal operation
   → Heartbeats every 30s
   → Tool executions
   → Events

4. Disconnect
   → Backend marks device as offline
   → Attempts reconnect (client side)
```

---

## Rate Limits (Future)

- **Max messages per second:** 10
- **Max tool executions per minute:** 20
- **Max heartbeat frequency:** 1 per 10 seconds

---

## Authentication (Future)

Voor productie deployment met remote access:

```json
{
  "type": "device_register",
  "device_id": "laptop-123",
  "auth_token": "Bearer eyJhbGciOiJIUzI1NiIs...",
  ...
}
```

Backend valideert JWT token voordat connectie wordt geaccepteerd.

---

## WebSocket States

**Client States:**

- `CONNECTING` - Handshake in progress
- `CONNECTED` - WebSocket open
- `REGISTERING` - Sending device_register
- `REGISTERED` - Device registered, ready
- `DISCONNECTED` - Connection lost
- `RECONNECTING` - Attempting reconnect

**Backend Device States:**

- `ONLINE` - Recently received heartbeat
- `IDLE` - No heartbeat for 60s
- `OFFLINE` - No heartbeat for 5 min
- `UNKNOWN` - Never registered

---

## Example Flows

### Flow 1: Create Directory

```text
Client                     Backend                    LLM
  │                           │                        │
  │──device_register─────────►│                        │
  │◄──device_registered───────│                        │
  │                           │                        │
  │                           │◄──user query───────────│
  │                           │   "Maak folder Test"   │
  │                           │                        │
  │                           │──prompt───────────────►│
  │                           │◄──tool_call────────────│
  │                           │   {create_directory}   │
  │                           │                        │
  │◄──tool_execute────────────│                        │
  │                           │                        │
  │──tool_result──────────────►│                        │
  │   {success: true}         │                        │
  │                           │──result────────────────►│
  │                           │◄──response─────────────│
  │                           │   "Folder aangemaakt"  │
```

### Flow 2: Low Disk Space Event

```text
Client                     Backend                    LLM
  │                           │                        │
  │──event────────────────────►│                        │
  │   {low_disk_space}        │                        │
  │                           │──prompt───────────────►│
  │                           │   "Disk space low..."  │
  │                           │                        │
  │                           │◄──response─────────────│
  │                           │   "Clean temp files"   │
  │                           │──tool_call────────────►│
  │◄──tool_execute────────────│                        │
  │   {delete_directory}      │                        │
```

---

## Testing

### Mock Client (Python)

```python
import asyncio
import websockets
import json

async def test_client():
    uri = "ws://localhost:8765/ws"
    async with websockets.connect(uri) as ws:
        # Register
        await ws.send(json.dumps({
            "type": "device_register",
            "device_id": "test-001",
            "hostname": "test-machine"
        }))
        
        # Wait for response
        response = await ws.recv()
        print(response)

asyncio.run(test_client())
```
