"""
config.py — Central configuration for the Email Generation Assistant project.

Provider is selectable via the PROVIDER env var:
  PROVIDER=openai     → OpenAI (default).  Best quality; needs an OPENAI_API_KEY.
  PROVIDER=groq       → Groq Cloud, free tier.  Get a key:
                        https://console.groq.com/keys
  PROVIDER=anthropic  → Anthropic Claude (if you have an ANTHROPIC_API_KEY).

Both strategies run on the SAME model so the comparison isolates the impact of
prompt engineering rather than model capability. Model names are overridable via
env vars (MODEL_A / MODEL_B / JUDGE_MODEL) if you'd rather do a model-vs-model run.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider + API keys
# ---------------------------------------------------------------------------
PROVIDER = os.environ.get("PROVIDER", "openai").lower().strip()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

_KEY_BY_PROVIDER = {
    "openai": OPENAI_API_KEY,
    "groq": GROQ_API_KEY,
    "anthropic": ANTHROPIC_API_KEY,
}


def has_api_key() -> bool:
    """True if the key for the active provider is present."""
    return bool(_KEY_BY_PROVIDER.get(PROVIDER))


# ---------------------------------------------------------------------------
# Default model per provider
#   Strategy A → advanced prompt.   Strategy B → baseline prompt.
#   Same model for both, so any gap is attributable to prompt design alone.
#   Judge model is also the same model, used for all LLM-as-Judge metrics.
# ---------------------------------------------------------------------------
_DEFAULT_MODELS = {
    "openai": "gpt-5.4-mini",
    "groq": "llama-3.3-70b-versatile",
    "anthropic": "claude-sonnet-4-6",
}
_DEFAULT_MODEL = _DEFAULT_MODELS.get(PROVIDER, "gpt-4o")

MODEL_A_NAME = os.environ.get("MODEL_A", _DEFAULT_MODEL)
MODEL_B_NAME = os.environ.get("MODEL_B", _DEFAULT_MODEL)
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", _DEFAULT_MODEL)

MODEL_A_LABEL = f"Strategy A — Advanced prompt · {MODEL_A_NAME}"
MODEL_B_LABEL = f"Strategy B — Baseline prompt · {MODEL_B_NAME}"

# Human-readable name of the model actually in use (for reports)
MODEL_USED = MODEL_A_NAME

# ---------------------------------------------------------------------------
# Generation settings
# ---------------------------------------------------------------------------
# Generous budgets: gpt-5/o-series spend part of this on internal reasoning,
# so a tight cap can truncate the visible output.
MAX_TOKENS_GENERATE = 3000
MAX_TOKENS_JUDGE = 2500

# ---------------------------------------------------------------------------
# Retry / rate-limit settings
# ---------------------------------------------------------------------------
MAX_RETRIES = 4
RETRY_DELAY = 3    # seconds (doubles on each retry); Groq free tier is rate-limited
CALL_PAUSE = 1.5   # seconds between consecutive API calls

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
OUTPUT_DIR = "results/latest"
RESULTS_JSON = "evaluation_results.json"
RESULTS_CSV = "evaluation_report.csv"
ANALYSIS_REPORT = "analysis_report.md"
ANALYSIS_PDF = "analysis_report.pdf"
