from __future__ import annotations

import json
import uuid

import httpx

from app.agent_runtime.types import AgentRunResult, RunStatus


class OpenAIAdapter:
    async def execute(
        self,
        *,
        api_key: str,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        run_id: str = "",
        agent_id: str = "",
        task_id: str = "",
    ) -> AgentRunResult:
        logs: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            return AgentRunResult(
                run_id=run_id,
                agent_id=agent_id,
                task_id=task_id,
                status=RunStatus.FAILED,
                error=f"OpenAI API error {exc.response.status_code}: {detail}",
                logs=[f"HTTP {exc.response.status_code}"],
            )
        except Exception as exc:
            return AgentRunResult(
                run_id=run_id,
                agent_id=agent_id,
                task_id=task_id,
                status=RunStatus.FAILED,
                error=str(exc),
                logs=[str(exc)],
            )

        usage = payload.get("usage", {})
        token_usage = int(usage.get("total_tokens", 0))
        content = payload["choices"][0]["message"]["content"]
        logs.append(f"Model {model} returned {token_usage} tokens")

        try:
            output = json.loads(content)
        except json.JSONDecodeError:
            output = {"status": "completed", "summary": content, "raw": True}

        if "status" not in output:
            output["status"] = "completed"

        return AgentRunResult(
            run_id=run_id,
            agent_id=agent_id,
            task_id=task_id,
            status=RunStatus.COMPLETED,
            output=output,
            token_usage=token_usage,
            logs=logs,
        )


class AnthropicAdapter:
    async def execute(
        self,
        *,
        api_key: str,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        run_id: str = "",
        agent_id: str = "",
        task_id: str = "",
    ) -> AgentRunResult:
        logs: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            return AgentRunResult(
                run_id=run_id,
                agent_id=agent_id,
                task_id=task_id,
                status=RunStatus.FAILED,
                error=f"Anthropic API error {exc.response.status_code}: {detail}",
                logs=[f"HTTP {exc.response.status_code}"],
            )
        except Exception as exc:
            return AgentRunResult(
                run_id=run_id,
                agent_id=agent_id,
                task_id=task_id,
                status=RunStatus.FAILED,
                error=str(exc),
                logs=[str(exc)],
            )

        usage = payload.get("usage", {})
        token_usage = int(usage.get("input_tokens", 0) + usage.get("output_tokens", 0))
        content = payload["content"][0]["text"]
        logs.append(f"Model {model} returned {token_usage} tokens")

        try:
            output = json.loads(content)
        except json.JSONDecodeError:
            output = {"status": "completed", "summary": content, "raw": True}

        if "status" not in output:
            output["status"] = "completed"

        return AgentRunResult(
            run_id=run_id,
            agent_id=agent_id,
            task_id=task_id,
            status=RunStatus.COMPLETED,
            output=output,
            token_usage=token_usage,
            logs=logs,
        )
