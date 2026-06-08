"""
main.py
Entry point for the Cantordust Task 1 agent (Groq free tier).

Expected layout:
  data/
    DSS_GZES230100125901_combined-1.pdf   ← Manufacturer PDF 1
    188_1115.pdf                           ← Manufacturer PDF 2
    nepqa_2025.pdf                         ← NEPQA 2025 guideline
  output/                                  ← Created automatically
"""

import os
import sys
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from src.pdf_reader import extract_text
from src.agent import run_agent
from src.report import write_all

load_dotenv()
console = Console()

# ── File configuration ────────────────────────────────────────────────────────
DATA_DIR = Path("data")

PDF1_NAME = "DSS_GZES230100125901_combined-1.pdf"
PDF2_NAME = "188_1115.pdf"
NEPQA_NAME = "nepqa_2025.pdf"   # rename your NEPQA 2025 file to this

OUTPUT_DIR = Path("output")


def check_files() -> bool:
    """Verify all required input files exist."""
    ok = True
    for name in [PDF1_NAME, PDF2_NAME, NEPQA_NAME]:
        p = DATA_DIR / name
        if not p.exists():
            console.print(f"[red]MISSING:[/red] {p}")
            ok = False
        else:
            console.print(f"[green]FOUND:[/green]   {p}")
    return ok


def main() -> None:
    console.print(Panel.fit(
        "[bold]Cantordust Task 1 — Nepal Compliance Draft Agent[/bold]\n"
        "China → Nepal | Solar Grid-Tied Inverter\n"
        "[dim]Powered by Groq (free tier) — llama-3.3-70b-versatile[/dim]",
        border_style="bright_blue",
    ))

    # ── API key ───────────────────────────────────────────────────────────────
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        console.print("[red]ERROR:[/red] GROQ_API_KEY not set. Add it to .env")
        console.print("  Get a free key at: https://console.groq.com")
        sys.exit(1)

    # ── File checks ───────────────────────────────────────────────────────────
    console.print("\n[bold]Checking input files…[/bold]")
    if not check_files():
        console.print(
            "\n[yellow]Place all required PDFs in the data/ directory and re-run.[/yellow]"
        )
        sys.exit(1)

    # ── Extract PDF text ──────────────────────────────────────────────────────
    console.print("\n[bold]Extracting text from PDFs…[/bold]")
    pdf1_text = extract_text(DATA_DIR / PDF1_NAME)
    console.print(f"  PDF 1: {len(pdf1_text):,} characters extracted")

    pdf2_text = extract_text(DATA_DIR / PDF2_NAME)
    console.print(f"  PDF 2: {len(pdf2_text):,} characters extracted")

    nepqa_text = extract_text(DATA_DIR / NEPQA_NAME)
    console.print(f"  NEPQA: {len(nepqa_text):,} characters extracted")

    # ── Run agent ─────────────────────────────────────────────────────────────
    client = Groq(api_key=api_key)
    outputs = run_agent(
        client=client,
        pdf1_label=PDF1_NAME,
        pdf1_text=pdf1_text,
        pdf2_label=PDF2_NAME,
        pdf2_text=pdf2_text,
        nepqa_text=nepqa_text,
    )

    # ── Write outputs ─────────────────────────────────────────────────────────
    console.print("\n[bold]Writing outputs…[/bold]")
    draft_path = write_all(outputs, OUTPUT_DIR)

    console.print(Panel.fit(
        f"[bold green]Done![/bold green]\n\n"
        f"Main deliverable:  [cyan]{draft_path}[/cyan]\n"
        f"Intermediate files in [cyan]{OUTPUT_DIR}/[/cyan]:\n"
        f"  • cover_note_to_ramesh.md   ← email reply to Ramesh\n"
        f"  • facts_manufacturer_pdf1.md\n"
        f"  • facts_manufacturer_pdf2.md\n"
        f"  • reconciliation_report.md\n"
        f"  • nepal_compliance_draft.md  ← share this with the agent",
        border_style="green",
    ))


if __name__ == "__main__":
    main()