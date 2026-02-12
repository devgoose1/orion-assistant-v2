# Tool Calling System

## Overview

Het tool systeem is de kern van Orion Assistant. Het LLM genereert **gestructureerde tool calls**, de backend **valideert en routeert** deze, en de clients **voeren ze veilig uit**.

---

## Tool Call Flow

```text
1. User: "Maak een folder Test"
        ↓
2. LLM generates tool call:
   {
     "tool": "create_directory",
     "device": "laptop-123",
     "path": "C:/Users/njsch/Test"
   }
        ↓
3. Backend validates:
   ✓ Tool exists?
   ✓ Device has permission?
   ✓ Path is allowed?
        ↓
4. Backend routes to device
        ↓
5. Client executes tool
        ↓
6. Client returns result
        ↓
7. Backend sends to LLM
        ↓
8. LLM generates user-friendly response
```

---

## Tool Definition Schema

Elke tool heeft:

```python
{
    "name": "create_directory",
    "description": "Creates a new directory on the specified device",
    "category": "file_operations",
    "risk_level": "low",  # low, medium, high, critical
    "parameters": {
        "device": {
            "type": "string",
            "description": "Device ID to execute on",
            "required": true
        },
        "path": {
            "type": "string",
            "description": "Full path of directory to create",
            "required": true
        }
    },
    "returns": {
        "success": "bool",
        "created_path": "string",
        "message": "string"
    },
    "permissions_required": ["file_write"],
    "allowed_devices": ["all"]  # or specific device IDs
}
```

---

## Core Tools (Phase 1)

### File Operations

#### 1. create_directory

**Description:** Maakt een nieuwe directory aan.

**Parameters:**

- `device` (string, required) - Device ID
- `path` (string, required) - Full path

**Example:**

```json
{
  "tool": "create_directory",
  "device": "laptop-123",
  "path": "C:/Projects/NewFolder"
}
```

**Returns:**

```json
{
  "success": true,
  "created_path": "C:/Projects/NewFolder",
  "message": "Directory created successfully"
}
```

**Risk Level:** Low  
**Permissions:** `file_write`

---

#### 2. delete_directory

**Description:** Verwijdert een directory (optioneel recursief).

**Parameters:**

- `device` (string, required)
- `path` (string, required)
- `recursive` (bool, default: false)
- `confirm` (bool, required: true) - Safety check

**Example:**

```json
{
  "tool": "delete_directory",
  "device": "laptop-123",
  "path": "C:/Temp/OldFolder",
  "recursive": true,
  "confirm": true
}
```

**Risk Level:** High  
**Permissions:** `file_write`, `file_delete`

---

#### 3. search_files

**Description:** Zoekt bestanden op een device.

**Parameters:**

- `device` (string, required)
- `query` (string, required) - Filename pattern
- `path` (string, default: user home) - Search root
- `recursive` (bool, default: true)
- `max_results` (int, default: 100)

**Example:**

```json
{
  "tool": "search_files",
  "device": "laptop-123",
  "query": "*.zip",
  "path": "C:/Users/njsch",
  "recursive": true
}
```

**Returns:**

```json
{
  "success": true,
  "results": [
    {
      "path": "C:/Users/njsch/Downloads/project.zip",
      "size_bytes": 1048576,
      "modified": "2026-02-10T15:30:00Z"
    }
  ],
  "count": 1
}
```

**Risk Level:** Low  
**Permissions:** `file_read`

---

### Application Control

#### 4. open_app

**Description:** Opent een applicatie.

**Parameters:**

- `device` (string, required)
- `app` (string, required) - App identifier (chrome, code, etc.)
- `args` (array, optional) - Command line arguments

**Example:**

```json
{
  "tool": "open_app",
  "device": "laptop-123",
  "app": "chrome",
  "args": ["https://google.com"]
}
```

**Whitelisted Apps:**

- `chrome` → Google Chrome
- `firefox` → Mozilla Firefox
- `code` → VS Code
- `explorer` → File Explorer
- `terminal` → Terminal/PowerShell

**Risk Level:** Medium  
**Permissions:** `app_control`

---

#### 5. close_app (Optional, Phase 2)

**Description:** Sluit een draaiende applicatie.

**Risk Level:** High  
**Permissions:** `app_control`, `process_kill`

---

### Device Information

#### 6. get_device_info

**Description:** Haalt device informatie op.

**Parameters:**

- `device` (string, required)
- `include` (array, optional) - ["system", "disk", "network", "processes"]

**Example:**

```json
{
  "tool": "get_device_info",
  "device": "laptop-123",
  "include": ["system", "disk"]
}
```

**Returns:**

```json
{
  "success": true,
  "device_id": "laptop-123",
  "system": {
    "hostname": "NJSCH-LAPTOP",
    "os": "Windows 11",
    "cpu": "AMD Ryzen 7",
    "ram_gb": 16
  },
  "disk": {
    "drives": [
      {
        "letter": "C:",
        "total_gb": 512,
        "free_gb": 128,
        "percentage_free": 25
      }
    ]
  }
}
```

**Risk Level:** Low  
**Permissions:** `device_info`

---

## Advanced Tools (Phase 2+)

### Homelab Integration

#### 7. check_service_health

**Description:** Controleert health van homelab service.

**Parameters:**

- `service` (string) - docker, grafana, prometheus, pihole
- `endpoint` (string, optional) - Custom endpoint

**Risk Level:** Low

---

#### 8. restart_service

**Description:** Herstart een service/container.

**Risk Level:** High  
**Permissions:** `homelab_control`

---

### Web Tools

#### 9. fetch_webpage

**Description:** Haalt webpage content op.

**Parameters:**

- `url` (string, required)
- `extract` (string, optional) - "text", "links", "images"

**Risk Level:** Low

---

### Creative Tools

#### 10. generate_openscad

**Description:** Genereert OpenSCAD code voor 3D model.

**Risk Level:** Low

---

#### 11. generate_arduino_code

**Description:** Genereert Arduino sketch.

**Risk Level:** Low

---

## Tool Validation

### Backend Validation Steps

```python
def validate_tool_call(tool_call, device_id):
    # 1. Check if tool exists
    if tool_call["tool"] not in REGISTERED_TOOLS:
        raise ToolNotFoundError()
    
    # 2. Check device permissions
    device = get_device(device_id)
    if tool_call["tool"] not in device.allowed_tools:
        raise PermissionDeniedError()
    
    # 3. Validate parameters
    tool_schema = TOOLS[tool_call["tool"]]
    validate_parameters(tool_call["parameters"], tool_schema)
    
    # 4. Path validation (voor file operations)
    if "path" in tool_call["parameters"]:
        if not is_path_allowed(tool_call["parameters"]["path"], device):
            raise PathNotAllowedError()
    
    # 5. Risk assessment
    if tool_schema["risk_level"] == "high":
        require_confirmation(tool_call)
    
    return True
```

---

## Client-Side Tool Execution

### GDScript Tool Executor

```gdscript
# tools/file_operations.gd
extends Node

func create_directory(path: String) -> Dictionary:
    # Double-check path is allowed
    if not is_path_safe(path):
        return {
            "success": false,
            "error": "Path not allowed"
        }
    
    # Execute
    var dir = DirAccess.open(path.get_base_dir())
    if dir == null:
        return {"success": false, "error": "Invalid path"}
    
    var err = dir.make_dir(path.get_file())
    if err == OK:
        return {
            "success": true,
            "created_path": path,
            "message": "Directory created"
        }
    else:
        return {
            "success": false,
            "error": "Failed to create directory"
        }
```

---

## Safety Mechanisms

### 1. Whitelisting

**Backend:**

```python
DEVICE_PERMISSIONS = {
    "laptop-123": {
        "allowed_tools": ["create_directory", "open_app"],
        "allowed_paths": ["C:/Users/njsch", "D:/Projects"],
        "allowed_apps": ["chrome", "code"]
    }
}
```

**Client:**

```gdscript
const SAFE_PATHS = [
    "C:/Users/njsch",
    "D:/Projects"
]

func is_path_safe(path: String) -> bool:
    for safe_path in SAFE_PATHS:
        if path.begins_with(safe_path):
            return true
    return false
```

---

### 2. Confirmation for High-Risk

High-risk tools (delete, restart, etc.) vereisen expliciete confirmatie:

```json
{
  "tool": "delete_directory",
  "path": "C:/Important",
  "confirm": true  // REQUIRED
}
```

Backend weigert zonder `confirm: true`.

---

### 3. Dry Run Mode (Future)

```json
{
  "tool": "delete_directory",
  "path": "C:/Temp",
  "dry_run": true  // Don't actually execute
}
```

Simuleert de actie en geeft preview van wat er zou gebeuren.

---

### 4. Audit Logging

Elke tool execution wordt gelogd:

```python
log_tool_execution(
    device_id="laptop-123",
    tool="create_directory",
    parameters={"path": "C:/Test"},
    result={"success": True},
    timestamp=datetime.now()
)
```

---

## LLM Integration

### System Prompt (Tool Definitions)

```text
You are Orion Assistant. You have access to these tools:

1. create_directory
   Creates a directory on a device.
   Parameters:
   - device (string): Device ID (e.g., "laptop-123")
   - path (string): Full path (e.g., "C:/Projects/NewFolder")
   
   Example:
   {"tool": "create_directory", "device": "laptop-123", "path": "C:/Test"}

2. open_app
   Opens an application.
   Parameters:
   - device (string): Device ID
   - app (string): App name (chrome, code, explorer)
   - args (optional array): Arguments
   
   Example:
   {"tool": "open_app", "device": "laptop-123", "app": "chrome", "args": ["https://google.com"]}

...

When the user asks you to perform an action, respond with ONLY the tool call JSON, nothing else.
After receiving the tool result, provide a natural language response to the user.
```

---

### Tool Call Extraction

Backend extracts tool calls van LLM response:

```python
def extract_tool_call(llm_response: str) -> dict:
    # Try to parse as JSON
    try:
        tool_call = json.loads(llm_response)
        if "tool" in tool_call:
            return tool_call
    except:
        pass
    
    # Try to find JSON in text
    import re
    json_match = re.search(r'\{.*"tool".*\}', llm_response, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    
    return None
```

---

## Error Handling

### Tool Execution Errors

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Access to C:/Windows/System32 is not allowed",
    "details": {
      "attempted_path": "C:/Windows/System32/Test",
      "allowed_paths": ["C:/Users/njsch", "D:/Projects"]
    }
  }
}
```

**Error Codes:**

- `INVALID_PATH` - Path doesn't exist or is invalid
- `PERMISSION_DENIED` - Permission check failed
- `PATH_NOT_ALLOWED` - Path outside allowed directories
- `APP_NOT_WHITELISTED` - App not in whitelist
- `EXECUTION_FAILED` - Tool crashed
- `TIMEOUT` - Tool took too long
- `NOT_SUPPORTED` - Tool not available on this OS

---

## Testing Tools

### Unit Tests (Backend)

```python
def test_create_directory_validation():
    tool_call = {
        "tool": "create_directory",
        "device": "laptop-123",
        "path": "C:/Users/njsch/Test"
    }
    
    result = validate_tool_call(tool_call, "laptop-123")
    assert result == True

def test_invalid_path():
    tool_call = {
        "tool": "create_directory",
        "device": "laptop-123",
        "path": "C:/Windows/System32/Test"
    }
    
    with pytest.raises(PathNotAllowedError):
        validate_tool_call(tool_call, "laptop-123")
```

### Integration Tests (Client)

```gdscript
# tests/test_tools.gd
func test_create_directory():
    var result = FileOperations.create_directory("C:/Users/njsch/Test_" + str(Time.get_ticks_msec()))
    assert(result.success == true)
    assert(result.created_path != "")
```

---

## Future Enhancements

1. **Tool Composition** - Chain multiple tools
2. **Async Tools** - Long-running operations
3. **Tool Aliases** - User-defined shortcuts
4. **Tool Macros** - Recorded sequences
5. **Tool Analytics** - Usage statistics
6. **Smart Suggestions** - AI recommends tools based on context
