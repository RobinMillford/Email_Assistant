"""
llm_client.py — Provider-agnostic chat wrapper.

Supports two providers, selected via the PROVIDER env var (default: "groq"):

  PROVIDER=groq       → Groq Cloud (OpenAI-compatible, free tier).  [default]
  PROVIDER=anthropic  → Anthropic Claude.

Both expose one function:

    chat(system, user, model, max_tokens) -> {
        "text": str,
        "input_tokens": int,
        "output_tokens": int,
        "error": str | None,
    }

Retry with exponential backoff on rate-limit errors. The rest of the codebase
talks only to this module, so swapping providers never touches generator/evaluator.
"""

import time

from src.config import (
    PROVIDER,
    OPENAI_API_KEY,
    GROQ_API_KEY,
    ANTHROPIC_API_KEY,
    MAX_RETRIES,
    RETRY_DELAY,
    CALL_PAUSE,
)

# Providers that speak the OpenAI chat-completions API shape.
_OPENAI_COMPATIBLE = {"openai", "groq"}

# ---------------------------------------------------------------------------
# Lazy, provider-specific client construction
# ---------------------------------------------------------------------------
_client = None


def _get_client():
    """Build the provider client once and cache it."""
    global _client
    if _client is not None:
        return _client

    if PROVIDER == "openai":
        from openai import OpenAI

        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
        _client = OpenAI(api_key=OPENAI_API_KEY)

    elif PROVIDER == "groq":
        from groq import Groq

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file. "
                "Get a free key at https://console.groq.com/keys"
            )
        _client = Groq(api_key=GROQ_API_KEY)

    elif PROVIDER == "anthropic":
        import anthropic

        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file."
            )
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    else:
        raise ValueError(
            f"Unknown PROVIDER '{PROVIDER}'. Use 'openai', 'groq', or 'anthropic'."
        )

    return _client


# ---------------------------------------------------------------------------
# Error classes resolved per provider (so we can catch rate limits generically)
# ---------------------------------------------------------------------------
def _error_classes():
    if PROVIDER == "openai":
        from openai import RateLimitError, APIError

        return RateLimitError, APIError
    if PROVIDER == "groq":
        from groq import RateLimitError, APIError

        return RateLimitError, APIError
    import anthropic

    return anthropic.RateLimitError, anthropic.APIError


# ---------------------------------------------------------------------------
# Public: chat
# ---------------------------------------------------------------------------
def chat(system: str, user: str, model: str, max_tokens: int) -> dict:
    """
    Send a system + user message to the configured provider and return the reply.
    Retries with exponential backoff on rate-limit errors.
    """
    client = _get_client()
    RateLimitError, APIError = _error_classes()
    delay = RETRY_DELAY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if PROVIDER in _OPENAI_COMPATIBLE:
                messages = (
                    ([{"role": "system", "content": system}] if system else [])
                    + [{"role": "user", "content": user}]
                )
                # gpt-5 / o-series reasoning models require max_completion_tokens
                # and reject the legacy max_tokens parameter.
                m = model.lower()
                if PROVIDER == "openai" and (m.startswith("gpt-5") or m.startswith("o")):
                    token_kwarg = {"max_completion_tokens": max_tokens}
                else:
                    token_kwarg = {"max_tokens": max_tokens}
                resp = client.chat.completions.create(
                    model=model, messages=messages, **token_kwarg
                )
                text = resp.choices[0].message.content or ""
                usage = resp.usage
                in_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
                out_tok = getattr(usage, "completion_tokens", 0) if usage else 0

            else:  # anthropic
                resp = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system or "",
                    messages=[{"role": "user", "content": user}],
                )
                text = resp.content[0].text
                in_tok = resp.usage.input_tokens
                out_tok = resp.usage.output_tokens

            time.sleep(CALL_PAUSE)
            return {
                "text": text,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "error": None,
            }

        except RateLimitError as e:
            if attempt == MAX_RETRIES:
                return {
                    "text": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "error": f"RateLimitError after {MAX_RETRIES} attempts: {e}",
                }
            print(f"    [Rate limit] Waiting {delay}s before retry {attempt}/{MAX_RETRIES}…")
            time.sleep(delay)
            delay *= 2

        except APIError as e:
            return {
                "text": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "error": f"APIError: {e}",
            }

    return {"text": "", "input_tokens": 0, "output_tokens": 0, "error": "Max retries exceeded"}
