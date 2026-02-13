extends Node

var ws_client: WebSocketPeer = WebSocketPeer.new()
var BACKEND_URL: String = "ws://localhost:8765/ws"
var connected_to_backend: bool = false
var registered: bool = false
var current_response: String = ""
var device_id: String = ""
var permissions: Dictionary = {}
var tool_registry: Node = null

signal llm_response_received(response: String)
signal llm_chunk_received(chunk: String)
signal llm_response_complete(full_response: String)
signal device_registered(perms: Dictionary)
signal tool_executed(tool_name: String, success: bool, result: Variant)
signal tool_executing(tool_name: String, parameters: Dictionary)

func _ready() -> void:
	# Initialize tool registry
	var ToolRegistryClass = load("res://tools/tool_registry.gd")
	tool_registry = ToolRegistryClass.new()
	add_child(tool_registry)
	
	# Generate unique device ID
	device_id = _generate_device_id()
	print("Device ID: ", device_id)
	
	ws_client.connect_to_url(BACKEND_URL)
	print("WebSocket initialiseren...")
	
	# Setup heartbeat timer
	var heartbeat_timer = Timer.new()
	heartbeat_timer.wait_time = 30.0  # Every 30 seconds
	heartbeat_timer.timeout.connect(send_heartbeat)
	heartbeat_timer.autostart = true
	add_child(heartbeat_timer)


func _process(_delta: float) -> void:
	ws_client.poll()
	
	# Check voor staat veranderingen
	var state = ws_client.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN and not connected_to_backend:
		connected_to_backend = true
		print("Verbonden met backend!")
		# Send device registration
		_register_device()
	elif state == WebSocketPeer.STATE_CLOSED and connected_to_backend:
		connected_to_backend = false
		registered = false
		print("Verbroken van backend!")
	
	# Ontvang berichten van server
	if ws_client.get_ready_state() == WebSocketPeer.STATE_OPEN:
		while ws_client.get_available_packet_count() > 0:
			var packet = ws_client.get_packet()
			if packet.size() > 0:
				var json_string = packet.get_string_from_utf8()
				if json_string:
					var message = JSON.parse_string(json_string)
					if message != null:
						_handle_server_message(message)

func _handle_server_message(message: Dictionary) -> void:
	if message == null:
		return
		
	match message.get("type", ""):
		"device_registered":
			registered = true
			permissions = message.get("permissions", {})
			print("Device geregistreerd!")
			print("  Allowed tools: ", permissions.get("allowed_tools", []))
			print("  Allowed paths: ", permissions.get("allowed_paths", []))
			device_registered.emit(permissions)
		
		"heartbeat_ack":
			pass  # Heartbeat acknowledged
		
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
		
		"tool_execute":
			# Backend requests tool execution
			var tool_name = message.get("tool_name")
			var parameters = message.get("parameters", {})
			# Support both request_id (test endpoint) and execution_id (LLM tool calling)
			var exec_id = message.get("execution_id", message.get("request_id", ""))
			
			print("Tool execution request: ", tool_name)
			print("Parameters: ", parameters)
			print("Execution ID: ", exec_id)
			
			# Execute tool
			var result = tool_registry.execute_tool(tool_name, parameters)
			
			# Send result back to backend
			var tool_result = {
				"type": "tool_result",
				"execution_id": exec_id,  # Use execution_id as primary
				"request_id": exec_id,    # Keep for backward compatibility
				"success": result.get("success", false),
				"result": result,
				"error": result.get("error")
			}
			
			ws_client.send_text(JSON.stringify(tool_result))
			
			# Emit signal for UI
			tool_executed.emit(tool_name, result.get("success", false), result)
		
		"tool_executing":
			# LLM is executing a tool - notify UI
			var tool_name = message.get("tool_name")
			var parameters = message.get("parameters", {})
			
			print("LLM is executing tool: ", tool_name)
			tool_executing.emit(tool_name, parameters)
		
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
		print("Fout: Niet verbonden met backend!")
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

func _register_device() -> void:
	"""
	Registreert dit device bij de backend.
	"""
	var device_info = {
		"type": "device_register",
		"device_id": device_id,
		"hostname": OS.get_name() + "_" + OS.get_model_name(),
		"os_type": OS.get_name(),
		"capabilities": {
			"screen_width": DisplayServer.screen_get_size().x,
			"screen_height": DisplayServer.screen_get_size().y,
			"processor_name": OS.get_processor_name(),
			"processor_count": OS.get_processor_count(),
		},
		"metadata": {
			"godot_version": Engine.get_version_info()["string"],
			"locale": OS.get_locale(),
		}
	}
	
	ws_client.send_text(JSON.stringify(device_info))
	print("Device registratie verzonden...")

func _generate_device_id() -> String:
	"""
	Genereert een unieke device ID. In productie zou dit persistent opgeslagen worden.
	"""
	# Simple ID based on system properties
	var id_base = OS.get_name() + "_" + OS.get_model_name() + "_" + str(OS.get_unique_id())
	# Convert to simple hash
	return id_base.sha256_text().substr(0, 16)

func send_heartbeat() -> void:
	"""
	Stuur heartbeat naar backend om verbinding actief te houden.
	"""
	if not connected_to_backend or not registered:
		return
	
	var heartbeat = {
		"type": "device_heartbeat",
		"device_id": device_id
	}
	
	ws_client.send_text(JSON.stringify(heartbeat))
