import json
from pathlib import Path
import re

BUILTIN_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

_SKILL_META = re.compile(
    r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?",
    re.DOTALL,
)

class SkillsStore:

    def __init__(
        self,
        workspace_dir: Path,
        *,
        builtin_skills_dir: Path | None = BUILTIN_SKILLS_DIR,
        skip_skills: list[str] = []
    ):
        self.workspace_dir = workspace_dir
        self.workspace_skills_dir = workspace_dir / "skills"
        self.builtin_skills_dir = builtin_skills_dir
        
        if not skip_skills:
            self.skip_skills = set()
        else:
            self.skip_skills = set(skip_skills)
    
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

        skills = SkillsStore._list_skills_from_dir(self.workspace_skills_dir, "workspace")
        workspace_skills = {entry["name"] for entry in skills}

        # workspace skill will override builtin skill
        if self.builtin_skills_dir:
            skills.extend(SkillsStore._list_skills_from_dir(self.builtin_skills_dir, "builtin", skip_skills=workspace_skills))

        if self.skip_skills:
            skills = [s for s in skills if s["name"] not in self.skip_skills]

        return skills
    
    def load_skill_md_file(self, skill_name: str) -> str | None:
        dirs = [self.workspace_skills_dir]
        if self.builtin_skills_dir:
            dirs.append(self.builtin_skills_dir)
        
        for d in dirs:
            file_path = d / skill_name / "SKILL.md"
            if file_path.exists():
                return file_path.read_text(encoding="utf-8")
        
        return None

    def load_skills(self, skill_names: list[str]) -> str:
        components = []

        for name in skill_names:
            if (md := self.load_skill_md_file(name)):
                components.append(f"## Skill: {name}\n\n{self._maybe_remove_skill_meta(md)}")
        
        return "\n\n---\n\n".join(components)

    def _maybe_remove_skill_meta(self, content: str) -> str:
        if not content.startswith("---"):
            return content
        if (match := _SKILL_META.match(content)):
            return content[match.end():].strip()
        return content
    
    def load_skill_metadata(self, skill_name: str) -> dict | None:
        content = self.load_skill_md_file(skill_name)
        if not content or not content.startswith("---"):
            return None
        
        match = _SKILL_META.match(content)
        if not match:
            return None

        return self._parse_skill_meta(match.group(1))

    @staticmethod
    def _parse_skill_meta(meta: str) -> dict:
        ret = {}

        for line in meta.splitlines():
            key, sep, value = line.partition(":")
            if not sep:
                continue

            ret[key.strip()] = SkillsStore._parse_skill_meta_value(value.strip())
        
        return ret

    @staticmethod
    def _parse_skill_meta_value(value: str):
        if value.startswith(("{", "[")):
            return json.loads(value)
        
        return value.strip("\"'")
