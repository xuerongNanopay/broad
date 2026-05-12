from pathlib import Path
from utils.markdown import render_markdown
from agent.skills import SkillsStore
from typing import Any

class Context:
    
    def __init__(
        self, 
        workspace_dir: Path, 
        skills: list[str] | None = None, 
        timezone: str | None = None,
        *,
        system_prompt: str | None = None,
        builtin_system_prompt_mds: list[str] | None = None,
        workspace_dir_system_prompt_mds: list[str] | None = None):

        self.workspace_dir = workspace_dir
        self.skills = skills
        self.timezone = timezone
        self.system_prompt = system_prompt
        self.builtin_system_prompt_mds = builtin_system_prompt_mds or []
        self.workspace_dir_system_prompt_mds = workspace_dir_system_prompt_mds or []
        self.skill_store = SkillsStore(workspace_dir)

    def build_system_prompt(self) -> str:
        components = []

        if self.system_prompt:
            components.append(self.system_prompt)
        
        if (sp := self._load_builtin_system_prompt_md()):
            components.append(sp)

        if (sp := self._load_workspace_dir_system_prompt_md()):
            components.append(sp)
        
        if (skills_summary := self.skill_store.build_skills_summary()):
            components.append(render_markdown("system_prompts/skills_template.md", skills_summary=skills_summary))

        return "\n\n".join(components)

    def _load_builtin_system_prompt_md(self) -> str:
        parts = []

        for filename in self.builtin_system_prompt_mds:
            parts.append(render_markdown(filename))
        
        return "\n\n".join(parts) if parts else ""

    def _load_workspace_dir_system_prompt_md(self) -> str:
        parts = []

        for filename in self.workspace_dir_system_prompt_mds:
            file_path = self.workspace_dir / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                parts.append(content)
        
        return "\n\n".join(parts) if parts else ""



    
    
        
