import time
from typing import TypedDict

from groq import Groq
from langgraph.graph import StateGraph, END
from rich.console import Console

console = Console()

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096


# Shared state schema 

class AgentState(TypedDict):
    # Inputs 
    client: Groq
    pdf1_label: str
    pdf1_text: str
    pdf2_label: str
    pdf2_text: str
    nepqa_text: str
    # Outputs 
    facts_pdf1: str
    facts_pdf2: str
    reconciliation: str
    draft: str
    cover_note: str


# Groq helper 
def _call(client: Groq, system: str, user: str, retries: int = 3) -> str:
    """Blocking call to Groq with auto-retry on rate limit."""
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
                console.print(
                    f"[yellow]  Rate limit hit — waiting {wait}s "
                    f"before retry {attempt + 2}/{retries}…[/yellow]"
                )
                time.sleep(wait)
            else:
                raise
 

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

RECONCILE_SYSTEM = """You are a trade compliance analyst. You have been given structured fact
extracts from two manufacturer PDFs for the same or similar solar inverter product.

Your job is to:
  1. Identify facts that are CONSISTENT across both documents.
  2. Identify MISMATCHES — values that differ between the two documents.
  3. Identify SAME FACT, DIFFERENT FORMAT — where the underlying value is likely the same
     but is expressed differently (e.g. "230V" vs "230 volts", "IP65" vs "Ingress Protection 65",
     "≥97%" vs "97.6%"). Flag these separately — do not silently resolve them.
  4. Identify facts present in ONE document but missing from the other.
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

DRAFT_SYSTEM = """You are helping SunBridge Trading (Nepal) prepare an import compliance draft
for a solar inverter shipment from China into Nepal.

You have:
  - A reconciliation report showing what is consistent, what mismatches, and what is missing
    across two manufacturer PDFs.
  - A reference excerpt from NEPQA 2025 describing what Nepal import reviews typically ask for.

Your job is to write a DRAFT compliance document that SunBridge can share with its Nepal
import agent. The draft should:
  1. Open with a "DOCUMENT SUMMARY" section (2-3 sentences) that states:
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


# LangGraph nodes 

def node_extract_pdf1(state: AgentState) -> AgentState:
    """Node 1a: Extract facts from manufacturer PDF 1."""
    console.print("\n[bold green]NODE — extract_pdf1[/bold green]")
    console.print(f"[cyan]  → Extracting facts from {state['pdf1_label']}…[/cyan]")
    truncated = state["pdf1_text"][:24000]
    user = (
        f'The following is the full text of a manufacturer export document '
        f'called "{state["pdf1_label"]}".\n'
        f"Extract all facts relevant to a solar inverter Nepal import compliance review.\n\n"
        f"DOCUMENT TEXT:\n{truncated}"
    )
    return {"facts_pdf1": _call(state["client"], EXTRACT_SYSTEM, user)}


def node_extract_pdf2(state: AgentState) -> AgentState:
    """Node 1b: Extract facts from manufacturer PDF 2."""
    console.print("\n[bold green]NODE — extract_pdf2[/bold green]")
    console.print(f"[cyan]  → Extracting facts from {state['pdf2_label']}…[/cyan]")
    truncated = state["pdf2_text"][:24000]
    user = (
        f'The following is the full text of a manufacturer export document '
        f'called "{state["pdf2_label"]}".\n'
        f"Extract all facts relevant to a solar inverter Nepal import compliance review.\n\n"
        f"DOCUMENT TEXT:\n{truncated}"
    )
    return {"facts_pdf2": _call(state["client"], EXTRACT_SYSTEM, user)}


def node_reconcile(state: AgentState) -> AgentState:
    """Node 2: Reconcile the two fact extracts."""
    console.print("\n[bold green]NODE — reconcile[/bold green]")
    console.print("[cyan]  → Reconciling the two documents…[/cyan]")
    user = (
        f"Compare the following two structured fact extracts from manufacturer documents.\n\n"
        f"=== EXTRACT FROM {state['pdf1_label']} ===\n{state['facts_pdf1']}\n\n"
        f"=== EXTRACT FROM {state['pdf2_label']} ===\n{state['facts_pdf2']}\n\n"
        f"Produce a clear reconciliation report."
    )
    return {"reconciliation": _call(state["client"], RECONCILE_SYSTEM, user)}


def node_draft_compliance(state: AgentState) -> AgentState:
    """Node 3: Draft the Nepal compliance document."""
    console.print("\n[bold green]NODE — draft_compliance[/bold green]")
    console.print("[cyan]  → Drafting Nepal compliance document…[/cyan]")
    nepqa_excerpt = state["nepqa_text"][:5000].rsplit(".", 1)[0] + "."
    user = (
        f"Using the reconciliation report and NEPQA 2025 reference below, write the\n"
        f"Nepal import compliance draft for SunBridge Trading.\n\n"
        f"=== RECONCILIATION REPORT ===\n{state['reconciliation']}\n\n"
        f"=== NEPQA 2025 REFERENCE EXCERPT ===\n{nepqa_excerpt}"
    )
    return {"draft": _call(state["client"], DRAFT_SYSTEM, user)}


def node_write_cover_note(state: AgentState) -> AgentState:
    """Node 4: Write cover note to Ramesh."""
    console.print("\n[bold green]NODE — write_cover_note[/bold green]")
    console.print("[cyan]  → Writing cover note to Ramesh…[/cyan]")
    user = (
        f"Write the cover email to Ramesh based on this reconciliation summary:\n\n"
        f"{state['reconciliation'][:3000]}"
    )
    return {"cover_note": _call(state["client"], COVER_NOTE_SYSTEM, user)}


# Build graph 

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("extract_pdf1", node_extract_pdf1)
    graph.add_node("extract_pdf2", node_extract_pdf2)
    graph.add_node("reconcile", node_reconcile)
    graph.add_node("draft_compliance", node_draft_compliance)
    graph.add_node("write_cover_note", node_write_cover_note)

    # Entry points — both extractions run first
    graph.set_entry_point("extract_pdf1")
    graph.add_edge("extract_pdf1", "extract_pdf2")

    # Linear flow after extractions
    graph.add_edge("extract_pdf2", "reconcile")
    graph.add_edge("reconcile", "draft_compliance")
    graph.add_edge("draft_compliance", "write_cover_note")
    graph.add_edge("write_cover_note", END)

    return graph.compile()


# Public entry point 

def run_agent(
    client: Groq,
    pdf1_label: str,
    pdf1_text: str,
    pdf2_label: str,
    pdf2_text: str,
    nepqa_text: str,
) -> dict[str, str]:

    app = build_graph()

    initial_state: AgentState = {
        "client": client,
        "pdf1_label": pdf1_label,
        "pdf1_text": pdf1_text,
        "pdf2_label": pdf2_label,
        "pdf2_text": pdf2_text,
        "nepqa_text": nepqa_text,
        "facts_pdf1": "",
        "facts_pdf2": "",
        "reconciliation": "",
        "draft": "",
        "cover_note": "",
    }

    final_state = app.invoke(initial_state)

    return {
        "cover_note": final_state["cover_note"],
        "facts_pdf1": final_state["facts_pdf1"],
        "facts_pdf2": final_state["facts_pdf2"],
        "reconciliation": final_state["reconciliation"],
        "draft": final_state["draft"],
    }