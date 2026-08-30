from __future__ import annotations
"""Agent Runtime — provider-agnostic LLM execution abstraction (Phase 4)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentRunResult:
    run_id: str
    agent_id: str
    task_id: str
    status: RunStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    token_usage: int = 0
    cost: float = 0.0
    logs: list[str] = field(default_factory=list)


class AgentRuntimeAdapter(ABC):
    """Base adapter for AI model providers."""

    @abstractmethod
    async def execute(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        tools: list[str] | None = None,
    ) -> AgentRunResult:
        pass


class OpenAIAdapter(AgentRuntimeAdapter):
    async def execute(self, system_prompt, user_prompt, model, temperature, max_tokens, tools=None):
        raise NotImplementedError("OpenAI adapter — implement in Phase 4 with real API calls")


class AnthropicAdapter(AgentRuntimeAdapter):
    async def execute(self, system_prompt, user_prompt, model, temperature, max_tokens, tools=None):
        raise NotImplementedError("Anthropic adapter — implement in Phase 4")


class AgentRuntime:
    """Routes execution to the correct provider adapter."""

    def __init__(self):
        self._adapters: dict[str, AgentRuntimeAdapter] = {
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
        }

    def get_adapter(self, provider: str) -> AgentRuntimeAdapter:
        adapter = self._adapters.get(provider)
        if adapter is None:
            raise ValueError(f"Unknown provider: {provider}")
        return adapter

    async def run_agent_task(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        task_context: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[str] | None = None,
        run_id: str = "",
        agent_id: str = "",
        task_id: str = "",
    ) -> AgentRunResult:
        adapter = self.get_adapter(provider)
        return await adapter.execute(
            system_prompt=system_prompt,
            user_prompt=task_context,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )
