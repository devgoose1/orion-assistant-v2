extends Control

# References to UI elements
@onready var chat_container = $VBoxContainer/ChatContainer/MarginContainer/ScrollContainer/ChatContent
@onready var scroll_container = $VBoxContainer/ChatContainer/MarginContainer/ScrollContainer
@onready var input_field = $VBoxContainer/InputContainer/InputMargin/HBoxContainer/InputField
@onready var send_button = $VBoxContainer/InputContainer/InputMargin/HBoxContainer/SendButton
@onready var status_label = $VBoxContainer/StatusBar/StatusBarMargin/HBoxContainer/StatusLabel
@onready var connection_indicator = $VBoxContainer/StatusBar/StatusBarMargin/HBoxContainer/ConnectionIndicator

# WebSocket reference
var websocket: Node

func _ready() -> void:
	# Get WebSocket singleton
	websocket = get_node("/root/WebSocket")
	
	# Connect signals
	send_button.pressed.connect(_on_send_button_pressed)
	input_field.text_submitted.connect(_on_input_submitted)
	
	# Connect WebSocket signals
	websocket.llm_response_received.connect(_on_llm_response)
	websocket.llm_chunk_received.connect(_on_llm_chunk)
	websocket.llm_response_complete.connect(_on_llm_complete)
	websocket.device_registered.connect(_on_device_registered)
	websocket.tool_executed.connect(_on_tool_executed)
	websocket.tool_executing.connect(_on_tool_executing)
	
	# Update connection status
	_update_connection_status()

func _process(_delta: float) -> void:
	_update_connection_status()

func _update_connection_status() -> void:
	if websocket.connected_to_backend and websocket.registered:
		status_label.text = "Connected & Registered"
		connection_indicator.modulate = Color.GREEN
	elif websocket.connected_to_backend:
		status_label.text = "Connected (Registering...)"
		connection_indicator.modulate = Color.YELLOW
	else:
		status_label.text = "Disconnected"
		connection_indicator.modulate = Color.RED

func _on_send_button_pressed() -> void:
	_send_message()

func _on_input_submitted(_text: String) -> void:
	_send_message()

func _send_message() -> void:
	var message = input_field.text.strip_edges()
	
	if message.is_empty():
		return
	
	if not websocket.connected_to_backend:
		_add_system_message("Error: Not connected to backend")
		return
	
	# Add user message to chat
	_add_user_message(message)
	
	# Clear input
	input_field.text = ""
	
	# Send to LLM
	websocket.ask_llm(message, "gpt-oss:120b", true)
	
	# Add "thinking" indicator
	_add_assistant_message("", true)

func _add_user_message(text: String) -> void:
	var message_container = HBoxContainer.new()
	message_container.alignment = BoxContainer.ALIGNMENT_END
	
	var message_bubble = PanelContainer.new()
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.2, 0.5, 0.8, 0.8)
	style.corner_radius_top_left = 10
	style.corner_radius_top_right = 10
	style.corner_radius_bottom_left = 10
	style.corner_radius_bottom_right = 2
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	message_bubble.add_theme_stylebox_override("panel", style)
	
	var label = Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size = Vector2(400, 0)
	
	message_bubble.add_child(label)
	message_container.add_child(message_bubble)
	chat_container.add_child(message_container)
	
	_scroll_to_bottom()

var current_assistant_message: Label = null

func _add_assistant_message(text: String, is_streaming: bool = false) -> void:
	if is_streaming and current_assistant_message != null:
		# Update existing message
		current_assistant_message.text += text
		_scroll_to_bottom()
		return
	
	var message_container = HBoxContainer.new()
	message_container.alignment = BoxContainer.ALIGNMENT_BEGIN
	
	var message_bubble = PanelContainer.new()
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.25, 0.25, 0.25, 0.8)
	style.corner_radius_top_left = 10
	style.corner_radius_top_right = 10
	style.corner_radius_bottom_left = 2
	style.corner_radius_bottom_right = 10
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	message_bubble.add_theme_stylebox_override("panel", style)
	
	var label = Label.new()
	label.text = text if text else "●●●"  # Thinking indicator
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size = Vector2(400, 0)
	
	current_assistant_message = label
	
	message_bubble.add_child(label)
	message_container.add_child(message_bubble)
	chat_container.add_child(message_container)
	
	_scroll_to_bottom()

func _add_system_message(text: String) -> void:
	var message_container = CenterContainer.new()
	
	var label = Label.new()
	label.text = text
	label.modulate = Color(0.7, 0.7, 0.7, 1.0)
	label.add_theme_font_size_override("font_size", 12)
	
	message_container.add_child(label)
	chat_container.add_child(message_container)
	
	_scroll_to_bottom()

func _scroll_to_bottom() -> void:
	await get_tree().process_frame
	scroll_container.scroll_vertical = int(scroll_container.get_v_scroll_bar().max_value)

func _on_llm_response(response: String) -> void:
	# Non-streaming response
	if current_assistant_message:
		current_assistant_message.text = response
	else:
		_add_assistant_message(response)
	current_assistant_message = null

func _on_llm_chunk(chunk: String) -> void:
	# Streaming chunk
	if current_assistant_message and current_assistant_message.text == "●●●":
		# Replace thinking indicator with first chunk
		current_assistant_message.text = chunk
	else:
		_add_assistant_message(chunk, true)

func _on_llm_complete(_full_response: String) -> void:
	# Streaming complete
	current_assistant_message = null
	_add_system_message("Response complete")

func _on_device_registered(_permissions: Dictionary) -> void:
	_add_system_message("Device registered successfully")

func _on_tool_executing(tool_name: String, parameters: Dictionary) -> void:
	# Show that LLM is executing a tool
	var params_str = JSON.stringify(parameters)
	_add_system_message("🔧 Executing tool: " + tool_name + " with params: " + params_str)

func _on_tool_executed(tool_name: String, success: bool, result: Variant) -> void:
	# Show tool execution result in chat
	if success:
		var result_text = "Tool executed: " + tool_name
		if result != null:
			result_text += " - " + str(result)
		_add_system_message("✓ " + result_text)
	else:
		var error_text = "Tool failed: " + tool_name
		if result != null and typeof(result) == TYPE_DICTIONARY and result.has("error"):
			error_text += " - " + result["error"]
		_add_system_message("✗ " + error_text)

