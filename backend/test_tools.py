"""
Test script voor tool execution
Gebruik dit om tools te testen vanaf de command line
"""
import requests
import json

BASE_URL = "http://localhost:8765"

def list_devices():
    """Toon alle verbonden devices"""
    try:
        response = requests.get(f"{BASE_URL}/test/devices")
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            print(f"\n📱 Verbonden devices ({data['count']}):")
            for device in data["devices"]:
                print(f"  • {device['device_id']}")
            return [d["device_id"] for d in data["devices"]]
        else:
            print("❌ Kon devices niet ophalen")
            return []
    except requests.exceptions.ConnectionError:
        print("❌ Kan niet verbinden met backend. Is de server gestart?")
        print("   Start met: python main.py")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def execute_tool(device_id: str, tool: str, params: dict):
    """Execute een tool op een device"""
    payload = {
        "device_id": device_id,
        "tool": tool,
        "params": params
    }
    
    print(f"\n🔧 Executing {tool} op {device_id}...")
    print(f"   Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/test/tool",
            json=payload  # Send as JSON body instead of query params
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            print(f"✅ Tool execution gestart!")
            print(f"   Request ID: {data['request_id']}")
        else:
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
        
        return data
    except requests.exceptions.ConnectionError:
        print("❌ Kan niet verbinden met backend. Is de server gestart?")
        return {"success": False, "error": "Connection failed"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def test_create_directory():
    """Test: Create directory"""
    devices = list_devices()
    if not devices:
        print("❌ Geen devices verbonden")
        return
    
    device_id = devices[0]
    execute_tool(
        device_id,
        "create_directory",
        {"path": "C:/Users/njsch/Desktop/OrionTestFolder"}
    )

def test_get_device_info():
    """Test: Get device info"""
    devices = list_devices()
    if not devices:
        print("❌ Geen devices verbonden")
        return
    
    device_id = devices[0]
    execute_tool(
        device_id,
        "get_device_info",
        {"info_type": "all"}
    )

def test_search_files():
    """Test: Search files"""
    devices = list_devices()
    if not devices:
        print("❌ Geen devices verbonden")
        return
    
    device_id = devices[0]
    execute_tool(
        device_id,
        "search_files",
        {
            "path": "C:/Users/njsch/Desktop",
            "pattern": "*.txt",
            "recursive": False
        }
    )

def test_open_app():
    """Test: Open application"""
    devices = list_devices()
    if not devices:
        print("❌ Geen devices verbonden")
        return
    
    device_id = devices[0]
    execute_tool(
        device_id,
        "open_app",
        {
            "app_name": "notepad",
            "arguments": []
        }
    )

if __name__ == "__main__":
    print("="*60)
    print("🧪 Orion Assistant - Tool Testing")
    print("="*60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/test/devices", timeout=2)
        response.raise_for_status()
        print("✅ Backend is online")
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend is NIET bereikbaar!")
        print("   Start eerst de backend met: python main.py")
        print("\n   Druk op Enter om af te sluiten...")
        input()
        exit(1)
    except Exception as e:
        print(f"\n⚠️  Waarschuwing: {e}")
    
    # Toon menu
    print("\nBeschikbare tests:")
    print("  1. List devices")
    print("  2. Create directory")
    print("  3. Get device info")
    print("  4. Search files")
    print("  5. Open notepad")
    print("  0. Exit")
    
    while True:
        choice = input("\nKies een test (0-5): ").strip()
        
        if choice == "0":
            print("👋 Tot ziens!")
            break
        elif choice == "1":
            list_devices()
        elif choice == "2":
            test_create_directory()
        elif choice == "3":
            test_get_device_info()
        elif choice == "4":
            test_search_files()
        elif choice == "5":
            test_open_app()
        else:
            print("❌ Ongeldige keuze")
