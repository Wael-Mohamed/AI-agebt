from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationHistory:
    messages: list[dict[str, Any]] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def get_recent(self, n: int = 10) -> list[dict[str, Any]]:
        return self.messages[-n:]

    def clear(self) -> None:
        self.messages.clear()
