"""
email_generator.py — Generates emails using Strategy A (advanced) or Strategy B (baseline).

Strategy A: configured model + Role-play + 6-step CoT + 3 Few-shot examples
Strategy B: configured model + Simple one-line system prompt (baseline)

Both strategies use identical inputs and the same model, so any difference in
output quality is attributable to prompt design alone — isolating the impact of
prompt engineering. Provider (Groq / Anthropic) is handled by src.llm_client.
"""

import time

from src.config import (
    MODEL_A_NAME,
    MODEL_B_NAME,
    MAX_TOKENS_GENERATE,
)
from src.llm_client import chat
from src.prompts import (
    ADVANCED_SYSTEM_PROMPT,
    ADVANCED_USER_TEMPLATE,
    BASELINE_SYSTEM_PROMPT,
    BASELINE_USER_TEMPLATE,
)


# ---------------------------------------------------------------------------
# Public: generate_email
# ---------------------------------------------------------------------------
def generate_email(
    intent: str,
    key_facts: list[str],
    tone: str,
    strategy: str = "A",
    model_override: str | None = None,
) -> dict:
    """
    Generate a professional email for the given inputs.

    Args:
        intent        : The core purpose of the email.
        key_facts     : List of facts that MUST appear in the email.
        tone          : Desired tone / style descriptor.
        strategy      : "A" → advanced prompt, "B" → baseline prompt.
        model_override: Override the default model for this call.

    Returns:
        {
            "email_text"     : str,
            "model"          : str,
            "strategy"       : str,
            "latency_seconds": float,
            "input_tokens"   : int,
            "output_tokens"  : int,
            "error"          : str | None
        }
    """
    strategy = strategy.upper()

    # ------------------------------------------------------------------
    # Build system + user messages
    # ------------------------------------------------------------------
    if strategy == "A":
        model = model_override or MODEL_A_NAME
        system_prompt = ADVANCED_SYSTEM_PROMPT
        facts_formatted = "\n".join(f"• {fact}" for fact in key_facts)
        user_message = ADVANCED_USER_TEMPLATE.format(
            intent=intent,
            facts_formatted=facts_formatted,
            tone=tone,
        )
    else:  # strategy == "B"
        model = model_override or MODEL_B_NAME
        system_prompt = BASELINE_SYSTEM_PROMPT
        facts_plain = "; ".join(key_facts)
        user_message = BASELINE_USER_TEMPLATE.format(
            intent=intent,
            facts_plain=facts_plain,
            tone=tone,
        )

    # ------------------------------------------------------------------
    # Call the model and measure latency
    # ------------------------------------------------------------------
    t0 = time.time()
    result = chat(system_prompt, user_message, model, MAX_TOKENS_GENERATE)
    latency = round(time.time() - t0, 2)

    return {
        "email_text": result["text"],
        "model": model,
        "strategy": strategy,
        "latency_seconds": latency,
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "error": result["error"],
    }
