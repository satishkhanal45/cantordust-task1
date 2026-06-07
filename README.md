# Cantordust Task 1 — Nepal Import Compliance Draft Agent

**China → Nepal | Solar Grid-Tied Inverter**  
Cantordust AI Engineer Assessment — Task 1  
Powered by **Groq** (free tier) — `llama-3.3-70b-versatile`

---

## What this does

A three-step LLM agent that:

1. **Extracts** structured facts from each of the two manufacturer PDFs independently.
2. **Reconciles** the two extracts — surfaces consistent values, explicit mismatches, and gaps.
3. **Drafts** a Nepal import compliance document for SunBridge Trading, using NEPQA 2025 only as a reference for what Nepal reviewers expect.

All intermediate outputs are saved so you can inspect every step.

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
```

Takes about 30–60 seconds. You will see live progress for each step.

---

## Output files

After the run, check the `output/` directory:

| File | Contents |
|------|----------|
| `nepal_compliance_draft.md` | **Main deliverable** — share with the Nepal import agent |
| `facts_manufacturer_pdf1.md` | Structured facts extracted from PDF 1 |
| `facts_manufacturer_pdf2.md` | Structured facts extracted from PDF 2 |
| `reconciliation_report.md` | Side-by-side comparison: matches, mismatches, gaps |

---

## Project structure

```
cantordust-task1/
├── data/                          # Input PDFs (you add these)
│   ├── DSS_GZES230100125901_combined-1.pdf
│   ├── 188_1115.pdf
│   └── nepqa_2025.pdf
├── output/                        # Generated automatically
├── src/
│   ├── __init__.py
│   ├── pdf_reader.py              # PDF text extraction (PyMuPDF)
│   ├── agent.py                   # Three-step Groq agent logic
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
         ├─► Step 1: Extract facts (Groq) ──┐
PDF 2 ──┘                                   │
                                             ├─► Step 2: Reconcile (Groq) ──► Step 3: Draft (Groq) ──► output
NEPQA 2025 ─────────────────────────────────┘                                      ↑ reference only
```

- **Step 1** runs independently on each PDF — no cross-contamination between sources.
- **Step 2** compares the two extracts and explicitly flags mismatches with both values shown.
- **Step 3** uses the reconciliation + NEPQA 2025 (as a reference, not a template) to write the draft. Missing values are marked *"Pending / Not available"*; mismatches are flagged with `[MISMATCH: ...]`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `MISSING: data/...pdf` | Add the required PDFs to `data/` with the exact filenames shown above |
| `GROQ_API_KEY not set` | Make sure `.env` exists and contains your key from console.groq.com |
| `ModuleNotFoundError` | Run `uv pip install -e .` again inside the activated venv |
| Rate limit error | Groq free tier has per-minute token limits; wait ~60 s and re-run |
| Very short extraction (< 500 chars) | The PDF may be image-based; try a text-layer version |
