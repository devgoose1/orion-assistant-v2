# Godot 4.6 - MetricsPanel.gd
# Display real-time system metrics in a visual panel
extends PanelContainer

var metrics: Dictionary = {}
var cpu_bar: ProgressBar
var memory_bar: ProgressBar  
var disk_bar: ProgressBar
var cpu_label: Label
var memory_label: Label
var disk_label: Label


func _ready() -> void:
	"""Initialize metrics panel UI."""
	# Create visual elements for metrics display
	var vbox = VBoxContainer.new()
	add_child(vbox)
	
	# CPU metrics
	cpu_label = Label.new()
	cpu_label.text = "CPU: 0%"
	vbox.add_child(cpu_label)
	
	cpu_bar = ProgressBar.new()
	cpu_bar.min_value = 0
	cpu_bar.max_value = 100
	cpu_bar.value = 0
	cpu_bar.custom_minimum_size = Vector2(200, 20)
	vbox.add_child(cpu_bar)
	
	# Memory metrics
	memory_label = Label.new()
	memory_label.text = "Memory: 0%"
	vbox.add_child(memory_label)
	
	memory_bar = ProgressBar.new()
	memory_bar.min_value = 0
	memory_bar.max_value = 100
	memory_bar.value = 0
	memory_bar.custom_minimum_size = Vector2(200, 20)
	vbox.add_child(memory_bar)
	
	# Disk metrics
	disk_label = Label.new()
	disk_label.text = "Disk: 0%"
	vbox.add_child(disk_label)
	
	disk_bar = ProgressBar.new()
	disk_bar.min_value = 0
	disk_bar.max_value = 100
	disk_bar.value = 0
	disk_bar.custom_minimum_size = Vector2(200, 20)
	vbox.add_child(disk_bar)
	
	print("Metrics panel initialized")


func update_metrics(new_metrics: Dictionary) -> void:
	"""Update display with new metrics data.
	
	Args:
		new_metrics: Dictionary with cpu_percent, memory_percent, disk_percent
	"""
	metrics = new_metrics
	
	var cpu = metrics.get("cpu_percent", 0.0)
	var memory = metrics.get("memory_percent", 0.0)
	var disk = metrics.get("disk_percent", 0.0)
	
	# Update progress bars
	if cpu_bar:
		cpu_bar.value = cpu
		cpu_label.text = "CPU: %.1f%%" % cpu
	
	if memory_bar:
		memory_bar.value = memory
		memory_label.text = "Memory: %.1f%%" % memory
	
	if disk_bar:
		disk_bar.value = disk
		disk_label.text = "Disk: %.1f%%" % disk


func get_metrics() -> Dictionary:
	"""Return current metrics.
	
	Returns:
		Dictionary with latest metrics
	"""
	return metrics
