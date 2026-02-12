extends RefCounted

class_name FileSystemTools

static func create_directory_tool() -> Dictionary:
	return {
		"name": "create_directory",
		"execute": func(params: Dictionary) -> Dictionary:
			var path = params["path"]
			
			var dir = DirAccess.open(path.get_base_dir())
			if dir == null:
				return {"success": false, "error": "Parent directory not found"}
			
			var err = dir.make_dir_recursive(path)
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
				_remove_recursive(path)
			
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
			
			var results = []
			_search_directory(path, pattern, recursive, results)
			
			return {"success": true, "files": results, "count": results.size()}
	}

static func _remove_recursive(path: String) -> void:
	var dir = DirAccess.open(path)
	if dir:
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if dir.current_is_dir():
				if file_name != "." and file_name != "..":
					_remove_recursive(path.path_join(file_name))
			else:
				dir.remove(file_name)
			file_name = dir.get_next()
		dir.list_dir_end()

static func _search_directory(path: String, pattern: String, recursive: bool, results: Array) -> void:
	var dir = DirAccess.open(path)
	if dir == null:
		return
	
	dir.list_dir_begin()
	var file_name = dir.get_next()
	while file_name != "":
		if dir.current_is_dir():
			if recursive and file_name != "." and file_name != "..":
				_search_directory(path.path_join(file_name), pattern, recursive, results)
		else:
			if file_name.match(pattern):
				results.append(path.path_join(file_name))
		file_name = dir.get_next()
	dir.list_dir_end()
