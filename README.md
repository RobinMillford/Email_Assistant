# Email Generation Assistant — AI Engineer Assessment

An email generation and evaluation system for the AI Engineer candidate assessment.
Generates professional emails from structured input using advanced prompt engineering,
then scores them with custom LLM-as-Judge metrics and compares two prompting strategies.

Runs on **OpenAI** by default (`gpt-5.4-mini`); **Groq** (free tier) and **Anthropic** are also selectable via `PROVIDER`.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Quick Start](#quick-start)
3. [How It Works](#how-it-works)
4. [Prompt Engineering Strategy](#prompt-engineering-strategy)
5. [Evaluation Metrics](#evaluation-metrics)
6. [Running the Evaluation](#running-the-evaluation)
7. [Understanding the Output](#understanding-the-output)
8. [Design Decisions](#design-decisions)

---

## Project Structure

```
email_assistant/
├── run_evaluation.py        ← Main entry point (CLI runner)
├── requirements.txt         ← Python dependencies
├── .env.example             ← Copy to .env and add your key
│
├── src/
│   ├── config.py            ← Provider, API keys, model names, limits
│   ├── llm_client.py        ← Provider-agnostic chat wrapper (OpenAI / Groq / Anthropic)
│   ├── prompts.py           ← All prompt templates (Strategy A + B + Judge prompts)
│   ├── test_scenarios.py    ← 10 evaluation scenarios + human-reference emails
│   ├── email_generator.py   ← Generates emails with Strategy A or B
│   ├── evaluator.py         ← FRS, TAS, PESS metrics (+ RAS reference metric)
│   ├── report_generator.py  ← Writes JSON, CSV, and Markdown reports
│   └── pdf_report.py        ← Writes the PDF final report
│
└── results/                 ← Evaluation outputs
    ├── prompt_comparison/   ← Run 1: advanced vs baseline prompt (same model)
    ├── model_vs_model/      ← Run 2: advanced @ gpt-5.4-mini vs baseline @ gpt-4o-mini
    └── latest/              ← Scratch — where a default run writes (gitignored)

each run folder contains:
    evaluation_results.json · evaluation_report.csv · analysis_report.md · analysis_report.pdf
```

---

## Quick Start

### 1. Install dependencies

```bash
git clone <your-repo-url>
cd email_assistant
python -m venv .venv && source .venv/bin/activate   # or use uv
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
```

Then edit `.env`. By default it uses **OpenAI**:

```
PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
```

To use the free **Groq** tier instead, set `PROVIDER=groq` and `GROQ_API_KEY=...`
(get a free key at <https://console.groq.com/keys>). Anthropic: `PROVIDER=anthropic`
and `ANTHROPIC_API_KEY=...`.

### 3. Run

```bash
# Full run — both strategies, all 10 scenarios, writes JSON+CSV+MD+PDF to results/latest/
python run_evaluation.py

# No key handy? Try the pipeline on mock data:
python run_evaluation.py --dry-run
```

Output of a default run goes to `results/latest/`. The two curated runs committed in the
repo live in `results/prompt_comparison/` and `results/model_vs_model/` (see [Results](#two-evaluation-runs-included)).

---

## How It Works

```
User Inputs (Intent + Key Facts + Tone)
         │
         ▼
Email Generation  (same model, two prompts)
  ├── Strategy A: Role-play + 6-step CoT + 3 Few-shot examples
  └── Strategy B: Simple baseline prompt
         │
         ▼
Evaluation (LLM-as-Judge + rule-based)
  ├── Metric 1: Fact Recall Score (FRS)
  ├── Metric 2: Tone Alignment Score (TAS)
  ├── Metric 3: Professional Email Structure Score (PESS)
  └── Supplementary: Reference Alignment Score (RAS) — vs human reference
         │
         ▼
Reports → results/ (JSON · CSV · analysis.md · analysis.pdf)
```

---

## Prompt Engineering Strategy

### Strategy A — Three-Layer Advanced Prompt

Combines three techniques into one system prompt ([src/prompts.py](src/prompts.py)):

1. **Role-Playing** — the model is a *"business communication specialist with 15+ years
   of experience"*, framing every generation with authority and precision.
2. **6-Step Chain-of-Thought** — six silent planning steps before writing:
   decode intent → profile relationship → architect the email → weave facts →
   calibrate tone → internal review.
3. **Three Few-Shot Examples** — diverse demonstrations (professional/warm follow-up,
   formal/apologetic request, warm client welcome) anchoring format and tone variety.

### Strategy B — Baseline Prompt

A minimal system message: `"You are a helpful assistant. Write professional emails."`
No role, no CoT, no examples — the comparison baseline.

---

## Evaluation Metrics

All metrics normalised to **0.0 – 1.0** (higher is better). The **composite** is the
equal-weighted average of the three required metrics (FRS + TAS + PESS).

### Metric 1 — Fact Recall Score (FRS)
- **Method:** LLM-as-Judge · **Formula:** `facts_present / total_facts`
- The judge checks each input fact against the email (verbatim or paraphrased).
- *Why:* a business email that drops a deadline, invoice number, or name fails its purpose.

### Metric 2 — Tone Alignment Score (TAS)
- **Method:** LLM-as-Judge (1–10 rubric) · **Formula:** `alignment_score / 10`
- Rates tone match across vocabulary, sentence structure, formality, emotional register.
- *Why:* an empathetic complaint reply that reads as bureaucratic fails as badly as a wrong fact.

### Metric 3 — Professional Email Structure Score (PESS)
- **Method:** 40% rule-based Python + 60% LLM-as-Judge · **Formula:** `0.4×rule + 0.6×llm`
- **Rules (0.25 each):** subject line · greeting · professional closing · multi-paragraph body.
- **LLM:** holistic structural quality on a 1–10 scale.
- *Why:* combines hard, auditable requirements with nuanced quality assessment.

### Supplementary — Reference Alignment Score (RAS)
- **Method:** LLM-as-Judge comparing the generated email against the **human reference**.
- **Formula:** `alignment_score / 10` (over coverage, tone-match, and quality vs the ideal).
- The only metric that uses the human-written reference emails. Reported **separately** and
  **not** folded into the composite — it validates the three standalone metrics against a
  human gold standard.

---

## Running the Evaluation

| Command | Description |
|---------|-------------|
| `python run_evaluation.py` | Full live run (both strategies, all 10 scenarios) + PDF |
| `python run_evaluation.py --dry-run` | Mock data — no API key needed |
| `python run_evaluation.py --scenario N` | Run scenario N only (1–10) |
| `python run_evaluation.py --strategy-a-only` | Strategy A only |
| `python run_evaluation.py --strategy-b-only` | Strategy B only |
| `python run_evaluation.py --no-pdf` | Skip PDF generation |
| `python run_evaluation.py --output-dir path/` | Custom output directory |

---

## Understanding the Output

- **`evaluation_results.json`** — full raw data: every metric definition, per-fact
  evaluations, tone/structure observations, and reference-comparison notes.
- **`evaluation_report.csv`** — one row per scenario, all metrics under both strategies,
  computed deltas (A − B), and an appended AVERAGE row.
- **`analysis_report.md`** / **`analysis_report.pdf`** — the one-page comparative analysis
  answering the three required questions, backed by the metric data.

### Two evaluation runs included

| Folder | Comparison | Result |
|--------|-----------|--------|
| `results/prompt_comparison/` | **Prompt-only** — advanced vs baseline prompt, both on `gpt-5.4-mini` | Effective tie (+0.25%): a strong model writes good emails even from the bare prompt, so the metrics saturate. |
| `results/model_vs_model/` | **Model + prompt** — advanced @ `gpt-5.4-mini` vs baseline @ `gpt-4o-mini` | Strategy A ahead (+3.21%, wins 9/10): the advanced setup leads clearly, biggest gap on Fact Recall. |

Reproduce them:

```bash
# Run 1 — prompt-only (same model)
python run_evaluation.py --output-dir results/prompt_comparison

# Run 2 — model-vs-model
MODEL_B=gpt-4o-mini python run_evaluation.py --output-dir results/model_vs_model
```

The analysis prose is generated **from the data** — it reports whichever strategy actually
won (or a tie), so it never overstates the result.

---

## Design Decisions

**Why two strategies on the same model rather than two different models?**
Comparing Model A vs Model B conflates prompt-engineering skill with raw model capability.
Running both prompts on the *same* model isolates the impact of prompt design — any gap is
attributable only to the prompt. (To do a model-vs-model run instead, set `MODEL_A` and
`MODEL_B` to different models in `.env`.)

**Why LLM-as-Judge instead of BLEU/ROUGE?**
A great email rarely reproduces the reference word-for-word, and tone requires semantic
judgment. LLM-as-Judge evaluates what a human reviewer would: right message, right voice,
right structure. The reference emails are still used — by the RAS metric — as a gold standard.

**Why is PESS hybrid (rule + LLM)?**
Pure rules are brittle (a "Hey" greeting passes the rule but is wrong in a formal email);
pure LLM scoring can miss hard requirements. The 40/60 split checks structural completeness
while still assessing nuanced quality.

---

## Dependencies

```
groq>=0.11.0          # Groq Cloud SDK (default provider, free tier)
anthropic>=0.30.0     # Optional: only if PROVIDER=anthropic
python-dotenv>=1.0.0  # .env support
tabulate>=0.9.0       # Console tables
fpdf2>=2.7.0          # Pure-Python PDF (final report)
```

Python 3.10+ required (uses `str | None` union syntax).
# Email_Assistant
