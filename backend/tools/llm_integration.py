"""
LLM Tool Integration
Provides functionality for integrating tools with LLM conversations
"""
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from .registry import get_registry, Tool, ParameterType

def generate_tool_schema_for_llm() -> str:
    """
    Generate a formatted tool schema that can be included in the LLM system prompt.
    Returns a text description of all available tools.
    """
    registry = get_registry()
    tools = registry.list_all()
    
    if not tools:
        return "No tools available."
    
    schema_parts = [
        "# Available Tools",
        "",
        "You have access to the following tools. To use a tool, respond with a JSON block in this exact format:",
        "",
        "```json",
        "{",
        '  "tool_call": {',
        '    "tool_name": "tool_name_here",',
        '    "parameters": {',
        '      "param1": "value1",',
        '      "param2": "value2"',
        "    }",
        "  }",
        "}",
        "```",
        "",
        "## Tools:",
        ""
    ]
    
    for tool in tools:
        # Tool header
        schema_parts.append(f"### {tool.name}")
        schema_parts.append(f"**Category:** {tool.category.value}")
        schema_parts.append(f"**Description:** {tool.description}")
        schema_parts.append("")
        
        # Parameters
        if tool.parameters:
            schema_parts.append("**Parameters:**")
            for param in tool.parameters:
                required = " (required)" if param.required else " (optional)"
                param_type = param.type.value
                schema_parts.append(f"- `{param.name}` ({param_type}){required}: {param.description}")
                if param.default is not None:
                    schema_parts.append(f"  - Default: `{param.default}`")
            schema_parts.append("")
        
        # Example
        schema_parts.append("**Example:**")
        example_params = {}
        for param in tool.parameters:
            if param.required:
                # Generate example value based on type
                if param.type == ParameterType.STRING:
                    if param.name == "path":
                        example_params[param.name] = "C:/Users/Example/Documents"
                    elif param.name == "app_name":
                        example_params[param.name] = "notepad"
                    elif param.name == "pattern":
                        example_params[param.name] = "*.txt"
                    else:
                        example_params[param.name] = f"example_{param.name}"
                elif param.type == ParameterType.BOOLEAN:
                    example_params[param.name] = False
                elif param.type == ParameterType.INTEGER:
                    example_params[param.name] = 0
                elif param.type == ParameterType.ARRAY:
                    example_params[param.name] = []
        
        schema_parts.append("```json")
        schema_parts.append("{")
        schema_parts.append('  "tool_call": {')
        schema_parts.append(f'    "tool_name": "{tool.name}",')
        schema_parts.append('    "parameters": {')
        param_lines = [f'      "{k}": "{v}"' if isinstance(v, str) else f'      "{k}": {str(v).lower()}' 
                      for k, v in example_params.items()]
        schema_parts.append(',\n'.join(param_lines))
        schema_parts.append('    }')
        schema_parts.append('  }')
        schema_parts.append('}')
        schema_parts.append("```")
        schema_parts.append("")
        schema_parts.append("---")
        schema_parts.append("")
    
    return "\n".join(schema_parts)


def generate_system_prompt() -> str:
    """
    Generate the complete system prompt for the LLM, including tool descriptions.
    """
    tool_schema = generate_tool_schema_for_llm()
    
    system_prompt = f"""You are Orion Assistant, a helpful AI assistant that can perform actions on user devices.

You have access to various tools that allow you to interact with the user's system. You MUST use these tools proactively when appropriate.

CRITICAL RULES FOR TOOL USAGE:
1. If a user asks you to perform an action that requires a tool, USE THE TOOL IMMEDIATELY - do NOT ask for more information first
2. If you need information to complete a task, use get_device_info to gather it automatically
3. The get_device_info tool returns desktop_path, home_directory, and other useful paths - use these directly
4. ALWAYS respond with a tool call JSON when a tool is needed - do not ask the user for paths or details you can discover yourself
5. For any OS/device questions (e.g., "What operating system am I running?"), call get_device_info first

EXAMPLE WORKFLOW for "Create a folder called TestFolder on my desktop":
Step 1 - First request:
```json
{{
  "tool_call": {{
    "tool_name": "get_device_info",
    "parameters": {{}}
  }}
}}
```

Step 2 - After receiving device info with desktop_path "C:/Users/John/Desktop":
```json
{{
  "tool_call": {{
    "tool_name": "create_directory", 
    "parameters": {{
      "path": "C:/Users/John/Desktop/TestFolder"
    }}
  }}
}}
```

Step 3 - After successful creation:
"I've created the TestFolder on your desktop."

When you decide to use a tool:
- Respond with the tool_call JSON format IMMEDIATELY
- You may include brief explanatory text with the JSON
- The backend will execute the tool and provide you with the result
- After receiving the result, provide a natural language response to the user

{tool_schema}

Remember: 
- Use the EXACT JSON format shown above for tool calls
- Be PROACTIVE - use tools without asking for information you can discover
- You can call ONE tool at a time, wait for the result, then decide the next action
- Always provide a friendly confirmation after successful tool execution
"""
    
    return system_prompt


def parse_tool_call_from_response(response: str) -> Optional[Dict[str, Any]]:
    """
    Parse an LLM response to extract tool call information.
    
    Returns:
        Dictionary with tool_name and parameters if a tool call is detected, None otherwise.
        Format: {"tool_name": "...", "parameters": {...}}
    """
    # Try to find JSON code block first
    json_pattern = r'```json\s*(\{.*?\})\s*```'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    if matches:
        for match in matches:
            try:
                data = json.loads(match)
                if "tool_call" in data:
                    tool_call = data["tool_call"]
                    if "tool_name" in tool_call and "parameters" in tool_call:
                        return {
                            "tool_name": tool_call["tool_name"],
                            "parameters": tool_call["parameters"]
                        }
            except json.JSONDecodeError:
                continue
    
    # Try to find JSON without code block markers - more flexible approach
    # Look for anything that starts with { and contains "tool_call"
    try:
        # Find all potential JSON objects in the response
        brace_depth = 0
        json_start = -1
        
        for i, char in enumerate(response):
            if char == '{':
                if brace_depth == 0:
                    json_start = i
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth == 0 and json_start >= 0:
                    # Complete JSON object found
                    json_str = response[json_start:i+1]
                    if "tool_call" in json_str:
                        try:
                            data = json.loads(json_str)
                            if "tool_call" in data:
                                tool_call = data["tool_call"]
                                if "tool_name" in tool_call and "parameters" in tool_call:
                                    return {
                                        "tool_name": tool_call["tool_name"],
                                        "parameters": tool_call["parameters"]
                                    }
                        except json.JSONDecodeError:
                            pass
                    json_start = -1
    except Exception:
        pass
    
    return None


def extract_text_and_tool_call(response: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extract both the text message and tool call from an LLM response.
    
    Returns:
        Tuple of (message_text, tool_call_dict or None)
    """
    tool_call = parse_tool_call_from_response(response)
    
    if tool_call:
        # Remove the JSON from the response to get just the text
        # Remove ```json ... ``` blocks
        text = re.sub(r'```json\s*\{.*?\}\s*```', '', response, flags=re.DOTALL)
        
        # Remove standalone JSON objects containing tool_call
        # Use the same brace-counting approach to find and remove the JSON
        result_text = []
        brace_depth = 0
        json_start = -1
        skip_until = -1
        
        for i, char in enumerate(response):
            if i < skip_until:
                continue
                
            if char == '{':
                if brace_depth == 0:
                    json_start = i
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth == 0 and json_start >= 0:
                    # Check if this JSON contains tool_call
                    json_str = response[json_start:i+1]
                    if "tool_call" in json_str:
                        try:
                            json.loads(json_str)
                            # Valid JSON with tool_call - skip it
                            skip_until = i + 1
                            json_start = -1
                            continue
                        except json.JSONDecodeError:
                            pass
                    json_start = -1
            
            # Add character to result if we're not skipping
            if skip_until <= i:
                result_text.append(char)
        
        text = ''.join(result_text).strip()
        return (text, tool_call)
    
    return (response, None)


def format_tool_result_for_llm(tool_name: str, success: bool, result: Any, error: Optional[str] = None) -> str:
    """
    Format a tool execution result for inclusion in the LLM conversation context.
    
    Returns:
        A formatted string describing the tool result
    """
    if success:
        if tool_name == "get_device_info" and isinstance(result, dict):
            info = result.get("info") if isinstance(result.get("info"), dict) else None
            if info and isinstance(info.get("os_name"), str) and isinstance(info.get("os_version"), str):
                if info["os_name"].lower().startswith("windows"):
                    info["os_friendly_name"] = _windows_friendly_name(info["os_version"])
        result_text = f"Tool '{tool_name}' executed successfully.\n"
        if result:
            result_text += f"Result: {json.dumps(result, indent=2)}"
        return result_text
    else:
        error_text = f"Tool '{tool_name}' failed.\n"
        if error:
            error_text += f"Error: {error}"
        return error_text


def _windows_friendly_name(os_version: str) -> str:
    """Return a friendly Windows release name based on build number."""
    build = _parse_windows_build(os_version)
    if build is None:
        return "Windows (version unknown)"
    if build >= 22000:
        return f"Windows 11 (build {build})"
    return f"Windows 10 (build {build})"


def _parse_windows_build(os_version: str) -> Optional[int]:
    """Extract build number from a version string like '10.0.26200'."""
    parts = os_version.split(".")
    if not parts:
        return None
    try:
        return int(parts[-1])
    except ValueError:
        return None


if __name__ == "__main__":
    # Test the schema generation
    print(generate_system_prompt())
