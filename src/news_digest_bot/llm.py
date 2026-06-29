from __future__ import annotations

import httpx

from news_digest_bot.config import Settings
from news_digest_bot.digest import SYSTEM_PROMPT
from news_digest_bot.modes import DigestMode


def generate_digest(settings: Settings, user_prompt: str) -> str:
    return generate_digest_with_prompt(settings, SYSTEM_PROMPT, user_prompt)


def generate_mode_digest(settings: Settings, mode: DigestMode, user_prompt: str) -> str:
    return generate_digest_with_prompt(settings, mode.system_prompt, user_prompt)


def generate_digest_with_prompt(settings: Settings, system_prompt: str, user_prompt: str) -> str:
    if not settings.deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY is required for digest generation")

    url = settings.deepseek_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {settings.deepseek_api_key}"}
    with httpx.Client(timeout=60) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
