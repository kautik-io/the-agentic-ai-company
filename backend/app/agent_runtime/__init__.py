from __future__ import annotations

"""Agent Runtime — provider-agnostic LLM execution abstraction."""

from app.agent_runtime.adapters import AnthropicAdapter, OpenAIAdapter
from app.agent_runtime.types import AgentRunResult, RunStatus


class AgentRuntime:
    """Routes execution to the correct provider adapter."""

    def __init__(self):
        self._openai = OpenAIAdapter()
        self._anthropic = AnthropicAdapter()

    async def run_agent_task(
        self,
        *,
        provider: str,
        api_key: str,
        model: str,
        system_prompt: str,
        task_context: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        run_id: str = "",
        agent_id: str = "",
        task_id: str = "",
    ) -> AgentRunResult:
        kwargs = {
            "api_key": api_key,
            "system_prompt": system_prompt,
            "user_prompt": task_context,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "run_id": run_id,
            "agent_id": agent_id,
            "task_id": task_id,
        }
        if provider == "openai":
            return await self._openai.execute(**kwargs)
        if provider == "anthropic":
            return await self._anthropic.execute(**kwargs)
        return AgentRunResult(
            run_id=run_id,
            agent_id=agent_id,
            task_id=task_id,
            status=RunStatus.FAILED,
            error=f"Unknown provider: {provider}",
        )
