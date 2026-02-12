from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from typing import Optional
from dotenv import load_dotenv
from ollama import Client

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

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

clients = []

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    print(f"Client verbonden. Totaal clients: {len(clients)}")
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            print("Event van client:", event)
            
            # Verwerk LLM requests
            if event.get("type") == "llm_request":
                prompt = event.get("prompt", "")
                model = event.get("model", OLLAMA_MODEL)
                stream = event.get("stream", False)
                
                print(f"📝 LLM Request ontvangen:")
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
                
    except WebSocketDisconnect:
        clients.remove(websocket)
        print(f"Client verbroken. Totaal clients: {len(clients)}")
    except Exception as e:
        print(f"WebSocket fout: {e}")
        if websocket in clients:
            clients.remove(websocket)

async def send_command_to_all(command):
    """Stuurt een command naar alle verbonden clients."""
    for client in clients:
        try:
            await client.send_text(json.dumps(command))
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)