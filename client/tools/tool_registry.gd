extends Node

class_name ToolRegistry

# Registry of available tools
var tools: Dictionary = {}

func _ready() -> void:
	_register_tools()

func _register_tools() -> void:
	# Register file system tools
	tools["create_directory"] = FileSystemTools.create_directory_tool()
	tools["delete_directory"] = FileSystemTools.delete_directory_tool()
	tools["search_files"] = FileSystemTools.search_files_tool()
	
	# Register application tools
	tools["open_app"] = ApplicationTools.open_app_tool()
	tools["close_app"] = ApplicationTools.close_app_tool()
	
	# Register device tools
	tools["get_device_info"] = DeviceTools.get_device_info_tool()
	tools["get_running_processes"] = DeviceTools.get_running_processes_tool()

func execute_tool(tool_name: String, parameters: Dictionary) -> Dictionary:
	if not tools.has(tool_name):
		return {
			"success": false,
			"error": "Unknown tool: " + tool_name
		}
	
	var tool = tools[tool_name]
	
	# Execute the tool
	var result = tool["execute"].call(parameters)
	
	return result

func has_tool(tool_name: String) -> bool:
	return tools.has(tool_name)

func get_tool_names() -> Array:
	return tools.keys()
