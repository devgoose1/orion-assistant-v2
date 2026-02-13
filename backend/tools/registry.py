"""
Tool Registry - Central registry for all available tools
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class ToolCategory(str, Enum):
    """Categories of tools"""
    FILE_SYSTEM = "file_system"
    APPLICATION = "application"
    DEVICE = "device"
    NETWORK = "network"
    HOMELAB = "homelab"
    SYSTEM = "system"


class ParameterType(str, Enum):
    """Parameter types for validation"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    PATH = "path"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Definition of a tool parameter"""
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    validation_regex: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None


@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    requires_device: bool = True
    requires_permission: bool = True
    permission_type: Optional[str] = None  # 'tool', 'path', 'app'
    dangerous: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for API responses"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type.value,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ],
            "requires_device": self.requires_device,
            "dangerous": self.dangerous
        }


class ToolRegistry:
    """Central registry for all tools"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._initialize_default_tools()
    
    def register(self, tool: Tool) -> None:
        """Register a new tool"""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        print(f"✓ Registered tool: {tool.name}")
    
    def get(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(tool_name)
    
    def list_all(self) -> List[Tool]:
        """List all registered tools"""
        return list(self._tools.values())
    
    def list_by_category(self, category: ToolCategory) -> List[Tool]:
        """List tools by category"""
        return [tool for tool in self._tools.values() if tool.category == category]
    
    def exists(self, tool_name: str) -> bool:
        """Check if a tool exists"""
        return tool_name in self._tools
    
    def _initialize_default_tools(self) -> None:
        """Initialize default tools"""
        
        # File System Tools
        self.register(Tool(
            name="create_directory",
            description="Create a new directory at the specified path",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.PATH,
                    description="Full path where the directory should be created"
                ),
                ToolParameter(
                    name="recursive",
                    type=ParameterType.BOOLEAN,
                    description="Create parent directories if they don't exist",
                    required=False,
                    default=True
                )
            ],
            permission_type="path"
        ))
        
        self.register(Tool(
            name="delete_directory",
            description="Delete a directory and optionally its contents",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.PATH,
                    description="Full path of the directory to delete"
                ),
                ToolParameter(
                    name="recursive",
                    type=ParameterType.BOOLEAN,
                    description="Delete directory contents recursively",
                    required=False,
                    default=False
                )
            ],
            permission_type="path",
            dangerous=True
        ))
        
        self.register(Tool(
            name="search_files",
            description="Search for files matching a pattern in a directory",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.PATH,
                    description="Directory path to search in"
                ),
                ToolParameter(
                    name="pattern",
                    type=ParameterType.STRING,
                    description="Search pattern (e.g., '*.txt', 'readme*')"
                ),
                ToolParameter(
                    name="recursive",
                    type=ParameterType.BOOLEAN,
                    description="Search recursively in subdirectories",
                    required=False,
                    default=True
                )
            ],
            permission_type="path"
        ))

        self.register(Tool(
            name="list_directory",
            description="List files and folders in a directory",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.PATH,
                    description="Directory path to list"
                ),
                ToolParameter(
                    name="recursive",
                    type=ParameterType.BOOLEAN,
                    description="List contents recursively",
                    required=False,
                    default=False
                )
            ],
            permission_type="path"
        ))

        self.register(Tool(
            name="read_text_file",
            description="Read a text file and return its contents",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.PATH,
                    description="Full path of the text file to read"
                )
            ],
            permission_type="path"
        ))

        self.register(Tool(
            name="write_text_file",
            description="Write text to a file (overwrite or append)",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.PATH,
                    description="Full path of the text file to write"
                ),
                ToolParameter(
                    name="content",
                    type=ParameterType.STRING,
                    description="Text content to write"
                ),
                ToolParameter(
                    name="append",
                    type=ParameterType.BOOLEAN,
                    description="Append to the file instead of overwriting",
                    required=False,
                    default=False
                )
            ],
            permission_type="path"
        ))

        self.register(Tool(
            name="copy_file",
            description="Copy a file to a new path",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="source_path",
                    type=ParameterType.PATH,
                    description="Full path of the source file"
                ),
                ToolParameter(
                    name="destination_path",
                    type=ParameterType.PATH,
                    description="Full path of the destination file"
                ),
                ToolParameter(
                    name="overwrite",
                    type=ParameterType.BOOLEAN,
                    description="Overwrite the destination if it exists",
                    required=False,
                    default=False
                )
            ],
            permission_type="path"
        ))

        self.register(Tool(
            name="move_file",
            description="Move or rename a file",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="source_path",
                    type=ParameterType.PATH,
                    description="Full path of the source file"
                ),
                ToolParameter(
                    name="destination_path",
                    type=ParameterType.PATH,
                    description="Full path of the destination file"
                ),
                ToolParameter(
                    name="overwrite",
                    type=ParameterType.BOOLEAN,
                    description="Overwrite the destination if it exists",
                    required=False,
                    default=False
                )
            ],
            permission_type="path"
        ))

        self.register(Tool(
            name="delete_file",
            description="Delete a file (requires explicit confirmation)",
            category=ToolCategory.FILE_SYSTEM,
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.PATH,
                    description="Full path of the file to delete"
                ),
                ToolParameter(
                    name="confirm",
                    type=ParameterType.STRING,
                    description="Type DELETE to confirm deletion"
                )
            ],
            permission_type="path",
            dangerous=True
        ))
        
        # Application Tools
        self.register(Tool(
            name="open_app",
            description="Open an application on the device",
            category=ToolCategory.APPLICATION,
            parameters=[
                ToolParameter(
                    name="app_name",
                    type=ParameterType.STRING,
                    description="Name of the application to open"
                ),
                ToolParameter(
                    name="arguments",
                    type=ParameterType.ARRAY,
                    description="Optional command-line arguments",
                    required=False,
                    default=[]
                )
            ],
            permission_type="app"
        ))
        
        self.register(Tool(
            name="close_app",
            description="Close a running application",
            category=ToolCategory.APPLICATION,
            parameters=[
                ToolParameter(
                    name="app_name",
                    type=ParameterType.STRING,
                    description="Name of the application to close"
                )
            ],
            permission_type="app"
        ))
        
        # Device Information Tools
        self.register(Tool(
            name="get_device_info",
            description="Get information about the device including OS name, version, hardware specs. Use this to determine the operating system when you need to construct file paths (e.g., finding the Desktop folder location).",
            category=ToolCategory.DEVICE,
            parameters=[
                ToolParameter(
                    name="include_hardware",
                    type=ParameterType.BOOLEAN,
                    description="Include detailed hardware information",
                    required=False,
                    default=True
                )
            ],
            requires_permission=False
        ))
        
        self.register(Tool(
            name="get_running_processes",
            description="Get list of running processes on the device",
            category=ToolCategory.DEVICE,
            parameters=[],
            requires_permission=False
        ))
        
        print(f"✓ Initialized {len(self._tools)} default tools")


# Global registry instance
_registry = None

def get_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
