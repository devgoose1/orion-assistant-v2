"""
Tool Router - Routes tool execution requests to appropriate devices
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json

from .registry import get_registry, Tool
from .validator import ToolValidator, ValidationError
from services.tool_execution_service import log_tool_execution


class ToolRouter:
    """Routes and manages tool execution"""
    
    def __init__(self):
        self.registry = get_registry()
        self.validator = ToolValidator()
    
    async def execute_tool(
        self,
        db: Session,
        device_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        websocket_send_func
    ) -> Dict[str, Any]:
        """
        Execute a tool request:
        1. Validate tool exists
        2. Validate parameters
        3. Validate permissions
        4. Route to device
        5. Log execution
        
        Returns execution result or error
        """
        execution_id = None
        
        try:
            # Get tool definition
            tool = self.registry.get(tool_name)
            if not tool:
                raise ValidationError(f"Tool '{tool_name}' not found")
            
            # Validate parameters and permissions
            validated_params = self.validator.validate_tool_request(
                db, device_id, tool, parameters
            )
            
            # Create execution log
            execution = log_tool_execution(
                db=db,
                execution_data={
                    'device_id': device_id,
                    'tool_name': tool_name,
                    'parameters': validated_params,
                    'success': None,
                    'executed_at': datetime.now()
                }
            )
            execution_id = execution.id
            
            # Route to device
            command = {
                "type": "tool_execute",
                "execution_id": execution_id,
                "tool_name": tool_name,
                "parameters": validated_params,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to device
            success = await websocket_send_func(device_id, command)
            
            if not success:
                raise Exception(f"Failed to send command to device '{device_id}'")
            
            return {
                "success": True,
                "execution_id": execution_id,
                "message": f"Tool '{tool_name}' execution started on device '{device_id}'"
            }
        
        except ValidationError as e:
            # Log validation failure
            if execution_id is not None:
                from services.tool_execution_service import get_tool_execution
                execution = get_tool_execution(db, str(execution_id))
                if execution:
                    setattr(execution, 'success', False)
                    setattr(execution, 'error_message', str(e))
                    db.commit()
            
            return {
                "success": False,
                "error": "validation_error",
                "message": str(e)
            }
        
        except Exception as e:
            # Log execution failure
            if execution_id is not None:
                from services.tool_execution_service import get_tool_execution
                execution = get_tool_execution(db, str(execution_id))
                if execution:
                    setattr(execution, 'success', False)
                    setattr(execution, 'error_message', str(e))
                    db.commit()
            
            return {
                "success": False,
                "error": "execution_error",
                "message": str(e)
            }
    
    def handle_tool_result(
        self,
        db: Session,
        execution_id: int,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Handle tool execution result from device.
        Updates execution log with final status.
        """
        from services.tool_execution_service import get_tool_execution
        execution = get_tool_execution(db, str(execution_id))
        if execution:
            setattr(execution, 'success', success)
            if result:
                setattr(execution, 'result', result)
            if error:
                setattr(execution, 'error_message', error)
            db.commit()
    
    def get_available_tools(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of available tools.
        Optionally filter by device permissions.
        """
        tools = self.registry.list_all()
        
        return {
            "tools": [tool.to_dict() for tool in tools],
            "count": len(tools),
            "categories": list(set(tool.category.value for tool in tools))
        }


# Global router instance
_router = None

def get_router() -> ToolRouter:
    """Get the global tool router instance"""
    global _router
    if _router is None:
        _router = ToolRouter()
    return _router
