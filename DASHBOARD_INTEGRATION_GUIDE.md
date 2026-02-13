# Godot Dashboard Integration Guide

## Overview

Phase 3.1 adds a Jarvis-style monitoring dashboard to the Orion Assistant client. This guide explains how to integrate the dashboard components into your Godot 4.6 project.

## Architecture

### Backend

- **Models**: `DeviceMetrics` - stores CPU/memory/disk usage metrics
- **Services**: `dashboard_service.py` - dashboard data API
- **HTTP API**:
  - `GET /api/dashboard/overview` - all devices summary
  - `GET /api/dashboard/device/{device_id}` - device details
  - `GET /api/dashboard/metrics/{device_id}` - metric history

### Client (Godot)

- **websocket.gd** - enhanced with metrics collection
  - Collects CPU, memory, disk metrics via `_get_system_metrics()`
  - Includes metrics in heartbeat messages
  - Emits `metrics_collected` signal for real-time updates

- **dashboard.gd** - main dashboard controller
  - Fetches device overview via HTTP API
  - Manages device list and selection
  - Updates metrics display in real-time

- **device_list_panel.gd** - device list UI
  - Displays all connected devices
  - Shows status, OS info, latest metrics
  - Handles device selection

- **metrics_panel.gd** - system metrics visualization
  - Progress bars for CPU, memory, disk
  - Real-time updates from WebSocket

- **activity_log_panel.gd** - execution log
  - Logs tool executions
  - Logs LLM interactions
  - System event messages

## Integration Steps

### 1. Create Main Dashboard Scene

```gdscript
# In Godot Editor: Create new Scene
# Root node: Control named "Dashboard"
# Attach script: res://dashboard.gd
```

### 2. Add Dashboard to Project

In `project.godot`:

```text
[autoload]
Dashboard="res://dashboard.tscn"
```

Or manually instantiate in your main scene:

```gdscript
# In your main scene script
@onready var dashboard = preload("res://dashboard.tscn").instantiate()

func _ready() -> void:
    add_child(dashboard)
```

### 3. Create Dashboard Scene Layout

In Godot Editor, with Dashboard scene open:

```text
Dashboard (Control)
├── VBoxContainer
│   ├── HBoxContainer (Top bar)
│   │   ├── Label "Orion Dashboard"
│   │   └── Label "Status: Connected"
│   ├── HBoxContainer (Main content)
│   │   ├── DeviceListPanel (TabContainer)
│   │   └── VBoxContainer (Right panel)
│   │       ├── MetricsPanel (PanelContainer)
│   │       └── ActivityLogPanel (PanelContainer)
```

### 4. Add UI Components Programmatically

```gdscript
# In dashboard.gd _setup_ui()
func _setup_ui() -> void:
    # Create main container
    var main_vbox = VBoxContainer.new()
    add_child(main_vbox)
    
    # Add metrics panel
    var metrics = MetricsPanel.new()
    main_vbox.add_child(metrics)
    
    # Add device list
    var device_list = DeviceListPanel.new()
    device_list.device_selected.connect(_on_device_selected)
    main_vbox.add_child(device_list)
    
    # Add activity log
    var activity = ActivityLogPanel.new()
    main_vbox.add_child(activity)
    self.activity_log = activity
```

### 5. Connect WebSocket Signals

```gdscript
# In dashboard.gd _ready()
func _ready() -> void:
    websocket = get_node("/root/WebSocketManager")
    
    if websocket:
        # Listen for metrics updates
        websocket.metrics_collected.connect(_on_metrics_collected)
        
        # Listen for tool executions
        websocket.tool_executed.connect(_on_tool_executed)
        
        # Listen for LLM responses
        websocket.llm_response_received.connect(_on_llm_response)
```

### 6. Update Heartbeat with Metrics

The updated `websocket.gd` now automatically includes metrics in heartbeats:

```gdscript
# Heartbeat message format (sent from client every 30 seconds)
{
    "type": "device_heartbeat",
    "device_id": "unique-id",
    "timestamp": 1234567890.5,
    "status": "online",
    "metrics": {
        "cpu_percent": 35.2,
        "memory_percent": 42.8,
        "disk_percent": 60.1,
        "timestamp": 1234567890.5
    }
}
```

### 7. Display Real-Time Metrics

In your dashboard scene:

```gdscript
func _on_metrics_collected(metrics: Dictionary) -> void:
    """Update all metric displays with latest data."""
    
    # Update main metrics panel
    metrics_panel.update_metrics(metrics)
    
    # Log to activity
    activity_log.add_system_message(
        "CPU: %.1f%% | MEM: %.1f%% | DISK: %.1f%%" % [
            metrics.get("cpu_percent", 0),
            metrics.get("memory_percent", 0),
            metrics.get("disk_percent", 0)
        ]
    )
```

### 8. Load Dashboard Data

```gdscript
# In dashboard.gd, after scene is ready
func _ready() -> void:
    super._ready()
    fetch_dashboard_overview()  # Load initial device list

    # Refresh every 5 seconds
    var refresh_timer = Timer.new()
    refresh_timer.wait_time = 5.0
    refresh_timer.timeout.connect(fetch_dashboard_overview)
    add_child(refresh_timer)
    refresh_timer.start()
```

## Metrics Collection

The client now collects three system metrics:

### CPU Usage

- **Currently**: Placeholder (random 10-40%)
- **To implement**: Use `OS.execute()` to run system commands
  - Windows: `wmic CPU get LoadPercentage`
  - Linux: Parse `/proc/stat`

### Memory Usage

- **Currently**: Uses Godot's `OS.get_static_memory_usage()`
- **Limitation**: Only tracks Godot process, not system

### Disk Usage

- **Currently**: Placeholder (random 30-70%)
- **To implement**: Use `OS.execute()` to run system commands
  - Windows: `wmic logicaldisk get size,freespace`
  - Linux: `df -h /`

## Improving Metrics Implementation

For production, enhance metrics collection:

```gdscript
# Windows CPU usage
func _get_windows_cpu_usage() -> float:
    var output = []
    OS.execute("cmd", ["/C", "wmic cpu get loadpercentage"], output)
    if output.size() > 0:
        var value = output[0].strip_edges().to_float()
        return value
    return 0.0

# Linux CPU usage
func _get_linux_cpu_usage() -> float:
    var output = []
    OS.execute("cat", ["/proc/loadavg"], output)
    if output.size() > 0:
        var parts = output[0].split(" ")
        if parts.size() > 0:
            return parts[0].to_float() * 25  # Approximate percentage
    return 0.0
```

## API Endpoints

### Dashboard Overview

**GET** `/api/dashboard/overview`

Response:

```json
{
    "success": true,
    "data": {
        "total_devices": 3,
        "online_devices": 2,
        "offline_devices": 1,
        "recent_executions": 15,
        "timestamp": "2024-01-15T10:30:45",
        "devices": [
            {
                "device_id": "device-1",
                "hostname": "laptop",
                "os_type": "Windows",
                "status": "online",
                "metrics": {
                    "cpu_percent": 35.2,
                    "memory_percent": 42.8,
                    "disk_percent": 60.1
                }
            }
        ]
    }
}
```

### Device Details

**GET** `/api/dashboard/device/{device_id}`

Returns device info, current metrics, execution history, and active sessions.

### Metrics History

**GET** `/api/dashboard/metrics/{device_id}?limit=50`

Returns 50 most recent metric snapshots for charting.

## Testing the Dashboard

1. **Start backend**:

   ```bash
   cd backend
   python main.py
   ```

2. **Run Godot client** with dashboard scene

3. **Monitor in browser**:
   - `http://localhost:8765/api/dashboard/overview`
   - Should show connected devices with metrics

4. **Check WebSocket messages**:
   - Heartbeats include metrics every 30 seconds
   - Backend records metrics in database
   - Dashboard updates automatically

## Next Steps

- [ ] Custom theme for Jarvis-style UI (blue/cyan colors, futuristic fonts)
- [ ] Add charts using CharacterBody2D or custom draw
- [ ] Drill-down to view metric history
- [ ] Real-time CPU/memory/disk collection (not placeholders)
- [ ] Alert system for high resource usage
- [ ] Export metrics to CSV/JSON
