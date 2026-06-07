"""
report.py
Write all agent outputs to the output/ directory.
"""

from datetime import datetime
from pathlib import Path


HEADER = """# SunBridge Trading — Nepal Import Compliance Draft
## China → Nepal | Solar Grid-Tied Inverter
Generated: {ts}
---

"""


def write_all(outputs: dict[str, str], output_dir: str | Path = "output") -> Path:
    """
    Write intermediate outputs and the final draft to the output directory.
    Returns the path of the final draft file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Intermediate: facts from each PDF
    for key, label in [
        ("facts_pdf1", "facts_manufacturer_pdf1"),
        ("facts_pdf2", "facts_manufacturer_pdf2"),
        ("reconciliation", "reconciliation_report"),
    ]:
        p = out / f"{label}.md"
        p.write_text(f"# {label.replace('_', ' ').title()}\nGenerated: {ts}\n\n---\n\n{outputs[key]}\n")

    # Final draft — the main deliverable
    draft_path = out / "nepal_compliance_draft.md"
    draft_path.write_text(HEADER.format(ts=ts) + outputs["draft"] + "\n")

    return draft_path
