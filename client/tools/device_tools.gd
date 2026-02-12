extends RefCounted

class_name DeviceTools

static func get_device_info_tool() -> Dictionary:
	return {
		"name": "get_device_info",
		"execute": func(params: Dictionary) -> Dictionary:
			var info_type = params.get("info_type", "all")
			
			var info = {
				"os_name": OS.get_name(),
				"os_version": OS.get_version(),
				"processor_count": OS.get_processor_count(),
				"processor_name": OS.get_processor_name(),
				"video_adapter_driver_info": OS.get_video_adapter_driver_info()
			}
			
			if info_type != "all":
				if info.has(info_type):
					return {"success": true, "info": {info_type: info[info_type]}}
				else:
					return {"success": false, "error": "Unknown info type: " + info_type}
			
			return {"success": true, "info": info}
	}

static func get_running_processes_tool() -> Dictionary:
	return {
		"name": "get_running_processes",
		"execute": func(params: Dictionary) -> Dictionary:
			var filter_name = params.get("filter", "")
			
			var output = []
			var err
			
			if OS.get_name() == "Windows":
				err = OS.execute("tasklist", [], output, true)
			else:
				err = OS.execute("ps", ["aux"], output, true)
			
			if err != 0:
				return {"success": false, "error": "Failed to get processes"}
			
			var processes = []
			var lines = ("\n".join(output)).split("\n")
			
			for line in lines:
				if filter_name.is_empty() or filter_name.to_lower() in line.to_lower():
					processes.append(line.strip_edges())
			
			return {
				"success": true,
				"processes": processes,
				"count": processes.size()
			}
	}
