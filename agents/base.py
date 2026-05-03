import json
from typing import Any

import anthropic

from config import MODEL, MAX_TOKENS
from tools.crm_tools import CRMStore, get_crm_tool_definitions, handle_crm_tool_call


class BaseAgent:
    """Base class for all sales agents. Handles the tool-use agentic loop."""

    name: str = "BaseAgent"
    system_prompt: str = "You are a helpful sales assistant."

    def __init__(self, client: anthropic.Anthropic, crm: CRMStore):
        self.client = client
        self.crm = crm
        self.tools = get_crm_tool_definitions()

    def run(self, user_message: str, context: dict[str, Any] | None = None) -> str:
        """Run the agent on a message, looping through tool calls until done."""
        messages = self._build_messages(user_message, context)
        system = self._build_system(context)

        for _ in range(10):  # max 10 tool-call iterations
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
                tools=self.tools,
            )

            # Collect all text blocks and tool use blocks
            text_blocks = []
            tool_calls = []
            for block in response.content:
                if block.type == "text":
                    text_blocks.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            if response.stop_reason == "end_turn" or not tool_calls:
                return "\n".join(text_blocks).strip()

            # Append assistant message with all content blocks
            messages.append({"role": "assistant", "content": response.content})

            # Execute every tool call and gather results
            tool_results = []
            for tc in tool_calls:
                result = handle_crm_tool_call(self.crm, tc.name, tc.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tc.id, "content": result}
                )

            messages.append({"role": "user", "content": tool_results})

        return "Maximum tool iterations reached. Please try again."

    # ── Overridable helpers ───────────────────────────────────────────────

    def _build_system(self, context: dict | None) -> list[dict]:
        """Build system prompt blocks (supports prompt caching)."""
        blocks = [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        if context:
            blocks.append(
                {
                    "type": "text",
                    "text": f"Current context:\n{json.dumps(context, indent=2)}",
                }
            )
        return blocks

    def _build_messages(self, user_message: str, context: dict | None) -> list[dict]:
        return [{"role": "user", "content": user_message}]
