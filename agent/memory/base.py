from typing import Any

from utils.time import utc_now


class Memory:

    def __init__(self, workspace_dir):
        self.workspace_dir = workspace_dir

        self.messages: list[dict[str, Any]]  = []
        self.created_at = utc_now()
        self.update_at = self.created_at


    def add_message(self, role: str, content: Any, **kwargs: Any) -> dict[str, Any]:
        timestamp = utc_now()
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            **kwargs,
        }
        self.messages.append(message)
        self.update_at = timestamp
        return message

    def get_short_mem(
        self,
        *,
        max_messages: int = 120,
        max_tokens: int = 0,
    ) -> list[dict[str, Any]]:
        max_messages = max_messages if max_messages > 0 else 120

        messages = list(self.messages)
        messages = messages[-max_messages:]
        messages = self._filter_begin_non_user_role(messages)
        messages = self._filter_until_a_paired_tool_turn(messages)

        if max_tokens <= 0 or not messages:
            return messages

        ret = []
        total_tokens = 0
        for message in reversed(messages):
            message_tokens = self._estimate_message_tokens(message)
            if total_tokens + message_tokens > max_tokens and message.get("role") == "user":
                break

            ret.append(message)
            total_tokens += message_tokens

        ret.reverse()
        return ret

    def _filter_begin_non_user_role(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for i, msg in enumerate(messages):
            if msg.get("role") == "user":
                return messages[i:]
        return messages

    def _filter_until_a_paired_tool_turn(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tool_ids: set[str] = set()
        offset = 0
        for i, msg in enumerate(messages):
            role = msg.get("role")
            if role == "assistant":
                for tool in msg.get("tool_calls") or []:
                    if isinstance(tool, dict) and tool.get("id"):
                        tool_ids.add(str(tool["id"]))
            elif role == "tool":
                tool_id = msg.get("tool_call_id")
                if tool_id and str(tool_id) not in tool_ids:
                    offset = i + 1

        return messages if not offset else messages[offset:]

    @staticmethod
    def _estimate_message_tokens(message: dict[str, Any]) -> int:
        content = message.get("content", "")
        return max(4, len(content) // 4 + 4)
