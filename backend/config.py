"""
Configuration and constants for Orion Assistant backend
"""

# LLM Configuration
DEFAULT_OLLAMA_MODEL = "gpt-oss:120b"
DEFAULT_OLLAMA_URL = "https://ollama.com"
CONVERSATION_HISTORY_LIMIT = 20
MAX_TOOL_ITERATIONS = 5
TOOL_EXECUTION_TIMEOUT = 10.0  # seconds

# Tool Execution
TOOL_HEURISTIC_PHRASES = {
    # File operations
    "create a folder",
    "create folder",
    "make a folder",
    "create directory",
    "make directory",
    "read file",
    "read content",
    "write file",
    "write content",
    "copy file",
    "list files",
    "search files",
    "move file",
    "delete file",
    # System info
    "operating system",
    "what os",
    "which os",
    "os am i",
    # Application control
    "open app",
    "open application",
    "close app",
    "close application",
    "launch",
    "quit",
    "start",
}

# Message types
MESSAGE_TYPE_LLM_RESPONSE_CHUNK = "llm_response_chunk"
MESSAGE_TYPE_LLM_RESPONSE = "llm_response"
MESSAGE_TYPE_TOOL_EXECUTE = "tool_execute"
MESSAGE_TYPE_TOOL_EXECUTING = "tool_executing"
MESSAGE_TYPE_TOOL_RESULT = "tool_result"
MESSAGE_TYPE_DEVICE_REGISTER = "device_register"
MESSAGE_TYPE_DEVICE_HEARTBEAT = "device_heartbeat"
MESSAGE_TYPE_GET_TOOLS = "get_tools"
MESSAGE_TYPE_ERROR = "error"

# Default device permissions
DEFAULT_ALLOWED_TOOLS = [
    # File system
    "create_directory",
    "delete_directory",
    "search_files",
    "list_directory",
    "read_text_file",
    "write_text_file",
    "copy_file",
    "move_file",
    "delete_file",
    # Applications
    "open_app",
    "close_app",
    # Device
    "get_device_info",
    "get_running_processes",
]

DEFAULT_ALLOWED_PATHS = [
    "C:/Users",
    "D:/Projects",
    "/home",
    "/Users",
]

DEFAULT_ALLOWED_APPS = [
    "notepad",
    "calculator",
    "chrome",
    "firefox",
    "edge",
    "terminal",
    "cmd",
]

# Status codes
STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"

# Logging
LOG_PREFIX_DEVICE = "📱"
LOG_PREFIX_LLM = "📝"
LOG_PREFIX_TOOL = "🔧"
LOG_PREFIX_ITER = "🔄"
LOG_PREFIX_SUCCESS = "✓"
LOG_PREFIX_ERROR = "✗"
LOG_PREFIX_WAIT = "⏳"
LOG_PREFIX_RESULT = "🧾"
LOG_PREFIX_ALERT = "⚠️"
LOG_PREFIX_CHECK = "✅"
