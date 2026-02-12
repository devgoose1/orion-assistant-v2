# Security Model

## Overview

Orion Assistant heeft toegang tot file systems, applicaties en potentieel kritieke services. Een robuust security model is **essentieel**.

---

## Security Principles

### 1. Zero Trust Architecture

**Principe:** Trust nothing by default.

- Elke tool call wordt gevalideerd
- Elke device heeft expliciete permissions
- Elke path wordt gecheckt
- Elke action wordt gelogd

---

### 2. Least Privilege

**Principe:** Minimale rechten voor maximale veiligheid.

- Devices krijgen alleen tools die ze nodig hebben
- Paths zijn whitelisted, niet blacklisted
- Apps moeten expliciet toegestaan worden
- No wildcard permissions

---

### 3. Defense in Depth

**Principe:** Meerdere lagen van bescherming.

```text
Layer 1: LLM validation (prompt engineering)
Layer 2: Backend validation (permissions)
Layer 3: Client-side validation (path checks)
Layer 4: OS-level permissions (user context)
Layer 5: Audit logging (forensics)
```

---

### 4. Fail Secure

**Principe:** Bij twijfel: blokkeren.

- Unknown tool? → Block
- Path not in whitelist? → Block
- Permission mismatch? → Block
- Error during validation? → Block

---

## Permission System

### Device Permission Model

```python
DEVICE_PERMISSIONS = {
    "laptop-123": {
        "name": "NJSCH Laptop",
        "allowed_tools": [
            "create_directory",
            "delete_directory",
            "search_files",
            "open_app",
            "get_device_info"
        ],
        "allowed_paths": [
            "C:/Users/njsch",
            "D:/Projects",
            "C:/Temp"
        ],
        "allowed_apps": [
            "chrome",
            "firefox",
            "code",
            "explorer",
            "terminal"
        ],
        "risk_limits": {
            "max_delete_size_mb": 100,
            "max_file_search_results": 1000,
            "require_confirmation": ["delete_directory", "restart_service"]
        },
        "restrictions": {
            "no_system_paths": true,
            "no_recursive_delete_root": true,
            "no_service_control": false
        }
    }
}
```

---

### Path Whitelisting

#### Allowed Paths

Devices hebben expliciete allowed paths:

```python
ALLOWED_PATHS = {
    "laptop-123": [
        "C:/Users/njsch",      # User directory
        "D:/Projects",         # Projects
        "C:/Temp"              # Temp files
    ]
}
```

#### Forbidden Paths (Global Blacklist)

Sommige paths zijn **altijd** verboden:

```python
FORBIDDEN_PATHS = [
    "C:/Windows",
    "C:/Program Files",
    "C:/Program Files (x86)",
    "/etc",           # Linux
    "/usr",           # Linux
    "/System",        # macOS
    "/Applications"   # macOS
]
```

#### Validation Logic

```python
def is_path_allowed(path: str, device_id: str) -> bool:
    # 1. Check global blacklist
    for forbidden in FORBIDDEN_PATHS:
        if path.lower().startswith(forbidden.lower()):
            return False
    
    # 2. Check device whitelist
    device_allowed = ALLOWED_PATHS.get(device_id, [])
    for allowed in device_allowed:
        if path.startswith(allowed):
            return True
    
    # 3. Default deny
    return False
```

---

### Tool Risk Levels

Elke tool heeft een risk level:

| Level | Description | Examples | Requires |
| ----- | ----------- | -------- | -------- |
| **Low** | Read-only, safe operations | `get_device_info`, `search_files` | Nothing |
| **Medium** | Write operations, reversible | `create_directory`, `open_app` | Permission |
| **High** | Destructive, irreversible | `delete_directory`, `close_app` | Permission + Confirmation |
| **Critical** | System-level, dangerous | `restart_service`, `execute_command` | Permission + Confirmation + Admin |

---

## Authentication & Authorization

### Current (v2.0 - Local Network)

**Authentication:** None (trust local network)  
**Authorization:** Device-based permissions

### Future (v3.0 - Remote Access)

#### JWT Token Authentication

```python
# Device registration with token
{
    "type": "device_register",
    "device_id": "laptop-123",
    "auth_token": "Bearer eyJhbGciOiJIUzI1NiIs..."
}
```

**Token Contents:**

```json
{
  "device_id": "laptop-123",
  "user_id": "user-456",
  "permissions": ["file_operations", "app_control"],
  "exp": 1707829200,
  "iat": 1707742800
}
```

#### API Key for Backend

```bash
# .env
BACKEND_API_KEY=supersecret123
```

Clients moeten API key meesturen in headers.

---

## Input Validation

### Parameter Validation

Alle tool parameters worden gevalideerd:

```python
def validate_path_parameter(path: str) -> bool:
    # 1. Not empty
    if not path or len(path) == 0:
        return False
    
    # 2. No path traversal
    if ".." in path or "~" in path:
        return False
    
    # 3. Valid characters only
    import re
    if not re.match(r'^[a-zA-Z0-9_/:\\\-\. ]+$', path):
        return False
    
    # 4. Maximum length
    if len(path) > 260:  # Windows MAX_PATH
        return False
    
    return True
```

### JSON Validation

Alle incoming messages worden gevalideerd tegen schema:

```python
from pydantic import BaseModel

class ToolExecuteMessage(BaseModel):
    type: str = "tool_execute"
    tool_call_id: str
    tool: str
    parameters: dict
    timeout_sec: int = 30
```

Pydantic zorgt voor automatic validation.

---

## Logging & Audit Trail

### What to Log

**Every tool execution:**

```python
{
    "timestamp": "2026-02-12T10:30:05Z",
    "device_id": "laptop-123",
    "tool": "create_directory",
    "parameters": {"path": "C:/Test"},
    "result": {"success": true},
    "duration_ms": 45,
    "user_session_id": "session-abc123"
}
```

**Security events:**

```python
{
    "timestamp": "2026-02-12T10:35:10Z",
    "event_type": "PERMISSION_DENIED",
    "device_id": "laptop-123",
    "tool": "delete_directory",
    "attempted_path": "C:/Windows/System32",
    "reason": "Path not allowed"
}
```

**Errors:**

```python
{
    "timestamp": "2026-02-12T10:40:00Z",
    "event_type": "ERROR",
    "device_id": "laptop-123",
    "error": "Tool execution failed",
    "details": "..."
}
```

---

### Log Storage

**Backend:**

- File: `logs/orion-assistant.log`
- Database: `tool_executions` table
- Retention: 90 days

**Client:**

- File: `client_logs/device-{id}.log`
- Retention: 30 days

---

### Log Analysis (Future)

- **Anomaly detection** - Unusual patterns
- **Alert on suspicious activity** - Multiple denied requests
- **Usage statistics** - Most used tools
- **Performance monitoring** - Slow operations

---

## Rate Limiting

### Per Device

```python
RATE_LIMITS = {
    "tool_executions_per_minute": 20,
    "llm_requests_per_minute": 10,
    "file_operations_per_minute": 30
}
```

### Backend Implementation

```python
from collections import defaultdict
import time

rate_limit_tracker = defaultdict(list)

def check_rate_limit(device_id: str, limit_type: str) -> bool:
    now = time.time()
    
    # Get recent requests
    recent = [ts for ts in rate_limit_tracker[device_id] if now - ts < 60]
    
    # Check limit
    if len(recent) >= RATE_LIMITS[limit_type]:
        return False
    
    # Add current request
    rate_limit_tracker[device_id].append(now)
    return True
```

---

## Sandboxing (Future)

### User Context Isolation

Clients draaien in user context (niet admin/root):

- **Windows:** Normale gebruiker (geen UAC elevation)
- **Linux:** Normale gebruiker (geen sudo)
- **macOS:** Standaard gebruiker

### Container Deployment

Voor extra isolatie:

```dockerfile
# Backend in container
FROM python:3.11-slim
RUN useradd -m -s /bin/bash orion
USER orion
COPY --chown=orion:orion . /app
WORKDIR /app
CMD ["python", "main.py"]
```

Clients blijven native (hebben OS access nodig).

---

## Secrets Management

### Environment Variables

**Never hardcode secrets!**

```python
# ✗ BAD
OLLAMA_API_KEY = "abc123..."

# ✓ GOOD
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
```

### .env Files

```bash
# .env (NEVER commit to git!)
OLLAMA_API_KEY=your_key_here
BACKEND_SECRET_KEY=supersecret
DATABASE_URL=postgresql://...
```

**.gitignore:**

```text
.env
*.log
__pycache__/
```

### Future: Vault Integration

Voor productie:

- **HashiCorp Vault**
- **AWS Secrets Manager**
- **Azure Key Vault**

---

## Network Security

### Current (Local Network)

- **WebSocket:** `ws://` (unencrypted)
- **Trust:** Local network is trusted

### Future (Remote Access)

#### WSS (WebSocket Secure)

```python
# Backend with SSL
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('cert.pem', 'key.pem')

uvicorn.run(app, host="0.0.0.0", port=8765, ssl=ssl_context)
```

Client:

```gdscript
var BACKEND_URL: String = "wss://orion.example.com:8765/ws"
```

#### Firewall Rules

- **Allow:** Port 8765 only from known IPs
- **Block:** All other traffic

---

## Incident Response

### Detection

**Automated alerts bij:**

- Multiple permission denials (>5 per minuut)
- Attempts to access forbidden paths
- Abnormal tool usage patterns
- Client disconnects during tool execution

### Response Procedure

1. **Alert Admin** - Email/SMS notification
2. **Block Device** - Temporarily disable device
3. **Review Logs** - Analyze what happened
4. **Revoke Permissions** - If necessary
5. **Investigate** - Root cause analysis

---

## Security Checklist

### Before Deployment

- [ ] All paths are whitelisted
- [ ] All tools have risk levels
- [ ] Logging is enabled
- [ ] Rate limits are configured
- [ ] .env file is not in git
- [ ] Secrets are externalized
- [ ] Input validation is implemented
- [ ] Error messages don't leak info
- [ ] Audit trail is tested

### Regular Maintenance

- [ ] Review logs weekly
- [ ] Update dependencies monthly
- [ ] Rotate API keys quarterly
- [ ] Review permissions quarterly
- [ ] Test incident response annually

---

## Known Limitations

### Current Version (v2.0)

1. **No encryption** - WebSocket traffic is unencrypted
2. **No authentication** - Any device can connect
3. **Local network only** - Not secure for internet exposure
4. **No user accounts** - Single user model
5. **Basic permissions** - Simple whitelist/blacklist

### Mitigation

**DO NOT expose backend to internet without:**

- SSL/TLS encryption
- Authentication
- Firewall rules
- Rate limiting
- Intrusion detection

---

## Security Best Practices

1. **Keep it updated** - Dependencies, OS, tools
2. **Minimal exposure** - Only open necessary ports
3. **Monitor logs** - Regularly check for anomalies
4. **Test permissions** - Verify whitelist/blacklist works
5. **Backup before destructive ops** - Safety net
6. **Document changes** - Track permission modifications
7. **Review regularly** - Security is ongoing

---

## Future Security Features

- **Two-factor authentication**
- **User role management** (admin, user, guest)
- **Encrypted WebSocket (WSS)**
- **Certificate pinning**
- **Intrusion detection system**
- **Automated security scanning**
- **Vulnerability alerts**
- **Zero-knowledge architecture** (data encryption)
