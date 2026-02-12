extends Node

@onready var ws: Node = $WebSocketNode

func _ready() -> void:
	await get_tree().process_frame
	ws.llm_chunk_received.connect(_on_chunk)
	ws.llm_response_complete.connect(_on_complete)
	ws.ask_llm("Hallo!", "mistral", true)

func _on_chunk(chunk: String) -> void:
	print("📝 ", chunk)

func _on_complete(full: String) -> void:
	print("✓ Klaar! ", full)
