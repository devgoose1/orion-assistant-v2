# Database Schema & Context Management

## Overview

Database voor:

- Device registry
- Session/context management
- Tool execution history
- Event logging
- Memory/knowledge base

---

## Database Choice

### Phase 1: SQLite

- **Pro:** Simple, geen server nodig, embedded
- **Con:** Geen concurrent writes, niet geschikt voor productie

### Phase 2+: PostgreSQL

- **Pro:** Robuust, concurrent, production-ready
- **Con:** Requires server

---

## Schema Design

### Table: devices

Registreert alle verbonden devices.

```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    os_type VARCHAR(50) NOT NULL,
    os_version VARCHAR(50),
    
    -- Capabilities
    capabilities JSONB DEFAULT '{}',
    
    -- Permissions
    allowed_tools TEXT[] DEFAULT '{}',
    allowed_paths TEXT[] DEFAULT '{}',
    allowed_apps TEXT[] DEFAULT '{}',
    
    -- Metadata
    cpu_info TEXT,
    ram_gb INTEGER,
    disk_gb INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'online',
    last_heartbeat TIMESTAMP,
    
    -- Timestamps
    registered_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_devices_device_id ON devices(device_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_heartbeat ON devices(last_heartbeat);
```

**Example Row:**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "device_id": "laptop-123",
    "hostname": "NJSCH-LAPTOP",
    "os_type": "Windows",
    "os_version": "11",
    "capabilities": {
        "file_operations": true,
        "app_control": true,
        "voice": false
    },
    "allowed_tools": ["create_directory", "open_app"],
    "allowed_paths": ["C:/Users/njsch", "D:/Projects"],
    "allowed_apps": ["chrome", "code"],
    "status": "online",
    "last_heartbeat": "2026-02-12T10:45:00Z",
    "registered_at": "2026-02-10T08:00:00Z"
}
```

---

### Table: sessions

Conversatie sessies met context.

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) REFERENCES devices(device_id),
    
    -- Session info
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    -- Context
    context JSONB DEFAULT '{}',
    
    -- Stats
    message_count INTEGER DEFAULT 0,
    tool_execution_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_device_id ON sessions(device_id);
CREATE INDEX idx_sessions_active ON sessions(is_active);
CREATE INDEX idx_sessions_started ON sessions(started_at);
```

**Context Example:**

```json
{
    "user_name": "Nick",
    "current_project": "orion-assistant-v2",
    "recent_files": [
        "C:/Projects/orion/main.py",
        "C:/Projects/orion/README.md"
    ],
    "preferences": {
        "model": "gpt-oss:120b",
        "streaming": true
    }
}
```

---

### Table: tool_executions

Audit log van alle tool executions.

```sql
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    device_id VARCHAR(255) REFERENCES devices(device_id),
    
    -- Tool info
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    
    -- Result
    success BOOLEAN NOT NULL,
    result JSONB,
    error_message TEXT,
    
    -- Timing
    executed_at TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER,
    
    -- Context
    user_query TEXT,
    llm_reasoning TEXT,
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

CREATE INDEX idx_tool_executions_device ON tool_executions(device_id);
CREATE INDEX idx_tool_executions_tool ON tool_executions(tool_name);
CREATE INDEX idx_tool_executions_time ON tool_executions(executed_at);
CREATE INDEX idx_tool_executions_success ON tool_executions(success);
```

**Example Row:**

```json
{
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "session_id": "770e8400-e29b-41d4-a716-446655440002",
    "device_id": "laptop-123",
    "tool_name": "create_directory",
    "parameters": {
        "path": "C:/Users/njsch/Test"
    },
    "success": true,
    "result": {
        "created_path": "C:/Users/njsch/Test",
        "message": "Directory created"
    },
    "executed_at": "2026-02-12T10:30:05Z",
    "duration_ms": 45,
    "user_query": "Maak een folder Test"
}
```

---

### Table: events

Device events (low disk, high CPU, etc.)

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) REFERENCES devices(device_id),
    
    -- Event details
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    data JSONB,
    
    -- Status
    acknowledged BOOLEAN DEFAULT false,
    resolved BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

CREATE INDEX idx_events_device ON events(device_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_severity ON events(severity);
CREATE INDEX idx_events_created ON events(created_at);
CREATE INDEX idx_events_unresolved ON events(resolved) WHERE resolved = false;
```

**Event Types:**

- `low_disk_space`
- `high_cpu_usage`
- `high_memory_usage`
- `new_file_detected`
- `service_down`
- `error_occurred`

---

### Table: context_memory

Long-term knowledge base.

```sql
CREATE TABLE context_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Memory key-value
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    
    -- Scope
    device_id VARCHAR(255) REFERENCES devices(device_id),
    scope VARCHAR(50) DEFAULT 'global',
    
    -- Metadata
    category VARCHAR(100),
    tags TEXT[],
    
    -- Expiration
    expires_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

CREATE INDEX idx_context_key ON context_memory(key);
CREATE INDEX idx_context_device ON context_memory(device_id);
CREATE INDEX idx_context_scope ON context_memory(scope);
CREATE INDEX idx_context_category ON context_memory(category);
```

**Examples:**

**File Location:**

```json
{
    "key": "file_location:project_alpha.zip",
    "value": {
        "device_id": "laptop-123",
        "path": "C:/Users/njsch/Downloads/project_alpha.zip",
        "size_bytes": 1048576,
        "last_modified": "2026-02-10T15:30:00Z"
    },
    "scope": "global",
    "category": "file_index"
}
```

**User Preference:**

```json
{
    "key": "user_preference:default_model",
    "value": {
        "model": "gpt-oss:120b",
        "reason": "User selected"
    },
    "scope": "global",
    "category": "preferences"
}
```

**Service Status:**

```json
{
    "key": "service_status:grafana",
    "value": {
        "status": "online",
        "url": "http://192.168.1.100:3000",
        "last_check": "2026-02-12T10:40:00Z"
    },
    "device_id": "homelab-server",
    "scope": "device",
    "category": "homelab"
}
```

---

## Database Access Layer

### Python ORM (SQLAlchemy)

```python
from sqlalchemy import create_engine, Column, String, Integer, Boolean, TIMESTAMP, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, unique=True, nullable=False)
    hostname = Column(String, nullable=False)
    os_type = Column(String, nullable=False)
    os_version = Column(String)
    capabilities = Column(JSON, default={})
    allowed_tools = Column(ARRAY(String), default=[])
    allowed_paths = Column(ARRAY(String), default=[])
    allowed_apps = Column(ARRAY(String), default=[])
    status = Column(String, default='online')
    last_heartbeat = Column(TIMESTAMP)
    registered_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///orion.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)
```

### CRUD Operations

```python
# Register device
def register_device(device_data: dict):
    db = SessionLocal()
    device = Device(**device_data)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

# Get device
def get_device(device_id: str):
    db = SessionLocal()
    return db.query(Device).filter(Device.device_id == device_id).first()

# Update heartbeat
def update_heartbeat(device_id: str):
    db = SessionLocal()
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        device.last_heartbeat = datetime.now()
        device.status = 'online'
        db.commit()
```

---

## Queries & Analytics

### Most Used Tools

```sql
SELECT 
    tool_name,
    COUNT(*) as execution_count,
    AVG(duration_ms) as avg_duration_ms,
    SUM(CASE WHEN success = true THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate
FROM tool_executions
WHERE executed_at > NOW() - INTERVAL '30 days'
GROUP BY tool_name
ORDER BY execution_count DESC;
```

### Device Activity

```sql
SELECT 
    d.device_id,
    d.hostname,
    COUNT(te.id) as tool_executions,
    MAX(te.executed_at) as last_activity
FROM devices d
LEFT JOIN tool_executions te ON d.device_id = te.device_id
WHERE te.executed_at > NOW() - INTERVAL '7 days'
GROUP BY d.device_id, d.hostname
ORDER BY tool_executions DESC;
```

### Failed Operations

```sql
SELECT 
    device_id,
    tool_name,
    error_message,
    COUNT(*) as failure_count
FROM tool_executions
WHERE success = false
GROUP BY device_id, tool_name, error_message
HAVING COUNT(*) > 3
ORDER BY failure_count DESC;
```

---

## Context Management

### Session Context

Elke sessie heeft context die wordt bijgehouden:

```python
class SessionContext:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context = {}
    
    def set(self, key: str, value: any):
        self.context[key] = value
        # Persist to database
        update_session_context(self.session_id, self.context)
    
    def get(self, key: str, default=None):
        return self.context.get(key, default)
    
    def update(self, data: dict):
        self.context.update(data)
        update_session_context(self.session_id, self.context)
```

### Global Memory

Long-term memory over alle sessies:

```python
def remember(key: str, value: any, scope='global', device_id=None):
    """Store in long-term memory"""
    db = SessionLocal()
    memory = ContextMemory(
        key=key,
        value=value,
        scope=scope,
        device_id=device_id
    )
    db.add(memory)
    db.commit()

def recall(key: str, device_id=None):
    """Retrieve from long-term memory"""
    db = SessionLocal()
    query = db.query(ContextMemory).filter(ContextMemory.key == key)
    if device_id:
        query = query.filter(ContextMemory.device_id == device_id)
    return query.first()
```

---

## Maintenance

### Cleanup Old Data

```sql
-- Delete old tool executions (>90 days)
DELETE FROM tool_executions 
WHERE executed_at < NOW() - INTERVAL '90 days';

-- Delete resolved events (>30 days)
DELETE FROM events 
WHERE resolved = true 
  AND resolved_at < NOW() - INTERVAL '30 days';

-- Delete expired context memory
DELETE FROM context_memory 
WHERE expires_at IS NOT NULL 
  AND expires_at < NOW();
```

### Vacuum & Optimize

```sql
-- PostgreSQL
VACUUM ANALYZE;
REINDEX DATABASE orion_db;

-- SQLite
VACUUM;
ANALYZE;
```

---

## Backup Strategy

### Daily Backups

```bash
#!/bin/bash
# backup.sh

DB_NAME="orion_db"
BACKUP_DIR="/backups/orion"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL
pg_dump $DB_NAME > "$BACKUP_DIR/orion_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/orion_$DATE.sql"

# Keep only last 30 days
find $BACKUP_DIR -name "orion_*.sql.gz" -mtime +30 -delete
```

### Restore

```bash
gunzip orion_20260212_100000.sql.gz
psql orion_db < orion_20260212_100000.sql
```

---

## Migration Strategy

### SQLite → PostgreSQL

```python
# Export from SQLite
import sqlite3
import json

conn = sqlite3.connect('orion.db')
cursor = conn.cursor()

# Export devices
cursor.execute("SELECT * FROM devices")
devices = cursor.fetchall()

with open('devices_export.json', 'w') as f:
    json.dump(devices, f)

# Import to PostgreSQL
import psycopg2

pg_conn = psycopg2.connect("postgresql://...")
pg_cursor = pg_conn.cursor()

for device in devices:
    pg_cursor.execute(
        "INSERT INTO devices VALUES (%s, %s, ...)",
        device
    )

pg_conn.commit()
```

---

## Future Enhancements

1. **Full-text search** - Voor logs en context
2. **Time-series data** - Voor metrics
3. **Graph relationships** - Device dependencies
4. **Caching layer** - Redis voor hot data
5. **Replication** - Multi-region support
6. **Sharding** - Scale horizontally
