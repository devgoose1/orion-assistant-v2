# Orion Assistant API Documentation

## Overview

Orion Assistant provides a WebSocket-based API for bidirectional communication between Godot clients and a Python backend. The backend orchestrates LLM requests, tool execution, and device management.

**Version:** 2.0  
**Python:** 3.8+  
**Framework:** FastAPI with Uvicorn  
**LLM:** Ollama Cloud API (gpt-oss:120b)  
**Database:** SQLite

---

## Table of Contents

1. [WebSocket API](#websocket-api)
2. [HTTP REST API](#http-rest-api)
3. [Message Types](#message-types)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Examples](#examples)
7. [Configuration](#configuration)

---

## WebSocket API

### Endpoint

```text
ws://localhost:8765/ws
```

### Connection Lifecycle

1. **Connect** - Client establishes WebSocket connection
2. **Register** - Send `device_register` message with device info
3. **Communicate** - Bidirectional message exchange
4. **Heartbeat** - Periodic keep-alive messages (recommended: 30-60s)
5. **Disconnect** - Clean closure or timeout after 5 min inactivity

### Message Format

All WebSocket messages are JSON objects:

```json
{
  "type": "message_type",
  "data": { /* type-specific fields */ }
}
```

---

## Message Types

### 1. Device Registration

**Direction:** Client → Server  
**Description:** Register a new device with capabilities and metadata

```json
{
  "type": "device_register",
  "device_id": "11b747f61a920705",
  "device_name": "Desktop-PC",
  "os_type": "Windows",
  "os_version": "10.0.26200",
  "capabilities": {
    "gpu": "NVIDIA RTX 3080",
    "browser": "Chrome"
  },
  "metadata": {
    "processor_name": "Intel Core i9-13900K",
    "ram_gb": 32,
    "disk_gb": 2000
  }
}
```

**Response:**

```json
{
  "type": "device_registered",
  "device_id": "11b747f61a920705",
  "status": "registered"
}
```

---

### 2. Heartbeat

**Direction:** Client → Server  
**Description:** Keep-alive signal with device status

```json
{
  "type": "heartbeat",
  "device_id": "11b747f61a920705",
  "timestamp": "2026-02-13T10:30:00.000Z",
  "status": "online"
}
```

**Response:** Acknowledged by server, updated last_heartbeat timestamp

---

### 3. LLM Request

**Direction:** Client → Server  
**Description:** Request LLM processing with optional streaming

```json
{
  "type": "llm_request",
  "prompt": "Create a folder called Documents on my desktop",
  "stream": true,
  "session_id": "session_abc123",
  "model": "gpt-oss:120b"
}
```

**Responses (streaming mode):**

```json
{
  "type": "llm_response_chunk",
  "chunk": "I'll create ",
  "complete": false
}
```

```json
{
  "type": "llm_response_chunk",
  "chunk": "the Documents folder on your desktop...",
  "complete": true
}
```

**Streaming with Tool Calls:**

```json
{
  "type": "tool_executing",
  "tool_name": "create_directory",
  "parameters": {
    "path": "C:/Users/Desktop/Documents"
  }
}
```

```json
{
  "type": "llm_response",
  "message": "I've created the Documents folder on your desktop."
}
```

---

### 4. Tool Result

**Direction:** Client → Server  
**Description:** Send tool execution result back to LLM

```json
{
  "type": "tool_result",
  "request_id": "exec_12345",
  "tool_name": "create_directory",
  "success": true,
  "result": {
    "path": "C:/Users/Desktop/Documents",
    "created": true
  }
}
```

---

### 5. Tool Execution (Device-side)

**Direction:** Server → Client  
**Description:** Command to execute tool on device

```json
{
  "type": "tool_execute",
  "request_id": "exec_12345",
  "tool_name": "create_directory",
  "parameters": {
    "path": "C:/Users/Desktop/Documents"
  }
}
```

---

## HTTP REST API

### Base URL

```text
http://localhost:8765
```

### Endpoints

#### 1. Test Tool Execution

**Endpoint:** `POST /test/tool`  
**Description:** Manually trigger a tool execution (testing only)

**Request:**

```json
{
  "device_id": "11b747f61a920705",
  "tool": "get_device_info",
  "params": {}
}
```

**Response:**

```json
{
  "success": true,
  "request_id": "test_1623456789",
  "device_id": "11b747f61a920705",
  "tool": "get_device_info",
  "message": "Tool execution triggered"
}
```

**Status Codes:**

- `200` - Tool execution triggered successfully
- `404` - Device not connected
- `400` - Invalid request

---

#### 2. List Connected Devices

**Endpoint:** `GET /test/devices`  
**Description:** Get list of currently connected devices

**Response:**

```json
{
  "success": true,
  "devices": [
    {
      "device_id": "11b747f61a920705",
      "connected": true
    },
    {
      "device_id": "xxxxxxxxxxxxxxxx",
      "connected": true
    }
  ],
  "count": 2
}
```

**Status Codes:**

- `200` - Success
- `500` - Server error

---

## Data Models

### Device

```python
{
  "device_id": str,           # Unique device identifier
  "device_name": str,         # Human-readable name
  "os_type": str,             # "Windows", "Linux", "macOS"
  "os_version": str,          # Version number (e.g., "10.0.26200")
  "architecture": str,        # "x86_64", "arm64"
  "capabilities": dict,       # Custom capabilities dict
  "cpu_info": str,            # Processor name
  "ram_gb": int,              # RAM in gigabytes
  "disk_gb": int,             # Total disk in gigabytes
  "allowed_tools": list,      # List of tool names
  "allowed_paths": list,      # List of accessible paths
  "allowed_apps": list,       # List of executable apps
  "status": str,              # "online", "offline"
  "last_heartbeat": datetime, # Last heartbeat timestamp
  "registered_at": datetime   # Registration timestamp
}
```

### Tool Definition

```python
{
  "name": str,                # Tool identifier
  "description": str,         # Human-readable description
  "category": str,            # "file_system", "application", "device"
  "parameters": [
    {
      "name": str,            # Parameter name
      "type": str,            # "string", "integer", "boolean", "array"
      "required": bool,       # Is this parameter required?
      "description": str,
      "default": any,         # Default value if optional
      "validation_regex": str  # Optional regex validation
    }
  ],
  "permission_type": str,     # "tool", "path", "app"
  "dangerous": bool           # Requires confirmation?
}
```

### Conversation Message

```python
{
  "role": str,        # "system", "user", "assistant"
  "content": str      # Message text
}
```

---

## Configuration

Configuration constants are stored in `backend/config.py`:

```python
# Ollama settings
DEFAULT_OLLAMA_MODEL = "gpt-oss:120b"
DEFAULT_OLLAMA_URL = "https://ollama.com"

# Conversation management
CONVERSATION_HISTORY_LIMIT = 20      # Keep last N messages
MAX_TOOL_ITERATIONS = 5              # Max tool call loops
TOOL_EXECUTION_TIMEOUT = 10.0        # Seconds to wait for result

# Heuristic phrases for tool detection
TOOL_HEURISTIC_PHRASES = {
  "create a folder", "create directory", "write file",
  "copy file", "move file", "delete file", ...
}

# Default permissions for new devices
DEFAULT_ALLOWED_TOOLS = [
  "create_directory", "delete_directory", "search_files",
  "list_directory", "read_text_file", "write_text_file",
  ...
]
DEFAULT_ALLOWED_PATHS = ["C:/Users", "D:/Projects", ...]
DEFAULT_ALLOWED_APPS = ["chrome", "firefox", "code", ...]
```

---

## Error Handling

### WebSocket Errors

**Device Not Registered:**

```json
{
  "type": "error",
  "error": "Device not registered"
}
```

**Tool Execution Failure:**

```json
{
  "type": "error",
  "error": "Tool execution failed: [details]"
}
```

**LLM Request Error:**

```json
{
  "type": "error",
  "error": "LLM API error: [details]"
}
```

### HTTP Errors

**404 Device Not Found:**

```json
{
  "success": false,
  "error": "Device xyz not connected"
}
```

**500 Server Error:**

```json
{
  "success": false,
  "error": "Internal server error"
}
```

---

## Examples

### Example 1: Full LLM + Tool Workflow (Streaming)

```text
CLIENT: Connect to ws://localhost:8765/ws
SERVER: Connection accepted

CLIENT: Register device
{
  "type": "device_register",
  "device_id": "device123",
  "device_name": "My PC",
  "os_type": "Windows",
  "os_version": "10.0.26200",
  "capabilities": {},
  "metadata": {"ram_gb": 16, "disk_gb": 512}
}

SERVER: Registration acknowledged
{
  "type": "device_registered",
  "device_id": "device123",
  "status": "registered"
}

CLIENT: Request LLM processing with streaming
{
  "type": "llm_request",
  "prompt": "Create a test folder on my desktop",
  "stream": true,
  "session_id": "session001",
  "model": "gpt-oss:120b"
}

SERVER: Stream response chunks
{
  "type": "llm_response_chunk",
  "chunk": "I'll create",
  "complete": false
}
{
  "type": "llm_response_chunk",
  "chunk": " a test folder on your desktop.",
  "complete": false
}

SERVER: Detected tool call, send to device
{
  "type": "tool_execute",
  "request_id": "exec_001",
  "tool_name": "create_directory",
  "parameters": {"path": "C:/Users/Desktop/TestFolder"}
}

CLIENT: Execute tool and return result
{
  "type": "tool_result",
  "request_id": "exec_001",
  "tool_name": "create_directory",
  "success": true,
  "result": {"path": "C:/Users/Desktop/TestFolder", "created": true}
}

SERVER: Continue LLM processing with result
SERVER: Stream final response
{
  "type": "llm_response",
  "message": "Done! I've created the TestFolder on your desktop."
}
```

### Example 2: Manual Tool Testing

```bash
curl -X POST http://localhost:8765/test/tool \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device123",
    "tool": "get_device_info",
    "params": {}
  }'
```

Response:

```json
{
  "success": true,
  "request_id": "test_1623456789",
  "device_id": "device123",
  "tool": "get_device_info",
  "message": "Tool execution triggered"
}
```

---

## Authentication & Security

- **WebSocket:** Device-based via `device_id` (assumed trusted network)
- **HTTP Testing Endpoints:** Local only, should be protected in production
- **Tool Execution:** Permission checks per device for tools/paths/apps
- **Dangerous Operations:** Require explicit confirmation (e.g., `confirm="DELETE"` for delete_file)

---

## Performance Considerations

- **Conversation History:** Limited to 20 messages to manage token usage
- **Tool Iterations:** Max 5 iterations per request to prevent infinite loops
- **Tool Timeout:** 10 seconds per tool execution result wait (configurable)
- **Streaming:** Real-time chunks sent as they arrive from LLM

---

## Troubleshooting

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| "Device not connected" | Device not registered | Call device_register first |
| Tool execution timeout | Device offline or slow | Check device heartbeat, increase timeout |
| LLM API errors | Ollama Cloud unavailable | Verify API key, check network connectivity |
| Partial responses | Connection interrupted | Reconnect and retry |
| Tool not found | Tool name misspelled | Check TOOL_HEURISTIC_PHRASES, list tools |

---

## Related Files

- `backend/main.py` - WebSocket/HTTP endpoint implementations  
- `backend/tools/router.py` - Tool execution routing and validation
- `backend/tools/registry.py` - Tool definitions and metadata
- `backend/config.py` - Configuration constants
- `backend/database.py` - SQLite models and initialization

---

**Last Updated:** February 13, 2026  
**Maintainer:** Orion Assistant Development Team
