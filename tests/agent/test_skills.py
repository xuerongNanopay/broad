from agent.skills import BUILTIN_SKILLS_DIR, SkillsLoader


def test_list_skills_includes_workspace_and_builtin_skills(tmp_path):
    workspace_skill = tmp_path / "skills" / "custom"
    workspace_skill.mkdir(parents=True)
    workspace_skill.joinpath("SKILL.md").write_text("# Custom\n", encoding="utf-8")

    loader = SkillsLoader(tmp_path)

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

    skills = SkillsLoader(tmp_path).list_skills()
    weather_entries = [skill for skill in skills if skill["name"] == "weather"]

    assert weather_entries == [
        {
            "name": "weather",
            "path": str(workspace_weather / "SKILL.md"),
            "source": "workspace",
        }
    ]


def test_list_skills_skips_configured_skills(tmp_path):
    loader = SkillsLoader(tmp_path, skip_skills=["weather"])

    skills = loader.list_skills()

    assert "weather" not in {skill["name"] for skill in skills}

def test_list_skills(tmp_path):
    loader = SkillsLoader(tmp_path)
    skills = loader.list_skills()
    print(skills)