from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import requests
import os
from typing import Optional

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
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "https://api.ollama.ai/api/generate")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

clients = []

def call_llm(prompt: str, model: Optional[str] = None) -> str:
    """
    Stuurt een prompt naar Ollama Cloud API en krijgt een response.
    """
    model = model or OLLAMA_MODEL
    
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"Fout bij LLM API call: {e}")
        return f"Fout: {str(e)}"

def call_llm_stream(prompt: str, model: Optional[str] = None):
    """
    Stuurt een prompt naar Ollama Cloud API met streaming.
    Yieldt response chunks één voor één.
    """
    model = model or OLLAMA_MODEL
    
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                response_text = chunk.get("response", "")
                if response_text:
                    yield response_text
    except requests.exceptions.RequestException as e:
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
                
                if stream:
                    # Streaming modus
                    for chunk in call_llm_stream(prompt, model):
                        await websocket.send_text(json.dumps({
                            "type": "llm_response_chunk",
                            "chunk": chunk,
                            "complete": False
                        }))
                    
                    # Signaal dat streaming klaar is
                    await websocket.send_text(json.dumps({
                        "type": "llm_response_chunk",
                        "chunk": "",
                        "complete": True
                    }))
                else:
                    # Niet-streaming modus
                    response = await asyncio.to_thread(call_llm, prompt, model)
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