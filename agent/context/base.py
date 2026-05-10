from pathlib import Path
from utils.markdown import render_markdown

class Context:
    
    def __init__(self, work_dir: Path, skills: list[str] | None, timezone: str | None = None):
        self.work_dir = work_dir
        self.skills = skills
        self.timezone = timezone
    

class SimpleContext(Context):

    def __init__(
        self, 
        work_dir: Path, 
        *,
        system_prompt: str | None = None,
        system_prompt_mds: list[str] | None = None,
        work_dir_system_prompt_mds: list[str] | None = None,
        skills: list[str] | None = None, 
        timezone: str | None = None):

        super().__init__(work_dir, skills, timezone)
        
        self.system_prompt = system_prompt
        self.system_prompt_mds = system_prompt_mds
        self.work_dir_system_prompt_mds = work_dir_system_prompt_mds

    def build_system_prompt(self) -> str:
        components = []

        if self.system_prompt:
            components.append(self.system_prompt)
        
        if (sp := self._load_system_prompt_md()):
            components.append(sp)

        if (sp := self._load_work_dir_system_prompt_md()):
            components.append(sp)
        
        

    def _load_system_prompt_md(self) -> str:
        parts = []

        for filename in self.system_prompt_mds:
            parts.append(f"## {filename}\n\n{render_markdown(filename)}")
        
        return "\n\n".join(parts) if parts else ""

    def _load_work_dir_system_prompt_md(self) -> str:
        parts = []

        for filename in self.work_dir_system_prompt_mds:
            file_path = self.work_dir / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                parts.append(f"## {filename}\n\n{content}")
        
        return "\n\n".join(parts) if parts else ""



    
    
        
