"""
evaluator.py — Implements the evaluation metrics.

THREE REQUIRED CUSTOM METRICS (composite is their equal-weighted average):

METRIC 1: Fact Recall Score (FRS)
    Method: LLM-as-Judge
    Logic : Judge checks whether each input fact is semantically present in the email.
            Score = facts_present / total_facts  (range 0.0 – 1.0)
    Why   : A business email that omits key facts fails its primary purpose.

METRIC 2: Tone Alignment Score (TAS)
    Method: LLM-as-Judge
    Logic : Judge rates tone match on a 1–10 rubric; normalised to 0.0–1.0.
    Why   : Professional communication depends on tone being correctly calibrated.

METRIC 3: Professional Email Structure Score (PESS)
    Method: 40% rule-based Python checks + 60% LLM-as-Judge quality score
    Logic : Rule layer checks subject line, greeting, professional closing, and
            multi-paragraph body. LLM layer rates holistic structure on 1–10.
            Final = 0.4 × rule_score + 0.6 × llm_score.
    Why   : Combines hard structural requirements with nuanced quality assessment.

SUPPLEMENTARY METRIC: Reference Alignment Score (RAS)
    Method: LLM-as-Judge, comparing the generated email against the HUMAN REFERENCE.
    Logic : Judge scores coverage + tone-match + quality vs the ideal email; 1–10
            overall alignment, normalised to 0.0–1.0.
    Why   : The only metric that uses the human-written reference emails. It
            validates the three standalone metrics against a human gold standard
            and is reported separately (not folded into the composite).
"""

import json
import re

from src.config import (
    JUDGE_MODEL,
    MAX_TOKENS_JUDGE,
)
from src.llm_client import chat
from src.prompts import (
    FACT_RECALL_JUDGE,
    TONE_ALIGNMENT_JUDGE,
    STRUCTURE_QUALITY_JUDGE,
    REFERENCE_ALIGNMENT_JUDGE,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _call_judge(user_content: str) -> str:
    """Call the LLM judge and return its raw text response (expected JSON)."""
    result = chat(system="", user=user_content, model=JUDGE_MODEL, max_tokens=MAX_TOKENS_JUDGE)
    if result["error"]:
        return "{}"
    return result["text"]


def _parse_json_safe(text: str, fallback: dict) -> dict:
    """Parse JSON that may be wrapped in markdown fences; regex-extract as fallback."""
    clean = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return fallback


# ---------------------------------------------------------------------------
# METRIC 1 — Fact Recall Score (FRS)
# ---------------------------------------------------------------------------
def evaluate_fact_recall(email_text: str, key_facts: list[str]) -> dict:
    facts_json_str = json.dumps(key_facts, indent=2)
    prompt = FACT_RECALL_JUDGE.format(email=email_text, facts_json=facts_json_str)

    raw = _call_judge(prompt)
    fallback = {
        "fact_evaluations": [],
        "total_facts": len(key_facts),
        "facts_present": 0,
        "score": 0.0,
    }
    parsed = _parse_json_safe(raw, fallback)

    total = parsed.get("total_facts", len(key_facts))
    present = parsed.get("facts_present", 0)
    score = parsed.get("score", present / total if total > 0 else 0.0)

    return {
        "score": round(float(score), 4),
        "total_facts": total,
        "facts_present": present,
        "detail": parsed.get("fact_evaluations", []),
    }


# ---------------------------------------------------------------------------
# METRIC 2 — Tone Alignment Score (TAS)
# ---------------------------------------------------------------------------
def evaluate_tone_alignment(email_text: str, tone: str) -> dict:
    prompt = TONE_ALIGNMENT_JUDGE.format(tone=tone, email=email_text)

    raw = _call_judge(prompt)
    fallback = {
        "requested_tone": tone,
        "observed_tone": "unknown",
        "alignment_score": 5,
        "normalized_score": 0.5,
        "positive_examples": "",
        "negative_examples": "",
    }
    parsed = _parse_json_safe(raw, fallback)

    raw_score = parsed.get("alignment_score", 5)
    normalized = parsed.get("normalized_score", round(raw_score / 10, 4))

    return {
        "score": round(float(normalized), 4),
        "raw_score": int(raw_score),
        "observed_tone": parsed.get("observed_tone", ""),
        "positive_examples": parsed.get("positive_examples", ""),
        "negative_examples": parsed.get("negative_examples", ""),
    }


# ---------------------------------------------------------------------------
# METRIC 3 — Professional Email Structure Score (PESS)
# ---------------------------------------------------------------------------
def _rule_based_structure_score(email_text: str) -> tuple[float, dict]:
    """Four binary structural checks, 0.25 each → rule_score in [0,1]."""
    lines = email_text.strip().splitlines()
    text_lower = email_text.lower()

    has_subject = any(line.strip().lower().startswith("subject:") for line in lines[:5])

    has_greeting = any(
        text_lower.startswith(g) or f"\n{g}" in text_lower
        for g in ("dear ", "hi ", "hello ", "good morning", "good afternoon")
    )

    professional_closings = [
        "sincerely", "regards", "best regards", "yours", "warmly",
        "kind regards", "faithfully", "respectfully", "thank you",
        "warm regards", "many thanks",
    ]
    has_closing = any(c in text_lower for c in professional_closings)

    non_empty_lines = [l for l in lines if l.strip()]
    has_multi_paragraph = len(non_empty_lines) >= 6

    checks = {
        "has_subject_line": has_subject,
        "has_greeting": has_greeting,
        "has_professional_closing": has_closing,
        "has_multi_paragraph": has_multi_paragraph,
    }

    passed = sum(1 for v in checks.values() if v)
    return passed / 4.0, checks


def evaluate_structure_quality(email_text: str) -> dict:
    """Hybrid metric: 40% rule-based + 60% LLM judge."""
    rule_score, rule_checks = _rule_based_structure_score(email_text)

    prompt = STRUCTURE_QUALITY_JUDGE.format(email=email_text)
    raw = _call_judge(prompt)
    fallback = {
        "structure_score": 5,
        "normalized_score": 0.5,
        "structure_observations": "Could not evaluate.",
    }
    parsed = _parse_json_safe(raw, fallback)

    llm_raw = parsed.get("structure_score", 5)
    llm_score = parsed.get("normalized_score", round(llm_raw / 10, 4))

    composite = round(0.4 * rule_score + 0.6 * float(llm_score), 4)

    return {
        "score": composite,
        "rule_score": round(rule_score, 4),
        "llm_score": round(float(llm_score), 4),
        "rule_checks": rule_checks,
        "llm_raw_score": int(llm_raw),
        "structure_observations": parsed.get("structure_observations", ""),
    }


# ---------------------------------------------------------------------------
# SUPPLEMENTARY METRIC — Reference Alignment Score (RAS)
# ---------------------------------------------------------------------------
def evaluate_reference_alignment(email_text: str, reference_text: str) -> dict:
    """
    Compare the generated email against the human-written reference email.
    This is the only metric that uses the scenario's human_reference.
    """
    if not reference_text:
        return {
            "score": 0.0,
            "raw_score": 0,
            "coverage_score": 0,
            "tone_match_score": 0,
            "quality_score": 0,
            "comparison_notes": "No reference provided.",
        }

    prompt = REFERENCE_ALIGNMENT_JUDGE.format(reference=reference_text, email=email_text)
    raw = _call_judge(prompt)
    fallback = {
        "coverage_score": 5,
        "tone_match_score": 5,
        "quality_score": 5,
        "alignment_score": 5,
        "normalized_score": 0.5,
        "comparison_notes": "Could not evaluate.",
    }
    parsed = _parse_json_safe(raw, fallback)

    raw_score = parsed.get("alignment_score", 5)
    normalized = parsed.get("normalized_score", round(raw_score / 10, 4))

    return {
        "score": round(float(normalized), 4),
        "raw_score": int(raw_score),
        "coverage_score": int(parsed.get("coverage_score", 0)),
        "tone_match_score": int(parsed.get("tone_match_score", 0)),
        "quality_score": int(parsed.get("quality_score", 0)),
        "comparison_notes": parsed.get("comparison_notes", ""),
    }


# ---------------------------------------------------------------------------
# Master evaluator
# ---------------------------------------------------------------------------
def evaluate_email(
    email_text: str,
    key_facts: list[str],
    tone: str,
    reference_text: str | None = None,
) -> dict:
    """
    Run all metrics and return a combined evaluation dict.

    The composite_score is the equal-weighted average of the THREE required
    custom metrics (FRS, TAS, PESS). Reference Alignment (RAS) is reported
    separately and is NOT folded into the composite.
    """
    print("      → Running Fact Recall evaluation…")
    frs = evaluate_fact_recall(email_text, key_facts)

    print("      → Running Tone Alignment evaluation…")
    tas = evaluate_tone_alignment(email_text, tone)

    print("      → Running Structure Quality evaluation…")
    pess = evaluate_structure_quality(email_text)

    composite = round((frs["score"] + tas["score"] + pess["score"]) / 3, 4)

    result = {
        "fact_recall": frs,
        "tone_alignment": tas,
        "structure_quality": pess,
        "composite_score": composite,
    }

    if reference_text is not None:
        print("      → Running Reference Alignment evaluation…")
        result["reference_alignment"] = evaluate_reference_alignment(email_text, reference_text)

    return result
