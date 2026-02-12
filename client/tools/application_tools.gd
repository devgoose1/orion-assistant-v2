extends RefCounted

class_name ApplicationTools

static func open_app_tool() -> Dictionary:
	return {
		"name": "open_app",
		"execute": func(params: Dictionary) -> Dictionary:
			var app_name = params["app_name"]
			var arguments = params.get("arguments", [])
			
			# Map app names to executables
			var app_map = {
				"notepad": "notepad.exe",
				"calculator": "calc.exe", 
				"browser": "chrome.exe",
				"firefox": "firefox.exe",
				"edge": "msedge.exe",
				"terminal": "wt.exe",
				"cmd": "cmd.exe"
			}
			
			var executable = app_map.get(app_name.to_lower(), app_name)
			
			# Build command with arguments
			var cmd_args = [executable]
			cmd_args.append_array(arguments)
			
			var output = []
			var pid = OS.execute("cmd.exe", ["/c", "start", "", executable] + arguments, output, false)
			
			return {
				"success": true,
				"app_name": app_name,
				"executable": executable,
				"pid": pid
			}
	}

static func close_app_tool() -> Dictionary:
	return {
		"name": "close_app",
		"execute": func(params: Dictionary) -> Dictionary:
			var app_name = params["app_name"]
			var force = params.get("force", false)
			
			var output = []
			var err
			
			if OS.get_name() == "Windows":
				var taskkill_args = ["/IM", app_name + ".exe"]
				if force:
					taskkill_args.append("/F")
				err = OS.execute("taskkill", taskkill_args, output, true)
			else:
				var kill_signal = "-15" if not force else "-9"
				err = OS.execute("pkill", [kill_signal, app_name], output, true)
			
			if err != 0:
				return {
					"success": false,
					"error": "Failed to close app",
					"output": "\n".join(output)
				}
			
			return {
				"success": true,
				"app_name": app_name,
				"output": "\n".join(output)
			}
	}
