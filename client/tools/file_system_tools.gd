extends RefCounted

class_name FileSystemTools

static func create_directory_tool() -> Dictionary:
	return {
		"name": "create_directory",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			
			# Use DirAccess to create directory recursively
			var err = DirAccess.make_dir_recursive_absolute(path)
			if err != OK:
				return {"success": false, "error": "Failed to create directory: " + str(err)}
			
			return {"success": true, "path": path}
	}

static func delete_directory_tool() -> Dictionary:
	return {
		"name": "delete_directory",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			var recursive = params.get("recursive", false)
			
			var dir = DirAccess.open(path)
			if dir == null:
				return {"success": false, "error": "Directory not found"}
			
			if recursive:
				# Recursively delete contents
				var helper = FileSystemHelper.new()
				helper.remove_recursive(path)
			
			var err = DirAccess.remove_absolute(path)
			if err != OK:
				return {"success": false, "error": "Failed to delete directory: " + str(err)}
			
			return {"success": true, "path": path}
	}

static func search_files_tool() -> Dictionary:
	return {
		"name": "search_files",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			var pattern = params["pattern"]
			var recursive = params.get("recursive", true)
			
			# Check if directory exists
			if not DirAccess.dir_exists_absolute(path):
				return {"success": false, "error": "Directory not found: " + path}
			
			var results = []
			var helper = FileSystemHelper.new()
			helper.search_directory(path, pattern, recursive, results)
			
			return {"success": true, "files": results, "count": results.size()}
	}

static func list_directory_tool() -> Dictionary:
	return {
		"name": "list_directory",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			var recursive = params.get("recursive", false)
			
			if not DirAccess.dir_exists_absolute(path):
				return {"success": false, "error": "Directory not found: " + path}
			
			var items = []
			var helper = FileSystemHelper.new()
			helper.list_directory(path, recursive, items)
			
			return {"success": true, "items": items, "count": items.size()}
	}

static func read_text_file_tool() -> Dictionary:
	return {
		"name": "read_text_file",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			
			if not FileAccess.file_exists(path):
				return {"success": false, "error": "File not found: " + path}
			
			var file = FileAccess.open(path, FileAccess.READ)
			if file == null:
				return {"success": false, "error": "Failed to open file"}
			
			var content = file.get_as_text()
			file.close()
			
			return {"success": true, "path": path, "content": content}
	}

static func write_text_file_tool() -> Dictionary:
	return {
		"name": "write_text_file",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			var content = params["content"]
			var append = params.get("append", false)
			
			var file_mode = FileAccess.WRITE
			if append:
				file_mode = FileAccess.READ_WRITE
			
			var file = FileAccess.open(path, file_mode)
			if file == null:
				return {"success": false, "error": "Failed to open file for writing"}
			
			if append:
				file.seek_end()
			
			file.store_string(content)
			file.close()
			
			return {"success": true, "path": path, "bytes": content.length()}
	}

static func copy_file_tool() -> Dictionary:
	return {
		"name": "copy_file",
		"execute": func(params: Dictionary) -> Dictionary:
			var source_path = params["source_path"]
			var destination_path = params["destination_path"]
			var overwrite = params.get("overwrite", false)
			
			if not FileAccess.file_exists(source_path):
				return {"success": false, "error": "Source file not found: " + source_path}
			
			if FileAccess.file_exists(destination_path) and not overwrite:
				return {"success": false, "error": "Destination exists and overwrite=false"}
			
			var source = FileAccess.open(source_path, FileAccess.READ)
			if source == null:
				return {"success": false, "error": "Failed to open source file"}
			
			var dest = FileAccess.open(destination_path, FileAccess.WRITE)
			if dest == null:
				source.close()
				return {"success": false, "error": "Failed to open destination file"}
			
			var buffer_size = 65536
			while source.get_position() < source.get_length():
				var remaining = source.get_length() - source.get_position()
				var chunk = source.get_buffer(min(buffer_size, remaining))
				dest.store_buffer(chunk)
			
			source.close()
			dest.close()
			
			return {"success": true, "source_path": source_path, "destination_path": destination_path}
	}

static func move_file_tool() -> Dictionary:
	return {
		"name": "move_file",
		"execute": func(params: Dictionary) -> Dictionary:
			var source_path = params["source_path"]
			var destination_path = params["destination_path"]
			var overwrite = params.get("overwrite", false)
			
			var copy_result = FileSystemTools.copy_file_tool()["execute"].call({
				"source_path": source_path,
				"destination_path": destination_path,
				"overwrite": overwrite
			})
			
			if not copy_result.get("success", false):
				return copy_result
			
			var err = DirAccess.remove_absolute(source_path)
			if err != OK:
				return {"success": false, "error": "Failed to remove source file: " + str(err)}
			
			return {"success": true, "source_path": source_path, "destination_path": destination_path}
	}

static func delete_file_tool() -> Dictionary:
	return {
		"name": "delete_file",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			var confirm = params.get("confirm", "")
			
			if confirm != "DELETE":
				return {"success": false, "error": "Confirmation missing. Set confirm=DELETE"}
			
			if not FileAccess.file_exists(path):
				return {"success": false, "error": "File not found: " + path}
			
			var err = DirAccess.remove_absolute(path)
			if err != OK:
				return {"success": false, "error": "Failed to delete file: " + str(err)}
			
			return {"success": true, "path": path}
	}

# Helper class for recursive operations
class FileSystemHelper:
	func list_directory(path: String, recursive: bool, results: Array) -> void:
		var dir = DirAccess.open(path)
		if dir == null:
			return
		
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if file_name != "." and file_name != "..":
				var full_path = path.path_join(file_name)
				results.append(full_path)
				if recursive and dir.current_is_dir():
					list_directory(full_path, recursive, results)
			file_name = dir.get_next()
		dir.list_dir_end()

	func remove_recursive(path: String) -> void:
		var dir = DirAccess.open(path)
		if dir:
			dir.list_dir_begin()
			var file_name = dir.get_next()
			while file_name != "":
				if dir.current_is_dir():
					if file_name != "." and file_name != "..":
						remove_recursive(path.path_join(file_name))
				else:
					dir.remove(file_name)
				file_name = dir.get_next()
			dir.list_dir_end()
	
	func search_directory(path: String, pattern: String, recursive: bool, results: Array) -> void:
		var dir = DirAccess.open(path)
		if dir == null:
			return
		
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if dir.current_is_dir():
				if recursive and file_name != "." and file_name != "..":
					search_directory(path.path_join(file_name), pattern, recursive, results)
			else:
				if file_name.match(pattern):
					results.append(path.path_join(file_name))
			file_name = dir.get_next()
		dir.list_dir_end()
