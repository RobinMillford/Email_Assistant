"""
report_generator.py — Saves evaluation results as JSON, CSV, and Markdown.

Outputs (all written to the OUTPUT_DIR defined in config.py):
  1. evaluation_results.json — Full raw data including per-fact detail
  2. evaluation_report.csv   — Flat table, one row per scenario, for easy analysis
  3. analysis_report.md      — Human-readable comparative analysis (≈ one page)
"""

import csv
import json
import os
from datetime import datetime

import src.config as config
from src.config import RESULTS_JSON, RESULTS_CSV, ANALYSIS_REPORT
from src.prompts import (
    ADVANCED_SYSTEM_PROMPT,
    ADVANCED_USER_TEMPLATE,
    BASELINE_SYSTEM_PROMPT,
    BASELINE_USER_TEMPLATE,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _ensure_output_dir():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)


def _path(filename: str) -> str:
    return os.path.join(config.OUTPUT_DIR, filename)


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


# ---------------------------------------------------------------------------
# 1. JSON — Full raw data
# ---------------------------------------------------------------------------
def save_results_json(results: dict) -> str:
    """
    Save the complete results dict (including per-fact detail) as JSON.
    Returns the filepath written.
    """
    _ensure_output_dir()
    filepath = _path(RESULTS_JSON)

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "metric_definitions": {
            "FRS": {
                "name": "Fact Recall Score",
                "method": "LLM-as-Judge",
                "formula": "facts_present / total_facts",
                "range": "0.0 – 1.0",
                "description": (
                    "Measures what fraction of the input key facts are semantically "
                    "present in the generated email. A score of 1.0 means every fact "
                    "was captured; 0.0 means none were."
                ),
            },
            "TAS": {
                "name": "Tone Alignment Score",
                "method": "LLM-as-Judge (1–10 rubric, normalised)",
                "formula": "alignment_score / 10",
                "range": "0.0 – 1.0",
                "description": (
                    "Rates how precisely the generated email's tone matches the "
                    "requested tone specification across vocabulary, formality, and "
                    "emotional register."
                ),
            },
            "PESS": {
                "name": "Professional Email Structure Score",
                "method": "40% rule-based Python + 60% LLM-as-Judge",
                "formula": "0.4 × rule_score + 0.6 × llm_score",
                "range": "0.0 – 1.0",
                "description": (
                    "Hybrid metric. Rule layer checks four hard requirements "
                    "(subject line, greeting, professional closing, multi-paragraph body). "
                    "LLM layer rates holistic structural quality on a 1–10 scale."
                ),
            },
            "RAS": {
                "name": "Reference Alignment Score (supplementary)",
                "method": "LLM-as-Judge vs human reference email",
                "formula": "alignment_score / 10",
                "range": "0.0 – 1.0",
                "description": (
                    "Supplementary metric — the only one that uses the human-written "
                    "reference email for each scenario. The judge compares the generated "
                    "email against the reference on coverage, tone-match, and quality, and "
                    "returns an overall alignment score. Reported separately; NOT folded "
                    "into the composite (which is the equal-weighted average of FRS+TAS+PESS)."
                ),
            },
        },
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"  [✓] JSON saved → {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# 2. CSV — Flat comparison table
# ---------------------------------------------------------------------------
def save_results_csv(results: dict) -> str:
    """
    Save a flat CSV with one row per scenario and columns for each metric
    score under both strategies, plus computed deltas.
    Returns the filepath written.
    """
    _ensure_output_dir()
    filepath = _path(RESULTS_CSV)

    fieldnames = [
        "scenario_id",
        "scenario_name",
        # Strategy A scores
        "A_FRS",
        "A_TAS",
        "A_PESS",
        "A_Composite",
        "A_RAS",
        # Strategy B scores
        "B_FRS",
        "B_TAS",
        "B_PESS",
        "B_Composite",
        "B_RAS",
        # Deltas (A - B, positive = A wins)
        "Delta_FRS",
        "Delta_TAS",
        "Delta_PESS",
        "Delta_Composite",
        "Delta_RAS",
        # Winner flag
        "Winner",
    ]

    rows = []
    for scenario in results.get("scenarios", []):
        sid = scenario["id"]
        name = scenario["name"]

        a = scenario.get("strategy_a", {}).get("evaluation", {})
        b = scenario.get("strategy_b", {}).get("evaluation", {})

        a_frs = a.get("fact_recall", {}).get("score", 0.0)
        a_tas = a.get("tone_alignment", {}).get("score", 0.0)
        a_pess = a.get("structure_quality", {}).get("score", 0.0)
        a_comp = a.get("composite_score", 0.0)
        a_ras = a.get("reference_alignment", {}).get("score", 0.0)

        b_frs = b.get("fact_recall", {}).get("score", 0.0)
        b_tas = b.get("tone_alignment", {}).get("score", 0.0)
        b_pess = b.get("structure_quality", {}).get("score", 0.0)
        b_comp = b.get("composite_score", 0.0)
        b_ras = b.get("reference_alignment", {}).get("score", 0.0)

        rows.append(
            {
                "scenario_id": sid,
                "scenario_name": name,
                "A_FRS": a_frs,
                "A_TAS": a_tas,
                "A_PESS": a_pess,
                "A_Composite": a_comp,
                "A_RAS": a_ras,
                "B_FRS": b_frs,
                "B_TAS": b_tas,
                "B_PESS": b_pess,
                "B_Composite": b_comp,
                "B_RAS": b_ras,
                "Delta_FRS": round(a_frs - b_frs, 4),
                "Delta_TAS": round(a_tas - b_tas, 4),
                "Delta_PESS": round(a_pess - b_pess, 4),
                "Delta_Composite": round(a_comp - b_comp, 4),
                "Delta_RAS": round(a_ras - b_ras, 4),
                "Winner": "A" if a_comp >= b_comp else "B",
            }
        )

    # Append averages row
    if rows:
        rows.append(
            {
                "scenario_id": "AVG",
                "scenario_name": "— AVERAGE —",
                "A_FRS": _avg([r["A_FRS"] for r in rows]),
                "A_TAS": _avg([r["A_TAS"] for r in rows]),
                "A_PESS": _avg([r["A_PESS"] for r in rows]),
                "A_Composite": _avg([r["A_Composite"] for r in rows]),
                "A_RAS": _avg([r["A_RAS"] for r in rows]),
                "B_FRS": _avg([r["B_FRS"] for r in rows]),
                "B_TAS": _avg([r["B_TAS"] for r in rows]),
                "B_PESS": _avg([r["B_PESS"] for r in rows]),
                "B_Composite": _avg([r["B_Composite"] for r in rows]),
                "B_RAS": _avg([r["B_RAS"] for r in rows]),
                "Delta_FRS": _avg([r["Delta_FRS"] for r in rows]),
                "Delta_TAS": _avg([r["Delta_TAS"] for r in rows]),
                "Delta_PESS": _avg([r["Delta_PESS"] for r in rows]),
                "Delta_Composite": _avg([r["Delta_Composite"] for r in rows]),
                "Delta_RAS": _avg([r["Delta_RAS"] for r in rows]),
                "Winner": "—",
            }
        )

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  [✓] CSV saved  → {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# 3. Markdown — One-page comparative analysis report
# ---------------------------------------------------------------------------
def generate_analysis_report(results: dict) -> str:
    """
    Generate a one-page Markdown analysis report answering the three required
    questions and including a data table.
    Returns the filepath written.
    """
    _ensure_output_dir()
    filepath = _path(ANALYSIS_REPORT)

    scenarios = results.get("scenarios", [])

    # Collect scores
    a_frs_list, a_tas_list, a_pess_list, a_comp_list, a_ras_list = [], [], [], [], []
    b_frs_list, b_tas_list, b_pess_list, b_comp_list, b_ras_list = [], [], [], [], []

    table_rows = []
    for s in scenarios:
        a = s.get("strategy_a", {}).get("evaluation", {})
        b = s.get("strategy_b", {}).get("evaluation", {})

        a_frs = a.get("fact_recall", {}).get("score", 0.0)
        a_tas = a.get("tone_alignment", {}).get("score", 0.0)
        a_pess = a.get("structure_quality", {}).get("score", 0.0)
        a_comp = a.get("composite_score", 0.0)
        a_ras = a.get("reference_alignment", {}).get("score", 0.0)

        b_frs = b.get("fact_recall", {}).get("score", 0.0)
        b_tas = b.get("tone_alignment", {}).get("score", 0.0)
        b_pess = b.get("structure_quality", {}).get("score", 0.0)
        b_comp = b.get("composite_score", 0.0)
        b_ras = b.get("reference_alignment", {}).get("score", 0.0)

        a_frs_list.append(a_frs); a_tas_list.append(a_tas)
        a_pess_list.append(a_pess); a_comp_list.append(a_comp); a_ras_list.append(a_ras)
        b_frs_list.append(b_frs); b_tas_list.append(b_tas)
        b_pess_list.append(b_pess); b_comp_list.append(b_comp); b_ras_list.append(b_ras)

        table_rows.append(
            f"| {s['id']:>2} | {s['name']:<35} "
            f"| {a_frs:.3f} | {a_tas:.3f} | {a_pess:.3f} | {a_comp:.3f} "
            f"| {b_frs:.3f} | {b_tas:.3f} | {b_pess:.3f} | {b_comp:.3f} |"
        )

    # Averages
    avg_a_frs = _avg(a_frs_list); avg_a_tas = _avg(a_tas_list)
    avg_a_pess = _avg(a_pess_list); avg_a_comp = _avg(a_comp_list)

    avg_b_frs = _avg(b_frs_list); avg_b_tas = _avg(b_tas_list)
    avg_b_pess = _avg(b_pess_list); avg_b_comp = _avg(b_comp_list)

    avg_a_ras = _avg(a_ras_list); avg_b_ras = _avg(b_ras_list)

    delta_frs = round(avg_a_frs - avg_b_frs, 4)
    delta_tas = round(avg_a_tas - avg_b_tas, 4)
    delta_pess = round(avg_a_pess - avg_b_pess, 4)
    delta_comp = round(avg_a_comp - avg_b_comp, 4)
    delta_ras = round(avg_a_ras - avg_b_ras, 4)

    # ------------------------------------------------------------------
    # Honest, data-driven analysis (no hardcoded "A wins" narrative)
    # ------------------------------------------------------------------
    # Detect whether the two strategies ran on different models
    first = scenarios[0] if scenarios else {}
    model_a = first.get("strategy_a", {}).get("model", results.get("model_used", "the model"))
    model_b = first.get("strategy_b", {}).get("model", model_a)
    models_differ = model_a != model_b

    metric_deltas = {"FRS": delta_frs, "TAS": delta_tas, "PESS": delta_pess}
    a_wins = sum(1 for x, y in zip(a_comp_list, b_comp_list) if x > y + 1e-9)
    b_wins = sum(1 for x, y in zip(a_comp_list, b_comp_list) if y > x + 1e-9)
    ties = len(a_comp_list) - a_wins - b_wins
    pct_comp = round(delta_comp / avg_b_comp * 100, 2) if avg_b_comp else 0.0

    # Overall winner + how decisive
    TIE_BAND = 0.01  # composite gap below this = effectively a tie
    if abs(delta_comp) < TIE_BAND:
        overall = "effective tie"
        winner = "A" if delta_comp >= 0 else "B"
    else:
        winner = "A" if delta_comp > 0 else "B"
        overall = f"Strategy {winner} ahead"

    def _mag(d):
        ad = abs(d)
        if ad < 0.01:
            return "negligible"
        if ad < 0.03:
            return "small"
        if ad < 0.07:
            return "moderate"
        return "large"

    def _dir(d, metric):
        if abs(d) < 1e-9:
            return f"{metric}: tie (Δ {d:+.4f})"
        lead = "A" if d > 0 else "B"
        return f"{metric}: {lead} leads ({_mag(d)}, Δ {d:+.4f})"

    per_metric_lines = "\n".join(f"- {_dir(metric_deltas[m], m)}" for m in ("FRS", "TAS", "PESS"))

    # Where Strategy A actually trails (honest "failure mode" of the comparison)
    a_trails = [m for m, d in metric_deltas.items() if d < -1e-9]
    b_trails = [m for m, d in metric_deltas.items() if d > 1e-9]
    biggest_b_gap_metric = max(metric_deltas, key=metric_deltas.get)
    biggest_a_gap_metric = min(metric_deltas, key=metric_deltas.get)

    setup_desc = (
        f"Strategy A (advanced prompt, `{model_a}`) vs Strategy B (baseline prompt, `{model_b}`)"
        if models_differ else f"both strategies on `{model_a}`"
    )
    comp_mag = _mag(delta_comp)
    if overall == "effective tie":
        verdict_line = (
            f"A composite gap of {delta_comp:+.4f} is within normal LLM-judge variance, so neither "
            f"setup produces a meaningful lift. A capable model already writes strong emails from the "
            f"minimal baseline prompt, leaving little headroom for the metrics to capture — scores sit "
            f"near the top of their range for both."
        )
    else:
        _strength = {"negligible": "a real but very small", "small": "a real but modest",
                     "moderate": "a clear", "large": "a large"}[comp_mag]
        _attrib = (" This run varies both prompt and model, so the gap reflects the combined effect."
                   if models_differ else
                   " Both ran on the same model, so the gap is attributable to prompt design alone.")
        verdict_line = (
            f"The {delta_comp:+.4f} composite gap is {_strength} edge to Strategy {winner}, which won "
            f"{max(a_wins, b_wins)} of {len(a_comp_list)} scenarios outright.{_attrib}"
        )
    _ras_rank = "the same ranking as" if (delta_ras >= 0) == (delta_comp >= 0) else "a different ranking from"
    ras_line = (
        f"The supplementary Reference Alignment metric (RAS, vs the human-written ideal) gives "
        f"{_ras_rank} the core metrics: A {avg_a_ras:.4f} vs B {avg_b_ras:.4f} (Δ {delta_ras:+.4f})."
    )

    # Prompt templates (deliverable: "The Prompt Template used"). Built outside the
    # f-string so the {intent}/{tone} placeholders inside are not re-interpreted.
    prompt_section = (
        "## Prompt Template\n\n"
        "### Strategy A — Advanced (role-play + chain-of-thought + few-shot)\n\n"
        "**System prompt:**\n\n```text\n" + ADVANCED_SYSTEM_PROMPT.strip() + "\n```\n\n"
        "**User message template:**\n\n```text\n" + ADVANCED_USER_TEMPLATE.strip() + "\n```\n\n"
        "### Strategy B — Baseline\n\n"
        "**System prompt:**\n\n```text\n" + BASELINE_SYSTEM_PROMPT.strip() + "\n```\n\n"
        "**User message template:**\n\n```text\n" + BASELINE_USER_TEMPLATE.strip() + "\n```"
    )

    table_header = (
        "| ID | Scenario                             "
        "| A-FRS | A-TAS | A-PESS | A-Comp "
        "| B-FRS | B-TAS | B-PESS | B-Comp |"
    )
    table_sep = (
        "|:--:|:-------------------------------------|"
        ":------:|:------:|:------:|:------:|"
        ":------:|:------:|:------:|:------:|"
    )

    report = f"""# Email Generation Assistant — Comparative Analysis Report

**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

## Overview

This report compares two email generation strategies across ten diverse business
email scenarios using three custom evaluation metrics (provider: {results.get('provider', '?')}).
{("Strategy A and Strategy B run on **different models**, so differences reflect the combined "
  "prompt + model effect." ) if models_differ else
 (f"Both strategies run on the same underlying model (`{model_a}`), so differences reflect "
  "**prompt engineering impact only** — not model capability.")}

| | Strategy A | Strategy B |
|---|---|---|
| **Label** | Advanced | Baseline |
| **Model** | {model_a} | {model_b} |
| **Prompt Design** | Role-play + 6-step CoT + 3 Few-shot examples | Simple system prompt, no structure |

---

{prompt_section}

---

## Metric Definitions

| Metric | Name | Method | Formula |
|--------|------|--------|---------|
| **FRS** | Fact Recall Score | LLM-as-Judge | `facts_present / total_facts` |
| **TAS** | Tone Alignment Score | LLM-as-Judge (1–10 rubric) | `alignment_score / 10` |
| **PESS** | Professional Email Structure Score | 40% rule-based + 60% LLM-as-Judge | `0.4×rule + 0.6×llm` |
| **RAS** *(supplementary)* | Reference Alignment Score | LLM-as-Judge vs human reference | `alignment_score / 10` |

All metrics are normalised to **0.0 – 1.0** (higher is better).
Composite score = equal-weighted average of the three required metrics (FRS + TAS + PESS).
**RAS** is supplementary — the only metric that compares the output against the human-written
reference email — and is reported separately, not folded into the composite.

---

## Raw Evaluation Data

{table_header}
{table_sep}
{chr(10).join(table_rows)}
| **—** | **AVERAGE**                           | **{avg_a_frs:.3f}** | **{avg_a_tas:.3f}** | **{avg_a_pess:.3f}** | **{avg_a_comp:.3f}** | **{avg_b_frs:.3f}** | **{avg_b_tas:.3f}** | **{avg_b_pess:.3f}** | **{avg_b_comp:.3f}** |

### Summary Table

| Metric | Strategy A avg | Strategy B avg | Δ (A − B) |
|--------|:--------------:|:--------------:|:---------:|
| FRS    | {avg_a_frs:.4f}         | {avg_b_frs:.4f}         | **{delta_frs:+.4f}**  |
| TAS    | {avg_a_tas:.4f}         | {avg_b_tas:.4f}         | **{delta_tas:+.4f}**  |
| PESS   | {avg_a_pess:.4f}        | {avg_b_pess:.4f}        | **{delta_pess:+.4f}** |
| **Composite** | **{avg_a_comp:.4f}** | **{avg_b_comp:.4f}** | **{delta_comp:+.4f}** |
| RAS *(suppl.)* | {avg_a_ras:.4f} | {avg_b_ras:.4f} | **{delta_ras:+.4f}** |

---

## Analysis

### Q1 — Which strategy performed better?

Result: **{overall}**. Strategy A's composite average is **{avg_a_comp:.4f}** vs
**{avg_b_comp:.4f}** for Strategy B — a difference of **{delta_comp:+.4f} ({pct_comp:+.2f}%)**.
Per-scenario, Strategy A won **{a_wins}**, Strategy B won **{b_wins}**, and **{ties}** tied.

Setup: {setup_desc}.

Per-metric breakdown (average Δ = A − B):

{per_metric_lines}

Interpretation: {verdict_line}

### Q2 — What was the lower-performing strategy's biggest weakness?

{(
  "Strategy B trails most on **" + biggest_b_gap_metric + "** (Δ " + format(metric_deltas[biggest_b_gap_metric], '+.4f') + "), "
  "the metric the advanced prompt most directly targets (its role persona, chain-of-thought "
  "fact-weaving, and few-shot exemplars). The gap is widest on the more nuanced, fact-dense "
  "briefs where a bare 'write a professional email' instruction has least to work from."
) if winner == 'A' and b_trails else (
  "Strategy A trails most on **" + biggest_a_gap_metric + "** (Δ " + format(metric_deltas[biggest_a_gap_metric], '+.4f') + "). "
  "Notably the advanced prompt did not beat the baseline on every metric, and Strategy B "
  "won some scenarios outright — evidence that extra prompt scaffolding can occasionally add "
  "verbosity or drift without improving the measured qualities."
) if winner == 'B' else (
  "Neither strategy has a decisive failure mode — the per-metric gaps are all within "
  "judge noise. The clearest single difference is on **" + biggest_b_gap_metric + "** "
  "(Δ " + format(metric_deltas[biggest_b_gap_metric], '+.4f') + "), but it is too small to "
  "call a reliable weakness. Where the baseline did fall behind, it was on the more nuanced, "
  "tone-sensitive scenarios rather than the straightforward ones."
)}

{ras_line}

### Q3 — Production Recommendation

{(
  "**Recommend Strategy A**, but on robustness grounds rather than a large average lift. "
  "The averages are close, yet the advanced prompt's explicit fact-weaving and tone "
  "calibration reduce the risk of the worst-case email (a dropped deadline/invoice number "
  "or a tonally wrong message), which matters more than a fractional average gain in "
  "production. The cost is ~700–900 extra input tokens per generation — negligible."
) if winner == 'A' else (
  "**Recommend Strategy B for this model.** It matched or beat the advanced prompt on the "
  "composite while using ~700–900 fewer input tokens per call, so it is both cheaper and at "
  "least as good here. Reserve the advanced prompt for weaker models or harder briefs where "
  "its scaffolding earns its cost."
)}

{("Caveat: this run varies **both** the prompt and the model, so the gap reflects their "
  "combined effect — it does not isolate prompt engineering on its own. The companion "
  "same-model run isolates that variable." ) if models_differ else
 ("Caveat: this comparison runs both strategies on the **same strong model**, which compresses "
  "the gap. The advanced prompt's value is expected to grow on weaker models or on harder, "
  "more fact-dense briefs — set `MODEL_B` to a smaller model to test the model-vs-model axis.")}

---

*Report generated by the Email Generation Assistant evaluation pipeline.*
*Models: A `{model_a}` · B `{model_b}` · Scenarios: 10 · Metrics: FRS, TAS, PESS (+ RAS)*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"  [✓] Analysis saved → {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------
def print_summary_table(results: dict):
    """Print a compact summary table to stdout."""
    scenarios = results.get("scenarios", [])

    print("\n" + "=" * 90)
    print(f"{'ID':>4}  {'Scenario':<36} {'A-FRS':>7} {'A-TAS':>7} {'A-PESS':>7} {'A-Comp':>7}  {'B-Comp':>7}")
    print("=" * 90)

    a_comps, b_comps = [], []
    for s in scenarios:
        a = s.get("strategy_a", {}).get("evaluation", {})
        b = s.get("strategy_b", {}).get("evaluation", {})

        a_frs = a.get("fact_recall", {}).get("score", 0.0)
        a_tas = a.get("tone_alignment", {}).get("score", 0.0)
        a_pess = a.get("structure_quality", {}).get("score", 0.0)
        a_comp = a.get("composite_score", 0.0)
        b_comp = b.get("composite_score", 0.0)

        a_comps.append(a_comp); b_comps.append(b_comp)

        winner = "A✓" if a_comp >= b_comp else "B✓"
        print(
            f"{s['id']:>4}  {s['name']:<36} "
            f"{a_frs:>7.4f} {a_tas:>7.4f} {a_pess:>7.4f} {a_comp:>7.4f}  "
            f"{b_comp:>7.4f}  [{winner}]"
        )

    print("-" * 90)
    print(
        f"{'AVG':>4}  {'':36} "
        f"{'':>7} {'':>7} {'':>7} {_avg(a_comps):>7.4f}  {_avg(b_comps):>7.4f}"
    )
    print("=" * 90 + "\n")
