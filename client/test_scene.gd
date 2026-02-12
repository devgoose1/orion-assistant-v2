extends Node

@onready var ws: Node = $WebSocketNode

func _ready() -> void:
	# Wacht tot WebSocket verbonden is
	while not ws.connected_to_backend:
		await get_tree().process_frame
	
	print("Test: WebSocket is verbonden, sturen LLM request...")
	ws.llm_chunk_received.connect(_on_chunk)
	ws.llm_response_complete.connect(_on_complete)
	ws.ask_llm("Hallo! Wat kun je doen?", "gpt-oss:120b", true)

func _on_chunk(chunk: String) -> void:
	print("📝 ", chunk)

func _on_complete(full: String) -> void:
	print("✓ Klaar! ", full)
