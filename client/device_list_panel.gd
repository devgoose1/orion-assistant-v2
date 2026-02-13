# Godot 4.6 - DeviceListPanel.gd
# Display connected devices in a list
extends TabContainer

signal device_selected(device_id: String)

var devices: Array = []
var device_items: Dictionary = {}  # device_id -> Node


func _ready() -> void:
	"""Initialize device list panel."""
	print("Device list panel initialized")


func update_device_list(device_list: Array) -> void:
	"""Update the list of connected devices.
	
	Args:
		device_list: Array of device dictionaries from dashboard API
	"""
	devices = device_list
	_rebuild_device_display()


func _rebuild_device_display() -> void:
	"""Rebuild the device list UI."""
	# Clear existing tabs
	for i in range(get_tab_count()):
		get_tab_control(i).queue_free()
	
	# Create device panels
	for device in devices:
		var device_id = device.get("device_id")
		var hostname = device.get("hostname", "Unknown")
		
		# Create panel for this device
		var device_panel = _create_device_panel(device)
		add_child(device_panel)
		set_tab_title(get_tab_count() - 1, hostname)
		
		device_items[device_id] = device_panel


func _create_device_panel(device: Dictionary) -> Control:
	"""Create a panel displaying a single device's info.
	
	Args:
		device: Device information dictionary
		
	Returns:
		Control node containing device UI
	"""
	var panel = PanelContainer.new()
	var vbox = VBoxContainer.new()
	panel.add_child(vbox)
	
	# Device name
	var device_label = Label.new()
	device_label.text = "[%s] %s" % [device.get("device_id"), device.get("hostname", "Unknown")]
	device_label.add_theme_font_size_override("font_size", 14)
	vbox.add_child(device_label)
	
	# Status
	var status_label = Label.new()
	var status = device.get("status", "offline")
	var status_color = "🟢 Online" if status == "online" else "🔴 Offline"
	status_label.text = "Status: %s" % status_color
	vbox.add_child(status_label)
	
	# OS Info
	var os_label = Label.new()
	os_label.text = "OS: %s %s" % [device.get("os_type"), device.get("os_version", "")]
	vbox.add_child(os_label)
	
	# Last heartbeat
	var heartbeat_label = Label.new()
	var last_hb = device.get("last_heartbeat", "Never")
	heartbeat_label.text = "Last seen: %s" % last_hb
	vbox.add_child(heartbeat_label)
	
	# Metrics display
	var metrics = device.get("metrics")
	if metrics:
		var metrics_label = Label.new()
		metrics_label.text = "Metrics: CPU=%.1f%% MEM=%.1f%% DISK=%.1f%%" % [
			metrics.get("cpu_percent", 0),
			metrics.get("memory_percent", 0),
			metrics.get("disk_percent", 0)
		]
		vbox.add_child(metrics_label)
	
	# Select button
	var select_button = Button.new()
	select_button.text = "View Details"
	select_button.pressed.connect(_on_device_selected.bindv([device.get("device_id")]))
	vbox.add_child(select_button)
	
	return panel


func _on_device_selected(device_id: String) -> void:
	"""Handle device selection.
	
	Args:
		device_id: The selected device ID
	"""
	print("Device selected: %s" % device_id)
	device_selected.emit(device_id)


func get_device_panel(device_id: String) -> Control:
	"""Get the panel for a specific device.
	
	Args:
		device_id: Device identifier
		
	Returns:
		Control node or null if not found
	"""
	return device_items.get(device_id)
