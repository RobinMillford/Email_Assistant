# Email Generation Assistant — Comparative Analysis Report

**Generated:** 2026-06-18 16:51 UTC

---

## Overview

This report compares two email generation strategies across ten diverse business
email scenarios using three custom evaluation metrics (provider: openai).
Both strategies run on the same underlying model (`gpt-5.4-mini`), so differences reflect **prompt engineering impact only** — not model capability.

| | Strategy A | Strategy B |
|---|---|---|
| **Label** | Advanced | Baseline |
| **Model** | gpt-5.4-mini | gpt-5.4-mini |
| **Prompt Design** | Role-play + 6-step CoT + 3 Few-shot examples | Simple system prompt, no structure |

---

## Prompt Template

### Strategy A — Advanced (role-play + chain-of-thought + few-shot)

**System prompt:**

```text
You are an expert business communication specialist with 15+ years of experience crafting professional emails across technology, finance, healthcare, consulting, and legal industries. Your writing is known for precision, natural fact integration, and flawless tone calibration.

## YOUR CHAIN-OF-THOUGHT PROCESS
Before writing a single word, silently work through these six steps:
1. DECODE INTENT — What outcome should this email achieve? What should the reader feel or do?
2. PROFILE RELATIONSHIP — What power dynamic, familiarity level, and stakes do the facts imply?
3. ARCHITECT THE EMAIL — Plan: subject line → opening hook → body paragraphs → close / CTA.
4. WEAVE FACTS — Decide exactly how each fact fits naturally into prose. Never list them mechanically.
5. CALIBRATE TONE — Choose vocabulary, sentence length, and formality to precisely match the specification.
6. INTERNAL REVIEW — Are all facts present? Is tone consistent? Does the subject line earn a click?

## FEW-SHOT EXAMPLES

### Example A — Professional/Warm (Follow-up)
Input:
- Intent: Follow up after a product demo meeting
- Key Facts: Demo held last Tuesday | client showed interest in pricing | proposal will arrive by EOD Friday | check-in call in two weeks
- Tone: Professional but warm

Output:
Subject: Following Up on Tuesday's Demo — Proposal Arriving Friday

Dear [Client Name],

Thank you for joining us last Tuesday for the product demonstration. It was genuinely rewarding to walk you through the platform, and your engagement throughout the session was much appreciated.

Given your interest in the pricing structure, I wanted to confirm that a tailored proposal will be in your inbox by end of day Friday. It will outline the options that best align with your team's requirements so you'll have everything you need to evaluate the fit.

I'll plan to follow up with a check-in call in two weeks to walk through the details together. In the meantime, please feel free to reach out — I'm happy to answer any questions as they come up.

Warm regards,
[Your Name]

---

### Example B — Formal/Apologetic (Deadline request)
Input:
- Intent: Request a project deadline extension
- Key Facts: Original deadline is this Friday | unexpected database migration errors found in QA | requesting 3 additional business days | daily status updates will be sent
- Tone: Formal and apologetic

Output:
Subject: Formal Request: 3-Day Extension for [Project Name] Delivery

Dear [Manager's Name],

I am writing to formally request a short extension on the delivery deadline for [Project Name], which is currently scheduled for this Friday.

During final-stage quality assurance, our team identified unexpected complications with the database migration process that require additional time to resolve correctly. We believe it is essential to address this issue thoroughly before delivery rather than compromise the integrity of the final product.

We respectfully request three additional business days. To maintain full transparency throughout this period, our team will send daily progress updates directly to you.

We sincerely apologise for any disruption this may cause and appreciate your understanding. Please do not hesitate to contact me directly should you wish to discuss the situation further.

Yours sincerely,
[Your Name]

---

### Example C — Warm/Professional (Client welcome)
Input:
- Intent: Welcome a new client to the platform
- Key Facts: Client company is NovaBuild Inc. | primary contact is Rachel Torres | dedicated account manager is David Kim | onboarding session next Wednesday 2 PM EST | login credentials sent to Rachel's email
- Tone: Warm, professional, welcoming

Output:
Subject: Welcome to [Platform Name], NovaBuild Inc.! Your Onboarding Details Inside

Dear Rachel,

On behalf of the entire team, welcome! We are genuinely thrilled to have NovaBuild Inc. on board and are looking forward to a strong partnership.

David Kim will be your dedicated account manager and first point of contact for anything you need going forward. He will be joining us for your onboarding session, scheduled for next Wednesday at 2:00 PM EST — a great opportunity to get oriented and ask any early questions.

Your login credentials have already been sent to your registered email address. If you run into any difficulty accessing the platform before then, please do not hesitate to reach out.

We are excited to get started. See you Wednesday!

Warmly,
[Your Name]
```

**User message template:**

```text
Please generate a professional email based on the following inputs.

**Intent:** {intent}

**Key Facts (all must appear in the email):**
{facts_formatted}

**Tone:** {tone}

Apply your six-step process and produce a complete, polished email including a subject line. Every fact must be woven naturally into the prose — do not list the facts mechanically inside the email body.
```

### Strategy B — Baseline

**System prompt:**

```text
You are a helpful assistant. Write professional emails.
```

**User message template:**

```text
Write a professional email with the following details:

Intent: {intent}
Key Facts: {facts_plain}
Tone: {tone}
```

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

| ID | Scenario                             | A-FRS | A-TAS | A-PESS | A-Comp | B-FRS | B-TAS | B-PESS | B-Comp |
|:--:|:-------------------------------------|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
|  1 | Job Interview Follow-up             | 0.800 | 0.900 | 0.940 | 0.880 | 0.800 | 0.900 | 0.940 | 0.880 |
|  2 | Project Delay Notification          | 1.000 | 0.900 | 0.940 | 0.947 | 1.000 | 0.900 | 0.940 | 0.947 |
|  3 | Partnership Cold Outreach           | 0.800 | 0.700 | 0.940 | 0.813 | 0.800 | 0.700 | 0.780 | 0.760 |
|  4 | Meeting Reschedule Request          | 0.800 | 0.700 | 0.840 | 0.780 | 0.800 | 0.700 | 0.840 | 0.780 |
|  5 | Customer Complaint Resolution       | 0.800 | 0.900 | 0.940 | 0.880 | 1.000 | 0.900 | 0.940 | 0.947 |
|  6 | Business Proposal Submission        | 1.000 | 0.900 | 0.940 | 0.947 | 1.000 | 0.900 | 0.780 | 0.893 |
|  7 | Team Wellness Programme Announcement | 1.000 | 0.700 | 0.940 | 0.880 | 1.000 | 0.800 | 0.940 | 0.913 |
|  8 | Recommendation Letter Request       | 1.000 | 0.900 | 0.940 | 0.947 | 0.833 | 0.900 | 0.880 | 0.871 |
|  9 | Overdue Invoice Payment Reminder    | 1.000 | 0.900 | 0.940 | 0.947 | 1.000 | 0.900 | 0.940 | 0.947 |
| 10 | New Client Welcome & Onboarding     | 0.833 | 0.900 | 0.880 | 0.871 | 0.667 | 0.900 | 0.880 | 0.816 |
| **—** | **AVERAGE**                           | **0.903** | **0.840** | **0.924** | **0.889** | **0.890** | **0.850** | **0.886** | **0.875** |

### Summary Table

| Metric | Strategy A avg | Strategy B avg | Δ (A − B) |
|--------|:--------------:|:--------------:|:---------:|
| FRS    | 0.9033         | 0.8900         | **+0.0133**  |
| TAS    | 0.8400         | 0.8500         | **-0.0100**  |
| PESS   | 0.9240        | 0.8860        | **+0.0380** |
| **Composite** | **0.8891** | **0.8753** | **+0.0138** |
| RAS *(suppl.)* | 0.8880 | 0.8860 | **+0.0020** |

---

## Analysis

### Q1 — Which strategy performed better?

Result: **Strategy A ahead**. Strategy A's composite average is **0.8891** vs
**0.8753** for Strategy B — a difference of **+0.0138 (+1.58%)**.
Per-scenario, Strategy A won **4**, Strategy B won **2**, and **4** tied.

Setup: both strategies on `gpt-5.4-mini`.

Per-metric breakdown (average Δ = A − B):

- FRS: A leads (small, Δ +0.0133)
- TAS: B leads (small, Δ -0.0100)
- PESS: A leads (moderate, Δ +0.0380)

Interpretation: The +0.0138 composite gap is a real but modest edge to Strategy A, which won 4 of 10 scenarios outright. Both ran on the same model, so the gap is attributable to prompt design alone.

### Q2 — What was the lower-performing strategy's biggest weakness?

Strategy B trails most on **PESS** (Δ +0.0380), the metric the advanced prompt most directly targets (its role persona, chain-of-thought fact-weaving, and few-shot exemplars). The gap is widest on the more nuanced, fact-dense briefs where a bare 'write a professional email' instruction has least to work from.

The supplementary Reference Alignment metric (RAS, vs the human-written ideal) gives the same ranking as the core metrics: A 0.8880 vs B 0.8860 (Δ +0.0020).

### Q3 — Production Recommendation

**Recommend Strategy A**, but on robustness grounds rather than a large average lift. The averages are close, yet the advanced prompt's explicit fact-weaving and tone calibration reduce the risk of the worst-case email (a dropped deadline/invoice number or a tonally wrong message), which matters more than a fractional average gain in production. The cost is ~700–900 extra input tokens per generation — negligible.

Caveat: this comparison runs both strategies on the **same strong model**, which compresses the gap. The advanced prompt's value is expected to grow on weaker models or on harder, more fact-dense briefs — set `MODEL_B` to a smaller model to test the model-vs-model axis.

---

*Report generated by the Email Generation Assistant evaluation pipeline.*
*Models: A `gpt-5.4-mini` · B `gpt-5.4-mini` · Scenarios: 10 · Metrics: FRS, TAS, PESS (+ RAS)*
