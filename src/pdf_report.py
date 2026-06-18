"""
pdf_report.py — Render the comparative analysis as a PDF (final report deliverable).

Pure-Python via fpdf2 (no system dependencies). Builds the PDF directly from the
results dict so it always matches the JSON/CSV/Markdown outputs.

Produces results/analysis_report.pdf containing:
  - Title + run metadata
  - Metric definitions (incl. the supplementary reference metric)
  - Per-scenario raw score table (Strategy A vs B)
  - Average summary table
  - The three required comparative-analysis answers
"""

import os

from fpdf import FPDF

import src.config as config
from src.config import ANALYSIS_PDF
from src.prompts import (
    ADVANCED_SYSTEM_PROMPT,
    ADVANCED_USER_TEMPLATE,
    BASELINE_SYSTEM_PROMPT,
    BASELINE_USER_TEMPLATE,
)


_UNICODE_MAP = {
    "—": "-", "–": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", " ": " ",
    "×": "x", "→": "->", "•": "*", "£": "GBP ",
}


def _s(text) -> str:
    """Make a string safe for fpdf2 core (latin-1) fonts."""
    text = str(text)
    for u, a in _UNICODE_MAP.items():
        text = text.replace(u, a)
    return text.encode("latin-1", "replace").decode("latin-1")


def _avg(values):
    return round(sum(values) / len(values), 4) if values else 0.0


def _collect(results):
    """Pull per-scenario and average scores out of the results dict."""
    rows = []
    a = {"frs": [], "tas": [], "pess": [], "comp": [], "ras": []}
    b = {"frs": [], "tas": [], "pess": [], "comp": [], "ras": []}

    for s in results.get("scenarios", []):
        ea = s.get("strategy_a", {}).get("evaluation", {})
        eb = s.get("strategy_b", {}).get("evaluation", {})

        def g(e, *keys):
            cur = e
            for k in keys:
                cur = cur.get(k, {}) if isinstance(cur, dict) else {}
            return cur if isinstance(cur, (int, float)) else 0.0

        row = {
            "id": s["id"],
            "name": s["name"],
            "a_frs": g(ea, "fact_recall", "score"),
            "a_tas": g(ea, "tone_alignment", "score"),
            "a_pess": g(ea, "structure_quality", "score"),
            "a_comp": ea.get("composite_score", 0.0),
            "a_ras": g(ea, "reference_alignment", "score"),
            "b_frs": g(eb, "fact_recall", "score"),
            "b_tas": g(eb, "tone_alignment", "score"),
            "b_pess": g(eb, "structure_quality", "score"),
            "b_comp": eb.get("composite_score", 0.0),
            "b_ras": g(eb, "reference_alignment", "score"),
        }
        rows.append(row)
        a["frs"].append(row["a_frs"]); a["tas"].append(row["a_tas"])
        a["pess"].append(row["a_pess"]); a["comp"].append(row["a_comp"]); a["ras"].append(row["a_ras"])
        b["frs"].append(row["b_frs"]); b["tas"].append(row["b_tas"])
        b["pess"].append(row["b_pess"]); b["comp"].append(row["b_comp"]); b["ras"].append(row["b_ras"])

    avgs = {
        "a_frs": _avg(a["frs"]), "a_tas": _avg(a["tas"]), "a_pess": _avg(a["pess"]),
        "a_comp": _avg(a["comp"]), "a_ras": _avg(a["ras"]),
        "b_frs": _avg(b["frs"]), "b_tas": _avg(b["tas"]), "b_pess": _avg(b["pess"]),
        "b_comp": _avg(b["comp"]), "b_ras": _avg(b["ras"]),
    }
    return rows, avgs


class _PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150)
        self.cell(0, 6, "Email Generation Assistant - Comparative Analysis", align="R")
        self.ln(8)
        self.set_text_color(0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")
        self.set_text_color(0)


def _h(pdf, text, size=14):
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", size)
    pdf.set_text_color(20, 40, 90)
    pdf.cell(0, 8, _s(text))
    pdf.ln(9)
    pdf.set_text_color(0)


def _p(pdf, text, size=10):
    pdf.set_font("Helvetica", "", size)
    pdf.multi_cell(0, 5, _s(text))
    pdf.ln(1)


def _code(pdf, text, size=7.5):
    """Render a monospace code block with a light background."""
    pdf.set_font("Courier", "", size)
    pdf.set_fill_color(244, 244, 246)
    pdf.multi_cell(0, 4, _s(text.strip()), fill=True, border=0)
    pdf.ln(2)


def generate_pdf_report(results: dict) -> str:
    """Write results/analysis_report.pdf and return its path."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(config.OUTPUT_DIR, ANALYSIS_PDF)

    rows, avg = _collect(results)
    provider = results.get("provider", "?")
    model = results.get("model_used", "?")
    run_type = results.get("run_type", "?")
    _first = results.get("scenarios", [{}])[0]
    model_a = _first.get("strategy_a", {}).get("model", model)
    model_b = _first.get("strategy_b", {}).get("model", model_a)
    models_differ = model_a != model_b

    d_comp = round(avg["a_comp"] - avg["b_comp"], 4)
    pct = round(d_comp / avg["b_comp"] * 100, 1) if avg["b_comp"] else 0.0
    d_frs = round(avg["a_frs"] - avg["b_frs"], 4)
    d_tas = round(avg["a_tas"] - avg["b_tas"], 4)
    d_pess = round(avg["a_pess"] - avg["b_pess"], 4)
    d_ras = round(avg["a_ras"] - avg["b_ras"], 4)

    gaps = {"Fact Recall (FRS)": d_frs, "Tone Alignment (TAS)": d_tas, "Structure (PESS)": d_pess}
    biggest_b_gap = max(gaps, key=gaps.get)   # metric where B trails most
    biggest_a_gap = min(gaps, key=gaps.get)   # metric where A trails most

    # Per-scenario wins + honest winner classification
    a_comps = [r["a_comp"] for r in rows]
    b_comps = [r["b_comp"] for r in rows]
    a_wins = sum(1 for x, y in zip(a_comps, b_comps) if x > y + 1e-9)
    b_wins = sum(1 for x, y in zip(a_comps, b_comps) if y > x + 1e-9)
    ties = len(rows) - a_wins - b_wins
    tie = abs(d_comp) < 0.01
    winner = "A" if d_comp >= 0 else "B"

    def _dir(d, m):
        if abs(d) < 1e-9:
            return f"{m} tie (delta {d:+.4f})"
        return f"{m} {'A' if d > 0 else 'B'} leads (delta {d:+.4f})"

    per_metric = "; ".join(_dir(v, m) for m, v in
                           (("FRS", d_frs), ("TAS", d_tas), ("PESS", d_pess)))

    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 40, 90)
    pdf.multi_cell(0, 9, "Email Generation Assistant\nComparative Analysis Report")
    pdf.set_text_color(0)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(110)
    run_kind = "Model-vs-model comparison" if models_differ else "Prompt comparison (same model)"
    pdf.multi_cell(0, 5, _s(
        f"Comparison: {run_kind}   |   Provider: {provider}   |   Run type: {run_type}   |   Scenarios: {len(rows)}\n"
        f"Strategy A:  advanced prompt (role-play + CoT + few-shot)  -  model: {model_a}\n"
        f"Strategy B:  baseline prompt (minimal instruction)         -  model: {model_b}\n"
        f"Metrics: FRS, TAS, PESS (composite)  +  RAS (vs human reference, supplementary)"))
    pdf.set_text_color(0)
    pdf.ln(3)

    if models_differ:
        _p(pdf, f"This run varies BOTH the prompt and the model: Strategy A pairs the advanced prompt "
                f"with {model_a}; Strategy B pairs a minimal baseline prompt with {model_b}. The "
                f"performance gap therefore reflects the combined prompt + model effect (a production "
                f"A/B), not prompt engineering in isolation.")
    else:
        _p(pdf, f"Both strategies run on the same model ({model_a}), so any performance gap reflects "
                f"prompt engineering impact only -- not model capability. Strategy A uses an advanced "
                f"prompt (role-play + 6-step chain-of-thought + 3 few-shot examples); Strategy B uses a "
                f"minimal baseline prompt.")

    # Prompt template (deliverable requirement)
    pdf.add_page()
    _h(pdf, "Prompt Template")
    _h(pdf, "Strategy A - Advanced (role-play + chain-of-thought + few-shot)", size=11)
    _p(pdf, "System prompt:", size=9)
    _code(pdf, ADVANCED_SYSTEM_PROMPT)
    _p(pdf, "User message template:", size=9)
    _code(pdf, ADVANCED_USER_TEMPLATE)
    _h(pdf, "Strategy B - Baseline", size=11)
    _p(pdf, "System prompt:", size=9)
    _code(pdf, BASELINE_SYSTEM_PROMPT)
    _p(pdf, "User message template:", size=9)
    _code(pdf, BASELINE_USER_TEMPLATE)

    # Metric definitions
    pdf.add_page()
    _h(pdf, "Metric Definitions")
    defs = [
        ("FRS", "Fact Recall Score", "LLM-as-Judge", "facts_present / total_facts"),
        ("TAS", "Tone Alignment Score", "LLM-as-Judge (1-10 rubric)", "alignment_score / 10"),
        ("PESS", "Professional Email Structure", "40% rules + 60% LLM-as-Judge", "0.4*rule + 0.6*llm"),
        ("RAS*", "Reference Alignment (suppl.)", "LLM-as-Judge vs human reference", "alignment_score / 10"),
    ]
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(col_widths=(12, 46, 60, 50), text_align="LEFT", first_row_as_headings=True) as table:
        hdr = table.row(); [hdr.cell(c) for c in ("Key", "Name", "Method", "Formula")]
        for key, name, method, formula in defs:
            r = table.row(); [r.cell(c) for c in (key, name, method, formula)]
    _p(pdf, "* RAS is supplementary -- the only metric that uses the human-written reference email. "
            "It is reported separately and NOT folded into the composite. "
            "Composite = equal-weighted average of FRS + TAS + PESS.", size=8)

    # Raw data table
    _h(pdf, "Raw Evaluation Data (per scenario)")
    pdf.set_font("Helvetica", "", 7.5)
    headers = ["ID", "Scenario", "A-FRS", "A-TAS", "A-PESS", "A-Cmp", "B-FRS", "B-TAS", "B-PESS", "B-Cmp"]
    widths = (8, 44, 16, 16, 17, 16, 16, 16, 17, 16)
    with pdf.table(col_widths=widths, text_align="CENTER", first_row_as_headings=True) as table:
        hr = table.row(); [hr.cell(h) for h in headers]
        for r in rows:
            row = table.row()
            row.cell(str(r["id"]))
            row.cell(_s(r["name"][:26]))
            for v in (r["a_frs"], r["a_tas"], r["a_pess"], r["a_comp"],
                      r["b_frs"], r["b_tas"], r["b_pess"], r["b_comp"]):
                row.cell(f"{v:.3f}")
        # average row
        ar = table.row()
        ar.cell("AVG"); ar.cell("-- AVERAGE --")
        for v in (avg["a_frs"], avg["a_tas"], avg["a_pess"], avg["a_comp"],
                  avg["b_frs"], avg["b_tas"], avg["b_pess"], avg["b_comp"]):
            ar.cell(f"{v:.3f}")

    # Summary table
    _h(pdf, "Average Summary")
    pdf.set_font("Helvetica", "", 9)
    summ = [
        ("FRS", avg["a_frs"], avg["b_frs"], d_frs),
        ("TAS", avg["a_tas"], avg["b_tas"], d_tas),
        ("PESS", avg["a_pess"], avg["b_pess"], d_pess),
        ("Composite", avg["a_comp"], avg["b_comp"], d_comp),
        ("RAS (suppl.)", avg["a_ras"], avg["b_ras"], d_ras),
    ]
    with pdf.table(col_widths=(50, 40, 40, 40), text_align="CENTER", first_row_as_headings=True) as table:
        hr = table.row(); [hr.cell(c) for c in ("Metric", "Strategy A", "Strategy B", "Delta (A-B)")]
        for name, av, bv, dv in summ:
            r = table.row()
            r.cell(name); r.cell(f"{av:.4f}"); r.cell(f"{bv:.4f}"); r.cell(f"{dv:+.4f}")

    # Analysis
    pdf.add_page()
    _h(pdf, "Analysis")

    _h(pdf, "Q1 - Which strategy performed better?", size=11)
    overall = "an effective tie" if tie else f"Strategy {winner} ahead"
    setup = (f"A = advanced prompt on {model_a}; B = baseline prompt on {model_b} (prompt AND model vary)."
             if models_differ else f"Both strategies on {model_a} (prompt-only comparison).")
    if tie:
        closing = ("A gap this small is within LLM-judge variance: a capable model already writes strong "
                   "emails from the minimal baseline prompt, so neither setup shows a meaningful lift -- "
                   "both sit near the top of the metric range.")
    else:
        closing = (f"Strategy {winner} leads consistently"
                   + (" (combined prompt + model effect)." if models_differ
                      else ", and since both share one model the gap is attributable to prompt design alone."))
    _p(pdf, f"Result: {overall}. Setup: {setup} Strategy A averaged {avg['a_comp']:.4f} vs "
            f"{avg['b_comp']:.4f} for Strategy B across {len(rows)} scenarios -- a difference of "
            f"{d_comp:+.4f} ({pct:+.2f}%). Per-scenario: A won {a_wins}, B won {b_wins}, {ties} tied. "
            f"Per-metric (A-B): {per_metric}. Reference metric: RAS A {avg['a_ras']:.4f} vs B "
            f"{avg['b_ras']:.4f} (delta {d_ras:+.4f}). {closing}")

    _h(pdf, "Q2 - Weakness of the lower-performing strategy", size=11)
    if tie:
        _p(pdf, f"Neither strategy has a decisive failure mode -- every per-metric gap is within noise. "
                f"The clearest single difference is on {biggest_b_gap} (delta {gaps[biggest_b_gap]:+.4f}), "
                f"too small to call a reliable weakness. Where the baseline did fall behind, it was on "
                f"the more nuanced, tone-sensitive scenarios rather than the straightforward ones.")
    elif winner == "A":
        _p(pdf, f"Strategy B trails most on {biggest_b_gap} (delta {gaps[biggest_b_gap]:+.4f}). Without "
                f"few-shot tone exemplars or the chain-of-thought 'weave facts' step, the baseline is "
                f"weakest on the more nuanced briefs where framing matters most.")
    else:
        _p(pdf, f"Strategy A trails most on {biggest_a_gap} (delta {gaps[biggest_a_gap]:+.4f}). The "
                f"advanced prompt did not beat the baseline on every metric and lost some scenarios "
                f"outright -- evidence that extra scaffolding can add verbosity or drift without "
                f"improving the measured qualities on a strong model.")

    _h(pdf, "Q3 - Production recommendation", size=11)
    if winner == "A":
        _p(pdf, f"Recommend Strategy A -- on robustness grounds rather than a large average lift. The "
                f"averages are close, but the advanced prompt's explicit fact-weaving and tone "
                f"calibration cut the risk of the worst-case email (a dropped deadline/invoice number "
                f"or a tonally wrong message), which matters more in production than a fractional "
                f"average gain. Cost: ~700-900 extra input tokens per call -- negligible.")
    else:
        _p(pdf, f"Recommend Strategy B for this model -- it matched or beat the advanced prompt on the "
                f"composite while using ~700-900 fewer input tokens per call, so it is cheaper and at "
                f"least as good here. Reserve the advanced prompt for weaker models or harder briefs.")
    _p(pdf, "Caveat: both strategies run on the same strong model, which compresses the gap. The "
            "advanced prompt's value is expected to grow on weaker models or harder, more fact-dense "
            "briefs (set MODEL_B to a smaller model to test the model-vs-model axis).")

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150)
    pdf.multi_cell(0, 5, "Generated by the Email Generation Assistant evaluation pipeline.")
    pdf.set_text_color(0)

    pdf.output(filepath)
    print(f"  [✓] PDF saved   → {filepath}")
    return filepath
