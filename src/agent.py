"""
agent.py
Multi-step agent using Groq (free tier) that:
  1. Extracts key facts from each manufacturer PDF independently.
  2. Reconciles the two extracts and flags mismatches.
  3. Drafts the Nepal import compliance document using NEPQA 2025 as a reference.
  4. Writes a short cover note back to Ramesh at SunBridge Trading.
"""

from groq import Groq
from rich.console import Console

console = Console()

# llama-3.3-70b-versatile is Groq's best free model for long-context reasoning
MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096


import time

def _call(client: Groq, system: str, user: str, retries: int = 3) -> str:
    """Single blocking call to Groq with retry on rate limit."""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < retries - 1:
                wait = 60 * (attempt + 1)
                console.print(f"[yellow]  Rate limit hit — waiting {wait}s before retry {attempt + 2}/{retries}…[/yellow]")
                time.sleep(wait)
            else:
                raise

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
    # Groq free tier has token limits; trim large PDFs to ~12000 chars
    truncated = pdf_text[:24000]
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
  4. Identify SAME FACT, DIFFERENT FORMAT — where the underlying value is likely the same
     but is expressed differently (e.g. "230V" vs "230 volts", "IP65" vs "Ingress Protection 65",
     "≥97%" vs "97.6%"). Flag these separately — do not silently resolve them.
  5. Note anything that is ambiguous or needs clarification.

Be honest. If you are not sure whether two differently-worded values mean the same thing,
flag that as uncertain rather than resolving it yourself.

Format output clearly under:
  CONSISTENT FACTS
  MISMATCHES (show both values side-by-side)
  SAME FACT DIFFERENT FORMAT (show both, note they likely agree but need confirmation)
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
  1. Open with a "Document Summary" section that states in 2-3 sentences:
     - What product and variant PDF-1 appears to describe.
     - What product and variant PDF-2 appears to describe.
     - Whether they appear to be the same product, different variants, or unclear.
     Then cover: Product Identity, Manufacturer Details, Technical Specifications,
     Test & Certification Information, Labeling & Markings.
  2. Where values match across both PDFs → state the value confidently.
  3. Where values mismatch → show BOTH values and flag the discrepancy clearly (e.g.,
     "[MISMATCH: PDF-1 says X; PDF-2 says Y — needs clarification before filing]").
  4. Where information is missing → write "Pending / Not available in current documents".
  5. End with two sections:
     a) "APPROACH NOTE" (3-5 sentences) — how you compiled this draft.
     b) "OUTSTANDING UNCLEAR ITEMS" — a numbered list of every item that is still
        ambiguous, missing, or needs factory clarification before the Nepal agent can file.
        If nothing is unclear, write "None identified."

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


# ── Step 4 ──────────────────────────────────────────────────────────────────

COVER_NOTE_SYSTEM = """You are writing a short professional email reply from a compliance
analyst back to Ramesh at SunBridge Trading.

The email should:
  1. Be addressed to Ramesh.
  2. State clearly whether the two manufacturer PDFs appear to describe the same product
     or possibly different variants, based on the reconciliation findings.
  3. In 3-5 sentences, explain what is attached (the Nepal compliance draft), how it was
     compiled (two manufacturer PDFs reconciled against NEPQA 2025), and what he should
     watch out for (mismatches, format differences, and pending items needing factory
     clarification before the Nepal agent can file).
  4. Be plain, direct, and professional. No fluff.
  5. Sign off as: "Compliance Review Team"
"""


def write_cover_note(client: Groq, reconciliation: str) -> str:
    """Step 4: Write a short cover note to Ramesh summarising the approach."""
    console.print("[cyan]  → Writing cover note to Ramesh…[/cyan]")
    user = f"""Write the cover email to Ramesh based on this reconciliation summary:

{reconciliation[:3000]}
"""
    return _call(client, COVER_NOTE_SYSTEM, user)


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
    Run the full four-step agent and return all intermediate outputs
    plus the final draft and cover note.
    """
    console.print("\n[bold green]STEP 1 — Extracting facts from manufacturer PDFs[/bold green]")
    facts1 = extract_facts(client, pdf1_label, pdf1_text)
    facts2 = extract_facts(client, pdf2_label, pdf2_text)

    console.print("\n[bold green]STEP 2 — Reconciling the two documents[/bold green]")
    reconciliation = reconcile(client, pdf1_label, facts1, pdf2_label, facts2)

    console.print("\n[bold green]STEP 3 — Drafting Nepal compliance document[/bold green]")
    # Split at sentence boundary instead of hard cut
    nepqa_excerpt = nepqa_text[:5000].rsplit(".", 1)[0] + "."
    draft = draft_compliance(client, reconciliation, nepqa_excerpt)

    console.print("\n[bold green]STEP 4 — Writing cover note to Ramesh[/bold green]")
    cover_note = write_cover_note(client, reconciliation)

    return {
        "cover_note": cover_note,
        "facts_pdf1": facts1,
        "facts_pdf2": facts2,
        "reconciliation": reconciliation,
        "draft": draft,
    }