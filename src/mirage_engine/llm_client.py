"""Minimal OpenAI Chat Completions client using urllib."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Sequence


class OpenAIError(RuntimeError):
    """Raised when the OpenAI API returns an error."""


class OpenAIClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-5-mini",
        temperature: float = 1.0,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIError(
                "OPENAI_API_KEY is not set. Provide one via the environment or .env file."
            )
        self.model = model
        self.temperature = temperature

    def complete(
        self,
        messages: Sequence[Dict[str, Any]],
        *,
        tools: Sequence[Dict[str, Any]] | None = None,
        tool_choice: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": list(messages),
        }
        if tools:
            payload["tools"] = list(tools)
        if tool_choice:
            payload["tool_choice"] = tool_choice
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="ignore") if error.fp else ""
            raise OpenAIError(f"HTTP error {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise OpenAIError(f"Connection error: {error.reason}") from error

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as error:
            raise OpenAIError(f"Failed to decode OpenAI response: {body}") from error

        try:
            return parsed["choices"][0]
        except (KeyError, IndexError, TypeError) as error:
            raise OpenAIError(f"Unexpected OpenAI response: {parsed}") from error
