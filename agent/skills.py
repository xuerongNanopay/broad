from pathlib import Path

BUILTIN_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

class SkillsLoader:

    def __init__(
        self,
        workspace_dir: Path,
        *,
        skip_skills: list[str] = []
    ):
        self.workspace_dir = workspace_dir
        self.workspace_skills_dir = workspace_dir / "skills"
        
        if not skip_skills:
            self.skip_skills = set()
        else:
            self.skip_skills = set(skip_skills)

        print(f"{str(BUILTIN_SKILLS_DIR)}")
    
    @staticmethod
    def _list_skills_from_dir(skills_dir: Path, source: str, *, skip_skills: set[str] | None = None) -> list[dict[str, str]]:
        if not skills_dir.exists():
            return []

        ret: list[dict[str, str]] = []
        for d in skills_dir.iterdir():
            if not d.is_dir():
                continue

            skill_file = d / "SKILL.md"
            if not skill_file.exists():
                continue

            skill_name = d.name
            if skip_skills is not None and skill_name in skip_skills:
                continue
            ret.append({"name": skill_name, "path": str(skill_file), "source": source})
        
        return ret
    
    def list_skills(self) -> list[dict[str, str]]:

        skills = SkillsLoader._list_skills_from_dir(self.workspace_skills_dir, "workspace")
        workspace_skills = {entry["name"] for entry in skills}

        # workspace skill will override builtin skill
        skills.extend(SkillsLoader._list_skills_from_dir(BUILTIN_SKILLS_DIR, "builtin", skip_skills=workspace_skills))

        if self.skip_skills:
            skills = [s for s in skills if s["name"] not in self.skip_skills]

        return skills
