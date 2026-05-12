from agent.context.base import Context


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
