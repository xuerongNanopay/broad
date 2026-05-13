from datetime import datetime, timezone

from agent.memory.base import Memory


def test_memory_starts_empty(tmp_path):
    memory = Memory(tmp_path)

    assert memory.workspace_dir == tmp_path
    assert memory.messages == []
    assert _parse_timestamp(memory.created_at).tzinfo is timezone.utc
    assert memory.update_at == memory.created_at


def test_memory_add_message_tracks_messages_and_timestamp(tmp_path):
    memory = Memory(tmp_path)

    added = memory.add_message("user", "Hello", name="user")

    assert added["role"] == "user"
    assert added["content"] == "Hello"
    assert added["name"] == "user"
    assert _parse_timestamp(added["timestamp"]).tzinfo is timezone.utc
    assert memory.messages == [added]
    assert memory.update_at == added["timestamp"]


def test_memory_get_short_mem_returns_copy(tmp_path):
    memory = Memory(tmp_path)
    memory.add_message("user", "Hello")

    short_mem = memory.get_short_mem(max_tokens=500_000)
    short_mem.append({"role": "assistant", "content": "External mutation"})

    assert len(short_mem) == 2
    assert len(memory.messages) == 1
    assert memory.get_short_mem(max_tokens=500_000) == memory.messages


def test_memory_get_short_mem_limits_max_messages(tmp_path):
    memory = Memory(tmp_path)
    memory.add_message("user", "one")
    memory.add_message("assistant", "two")
    memory.add_message("user", "three")

    short_mem = memory.get_short_mem(max_messages=2, max_tokens=500_000)

    assert [message["content"] for message in short_mem] == ["three"]


def test_memory_get_short_mem_limits_max_tokens(tmp_path):
    memory = Memory(tmp_path)
    memory.add_message("user", "one two")
    memory.add_message("assistant", "three four five")
    memory.add_message("user", "six")

    short_mem = memory.get_short_mem(max_tokens=4)

    assert [message["content"] for message in short_mem] == ["three four five", "six"]


def test_memory_get_short_mem_filters_unpaired_tool_turns(tmp_path):
    memory = Memory(tmp_path)
    memory.add_message("user", "one")
    memory.add_message("tool", "orphan", tool_call_id="missing")
    memory.add_message("user", "two")
    memory.add_message(
        "assistant",
        "",
        tool_calls=[{"id": "call_1", "type": "function"}],
    )
    memory.add_message("tool", "paired", tool_call_id="call_1")

    short_mem = memory.get_short_mem(max_tokens=500_000)

    assert [message["content"] for message in short_mem] == ["two", "", "paired"]


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)
