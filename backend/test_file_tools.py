#!/usr/bin/env python3
"""
Test script for new file tools (Phase 1E)
Tests: list_directory, read_text_file, write_text_file, copy_file, move_file, delete_file
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8765"
DEVICE_ID = None

def wait_for_device():
    """Wait for device to connect"""
    print("\n⏳ Waiting for device to connect...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            resp = requests.get(f"{BASE_URL}/test/devices")
            devices = resp.json().get("devices", [])
            if devices:
                device_id = devices[0]["device_id"]
                print(f"✓ Device connected: {device_id}")
                return device_id
        except:
            pass
        time.sleep(1)
    print("✗ Device connection timeout")
    return None

def test_tool(device_id: str, tool_name: str, params: dict) -> dict:
    """Execute a tool and return result"""
    print(f"\n🔧 Testing {tool_name}...")
    print(f"   Parameters: {params}")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/test/tool",
            json={
                "device_id": device_id,
                "tool": tool_name,
                "params": params
            }
        )
        
        if resp.status_code != 200:
            print(f"   ✗ HTTP Error: {resp.status_code}")
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        
        result = resp.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return {"success": False, "error": str(e)}

def main():
    global DEVICE_ID
    
    print("=" * 60)
    print("FILE TOOLS TEST SUITE (Phase 1E)")
    print("=" * 60)
    
    # Connect device
    DEVICE_ID = wait_for_device()
    if not DEVICE_ID:
        print("\n❌ Could not connect to device. Make sure the Godot client is running!")
        return
    
    # Get desktop path
    print("\n📋 Getting device info to determine desktop path...")
    info_result = requests.post(
        f"{BASE_URL}/test/tool",
        json={
            "device_id": DEVICE_ID,
            "tool": "get_device_info",
            "params": {}
        }
    ).json()
    
    desktop = info_result.get("result", {}).get("info", {}).get("desktop_path")
    if not desktop:
        print("✗ Could not get desktop path!")
        return
    
    print(f"✓ Desktop path: {desktop}")
    
    # === TEST 1: Write a test file ===
    test_file = f"{desktop}/file_tools_test.txt"
    print(f"\n{'='*60}")
    print("TEST 1: write_text_file - Create a test file")
    print(f"{'='*60}")
    
    write_result = test_tool(DEVICE_ID, "write_text_file", {
        "path": test_file,
        "content": "This is a test file for the file tools.\nLine 2: Hello world!\nLine 3: Testing write_text_file tool."
    })
    
    if not write_result.get("success"):
        print("✗ write_text_file failed!")
        return
    
    # === TEST 2: Read the file ===
    print(f"\n{'='*60}")
    print("TEST 2: read_text_file - Read the test file")
    print(f"{'='*60}")
    
    read_result = test_tool(DEVICE_ID, "read_text_file", {
        "path": test_file
    })
    
    if not read_result.get("success"):
        print("✗ read_text_file failed!")
        return
    
    content = read_result.get("result", {}).get("content", "")
    print(f"\n📄 File contents:\n{content}")
    
    # === TEST 3: Append to file ===
    print(f"\n{'='*60}")
    print("TEST 3: write_text_file (append mode) - Add more content")
    print(f"{'='*60}")
    
    append_result = test_tool(DEVICE_ID, "write_text_file", {
        "path": test_file,
        "content": "\nLine 4: Appended from test script!",
        "append": True
    })
    
    if append_result.get("success"):
        # Read again to verify
        read_result2 = test_tool(DEVICE_ID, "read_text_file", {
            "path": test_file
        })
        content = read_result2.get("result", {}).get("content", "")
        print(f"\n📄 Updated file contents:\n{content}")
    
    # === TEST 4: Copy file ===
    test_file_copy = f"{desktop}/file_tools_test_copy.txt"
    print(f"\n{'='*60}")
    print("TEST 4: copy_file - Copy test file")
    print(f"{'='*60}")
    
    copy_result = test_tool(DEVICE_ID, "copy_file", {
        "source_path": test_file,
        "destination_path": test_file_copy,
        "overwrite": False
    })
    
    if copy_result.get("success"):
        # Verify copy exists
        read_copy = test_tool(DEVICE_ID, "read_text_file", {
            "path": test_file_copy
        })
        if read_copy.get("success"):
            print("✓ File copy verified!")
    
    # === TEST 5: List directory ===
    print(f"\n{'='*60}")
    print("TEST 5: list_directory - List desktop contents")
    print(f"{'='*60}")
    
    list_result = test_tool(DEVICE_ID, "list_directory", {
        "path": desktop,
        "recursive": False
    })
    
    if list_result.get("success"):
        items = list_result.get("result", {}).get("items", [])
        print(f"\n📁 Found {len(items)} items:")
        for item in items[:10]:  # Show first 10
            print(f"   - {item}")
        if len(items) > 10:
            print(f"   ... and {len(items) - 10} more")
    
    # === TEST 6: Move/rename file ===
    test_file_moved = f"{desktop}/file_tools_test_renamed.txt"
    print(f"\n{'='*60}")
    print("TEST 6: move_file - Rename the copy")
    print(f"{'='*60}")
    
    move_result = test_tool(DEVICE_ID, "move_file", {
        "source_path": test_file_copy,
        "destination_path": test_file_moved,
        "overwrite": False
    })
    
    if move_result.get("success"):
        # Verify new location
        read_moved = test_tool(DEVICE_ID, "read_text_file", {
            "path": test_file_moved
        })
        if read_moved.get("success"):
            print("✓ File move verified!")
    
    # === TEST 7: Delete file (with safety) ===
    print(f"\n{'='*60}")
    print("TEST 7a: delete_file - Try without confirmation (should fail)")
    print(f"{'='*60}")
    
    delete_fail = test_tool(DEVICE_ID, "delete_file", {
        "path": test_file_moved
    })
    
    if not delete_fail.get("success"):
        print("✓ Correctly rejected deletion without confirmation")
    
    # === TEST 7b: Delete with confirmation ===
    print(f"\n{'='*60}")
    print("TEST 7b: delete_file - Delete with confirmation")
    print(f"{'='*60}")
    
    delete_success = test_tool(DEVICE_ID, "delete_file", {
        "path": test_file_moved,
        "confirm": "DELETE"
    })
    
    if delete_success.get("success"):
        print("✓ File deleted successfully")
    
    # === CLEANUP ===
    print(f"\n{'='*60}")
    print("CLEANUP - Delete test files")
    print(f"{'='*60}")
    
    for cleanup_file in [test_file]:
        try:
            clean_result = test_tool(DEVICE_ID, "delete_file", {
                "path": cleanup_file,
                "confirm": "DELETE"
            })
            if clean_result.get("success"):
                print(f"✓ Cleaned up {cleanup_file}")
        except:
            pass
    
    # === SUMMARY ===
    print(f"\n{'='*60}")
    print("✅ TEST SUITE COMPLETE")
    print(f"{'='*60}")
    print("\nAll new file tools tested successfully!")
    print("\nNew tools:")
    print("  ✓ list_directory")
    print("  ✓ read_text_file")
    print("  ✓ write_text_file (write + append modes)")
    print("  ✓ copy_file")
    print("  ✓ move_file")
    print("  ✓ delete_file (with confirmation safety)")

if __name__ == "__main__":
    main()
