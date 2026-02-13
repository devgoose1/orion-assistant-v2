# Integration Test Suite

Comprehensive end-to-end integration tests for Orion Assistant.

## Features Tested

- ✅ Device registration and management
- ✅ WebSocket connection lifecycle
- ✅ Heartbeat/keep-alive mechanism
- ✅ Tool execution workflows
- ✅ LLM request processing (streaming and non-streaming)
- ✅ Multi-turn conversations with context
- ✅ Error handling and edge cases
- ✅ Concurrent connections
- ✅ High-frequency message handling
- ✅ HTTP REST endpoints

## Requirements

```bash
pip install pytest pytest-asyncio websockets requests
```

## Running Tests

### Run all tests

```bash
pytest backend/test_integration_suite.py -v
```

### Run specific test class

```bash
pytest backend/test_integration_suite.py::TestDeviceManagement -v
```

### Run specific test

```bash
pytest backend/test_integration_suite.py::TestLLMProcessing::test_llm_request_streaming -v
```

### Run with output

```bash
pytest backend/test_integration_suite.py -v -s
```

### Run with coverage

```bash
pytest backend/test_integration_suite.py --cov=backend --cov-report=html
```

## Prerequisites

Before running tests, ensure:

1. **Backend is running:**

   ```bash
   cd backend
   conda activate orion-assistant-v2
   python main.py
   ```

   Server should be available at `http://localhost:8765`

2. **Ollama service is accessible:**
   - Set `OLLAMA_API_KEY` environment variable
   - Verify Ollama Cloud connectivity

3. **Database is initialized:**
   - SQLite database `orion.db` will be created on first run

## Test Organization

### TestDeviceManagement

Tests device registration, listing, and lifecycle:

- `test_http_list_devices()` - HTTP GET /test/devices
- `test_device_registration()` - WebSocket device registration
- `test_heartbeat_keepalive()` - Heartbeat mechanism

### TestToolExecution

Tests tool execution workflows:

- `test_http_tool_trigger()` - HTTP POST /test/tool
- `test_tool_execution_result_handling()` - Tool result processing

### TestLLMProcessing

Tests LLM request handling:

- `test_llm_request_non_streaming()` - Non-streaming mode
- `test_llm_request_streaming()` - Streaming chunks mode

### TestMultiTurnConversation

Tests conversation context:

- `test_conversation_context_maintained()` - Multi-turn context preservation

### TestErrorHandling

Tests error scenarios:

- `test_invalid_message_type()` - Invalid message type handling
- `test_malformed_json()` - JSON parse error handling
- `test_llm_request_without_device_id()` - Missing device registration

### TestPerformance

Tests performance and concurrency:

- `test_concurrent_connections()` - 5 simultaneous connections
- `test_rapid_message_sequence()` - 10+ rapid messages

## Expected Outcomes

### Passing Tests

All tests should pass with working Ollama service:

```text
test_http_list_devices PASSED
test_device_registration PASSED
test_heartbeat_keepalive PASSED
...
===================== 15 passed in 45.23s =====================
```

### Skipped Tests

Tests requiring Ollama API are skipped if service unavailable:

```text
test_llm_request_non_streaming SKIPPED [LLM API timeout (expected...)]
```

### Failed Tests

Investigate failures indicating bugs:

- **Connection refused:** Backend not running on port 8765
- **Timeout on registration:** Device management issue
- **JSON decode errors:** Protocol mismatch

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Run tests with timeout and fail on first error
pytest backend/test_integration_suite.py -v --timeout=120 -x

# Generate JUnit XML report
pytest backend/test_integration_suite.py --junit-xml=test_results.xml

# Generate HTML report
pytest backend/test_integration_suite.py --html=test_report.html
```

## Debugging Failed Tests

Enable debug logging:

```bash
pytest backend/test_integration_suite.py -v -s --log-cli-level=DEBUG
```

Or run individual test with print statements:

```python
@pytest.mark.asyncio
async def test_example():
    async with websockets.connect(WS_URL) as ws:
        print(f"Connected to {WS_URL}")
        # ... test code ...
```

## Performance Baselines

Expected timing (with working Ollama):

| Test | Duration |
| ------ | ---------- |
| Device registration | < 1 sec |
| Heartbeat | < 0.5 sec |
| Non-streaming LLM | 5-30 sec |
| Streaming LLM | 5-30 sec |
| 5 concurrent devices | 2-5 sec |

## Known Limitations

1. **Ollama API Required:** Tests requiring LLM skip if service unavailable
2. **Local Network Only:** Tests use localhost (127.0.0.1)
3. **Serial Execution:** Some tests are sequential per WebSocket connection
4. **No Cleanup:** Test data persists in database (use `test_*` device IDs)

## Maintenance

### Adding New Tests

1. Create new test class inheriting `unittest.TestCase` or use `@pytest.mark.asyncio`
2. Follow naming convention: `test_<feature_name>`
3. Use descriptive docstrings
4. Handle timeouts gracefully
5. Clean up resources in `finally` blocks or use fixtures

### Updating Expected Values

If API changes, update:

- Expected message types in `assert data.get("type") in [...]`
- Response structure checks
- Configuration values from `config.py`

### Debugging Performance

Use pytest-benchmark for performance measurements:

```bash
pip install pytest-benchmark
pytest backend/test_integration_suite.py --benchmark-only
```

---

**Last Updated:** February 13, 2026  
**Test Count:** 16 tests covering 6 feature areas
