"""Async DeepSeek API client.

Thin wrapper around httpx for DeepSeek's OpenAI-compatible chat completions.
Supports structured output via json_object + embedded schema, reasoning_effort,
and token tracking.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_TIMEOUT_S = 180

ModelName = str

V4_FLASH: ModelName = "deepseek-v4-flash"
V4_PRO: ModelName = "deepseek-v4-pro"

ReasoningEffort = str  # "low" | "medium" | "high" | "max"


def _api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")
    return key


def _schema_instructions(model: type[BaseModel]) -> str:
    """Generate a human-readable description of the expected JSON shape.

    DeepSeek supports response_format json_object but NOT json_schema strict.
    So we describe the schema in the prompt itself and parse on our side.
    """
    schema = model.model_json_schema()
    lines = [
        "Output a single JSON object. Use EXACTLY the field names listed below.",
        "Do not rename, abbreviate, or invent new field names.",
        "",
    ]

    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))
    defs = schema.get("$defs", {})

    def resolve_ref(ref_str: str) -> dict:
        """Resolve a $ref like '#/$defs/Foo' to the sub-schema dict."""
        key = ref_str.split("/")[-1]
        return defs.get(key, {})

    def describe_property(name: str, info: dict, indent: int, parent_type: str) -> None:
        prefix = "  " * indent
        field_type = info.get("type", "any")
        description = info.get("description", "")
        anyof = info.get("anyOf")

        # Handle anyOf (e.g., string | null)
        if anyof and not field_type:
            types = [t.get("type", "any") for t in anyof]
            field_type = " or ".join(types)

        # Handle array types
        if field_type == "array":
            items = info.get("items", {})
            item_ref = items.get("$ref", "")
            if item_ref:
                sub_schema = resolve_ref(item_ref)
                sub_props = sub_schema.get("properties", {})
                req_mark = " (REQUIRED)" if name in required_fields else ""
                lines.append(f"{prefix}\"{name}\": [array of objects]{req_mark}")
                if description:
                    lines.append(f"{prefix}  — {description}")
                lines.append(f"{prefix}  Each object MUST have these exact keys:")
                for sub_name, sub_info in sub_props.items():
                    sub_type = sub_info.get("type", "any")
                    sub_desc = sub_info.get("description", "")
                    sub_enum = sub_info.get("enum")
                    sub_anyof = sub_info.get("anyOf")
                    sub_items = sub_info.get("items", {})
                    sub_item_ref = sub_items.get("$ref", "")

                    if sub_enum:
                        sub_type = " | ".join(repr(v) for v in sub_enum)
                    elif sub_anyof:
                        types = [t.get("type", "any") for t in sub_anyof]
                        sub_type = " or ".join(types)
                    elif sub_item_ref:
                        # Nested array of objects — show recursively
                        nested_schema = resolve_ref(sub_item_ref)
                        nested_props = nested_schema.get("properties", {})
                        lines.append(f"{prefix}    \"{sub_name}\": [array of objects, each with:]")
                        for n_name, n_info in nested_props.items():
                            n_type = n_info.get("type", "any")
                            n_desc = n_info.get("description", "")
                            lines.append(f"{prefix}      \"{n_name}\": {n_type}")
                            if n_desc:
                                lines.append(f"{prefix}        — {n_desc}")
                        continue  # skip the normal sub-field line

                    lines.append(f"{prefix}    \"{sub_name}\": {sub_type}")
                    if sub_desc:
                        lines.append(f"{prefix}      — {sub_desc}")
            else:
                item_type = items.get("type", "string")
                req_mark = " (REQUIRED)" if name in required_fields else ""
                lines.append(f"{prefix}\"{name}\": [array of {item_type}]{req_mark}")
                if description:
                    lines.append(f"{prefix}  — {description}")
            return

        # Handle enum
        if "enum" in info:
            field_type = " | ".join(repr(v) for v in info["enum"])

        req_mark = " (REQUIRED)" if name in required_fields else ""
        lines.append(f"{prefix}\"{name}\": {field_type}{req_mark}")
        if description:
            lines.append(f"{prefix}  — {description}")

    for field_name, field_info in properties.items():
        describe_property(field_name, field_info, indent=0, parent_type="root")

    # Add constraints section
    constraints = []
    for field_name, field_info in properties.items():
        if "minItems" in field_info:
            constraints.append(f"\"{field_name}\" must have at least {field_info['minItems']} items")
        if "maxItems" in field_info:
            constraints.append(f"\"{field_name}\" must have at most {field_info['maxItems']} items")
    if constraints:
        lines.append("")
        lines.append("CONSTRAINTS:")
        for c in constraints:
            lines.append(f"  - {c}")

    return "\n".join(lines)


def _extract_json(text: str) -> str:
    """Extract JSON from model output, stripping markdown fences and recovering truncation."""
    text = text.strip()
    # Strip markdown code fences
    fence_match = re.match(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    # Find the outermost { }
    start = text.find("{")
    if start < 0:
        return text
    # Walk from start counting braces to find the matching closing brace
    depth = 0
    end = start
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    text = text[start : end + 1]
    # Attempt to recover truncated JSON by closing open brackets/braces
    open_braces = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")
    if open_braces > 0 or open_brackets > 0:
        text = text + "]" * open_brackets + "}" * open_braces
    return text


class DeepSeekClient:
    """Async client for DeepSeek's chat completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._api_key = api_key or _api_key()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_s

    async def structured_output(
        self,
        *,
        model: ModelName,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        run_id: str = "",
    ) -> BaseModel:
        """Call DeepSeek with structured output and return a parsed Pydantic model.

        DeepSeek doesn't support strict json_schema, so we use json_object mode
        and embed schema instructions in the system prompt.
        """
        schema_text = _schema_instructions(response_model)
        full_system = f"{system_prompt}\n\nEXPECTED OUTPUT SCHEMA:\n{schema_text}"

        messages: list[dict[str, str]] = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_prompt},
        ]

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        if model == V4_PRO:
            body["reasoning_effort"] = reasoning_effort

        log = logger.bind(run_id=run_id, model=model)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        usage = data.get("usage", {})
        log.info(
            "deepseek_api_call",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

        content = data["choices"][0]["message"]["content"]
        json_str = _extract_json(content)

        try:
            return response_model.model_validate_json(json_str)
        except Exception as first_error:
            log.warning("json_validation_failed", attempt=1, error=str(first_error)[:200])
            # Retry loop: send error back to model, up to 3 attempts
            last_content = content
            last_error = first_error
            for attempt in range(1, 4):
                retry_user = (
                    f"{user_prompt}\n\n"
                    f"Your previous output failed JSON validation with this error:\n{last_error}\n\n"
                    f"Please fix the JSON and output the complete, valid JSON only. "
                    f"Make sure ALL required fields are present and lists have enough items."
                )
                retry_body: dict[str, Any] = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": full_system},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": last_content},
                        {"role": "user", "content": retry_user},
                    ],
                    "temperature": min(temperature + (attempt * 0.1), 1.0),
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                }
                if model == V4_PRO:
                    retry_body["reasoning_effort"] = reasoning_effort

                async with httpx.AsyncClient(timeout=self._timeout) as client2:
                    retry_resp = await client2.post(
                        f"{self._base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json=retry_body,
                    )
                    retry_resp.raise_for_status()
                    retry_data = retry_resp.json()

                retry_content = retry_data["choices"][0]["message"]["content"]
                retry_json = _extract_json(retry_content)

                retry_usage = retry_data.get("usage", {})
                log.info(
                    "deepseek_retry_call",
                    attempt=attempt + 1,
                    prompt_tokens=retry_usage.get("prompt_tokens", 0),
                    completion_tokens=retry_usage.get("completion_tokens", 0),
                )

                try:
                    return response_model.model_validate_json(retry_json)
                except Exception as retry_error:
                    last_content = retry_content
                    last_error = retry_error
                    log.warning("json_validation_failed", attempt=attempt + 1, error=str(retry_error)[:200])

            # All retries exhausted
            raise last_error

    async def chat(
        self,
        *,
        model: ModelName,
        system_prompt: str,
        user_prompt: str,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        run_id: str = "",
    ) -> str:
        """Call DeepSeek without structured output — returns raw text."""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if model == V4_PRO:
            body["reasoning_effort"] = reasoning_effort

        log = logger.bind(run_id=run_id, model=model)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        usage = data.get("usage", {})
        log.info(
            "deepseek_api_call",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

        return data["choices"][0]["message"]["content"]


# ── LangChain ChatModel wrapper ───────────────────────────────────────────────


class ChatDeepSeek:
    """LangChain-compatible chat model for DeepSeek.

    Implements the minimal LangChain BaseChatModel interface so pipeline code
    can use `model.invoke(messages)` with the standard LCEL pattern while
    still hitting DeepSeek's API directly (avoiding the langchain-deepseek
    package dependency for the actual HTTP calls).

    Usage:
        model = ChatDeepSeek(model="deepseek-v4-pro", reasoning_effort="high")
        response = await model.ainvoke([HumanMessage(content="...")])
    """

    def __init__(
        self,
        model: ModelName = V4_PRO,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = DeepSeekClient(
            api_key=api_key, base_url=base_url, timeout_s=timeout_s
        )

    async def ainvoke(
        self,
        messages: list[dict[str, str]],
        *,
        system: str = "",
        run_id: str = "",
    ) -> str:
        """Async invoke with LangChain-style message list.

        If `system` is provided it is prepended as a system message.
        """
        if system:
            return await self._client.chat(
                model=self.model,
                system_prompt=system,
                user_prompt=messages[-1]["content"] if messages else "",
                reasoning_effort=self.reasoning_effort,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                run_id=run_id,
            )

        # Separate system and user messages from the list
        system_content = ""
        user_content = ""
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                system_content = msg.get("content", "")
            elif role == "user":
                user_content = msg.get("content", "")

        return await self._client.chat(
            model=self.model,
            system_prompt=system_content,
            user_prompt=user_content,
            reasoning_effort=self.reasoning_effort,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            run_id=run_id,
        )

    async def ainvoke_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        *,
        system: str = "",
        run_id: str = "",
    ) -> BaseModel:
        """Async structured output invocation."""
        if system:
            return await self._client.structured_output(
                model=self.model,
                system_prompt=system,
                user_prompt=messages[-1]["content"] if messages else "",
                response_model=response_model,
                reasoning_effort=self.reasoning_effort,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                run_id=run_id,
            )

        system_content = ""
        user_content = ""
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                system_content = msg.get("content", "")
            elif role == "user":
                user_content = msg.get("content", "")

        return await self._client.structured_output(
            model=self.model,
            system_prompt=system_content,
            user_prompt=user_content,
            response_model=response_model,
            reasoning_effort=self.reasoning_effort,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            run_id=run_id,
        )

    def invoke(self, messages: list[dict[str, str]], *, system: str = "", run_id: str = "") -> str:
        """Sync invoke — thin sync wrapper for environments that need it."""
        import asyncio

        return asyncio.run(self.ainvoke(messages, system=system, run_id=run_id))
