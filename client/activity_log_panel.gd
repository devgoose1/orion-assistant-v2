# Godot 4.6 - ActivityLogPanel.gd
# Display recent tool executions and system events
extends PanelContainer

var activity_log: Array = []
var log_display: TextEdit
var max_log_entries: int = 100


func _ready() -> void:
	"""Initialize activity log panel."""
	var vbox = VBoxContainer.new()
	add_child(vbox)
	
	# Title
	var title_label = Label.new()
	title_label.text = "Activity Log"
	title_label.add_theme_font_size_override("font_size", 14)
	vbox.add_child(title_label)
	
	# Log display
	log_display = TextEdit.new()
	log_display.custom_minimum_size = Vector2(400, 300)
	log_display.read_only = true
	log_display.editable = false
	log_display.text = "[System started]\n"
	vbox.add_child(log_display)
	
	# Clear button
	var clear_button = Button.new()
	clear_button.text = "Clear Log"
	clear_button.pressed.connect(_clear_log)
	vbox.add_child(clear_button)
	
	print("Activity log panel initialized")


func add_log_entry(tool_name: String, success: bool, result: String = "") -> void:
	"""Add a tool execution entry to the log.
	
	Args:
		tool_name: Name of executed tool
		success: Whether execution succeeded
		result: Result message
	"""
	var status = "✓" if success else "✗"
	var timestamp = Time.get_ticks_msec() / 1000.0
	var entry = "[%.2f] %s %s: %s" % [timestamp, status, tool_name, result]
	
	activity_log.append(entry)
	
	# Update display
	if log_display:
		log_display.text += entry + "\n"
		# Auto-scroll to bottom
		log_display.scroll_vertical = log_display.get_line_count()
	
	# Keep log size manageable
	if activity_log.size() > max_log_entries:
		activity_log.pop_front()


func add_system_message(message: String) -> void:
	"""Add a system message to the log.
	
	Args:
		message: Message text
	"""
	var timestamp = Time.get_ticks_msec() / 1000.0
	var entry = "[%.2f] [System] %s" % [timestamp, message]
	
	activity_log.append(entry)
	
	if log_display:
		log_display.text += entry + "\n"
		log_display.scroll_vertical = log_display.get_line_count()


func add_llm_message(prompt: String, response: String) -> void:
	"""Add an LLM interaction to the log.
	
	Args:
		prompt: User prompt
		response: LLM response (first 100 chars)
	"""
	var short_response = response.substr(0, 100) + ("..." if response.length() > 100 else "")
	var timestamp = Time.get_ticks_msec() / 1000.0
	var entry = "[%.2f] [LLM] Q: %s → %s" % [timestamp, prompt.substr(0, 50), short_response]
	
	activity_log.append(entry)
	
	if log_display:
		log_display.text += entry + "\n"
		log_display.scroll_vertical = log_display.get_line_count()


func _clear_log() -> void:
	"""Clear the activity log."""
	activity_log.clear()
	if log_display:
		log_display.text = "[Log cleared]\n"


func get_log_entries() -> Array:
	"""Get all log entries.
	
	Returns:
		Array of log entry strings
	"""
	return activity_log.duplicate()
