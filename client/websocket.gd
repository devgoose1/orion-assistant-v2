extends Node

var ws_client: WebSocketPeer = WebSocketPeer.new()
var BACKEND_URL: String = "ws://localhost:8765/ws"
var connected_to_backend: bool = false
var current_response: String = ""

signal llm_response_received(response: String)
signal llm_chunk_received(chunk: String)
signal llm_response_complete(full_response: String)

func _ready() -> void:
	ws_client.connect_to_url(BACKEND_URL)
	print("WebSocket initialiseren...")

func _process(_delta: float) -> void:
	ws_client.poll()
	
	# Check voor staat veranderingen
	var state = ws_client.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN and not connected_to_backend:
		connected_to_backend = true
		print("✓ Verbonden met backend!")
	elif state == WebSocketPeer.STATE_CLOSED and connected_to_backend:
		connected_to_backend = false
		print("✗ Verbroken van backend!")
	
	# Ontvang berichten van server
	if ws_client.get_ready_state() == WebSocketPeer.STATE_OPEN:
		var json_string = ws_client.get_text()
		if json_string:
			var message = JSON.parse_string(json_string)
			if message != null:
				_handle_server_message(message)

func _handle_server_message(message: Dictionary) -> void:
	if message == null:
		return
		
	match message.get("type", ""):
		"llm_response":
			# Niet-streaming response
			var response = message.get("response", "")
			print("LLM antwoord:", response)
			current_response = response
			llm_response_received.emit(response)
			
		"llm_response_chunk":
			# Streaming response
			var chunk = message.get("chunk", "")
			var complete = message.get("complete", false)
			
			if not complete:
				# Voeg chunk toe aan volledige response
				current_response += chunk
				# Emit telkens een chunk - UI kan real-time updaten
				llm_chunk_received.emit(chunk)
				print("Chunk ontvangen: ", chunk)
			else:
				# Response klaar
				print("Response streaming klaar!")
				llm_response_complete.emit(current_response)
				current_response = ""
		
		_:
			if message.get("type"):
				print("Onbekend berichttype:", message.get("type"))

func ask_llm(prompt: String, model: String = "mistral", stream: bool = true) -> void:
	"""
	Stuurt een LLM request naar de backend.
	Als stream=true: ontvangt chunks real-time
	Als stream=false: ontvangt volledige response in één keer
	"""
	if not connected_to_backend:
		print("✗ Fout: Niet verbonden met backend!")
		print("  Wacht tot verbonden te zijn")
		return
	
	current_response = ""
	
	var request = {
		"type": "llm_request",
		"prompt": prompt,
		"model": model,
		"stream": stream
	}
	
	ws_client.send_text(JSON.stringify(request))
	print("LLM request verzonden (stream=%s): %s" % [stream, prompt])
