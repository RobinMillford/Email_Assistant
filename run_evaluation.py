"""
run_evaluation.py — Main entry point for the evaluation pipeline.

USAGE
  # Full run (requires a key for the active provider — Groq by default)
  python run_evaluation.py

  # Test without an API key — loads realistic mock results
  python run_evaluation.py --dry-run

  # Run a single scenario (1-indexed)
  python run_evaluation.py --scenario 3

  # Run only one strategy
  python run_evaluation.py --strategy-a-only
  python run_evaluation.py --strategy-b-only

  # Skip PDF generation
  python run_evaluation.py --no-pdf

  # Custom output directory
  python run_evaluation.py --output-dir my_results

STRATEGY COMPARISON
  Strategy A: <model> + Role-play + 6-step CoT + 3 Few-shot examples
  Strategy B: <model> + Simple baseline prompt (no CoT, no examples)
  Both strategies use the SAME model, so the gap reflects prompt design only.

PROVIDER
  Set PROVIDER=groq (default) or PROVIDER=anthropic in your .env file.
"""

import argparse
import os
import sys
import time

# Ensure the project root is on sys.path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import (
    has_api_key,
    PROVIDER,
    MODEL_USED,
    MODEL_A_LABEL,
    MODEL_B_LABEL,
    OUTPUT_DIR,
)
from src.test_scenarios import SCENARIOS
from src.email_generator import generate_email
from src.evaluator import evaluate_email
from src.report_generator import (
    save_results_json,
    save_results_csv,
    generate_analysis_report,
    print_summary_table,
)


# ---------------------------------------------------------------------------
# Mock data for --dry-run mode
# ---------------------------------------------------------------------------
_MOCK_A_SCORES = [
    (0.92, 0.87, 0.90), (0.88, 0.84, 0.86), (0.94, 0.91, 0.88),
    (0.86, 0.82, 0.85), (0.90, 0.89, 0.92), (0.93, 0.88, 0.91),
    (0.85, 0.90, 0.87), (0.91, 0.86, 0.88), (0.89, 0.85, 0.90),
    (0.94, 0.92, 0.93),
]
_MOCK_B_SCORES = [
    (0.78, 0.72, 0.76), (0.74, 0.68, 0.74), (0.80, 0.75, 0.77),
    (0.72, 0.69, 0.73), (0.76, 0.71, 0.78), (0.79, 0.74, 0.76),
    (0.71, 0.76, 0.74), (0.77, 0.70, 0.75), (0.75, 0.69, 0.76),
    (0.80, 0.78, 0.80),
]


def _mock_eval(frs, tas, pess, ref_norm, is_a):
    comp = round((frs + tas + pess) / 3, 4)
    return {
        "fact_recall": {"score": frs, "total_facts": 5, "facts_present": round(frs * 5), "detail": []},
        "tone_alignment": {
            "score": tas, "raw_score": round(tas * 10),
            "observed_tone": "accurate" if is_a else "slightly generic",
            "positive_examples": "Tone alignment present.", "negative_examples": "none" if is_a else "minor drift",
        },
        "structure_quality": {
            "score": pess, "rule_score": min(pess + 0.05, 1.0), "llm_score": pess,
            "rule_checks": {"has_subject_line": True, "has_greeting": True,
                            "has_professional_closing": True, "has_multi_paragraph": True},
            "llm_raw_score": round(pess * 10), "structure_observations": "Well-structured.",
        },
        "composite_score": comp,
        "reference_alignment": {
            "score": ref_norm, "raw_score": round(ref_norm * 10),
            "coverage_score": round(ref_norm * 10), "tone_match_score": round(ref_norm * 10),
            "quality_score": round(ref_norm * 10),
            "comparison_notes": "Close to reference." if is_a else "Weaker than reference.",
        },
    }


def load_mock_results() -> dict:
    """Return realistic mock evaluation results for --dry-run mode."""
    scenarios = []
    for i, sc in enumerate(SCENARIOS):
        a_frs, a_tas, a_pess = _MOCK_A_SCORES[i]
        b_frs, b_tas, b_pess = _MOCK_B_SCORES[i]
        scenarios.append({
            "id": sc["id"], "name": sc["name"], "intent": sc["intent"],
            "tone": sc["tone"], "key_facts": sc["key_facts"],
            "strategy_a": {
                "model": MODEL_USED, "strategy": "A", "latency_seconds": round(2.1 + i * 0.15, 2),
                "input_tokens": 1420 + i * 12, "output_tokens": 290 + i * 8,
                "email_text": f"[MOCK] Strategy A email for scenario {sc['id']}: {sc['name']}",
                "error": None,
                "evaluation": _mock_eval(a_frs, a_tas, a_pess, round((a_frs + a_tas + a_pess) / 3 + 0.02, 4), True),
            },
            "strategy_b": {
                "model": MODEL_USED, "strategy": "B", "latency_seconds": round(1.6 + i * 0.10, 2),
                "input_tokens": 680 + i * 6, "output_tokens": 250 + i * 7,
                "email_text": f"[MOCK] Strategy B email for scenario {sc['id']}: {sc['name']}",
                "error": None,
                "evaluation": _mock_eval(b_frs, b_tas, b_pess, round((b_frs + b_tas + b_pess) / 3 - 0.03, 4), False),
            },
        })

    return {
        "run_type": "dry-run (mock data)",
        "provider": PROVIDER,
        "model_used": MODEL_USED,
        "strategy_a_label": MODEL_A_LABEL,
        "strategy_b_label": MODEL_B_LABEL,
        "scenarios": scenarios,
    }


# ---------------------------------------------------------------------------
# Live evaluation runner
# ---------------------------------------------------------------------------
_ZERO_EVAL = {
    "fact_recall": {"score": 0.0},
    "tone_alignment": {"score": 0.0},
    "structure_quality": {"score": 0.0},
    "composite_score": 0.0,
    "reference_alignment": {"score": 0.0},
}


def _run_strategy(label, scenario, strategy):
    print(f"\n  [Strategy {strategy} — {label}]")
    gen = generate_email(
        intent=scenario["intent"],
        key_facts=scenario["key_facts"],
        tone=scenario["tone"],
        strategy=strategy,
    )
    print(f"    Generated in {gen['latency_seconds']}s | "
          f"{gen['input_tokens']} in / {gen['output_tokens']} out tokens")

    if gen["error"]:
        print(f"    [!] Generation error: {gen['error']}")
        return {**gen, "evaluation": dict(_ZERO_EVAL)}

    print("    Evaluating…")
    ev = evaluate_email(
        gen["email_text"],
        scenario["key_facts"],
        scenario["tone"],
        reference_text=scenario.get("human_reference"),
    )
    print(
        f"    FRS={ev['fact_recall']['score']:.4f}  "
        f"TAS={ev['tone_alignment']['score']:.4f}  "
        f"PESS={ev['structure_quality']['score']:.4f}  "
        f"Composite={ev['composite_score']:.4f}  "
        f"RAS={ev.get('reference_alignment', {}).get('score', 0.0):.4f}"
    )
    return {**gen, "evaluation": ev}


def run_live_evaluation(scenarios, run_a=True, run_b=True) -> dict:
    evaluated = []
    total = len(scenarios)

    try:
        for idx, scenario in enumerate(scenarios, 1):
            print(f"\n{'─'*70}")
            print(f"  Scenario {idx}/{total}: {scenario['name']}")
            print(f"  Intent  : {scenario['intent']}")
            print(f"  Tone    : {scenario['tone']}")
            print(f"{'─'*70}")

            record = {
                "id": scenario["id"], "name": scenario["name"],
                "intent": scenario["intent"], "tone": scenario["tone"],
                "key_facts": scenario["key_facts"],
            }
            if run_a:
                record["strategy_a"] = _run_strategy("Advanced Prompt", scenario, "A")
            if run_b:
                record["strategy_b"] = _run_strategy("Baseline Prompt", scenario, "B")

            evaluated.append(record)

            if idx < total:
                print("\n  Pausing 2s before next scenario…")
                time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n  [!] Interrupted — saving partial results ({len(evaluated)}/{total} scenarios).")
    except Exception as e:  # noqa: BLE001 — keep whatever completed
        print(f"\n  [!] Run stopped ({type(e).__name__}: {e}) — saving partial results "
              f"({len(evaluated)}/{total} scenarios).")

    return {
        "run_type": "live",
        "provider": PROVIDER,
        "model_used": MODEL_USED,
        "strategy_a_label": MODEL_A_LABEL,
        "strategy_b_label": MODEL_B_LABEL,
        "scenarios": evaluated,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Email Generation Assistant — Evaluation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dry-run", action="store_true",
                   help="Load mock results instead of calling the API (no key required).")
    p.add_argument("--scenario", type=int, metavar="N",
                   help="Run only scenario N (1-indexed). Default: all 10.")
    p.add_argument("--strategy-a-only", action="store_true", help="Run Strategy A only.")
    p.add_argument("--strategy-b-only", action="store_true", help="Run Strategy B only.")
    p.add_argument("--no-pdf", action="store_true", help="Skip PDF generation.")
    p.add_argument("--output-dir", type=str, default=None,
                   help=f"Override output directory (default: '{OUTPUT_DIR}').")
    return p.parse_args()


def _write_reports(results, make_pdf, out_dir):
    print_summary_table(results)
    save_results_json(results)
    save_results_csv(results)
    md_path = generate_analysis_report(results)
    if make_pdf:
        try:
            from src.pdf_report import generate_pdf_report
            generate_pdf_report(results)
        except Exception as e:
            print(f"  [!] PDF generation skipped: {e}")
    print("\n  [✓] Done. Reports saved to:", out_dir)


def main():
    args = parse_args()

    if args.output_dir:
        import src.config as cfg
        cfg.OUTPUT_DIR = args.output_dir

    out_dir = args.output_dir or OUTPUT_DIR

    print("\n" + "=" * 70)
    print("  Email Generation Assistant — Evaluation Pipeline")
    print("=" * 70)

    # DRY-RUN
    if args.dry_run:
        print("\n  MODE: DRY-RUN (mock data — no API calls)\n")
        _write_reports(load_mock_results(), not args.no_pdf, out_dir)
        return

    # LIVE — check key
    if not has_api_key():
        key_name = "GROQ_API_KEY" if PROVIDER == "groq" else "ANTHROPIC_API_KEY"
        hint = ("  Get a free Groq key at https://console.groq.com/keys\n"
                if PROVIDER == "groq" else "")
        print(
            f"\n  [ERROR] {key_name} not found for PROVIDER='{PROVIDER}'.\n"
            f"  Create a .env file with:\n    {key_name}=your-key-here\n"
            f"{hint}"
            "  Or run with --dry-run to test without a key.\n"
        )
        sys.exit(1)

    print(f"\n  MODE: LIVE  |  Provider: {PROVIDER}  |  Model: {MODEL_USED}")
    print(f"  Strategy A: {MODEL_A_LABEL}")
    print(f"  Strategy B: {MODEL_B_LABEL}\n")

    scenarios = SCENARIOS
    if args.scenario:
        scenarios = [s for s in SCENARIOS if s["id"] == args.scenario]
        if not scenarios:
            print(f"  [ERROR] No scenario with id={args.scenario}. Valid IDs: 1–10.")
            sys.exit(1)
        print(f"  Running single scenario: [{args.scenario}] {scenarios[0]['name']}")
    else:
        print(f"  Running all {len(SCENARIOS)} scenarios…")

    run_a = not args.strategy_b_only
    run_b = not args.strategy_a_only
    if not run_a and not run_b:
        print("  [ERROR] Cannot use --strategy-a-only and --strategy-b-only together.")
        sys.exit(1)

    results = run_live_evaluation(scenarios, run_a, run_b)
    _write_reports(results, not args.no_pdf, out_dir)


if __name__ == "__main__":
    main()
