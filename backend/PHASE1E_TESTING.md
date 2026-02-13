# Phase 1E: New File Tools - Testing Guide

## 📋 Overview

Phase 1E adds 6 powerful new file manipulation tools: `list_directory`, `read_text_file`, `write_text_file`, `copy_file`, `move_file`, and `delete_file`.

**New Tools:**

- ✅ list_directory - List directory contents
- ✅ read_text_file - Read file contents
- ✅ write_text_file - Create/append to files
- ✅ copy_file - Copy files with overwrite protection
- ✅ move_file - Move/rename files
- ✅ delete_file - Delete files (with confirmation safety)

## 🚀 Quick Start

### Option 1: Automated Test Script

```bash
cd backend
python main.py  # Start backend in one terminal

# In another terminal:
cd backend
python test_file_tools.py  # Run comprehensive test
```

The script will:

1. Wait for device connection
2. Create a test file on desktop
3. Read it back
4. Append content
5. Copy the file
6. List directory
7. Move/rename the copy
8. Test delete safety (confirm required)
9. Clean up

### Option 2: Manual LLM-based Testing (via Chat UI)

Start backend and client, then send these prompts in the chat:

#### Test 1: Create and Read

**Prompt:** "Create a test.md file on my desktop with the content 'Hello from LLM!', then read it back"

**Expected:**

- LLM calls `write_text_file`
- LLM calls `read_text_file`
- Chat shows file contents

#### Test 2: List Directory

**Prompt:** "What files are on my desktop?"

**Expected:**

- LLM calls `list_directory` on desktop
- Lists files found

#### Test 3: Copy File

**Prompt:** "Copy test.md to test_backup.md on my desktop"

**Expected:**

- LLM calls `copy_file` with overwrite=false
- Both files exist after

#### Test 4: Move/Rename

**Prompt:** "Rename test_backup.md to test_archive.md"

**Expected:**

- LLM calls `move_file`
- Old name gone, new name exists

#### Test 5: Delete Safety

**Prompt:** "Delete test_archive.md"

**Expected:**

- First attempt: LLM tries without `confirm="DELETE"` → fails
- LLM retries with `confirm="DELETE"` parameter
- File deleted

#### Test 6: Multi-step

**Prompt:** "Create a notes.txt file with 'Task 1: Test tools' on my desktop, then copy it to Documents"

**Expected:**

- LLM creates the file
- LLM copies to Documents folder
- Both files exist

## 🔒 Security Features

### Path Safety

- All tools check against `allowed_paths` (database permissions)
- Respects Windows/Linux path conventions
- Mixed separators handled gracefully

### Delete Safety

- `delete_file` requires explicit `confirm="DELETE"` parameter
- Blocks deletion of root paths (C:/, /root, etc.)
- LLM will retry automatically if confirmation missing

### Copy/Move Overwrite

- Default `overwrite=false` - errors if destination exists
- Set `overwrite=true` explicitly to allow replacement

## 📊 Tool Parameters

| Tool | Parameters | Notes |
| --- | --- | --- |
| `list_directory` | path, recursive? | Returns array of file/folder paths |
| `read_text_file` | path | Returns file contents as string |
| `write_text_file` | path, content, append? | append=true adds to end |
| `copy_file` | source_path, destination_path, overwrite? | Default: no overwrite |
| `move_file` | source_path, destination_path, overwrite? | Works across volumes |
| `delete_file` | path, confirm="DELETE" | Confirmation required |

## 🧪 Expected Behavior

### Success Case

```text
User: "Read content of test.txt on my desktop"
  ↓
LLM: Calls read_text_file(path="C:.../Desktop/test.txt")
  ↓
Tool: Returns {"success": true, "content": "..."}
  ↓
LLM: "Here's the content of test.txt: ..."
```

### Permission Denied

```text
LLM tries: write_text_file(path="C:/Windows/System32/test.txt")
  ↓
Router: Permission check fails
  ↓
LLM receives: {"success": false, "message": "...does not have permission..."}
  ↓
LLM: "I don't have permission to write there"
```

### Delete with Safety

```text
User: "Delete test.txt"
  ↓
LLM: Tries delete_file(path="...", confirm="")
  ↓
Router: Validation error - confirm missing
  ↓
LLM receives: {"success": false, "message": "confirm=DELETE"}
  ↓
Forced retry: LLM adds confirm="DELETE"
  ↓
File deleted ✓
```

## ✅ Verification Checklist

- [ ] **list_directory** works, returns file array
- [ ] **read_text_file** returns correct content
- [ ] **write_text_file** creates files correctly
- [ ] **write_text_file** with append=true adds content
- [ ] **copy_file** without overwrite=true rejects existing files
- [ ] **copy_file** with overwrite=true replaces files
- [ ] **move_file** renames files successfully
- [ ] **delete_file** requires confirm="DELETE"
- [ ] **delete_file** blocks execution if confirm missing
- [ ] LLM integrates all tools into natural workflows
- [ ] Path permissions enforced correctly
- [ ] No unintended file modifications

## 🐛 Troubleshooting

### "Directory not found"

Check that the path exists and has proper separators for the OS.

### "Does not have permission"

Device doesn't have this path in `allowed_paths`. Check database permissions or requests to expand allowed_paths.

### "Confirmat ion missing" (delete_file)

Normal behavior - LLM should retry with `confirm="DELETE"`. If it doesn't, check the system prompt.

### File not deleted despite confirm="DELETE"

- Check file isn't open in another application
- Check file permissions (read-only?)
- Check path isn't a root/system directory (blocked for safety)

## 📈 Success Metrics

✅ **Phase 1E Complete When:**

- [ ] All 6 file tools execute successfully via HTTP test endpoint
- [ ] LLM calls tools appropriately based on natural language
- [ ] Permission system blocks unauthorized paths
- [ ] Delete safety (confirm parameter) works
- [ ] Copy/move with overwrite protection works
- [ ] Multi-step workflows work (create → read, copy → delete, etc.)
- [ ] No errors in backend or client logs
- [ ] Conversation context maintains file operation state

## 🔮 Future Enhancements

- **Batch operations:** Delete multiple files with single call
- **File metadata:** Get file size, modified date via separate tool
- **Permission UI:** Visual prompt for user approval before delete
- **Bulk copy:** Copy entire directories
- **Text search:** Search within file contents
- **File templates:** Create files from templates

---

**Last Updated:** 2026-02-13  
**Test Script:** `backend/test_file_tools.py`
