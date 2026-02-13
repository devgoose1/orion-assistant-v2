# Godot 4.6 - Dashboard.gd
# Main dashboard scene controller
extends Control

var websocket: Node = null
var dashboard_data: Dictionary = {}
var current_device_id: String = ""

func _ready() -> void:
	"""Initialize dashboard on scene load."""
	# Find the WebSocket node in parent
	websocket = get_node("/root/WebSocketManager")
	
	if websocket:
		# Connect to metrics updates
		if websocket.has_signal("metrics_collected"):
			websocket.metrics_collected.connect(_on_metrics_collected)
		
		print("Dashboard initialized")
	else:
		print("Warning: WebSocket manager not found")
	
	# Initialize UI
	_setup_ui()


func _setup_ui() -> void:
	"""Setup the dashboard user interface."""
	# This will be built in the .tscn file, but we setup dynamic elements here
	anchor_left = 0.0
	anchor_top = 0.0
	anchor_right = 1.0
	anchor_bottom = 1.0
	
	print("Dashboard UI setup complete")


func _on_metrics_collected(metrics: Dictionary) -> void:
	"""Called when websocket collects new metrics.
	
	Args:
		metrics: Dictionary with cpu_percent, memory_percent, disk_percent
	"""
	# Update dashboard with latest metrics
	dashboard_data["latest_metrics"] = metrics
	
	# Trigger UI update
	_update_metrics_display(metrics)


func _update_metrics_display(metrics: Dictionary) -> void:
	"""Update the metrics display on the dashboard.
	
	Args:
		metrics: Dictionary with current system metrics
	"""
	# This will update progress bars, labels, etc
	print("Updating metrics display: CPU=%.1f%% MEM=%.1f%% DISK=%.1f%%" % [
		metrics.get("cpu_percent", 0),
		metrics.get("memory_percent", 0),
		metrics.get("disk_percent", 0)
	])
	
	# Update UI elements here (will be implemented in .tscn)


func fetch_dashboard_overview() -> void:
	"""Fetch dashboard overview from backend API."""
	# This would be called on scene load to get initial data
	# Uses HTTP GET /api/dashboard/overview
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_dashboard_overview_loaded)
	
	var error = http.request("http://localhost:8765/api/dashboard/overview")
	if error != OK:
		print("Error fetching dashboard: ", error)


func _on_dashboard_overview_loaded(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	"""Handle dashboard overview API response."""
	if response_code != 200:
		print("Dashboard API error: ", response_code)
		return
	
	var json_string = body.get_string_from_utf8()
	var data = JSON.parse_string(json_string)
	
	if data and data.get("success"):
		dashboard_data = data.get("data", {})
		print("Dashboard data loaded: %d devices" % dashboard_data.get("total_devices", 0))
		_display_device_list()


func _display_device_list() -> void:
	"""Display list of connected devices on dashboard."""
	var devices = dashboard_data.get("devices", [])
	
	print("Displaying %d devices:" % devices.size())
	for device in devices:
		print("  - %s: %s" % [device.get("device_id"), device.get("status")])


func select_device(device_id: String) -> void:
	"""Select a device to view details.
	
	Args:
		device_id: The device to select
	"""
	current_device_id = device_id
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_device_details_loaded.bindv([device_id]))
	
	var error = http.request("http://localhost:8765/api/dashboard/device/%s" % device_id)
	if error != OK:
		print("Error fetching device details: ", error)


func _on_device_details_loaded(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray, device_id: String) -> void:
	"""Handle device details API response."""
	if response_code != 200:
		print("Device API error: ", response_code)
		return
	
	var json_string = body.get_string_from_utf8()
	var data = JSON.parse_string(json_string)
	
	if data and data.get("success"):
		var device_data = data.get("data", {})
		print("Device %s details loaded" % device_id)
		_display_device_details(device_data)


func _display_device_details(device_data: Dictionary) -> void:
	"""Display selected device's detailed information.
	
	Args:
		device_data: Device information and metrics
	"""
	print("Device details:")
	print("  Device: ", device_data.get("device", {}).get("device_id"))
	print("  Status: ", device_data.get("device", {}).get("status"))
	
	var metrics = device_data.get("current_metrics")
	if metrics:
		print("  Metrics: CPU=%.1f%% MEM=%.1f%% DISK=%.1f%%" % [
			metrics.get("cpu_percent", 0),
			metrics.get("memory_percent", 0),
			metrics.get("disk_percent", 0)
		])
	
	var executions = device_data.get("recent_executions", [])
	print("  Recent executions: %d" % executions.size())
