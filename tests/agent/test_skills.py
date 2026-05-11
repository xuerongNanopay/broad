from agent.skills import BUILTIN_SKILLS_DIR, SkillsStore


def test_list_skills_includes_workspace_and_builtin_skills(tmp_path):
    workspace_skill = tmp_path / "skills" / "custom"
    workspace_skill.mkdir(parents=True)
    workspace_skill.joinpath("SKILL.md").write_text("# Custom\n", encoding="utf-8")

    loader = SkillsStore(tmp_path)

    skills = loader.list_skills()
    by_name = {skill["name"]: skill for skill in skills}

    assert by_name["custom"] == {
        "name": "custom",
        "path": str(workspace_skill / "SKILL.md"),
        "source": "workspace",
    }
    assert by_name["weather"] == {
        "name": "weather",
        "path": str(BUILTIN_SKILLS_DIR / "weather" / "SKILL.md"),
        "source": "builtin",
    }


def test_list_skills_workspace_skill_overrides_builtin_skill(tmp_path):
    workspace_weather = tmp_path / "skills" / "weather"
    workspace_weather.mkdir(parents=True)
    workspace_weather.joinpath("SKILL.md").write_text("# Workspace Weather\n", encoding="utf-8")

    skills = SkillsStore(tmp_path).list_skills()
    weather_entries = [skill for skill in skills if skill["name"] == "weather"]

    assert weather_entries == [
        {
            "name": "weather",
            "path": str(workspace_weather / "SKILL.md"),
            "source": "workspace",
        }
    ]


def test_list_skills_skips_configured_skills(tmp_path):
    loader = SkillsStore(tmp_path, skip_skills=["weather"])

    skills = loader.list_skills()

    assert "weather" not in {skill["name"] for skill in skills}

def test_list_skills(tmp_path):
    loader = SkillsStore(tmp_path)
    skills = loader.list_skills()
    print(skills)


def test_load_skill_metadata_returns_builtin_skill_meta(tmp_path):
    loader = SkillsStore(tmp_path)

    metadata = loader.load_skill_metadata("weather")

    assert metadata == {
        "name": "weather",
        "description": "Get current weather and forecasts with verified location matching (no API key required).",
        "homepage": "https://wttr.in/:help",
        "metadata": {"nanobot": {"emoji": "🌤️", "requires": {"bins": ["curl"]}}},
    }


def test_load_skill_metadata_prefers_workspace_skill_meta(tmp_path):
    workspace_weather = tmp_path / "skills" / "weather"
    workspace_weather.mkdir(parents=True)
    workspace_weather.joinpath("SKILL.md").write_text(
        """---
name: weather
description: Workspace weather skill.
metadata: {"custom":true}
---

# Workspace Weather
""",
        encoding="utf-8",
    )

    metadata = SkillsStore(tmp_path).load_skill_metadata("weather")

    assert metadata == {
        "name": "weather",
        "description": "Workspace weather skill.",
        "metadata": {"custom": True},
    }


def test_build_skills_summary_uses_skill_metadata_description(tmp_path):
    workspace_skill = tmp_path / "skills" / "custom"
    workspace_skill.mkdir(parents=True)
    workspace_skill.joinpath("SKILL.md").write_text(
        """---
name: custom
description: Custom workspace skill.
---

# Custom
""",
        encoding="utf-8",
    )

    summary = SkillsStore(tmp_path, builtin_skills_dir=None).build_skills_summary()

    assert summary == "- **custom** - Custom workspace skill."
