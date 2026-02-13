from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import os
import time
from typing import Optional, Dict, Any, Tuple
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from ollama import Client
from datetime import datetime

# Local imports
from database import init_db, SessionLocal
from services.device_service import (
    create_device, get_device, update_heartbeat, 
    check_device_permission, check_path_allowed
)
from tools.router import get_router
from tools.registry import get_registry
from tools.llm_integration import (
    generate_system_prompt,
    extract_text_and_tool_call,
    format_tool_result_for_llm
)
from config import (
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_ALLOWED_TOOLS,
    DEFAULT_ALLOWED_PATHS,
    DEFAULT_ALLOWED_APPS,
    CONVERSATION_HISTORY_LIMIT,
    MAX_TOOL_ITERATIONS,
    TOOL_EXECUTION_TIMEOUT,
    TOOL_HEURISTIC_PHRASES,
)

# Load environment variables from .env file
load_dotenv()

# Type models
class ToolTestRequest(BaseModel):
    """HTTP request to execute a tool on a device."""
    device_id: str
    tool: str
    params: dict

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Initialize tool registry
    registry = get_registry()
    print(f"✓ Tool registry initialized with {len(registry.list_all())} tools")
    print("✓ Application started")
    yield
    print("✓ Application shutdown")

app = FastAPI(lifespan=lifespan)

# Track background tasks per device to avoid blocking the receive loop
llm_tasks = {}  # device_id -> asyncio.Task

async def _process_tool_call(
    websocket: WebSocket,
    tool_call: Dict[str, Any],
    device_id: Optional[str],
    session_id: str,
    db: Any
) -> Tuple[bool, Optional[str]]:
    """
    Process a single tool call and return whether to continue the loop and next prompt.
    
    Returns: (should_continue, next_prompt_or_none)
    - should_continue: True to continue the loop, False to break
    - next_prompt_or_none: Text to use as next prompt if continuing, None if breaking
    """
    print(f"   🔧 Tool call detected: {tool_call['tool_name']}")
    
    # Check device_id is available
    if not device_id:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": "Device not registered"
        }))
        return (False, None)
    
    # Execute tool
    router = get_router()
    result = await router.execute_tool(
        db=db,
        device_id=device_id,
        tool_name=tool_call['tool_name'],
        parameters=tool_call['parameters'],
        websocket_send_func=send_command_to_device
    )
    print(f"   🧾 Router result: {result}")
    if not result.get("success"):
        error_message = result.get("message") or result.get("error") or "Tool execution failed"
        tool_result_text = format_tool_result_for_llm(
            tool_call['tool_name'],
            False,
            None,
            error_message
        )
        add_message_to_conversation(session_id, "user", f"[TOOL RESULT]\n{tool_result_text}")
        return (True, "Please provide a natural language response based on the tool result above.")
    
    # Get the execution/request ID
    request_id = result.get('execution_id')
    if not request_id:
        print(f"   ⚠️  No execution ID returned from router")
        tool_result_text = format_tool_result_for_llm(
            tool_call['tool_name'],
            False,
            None,
            "No execution ID returned from router"
        )
        add_message_to_conversation(session_id, "user", f"[TOOL RESULT]\n{tool_result_text}")
        return (True, "Please provide a natural language response based on the tool result above.")
    
    # Create event to wait for tool result
    tool_event = asyncio.Event()
    tool_executions[request_id] = {
        "event": tool_event,
        "result": None
    }
    
    # Wait for tool result with timeout
    print(f"   ⏳ Waiting for tool result (request_id: {request_id})...")
    try:
        await asyncio.wait_for(tool_event.wait(), timeout=TOOL_EXECUTION_TIMEOUT)
        actual_result = tool_executions[request_id]["result"]
        print(f"   ✓ Tool result received!")
    except asyncio.TimeoutError:
        print(f"   ⚠️  Timeout waiting for tool result")
        actual_result = {
            "success": False,
            "error": "Tool execution timeout"
        }
    finally:
        # Clean up
        if request_id in tool_executions:
            del tool_executions[request_id]
    
    # Format tool result for LLM
    tool_result_text = format_tool_result_for_llm(
        tool_call['tool_name'],
        actual_result['success'],
        actual_result.get('result'),
        actual_result.get('error')
    )
    
    # Add tool result to conversation and continue
    add_message_to_conversation(session_id, "user", f"[TOOL RESULT]\n{tool_result_text}")
    return (True, "Please provide a natural language response based on the tool result above.")

async def _get_llm_response(
    prompt: str,
    model: str,
    session_id: str,
    stream: bool,
    websocket: Optional[WebSocket] = None
) -> str:
    """
    Get LLM response with optional streaming to websocket.
    
    Returns the complete response text.
    If streaming, sends chunks to websocket in real-time.
    """
    if stream and websocket:
        response_buffer = ""
        chunk_count = 0
        for chunk in call_llm_stream(prompt, model, session_id):
            chunk_count += 1
            response_buffer += chunk
            await websocket.send_text(json.dumps({
                "type": "llm_response_chunk",
                "chunk": chunk,
                "complete": False
            }))
        print(f"   ✓ Streaming complete ({chunk_count} chunks)")
        return response_buffer
    else:
        # Non-streaming mode
        return await asyncio.to_thread(call_llm, prompt, model, session_id)

async def handle_llm_request(websocket: WebSocket, event: dict, device_id: Optional[str]):
    """Process an LLM request without blocking the websocket receive loop."""
    db = SessionLocal()
    try:
        prompt = event.get("prompt", "")
        model = event.get("model", OLLAMA_MODEL)
        stream = event.get("stream", False)
        session_id = event.get("session_id", device_id)  # Use device_id as default session
        
        print(f"📝 LLM Request:")
        print(f"   Device: {device_id}")
        print(f"   Session: {session_id}")
        print(f"   Prompt: {prompt}")
        print(f"   Model: {model}")
        print(f"   Stream: {stream}")
        
        # Tool-aware execution loop
        iteration = 0
        current_prompt = prompt
        
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            
            print(f"   🔄 Iteration {iteration}: {'Streaming' if stream else 'Getting response'}...")
            response = await _get_llm_response(current_prompt, model, session_id, stream, websocket)
            print(f"   ✓ Response received: {response[:100]}...")
            
            # Check for tool calls
            text, tool_call = extract_text_and_tool_call(response)
            
            if tool_call:
                # Use extracted helper function for tool processing
                should_continue, next_prompt = await _process_tool_call(
                    websocket, tool_call, device_id, session_id, db
                )
                if should_continue:
                    current_prompt = next_prompt
                    continue
                else:
                    break
            else:
                # No tool call - send response and finish
                if stream:
                    await websocket.send_text(json.dumps({
                        "type": "llm_response_chunk",
                        "chunk": "",
                        "complete": True
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "llm_response",
                        "response": response
                    }))
                break
        
        if iteration >= MAX_TOOL_ITERATIONS:
            print(f"   ⚠️  Max tool iterations reached ({MAX_TOOL_ITERATIONS})")
            await websocket.send_text(json.dumps({
                "type": "llm_response",
                "response": "I apologize, but I've reached the maximum number of tool execution attempts. Please try rephrasing your request."
            }))
    finally:
        db.close()

# CORS setup voor Godot client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", DEFAULT_OLLAMA_URL)
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)

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

# Conversation contexts (session_id -> messages list)
conversations = {}  # session_id -> [{"role": "system|user|assistant", "content": "..."}]

# Tool execution tracking (request_id -> asyncio.Event and result)
tool_executions = {}  # request_id -> {"event": Event, "result": dict}

def requires_tool_for_prompt(prompt: str) -> bool:
    """Check if user prompt likely requires a tool to execute."""
    lowered = prompt.lower()
    return any(phrase in lowered for phrase in TOOL_HEURISTIC_PHRASES)

def get_or_create_conversation(session_id: str) -> list:
    """Get or create a conversation context for a session."""
    if session_id not in conversations:
        system_prompt = generate_system_prompt()
        conversations[session_id] = [
            {"role": "system", "content": system_prompt}
        ]
    return conversations[session_id]

def add_message_to_conversation(session_id: str, role: str, content: str):
    """Add a message to the conversation history."""
    conversation = get_or_create_conversation(session_id)
    conversation.append({"role": role, "content": content})
    
    # Keep conversation history reasonable (system prompt + limit)
    if len(conversation) > CONVERSATION_HISTORY_LIMIT + 1:
        conversations[session_id] = [conversation[0]] + conversation[-(CONVERSATION_HISTORY_LIMIT):]


def call_llm(prompt: str, model: Optional[str] = None, session_id: Optional[str] = None):
    """
    Stuurt een prompt naar Ollama Cloud API.
    Geeft volledige response terug.
    """
    model = model or OLLAMA_MODEL
    
    try:
        if session_id:
            # Use conversation context
            conversation = get_or_create_conversation(session_id)
            add_message_to_conversation(session_id, "user", prompt)
            messages = conversation.copy()
        else:
            # Single-shot without context
            messages = [{'role': 'user', 'content': prompt}]
        
        response = ollama_client.chat(model=model, messages=messages, stream=False)
        content = response['message']['content']
        
        if session_id:
            add_message_to_conversation(session_id, "assistant", content)
        
        return content
    except Exception as e:
        print(f"Fout bij LLM API call: {e}")
        return f"Fout: {str(e)}"

def call_llm_stream(prompt: str, model: Optional[str] = None, session_id: Optional[str] = None):
    """
    Stuurt een prompt naar Ollama Cloud API met streaming.
    Yieldt response chunks één voor één.
    """
    model = model or OLLAMA_MODEL
    
    try:
        if session_id:
            # Use conversation context
            conversation = get_or_create_conversation(session_id)
            add_message_to_conversation(session_id, "user", prompt)
            messages = conversation.copy()
        else:
            # Single-shot without context
            messages = [{'role': 'user', 'content': prompt}]
        
        full_response = ""
        for part in ollama_client.chat(model=model, messages=messages, stream=True):
            if 'message' in part and 'content' in part['message']:
                content = part['message']['content']
                if content:
                    full_response += content
                    yield content
        
        # Add complete response to conversation
        if session_id and full_response:
            add_message_to_conversation(session_id, "assistant", full_response)
    except Exception as e:
        print(f"Fout bij streaming LLM call: {e}")
        yield f"Fout: {str(e)}"

async def send_command_to_device(device_id: str, command: Dict[str, Any]) -> bool:
    """Send a command to a specific device via WebSocket."""
    if device_id in clients:
        try:
            await clients[device_id].send_text(json.dumps(command))
            return True
        except Exception as e:
            print(f"Error sending command to {device_id}: {e}")
            return False
    return False

async def send_command_to_all(command: Dict[str, Any]) -> None:
    """Send a command to all connected devices."""
    for device_id, client in clients.items():
        try:
            await client.send_text(json.dumps(command))
        except Exception as e:
            print(f"Error sending to {device_id}: {e}")

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
                        'allowed_tools': DEFAULT_ALLOWED_TOOLS,
                        'allowed_paths': DEFAULT_ALLOWED_PATHS,
                        'allowed_apps': DEFAULT_ALLOWED_APPS,
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
                existing_task = llm_tasks.get(device_id)
                if existing_task and not existing_task.done():
                    existing_task.cancel()
                llm_tasks[device_id] = asyncio.create_task(handle_llm_request(websocket, event, device_id))
            
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
                
                # Notify any waiting LLM request
                if execution_id and execution_id in tool_executions:
                    tool_executions[execution_id]["result"] = {
                        "success": success,
                        "result": result,
                        "error": error
                    }
                    tool_executions[execution_id]["event"].set()
                
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
        if device_id and device_id in llm_tasks:
            task = llm_tasks.pop(device_id)
            if not task.done():
                task.cancel()
        print(f"📱 Client verbroken: {device_id}")
    except Exception as e:
        print(f"❌ WebSocket fout: {e}")
        import traceback
        traceback.print_exc()
        if device_id and device_id in clients:
            del clients[device_id]
        if device_id and device_id in llm_tasks:
            task = llm_tasks.pop(device_id)
            if not task.done():
                task.cancel()
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
