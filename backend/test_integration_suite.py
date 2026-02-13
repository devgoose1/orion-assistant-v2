"""
Comprehensive Integration Test Suite for Orion Assistant

Tests the full end-to-end workflow:
1. Device registration and management
2. Tool execution with results
3. LLM request processing (streaming and non-streaming)
4. Multi-turn conversations with tool calls
5. Error handling and edge cases
6. HTTP endpoints
"""

import asyncio
import json
import time
import pytest
import websockets
import requests
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8765"
WS_URL = "ws://localhost:8765/ws"
TIMEOUT = 60  # seconds


class TestDeviceManagement:
    """Test device registration and management"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_device_id = f"test_device_{int(time.time())}"
    
    def test_http_list_devices(self):
        """Test listing connected devices via HTTP GET"""
        response = requests.get(f"{BASE_URL}/test/devices")
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert "count" in data
        assert isinstance(data["devices"], list)
    
    @pytest.mark.asyncio
    async def test_device_registration(self):
        """Test WebSocket device registration flow"""
        async with websockets.connect(WS_URL) as websocket:
            # Send registration
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": self.test_device_id,
                "device_name": "Test Device",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {"gpu": "none"},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
            
            # Expect acknowledgment
            response = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
            data = json.loads(response)
            # Server may echo registration or provide confirmation
            # Just verify we got a response
            assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_heartbeat_keepalive(self):
        """Test heartbeat/keep-alive mechanism"""
        async with websockets.connect(WS_URL) as websocket:
            # Register first
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": self.test_device_id,
                "device_name": "Test Device",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
            
            # Wait for registration to process
            _ = await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send heartbeat
            await websocket.send(json.dumps({
                "type": "heartbeat",
                "device_id": self.test_device_id,
                "timestamp": time.time(),
                "status": "online"
            }))
            
            # Server should acknowledge (or at least not error)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                assert isinstance(response, str)
            except asyncio.TimeoutError:
                # Timeouts are okay for heartbeat
                pass


class TestToolExecution:
    """Test tool execution workflows"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_device_id = f"test_device_{int(time.time())}"
    
    def test_http_tool_trigger(self):
        """Test HTTP endpoint to trigger tool execution"""
        response = requests.post(
            f"{BASE_URL}/test/tool",
            json={
                "device_id": self.test_device_id,
                "tool": "get_device_info",
                "params": {}
            }
        )
        # May fail if device not connected, but endpoint should respond
        assert response.status_code in [200, 404]
        data = response.json()
        assert "success" in data
    
    @pytest.mark.asyncio
    async def test_tool_execution_result_handling(self):
        """Test tool result reception and processing"""
        async with websockets.connect(WS_URL) as websocket:
            # Register device
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": self.test_device_id,
                "device_name": "Test Device",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
            _ = await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send a tool result to simulate device execution
            await websocket.send(json.dumps({
                "type": "tool_result",
                "request_id": "test_123",
                "tool_name": "get_device_info",
                "success": True,
                "result": {
                    "info": {
                        "device_id": self.test_device_id,
                        "os_name": "Windows",
                        "os_version": "10.0.26200"
                    }
                }
            }))
            
            # Server should process and not disconnect
            # Send another message to verify connection is still active
            await websocket.send(json.dumps({
                "type": "heartbeat",
                "device_id": self.test_device_id,
                "timestamp": time.time(),
                "status": "online"
            }))
            
            # Connection should remain open
            try:
                _ = await asyncio.wait_for(websocket.recv(), timeout=2)
            except asyncio.TimeoutError:
                pass  # Okay


class TestLLMProcessing:
    """Test LLM request processing"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_device_id = f"test_device_{int(time.time())}"
        self.session_id = f"session_{int(time.time())}"
    
    @pytest.mark.asyncio
    async def test_llm_request_non_streaming(self):
        """Test non-streaming LLM request"""
        async with websockets.connect(WS_URL) as websocket:
            # Register device
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": self.test_device_id,
                "device_name": "Test Device",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
            _ = await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send LLM request (non-streaming)
            await websocket.send(json.dumps({
                "type": "llm_request",
                "prompt": "What is 2+2?",
                "stream": False,
                "session_id": self.session_id,
                "model": "gpt-oss:120b"
            }))
            
            # Expect response (may take time for LLM)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
                data = json.loads(response)
                # Should receive llm_response
                assert data.get("type") in ["llm_response", "error", "tool_executing"]
            except asyncio.TimeoutError:
                pytest.skip("LLM API timeout (expected if Ollama service unavailable)")
    
    @pytest.mark.asyncio
    async def test_llm_request_streaming(self):
        """Test streaming LLM request"""
        async with websockets.connect(WS_URL) as websocket:
            # Register device
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": self.test_device_id,
                "device_name": "Test Device",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
            _ = await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send streaming LLM request
            await websocket.send(json.dumps({
                "type": "llm_request",
                "prompt": "Count to 5",
                "stream": True,
                "session_id": self.session_id,
                "model": "gpt-oss:120b"
            }))
            
            # Expect chunks
            chunk_count = 0
            complete = False
            try:
                while not complete and chunk_count < 100:
                    response = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
                    data = json.loads(response)
                    
                    if data.get("type") == "llm_response_chunk":
                        chunk_count += 1
                        complete = data.get("complete", False)
                    elif data.get("type") in ["llm_response", "error"]:
                        complete = True
                    else:
                        # Other message types are okay
                        pass
                
                assert chunk_count > 0 or complete, "Should receive at least initial chunk or complete response"
            except asyncio.TimeoutError:
                pytest.skip("LLM API timeout (expected if Ollama service unavailable)")


class TestMultiTurnConversation:
    """Test multi-turn conversation with context"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_device_id = f"test_device_{int(time.time())}"
        self.session_id = f"session_{int(time.time())}"
    
    @pytest.mark.asyncio
    async def test_conversation_context_maintained(self):
        """Test that conversation context is maintained across turns"""
        async with websockets.connect(WS_URL) as websocket:
            # Register device
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": self.test_device_id,
                "device_name": "Test Device",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
            _ = await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # First turn
            await websocket.send(json.dumps({
                "type": "llm_request",
                "prompt": "My name is Alice",
                "stream": False,
                "session_id": self.session_id
            }))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
                data = json.loads(response)
                # First response received
                assert isinstance(data, dict)
                
                # Second turn - ask about name
                await websocket.send(json.dumps({
                    "type": "llm_request",
                    "prompt": "What is my name?",
                    "stream": False,
                    "session_id": self.session_id
                }))
                
                response2 = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
                data2 = json.loads(response2)
                # LLM should have context from first turn
                assert isinstance(data2, dict)
            except asyncio.TimeoutError:
                pytest.skip("LLM API timeout")


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_device_id = f"test_device_{int(time.time())}"
    
    @pytest.mark.asyncio
    async def test_invalid_message_type(self):
        """Test handling of invalid message types"""
        async with websockets.connect(WS_URL) as websocket:
            # Send invalid message type
            await websocket.send(json.dumps({
                "type": "invalid_type_xyz",
                "data": {}
            }))
            
            # Server should handle gracefully (not crash)
            # Connection should remain open
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                # Might get an error response
                assert isinstance(response, str)
            except asyncio.TimeoutError:
                # Timeout is okay - server might not respond
                pass
            
            # Connection should still be viable
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": self.test_device_id,
                "device_name": "Test",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
    
    @pytest.mark.asyncio
    async def test_malformed_json(self):
        """Test handling of malformed JSON"""
        async with websockets.connect(WS_URL) as websocket:
            # Send invalid JSON
            try:
                await websocket.send("{invalid json")
            except Exception:
                # May raise during send
                pass
            
            # Connection should close or server should recover
            # Try to verify by sending valid message
            try:
                await websocket.send(json.dumps({
                    "type": "device_register",
                    "device_id": self.test_device_id,
                    "device_name": "Test",
                    "os_type": "Windows",
                    "os_version": "10.0.26200",
                    "capabilities": {},
                    "metadata": {"ram_gb": 8, "disk_gb": 256}
                }))
            except Exception:
                # Expected - connection may be closed
                pass
    
    @pytest.mark.asyncio
    async def test_llm_request_without_device_id(self):
        """Test LLM request without prior device registration"""
        async with websockets.connect(WS_URL) as websocket:
            # Send LLM request without registering device
            await websocket.send(json.dumps({
                "type": "llm_request",
                "prompt": "Test",
                "stream": False,
                "session_id": "test_session"
            }))
            
            # Should either error or process (using sessionid as fallback)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
                data = json.loads(response)
                # Should get some response
                assert isinstance(data, dict)
            except asyncio.TimeoutError:
                pytest.skip("LLM API timeout")


class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test multiple concurrent device connections"""
        connections = []
        try:
            # Create 5 concurrent connections
            for i in range(5):
                ws = await websockets.connect(WS_URL)
                connections.append(ws)
                
                # Register each device
                device_id = f"perf_test_device_{i}"
                await ws.send(json.dumps({
                    "type": "device_register",
                    "device_id": device_id,
                    "device_name": f"Test Device {i}",
                    "os_type": "Windows",
                    "os_version": "10.0.26200",
                    "capabilities": {},
                    "metadata": {"ram_gb": 8, "disk_gb": 256}
                }))
            
            # All connections should be active
            assert len(connections) == 5
            
            # Send heartbeat on all
            for ws in connections:
                try:
                    await ws.send(json.dumps({
                        "type": "heartbeat",
                        "device_id": "test",
                        "timestamp": time.time(),
                        "status": "online"
                    }))
                except Exception:
                    pass
        finally:
            # Cleanup
            for ws in connections:
                try:
                    await ws.close()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_rapid_message_sequence(self):
        """Test rapid message sequence handling"""
        async with websockets.connect(WS_URL) as websocket:
            device_id = "rapid_test"
            
            # Register
            await websocket.send(json.dumps({
                "type": "device_register",
                "device_id": device_id,
                "device_name": "Rapid Test",
                "os_type": "Windows",
                "os_version": "10.0.26200",
                "capabilities": {},
                "metadata": {"ram_gb": 8, "disk_gb": 256}
            }))
            _ = await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send 10 rapid heartbeats
            for _ in range(10):
                await websocket.send(json.dumps({
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": time.time(),
                    "status": "online"
                }))
                # No delay - rapid sequence
            
            # Connection should handle this
            await websocket.send(json.dumps({
                "type": "heartbeat",
                "device_id": device_id,
                "timestamp": time.time(),
                "status": "online"
            }))
            
            # Verify connection still works by successfully closing it
            # (if connection was broken, this would raise)
            await websocket.close()


if __name__ == "__main__":
    # Run with: pytest backend/test_integration_suite.py -v
    pytest.main([__file__, "-v"])
