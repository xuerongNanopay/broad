from datetime import datetime, timezone

from agent.context.base import Context, InMemSessionContext


class FakeSkillStore:
    def __init__(self, skills_summary: str):
        self.skills_summary = skills_summary

    def build_skills_summary(self) -> str:
        return self.skills_summary


def test_context_build_system_prompt_combines_sources(tmp_path):
    workspace_prompt = tmp_path / "WORKSPACE.md"
    workspace_prompt.write_text("# Workspace\n\nUse local instructions.", encoding="utf-8")
    context = Context(
        tmp_path,
        system_prompt="Base instructions.",
        workspace_dir_system_prompt_mds=["WORKSPACE.md"],
    )
    context.skill_store = FakeSkillStore("- **custom** - Custom workspace skill.")

    prompt = context.build_system_prompt()

    assert "Base instructions." in prompt
    assert "# Workspace\n\nUse local instructions." in prompt
    assert "# Skills" in prompt
    assert "- **custom** - Custom workspace skill." in prompt
    assert "WORKSPACE.md" not in prompt


def test_context_build_system_prompt_handles_empty_defaults(tmp_path):
    context = Context(tmp_path)
    context.skill_store = FakeSkillStore("")

    assert context.build_system_prompt() == ""


def test_in_mem_session_context_extends_context_and_tracks_history(tmp_path):
    context = InMemSessionContext(
        tmp_path,
        system_prompt="Base instructions.",
    )
    context.skill_store = FakeSkillStore("")

    assert isinstance(context, Context)
    assert _parse_timestamp(context.created_at).tzinfo is timezone.utc
    assert context.update_at == context.created_at

    context.add_message("user", "Hello")
    added = context.add_message("assistant", "Hi", name="assistant")

    assert added["role"] == "assistant"
    assert added["content"] == "Hi"
    assert added["name"] == "assistant"
    assert _parse_timestamp(added["timestamp"]).tzinfo is timezone.utc
    assert context.update_at == added["timestamp"]
    assert len(context.history) == 2
    assert context.history[0]["role"] == "user"
    assert context.history[0]["content"] == "Hello"
    assert _parse_timestamp(context.history[0]["timestamp"]).tzinfo is timezone.utc
    assert context.get_history(max_tokens=500_000) == context.history


def test_in_mem_session_context_starts_empty(tmp_path):
    context = InMemSessionContext(tmp_path)

    assert context.history == []
    assert _parse_timestamp(context.created_at).tzinfo is timezone.utc
    assert context.update_at == context.created_at

    context.add_message("user", "Hello")

    assert len(context.history) == 1
    assert context.history[0]["role"] == "user"
    assert context.history[0]["content"] == "Hello"
    assert _parse_timestamp(context.history[0]["timestamp"]).tzinfo is timezone.utc
    assert context.update_at == context.history[0]["timestamp"]


def test_in_mem_session_context_get_history_returns_copy(tmp_path):
    context = InMemSessionContext(tmp_path)
    context.add_message("user", "Hello")

    history = context.get_history(max_tokens=500_000)
    history.append({"role": "assistant", "content": "External mutation"})

    assert len(history) == 2
    assert len(context.history) == 1
    assert context.get_history(max_tokens=500_000) == context.history


def test_in_mem_session_context_get_history_limits_max_messages(tmp_path):
    context = InMemSessionContext(tmp_path)
    context.add_message("user", "one")
    context.add_message("assistant", "two")
    context.add_message("user", "three")

    history = context.get_history(max_messages=2, max_tokens=500_000)

    assert [message["content"] for message in history] == ["three"]


def test_in_mem_session_context_get_history_limits_max_tokens(tmp_path):
    context = InMemSessionContext(tmp_path)
    context.add_message("user", "one two")
    context.add_message("assistant", "three four five")
    context.add_message("user", "six")

    history = context.get_history(max_tokens=4)

    assert [message["content"] for message in history] == ["three four five", "six"]


def test_in_mem_session_context_get_history_limits_messages_and_tokens(tmp_path):
    context = InMemSessionContext(tmp_path)
    context.add_message("user", "one two")
    context.add_message("assistant", "three")
    context.add_message("user", "four five")

    history = context.get_history(max_messages=2, max_tokens=2)

    assert [message["content"] for message in history] == ["four five"]


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)
