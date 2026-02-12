import asyncio
import json
from main import send_command_to_all

asyncio.run(send_command_to_all({"tool": "create_directory", "path": "/tmp/test_folder"}))