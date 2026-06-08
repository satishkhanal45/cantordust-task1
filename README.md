# Cantordust Task 1 — Nepal Import Compliance Draft Agent

**China → Nepal | Solar Grid-Tied Inverter**  
Cantordust AI Engineer Assessment — Task 1  
Powered by **Groq** (free tier) — `llama-3.3-70b-versatile`

---

## What this does

A four-step LLM agent that reads two Chinese manufacturer PDFs, reconciles them against each
other, and produces a Nepal import compliance draft for SunBridge Trading — using NEPQA 2025
only as a reference for what Nepal reviewers expect.

**Step 1 — Extract**  
Reads each manufacturer PDF independently (up to 24,000 characters) and pulls out structured
facts: product identity, manufacturer details, electrical specs, test/certification info,
labeling, and any unclear items. The two PDFs are processed separately to avoid
cross-contamination.

**Step 2 — Reconcile**  
Compares the two extracts side by side. Surfaces four categories explicitly:
- Consistent facts (same value in both PDFs)
- Mismatches (different values — both shown)
- Same fact, different format (e.g. "230V" vs "230 volts" — flagged, not silently resolved)
- Only in one PDF / missing from the other

**Step 3 — Draft**  
Writes the Nepal compliance draft using the reconciliation plus NEPQA 2025 as a topic
reference. Opens with a Document Summary stating what variant each PDF appears to describe
and whether they look like the same product or different variants. Mismatches are flagged
inline with `[MISMATCH: ...]`. Ends with an Approach Note and a numbered Outstanding Unclear
Items list.

**Step 4 — Cover note**  
Writes a short professional email back to Ramesh at SunBridge Trading. Addresses the variant
uncertainty directly, explains how the draft was compiled, and flags what still needs factory
clarification before the Nepal agent can file.

All intermediate outputs are saved so every step can be inspected.

---

## Prerequisites

| Tool | Minimum version | Check |
|------|----------------|-------|
| Python | 3.11 | `python --version` |
| uv | any recent | `uv --version` |

Install `uv` if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Step-by-step setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/cantordust-task1.git
cd cantordust-task1
```

### 2. Create and activate a virtual environment with uv

```bash
uv venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
uv pip install -e .
```

Installs: `groq`, `pymupdf`, `python-dotenv`, `rich`

### 4. Get a free Groq API key

1. Go to **https://console.groq.com**
2. Sign up (free, no credit card needed)
3. Navigate to **API Keys → Create API Key**
4. Copy the key

### 5. Set your Groq API key

```bash
cp .env.example .env
```

Open `.env` and paste your key:

```
GROQ_API_KEY=gsk_...your key here...
```

### 6. Place the required PDFs in `data/`

Create the `data/` folder and add these three files with **exactly** these names:

```
data/
  DSS_GZES230100125901_combined-1.pdf   ← Manufacturer PDF 1 (from Cantordust)
  188_1115.pdf                           ← Manufacturer PDF 2 (from Cantordust)
  nepqa_2025.pdf                         ← NEPQA 2025 guideline (rename yours to this)
```

> If your NEPQA 2025 file has a different name, rename it to `nepqa_2025.pdf`
> or change the `NEPQA_NAME` constant at the top of `main.py`.

### 7. Run the agent

```bash
python main.py
uv run main.py
```

Takes about 30–60 seconds. You will see live progress for each step.
If a Groq rate limit is hit, the agent waits automatically and retries — no need to restart.

---

## Output files

After the run, check the `output/` directory:

| File | Contents |
|------|----------|
| `nepal_compliance_draft.md` | ⭐ **Main deliverable** — share with the Nepal import agent |
| `cover_note_to_ramesh.md` | Email reply to Ramesh: variant summary, approach, open items |
| `facts_manufacturer_pdf1.md` | Structured facts extracted from PDF 1 |
| `facts_manufacturer_pdf2.md` | Structured facts extracted from PDF 2 |
| `reconciliation_report.md` | Full reconciliation: matches, mismatches, format differences, gaps |

---

## Project structure

```
cantordust-task1/
├── data/                          # Input PDFs (you add these)
│   ├── DSS_GZES230100125901_combined-1.pdf
│   ├── 188_1115.pdf
│   └── nepqa_2025.pdf
├── output/                        # Generated automatically
│   ├── nepal_compliance_draft.md
│   ├── cover_note_to_ramesh.md
│   ├── facts_manufacturer_pdf1.md
│   ├── facts_manufacturer_pdf2.md
│   └── reconciliation_report.md
├── src/
│   ├── __init__.py
│   ├── pdf_reader.py              # PDF text extraction (PyMuPDF)
│   ├── agent.py                   # Four-step Groq agent logic
│   └── report.py                  # Writes output files
├── main.py                        # Entry point
├── pyproject.toml                 # uv / pip project config
├── .env.example                   # API key template
├── .gitignore
└── README.md
```

---

## How the agent works

```
PDF 1 ──┐
         ├─► Step 1: Extract facts (Groq, up to 24k chars each) ──┐
PDF 2 ──┘                                                          │
                                                                    ├─► Step 2: Reconcile ──► Step 3: Draft ──► nepal_compliance_draft.md
NEPQA 2025 ────────────────────────────────────────────────────────┘         │                    ↑ reference only
                                                                              └──► Step 4: Cover note ──► cover_note_to_ramesh.md
```

### Design decisions

**PDFs processed independently in Step 1** — each PDF is extracted in isolation so the model
cannot blend facts from one document into the other before comparison.

**24,000 character limit per PDF** — large enough to capture facts that appear later in the
document (the assessment notes the same facts can appear in different places), while staying
within Groq's free-tier context limits.

**Four reconciliation categories in Step 2** — consistent, mismatch, same-fact-different-format,
and one-sided. The "same fact, different format" category is explicit because the assessment
flags that formats may not match across the two PDFs.

**Document Summary opens the draft** — the first section of the compliance draft states what
variant each PDF appears to describe and whether they look like the same product, so the Nepal
import agent immediately knows what they are reviewing.

**Auto-retry on rate limit** — if Groq's free tier returns a rate limit error, the agent
waits 60 seconds and retries up to 3 times before failing, so a long run is not lost to a
transient limit.

**NEPQA 2025 used as reference only** — the guideline is never copied section-by-section.
It is used only to decide what topics Nepal reviewers typically ask for.

**Honest gaps** — missing information is written as "Pending / Not available in current
documents" rather than omitted or guessed.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `MISSING: data/...pdf` | Add the required PDFs to `data/` with the exact filenames shown above |
| `GROQ_API_KEY not set` | Make sure `.env` exists and contains your key from console.groq.com |
| `ModuleNotFoundError` | Run `uv pip install -e .` again inside the activated venv |
| Rate limit error (repeated) | The agent retries automatically; if it still fails, wait 2–3 minutes and re-run |
| Very short extraction (< 500 chars) | The PDF may be image-based; try a text-layer version |
