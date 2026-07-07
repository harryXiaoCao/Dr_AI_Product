import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from app.config import Settings


class DeepSeekChatError(Exception):
    def __init__(self, fallback_reason: str) -> None:
        self.fallback_reason = fallback_reason


@dataclass(frozen=True)
class DeepSeekChatResult:
    content: str
    model: str


class DeepSeekChatAdapter:
    def complete(self, *, message: str, settings: Settings) -> DeepSeekChatResult:
        if settings.environment in {"local", "test"} or settings.deepseek_api_key is None:
            return DeepSeekChatResult(
                content=(
                    "Educational information only - not medical advice. "
                    "You can ask your clinician what the synthetic recovery-plan task means, "
                    "what warning signs should prompt urgent care, and what questions to prepare "
                    "for the next appointment."
                ),
                model=f"{settings.deepseek_model}:local-safe-fallback",
            )

        api_key = settings.deepseek_api_key.get_secret_value()
        request_body = {
            "model": settings.deepseek_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Dr. AI's educational question-preparation assistant. "
                        "Do not diagnose, recommend medication changes, or ask for personal data. "
                        "Keep answers brief, include limitations, and suggest questions for a "
                        "qualified clinician."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Provide general educational context and appointment questions for this "
                        f"non-clinical beta prompt: {message}"
                    ),
                },
            ],
            "stream": False,
            "max_tokens": 360,
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            settings.deepseek_base_url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - configured HTTPS DeepSeek endpoint.
                request,
                timeout=settings.deepseek_timeout_seconds,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise DeepSeekChatError("timeout") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in {402, 429}:
                raise DeepSeekChatError("quota") from exc
            raise DeepSeekChatError("service_unavailable") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise DeepSeekChatError("malformed") from exc

        try:
            content = payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise DeepSeekChatError("malformed") from exc
        if not content:
            raise DeepSeekChatError("malformed")
        return DeepSeekChatResult(content=content, model=settings.deepseek_model)


deepseek_chat_adapter = DeepSeekChatAdapter()
