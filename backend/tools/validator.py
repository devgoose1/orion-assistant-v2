"""
Tool Validator - Validates tool parameters and permissions
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import re

from .registry import Tool, ToolParameter, ParameterType
from services.device_service import check_device_permission, check_path_allowed


class ValidationError(Exception):
    """Raised when tool validation fails"""
    pass


class ToolValidator:
    """Validates tool execution requests"""
    
    @staticmethod
    def validate_parameters(tool: Tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool parameters against tool definition.
        Returns validated parameters with defaults applied.
        """
        validated = {}
        
        for param_def in tool.parameters:
            param_name = param_def.name
            param_value = parameters.get(param_name)
            
            # Check required parameters
            if param_def.required and param_value is None:
                raise ValidationError(f"Required parameter '{param_name}' is missing")
            
            # Use default if not provided
            if param_value is None:
                param_value = param_def.default
            
            # Skip validation for None values (optional parameters)
            if param_value is None:
                continue
            
            # Type validation
            param_value = ToolValidator._validate_type(param_name, param_value, param_def)
            
            # Additional validation
            if param_def.validation_regex:
                ToolValidator._validate_regex(param_name, param_value, param_def.validation_regex)
            
            if param_def.min_value is not None or param_def.max_value is not None:
                ToolValidator._validate_range(param_name, param_value, param_def.min_value, param_def.max_value)
            
            validated[param_name] = param_value
        
        # Check for unknown parameters
        unknown_params = set(parameters.keys()) - {p.name for p in tool.parameters}
        if unknown_params:
            raise ValidationError(f"Unknown parameters: {', '.join(unknown_params)}")
        
        return validated
    
    @staticmethod
    def _validate_type(param_name: str, value: Any, param_def: ToolParameter) -> Any:
        """Validate parameter type"""
        expected_type = param_def.type
        
        if expected_type == ParameterType.STRING:
            if not isinstance(value, str):
                raise ValidationError(f"Parameter '{param_name}' must be a string")
            return value
        
        elif expected_type == ParameterType.INTEGER:
            if not isinstance(value, int):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    raise ValidationError(f"Parameter '{param_name}' must be an integer")
            return value
        
        elif expected_type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'yes'):
                        return True
                    elif value.lower() in ('false', '0', 'no'):
                        return False
                raise ValidationError(f"Parameter '{param_name}' must be a boolean")
            return value
        
        elif expected_type == ParameterType.PATH:
            if not isinstance(value, str):
                raise ValidationError(f"Parameter '{param_name}' must be a path string")
            # Basic path validation
            if not value or value.strip() == "":
                raise ValidationError(f"Parameter '{param_name}' cannot be an empty path")
            return value
        
        elif expected_type == ParameterType.ARRAY:
            if not isinstance(value, list):
                raise ValidationError(f"Parameter '{param_name}' must be an array")
            return value
        
        elif expected_type == ParameterType.OBJECT:
            if not isinstance(value, dict):
                raise ValidationError(f"Parameter '{param_name}' must be an object")
            return value
        
        return value
    
    @staticmethod
    def _validate_regex(param_name: str, value: str, pattern: str) -> None:
        """Validate parameter against regex pattern"""
        if not re.match(pattern, value):
            raise ValidationError(f"Parameter '{param_name}' does not match required pattern")
    
    @staticmethod
    def _validate_range(param_name: str, value: int, min_val: Optional[int], max_val: Optional[int]) -> None:
        """Validate parameter is within range"""
        if min_val is not None and value < min_val:
            raise ValidationError(f"Parameter '{param_name}' must be at least {min_val}")
        if max_val is not None and value > max_val:
            raise ValidationError(f"Parameter '{param_name}' must be at most {max_val}")
    
    @staticmethod
    def validate_permissions(db: Session, device_id: str, tool: Tool, parameters: Dict[str, Any]) -> None:
        """
        Validate device has permission to execute tool.
        Raises ValidationError if permission check fails.
        """
        if not tool.requires_permission:
            return  # Tool doesn't require permission
        
        permission_type = tool.permission_type
        
        if permission_type == "tool":
            # Check tool permission
            if not check_device_permission(db, device_id, tool.name):
                raise ValidationError(f"Device '{device_id}' does not have permission to use tool '{tool.name}'")
        
        elif permission_type == "path":
            # Check path permission
            path = parameters.get("path")
            if path and not check_path_allowed(db, device_id, path):
                raise ValidationError(f"Device '{device_id}' does not have permission to access path '{path}'")
        
        elif permission_type == "app":
            # Check app permission
            app_name = parameters.get("app_name")
            if app_name:
                # Check if app is in allowed_apps list
                if not check_device_permission(db, device_id, app_name, permission_type="app"):
                    raise ValidationError(f"Device '{device_id}' does not have permission to access app '{app_name}'")
    
    @staticmethod
    def validate_tool_request(db: Session, device_id: str, tool: Tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete validation: parameters + permissions.
        Returns validated parameters.
        """
        # Validate parameters
        validated_params = ToolValidator.validate_parameters(tool, parameters)
        
        # Validate permissions
        ToolValidator.validate_permissions(db, device_id, tool, validated_params)
        
        return validated_params
