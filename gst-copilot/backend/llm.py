"""Thin LLM provider wrapper.

The whole prototype must run with zero external dependencies/keys (so a demo never
fails offline). When `LLM_PROVIDER=openai` and a key is present, we upgrade to a real
model; otherwise callers fall back to deterministic templates.
"""

from __future__ import annotations

import os


def is_enabled() -> bool:
    return (
        os.getenv("LLM_PROVIDER", "offline").lower() == "openai"
        and bool(os.getenv("OPENAI_API_KEY"))
    )


def chat(system: str, user: str, *, temperature: float = 0.2) -> str | None:
    """Return model text, or None if LLM is disabled/unavailable (caller falls back)."""
    if not is_enabled():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content
    except Exception:
        # Never let an LLM error break the core flow.
        return None
