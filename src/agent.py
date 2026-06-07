"""
agent.py
Multi-step agent using Groq (free tier) that:
  1. Extracts key facts from each manufacturer PDF independently.
  2. Reconciles the two extracts and flags mismatches.
  3. Drafts the Nepal import compliance document using NEPQA 2025 as a reference.
"""

from groq import Groq
from rich.console import Console

console = Console()

# llama-3.3-70b-versatile is Groq's best free model for long-context reasoning
MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096


def _call(client: Groq, system: str, user: str) -> str:
    """Single blocking call to Groq."""
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


# ── Step 1 ──────────────────────────────────────────────────────────────────

EXTRACT_SYSTEM = """You are a technical document analyst helping a trading company prepare
import paperwork. Your job is to read manufacturer export documents and pull out the facts
that matter for an import compliance review.

Extract ONLY information that is actually present in the document.
Do NOT invent or assume values. If something is missing, say "Not stated".

Format your output as structured plain text under these headings:
  PRODUCT IDENTITY
  MANUFACTURER DETAILS
  ELECTRICAL / TECHNICAL SPECIFICATIONS
  TEST & CERTIFICATION INFORMATION
  LABELING & MARKINGS
  OTHER NOTABLE DETAILS
  UNCLEAR OR AMBIGUOUS ITEMS
"""


def extract_facts(client: Groq, label: str, pdf_text: str) -> str:
    """Step 1: Extract structured facts from one manufacturer PDF."""
    console.print(f"[cyan]  → Extracting facts from {label}…[/cyan]")
    # Groq has a 6000 token/min limit on free tier; trim large PDFs to ~12000 chars
    truncated = pdf_text[:12000]
    user = f"""The following is the full text of a manufacturer export document called "{label}".
Extract all facts relevant to a solar inverter Nepal import compliance review.

DOCUMENT TEXT:
{truncated}
"""
    return _call(client, EXTRACT_SYSTEM, user)


# ── Step 2 ──────────────────────────────────────────────────────────────────

RECONCILE_SYSTEM = """You are a trade compliance analyst. You have been given structured fact
extracts from two manufacturer PDFs for the same or similar solar inverter product.

Your job is to:
  1. Identify facts that are CONSISTENT across both documents.
  2. Identify MISMATCHES — values that differ between the two documents.
  3. Identify facts present in ONE document but missing from the other.
  4. Note anything that is ambiguous or needs clarification.

Be honest. If you are not sure whether two differently-worded values mean the same thing,
flag that as uncertain rather than resolving it yourself.

Format output clearly under:
  CONSISTENT FACTS
  MISMATCHES (show both values side-by-side)
  ONLY IN PDF-1 / ONLY IN PDF-2
  AMBIGUOUS / NEEDS CLARIFICATION
"""


def reconcile(
    client: Groq,
    label1: str,
    facts1: str,
    label2: str,
    facts2: str,
) -> str:
    """Step 2: Reconcile the two fact extracts."""
    console.print("[cyan]  → Reconciling the two documents…[/cyan]")
    user = f"""Compare the following two structured fact extracts from manufacturer documents.

=== EXTRACT FROM {label1} ===
{facts1}

=== EXTRACT FROM {label2} ===
{facts2}

Produce a clear reconciliation report.
"""
    return _call(client, RECONCILE_SYSTEM, user)


# ── Step 3 ──────────────────────────────────────────────────────────────────

DRAFT_SYSTEM = """You are helping SunBridge Trading (Nepal) prepare an import compliance draft
for a solar inverter shipment from China into Nepal.

You have:
  - A reconciliation report showing what is consistent, what mismatches, and what is missing
    across two manufacturer PDFs.
  - A reference excerpt from NEPQA 2025 describing what Nepal import reviews typically ask for.

Your job is to write a DRAFT compliance document that SunBridge can share with its Nepal
import agent. The draft should:
  1. Cover: Product Identity, Manufacturer Details, Technical Specifications,
     Test & Certification Information, Labeling & Markings.
  2. Where values match across both PDFs → state the value confidently.
  3. Where values mismatch → show BOTH values and flag the discrepancy clearly (e.g.,
     "[MISMATCH: PDF-1 says X; PDF-2 says Y — needs clarification before filing]").
  4. Where information is missing → write "Pending / Not available in current documents".
  5. End with a short "Approach Note" (3-5 sentences) explaining how you compiled the draft.

Use plain professional English. Do NOT copy the NEPQA 2025 guideline section-by-section;
use it only to decide what topics to cover and what Nepal reviewers typically want.
Do not invent technical values.
"""


def draft_compliance(
    client: Groq,
    reconciliation: str,
    nepqa_excerpt: str,
) -> str:
    """Step 3: Draft the Nepal import compliance document."""
    console.print("[cyan]  → Drafting Nepal compliance document…[/cyan]")
    user = f"""Using the reconciliation report and NEPQA 2025 reference below, write the
Nepal import compliance draft for SunBridge Trading.

=== RECONCILIATION REPORT ===
{reconciliation}

=== NEPQA 2025 REFERENCE EXCERPT ===
{nepqa_excerpt}
"""
    return _call(client, DRAFT_SYSTEM, user)


# ── Orchestrator ─────────────────────────────────────────────────────────────


def run_agent(
    client: Groq,
    pdf1_label: str,
    pdf1_text: str,
    pdf2_label: str,
    pdf2_text: str,
    nepqa_text: str,
) -> dict[str, str]:
    """
    Run the full three-step agent and return all intermediate outputs
    plus the final draft.
    """
    console.print("\n[bold green]STEP 1 — Extracting facts from manufacturer PDFs[/bold green]")
    facts1 = extract_facts(client, pdf1_label, pdf1_text)
    facts2 = extract_facts(client, pdf2_label, pdf2_text)

    console.print("\n[bold green]STEP 2 — Reconciling the two documents[/bold green]")
    reconciliation = reconcile(client, pdf1_label, facts1, pdf2_label, facts2)

    console.print("\n[bold green]STEP 3 — Drafting Nepal compliance document[/bold green]")
    # Use first ~5000 chars of NEPQA as reference context
    nepqa_excerpt = nepqa_text[:5000]
    draft = draft_compliance(client, reconciliation, nepqa_excerpt)

    return {
        "facts_pdf1": facts1,
        "facts_pdf2": facts2,
        "reconciliation": reconciliation,
        "draft": draft,
    }
