from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import os
import time
from typing import Optional
from dotenv import load_dotenv
from ollama import Client
from datetime import datetime

# Database imports
from database import init_db, SessionLocal
from services.device_service import (
    create_device, get_device, update_heartbeat, 
    check_device_permission, check_path_allowed
)
from services.tool_execution_service import log_tool_execution

# Tool system imports
from tools.router import get_router
from tools.registry import get_registry

# Load environment variables from .env file
load_dotenv()

# Pydantic models
class ToolTestRequest(BaseModel):
    device_id: str
    tool: str
    params: dict

app = FastAPI()

# Initialize database and tools on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    # Initialize tool registry
    registry = get_registry()
    print(f"✓ Tool registry initialized with {len(registry.list_all())} tools")
    print("✓ Application started")

@app.on_event("shutdown")
async def shutdown_event():
    print("✓ Application shutdown")

# CORS setup voor Godot client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama Cloud configuratie
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "https://ollama.com")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")

print(f"🔧 Backend configuratie:")
print(f"   API URL: {OLLAMA_API_URL}")
print(f"   API Key: {'✓ Ingesteld' if OLLAMA_API_KEY else '✗ NIET INGESTELD!'}")
print(f"   Model: {OLLAMA_MODEL}")

# Initialize Ollama client
ollama_client = Client(
    host=OLLAMA_API_URL,
    headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
)

# Connected clients (WebSocket connections)
clients = {}  # device_id -> websocket mapping

def call_llm(prompt: str, model: Optional[str] = None):
    """
    Stuurt een prompt naar Ollama Cloud API.
    Geeft volledige response terug.
    """
    model = model or OLLAMA_MODEL
    
    try:
        messages = [{'role': 'user', 'content': prompt}]
        response = ollama_client.chat(model=model, messages=messages, stream=False)
        return response['message']['content']
    except Exception as e:
        print(f"Fout bij LLM API call: {e}")
        return f"Fout: {str(e)}"

def call_llm_stream(prompt: str, model: Optional[str] = None):
    """
    Stuurt een prompt naar Ollama Cloud API met streaming.
    Yieldt response chunks één voor één.
    """
    model = model or OLLAMA_MODEL
    
    try:
        messages = [{'role': 'user', 'content': prompt}]
        for part in ollama_client.chat(model=model, messages=messages, stream=True):
            if 'message' in part and 'content' in part['message']:
                content = part['message']['content']
                if content:
                    yield content
    except Exception as e:
        print(f"Fout bij streaming LLM call: {e}")
        yield f"Fout: {str(e)}"

async def send_command_to_device(device_id: str, command: dict):
    """Stuurt een command naar een specifieke device."""
    if device_id in clients:
        try:
            await clients[device_id].send_text(json.dumps(command))
            return True
        except:
            return False
    return False

async def send_command_to_all(command: dict):
    """Stuurt een command naar alle verbonden clients."""
    for device_id, client in clients.items():
        try:
            await client.send_text(json.dumps(command))
        except:
            pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    device_id = None
    db = SessionLocal()
    
    try:
        print(f"📱 New WebSocket connection")
        
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            event_type = event.get("type")
            
            print(f"📨 Received: {event_type}")
            
            # Handle device registration
            if event_type == "device_register":
                device_id = event.get("device_id")
                
                # Check if device exists
                existing_device = get_device(db, device_id)
                
                if existing_device:
                    # Update existing device heartbeat
                    update_heartbeat(db, device_id)
                    device = existing_device
                    print(f"✓ Device updated: {device_id}")
                else:
                    # Create new device with default permissions
                    device_data = {
                        'device_id': device_id,
                        'hostname': event.get('hostname', 'unknown'),
                        'os_type': event.get('os_type', 'unknown'),
                        'os_version': event.get('os_version'),
                        'capabilities': event.get('capabilities', {}),
                        'cpu_info': event.get('metadata', {}).get('processor_name'),
                        'ram_gb': event.get('metadata', {}).get('ram_gb'),
                        'disk_gb': event.get('metadata', {}).get('disk_gb'),
                        # Default permissions
                        'allowed_tools': ['create_directory', 'delete_directory', 'search_files', 'open_app', 'get_device_info'],
                        'allowed_paths': ['C:/Users', 'D:/Projects'] if event.get('os_type') == 'Windows' else ['/home'],
                        'allowed_apps': ['chrome', 'firefox', 'code', 'explorer', 'terminal'],
                        'status': 'online',
                        'last_heartbeat': datetime.now()
                    }
                    device = create_device(db, device_data)
                    print(f"✓ New device registered: {device_id}")
                
                # Store WebSocket connection
                clients[device_id] = websocket
                
                # Send permissions back to device
                await websocket.send_text(json.dumps({
                    "type": "device_registered",
                    "device_id": device_id,
                    "permissions": {
                        "allowed_tools": device.allowed_tools,
                        "allowed_paths": device.allowed_paths,
                        "allowed_apps": device.allowed_apps
                    }
                }))
            
            # Handle heartbeat
            elif event_type == "device_heartbeat":
                if device_id:
                    update_heartbeat(db, device_id)
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            # Handle LLM requests (existing functionality)
            elif event_type == "llm_request":
                prompt = event.get("prompt", "")
                model = event.get("model", OLLAMA_MODEL)
                stream = event.get("stream", False)
                
                print(f"📝 LLM Request:")
                print(f"   Device: {device_id}")
                print(f"   Prompt: {prompt}")
                print(f"   Model: {model}")
                print(f"   Stream: {stream}")
                
                if stream:
                    # Streaming modus
                    print("   🔄 Starten streaming...")
                    chunk_count = 0
                    for chunk in call_llm_stream(prompt, model):
                        chunk_count += 1
                        await websocket.send_text(json.dumps({
                            "type": "llm_response_chunk",
                            "chunk": chunk,
                            "complete": False
                        }))
                    
                    print(f"   ✓ Streaming compleet ({chunk_count} chunks)")
                    # Signaal dat streaming klaar is
                    await websocket.send_text(json.dumps({
                        "type": "llm_response_chunk",
                        "chunk": "",
                        "complete": True
                    }))
                else:
                    # Niet-streaming modus
                    print("   🔄 Ophalen response...")
                    response = await asyncio.to_thread(call_llm, prompt, model)
                    print(f"   ✓ Response ontvangen: {response[:100]}...")
                    await websocket.send_text(json.dumps({
                        "type": "llm_response",
                        "response": response
                    }))
            
            # Handle tool execution requests
            elif event_type == "tool_execute":
                tool_name = event.get("tool_name")
                parameters = event.get("parameters", {})
                
                print(f"🔧 Tool Execution Request:")
                print(f"   Device: {device_id}")
                print(f"   Tool: {tool_name}")
                print(f"   Parameters: {parameters}")
                
                # Execute tool via router
                if not device_id:
                    await websocket.send_text(json.dumps({
                        "type": "tool_execute_response",
                        "success": False,
                        "error": "Device not registered"
                    }))
                    continue
                    
                router = get_router()
                result = await router.execute_tool(
                    db=db,
                    device_id=device_id,
                    tool_name=tool_name,
                    parameters=parameters,
                    websocket_send_func=send_command_to_device
                )
                
                # Send result back to requesting device
                await websocket.send_text(json.dumps({
                    "type": "tool_execute_response",
                    "success": result["success"],
                    "execution_id": result.get("execution_id"),
                    "message": result.get("message"),
                    "error": result.get("error")
                }))
            
            # Handle tool execution results from devices
            elif event_type == "tool_result":
                # Support both execution_id (from router) and request_id (from test endpoint)
                execution_id = event.get("execution_id") or event.get("request_id")
                success = event.get("success", False)
                result = event.get("result")
                error = event.get("error")
                
                print(f"✓ Tool Result Received:")
                print(f"   Execution ID: {execution_id}")
                print(f"   Success: {success}")
                if result:
                    print(f"   Result: {result}")
                if error:
                    print(f"   Error: {error}")
                
                # Update execution log if execution_id exists
                if execution_id:
                    router = get_router()
                    router.handle_tool_result(
                        db=db,
                        execution_id=execution_id,
                        success=success,
                        result=result,
                        error=error
                    )
            
            # Handle request for available tools
            elif event_type == "get_tools":
                router = get_router()
                tools_info = router.get_available_tools(device_id)
                
                await websocket.send_text(json.dumps({
                    "type": "tools_list",
                    "tools": tools_info["tools"],
                    "count": tools_info["count"],
                    "categories": tools_info["categories"]
                }))
                
    except WebSocketDisconnect:
        if device_id and device_id in clients:
            del clients[device_id]
        print(f"📱 Client verbroken: {device_id}")
    except Exception as e:
        print(f"❌ WebSocket fout: {e}")
        import traceback
        traceback.print_exc()
        if device_id and device_id in clients:
            del clients[device_id]
    finally:
        db.close()

@app.post("/test/tool")
async def test_tool_endpoint(request: ToolTestRequest):
    """Test endpoint to trigger tool execution on a device"""
    
    # Find device WebSocket
    if request.device_id not in clients:
        return {
            "success": False,
            "error": f"Device {request.device_id} not connected"
        }
    
    target_ws = clients[request.device_id]
    
    # Generate request
    request_id = f"test_{int(time.time())}"
    message = {
        "type": "tool_execute",
        "request_id": request_id,
        "tool_name": request.tool,
        "parameters": request.params
    }
    
    print(f"📤 Test tool execution: {message}")
    await target_ws.send_json(message)
    
    return {
        "success": True,
        "request_id": request_id,
        "device_id": request.device_id,
        "tool": request.tool,
        "message": "Tool execution triggered"
    }

@app.get("/test/devices")
async def list_connected_devices():
    """List all currently connected devices"""
    devices = []
    for device_id in clients.keys():
        devices.append({
            "device_id": device_id,
            "connected": True
        })
    
    return {
        "success": True,
        "devices": devices,
        "count": len(devices)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
