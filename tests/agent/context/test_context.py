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


def test_in_mem_session_context_extends_context_and_tracks_messages(tmp_path):
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
    assert len(context.messages) == 2
    assert context.messages[0]["role"] == "user"
    assert context.messages[0]["content"] == "Hello"
    assert _parse_timestamp(context.messages[0]["timestamp"]).tzinfo is timezone.utc


def test_in_mem_session_context_starts_empty(tmp_path):
    context = InMemSessionContext(tmp_path)

    assert context.messages == []
    assert _parse_timestamp(context.created_at).tzinfo is timezone.utc
    assert context.update_at == context.created_at

    context.add_message("user", "Hello")

    assert len(context.messages) == 1
    assert context.messages[0]["role"] == "user"
    assert context.messages[0]["content"] == "Hello"
    assert _parse_timestamp(context.messages[0]["timestamp"]).tzinfo is timezone.utc
    assert context.update_at == context.messages[0]["timestamp"]


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)
