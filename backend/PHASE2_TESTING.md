# Phase 2: LLM Tool Calling - Testing Guide

## 🎯 Overview

Phase 2 integreert tool calling in de LLM conversatie. De LLM kan nu zelfstandig beslissen om tools te gebruiken en krijgt de resultaten terug in de conversatie context.

## 🏗️ Architecture

```text
User Message
    ↓
LLM (with tool schema in system prompt)
    ↓
Response with tool_call JSON?
    ├─ NO  → Stream response to client → DONE
    └─ YES → Parse tool call
              ↓
         Execute tool on device
              ↓
         Get tool result
              ↓
         Add result to conversation
              ↓
         LLM generates new response
              ↓
         (Loop max 5 times)
              ↓
         Stream final response to client
```

## 🧪 Testing Scenarios

### Test 1: Simple Tool Call - Create Directory

**User:** "Create a folder called TestLLM on my desktop"

**Expected Flow:**

1. LLM responds with tool_call JSON for `create_directory`
2. Backend executes tool on client device
3. Tool creates `C:/Users/njsch/Desktop/TestLLM`
4. Tool result goes back to LLM
5. LLM responds: "I've created the folder TestLLM on your desktop"

**Check:**

- [ ] Folder created on desktop
- [ ] UI shows "🔧 Executing tool: create_directory"
- [ ] UI shows "✓ Tool executed: create_directory"
- [ ] LLM provides natural language confirmation

### Test 2: Tool Call With Parameters - Search Files

**User:** "Find all txt files on my desktop"

**Expected Flow:**

1. LLM calls `search_files` with path="C:/Users/njsch/Desktop", pattern="*.txt"
2. Tool searches and returns list of files
3. LLM responds with natural language listing the files found

**Check:**

- [ ] Tool executes with correct parameters
- [ ] LLM mentions specific files found (or says none found)

### Test 3: Information Gathering - Device Info

**User:** "What operating system am I running?"

**Expected Flow:**

1. LLM calls `get_device_info`
2. Tool returns OS info
3. LLM responds: "You're running Windows 11" (or similar)

**Check:**

- [ ] Tool executes
- [ ] LLM incorporates device info in natural language

### Test 4: Application Control

**User:** "Open notepad"

**Expected Flow:**

1. LLM calls `open_app` with app_name="notepad"
2. Tool launches notepad.exe
3. LLM confirms: "I've opened Notepad for you"

**Check:**

- [ ] Notepad actually opens
- [ ] Natural language confirmation

### Test 5: No Tool Needed

**User:** "Hello, how are you?"

**Expected Flow:**

1. LLM responds directly without tool calls
2. Normal conversation

**Check:**

- [ ] No tool execution
- [ ] Direct response streaming

### Test 6: Multi-Step (Future Enhancement)

**User:** "Create a folder called Projects on my desktop, then search for all Python files in my Documents"

**Expected:**

- Currently: LLM will do ONE tool at a time
- Future: Support chaining multiple tools

## 🚀 How to Test

### 1. Start Backend

```bash
cd backend
python main.py
```

### 2. Start Godot Client

- Open `client/project.godot`
- Press F5 to run
- Check "Device registered successfully" appears

### 3. Send Test Messages

Type in the chat UI:

- "Create a folder called AITest on my desktop"
- "What files are on my desktop?"
- "What OS am I using?"
- "Open calculator"

### 4. Check Logs

**Backend Console:**

```text
📝 LLM Request:
   Iteration 1: Streaming...
   🔧 Tool call detected: create_directory
   ✓ Tool result: success
   Iteration 2: Streaming...
   ✓ No tool call detected, finishing
```

**Godot Console:**

```text
Tool execution request: create_directory
Parameters: {path: C:/Users/njsch/Desktop/AITest}
LLM is executing tool: create_directory
```

**UI Chat:**

```text
You: Create a folder called AITest on my desktop
🔧 Executing tool: create_directory with params: {"path":"C:/Users/njsch/Desktop/AITest"}
✓ Tool executed: create_directory - {"success":true,"path":"..."}
Assistant: I've created the folder AITest on your desktop.
```

## 🐛 Troubleshooting

### LLM doesn't call tools

**Cause:** System prompt not being used or LLM doesn't understand format

**Fix:**

- Check `generate_system_prompt()` output
- Try more explicit prompts: "Use the create_directory tool to make a folder"

### Tool call detected but not executing

**Check:**

- Device permissions in database (`allowed_tools`)
- Tool name matches registry
- Parameters are valid

### Infinite loop / max iterations

**Cause:** LLM keeps generating tool calls

**Fix:**

- Check max_tool_iterations in main.py (currently 5)
- Improve system prompt instructions

### Tool result not going back to LLM

**Check:**

- `add_message_to_conversation()` being called with tool result
- Conversation context in `conversations` dictionary
- Session ID consistency

### Tool result times out even though device replied

**Cause:** WebSocket receive loop was blocked by the LLM tool loop.

**Fix:** LLM processing now runs in a background task with its own DB session, so tool results are handled immediately.

### LLM responds without tool_call JSON

**Cause:** Model occasionally answers with text instead of a tool call.

**Fix:** One-time strict retry forces a JSON-only tool response when the prompt requires a tool.

### Permission denied for allowed paths on Windows

**Cause:** Mixed path separators or casing mismatches caused false negatives.

**Fix:** Path normalization now handles separators and casing consistently.

## 📊 Success Criteria

✅ **Phase 2 Complete When:**

- [ ] LLM can call all 7 tools based on natural language requests
- [ ] Tool results are incorporated in LLM responses  
- [ ] UI shows tool execution feedback
- [ ] Conversation context maintains history
- [ ] No errors in streaming with tool calls
- [ ] System remains stable after multiple tool executions

## ✅ Recent Verification (2026-02-13)

- LLM calls `get_device_info` and receives tool result without timeouts
- Tool results immediately trigger the waiting event
- Permission checks accept Windows paths with backslashes
- LLM retries with strict JSON when it fails to emit a tool_call

## 🎓 Key Learnings

1. **System Prompt is Critical** - Tool schema must be clear and follow exact format
2. **Conversation Context** - Tool results must be added to maintain flow
3. **Streaming + Tool Calling** - Buffer complete response before parsing for tools
4. **Iteration Limit** - Prevent infinite loops with max iterations
5. **UI Feedback** - Show user what's happening during tool execution

## 🔮 Future Enhancements

- **Multi-tool chaining** - Execute multiple tools in sequence
- **Tool call streaming** - Show tool call as it's being generated
- **Parallel tools** - Run independent tools simultaneously  
- **Retry logic** - Retry failed tools automatically
- **Permission UI** - Ask user to approve tool executions
- **Tool result formatting** - Better presentation in conversation
