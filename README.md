# Cantordust Task 1 — Nepal Import Compliance Draft Agent

**China → Nepal | Solar Grid-Tied Inverter**  
Cantordust AI Engineer Assessment — Task 1  
Powered by **Groq** (free tier) — `llama-3.3-70b-versatile` · Orchestrated with **LangGraph**

---

## What this does

A LangGraph state graph agent that reads two Chinese manufacturer PDFs, reconciles them
against each other, and produces a Nepal import compliance draft for SunBridge Trading —
using NEPQA 2025 only as a reference for what Nepal reviewers expect.

**Node 1a — extract_pdf1**  
Reads Manufacturer PDF 1 independently (up to 24,000 characters) and pulls out structured
facts: product identity, manufacturer details, electrical specs, test/certification info,
labeling, and any unclear items.

**Node 1b — extract_pdf2**  
Same extraction on Manufacturer PDF 2 in isolation — no cross-contamination between sources.

**Node 2 — reconcile**  
Compares the two extracts side by side across four explicit categories:
- Consistent facts (same value in both PDFs)
- Mismatches (different values — both shown)
- Same fact, different format (e.g. "230V" vs "230 volts" — flagged, not silently resolved)
- Only in one PDF / missing from the other

**Node 3 — draft_compliance**  
Writes the Nepal compliance draft. Opens with a Document Summary stating what variant each
PDF appears to describe and whether they look like the same product or different variants.
Mismatches flagged inline with `[MISMATCH: ...]`. Ends with an Approach Note and a numbered
Outstanding Unclear Items list.

**Node 4 — write_cover_note**  
Writes a short professional email back to Ramesh at SunBridge Trading. Addresses the variant
uncertainty directly and flags what still needs factory clarification before filing.

All intermediate outputs are saved so every node's output can be inspected.

---

## Graph structure

```
PDF 1 ──► extract_pdf1 ──┐
    │                     ├──► reconcile ──► draft_compliance ──► write_cover_note ──► END
PDF 2 ──► extract_pdf2 ──┘        │               │  (NEPQA 2025             │
    │    (24k chars each)          │               │   used here as           │
    │                              │               │   reference only)        │
    ↓                              ↓               ↓                          ↓
facts_pdf1.md             reconciliation_    nepal_compliance_         cover_note_to_
facts_pdf2.md             report.md          draft.md                  ramesh.md
```

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

Installs: `groq`, `langgraph`, `pymupdf`, `python-dotenv`, `rich`

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
uv run main.py
```

Takes about 30–60 seconds. You will see each LangGraph node name printed as it executes.
If a Groq rate limit is hit, the agent waits automatically and retries — no need to restart.

---

## Output files

After the run, check the `output/` directory:

| File | Contents |
|------|----------|
| `nepal_compliance_draft.md` |  **Main deliverable** — share with the Nepal import agent |
| `cover_note_to_ramesh.md` | Email reply to Ramesh: variant summary, approach, open items |
| `facts_manufacturer_pdf1.md` | Facts extracted by node extract_pdf1 |
| `facts_manufacturer_pdf2.md` | Facts extracted by node extract_pdf2 |
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
│   ├── agent.py                   # LangGraph graph + node definitions
│   └── report.py                  # Writes output files
├── main.py                        # Entry point
├── pyproject.toml                 # uv / pip project config
├── .env.example                   # API key template
├── .gitignore
└── README.md
```

---

## Design decisions

**LangGraph StateGraph** — each processing step is a named node in a state graph. The shared
`AgentState` TypedDict passes data between nodes cleanly without global variables.

**PDFs extracted in separate nodes** — `extract_pdf1` and `extract_pdf2` are independent
nodes so the model cannot blend facts from one document into the other before comparison.

**24,000 character limit per PDF** — large enough to capture facts that appear later in the
document (the assessment notes the same facts can appear in different places), while staying
within Groq's free-tier context limits.

**Four reconciliation categories** — consistent, mismatch, same-fact-different-format, and
one-sided. The "same fact, different format" category is explicit because the assessment flags
that formats may not match across the two PDFs.

**Document Summary opens the draft** — the first section states what variant each PDF appears
to describe and whether they look like the same product, so the Nepal import agent immediately
knows what they are reviewing.

**Auto-retry on rate limit** — if Groq's free tier returns a rate limit error, `_call()`
waits 60 seconds and retries up to 3 times before failing.

**NEPQA 2025 used as reference only** — the guideline is never copied section-by-section.
It is trimmed at a sentence boundary and used only to inform what topics to cover.

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
```