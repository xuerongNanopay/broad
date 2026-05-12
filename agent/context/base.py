from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from utils.markdown import render_markdown
from agent.skills import SkillsStore

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


class InMemSessionContext(Context):

    def __init__(
        self,
        workspace_dir: Path,
        skills: list[str] | None = None,
        timezone: str | None = None,
        *,
        system_prompt: str | None = None,
        builtin_system_prompt_mds: list[str] | None = None,
        workspace_dir_system_prompt_mds: list[str] | None = None,
    ):
        super().__init__(
            workspace_dir,
            skills,
            timezone,
            system_prompt=system_prompt,
            builtin_system_prompt_mds=builtin_system_prompt_mds,
            workspace_dir_system_prompt_mds=workspace_dir_system_prompt_mds,
        )
        self.history: list[dict[str, Any]] = []
        self.created_at = self._utc_now()
        self.update_at = self.created_at

    def add_message(self, role: str, content: Any, **kwargs: Any) -> dict[str, Any]:
        timestamp = self._utc_now()
        message = {
            "role": role, 
            "content": content,
            "timestamp": timestamp,
            **kwargs,
        }
        self.history.append(message)
        self.update_at = timestamp
        return message
    
    def get_history(
        self,
        *,
        max_messages: int = 120, 
        max_tokens: int = 0
    ) -> list[dict[str, Any]]:
        
        max_messages = max_messages if max_messages > 0 else 120
        
        history = list(self.history)
        history = history[-max_messages:]
        history = self._filter_begin_non_user_role(history)
        history = self._filter_until_a_paired_tool_turn(history)
        

        if max_messages <= 0:
            return []
        history = history[-max_messages:]

        if max_tokens <= 0:
            return []
        
        if max_tokens > 0 and history:
            pass

        ret = []
        total_tokens = 0
        for message in reversed(history):
            message_tokens = self._count_message_tokens(message)
            if total_tokens + message_tokens > max_tokens:
                break

            ret.append(message)
            total_tokens += message_tokens

        ret.reverse()
        return ret
    
    def _filter_begin_non_user_role(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for i, msg in enumerate(history):
            if msg.get("role") == "user":
                history = history[i:]
                return history
        return history
    
    def _filter_until_a_paired_tool_turn(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tool_ids: set[str] = set()
        offset = 0
        for i, msg in enumerate(history):
            role = msg.get("role")
            if role == "assistant":
                for tool in msg.get("tool_calls") or []:
                    if isinstance(tool, dict) and tc.get("id"):
                        tool_ids.add(str[tool["id"]])
            elif role == "tool":
                tool_id = msg.get("tool_call_id")
                if tool_id and str(tool_id) not in tool_ids:
                    offset = i + 1
        
        return history if not offset else history[offset:]



    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _count_message_tokens(message: dict[str, Any]) -> int:
        content = message.get("content", "")
        return len(str(content).split())


    
    
        
