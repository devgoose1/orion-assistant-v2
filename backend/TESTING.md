# Tool Testing Guide

## 🧪 Test Endpoints

De backend heeft nu 2 test endpoints:

### 1. List Connected Devices

```bash
curl http://localhost:8765/test/devices
```

Response:

```json
{
  "success": true,
  "devices": [
    {"device_id": "WIN_DESKTOP-ABC_12345", "connected": true}
  ],
  "count": 1
}
```

### 2. Execute Tool

```bash
curl -X POST "http://localhost:8765/test/tool" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "WIN_DESKTOP-ABC_12345",
    "tool": "create_directory",
    "params": {"path": "C:/Users/njsch/Desktop/TestFolder"}
  }'
```

Response:

```json
{
  "success": true,
  "request_id": "test_1739404800",
  "device_id": "WIN_DESKTOP-ABC_12345",
  "tool": "create_directory",
  "message": "Tool execution triggered"
}
```

## 🐍 Python Test Script

Gebruik het interactieve test script:

```bash
cd backend
python test_tools.py
```

Menu opties:

- `1` - Toon alle verbonden devices
- `2` - Test create_directory (maakt C:/Users/njsch/Desktop/OrionTestFolder)
- `3` - Test get_device_info (haalt systeem info op)
- `4` - Test search_files (zoekt .txt files op Desktop)
- `5` - Test open_app (opent Notepad)

## 📋 Stappen voor Testing

1. **Start Backend**

   ```bash
   cd backend
   python main.py
   ```

2. **Start Godot Client**
   - Open `client/project.godot` in Godot
   - Druk op Play (F5)
   - Device registreert automatisch

3. **Run Tests**

   ```bash
   # In een nieuwe terminal:
   cd backend
   python test_tools.py
   ```

4. **Check Results**
   - Backend terminal: zie tool_execute en tool_result messages
   - Godot console: zie tool execution logs
   - UI: zie tool results in chat

## 🔧 Available Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `create_directory` | `path: str` | Maakt een directory |
| `delete_directory` | `path: str, recursive: bool` | Verwijdert directory |
| `search_files` | `path: str, pattern: str, recursive: bool` | Zoekt bestanden |
| `list_directory` | `path: str, recursive: bool` | Lijst directory contents |
| `read_text_file` | `path: str` | Leest tekstbestand |
| `write_text_file` | `path: str, content: str, append: bool` | Schrijft tekstbestand |
| `copy_file` | `source_path: str, destination_path: str, overwrite: bool` | Kopieert bestand |
| `move_file` | `source_path: str, destination_path: str, overwrite: bool` | Verplaatst bestand |
| `delete_file` | `path: str, confirm: str` | Verwijdert bestand (confirm=DELETE) |
| `open_app` | `app_name: str, arguments: list` | Opent applicatie |
| `close_app` | `app_name: str, force: bool` | Sluit applicatie |
| `get_device_info` | `info_type: str` | Haalt device info op |
| `get_running_processes` | `filter: str` | Lijst draaiende processes |

## 🐛 Troubleshooting

**Device niet verbonden?**

- Check of Godot client draait
- Check WebSocket connectie in Godot console
- Check `GET /test/devices` om te zien of device geregistreerd is

**Tool execution werkt niet?**

- Check backend logs voor errors
- Check Godot console voor execution logs
- Verify device permissions in database

**Geen results terug?**

- Check of client tool_result teruggestuurd wordt
- Check backend tool_result handler
- Check database ToolExecution table voor logs
